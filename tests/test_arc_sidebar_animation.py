"""Execute Arc layout callbacks with explicit Android view-boundary doubles.

The probe checks callback work and lifecycle, not device frame timing or visual smoothness.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from arc_toolbar_probe import ROOT, method_body


COORD = ROOT / "chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java"

JAVA = r"""
class SidebarAnimationRegression {
    static class View {
        interface OnLayoutChangeListener {
            void onLayoutChange(View view, int l, int t, int r, int b,
                    int ol, int ot, int or, int ob);
        }
    }
    static class Activity {}
    static class ArcDesktopAppearance {
        static boolean desktop = true;
        static boolean isDesktopWindow(Activity activity) { return desktop; }
    }
    final Activity mActivity = new Activity();
    boolean mDestroyed, mArcToolbarCompositionActive = true;
    int appearances, rebinds, sidebarGeometry, frameGeometry, controlUpdates;
    View.OnLayoutChangeListener mLayoutListener, mColumnLayoutListener;
    // Preserve the real methods' guards and geometry effects at this boundary.
    void applyAppearance() {
        if (mDestroyed) return;
        appearances++;
        applySidebarGeometry();
        applyFrameGeometry();
    }
    void rebindCollections() { if (!mDestroyed) rebinds++; }
    void applySidebarGeometry() { sidebarGeometry++; }
    void applyFrameGeometry() { frameGeometry++; }
    void updateSidebarControls() {
        controlUpdates++;
        applySidebarGeometry();
        applyFrameGeometry();
    }
    HELPERS
    SidebarAnimationRegression() {
        mLayoutListener = (v, l, t, r, b, ol, ot, or, ob) -> RAIL;
        mColumnLayoutListener = (v, l, t, r, b, ol, ot, or, ob) -> COLUMN;
    }
    static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    void layout(View.OnLayoutChangeListener listener, int oldWidth, int newWidth) {
        listener.onLayoutChange(new View(), 0, 0, newWidth, 800, 0, 0, oldWidth, 800);
    }
    public static void main(String[] args) {
        SidebarAnimationRegression r = new SidebarAnimationRegression();
        if (args[0].equals("animation")) {
            // ChangeBounds changes both the rail root and the nested Arc column.
            int oldWidth = 334;
            for (int width : new int[] {310, 280, 248, 210, 166, 120, 80, 52,
                    80, 120, 166, 210, 248, 280, 310, 334}) {
                r.layout(r.mLayoutListener, oldWidth, width);
                r.layout(r.mColumnLayoutListener, oldWidth, width);
                oldWidth = width;
            }
            check(r.appearances == 0, "animated width callbacks must not refresh palettes/tint hierarchy: " + r.appearances);
            check(r.rebinds == 0, "animated width callbacks must not rebind profile collections");
            check(r.sidebarGeometry > 0, "width changes still update sidebar geometry");
        } else if (args[0].equals("stable")) {
            r.layout(r.mLayoutListener, 334, 334);
            r.layout(r.mColumnLayoutListener, 334, 334);
            // Moving a rail while its dimensions stay fixed is not a geometry change.
            r.mLayoutListener.onLayoutChange(new View(), 9, 4, 343, 804, 0, 0, 334, 800);
            check(r.appearances + r.rebinds + r.sidebarGeometry + r.frameGeometry + r.controlUpdates == 0,
                    "same-size and position-only layouts must not refresh shell");
        } else if (args[0].equals("destroyed")) {
            r.mDestroyed = true;
            r.layout(r.mLayoutListener, 334, 52);
            r.layout(r.mColumnLayoutListener, 334, 52);
            check(r.appearances + r.rebinds + r.sidebarGeometry + r.frameGeometry + r.controlUpdates == 0,
                    "destroyed layout callbacks must not mutate the shell");
        } else if (args[0].equals("manual")) {
            r.layout(r.mColumnLayoutListener, 334, 370);
            check(r.sidebarGeometry > 0, "live manual resize must retain responsive geometry");
            check(r.appearances == 0 && r.rebinds == 0, "manual resize must not restyle or rebind");
            int previous = r.sidebarGeometry;
            r.mLayoutListener.onLayoutChange(new View(), 0, 0, 370, 600, 0, 0, 370, 800);
            check(r.sidebarGeometry > previous, "height-only resize must update the native tab budget");
        } else if (args[0].equals("mobile")) {
            r.mArcToolbarCompositionActive = false;
            ArcDesktopAppearance.desktop = false;
            r.layout(r.mLayoutListener, 334, 52);
            r.layout(r.mColumnLayoutListener, 334, 52);
            check(r.appearances + r.rebinds + r.sidebarGeometry + r.frameGeometry + r.controlUpdates == 0,
                    "MOBILE layout callbacks must not restore Arc geometry");
        }
    }
}
"""


class ArcSidebarAnimationCallbacksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = COORD.read_text()
        rail = method_body(source, r"mLayoutListener = \(v, l, t, r, b, ol, ot, or, ob\) ->")
        column = method_body(source, r"mColumnLayoutListener = \(v, l, t, r, b, ol, ot, or, ob\) ->")
        helpers = ""
        signature = "private void onSidebarGeometryChanged()"
        if signature in source:
            helpers = signature + " " + method_body(source, re.escape(signature))
        cls.tmp = tempfile.TemporaryDirectory(prefix="arc-sidebar-animation-")
        cls.work = Path(cls.tmp.name)
        path = cls.work / "SidebarAnimationRegression.java"
        path.write_text(JAVA.replace("HELPERS", helpers).replace("RAIL", rail).replace("COLUMN", column))
        compiled = subprocess.run(["javac", "--release", "17", "-d", str(cls.work), str(path)],
                                  capture_output=True, text=True)
        if compiled.returncode:
            raise AssertionError(compiled.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_case(self, name):
        result = subprocess.run(["java", "-ea", "-cp", str(self.work), "SidebarAnimationRegression", name],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_animated_width_does_not_restyle_or_rebind(self):
        self.run_case("animation")

    def test_same_dimensions_do_no_shell_work(self):
        self.run_case("stable")

    def test_destroyed_callbacks_do_no_shell_work(self):
        self.run_case("destroyed")

    def test_manual_resize_retains_geometry(self):
        self.run_case("manual")

    def test_mobile_callbacks_do_no_arc_work(self):
        self.run_case("mobile")
