#!/usr/bin/env python3
"""Exercise delivered footer layout, late attachment and restoration on real Android views."""
import argparse,importlib.util,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from arc_toolbar_probe import method_body
p=argparse.ArgumentParser();p.add_argument('--classpath-file',type=Path,required=True);p.add_argument('--java-home',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True)
s=(ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java').read_text()
layout=method_body(s,r'private void layoutFooter\(') if 'private void layoutFooter(' in s else '{'+s[s.index('        mFooter.setVisibility(View.VISIBLE);',s.index('// The native app menu remains reachable')):s.index('        if (mCollectionsView != null)',s.index('// The native app menu remains reachable'))]+'}'
f=r'''
import static org.junit.Assert.*;
import android.app.Activity;import android.view.*;import android.widget.*;
import org.junit.*;import org.junit.runner.RunWith;import org.robolectric.*;import org.robolectric.annotation.*;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
import androidx.recyclerview.widget.RecyclerView;
class R {static class id {static final int toolbar=1234,extensions_toolbar_container=1235;}}
class ToolbarTablet extends View {int width=-1;ToolbarTablet(android.content.Context c){super(c);}void updateArcExtensionsWidth(int n){width=n;}void clearArcExtensionsWidth(){width=-1;}}
@RunWith(RobolectricTestRunner.class) @Config(manifest=Config.NONE,sdk={30,36})
@GraphicsMode(GraphicsMode.Mode.LEGACY) @SQLiteMode(SQLiteMode.Mode.LEGACY)
public class DesktopFooterProbe {
 Activity activity;org.robolectric.android.controller.ActivityController<Activity> controller;
 @Before public void setup(){controller=Robolectric.buildActivity(Activity.class).setup();activity=controller.get();}
 @After public void close(){controller.pause().stop().destroy();}
 static class Shell {
 Activity mActivity;LinearLayout mFooter,mBrowserControlsRow,mExtensionsRow,mColumn,mNavigationRow,mHeader;
 ViewGroup mRail,mMenuButtonOriginalParent,mExtensionsToolbarOriginalParent;
 View mMenuButtonWrapper,mExtensionsToolbarHost,mCollapseButton,mLocationBarHost;
 int mMenuButtonOriginalMinimumWidth;
 int mMenuButtonOriginalIndex,mExtensionsToolbarOriginalIndex,mExtensionsToolbarOriginalVisibility;
 ViewGroup.LayoutParams mMenuButtonOriginalLayoutParams,mExtensionsToolbarOriginalLayoutParams;
 boolean mArcToolbarCompositionActive=true;View camera,about,appearance;ToolbarTablet toolbar;
 Shell(Activity a){mActivity=a;LinearLayout root=new LinearLayout(a);a.setContentView(root);
 mRail=new LinearLayout(a);mRail.layout(0,0,216,800);mRail.setPadding(4,0,4,0);
 toolbar=new ToolbarTablet(a);toolbar.setId(R.id.toolbar);root.addView(toolbar);
 mMenuButtonOriginalParent=new LinearLayout(a);root.addView(mMenuButtonOriginalParent);
 mMenuButtonWrapper=new View(a);mMenuButtonOriginalLayoutParams=new LinearLayout.LayoutParams(44,44);
 mMenuButtonOriginalParent.addView(mMenuButtonWrapper,mMenuButtonOriginalLayoutParams);
 ROWS
 root.addView(mFooter);root.getViewTreeObserver().addOnGlobalLayoutListener(this::observeExtensions);
 camera=new View(a);about=new View(a);appearance=new View(a);
 for(View v:new View[]{camera,about,appearance})mBrowserControlsRow.addView(v,new LinearLayout.LayoutParams(44,44));
 mColumn=new LinearLayout(a);mNavigationRow=new LinearLayout(a);mHeader=new LinearLayout(a);mHeader.addView(new View(a));
 mCollapseButton=new View(a);mLocationBarHost=new View(a);attachToolbarControlsToArc();}
 void scheduleAppearance(){ensureExtensionsToolbar();layoutFooter(ArcDesktopPolicy.showFullControls(mRail.getWidth(),mRail.getHeight(),1));}
 void observeExtensions() { OBSERVE }
 int dp(int n){return n;}
 LinearLayout.LayoutParams arcLocationBarLayoutParams(){return new LinearLayout.LayoutParams(-1,44);}
 int compactFooterExtraHeightPx() COMPACT_BUDGET
 boolean canExpandControls() CAN_EXPAND
 void layoutFooter(boolean expanded) LAYOUT
 void ensureExtensionsToolbar() ENSURE
 void attachToolbarControlsToArc() ATTACH
 void restoreToolbarUtilityControls() RESTORE
 HELPERS
 View addNativeHost(int visibility){LinearLayout nativeParent=new LinearLayout(mActivity);((ViewGroup)mFooter.getParent()).addView(nativeParent);
 LinearLayout host=new LinearLayout(mActivity);host.setId(R.id.extensions_toolbar_container);host.setVisibility(visibility);
 View action=new View(mActivity);host.addView(action,new LinearLayout.LayoutParams(44,44));nativeParent.addView(host,new LinearLayout.LayoutParams(99,55));return host;}
 }
 static class NativeActions extends RecyclerView.Adapter<RecyclerView.ViewHolder> {
 int count;
 public int getItemCount(){return count;}
 public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){return new RecyclerView.ViewHolder(new View(parent.getContext())){};}
 public void onBindViewHolder(RecyclerView.ViewHolder holder,int position){}
 }
 @Test public void hiddenRowOpensForFirstNativeAdapterItemBeforeChildrenAttach(){Shell s=new Shell(activity);ViewGroup host=(ViewGroup)s.addNativeHost(View.VISIBLE);
 host.getChildAt(0).setVisibility(View.GONE); // Native puzzle/access buttons remain hidden.
 RecyclerView list=new RecyclerView(activity);NativeActions actions=new NativeActions();list.setAdapter(actions);host.addView(list,new LinearLayout.LayoutParams(-1,44));
 s.ensureExtensionsToolbar();s.layoutFooter(true);assertEquals(View.GONE,s.mExtensionsRow.getVisibility());assertEquals(0,list.getChildCount());
 actions.count=1;actions.notifyItemInserted(0);s.mFooter.getViewTreeObserver().dispatchOnGlobalLayout();
 assertEquals("Native actions must open their row before RecyclerView can attach children",View.VISIBLE,s.mExtensionsRow.getVisibility());assertEquals(0,list.getChildCount());
 actions.count=0;actions.notifyItemRemoved(0);s.mFooter.getViewTreeObserver().dispatchOnGlobalLayout();assertEquals(View.GONE,s.mExtensionsRow.getVisibility());}
 @Test public void expandedRowsReuseNativeHostAndFullWidth(){Shell s=new Shell(activity);View host=s.addNativeHost(View.VISIBLE);s.ensureExtensionsToolbar();s.layoutFooter(true);
 assertNotSame("native extensions need a separate second row",s.mMenuButtonWrapper.getParent(),host.getParent());
 assertSame(s.mBrowserControlsRow,s.mMenuButtonWrapper.getParent());assertSame(s.mExtensionsRow,host.getParent());
 assertSame(s.mMenuButtonWrapper,s.mBrowserControlsRow.getChildAt(0));assertEquals(4,s.mBrowserControlsRow.getChildCount());
 assertEquals(208,s.toolbar.width);assertEquals(44,host.getLayoutParams().height);
 s.mFooter.measure(View.MeasureSpec.makeMeasureSpec(208,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.AT_MOST));
 s.mFooter.layout(0,0,208,s.mFooter.getMeasuredHeight());assertEquals(92,s.mFooter.getMeasuredHeight());
 assertEquals(48,s.mExtensionsRow.getTop());}
 @Test public void nativeGoneHostNeverForcedVisibleAndEmptyRowHidden(){Shell s=new Shell(activity);View h=s.addNativeHost(View.GONE);s.ensureExtensionsToolbar();s.layoutFooter(true);
 assertEquals(View.GONE,h.getVisibility());assertEquals(View.GONE,s.mExtensionsRow.getVisibility());
 h.setVisibility(View.VISIBLE);s.layoutFooter(true);assertEquals(View.VISIBLE,s.mExtensionsRow.getVisibility());
 ((ViewGroup)h).getChildAt(0).setVisibility(View.GONE);s.layoutFooter(true);assertEquals(View.GONE,s.mExtensionsRow.getVisibility());}
 @Test public void compactKeepsMenuAndTargetsWithoutChangingNativeAvailability(){Shell s=new Shell(activity);View h=s.addNativeHost(View.VISIBLE);s.ensureExtensionsToolbar();s.layoutFooter(false);
 assertEquals(View.VISIBLE,h.getVisibility());assertEquals(View.GONE,s.mExtensionsRow.getVisibility());
 assertEquals(View.VISIBLE,s.mMenuButtonWrapper.getVisibility());assertEquals(44,s.mMenuButtonWrapper.getLayoutParams().height);
 s.layoutFooter(true);assertEquals(View.VISIBLE,s.mExtensionsRow.getVisibility());}
 @Test public void restoreLateAttachmentAndRepeatedDesktopEntryPreserveIdentityAndListeners(){Shell s=new Shell(activity);View h=s.addNativeHost(View.VISIBLE);ViewGroup parent=(ViewGroup)h.getParent();ViewGroup.LayoutParams lp=h.getLayoutParams();int[] clicks={0};h.setOnClickListener(v->clicks[0]++);
 s.ensureExtensionsToolbar();s.layoutFooter(true);s.restoreToolbarUtilityControls();assertSame(parent,h.getParent());assertSame(lp,h.getLayoutParams());assertEquals(View.VISIBLE,h.getVisibility());
 s.attachToolbarControlsToArc();s.layoutFooter(true);s.attachToolbarControlsToArc();assertEquals(1,s.mExtensionsRow.getChildCount());
 h.performClick();assertEquals(1,clicks[0]);s.restoreToolbarUtilityControls();assertSame(parent,h.getParent());}
 @Test public void nativeAvailabilityChangesUseExistingGlobalLayoutObserver(){Shell s=new Shell(activity);View h=s.addNativeHost(View.GONE);s.ensureExtensionsToolbar();s.layoutFooter(true);
 assertEquals(View.GONE,s.mExtensionsRow.getVisibility());h.setVisibility(View.VISIBLE);s.mFooter.getViewTreeObserver().dispatchOnGlobalLayout();assertEquals(View.VISIBLE,s.mExtensionsRow.getVisibility());
 ((ViewGroup)h).getChildAt(0).setVisibility(View.GONE);s.mFooter.getViewTreeObserver().dispatchOnGlobalLayout();assertEquals(View.GONE,s.mExtensionsRow.getVisibility());}
 @Test public void absentHostAndShortWindowRetainMenuSpace(){Shell s=new Shell(activity);s.layoutFooter(true);assertEquals(View.GONE,s.mExtensionsRow.getVisibility());
 s.mRail.layout(0,0,216,300);s.layoutFooter(false);assertEquals(View.VISIBLE,s.mMenuButtonWrapper.getVisibility());assertEquals(View.GONE,s.camera.getVisibility());
 s.mFooter.measure(View.MeasureSpec.makeMeasureSpec(208,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(300,View.MeasureSpec.AT_MOST));assertEquals(44,s.mFooter.getMeasuredHeight());}
 @Test public void restorationRetainsLatestNativeVisibility(){Shell s=new Shell(activity);View h=s.addNativeHost(View.VISIBLE);ViewGroup parent=(ViewGroup)h.getParent();s.ensureExtensionsToolbar();s.layoutFooter(true);
 h.setVisibility(View.GONE);s.restoreToolbarUtilityControls();assertSame(parent,h.getParent());assertEquals(View.GONE,h.getVisibility());}
 @Test public void compactFooterReservesEveryVisibleSecondaryRow(){Shell s=new Shell(activity);s.mRail.layout(0,0,52,800);s.layoutFooter(false);assertEquals(132,s.compactFooterExtraHeightPx());
 s.mRail.layout(0,0,52,300);s.layoutFooter(false);assertEquals(0,s.compactFooterExtraHeightPx());}
 @Test public void measuredNativeMenuWidthDecidesFullControls(){Shell s=new Shell(activity);s.mRail.layout(0,0,176,800);s.mRail.setPadding(0,0,0,0);
 s.mMenuButtonWrapper.measure(View.MeasureSpec.makeMeasureSpec(48,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(44,View.MeasureSpec.EXACTLY));
 assertFalse("48px native menu +132px controls need180px",s.canExpandControls());s.mRail.layout(0,0,180,800);assertTrue(s.canExpandControls());}
 @Test public void fractionalDensityReservesEachMeasuredRowAndGap(){assertEquals(127,
 ArcDesktopPolicy.collectionScrollBudgetPx(1600,2.625f,0,false)-ArcDesktopPolicy.collectionScrollBudgetPx(1600,2.625f,0,true));}
 @Test public void extraRowReservedBeforeCollections(){assertEquals(304,ArcDesktopPolicy.collectionScrollBudgetPx(700,1,0,true));assertEquals(352,ArcDesktopPolicy.collectionScrollBudgetPx(700,1,0,false));}
}
'''
rows='mFooter=new LinearLayout(a);mFooter.setOrientation(LinearLayout.VERTICAL);mBrowserControlsRow=mFooter;mExtensionsRow=mFooter;'
if 'private void layoutFooter(' in s:
 rows=s[s.index('        mFooter = new LinearLayout(activity);'):s.index('        // VerticalTabRailLayout already owns',s.index('        mFooter = new LinearLayout(activity);'))].replace('(activity)','(a)')
helpers=''
for name in ['attachExtensionsToolbarToArc','hasVisibleExtensionActions']:
 if re.search(r'private (?:static )?\w+ '+name+r'\(',s):
  signature=re.search(r'private ((?:static )?\w+ '+name+r'\([^)]*\))',s).group(1)
  helpers+=signature+' '+method_body(s,r'private (?:static )?\w+ '+name+r'\(')+'\n'
observe=s[s.index('            if (mExtensionsToolbarHost == null',s.index('mFontLayoutListener =')):s.index('            View controls =',s.index('mFontLayoutListener ='))]
for key,value in {'COMPACT_BUDGET':method_body(s,r'private int compactFooterExtraHeightPx\(') if 'private int compactFooterExtraHeightPx(' in s else '{return 0;}', 'CAN_EXPAND':method_body(s,r'private boolean canExpandControls\(') if 'private boolean canExpandControls(' in s else '{return ArcDesktopPolicy.showFullControls(mRail.getWidth(),mRail.getHeight(),1);}', 'OBSERVE':observe,'ROWS':rows,'LAYOUT':layout,'ENSURE':method_body(s,r'private void ensureExtensionsToolbar\('),'ATTACH':method_body(s,r'private void attachToolbarControlsToArc\('),'RESTORE':method_body(s,r'private void restoreToolbarUtilityControls\('),'HELPERS':helpers}.items():f=f.replace(key,value)
policy=next(ROOT.glob('chromium/**/ArcDesktopPolicy.java'))
# The baseline has no row-aware overload: retain its real old budget for the RED comparison.
if 'int captionHeight, boolean' not in policy.read_text():f=f.replace('700,1,0,true','700,1,0').replace('700,1,0,false','700,1,0')
java=a.work/'DesktopFooterProbe.java';java.write_text(f);classes=a.work/'classes';classes.mkdir(exist_ok=True);cp=a.classpath_file.read_text().strip()
spec=importlib.util.spec_from_file_location('window_core',ROOT/'scripts/fetch-window-core.py');window_core=importlib.util.module_from_spec(spec);spec.loader.exec_module(window_core);cp+=':'+str(window_core.ensure_jar())
from footer_androidx import prepare
androidx_jars,androidx_sources=prepare(a.work.parent/'footer-androidx');cp+=':'+':'.join(map(str,androidx_jars))
subprocess.run([str(a.java_home/'bin/javac'),'-cp',cp,'-d',str(classes),str(java),str(policy),str(next(ROOT.glob('chromium/**/ArchiumWindowClass.java'))),*map(str,androidx_sources)],check=True)
r=subprocess.run([str(a.java_home/'bin/java'),'-ea','-Drobolectric.conscryptMode=OFF','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(classes)+':'+cp,'org.junit.runner.JUnitCore','DesktopFooterProbe']);print('SCOPE=real Android footer views; delivered layout/attach/restore methods; not APK or physical-device evidence');raise SystemExit(r.returncode)
