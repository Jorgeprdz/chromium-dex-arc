import androidx.preference.Preference;
import androidx.preference.PreferenceScreen;

import android.app.AlertDialog;

import org.chromium.chrome.browser.password_manager.ArchiumPasswordCsv;
import org.chromium.chrome.browser.password_manager.ArchiumPasswordManagerBridge;
import org.chromium.chrome.browser.password_manager.ArchiumPasswordManagerBridgeJni;
import org.chromium.chrome.browser.password_manager.ArchiumPasswordSettingsFragment;
import org.chromium.chrome.browser.profiles.Profile;

import java.io.StringReader;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.List;
import java.util.Map;

/** Executes the delivered fragment; Android/AndroidX lifecycle and JNI boundaries are synthetic. */
public final class ArchiumPasswordSettingsLifecycleSyntheticBoundaryTest {
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static ArchiumPasswordSettingsFragment create(Profile profile) {
        ArchiumPasswordSettingsFragment fragment = new ArchiumPasswordSettingsFragment();
        fragment.setProfile(profile);
        // The superclass dispatches onCreatePreferences synchronously, just as the pinned
        // PreferenceFragmentCompat does. We execute that virtual dispatch, not source matching.
        fragment.onCreate(null);
        return fragment;
    }

    private static void enabledProfileStartsBridgeDuringPreferenceCreation() {
        ArchiumPasswordManagerBridgeJni.reset();
        ArchiumPasswordSettingsFragment fragment = create(new Profile(false));
        try {
            PreferenceScreen screen = fragment.getPreferenceScreen();
            check(screen.getPreferenceCount() == 5,
                    "regular profile must construct interactive preferences during onCreate");
            check(screen.getPreference(0).getTitle().equals("Search"), "search control missing");
            check(screen.getPreference(1).getTitle().equals("Add password"), "add control missing");
            check(screen.getPreference(2).getTitle().equals("Import CSV"), "import control missing");
            check(screen.getPreference(3).getTitle().equals("Export CSV"), "export control missing");
            check(ArchiumPasswordManagerBridgeJni.initialized == 1, "one native peer expected");
            check(ArchiumPasswordManagerBridgeJni.refreshed == 1,
                    "bridge must start during synchronous preference construction");
            fragment.onCreatePreferences(null, null);
            check(ArchiumPasswordManagerBridgeJni.initialized == 1,
                    "rebuilding preferences must reuse the live peer");
            check(ArchiumPasswordManagerBridgeJni.refreshed == 1,
                    "rebuilding preferences must not start the bridge twice");
        } finally {
            fragment.onDestroy();
        }
        check(ArchiumPasswordManagerBridgeJni.destroyed == 1, "destroy must release native peer");
        check(ArchiumPasswordManagerBridgeJni.cancelled == 1, "destroy must cancel import");
    }

    private static void unavailable(Profile profile, boolean enabled, String expectedTitle) {
        ArchiumPasswordManagerBridgeJni.reset();
        ArchiumPasswordManagerBridgeJni.enabled = enabled;
        ArchiumPasswordSettingsFragment fragment = create(profile);
        try {
            PreferenceScreen screen = fragment.getPreferenceScreen();
            check(screen.getPreferenceCount() == 1, "unavailable vault must expose only one row");
            Preference row = screen.getPreference(0);
            check(row.getTitle().equals(expectedTitle), "wrong unavailable reason: " + row.getTitle());
            check(!row.isEnabled(), "unavailable row must not be interactive");
            check(ArchiumPasswordManagerBridgeJni.initialized == 0,
                    "OTR, missing profile and disabled capability must not create JNI peer");
            check(ArchiumPasswordManagerBridgeJni.refreshed == 0, "unavailable bridge must not start");
        } finally {
            fragment.onDestroy();
        }
        check(ArchiumPasswordManagerBridgeJni.destroyed == 0, "no peer may be destroyed when denied");
    }

    private static int preview(ArchiumPasswordSettingsFragment fragment, int duplicates, boolean invalid)
            throws Exception {
        return preview(fragment, duplicates, invalid, 1);
    }

    private static int preview(
            ArchiumPasswordSettingsFragment fragment, int duplicates, boolean invalid, int validRows)
            throws Exception {
        String csv = "url,username,password\nhttps://first.test/,user,synthetic\n";
        for (int i = 0; i < duplicates; i++) csv += "https://first.test/,user,synthetic\n";
        for (int i = 1; i < validRows; i++) {
            csv += "https://first.test/path" + i + ",user,synthetic\n";
        }
        if (invalid) csv += ",missing-url,synthetic\n";
        ArchiumPasswordCsv.ParseResult parsed = ArchiumPasswordCsv.parse(new StringReader(csv));
        check(parsed.duplicateCount == duplicates, "parser fixture must remove duplicates");
        Method method = fragment.getClass().getDeclaredMethod(
                "startImportPreview", ArchiumPasswordCsv.ParseResult.class);
        method.setAccessible(true);
        try {
            method.invoke(fragment, parsed);
        } catch (InvocationTargetException failure) {
            throw (Exception) failure.getCause();
        }
        for (char[] secret : ArchiumPasswordManagerBridgeJni.lastPasswords) {
            for (char c : secret) check(c == 0, "native preview input must still be erased");
        }
        return ArchiumPasswordManagerBridgeJni.previewRequest;
    }

    private static ArchiumPasswordManagerBridge.ImportRow row(int index, int kind, int decision)
            throws Exception {
        Constructor<ArchiumPasswordManagerBridge.ImportRow> constructor =
                ArchiumPasswordManagerBridge.ImportRow.class.getDeclaredConstructor(
                        int.class, int.class, String.class, String.class, String.class, int.class);
        constructor.setAccessible(true);
        return constructor.newInstance(index, kind, "https://first.test/", "user",
                "https://first.test/", decision);
    }

    private static void summary(int duplicates, int invalid) {
        AlertDialog dialog = AlertDialog.lastShown;
        check(dialog != null && dialog.title.equals("Review password import"),
                "actual fragment must show the review summary");
        String text = dialog.message.toString();
        check(text.contains("\nDuplicates: " + duplicates + "\n"),
                "displayed summary lost parser/native duplicates: " + text);
        check(text.contains("\nInvalid: " + invalid + "\n"),
                "displayed summary lost invalid rows");
    }

    private static void parserDuplicatesSurviveRequestAndConflictCallbacks() throws Exception {
        ArchiumPasswordManagerBridgeJni.reset();
        ArchiumPasswordSettingsFragment fragment = create(new Profile(false));
        try {
            int first = preview(fragment, 2, true, 4);
            int second = preview(fragment, 0, false);
            fragment.onPreview(second, ArchiumPasswordManagerBridge.SUCCESS, List.of(row(0, 0, 1)));
            summary(0, 0);
            fragment.onPreview(first, ArchiumPasswordManagerBridge.SUCCESS,
                    List.of(row(0, 2, 2), row(1, 1, 0), row(2, 4, 0), row(3, 3, 0)));
            check(AlertDialog.lastShown.title.equals("Review import conflict"), "conflict not reviewed");
            AlertDialog.lastShown.clickPositive();
            summary(4, 2); // Two parser duplicates plus exact-store/file duplicate; one invalid each.
            check(AlertDialog.lastShown.message.toString().contains("Replacements: 1"),
                    "replacement decision must remain unchanged");
            AlertDialog.lastShown.clickPositive();
            check(ArchiumPasswordManagerBridgeJni.confirmedRequest == first, "wrong import confirmed");
            check(java.util.Arrays.equals(ArchiumPasswordManagerBridgeJni.confirmedDecisions,
                    new int[] {2, 0, 0, 0}), "source counts must not change native decisions");

            int skipped = preview(fragment, 1, false);
            fragment.onPreview(skipped, ArchiumPasswordManagerBridge.SUCCESS, List.of(row(0, 5, 1)));
            AlertDialog.lastShown.clickNegative();
            summary(1, 0);
            check(AlertDialog.lastShown.message.toString().contains("Skipped: 1"),
                    "skip conflict callback must preserve the summary counts");
        } finally {
            fragment.onDestroy();
        }
    }

    private static int pendingSourceCounts(ArchiumPasswordSettingsFragment fragment) throws Exception {
        Field field = fragment.getClass().getDeclaredField("mPreviewSourceCounts");
        field.setAccessible(true);
        return ((Map<?, ?>) field.get(fragment)).size();
    }

    private static void importSourceCountsAreClearedOnFailureAndDestroy() throws Exception {
        ArchiumPasswordManagerBridgeJni.reset();
        ArchiumPasswordSettingsFragment fragment = create(new Profile(false));
        try {
            int rejected = preview(fragment, 3, true);
            fragment.onPreview(rejected, ArchiumPasswordManagerBridge.BUSY, List.of());
            check(pendingSourceCounts(fragment) == 0, "native rejection must release source counts");
            fragment.onPreview(rejected, ArchiumPasswordManagerBridge.SUCCESS, List.of(row(0, 0, 1)));
            summary(0, 0); // A repeated callback cannot reuse the rejected source metadata.

            ArchiumPasswordManagerBridgeJni.throwPreview = true;
            try {
                preview(fragment, 4, true);
                throw new AssertionError("synthetic JNI failure must reach the caller");
            } catch (IllegalStateException expected) {
                check(pendingSourceCounts(fragment) == 0, "JNI exception must release source counts");
                for (char[] secret : ArchiumPasswordManagerBridgeJni.lastPasswords) {
                    for (char c : secret) check(c == 0, "failed preview must still erase secrets");
                }
            }
            ArchiumPasswordManagerBridgeJni.throwPreview = false;
            preview(fragment, 2, false);
            check(pendingSourceCounts(fragment) == 1, "pending request must retain only its own counts");
        } finally {
            fragment.onDestroy();
        }
        check(pendingSourceCounts(fragment) == 0, "destroy must release pending source counts");
        AlertDialog.lastShown = null;
        fragment.onPreview(ArchiumPasswordManagerBridgeJni.previewRequest,
                ArchiumPasswordManagerBridge.SUCCESS, List.of(row(0, 0, 1)));
        check(AlertDialog.lastShown == null, "late preview must not open a summary after destroy");
    }

    public static void main(String[] args) throws Exception {
        enabledProfileStartsBridgeDuringPreferenceCreation();
        unavailable(new Profile(true), true, "Local passwords are unavailable in Incognito");
        unavailable(null, true, "Local passwords are unavailable in Incognito");
        unavailable(new Profile(false), false, "Local password storage is unavailable");
        parserDuplicatesSurviveRequestAndConflictCallbacks();
        importSourceCountsAreClearedOnFailureAndDestroy();
        System.out.println("PASS: password settings lifecycle/import summary (synthetic Android/dialog/JNI boundaries)");
    }
}
