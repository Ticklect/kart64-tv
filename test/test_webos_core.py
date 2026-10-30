import json,tempfile,unittest,zipfile
from pathlib import Path
from webos_core import prepare_webos_stage
class WebOSTests(unittest.TestCase):
 def test_prepares_private_webos_app(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);runtime=p/'runtime';out=p/'out';runtime.mkdir();out.mkdir();game=p/'game.o2r'
   for n in ['index.html','Spaghettify.js','Spaghettify.wasm','Spaghettify.data','spaghetti.o2r','courses.json','courses/silverstone/silverstone-v1.9.o2r','apple-touch-icon.png','diagnostics.js','packaged-boot.js','config.xml']:
    x=runtime/n;x.parent.mkdir(parents=True,exist_ok=True);x.write_bytes(b'test')
   with zipfile.ZipFile(game,'w') as z:z.writestr('asset','test')
   prepare_webos_stage(runtime,game,out)
   info=json.loads((out/'appinfo.json').read_text());self.assertEqual(info['type'],'web');self.assertEqual(info['id'],'com.ticklect.kart64');self.assertTrue((out/'icon.png').is_file());self.assertTrue((out/'mk64.o2r').is_file());self.assertFalse((out/'config.xml').exists())
 def test_refuses_nonempty_output(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);out=p/'out';out.mkdir();(out/'keep').write_text('preserve')
   with self.assertRaises(ValueError):prepare_webos_stage(p/'no-runtime',p/'no-game',out)
   self.assertEqual((out/'keep').read_text(),'preserve')
if __name__=='__main__':unittest.main()
