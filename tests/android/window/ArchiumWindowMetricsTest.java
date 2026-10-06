package app.archium.windowtests;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Context;
import android.content.Intent;
import android.content.res.Configuration;
import android.os.Bundle;
import android.widget.TextView;

import java.lang.reflect.Method;

/** Exercises production metrics on Android and rejects application-context display guessing. */
public final class ArchiumWindowMetricsTest extends Instrumentation {
    public static final class WindowTestActivity extends Activity {
        public int recreations;
        @Override public void recreate() { recreations++; }
        @Override public void onCreate(Bundle state) {
            super.onCreate(state);
            TextView view = new TextView(this);
            view.setText("Archium: prueba temporal de ventana");
            setContentView(view);
        }
    }
    private String mPhase;

    @Override public void onCreate(Bundle args) {
        super.onCreate(args);
        mPhase = args == null ? "suite" : args.getString("phase", "suite");
        start();
    }

    private void appearancePreferences() throws Exception {
        Context context = getTargetContext().getApplicationContext();
        Class<?> type = Class.forName(
                "org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearance");
        Method getMode;
        Method setMode;
        try {
            getMode = type.getMethod("getUiMode", Context.class);
            setMode = type.getMethod("setUiMode", Context.class, int.class);
        } catch (NoSuchMethodException missing) {
            throw new AssertionError("Persistent Arc UI mode is missing");
        }
        android.content.SharedPreferences preferences =
                (android.content.SharedPreferences) type.getMethod("preferences", Context.class)
                        .invoke(null, context);
        if ("reopen".equals(mPhase)) {
            check((Integer) getMode.invoke(null, context) == 1, "Arc UI mode survives process restart");
            check(preferences.getInt("frame_color", 0) == 0xffd88474,
                    "frame preference survives process restart");
            return;
        }
        preferences.edit().clear().putInt("frame_color", 0xffd88474).commit();
        check((Integer) getMode.invoke(null, context) == 0, "missing mode defaults to AUTO");
        setMode.invoke(null, context, 1);
        check((Integer) getMode.invoke(null, context) == 1, "explicit ARC stored independently");
        check((Boolean) type.getMethod("isDesktopWindow", Context.class).invoke(null, context),
                "explicit Arc appearance does not guess a display");
        setMode.invoke(null, context, 2);
        check(!(Boolean) type.getMethod("isDesktopWindow", Context.class).invoke(null, context),
                "MOBILE disables Arc appearance");
        preferences.edit().putInt("ui_mode", 99).commit();
        check((Integer) getMode.invoke(null, context) == 0, "unknown stored mode falls back to AUTO");
        check(preferences.getInt("frame_color", 0) == 0xffd88474, "mode keeps frame preference");
        setMode.invoke(null, context, 1);
        check(preferences.edit().putInt("frame_color", 0xffd88474).commit(),
                "flush synthetic preferences before process restart");
    }
    @Override public void onStart() {
        Activity activity = null;
        Bundle result = new Bundle();
        try {
            appearancePreferences();
            if ("reopen".equals(mPhase)) {
                result.putString("stream", "PASS: persisted appearance mode reopened after restart\n");
                finish(-1, result);
                return;
            }
            Class<?> metrics = Class.forName("org.chromium.chrome.browser.desktop_policy.ArchiumWindowMetrics");
            Class<?> policy = Class.forName("org.chromium.chrome.browser.desktop_policy.ArchiumWindowClass");
            Method currentWidth = metrics.getMethod("currentWidthDp", Context.class);
            Method configurationWidth = metrics.getMethod("configurationWidthDp", Configuration.class);
            Method classify = policy.getMethod("classify", int.class);
            int[] widths = {520, 580, 600, 620, 840, 900, 520, 700};
            for (int width : widths) {
                Configuration config = new Configuration(getTargetContext().getResources().getConfiguration());
                config.screenWidthDp = width;
                config.orientation = Configuration.ORIENTATION_LANDSCAPE;
                int actual = (Integer) configurationWidth.invoke(null, config);
                check(actual == width, "uses effective width rather than smallest width/orientation");
                String expected = width < 600 ? "COMPACT" : width < 840 ? "TABLET" : "DESKTOP";
                check(expected.equals(classify.invoke(null, actual).toString()), "window class");
                config.orientation = Configuration.ORIENTATION_PORTRAIT;
                check((Integer) configurationWidth.invoke(null, config) == width,
                        "rotation without width change preserves class");
            }
            if (android.os.Build.VERSION.SDK_INT >= 31) {
                check((Integer) currentWidth.invoke(null, getTargetContext().getApplicationContext()) == 0,
                        "application context cannot guess a window from primary display");
            }
            Intent intent = new Intent(getTargetContext(), WindowTestActivity.class);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            activity = startActivitySync(intent);
            waitForIdleSync();
            Activity window = activity;
            int[] width = new int[1];
            runOnMainSync(() -> {
                try { width[0] = (Integer) currentWidth.invoke(null, window); }
                catch (Exception error) { throw new RuntimeException(error); }
            });
            check(width[0] > 0, "actual Activity has measured window width");
            appearanceSelector(activity);
            ArcWindowObserverTest.run(this, (WindowTestActivity) activity);
            ArcCollectionsViewTest.run(this, activity);
            Throwable[] protocolFailure = new Throwable[1];
            runOnMainSync(() -> {
                try { ArchiumPasswordBridgeProtocolTest.run(window); }
                catch (Throwable failure) { protocolFailure[0] = failure; }
            });
            if (protocolFailure[0] != null) throw new AssertionError(protocolFailure[0]);
            int displayIndependentWidth = activity.getResources().getConfiguration().screenWidthDp;
            check(width[0] <= displayIndependentWidth + 2,
                    "usable Activity width does not include wider physical display");
            result.putString("stream", "PASS: Android window/configuration metrics, appearance/observer and collection views and password transport buffers; Chromium/JNI boundaries simulated\n");
            finish(-1, result);
        } catch (Throwable error) {
            result.putString("stream", "FAIL: " + error.getClass().getSimpleName() + ": " + error.getMessage() + "\n");
            finish(0, result);
        } finally {
            if (activity != null) {
                Activity window = activity;
                runOnMainSync(window::finish);
            }
        }
    }
    private void appearanceSelector(Activity activity) throws Exception {
        Class<?> selector;
        try {
            selector = Class.forName("org.chromium.chrome.browser.arc.ArcAppearanceDialog");
        } catch (ClassNotFoundException missing) {
            throw new AssertionError("Visible Arc appearance selector is missing");
        }
        Class<?> appearance = Class.forName(
                "org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearance");
        Method mode = appearance.getMethod("getUiMode", Context.class);
        Method setMode = appearance.getMethod("setUiMode", Context.class, int.class);
        Method create = selector.getMethod("create", Context.class, Runnable.class);
        int[] notifications = {0};
        android.app.AlertDialog[] dialog = {null};
        Throwable[] failure = {null};
        runOnMainSync(() -> {
            try {
                setMode.invoke(null, activity, 0);
                dialog[0] = (android.app.AlertDialog) create.invoke(null, activity,
                        (Runnable) () -> notifications[0]++);
                dialog[0].show();
                check(dialog[0].getListView().getCheckedItemPosition() == 0, "AUTO selected");
                dialog[0].cancel();
                check((Integer) mode.invoke(null, activity) == 0, "cancel keeps appearance");
                check(notifications[0] == 0, "cancel does not notify browser");
                for (int choice : new int[] {1, 2, 0}) {
                    dialog[0] = (android.app.AlertDialog) create.invoke(null, activity,
                            (Runnable) () -> notifications[0]++);
                    dialog[0].show();
                    android.widget.ListView list = dialog[0].getListView();
                    list.performItemClick(list.getChildAt(choice), choice,
                            list.getAdapter().getItemId(choice));
                    check((Integer) mode.invoke(null, activity) == choice, "choice persisted");
                    check(!dialog[0].isShowing(), "selection dismisses dialog");
                }
                check(notifications[0] == 3, "one callback per accepted selection");
                setMode.invoke(null, activity, 1);
            } catch (Throwable error) { failure[0] = error; }
            finally { if (dialog[0] != null) dialog[0].dismiss(); }
        });
        if (failure[0] != null) throw new AssertionError(failure[0]);
    }
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
