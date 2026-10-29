"""Production collection semantics on JVM, not native bookmark/Android acceptance."""
import pathlib,subprocess,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
ARC=ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc'
class FavoriteIdentityTests(unittest.TestCase):
 def test_same_url_converges_across_native_tabs_and_reopen(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp);src=p/'FavoriteIdentityProbe.java'
   src.write_text('''import org.chromium.chrome.browser.arc.*;
import java.util.*;
public class FavoriteIdentityProbe {
 static class Disk implements ArcSidebarStore.Persistence {String value="";public String read(){return value;}public void write(String s){value=s;}}
 static class Tabs implements ArcTabActions.NativeTabs {
  public boolean exists(int id){return id==1||id==2;} public void select(int id){} public int open(String u){return 2;}
  public void pin(int id){} public void unpin(int id){} public void move(int id,int i){} public void close(int id){}
 }
 public static void main(String[] args){
  Disk d=new Disk();ArcSidebarStore store=new ArcSidebarStore(d);Tabs t=new Tabs();
  ArcCollectionsController c=new ArcCollectionsController(store,new ArcTabActions(store,t),t);
  String id=c.rememberTab(1,"https://example.test/","Old",true);
  String second=c.rememberTab(2,"https://example.test/","New",true);
  if(!id.equals(second)||c.state().favorites().size()!=1)throw new AssertionError("Duplicate URL creates another favorite");
  if(!c.state().entry(id).title.equals("New"))throw new AssertionError("Native edited title not projected");
  ArcSidebarStore reopen=new ArcSidebarStore(d);
  if(reopen.load().favorites().size()!=1||!reopen.load().entry(id).title.equals("New"))throw new AssertionError("Persistence lost identity/title");
  c.rememberTab(2,"https://example.test/","New",true);
  if(c.state().favorites().size()!=1)throw new AssertionError("Repeated save duplicates favorite");
  c.updateFavorite(id,"https://edited.test/","Edited natively");
  if(!new ArcSidebarStore(d).load().entry(id).url.equals("https://edited.test/"))throw new AssertionError("Native URL edit lost");
  c.rememberTab(1,"https://another.test/","Another page",true);
  if(c.state().favorites().size()!=2||!c.state().entry(id).url.equals("https://edited.test/"))throw new AssertionError("Saving navigated tab overwrote previous favorite");
  String stable=d.value;
  ArcSidebarStore broken=new ArcSidebarStore(new ArcSidebarStore.Persistence(){public String read(){return stable;}public void write(String v){throw new IllegalStateException("disk");}});
  ArcCollectionsController failure=new ArcCollectionsController(broken,new ArcTabActions(broken,t),t);
  try{failure.rememberTab(2,"https://failure.test/","Failure",true);throw new AssertionError("Write failure hidden");}catch(IllegalStateException expected){}
  if(!d.value.equals(stable))throw new AssertionError("Persisted state damaged");
  if(c.state().spaces().size()!=1)throw new AssertionError("Migration touched spaces");
 }
}''')
   r=subprocess.run(['javac','-d',str(p),*[str(ARC/(n+'.java')) for n in ['ArcSidebarState','ArcSidebarStore','ArcTabActions','ArcCollectionsController']],str(src)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr)
   r=subprocess.run(['java','-ea','-cp',str(p),'FavoriteIdentityProbe'],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr)
