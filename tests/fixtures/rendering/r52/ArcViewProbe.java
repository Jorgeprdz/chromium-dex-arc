package org.archium.forensics;

import android.app.Activity;
import android.graphics.Rect;
import android.os.Looper;
import android.os.SystemClock;
import android.view.SurfaceHolder;
import java.util.ArrayList;
import java.util.List;
import android.view.SurfaceView;
import android.view.View;
import android.view.ViewGroup;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/** Optional instrumentation helper. Never reads text, hints, tags, URLs or form values.
 * Not linked into the Archium APK; invoke only from an explicitly prepared test harness.
 */
public final class ArcViewProbe {
    private ArcViewProbe() {}
    public static JSONObject capture(Activity activity, View root, int limit)
            throws JSONException {
        if (Looper.myLooper() != Looper.getMainLooper()) {
            throw new IllegalStateException("Capture on the UI thread");
        }
        if (limit < 1 || limit > 256) throw new IllegalArgumentException("Node limit");
        JSONObject result = new JSONObject();
        JSONArray nodes = new JSONArray();
        visit(root, -1, 0, nodes, limit);
        result.put("nodes", nodes);
        result.put("node_limit_reached", nodes.length() == limit);
        result.put("window_focus", activity.hasWindowFocus());
        result.put("window_type", activity.getWindow().getAttributes().type);
        result.put("window_alpha", activity.getWindow().getAttributes().alpha);
        result.put("window_flags", activity.getWindow().getAttributes().flags);
        result.put("window_token_identity", identity(root.getWindowToken()));
        result.put("surface_control_order", "NOT_OBSERVED");
        result.put("browser_controls_gate", "REQUIRES_CHROMIUM_PROVIDER_ADAPTER");
        return result;
    }
    /** Explicit owner must close; callbacks observe lifecycle and never recreate surfaces. */
    public static final class Session implements SurfaceHolder.Callback, AutoCloseable {
        private final List<SurfaceHolder> holders = new ArrayList<>();
        private final JSONArray events = new JSONArray();
        private int created, changed, destroyed;
        public JSONObject snapshot(Activity activity, View root, int limit) throws JSONException {
            watch(root, new int[]{0});
            JSONObject result = capture(activity, root, limit);
            result.put("surface_created_callbacks", created);
            result.put("surface_changed_callbacks", changed);
            result.put("surface_destroyed_callbacks", destroyed);
            result.put("surface_events", new JSONArray(events.toString()));
            return result;
        }
        private void watch(View view, int[] visited) {
            if (++visited[0] > 256) return;
            if (view instanceof SurfaceView) {
                SurfaceHolder holder = ((SurfaceView) view).getHolder();
                if (!holders.contains(holder)) { holders.add(holder); holder.addCallback(this); }
            }
            if (view instanceof ViewGroup) {
                ViewGroup group = (ViewGroup) view;
                for (int i=0;i<group.getChildCount() && visited[0]<256;i++) watch(group.getChildAt(i), visited);
            }
        }
        private void event(String phase, SurfaceHolder holder) {
            if (events.length() >= 64) return;
            try {
                JSONObject row = new JSONObject();
                row.put("phase", phase); row.put("monotonic_ns", SystemClock.elapsedRealtimeNanos());
                row.put("holder_identity", identity(holder));
                row.put("surface_identity", identity(holder.getSurface()));
                row.put("valid", holder.getSurface() != null && holder.getSurface().isValid()); events.put(row);
            } catch (JSONException error) { throw new IllegalStateException(error); }
        }
        @Override public void surfaceCreated(SurfaceHolder holder) { created++; event("created", holder); }
        @Override public void surfaceChanged(SurfaceHolder holder, int format, int w, int h) {
            changed++; event("changed", holder);
        }
        @Override public void surfaceDestroyed(SurfaceHolder holder) { destroyed++; event("destroyed", holder); }
        @Override public void close() {
            for (SurfaceHolder holder: holders) holder.removeCallback(this);
            holders.clear();
        }
    }
    private static String identity(Object value) {
        return value == null ? "UNATTACHED" : Integer.toHexString(System.identityHashCode(value));
    }
    private static void visit(View view, int parent, int childIndex, JSONArray nodes, int limit)
            throws JSONException {
        if (nodes.length() >= limit) return;
        int index = nodes.length();
        int[] location = new int[2];
        view.getLocationInWindow(location);
        Rect visible = new Rect();
        boolean globallyVisible = view.getGlobalVisibleRect(visible);
        JSONObject row = new JSONObject();
        row.put("node", index); row.put("parent", parent); row.put("child_index", childIndex);
        row.put("kind", view.getClass().getName()); row.put("identity", identity(view));
        row.put("resource_id", view.getId()); row.put("visibility", view.getVisibility());
        row.put("width", view.getWidth()); row.put("height", view.getHeight());
        row.put("x_in_window", location[0]); row.put("y_in_window", location[1]);
        row.put("global_visible", globallyVisible);
        row.put("visible_bounds", new JSONArray(new int[]{visible.left,visible.top,visible.right,visible.bottom}));
        row.put("elevation", view.getElevation()); row.put("z", view.getZ());
        row.put("alpha", view.getAlpha()); row.put("translation_x", view.getTranslationX());
        row.put("translation_y", view.getTranslationY()); row.put("scale_x", view.getScaleX());
        row.put("scale_y", view.getScaleY()); row.put("focused", view.hasFocus());
        row.put("attached", view.isAttachedToWindow());
        row.put("token_identity", identity(view.getWindowToken()));
        Rect clip = view.getClipBounds();
        row.put("clip_bounds", clip == null ? JSONObject.NULL
                : new JSONArray(new int[]{clip.left,clip.top,clip.right,clip.bottom}));
        if (view instanceof SurfaceView) {
            SurfaceView surface = (SurfaceView) view;
            row.put("surface_identity", identity(surface.getHolder().getSurface()));
            row.put("surface_valid", surface.getHolder().getSurface() != null && surface.getHolder().getSurface().isValid());
            Rect frame = surface.getHolder().getSurfaceFrame();
            row.put("surface_width", frame == null ? 0 : frame.width());
            row.put("surface_height", frame == null ? 0 : frame.height());
        }
        nodes.put(row);
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i=0;i<group.getChildCount() && nodes.length()<limit;i++) {
                visit(group.getChildAt(i),index,i,nodes,limit);
            }
        }
    }
}
