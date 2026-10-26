// Copyright 2025 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package org.chromium.chrome.browser.media;

import static org.chromium.build.NullUtil.assumeNonNull;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.media.projection.MediaProjectionManager;

import androidx.activity.result.ActivityResult;
import androidx.fragment.app.FragmentActivity;

import org.chromium.base.ContextUtils;
import org.chromium.base.Log;
import org.chromium.base.ServiceLoaderUtil;
import org.chromium.build.annotations.NullMarked;
import org.chromium.chrome.browser.media.MediaCapturePickerHeadlessFragment.CaptureAction;
import org.chromium.chrome.browser.tab.Tab;
import org.chromium.content_public.browser.WebContents;
import org.chromium.content_public.browser.media.capture.ScreenCapture;

/** Media picker bridge, with the public Android consent flow for unbranded builds. */
@NullMarked
public class MediaCapturePickerInvoker {
    private static final String TAG = "MediaCapture";

    /**
     * Shows the new media capture picker UI.
     *
     * @param context The {@link Context} to use.
     * @param params The parameters for showing the media capture picker.
     * @param delegate The delegate to notify of the user's choice.
     */
    public static void show(
            Context context,
            MediaCapturePickerManager.Params params,
            MediaCapturePickerManager.Delegate delegate) {
        MediaCapturePickerDelegate impl =
                ServiceLoaderUtil.maybeCreate(MediaCapturePickerDelegate.class);
        if (impl != null) {
            Intent intent = impl.createScreenCaptureIntent(context, params, delegate);
            if (intent != null) {
                Activity activity = ContextUtils.activityFromContext(context);
                // We should always get a non-null ChromeActivity which is a FragmentActivity.
                // Crash here if this is not true for investigation.
                MediaCapturePickerHeadlessFragment fragment =
                        MediaCapturePickerHeadlessFragment.getInstance(
                                assumeNonNull((FragmentActivity) activity));
                Log.d(
                        TAG,
                        "PickerInvoker: Starting AndroidCapturePrompt for tab/ window/ screen"
                                + " sharing");
                fragment.startAndroidCapturePrompt(
                        (action, result) ->
                                onPickAndroidCapturePrompt(
                                        context,
                                        action,
                                        result,
                                        params.webContents,
                                        delegate,
                                        impl),
                        intent);
                return;
            }
            Log.e(TAG, "PickerInvoker: Failed to create ScreenCapture Intent, cancel request");
            // The delegate will record pre-show failure in createScreenCaptureIntent() before
            // returning null.
            delegate.onCancel();
            return;
        }
        showSystemPicker(context, params, delegate);
    }

    // The public Android chooser cannot filter individual browser tabs or guarantee
    // a window-only choice. Fail closed for enterprise/source restrictions instead
    // of silently offering a monitor forbidden by the request. excludeSelfBrowserSurface
    // filters browser tabs only; the system picker does not enumerate browser tabs.
    static boolean canUseSystemPicker(MediaCapturePickerManager.Params params) {
        return params.allowedCaptureLevel == AllowedScreenCaptureLevel.DESKTOP
                && !params.captureThisTab && !params.excludeMonitorTypeSurfaces;
    }

    private static void showSystemPicker(
            Context context, MediaCapturePickerManager.Params params,
            MediaCapturePickerManager.Delegate delegate) {
        Activity activity = ContextUtils.activityFromContext(context);
        MediaProjectionManager manager =
                (MediaProjectionManager) context.getSystemService(Context.MEDIA_PROJECTION_SERVICE);
        if (!(activity instanceof FragmentActivity fragmentActivity)
                || activity.isFinishing() || activity.isDestroyed() || manager == null
                || params.webContents.isDestroyed() || !canUseSystemPicker(params)) {
            delegate.onCancel();
            return;
        }
        try {
            MediaCapturePickerHeadlessFragment.getInstance(fragmentActivity)
                    .startAndroidCapturePrompt((action, result) -> {
                        if (!delegate.isActive()) return;
                        if (action == CaptureAction.CAPTURE_CANCELLED
                                || params.webContents.isDestroyed()) {
                            delegate.onCancel();
                            MediaCapturePickerManager.recordResult(
                                    MediaCapturePickerManager.Result.CANCELLED);
                            return;
                        }
                        // Pass the unmodified, single-use consent token to upstream.
                        // Android owns phone / DeX display / application selection.
                        // TYPE_WINDOW and TYPE_SCREEN both use DesktopCapturerAndroid;
                        // the public result does not expose which source was selected.
                        ScreenCapture.onPick(params.webContents, result);
                        delegate.onPickWindow();
                        MediaCapturePickerManager.recordResult(
                                MediaCapturePickerManager.Result.WINDOW_SELECTED);
                    }, manager.createScreenCaptureIntent());
        } catch (android.content.ActivityNotFoundException | IllegalStateException
                | SecurityException unavailable) {
            Log.e(TAG, "Cannot launch Android capture consent", unavailable);
            delegate.onCancel();
        }
    }

    private static void onPickAndroidCapturePrompt(
            Context context,
            @CaptureAction int action,
            ActivityResult result,
            WebContents webContents,
            MediaCapturePickerManager.Delegate delegate,
            MediaCapturePickerDelegate impl) {
        if (!delegate.isActive()) {
            impl.onFinish(webContents);
            return;
        }
        Log.d(TAG, "PickerInvoker: AndroidCapturePrompt received user action %d", action);
        if (action == CaptureAction.CAPTURE_CANCELLED) {
            delegate.onCancel();
            MediaCapturePickerManager.recordResult(MediaCapturePickerManager.Result.CANCELLED);
        } else {
            Tab tab = (action == CaptureAction.CAPTURE_WINDOW) ? impl.getPickedTab() : null;
            if (tab != null) {
                // User selected from app provided contents, i.e. a tab.
                Log.d(
                        TAG,
                        "PickerInvoker: Tab %d with title '%s' was picked",
                        tab.getId(),
                        tab.getTitle());
                tab.loadIfNeeded(/* forceBackingSize= */ true);
                WebContents pickedTabwebContents = tab.getWebContents();
                assert pickedTabwebContents != null;

                // Bring tab and its window to front. This is necessary for tabs belonging to a
                // minimized window, or sharing will not be able to start.
                // TODO(crbug.com/454192534): reconsider this behavior when the android system bug
                // is fixed to keep it consistent with desktop Chrome.
                MediaCapturePickerManager.bringTabToFront(context, tab);

                impl.startAppContentMediaProjection(webContents, result);

                Log.d(TAG, "PickerInvoker: call delegate.onPickTab");
                delegate.onPickTab(pickedTabwebContents, impl.shouldShareAudio());
                MediaCapturePickerManager.recordResult(
                        MediaCapturePickerManager.Result.TAB_SELECTED);
            } else {
                // User selected a window or screen.
                Log.d(TAG, "PickerInvoker: A window or screen was picked");
                // Detach any active tab projection session for this WebContents before starting
                // the new window/screen MediaProjection, so the old MediaProjection's onStop()
                // callback will not treat the replacement as a user-initiated stop.
                impl.stopAppContentMediaProjection(webContents);
                if (action == CaptureAction.CAPTURE_SCREEN) {
                    delegate.onPickScreen();
                    MediaCapturePickerManager.recordResult(
                            MediaCapturePickerManager.Result.SCREEN_SELECTED);
                } else {
                    ScreenCapture.onPick(webContents, result);
                    delegate.onPickWindow();
                    MediaCapturePickerManager.recordResult(
                            MediaCapturePickerManager.Result.WINDOW_SELECTED);
                }
            }
        }
        impl.onFinish(webContents);
    }
}
