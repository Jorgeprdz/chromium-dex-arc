#!/usr/bin/env python3
"""Run delivered surface clip lifecycle methods against Robolectric Android views.

The Chromium compositor getter and frame entry point are explicit adapters.
This verifies clip rectangles/listener cleanup, not GPU rendering or APK runtime.
"""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from arc_toolbar_probe import method_body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--classpath-file', type=Path, required=True)
    parser.add_argument('--java-home', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--omit-surface-layout-listener', action='store_true',
                        help='Negative regression: reproduce the previous stale clip')
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    arc = ROOT / 'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc'
    shell = (arc / 'ArcDesktopCoordinator.java').read_text()
    methods = '\n'.join('private ' + result + ' ' + name + '(' + params + ') ' +
        method_body(shell, r'private ' + result + ' ' + name + r'\(')
        for result, name, params in [('void', 'applyActiveSurfaceClip', ''),
                                    ('void', 'restoreClippedSurface', ''),
                                    ('int', 'arcClipLeftForView', 'View view')])
    if args.omit_surface_layout_listener:
        methods = methods.replace('        activeSurface.addOnLayoutChangeListener(mContentLayoutListener);', '')
    listener = method_body(shell, r'mContentLayoutListener =\s*\(v, l, t, r, b, ol, ot, or, ob\) ->')
    source = r'''
import static org.junit.Assert.*;
import android.app.Activity;
import android.graphics.Rect;
import android.view.View;
import android.view.SurfaceView;
import android.view.ViewOutlineProvider;
import android.widget.FrameLayout;
import org.junit.Test;
import org.junit.After;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.Shadows;
import org.robolectric.annotation.*;
import org.chromium.chrome.browser.arc.ArcFrameDispatch;
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36},qualifiers="mdpi")
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class SurfaceClipProbe {
    final org.robolectric.android.controller.ActivityController<Activity> activity =
        Robolectric.buildActivity(Activity.class).setup();
    @After public void close(){activity.pause().stop().destroy();}
    static class Holder extends FrameLayout {
        View active;
        Holder(Activity a){super(a);}
        View getActiveSurfaceView(){return active;}
    }
    static class Shell {
        final Holder mCompositorViewHolder;
        View mClippedSurface;
        ViewOutlineProvider mClippedSurfaceOriginalOutlineProvider;
        boolean mClippedSurfaceOriginalClipToOutline;
        Rect mClippedSurfaceOriginalClipBounds;
        final ViewOutlineProvider mArcContentOutlineProvider = ViewOutlineProvider.BOUNDS;
        final View.OnAttachStateChangeListener mSurfaceAttachStateListener =
            new View.OnAttachStateChangeListener(){
                public void onViewAttachedToWindow(View v){}
                public void onViewDetachedFromWindow(View v){}
            };
        boolean mArcFrameActive=true;
        final ArcFrameDispatch mFrameDispatch=new ArcFrameDispatch(()->mArcFrameActive);
        final View.OnLayoutChangeListener mContentLayoutListener =
            (v,l,t,r,b,ol,ot,or,ob)-> __LISTENER__;
        Shell(Activity a){
            mCompositorViewHolder=new Holder(a);
            FrameLayout root=new FrameLayout(a);
            root.addView(mCompositorViewHolder,new FrameLayout.LayoutParams(400,600));
            a.setContentView(root);
            Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();
            mCompositorViewHolder.layout(0,0,400,600);
        }
        int dp(int n){return n;}
        int reservedLeftWidth(){return 52;}
        void applyFrameGeometry(){applyActiveSurfaceClip();}
        __METHODS__
    }
    @Test public void initiallyEmptySurfaceRecoversWithoutHolderResize(){
        Shell s=new Shell(activity.get());
        SurfaceView surface=new SurfaceView(activity.get());
        s.mCompositorViewHolder.addView(surface);s.mCompositorViewHolder.active=surface;
        s.applyActiveSurfaceClip();assertEquals(new Rect(),surface.getClipBounds());
        surface.layout(0,0,400,600);Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();
        assertEquals("Surface grew but stale empty clip still hides WebContents",
            new Rect(52,0,400,600),surface.getClipBounds());
    }
    @Test public void surfaceResizeUpdatesCropAndReplacementRemovesListener(){
        Shell s=new Shell(activity.get());
        View old=new SurfaceView(activity.get());s.mCompositorViewHolder.addView(old);
        old.layout(0,0,348,600);s.mCompositorViewHolder.active=old;
        Rect original=new Rect(1,2,330,580);old.setClipBounds(original);
        s.applyActiveSurfaceClip();assertEquals(new Rect(0,0,348,600),old.getClipBounds());
        old.layout(0,0,400,600);Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();
        assertEquals(new Rect(52,0,400,600),old.getClipBounds());
        View next=new SurfaceView(activity.get());s.mCompositorViewHolder.addView(next);
        next.layout(0,0,400,600);s.mCompositorViewHolder.active=next;s.applyActiveSurfaceClip();
        assertEquals(original,old.getClipBounds());
        // Re-enable eligibility deliberately: an obsolete listener would now reapply clipping.
        s.restoreClippedSurface();old.layout(0,0,300,500);
        Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();
        assertNull("Old surface must not trigger work after restoration",s.mClippedSurface);
        assertEquals(original,old.getClipBounds());
        assertNull(next.getClipBounds());
    }
}
'''.replace('__METHODS__', methods).replace('__LISTENER__', listener)
    fixture = args.work / 'SurfaceClipProbe.java'
    fixture.write_text(source)
    cp = args.classpath_file.read_text().strip()
    subprocess.run([str(args.java_home / 'bin/javac'), '-cp', cp, '-d', str(args.work),
                    str(arc / 'ArcFrameDispatch.java'), str(fixture)], check=True)
    result = subprocess.run([str(args.java_home / 'bin/java'), '-ea',
        '-Drobolectric.conscryptMode=OFF',
        '-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2',
        '-cp', str(args.work) + ':' + cp, 'org.junit.runner.JUnitCore', 'SurfaceClipProbe'])
    print('SCOPE=delivered_clip_lifecycle_Robolectric_NOT_GPU_OR_APK_RUNTIME', flush=True)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
