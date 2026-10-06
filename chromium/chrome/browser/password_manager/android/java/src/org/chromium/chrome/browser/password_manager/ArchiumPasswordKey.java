// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.password_manager;

import android.content.Context;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.AtomicFile;
import android.system.ErrnoException;
import android.system.Os;
import android.system.OsConstants;

import java.io.File;
import java.io.FileOutputStream;
import java.io.FileDescriptor;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.channels.FileLock;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.KeyStore;
import java.security.SecureRandom;
import java.util.Arrays;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** Persistent data key protected by a nonexportable Android Keystore wrapping key. */
public final class ArchiumPasswordKey {
    private static final String ALIAS = "archium.passwords.wrap.v1";
    private static final String RECORD = "archium-password-key-v1";
    private static final int MAGIC = 0x41505731; // APW1
    private static final int DATA_KEY_BYTES = 32;
    private static final int NONCE_BYTES = 12;
    private static final int TAG_BYTES = 16;
    private static final int RECORD_BYTES = 4 + NONCE_BYTES + DATA_KEY_BYTES + TAG_BYTES;

    private ArchiumPasswordKey() {}

    /**
     * Runs on a worker thread. Errors are surfaced to the caller; existing invalid state is never
     * replaced. The caller must not fall back to a fresh or less protected key after failure.
     */
    public static synchronized byte[] getOrCreateDataKey(Context context)
            throws GeneralSecurityException, IOException {
        File directory = context.getNoBackupFilesDir();
        if (directory == null || !directory.isDirectory()) {
            throw new IOException("Password key storage unavailable");
        }
        // Serialize initialization across browser processes as well as threads. Renderers should
        // receive the native Encryptor over IPC and must not initialize a key themselves.
        try (RandomAccessFile lockFile = new RandomAccessFile(new File(directory, RECORD + ".lock"), "rw");
                FileLock lock = lockFile.getChannel().lock()) {
            return loadOrCreate(context, new File(directory, RECORD));
        }
    }

    private static byte[] loadOrCreate(Context context, File file)
            throws GeneralSecurityException, IOException {
        KeyStore keystore = KeyStore.getInstance("AndroidKeyStore");
        keystore.load(null);
        AtomicFile storage = new AtomicFile(file);
        byte[] aad = (context.getPackageName() + "|archium-password-key|v1")
                .getBytes(StandardCharsets.UTF_8);
        boolean recordExists = file.exists() || new File(file.getPath() + ".bak").exists();
        boolean keyExists = keystore.containsAlias(ALIAS);
        if (recordExists) {
            if (!keyExists) throw new GeneralSecurityException("Password wrapping key unavailable");
            byte[] record = storage.readFully();
            if (record.length != RECORD_BYTES || ByteBuffer.wrap(record).getInt() != MAGIC) {
                throw new GeneralSecurityException("Invalid wrapped password key record");
            }
            SecretKey kek = (SecretKey) keystore.getKey(ALIAS, null);
            if (kek == null) throw new GeneralSecurityException("Password wrapping key unavailable");
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.DECRYPT_MODE, kek,
                    new GCMParameterSpec(128, record, 4, NONCE_BYTES));
            cipher.updateAAD(aad);
            byte[] dataKey = cipher.doFinal(record, 4 + NONCE_BYTES,
                    DATA_KEY_BYTES + TAG_BYTES);
            if (dataKey.length != DATA_KEY_BYTES) {
                Arrays.fill(dataKey, (byte) 0);
                throw new GeneralSecurityException("Invalid password data key");
            }
            return dataKey;
        }
        // A missing record with an existing KEK may mean data was lost. Do not create a new DEK
        // that would render existing passwords undecryptable or hide the loss from the user.
        if (keyExists) throw new GeneralSecurityException("Wrapped password key unavailable");
        KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,
                "AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(ALIAS,
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setKeySize(256)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .setUnlockedDeviceRequired(true)
                .build());
        SecretKey kek = generator.generateKey();
        byte[] dataKey = new byte[DATA_KEY_BYTES];
        new SecureRandom().nextBytes(dataKey);
        try {
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.ENCRYPT_MODE, kek);
            cipher.updateAAD(aad);
            byte[] encrypted = cipher.doFinal(dataKey);
            byte[] nonce = cipher.getIV();
            if (nonce.length != NONCE_BYTES || encrypted.length != DATA_KEY_BYTES + TAG_BYTES) {
                throw new GeneralSecurityException("Unsupported password wrapping parameters");
            }
            byte[] record = ByteBuffer.allocate(RECORD_BYTES).putInt(MAGIC)
                    .put(nonce).put(encrypted).array();
            writeWrappedRecord(storage, record);
            return dataKey;
        } catch (IOException | GeneralSecurityException | RuntimeException exception) {
            Arrays.fill(dataKey, (byte) 0);
            // Keep the KEK/state for explicit recovery. Automatic replacement would conceal
            // a failed key initialization and risks losing already encrypted data.
            throw exception;
        }
    }

    private static void writeWrappedRecord(AtomicFile storage, byte[] record) throws IOException {
        FileOutputStream output = null;
        try {
            output = storage.startWrite();
            output.write(record);
            // AtomicFile.finishWrite() logs some sync/rename errors without throwing.
            // Explicitly flush the file and verify the committed record before vending a DEK.
            output.getFD().sync();
            storage.finishWrite(output);
            output = null;
            if (!Arrays.equals(record, storage.readFully())) {
                throw new IOException("Password key record was not committed");
            }
            File directory = storage.getBaseFile().getParentFile();
            if (directory == null) throw new IOException("Password key directory unavailable");
            FileDescriptor descriptor = null;
            try {
                descriptor = Os.open(directory.getAbsolutePath(),
                        OsConstants.O_RDONLY, 0);
                if (!OsConstants.S_ISDIR(Os.fstat(descriptor).st_mode)) {
                    throw new IOException("Password key storage is not a directory");
                }
                Os.fsync(descriptor);  // Persist the rename, not just the contents of .new.
            } catch (ErrnoException error) {
                throw new IOException("Password key directory commit failed", error);
            } finally {
                if (descriptor != null) {
                    try { Os.close(descriptor); }
                    catch (ErrnoException error) {
                        throw new IOException("Password key directory close failed", error);
                    }
                }
            }
        } catch (IOException | RuntimeException error) {
            if (output != null) storage.failWrite(output);
            throw error;
        }
    }

}
