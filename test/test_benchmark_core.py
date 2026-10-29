import json,tempfile,unittest,zipfile
from pathlib import Path
from benchmark_core import make_benchmark,parse_debug_port,format_benchmark
class BenchmarkTests(unittest.TestCase):
 def test_private_benchmark_package(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);app=make_benchmark(Path('benchmark'),p/'check.wgt','KB1234ABCD')
   self.assertEqual(app,'KB1234ABCD.Check')
   with zipfile.ZipFile(p/'check.wgt') as z:
    self.assertEqual(set(z.namelist()),{'config.xml','index.html','run.js','benchmark.js','icon.png'});self.assertIsNone(z.testzip());self.assertIn(b'KB1234ABCD.Check',z.read('config.xml'))
 def test_debug_port_is_validated(self):
  self.assertEqual(parse_debug_port('successfully launched pid = 5 with debug 1 port: 40491'),40491)
  for x in ['port: 2','port: 999999','no port']:
   with self.assertRaises(ValueError):parse_debug_port(x)
 def test_format_never_labels_synthetic_as_game_fps(self):
  obj={'version':1,'capabilities':{'status':'features-present-untested','webgl2':True,'sharedArrayBuffer':True,'sharedWasm':True,'audioWorklet':True},'cpu':{'iterationsPerSecond':1000},'graphics':{'timing':{'kind':'animation_callback_rate','callbackRate':57}}}
  text=format_benchmark(obj);self.assertIn('57',text);self.assertIn('not game FPS',text)
if __name__=='__main__':unittest.main()
