package org.chromium.chrome.browser.password_manager;

import android.app.Activity;
import org.chromium.chrome.browser.profiles.Profile;

/** JNI replacement in the disposable protocol test APK only. */
public final class ArchiumPasswordManagerBridgeJni {
    public static int commands, destroyed;
    public static void reset() { commands = 0; destroyed = 0; }
    private static final ArchiumPasswordManagerBridge.Natives INSTANCE = new ArchiumPasswordManagerBridge.Natives() {
        public boolean isLocalEnabled() { return true; }
        public long init(ArchiumPasswordManagerBridge peer, Profile profile, Activity activity) { return 1; }
        public void refresh(long ptr) { commands++; }
        public void add(long ptr, int request, String url, String username, char[] password) { commands++; }
        public void update(long ptr, int request, long id, String username, char[] password) { commands++; }
        public void delete(long ptr, int request, long id) { commands++; }
        public void reveal(long ptr, int request, long id) { commands++; }
        public void export(long ptr, int request) { commands++; }
        public void previewImport(long ptr, int request, String[] urls, String[] users, char[][] passwords) { commands++; }
        public void confirmImport(long ptr, int request, int[] decisions) { commands++; }
        public void cancelImport(long ptr) { commands++; }
        public void destroy(long ptr) { commands++; destroyed++; }
    };
    public static ArchiumPasswordManagerBridge.Natives get() { return INSTANCE; }
}
