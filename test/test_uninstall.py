import unittest,queue,tempfile
from pathlib import Path
from unittest.mock import patch,Mock
from uninstall import remove_app

class UninstallTests(unittest.TestCase):
 def test_android_removes_only_our_package_on_matching_target(self):
  calls=[]
  def command(args):calls.append(args)
  def run(args,**kw):return Mock(returncode=0,stdout='feature:amazon.hardware.fire_tv\n' if 'features' in args else '',stderr='')
  with patch('uninstall.shutil.which',return_value='adb.exe'),patch('uninstall.subprocess.run',side_effect=run):
   remove_app({'ip':'10.0.0.2','brand':'Amazon','platform':'firetv','adb_serial':'10.0.0.2:5555'},'',Path('.'),'','',command,lambda x:None)
  self.assertEqual(calls,[['adb.exe','-s','10.0.0.2:5555','uninstall','com.ticklect.kart64']])
 def test_mismatched_android_ip_never_uninstalls(self):
  command=Mock()
  with self.assertRaises(ValueError):remove_app({'ip':'10.0.0.2','platform':'androidtv','adb_serial':'10.0.0.3:5555'},'',Path('.'),'','',command,lambda x:None)
  command.assert_not_called()
 def test_unknown_platform_never_runs_command(self):
  command=Mock()
  with self.assertRaises(ValueError):remove_app({'ip':'10.0.0.2','brand':'Other'},'',Path('.'),'','',command,lambda x:None)
  command.assert_not_called()
 def test_samsung_confirmation_requires_verified_absence(self):
  command=Mock()
  with patch('uninstall.resolve_cli',return_value=Path('apps2samsung-cli.exe')),patch('uninstall.samsung_installed',side_effect=[True,False]):
   remove_app({'ip':'10.0.0.2','brand':'Samsung'},'',Path('.'),'','',command,lambda x:None)
  command.assert_called_once_with(['apps2samsung-cli.exe','uninstall','KART64TV01.Kart64','--tv','10.0.0.2'])
 def test_lg_registration_must_match_before_removal(self):
  command=Mock()
  with tempfile.TemporaryDirectory() as d:
   for n in ['ares-install.cmd','ares-setup-device.cmd']:(Path(d)/n).write_text('test')
   with patch('uninstall.subprocess.run',return_value=Mock(returncode=0,stdout='[{"name":"tv","profile":"tv","deviceinfo":{"ip":"10.0.0.3"}}]')):
    with self.assertRaises(ValueError):remove_app({'ip':'10.0.0.2','brand':'LG'},'',Path('.'),d,'tv',command,lambda x:None)
  command.assert_not_called()
 def test_samsung_does_not_claim_success_if_app_remains(self):
  with patch('uninstall.resolve_cli',return_value=Path('apps2samsung-cli.exe')),patch('uninstall.samsung_installed',return_value=True),patch('uninstall.time.sleep'):
   with self.assertRaisesRegex(ValueError,'still reports'):remove_app({'ip':'10.0.0.2','brand':'Samsung'},'',Path('.'),'','',Mock(),lambda x:None)
 def test_lg_removal_uses_fixed_app_id(self):
  command=Mock()
  with tempfile.TemporaryDirectory() as d:
   for n in ['ares-install.cmd','ares-setup-device.cmd']:(Path(d)/n).write_text('test')
   outputs=[Mock(returncode=0,stdout='[{"name":"tv","profile":"tv","deviceinfo":{"ip":"10.0.0.2"}}]'),Mock(returncode=0,stdout='com.other.app\n')]
   with patch('uninstall.subprocess.run',side_effect=outputs):remove_app({'ip':'10.0.0.2','brand':'LG'},'',Path('.'),d,'tv',command,lambda x:None)
   command.assert_called_once_with([str(Path(d)/'ares-install.cmd'),'--device','tv','--remove','com.ticklect.kart64'])
