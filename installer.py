"""Experimental Windows installer. Creates private packages only on this computer."""
from pathlib import Path
import json, os, queue, secrets, shutil, socket, subprocess, sys, tempfile, threading, tkinter as tk, urllib.error, urllib.request, webbrowser
from tkinter import filedialog, messagebox, ttk
from installer_core import validate_tv_ip, validate_archive, make_package, parse_discovery, identify_game, prepare_rom
from tools_core import prepare_tool, resolve_cli
from benchmark_core import make_benchmark, parse_debug_port, format_benchmark
from discovery import discover_other_tvs, merge_devices
from performance_store import save_result,load_results
from dashboard import device_status,latest_for_device,game_status

ROOT = Path(__file__).resolve().parent

class Installer:
    def __init__(self, root):
        self.root=root; root.title('Kart64 TV — prototype');root.geometry('980x820');root.minsize(850,800)
        style=ttk.Style(root);style.theme_use('clam')
        style.configure('.',font=('Segoe UI',10),background='#f3f6fc',foreground='#17233e')
        style.configure('TFrame',background='#f3f6fc');style.configure('TLabel',background='#f3f6fc')
        style.configure('TButton',padding=(12,8),background='#e4eafa',borderwidth=0)
        style.map('TButton',background=[('active','#d2def7'),('disabled','#edf0f6')])
        style.configure('Primary.TButton',padding=(16,11),font=('Segoe UI',10,'bold'),background='#315fc0',foreground='#ffffff')
        style.map('Primary.TButton',background=[('active','#244eaa'),('disabled','#a7b6d2')],foreground=[('disabled','#eef1f7')])
        style.configure('TNotebook',background='#f3f6fc',borderwidth=0)
        style.configure('TNotebook.Tab',padding=(16,9),background='#e5eaf4')
        style.map('TNotebook.Tab',background=[('selected','#ffffff')])
        style.configure('Treeview',rowheight=31,background='#ffffff',fieldbackground='#ffffff',borderwidth=0)
        style.configure('Treeview.Heading',font=('Segoe UI',10,'bold'),padding=7)
        style.map('Treeview',background=[('selected','#315fc0')],foreground=[('selected','#ffffff')])
        self.events=queue.Queue();self.busy=False;self.tool_temp=tempfile.TemporaryDirectory(prefix='kart64-tools-');self.tool_dir=Path(self.tool_temp.name)
        self.history_path=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'Kart64TV'/'performance.json'
        self.ip=tk.StringVar();self.archive=tk.StringVar();self.cli=tk.StringVar();self.found=[]
        shell=ttk.Frame(root,padding=20);shell.pack(fill='both',expand=True)
        header=tk.Frame(shell,background='#17233e',padx=20,pady=14);header.pack(fill='x',pady=(0,14))
        tk.Label(header,text='KART64',font=('Segoe UI',20,'bold'),foreground='#ffffff',background='#17233e').pack(side='left')
        tk.Label(header,text='TV',font=('Segoe UI',20,'bold'),foreground='#7ea5ff',background='#17233e').pack(side='left',padx=(5,0))
        tk.Label(header,text='EXPERIMENTAL PROTOTYPE',font=('Segoe UI',9,'bold'),foreground='#bfd0f2',background='#17233e').pack(side='right')
        activity=ttk.Frame(shell);activity.pack(side='bottom',fill='x',pady=(10,0))
        tabs=ttk.Notebook(shell);tabs.pack(fill='both',expand=True);self.tabs=tabs
        main=ttk.Frame(tabs,padding=16);devices=ttk.Frame(tabs,padding=16);performance=ttk.Frame(tabs,padding=16)
        tabs.add(main,text='  Install  ');tabs.add(devices,text='  TVs  ');tabs.add(performance,text='  Performance  ')
        ttk.Label(main,text='Let’s get you racing',font=('Segoe UI',19,'bold')).pack(anchor='w')
        ttk.Label(main,text='Choose your TV and your game file. We’ll prepare the rest on this PC.',wraplength=760).pack(anchor='w',pady=(3,12))
        selected=tk.Frame(main,background='#ffffff',padx=16,pady=11,highlightbackground='#dbe4f4',highlightthickness=1);selected.pack(fill='x',pady=(0,8))
        tk.Label(selected,text='01  YOUR TV',font=('Segoe UI',9,'bold'),foreground='#5573af',background='#ffffff').pack(anchor='w')
        self.selected_title=tk.Label(selected,text='No TV selected',font=('Segoe UI',13,'bold'),foreground='#17233e',background='#ffffff');self.selected_title.pack(anchor='w')
        self.selected_detail=tk.Label(selected,text='Find a TV or enter a Samsung TV address.',font=('Segoe UI',9),foreground='#56647e',background='#ffffff');self.selected_detail.pack(anchor='w')
        ttk.Button(selected,text='Choose a TV →',command=lambda:self.tabs.select(1)).pack(anchor='e')
        ttk.Label(devices,text='Your TVs',font=('Segoe UI',16,'bold')).pack(anchor='w')
        ttk.Label(devices,text='Discovery can find several brands. Installation and testing currently use Samsung developer tools.',wraplength=760).pack(anchor='w',pady=(5,10))
        self.field(devices,'TV local IP address (manual entry is for Samsung only)',self.ip,None)
        scanrow=ttk.Frame(devices);scanrow.pack(fill='x');self.scan_button=ttk.Button(scanrow,text='Find TVs',command=self.find_tvs);self.scan_button.pack(side='left');self.tv_choice=ttk.Combobox(scanrow,state='readonly');self.tv_choice.pack(side='left',fill='x',expand=True,padx=(8,0));self.tv_choice.bind('<<ComboboxSelected>>',self.select_tv)
        self.tv_table=ttk.Treeview(devices,columns=('brand','model','support'),show='headings',height=8)
        for key,title in [('brand','Brand'),('model','Model / name'),('support','Installation')]:self.tv_table.heading(key,text=title);self.tv_table.column(key,width=200,anchor='w')
        self.tv_table.pack(fill='both',expand=True,pady=(14,0));self.tv_table.bind('<<TreeviewSelect>>',self.select_table_tv)
        advanced=ttk.LabelFrame(devices,text='Advanced: optional Apps2Samsung CLI override',padding=6);advanced.pack(fill='x',pady=(10,0));self.field(advanced,'Leave blank to download automatically',self.cli,self.pick_cli)
        ttk.Label(performance,text='TV performance',font=('Segoe UI',16,'bold')).pack(anchor='w')
        ttk.Label(performance,text='Local compatibility checks saved on this PC. Synthetic graphics callbacks are not game FPS; CPU scores are a synthetic workload, not CPU utilisation. No data is uploaded.',wraplength=760).pack(anchor='w',pady=(5,10))
        self.performance_summary=tk.Label(performance,text='',font=('Segoe UI',11,'bold'),foreground='#244eaa',background='#e4ebfa',padx=14,pady=12,anchor='w',justify='left');self.performance_summary.pack(fill='x',pady=(0,10))
        self.history_table=ttk.Treeview(performance,columns=('date','model','cpu','graphics'),show='headings',height=7)
        for key,title,width in [('date','Time (UTC)',160),('model','TV model',220),('cpu','CPU work / sec',150),('graphics','Graphics callbacks / sec',180)]:self.history_table.heading(key,text=title);self.history_table.column(key,width=width,anchor='w')
        self.history_table.pack(fill='both',expand=True);self.refresh_history()
        ttk.Label(main,text='02  YOUR GAME',font=('Segoe UI',9,'bold'),foreground='#5573af').pack(anchor='w',pady=(5,0))
        self.field(main,'Supported US ROM (.z64) or SpaghettiKart archive (.o2r)',self.archive,self.pick_archive)
        self.game_label=ttk.Label(main,text='No game file selected',foreground='#56647e');self.game_label.pack(anchor='w')
        ttk.Button(main,text='Get SpaghettiKart ↗',command=lambda:webbrowser.open('https://github.com/HarbourMasters/SpaghettiKart/releases')).pack(anchor='w',pady=(4,0))
        ttk.Label(main,text='Samsung Developer Mode and account sign-in are required. Setup tools are downloaded and checked. Your game data stays on this PC and the selected TV.',wraplength=760).pack(anchor='w',pady=(8,10))
        actions=ttk.Frame(main);actions.pack(anchor='w');self.install=ttk.Button(actions,text='Prepare & install →',style='Primary.TButton',command=self.start);self.install.pack(side='left');self.benchmark_button=ttk.Button(actions,text='Test TV compatibility',command=self.start_benchmark);self.benchmark_button.pack(side='left',padx=(10,0))
        ttk.Label(activity,text='Activity',font=('Segoe UI',10,'bold')).pack(anchor='w')
        self.log=tk.Text(activity,height=4,wrap='word',state='disabled',background='#17233e',foreground='#e7eeff',insertbackground='white',relief='flat',padx=10,pady=8,font=('Segoe UI',9));self.log.pack(fill='x',pady=(4,0))
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        self.ip.trace_add('write',lambda *_:self.refresh_selection());self.archive.trace_add('write',lambda *_:self.game_label.config(text=game_status(self.archive.get())))
        self.root.after(100,self.poll)
        found_cli=shutil.which('apps2samsung-cli.exe')
        if found_cli:self.cli.set(found_cli)
        self.root.after(250,self.find_tvs)
    def close(self):
        if self.busy:messagebox.showwarning('Installation in progress','Please wait for the current installation to finish before closing.')
        else:self.tool_temp.cleanup();self.root.destroy()
    def field(self,parent,label,var,browse):
        row=ttk.Frame(parent);row.pack(fill='x',pady=4);ttk.Label(row,text=label).pack(anchor='w');line=ttk.Frame(row);line.pack(fill='x');ttk.Entry(line,textvariable=var).pack(side='left',fill='x',expand=True)
        if browse:ttk.Button(line,text='Browse…',command=browse).pack(side='left',padx=(6,0))
    def pick_archive(self):
        f=filedialog.askopenfilename(title='Choose your own game file',filetypes=[('Supported ROM or game archive','*.z64 *.o2r'),('All files','*.*')]);
        if f:self.archive.set(f)
    def pick_cli(self):
        f=filedialog.askopenfilename(title='Choose Apps2Samsung CLI',filetypes=[('Windows program','*.exe'),('All files','*.*')]);
        if f:
            self.cli.set(f);self.find_tvs()
    def select_tv(self,event=None):
        index=self.tv_choice.current()
        if 0<=index<len(self.found):
            device=self.found[index];self.ip.set(device['ip'])
            if not device.get('supported',True):self.say(device['brand']+' TV found; installation and testing on this brand are not supported yet.')
    def select_table_tv(self,event=None):
        selected=self.tv_table.selection()
        if selected:
            index=int(selected[0]);self.tv_choice.current(index);self.select_tv()
    def selected_device(self):
        return next((d for d in self.found if d.get('ip')==self.ip.get().strip()),None)
    def refresh_selection(self):
        title,detail=device_status(self.selected_device(),self.ip.get().strip())
        self.selected_title.config(text=title);self.selected_detail.config(text=detail)
        self.refresh_history()
    def refresh_history(self):
        self.history_table.delete(*self.history_table.get_children())
        rows=load_results(self.history_path);last=latest_for_device(rows,self.selected_device())
        if last:
            graphics=last.get('graphics_callbacks')
            self.performance_summary.config(text='Latest for '+last['model']+'   •   '+str(last.get('cpu_iterations','—'))+' CPU work/sec   •   '+(str(graphics) if graphics is not None else 'unavailable')+' graphics callbacks/sec')
        else:self.performance_summary.config(text='No saved check for the selected model yet.\nSelect a supported Samsung TV and run Test TV compatibility.')
        for row in reversed(rows):
            self.history_table.insert('','end',values=(row.get('time',''),row.get('model','Unknown'),row.get('cpu_iterations',''),row.get('graphics_callbacks','')))
    def find_tvs(self):
        if self.busy:return
        cli=self.cli.get().strip()
        self.busy=True;self.install.config(state='disabled');self.benchmark_button.config(state='disabled');self.scan_button.config(state='disabled');self.say('Looking for TVs on your network…')
        threading.Thread(target=self.scan,args=(cli,),daemon=True).start()
    def scan(self,cli):
        samsung=[];other=[]
        try:
            try:other=discover_other_tvs()
            except OSError:self.say('Network TV discovery is unavailable.')
            try:
                cli=resolve_cli(cli,self.tool_dir,progress=self.say);self.events.put(('cli_ready',str(cli)))
                flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
                p=subprocess.run([str(cli),'scan','--json'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30,creationflags=flags)
                if p.returncode:raise ValueError('Samsung discovery failed.')
                samsung=parse_discovery(json.loads(p.stdout))
            except (ValueError,OSError,subprocess.TimeoutExpired):self.say('Samsung-specific discovery failed. You can enter a Samsung TV IP manually.')
            devices=merge_devices(samsung,other)
            from android_core import discover_android
            for android in discover_android():
                devices=[d for d in devices if d['ip']!=android['ip']]+[android]
            self.events.put(('tvs',devices))
        finally:self.events.put(('done',True))
    def ensure_supported(self,ip):
        for device in self.found:
            if device['ip']==ip and not device.get('supported',True):raise ValueError(device['brand']+' was found, but installing or testing it is not supported yet.')
    def say(self,s):self.events.put(('log',s))
    def start(self):
        if self.busy:return
        try:
            ip=validate_tv_ip(self.ip.get());self.ensure_supported(ip);archive=Path(self.archive.get()).resolve();cli=self.cli.get().strip()
            if not archive.is_file():raise ValueError('Choose your local game file.')
            if cli and (not Path(cli).is_file() or Path(cli).name.lower()!='apps2samsung-cli.exe'):raise ValueError('Choose apps2samsung-cli.exe or leave the field blank.')
        except (ValueError,OSError) as e:messagebox.showerror('Cannot start',str(e));return
        self.busy=True;self.install.config(state='disabled');self.benchmark_button.config(state='disabled');self.scan_button.config(state='disabled');threading.Thread(target=self.run,args=(ip,archive,cli),daemon=True).start()
    def start_benchmark(self):
        if self.busy:return
        try:ip=validate_tv_ip(self.ip.get());self.ensure_supported(ip)
        except ValueError as e:messagebox.showerror('Cannot start',str(e));return
        self.busy=True;self.install.config(state='disabled');self.benchmark_button.config(state='disabled');self.scan_button.config(state='disabled')
        threading.Thread(target=self.run_benchmark,args=(ip,self.cli.get().strip()),daemon=True).start()
    def run_benchmark(self,ip,cli):
        installed=False;app=None;cli_path=None;success=False
        try:
            cli_path=resolve_cli(cli,self.tool_dir,progress=self.say)
            node=prepare_tool('node',self.tool_dir,progress=self.say)
            sdb=prepare_tool('sdb',self.tool_dir,progress=self.say)
            with tempfile.TemporaryDirectory(prefix='kart64-benchmark-') as tmp:
                package='KB'+secrets.token_hex(4).upper();app=package+'.Check'
                url='http://'+ip+':8001/api/v2/applications/'+app
                try:
                    with urllib.request.urlopen(url,timeout=5):raise ValueError('Benchmark ID already exists; retry the check.')
                except urllib.error.HTTPError as e:
                    if e.code!=404:raise ValueError('Could not verify benchmark installation state.') from e
                wgt=Path(tmp)/'TVCheck.wgt';make_benchmark(ROOT/'benchmark',wgt,package)
                self.say('Installing a temporary TV compatibility check…')
                self.command([str(cli_path),'install',str(wgt),'--tv',ip]);installed=True
                flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
                def sdb_run(args):
                    p=subprocess.run([str(sdb)]+args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30,creationflags=flags)
                    if p.returncode:raise ValueError('Could not connect the TV debugger.')
                    return p.stdout+p.stderr
                sdb_run(['connect',ip]);serial=ip+':26101'
                result=sdb_run(['-s',serial,'shell','0','debug',app]);remote_port=parse_debug_port(result)
                with socket.socket() as sock:
                    sock.bind(('127.0.0.1',0));local_port=sock.getsockname()[1]
                sdb_run(['-s',serial,'forward','tcp:'+str(local_port),'tcp:'+str(remote_port)])
                self.say('Running the graphics and capability check on the TV…')
                p=subprocess.run([str(node),str(ROOT/'src'/'collect-benchmark.cjs'),str(local_port)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=75,creationflags=flags)
                if p.returncode:raise ValueError('The TV benchmark did not return a result.')
                result=json.loads(p.stdout);self.say(format_benchmark(result))
                device=next((d for d in self.found if d['ip']==ip),{'brand':'Samsung','model':'Unknown model'})
                try:save_result(self.history_path,device,result);self.events.put(('history',True));self.say('Saved this check locally in the Performance tab.')
                except OSError:self.say('Could not save this result locally; the check still completed.')
                success=True
        except Exception as e:self.say('Compatibility check stopped: '+str(e))
        finally:
            if installed and cli_path and app:
                try:
                    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
                    result=subprocess.run([str(cli_path),'uninstall',app,'--tv',ip],capture_output=True,text=True,timeout=60,creationflags=flags)
                    if result.returncode:self.say('Could not remove the temporary TV check; remove Kart64 TV Check from TV Apps if it remains.')
                    else:self.say('Temporary TV check removed.')
                except (OSError,subprocess.TimeoutExpired):self.say('Could not remove the temporary TV check; remove Kart64 TV Check from TV Apps if it remains.')
            self.events.put(('done',success))
    def run(self,ip,archive,cli):
        try:
            self.say('Checking your game file…');kind=identify_game(archive)
            cli=resolve_cli(cli,self.tool_dir,progress=self.say)
            node=prepare_tool('node',self.tool_dir,progress=self.say)
            with tempfile.TemporaryDirectory(prefix='kart64-private-') as tmp:
                tmp=Path(tmp)
                if kind=='rom':archive=prepare_rom(archive,tmp,self.say)
                stage=tmp/'stage';stage.mkdir()
                self.say('Downloading and checking the supported runtime…')
                self.command([node,str(ROOT/'src'/'build-runtime.cjs'),str(stage)])
                self.say('Packaging your game data locally…')
                package=make_package(stage,archive,tmp/'Kart64TV.wgt')
                self.say('Signing and installing. If Samsung opens a sign-in window, finish signing in there.')
                self.command([str(cli),'install',str(package),'--tv',ip])
                self.say('Installer reported success. Find Kart64 TV in the TV Apps list.');self.events.put(('done',True))
        except Exception as e:self.say('Installation stopped: '+str(e));self.events.put(('done',False))
    def command(self,args,timeout=600):
        flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        p=subprocess.Popen(args,cwd=str(ROOT),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',creationflags=flags)
        def read_output():
            try:
                for line in p.stdout:
                    line=line.strip()
                    if not line:continue
                    if 'http://' in line or 'https://' in line:line='A sign-in link was provided; use the browser window opened by Samsung.'
                    self.say(line)
            finally:p.stdout.close()
        reader=threading.Thread(target=read_output,daemon=True);reader.start()
        try:code=p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.terminate()
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:p.kill();p.wait(timeout=10)
            reader.join(timeout=5)
            raise RuntimeError('Setup step timed out.')
        reader.join(timeout=5)
        if code:raise RuntimeError('A setup step failed (exit '+str(code)+'). Check the messages above.')
    def poll(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind=='log':self.log.config(state='normal');self.log.insert('end',value+'\n');self.log.see('end');self.log.config(state='disabled')
                elif kind=='cli_ready':self.cli.set(value)
                elif kind=='tvs':
                    self.found=value;self.tv_choice['values']=[v.get('brand','Samsung')+' — '+(v['name'] or 'TV')+' — '+(v['model'] or 'unknown model')+' ('+v['ip']+')'+(' — not supported yet' if not v.get('supported',True) else '') for v in value]
                    self.refresh_selection()
                    self.tv_table.delete(*self.tv_table.get_children())
                    for i,v in enumerate(value):self.tv_table.insert('','end',iid=str(i),values=(v.get('brand','Samsung'),v.get('model') or v.get('name') or 'Unknown', 'Samsung experimental' if v.get('supported',True) else 'Not supported yet'))
                    if len(value)==1:self.tv_choice.current(0);self.select_tv();self.say('Found one TV.')
                    elif len(value)>1:self.ip.set('');self.tv_choice.set('Choose a TV');self.say('Found '+str(len(value))+' TVs; choose one from the list.')
                    else:self.tv_choice.set('');self.say('No TVs found. You can enter a Samsung TV IP manually.')
                elif kind=='done':self.busy=False;self.install.config(state='normal');self.benchmark_button.config(state='normal');self.scan_button.config(state='normal')
                elif kind=='history':self.refresh_history()
        except queue.Empty:pass
        self.root.after(100,self.poll)

def main():
    root=tk.Tk();Installer(root);root.mainloop()
if __name__=='__main__':
    if sys.argv[1:]==['--self-test']:
        required=('build-runtime.cjs','runtime.cjs','runtime-pins.json','web-patch.cjs','diagnostics.js','collect-benchmark.cjs')
        sys.exit(0 if all((ROOT/'src'/name).is_file() for name in required) and all((ROOT/'benchmark'/name).is_file() for name in ('index.html','run.js','benchmark.js')) else 1)
    main()
