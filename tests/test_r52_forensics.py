"""Offline faults in collector/oracle; never an Android or GPU PASS."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

class ForensicTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  spec=importlib.util.spec_from_file_location('r52',ROOT/'scripts/r52_forensics.py')
  cls.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.m)
 def test_view_metadata_excludes_text_urls_and_intents(self):
  text='''ACTIVITY app.archium.android/com.google.android.apps.chrome.Main
 mIntent dat=https://private.example/?token=SECRET
 android.widget.FrameLayout{abc V.E...... ........ 52,0-1298,878 #7f001 app:id/secondary_ui_container_tab_modal}
 android.widget.FrameLayout{def GFE...C.. ......I. 0,0-0,0 #7f002 app:id/tab_modal_dialog_container}
 mText=SECRET user@example.com
'''
  rows=self.m.parse_views(text)
  self.assertEqual(len(rows),2);self.assertEqual(rows[1]['bounds'],[0,0,0,0])
  self.assertEqual(rows[1]['visibility'],'GONE');self.assertNotIn('SECRET',str(rows));self.assertNotIn('private.example',str(rows))
 def test_log_classifier_never_exports_raw_message(self):
  r=self.m.gpu_events('10-19 11:22:00.123 123 124 E chromium: VK_ERROR_DEVICE_LOST url=https://secret/?password=SECRET')
  self.assertEqual(r[0]['code'],'VK_ERROR_DEVICE_LOST');self.assertNotIn('SECRET',str(r))
 def test_missing_dialog_evidence_is_unknown_not_closed(self):
  self.assertEqual(self.m.dialog_observation([])['state'],'UNKNOWN')
 def test_gone_zero_container_is_observation_not_root_cause(self):
  rows=self.m.parse_views('android.widget.FrameLayout{def GFE...C.. ......I. 0,0-0,0 #7f002 app:id/tab_modal_dialog_container}')
  r=self.m.dialog_observation(rows)
  self.assertEqual(r['state'],'CONTAINER_GONE_ZERO_BOUNDS');self.assertEqual(r['cause'],'NOT_PROVEN')
 def oracle(self,kind):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);a=Image.new('RGB',(100,80),'white');a.paste((230,40,70),(5,5,45,65));a.paste((20,170,210),(55,5,95,65));b=a.copy()
   if kind=='black':b.paste((0,0,0),(5,5,45,65))
   if kind=='duplicate':b.paste((230,40,70),(55,5,95,65))
   if kind=='stale':b.paste((20,170,210),(5,5,45,65))
   if kind=='outside':b.paste((0,0,0),(0,70,100,80))
   a.save(p/'a.png');b.save(p/'b.png')
   return self.m.compare_pixels(p/'a.png',p/'b.png',[[5,5,45,65],[55,5,95,65]],tolerance=3,max_changed_fraction=0.001)
 def test_matching_fixture_regions_pass_only_pixel_comparison(self):self.assertEqual(self.oracle('same')['status'],'PIXEL_MATCH')
 def test_black_region_is_detected(self):self.assertEqual(self.oracle('black')['status'],'PIXEL_MISMATCH')
 def test_duplicate_tile_is_detected(self):self.assertEqual(self.oracle('duplicate')['status'],'PIXEL_MISMATCH')
 def test_stale_phase_is_detected(self):self.assertEqual(self.oracle('stale')['status'],'PIXEL_MISMATCH')
 def test_outside_fixture_is_excluded(self):self.assertEqual(self.oracle('outside')['status'],'PIXEL_MATCH')
 def test_invalid_crop_fails_closed(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.png';Image.new('RGB',(10,10)).save(p)
   with self.assertRaises(ValueError):self.m.compare_pixels(p,p,[[0,0,100,100]])
 def test_capture_requires_explicit_serial_and_bounded_samples(self):
  with self.assertRaises(ValueError):self.m.validate_capture('',31,4)
  with self.assertRaises(ValueError):self.m.validate_capture('device',0,1)
  with self.assertRaises(ValueError):self.m.validate_capture('device',2,20)
  self.m.validate_capture('device:5555',3,1)

class TraceCaptureTests(unittest.TestCase):
 def module(self):
  import sys
  sys.path.insert(0,str(ROOT/'scripts'))
  spec=importlib.util.spec_from_file_location('r52trace',ROOT/'scripts/r52_capture_trace.py')
  m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def test_default_plan_never_calls_adb(self):
  import sys
  from unittest.mock import patch
  m=self.module()
  with tempfile.TemporaryDirectory() as d:
   with patch.object(sys,'argv',['trace','--serial','device','--output',d+'/plan']),patch.object(m.subprocess,'run',side_effect=AssertionError('Unexpected device command')) as command:
    self.assertEqual(m.main(),0);command.assert_not_called()
 def test_execution_requires_fixture_confirmation(self):
  import sys
  from unittest.mock import patch
  m=self.module()
  with tempfile.TemporaryDirectory() as d:
   with patch.object(sys,'argv',['trace','--serial','device','--output',d+'/capture','--execute']),patch.object(m.subprocess,'run') as command:
    with self.assertRaises(SystemExit):m.main()
    command.assert_not_called()
 def test_timeout_keeps_blocked_receipt_without_raw_error_text(self):
  import sys,json,subprocess
  from unittest.mock import patch
  m=self.module()
  with tempfile.TemporaryDirectory() as d:
   with patch.object(sys,'argv',['trace','--serial','device','--output',d+'/capture','--execute','--fixture-confirmed']),patch.object(m.subprocess,'run',side_effect=subprocess.TimeoutExpired('SECRET',20)):
    try:result=m.main()
    except subprocess.TimeoutExpired:result='raised instead of preserving receipt'
    self.assertEqual(result,1)
   receipt=json.loads((Path(d)/'capture/trace-receipt.json').read_text())
   self.assertEqual(receipt['status'],'CAPTURE_BLOCKED');self.assertNotIn('SECRET',str(receipt))
