// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.app.Activity;
import java.lang.ref.WeakReference;
import java.util.WeakHashMap;
import java.util.function.BooleanSupplier;
import org.chromium.chrome.browser.tab.Tab;
import org.chromium.content_public.browser.LoadUrlParams;
import org.chromium.content_public.browser.WebContents;
import org.chromium.url.GURL;
import org.chromium.content_public.common.ResourceRequestBody;

/** UI-thread routing by exact source window; neither activities nor coordinators are retained. */
public final class ArcSplitLinkRouter {
    private static final WeakHashMap<Activity,WeakReference<ArcSplitViewCoordinator>> WINDOWS = new WeakHashMap<>();
    private ArcSplitLinkRouter() {}
    static void register(Activity activity, ArcSplitViewCoordinator controller) {
        WINDOWS.put(activity,new WeakReference<>(controller));
    }
    static void unregister(Activity activity, ArcSplitViewCoordinator controller) {
        WeakReference<ArcSplitViewCoordinator> value=WINDOWS.get(activity);
        if(value!=null && value.get()==controller)WINDOWS.remove(activity);
    }
    private static ArcSplitViewCoordinator controller(Tab tab) {
        if(tab==null || tab.isDestroyed() || tab.getWindowAndroid()==null)return null;
        Activity activity=tab.getWindowAndroid().getActivity().get();
        if(activity==null || activity.isFinishing() || activity.isDestroyed())return null;
        WeakReference<ArcSplitViewCoordinator> value=WINDOWS.get(activity);
        return value==null?null:value.get();
    }
    public static boolean isWebLink(GURL url) {
        return url!=null && url.isValid() && ("https".equals(url.getScheme()) || "http".equals(url.getScheme()));
    }
    public static boolean canOpen(Tab source,GURL url) {
        ArcSplitViewCoordinator controller=controller(source);
        return isWebLink(url) && controller!=null && controller.canOpenLink(source);
    }
    public static boolean open(Tab source,LoadUrlParams params) {
        ArcSplitViewCoordinator controller=controller(source);
        return params!=null && controller!=null && controller.openLink(source,params);
    }
    public static boolean openNative(Tab source,GURL url,String headers,ResourceRequestBody body,boolean renderer) {
        if(!canOpen(source,url))return false;
        LoadUrlParams params=new LoadUrlParams(url.getSpec());
        params.setVerbatimHeaders(headers);
        if(body!=null)params.setPostData(body);
        params.setIsRendererInitiated(renderer);params.setHasUserGesture(true);
        return open(source,params);
    }
    /** Keep the renderer-created WebContents and all opener/request metadata under native ownership. */
    public static boolean create(Tab source,GURL url,WebContents contents,BooleanSupplier create) {
        ArcSplitViewCoordinator controller=controller(source);
        if(!isWebLink(url) || controller==null || !controller.canOpenLink(source))return create.getAsBoolean();
        return controller.adoptLink(source,contents,create);
    }
}
