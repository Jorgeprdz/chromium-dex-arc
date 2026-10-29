"""Execute native command focus/close bodies; session and animation boundaries are adapters."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from arc_toolbar_probe import method_body

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / '.source-modified/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox'


class CommandTransitionTests(unittest.TestCase):
    def test_command_owns_focus_transition_and_reentrant_native_end(self):
        focus = method_body((NATIVE / 'LocationBarMediator.java').read_text(), r'void handleUrlFocusAnimation\(')
        close = method_body((NATIVE / 'LocationBarLayout.java').read_text(), r'public boolean closeArcCommandBarForInputEnd\(')
        source = '''
import java.util.*;
public class CommandTransitionProbe {
 static class Rect {int height(){return 800;}int width(){return 1000;}}
 static class Animator {}
 static class ObjectAnimator extends Animator {
  static int starts; boolean isRunning(){return false;} void cancel(){}
  static ObjectAnimator ofFloat(Object target,Object property,float value){return new ObjectAnimator();}
  void setDuration(long duration){} void addListener(CancelAwareAnimatorListener listener){}
  void start(){starts++;}
 }
 static class CancelAwareAnimatorListener {public void onEnd(Animator a){}public void onCancel(Animator a){}}
 static class DisplayState {static int DRAFTING_NO_FOCUS=1;}
 interface UrlFocusChangeListener {void onUrlFocusChange(boolean focus);}
 static class Layout {
  Rect mArcCommandResults; Runnable mArcCommandInputEnd;
  Rect getArcCommandResults(){return mArcCommandResults;}
  Layout getRootView(){return this;} void getLocalVisibleRect(Rect bounds){}
  public boolean closeArcCommandBarForInputEnd() {{CLOSE}}
 }
 static class Provider {
  Provider getNewTabPageDelegate(){return this;} boolean isCurrentlyVisible(){return false;}
 }
 static class Mediator {
  boolean mUrlFocusedWithoutAnimations,mIsTablet=true;
  Object mCurrentInput=new Object(),mUrlFocusChangeFractionProperty=new Object();
  ObjectAnimator mUrlFocusChangeAnimator;
  Provider mLocationBarDataProvider=new Provider(); Layout mLocationBarLayout=new Layout();
  Rect mRootViewBounds=new Rect(); int NTP_KEYBOARD_FOCUS_DURATION_MS=200;
  List<UrlFocusChangeListener> mUrlFocusChangeListeners=new ArrayList<>();
  int finished;boolean expanded,keyboard;
  void beginOrResumeInput(boolean activate){} boolean userTextDiffersFromInitial(){return false;}
  void enterDraftingNoFocus(){} boolean displayStateEquals(int state){return true;}
  void endInput(){} void setUrlFocusChangeInProgress(boolean progress){}
  void finishUrlFocusChange(boolean focus,boolean showKeyboard){finished++;expanded=focus;keyboard=showKeyboard;}
  void handleUrlFocusAnimation(boolean hasFocus) {{FOCUS}}
 }
 public static void main(String[] args) {
  Mediator m=new Mediator();m.mLocationBarLayout.mArcCommandResults=new Rect();
  m.handleUrlFocusAnimation(true);m.handleUrlFocusAnimation(false);
  if(ObjectAnimator.starts!=0 || m.finished!=2 || m.expanded || m.keyboard)
   throw new AssertionError("Command must finish native focus synchronously, starts="+ObjectAnimator.starts+", finished="+m.finished);
  m.mLocationBarLayout.mArcCommandResults=null;m.handleUrlFocusAnimation(true);
  if(ObjectAnimator.starts!=1)throw new AssertionError("Ordinary tablet focus must retain animation");
  Layout l=new Layout();l.mArcCommandResults=new Rect();l.mArcCommandInputEnd=()->{};
  if(l.closeArcCommandBarForInputEnd())throw new AssertionError("Guarded close must allow native endInput to continue");
  if(l.closeArcCommandBarForInputEnd())throw new AssertionError("Callback must be consumed once");
  l.mArcCommandInputEnd=()->l.mArcCommandResults=null;
  if(!l.closeArcCommandBarForInputEnd())throw new AssertionError("Completed external close must consume native endInput");
 }
}
'''.replace('{{FOCUS}}', focus).replace('{{CLOSE}}', close)
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary); path = work / 'CommandTransitionProbe.java'; path.write_text(source)
            compiled = subprocess.run(['javac', '-d', str(work), str(path)], capture_output=True, text=True)
            self.assertEqual(0, compiled.returncode, compiled.stderr)
            result = subprocess.run(['java', '-cp', str(work), 'CommandTransitionProbe'], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)


if __name__ == '__main__':
    unittest.main()
