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
        private ImportRow(int index, int kind, String url, String username) {
            this.index = index; this.kind = kind; this.url = url; this.username = username;
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

    private long mNativePtr;
    private boolean mStarted;
    private @Nullable Listener mListener;
    private final List<Entry> mEntries = new ArrayList<>();
    private final Map<Integer, List<ArchiumPasswordCsv.SecretRow>> mExports = new HashMap<>();
    private final Map<Integer, List<ImportRow>> mPreviews = new HashMap<>();

    public ArchiumPasswordManagerBridge(Activity activity, Profile profile, Listener listener) {
        mListener = listener;
        mNativePtr = ArchiumPasswordManagerBridgeJni.get().init(this, profile, activity);
    }

    public static boolean isLocalEnabled() {
        return ArchiumPasswordManagerBridgeJni.get().isLocalEnabled();
    }
    public void start() {
        if (mStarted || mListener == null) return;
        mStarted = true;
        if (mNativePtr == 0) mListener.onMetadata(List.of(), UNAVAILABLE);
        else refresh();
    }
    private boolean active() { return mStarted && mNativePtr != 0 && mListener != null; }
    public void refresh() { if (active()) ArchiumPasswordManagerBridgeJni.get().refresh(mNativePtr); }
    public void reveal(int request, long id) {
        if (active()) ArchiumPasswordManagerBridgeJni.get().reveal(mNativePtr, request, id);
    }
    public void export(int request) {
        if (active()) ArchiumPasswordManagerBridgeJni.get().export(mNativePtr, request);
    }
    /** Input password buffers are consumed/erased, including cancellation or a JNI exception. */
    public void previewImport(int request, String[] urls, String[] users, char[][] passwords) {
        try {
            if (active()) ArchiumPasswordManagerBridgeJni.get().previewImport(mNativePtr, request, urls, users, passwords);
        } finally {
            for (char[] password : passwords) if (password != null) Arrays.fill(password, '\0');
        }
    }
    public void confirmImport(int request, int[] decisions) {
        if (active()) ArchiumPasswordManagerBridgeJni.get().confirmImport(mNativePtr, request, decisions);
    }
    public void cancelImport() {
        if (active()) ArchiumPasswordManagerBridgeJni.get().cancelImport(mNativePtr);
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
    @CalledByNative private void onPreviewRow(int request, int index, int kind,
            @JniType("std::string") String url, @JniType("std::u16string") String username) {
        List<ImportRow> rows = mPreviews.get(request);
        if (rows != null && mListener != null) rows.add(new ImportRow(index, kind, url, username));
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
        long pointer = mNativePtr;
        mNativePtr = 0;
        if (pointer != 0) ArchiumPasswordManagerBridgeJni.get().destroy(pointer);
    }

    @NativeMethods public interface Natives {
        boolean isLocalEnabled();
        long init(ArchiumPasswordManagerBridge bridge, @JniType("Profile*") Profile profile, Activity activity);
        void refresh(long nativeArchiumPasswordManagerBridge);
        void reveal(long nativeArchiumPasswordManagerBridge, int request, long id);
        void export(long nativeArchiumPasswordManagerBridge, int request);
        void previewImport(long nativeArchiumPasswordManagerBridge, int request, String[] urls, String[] users, char[][] passwords);
        void confirmImport(long nativeArchiumPasswordManagerBridge, int request, int[] decisions);
        void cancelImport(long nativeArchiumPasswordManagerBridge);
        void destroy(long nativeArchiumPasswordManagerBridge);
    }
}
