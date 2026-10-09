import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;

/** Literal image fixtures and continuous resize invariants against the production policy. */
public final class ArcDesktopGeometryTest {
    static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    public static void main(String[] args) throws Exception {
        // Reflection gives a meaningful assertion failure before the feature exists.
        try {
            ArcDesktopPolicy.class.getMethod("expandedSidebarWidth", int.class, int.class, float.class);
        } catch (NoSuchMethodException e) {
            throw new AssertionError("Arc reference-ratio sidebar sizing is missing", e);
        }
        int width = (int) ArcDesktopPolicy.class.getMethod("expandedSidebarWidth", int.class, int.class, float.class)
                .invoke(null, 1382, 1062, 1f);
        check(width == 334, "reference sidebar must be 334 physical pixels, not fixed 240dp");
        runGeometryCases();
        runSidebarBudgetCases();
    }
    static void runGeometryCases() throws Exception {
        // Until the interface exists, execute the additional fixtures reflectively as well.
        var method = ArcDesktopPolicy.class.getMethod("geometry", int.class, int.class,
                int.class, float.class, boolean.class);
        Object g = method.invoke(null, 1382, 863, 334, 1f, false);
        check(value(g,"viewportLeft") == 334 && value(g,"viewportTop") == 12,
                "reference viewport has no artificial gap at sidebar edge");
        check(value(g,"viewportRight") == 1371 && value(g,"viewportBottom") == 852,
                "reference viewport is 1037x840 with right/bottom11");
        check(value(g,"outerRadius") == 13 && value(g,"viewportRadius") == 11,
                "reference rounding is normalized image geometry");
        check(value(g,"sideInset") == 9 && value(g,"omniboxHeight") == 49,
                "reference omnibox spans x9..325 at height49");
        check(value(g,"navigationHeight") == 48 && value(g,"headerTopInset") == 9,
                "reference navigation leaves omnibox y57 and Android48dp targets");
        check(value(g,"quickAccessHeight") == 57 && value(g,"quickAccessGap") == 9,
                "reference quick access y116 and equal-height tiles");
        check(value(g,"footerBottomInset") == 6 && value(g,"footerHeight") == 48,
                "anchored footer center is833 at H863");
        Object rtl=method.invoke(null,1382,863,334,1f,true);
        check(value(rtl,"viewportLeft")==11 && value(rtl,"viewportRight")==1048,
                "RTL mirrors physical bounds without introducing a sidebar gap");
        Object dense=method.invoke(null,2764,1726,668,2f,false);
        check(value(dense,"viewportLeft")==668 && value(dense,"viewportTop")==24
                && value(dense,"viewportRight")==2742 && value(dense,"viewportBottom")==1704,
                "2x window and density scales reference composition");
        check(value(dense,"navigationHeight")>=96,"density sets touch targets, not screenshot pixels");
        Object collapsed=method.invoke(null,1382,863,52,1f,false);
        check(value(collapsed,"viewportLeft")==52,"collapsed native width remains52dp");
        var sidebar=ArcDesktopPolicy.class.getMethod("expandedSidebarWidth",int.class,int.class,float.class);
        int previous=0;
        for(int w=372;w<=3000;w++) {
            int s=(int)sidebar.invoke(null,w,w-320,1f);
            check(s>=0 && s<=w-320 && s>=previous,"continuous width respects content budget and monotonic sizing");
            Object resized=method.invoke(null,w,863,s,1f,false);
            check(value(resized,"viewportLeft")==s,"resize never uses obsolete sidebar width");
            previous=s;
        }
        for(int h=0;h<=1000;h++) {
            Object resized=method.invoke(null,1382,h,334,1f,false);
            check(value(resized,"viewportBottom")>=value(resized,"viewportTop"),"short windows never produce negative viewport height");
            check(value(resized,"viewportBottom")<=h,"vertical clipping stays within measured window");
        }
        check((int)sidebar.invoke(null,1382,1062,Float.NaN)==0,"invalid density fails closed");
        check((int)sidebar.invoke(null,1382,1062,Float.POSITIVE_INFINITY)==0,"infinite density fails closed");
        System.out.println("PASS Arc geometry: reference, scaling, RTL/LTR, collapsed and continuous resize");
    }
    static void runSidebarBudgetCases() throws Exception {
        java.lang.reflect.Method budget;
        try { budget=ArcDesktopPolicy.class.getMethod("sidebarBudget",int.class,int.class,int.class,float.class); }
        catch(NoSuchMethodException e){throw new AssertionError("short-window tab budget is missing",e);}
        Object normal=budget.invoke(null,863,40,300,1f);
        check(value(normal,"headerHeight")==245 && value(normal,"footerHeight")==48,
                "normal desktop leaves tab list flexible and footer anchored");
        Object reference=budget.invoke(null,863,0,505,1f);
        check(value(reference,"headerHeight")==257 && value(reference,"tabHeight")==558,
                "secondary collections must not push native tabs far below the305px reference band");
        Object shortWindow=budget.invoke(null,180,40,180,1f);
        check(value(shortWindow,"headerHeight")<=92 && value(shortWindow,"footerHeight")==0,
                "short windows hide utility footer before starving tabs");
        for(int height=1;height<1000;height++) {
            Object b=budget.invoke(null,height,0,800,1f);
            check(value(b,"tabHeight")>0,"positive content height retains a positive tab allocation");
            check(value(b,"headerHeight")+value(b,"footerHeight")+value(b,"tabHeight")==height,
                    "responsive chrome budget exactly partitions available height");
        }
        Object caption=budget.invoke(null,863,40,300,1f);
        check(value(caption,"headerHeight")+value(caption,"footerHeight")+value(caption,"tabHeight")==823,
                "caption is counted once outside flexible sidebar content");
    }
    static int value(Object obj,String field)throws Exception {
        return obj.getClass().getField(field).getInt(obj);
    }
}
