// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package org.chromium.chrome.browser.password_manager;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.util.ArrayList;
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

    /** Contains secrets for a user-authorized preview/commit/export; never pass rows to logging. */
    public static final class Row {
        public final String url;
        public final String username;
        public final String password;

        public Row(String url, String username, String password) {
            this.url = Objects.requireNonNull(url);
            this.username = Objects.requireNonNull(username);
            this.password = Objects.requireNonNull(password);
        }

        @Override
        public boolean equals(Object other) {
            if (!(other instanceof Row)) return false;
            Row row = (Row) other;
            return url.equals(row.url)
                    && username.equals(row.username)
                    && password.equals(row.password);
        }

        @Override
        public int hashCode() {
            return Objects.hash(url, username, password);
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

    public static final class ParseResult {
        public final List<Row> rows;
        public final List<LineError> errors;
        public final int duplicateCount;

        private ParseResult(List<Row> rows, List<LineError> errors, int duplicateCount) {
            this.rows = Collections.unmodifiableList(new ArrayList<>(rows));
            this.errors = Collections.unmodifiableList(new ArrayList<>(errors));
            this.duplicateCount = duplicateCount;
        }
    }

    private static final class Record {
        final List<String> fields;
        final int line;

        Record(List<String> fields, int line) {
            this.fields = fields;
            this.line = line;
        }
    }

    private static final class CsvReader {
        private static final int START = 0;
        private static final int UNQUOTED = 1;
        private static final int QUOTED = 2;
        private static final int AFTER_QUOTE = 3;

        private final Reader input;
        private int line = 1;
        private boolean firstCharacter = true;
        private boolean previousWasCr;
        private boolean skipLf;
        private int characters;

        CsvReader(Reader input) {
            this.input = new BufferedReader(input);
        }

        private int readRaw() throws IOException {
            int c = input.read();
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

        private void append(StringBuilder field, int c, int recordLine) throws IOException {
            if (field.length() == MAX_FIELD_CHARS) {
                throw new IOException("CSV field is too large at line " + recordLine);
            }
            field.append((char) c);
        }

        private void addField(List<String> fields, StringBuilder field, int recordLine)
                throws IOException {
            if (fields.size() == MAX_COLUMNS) {
                throw new IOException("Too many CSV columns at line " + recordLine);
            }
            fields.add(field.toString());
        }

        Record next() throws IOException {
            int startLine = line;
            List<String> fields = new ArrayList<>();
            StringBuilder field = new StringBuilder();
            int state = START;
            boolean anyCharacter = false;
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
                    addField(fields, field, startLine);
                    return new Record(fields, startLine);
                }
                anyCharacter = true;
                if (state == QUOTED) {
                    if (c == '"') state = AFTER_QUOTE;
                    else append(field, c, startLine);
                    continue;
                }
                if (state == AFTER_QUOTE && c == '"') {
                    append(field, c, startLine);
                    state = QUOTED;
                    continue;
                }
                if (c == ',' || c == '\r' || c == '\n') {
                    addField(fields, field, startLine);
                    if (c != ',') {
                        skipLf = c == '\r';
                        return new Record(fields, startLine);
                    }
                    field.setLength(0);
                    state = START;
                    continue;
                }
                if (state == AFTER_QUOTE || (state == UNQUOTED && c == '"')) {
                    throw new IOException("Invalid CSV quoting at line " + startLine);
                }
                if (state == START && c == '"') {
                    state = QUOTED;
                } else {
                    append(field, c, startLine);
                    state = UNQUOTED;
                }
            }
        }
    }

    /** Does not close the caller's reader and has no filesystem or PasswordStore side effects. */
    public static ParseResult parse(Reader input) throws IOException {
        Objects.requireNonNull(input);
        CsvReader reader = new CsvReader(input);
        List<Row> rows = new ArrayList<>();
        List<LineError> errors = new ArrayList<>();
        Record header = reader.next();
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
        for (Record record; (record = reader.next()) != null; ) {
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
                    record.fields.get(password));
            if (identicalRows.add(row)) rows.add(row);
            else duplicates++;
        }
        return new ParseResult(rows, errors, duplicates);
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

    /** Streams to the selected output. Ownership/flush/close remain with the SAF caller. */
    public static void write(Writer output, List<Row> rows) throws IOException {
        Objects.requireNonNull(output);
        Objects.requireNonNull(rows);
        output.write("url,username,password\r\n");
        for (Row row : rows) {
            writeField(output, row.url);
            output.write(',');
            writeField(output, row.username);
            output.write(',');
            writeField(output, row.password);
            output.write("\r\n");
        }
    }

    private ArchiumPasswordCsv() {}
}
