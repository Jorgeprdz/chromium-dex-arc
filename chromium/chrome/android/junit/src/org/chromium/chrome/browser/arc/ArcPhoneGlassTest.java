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
    @Test public void statusSampleOnlyDoesNotPaintPillTintOrOpaqueFallback() {
        var backdrop=new ArcPhoneGlass.Backdrop();backdrop.setSampleOnly(true);backdrop.setCornerRadius(0);backdrop.setBounds(0,0,200,30);
        final int[] fills={0};
        var canvas=new Canvas(){@Override public void drawRect(RectF rect,Paint paint){fills[0]++;}};
        backdrop.draw(canvas);assertEquals(0,fills[0]);
        Bitmap frame=Bitmap.createBitmap(20,3,Bitmap.Config.ARGB_8888);backdrop.setFrame(frame);
        backdrop.draw(canvas);assertEquals(0,fills[0]);backdrop.clear();frame.recycle();
    }

    @Test public void milkyPopupWithPartialWebFramePaintsAnOpaqueBase() {
        var backdrop=new ArcPhoneGlass.Backdrop();
        backdrop.setMilky(true);backdrop.setSurface(0xff303238);backdrop.setBounds(0,0,200,100);
        Bitmap frame=Bitmap.createBitmap(2,2,Bitmap.Config.ARGB_8888);
        backdrop.setFrame(frame,new Rect(0,0,200,100),new Rect(100,0,200,100));
        class RecordingCanvas extends Canvas {
            int rectangles,firstAlpha;
            @Override public void drawRect(RectF rect,Paint paint){
                if(rectangles++==0)firstAlpha=paint.getAlpha();
            }
        }
        var canvas=new RecordingCanvas();backdrop.draw(canvas);
        assertTrue("A popup outside the web capture needs a base before its tinted layer",canvas.rectangles>=2);
        assertEquals(255,canvas.firstAlpha);
    }

    @Test public void popupRegionUsesScreenCoordinatesAcrossSeparateWindows() {
        View content=new View(Robolectric.buildActivity(Activity.class).setup().get()) {
            @Override public void getLocationOnScreen(int[] out){out[0]=100;out[1]=200;}
            @Override public void getLocationInWindow(int[] out){out[0]=0;out[1]=0;}
        };
        content.layout(0,0,400,800);
        assertEquals(new Rect(20,30,220,330),ArcPhoneGlass.contentRegion(content,new Rect(120,230,320,530)));
    }
    @Test public void nativeMenuDecoratorRestoresBackgroundOnDisableAndDetach() {
        var activity=Robolectric.buildActivity(Activity.class).setup();
        View target=new View(activity.get());target.setBackgroundColor(Color.RED);
        var original=target.getBackground();target.setPadding(3,4,5,6);
        var glass=new ArcPhoneGlass(target,new ArcPhoneGlass.Capture(){
            public boolean available(){return false;}
            public void copy(Rect r,Bitmap b,Consumer<Boolean> result){result.accept(false);}
            public void close(){}
        });
        int layersTag=0x7f0f1234;View layer=new View(activity.get());layer.setBackgroundColor(Color.BLUE);
        var originalLayer=layer.getBackground();target.setTag(layersTag,new View[]{layer});glass.setSurfaceLayersTag(layersTag);
        var decorator=glass.getSurfaceDecorator();
        decorator.onViewAttachedToWindow(target);
        assertSame(original,target.getBackground());
        glass.setEnabled(true);assertTrue(target.getBackground() instanceof ArcPhoneGlass.Backdrop);assertNull(layer.getBackground());
        assertEquals(3,target.getPaddingLeft());assertEquals(6,target.getPaddingBottom());
        glass.setSurface(0xff202124);
        assertTrue(Color.luminance(((ArcPhoneGlass.Backdrop)target.getBackground()).tintColor())<.1);
        glass.setEnabled(false);assertSame(original,target.getBackground());assertSame(originalLayer,layer.getBackground());
        glass.setEnabled(true);assertTrue(target.getBackground() instanceof ArcPhoneGlass.Backdrop);
        decorator.onViewDetachedFromWindow(target);assertSame(original,target.getBackground());
        glass.destroy();activity.pause().stop().destroy();
    }
    @Test public void translatedSheetCapturesOnlyVisibleWebIntersectionWithoutStretching() {
        var activity=Robolectric.buildActivity(Activity.class).setup();
        for(boolean localClip:new boolean[]{false,true}){
            View sheet=new View(activity.get()){
                @Override public boolean isShown(){return true;}
                @Override public int getWindowVisibility(){return View.VISIBLE;}
                @Override public void getLocationOnScreen(int[] xy){xy[0]=0;xy[1]=640;}
                @Override public boolean getGlobalVisibleRect(Rect rect,android.graphics.Point offset){rect.set(0,640,904,640+(localClip?1326:1880));if(offset!=null)offset.set(0,640);return true;}
            };sheet.layout(0,0,904,1880);
            FakeCopy copy=new FakeCopy(){
                @Override public Rect clip(Rect screen){Rect out=new Rect(screen);return out.intersect(0,0,904,1966)?out:null;}
                @Override public void copy(Rect screen,Bitmap output,Consumer<Boolean> done){assertEquals(new Rect(0,640,904,1966),screen);super.copy(screen,output,done);}
            };
            var sampler=new ArcPhoneGlass(sheet,copy);var backdrop=sampler.add(sheet,sheet::getDrawingRect);
            sampler.setEnabled(true);sampler.sampleNow();assertEquals(1,copy.calls);copy.pending.accept(true);assertTrue(backdrop.hasFrame());
            backdrop.setBounds(0,0,904,1880);var canvas=new RecordingCanvas();backdrop.draw(canvas);
            assertEquals("crop must occupy only the visible part, not stretch down the hidden sheet",new RectF(0,0,904,1326),canvas.imageRect);
            sampler.destroy();
        }
        activity.pause().stop().destroy();
    }
    @Test public void milkyPanelsKeepNativeTintAndContrastEvenWithoutWebReadback() {
        var d=new ArcPhoneGlass.Backdrop();d.setMilky(true);d.setBounds(0,0,100,50);
        for(int surface:new int[]{Color.WHITE,0xff202124,0xffc4d9e4}){
            d.setSurface(surface);assertEquals(surface&0xffffff,d.tintColor()&0xffffff);
            assertTrue(Color.alpha(d.tintColor())>=230);assertTrue(Color.alpha(d.tintColor())<255);
            var canvas=new RecordingCanvas();d.draw(canvas);assertEquals("failed/protected capture must not expose sharp page text",255,Color.alpha(canvas.tint));
            d.setFrame(Bitmap.createBitmap(25,13,Bitmap.Config.ARGB_8888));canvas=new RecordingCanvas();d.draw(canvas);assertEquals(230,Color.alpha(canvas.tint));d.clear();
        }
    }
    @Test public void desktopMaterialKeepsPanelCornersPaletteAndNativeContrast() {
        var d=new ArcPhoneGlass.Backdrop();d.setDesktopMaterial();d.setCornerRadius(12);d.setBounds(0,0,500,300);
        var outline=new android.graphics.Outline();d.getOutline(outline);assertEquals(12f,outline.getRadius(),0f);
        for(int color:new int[]{0xffeee7dc,0xff202124,0xffc4d9e4}){
            d.setSurface(color);assertEquals(color&0xffffff,d.tintColor()&0xffffff);
            var canvas=new RecordingCanvas();d.draw(canvas);assertEquals(255,Color.alpha(canvas.tint));
            d.setFrame(Bitmap.createBitmap(64,32,Bitmap.Config.ARGB_8888));
            canvas=new RecordingCanvas();d.draw(canvas);assertEquals(230,Color.alpha(canvas.tint));d.clear();
        }
    }
    private static int composite(int top,int bottom){
        double a=Color.alpha(top)/255.0;return Color.rgb((int)Math.round(Color.red(top)*a+Color.red(bottom)*(1-a)),
                (int)Math.round(Color.green(top)*a+Color.green(bottom)*(1-a)),(int)Math.round(Color.blue(top)*a+Color.blue(bottom)*(1-a)));
    }
    @Test public void desktopCustomPalettesKeepAaContrastOverOppositePages() {
        var d=new ArcPhoneGlass.Backdrop();d.setDesktopMaterial();
        for(int red=0;red<256;red+=17)for(int green=0;green<256;green+=17)for(int blue=0;blue<256;blue+=17){
            int color=Color.rgb(red,green,blue);double source=Color.luminance(color);
            int foreground=(source+.05)/.05>=1.05/(source+.05)?Color.BLACK:Color.WHITE;
            d.setSurface(color);
            for(int page:new int[]{Color.BLACK,Color.WHITE}){
                int result=composite(d.tintColor(),page);
                // The sheen must improve the existing native foreground contrast in both themes.
                result=composite((d.sheenColor()&0xffffff)|0x12000000,result);
                double l=Color.luminance(result),f=Color.luminance(foreground);
                assertTrue("AA palette="+Integer.toHexString(color), (Math.max(l,f)+.05)/(Math.min(l,f)+.05)>=4.5);
            }
        }
    }
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
    @Test public void regionReadbackUsesWebPixelsWithoutSurfaceViewBuffers() {
        var activity=Robolectric.buildActivity(Activity.class).setup();
        View content=new View(activity.get());activity.get().setContentView(content);activity.visible();
        content.layout(0,0,400,800);
        int[] location=new int[2];content.getLocationOnScreen(location);
        Rect window=new Rect(location[0]+16,location[1]+600,location[0]+384,location[1]+656);
        assertEquals(new Rect(16,600,384,656),ArcPhoneGlass.contentRegion(content,window));
        assertNull(ArcPhoneGlass.contentRegion(content,new Rect(-10,-10,20,20)));
        assertNull(ArcPhoneGlass.contentRegion(content,new Rect(0,0,0,0)));
        activity.pause().stop().destroy();
    }
    @Test public void closingContentSourceRejectsPendingNativeReadbackBeforeBlur() {
        var activity=Robolectric.buildActivity(Activity.class).setup();
        View content=new View(activity.get()){@Override public boolean isShown(){return true;} @Override public int getWindowVisibility(){return View.VISIBLE;}};
        activity.get().setContentView(content);activity.visible();content.layout(0,0,400,800);
        java.util.List<Consumer<Bitmap>> pending=new java.util.ArrayList<>();
        var capture=ArcPhoneGlass.contentSource(()->content,(rect,width,height,callback)->{
            assertEquals(new Rect(16,600,384,656),rect);assertEquals(92,width);assertEquals(14,height);pending.add(callback);
        });
        int[] position=new int[2];content.getLocationOnScreen(position);
        Rect bounds=new Rect(16,600,384,656);bounds.offset(position[0],position[1]);
        java.util.List<Boolean> results=new java.util.ArrayList<>();
        capture.copy(bounds,Bitmap.createBitmap(92,14,Bitmap.Config.ARGB_8888),results::add);
        assertEquals(1,pending.size());assertTrue(results.isEmpty());capture.close();
        pending.get(0).accept(Bitmap.createBitmap(92,14,Bitmap.Config.ARGB_8888));
        assertEquals(java.util.List.of(false),results);
        activity.pause().stop().destroy();
    }
    @Test public void frostedBackdropDissolvesSmallTextInsteadOfShowingSharpGhosts() {
        Bitmap b=Bitmap.createBitmap(200,40,Bitmap.Config.ARGB_8888);b.eraseColor(Color.WHITE);
        for(int x=99;x<=100;x++)for(int y=0;y<40;y++)b.setPixel(x,y,Color.BLACK);
        ArcPhoneGlass.blur(b);
        assertTrue("small text must dissolve into the frosted surface",Color.red(b.getPixel(100,20))>220);
        assertEquals(Color.WHITE,b.getPixel(10,20));
        var d=new ArcPhoneGlass.Backdrop();d.setSurface(Color.WHITE);
        assertTrue("light glass must retain at least 70% surface tint",Color.alpha(d.tintColor())>=179);
        d.setSurface(0xff202124);assertTrue(Color.alpha(d.tintColor())>=196);
    }
    @Test public void navigationPillHasThinThemeAwareEdgeWithoutChangingBounds() {
        var d=new ArcPhoneGlass.Backdrop();d.setBounds(0,0,100,50);d.setEdgeEnabled(true,2f);
        for(int color:new int[]{Color.WHITE,0xff202124}){
            d.setSurface(color);var canvas=new RecordingCanvas();d.draw(canvas);
            assertTrue(canvas.edgeWidth>0&&canvas.edgeWidth<=1f);
            assertTrue(Color.alpha(canvas.edgeColor)>0&&Color.alpha(canvas.edgeColor)<=48);
            assertEquals(new Rect(0,0,100,50),d.getBounds());
            if(color==Color.WHITE)assertTrue(Color.luminance(canvas.edgeColor)<.1);
            else assertTrue(Color.luminance(canvas.edgeColor)>.9);
        }
    }
    private static class RecordingCanvas extends Canvas {
        Bitmap frame;boolean clipped;RectF imageRect;int tint;float edgeWidth;int edgeColor;
        @Override public boolean clipPath(Path path){clipped=true;return true;}
        @Override public void drawBitmap(Bitmap bitmap,Rect src,RectF dst,Paint paint){assertTrue(clipped);frame=bitmap;imageRect=new RectF(dst);}
        @Override public void drawRect(RectF rect,Paint paint){assertTrue(clipped);tint=(paint.getColor()&0xffffff)|(paint.getAlpha()<<24);}
        @Override public void drawRoundRect(RectF rect,float rx,float ry,Paint paint){assertEquals(Paint.Style.STROKE,paint.getStyle());edgeWidth=paint.getStrokeWidth();edgeColor=paint.getColor();}
    }
    @Test public void backdropUsesClippedPagePixelsAndTranslucentTint() {
        var d=new ArcPhoneGlass.Backdrop();d.setSurface(Color.WHITE);d.setBounds(0,0,100,50);
        Bitmap page=Bitmap.createBitmap(25,13,Bitmap.Config.ARGB_8888);page.eraseColor(Color.RED);d.setFrame(page);
        var canvas=new RecordingCanvas();d.draw(canvas);assertSame(page,canvas.frame);assertEquals(new RectF(0,0,100,50),canvas.imageRect);assertTrue(Color.alpha(canvas.tint)<255);
        android.graphics.Outline outline=new android.graphics.Outline();d.getOutline(outline);assertEquals(25f,outline.getRadius(),0);
        d.clear();assertFalse(d.hasFrame());d.setSurface(0xff202124);assertTrue(Color.alpha(d.tintColor())<255);
    }
    @Test public void themeChangesRetintExistingFrameWithoutWhiteResetOrGeometryChange(){
        var d=new ArcPhoneGlass.Backdrop();d.setBounds(0,0,100,50);
        Bitmap page=Bitmap.createBitmap(25,13,Bitmap.Config.ARGB_8888);page.eraseColor(Color.WHITE);d.setFrame(page);
        for(int color:new int[]{0xff202124,Color.WHITE,0xff202124,Color.WHITE}){
            d.setSurface(color);var canvas=new RecordingCanvas();d.draw(canvas);
            assertSame(page,canvas.frame);assertTrue(d.hasFrame());assertEquals(new RectF(0,0,100,50),canvas.imageRect);
            assertEquals(color&0xffffff,canvas.tint&0xffffff);assertTrue(Color.alpha(canvas.tint)<255);
            if(color!=Color.WHITE)assertTrue(Color.luminance(canvas.tint)<.05);
        }
    }
    private static class FakeCopy implements ArcPhoneGlass.Capture {
        int calls,closed;Consumer<Boolean> pending;
        public boolean available(){return true;}
        public void copy(Rect bounds,Bitmap output,Consumer<Boolean> done){calls++;output.eraseColor(Color.RED);pending=done;}
        public void close(){closed++;}
    }
    @Test public void hiddenMenuAndSuggestionTargetsDoNotDelayVisibleBarReadback() {
        var activity=Robolectric.buildActivity(Activity.class).setup();
        View hidden=new View(activity.get());
        View shown=new View(activity.get()){
            @Override public boolean isShown(){return true;}
            @Override public int getWindowVisibility(){return View.VISIBLE;}
        };
        activity.get().setContentView(shown);shown.layout(0,0,100,50);
        FakeCopy copy=new FakeCopy();var sampler=new ArcPhoneGlass(shown,copy);
        sampler.add(hidden,r->r.set(0,0,100,50));sampler.add(shown,r->r.set(0,0,100,50));
        sampler.setEnabled(true);sampler.sampleNow();assertEquals(1,copy.calls);
        copy.pending.accept(true);sampler.destroy();activity.pause().stop().destroy();
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
