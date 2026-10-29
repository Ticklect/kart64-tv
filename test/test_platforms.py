import unittest
from platforms import platform_for,verify_webos_target
class PlatformTests(unittest.TestCase):
 def test_brand_does_not_determine_ambiguous_os(self):
  self.assertEqual(platform_for({'brand':'Hisense (likely)'}),'unknown')
  self.assertEqual(platform_for({'brand':'LG'}),'webos')
  self.assertEqual(platform_for({'brand':'Samsung'}),'tizen')
  self.assertEqual(platform_for({'brand':'Sony'}),'unknown')
  self.assertEqual(platform_for({'brand':'Sony','platform':'androidtv','adb_serial':'10.0.0.4:5555'}),'androidtv')
 def test_webos_target_must_match_selected_tv(self):
  rows=[{'name':'mytv','profile':'tv','deviceinfo':{'ip':'10.0.0.3'}}]
  self.assertEqual(verify_webos_target(rows,'mytv','10.0.0.3'),'mytv')
  with self.assertRaises(ValueError):verify_webos_target(rows,'mytv','10.0.0.4')
  with self.assertRaises(ValueError):verify_webos_target(rows,'--all','10.0.0.3')
