"""Pinned cfd94726 native API boundaries for host probes; not implementations of Chromium."""
def definitions():
    return {
        'androidx.annotation.VisibleForTesting': 'public @interface VisibleForTesting {}',
        'org.chromium.base.ObserverList': 'public class ObserverList<T> extends java.util.ArrayList<T> {public void addObserver(T v){add(v);}public void removeObserver(T v){remove(v);}}',
        'org.chromium.chrome.browser.theme.ThemeColorProvider': """public class ThemeColorProvider {
        public interface ThemeColorObserver{void onThemeColorChanged(int color,boolean animate);}public interface TintObserver{void onTintChanged(android.content.res.ColorStateList t,android.content.res.ColorStateList f,int s);}
        private int color,scheme;private android.content.res.ColorStateList tint,focus;
        public ThemeColorProvider(android.content.Context c){}public void destroy(){}public int getThemeColor(){return color;}public int getBrandedColorScheme(){return scheme;}
        public android.content.res.ColorStateList getTint(){return tint;}public android.content.res.ColorStateList getActivityFocusTint(){return focus;}
        protected void updatePrimaryColor(int c,boolean a){color=c;}protected void updateTint(android.content.res.ColorStateList t,android.content.res.ColorStateList f,int s){tint=t;focus=f;scheme=s;}
        public void addThemeColorObserver(ThemeColorObserver o){}public void removeThemeColorObserver(ThemeColorObserver o){}public void addTintObserver(TintObserver o){}public void removeTintObserver(TintObserver o){}
        }""",
        'org.chromium.chrome.browser.theme.TopUiThemeColorProvider': 'public class TopUiThemeColorProvider extends ThemeColorProvider {public TopUiThemeColorProvider(){super(null);}public int getThemeColorOrFallback(org.chromium.chrome.browser.tab.Tab tab,int fallback){return fallback;}public int getToolbarBackgroundColor(org.chromium.chrome.browser.tab.Tab tab){return getThemeColor();}}',
        'org.chromium.chrome.browser.theme.BottomUiThemeColorProvider': 'public class BottomUiThemeColorProvider extends ThemeColorProvider {public BottomUiThemeColorProvider(){super(null);}}',
        'org.chromium.chrome.browser.theme.ThemeUtils': 'public class ThemeUtils {public static android.content.res.ColorStateList getThemedToolbarIconTint(android.content.Context c,int scheme){return c.getColorStateList(android.R.color.black);}public static android.content.res.ColorStateList getThemedToolbarIconTintForActivityState(android.content.Context c,int scheme,boolean focused){return getThemedToolbarIconTint(c,scheme);}}',
        'org.chromium.chrome.browser.ui.theme.BrandedColorScheme': 'public @interface BrandedColorScheme {int LIGHT_BRANDED_THEME=0,DARK_BRANDED_THEME=1,INCOGNITO=2,APP_DEFAULT=3;}',
        'org.chromium.chrome.browser.ui.bottombar.BottomBarConfigUtils': 'public class BottomBarConfigUtils {public static boolean isBottomBarEnabled(android.content.Context c){return false;}}',
        'org.chromium.components.browser_ui.styles.ChromeColors': 'public class ChromeColors {public static int getDefaultThemeColor(android.content.Context c,boolean incognito){return incognito?0xff202124:android.graphics.Color.WHITE;}}',
        'org.chromium.ui.util.ColorUtils': 'public class ColorUtils {public static boolean shouldUseLightForegroundOnBackground(int c){return android.graphics.Color.luminance(c)<.45;}}',
        'org.chromium.chrome.browser.browser_controls.BrowserControlsStateProvider': 'public interface BrowserControlsStateProvider {interface Observer{default void onControlsPositionChanged(int p){}}@interface ControlsPosition{int TOP=0,BOTTOM=1;}int getControlsPosition();void addObserver(Observer o);void removeObserver(Observer o);}',
        'org.chromium.chrome.browser.profiles.Profile': 'public class Profile {}',
        'org.chromium.chrome.browser.ui.bottombar.BottomBar': 'public interface BottomBar {android.view.View getView();int getBackgroundColor();void setParent(int host);boolean maybeShowPromoDialog(org.chromium.chrome.browser.profiles.Profile profile);void onStartupPromoFlowFinished(boolean shown);}',
        'org.chromium.chrome.browser.ui.bottombar.BottomBarHostManager': 'public class BottomBarHostManager {public @interface Host {int TABBED=0,HUB=1;}}',

        'org.chromium.chrome.browser.browser_controls.BottomControlsStacker': 'public class BottomControlsStacker { public @interface LayerScrollBehavior { int DEFAULT_SCROLL_OFF=0; } }',
        'org.chromium.chrome.browser.toolbar.bottom.BottomControlsCoordinator': 'public class BottomControlsCoordinator { public interface BottomControlsVisibilityController {void setBottomControlsVisible(boolean visible);} }',
        'org.chromium.chrome.browser.toolbar.bottom.BottomControlsContentDelegate': '''public interface BottomControlsContentDelegate {void initializeWithNative(BottomControlsCoordinator.BottomControlsVisibilityController v,org.chromium.base.Callback<Object> c);void destroy();int getScrollBehavior();Integer getBackgroundColor();}''',
        'org.chromium.components.browser_ui.bottomsheet.BottomSheetController': 'public interface BottomSheetController {boolean requestShowContent(BottomSheetContent c,boolean animate);void hideContent(BottomSheetContent c,boolean animate);void onSheetBackgroundColorOverrideChanged();}',
        'org.chromium.components.browser_ui.bottomsheet.BottomSheetType': '''public class BottomSheetType { public static class Builder {public Builder setUserInitiated(boolean b){return this;}public Builder setModal(boolean b){return this;}public BottomSheetType build(){return new BottomSheetType();}} }''',
        'org.chromium.components.browser_ui.bottomsheet.BottomSheetContent': '''public interface BottomSheetContent {
        interface ContentPriority {int HIGH=0;} interface HeightMode {int DISABLED=-3,WRAP_CONTENT=-1;}
        android.view.View getContentView();android.view.View getToolbarView();int getVerticalScrollOffset();void destroy();int getPriority();boolean swipeToDismissEnabled();
        default boolean coversBottomControls(){return false;}default float getHalfHeightRatio(){return 0;}default float getFullHeightRatio(){return 0;}
        default BottomSheetType getSheetType(){return new BottomSheetType();}default int getSheetBackgroundColorOverride(){return 0;}
        int getSheetHalfHeightAccessibilityStringId();int getSheetFullHeightAccessibilityStringId();int getSheetClosedAccessibilityStringId();}''',
    }
