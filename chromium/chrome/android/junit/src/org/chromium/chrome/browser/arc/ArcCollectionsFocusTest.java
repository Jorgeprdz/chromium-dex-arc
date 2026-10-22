// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import static org.junit.Assert.*;
import static org.mockito.Mockito.*;
import static org.robolectric.Shadows.shadowOf;

import android.app.Activity;
import android.os.Looper;
import android.view.View;

import org.junit.Test;
import org.junit.After;
import org.robolectric.android.controller.ActivityController;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;

/** Bookmark/favicon refresh may rebuild controls without losing keyboard focus. */
@RunWith(RobolectricTestRunner.class)
@Config(manifest = Config.NONE, sdk = {30, 36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcCollectionsFocusTest {
    private final java.util.List<ActivityController<Activity>> mActivities = new java.util.ArrayList<>();
    private final java.util.List<ArcCollectionsView> mViews = new java.util.ArrayList<>();
    private final java.util.List<ArcCollectionsController> mControllers = new java.util.ArrayList<>();

    private Activity createActivity() {
        ActivityController<Activity> activity = Robolectric.buildActivity(Activity.class).setup();
        mActivities.add(activity);
        return activity.get();
    }

    @After
    public void tearDown() {
        for (ArcCollectionsView view : mViews) view.destroy();
        for (ArcCollectionsController controller : mControllers) controller.destroy();
        for (ActivityController<Activity> activity : mActivities) activity.pause().stop().destroy();
        shadowOf(Looper.getMainLooper()).idle();
    }

    @Test
    public void focusedEntrySurvivesRefreshByIdentity() {
        checkFocus(false);
    }

    @Test
    public void focusedFavoriteSurvivesRefreshByIdentity() {
        checkFocus(true);
    }

    @Test
    public void rightClickCanRemovePinWithoutClosingAndRemovalPersists() {
        Fixture f=new Fixture();
        String id=f.controller.rememberTab(7,"https://example.test","Pinned",false);
        String other=f.controller.rememberTab(8,"https://other.test","Favorite",true);
        f.view.refresh();View row=f.view.findViewWithTag("arc-entry:"+id);
        assertTrue(row.performContextClick());
        android.widget.PopupMenu menu=org.robolectric.shadows.ShadowPopupMenu.getLatestPopupMenu();
        assertTrue(menu.getMenu().performIdentifierAction(0,0));
        verify(f.tabs).unpin(7);verify(f.tabs,never()).close(anyInt());
        ArcSidebarState restored=ArcSidebarState.deserialize(f.controller.state().serialize());
        assertTrue(restored.entries(restored.selectedSpace()).isEmpty());
        assertEquals(other,restored.favorites().get(0).id);
        f.view.refresh();assertNull(f.view.findViewWithTag("arc-entry:"+id));
    }

    @Test
    public void longPressCloseUsesNativeTabAndPreservesSavedEntryUntilConfirmation() {
        Fixture f=new Fixture();String id=f.controller.rememberTab(7,"https://example.test","Pinned",false);
        f.view.refresh();View row=f.view.findViewWithTag("arc-entry:"+id);
        assertTrue(row.performLongClick());
        android.widget.PopupMenu menu=org.robolectric.shadows.ShadowPopupMenu.getLatestPopupMenu();
        assertNotNull(menu.getMenu().findItem(2));
        assertTrue(menu.getMenu().performIdentifierAction(2,0));
        verify(f.tabs).close(7);verify(f.tabs,never()).unpin(anyInt());
        assertEquals(Integer.valueOf(7),f.controller.state().entry(id).tabId);
        assertEquals("https://example.test",f.controller.state().entry(id).url);
    }

    @Test
    public void stalePinnedRowCannotCrashAfterItsMetadataWasRemoved() {
        Fixture f=new Fixture();String id=f.controller.rememberTab(7,"https://example.test","Pinned",false);
        f.view.refresh();View row=f.view.findViewWithTag("arc-entry:"+id);
        f.controller.remove(id); // Native notification can precede the next view refresh.
        assertTrue(row.performContextClick());verify(f.tabs,never()).close(anyInt());
    }

    @Test
    public void pointerHoverDoesNotHideKeyboardFocus() {
        Fixture f=new Fixture();f.view.setAppearance(0xffeeeeee,0xff111111,0xff777777);
        View space=f.view.findViewWithTag("arc-current-space");
        var ripple=(android.graphics.drawable.RippleDrawable)space.getBackground();
        var states=(android.graphics.drawable.StateListDrawable)ripple.getDrawable(0);
        states.setState(new int[]{android.R.attr.state_enabled,android.R.attr.state_focused});
        var focus=states.getCurrent();
        states.setState(new int[]{android.R.attr.state_enabled,android.R.attr.state_focused,android.R.attr.state_hovered});
        assertSame(focus,states.getCurrent());
    }

    private final class Fixture {
        final Activity activity = createActivity();
        final ArcTabActions.NativeTabs tabs = mock(ArcTabActions.NativeTabs.class);
        final ArcSidebarStore store = new ArcSidebarStore(null);
        final ArcCollectionsController controller = new ArcCollectionsController(store, new ArcTabActions(store, tabs), tabs);
        final ArcCollectionsView view;
        Fixture() {
            when(tabs.exists(anyInt())).thenReturn(true);
            view = new ArcCollectionsView(activity, controller,
                    () -> new ArcCollectionsView.CurrentTab(7, "https://example.test", "Saved"),
                    (entry, button) -> {});
            activity.setContentView(view);
            mViews.add(view);
            mControllers.add(controller);
            shadowOf(Looper.getMainLooper()).idle();
        }
        void measure() {
            view.measure(View.MeasureSpec.makeMeasureSpec(320, View.MeasureSpec.EXACTLY),
                    View.MeasureSpec.makeMeasureSpec(1200, View.MeasureSpec.AT_MOST));
            view.layout(0, 0, view.getMeasuredWidth(), view.getMeasuredHeight());
        }
    }

    @Test
    public void emptyCollectionWrapsContentInsideBudget() {
        Fixture f = new Fixture();
        f.view.setCollectionHeight(240);
        f.measure();
        View newFolder = f.view.findViewWithTag("arc-new-folder:" + f.controller.state().selectedSpace());
        View scroll = (View) newFolder.getParent().getParent();
        assertEquals("Empty collection has only its actual New folder row", newFolder.getMeasuredHeight(), scroll.getMeasuredHeight());
        assertEquals(android.view.ViewGroup.LayoutParams.WRAP_CONTENT, scroll.getLayoutParams().height);
    }

    @Test
    public void collectionCapsOverflowAndRespondsToSmallerBudget() {
        Fixture f = new Fixture();
        for (int i = 0; i < 20; i++) f.controller.createFolder(null, "Folder " + i);
        f.view.refresh(); f.view.setCollectionHeight(240); f.measure();
        View scroll = (View) f.view.findViewWithTag("arc-new-folder:" + f.controller.state().selectedSpace()).getParent().getParent();
        assertEquals(240, scroll.getMeasuredHeight());
        f.view.setCollectionHeight(100); f.measure();
        assertEquals(100, scroll.getMeasuredHeight());
    }

    @Test
    public void stableCollectionBudgetDoesNotRequestAnotherBrowserLayout() {
        Fixture f = new Fixture(); f.view.setCollectionHeight(240); f.measure();
        View scroll = f.view.findViewWithTag("arc-collection-scroll");
        assertFalse(scroll.isLayoutRequested());
        f.view.setCollectionHeight(240);
        assertFalse(scroll.isLayoutRequested());
        f.view.setCollectionHeight(100);
        assertTrue(scroll.isLayoutRequested());
    }

    @Test
    public void favoriteIsSquareRoundedTileAndKeepsFaviconColors() throws Exception {
        Fixture f = new Fixture();
        String id = f.controller.rememberTab(7, "https://example.test", "Saved", true);
        f.view.refresh();
        android.widget.ImageButton tile = f.view.findViewWithTag("arc-entry:" + id);
        android.graphics.drawable.ColorDrawable favicon = new android.graphics.drawable.ColorDrawable(0xffe04020);
        tile.setImageDrawable(favicon);
        ArcCollectionsView.class.getMethod("setAppearance", int.class, int.class, int.class)
                .invoke(f.view, 0xffe0e0e0, 0xff222222, 0xff777777);
        f.measure();
        assertEquals(tile.getMeasuredWidth(), tile.getMeasuredHeight());
        assertTrue(tile.getBackground() instanceof android.graphics.drawable.RippleDrawable);
        android.graphics.drawable.RippleDrawable background = (android.graphics.drawable.RippleDrawable) tile.getBackground();
        assertTrue(background.getDrawable(0) instanceof android.graphics.drawable.GradientDrawable);
        assertTrue(((android.graphics.drawable.GradientDrawable) background.getDrawable(0)).getCornerRadius() > 0);
        assertSame(favicon, tile.getDrawable());
        assertNull(tile.getColorFilter());
    }

    @Test
    public void folderContextMenuConfirmsAndDissolvesWithoutRemovingPinnedTab() {
        Fixture f = new Fixture();
        String folder = f.controller.createFolder(null, "Read");
        String id = f.controller.rememberTab(7, "https://example.test", "Saved", false);
        f.controller.move(id, f.controller.state().selectedSpace(), folder, 0);
        f.view.refresh();
        View row = f.view.findViewWithTag("arc-folder:" + folder);
        assertTrue(row.performLongClick());
        android.widget.PopupMenu menu = org.robolectric.shadows.ShadowPopupMenu.getLatestPopupMenu();
        assertNotNull(menu);
        menu.getMenu().performIdentifierAction(0, 0);
        android.app.AlertDialog dialog = org.robolectric.shadows.ShadowAlertDialog.getLatestAlertDialog();
        assertNotNull(dialog);
        dialog.getButton(android.app.AlertDialog.BUTTON_NEGATIVE).performClick();
        shadowOf(Looper.getMainLooper()).idle();
        assertEquals(folder, f.controller.state().entry(id).folderId);
        assertTrue(row.performContextClick());
        org.robolectric.shadows.ShadowPopupMenu.getLatestPopupMenu().getMenu().performIdentifierAction(0, 0);
        dialog = org.robolectric.shadows.ShadowAlertDialog.getLatestAlertDialog();
        dialog.getButton(android.app.AlertDialog.BUTTON_POSITIVE).performClick();
        shadowOf(Looper.getMainLooper()).idle();
        assertNull(f.controller.state().entry(id).folderId);
        assertEquals(Integer.valueOf(7), f.controller.state().entry(id).tabId);
        verify(f.tabs, never()).close(anyInt());
        verify(f.tabs, never()).unpin(anyInt());
    }

    @Test
    public void spaceDropdownConfirmsDeletionAndDisablesLastSpace() {
        Fixture f = new Fixture();
        String personal = f.controller.state().selectedSpace();
        String work = f.controller.createSpace("Work");
        String id = f.controller.rememberTab(7, "https://example.test", "Saved", false);
        f.view.refresh();
        f.view.findViewWithTag("arc-current-space").performClick();
        android.widget.PopupMenu menu = org.robolectric.shadows.ShadowPopupMenu.getLatestPopupMenu();
        android.view.MenuItem deletion = menu.getMenu().findItem(3);
        assertNotNull("Space dropdown offers explicit deletion", deletion);
        assertTrue(deletion.isEnabled());
        menu.getMenu().performIdentifierAction(3, 0);
        android.app.AlertDialog dialog = org.robolectric.shadows.ShadowAlertDialog.getLatestAlertDialog();
        assertNotNull(dialog);
        dialog.getButton(android.app.AlertDialog.BUTTON_NEGATIVE).performClick();
        shadowOf(Looper.getMainLooper()).idle();
        assertEquals(work, f.controller.state().selectedSpace());
        f.view.findViewWithTag("arc-current-space").performClick();
        org.robolectric.shadows.ShadowPopupMenu.getLatestPopupMenu().getMenu().performIdentifierAction(3, 0);
        org.robolectric.shadows.ShadowAlertDialog.getLatestAlertDialog().getButton(android.app.AlertDialog.BUTTON_POSITIVE).performClick();
        shadowOf(Looper.getMainLooper()).idle();
        assertEquals(personal, f.controller.state().selectedSpace());
        assertEquals(personal, f.controller.state().entry(id).spaceId);
        f.view.findViewWithTag("arc-current-space").performClick();
        assertFalse(org.robolectric.shadows.ShadowPopupMenu.getLatestPopupMenu().getMenu().findItem(2).isEnabled());
        verify(f.tabs, never()).close(anyInt());
        verify(f.tabs, never()).unpin(anyInt());
    }

    @Test
    public void favoritesReflowWithoutDroppingOrReplacingTiles() {
        Fixture f = new Fixture();
        java.util.List<String> ids = new java.util.ArrayList<>();
        for (int i = 0; i < 4; i++) ids.add(f.controller.rememberTab(7 + i,
                "https://example.test/" + i, "Favorite " + i, true));
        f.view.refresh();
        View[] original = new View[4];
        for (int i = 0; i < 4; i++) original[i] = f.view.findViewWithTag("arc-entry:" + ids.get(i));
        float density = f.activity.getResources().getDisplayMetrics().density;
        for (int widthDp : new int[] {304, 160, 120, 304, 160}) {
            int width = Math.round(widthDp * density);
            f.view.measure(View.MeasureSpec.makeMeasureSpec(width, View.MeasureSpec.EXACTLY),
                    View.MeasureSpec.makeMeasureSpec(1600, View.MeasureSpec.AT_MOST));
            f.view.layout(0, 0, width, f.view.getMeasuredHeight());
            View menu = f.view.findViewWithTag("arc-favorites-menu");
            assertEquals(widthDp == 120 ? View.VISIBLE : View.GONE, menu.getVisibility());
            for (int i = 0; i < 4; i++) assertSame(original[i], f.view.findViewWithTag("arc-entry:" + ids.get(i)));
            if (widthDp != 120) {
                assertEquals(widthDp == 304 ? original[0].getTop() : original[0].getBottom() + Math.round(8 * density),
                        original[2].getTop());
                assertTrue(original[3].getRight() <= width);
            }
            assertEquals(4, f.controller.state().favorites().size());
        }
    }

    @Test
    public void narrowMenuExposesEveryFavoriteInStoredOrder() {
        Fixture f = new Fixture();
        for (int i = 0; i < 4; i++) f.controller.rememberTab(7+i,
                "https://example.test/"+i, "Favorite "+i, true);
        f.view.refresh();
        int width = Math.round(120 * f.activity.getResources().getDisplayMetrics().density);
        f.view.measure(View.MeasureSpec.makeMeasureSpec(width, View.MeasureSpec.EXACTLY),
                View.MeasureSpec.makeMeasureSpec(1600, View.MeasureSpec.AT_MOST));
        f.view.layout(0,0,width,f.view.getMeasuredHeight());
        f.view.setCompact(true);
        assertEquals(View.GONE, f.view.findViewWithTag("arc-current-space").getVisibility());
        assertEquals(View.VISIBLE, f.view.findViewWithTag("arc-favorites-menu").getVisibility());
        assertTrue(f.view.findViewWithTag("arc-favorites-menu").performClick());
        android.widget.PopupMenu menu = org.robolectric.shadows.ShadowPopupMenu.getLatestPopupMenu();
        assertEquals(4,menu.getMenu().size());
        java.util.List<ArcSidebarState.Entry> stored = f.controller.state().favorites();
        for (int i=0;i<4;i++) assertEquals(stored.get(i).title,menu.getMenu().getItem(i).getTitle());
        assertTrue(menu.getMenu().performIdentifierAction(3,0));
        verify(f.tabs).select(stored.get(3).tabId);
    }

    private void checkFocus(boolean favorite) {
        Activity activity = createActivity();
        ArcTabActions.NativeTabs tabs = mock(ArcTabActions.NativeTabs.class);
        when(tabs.exists(anyInt())).thenReturn(true);
        ArcSidebarStore store = new ArcSidebarStore(null);
        ArcCollectionsController controller = new ArcCollectionsController(
                store, new ArcTabActions(store, tabs), tabs);
        String id = controller.rememberTab(7, "https://example.test", "Saved", favorite);
        ArcCollectionsView view = new ArcCollectionsView(activity, controller,
                () -> new ArcCollectionsView.CurrentTab(7, "https://example.test", "Saved"),
                (entry, button) -> {});
        activity.setContentView(view);
        mViews.add(view);
        mControllers.add(controller);
        shadowOf(Looper.getMainLooper()).idle();
        View before = view.findViewWithTag("arc-entry:" + id);
        assertTrue(before.requestFocus());
        assertTrue(before.hasFocus());
        view.refresh();
        View after = view.findViewWithTag("arc-entry:" + id);
        assertNotSame(before, after);
        assertTrue(after.hasFocus());
        view.destroy();
        controller.destroy();
    }
}
