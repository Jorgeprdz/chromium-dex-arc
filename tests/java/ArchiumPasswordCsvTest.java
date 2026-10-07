import java.io.IOException;
import java.io.Reader;
import java.io.StringReader;
import java.io.StringWriter;
import java.io.Writer;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.List;

/** Synthetic credentials only; tests never print row contents. */
public final class ArchiumPasswordCsvTest {
    private static Class<?> csv;
    private static Class<?> rowClass;
    private static int cases;

    private static void check(boolean value, String reason) {
        if (!value) throw new AssertionError(reason);
    }

    private static Object parse(String value) throws Exception {
        try {
            return csv.getMethod("parse", Reader.class).invoke(null, new StringReader(value));
        } catch (InvocationTargetException e) {
            throw (Exception) e.getCause();
        }
    }

    private static List<?> rows(Object result) throws Exception {
        return (List<?>) result.getClass().getField("rows").get(result);
    }

    private static String field(Object row, String name) throws Exception {
        if (name.equals("password")) {
            char[] buffer = (char[]) rowClass.getMethod("copyPassword").invoke(row);
            try { return new String(buffer); }
            finally { java.util.Arrays.fill(buffer, '\0'); }
        }
        return (String) rowClass.getField(name).get(row);
    }

    private static Object row(String url, String username, String password) throws Exception {
        return rowClass.getConstructor(String.class, String.class, String.class)
                .newInstance(url, username, password);
    }

    private static void malformed(String value) throws Exception {
        try {
            parse(value);
            throw new AssertionError("Malformed quoting accepted");
        } catch (IOException expected) {
            check(!expected.getMessage().contains("synthetic-secret"), "Error exposed a field");
        }
        cases++;
    }

    private static void eofAndBufferBoundaries() throws Exception {
        String header = "url,username,password\n";
        String prefix = header + "https://boundary.example,u,";
        for (int length : new int[] {8192, 8193, 16384}) {
            String password = "x".repeat(length - prefix.length());
            try (AutoCloseable result = (AutoCloseable) parse(prefix + password)) {
                check(rows(result).size() == 1, "Buffer boundary invented or lost a record");
                check(field(rows(result).get(0), "password").equals(password),
                        "Buffer boundary changed the final field");
            }
            cases++;
        }
        for (String[] fixture : new String[][] {
                {"\"quoted\"", "quoted"},
                {"\"escaped-\"\"\"", "escaped-\""},
                {"", ""}}) {
            try (AutoCloseable result = (AutoCloseable) parse(prefix + fixture[0])) {
                check(rows(result).size() == 1, "EOF after final field lost a record");
                check(field(rows(result).get(0), "password").equals(fixture[1]),
                        "EOF changed the quoted or empty final field");
            }
            cases++;
        }
        try (AutoCloseable empty = (AutoCloseable) parse("")) {
            check(rows(empty).isEmpty(), "Empty input invented a record");
            check(((List<?>) empty.getClass().getField("errors").get(empty)).size() == 1,
                    "Empty input must retain its missing-header error");
        }
        cases++;

        // CR ends the first chunk; LF and the next record start the second.
        String firstPassword = "x".repeat(8191 - prefix.length());
        try (AutoCloseable result = (AutoCloseable) parse(prefix + firstPassword
                + "\r\nhttps://second.example,u,p")) {
            check(rows(result).size() == 2, "Split CRLF invented or lost a record");
            check(field(rows(result).get(0), "password").equals(firstPassword),
                    "Split CRLF changed the first password");
            check(field(rows(result).get(1), "password").equals("p"),
                    "Split CRLF changed the final password");
        }
        cases++;

        // The two quotes encoding a literal quote straddle the chunk boundary.
        String quotedPrefix = prefix + "\"";
        String quotedPassword = "x".repeat(8191 - quotedPrefix.length());
        try (AutoCloseable result = (AutoCloseable) parse(quotedPrefix + quotedPassword + "\"\"\"")) {
            check(rows(result).size() == 1, "Split escaped quote lost a record");
            check(field(rows(result).get(0), "password").equals(quotedPassword + "\""),
                    "Split escaped quote changed the password");
        }
        cases++;

        for (String separator : new String[] {"\n", "\r", "\r\n"}) {
            try (AutoCloseable result = (AutoCloseable) parse("url,username,password"
                    + separator + "https://one.example,,p" + separator)) {
                check(rows(result).size() == 1, "Line ending invented or lost a record");
                check(field(rows(result).get(0), "username").isEmpty(), "Empty username changed");
            }
            cases++;
        }

        Class<?> readerClass = Class.forName(csv.getName() + "$CsvReader");
        var constructor = readerClass.getDeclaredConstructor(Reader.class);
        constructor.setAccessible(true);
        var readRaw = readerClass.getDeclaredMethod("readRaw");
        readRaw.setAccessible(true);
        int[] reads = {0};
        Object emptyReader = constructor.newInstance(new StringReader("") {
            @Override public int read(char[] data, int off, int len) throws IOException {
                reads[0]++;
                return super.read(data, off, len);
            }
        });
        for (int i = 0; i < 3; i++) {
            check((int) readRaw.invoke(emptyReader) == -1, "Repeated EOF returned buffered data");
        }
        check(reads[0] == 1, "Terminal EOF read the input again");
        cases++;

        reads[0] = 0;
        Object zeroBulkReader = constructor.newInstance(new StringReader("z") {
            @Override public int read(char[] data, int off, int len) { return 0; }
            @Override public int read() throws IOException {
                reads[0]++;
                return super.read();
            }
        });
        check((int) readRaw.invoke(zeroBulkReader) == 'z', "Zero bulk read lost fallback data");
        for (int i = 0; i < 3; i++) {
            check((int) readRaw.invoke(zeroBulkReader) == -1, "Fallback EOF returned data");
        }
        check(reads[0] == 2, "Fallback EOF was not terminal");
        cases++;
    }

    public static void main(String[] ignored) throws Exception {
        try {
            csv = Class.forName("org.chromium.chrome.browser.password_manager.ArchiumPasswordCsv");
            rowClass = Class.forName(csv.getName() + "$Row");
        } catch (ClassNotFoundException missing) {
            throw new AssertionError("CSV parser is not implemented");
        }
        eofAndBufferBoundaries();
        Object normal = parse("\ufeffname,url,username,password,note\r\nDemo,https://one.example/login,,synthetic-secret,note\r\n");
        check(rows(normal).size() == 1, "BOM/additional column import");
        check(field(rows(normal).get(0), "username").isEmpty(), "Empty username changed");
        cases++;

        Object reordered = parse("PASSWORD, USERNAME ,URL\nsynthetic-secret,usuario,https://one.example\n");
        check(rows(reordered).size() == 1, "Header order/case/whitespace");
        check(field(rows(reordered).get(0), "password").equals("synthetic-secret"), "Column mapping");
        cases++;

        Object quoted = parse("url,username,password\nhttps://one.example,\"u,ñ\",\"synthetic-\"\"secret\"\"\nline2\"\n");
        check(rows(quoted).size() == 1, "Quoted field import");
        check(field(rows(quoted).get(0), "username").equals("u,ñ"), "Unicode/comma preservation");
        check(field(rows(quoted).get(0), "password").equals("synthetic-\"secret\"\nline2"), "Quote/newline preservation");
        cases++;

        Object missing = parse("url,username\nhttps://one.example,user\n");
        check(rows(missing).isEmpty(), "Missing password header accepted");
        check(((List<?>) missing.getClass().getField("errors").get(missing)).size() == 1,
                "Missing header must report an error");
        cases++;
        check(rows(parse("url,username,password,password\nhttps://one.example,u,a,b\n")).isEmpty(),
                "Ambiguous header accepted");
        cases++;

        Object partial = parse("url,username,password\n,synthetic-user,synthetic-secret\nhttps://one.example,u,p\n");
        check(rows(partial).size() == 1, "Valid row lost on missing URL");
        List<?> errors = (List<?>) partial.getClass().getField("errors").get(partial);
        check(errors.size() == 1, "Missing URL error");
        check(errors.get(0).getClass().getField("line").getInt(errors.get(0)) == 2, "Error line number");
        cases++;
        Object duplicate = parse("url,username,password\nhttps://one.example,u,p\nhttps://one.example,u,p\nhttps://one.example,u,different\n");
        check(rows(duplicate).size() == 2, "Conflicting password was silently discarded");
        check(duplicate.getClass().getField("duplicateCount").getInt(duplicate) == 1, "Duplicate count");
        cases++;
        check(rows(parse("url,username,password\n\nhttps://one.example,u,p")).size() == 1,
                "Blank line or final record without newline");
        cases++;

        malformed("url,username,password\nhttps://one.example,u,\"synthetic-secret");
        malformed("url,username,password\nhttps://one.example,u,synthetic-\"secret\"\n");
        malformed("url,username,password\nhttps://one.example,u,\"synthetic-secret\"junk\n");
        malformed("url,username,password\nhttps://one.example,u,\"synthetic-secret\" \n");

        List<Object> fixture = new ArrayList<>();
        fixture.add(row("https://one.example/login", "u,ñ", "a\"b\r\nc"));
        fixture.add(row("https://two.example", "", ""));
        StringWriter encoded = new StringWriter();
        csv.getMethod("write", Writer.class, List.class).invoke(null, encoded, fixture);
        List<?> roundtrip = rows(parse(encoded.toString()));
        check(roundtrip.size() == fixture.size(), "Roundtrip count");
        for (int i = 0; i < fixture.size(); i++) {
            for (String name : new String[] {"url", "username", "password"}) {
                check(field(fixture.get(i), name).equals(field(roundtrip.get(i), name)), "Roundtrip value");
            }
            check(!fixture.get(i).toString().contains(field(fixture.get(i), "url")), "Row debug string exposes data");
        }
        cases++;

        // REAL_CONTRACT_TEST (synthetic CSV): parser and row secrets are
        // explicitly erasable. This doesn't claim Java String/Reader erasure.
        Object scrubbedResult = parse("url,username,password\nhttps://erase.example,u,synthetic-secret\n");
        Object scrubbedRow = rows(scrubbedResult).get(0);
        char[] borrowed = (char[]) rowClass.getMethod("copyPassword").invoke(scrubbedRow);
        ((AutoCloseable) scrubbedResult).close();
        java.lang.reflect.Field passwordField = rowClass.getDeclaredField("mPassword");
        passwordField.setAccessible(true);
        for (char c : (char[]) passwordField.get(scrubbedRow)) check(c == 0, "parser row not scrubbed");
        java.util.Arrays.fill(borrowed, '\0');
        try {
            rowClass.getMethod("copyPassword").invoke(scrubbedRow);
            throw new AssertionError("Closed import buffer reused");
        } catch (InvocationTargetException closed) {
            check(closed.getCause() instanceof IllegalStateException,
                    "closed parser row failed with wrong error");
        }
        cases++;

        Writer failed = new Writer() {
            @Override public void write(char[] chars, int off, int len) throws IOException {
                throw new IOException("Synthetic output failure");
            }
            @Override public void flush() {}
            @Override public void close() {}
        };
        try {
            csv.getMethod("write", Writer.class, List.class).invoke(null, failed, fixture);
            throw new AssertionError("Output failure was swallowed");
        } catch (InvocationTargetException expected) {
            check(expected.getCause() instanceof IOException, "Wrong export failure type");
        }
        cases++;
        Object largeField = null;
        try {
            largeField = parse("url,username,password\nhttps://one.example,u," + "x".repeat(1_048_577));
        } catch (IOException expected) {
            cases++;
        }
        check(largeField == null, "Oversized input field accepted");
        for (String oversized : new String[] {
                "url,username,password," + "extra,".repeat(512) + "last\n",
                "url,username,password\n" + "\n".repeat(100_001),
                "url,username,password\n"
                        + ("https://one.example,u," + "x".repeat(1_024) + "\n").repeat(17_000)}) {
            try {
                parse(oversized);
                throw new AssertionError("Unbounded input accepted");
            } catch (IOException expected) {
                cases++;
            }
        }
        Class<?> secretRow = Class.forName(csv.getName() + "$SecretRow");
        char[] source = "quote\",comma\n🔒".toCharArray();
        Object secret = secretRow.getConstructor(String.class, String.class, char[].class)
                .newInstance("https://export.example/", "user", source);
        String expectedPassword = new String(source);
        java.util.Arrays.fill(source, 'x');
        StringWriter exported = new StringWriter();
        csv.getMethod("writeSecrets", Writer.class, List.class)
                .invoke(null, exported, List.of(secret));
        check(field(rows(parse(exported.toString())).get(0), "password").equals(expectedPassword),
                "owned export buffer preserves quotes, newline and Unicode independently of caller buffer");
        cases++;
        secretRow.getMethod("close").invoke(secret);
        java.lang.reflect.Field owned = secretRow.getDeclaredField("mPassword");
        owned.setAccessible(true);
        for (char value : (char[]) owned.get(secret)) check(value == 0, "closed export buffer was not erased");
        cases++;
        StringWriter closedOutput = new StringWriter();
        try {
            csv.getMethod("writeSecrets", Writer.class, List.class)
                    .invoke(null, closedOutput, List.of(secret));
            throw new AssertionError("Closed credentials exported again");
        } catch (InvocationTargetException expected) {
            check(expected.getCause() instanceof IOException, "closed secret has wrong failure type");
            check(closedOutput.toString().isEmpty(), "closed export wrote a partial header");
        }
        cases++;
        // REAL_CONTRACT_TEST on synthetic data; NOT_EXECUTED in Prompt 2.
        // The private buffer used by production CsvReader must be erasable.
        Class<?> readerClass = Class.forName(csv.getName() + "$CsvReader");
        var readerConstructor = readerClass.getDeclaredConstructor(Reader.class);
        readerConstructor.setAccessible(true);
        Object bufferedParser = readerConstructor.newInstance(new StringReader("synthetic-secret"));
        var readRaw = readerClass.getDeclaredMethod("readRaw");
        readRaw.setAccessible(true);
        check((int) readRaw.invoke(bufferedParser) == 's', "reader did not consume test data");
        java.lang.reflect.Field bufferField = readerClass.getDeclaredField("readBuffer");
        bufferField.setAccessible(true);
        char[] internalBuffer = (char[]) bufferField.get(bufferedParser);
        check(internalBuffer[0] == 's', "reader did not buffer data");
        var eraseReader = readerClass.getDeclaredMethod("erase");
        eraseReader.setAccessible(true);
        eraseReader.invoke(bufferedParser);
        for (char c : internalBuffer) check(c == 0, "CSV buffer survived erase");
        cases++;

        // REAL_CONTRACT_TEST: cancellation before export cannot emit a header.
        Object cancelSecret = secretRow.getConstructor(String.class, String.class, char[].class)
                .newInstance("https://cancel.example/", "user", "synthetic-secret".toCharArray());
        StringWriter cancelled = new StringWriter();
        Thread.currentThread().interrupt();
        try {
            csv.getMethod("writeSecrets", Writer.class, List.class)
                    .invoke(null, cancelled, List.of(cancelSecret));
            throw new AssertionError("Cancelled CSV export accepted");
        } catch (InvocationTargetException expected) {
            check(expected.getCause() instanceof IOException, "Export cancel wrong error type");
            check(cancelled.toString().isEmpty(), "Cancelled export emitted a header");
        } finally {
            Thread.interrupted(); // Clear the test's interrupted status.
            secretRow.getMethod("close").invoke(cancelSecret);
        }
        cases++;

        // REAL_CONTRACT_TEST: interruption aborts CSV parsing (also triggers
        // the parser's finally-owned-buffer scrub path). NOT_EXECUTED.
        Thread.currentThread().interrupt();
        try {
            parse("url,username,password\nhttps://cancel.example,u,synthetic-secret\n");
            throw new AssertionError("Cancelled CSV read accepted");
        } catch (IOException expected) {
            check(!expected.getMessage().contains("synthetic-secret"), "Cancel leaked password");
        } finally {
            Thread.interrupted();
        }
        cases++;
        System.out.println("ArchiumPasswordCsv: " + cases + " synthetic cases passed");
    }
}
