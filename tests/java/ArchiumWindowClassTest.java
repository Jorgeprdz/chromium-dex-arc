import java.lang.reflect.Method;

/** Current window width, independent of device labels/orientation/display implementation. */
public final class ArchiumWindowClassTest {
    public static void main(String[] args) throws Exception {
        Class<?> type = Class.forName("org.chromium.chrome.browser.desktop_policy.ArchiumWindowClass");
        Method classify = type.getMethod("classify", int.class);
        int[] widths = {0, 520, 580, 599, 600, 620, 700, 839, 840, 900};
        String[] expected = {"COMPACT", "COMPACT", "COMPACT", "COMPACT", "TABLET",
                             "TABLET", "TABLET", "TABLET", "DESKTOP", "DESKTOP"};
        for (int i = 0; i < widths.length; i++) check(classify, widths[i], expected[i]);
        // Changes must be reversible; no sticky state after expanding/maximizing.
        for (int width : new int[] {580, 620, 900, 520, 700, 580}) {
            check(classify, width, width < 600 ? "COMPACT" : width < 840 ? "TABLET" : "DESKTOP");
        }
        // Same width remains the same class, regardless of how often a rotation/layout occurs.
        for (int repeat = 0; repeat < 20; repeat++) check(classify, 580, "COMPACT");
        System.out.println("ArchiumWindowClass: boundaries, reversible resize and repeated layout passed");
    }
    private static void check(Method classify, int width, String expected) throws Exception {
        String actual = classify.invoke(null, width).toString();
        if (!expected.equals(actual)) throw new AssertionError(width + "dp: " + actual + " != " + expected);
    }
}
