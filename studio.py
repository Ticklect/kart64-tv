"""Kart64 TV desktop dashboard. Uses the existing, tested installer workers."""
import time,os,queue,sys,tempfile,threading,webbrowser,subprocess,json,shutil
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QSize
from PySide6.QtGui import QPainter,QPainterPath,QPen,QColor,QFont,QIcon
from PySide6.QtWidgets import (QApplication,QFileDialog,QFrame,QHBoxLayout,QLabel,QLineEdit,
    QListWidget,QListWidgetItem,QMainWindow,QMessageBox,QPlainTextEdit,QProgressBar,
    QPushButton,QScrollArea,QStackedWidget,QVBoxLayout,QWidget)
from installer import Installer
from installer_core import validate_tv_ip
from performance_store import load_results
from dashboard import latest_for_device
from platforms import platform_for,verify_webos_target
from webos_core import prepare_webos_stage
from installer_core import identify_game,prepare_rom
from tools_core import prepare_tool
from android_core import validate_android_serial,create_content_tar,classify_android_target,discover_android
from android_runtime import prepare_android_runtime
from uninstall import remove_app

DOWNLOADER_CODE = '7989374'
DOWNLOADER_URL = 'https://aftv.news/' + DOWNLOADER_CODE

# Original racing-menu palette; no game artwork is bundled.
STYLE = """
QWidget { background:#103364; color:#fff9e5; font-family:"Segoe UI"; font-size:14px; }
QFrame#sidebar { background:#081f40; border-right:2px solid #061730; }
QLabel { background:transparent; }
QLabel#title { font-family:"Arial Black"; font-size:28px; color:#ffe047; }
QLabel#muted { color:#bad0e7; }
QLabel#cardTitle { color:#ffffff; font-size:16px; font-weight:700; }
QLabel#eyebrow { color:#ffdc42; font-size:11px; font-weight:700; }
QLabel#downloaderCode { color:#ffe047; font-family:Consolas; font-size:30px; font-weight:700; }
QFrame#card, QFrame#catalogCard { background:#1c4370; border:1px solid #54799d; border-bottom:3px solid #061d39; border-radius:8px; }
QFrame#progressCard { background:#09254c; border:1px solid #597b9f; border-top:3px solid #ffdc42; border-radius:8px; }
QLabel#badgeTested { color:#b7efc8; background:#123d36; border:1px solid #438768; border-radius:4px; padding:5px 9px; font-size:12px; font-weight:700; }
QLabel#badgeExperimental { color:#ffe59a; background:#493f26; border:1px solid #847043; border-radius:4px; padding:5px 9px; font-size:12px; font-weight:700; }
QPushButton { background:#2d557f; border:1px solid #7795b4; border-bottom:3px solid #071f3d; color:white; border-radius:5px; font-weight:600; padding:10px 16px; }
QPushButton:hover { background:#3c6590; border-color:#ffe047; }
QPushButton:focus, QLineEdit:focus { border:2px solid #ffe047; }
QPushButton:disabled { background:#234566; color:#91a5ba; border-color:#365775; }
QPushButton#primary { background:#d94b32; color:white; border-color:#ffae70; border-bottom-color:#6a211c; }
QPushButton#primary:hover { background:#ee6146; }
QPushButton#primary:disabled { background:#493f4a; border-color:#645967; color:#a599a9; }
QPushButton#nav { background:transparent; color:#c7d9e7; border:1px solid transparent; text-align:left; padding:12px; }
QPushButton#nav:hover { background:#153a61; }
QPushButton#nav:checked { background:#ffdc42; color:#172d4d; border:1px solid #fff1a2; border-bottom:3px solid #b78420; }
QLineEdit { background:#0b284d; color:white; border:1px solid #648aab; border-radius:5px; padding:11px; selection-background-color:#315d8d; }
QListWidget { background:transparent; border:0; outline:0; }
QListWidget::item { background:#1c4370; border:1px solid #54799d; padding:6px; margin-bottom:5px; border-radius:4px; }
QListWidget::item:selected { background:#2a537b; border:1px solid #ffdc42; }
QListWidget#stageList::item { background:#12365c; border:0; border-left:3px solid #6d8ba6; padding:9px 12px; }
QListWidget#catalogList::item { background:transparent; border:0; padding:0; margin:0; }
QPlainTextEdit { background:#081f40; color:#d1e3f0; border:1px solid #54799d; border-radius:5px; padding:12px; font-family:Consolas; font-size:12px; }
QProgressBar { background:#061c39; border:0; border-radius:4px; min-height:8px; max-height:8px; }
QProgressBar::chunk { background:#ffdc42; border-radius:4px; }
QScrollBar:vertical { background:#09254c; width:8px; margin:0; }
QScrollBar::handle:vertical { background:#6484a5; border-radius:4px; min-height:28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background:none; }
"""

class CardList(QListWidget):
    def fit_cards(self):
        width=max(100,self.viewport().width()-18)
        for index in range(self.count()):
            item=self.item(index);widget=self.itemWidget(item)
            if widget:
                widget.setFixedWidth(width)
                height=widget.layout().totalHeightForWidth(width)
                item.setSizeHint(QSize(width,max(widget.minimumSizeHint().height(),height)))
    def resizeEvent(self,event):
        super().resizeEvent(event);self.fit_cards()

class RaceMark(QWidget):
    def __init__(self):
        super().__init__();self.setFixedHeight(110)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        for label,y,size,color in [('KART64',39,24,'#ffe047'),('TV',72,25,'#ff694a')]:
            shape=QPainterPath();font=QFont('Arial Black',size);font.setItalic(True);shape.addText(3,y,font,label)
            p.strokePath(shape,QPen(QColor('#030e22'),5,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin));p.fillPath(shape,QColor(color))
        p.setPen(Qt.NoPen)
        for row in range(2):
            for col in range((self.width()+9)//10):
                p.setBrush(QColor('#e9f0e6' if (row+col)%2==0 else '#122746'));p.drawRect(col*10,88+row*10,10,10)

def text(value,kind=None):
    label=QLabel(value);label.setWordWrap(True)
    if kind:label.setObjectName(kind)
    return label

def card():
    frame=QFrame();frame.setObjectName('card');layout=QVBoxLayout(frame);layout.setContentsMargins(18,14,18,18);layout.setSpacing(8);return frame,layout

class Engine(Installer):
    def __init__(self):
        self.events=queue.Queue();self.temp=tempfile.TemporaryDirectory(prefix='kart64-tools-');self.tool_dir=Path(self.temp.name);self.found=[]
        self.history_path=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'Kart64TV'/'performance.json'
    def run_uninstall(self,device,cli,lg_cli,lg_target):
        try:
            self.say('Removing Kart64 TV from '+device.get('name',device['ip'])+' ('+device['ip']+')…')
            remove_app(device,cli,self.tool_dir,lg_cli,lg_target,self.command,self.say);self.events.put(('done',True))
        except Exception as e:self.say('Uninstall stopped: '+str(e));self.events.put(('done',False))
    def connect_adb(self,address):
        try:
            address=validate_android_serial(address);adb=shutil.which('adb.exe') or shutil.which('adb')
            if not adb:raise ValueError('Install official Android platform-tools and add adb to PATH first.')
            self.say('Connecting to the selected ADB address. If the TV asks for debugging permission, approve it there.')
            result=subprocess.run([adb,'connect',address],capture_output=True,text=True,timeout=20,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if result.returncode:raise ValueError('ADB connection failed. Check the TV address and debugging settings.')
            found=discover_android()
            if not any(d['adb_serial']==address for d in found):raise ValueError('The target is not yet authorised or does not report TV features. Approve the prompt on the TV, or finish wireless pairing, then retry.')
            addresses={d['ip'] for d in found};self.found=[d for d in self.found if d['ip'] not in addresses]+found
            self.events.put(('tvs',self.found));self.say('Paired TV detected. Select it under Devices.');self.events.put(('done',True))
        except Exception as e:self.say('ADB connection stopped: '+str(e));self.events.put(('done',False))
    def run_android(self,serial,game):
        try:
            self.stage('Checking TV connection')
            serial=validate_android_serial(serial);adb=shutil.which('adb.exe') or shutil.which('adb')
            if not adb:raise ValueError('Install Android platform-tools and add adb to PATH, then pair your TV.')
            flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
            def query(args,**kwargs):return subprocess.run([adb,'-s',serial]+args,capture_output=True,timeout=60,creationflags=flags,**kwargs)
            features=query(['shell','pm','list','features'])
            if features.returncode:raise ValueError('This target is not authorised. Pair it and scan again.')
            sdk=query(['shell','getprop','ro.build.version.sdk']);abis=query(['shell','getprop','ro.product.cpu.abilist'])
            target_platform=classify_android_target(features.stdout.decode(errors='replace'),sdk.stdout.decode(errors='replace'),abis.stdout.decode(errors='replace'))
            self.say(('Fire OS TV' if target_platform=='firetv' else 'Android / Google TV')+' target verified. Installation remains experimental.')
            root=Path(__file__).resolve().parent
            cache=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'Kart64TV'/'runtimes'
            self.stage('Getting the TV launcher')
            apk=prepare_android_runtime(abis.stdout.decode(errors='replace'),cache,progress=self.say,transfer_progress=lambda done,total:self.stage('Downloading the TV launcher',done,total))
            self.stage('Launcher verified')
            node=self.tool('node')
            with tempfile.TemporaryDirectory(prefix='kart64-android-private-') as tmp:
                tmp=Path(tmp);archive=Path(game)
                self.stage('Preparing your game files')
                if identify_game(archive)=='rom':archive=prepare_rom(archive,tmp,self.say)
                runtime=tmp/'runtime';runtime.mkdir();self.say('Preparing Android TV game data locally…')
                self.stage('Downloading and verifying the game runtime')
                self.command([str(node),str(root/'src'/'build-runtime.cjs'),str(runtime)])
                self.stage('Packaging your game files')
                content=create_content_tar(runtime,archive,tmp/'content.tar')
                self.stage('Installing the TV launcher')
                self.say('Installing the Android TV app…');self.command([adb,'-s',serial,'install','-r',str(apk)])
                ready=query(['shell','run-as','com.ticklect.kart64','mkdir','-p','files/web'])
                if ready.returncode:raise ValueError('Could not open the private Android game folder.')
                clear=query(['shell','run-as','com.ticklect.kart64','rm','-f','files/web/ready.json'])
                if clear.returncode:raise ValueError('Could not prepare the Android installation marker.')
                self.stage('Transferring your game files to the TV')
                with content.open('rb') as stream:
                    result=subprocess.run([adb,'-s',serial,'exec-in','run-as','com.ticklect.kart64','tar','-x','-f','-','-C','files/web'],stdin=stream,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=300,creationflags=flags)
                if result.returncode:raise ValueError('Private game-data transfer did not complete.')
                self.stage('Finalising game installation')
                marker=query(['shell','run-as','com.ticklect.kart64','touch','files/web/ready.json'])
                if marker.returncode:raise ValueError('Could not mark Android game data ready.')
            self.say('Android TV app and private game data installed. Open Kart64 TV from the TV apps list; performance and controllers need testing on this device.');self.events.put(('done',True))
        except Exception as e:self.say('Android installation stopped: '+str(e));self.events.put(('done',False))
    def run_webos(self,ip,game,cli_dir,target):
        try:
            self.stage('Checking LG connection and tools')
            tools={name:Path(cli_dir)/(name+'.cmd') for name in ('ares-package','ares-install','ares-setup-device')}
            if not all(p.is_file() for p in tools.values()):raise ValueError('Select the official webOS CLI bin folder containing ares-package.cmd, ares-install.cmd and ares-setup-device.cmd.')
            flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
            p=subprocess.run([str(tools['ares-setup-device']),'--listfull'],capture_output=True,text=True,timeout=30,creationflags=flags)
            if p.returncode:raise ValueError('Could not read registered LG devices.')
            verify_webos_target(json.loads(p.stdout),target,ip)
            node=self.tool('node')
            with tempfile.TemporaryDirectory(prefix='kart64-webos-private-') as tmp:
                tmp=Path(tmp);archive=Path(game)
                self.stage('Preparing your game files')
                if identify_game(archive)=='rom':archive=prepare_rom(archive,tmp,self.say)
                runtime=tmp/'runtime';runtime.mkdir();stage=tmp/'webos';stage.mkdir()
                self.stage('Downloading and verifying the game runtime')
                self.say('Preparing the experimental webOS runtime…');self.command([str(node),str(Path(__file__).resolve().parent/'src'/'build-runtime.cjs'),str(runtime)])
                self.stage('Packaging your game files')
                prepare_webos_stage(runtime,archive,stage)
                self.command([str(tools['ares-package']),'--no-minify','--outdir',str(tmp),str(stage)])
                packages=list(tmp.glob('com.ticklect.kart64_*.ipk'))
                if len(packages)!=1:raise ValueError('webOS packaging did not produce exactly one app package.')
                self.stage('Installing on your LG TV')
                self.say('Installing on the selected registered LG TV…');self.command([str(tools['ares-install']),'--device',target,str(packages[0])])
                self.stage('Verifying the installed TV app')
                check=subprocess.run([str(tools['ares-install']),'--device',target,'--list'],capture_output=True,text=True,timeout=30,creationflags=flags)
                if check.returncode or 'com.ticklect.kart64' not in check.stdout:raise ValueError('Could not verify the installed LG app.')
            self.say('LG app installation verified. Game execution and controller support on this TV still need a real-device test.');self.events.put(('done',True))
        except Exception as e:self.say('LG installation stopped: '+str(e));self.events.put(('done',False))

class Studio(QMainWindow):
    def __init__(self,start_scan=True):
        super().__init__();self.engine=Engine();self.selected=None;self.busy=False;self.game='';self.cli='';self.devices=[]
        self.setWindowIcon(QIcon(str(Path(__file__).resolve().parent/'assets'/'kart64.ico')))
        self.setWindowTitle('Kart64 TV');self.resize(1200,800);self.setMinimumSize(950,680);self.setStyleSheet(STYLE)
        base=QWidget();self.setCentralWidget(base);outer=QHBoxLayout(base);outer.setContentsMargins(0,0,0,0);outer.setSpacing(0)
        sidebar=QFrame();sidebar.setObjectName('sidebar');sidebar.setFixedWidth(200);outer.addWidget(sidebar)
        side=QVBoxLayout(sidebar);side.setContentsMargins(18,28,18,22);side.setSpacing(8)
        side.addWidget(RaceMark());side.addSpacing(20)
        self.stack=QStackedWidget();self.nav=[]
        for i,label in enumerate(('Install','Devices','Performance','Activity','TV guide')):
            b=QPushButton(label);b.setObjectName('nav');b.setCheckable(True);b.clicked.connect(lambda checked=False,n=i:self.navigate(n));side.addWidget(b);self.nav.append(b)
        side.addStretch();self.task_status=text('Ready','muted');side.addWidget(self.task_status);side.addSpacing(8);side.addWidget(text('Development preview','muted'))
        outer.addWidget(self.stack,1)
        self.overview=self.page();self.tv_page=self.page();self.performance=self.page();self.activity=self.page();self.catalog=self.page()
        self.build_overview();self.build_tvs();self.build_performance();self.build_activity();self.build_catalog();self.update_selection();self.navigate(0)
        self.timer=QTimer(self);self.timer.timeout.connect(self.poll);self.timer.start(100)
        if start_scan:QTimer.singleShot(300,self.scan)
    def page(self):
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.NoFrame);body=QWidget();layout=QVBoxLayout(body);layout.setContentsMargins(36,30,36,30);layout.setSpacing(16);scroll.setWidget(body);self.stack.addWidget(scroll);return layout
    def navigate(self,index):
        self.stack.setCurrentIndex(index)
        for i,b in enumerate(self.nav):b.setChecked(i==index)
        if index==2:self.refresh_performance()
    def heading(self,layout,kicker,title,subtitle):
        layout.addWidget(text(title,'title'));layout.addWidget(text(subtitle,'muted'));layout.addSpacing(12)
    def build_overview(self):
        self.heading(self.overview,'','Install game','Choose a television and a local game file.')
        downloader,short=card();short.addWidget(text('Quick TV app install · Android / Google TV / Fire OS','cardTitle'))
        short.addWidget(text('On your TV, open Downloader by AFTVnews, enter this code and press Go to download and install Kart64 TV.','muted'))
        code_row=QHBoxLayout();self.downloader_code=text(DOWNLOADER_CODE,'downloaderCode');self.downloader_code.setTextInteractionFlags(Qt.TextSelectableByMouse);code_row.addWidget(self.downloader_code)
        copy=QPushButton('Copy code');copy.clicked.connect(self.copy_downloader_code);code_row.addWidget(copy);code_row.addStretch();short.addLayout(code_row)
        link=text('Short link: '+DOWNLOADER_URL,'muted');link.setTextInteractionFlags(Qt.TextSelectableByMouse);short.addWidget(link)
        short.addWidget(text('Downloader installs the TV launcher only. To play, use this Windows app and a paired TV to transfer your own compatible game data.','muted'))
        self.overview.addWidget(downloader)
        device,dl=card();dl.addWidget(text('Television','muted'));self.device_info=text('No TV selected','cardTitle');dl.addWidget(self.device_info);self.device_detail=text('Select a device from your network.','muted');dl.addWidget(self.device_detail);db=QPushButton('Select device');db.clicked.connect(lambda:self.navigate(1));dl.addWidget(db,alignment=Qt.AlignLeft);self.overview.addWidget(device)
        game,gl=card();gl.addWidget(text('Game file','muted'));self.game_name=text('No game file selected','cardTitle');gl.addWidget(self.game_name);self.game_info=text('US Mario Kart 64 ROM (.z64) or SpaghettiKart archive (.o2r).','muted');gl.addWidget(self.game_info);gb=QPushButton('Browse files');gb.clicked.connect(self.pick_game);gl.addWidget(gb,alignment=Qt.AlignLeft);self.overview.addWidget(game)
        self.next_title=text('Select a device','cardTitle');self.next_detail=text('','muted');self.overview.addWidget(self.next_title);self.overview.addWidget(self.next_detail)
        controls=QHBoxLayout();self.install_button=QPushButton('Install');self.install_button.setObjectName('primary');self.install_button.clicked.connect(self.install);controls.addWidget(self.install_button);self.test_button=QPushButton('Check compatibility');self.test_button.clicked.connect(self.benchmark);controls.addWidget(self.test_button);controls.addStretch();self.overview.addLayout(controls)
        self.overview.addWidget(text('Developer Mode and platform-specific setup are required. First game launch can take several minutes.','muted'))
        self.progress=QProgressBar();self.progress.setRange(0,0);self.progress.hide();self.overview.addWidget(self.progress);self.overview.addStretch()
    def copy_downloader_code(self):
        QApplication.clipboard().setText(DOWNLOADER_CODE)
    def build_tvs(self):
        self.heading(self.tv_page,'','Devices','Televisions on your local network.')
        bar=QHBoxLayout();self.scan_button=QPushButton('Scan network');self.scan_button.clicked.connect(self.scan);bar.addWidget(self.scan_button);bar.addStretch();self.tv_page.addLayout(bar)
        self.found_label=text('Searching finds devices on the same local network.','muted');self.tv_page.addWidget(self.found_label)
        self.tv_list=QListWidget();self.tv_list.setMinimumHeight(260);self.tv_list.currentRowChanged.connect(self.select_device);self.tv_page.addWidget(self.tv_list,1)
        self.selected_tv_note=text('Select a device to continue.','muted');self.tv_page.addWidget(self.selected_tv_note)
        go=QPushButton('Use selected device');go.clicked.connect(lambda:self.navigate(0));self.tv_page.addWidget(go,alignment=Qt.AlignLeft)
        self.uninstall_button=QPushButton('Uninstall Kart64 TV…');self.uninstall_button.clicked.connect(self.uninstall_selected);self.tv_page.addWidget(self.uninstall_button,alignment=Qt.AlignLeft)
        self.tv_note=text('Samsung, experimental LG webOS, Android/Google TV and eligible Fire OS TV routes. Gameplay varies by model.','muted');self.tv_page.addWidget(self.tv_note)
        adb_guide=QPushButton('Android / Google TV pairing instructions');adb_guide.clicked.connect(lambda:webbrowser.open('https://developer.android.com/tools/adb#connect-to-a-device-over-wi-fi'));self.tv_page.addWidget(adb_guide,alignment=Qt.AlignLeft)
        self.tv_page.addWidget(text('Pair Android or Fire OS TVs with adb first, then scan again. Only authorised network targets reporting TV features are listed.','muted'))
        adb_row=QHBoxLayout();self.adb_address=QLineEdit();self.adb_address.setPlaceholderText('Android / Fire OS TV IP:ADB port, e.g. 192.168.1.20:5555');adb_row.addWidget(self.adb_address)
        connect=QPushButton('Connect ADB');connect.clicked.connect(self.connect_adb);adb_row.addWidget(connect);self.tv_page.addLayout(adb_row)
        fire_guide=QPushButton('Fire TV connection instructions');fire_guide.clicked.connect(lambda:webbrowser.open('https://developer.amazon.com/docs/fire-tv/connecting-adb-to-device.html'));self.tv_page.addWidget(fire_guide,alignment=Qt.AlignLeft)
        manual=QHBoxLayout();self.manual_ip=QLineEdit();self.manual_ip.setPlaceholderText('Samsung TV local IP address');manual.addWidget(self.manual_ip);use=QPushButton('Use address');use.clicked.connect(self.use_manual);manual.addWidget(use);self.tv_page.addLayout(manual)
        self.tv_page.addWidget(text('Manual addresses are treated as Samsung and are not verified until connection.','muted'))
        override=QPushButton('Advanced: choose an Apps2Samsung CLI');override.clicked.connect(self.pick_cli);self.tv_page.addWidget(override,alignment=Qt.AlignLeft)
        self.lg_setup=QFrame();lg=QVBoxLayout(self.lg_setup);lg.setContentsMargins(0,8,0,8)
        lg.addWidget(text('LG webOS · experimental installer','cardTitle'))
        lg.addWidget(text('Enable LG Developer Mode, pair the TV with the official webOS CLI, then select its bin folder and registered device name. Gameplay is unverified.','muted'))
        self.lg_cli=QLineEdit();self.lg_cli.setPlaceholderText('webOS CLI bin folder');lg.addWidget(self.lg_cli)
        choose_lg=QPushButton('Choose CLI folder');choose_lg.clicked.connect(self.pick_lg_cli);lg.addWidget(choose_lg,alignment=Qt.AlignLeft)
        self.lg_target=QLineEdit();self.lg_target.setPlaceholderText('Registered device name, e.g. livingroom');lg.addWidget(self.lg_target)
        guide=QPushButton('LG setup instructions');guide.clicked.connect(lambda:webbrowser.open('https://webostv.developer.lge.com/develop/getting-started/developer-mode-app'));lg.addWidget(guide,alignment=Qt.AlignLeft)
        self.lg_cli.textChanged.connect(lambda _:self.update_selection());self.lg_target.textChanged.connect(lambda _:self.update_selection());self.lg_setup.hide();self.tv_page.addWidget(self.lg_setup)
    def build_performance(self):
        self.heading(self.performance,'MEASURED ON YOUR TV','Performance','Local results from compatibility checks. No automatic uploads.')
        self.performance_title=text('No recorded result','cardTitle');panel,pl=card();pl.addWidget(text('Latest result','muted'));pl.addWidget(self.performance_title);self.performance_detail=text('Select a device to view its results.','muted');pl.addWidget(self.performance_detail);self.performance.addWidget(panel)
        self.performance_test=QPushButton('Run TV compatibility check');self.performance_test.setObjectName('primary');self.performance_test.clicked.connect(self.benchmark);self.performance.addWidget(self.performance_test,alignment=Qt.AlignLeft)
        self.performance.addWidget(text('History','cardTitle'));self.history=QListWidget();self.history.setMinimumHeight(200);self.performance.addWidget(self.history,1)
        self.performance.addWidget(text('Graphics callbacks are a synthetic workload, not game FPS. CPU work is a synthetic score, not utilisation. These figures do not predict gameplay.','muted'))
    def build_activity(self):
        self.heading(self.activity,'WHAT IS HAPPENING','Activity','Setup progress and diagnostic messages appear here.')
        hero,hero_layout=card();hero.setObjectName('progressCard')
        hero_layout.setContentsMargins(22,18,22,20)
        hero_layout.addWidget(text('INSTALLATION STATUS','eyebrow'))
        self.activity_state=text('Ready when you are','cardTitle');hero_layout.addWidget(self.activity_state)
        self.activity_progress=QProgressBar();self.activity_progress.setTextVisible(False);self.activity_progress.setRange(0,0);self.activity_progress.hide();hero_layout.addWidget(self.activity_progress)
        hero_layout.addWidget(text('Percentages measure this download. Other steps show elapsed time.','muted'))
        self.activity.addWidget(hero)
        self.stage_list=QListWidget();self.stage_list.setObjectName('stageList');self.stage_list.setMinimumHeight(120);self.stage_list.setMaximumHeight(240);self.stage_list.hide();self.activity.addWidget(self.stage_list)
        self.current_stage=None;self.stage_started=0;self.stage_finished=False;self.stage_percent=None
        self.diagnostics_toggle=QPushButton('Show diagnostic log');self.diagnostics_toggle.setCheckable(True);self.activity.addWidget(self.diagnostics_toggle,alignment=Qt.AlignLeft)
        self.log=QPlainTextEdit();self.log.setReadOnly(True);self.log.setMinimumHeight(180);self.log.hide();self.activity.addWidget(self.log,1)
        self.diagnostics_toggle.toggled.connect(self.show_diagnostics)
        self.activity.addStretch()
        b=QPushButton('Official SpaghettiKart releases');b.clicked.connect(lambda:webbrowser.open('https://github.com/HarbourMasters/SpaghettiKart/releases'));self.activity.addWidget(b,alignment=Qt.AlignLeft)
    def show_diagnostics(self,visible):
        self.log.setVisible(visible)
        self.diagnostics_toggle.setText('Hide diagnostic log' if visible else 'Show diagnostic log')
    def build_catalog(self):
        self.heading(self.catalog,'','TV guide','Search recorded evidence and experimental installation routes.')
        self.catalog_search=QLineEdit();self.catalog_search.setClearButtonEnabled(True);self.catalog_search.setPlaceholderText('Search model, brand, operating system or controller')
        self.catalog.addWidget(self.catalog_search)
        self.catalog_summary=text('','muted');self.catalog.addWidget(self.catalog_summary)
        self.catalog_list=CardList();self.catalog_list.setObjectName('catalogList');self.catalog_list.setWordWrap(True);self.catalog_list.setSpacing(8);self.catalog.addWidget(self.catalog_list,1)
        self.catalog_rows=json.loads((Path(__file__).resolve().parent/'assets'/'tv-catalog.json').read_text(encoding='utf-8'))
        self.catalog_search.textChanged.connect(self.refresh_catalog);self.refresh_catalog()
        self.catalog.addWidget(text('Recorded observations, not predictions. A matching brand or similar model does not establish compatibility. No results are uploaded automatically.','muted'))
    def refresh_catalog(self):
        terms=self.catalog_search.text().casefold().split();self.catalog_list.clear()
        for row in self.catalog_rows:
            if not all(term in ' '.join(row.values()).casefold() for term in terms):continue
            value=f"{row['brand']} · {row['model']}\n{row['status']} · {row['os']}\nController: {row['controller']}\nBoot: {row['timing']}\nFPS: not measured\n{row['notes']}"
            item=QListWidgetItem(value);self.catalog_list.addItem(item)
            panel,body=card();panel.setObjectName('catalogCard');body.setContentsMargins(18,16,18,18);body.setSpacing(10)
            top=QHBoxLayout();top.addWidget(text(row['brand'].upper(),'eyebrow'),1)
            badge=text(row['status'],'badgeTested' if row['status']=='Race tested' else 'badgeExperimental');badge.setWordWrap(False);top.addWidget(badge);body.addLayout(top)
            body.addWidget(text(row['model'],'cardTitle'));body.addWidget(text(row['os'],'muted'))
            body.addWidget(text('CONTROLLER','eyebrow'));body.addWidget(text(row['controller']))
            body.addWidget(text('RECORDED BOOT','eyebrow'));body.addWidget(text(row['timing']))
            body.addWidget(text('FPS: not measured','muted'));body.addWidget(text(row['notes'],'muted'))
            self.catalog_list.setItemWidget(item,panel)
        self.catalog_list.fit_cards()
        count=self.catalog_list.count()
        tested=sum(row['status']=='Race tested' for row in self.catalog_rows)
        self.catalog_summary.setText(f'{count} matching entries · {tested} exact TV model race-tested in this guide' if count else 'No matching evidence. This model has not been recorded in the guide.')
    def show_stage(self,value):
        label=value['label']
        if self.current_stage!=label:
            if self.current_stage and self.stage_list.count():self.stage_list.item(self.stage_list.count()-1).setText('Done · '+self.current_stage)
            self.current_stage=label;self.stage_started=time.monotonic();self.stage_finished=False
            self.stage_list.addItem('Working · '+label);self.stage_list.setFixedHeight(min(240,self.stage_list.count()*44+8));self.stage_list.show();self.stage_list.scrollToBottom()
        done,total=value.get('completed'),value.get('total');self.stage_percent=None
        if isinstance(total,(int,float)) and total>0 and isinstance(done,(int,float)) and 0<=done<=total:
            self.stage_percent=int(done*100/total)
            for bar in (self.progress,self.activity_progress):bar.setRange(0,100);bar.setValue(self.stage_percent)
        else:
            for bar in (self.progress,self.activity_progress):bar.setRange(0,0)
        self.update_stage_time()
    def update_stage_time(self):
        if self.current_stage and not self.stage_finished:
            seconds=int(time.monotonic()-self.stage_started)
            measured=f' · {self.stage_percent}% of download' if self.stage_percent is not None else ''
            self.activity_state.setText(f'{self.current_stage}{measured} · {seconds}s')
    def finish_stages(self,success):
        if not success:self.diagnostics_toggle.setChecked(True)
        if not self.current_stage:return
        self.stage_finished=True
        self.stage_list.item(self.stage_list.count()-1).setText(('Done' if success else 'Failed')+' · '+self.current_stage)
        self.activity_state.setText('Finished' if success else 'Stopped during '+self.current_stage+' — see details below')
    def set_game(self,path):
        self.game=path;self.game_name.setText(Path(path).name if path else 'No game file selected');self.game_info.setText('Selected — file is checked when installation starts.' if path else 'Use your own supported US ROM or compatible archive.');self.update_selection()
    def pick_game(self):
        path,_=QFileDialog.getOpenFileName(self,'Choose your game file','','Supported game files (*.z64 *.o2r);;All files (*)')
        if path:self.set_game(path)
    def pick_cli(self):
        path,_=QFileDialog.getOpenFileName(self,'Choose Apps2Samsung CLI','','Apps2Samsung CLI (apps2samsung-cli.exe)')
        if path:
            if Path(path).name.lower()!='apps2samsung-cli.exe':QMessageBox.warning(self,'Invalid tool','Choose apps2samsung-cli.exe.');return
            self.cli=path;self.log.appendPlainText('Using the selected Apps2Samsung CLI.')
    def pick_lg_cli(self):
        path=QFileDialog.getExistingDirectory(self,'Choose official webOS CLI bin folder')
        if path:self.lg_cli.setText(path)
    def set_devices(self,devices):
        previous=self.selected.get('ip') if self.selected else None
        self.tv_list.blockSignals(True);self.devices=devices;self.engine.found=devices;self.tv_list.clear();self.selected=None
        for d in devices:
            status='Incompatible runtime' if d.get('android_compatible') is False else ('Fire OS · experimental' if platform_for(d)=='firetv' else ('Android TV · experimental' if platform_for(d)=='androidtv' else ('LG setup required' if platform_for(d)=='webos' else ('Experimental' if d.get('supported') else 'Unsupported'))))
            title=d.get('name') or 'TV';model=d.get('model') or 'Model unknown';brand=d.get('brand','Unknown brand')
            tile=QWidget();tile.setAttribute(Qt.WA_TransparentForMouseEvents);tile.setStyleSheet('background:transparent;');row=QHBoxLayout(tile);row.setContentsMargins(14,7,14,7);row.setSpacing(15)
            details=QVBoxLayout();details.setSpacing(3);details.addWidget(text(title,'cardTitle'));details.addWidget(text(f"{brand}  ·  {model}  ·  {d.get('ip','')}",'muted'));row.addLayout(details,1)
            badge=text(status,'muted');row.addWidget(badge)
            item=QListWidgetItem();item.setSizeHint(QSize(0,84));self.tv_list.addItem(item);self.tv_list.setItemWidget(item,tile)
        index=next((i for i,d in enumerate(devices) if d.get('ip')==previous),0 if len(devices)==1 else -1)
        if index>=0:self.tv_list.setCurrentRow(index);self.selected=devices[index]
        self.tv_list.blockSignals(False)
        self.found_label.setText(f"{len(devices)} device{'s' if len(devices)!=1 else ''} found on your network." if devices else 'No TVs found. Check the connection or enter a Samsung TV address below.')
        self.update_selection();self.refresh_performance()
    def select_device(self,index):
        self.selected=self.devices[index] if 0<=index<len(self.devices) else None;self.update_selection();self.refresh_performance()
    def use_manual(self):
        try:ip=validate_tv_ip(self.manual_ip.text())
        except ValueError as e:QMessageBox.warning(self,'Invalid address',str(e));return
        self.selected=next((x for x in self.devices if x['ip']==ip),{'ip':ip,'brand':'Samsung','name':'Manual address','model':'','supported':True,'manual':True})
        self.update_selection();self.refresh_performance()
    def update_selection(self):
        device=self.selected
        if device:
            self.device_info.setText(device.get('name') or device.get('model') or 'TV selected')
            label='Manual address · Samsung not verified' if device.get('manual') else ((device.get('model') or 'Model unknown')+' · '+('Samsung experimental' if device.get('supported') else 'Installation not supported yet'))
            self.device_detail.setText(label)
            if hasattr(self,'selected_tv_note'):self.selected_tv_note.setText('Selected: '+(device.get('name') or device.get('model') or 'TV')+'  ·  '+label)
        else:
            self.device_info.setText('No TV selected');self.device_detail.setText('Find TVs on your local network.')
            if hasattr(self,'selected_tv_note'):self.selected_tv_note.setText('Select a device to continue.')
        allowed=bool(device and device.get('supported')) and not self.busy
        self.test_button.setEnabled(allowed);self.install_button.setEnabled(allowed and bool(self.game))
        webos=bool(device and platform_for(device)=='webos')
        android=bool(device and platform_for(device) in ('androidtv','firetv'))
        if android:
            self.install_button.setEnabled(not self.busy and bool(self.game) and device.get('android_compatible',True))
            self.device_detail.setText(device.get('compatibility_error') or ('Fire OS TV · experimental ADB installation' if platform_for(device)=='firetv' else 'Android / Google TV · experimental ADB installation'))
        if hasattr(self,'lg_setup'):
            self.lg_setup.setVisible(webos)
            if webos:self.install_button.setEnabled(not self.busy and bool(self.game) and bool(self.lg_cli.text().strip()) and bool(self.lg_target.text().strip()));self.device_detail.setText('LG webOS · experimental installation; configure in Devices')
        if hasattr(self,'performance_test'):self.performance_test.setEnabled(allowed)
        if hasattr(self,'uninstall_button'):
            removable=bool(device and platform_for(device) in ('tizen','webos','androidtv','firetv'))
            if webos:removable=bool(self.lg_cli.text().strip() and self.lg_target.text().strip())
            self.uninstall_button.setEnabled(removable and not self.busy)
        if not device:self.next_title.setText('Select a television to continue');self.next_detail.setText('Available televisions are listed under Devices.')
        elif android:self.next_title.setText('Experimental Fire OS installation' if platform_for(device)=='firetv' else 'Experimental Android TV installation');self.next_detail.setText(device.get('compatibility_error') or 'The app checks browser features on launch. Physical controls and performance need testing.')
        elif webos:self.next_title.setText('Experimental LG installation');self.next_detail.setText('Configure webOS CLI and the registered TV name under Devices.')
        elif not device.get('supported'):self.next_title.setText('Installation unavailable');self.next_detail.setText('This device does not have an installation adapter yet.')
        elif not self.game:self.next_title.setText('Select a game file to continue');self.next_detail.setText('The file will be validated before installation.')
        else:self.next_title.setText('Ready to install');self.next_detail.setText('You can check compatibility before installing.')
    def refresh_performance(self):
        rows=load_results(self.engine.history_path);self.history.clear();last=latest_for_device(rows,self.selected)
        if last:
            self.performance_title.setText(last.get('model','Unknown model'));self.performance_detail.setText(f"CPU work: {last.get('cpu_iterations','—')} / sec   •   Graphics callbacks: {last.get('graphics_callbacks','—')} / sec\nRecorded {last.get('time','')}")
        else:self.performance_title.setText('No result for this TV yet');self.performance_detail.setText('Select a supported TV and run a check to see its results here.')
        for row in reversed(rows):self.history.addItem(f"{row.get('model','Unknown model')}   •   {row.get('time','')}\nCPU work {row.get('cpu_iterations','—')} / sec   |   Graphics callbacks {row.get('graphics_callbacks','—')} / sec")
    def start_work(self,target,args,show_activity=True):
        if self.busy:return
        self.current_stage=None;self.stage_list.clear();self.stage_list.hide();self.stage_percent=None;self.stage_finished=False
        for bar in (self.progress,self.activity_progress):bar.setRange(0,0)
        self.busy=True;self.scan_button.setEnabled(False);self.tv_list.setEnabled(False);self.progress.show();self.activity_progress.show();self.activity_state.setText('Working…');self.task_status.setText('●  Working · see Activity');self.update_selection()
        if show_activity:self.navigate(3)
        threading.Thread(target=target,args=args,daemon=True).start()
    def scan(self):self.start_work(self.engine.scan,(self.cli,),show_activity=False)
    def uninstall_selected(self):
        if self.busy or not self.selected:return
        device=dict(self.selected)
        title=device.get('name') or device.get('model') or 'Selected TV'
        answer=QMessageBox.question(self,'Uninstall Kart64 TV',f"Remove Kart64 TV from {title} ({device['ip']})?\n\nThis removes the TV app and can delete its game data and saved progress.",QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
        if answer==QMessageBox.Yes:self.start_work(self.engine.run_uninstall,(device,self.cli,self.lg_cli.text().strip(),self.lg_target.text().strip()))
    def connect_adb(self):self.start_work(self.engine.connect_adb,(self.adb_address.text().strip(),))
    def benchmark(self):
        if self.selected and self.selected.get('supported'):self.start_work(self.engine.run_benchmark,(self.selected['ip'],self.cli))
    def install(self):
        if self.selected and platform_for(self.selected) in ('androidtv','firetv') and self.selected.get('android_compatible',True) and self.game:
            self.start_work(self.engine.run_android,(self.selected['adb_serial'],Path(self.game)))
        elif self.selected and platform_for(self.selected)=='webos' and self.game:
            self.start_work(self.engine.run_webos,(self.selected['ip'],Path(self.game),self.lg_cli.text().strip(),self.lg_target.text().strip()))
        elif self.selected and self.selected.get('supported') and self.game:self.start_work(self.engine.run,(self.selected['ip'],Path(self.game),self.cli))
    def poll(self):
        try:
            while True:
                kind,value=self.engine.events.get_nowait()
                if kind=='stage':self.show_stage(value)
                elif kind=='log':self.log.appendPlainText(str(value))
                elif kind=='cli_ready':self.cli=str(value)
                elif kind=='tvs':self.set_devices(value)
                elif kind=='history':self.refresh_performance()
                elif kind=='done':self.finish_stages(value);self.busy=False;self.scan_button.setEnabled(True);self.tv_list.setEnabled(True);self.progress.hide();self.activity_progress.hide();self.activity_state.setText(('Finished' if value else 'Stopped — see details below') if not self.current_stage else self.activity_state.text());self.task_status.setText('●  Ready' if value else '●  Check Activity');self.update_selection()
        except queue.Empty:pass
        self.update_stage_time()
    def shutdown(self):
        self.timer.stop();self.engine.temp.cleanup();self.hide()
    def closeEvent(self,event):
        if self.busy:QMessageBox.information(self,'Task in progress','Please wait for the current task to finish before closing.');event.ignore()
        else:self.shutdown();event.accept()

def main():
    if os.name=='nt':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Ticklect.Kart64TV')
    if sys.argv[1:]==['--self-test']:
        root=Path(__file__).resolve().parent
        pin=json.loads((root/'assets'/'android-runtime.json').read_text())
        variants=pin['variants']
        valid=all(abi in variants and variants[abi]['size']>0 and len(variants[abi]['sha256'])==64 and variants[abi]['url'].startswith('https://') for abi in ('arm64-v8a','armeabi-v7a','x86_64'))
        return 0 if all((root/'benchmark'/n).is_file() for n in ('index.html','run.js','benchmark.js')) and (root/'src'/'build-runtime.cjs').is_file() and valid else 1
    if sys.argv[1:]==['--smoke-test']:
        app=QApplication(sys.argv);window=Studio(start_scan=False);window.show();app.processEvents()
        window.set_devices([{'ip':'10.0.0.2','brand':'Samsung','name':'Test TV','model':'Test model','supported':True}]);window.set_game('test.z64');window.navigate(1);app.processEvents()
        ok=window.tv_list.count()==1 and window.install_button.isEnabled() and window.test_button.isEnabled() and window.downloader_code.text()==DOWNLOADER_CODE and not window.grab().isNull()
        window.shutdown();return 0 if ok else 1
    app=QApplication(sys.argv);window=Studio();window.show();return app.exec()
if __name__=='__main__':sys.exit(main())
