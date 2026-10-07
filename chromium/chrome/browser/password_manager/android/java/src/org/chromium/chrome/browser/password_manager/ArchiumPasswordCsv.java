// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package org.chromium.chrome.browser.password_manager;

import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;

/** CSV transport only. Chromium's native types validate URLs/realms before an import is committed. */
public final class ArchiumPasswordCsv {
    private static final int MAX_FIELD_CHARS = 1_048_576;
    private static final int MAX_INPUT_CHARS = 16_777_216;
    private static final int MAX_COLUMNS = 512;
    private static final int MAX_RECORDS = 100_000;

    /** Owned export buffer. The authorized SAF job must close every row in its finally block. */
    public static final class SecretRow implements AutoCloseable {
        public final String url;
        public final String username;
        private final char[] mPassword;
        private boolean mClosed;

        public SecretRow(String url, String username, char[] password) {
            this.url = Objects.requireNonNull(url);
            this.username = Objects.requireNonNull(username);
            mPassword = Objects.requireNonNull(password).clone();
        }

        @Override public synchronized void close() {
            Arrays.fill(mPassword, '\0');
            mClosed = true;
        }
    }

    /** An owned, explicitly closable import secret. Do not retain rows in UI state. */
    public static final class Row implements AutoCloseable {
        public final String url;
        public final String username;
        private final char[] mPassword;
        private boolean mClosed;

        // Compatibility for synthetic test fixtures only. The caller-supplied
        // String cannot be wiped by Java; the CSV parser never uses this path.
        public Row(String url, String username, String password) {
            this(url, username, Objects.requireNonNull(password).toCharArray());
        }

        public Row(String url, String username, char[] password) {
            this.url = Objects.requireNonNull(url);
            this.username = Objects.requireNonNull(username);
            this.mPassword = Objects.requireNonNull(password).clone();
        }

        /** Caller owns and must erase the returned temporary copy. */
        public synchronized char[] copyPassword() {
            if (mClosed) throw new IllegalStateException("Import secret no longer available");
            return mPassword.clone();
        }

        @Override public synchronized void close() {
            Arrays.fill(mPassword, '\0');
            mClosed = true;
        }

        @Override
        public boolean equals(Object other) {
            if (!(other instanceof Row)) return false;
            Row row = (Row) other;
            return url.equals(row.url)
                    && username.equals(row.username)
                    && Arrays.equals(mPassword, row.mPassword);
        }

        @Override
        public int hashCode() {
            return 31 * Objects.hash(url, username) + Arrays.hashCode(mPassword);
        }

        @Override
        public String toString() {
            return "ArchiumPasswordCsv.Row";
        }
    }

    public enum ErrorCode {
        MISSING_REQUIRED_HEADERS,
        AMBIGUOUS_HEADER,
        COLUMN_COUNT,
        MISSING_URL
    }

    /** Codes and physical line numbers only: no field values in error reporting. */
    public static final class LineError {
        public final int line;
        public final ErrorCode code;

        private LineError(int line, ErrorCode code) {
            this.line = line;
            this.code = code;
        }
    }

    public static final class ParseResult implements AutoCloseable {
        public final List<Row> rows;
        public final List<LineError> errors;
        public final int duplicateCount;

        private ParseResult(List<Row> rows, List<LineError> errors, int duplicateCount) {
            this.rows = Collections.unmodifiableList(new ArrayList<>(rows));
            this.errors = Collections.unmodifiableList(new ArrayList<>(errors));
            this.duplicateCount = duplicateCount;
        }

        @Override public void close() {
            for (Row row : rows) row.close();
        }
    }

    private static final class Record implements AutoCloseable {
        final List<String> fields;
        final int line;
        final char[] secret;

        Record(List<String> fields, int line, char[] secret) {
            this.fields = fields;
            this.line = line;
            this.secret = secret;
        }

        @Override public void close() { Arrays.fill(secret, '\0'); }
    }

    /** Resizable buffer with explicit scrubbing of old backing arrays on growth. */
    private static final class SecretBuffer {
        private char[] data = new char[64];
        private int length;

        void append(int c) {
            if (length == data.length) {
                char[] old = data;
                data = Arrays.copyOf(data, Math.min(MAX_FIELD_CHARS, data.length * 2));
                Arrays.fill(old, '\0');
            }
            data[length++] = (char) c;
        }

        char[] take() {
            char[] value = Arrays.copyOf(data, length);
            erase();
            return value;
        }

        void erase() {
            Arrays.fill(data, '\0');
            length = 0;
        }
    }

    private static final class RecordBuilder {
        final List<String> fields = new ArrayList<>();
        final StringBuilder text = new StringBuilder();
        final SecretBuffer secretBuffer = new SecretBuffer();
        final int secretColumn;
        char[] password = new char[0];

        RecordBuilder(int secretColumn) { this.secretColumn = secretColumn; }

        void append(int c, int line) throws IOException {
            if ((fields.size() == secretColumn ? secretLength : text.length()) == MAX_FIELD_CHARS) {
                throw new IOException("CSV field is too large at line " + line);
            }
            if (fields.size() == secretColumn) {
                secretBuffer.append(c);
                secretLength++;
            } else {
                text.append((char) c);
            }
        }

        private int secretLength;

        void addField(int line) throws IOException {
            if (fields.size() == MAX_COLUMNS) {
                throw new IOException("Too many CSV columns at line " + line);
            }
            if (fields.size() == secretColumn) {
                password = secretBuffer.take();
                fields.add(""); // Do not construct an immutable password String.
                secretLength = 0;
            } else {
                fields.add(text.toString());
            }
            text.setLength(0);
        }

        Record finish(int line) throws IOException {
            addField(line);
            char[] owned = password;
            password = new char[0];
            return new Record(fields, line, owned);
        }

        void erase() {
            secretBuffer.erase();
            Arrays.fill(password, '\0');
        }
    }

    private static final class CsvReader {
        private static final int START = 0;
        private static final int UNQUOTED = 1;
        private static final int QUOTED = 2;
        private static final int AFTER_QUOTE = 3;

        private final Reader input;
        // Own and scrub the buffering layer instead of retaining an opaque
        // BufferedReader with an inaccessible plaintext backing array.
        // The caller's Reader/decoder and pre-existing String input are outside
        // this class's erasure guarantees.
        private final char[] readBuffer = new char[8192];
        private int buffered;
        private int nextRead;
        private int line = 1;
        private boolean firstCharacter = true;
        private boolean previousWasCr;
        private boolean skipLf;
        private int characters;

        CsvReader(Reader input) {
            this.input = input;
        }

        void erase() {
            Arrays.fill(readBuffer, '\0');
            buffered = 0;
            nextRead = 0;
        }

        private int readRaw() throws IOException {
            int c;
            if (nextRead == buffered) {
                if (Thread.currentThread().isInterrupted()) {
                    throw new IOException("CSV read cancelled");
                }
                // Clear the previous chunk before reuse; the final chunk is
                // always cleared by parse()'s finally block, including errors.
                erase();
                buffered = input.read(readBuffer, 0, readBuffer.length);
                if (buffered < 0) return -1;
                c = buffered == 0 ? input.read() : readBuffer[nextRead++];
            } else {
                c = readBuffer[nextRead++];
            }
            if (c != -1 && ++characters > MAX_INPUT_CHARS) {
                throw new IOException("CSV input is too large");
            }
            return c;
        }

        private int read() throws IOException {
            int c = readRaw();
            if (firstCharacter) {
                firstCharacter = false;
                if (c == '\ufeff') c = readRaw();
            }
            if (c == '\r' || (c == '\n' && !previousWasCr)) line++;
            previousWasCr = c == '\r';
            return c;
        }

        Record next(int secretColumn) throws IOException {
            int startLine = line;
            RecordBuilder builder = new RecordBuilder(secretColumn);
            int state = START;
            boolean anyCharacter = false;
            try {
              while (true) {
                int c = read();
                if (skipLf) {
                    skipLf = false;
                    if (c == '\n') {
                        startLine = line;
                        continue;
                    }
                }
                if (c == -1) {
                    if (state == QUOTED) {
                        throw new IOException("Unclosed CSV quote at line " + startLine);
                    }
                    if (!anyCharacter) return null;
                    return builder.finish(startLine);
                }
                anyCharacter = true;
                if (state == QUOTED) {
                    if (c == '"') state = AFTER_QUOTE;
                    else builder.append(c, startLine);
                    continue;
                }
                if (state == AFTER_QUOTE && c == '"') {
                    builder.append(c, startLine);
                    state = QUOTED;
                    continue;
                }
                if (c == ',' || c == '\r' || c == '\n') {
                    builder.addField(startLine);
                    if (c != ',') {
                        skipLf = c == '\r';
                        char[] owned = builder.password;
                        builder.password = new char[0];
                        return new Record(builder.fields, startLine, owned);
                    }
                    state = START;
                    continue;
                }
                if (state == AFTER_QUOTE || (state == UNQUOTED && c == '"')) {
                    throw new IOException("Invalid CSV quoting at line " + startLine);
                }
                if (state == START && c == '"') {
                    state = QUOTED;
                } else {
                    builder.append(c, startLine);
                    state = UNQUOTED;
                }
              }
            } catch (IOException | RuntimeException exception) {
                builder.erase();
                throw exception;
            }
        }
    }

    /** Does not close the caller's reader and has no filesystem or PasswordStore side effects. */
    public static ParseResult parse(Reader input) throws IOException {
        Objects.requireNonNull(input);
        CsvReader reader = new CsvReader(input);
        try {
        List<Row> rows = new ArrayList<>();
        List<LineError> errors = new ArrayList<>();
        Record header = reader.next(-1);
        if (header == null) {
            errors.add(new LineError(1, ErrorCode.MISSING_REQUIRED_HEADERS));
            return new ParseResult(rows, errors, 0);
        }
        int url = -1;
        int username = -1;
        int password = -1;
        for (int i = 0; i < header.fields.size(); i++) {
            String name = header.fields.get(i).trim().toLowerCase(Locale.ROOT);
            if (name.equals("url")) {
                if (url != -1) errors.add(new LineError(header.line, ErrorCode.AMBIGUOUS_HEADER));
                url = i;
            } else if (name.equals("username")) {
                if (username != -1) {
                    errors.add(new LineError(header.line, ErrorCode.AMBIGUOUS_HEADER));
                }
                username = i;
            } else if (name.equals("password")) {
                if (password != -1) {
                    errors.add(new LineError(header.line, ErrorCode.AMBIGUOUS_HEADER));
                }
                password = i;
            }
        }
        if (url == -1 || username == -1 || password == -1) {
            errors.add(new LineError(header.line, ErrorCode.MISSING_REQUIRED_HEADERS));
        }
        if (!errors.isEmpty()) return new ParseResult(rows, errors, 0);
        Set<Row> identicalRows = new HashSet<>();
        int duplicates = 0;
        int recordCount = 0;
        try {
          for (Record record; (record = reader.next(password)) != null; ) {
            try {
            if (++recordCount > MAX_RECORDS) {
                throw new IOException("Too many CSV records");
            }
            if (record.fields.size() == 1 && record.fields.get(0).isEmpty()) continue;
            if (record.fields.size() != header.fields.size()) {
                errors.add(new LineError(record.line, ErrorCode.COLUMN_COUNT));
                continue;
            }
            if (record.fields.get(url).trim().isEmpty()) {
                errors.add(new LineError(record.line, ErrorCode.MISSING_URL));
                continue;
            }
            Row row = new Row(record.fields.get(url), record.fields.get(username),
                    record.secret);
            if (identicalRows.add(row)) rows.add(row);
            else { duplicates++; row.close(); }
            } finally { record.close(); }
          }
        } catch (IOException | RuntimeException failure) {
            for (Row row : rows) row.close();
            throw failure;
        }
        return new ParseResult(rows, errors, duplicates);
        } finally {
            reader.erase();
        }
    }

    private static void writeField(Writer output, String value) throws IOException {
        // Quote every field. Do not change characters such as spreadsheet formula prefixes:
        // changing a secret would break password export/reimport equivalence.
        output.write('"');
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            if (c == '"') output.write('"');
            output.write(c);
        }
        output.write('"');
    }

    private static void writeField(Writer output, char[] value) throws IOException {
        output.write('"');
        for (char c : value) {
            if (c == '"') output.write('"');
            output.write(c);
        }
        output.write('"');
    }

    /** Streams to the selected output. Ownership/flush/close remain with the SAF caller. */
    public static void write(Writer output, List<Row> rows) throws IOException {
        Objects.requireNonNull(output);
        Objects.requireNonNull(rows);
        for (Row row : rows) {
            synchronized (row) {
                if (row.mClosed) throw new IOException("Import secret no longer available");
            }
        }
        output.write("url,username,password\r\n");
        for (Row row : rows) {
          synchronized (row) {
            if (row.mClosed) throw new IOException("Import secret no longer available");
            writeField(output, row.url);
            output.write(',');
            writeField(output, row.username);
            output.write(',');
            writeField(output, row.mPassword);
            output.write("\r\n");
          }
        }
    }

    /** Streams authenticated export buffers without creating password String objects. */
    public static void writeSecrets(Writer output, List<SecretRow> rows) throws IOException {
        Objects.requireNonNull(output);
        Objects.requireNonNull(rows);
        for (SecretRow row : rows) {
            synchronized (row) {
                if (row.mClosed) throw new IOException("Export credentials no longer available");
            }
        }
        if (Thread.currentThread().isInterrupted()) {
            throw new IOException("CSV export cancelled");
        }
        output.write("url,username,password\r\n");
        for (SecretRow row : rows) {
            if (Thread.currentThread().isInterrupted()) {
                throw new IOException("CSV export cancelled");
            }
            // Closing cannot zero a password halfway through writing its field.
            synchronized (row) {
                if (row.mClosed) throw new IOException("Export credentials no longer available");
                writeField(output, row.url);
                output.write(',');
                writeField(output, row.username);
                output.write(',');
                output.write('"');
                for (int i = 0; i < row.mPassword.length; i++) {
                    // A destroyed screen interrupts its export executor. Even
                    // a long single password must respond to cancellation.
                    if ((i & 2047) == 0 && Thread.currentThread().isInterrupted()) {
                        throw new IOException("CSV export cancelled");
                    }
                    char value = row.mPassword[i];
                    if (value == '"') output.write('"');
                    output.write(value);
                }
                output.write('"');
                output.write("\r\n");
            }
        }
    }

    private ArchiumPasswordCsv() {}
}
