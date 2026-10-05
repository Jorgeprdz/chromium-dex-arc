import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;

public final class ArcDesktopPolicyTest {
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    public static void main(String[] args) {
        check(!ArcDesktopPolicy.isDesktopWindow(true, false, false), "phone landscape stays mobile");
        check(!ArcDesktopPolicy.isDesktopWindow(true, true, false), "phone stays mobile while DeX runs elsewhere");
        check(!ArcDesktopPolicy.isDesktopWindow(false, false, false), "external mirror is not DeX");
        check(ArcDesktopPolicy.isDesktopWindow(false, true, false), "DeX window uses Arc");
        check(ArcDesktopPolicy.isDesktopWindow(true, false, true), "actual PC uses Arc on primary display");
        check(ArcDesktopPolicy.isDesktopWindow(false, false, true), "actual PC secondary display uses Arc");
        for (int seed = 0; seed <= 0xffffff; seed += 7919) {
            for (boolean dark : new boolean[] {false, true}) {
                int bg = ArcDesktopPolicy.surface(seed, dark);
                check((bg >>> 24) == 255, "surface is opaque");
                check(ArcDesktopPolicy.contrast(bg, ArcDesktopPolicy.foreground(bg)) >= 4.5,
                        "text contrast meets 4.5:1");
            }
        }
        check(ArcDesktopPolicy.foreground(0xff000000) == 0xffffffff, "black needs white text");
        check(ArcDesktopPolicy.foreground(0xffffffff) == 0xff000000, "white needs black text");
        check(ArcDesktopPolicy.surface(0xff0044ee, true) != ArcDesktopPolicy.surface(0xffee4400, true),
                "chosen hue affects surface");
        System.out.println("ArcDesktopPolicy: desktop/mobile and 4,238 palette cases passed");
    }
}
