// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import static org.junit.Assert.*;
import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.Paint;
import android.graphics.Path;
import android.view.View;
import android.widget.FrameLayout;
import java.util.function.Consumer;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;

@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36},qualifiers="mdpi")
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcPhoneGlassTest {
    @Test public void copiesAreSmallAndPreserveAspectRatio() {
        int[] size=ArcPhoneGlass.copySize(1440,240);assertEquals(256,size[0]);assertTrue(size[1]<=43);
        size=ArcPhoneGlass.copySize(100,2000);assertTrue(size[0]<=7);assertEquals(128,size[1]);
        size=ArcPhoneGlass.copySize(4,4);assertEquals(1,size[0]);assertEquals(1,size[1]);
    }
    @Test public void blurSamplesActualPixelsAndPreservesUniformColors() {
        Bitmap b=Bitmap.createBitmap(20,20,Bitmap.Config.ARGB_8888);b.eraseColor(Color.RED);
        ArcPhoneGlass.blur(b);assertEquals(Color.RED,b.getPixel(10,10));
        for(int x=10;x<20;x++)for(int y=0;y<20;y++)b.setPixel(x,y,Color.BLUE);
        ArcPhoneGlass.blur(b);int mixed=b.getPixel(9,10);assertTrue(Color.red(mixed)>0);assertTrue(Color.blue(mixed)>0);assertEquals(255,Color.alpha(mixed));
    }
    private static class RecordingCanvas extends Canvas {
        Bitmap frame;boolean clipped;RectF imageRect;int tint;
        @Override public boolean clipPath(Path path){clipped=true;return true;}
        @Override public void drawBitmap(Bitmap bitmap,Rect src,RectF dst,Paint paint){assertTrue(clipped);frame=bitmap;imageRect=new RectF(dst);}
        @Override public void drawRect(RectF rect,Paint paint){assertTrue(clipped);tint=paint.getColor();}
    }
    @Test public void backdropUsesClippedPagePixelsAndTranslucentTint() {
        var d=new ArcPhoneGlass.Backdrop();d.setSurface(Color.WHITE);d.setBounds(0,0,100,50);
        Bitmap page=Bitmap.createBitmap(25,13,Bitmap.Config.ARGB_8888);page.eraseColor(Color.RED);d.setFrame(page);
        var canvas=new RecordingCanvas();d.draw(canvas);assertSame(page,canvas.frame);assertEquals(new RectF(0,0,100,50),canvas.imageRect);assertTrue(Color.alpha(canvas.tint)<255);
        android.graphics.Outline outline=new android.graphics.Outline();d.getOutline(outline);assertEquals(25f,outline.getRadius(),0);
        d.clear();assertFalse(d.hasFrame());d.setSurface(0xff202124);assertTrue(Color.alpha(d.tintColor())<255);
    }
    private static class FakeCopy implements ArcPhoneGlass.Capture {
        int calls,closed;Consumer<Boolean> pending;
        public boolean available(){return true;}
        public void copy(Rect bounds,Bitmap output,Consumer<Boolean> done){calls++;output.eraseColor(Color.RED);pending=done;}
        public void close(){closed++;}
    }
    private void lifecycle(boolean changeSource) {
        var activity=Robolectric.buildActivity(Activity.class).setup();FrameLayout slot=new FrameLayout(activity.get()){
            @Override public boolean isShown(){return true;}
            @Override public int getWindowVisibility(){return View.VISIBLE;}
        };activity.get().setContentView(slot);
        activity.visible();slot.layout(0,0,100,50);FakeCopy copy=new FakeCopy();var sampler=new ArcPhoneGlass(slot,copy);
        var d=sampler.add(slot,r->r.set(0,0,100,50));sampler.setEnabled(true);sampler.sampleNow();sampler.sampleNow();assertEquals(1,copy.calls);
        if(changeSource)sampler.invalidateSource();else sampler.setEnabled(false);
        copy.pending.accept(true);assertFalse(d.hasFrame());
        if(changeSource){sampler.sampleNow();assertEquals(2,copy.calls);copy.pending.accept(true);assertTrue(d.hasFrame());}
        sampler.destroy();assertFalse(d.hasFrame());sampler.sampleNow();assertTrue(copy.closed>=1);
        activity.pause().stop().destroy();
    }
    @Test public void lateCopyCannotPaintAnotherTab(){lifecycle(true);}
    @Test public void lateCopyCannotRepopulateAfterDisableOrDestroy(){lifecycle(false);}
}
