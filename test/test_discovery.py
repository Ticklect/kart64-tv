import unittest
from discovery import parse_description, merge_devices

class DiscoveryTests(unittest.TestCase):
 def test_lg_tv_is_identified(self):
  xml=b'<root><device><deviceType>urn:schemas-upnp-org:device:MediaRenderer:1</deviceType><friendlyName>Living room</friendlyName><manufacturer>LG Electronics</manufacturer><modelName>OLED C3</modelName></device></root>'
  self.assertEqual(parse_description(xml,'10.0.0.4'),{'ip':'10.0.0.4','name':'Living room','model':'OLED C3','brand':'LG','supported':False})
 def test_rejects_unrelated_device(self):
  self.assertIsNone(parse_description(b'<root><device><friendlyName>printer</friendlyName><manufacturer>LG</manufacturer><deviceType>printer</deviceType></device></root>','10.0.0.4'))
 def test_samsung_results_merge_without_duplicates(self):
  result=merge_devices([{'ip':'10.0.0.2','name':'TV','model':'A'}],[{'ip':'10.0.0.2','name':'TV','model':'A','brand':'Samsung','supported':False}])
  self.assertEqual(len(result),1);self.assertTrue(result[0]['supported'])
 def test_unknown_brand_tv_remains_unsupported(self):
  xml=b'<root><device><deviceType>urn:schemas-upnp-org:device:MediaRenderer:1</deviceType><friendlyName>Television</friendlyName><manufacturer>Example</manufacturer></device></root>'
  self.assertFalse(parse_description(xml,'10.0.0.9')['supported'])
 def test_unsupported_tv_cannot_use_samsung_installer(self):
  from installer import Installer
  app=Installer.__new__(Installer);app.found=[{'ip':'10.0.0.4','brand':'LG','supported':False}]
  with self.assertRaisesRegex(ValueError,'not supported'):app.ensure_supported('10.0.0.4')
 def test_hisense_code_does_not_include_private_metadata(self):
  xml=b'<root><device><deviceType>urn:schemas-upnp-org:device:MediaRenderer:1</deviceType><friendlyName>Bedroom TV</friendlyName><manufacturer>SmartTV</manufacturer><modelName>Renderer</modelName><modelDescription>brand=his\nmac=private</modelDescription></device></root>'
  tv=parse_description(xml,'10.0.0.4');self.assertEqual(tv['brand'],'Hisense (likely)');self.assertEqual(tv['model'],'');self.assertNotIn('private',str(tv))
