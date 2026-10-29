import unittest,tempfile,tarfile,zipfile
from pathlib import Path
from android_core import validate_android_serial,create_content_tar,parse_adb_devices,classify_android_target
from webos_core import FILES
class AndroidTests(unittest.TestCase):
 def test_fire_os_requires_the_actual_device_feature(self):
  self.assertEqual(classify_android_target('feature:amazon.hardware.fire_tv\n','28','armeabi-v7a'),'firetv')
  self.assertEqual(classify_android_target('feature:android.software.leanback\n','34','arm64-v8a,armeabi-v7a'),'androidtv')
  with self.assertRaises(ValueError):classify_android_target('Amazon Vega TV','34','arm64-v8a')
  with self.assertRaises(ValueError):classify_android_target('feature:amazon.hardware.fire_tv','25','armeabi-v7a')
  with self.assertRaises(ValueError):classify_android_target('feature:amazon.hardware.fire_tv','28','x86')
 def test_fire_feature_wins_when_both_are_present(self):
  self.assertEqual(classify_android_target('feature:amazon.hardware.fire_tv\nfeature:android.software.leanback','30','arm64-v8a'),'firetv')
 def test_connect_does_not_touch_public_or_unapproved_targets(self):
  from unittest.mock import patch
  from studio import Engine
  engine=Engine()
  try:
   with patch('studio.subprocess.run') as run:
    engine.connect_adb('8.8.8.8:5555');run.assert_not_called()
   self.assertIn(('done',False),list(engine.events.queue))
  finally:engine.temp.cleanup()
 def test_only_local_network_serials_are_accepted(self):
  self.assertEqual(validate_android_serial('10.0.0.2:5555'),'10.0.0.2:5555')
  for value in ['8.8.8.8:5555','emulator-5554','10.0.0.2:0','-all','10.0.0.2:5555 extra']:
   with self.assertRaises(ValueError):validate_android_serial(value)
 def test_discovery_ignores_unauthorised_devices(self):
  self.assertEqual(parse_adb_devices('List of devices attached\n10.0.0.2:5555 device product:test\n10.0.0.3:5555 unauthorized\nemulator-5554 device\n'),['10.0.0.2:5555'])
 def test_private_content_tar_has_no_other_files(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);stage=p/'stage';stage.mkdir();game=p/'game.o2r'
   for name in FILES:
    f=stage/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b'test')
   (stage/'secret.txt').write_text('private')
   with zipfile.ZipFile(game,'w') as z:z.writestr('asset','test')
   output=create_content_tar(stage,game,p/'content.tar')
   with tarfile.open(output) as t:self.assertNotIn('secret.txt',t.getnames());self.assertIn('mk64.o2r',t.getnames())
