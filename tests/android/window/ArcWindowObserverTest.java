package app.archium.windowtests;

import android.app.Instrumentation;
import android.content.res.Configuration;

import org.chromium.chrome.browser.lifecycle.ActivityLifecycleDispatcher;
import org.chromium.chrome.browser.lifecycle.ConfigurationChangedObserver;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearance;

/** Uses actual preferences and Android UI queue; dispatcher is a Chromium contract stub. */
public final class ArcWindowObserverTest {
    private static final class Dispatcher implements ActivityLifecycleDispatcher {
        ConfigurationChangedObserver observer;
        public void register(ConfigurationChangedObserver value) { observer = value; }
        public void unregister(ConfigurationChangedObserver value) {
            if (observer == value) observer = null;
        }
    }
    public static void run(Instrumentation instrumentation,
            ArchiumWindowMetricsTest.WindowTestActivity activity) throws Exception {
        Class<?> type = Class.forName("org.chromium.chrome.browser.arc.ArcDesktopWindowObserver");
        Dispatcher dispatcher = new Dispatcher();
        Object[] observer = {null};
        instrumentation.runOnMainSync(() -> {
            try {
                ArcDesktopAppearance.setUiMode(activity, 2);
                activity.recreations = 0;
                observer[0] = type.getConstructor(android.app.Activity.class,
                        ActivityLifecycleDispatcher.class).newInstance(activity, dispatcher);
                ArcDesktopAppearance.preferences(activity).edit().putInt("frame_color", 0xffd88474).apply();
            } catch (Exception error) { throw new RuntimeException(error); }
        });
        instrumentation.waitForIdleSync();
        check(activity.recreations == 0, "color changes do not recreate browser");
        instrumentation.runOnMainSync(() -> ArcDesktopAppearance.setUiMode(activity, 1));
        instrumentation.waitForIdleSync();
        check(activity.recreations == 1, "manual mode change requests a UI rebuild");
        instrumentation.runOnMainSync(() -> {
            try { type.getMethod("destroy").invoke(observer[0]); }
            catch (Exception error) { throw new RuntimeException(error); }
            ArcDesktopAppearance.setUiMode(activity, 2);
        });
        instrumentation.waitForIdleSync();
        check(dispatcher.observer == null, "destroy removes lifecycle observer");
        check(activity.recreations == 1, "destroy removes preference observer");
        instrumentation.runOnMainSync(() -> {
            try {
                observer[0] = type.getConstructor(android.app.Activity.class,
                        ActivityLifecycleDispatcher.class).newInstance(activity, dispatcher);
                ArcDesktopAppearance.setUiMode(activity, 1);
                ArcDesktopAppearance.setUiMode(activity, 2);
            } catch (Exception error) { throw new RuntimeException(error); }
        });
        instrumentation.waitForIdleSync();
        check(activity.recreations == 1, "reverted choice cancels queued recreation");
        instrumentation.runOnMainSync(() -> {
            try {
                ArcDesktopAppearance.setUiMode(activity, 1);
                type.getMethod("destroy").invoke(observer[0]);
            } catch (Exception error) { throw new RuntimeException(error); }
        });
        instrumentation.waitForIdleSync();
        check(activity.recreations == 1, "destroy cancels queued recreation");
    }
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
}
