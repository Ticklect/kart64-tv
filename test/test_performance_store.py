import unittest,tempfile
from pathlib import Path
from performance_store import save_result,load_results

class PerformanceTests(unittest.TestCase):
 def test_save_allowlisted_measured_result_only(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'results.json';save_result(p,{'model':'UE50','brand':'Samsung','ip':'10.0.0.1'},{'version':1,'capabilities':{'status':'features-present-untested','webgl2':True,'sharedArrayBuffer':True,'sharedWasm':True,'audioWorklet':True},'cpu':{'iterationsPerSecond':123},'graphics':{'timing':{'kind':'animation_callback_rate','callbackRate':58.4}}})
   result=load_results(p)[0];self.assertEqual(result['model'],'UE50');self.assertEqual(result['graphics_callbacks'],58.4);self.assertNotIn('10.0.0.1',p.read_text());self.assertNotIn('fps',p.read_text().lower())
 def test_corrupt_history_is_safe(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'results.json';p.write_text('{bad');self.assertEqual(load_results(p),[])
