"""Delivered ToolbarManager control policy; OS/JNI/animation delivery is simulated."""
from pathlib import Path
import unittest
from test_phone_overlay_insets import method,run_probe
ROOT=Path(__file__).resolve().parents[1]
class AdaptiveControlsTests(unittest.TestCase):
 def test_lifecycle_focus_and_scroll_restore_one_native_toolbar(self):
  src=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
  code='''public class AdaptiveProbe {
Object mArcPhoneGestureContents=new Object();boolean mArcPhoneFullscreen,mArcPhoneResumed=true,mArcPhoneCompact,mIsDestroyed,focus;
boolean isUrlBarFocused(){return focus;}
int insetUpdates;void updateArcPhoneContentInsets(){insetUpdates++;}
static class View {static final int VISIBLE=0,INVISIBLE=4;int visibility;float translation,alpha=1;void setAlpha(float a){alpha=a;}float getAlpha(){return alpha;}void setVisibility(int v){visibility=v;}int getHeight(){return 56;}void setTranslationY(float y){translation=y;}float getTranslationY(){return translation;}}
static class Navigation {boolean compact;void setCompact(boolean c){compact=c;}}Navigation mArcPhoneNavigation=new Navigation();
View mToolbarLayout=new View();android.animation.ValueAnimator mArcPhoneCompactAnimation;
'''+method(src,'private void setArcPhoneCompact(')+'''
static void check(boolean value){if(!value)throw new AssertionError("adaptive controls restoration/lifecycle");}
public static void main(String[] a){AdaptiveProbe p=new AdaptiveProbe();
p.setArcPhoneCompact(true);check(p.mArcPhoneCompact&&p.mArcPhoneNavigation.compact&&p.mToolbarLayout.visibility==0&&p.mToolbarLayout.alpha==0);
p.setArcPhoneCompact(false);check(!p.mArcPhoneCompact&&!p.mArcPhoneNavigation.compact&&p.mToolbarLayout.translation==0&&p.mToolbarLayout.alpha==1&&p.mToolbarLayout.visibility==0);
p.focus=true;p.setArcPhoneCompact(true);check(!p.mArcPhoneCompact);p.focus=false;
p.mArcPhoneFullscreen=true;p.setArcPhoneCompact(true);check(!p.mArcPhoneCompact);p.mArcPhoneFullscreen=false;
p.setArcPhoneCompact(true);p.mArcPhoneGestureContents=null;p.setArcPhoneCompact(false);check(!p.mArcPhoneCompact&&p.mToolbarLayout.translation==0);
p.mArcPhoneResumed=false;p.setArcPhoneCompact(true);check(!p.mArcPhoneCompact);
p.mArcPhoneCompactAnimation=new android.animation.ValueAnimator();p.mIsDestroyed=true;
p.setArcPhoneCompact(false);check(p.mArcPhoneCompactAnimation==null&&android.animation.ValueAnimator.cancelled);
}}
'''
  files={'AdaptiveProbe.java':code,
   'android/animation/Animator.java':'package android.animation;public class Animator {}',
   'android/animation/AnimatorListenerAdapter.java':'package android.animation;public class AnimatorListenerAdapter {public void onAnimationEnd(Animator a){}}',
   'android/animation/ValueAnimator.java':'''package android.animation;public class ValueAnimator extends Animator {
public static boolean areAnimatorsEnabled(){return false;}public static ValueAnimator ofFloat(float a,float b){return new ValueAnimator();}
public static boolean cancelled;public float getAnimatedFraction(){return 1;}public void cancel(){cancelled=true;}public void setDuration(long d){}public Object getAnimatedValue(){return Float.valueOf(0);}public void addUpdateListener(java.util.function.Consumer<ValueAnimator> c){}public void addListener(AnimatorListenerAdapter a){}public void start(){throw new AssertionError("reduced motion must not animate");}}
'''}
  run_probe(self,files,'AdaptiveProbe')

 def test_native_focus_owner_cannot_reenable_stale_toolbar_texture(self):
  import re
  src=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
  init=src[src.index('mToolbar.initializeWithNative('):]
  supplied=re.search(r'mBottomToolbarControlsOffsetSupplier,\s*(\w+),',init).group(1)
  update=method(src,'private void updateArcToolbarSceneGuard()') if 'private void updateArcToolbarSceneGuard()' in src else ''
  code='''public class SceneOwnerProbe {
static class Supplier {boolean value;void set(boolean v){value=v;}boolean get(){return value;}}
Supplier mSuppressToolbarSceneLayerSupplier=new Supplier(),mArcToolbarSceneGuardSupplier=new Supplier();
boolean mArcPhoneOverlayActive,mIsArcToolbarSuppressed,mIsXrFsm,mIsVerticalTabsHiddenDueToNarrow;
'''+update+'''void refresh(){'''+('updateArcToolbarSceneGuard();' if update else '')+'''}
public static void main(String[] a){SceneOwnerProbe p=new SceneOwnerProbe();
p.mArcPhoneOverlayActive=true;p.mSuppressToolbarSceneLayerSupplier.set(true);p.refresh();
Supplier actual=p.'''+supplied+''';
p.mSuppressToolbarSceneLayerSupplier.set(false);p.refresh();
if(!actual.get())throw new AssertionError("native mini-origin/focus release exposes retained toolbar texture");
p.mArcPhoneOverlayActive=false;p.refresh();if(actual.get())throw new AssertionError("Desktop/native ownership not restored");}}
'''
  run_probe(self,{'SceneOwnerProbe.java':code},'SceneOwnerProbe')
