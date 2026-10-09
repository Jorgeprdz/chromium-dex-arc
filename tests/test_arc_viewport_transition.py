"""Compile and run the shipped transition with an explicit Android animation boundary."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from arc_toolbar_probe import ROOT

SOURCE=ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcViewportTransition.java'

class ArcViewportTransitionTest(unittest.TestCase):
    def test_captured_width_animation_emits_native_values_and_handles_nonchanges(self):
        self.assertTrue(SOURCE.is_file(),'Arc viewport must join the native transition')
        definitions={
            'android.view.View':'public class View {}',
            'android.view.ViewGroup':'public class ViewGroup extends View {}',
            'android.animation.Animator':'public class Animator {}',
            'android.animation.ValueAnimator':'''public class ValueAnimator extends Animator {
                public interface AnimatorUpdateListener {void onAnimationUpdate(ValueAnimator value);}
                public AnimatorUpdateListener listener;public int value;
                public static ValueAnimator ofInt(int... values){return new ValueAnimator();}
                public void addUpdateListener(AnimatorUpdateListener update){listener=update;}
                public Object getAnimatedValue(){return value;}
                public void publish(int next){value=next;listener.onAnimationUpdate(this);}
            }''',
            'android.transition.TransitionValues':'''public class TransitionValues {
                public android.view.View view;public final java.util.Map<String,Object> values=new java.util.HashMap<>();
                public TransitionValues(android.view.View target){view=target;}
            }''',
            'android.transition.Transition':'''public abstract class Transition {
                public Transition addTarget(android.view.View view){return this;}
                public abstract void captureStartValues(TransitionValues values);
                public abstract void captureEndValues(TransitionValues values);
                public String[] getTransitionProperties(){return null;}
                public android.animation.Animator createAnimator(android.view.ViewGroup root,TransitionValues start,TransitionValues end){return null;}
            }''',
            'org.chromium.build.annotations.Nullable':'''import java.lang.annotation.*;
                @Target(ElementType.TYPE_USE) public @interface Nullable {}''',
        }
        program='''
import java.util.*;
import android.view.View;
import android.transition.TransitionValues;
import android.animation.ValueAnimator;
import org.chromium.chrome.browser.arc.ArcViewportTransition;
class ViewportTransitionProbe {
    static void check(boolean b,String why){if(!b)throw new AssertionError(why);}
    public static void main(String[]args){
        View target=new View();List<Integer> offsets=new ArrayList<>();
        var transition=new ArcViewportTransition(target,321,52,offsets::add);
        var start=new TransitionValues(target);var end=new TransitionValues(target);
        transition.captureStartValues(start);transition.captureEndValues(end);
        var animator=(ValueAnimator)transition.createAnimator(null,start,end);
        check(animator!=null,"different reserved widths create the synchronized animator");
        animator.publish(321);animator.publish(200);animator.publish(52);
        check(offsets.equals(List.of(321,200,52)),"callback follows actual native animator values including intermediate width");
        check(transition.createAnimator(null,null,end)==null,"missing start snapshot must not animate");
        var other=new TransitionValues(new View());transition.captureStartValues(other);
        check(transition.createAnimator(null,other,end)==null,"unrelated view cannot own viewport animation");
        var hover=new ArcViewportTransition(target,52,52,offsets::add);
        start=new TransitionValues(target);end=new TransitionValues(target);
        hover.captureStartValues(start);hover.captureEndValues(end);
        check(hover.createAnimator(null,start,end)==null,"hover's unchanged reserved width never starts a page resize animation");
        var hidden=new ArcViewportTransition(target,-1,52,offsets::add);
        start=new TransitionValues(target);end=new TransitionValues(target);
        hidden.captureStartValues(start);hidden.captureEndValues(end);
        check(start.values.containsValue(0),"hidden/negative start is bounded to viewport origin");
    }
}
'''
        with tempfile.TemporaryDirectory(prefix='arc-viewport-transition-') as tmp:
            work=Path(tmp)
            for name,body in definitions.items():
                path=work/(name.replace('.','/')+'.java');path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text('package '+name.rsplit('.',1)[0]+';\n'+body)
            probe=work/'ViewportTransitionProbe.java';probe.write_text(program)
            result=subprocess.run(['javac','--release','17','-d',tmp,*map(str,work.rglob('*.java')),str(SOURCE)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run(['java','-ea','-cp',tmp,'ViewportTransitionProbe'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_complete_transition_compiles_against_android37_with_type_use_nullable(self):
        jar=Path('/opt/android-sdk/platforms/android-37.0/android.jar')
        if not jar.is_file():self.skipTest('Android37 API unavailable')
        with tempfile.TemporaryDirectory(prefix='arc-transition-sdk-') as tmp:
            annotation=Path(tmp)/'Nullable.java'
            annotation.write_text('package org.chromium.build.annotations;\nimport java.lang.annotation.*;\n@Target(ElementType.TYPE_USE) public @interface Nullable {}')
            result=subprocess.run(['javac','--release','17','-cp',str(jar),'-d',tmp,str(annotation),str(SOURCE)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
