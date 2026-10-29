import unittest
from dashboard import device_status, latest_for_device, game_status

class DashboardTests(unittest.TestCase):
 def test_selected_devices_are_described_honestly(self):
  self.assertEqual(device_status(None,'')[0],'No TV selected')
  self.assertEqual(device_status({'brand':'Samsung','model':'A','supported':True},'10.0.0.2')[0],'Samsung TV selected')
  self.assertIn('not supported',device_status({'brand':'LG','supported':False},'10.0.0.3')[1].lower())
  self.assertIn('not verified',device_status(None,'10.0.0.4')[1].lower())
 def test_latest_result_does_not_compare_other_models(self):
  rows=[{'brand':'Samsung','model':'A','cpu_iterations':100},{'brand':'Samsung','model':'B','cpu_iterations':200}]
  self.assertEqual(latest_for_device(rows,{'brand':'Samsung','model':'A'})['cpu_iterations'],100)
  self.assertIsNone(latest_for_device(rows,{'brand':'Samsung','model':''}))
 def test_game_status_is_not_a_validation_claim(self):
  self.assertEqual(game_status(''),'No game file selected')
  self.assertEqual(game_status('C:/Games/mario.z64'),'Game file selected — checked when installation starts')
 def test_gui_selection_updates_and_primary_actions_remain_visible(self):
  import tkinter as tk
  from installer import Installer
  root=tk.Tk();app=Installer(root)
  try:
   root.geometry('850x800');root.update()
   app.found=[{'ip':'10.0.0.2','brand':'Samsung','model':'Model A','supported':True}];app.ip.set('10.0.0.2');root.update()
   self.assertEqual(app.selected_title.cget('text'),'Samsung TV selected')
   self.assertIn('Model A',app.selected_detail.cget('text'))
   self.assertTrue(app.install.winfo_ismapped());self.assertTrue(app.benchmark_button.winfo_ismapped());self.assertGreater(app.log.winfo_height(),40)
  finally:app.tool_temp.cleanup();root.destroy()
