package org.chromium.chrome.browser.arc;
import static org.junit.Assert.*;
import android.app.Activity;
import android.content.ContextWrapper;
import android.content.res.Resources;
import android.view.View;
import android.widget.PopupMenu;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowPopupMenu;
import org.chromium.chrome.browser.content.ContentUtils;
import org.chromium.content_public.browser.WebContents;
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcCameraControlsHostTest {
 private org.robolectric.android.controller.ActivityController<Activity> activity;
 private View anchor;
 @Before public void setup() {
  activity=Robolectric.buildActivity(Activity.class).setup();
  Resources real=activity.get().getResources();
  Resources strings=new Resources(real.getAssets(),real.getDisplayMetrics(),real.getConfiguration()) {
   @Override public String getString(int id,Object... args) {
    String value=org.chromium.chrome.R.labels.get(id);
    return value==null?super.getString(id,args):String.format(value,args);
   }
   @Override public CharSequence getText(int id) {
    String value=org.chromium.chrome.R.labels.get(id);
    return value==null?super.getText(id):value;
   }
  };
  anchor=new View(new ContextWrapper(activity.get()) {
   @Override public Resources getResources(){return strings;}
  });
  activity.get().setContentView(anchor);
 }
 @After public void cleanup(){PopupMenu popup=ShadowPopupMenu.getLatestPopupMenu();if(popup!=null)popup.dismiss();if(activity!=null)activity.pause().stop().destroy();}
 @Test public void onlyExplicitAnglesAppearAndEveryChoiceWritesItsOwnQuarterTurns() {
  WebContents tab=new WebContents();tab.turns=2;
  ArcCameraControls.show(anchor,tab);
  PopupMenu popup=ShadowPopupMenu.getLatestPopupMenu();
  assertEquals(3,popup.getMenu().size());
  String[] titles={"90°","180°","270°"};
  for(int index=0;index<3;index++) {
   var item=popup.getMenu().getItem(index);
   assertEquals(titles[index],item.getTitle());assertTrue(item.isCheckable());assertTrue(item.isEnabled());
   assertEquals(index==1,item.isChecked());
   assertTrue(popup.getMenu().performIdentifierAction(item.getItemId(),0));
   assertEquals(index+1,tab.turns);
  }
 }
 @Test public void selectionSurvivesReopeningAndNeverLeaksAcrossTabs() {
  WebContents first=new WebContents(),second=new WebContents();first.turns=3;second.turns=1;
  ArcCameraControls.show(anchor,first);
  PopupMenu popup=ShadowPopupMenu.getLatestPopupMenu();assertTrue(popup.getMenu().getItem(2).isChecked());popup.dismiss();
  ArcCameraControls.show(anchor,second);popup=ShadowPopupMenu.getLatestPopupMenu();assertTrue(popup.getMenu().getItem(0).isChecked());
  assertEquals(3,first.turns);assertEquals(1,second.turns);
 }
 @Test public void destroyedTabCannotBeChangedAfterOpening() {
  WebContents tab=new WebContents();tab.turns=2;ArcCameraControls.show(anchor,tab);
  var popup=ShadowPopupMenu.getLatestPopupMenu();tab.destroyed=true;
  popup.getMenu().performIdentifierAction(popup.getMenu().getItem(0).getItemId(),0);
  assertEquals(2,tab.turns);
 }
 @Test public void legacyZeroAngleIsNotSilentlyRewrittenByOpening() {
  WebContents tab=new WebContents();tab.turns=0;ArcCameraControls.show(anchor,tab);
  assertEquals(0,tab.turns);
  var menu=ShadowPopupMenu.getLatestPopupMenu().getMenu();
  for(int i=0;i<menu.size();i++)assertFalse(menu.getItem(i).isChecked());
 }
}
