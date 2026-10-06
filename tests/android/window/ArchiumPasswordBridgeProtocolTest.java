package app.archium.windowtests;

import android.app.Activity;
import java.lang.reflect.Method;
import java.util.List;
import org.chromium.chrome.browser.password_manager.ArchiumPasswordCsv;
import org.chromium.chrome.browser.password_manager.ArchiumPasswordManagerBridge;
import org.chromium.chrome.browser.password_manager.ArchiumPasswordManagerBridgeJni;
import org.chromium.chrome.browser.profiles.Profile;

/** Real Java transport/buffer lifecycle, simulated JNI boundary only. */
public final class ArchiumPasswordBridgeProtocolTest {
    private static void call(Object peer, String name, Class<?>[] types, Object... values) throws Exception {
        Method method = peer.getClass().getDeclaredMethod(name, types);
        method.setAccessible(true); method.invoke(peer, values);
    }
    private static void check(boolean value, String reason) {
        if (!value) throw new AssertionError(reason);
    }
    public static void run(Activity activity) throws Exception {
        ArchiumPasswordManagerBridgeJni.reset();
        int[] secrets = {0};
        int[] metadata = {0};
        List<?>[] exports = {null};
        ArchiumPasswordManagerBridge peer = new ArchiumPasswordManagerBridge(activity, new Profile(),
                new ArchiumPasswordManagerBridge.Listener() {
                    public void onMetadata(List<ArchiumPasswordManagerBridge.Entry> rows, int status) {
                        metadata[0]++;
                        check(rows.size() == 1 && rows.get(0).id == 17, "opaque metadata delivered");
                    }
                    public void onSecret(int request, int status, char[] password) {
                        check(new String(password).equals("synthetic"), "borrowed secret readable during callback");
                        secrets[0]++;
                    }
                    public void onExport(int request, int status, List<ArchiumPasswordCsv.SecretRow> rows) {
                        exports[0] = rows;
                    }
                    public void onPreview(int request, int status, List<ArchiumPasswordManagerBridge.ImportRow> rows) {}
                    public void onOperation(int request, int status) {}
                });
        peer.start();
        call(peer, "onListStart", new Class<?>[] {});
        call(peer, "onEntry", new Class<?>[] {long.class, String.class, String.class}, 17L, "https://test.example/", "user");
        call(peer, "onListEnd", new Class<?>[] {int.class}, 0);
        check(metadata[0] == 1, "metadata callback delivered once");
        char[] password = "synthetic".toCharArray();
        call(peer, "onSecret", new Class<?>[] {int.class, int.class, char[].class}, 1, 0, password);
        for (char c : password) check(c == 0, "borrowed JNI secret not erased");
        call(peer, "onExportStart", new Class<?>[] {int.class}, 2);
        char[] exportPassword = "synthetic export".toCharArray();
        call(peer, "onExportRow", new Class<?>[] {int.class, String.class, String.class, char[].class},
                2, "https://test.example/", "user", exportPassword);
        for (char c : exportPassword) check(c == 0, "JNI export source not erased");
        call(peer, "onExportEnd", new Class<?>[] {int.class, int.class}, 2, 0);
        check(exports[0] != null && exports[0].size() == 1, "owned export transferred");
        java.io.StringWriter writer = new java.io.StringWriter();
        ArchiumPasswordCsv.SecretRow exportRow = (ArchiumPasswordCsv.SecretRow) exports[0].get(0);
        ArchiumPasswordCsv.writeSecrets(writer, List.of(exportRow));
        check(writer.toString().contains("synthetic export"), "transport preserves export buffer until consumer closes");
        exportRow.close();
        char[][] input = {"synthetic import".toCharArray()};
        peer.previewImport(3, new String[] {"https://test.example/"}, new String[] {"user"}, input);
        for (char c : input[0]) check(c == 0, "JNI input source not erased");

        char[] added = "synthetic add".toCharArray();
        peer.add(30, "https://add.example/", "added-user", added);
        for (char c : added) check(c == 0, "CRUD add input not erased");
        char[] updated = "synthetic update".toCharArray();
        peer.update(31, 17, "updated-user", updated);
        for (char c : updated) check(c == 0, "CRUD update input not erased");
        peer.delete(32, 17);

        peer.destroy(); peer.destroy();
        int commands = ArchiumPasswordManagerBridgeJni.commands;
        peer.refresh(); peer.reveal(4, 17); peer.export(5);
        check(ArchiumPasswordManagerBridgeJni.commands == commands, "destroyed peer sends no commands");
        check(ArchiumPasswordManagerBridgeJni.destroyed == 1, "native peer destroyed exactly once");
        char[] late = "late synthetic".toCharArray();
        call(peer, "onSecret", new Class<?>[] {int.class, int.class, char[].class}, 6, 0, late);
        check(secrets[0] == 1, "destroyed peer drops late secret callback");
        for (char c : late) check(c == 0, "late JNI secret erased");
    }
}
