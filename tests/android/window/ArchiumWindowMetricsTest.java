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
        @Override public void onCreate(Bundle state) {
            super.onCreate(state);
            TextView view = new TextView(this);
            view.setText("Archium: prueba temporal de ventana");
            setContentView(view);
        }
    }
    @Override public void onCreate(Bundle args) { super.onCreate(args); start(); }
    @Override public void onStart() {
        Activity activity = null;
        Bundle result = new Bundle();
        try {
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
            int displayIndependentWidth = activity.getResources().getConfiguration().screenWidthDp;
            check(width[0] <= displayIndependentWidth + 2,
                    "usable Activity width does not include wider physical display");
            result.putString("stream", "PASS: Android window/configuration metrics and application-context rejection\n");
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
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
