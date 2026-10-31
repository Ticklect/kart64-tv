import os,unittest
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication,QLabel,QPushButton
from studio import Studio,DOWNLOADER_CODE,DOWNLOADER_URL

class StudioTests(unittest.TestCase):
 def test_self_test_works_without_a_bundled_android_apk(self):
  import subprocess,sys
  result=subprocess.run([sys.executable,'studio.py','--self-test'],capture_output=True,timeout=15)
  self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))

 @classmethod
 def setUpClass(cls):cls.qt=QApplication.instance() or QApplication([])
 def test_downloader_code_shown_and_copyable_before_tv_selection(self):
  window=Studio(start_scan=False)
  clipboard=QApplication.clipboard();previous=clipboard.text()
  try:
   self.assertEqual(DOWNLOADER_CODE,'7989374')
   self.assertEqual(window.downloader_code.text(),DOWNLOADER_CODE)
   labels=[label.text() for label in window.findChildren(QLabel)]
   self.assertTrue(any(DOWNLOADER_URL in label for label in labels))
   self.assertTrue(any('launcher only' in label.lower() and 'game data' in label.lower() for label in labels))
   copy=next(button for button in window.findChildren(QPushButton) if button.text()=='Copy code')
   self.assertTrue(copy.isEnabled())
   copy.click();self.assertEqual(clipboard.text(),DOWNLOADER_CODE)
  finally:
   clipboard.setText(previous);window.shutdown()
 def test_selection_and_support(self):
  window=Studio(start_scan=False)
  try:
   window.set_devices([{'ip':'10.0.0.2','brand':'Samsung','model':'Test TV','name':'Living room','supported':True},{'ip':'10.0.0.3','brand':'LG','model':'Test LG','name':'Bedroom','supported':False}])
   self.assertIsNone(window.selected)
   window.select_device(0);self.assertEqual(window.selected['model'],'Test TV');self.assertTrue(window.test_button.isEnabled())
   window.select_device(1);self.assertFalse(window.test_button.isEnabled());self.assertFalse(window.install_button.isEnabled())
  finally:window.shutdown()
 def test_game_selection_does_not_claim_validation(self):
  window=Studio(start_scan=False)
  try:
   window.set_game('C:/test/game.z64');self.assertIn('checked',window.game_info.text().lower())
  finally:window.shutdown()
 def test_benchmark_failure_does_not_report_success(self):
  from unittest.mock import patch
  from studio import Engine
  engine=Engine()
  try:
   with patch('installer.resolve_cli',side_effect=ValueError('failed')):engine.run_benchmark('10.0.0.2','')
   events=list(engine.events.queue);self.assertIn(('done',False),events)
  finally:engine.temp.cleanup()
 def test_buttons_dispatch_selected_device_and_game(self):
  window=Studio(start_scan=False)
  try:
   calls=[];window.start_work=lambda target,args:calls.append((target.__name__,args))
   window.set_devices([{'ip':'10.0.0.2','brand':'Samsung','model':'A','name':'TV','supported':True}]);window.set_game('C:/game.z64')
   window.benchmark();window.install()
   self.assertEqual(calls[0][0],'run_benchmark');self.assertEqual(calls[0][1][0],'10.0.0.2')
   self.assertEqual(calls[1][0],'run');self.assertEqual(calls[1][1][0],'10.0.0.2');self.assertEqual(str(calls[1][1][1]).replace('\\','/'),'C:/game.z64')
  finally:window.shutdown()
 def test_refresh_preserves_selection_if_device_remains(self):
  window=Studio(start_scan=False)
  try:
   devices=[{'ip':'10.0.0.2','brand':'Samsung','model':'A','name':'TV','supported':True},{'ip':'10.0.0.3','brand':'LG','model':'B','name':'TV2','supported':False}]
   window.set_devices(devices);window.select_device(0);window.set_devices(list(reversed(devices)))
   self.assertEqual(window.selected['ip'],'10.0.0.2')
  finally:window.shutdown()
 def test_scan_does_not_take_over_the_screen(self):
  window=Studio(start_scan=False)
  try:
   window.navigate(2);window.engine.events.put(('tvs',[]));window.poll()
   self.assertEqual(window.stack.currentIndex(),2)
  finally:window.shutdown()
 def test_run_check_button_in_performance_tracks_selection(self):
  window=Studio(start_scan=False)
  try:
   self.assertFalse(window.performance_test.isEnabled())
   window.set_devices([{'ip':'10.0.0.2','brand':'Samsung','model':'A','name':'TV','supported':True}]);self.assertTrue(window.performance_test.isEnabled())
  finally:window.shutdown()
 def test_tv_cards_are_visible_and_clickable(self):
  window=Studio(start_scan=False)
  try:
   window.set_devices([{'ip':'10.0.0.2','brand':'Samsung','model':'A','name':'TV','supported':True},{'ip':'10.0.0.3','brand':'LG','model':'B','name':'TV2','supported':False}])
   self.assertEqual(window.tv_list.count(),2)
   for index in range(2):self.assertGreaterEqual(window.tv_list.item(index).sizeHint().height(),window.tv_list.itemWidget(window.tv_list.item(index)).sizeHint().height())
   window.tv_list.setCurrentRow(1);self.assertEqual(window.selected['ip'],'10.0.0.3')
  finally:window.shutdown()
 def test_custom_icon_and_lg_route(self):
  window=Studio(start_scan=False)
  try:
   self.assertFalse(window.windowIcon().isNull())
   window.set_devices([{'ip':'10.0.0.3','brand':'LG','model':'A','name':'LG TV','supported':False}]);window.set_game('C:/game.z64')
   window.lg_cli.setText('C:/webos/bin');window.lg_target.setText('livingroom')
   self.assertTrue(window.install_button.isEnabled());self.assertFalse(window.test_button.isEnabled())
   calls=[];window.start_work=lambda target,args:calls.append((target.__name__,args));window.install()
   self.assertEqual(calls[0][0],'run_webos');self.assertEqual(calls[0][1][0],'10.0.0.3')
  finally:window.shutdown()
 def test_verified_android_route_dispatches_exact_adb_target(self):
  window=Studio(start_scan=False)
  try:
   window.set_devices([{'ip':'10.0.0.4','brand':'Sony','model':'Test Android TV','name':'TV','platform':'androidtv','adb_serial':'10.0.0.4:40123','supported':False}]);window.set_game('C:/game.z64')
   self.assertTrue(window.install_button.isEnabled());self.assertFalse(window.test_button.isEnabled())
   calls=[];window.start_work=lambda target,args:calls.append((target.__name__,args));window.install()
   self.assertEqual(calls[0][0],'run_android');self.assertEqual(calls[0][1][0],'10.0.0.4:40123')
  finally:window.shutdown()
 def test_fire_route_dispatch_and_old_fire_runtime_block(self):
  window=Studio(start_scan=False)
  try:
   device={'ip':'10.0.0.5','brand':'Amazon','model':'Fire TV','name':'Fire TV','platform':'firetv','adb_serial':'10.0.0.5:5555','supported':False,'android_compatible':True}
   window.set_devices([device]);window.set_game('C:/game.z64');self.assertTrue(window.install_button.isEnabled())
   calls=[];window.start_work=lambda target,args:calls.append((target.__name__,args));window.install();self.assertEqual(calls[0][1][0],'10.0.0.5:5555')
   device={**device,'android_compatible':False,'compatibility_error':'API too old'};window.set_devices([device]);self.assertFalse(window.install_button.isEnabled());window.install();self.assertEqual(len(calls),1)
  finally:window.shutdown()
 def test_uninstall_requires_confirmation_and_uses_selected_tv(self):
  from unittest.mock import patch
  from PySide6.QtWidgets import QMessageBox
  window=Studio(start_scan=False)
  try:
   device={'ip':'10.0.0.2','brand':'Samsung','name':'Living room','model':'A','supported':True};window.set_devices([device])
   self.assertTrue(window.uninstall_button.isEnabled())
   calls=[];window.start_work=lambda target,args:calls.append((target.__name__,args))
   with patch('studio.QMessageBox.question',return_value=QMessageBox.No):window.uninstall_selected()
   self.assertEqual(calls,[])
   with patch('studio.QMessageBox.question',return_value=QMessageBox.Yes) as prompt:window.uninstall_selected()
   self.assertIn('10.0.0.2',prompt.call_args.args[2]);self.assertEqual(calls[0][0],'run_uninstall');self.assertEqual(calls[0][1][0]['ip'],'10.0.0.2');self.assertIsNot(calls[0][1][0],device)
  finally:window.shutdown()
