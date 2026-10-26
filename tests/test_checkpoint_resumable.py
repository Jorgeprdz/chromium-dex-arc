"""Real local HTTP transfers with cuts; never claims an 8GiB or physical acceptance."""
import hashlib,http.server,importlib.util,json,socket,tempfile,threading,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=bytes(range(256))*4096
class ResumeTests(unittest.TestCase):
 def setUp(self):
  spec=importlib.util.spec_from_file_location('resume',ROOT/'scripts/resumable-checkpoint-transfer.py')
  self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.path=Path(self.temp.name)/'group.zip.part';self.calls=[];self.mode='cut';self.cut=False
  owner=self
  class Handler(http.server.BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_GET(self):
    import re
    match=re.fullmatch(r'bytes=(\d+)-(\d+)',self.headers.get('Range',''))
    if not match:self.send_error(400);return
    a,b=map(int,match.groups());owner.calls.append((a,b))
    if owner.mode=='503':self.send_response(503);self.send_header('Content-Length','0');self.end_headers();return
    if owner.mode=='ignore':self.send_response(200);self.send_header('Content-Length','0');self.end_headers();return
    self.send_response(206)
    self.send_header('Content-Range',f'bytes {a}-{b}/{len(DATA)}')
    self.send_header('Content-Length',str(b-a+1));self.end_headers()
    data=DATA[a:b+1]
    if owner.mode=='corrupt':data=b'!'+data[1:]
    if owner.mode=='cut' and not owner.cut:
     owner.cut=True;self.wfile.write(data[:131072]);self.wfile.flush();self.connection.shutdown(socket.SHUT_RDWR);self.connection.close();return
    self.wfile.write(data)
  self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
  threading.Thread(target=self.server.serve_forever,daemon=True).start()
  self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown)
  self.group=dict(id=1,name='checkpoint-00',size_in_bytes=len(DATA),digest='sha256:'+hashlib.sha256(DATA).hexdigest())
 def download(self,**kwargs):
  return self.m.download_archive(self.group,self.path,'owner/repo',time.monotonic()+10,
   get_url=lambda:f'http://127.0.0.1:{self.server.server_port}/data',chunk_bytes=524288,pause=lambda _:None,**kwargs)
 def test_cut_resumes_and_hashes_complete_file(self):
  self.download()
  self.assertEqual(self.calls[0][0],0);self.assertEqual(self.calls[1][0],131072)
  self.assertEqual(self.path.read_bytes(),DATA)
 def test_new_invocation_reuses_partial_with_same_identity(self):
  self.mode='503'
  with self.assertRaises(RuntimeError):self.download(recovery_limit=0)
  self.path.write_bytes(DATA[:131072]);self.mode='valid';self.calls=[]
  self.download();self.assertEqual(self.calls[0][0],131072)
 def test_changed_identity_rejected_before_network(self):
  self.mode='503'
  with self.assertRaises(RuntimeError):self.download(recovery_limit=0)
  self.group['id']=2;self.calls=[]
  with self.assertRaisesRegex(ValueError,'identity'):self.download()
  self.assertEqual(self.calls,[])
 def test_ignored_range_is_rejected_without_writing(self):
  self.mode='ignore'
  with self.assertRaisesRegex(ValueError,'Range'):self.download()
  self.assertFalse(self.path.exists() and self.path.stat().st_size)
 def test_retry_limit_stops_repeated_503(self):
  self.mode='503'
  with self.assertRaises(RuntimeError):self.download(recovery_limit=2)
  self.assertEqual(len(self.calls),3)
 def test_corrupt_complete_download_is_not_accepted(self):
  self.mode='corrupt'
  with self.assertRaisesRegex(ValueError,'hash'):self.download()
 def test_expired_budget_stops_before_network(self):
  with self.assertRaises(TimeoutError):
   self.m.download_archive(self.group,self.path,'owner/repo',time.monotonic()-1,get_url=lambda:'unused')
  self.assertEqual(self.calls,[])
if __name__=='__main__':unittest.main()
