import hashlib,tempfile,unittest,zipfile
from pathlib import Path
from tools_core import unpack_verified_tool,resolve_cli
class ToolTests(unittest.TestCase):
 def test_verified_tool_and_reuse(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);z=p/'tool.zip';out=p/'tool.exe';data=b'expected executable'
   with zipfile.ZipFile(z,'w') as f:f.writestr('package/tool.exe',data)
   spec={'zipSize':z.stat().st_size,'zipSha256':hashlib.sha256(z.read_bytes()).hexdigest(),'entry':'package/tool.exe','exeSize':len(data),'exeSha256':hashlib.sha256(data).hexdigest()}
   self.assertEqual(unpack_verified_tool(z,out,spec),out);self.assertEqual(out.read_bytes(),data)
   out.write_bytes(b'tampered')
   with self.assertRaises(ValueError):unpack_verified_tool(z,out,spec)
 def test_cli_uses_override_or_prepares_automatically(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);exe=p/'apps2samsung-cli.exe';exe.write_bytes(b'fake')
   self.assertEqual(resolve_cli(str(exe),p,lambda *args:None),exe)
   self.assertEqual(resolve_cli('',p,lambda name,folder,progress:exe),exe)
   with self.assertRaises(ValueError):resolve_cli(str(p/'wrong.exe'),p,lambda *args:exe)
 def test_wrong_archive_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);z=p/'a.zip';z.write_bytes(b'wrong')
   with self.assertRaises(ValueError):unpack_verified_tool(z,p/'x.exe',{'zipSize':5,'zipSha256':'0'*64,'entry':'x','exeSize':0,'exeSha256':'0'*64})
if __name__=='__main__':unittest.main()
