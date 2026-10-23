// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.ColorFilter;
import android.graphics.Outline;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.drawable.Drawable;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;
import android.view.PixelCopy;
import android.view.SurfaceView;
import android.view.View;
import java.util.ArrayList;
import java.util.function.Consumer;
import java.util.function.Supplier;

/** Local, bounded backdrop sampling. Never captures the window, native controls or a whole page. */
public final class ArcPhoneGlass {
    public interface Capture {
        boolean available();
        void copy(Rect windowBounds, Bitmap output, Consumer<Boolean> result);
        void close();
    }
    public static final class Backdrop extends Drawable {
        private final Paint mPaint=new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG);
        private final Path mClip=new Path();
        private final RectF mRect=new RectF();
        private Bitmap mFrame;
        private int mTint=0x99ffffff;
        private int mAlpha=255;
        public void setSurface(int color){mTint=(color&0xffffff)|(Color.luminance(color)>.45?0x99000000:0xb3000000);invalidateSelf();}
        public void setFrame(Bitmap image){mFrame=image;invalidateSelf();}
        public void clear(){mFrame=null;invalidateSelf();}
        boolean hasFrame(){return mFrame!=null;}
        int tintColor(){return mTint;}
        @Override public void draw(Canvas canvas){
            mRect.set(getBounds());if(mRect.isEmpty())return;
            mClip.reset();mClip.addRoundRect(mRect,mRect.height()/2,mRect.height()/2,Path.Direction.CW);
            int save=canvas.save();canvas.clipPath(mClip);
            mPaint.setAlpha(mAlpha);
            if(mFrame!=null)canvas.drawBitmap(mFrame,null,mRect,mPaint);
            mPaint.setColor(mTint);mPaint.setAlpha(Color.alpha(mTint)*mAlpha/255);canvas.drawRect(mRect,mPaint);
            canvas.restoreToCount(save);
        }
        @Override public void getOutline(Outline outline){outline.setRoundRect(getBounds(),getBounds().height()/2f);outline.setAlpha(.12f);}
        @Override public void setAlpha(int alpha){mAlpha=alpha;invalidateSelf();}
        @Override public void setColorFilter(ColorFilter filter){mPaint.setColorFilter(filter);invalidateSelf();}
        @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
    }
    private static final class Target {
        final View view;final Consumer<Rect> bounds;final Backdrop backdrop=new Backdrop();
        Bitmap spare;
        Target(View view,Consumer<Rect> bounds){this.view=view;this.bounds=bounds;}
    }
    private final View mClock;
    private final Capture mCapture;
    private final ArrayList<Target> mTargets=new ArrayList<>();
    private final Runnable mTick=()->{sampleNow();schedule();};
    private boolean mEnabled,mDestroyed,mInFlight;
    private int mGeneration,mNext;
    private long mInterval=120;
    public ArcPhoneGlass(View clock,Capture capture){mClock=clock;mCapture=capture;}
    public Backdrop add(View view,Consumer<Rect> bounds){Target t=new Target(view,bounds);mTargets.add(t);return t.backdrop;}
    public void setInMotion(boolean moving){mInterval=moving?64:250;}
    public void setEnabled(boolean enabled){
        if(mDestroyed||mEnabled==enabled)return;mEnabled=enabled;
        if(!enabled){mClock.removeCallbacks(mTick);invalidateSource();mCapture.close();}else mClock.postOnAnimation(mTick);
    }
    public void invalidateSource(){mGeneration++;for(Target t:mTargets){t.backdrop.clear();t.spare=null;}}
    private void schedule(){mClock.removeCallbacks(mTick);if(mEnabled&&!mDestroyed)mClock.postDelayed(mTick,mInterval);}
    /** Package visible for deterministic state tests; GPU capture remains an explicit boundary. */
    void sampleNow(){
        if(!mEnabled||mDestroyed||mInFlight||mTargets.isEmpty())return;
        if(!mCapture.available()){invalidateSource();return;}
        Target target=mTargets.get(mNext);mNext=(mNext+1)%mTargets.size();
        if(!target.view.isShown()||target.view.getWindowVisibility()!=View.VISIBLE){target.backdrop.clear();return;}
        Rect bounds=new Rect();target.bounds.accept(bounds);if(bounds.isEmpty())return;
        int[] location=new int[2];target.view.getLocationInWindow(location);bounds.offset(location[0],location[1]);
        int[] size=copySize(bounds.width(),bounds.height());
        Bitmap output=target.spare;target.spare=null;
        if(output==null||output.getWidth()!=size[0]||output.getHeight()!=size[1])output=Bitmap.createBitmap(size[0],size[1],Bitmap.Config.ARGB_8888);
        final Bitmap pending=output;final int generation=mGeneration;mInFlight=true;
        mCapture.copy(bounds,pending,success->{
            mInFlight=false;
            if(mDestroyed||!mEnabled||generation!=mGeneration)return;
            Rect current=new Rect();target.bounds.accept(current);
            int[] now=new int[2];target.view.getLocationInWindow(now);current.offset(now[0],now[1]);
            if(!success||!bounds.equals(current)){target.backdrop.clear();target.spare=pending;return;}
            Bitmap old=target.backdrop.mFrame;target.backdrop.setFrame(pending);target.spare=old;target.view.invalidate();
        });
    }
    public void destroy(){if(mDestroyed)return;mEnabled=false;mDestroyed=true;mClock.removeCallbacks(mTick);invalidateSource();mCapture.close();mTargets.clear();}
    static int[] copySize(int width,int height){float scale=Math.max(4f,Math.max(width/256f,height/128f));return new int[]{Math.max(1,Math.round(width/scale)),Math.max(1,Math.round(height/scale))};}
    static void blur(Bitmap bitmap){int count=bitmap.getWidth()*bitmap.getHeight();blur(bitmap,new int[count],new int[count]);}
    private static void blur(Bitmap bitmap,int[] pixels,int[] pass){
        int w=bitmap.getWidth(),h=bitmap.getHeight();bitmap.getPixels(pixels,0,w,0,0,w,h);
        for(int axis=0;axis<2;axis++){
            int[] in=axis==0?pixels:pass,out=axis==0?pass:pixels;
            for(int y=0;y<h;y++)for(int x=0;x<w;x++){
                int a=0,r=0,g=0,b=0;
                for(int delta=-4;delta<=4;delta++){
                    int xx=axis==0?Math.max(0,Math.min(w-1,x+delta)):x;
                    int yy=axis==1?Math.max(0,Math.min(h-1,y+delta)):y;
                    int c=in[yy*w+xx];a+=Color.alpha(c);r+=Color.red(c);g+=Color.green(c);b+=Color.blue(c);
                }
                out[y*w+x]=Color.argb(a/9,r/9,g/9,b/9);
            }
        }
        bitmap.setPixels(pixels,0,w,0,0,w,h);
    }
    /** Captures only SurfaceView pixels. UI overlays never enter a recursive window capture. */
    public static Capture pixelSource(Supplier<SurfaceView> supplier){
        return new Capture(){
            final Handler main=new Handler(Looper.getMainLooper());
            HandlerThread thread;Handler worker;int[] pixels=new int[0],pass=new int[0];
            public boolean available(){SurfaceView v=supplier.get();return v!=null&&v.isShown()&&v.getHolder().getSurface().isValid();}
            public void copy(Rect windowBounds,Bitmap output,Consumer<Boolean> result){
                SurfaceView view=supplier.get();
                if(view==null||!available()){result.accept(false);return;}
                int[] position=new int[2];view.getLocationInWindow(position);Rect source=new Rect(windowBounds);source.offset(-position[0],-position[1]);
                if(!new Rect(0,0,view.getWidth(),view.getHeight()).contains(source)){result.accept(false);return;}
                if(worker==null){thread=new HandlerThread("ArchiumGlass");thread.start();worker=new Handler(thread.getLooper());}
                try{
                    PixelCopy.request(view,source,output,status->{
                        boolean success=status==PixelCopy.SUCCESS;
                        if(success){int count=output.getWidth()*output.getHeight();if(pixels.length<count){pixels=new int[count];pass=new int[count];}blur(output,pixels,pass);}
                        main.post(()->result.accept(success));
                    },worker);
                }catch(IllegalArgumentException error){result.accept(false);}
            }
            public void close(){if(thread!=null)thread.quitSafely();thread=null;worker=null;}
        };
    }
}
