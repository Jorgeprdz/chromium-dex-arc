"""Extract the shipped Java methods for executable, explicitly bounded crash probes."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TOOLBAR = 'chrome/browser/ui/android/toolbar/java/src/org/chromium/chrome/browser/toolbar/top/ToolbarLayout.java'
TABBED = 'chrome/android/java/src/org/chromium/chrome/browser/tabbed_mode/TabbedRootUiCoordinator.java'


def method_body(text, signature):
    match = re.search(signature, text)
    if match is None:
        raise ValueError('Production method not found: ' + signature)
    start = text.index('{', match.start())
    depth = 1
    end = start + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


def toolbar_body():
    path = ROOT / '.source-modified' / TOOLBAR
    if not path.exists():
        path = ROOT / '.source-reference' / TOOLBAR
    return method_body(path.read_text(), r'void getLocationBarContentRect\(Rect outRect\)')


def transition_bodies():
    text = (ROOT / '.source-modified' / TABBED).read_text()
    active = method_body(text, r'private void onVerticalTabsActiveChanged\(boolean active\)')
    clear = method_body(text, r'private void maybeClearPendingTabStripUnsuppression\(\)')
    preference = method_body(
        text[text.index('mVerticalTabsPreferenceListener ='):], r'\(prefs, key\) ->')
    return active, clear, preference
