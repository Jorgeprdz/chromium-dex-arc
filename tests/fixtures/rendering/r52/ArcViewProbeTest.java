import static org.junit.Assert.*;
import android.app.Activity;
import android.view.View;
import android.view.SurfaceView;
import android.widget.EditText;
import android.widget.FrameLayout;
import org.archium.forensics.ArcViewProbe;
import org.json.JSONObject;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36},qualifiers="mdpi")
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcViewProbeTest {
    @Test public void capturesZeroAlphaAndZWithoutPrivateText() throws Exception {
        var controller=Robolectric.buildActivity(Activity.class).setup();
        try {
            Activity activity=controller.get();
            FrameLayout root=new FrameLayout(activity);activity.setContentView(root);
            EditText dialog=new EditText(activity);
            dialog.setText("SECRET_PASSWORD user@example.com https://private/?token=SECRET");
            dialog.setHint("SECRET_HINT");root.addView(dialog);
            root.layout(0,0,400,600);dialog.layout(0,0,0,0);
            dialog.setElevation(24);dialog.setTranslationZ(2);dialog.setAlpha(0);
            JSONObject report=ArcViewProbe.capture(activity,root,20);
            JSONObject node=report.getJSONArray("nodes").getJSONObject(1);
            assertEquals(0,node.getInt("width"));assertEquals(0,node.getInt("height"));
            assertEquals(26,node.getDouble("z"),0.01);assertEquals(0,node.getDouble("alpha"),0.01);
            assertFalse(report.toString().contains("SECRET"));
            assertFalse(report.toString().contains("user@example"));
            assertEquals("NOT_OBSERVED",report.getString("surface_control_order"));
        } finally {controller.pause().stop().destroy();}
    }
    @Test public void boundsBudgetAndVisibilityAreExplicit() throws Exception {
        var controller=Robolectric.buildActivity(Activity.class).setup();
        try {
            Activity a=controller.get();FrameLayout root=new FrameLayout(a);a.setContentView(root);
            View child=new View(a);root.addView(child);root.layout(0,0,400,600);
            child.layout(410,0,510,100);child.setVisibility(View.INVISIBLE);
            JSONObject result=ArcViewProbe.capture(a,root,2);
            JSONObject node=result.getJSONArray("nodes").getJSONObject(1);
            assertEquals(410,node.getInt("x_in_window"));
            assertEquals(View.INVISIBLE,node.getInt("visibility"));
            assertEquals(1,ArcViewProbe.capture(a,root,1).getJSONArray("nodes").length());
        } finally {controller.pause().stop().destroy();}
    }
    @Test public void surfaceCallbackRecordsAreBoundedAndOwnerCloses() throws Exception {
        var controller=Robolectric.buildActivity(Activity.class).setup();
        try (ArcViewProbe.Session session=new ArcViewProbe.Session()) {
            Activity a=controller.get();FrameLayout root=new FrameLayout(a);a.setContentView(root);
            SurfaceView surface=new SurfaceView(a);root.addView(surface);
            JSONObject before=session.snapshot(a,root,10);
            int initial=before.getInt("surface_changed_callbacks");
            int initialEvents=before.getJSONArray("surface_events").length();
            // Explicit callback fixture, not proof of real compositor surface recreation.
            for(int i=0;i<100;i++) session.surfaceChanged(surface.getHolder(),1,400,600);
            JSONObject after=session.snapshot(a,root,10);
            assertEquals(initialEvents,before.getJSONArray("surface_events").length());
            assertEquals(initial+100,after.getInt("surface_changed_callbacks"));
            assertTrue(after.getJSONArray("surface_events").length()<=64);
        } finally {controller.pause().stop().destroy();}
    }
}
