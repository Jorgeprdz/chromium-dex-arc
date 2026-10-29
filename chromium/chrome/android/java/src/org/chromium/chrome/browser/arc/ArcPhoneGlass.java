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
import android.graphics.LinearGradient;
import android.graphics.Shader;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;
import android.view.View;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.function.Consumer;
import java.util.function.Supplier;

/** Local, bounded backdrop sampling. Never captures the window, native controls or a whole page. */
public final class ArcPhoneGlass {
    public interface Capture {
        boolean available();
        default Rect clip(Rect screenBounds){return new Rect(screenBounds);}
        void copy(Rect windowBounds, Bitmap output, Consumer<Boolean> result);
        void close();
    }
    public static final class Backdrop extends Drawable {
        private final Paint mPaint=new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG);
        private final Path mClip=new Path();
        private final RectF mRect=new RectF();
        private final RectF mEdgeRect=new RectF();
        private final RectF mFrameFraction=new RectF(0,0,1,1);
        private final RectF mFrameRect=new RectF();
        private final Paint mEdgePaint=new Paint(Paint.ANTI_ALIAS_FLAG);
        private boolean mEdgeEnabled;
        private float mCornerRadius=-1;
        private boolean mTopCornersOnly;
        private boolean mCustomCorners;
        private final float[] mCornerRadii=new float[8];
        private float mEdgeWidth=0.5f;
        private Bitmap mFrame;
        private int mTint=0xb3ffffff;
        private int mSurface=Color.WHITE;
        private boolean mMilky;
        private boolean mFloating;
        /** Phone finish on the same backdrop; neither adds a capture target nor paints a base. */
        public void setFloatingMaterial(float density){
            if(mFloating){if(!mEdgeEnabled||mEdgeWidth!=Math.max(.5f,.5f*density))setEdgeEnabled(true,density);return;}
            mFloating=true;mMilky=false;mSurfaceInitialized=false;
            mSheen=new Paint(Paint.ANTI_ALIAS_FLAG);
            setEdgeEnabled(true,density);setSurface(mSurface);
        }
        private boolean mSampleOnly;
        public void setSampleOnly(boolean sampleOnly){mSampleOnly=sampleOnly;invalidateSelf();}
        private boolean mDesktop;
        private Paint mSheen;
        private int mAlpha=255;
        private boolean mPaintReported;
        public void setSurface(int color){
            if(mSurface==color&&mSurfaceInitialized)return;
            mSurface=color;mSurfaceInitialized=true;
            double luminance=Color.luminance(color);
            // Mid-tone custom Spaces need an opaque fill to preserve Chromium's chosen foreground.
            int alpha=mDesktop&&luminance>=.10&&luminance<=.32?255:230;
            mTint=mFloating?(luminance>.45?0xd4ffffff:0xd9202124)
                    :mMilky?(color&0xffffff)|(alpha<<24):luminance>.45?0xb3ffffff:0xc4202124;
            updateSheen();invalidateSelf();
        }
        private boolean mSurfaceInitialized;
        public void setMilky(boolean milky){mMilky=milky;mSurfaceInitialized=false;setSurface(mSurface);}
        /** Dense desktop material; no full-window readback or wallpaper capture. */
        public void setDesktopMaterial(){mDesktop=true;setMilky(true);mSheen=new Paint(Paint.ANTI_ALIAS_FLAG);updateSheen();}
        int sheenColor(){double l=Color.luminance(mSurface);return (l+.05)/.05>=1.05/(l+.05)?0x12ffffff:0x12000000;}
        private void updateSheen(){if(mSheen!=null)mSheen.setShader(new LinearGradient(0,getBounds().top,0,
                Math.max(getBounds().top+1,getBounds().bottom),sheenColor(),sheenColor()&0xffffff,Shader.TileMode.CLAMP));}
        @Override protected void onBoundsChange(Rect bounds){updateSheen();}
        public void setCornerRadius(float radius){mCornerRadius=radius;mTopCornersOnly=false;mCustomCorners=false;invalidateSelf();}
        public void setTopCorners(float radius){mCornerRadius=radius;mTopCornersOnly=true;mCustomCorners=false;invalidateSelf();}
        public void setCornerRadii(float[] radii){System.arraycopy(radii,0,mCornerRadii,0,8);mCustomCorners=true;invalidateSelf();}
        public void setEdgeEnabled(boolean enabled,float density){mEdgeEnabled=enabled;mEdgeWidth=Math.max(.5f,.5f*density);invalidateSelf();}
        public void setFrame(Bitmap image){mFrame=image;mFrameFraction.set(0,0,1,1);invalidateSelf();}
        void setFrame(Bitmap image,Rect requested,Rect crop){
            mFrame=image;mFrameFraction.set((float)(crop.left-requested.left)/requested.width(),
                    (float)(crop.top-requested.top)/requested.height(),(float)(crop.right-requested.left)/requested.width(),
                    (float)(crop.bottom-requested.top)/requested.height());invalidateSelf();
        }
        public void clear(){mFrame=null;mPaintReported=false;invalidateSelf();}
        boolean hasFrame(){return mFrame!=null;}
        int tintColor(){return mTint;}
        @Override public void draw(Canvas canvas){
            mRect.set(getBounds());if(mRect.isEmpty())return;
            float radius=mCornerRadius<0?mRect.height()/2:Math.min(mCornerRadius,mRect.height()/2);
            mClip.reset();
            if(mCustomCorners)mClip.addRoundRect(mRect,mCornerRadii,Path.Direction.CW);
            else if(mTopCornersOnly){for(int i=0;i<8;i++)mCornerRadii[i]=i<4?radius:0;mClip.addRoundRect(mRect,mCornerRadii,Path.Direction.CW);}
            else mClip.addRoundRect(mRect,radius,radius,Path.Direction.CW);
            int save=canvas.save();canvas.clipPath(mClip);
            // A popup may straddle sidebar/native UI and the web capture. Paint the uncovered
            // region too: a partial frame must not let unblurred underlying labels bleed through.
            // The floating navigation/omnibar do not use the milky popup treatment.
            if(mMilky){mPaint.setColor(mSurface|0xff000000);mPaint.setAlpha(mAlpha);canvas.drawRect(mRect,mPaint);}
            mPaint.setAlpha(mAlpha);
            if(mFrame!=null){
                mFrameRect.set(mRect.left+mFrameFraction.left*mRect.width(),mRect.top+mFrameFraction.top*mRect.height(),
                        mRect.left+mFrameFraction.right*mRect.width(),mRect.top+mFrameFraction.bottom*mRect.height());
                canvas.drawBitmap(mFrame,null,mFrameRect,mPaint);
                if(!mPaintReported){android.util.Log.i("ArchiumGlass","painted frame bounds="+getBounds().toShortString());mPaintReported=true;}
            }
            if(!mSampleOnly){mPaint.setColor(mTint);mPaint.setAlpha((mMilky&&mFrame==null?255:Color.alpha(mTint))*mAlpha/255);canvas.drawRect(mRect,mPaint);}
            if(mSheen!=null){mSheen.setAlpha(mAlpha);canvas.drawPath(mClip,mSheen);}
            if(mEdgeEnabled){
                mEdgeRect.set(mRect);mEdgeRect.inset(mEdgeWidth/2,mEdgeWidth/2);
                mEdgePaint.setStyle(Paint.Style.STROKE);mEdgePaint.setStrokeWidth(mEdgeWidth);
                int edge=Color.luminance(mTint)>.45?0x241d2733:0x2cffffff;
                mEdgePaint.setColor(edge);mEdgePaint.setAlpha(Color.alpha(edge)*mAlpha/255);
                canvas.drawRoundRect(mEdgeRect,Math.max(0,radius-mEdgeWidth/2),Math.max(0,radius-mEdgeWidth/2),mEdgePaint);
            }
            canvas.restoreToCount(save);
        }
        @Override public void getOutline(Outline outline){outline.setRoundRect(getBounds(),mCornerRadius<0?getBounds().height()/2f:Math.min(mCornerRadius,getBounds().height()/2f));outline.setAlpha(.12f);}
        @Override public void setAlpha(int alpha){mAlpha=alpha;invalidateSelf();}
        @Override public void setColorFilter(ColorFilter filter){mPaint.setColorFilter(filter);invalidateSelf();}
        @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
    }
    private static final class Target {
        final View view;final Consumer<Rect> bounds;final Backdrop backdrop=new Backdrop();
        Bitmap spare;boolean copyReported;
        Target(View view,Consumer<Rect> bounds){this.view=view;this.bounds=bounds;}
    }
    private final IdentityHashMap<View, DecoratedSurface> mDecoratedSurfaces=new IdentityHashMap<>();
    private int mSurface=Color.WHITE;
    private int mSurfaceLayersTag;
    private boolean mDesktopMaterial;
    public void setDesktopMaterial(){mDesktopMaterial=true;for(DecoratedSurface surface:mDecoratedSurfaces.values())surface.backdrop.setDesktopMaterial();}
    public void setSurfaceLayersTag(int key){mSurfaceLayersTag=key;}
    private static final class SurfaceLayer {
        final View view;final Drawable original;final int left,top,right,bottom;
        SurfaceLayer(View target){view=target;original=target.getBackground();left=target.getPaddingLeft();top=target.getPaddingTop();right=target.getPaddingRight();bottom=target.getPaddingBottom();}
        void apply(boolean glass){view.setBackground(glass?null:original);view.setPadding(left,top,right,bottom);}
    }
    private final class DecoratedSurface {
        final View view;
        final Drawable original;
        final Backdrop backdrop;
        final int left,top,right,bottom;
        final ArrayList<SurfaceLayer> layers=new ArrayList<>();
        DecoratedSurface(View target){
            view=target;original=target.getBackground();
            left=target.getPaddingLeft();top=target.getPaddingTop();right=target.getPaddingRight();bottom=target.getPaddingBottom();
            Object nativeLayers=mSurfaceLayersTag==0?null:target.getTag(mSurfaceLayersTag);
            if(nativeLayers instanceof View[] views)for(View layer:views)if(layer!=null&&layer!=target)layers.add(new SurfaceLayer(layer));
            backdrop=add(target,target::getDrawingRect);
            float radius=16*target.getResources().getDisplayMetrics().density;
            if(original!=null){Outline outline=new Outline();original.getOutline(outline);if(outline.getRadius()>=0)radius=outline.getRadius();}
            backdrop.setCornerRadius(radius);
            if(original instanceof GradientDrawable shape){float[] radii=shape.getCornerRadii();if(radii!=null)backdrop.setCornerRadii(radii);}
            if(mDesktopMaterial)backdrop.setDesktopMaterial();else backdrop.setMilky(true);backdrop.setSurface(mSurface);
        }
        void apply(){view.setBackground(mEnabled?backdrop:original);view.setPadding(left,top,right,bottom);for(SurfaceLayer layer:layers)layer.apply(mEnabled);}
        void restore(){view.setBackground(original);view.setPadding(left,top,right,bottom);for(SurfaceLayer layer:layers)layer.apply(false);}
    }
    private final View.OnAttachStateChangeListener mSurfaceDecorator=new View.OnAttachStateChangeListener(){
        @Override public void onViewAttachedToWindow(View view){
            if(mDestroyed||mDecoratedSurfaces.containsKey(view))return;
            DecoratedSurface surface=new DecoratedSurface(view);mDecoratedSurfaces.put(view,surface);surface.apply();
        }
        @Override public void onViewDetachedFromWindow(View view){
            DecoratedSurface surface=mDecoratedSurfaces.remove(view);
            if(surface!=null){surface.restore();remove(surface.backdrop);}
            view.removeOnAttachStateChangeListener(this);
        }
    };
    public View.OnAttachStateChangeListener getSurfaceDecorator(){return mSurfaceDecorator;}
    public void setSurface(int color){mSurface=color;for(DecoratedSurface s:mDecoratedSurfaces.values())s.backdrop.setSurface(color);}
    private final View mClock;
    private final Capture mCapture;
    private final ArrayList<Target> mTargets=new ArrayList<>();
    private final Runnable mTick=()->{sampleNow();schedule();};
    private boolean mEnabled,mDestroyed,mInFlight;
    private int mGeneration,mNext;
    private long mInterval=120;
    public ArcPhoneGlass(View clock,Capture capture){mClock=clock;mCapture=capture;}
    public Backdrop add(View view,Consumer<Rect> bounds){Target t=new Target(view,bounds);mTargets.add(t);return t.backdrop;}
    public void remove(Backdrop backdrop){
        mTargets.removeIf(t->{if(t.backdrop!=backdrop)return false;t.backdrop.clear();t.spare=null;return true;});
        mNext=0;
    }
    public void setInMotion(boolean moving){mInterval=moving?64:250;}
    public void setEnabled(boolean enabled){
        if(mDestroyed||mEnabled==enabled)return;mEnabled=enabled;
        for(DecoratedSurface surface:mDecoratedSurfaces.values())surface.apply();
        if(!enabled){mClock.removeCallbacks(mTick);invalidateSource();mCapture.close();}else mClock.postOnAnimation(mTick);
    }
    public void invalidateSource(){mGeneration++;for(Target t:mTargets){t.backdrop.clear();t.spare=null;t.copyReported=false;}}
    private void schedule(){mClock.removeCallbacks(mTick);if(mEnabled&&!mDestroyed)mClock.postDelayed(mTick,mInterval);}
    private Target nextVisibleTarget(){
        for(int tries=0;tries<mTargets.size();tries++){
            Target target=mTargets.get(mNext);mNext=(mNext+1)%mTargets.size();
            if(target.view.isShown()&&target.view.getWindowVisibility()==View.VISIBLE)return target;
            target.backdrop.clear();
        }
        return null;
    }
    private static final class SampleRegion {
        final Rect requested,local,screen;
        SampleRegion(Rect requested,Rect local,Rect screen){this.requested=requested;this.local=local;this.screen=screen;}
        boolean same(SampleRegion other){return other!=null&&requested.equals(other.requested)&&local.equals(other.local)&&screen.equals(other.screen);}
    }
    private SampleRegion sampleRegion(Target target){
        Rect requested=new Rect();target.bounds.accept(requested);if(requested.isEmpty())return null;
        Rect visible=new Rect();if(!target.view.getLocalVisibleRect(visible)||!visible.intersect(requested))return null;
        int[] location=new int[2];target.view.getLocationOnScreen(location);
        Rect screen=new Rect(visible);screen.offset(location[0],location[1]);screen=mCapture.clip(screen);
        if(screen==null||screen.isEmpty())return null;
        Rect local=new Rect(screen);local.offset(-location[0],-location[1]);
        return new SampleRegion(requested,local,screen);
    }
    /** Package visible for deterministic state tests; GPU capture remains an explicit boundary. */
    void sampleNow(){
        if(!mEnabled||mDestroyed||mInFlight||mTargets.isEmpty())return;
        if(!mCapture.available()){invalidateSource();mCapture.close();return;}
        Target target=nextVisibleTarget();if(target==null)return;
        SampleRegion region=sampleRegion(target);if(region==null){target.backdrop.clear();return;}
        int[] size=copySize(region.screen.width(),region.screen.height());
        Bitmap output=target.spare;target.spare=null;
        if(output==null||output.getWidth()!=size[0]||output.getHeight()!=size[1])output=Bitmap.createBitmap(size[0],size[1],Bitmap.Config.ARGB_8888);
        final Bitmap pending=output;final int generation=mGeneration;mInFlight=true;
        mCapture.copy(region.screen,pending,success->{
            mInFlight=false;
            if(mDestroyed||!mEnabled||generation!=mGeneration||!mTargets.contains(target))return;
            if(!target.copyReported){
                android.util.Log.i("ArchiumGlass","copy success="+success+" sample="+pending.getWidth()+"x"+pending.getHeight());target.copyReported=true;
            }
            if(!success||!region.same(sampleRegion(target))){target.backdrop.clear();target.spare=pending;return;}
            Bitmap old=target.backdrop.mFrame;target.backdrop.setFrame(pending,region.requested,region.local);target.spare=old;target.view.invalidate();
        });
    }
    public void destroy(){if(mDestroyed)return;mEnabled=false;mDestroyed=true;mClock.removeCallbacks(mTick);invalidateSource();mCapture.close();
        for(DecoratedSurface surface:mDecoratedSurfaces.values()){
            surface.restore();surface.view.removeOnAttachStateChangeListener(mSurfaceDecorator);
        }
        mDecoratedSurfaces.clear();mTargets.clear();}
    static int[] copySize(int width,int height){float scale=Math.max(4f,Math.max(width/256f,height/128f));return new int[]{Math.max(1,Math.round(width/scale)),Math.max(1,Math.round(height/scale))};}
    static void blur(Bitmap bitmap){int count=bitmap.getWidth()*bitmap.getHeight();blur(bitmap,new int[count],new int[count]);}
    private static void blur(Bitmap bitmap,int[] pixels,int[] pass){
        int w=bitmap.getWidth(),h=bitmap.getHeight();bitmap.getPixels(pixels,0,w,0,0,w,h);
        // Three sliding box passes approximate a soft Gaussian without larger captures or buffers.
        final int radius=6,divisor=2*radius+1;
        for(int iteration=0;iteration<3;iteration++)for(int axis=0;axis<2;axis++){
            int[] in=axis==0?pixels:pass,out=axis==0?pass:pixels;
            int length=axis==0?w:h,lines=axis==0?h:w,stride=axis==0?1:w;
            for(int line=0;line<lines;line++){
                int first=axis==0?line*w:line,a=0,r=0,g=0,b=0;
                for(int delta=-radius;delta<=radius;delta++){
                    int c=in[first+Math.max(0,Math.min(length-1,delta))*stride];
                    a+=Color.alpha(c);r+=Color.red(c);g+=Color.green(c);b+=Color.blue(c);
                }
                for(int position=0;position<length;position++){
                    out[first+position*stride]=Color.argb(a/divisor,r/divisor,g/divisor,b/divisor);
                    int remove=in[first+Math.max(0,position-radius)*stride];
                    int add=in[first+Math.min(length-1,position+radius+1)*stride];
                    a+=Color.alpha(add)-Color.alpha(remove);r+=Color.red(add)-Color.red(remove);
                    g+=Color.green(add)-Color.green(remove);b+=Color.blue(add)-Color.blue(remove);
                }
            }
        }
        bitmap.setPixels(pixels,0,w,0,0,w,h);
    }
    @FunctionalInterface
    public interface RegionCopy {
        void copy(Rect region, int width, int height, Consumer<Bitmap> callback);
    }
    static Rect contentRegion(View content, Rect windowBounds) {
        if(content==null||windowBounds.isEmpty())return null;
        int[] origin=new int[2];content.getLocationOnScreen(origin);
        Rect region=new Rect(windowBounds);region.offset(-origin[0],-origin[1]);
        return new Rect(0,0,content.getWidth(),content.getHeight()).contains(region)?region:null;
    }
    /** Read the web compositor region, never the window or the empty SurfaceView proxy. */
    public static Capture contentSource(Supplier<View> supplier, RegionCopy readback){
        return new Capture(){
            final Handler main=new Handler(Looper.getMainLooper());
            HandlerThread thread;Handler worker;int epoch;int[] pixels=new int[0],pass=new int[0];
            public boolean available(){View v=supplier.get();return v!=null&&v.isShown()&&v.getWindowVisibility()==View.VISIBLE;}
            public Rect clip(Rect screenBounds){
                View view=supplier.get();if(view==null||view.getWidth()<=0||view.getHeight()<=0)return null;
                int[] origin=new int[2];view.getLocationOnScreen(origin);
                Rect result=new Rect(screenBounds);return result.intersect(origin[0],origin[1],origin[0]+view.getWidth(),origin[1]+view.getHeight())?result:null;
            }
            public void copy(Rect windowBounds,Bitmap output,Consumer<Boolean> result){
                View view=supplier.get();Rect region=contentRegion(view,windowBounds);
                if(region==null||!available()){result.accept(false);return;}
                final int generation=epoch;
                readback.copy(region,output.getWidth(),output.getHeight(),bitmap->{
                    if(bitmap==null||generation!=epoch||supplier.get()!=view||!available()){result.accept(false);return;}
                    if(worker==null){thread=new HandlerThread("ArchiumGlass");thread.start();worker=new Handler(thread.getLooper());}
                    worker.post(()->{
                        new Canvas(output).drawBitmap(bitmap,null,new Rect(0,0,output.getWidth(),output.getHeight()),null);
                        int count=output.getWidth()*output.getHeight();
                        if(pixels.length<count){pixels=new int[count];pass=new int[count];}
                        blur(output,pixels,pass);
                        main.post(()->result.accept(generation==epoch&&supplier.get()==view&&available()));
                    });
                });
            }
            public void close(){epoch++;if(thread!=null)thread.quitSafely();thread=null;worker=null;}
        };
    }
}
