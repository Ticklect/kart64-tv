import unittest,tempfile,zipfile,subprocess,sys,hashlib
from pathlib import Path
from installer_core import validate_tv_ip,validate_archive,make_package,parse_discovery,identify_game,safe_extract_release,verify_extractor
class CoreTests(unittest.TestCase):
 def test_installer_self_check(self):
  result=subprocess.run([sys.executable,'installer.py','--self-test'],capture_output=True,timeout=15)
  self.assertEqual(result.returncode,0)
 def test_discovery_sanitizes_and_preserves_multiple_tvs(self):
  data={'ok':True,'tvs':[{'ip':'10.42.0.10','name':'Living Room','model':'A','mac':'secret'},{'ip':'10.42.0.11','name':'Bedroom','model':'B','duid':'private'},{'ip':'8.8.8.8','name':'bad'}]}
  tvs=parse_discovery(data)
  self.assertEqual(len(tvs),2);self.assertEqual(tvs[0],{'ip':'10.42.0.10','name':'Living Room','model':'A'});self.assertEqual(tvs[1]['ip'],'10.42.0.11')
  with self.assertRaises(ValueError):parse_discovery({'ok':False,'tvs':[]})
 def test_game_input_recognises_archive_and_rejects_unknown_rom(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);rom=p/'unknown.z64';rom.write_bytes(b'bad');archive=p/'game.o2r'
   with zipfile.ZipFile(archive,'w') as z:z.writestr('asset','test')
   self.assertEqual(identify_game(archive),'archive')
   with self.assertRaisesRegex(ValueError,'supported US'):identify_game(rom)
 def test_extraction_rejects_zip_path_traversal(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);archive=p/'unsafe.zip';target=p/'stage';target.mkdir()
   with zipfile.ZipFile(archive,'w') as z:z.writestr('../escaped','bad')
   with self.assertRaises(ValueError):safe_extract_release(archive,target)
   self.assertFalse((p/'escaped').exists())
 def test_extractor_integrity(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'tool.zip';f.write_bytes(b'good');digest=hashlib.sha256(b'good').hexdigest()
   self.assertTrue(verify_extractor(f,4,digest))
   f.write_bytes(b'evil')
   with self.assertRaises(ValueError):verify_extractor(f,4,digest)
 def test_discovery_requires_explicit_choice_for_multiple_tvs(self):
  import tkinter as tk
  from installer import Installer
  root=tk.Tk();root.withdraw()
  try:
   app=Installer(root);app.ip.set('192.168.0.10')
   app.events.put(('tvs',[{'ip':'192.168.0.20','name':'one','model':'A'},{'ip':'192.168.0.21','name':'two','model':'B'}]))
   app.poll();self.assertEqual(app.ip.get(),'')
  finally:app.tool_temp.cleanup();root.destroy()
 def test_child_process_timeout_and_url_redaction(self):
  import queue
  from installer import Installer
  app=Installer.__new__(Installer);app.events=queue.Queue()
  app.command([sys.executable,'-c',"print('https://example.com/secret')"],timeout=5)
  log=' '.join(str(x[1]) for x in list(app.events.queue));self.assertNotIn('example.com',log)
  with self.assertRaisesRegex(RuntimeError,'timed out'):app.command([sys.executable,'-c','import time;time.sleep(10)'],timeout=1)
 def test_address(self):
  self.assertEqual(validate_tv_ip('192.168.1.10'),'192.168.1.10')
  for v in ['127.0.0.1','8.8.8.8','nope','0.0.0.0']:
   with self.assertRaises(ValueError):validate_tv_ip(v)
 def test_invalid_archive(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'bad.o2r';f.write_bytes(b'not an archive')
   with self.assertRaises(ValueError):validate_archive(f)
 def test_package_contains_user_data_and_no_signatures(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);stage=p/'stage';stage.mkdir();archive=p/'game.o2r'
   for n in ('config.xml','index.html','Spaghettify.js','Spaghettify.wasm','diagnostics.js','packaged-boot.js'):(stage/n).write_bytes(b'test')
   with zipfile.ZipFile(archive,'w') as z:z.writestr('asset','example')
   target=p/'private.wgt';make_package(stage,archive,target)
   with zipfile.ZipFile(target) as z:
    self.assertIn('mk64.o2r',z.namelist());self.assertIsNone(z.testzip());self.assertNotIn('author-signature.xml',z.namelist())
 def test_refuses_incomplete_package(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'stage').mkdir()
   with zipfile.ZipFile(p/'a.o2r','w') as z:z.writestr('asset','x')
   with self.assertRaises(ValueError):make_package(p/'stage',p/'a.o2r',p/'out.wgt')
if __name__=='__main__':unittest.main()
