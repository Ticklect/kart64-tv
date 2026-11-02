import shutil, subprocess, tempfile, unittest
from pathlib import Path


@unittest.skipUnless(shutil.which('javac') and shutil.which('java'), 'JDK needed for the Android page upgrade test')
class GamePageTests(unittest.TestCase):
 def test_page_upgrade_is_idempotent_and_rejects_unknown_pages(self):
  root=Path(__file__).resolve().parents[1]
  with tempfile.TemporaryDirectory() as temp:
   folder=Path(temp)
   source=root/'android/app/src/main/java/com/ticklect/kart64/GamePage.java'
   test=folder/'GamePageCheck.java'
   test.write_text('''package com.ticklect.kart64;
public class GamePageCheck {
 public static void main(String[] args) {
  String page="<script>\\nconst ROM_SHA1=1;\\n  statusEl.textContent = t;\\nconst touchDevice = navigator.maxTouchPoints > 0 || qp.has('touch');";
  String upgraded=GamePage.augment(page);
  if(!upgraded.contains("tv-shell.js") || !upgraded.contains("loadingMessage(t, bad)") || !upgraded.contains("const touchDevice = false;"))throw new AssertionError();
  if(!upgraded.equals(GamePage.augment(upgraded)))throw new AssertionError("duplicate upgrade");
  try {GamePage.augment("unknown page");throw new AssertionError("accepted unknown runtime");}
  catch(IllegalArgumentException expected) {}
 }
}''',encoding='utf-8')
   subprocess.run(['javac','-d',str(folder),str(source),str(test)],check=True,capture_output=True)
   subprocess.run(['java','-cp',str(folder),'com.ticklect.kart64.GamePageCheck'],check=True,capture_output=True)
