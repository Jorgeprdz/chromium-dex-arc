// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;
import static org.junit.Assert.*;
import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Color;
import android.widget.SeekBar;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcDesktopMaterialTest {
    private static void idle(){org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();}
    private static int depth(int[] ramp){int max=0;for(int c:ramp)for(int d:ramp)for(int shift:new int[]{0,8,16})max=Math.max(max,Math.abs(((c>>shift)&255)-((d>>shift)&255)));return max;}
    @Test public void framePreservesRectangularClipAndSubtleNativeShadow(){
        var material=new ArcDesktopMaterial();material.setAppearance(0xffe6e8eb,60);material.setBounds(0,0,202,1294);
        var outline=new android.graphics.Outline();material.getOutline(outline);var rect=new android.graphics.Rect();
        assertTrue(outline.getRect(rect));assertEquals(new android.graphics.Rect(0,0,202,1294),rect);assertEquals(.12f,outline.getAlpha(),.001f);
    }
    @Test public void frameDepthIsVisibleWithoutAnyCapturedBitmap(){
        for(int c:new int[]{0xffe6e8eb,0xff202124}){
            int[] ramp=ArcDesktopMaterial.ramp(c,ArcDesktopMaterial.DEFAULT_INTENSITY);
            assertTrue("frame must not remain visually flat",depth(ramp)>=18);
            assertEquals(c,ramp[1]);for(int stop:ramp)assertEquals(255,Color.alpha(stop));
        }
    }
    @Test public void intensityControlsDepthAndZeroRemovesTheFinish(){
        for(int c:new int[]{0xffe6e8eb,0xff202124}){
            assertEquals(0,depth(ArcDesktopMaterial.ramp(c,0)));
            assertTrue(depth(ArcDesktopMaterial.ramp(c,100))>depth(ArcDesktopMaterial.ramp(c,30)));
        }
        assertEquals(0,ArcDesktopMaterial.clamp(-9));assertEquals(100,ArcDesktopMaterial.clamp(200));
    }
    @Test public void allPaletteStopsPreserveAaAgainstNativeForeground(){
        for(int r=0;r<256;r+=17)for(int g=0;g<256;g+=17)for(int b=0;b<256;b+=17){
            int c=Color.rgb(r,g,b);int foreground=ArcDesktopMaterial.foreground(c);
            for(int intensity:new int[]{0,60,100})for(int stop:ArcDesktopMaterial.ramp(c,intensity))
                assertTrue(Integer.toHexString(c),ArcDesktopMaterial.contrast(stop,foreground)>=4.5);
        }
    }
    @Test public void previewCancelAndApplyHaveSeparatePersistence(){
        var controller=Robolectric.buildActivity(Activity.class).setup();Activity a=controller.get();
        var prefs=a.getSharedPreferences("material-test",0);prefs.edit().clear().commit();
        final int[] preview={-1};
        var dialog=new ArcDesktopMaterialDialog(a,prefs,0xffe6e8eb,p->preview[0]=p).show();idle();
        SeekBar slider=dialog.findViewById(android.R.id.progress);slider.setProgress(83);
        assertEquals(83,preview[0]);assertFalse(prefs.contains(ArcDesktopMaterial.INTENSITY_KEY));
        dialog.getButton(AlertDialog.BUTTON_NEGATIVE).performClick();idle();assertEquals(-1,preview[0]);
        assertEquals(ArcDesktopMaterial.DEFAULT_INTENSITY,ArcDesktopMaterial.savedIntensity(prefs));
        dialog=new ArcDesktopMaterialDialog(a,prefs,0xffe6e8eb,p->preview[0]=p).show();idle();
        ((SeekBar)dialog.findViewById(android.R.id.progress)).setProgress(78);
        dialog.getButton(AlertDialog.BUTTON_POSITIVE).performClick();idle();assertEquals(78,ArcDesktopMaterial.savedIntensity(prefs));assertEquals(-1,preview[0]);
        controller.pause().stop().destroy();
    }
    @Test public void resetIsAReversibleDraftAndExternalDismissRestores(){
        var controller=Robolectric.buildActivity(Activity.class).setup();Activity a=controller.get();
        var prefs=a.getSharedPreferences("material-test-reset",0);prefs.edit().putInt(ArcDesktopMaterial.INTENSITY_KEY,89).commit();
        final int[] preview={-1};var dialog=new ArcDesktopMaterialDialog(a,prefs,0xff202124,p->preview[0]=p).show();idle();
        dialog.getButton(AlertDialog.BUTTON_NEUTRAL).performClick();idle();assertTrue(dialog.isShowing());
        assertEquals(ArcDesktopMaterial.DEFAULT_INTENSITY,preview[0]);assertEquals(89,ArcDesktopMaterial.savedIntensity(prefs));
        dialog.dismiss();idle();assertEquals(-1,preview[0]);assertEquals(89,ArcDesktopMaterial.savedIntensity(prefs));controller.pause().stop().destroy();
    }
}
