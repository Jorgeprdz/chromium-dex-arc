"""Pinned cfd94726 native API boundaries for host probes; not implementations of Chromium."""
def definitions():
    return {
        'org.chromium.chrome.browser.profiles.Profile': 'public class Profile {}',
        'org.chromium.chrome.browser.ui.bottombar.BottomBar': 'public interface BottomBar {android.view.View getView();int getBackgroundColor();void setParent(int host);boolean maybeShowPromoDialog(org.chromium.chrome.browser.profiles.Profile profile);void onStartupPromoFlowFinished(boolean shown);}',
        'org.chromium.chrome.browser.ui.bottombar.BottomBarHostManager': 'public class BottomBarHostManager {public @interface Host {int TABBED=0,HUB=1;}}',

        'org.chromium.chrome.browser.browser_controls.BottomControlsStacker': 'public class BottomControlsStacker { public @interface LayerScrollBehavior { int DEFAULT_SCROLL_OFF=0; } }',
        'org.chromium.chrome.browser.toolbar.bottom.BottomControlsCoordinator': 'public class BottomControlsCoordinator { public interface BottomControlsVisibilityController {void setBottomControlsVisible(boolean visible);} }',
        'org.chromium.chrome.browser.toolbar.bottom.BottomControlsContentDelegate': '''public interface BottomControlsContentDelegate {void initializeWithNative(BottomControlsCoordinator.BottomControlsVisibilityController v,org.chromium.base.Callback<Object> c);void destroy();int getScrollBehavior();Integer getBackgroundColor();}''',
        'org.chromium.components.browser_ui.bottomsheet.BottomSheetController': 'public interface BottomSheetController {boolean requestShowContent(BottomSheetContent c,boolean animate);void hideContent(BottomSheetContent c,boolean animate);}',
        'org.chromium.components.browser_ui.bottomsheet.BottomSheetType': '''public class BottomSheetType { public static class Builder {public Builder setUserInitiated(boolean b){return this;}public Builder setModal(boolean b){return this;}public BottomSheetType build(){return new BottomSheetType();}} }''',
        'org.chromium.components.browser_ui.bottomsheet.BottomSheetContent': '''public interface BottomSheetContent {
        interface ContentPriority {int HIGH=0;} interface HeightMode {int DISABLED=-3,WRAP_CONTENT=-1;}
        android.view.View getContentView();android.view.View getToolbarView();int getVerticalScrollOffset();void destroy();int getPriority();boolean swipeToDismissEnabled();
        default boolean coversBottomControls(){return false;}default float getHalfHeightRatio(){return 0;}default float getFullHeightRatio(){return 0;}
        default BottomSheetType getSheetType(){return new BottomSheetType();}default int getSheetBackgroundColorOverride(){return 0;}
        int getSheetHalfHeightAccessibilityStringId();int getSheetFullHeightAccessibilityStringId();int getSheetClosedAccessibilityStringId();}''',
    }
