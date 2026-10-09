"""Execute shipped native tab icon and passive input callbacks with bounded view doubles.

Exercises input routing/visibility, not rendered device appearance or frame timing.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from arc_toolbar_probe import ROOT, method_body

NATIVE = ROOT / '.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/TabVerticalViewBinder.java'

class ArcTabInteractionTest(unittest.TestCase):
    def test_native_mouse_focus_touch_close_and_event_preservation(self):
        source = NATIVE.read_text()
        signatures = [
            'private static void updateIcons(\n            PropertyModel model, VerticalTabItemLayout view, boolean isHovered)',
            'private static void updateIcons(PropertyModel model, VerticalTabItemLayout view)',
            'private static void setNullableClickListener(\n            @Nullable TabActionListener listener, View view, PropertyModel propertyModel)',
            'private static void setupTabHoverListener(\n            PropertyModel model,\n            VerticalTabItemLayout view,\n            @Nullable ColorStateList defaultBackgroundColor)',
        ]
        helpers = '\n'.join(sig + ' ' + method_body(source, re.escape(sig)) for sig in signatures)
        helpers = helpers.replace('model.get(TabProperties.IS_LOADING)', '(boolean) model.get(TabProperties.IS_LOADING)')
        helpers = helpers.replace('@Nullable ', '').replace('@ColorInt', '').replace('(View _,', '(View ignored,').replace('(View _)','(View ignored)')
        program = r'''
import java.util.*;
import java.util.function.*;
class TabInteractionProbe {
    static class Context {}
    interface Touch {boolean run(View v,MotionEvent e);}
    static class View {interface OnFocusChangeListener {void onFocusChange(View v,boolean f);}
        final Context context=new Context();OnFocusChangeListener focus;Touch touch;Consumer<View> click;boolean hovered,focused;Context getContext(){return context;}
        OnFocusChangeListener getOnFocusChangeListener(){return focus;}void setOnFocusChangeListener(OnFocusChangeListener l){focus=l;}void setOnTouchListener(Touch t){touch=t;}void setOnClickListener(Consumer<View> c){click=c;}boolean isHovered(){return hovered;}boolean hasFocus(){return focused;}}
    static class ViewGroup extends View {}
    static class ImageView extends View {}
    static class ColorStateList {}
    static class MotionEvent {static final int ACTION_DOWN=0,TOOL_TYPE_MOUSE=3,TOOL_TYPE_FINGER=1;int tool;MotionEvent(int t){tool=t;}int getActionMasked(){return ACTION_DOWN;}int getToolType(int i){return tool;}}
    static class MotionEventInfo {final MotionEvent event;MotionEventInfo(MotionEvent e){event=e;}static MotionEventInfo fromMotionEvent(MotionEvent e){return new MotionEventInfo(e);}}
    interface TabActionListener {void run(View v,int id,MotionEventInfo m);}
    interface TabHoverListener {}
    static class VerticalTabItemHoverController {static View.OnFocusChangeListener nativeFocus;static int focusEvents;static Consumer<Boolean> visual;static void setupTabHover(TabHoverListener l,int id,ViewGroup v,View a,Consumer<Boolean> cb){visual=cb;nativeFocus=(row,f)->focusEvents++;v.setOnFocusChangeListener(nativeFocus);}}
    static class VerticalTabItemLayout extends ViewGroup {ImageView action=new ImageView();boolean pinned,compact,showAction,showAlert,showLoading,showFavicon;ImageView getActionButton(){return action;}boolean isPinned(){return pinned;}
        View findViewById(int id){return id==R.id.action_button?action:new View();}
        void updateIconDisplay(boolean compact,boolean close,boolean alert,boolean actor,boolean loading,int color,boolean favicon){showAction=close;showAlert=alert;showLoading=loading;showFavicon=favicon;}}
    static class PropertyModel {Map<Integer,Object> values=new HashMap<>();@SuppressWarnings("unchecked")<T>T get(int key){return (T)values.get(key);}boolean containsKey(int key){return values.containsKey(key);}}
    static class TabProperties {static final int IS_SELECTED=1,TAB_ACTION_BUTTON_DATA=2,ALERT_STATE=3,IS_LOADING=4,FAVICON_FETCHER=5,TAB_ID=6,TAB_HOVER_LISTENER=7;}
    static class TabActionButtonData {}
    static class R {static class id {static final int action_button=1,alert_indicator_icon=2,tab_loading_spinner=3,tab_favicon=4;}}
    static class DeviceInfo {static boolean desktop=true;static boolean isDesktop(){return desktop;}}
    static class ArcDesktopAppearance {static boolean desktop=true;static boolean isDesktopWindow(Context c){return desktop;}}
    @interface TabAlert {static final int NONE=0,ACTOR_ACCESSING=1;}
    static class Color {static final int TRANSPARENT=0;}
    static final WeakHashMap<View,Boolean> sArcPointerRows=new WeakHashMap<>();
    static boolean isPinned(PropertyModel m,VerticalTabItemLayout v){return v.pinned;}
    static boolean shouldShowIconOnly(PropertyModel m,VerticalTabItemLayout v){return v.compact;}
    static int getLoadingSpinnerColor(PropertyModel m,Context c){return 0;}
    static void applyHoverBackgroundState(PropertyModel m,ViewGroup v,boolean h,ColorStateList c){}
    HELPERS
    static void check(boolean c,String s){if(!c)throw new AssertionError(s);}
    public static void main(String[]args){
        var view=new VerticalTabItemLayout();var model=new PropertyModel();model.values.put(TabProperties.IS_SELECTED,true);model.values.put(TabProperties.TAB_ACTION_BUTTON_DATA,new TabActionButtonData());model.values.put(TabProperties.IS_LOADING,false);model.values.put(TabProperties.FAVICON_FETCHER,new Object());model.values.put(TabProperties.TAB_ID,42);
        updateIcons(model,view,false);check(!view.showAction,"Arc desktop selected close must be contextual at rest");
        updateIcons(model,view,true);check(view.showAction,"hover close remains available");
        updateIcons(model,view,false);setupTabHoverListener(model,view,null);view.focused=true;view.focus.onFocusChange(view,true);check(view.showAction,"keyboard focus immediately reveals close");view.focused=false;view.focus.onFocusChange(view,false);check(!view.showAction,"keyboard focus exit returns contextual close");check(VerticalTabItemHoverController.focusEvents==2,"native focus listener runs exactly once per event");
        for(int bind=0;bind<200;bind++)setupTabHoverListener(model,view,null);
        view.focused=true;view.focus.onFocusChange(view,true);view.focused=false;view.focus.onFocusChange(view,false);
        check(VerticalTabItemHoverController.focusEvents==4,"repeated row binding must not stack native focus wrappers");
        setupTabHoverListener(model,view,null);DeviceInfo.desktop=false;view.hovered=true;VerticalTabItemHoverController.visual.accept(true);view.hovered=false;VerticalTabItemHoverController.visual.accept(false);
        check(!view.showAction,"mouse on touch-capable desktop remains contextual after hover exit");
        final int[] clicks={0};final MotionEventInfo[] forwarded={null};setNullableClickListener((v,id,event)->{check(id==42,"native tab identity");clicks[0]++;forwarded[0]=event;},view,model);
        MotionEvent touch=new MotionEvent(MotionEvent.TOOL_TYPE_FINGER);check(!view.touch.run(view,touch),"passive tracker must not consume native touch");
        check(view.showAction,"touch immediately restores accessible close on hybrid desktop");view.click.accept(view);check(clicks[0]==1&&forwarded[0].event==touch,"native click gets exact last input once");
        MotionEvent mouse=new MotionEvent(MotionEvent.TOOL_TYPE_MOUSE);check(!view.touch.run(view,mouse),"mouse native event preserved");check(!view.showAction,"mouse press uses contextual close");
        view.compact=true;view.touch.run(view,touch);check(view.showAction,"selected collapsed touch tab remains closable");model.values.put(TabProperties.IS_SELECTED,false);updateIcons(model,view,false);check(!view.showAction,"collapsed inactive tab keeps favicon priority");
        view.pinned=true;updateIcons(model,view,true);check(!view.showAction,"pinned tabs retain native no-close rule");view.pinned=false;view.compact=false;
        ArcDesktopAppearance.desktop=false;DeviceInfo.desktop=true;model.values.put(TabProperties.IS_SELECTED,true);updateIcons(model,view,false);check(view.showAction,"MOBILE preserves native desktop selected close");setupTabHoverListener(model,view,null);check(view.getOnFocusChangeListener()==VerticalTabItemHoverController.nativeFocus,"MOBILE restores exact native focus listener");
        model.values.put(TabProperties.IS_SELECTED,false);view.focused=true;view.hovered=false;
        VerticalTabItemHoverController.visual.accept(false);
        check(!view.showAction,"MOBILE unselected focused row retains native hover-exit close visibility");
        setNullableClickListener(null,view,model);check(view.touch==null&&view.click==null,"native clear listeners stays exact");
        System.out.println("PASS native hybrid close and event routing");
    }
}
'''.replace('HELPERS', helpers)
        with tempfile.TemporaryDirectory(prefix='arc-close-') as tmp:
            p=Path(tmp)/'TabInteractionProbe.java';p.write_text(program)
            result=subprocess.run(['javac','--release','17','-d',tmp,str(p)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run(['java','-ea','-cp',tmp,'TabInteractionProbe'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_focus_helper_nullable_nested_type_compiles_against_android37(self):
        import os
        jar=Path(os.environ.get('ANDROID_HOME','/opt/android-sdk'))/'platforms/android-37.0/android.jar'
        if not jar.exists():self.skipTest('Android37 API jar unavailable')
        signature='private static void setupTabHoverListener(\n            PropertyModel model,\n            VerticalTabItemLayout view,\n            @Nullable ColorStateList defaultBackgroundColor)'
        helper=signature+' '+method_body(NATIVE.read_text(),re.escape(signature))
        self.assertIn('View.@Nullable OnFocusChangeListener nativeFocus',helper,
                      'nullable getter result needs TYPE_USE annotation on the nested listener type')
        program=r'''
import android.content.Context;
import android.content.res.ColorStateList;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import java.util.WeakHashMap;
import java.util.function.Consumer;
import org.chromium.build.annotations.Nullable;
class FocusAndroidApiProbe {
    static class VerticalTabItemLayout extends ViewGroup {
        VerticalTabItemLayout(Context c){super(c);}
        protected void onLayout(boolean changed,int l,int t,int r,int b){}
        boolean isPinned(){return false;}
        ImageView getActionButton(){return new ImageView(getContext());}
    }
    static class PropertyModel {<T>T get(int key){return null;}}
    static class TabProperties {static final int TAB_ID=1,TAB_HOVER_LISTENER=2;}
    interface TabHoverListener {}
    static class VerticalTabItemHoverController {static void setupTabHover(TabHoverListener listener,int id,ViewGroup view,View action,Consumer<Boolean> cb){}}
    static class ArcDesktopAppearance {static boolean isDesktopWindow(Context c){return true;}}
    static final WeakHashMap<View,Boolean> sArcPointerRows=new WeakHashMap<>();
    static void applyHoverBackgroundState(PropertyModel model,ViewGroup view,boolean hovered,ColorStateList color){}
    static void updateIcons(PropertyModel model,VerticalTabItemLayout view,boolean hovered){}
    HELPER
}
'''.replace('HELPER',helper)
        with tempfile.TemporaryDirectory(prefix='arc-focus-android37-') as tmp:
            path=Path(tmp)
            nullable=path/'org/chromium/build/annotations/Nullable.java'
            nullable.parent.mkdir(parents=True)
            nullable.write_text('''package org.chromium.build.annotations;
import java.lang.annotation.ElementType;
import java.lang.annotation.Target;
@Target(ElementType.TYPE_USE) public @interface Nullable {}
''')
            p=path/'FocusAndroidApiProbe.java';p.write_text(program)
            compiled=subprocess.run(['javac','--release','17','-cp',str(jar),'-d',tmp,str(nullable),str(p)],capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            # Negative control verifies this is a real nested TYPE_USE boundary, not a
            # declaration-annotation double that would accept the previously broken syntax.
            p.write_text(program.replace('View.@Nullable OnFocusChangeListener nativeFocus',
                                         '@Nullable View.OnFocusChangeListener nativeFocus'))
            rejected=subprocess.run(['javac','--release','17','-cp',str(jar),'-d',tmp,str(nullable),str(p)],capture_output=True,text=True)
            self.assertNotEqual(rejected.returncode,0,'incorrect outer placement must fail against real Android View nested type')
            self.assertIn('scoping construct cannot be annotated',rejected.stderr)
