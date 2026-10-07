// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.password_manager;

import android.app.Activity;

import org.jni_zero.CalledByNative;
import org.jni_zero.JniType;
import org.jni_zero.NativeMethods;
import org.chromium.build.annotations.NullMarked;
import org.chromium.build.annotations.Nullable;
import org.chromium.chrome.browser.profiles.Profile;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Local native manager transport. It cannot provide an authentication-success boolean. */
@NullMarked
public final class ArchiumPasswordManagerBridge {
    public static final int SUCCESS = 0;
    public static final int UNAVAILABLE = 1;
    public static final int AUTHENTICATION_FAILED = 2;
    public static final int BUSY = 3;
    public static final int STALE = 4;
    public static final int INVALID = 5;
    public static final int WRITE_FAILED = 6;

    public static final class Entry {
        public final long id;
        public final String url;
        public final String username;
        private Entry(long id, String url, String username) {
            this.id = id; this.url = url; this.username = username;
        }
    }
    public static final class ImportRow {
        public final int index;
        public final int kind;
        public final String url;
        public final String username;
        /** Canonical sign-on realm computed by native Chromium. */
        public final String identity;
        /** Only non-skip decision accepted by the native preview for this row. */
        public final int requiredDecision;
        private ImportRow(
                int index,
                int kind,
                String url,
                String username,
                String identity,
                int requiredDecision) {
            this.index = index;
            this.kind = kind;
            this.url = url;
            this.username = username;
            this.identity = identity;
            this.requiredDecision = requiredDecision;
        }
    }
    public interface Listener {
        void onMetadata(List<Entry> entries, int status);
        /** Buffer is borrowed for this synchronous callback and erased immediately afterwards. */
        void onSecret(int request, int status, char[] password);
        /** Successful export transfers ownership; consumer must close every row in finally. */
        void onExport(int request, int status, List<ArchiumPasswordCsv.SecretRow> rows);
        void onPreview(int request, int status, List<ImportRow> rows);
        void onOperation(int request, int status);
    }

    private long mNativeHandle;
    private boolean mStarted;
    private @Nullable Listener mListener;
    private final List<Entry> mEntries = new ArrayList<>();
    private final Map<Integer, List<ArchiumPasswordCsv.SecretRow>> mExports = new HashMap<>();
    private final Map<Integer, List<ImportRow>> mPreviews = new HashMap<>();

    public ArchiumPasswordManagerBridge(Activity activity, Profile profile, Listener listener) {
        mListener = listener;
        // Defense in depth: do not create a JNI peer from any off-the-record
        // context; native Init independently repeats the real profile check.
        if (profile == null || profile.isOffTheRecord()) return;
        mNativeHandle = ArchiumPasswordManagerBridgeJni.get().init(this, profile, activity);
    }

    public static boolean isLocalEnabled() {
        return ArchiumPasswordManagerBridgeJni.get().isLocalEnabled();
    }
    public void start() {
        if (mStarted || mListener == null) return;
        mStarted = true;
        if (mNativeHandle == 0) mListener.onMetadata(List.of(), UNAVAILABLE);
        else refresh();
    }
    private boolean active() { return mStarted && mNativeHandle != 0 && mListener != null; }
    public void refresh() { if (active()) ArchiumPasswordManagerBridgeJni.get().refresh(mNativeHandle); }
    /** Password input is consumed and erased after the native call returns. */
    public void add(int request, String url, String username, char[] password) {
        try {
            if (active()) {
                ArchiumPasswordManagerBridgeJni.get().add(
                        mNativeHandle, request, url, username, password);
            }
        } finally {
            Arrays.fill(password, '\0');
        }
    }
    /** Password input is consumed and erased after the native call returns. */
    public void update(int request, long id, String username, char[] password) {
        try {
            if (active()) {
                ArchiumPasswordManagerBridgeJni.get().update(
                        mNativeHandle, request, id, username, password);
            }
        } finally {
            Arrays.fill(password, '\0');
        }
    }
    public void delete(int request, long id) {
        if (active()) ArchiumPasswordManagerBridgeJni.get().delete(mNativeHandle, request, id);
    }
    public void reveal(int request, long id) {
        if (active()) ArchiumPasswordManagerBridgeJni.get().reveal(mNativeHandle, request, id);
    }
    public void export(int request) {
        if (active()) ArchiumPasswordManagerBridgeJni.get().export(mNativeHandle, request);
    }
    /** Input password buffers are consumed/erased, including cancellation or a JNI exception. */
    public void previewImport(int request, String[] urls, String[] users, char[][] passwords) {
        try {
            if (active()) ArchiumPasswordManagerBridgeJni.get().previewImport(mNativeHandle, request, urls, users, passwords);
        } finally {
            for (char[] password : passwords) if (password != null) Arrays.fill(password, '\0');
        }
    }
    public void confirmImport(int request, int[] decisions) {
        if (active()) ArchiumPasswordManagerBridgeJni.get().confirmImport(mNativeHandle, request, decisions);
    }
    public void cancelImport() {
        if (active()) ArchiumPasswordManagerBridgeJni.get().cancelImport(mNativeHandle);
        mPreviews.clear();
    }

    @CalledByNative private void onListStart() { mEntries.clear(); }
    @CalledByNative private void onEntry(long id, @JniType("std::string") String url,
            @JniType("std::u16string") String username) {
        if (mListener != null) mEntries.add(new Entry(id, url, username));
    }
    @CalledByNative private void onListEnd(int status) {
        if (mStarted && mListener != null) mListener.onMetadata(List.copyOf(mEntries), status);
    }
    @CalledByNative private void onSecret(int request, int status, @Nullable char[] password) {
        char[] buffer = password == null ? new char[0] : password;
        try {
            if (mStarted && mListener != null) mListener.onSecret(request, status, buffer);
        } finally { Arrays.fill(buffer, '\0'); }
    }
    @CalledByNative private void onExportStart(int request) {
        closeRows(mExports.remove(request));
        if (mListener != null) mExports.put(request, new ArrayList<>());
    }
    @CalledByNative private void onExportRow(int request, @JniType("std::string") String url,
            @JniType("std::u16string") String username, char[] password) {
        try {
            List<ArchiumPasswordCsv.SecretRow> rows = mExports.get(request);
            if (rows != null && mListener != null) rows.add(new ArchiumPasswordCsv.SecretRow(url, username, password));
        } finally { Arrays.fill(password, '\0'); }
    }
    @CalledByNative private void onExportEnd(int request, int status) {
        List<ArchiumPasswordCsv.SecretRow> rows = mExports.remove(request);
        boolean transferred = false;
        try {
            if (status != SUCCESS) { closeRows(rows); rows = null; }
            if (mStarted && mListener != null) {
                mListener.onExport(request, status, rows == null ? List.of() : List.copyOf(rows));
                transferred = true;
            }
        } finally { if (!transferred) closeRows(rows); }
    }
    @CalledByNative private void onPreviewStart(int request) {
        if (mListener != null) mPreviews.put(request, new ArrayList<>());
    }
    @CalledByNative private void onPreviewRow(
            int request,
            int index,
            int kind,
            @JniType("std::string") String url,
            @JniType("std::u16string") String username,
            @JniType("std::string") String identity,
            int requiredDecision) {
        List<ImportRow> rows = mPreviews.get(request);
        if (rows != null && mListener != null) {
            rows.add(new ImportRow(
                    index, kind, url, username, identity, requiredDecision));
        }
    }
    @CalledByNative private void onPreviewEnd(int request, int status) {
        List<ImportRow> rows = mPreviews.remove(request);
        if (mStarted && mListener != null) mListener.onPreview(request, status, rows == null ? List.of() : List.copyOf(rows));
    }
    @CalledByNative private void onOperation(int request, int status) {
        if (mStarted && mListener != null) mListener.onOperation(request, status);
    }

    private static void closeRows(@Nullable List<ArchiumPasswordCsv.SecretRow> rows) {
        if (rows != null) for (ArchiumPasswordCsv.SecretRow row : rows) row.close();
    }
    public void destroy() {
        mStarted = false;
        mListener = null;
        mEntries.clear();
        mPreviews.clear();
        for (List<ArchiumPasswordCsv.SecretRow> rows : mExports.values()) closeRows(rows);
        mExports.clear();
        long handle = mNativeHandle;
        mNativeHandle = 0;
        if (handle != 0) ArchiumPasswordManagerBridgeJni.get().destroy(handle);
    }

    @NativeMethods public interface Natives {
        boolean isLocalEnabled();
        long init(ArchiumPasswordManagerBridge bridge, @JniType("Profile*") Profile profile, Activity activity);
        void refresh(long handle);
        void add(long handle, int request, String url,
                String username, char[] password);
        void update(long handle, int request, long id,
                String username, char[] password);
        void delete(long handle, int request, long id);
        void reveal(long handle, int request, long id);
        void export(long handle, int request);
        void previewImport(long handle, int request, String[] urls, String[] users, char[][] passwords);
        void confirmImport(long handle, int request, int[] decisions);
        void cancelImport(long handle);
        void destroy(long handle);
    }
}
