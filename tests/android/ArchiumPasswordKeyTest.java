package app.archium.keytests;

import android.app.Instrumentation;
import android.content.Context;
import android.os.Bundle;
import android.util.AtomicFile;

import java.io.FileOutputStream;
import java.io.IOException;

import java.io.File;
import java.lang.reflect.InvocationTargetException;
import java.nio.file.Files;
import java.security.KeyStore;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.Executors;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;

/** Runs against the real Android Keystore in a separate disposable test package. */
public final class ArchiumPasswordKeyTest extends Instrumentation {
    private static final String ALIAS = "archium.passwords.wrap.v1";
    private Context context;
    private String phase;

    @Override
    public void onCreate(Bundle arguments) {
        super.onCreate(arguments);
        phase = arguments == null ? null : arguments.getString("phase");
        start();
    }

    @Override
    public void onStart() {
        context = getTargetContext();
        Bundle result = new Bundle();
        try {
            if ("reopen".equals(phase)) {
                String expected = context.getSharedPreferences("test", 0).getString("hash", null);
                check(expected != null && expected.equals(hash(key())), "key survives process death");
                result.putString("stream", "PASS: persisted key reopened after process restart\n");
            } else {
                runSuite();
                result.putString("stream", "PASS: 9 real Keystore cases plus verified-commit failure regression\n");
            }
            finish(-1, result);
        } catch (Throwable error) {
            result.putString("stream", "FAIL: " + error.getClass().getSimpleName()
                    + ": " + error.getMessage() + "\n");
            finish(0, result);
        }
    }

    private void runSuite() throws Exception {
        // Break caught: generating a new data key on every load loses saved credentials.
        reset();
        byte[] first = key();
        check(first.length == 32 && Arrays.equals(first, key()), "same 256-bit key on reload");
        KeyStore ks = store();
        check(ks.getKey(ALIAS, null).getEncoded() == null, "wrapping key is nonexportable");
        byte[] wrapped = Files.readAllBytes(record().toPath());
        check(!contains(wrapped, first), "record does not contain plaintext data key");

        // Break caught: accepting an altered GCM record or replacing it silently.
        byte[] corrupted = wrapped.clone();
        corrupted[corrupted.length - 1] ^= 1;
        Files.write(record().toPath(), corrupted);
        expectFailure();
        check(Arrays.equals(corrupted, Files.readAllBytes(record().toPath())),
                "tampering does not replace record");

        // Break caught: recreating a missing wrapping key while encrypted data still exists.
        reset(); key();
        wrapped = Files.readAllBytes(record().toPath());
        store().deleteEntry(ALIAS);
        expectFailure();
        check(!store().containsAlias(ALIAS), "missing key is not silently recreated");
        check(Arrays.equals(wrapped, Files.readAllBytes(record().toPath())),
                "missing key leaves wrapped record untouched");

        // Break caught: silently creating a new data key after the record disappears.
        reset(); key();
        check(record().delete(), "delete test key record");
        expectFailure();
        check(!record().exists(), "lost record is not silently replaced");

        // Break caught: treating a restore that lost both record/KEK as a new installation.
        reset(); key();
        check(record().delete(), "delete synthetic wrapped key");
        store().deleteEntry(ALIAS);
        expectFailure();
        check(!record().exists() && !store().containsAlias(ALIAS),
                "double key loss is not replaced after prior initialization");

        // Break caught: fallback to a fresh key for a truncated/version-invalid record.
        reset(); key();
        Files.write(record().toPath(), new byte[] {1, 2, 3});
        expectFailure();
        check(Files.readAllBytes(record().toPath()).length == 3, "invalid state remains recoverable");

        // Break caught: racing first loads produces two incompatible persistent keys.
        reset();
        ExecutorService pool = Executors.newFixedThreadPool(4);
        try {
            List<Callable<byte[]>> calls = new ArrayList<>();
            for (int i = 0; i < 8; i++) calls.add(() -> key());
            List<Future<byte[]>> keys = pool.invokeAll(calls);
            first = keys.get(0).get();
            for (Future<byte[]> value : keys) check(Arrays.equals(first, value.get()), "concurrent init");
        } finally { pool.shutdown(); }
        check(Arrays.equals(first, key()), "concurrent key persisted");

        // Break caught: AtomicFile.finishWrite() may suppress sync/rename failures.
        // This injects only the suppressed commit failure; actual file I/O remains Android's.
        File failedCommit = new File(context.getNoBackupFilesDir(), "commit-failure-fixture");
        Files.write(failedCommit.toPath(), new byte[] {1, 2, 3});
        AtomicFile suppressedRename = new AtomicFile(failedCommit) {
            @Override public void finishWrite(FileOutputStream output) {
                try { output.close(); }
                catch (IOException error) { throw new IllegalStateException(error); }
                // Deliberately leave the previous base file in place, like failed rename.
            }
        };
        boolean rejected = false;
        try {
            Class<?> type = Class.forName(
                    "org.chromium.chrome.browser.password_manager.ArchiumPasswordKey");
            java.lang.reflect.Method persist = type.getDeclaredMethod(
                    "writeWrappedRecord", AtomicFile.class, byte[].class);
            persist.setAccessible(true);
            persist.invoke(null, suppressedRename, new byte[] {4, 5, 6});
        } catch (NoSuchMethodException missing) {
            throw new AssertionError("Wrapped key persistence lacks a verified commit");
        } catch (InvocationTargetException expected) {
            rejected = expected.getCause() instanceof IOException;
        }
        check(rejected, "suppressed commit failure must reject the data key");
        check(Arrays.equals(new byte[] {1, 2, 3}, Files.readAllBytes(failedCommit.toPath())),
                "commit failure preserves previous record");
        for (String suffix : new String[] {"", ".new", ".bak"}) {
            File fixture = new File(failedCommit.getPath() + suffix);
            if (fixture.exists()) check(fixture.delete(), "remove commit test fixture");
        }

        // The next instrumentation run executes in a new process and checks the same key.
        check(context.getSharedPreferences("test", 0).edit().putString("hash", hash(first)).commit(),
                "store restart expectation");
    }

    private byte[] key() throws Exception {
        try {
            Class<?> type = Class.forName(
                    "org.chromium.chrome.browser.password_manager.ArchiumPasswordKey");
            return (byte[]) type.getMethod("getOrCreateDataKey", Context.class).invoke(null, context);
        } catch (InvocationTargetException exception) {
            Throwable cause = exception.getCause();
            if (cause instanceof Exception) throw (Exception) cause;
            throw exception;
        }
    }

    private void expectFailure() throws Exception {
        try { key(); }
        catch (java.security.GeneralSecurityException | java.io.IOException expected) { return; }
        throw new AssertionError("invalid key state must fail closed");
    }

    private File record() { return new File(context.getNoBackupFilesDir(), "archium-password-key-v1"); }
    private KeyStore store() throws Exception {
        KeyStore value = KeyStore.getInstance("AndroidKeyStore");
        value.load(null); return value;
    }
    private void reset() throws Exception {
        // Only deletes synthetic test data in app.archium.keytests, never Archium user data.
        for (String suffix : new String[] {"", ".bak", ".new"}) {
            File file = new File(record().getPath() + suffix);
            if (file.exists() && !file.delete()) throw new java.io.IOException("test cleanup failed");
        }
        for (String suffix : new String[] {"", ".bak", ".new"}) {
            File marker = new File(context.getFilesDir(),
                    "archium-password-key-initialized-v1" + suffix);
            if (marker.exists() && !marker.delete()) throw new java.io.IOException("test marker cleanup failed");
        }
        store().deleteEntry(ALIAS);
    }
    private static boolean contains(byte[] haystack, byte[] needle) {
        outer: for (int i = 0; i <= haystack.length - needle.length; i++) {
            for (int j = 0; j < needle.length; j++) if (haystack[i + j] != needle[j]) continue outer;
            return true;
        }
        return false;
    }
    private static String hash(byte[] value) throws Exception {
        StringBuilder result = new StringBuilder();
        for (byte b : MessageDigest.getInstance("SHA-256").digest(value)) {
            result.append(String.format("%02x", b & 255));
        }
        return result.toString();
    }
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
