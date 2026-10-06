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

    public static void main(String[] ignored) throws Exception {
        try {
            csv = Class.forName("org.chromium.chrome.browser.password_manager.ArchiumPasswordCsv");
            rowClass = Class.forName(csv.getName() + "$Row");
        } catch (ClassNotFoundException missing) {
            throw new AssertionError("CSV parser is not implemented");
        }
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
        System.out.println("ArchiumPasswordCsv: " + cases + " synthetic cases passed");
    }
}
