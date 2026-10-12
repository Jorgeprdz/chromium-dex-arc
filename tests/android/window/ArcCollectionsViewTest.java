package app.archium.windowtests;

import android.app.Activity;
import android.app.Instrumentation;
import android.view.View;
import android.widget.ImageButton;
import java.util.HashSet;
import java.util.Set;
import org.chromium.chrome.browser.arc.ArcCollectionsController;
import org.chromium.chrome.browser.arc.ArcCollectionsView;
import org.chromium.chrome.browser.arc.ArcSidebarStore;
import org.chromium.chrome.browser.arc.ArcTabActions;

/** Actual Android views and production state; Chromium commands remain a simulated boundary. */
public final class ArcCollectionsViewTest {
    private static final class Native implements ArcTabActions.NativeTabs {
        final Set<Integer> ids = new HashSet<>();
        int selected = -1, opens, pinCalls;
        public boolean exists(int id) { return ids.contains(id); }
        public int open(String url) { opens++; ids.add(100 + opens); return 100 + opens; }
        public void select(int id) { selected = id; }
        public void pin(int id) { pinCalls++; }
        public void unpin(int id) {}
        public void close(int id) {}
    }
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    public static void run(Instrumentation instrumentation, Activity activity) {
        Throwable[] failure = new Throwable[1];
        instrumentation.runOnMainSync(() -> {
            try {
                Native nativeTabs = new Native(); nativeTabs.ids.add(7); nativeTabs.ids.add(8);
                ArcSidebarStore store = new ArcSidebarStore(null);
                ArcCollectionsController controller = new ArcCollectionsController(
                        store, new ArcTabActions(store, nativeTabs), nativeTabs);
                String personal = controller.state().selectedSpace();
                ArcCollectionsView view = new ArcCollectionsView(activity, controller,
                        () -> new ArcCollectionsView.CurrentTab(7, "https://example.test/", "Example"),
                        (entry, button) -> {});
                activity.setContentView(view);
                // REAL_ANDROID_VIEW: measure production controls, without claiming native Chromium
                // observer coverage at the simulated command boundary.
                view.setCollectionHeight(240);
                view.measure(View.MeasureSpec.makeMeasureSpec(320, View.MeasureSpec.EXACTLY),
                        View.MeasureSpec.makeMeasureSpec(1200, View.MeasureSpec.AT_MOST));
                View newFolder = view.findViewWithTag("arc-new-folder:" + personal);
                View collectionScroll = view.findViewWithTag("arc-collection-scroll");
                check(collectionScroll.getMeasuredHeight() == newFolder.getMeasuredHeight(),
                        "empty collection reserves only its real row height");
                check(collectionScroll.getLayoutParams().height == android.view.ViewGroup.LayoutParams.WRAP_CONTENT,
                        "collection budget caps content instead of reserving blank space");
                View pin = view.findViewWithTag("arc-pin-current");
                check(pin != null && pin.performClick(), "real pin button clickable");
                String id = controller.state().entries(personal).get(0).id;
                View pinnedRow = view.findViewWithTag("arc-entry:" + id);
                check(pinnedRow != null && pinnedRow.performClick(), "saved pin rendered and clickable");
                check(nativeTabs.selected == 7 && nativeTabs.opens == 0, "click selects existing native tab");
                View favorite = view.findViewWithTag("arc-favorite-current");
                check(favorite.performClick(), "real favorite button clickable");
                check(controller.state().favorites().get(0).id.equals(id), "conversion preserves identity");
                check(view.findViewWithTag("arc-entry:" + id) instanceof ImageButton,
                        "favorite rendered as an actual icon control");
                ImageButton tile = view.findViewWithTag("arc-entry:" + id);
                view.setAppearance(0xffe0e0e0, 0xff222222, 0xff777777);
                check(tile.getLayoutParams().width == tile.getLayoutParams().height
                                && tile.getBackground() instanceof android.graphics.drawable.RippleDrawable,
                        "Favorite uses a square tile with its own rounded interactive background");
                check(tile.getColorFilter() == null, "Favorite preserves site favicon colors");
                String work = controller.createSpace("Work");
                String workPin = controller.rememberTab(8, "https://work.test/", "Work tab", false);
                view.refresh();
                check(view.findViewWithTag("arc-entry:" + workPin) != null, "work collection visible");
                check(view.findViewWithTag("arc-entry:" + id) != null, "shared favorite visible in Work");
                controller.selectSpace(personal); view.refresh();
                check(view.findViewWithTag("arc-entry:" + workPin) == null, "other Space's pin hidden");
                check(view.findViewWithTag("arc-entry:" + id) != null, "shared favorite survives Space switch");
                controller.selectSpace(work); view.refresh();
                int before = nativeTabs.pinCalls;
                view.destroy(); pin.performClick(); favorite.performClick();
                check(nativeTabs.pinCalls == before, "destroyed view stops commands");
                controller.destroy();
                String[] damaged = {"future-or-damaged-state"};
                ArcSidebarStore corruptStore = new ArcSidebarStore(new ArcSidebarStore.Persistence() {
                    public String read() { return damaged[0]; }
                    public void write(String value) { damaged[0] = value; }
                });
                ArcCollectionsController corruptController = new ArcCollectionsController(
                        corruptStore, new ArcTabActions(corruptStore, nativeTabs), nativeTabs);
                ArcCollectionsView damagedView = new ArcCollectionsView(activity, corruptController,
                        () -> new ArcCollectionsView.CurrentTab(7, "https://example.test/", "Example"),
                        (entry, button) -> {});
                activity.setContentView(damagedView);
                check(((android.widget.TextView) damagedView.findViewWithTag("arc-current-space"))
                        .getText().toString().equals(activity.getString(org.chromium.chrome.R.string.arc_collection_error)),
                        "damaged state displays an explicit read error instead of empty fabricated collections");
                damagedView.findViewWithTag("arc-pin-current").performClick();
                check(damaged[0].equals("future-or-damaged-state"), "damaged metadata never overwritten");
                check(nativeTabs.pinCalls == before, "damaged metadata leaves native tabs untouched");
                damagedView.destroy(); corruptController.destroy();
            } catch (Throwable error) { failure[0] = error; }
        });
        if (failure[0] != null) throw new AssertionError(failure[0]);
    }
}
