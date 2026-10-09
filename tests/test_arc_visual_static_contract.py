#!/usr/bin/env python3
"""Static Prompt-4 contract checks. IMPLEMENTATION_MIRROR only; not runtime proof."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TABBED = ROOT / '.source-modified/chrome/android/java/src/org/chromium/chrome/browser/tabbed_mode/TabbedRootUiCoordinator.java'
ARC = ROOT / 'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java'
POLICY = ROOT / 'chromium/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopPolicy.java'
VERTICAL = ROOT / '.source-modified/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/VerticalTabUtils.java'


def text(path: Path) -> str:
    return path.read_text(encoding='utf-8')


class ArcVisualStaticContractTest(unittest.TestCase):
    """IMPLEMENTATION_MIRROR: source-level invariants, never runtime visual evidence."""

    @classmethod
    def setUpClass(cls):
        cls.tabbed = text(TABBED)
        cls.arc = text(ARC)
        cls.policy = text(POLICY)
        cls.vertical = text(VERTICAL)

    def test_toolbar_removed_from_browser_controls_and_restored(self):
        self.assertIn('toolbarView.clearFocus()', self.tabbed)
        self.assertIn('toolbarView.setVisibility(View.GONE)', self.tabbed)
        self.assertIn('toolbarHairline.setVisibility(View.GONE)', self.tabbed)
        self.assertIn('mTopControlsStacker.removeControl(toolbarCoordinator)', self.tabbed)
        self.assertIn('mTopControlsStacker.addControl(toolbarCoordinator)', self.tabbed)
        self.assertIn('toolbarView.setVisibility(mArcToolbarOriginalVisibility)', self.tabbed)
        self.assertIn('mTopControlsStacker.requestLayerUpdateSync', self.tabbed)

    def test_real_omnibox_is_reparented_not_reimplemented(self):
        self.assertIn('R.id.location_bar', self.arc)
        self.assertIn('R.id.location_bar_holder', self.arc)
        self.assertIn('mLocationBarOriginalParent.removeView(mLocationBarHost)', self.arc)
        self.assertIn('restoreLocationBar()', self.arc)
        self.assertNotIn('mAddressButton', self.arc)
        self.assertNotIn('Search or enter address', self.arc)


    def test_navigation_targets_real_tab_and_native_utility_controls_survive(self):
        # Forced ARC can run with ToolbarPhone, whose Chromium 157 layout has no forward/reload
        # Views. Arc therefore dispatches those controls directly to the current real Tab.
        for call in ('tab.canGoBack()', 'tab.goBack()', 'tab.canGoForward()',
                     'tab.goForward()', 'Tab::reload'):
            self.assertIn(call, self.arc)
        self.assertIn('R.id.menu_button_wrapper', self.arc)
        self.assertIn('restoreToolbarUtilityControls()', self.arc)
        self.assertIn('R.id.extensions_toolbar_container', self.arc)
        self.assertIn('mExtensionsToolbarHost', self.arc)
        # The omnibox itself is still Chromium's real LocationBar, not a parallel EditText.
        self.assertNotIn('mAddressButton', self.arc)

    def test_native_collapse_and_new_tab_contract(self):
        self.assertIn('R.id.collapse_button', self.arc)
        self.assertIn('restoreCollapseButton()', self.arc)
        # New tab remains owned by VerticalTabRailLayout/VerticalTabListCoordinator.
        self.assertNotIn('new LoadUrlParams("chrome://newtab/")', self.arc)
        self.assertIn('VerticalTabRailLayout already owns Chromium\'s real new-tab button', self.arc)

    def test_side_ui_drives_real_viewport_geometry(self):
        self.assertIn('getCurrentSideUiSpecs()', self.tabbed)
        self.assertIn('getReservedWidth(SideUiCoordinator.AnchorSide.LEFT)', self.tabbed)
        self.assertIn('mReservedLeftWidth', self.arc)
        self.assertNotIn('setTranslationX(', self.arc)
        self.assertNotIn('.setAlpha(0', self.arc)

    def test_clipping_uses_holder_and_active_surface_with_matching_hit_test(self):
        self.assertIn('mCompositorViewHolder.setOutlineProvider(mArcContentOutlineProvider)', self.arc)
        self.assertIn('mCompositorViewHolder.setClipToOutline(true)', self.arc)
        self.assertIn('mCompositorViewHolder.getActiveSurfaceView()', self.arc)
        self.assertIn('activeSurface.setClipToOutline(true)', self.arc)
        self.assertIn('new TouchEventObserver()', self.arc)
        self.assertIn('mayInterceptTouchSequenceInWebContents()', self.arc)
        self.assertIn('ArcDesktopPolicy.containsRoundedRectPoint', self.arc)
        self.assertNotIn('Canvas', self.arc)
        self.assertNotIn('drawRoundRect', self.arc)
        self.assertNotIn('mCompositorViewHolder.setBackgroundColor', self.arc)


    def test_frame_geometry_does_not_mutate_tab_model(self):
        start = self.arc.index('    private void applyFrameGeometry()')
        end = self.arc.index('    private void restoreFrameGeometry()', start)
        body = self.arc[start:end]
        for forbidden in ('mCurrentModel', 'mCurrentCreator', 'closeTabs(', 'setIndex(', 'pinTab(', 'unpinTab('):
            self.assertNotIn(forbidden, body)

    def test_arc_mode_guard_preserves_mobile(self):
        self.assertIn('VerticalTabUtils.isVerticalTabsEligible(mActivity)', self.tabbed)
        self.assertIn('return context != null && ArcDesktopAppearance.isDesktopWindow(context)', self.vertical)
        self.assertIn('if (preference == MODE_MOBILE) return false', self.policy)


    def test_arc_mobile_transition_restores_real_chrome_composition(self):
        self.assertIn('ArcDesktopAppearance.UI_MODE_KEY.equals(key)', self.arc)
        self.assertIn('setArcToolbarCompositionActive(desktop)', self.arc)
        self.assertIn('setArcToolbarCompositionActive(false)', self.arc)
        self.assertIn('attachToolbarControlsToArc()', self.arc)
        self.assertIn('clearFrameGeometry()', self.arc)
        self.assertIn('mArcFrameActive = true', self.arc)
        self.assertIn('mArcFrameActive = false', self.arc)
        # Re-enable order must put Chromium controls back before showing ToolbarTablet again.
        deactivate = self.arc.index('    private void setArcToolbarCompositionActive(boolean active)')
        restore_location = self.arc.index('restoreLocationBar();', deactivate)
        restore_utility = self.arc.index('restoreToolbarUtilityControls();', deactivate)
        restore_collapse = self.arc.index('restoreCollapseButton();', deactivate)
        show_toolbar = self.arc.index('mSetToolbarSuppressed.accept(false);', deactivate)
        self.assertLess(restore_location, show_toolbar)
        self.assertLess(restore_utility, show_toolbar)
        self.assertLess(restore_collapse, show_toolbar)

    def test_regular_incognito_paths_remain_distinct(self):
        # Execute the real coordinator's palette argument propagation. A specific flat-surface
        # source spelling would reject an intentional gradient without catching profile leakage.
        from test_arc_geometry_runtime import ArcFrameRuntimeTest
        ArcFrameRuntimeTest.setUpClass()
        try:
            ArcFrameRuntimeTest().run_case('incognito')
        finally:
            ArcFrameRuntimeTest.tearDownClass()


if __name__ == '__main__':
    unittest.main()
