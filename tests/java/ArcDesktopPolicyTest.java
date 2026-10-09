import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;

public final class ArcDesktopPolicyTest {
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    private static boolean arc(int preference, int width) {
        try {
            return (boolean) ArcDesktopPolicy.class
                    .getMethod("isArcWindow", int.class, int.class)
                    .invoke(null, preference, width);
        } catch (NoSuchMethodException missing) {
            throw new AssertionError("AUTO/ARC/MOBILE appearance policy is missing");
        } catch (ReflectiveOperationException error) {
            throw new AssertionError(error);
        }
    }

    public static void main(String[] args) {
        for (int width : new int[] {0, 520, 580, 599, 600, 620, 839, 840, 900}) {
            check(arc(0, width) == (width >= 600), "AUTO follows current window class");
            check(arc(1, width), "Explicit ARC is an appearance override");
            check(!arc(2, width), "Explicit MOBILE suppresses Arc appearance");
            check(arc(99, width) == arc(0, width), "Unknown preference falls back to AUTO");
            check(ArcDesktopPolicy.isDesktopWindow(width) == (width >= 600),
                    "Appearance preference must not affect desktop navigation eligibility");
        }
        check(!ArcDesktopPolicy.isDesktopWindow(580), "phone-sized window stays mobile");
        check(!ArcDesktopPolicy.isDesktopWindow(520), "narrow split/freeform stays mobile");
        check(ArcDesktopPolicy.isDesktopWindow(600), "tablet boundary enables Arc");
        check(ArcDesktopPolicy.isDesktopWindow(620), "tablet-sized window uses Arc");
        check(ArcDesktopPolicy.isDesktopWindow(840), "expanded window uses Arc");
        check(ArcDesktopPolicy.isDesktopWindow(900), "large window uses Arc independent of device");
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
        check(ArcDesktopPolicy.surface(0xff53657b, true)
                        != ArcDesktopPolicy.surface(0xff53657b, false),
                "incognito/dark treatment remains visually distinct from regular light Arc");

        // REAL_CONTRACT_TEST: production rounded-viewport hit testing. The sidebar lives left of
        // x=240; web content is the rounded rect [240, 0, 1000, 700].
        check(!ArcDesktopPolicy.containsRoundedRectPoint(239, 350, 240, 0, 1000, 700, 16),
                "sidebar/gap coordinates are outside web content");
        check(ArcDesktopPolicy.containsRoundedRectPoint(500, 350, 240, 0, 1000, 700, 16),
                "content center is interactive");
        check(!ArcDesktopPolicy.containsRoundedRectPoint(240, 0, 240, 0, 1000, 700, 16),
                "rounded top-left corner rejects invisible content");
        check(ArcDesktopPolicy.containsRoundedRectPoint(256, 16, 240, 0, 1000, 700, 16),
                "rounded top-left arc accepts its inner boundary");
        check(!ArcDesktopPolicy.containsRoundedRectPoint(999, 0, 240, 0, 1000, 700, 16),
                "rounded top-right corner rejects invisible content");
        check(!ArcDesktopPolicy.containsRoundedRectPoint(1000, 350, 240, 0, 1000, 700, 16),
                "right bound is exclusive");
        check(ArcDesktopPolicy.containsRoundedRectPoint(240, 0, 240, 0, 1000, 700, 0),
                "zero-radius rectangle retains normal rectangular hit testing");
        check(!ArcDesktopPolicy.containsRoundedRectPoint(0, 0, 0, 0, 2, 2, 99),
                "oversized radius is clamped instead of exposing a square corner");
        check(ArcDesktopPolicy.containsArcViewportPoint(240, 699, 240, 0, 1000, 700, 16),
                "square internal lower-left seam");
        check(!ArcDesktopPolicy.containsArcViewportPoint(240, 0, 240, 0, 1000, 700, 16),
                "upper-left rounded corner");
        check(!ArcDesktopPolicy.containsArcViewportPoint(999, 699, 240, 0, 1000, 700, 16),
                "lower-right rounded corner");
        check(!ArcDesktopPolicy.containsArcViewportPoint(239, 699, 240, 0, 1000, 700, 16),
                "sidebar outside web bounds");
        check(ArcDesktopPolicy.showFullControls(240, 700, 1f),
                "expanded 240dp rail exposes full Arc controls");
        check(!ArcDesktopPolicy.showFullControls(52, 700, 1f),
                "collapsed 52dp rail keeps compact controls");
        check(!ArcDesktopPolicy.showFullControls(240, 350, 1f),
                "short rail keeps compact controls");
        check(ArcDesktopPolicy.showFullControls(480, 720, 2f),
                "expanded contract scales with density rather than physical pixels");
        check(!ArcDesktopPolicy.showFullControls(240, 700, 0f),
                "invalid density fails compact instead of exposing oversized controls");

        check(ArcDesktopPolicy.ARC_OUTER_PADDING_DP > 0
                        && ArcDesktopPolicy.ARC_FRAME_GAP_DP > 0
                        && ArcDesktopPolicy.ARC_CONTENT_RADIUS_DP > 0
                        && ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP > 0
                        && ArcDesktopPolicy.ARC_NAV_BUTTON_WIDTH_DP > 0
                        && ArcDesktopPolicy.ARC_LOCATION_BAR_SIDE_MARGIN_DP >= 0
                        && ArcDesktopPolicy.ARC_FULL_CONTROLS_MIN_WIDTH_DP
                                >= ArcDesktopPolicy.ARC_NAV_BUTTON_WIDTH_DP * 4
                        && ArcDesktopPolicy.ARC_FULL_CONTROLS_MIN_HEIGHT_DP > 0,
                "Arc frame dimensions remain semantic and fit collapse plus native navigation");

        System.out.println("ArcDesktopPolicy: policy, palette and rounded-content contract cases defined");
    }
}
