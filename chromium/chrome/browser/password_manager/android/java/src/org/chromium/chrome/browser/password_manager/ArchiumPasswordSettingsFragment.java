// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package org.chromium.chrome.browser.password_manager;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ContentResolver;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.DocumentsContract;
import android.text.Editable;
import android.text.InputType;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.preference.Preference;
import androidx.preference.PreferenceCategory;
import androidx.preference.PreferenceScreen;

import org.chromium.base.supplier.ObservableSuppliers;
import org.chromium.base.supplier.SettableMonotonicObservableSupplier;
import org.chromium.build.annotations.NullMarked;
import org.chromium.build.annotations.Nullable;
import org.chromium.chrome.browser.settings.ChromeBaseSettingsFragment;
import org.chromium.chrome.browser.profiles.Profile;
import org.chromium.components.browser_ui.settings.SettingsFragment;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Native settings surface for Archium's profile-local password vault.
 *
 * <p>Metadata is safe to list without device authentication. Reveal, CRUD, import confirmation and
 * export are authenticated by the native manager. SAF is the only file transport.
 */
@NullMarked
public final class ArchiumPasswordSettingsFragment extends ChromeBaseSettingsFragment
        implements ArchiumPasswordManagerBridge.Listener {
    private static final int REQUEST_OPEN_CSV = 7401;
    private static final int REQUEST_CREATE_CSV = 7402;

    private static final int PREVIEW_NEW = 0;
    private static final int PREVIEW_EXACT = 1;
    private static final int PREVIEW_STORE_CONFLICT = 2;
    private static final int PREVIEW_INVALID = 3;
    private static final int PREVIEW_FILE_DUPLICATE = 4;
    private static final int PREVIEW_FILE_CONFLICT = 5;

    private static final int DECISION_SKIP = 0;
    private static final int DECISION_IMPORT = 1;
    private static final int DECISION_REPLACE = 2;

    private final SettableMonotonicObservableSupplier<String> mPageTitle =
            ObservableSuppliers.createMonotonic();
    private final ExecutorService mIo = Executors.newSingleThreadExecutor();
    private final Handler mMain = new Handler(Looper.getMainLooper());
    private final Map<Integer, ArchiumPasswordManagerBridge.Entry> mRevealRequests =
            new HashMap<>();
    private static final class ImportSourceCounts {
        final int invalidRows;
        final int duplicateRows;

        ImportSourceCounts(int invalidRows, int duplicateRows) {
            this.invalidRows = invalidRows;
            this.duplicateRows = duplicateRows;
        }
    }

    private final Map<Integer, ImportSourceCounts> mPreviewSourceCounts = new HashMap<>();
    private final Set<AlertDialog> mDialogs = new HashSet<>();
    private final Set<ExportWriteTask> mPendingExportTasks = ConcurrentHashMap.newKeySet();

    private @Nullable ArchiumPasswordManagerBridge mBridge;
    private @Nullable PreferenceCategory mEntriesCategory;
    private @Nullable Uri mPendingExportUri;
    private int mPendingExportRequest;
    private int mNextRequest = 1;
    private String mQuery = "";
    private List<ArchiumPasswordManagerBridge.Entry> mEntries = List.of();
    private volatile boolean mDestroyed;
    private boolean mOffTheRecord;

    @Override
    public void onCreate(@Nullable Bundle savedInstanceState) {
        mPageTitle.set("Local passwords");
        super.onCreate(savedInstanceState);
    }

    @Override
    public void onCreatePreferences(@Nullable Bundle savedInstanceState, @Nullable String rootKey) {
        // PreferenceFragmentCompat calls this synchronously from super.onCreate(). The
        // Settings profile is already injected; initialize before choosing the screen.
        Profile profile = getProfile();
        mOffTheRecord = profile == null || profile.isOffTheRecord();
        if (mBridge == null && !mOffTheRecord && ArchiumPasswordManagerBridge.isLocalEnabled()) {
            mBridge = new ArchiumPasswordManagerBridge(requireActivity(), profile, this);
        }
        PreferenceScreen screen = getPreferenceManager().createPreferenceScreen(requireContext());
        setPreferenceScreen(screen);

        // Do not even present interactive list/search/CRUD/SAF controls in OTR.
        ArchiumPasswordManagerBridge bridge = mBridge;
        if (mOffTheRecord || bridge == null) {
            Preference unavailable = new Preference(requireContext());
            unavailable.setTitle(mOffTheRecord
                    ? "Local passwords are unavailable in Incognito"
                    : "Local password storage is unavailable");
            unavailable.setEnabled(false);
            screen.addPreference(unavailable);
            return;
        }

        Preference search = new Preference(requireContext());
        search.setTitle("Search");
        search.setSummary("Filter by site or username");
        search.setOnPreferenceClickListener(
                preference -> {
                    showSearchDialog();
                    return true;
                });
        screen.addPreference(search);

        Preference add = new Preference(requireContext());
        add.setTitle("Add password");
        add.setSummary("Save a credential in this device profile");
        add.setOnPreferenceClickListener(
                preference -> {
                    showAddDialog();
                    return true;
                });
        screen.addPreference(add);

        Preference importCsv = new Preference(requireContext());
        importCsv.setTitle("Import CSV");
        importCsv.setSummary("Review before anything is written");
        importCsv.setOnPreferenceClickListener(
                preference -> {
                    launchImportPicker();
                    return true;
                });
        screen.addPreference(importCsv);

        Preference exportCsv = new Preference(requireContext());
        exportCsv.setTitle("Export CSV");
        exportCsv.setSummary("Device authentication is required before secrets are read");
        exportCsv.setOnPreferenceClickListener(
                preference -> {
                    launchExportPicker();
                    return true;
                });
        screen.addPreference(exportCsv);

        mEntriesCategory = new PreferenceCategory(requireContext());
        mEntriesCategory.setTitle("Saved passwords");
        screen.addPreference(mEntriesCategory);

        bridge.start();
    }

    @Override
    public SettableMonotonicObservableSupplier<String> getPageTitle() {
        return mPageTitle;
    }

    @Override
    public @SettingsFragment.AnimationType int getAnimationType() {
        return SettingsFragment.AnimationType.PROPERTY;
    }

    private int nextRequest() {
        return mNextRequest++;
    }

    private void showTrackedDialog(AlertDialog dialog) {
        if (mDestroyed) {
            dialog.dismiss();
            return;
        }
        mDialogs.add(dialog);
        dialog.setOnDismissListener(ignored -> mDialogs.remove(dialog));
        dialog.show();
    }

    private static char[] consumeSecret(EditText input) {
        Editable editable = input.getText();
        char[] secret = new char[editable.length()];
        editable.getChars(0, editable.length(), secret, 0);
        editable.clear();
        return secret;
    }

    private void setUnavailable(String message) {
        if (mEntriesCategory == null) return;
        mEntriesCategory.removeAll();
        Preference row = new Preference(requireContext());
        row.setTitle(message);
        row.setEnabled(false);
        mEntriesCategory.addPreference(row);
    }

    private void rebuildEntries() {
        if (mEntriesCategory == null || mDestroyed) return;
        mEntriesCategory.removeAll();
        String query = mQuery.trim().toLowerCase(Locale.ROOT);
        int shown = 0;
        for (ArchiumPasswordManagerBridge.Entry entry : mEntries) {
            String haystack = (entry.url + "\n" + entry.username).toLowerCase(Locale.ROOT);
            if (!query.isEmpty() && !haystack.contains(query)) continue;
            Preference row = new Preference(requireContext());
            row.setTitle(entry.username.isEmpty() ? "(no username)" : entry.username);
            row.setSummary(entry.url);
            row.setOnPreferenceClickListener(
                    preference -> {
                        showEntryActions(entry);
                        return true;
                    });
            mEntriesCategory.addPreference(row);
            shown++;
        }
        if (shown == 0) {
            Preference empty = new Preference(requireContext());
            empty.setTitle(query.isEmpty() ? "No saved passwords" : "No matching passwords");
            empty.setEnabled(false);
            mEntriesCategory.addPreference(empty);
        }
    }

    private void showSearchDialog() {
        EditText input = new EditText(requireContext());
        input.setSingleLine(true);
        input.setText(mQuery);
        input.setSelectAllOnFocus(true);
        AlertDialog dialog =
                new AlertDialog.Builder(requireContext())
                        .setTitle("Search saved passwords")
                        .setView(input)
                        .setPositiveButton(
                                android.R.string.ok,
                                (ignored, which) -> {
                                    mQuery = input.getText().toString();
                                    rebuildEntries();
                                })
                        .setNegativeButton(android.R.string.cancel, null)
                        .setNeutralButton(
                                "Clear",
                                (ignored, which) -> {
                                    mQuery = "";
                                    rebuildEntries();
                                })
                        .create();
        showTrackedDialog(dialog);
    }

    private LinearLayout credentialForm(
            @Nullable String url, @Nullable String username, boolean editableUrl) {
        LinearLayout layout = new LinearLayout(requireContext());
        layout.setOrientation(LinearLayout.VERTICAL);
        int padding = Math.round(20 * getResources().getDisplayMetrics().density);
        layout.setPadding(padding, 0, padding, 0);

        EditText urlInput = new EditText(requireContext());
        urlInput.setTag("url");
        urlInput.setHint("https://example.com");
        urlInput.setSingleLine(true);
        urlInput.setEnabled(editableUrl);
        if (url != null) urlInput.setText(url);
        layout.addView(
                urlInput,
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        EditText usernameInput = new EditText(requireContext());
        usernameInput.setTag("username");
        usernameInput.setHint("Username");
        usernameInput.setSingleLine(true);
        if (username != null) usernameInput.setText(username);
        layout.addView(
                usernameInput,
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        EditText passwordInput = new EditText(requireContext());
        passwordInput.setTag("password");
        passwordInput.setHint("Password");
        passwordInput.setSingleLine(true);
        passwordInput.setInputType(
                InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        layout.addView(
                passwordInput,
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        return layout;
    }

    private static EditText field(LinearLayout layout, String tag) {
        for (int i = 0; i < layout.getChildCount(); i++) {
            if (layout.getChildAt(i) instanceof EditText
                    && tag.equals(layout.getChildAt(i).getTag())) {
                return (EditText) layout.getChildAt(i);
            }
        }
        throw new IllegalStateException("Missing credential field " + tag);
    }

    private void showAddDialog() {
        ArchiumPasswordManagerBridge bridge = mBridge;
        if (bridge == null) return;
        LinearLayout form = credentialForm(null, null, true);
        AlertDialog dialog =
                new AlertDialog.Builder(requireContext())
                        .setTitle("Add password")
                        .setView(form)
                        .setPositiveButton("Save", null)
                        .setNegativeButton(android.R.string.cancel, null)
                        .create();
        dialog.setOnShowListener(
                ignored ->
                        dialog.getButton(AlertDialog.BUTTON_POSITIVE)
                                .setOnClickListener(
                                        view -> {
                                            String url = field(form, "url").getText().toString().trim();
                                            String username =
                                                    field(form, "username").getText().toString();
                                            char[] password =
                                                    consumeSecret(field(form, "password"));
                                            if (url.isEmpty() || password.length == 0) {
                                                Arrays.fill(password, '\0');
                                                Toast.makeText(
                                                                requireContext(),
                                                                "Site and password are required.",
                                                                Toast.LENGTH_SHORT)
                                                        .show();
                                                return;
                                            }
                                            bridge.add(
                                                    nextRequest(), url, username, password);
                                            dialog.dismiss();
                                        }));
        showTrackedDialog(dialog);
    }

    private void showEntryActions(ArchiumPasswordManagerBridge.Entry entry) {
        AlertDialog dialog =
                new AlertDialog.Builder(requireContext())
                        .setTitle(entry.username.isEmpty() ? entry.url : entry.username)
                        .setItems(
                                new String[] {"Reveal password", "Edit", "Delete"},
                                (ignored, which) -> {
                                    if (which == 0) reveal(entry);
                                    else if (which == 1) showEditDialog(entry);
                                    else confirmDelete(entry);
                                })
                        .create();
        showTrackedDialog(dialog);
    }

    private void reveal(ArchiumPasswordManagerBridge.Entry entry) {
        ArchiumPasswordManagerBridge bridge = mBridge;
        if (bridge == null) return;
        int request = nextRequest();
        mRevealRequests.put(request, entry);
        bridge.reveal(request, entry.id);
    }

    private void showEditDialog(ArchiumPasswordManagerBridge.Entry entry) {
        ArchiumPasswordManagerBridge bridge = mBridge;
        if (bridge == null) return;
        LinearLayout form = credentialForm(entry.url, entry.username, false);
        AlertDialog dialog =
                new AlertDialog.Builder(requireContext())
                        .setTitle("Edit password")
                        .setMessage("Enter the new password. The site cannot be changed in-place.")
                        .setView(form)
                        .setPositiveButton("Save", null)
                        .setNegativeButton(android.R.string.cancel, null)
                        .create();
        dialog.setOnShowListener(
                ignored ->
                        dialog.getButton(AlertDialog.BUTTON_POSITIVE)
                                .setOnClickListener(
                                        view -> {
                                            String username =
                                                    field(form, "username").getText().toString();
                                            char[] password =
                                                    consumeSecret(field(form, "password"));
                                            if (password.length == 0) {
                                                Arrays.fill(password, '\0');
                                                Toast.makeText(
                                                                requireContext(),
                                                                "Enter a new password.",
                                                                Toast.LENGTH_SHORT)
                                                        .show();
                                                return;
                                            }
                                            bridge.update(
                                                    nextRequest(), entry.id, username, password);
                                            dialog.dismiss();
                                        }));
        showTrackedDialog(dialog);
    }

    private void confirmDelete(ArchiumPasswordManagerBridge.Entry entry) {
        ArchiumPasswordManagerBridge bridge = mBridge;
        if (bridge == null) return;
        AlertDialog dialog =
                new AlertDialog.Builder(requireContext())
                        .setTitle("Delete password?")
                        .setMessage(entry.url)
                        .setPositiveButton(
                                "Delete",
                                (ignored, which) -> bridge.delete(nextRequest(), entry.id))
                        .setNegativeButton(android.R.string.cancel, null)
                        .create();
        showTrackedDialog(dialog);
    }

    private void launchImportPicker() {
        Intent intent =
                new Intent(Intent.ACTION_OPEN_DOCUMENT)
                        .addCategory(Intent.CATEGORY_OPENABLE)
                        .setType("text/*");
        startActivityForResult(intent, REQUEST_OPEN_CSV);
    }

    private void launchExportPicker() {
        Intent intent =
                new Intent(Intent.ACTION_CREATE_DOCUMENT)
                        .addCategory(Intent.CATEGORY_OPENABLE)
                        .setType("text/csv")
                        .putExtra(Intent.EXTRA_TITLE, "archium-passwords.csv");
        startActivityForResult(intent, REQUEST_CREATE_CSV);
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode != Activity.RESULT_OK || data == null || data.getData() == null) return;
        Uri uri = data.getData();
        if (requestCode == REQUEST_OPEN_CSV) {
            parseImport(uri);
        } else if (requestCode == REQUEST_CREATE_CSV) {
            mPendingExportUri = uri;
            mPendingExportRequest = nextRequest();
            ArchiumPasswordManagerBridge bridge = mBridge;
            if (bridge != null) bridge.export(mPendingExportRequest);
        }
    }

    private void parseImport(Uri uri) {
        ContentResolver resolver = requireContext().getContentResolver();
        mIo.execute(
                () -> {
                    try (InputStream stream = resolver.openInputStream(uri)) {
                        if (stream == null) throw new java.io.IOException("Unable to open selected file");
                        var decoder =
                                StandardCharsets.UTF_8
                                        .newDecoder()
                                        .onMalformedInput(CodingErrorAction.REPORT)
                                        .onUnmappableCharacter(CodingErrorAction.REPORT);
                        ArchiumPasswordCsv.ParseResult result;
                        // ArchiumPasswordCsv owns and scrubs its own char buffer.
                        // Avoid adding an opaque BufferedReader containing secrets.
                        try (InputStreamReader reader = new InputStreamReader(stream, decoder)) {
                            result = ArchiumPasswordCsv.parse(reader);
                        }
                        if (!mMain.post(() -> startImportPreview(result))) result.close();
                    } catch (Exception error) {
                        // Reader/provider exceptions are untrusted; never display their
                        // messages because some implementations embed field contents.
                        mMain.post(() -> showError("Import failed", "Could not read the selected CSV."));
                    }
                });
    }

    private void startImportPreview(ArchiumPasswordCsv.ParseResult parsed) {
      try {
        if (mDestroyed) return;
        if (parsed.rows.isEmpty()) {
            if (!parsed.errors.isEmpty()) {
                showError(
                        "CSV needs attention",
                        parsed.errors.size()
                                + " invalid row(s) found. There are no valid passwords to import.");
            } else {
                Toast.makeText(
                                requireContext(),
                                "No passwords found in the CSV.",
                                Toast.LENGTH_SHORT)
                        .show();
            }
            return;
        }

        String[] urls = new String[parsed.rows.size()];
        String[] users = new String[parsed.rows.size()];
        char[][] passwords = new char[parsed.rows.size()][];
        for (int i = 0; i < parsed.rows.size(); i++) {
            ArchiumPasswordCsv.Row row = parsed.rows.get(i);
            urls[i] = row.url;
            users[i] = row.username;
            passwords[i] = row.copyPassword();
        }

        int request = nextRequest();
        mPreviewSourceCounts.put(
                request, new ImportSourceCounts(parsed.errors.size(), parsed.duplicateCount));
        ArchiumPasswordManagerBridge bridge = mBridge;
        if (bridge != null) {
            try {
                bridge.previewImport(request, urls, users, passwords);
            } catch (RuntimeException | Error failure) {
                mPreviewSourceCounts.remove(request);
                throw failure;
            }
        } else {
            mPreviewSourceCounts.remove(request);
            for (char[] password : passwords) Arrays.fill(password, '\0');
        }
      } finally {
          // Erase every parser-owned password on success, early return,
          // cancellation, and even if JNI throws.
          parsed.close();
      }
    }

    private void reviewImport(
            int request,
            ImportSourceCounts sourceCounts,
            List<ArchiumPasswordManagerBridge.ImportRow> rows) {
        int maxIndex = -1;
        for (ArchiumPasswordManagerBridge.ImportRow row : rows) {
            maxIndex = Math.max(maxIndex, row.index);
        }
        int[] decisions = new int[maxIndex + 1];
        Set<String> acceptedFileConflicts = new HashSet<>();
        reviewNextConflict(
                request, sourceCounts, rows, decisions, acceptedFileConflicts, 0);
    }

    private void reviewNextConflict(
            int request,
            ImportSourceCounts sourceCounts,
            List<ArchiumPasswordManagerBridge.ImportRow> rows,
            int[] decisions,
            Set<String> acceptedFileConflicts,
            int position) {
        if (mDestroyed) return;
        for (int i = position; i < rows.size(); i++) {
            ArchiumPasswordManagerBridge.ImportRow row = rows.get(i);
            if (row.kind == PREVIEW_NEW) {
                decisions[row.index] = DECISION_IMPORT;
                continue;
            }
            if (row.kind == PREVIEW_EXACT
                    || row.kind == PREVIEW_INVALID
                    || row.kind == PREVIEW_FILE_DUPLICATE) {
                decisions[row.index] = DECISION_SKIP;
                continue;
            }
            if (row.kind == PREVIEW_STORE_CONFLICT || row.kind == PREVIEW_FILE_CONFLICT) {
                final int next = i + 1;
                final String identity = row.identity + "\u0000" + row.username;
                if (row.kind == PREVIEW_FILE_CONFLICT
                        && acceptedFileConflicts.contains(identity)) {
                    decisions[row.index] = DECISION_SKIP;
                    continue;
                }
                final int acceptedDecision = row.requiredDecision;
                if (acceptedDecision != DECISION_IMPORT
                        && acceptedDecision != DECISION_REPLACE) {
                    decisions[row.index] = DECISION_SKIP;
                    continue;
                }
                String message =
                        row.url
                                + "\n"
                                + (row.username.isEmpty() ? "(no username)" : row.username)
                                + (row.kind == PREVIEW_STORE_CONFLICT
                                        ? "\n\nA different password is already saved."
                                        : "\n\nThe CSV contains more than one password for this login.");
                AlertDialog dialog =
                        new AlertDialog.Builder(requireContext())
                                .setTitle("Review import conflict")
                                .setMessage(message)
                                .setPositiveButton(
                                        acceptedDecision == DECISION_REPLACE
                                                ? "Replace"
                                                : "Use this row",
                                        (ignored, which) -> {
                                            decisions[row.index] = acceptedDecision;
                                            if (row.kind == PREVIEW_FILE_CONFLICT) {
                                                acceptedFileConflicts.add(identity);
                                            }
                                            reviewNextConflict(
                                                    request,
                                                    sourceCounts,
                                                    rows,
                                                    decisions,
                                                    acceptedFileConflicts,
                                                    next);
                                        })
                                .setNegativeButton(
                                        "Skip",
                                        (ignored, which) -> {
                                            decisions[row.index] = DECISION_SKIP;
                                            reviewNextConflict(
                                                    request,
                                                    sourceCounts,
                                                    rows,
                                                    decisions,
                                                    acceptedFileConflicts,
                                                    next);
                                        })
                                .setOnCancelListener(
                                        ignored -> {
                                            ArchiumPasswordManagerBridge bridge = mBridge;
                                            if (bridge != null) bridge.cancelImport();
                                        })
                                .create();
                showTrackedDialog(dialog);
                return;
            }
        }
        showImportSummary(request, sourceCounts, rows, decisions);
    }

    private void showImportSummary(
            int request,
            ImportSourceCounts sourceCounts,
            List<ArchiumPasswordManagerBridge.ImportRow> rows,
            int[] decisions) {
        if (mDestroyed) return;
        int added = 0;
        int replaced = 0;
        int duplicates = sourceCounts.duplicateRows;
        int invalid = sourceCounts.invalidRows;
        int skipped = 0;
        for (ArchiumPasswordManagerBridge.ImportRow row : rows) {
            if (row.kind == PREVIEW_EXACT || row.kind == PREVIEW_FILE_DUPLICATE) {
                duplicates++;
            } else if (row.kind == PREVIEW_INVALID) {
                invalid++;
            } else if (decisions[row.index] == DECISION_REPLACE) {
                replaced++;
            } else if (decisions[row.index] == DECISION_IMPORT) {
                added++;
            } else {
                skipped++;
            }
        }

        String summary =
                "New: "
                        + added
                        + "\nReplacements: "
                        + replaced
                        + "\nDuplicates: "
                        + duplicates
                        + "\nInvalid: "
                        + invalid
                        + "\nSkipped: "
                        + skipped
                        + "\n\nNothing will be written until you confirm.";
        AlertDialog dialog =
                new AlertDialog.Builder(requireContext())
                        .setTitle("Review password import")
                        .setMessage(summary)
                        .setPositiveButton(
                                "Confirm import",
                                (ignored, which) -> {
                                    ArchiumPasswordManagerBridge bridge = mBridge;
                                    if (bridge != null) {
                                        bridge.confirmImport(request, decisions);
                                    }
                                })
                        .setNegativeButton(
                                android.R.string.cancel,
                                (ignored, which) -> {
                                    ArchiumPasswordManagerBridge bridge = mBridge;
                                    if (bridge != null) bridge.cancelImport();
                                })
                        .setOnCancelListener(
                                ignored -> {
                                    ArchiumPasswordManagerBridge bridge = mBridge;
                                    if (bridge != null) bridge.cancelImport();
                                })
                        .create();
        showTrackedDialog(dialog);
    }

    private final class ExportWriteTask implements Runnable {
        private final ContentResolver mResolver;
        private final Uri mUri;
        private final List<ArchiumPasswordCsv.SecretRow> mRows;
        private final AtomicBoolean mClaimed = new AtomicBoolean();

        ExportWriteTask(
                ContentResolver resolver,
                Uri uri,
                List<ArchiumPasswordCsv.SecretRow> rows) {
            mResolver = resolver;
            mUri = uri;
            mRows = rows;
        }

        @Override
        public void run() {
            if (!mClaimed.compareAndSet(false, true)) return;
            mPendingExportTasks.remove(this);
            String error = null;
            try (OutputStream stream = mResolver.openOutputStream(mUri, "wt");
                    OutputStreamWriter writer =
                            stream == null ? null : new OutputStreamWriter(stream, StandardCharsets.UTF_8)) {
                if (writer == null || mDestroyed || Thread.currentThread().isInterrupted()) {
                    throw new java.io.IOException("Export unavailable or cancelled");
                }
                // StreamEncoder already buffers output; avoid a second opaque
                // BufferedWriter holding a copy of exported secrets.
                ArchiumPasswordCsv.writeSecrets(writer, mRows);
                writer.flush();
            } catch (Exception failure) {
                error = "Could not write the selected CSV.";
            } finally {
                for (ArchiumPasswordCsv.SecretRow row : mRows) row.close();
            }
            if (error != null) {
                // This URI came exclusively from ACTION_CREATE_DOCUMENT.
                // A provider failure can leave a partial plaintext CSV; ask
                // SAF to remove that newly created document. Providers may
                // refuse deletion, so this is best-effort, not secure erasure.
                try {
                    DocumentsContract.deleteDocument(mResolver, mUri);
                } catch (Exception ignored) {
                    // Never surface provider exception text or credential data.
                }
            }

            String finalError = error;
            mMain.post(
                    () -> {
                        if (mDestroyed) return;
                        if (finalError == null) {
                            Toast.makeText(
                                            requireContext(),
                                            "Passwords exported.",
                                            Toast.LENGTH_SHORT)
                                    .show();
                        } else {
                            showError("Export failed", finalError);
                        }
                    });
        }

        void cancelWithoutRunning() {
            if (!mClaimed.compareAndSet(false, true)) return;
            mPendingExportTasks.remove(this);
            for (ArchiumPasswordCsv.SecretRow row : mRows) row.close();
        }
    }

    private void writeExport(Uri uri, List<ArchiumPasswordCsv.SecretRow> rows) {
        ExportWriteTask task = new ExportWriteTask(
                requireContext().getContentResolver(), uri, rows);
        mPendingExportTasks.add(task);
        try {
            mIo.execute(task);
        } catch (RuntimeException rejected) {
            task.cancelWithoutRunning();
            if (!mDestroyed) showError("Export failed", "Export task was not accepted.");
        }
    }

    private void showError(String title, @Nullable String detail) {
        if (mDestroyed || !isAdded()) return;
        AlertDialog dialog =
                new AlertDialog.Builder(requireContext())
                        .setTitle(title)
                        .setMessage(detail == null || detail.isEmpty() ? "Operation failed." : detail)
                        .setPositiveButton(android.R.string.ok, null)
                        .create();
        showTrackedDialog(dialog);
    }

    private static String statusMessage(int status) {
        return switch (status) {
            case ArchiumPasswordManagerBridge.AUTHENTICATION_FAILED ->
                    "Device authentication failed.";
            case ArchiumPasswordManagerBridge.BUSY -> "Another protected operation is running.";
            case ArchiumPasswordManagerBridge.STALE ->
                    "The password list changed. Refresh and try again.";
            case ArchiumPasswordManagerBridge.INVALID -> "The requested change is not valid.";
            case ArchiumPasswordManagerBridge.WRITE_FAILED ->
                    "The password store did not confirm the change.";
            default -> "Local password storage is unavailable.";
        };
    }

    @Override
    public void onMetadata(List<ArchiumPasswordManagerBridge.Entry> entries, int status) {
        if (mDestroyed) return;
        if (status != ArchiumPasswordManagerBridge.SUCCESS) {
            setUnavailable(statusMessage(status));
            return;
        }
        mEntries = entries;
        rebuildEntries();
    }

    @Override
    public void onSecret(int request, int status, char[] password) {
        ArchiumPasswordManagerBridge.Entry entry = mRevealRequests.remove(request);
        if (mDestroyed || entry == null) return;
        if (status != ArchiumPasswordManagerBridge.SUCCESS) {
            showError("Couldn't reveal password", statusMessage(status));
            return;
        }

        TextView secret = new TextView(requireContext());
        int padding = Math.round(20 * getResources().getDisplayMetrics().density);
        secret.setPadding(padding, padding, padding, padding);
        secret.setTextIsSelectable(true);
        secret.setText(password, 0, password.length);
        AlertDialog dialog =
                new AlertDialog.Builder(requireContext())
                        .setTitle(entry.username.isEmpty() ? entry.url : entry.username)
                        .setView(secret)
                        .setPositiveButton(android.R.string.ok, null)
                        .create();
        if (mDestroyed) {
            secret.setText("");
            dialog.dismiss();
            return;
        }
        mDialogs.add(dialog);
        dialog.setOnDismissListener(
                ignored -> {
                    secret.setText("");
                    mDialogs.remove(dialog);
                });
        dialog.show();
    }

    @Override
    public void onExport(
            int request, int status, List<ArchiumPasswordCsv.SecretRow> rows) {
        Uri destination =
                request == mPendingExportRequest ? mPendingExportUri : null;
        mPendingExportUri = null;
        mPendingExportRequest = 0;
        if (mDestroyed || status != ArchiumPasswordManagerBridge.SUCCESS || destination == null) {
            for (ArchiumPasswordCsv.SecretRow row : rows) row.close();
            if (!mDestroyed && status != ArchiumPasswordManagerBridge.SUCCESS) {
                showError("Couldn't export passwords", statusMessage(status));
            }
            return;
        }
        writeExport(destination, rows);
    }

    @Override
    public void onPreview(
            int request, int status, List<ArchiumPasswordManagerBridge.ImportRow> rows) {
        ImportSourceCounts sourceCounts = mPreviewSourceCounts.remove(request);
        if (mDestroyed) return;
        if (status != ArchiumPasswordManagerBridge.SUCCESS) {
            showError("Couldn't review import", statusMessage(status));
            return;
        }
        reviewImport(
                request, sourceCounts == null ? new ImportSourceCounts(0, 0) : sourceCounts, rows);
    }

    @Override
    public void onOperation(int request, int status) {
        if (mDestroyed) return;
        if (status == ArchiumPasswordManagerBridge.SUCCESS) {
            Toast.makeText(requireContext(), "Password store updated.", Toast.LENGTH_SHORT).show();
            ArchiumPasswordManagerBridge bridge = mBridge;
            if (bridge != null) bridge.refresh();
        } else {
            showError("Password operation failed", statusMessage(status));
        }
    }

    @Override
    public void onDestroy() {
        mDestroyed = true;
        for (AlertDialog dialog : List.copyOf(mDialogs)) dialog.dismiss();
        mDialogs.clear();
        mRevealRequests.clear();
        mPreviewSourceCounts.clear();
        ArchiumPasswordManagerBridge bridge = mBridge;
        mBridge = null;
        if (bridge != null) {
            bridge.cancelImport();
            bridge.destroy();
        }
        mIo.shutdownNow();
        for (ExportWriteTask task : List.copyOf(mPendingExportTasks)) {
            task.cancelWithoutRunning();
        }
        mPendingExportTasks.clear();
        super.onDestroy();
    }
}
