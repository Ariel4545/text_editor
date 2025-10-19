import sys
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, font, filedialog
from typing import Optional, Any, Dict, Callable

def show_library_installer(
	parent: Optional[tk.Misc] = None,
	base_libraries: Optional[list[str]] = None,
	optional_libraries: Optional[list[str]] = None,
	allow_upgrade_pip: bool = True,
	allow_optional: bool = True,
	title: Optional[str] = None,
	management_mode: bool = False,
	alias_map: Optional[dict[str, str]] = None,
	blocklist: Optional[set[str]] = None,
	pins: Optional[dict[str, str]] = None,
	skip_installed: bool = True,
	restart_script: Optional[str] = 'EgonTE.py',
	restart_args: Optional[list[str]] = None,
	builders: Optional[Any] = None,
	app: Optional[Any] = None,
	ui_text: Optional[Dict[str, str]] = None,
) -> dict:
	'''
	Functional library installer. Creates the window on the main thread (or a hidden root if needed),
	blocks until it is closed, and returns result_data.
	Addresses RuntimeError ("main thread is not in main loop") by:
	  - never calling .mainloop() from a background thread
	  - creating a temporary hidden Tk root when no parent/root exists
	  - using after() for all UI updates from worker threads
	'''
	# ---- static texts ----
	default_text = {
		'title': 'ETE - Install Required',
		'header': 'It seems that some required libraries are not installed',
		'header_management': 'Library Management',
		'options_frame': 'Additional Options',
		'install_optional': 'Install optional libraries',
		'upgrade_pip': 'Upgrade pip',
		'force_reinstall': 'Force re-install selected packages',
		'check_for_updates': 'Check for Updates',
		'base_libraries_label': 'Required Libraries',
		'optional_libraries_label': 'Optional Libraries',
		'status_installed_label': 'installed',
		'status_not_found_label': 'not found',
		'status_update_available': 'update available',
		'status_loading': 'Loading package information...',
		'install_button': 'Install',
		'cancel_button': 'Cancel',
		'close_button': 'Close',
		'restart_button': 'Restart program',
		'status_checking_pip': 'Checking pip availability...',
		'status_pip_unavailable': 'pip is not available in this interpreter.',
		'status_no_packages': 'Nothing to install.',
		'status_upgrading_pip': 'Upgrading pip...',
		'status_upgrade_failed': 'Failed to upgrade pip',
		'status_installing': 'Installing {package_name} ({index}/{total})...',
		'status_installed': '✔ Installed {package_name}',
		'status_already_installed': '✔ Already installed: {package_name}',
		'status_failed': '✖ Failed to install {package_name}.',
		'status_pip_error_details': 'Details: {details}',
		'status_cancelled': 'Cancelled (installed {installed}/{attempted}, failed {failed}).',
		'status_complete': '✔ Completed. Installed {installed} packages.',
		'status_complete_failures': '✖ Completed with {failed} failures (installed {installed}/{attempted}).',
		'status_error': '✖ Installer encountered an unexpected error.',
		'status_cancelling': 'Cancelling...',
		'status_checking_updates': 'Checking for updates...',
		'status_no_updates': 'All packages are up-to-date.',
		'status_updates_found': 'Found {count} updates. You can now select and install them.',
		'filter_placeholder': 'Filter packages...',
		'select_all': 'Select all',
		'select_none': 'Select none',
		# Improvements
		'env_label': 'Environment',
		'refresh': 'Refresh',
		'problems': 'Problems',
		'problems_hint': 'Installer diagnostics and common fixes will appear here.',
		'context_install_exact': 'Install exact...',
		'context_pin_version': 'Pin version',
		'context_open_pypi': 'Open on PyPI',
		'context_copy_cmd': 'Copy install command',
		'export_reqs': 'Export requirements...',
		'import_reqs': 'Import requirements...',
	}
	ui_text = {**default_text, **(ui_text or {})}
	if title:
		ui_text['title'] = title

	# ---- normalize inputs ----
	base_libraries = list(base_libraries or [])
	optional_libraries = list(optional_libraries or [])
	alias_map = {k.lower(): v for k, v in (alias_map or {}).items()}
	blocklist = {n.lower() for n in (blocklist or set())}
	pins = {k.lower(): v for k, v in (pins or {}).items()}
	restart_args = list(restart_args or [])
	python_default = sys.executable

	# ---- installer state (captured by nested functions) ----
	result_data = {'installed': 0, 'failed': 0, 'attempted': 0, 'upgraded_pip': False,
				   'extras_selected': False, 'cancelled': False, 'packages': []}
	window_root = None
	owns_mainloop = False
	use_builders = False

	installed_packages: Dict[str, str] = {}
	cached_lists: Dict[str, Any] = {}
	envs: list[tuple[str, str]] = []

	# Tk variables and UI refs
	active_env = None
	filter_var = None
	force_reinstall = None
	upgrade_pip_var = None

	env_combo = None
	problems_area = None
	log_area = None
	progress_bar = None
	list_container = None
	install_button = None
	cancel_button = None
	close_button = None
	check_updates_button = None

	package_vars: Dict[str, tk.BooleanVar] = {}
	package_widgets: Dict[str, Dict[str, Any]] = {}
	all_checkbuttons: list[tuple[str, ttk.Checkbutton]] = []

	# ---- thread safety helpers ----
	def on_main_thread() -> bool:
		# Tk isn't thread-safe; compare with the thread where root was created
		return threading.current_thread() == threading.main_thread()

	def ui_call(cb: Callable, *args, **kwargs):
		try:
			if window_root and window_root.winfo_exists():
				window_root.after(0, cb, *args, **kwargs)
		except tk.TclError:
			pass

	# ---- utils ----
	def normalize_packages(pkgs: list[str]) -> list[str]:
		seen = set()
		out = []
		for raw in pkgs:
			cand = (raw or '').strip()
			if not cand:
				continue
			lower_key = cand.lower()
			if lower_key in blocklist:
				continue
			canon = alias_map.get(lower_key, cand)
			base = canon.lower().split('==')[0].split('>=')[0].split('<=')[0].strip()
			final = pins.get(base, canon)
			if final.lower() not in seen:
				seen.add(final.lower())
				out.append(final)
		return out

	base_libraries = normalize_packages(base_libraries)
	optional_libraries = normalize_packages(optional_libraries)

	def run_command(cmd: list[str]) -> dict:
		try:
			proc = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
			return {'success': True, 'output': proc.stdout}
		except (subprocess.CalledProcessError, OSError) as e:
			out = e.stderr if getattr(e, 'stderr', '') else ''
			if getattr(e, 'stdout', ''):
				out += '\n' + e.stdout
			if not out:
				out = str(e)
			return {'success': False, 'output': out.strip()}

	def active_python() -> str:
		val = (active_env.get() or python_default).strip()
		return val or python_default

	def problems_log(text: str):
		def append():
			try:
				problems_area.configure(state='normal')
				problems_area.insert('end', text.strip() + '\n')
				problems_area.configure(state='disabled')
				problems_area.yview('end')
			except tk.TclError:
				pass
		ui_call(append)

	def problems_from_output(output: str):
		out = (output or '').lower()
		hints = []
		if 'failed building wheel' in out or 'bdist_wheel' in out:
			hints.append('Hint: build tools may be missing (e.g., Visual C++ Build Tools on Windows).')
		if 'gcc' in out or 'cl.exe' in out or 'build error' in out:
			hints.append('Hint: a C/C++ compiler might be required for this package.')
		if 'permission denied' in out or 'permissionerror' in out:
			hints.append('Hint: try running in a writable environment or add --user.')
		if 'ssl' in out:
			hints.append('Hint: SSL issue; ensure certificates are installed and time is correct.')
		if 'not found' in out and 'pip' in out:
			hints.append('Hint: pip not found in selected interpreter.')
		if 'requires python' in out:
			hints.append('Hint: package may not support this Python version.')
		if hints:
			problems_log('\n'.join(hints))
		else:
			if output:
				problems_log(output.strip()[:2000])

	def log_message(key: str, level: str = 'info', **kwargs):
		def append():
			try:
				msg = ui_text.get(key, key)
				try:
					msg = msg.format(**kwargs)
				except Exception:
					pass
				log_area.configure(state='normal')
				log_area.insert('end', msg + '\n', level)
				log_area.configure(state='disabled')
				log_area.yview('end')
			except tk.TclError:
				pass
		ui_call(append)

	def set_progress(maximum: Optional[int] = None, value: Optional[int] = None):
		def apply():
			try:
				if maximum is not None:
					progress_bar.configure(maximum=maximum)
				if value is not None:
					progress_bar.configure(value=value)
			except tk.TclError:
				pass
		ui_call(apply)

	def set_buttons(install: bool, cancel: bool, close: bool, updates: bool = True):
		def apply():
			try:
				install_button.state(['!disabled'] if install else ['disabled'])
				cancel_button.state(['!disabled'] if cancel else ['disabled'])
				close_button.state(['!disabled'] if close else ['disabled'])
				if management_mode and check_updates_button:
					check_updates_button.state(['!disabled'] if updates else ['disabled'])
				for w in package_widgets.values():
					chk = w['check']
					if chk.instate(['!disabled']):
						chk.state(['!disabled'] if install else ['disabled'])
			except tk.TclError:
				pass
		ui_call(apply)

	def which(name: str) -> Optional[str]:
		try:
			from shutil import which as _which
			return _which(name)
		except Exception:
			return None

	# ---- environment discovery ----
	def discover_envs() -> list[tuple[str, str]]:
		found = []
		seen = set()
		def add_env(label, exe):
			if exe and exe not in seen and os.path.isfile(exe):
				seen.add(exe); found.append((label, exe))
		add_env('current', python_default)
		for name in ('python', 'python3', 'py'):
			exe = which(name)
			if exe:
				add_env(name, exe)
		if os.name == 'nt':
			for tag in ('-3', '-3.11', '-3.10', '-3.9'):
				r = run_command(['py', tag, '-c', 'import sys;print(sys.executable)'])
				if r['success']:
					exe = (r['output'] or '').strip().splitlines()[-1].strip()
					add_env(f'py {tag}', exe)
		return found

	def populate_envs(values: list[tuple[str, str]]):
		_envs = [exe for _, exe in values]
		if python_default not in _envs:
			_envs.insert(0, python_default)
		env_combo['values'] = _envs
		active_env.set(python_default)

	# ---- list loading ----
	def async_load_packages():
		set_buttons(False, False, False, False)
		threading.Thread(target=load_packages_worker, daemon=True).start()

	def load_packages_worker(refresh_ui=True):
		key = f'pip_list@{active_python()}'
		if key in cached_lists:
			installed_packages.clear()
			installed_packages.update(cached_lists[key])
		else:
			r = run_command([active_python(), '-m', 'pip', 'list'])
			if r['success']:
				installed_packages.clear()
				lines = r['output'].splitlines()
				if len(lines) > 2:
					for line in lines[2:]:
						parts = line.split()
						if len(parts) >= 2:
							installed_packages[parts[0].lower()] = parts[1]
				cached_lists[key] = dict(installed_packages)
			else:
				problems_from_output(r['output'])
		if refresh_ui:
			ui_call(finish_ui_population)

	def finish_ui_population():
		for w in list_container.winfo_children():
			w.destroy()
		package_vars.clear()
		package_widgets.clear()
		all_checkbuttons.clear()
		populate_library_list(list_container)
		set_buttons(True, False, True, management_mode)
		apply_filter()

	def populate_library_list(parent: ttk.Frame):
		canvas = tk.Canvas(parent, highlightthickness=0)
		scrollbar = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
		scrollable = ttk.Frame(canvas)
		scrollable.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
		canvas.create_window((0, 0), window=scrollable, anchor='nw')
		canvas.configure(yscrollcommand=scrollbar.set)
		canvas.pack(side='left', fill='both', expand=True)
		scrollbar.pack(side='right', fill='y')

		def add_group(lbl: str, libs: list[str], required: bool):
			if not libs:
				return
			group = ttk.LabelFrame(scrollable, text=lbl, padding=8)
			group.pack(fill='x', expand=True, padx=2, pady=(0, 6))
			for lib in libs:
				add_library_row(group, lib, required)

		add_group(ui_text['base_libraries_label'], base_libraries, True)
		if allow_optional:
			add_group(ui_text['optional_libraries_label'], optional_libraries, False)

	def add_library_row(parent: ttk.Frame, lib_name: str, required: bool):
		base = lib_name.split('==')[0].split('>=')[0].split('<=')[0].strip().lower()
		version = installed_packages.get(base)
		is_installed = version is not None

		var = tk.BooleanVar()
		package_vars[lib_name] = var

		row = ttk.Frame(parent); row.pack(fill='x', expand=True, pady=2)
		chk = ttk.Checkbutton(row, text=lib_name, variable=var); chk.pack(side='left', padx=(6, 0))
		status_text = f'(v{version})' if version else f"({ui_text['status_not_found_label']})"
		status_color = '#008000' if is_installed else '#FF0000'
		stat = ttk.Label(row, text=status_text, foreground=status_color); stat.pack(side='left', padx=6)

		menu = tk.Menu(row, tearoff=False)
		menu.add_command(label=ui_text['context_install_exact'], command=lambda n=base: install_exact_prompt(n))
		menu.add_command(label=ui_text['context_pin_version'], command=lambda n=base: pin_version_prompt(n))
		menu.add_separator()
		menu.add_command(label=ui_text['context_open_pypi'], command=lambda n=base: open_pypi(n))
		menu.add_command(label=ui_text['context_copy_cmd'], command=lambda n=lib_name: copy_cmd(n))

		def popup(e, m=menu):
			try:
				m.tk_popup(e.x_root, e.y_root)
			finally:
				m.grab_release()

		row.bind('<Button-3>', popup); chk.bind('<Button-3>', popup); stat.bind('<Button-3>', popup)
		package_widgets[lib_name] = {'check': chk, 'status': stat, 'frame': row}
		all_checkbuttons.append((lib_name, chk))

		if required and not management_mode and not is_installed:
			var.set(True); chk.state(['disabled'])

	def apply_filter(_e=None):
		query = (filter_var.get() or '').strip().lower()
		placeholder = ui_text['filter_placeholder'].lower()
		if query == placeholder:
			query = ''
		for name, widgets in package_widgets.items():
			row = widgets['frame']
			visible = True if not query else (query in name.lower())
			if visible:
				row.pack(fill='x', expand=True, pady=2)
			else:
				row.pack_forget()

	def select_all(mark: bool):
		for name, chk in all_checkbuttons:
			if not chk.instate(['disabled']):
				package_vars.get(name, tk.BooleanVar()).set(bool(mark))

	# ---- per-package actions ----
	def open_pypi(name: str):
		try:
			import webbrowser
			webbrowser.open_new_tab(f'https://pypi.org/project/{name}/')
		except Exception:
			problems_log(f'Could not open PyPI for {name}')

	def copy_cmd(spec: str):
		try:
			window_root.clipboard_clear()
			window_root.clipboard_append(f'{active_python()} -m pip install --upgrade {spec}')
		except Exception:
			pass

	def install_exact_prompt(base_name: str):
		top = tk.Toplevel(window_root); top.title(ui_text['context_install_exact']); top.resizable(False, False)
		ttk.Label(top, text=f'{base_name}==').grid(row=0, column=0, padx=6, pady=6)
		v = tk.StringVar()
		e = ttk.Entry(top, textvariable=v, width=16); e.grid(row=0, column=1, padx=6, pady=6); e.focus_set()
		def go():
			ver = v.get().strip()
			if ver:
				install_now(f'{base_name}=={ver}')
			top.destroy()
		ttk.Button(top, text='OK', command=go).grid(row=0, column=2, padx=6, pady=6)

	def pin_version_prompt(base_name: str):
		installed_ver = installed_packages.get(base_name.lower())
		def set_pin(ver: str):
			if ver:
				pins[base_name.lower()] = f'{base_name}=={ver}'
				log_message('info', 'info', details=f'pinned {base_name}=={ver}')
		if installed_ver:
			set_pin(installed_ver)
		else:
			top = tk.Toplevel(window_root); top.title(ui_text['context_pin_version']); top.resizable(False, False)
			v = tk.StringVar()
			ttk.Label(top, text=f'{base_name}==').grid(row=0, column=0, padx=6, pady=6)
			e = ttk.Entry(top, textvariable=v, width=16); e.grid(row=0, column=1, padx=6, pady=6); e.focus_set()
			def go():
				set_pin(v.get().strip()); top.destroy()
			ttk.Button(top, text='OK', command=go).grid(row=0, column=2, padx=6, pady=6)

	def install_now(spec: str):
		def worker():
			set_buttons(False, False, False, False)
			res = run_command([active_python(), '-m', 'pip', 'install', spec])
			if res['success']:
				log_message('status_installed', 'success', package_name=spec)
				refresh_lists()
			else:
				log_message('status_failed', 'error', package_name=spec)
				log_message('status_pip_error_details', 'error', details=res['output'])
				problems_from_output(res['output'])
			set_buttons(True, False, True, True)
		threading.Thread(target=worker, daemon=True).start()

	# ---- actions ----
	def refresh_lists():
		async_load_packages()

	def _check_for_updates_worker():
		set_buttons(False, True, False, False)
		log_message('status_checking_updates', 'warning')
		key = f'pip_outdated@{active_python()}'
		if key in cached_lists:
			output = cached_lists[key]
		else:
			r = run_command([active_python(), '-m', 'pip', 'list', '--outdated'])
			if not r['success']:
				log_message('status_error', 'error'); problems_from_output(r['output'])
				set_buttons(True, False, True, True); return
			output = r['output']; cached_lists[key] = output
		outdated = {}
		lines = output.splitlines()
		if len(lines) > 2:
			for line in lines[2:]:
				parts = line.split()
				if len(parts) >= 3:
					outdated[parts[0].lower()] = parts[2]
		if not outdated:
			log_message('status_no_updates', 'success'); set_buttons(True, False, True, True); return

		log_message('status_updates_found', 'success', count=len(outdated))
		def mark_updates():
			for lib, widgets in package_widgets.items():
				base = lib.split('==')[0].split('>=')[0].split('<=')[0].strip().lower()
				if base in outdated:
					new_ver = outdated[base]
					try:
						widgets['status'].configure(text=f"(v{installed_packages.get(base, '?')} -> {new_ver})",
													foreground='#FFA500')
						package_vars[lib].set(True)
					except tk.TclError:
						pass
		ui_call(mark_updates)
		set_buttons(True, False, True, True)

	def check_for_updates():
		threading.Thread(target=_check_for_updates_worker, daemon=True).start()

	def start_install():
		threading.Thread(target=install_worker, daemon=True).start()

	def install_worker():
		set_buttons(False, True, False, False)
		queue = [n for n, v in package_vars.items() if v.get()]
		result_data['extras_selected'] = any((n in optional_libraries) for n in queue)

		log_message('status_checking_pip', 'warning')
		pip_ok = run_command([active_python(), '-m', 'pip', '--version'])
		if not pip_ok['success']:
			log_message('status_pip_unavailable', 'error')
			set_buttons(True, False, True, True); return

		total = len(queue)
		if total == 0:
			log_message('status_no_packages', 'warning')
			set_buttons(True, False, True, True); return
		set_progress(maximum=total, value=0)

		if allow_upgrade_pip and upgrade_pip_var.get():
			log_message('status_upgrading_pip', 'warning')
			up_res = run_command([active_python(), '-m', 'pip', 'install', '--upgrade', 'pip'])
			result_data['upgraded_pip'] = up_res['success']
			if not up_res['success']:
				log_message('status_upgrade_failed', 'error')
				log_message('status_pip_error_details', 'error', details=up_res['output'])
				problems_from_output(up_res['output'])

		for i, spec in enumerate(queue, start=1):
			set_progress(value=i - 1)
			log_message('status_installing', 'warning', package_name=spec, index=i, total=total)

			base = spec.split('==')[0].split('>=')[0].split('<=')[0].strip().lower()
			is_inst = base in installed_packages
			skipped = False

			if skip_installed and is_inst and not force_reinstall.get():
				skipped = True
				ok = True
				log_message('status_already_installed', 'success', package_name=spec)
			else:
				cmd = [active_python(), '-m', 'pip', 'install', '--upgrade', spec]
				if force_reinstall.get():
					cmd.append('--force-reinstall')
				res = run_command(cmd)
				ok = res['success']
				if not ok:
					problems_from_output(res['output'])

			result_data['attempted'] += 1
			result_data['packages'].append({'name': spec, 'ok': ok, 'skipped': skipped})
			if ok:
				result_data['installed'] += 1
				if not skipped:
					log_message('status_installed', 'success', package_name=spec)
			else:
				result_data['failed'] += 1
				log_message('status_failed', 'error', package_name=spec)
				if not skipped:
					log_message('status_pip_error_details', 'error', details=res.get('output', ''))

			set_progress(value=i)

		if result_data['failed'] == 0:
			log_message('status_complete', 'success', **result_data)
		else:
			log_message('status_complete_failures', 'error', **result_data)

		load_packages_worker(refresh_ui=False)
		ui_call(prepare_restart_ui)

	def prepare_restart_ui():
		finish_ui_population()
		install_button.configure(text=ui_text['restart_button'], command=restart_program)
		set_buttons(True, False, True, True)

	def resolve_restart_command() -> list[str]:
		if not restart_script:
			return [active_python()] + sys.argv
		candidates = []
		try:
			launch_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
			candidates.append(os.path.join(launch_dir, restart_script))
		except Exception:
			pass
		try:
			module_dir = os.path.dirname(os.path.abspath(__file__))
			candidates.append(os.path.join(module_dir, restart_script))
		except Exception:
			pass
		for path in candidates:
			if os.path.isfile(path):
				return [active_python(), path, *restart_args]
		return [active_python()] + sys.argv

	def restart_program():
		cmd = resolve_restart_command()
		try:
			os.execv(cmd[0], cmd)
		except Exception:
			try:
				subprocess.Popen(cmd, close_fds=True)
			except Exception:
				pass
			try:
				window_root.destroy()
			except Exception:
				pass
			os._exit(0)

	def export_requirements():
		try:
			path = filedialog.asksaveasfilename(
				title='Export requirements.txt', defaultextension='.txt',
				filetypes=[('Text files', '*.txt'), ('All files', '*.*')]
			)
			if not path:
				return
			selected = [n for n, v in package_vars.items() if v.get()]
			lines = []
			for spec in selected:
				base = spec.split('==')[0].split('>=')[0].split('<=')[0].strip()
				lines.append(pins.get(base.lower(), spec))
			with open(path, 'w', encoding='utf-8') as f:
				f.write('\n'.join(lines) + '\n')
			problems_log(f'Exported {len(lines)} entries to {path}')
		except Exception as e:
			problems_log(f'Export failed: {e}')

	def import_requirements():
		try:
			path = filedialog.askopenfilename(
				title='Import requirements.txt',
				filetypes=[('Text files', '*.txt *.in *.req'), ('All files', '*.*')]
			)
			if not path:
				return
			with open(path, 'r', encoding='utf-8') as f:
				lines = [ln.strip() for ln in f if ln.strip() and not ln.lstrip().startswith('#')]
			known = set(package_vars.keys())
			added = 0
			for spec in lines:
				base = spec.split('==')[0].split('>=')[0].split('<=')[0].strip().lower()
				match = None
				for k in known:
					if k.split('==')[0].split('>=')[0].split('<=')[0].strip().lower() == base:
						match = k; break
				if match:
					package_vars[match].set(True); added += 1
				else:
					problems_log(f'Not in list: {spec}')
			problems_log(f'Imported {added} selections from {os.path.basename(path)}')
		except Exception as e:
			problems_log(f'Import failed: {e}')

	def on_close_request():
		try:
			window_root.destroy()
		except Exception:
			pass

	# ---- build window on main thread safely ----
	def _build_and_run():
		nonlocal window_root, owns_mainloop, use_builders, active_env, filter_var, force_reinstall, upgrade_pip_var
		nonlocal env_combo, problems_area, log_area, progress_bar, list_container, install_button, cancel_button, close_button, check_updates_button

		# choose/build root
		built = False
		if builders and app:
			try:
				from UI.ui_builders import UIBuilders  # optional
				if hasattr(builders, 'make_pop_ups_window'):
					window_root = builders.make_pop_ups_window(function=lambda: None,
						custom_title=(ui_text['title'] if not management_mode else ui_text['header_management']),
						parent=parent, modal=False, title=(ui_text['title'] if not management_mode else ui_text['header_management']))
					use_builders = True
					built = True
			except Exception:
				use_builders = False

		if not built:
			if parent is None:
				default_root = getattr(tk, '_default_root', None)
				if default_root is not None:
					window_root = tk.Toplevel(default_root); window_root.transient(default_root)
				else:
					window_root = tk.Tk(); owns_mainloop = True
			else:
				window_root = tk.Toplevel(parent); window_root.transient(parent)
				try:
					window_root.grab_set()
				except tk.TclError:
					pass
			window_root.title(ui_text['title'] if not management_mode else ui_text['header_management'])
			window_root.resizable(True, True); window_root.minsize(800, 600)

		# style
		try:
			sty = ttk.Style()
			if 'clam' in sty.theme_names():
				sty.theme_use('clam')
		except Exception:
			pass
		try:
			bold = font.nametofont('TkDefaultFont').copy(); bold.configure(weight='bold')
		except Exception:
			bold = ('TkDefaultFont', 10, 'bold')

		# layout
		main = ttk.Frame(window_root, padding=12); main.grid(row=0, column=0, sticky='nsew')
		window_root.grid_rowconfigure(0, weight=1); window_root.grid_columnconfigure(0, weight=1)
		main.grid_rowconfigure(4, weight=1); main.grid_columnconfigure(0, weight=1)

		tt = ttk.Label(main, text=(ui_text['header'] if not management_mode else ui_text['header_management']), font=bold)
		tt.grid(row=0, column=0, sticky='w', pady=(0, 8))

		# top bar
		top = ttk.Frame(main); top.grid(row=1, column=0, sticky='ew', pady=(0, 6))
		for i in range(6): top.grid_columnconfigure(i, weight=0)
		top.grid_columnconfigure(2, weight=1)
		tt_env = ttk.Label(top, text=f"{ui_text['env_label']}:")
		active_env = tk.StringVar(value=python_default)
		env_combo = ttk.Combobox(top, state='readonly', textvariable=active_env, width=45, values=[python_default])
		refresh_btn = ttk.Button(top, text=ui_text['refresh'], command=refresh_lists)
		export_btn = ttk.Button(top, text=ui_text['export_reqs'], command=export_requirements)
		import_btn = ttk.Button(top, text=ui_text['import_reqs'], command=import_requirements)
		tt_env.grid(row=0, column=0, padx=(0, 6)); env_combo.grid(row=0, column=1, sticky='w')
		refresh_btn.grid(row=0, column=3, padx=(6, 0)); export_btn.grid(row=0, column=4, padx=(6, 0)); import_btn.grid(row=0, column=5, padx=(6, 0))
		env_combo.bind('<<ComboboxSelected>>', lambda _e: (cached_lists.clear(), installed_packages.clear(), refresh_lists()))

		# filter
		filter_bar = ttk.Frame(main); filter_bar.grid(row=2, column=0, sticky='ew', pady=(0, 6))
		filter_bar.grid_columnconfigure(0, weight=1)
		filter_var = tk.StringVar(value='')
		filter_entry = ttk.Entry(filter_bar, textvariable=filter_var)
		filter_entry.insert(0, ui_text['filter_placeholder'])
		def _f_in(_e):
			if filter_entry.get() == ui_text['filter_placeholder']: filter_entry.delete(0, 'end')
		def _f_out(_e):
			if not filter_entry.get().strip(): filter_entry.insert(0, ui_text['filter_placeholder'])
		filter_entry.bind('<FocusIn>', _f_in); filter_entry.bind('<FocusOut>', _f_out)
		filter_entry.bind('<KeyRelease>', apply_filter)
		filter_entry.grid(row=0, column=0, sticky='ew', padx=(0, 8))
		ttk.Button(filter_bar, text=ui_text['select_all'], command=lambda: select_all(True)).grid(row=0, column=1, padx=(0, 4))
		ttk.Button(filter_bar, text=ui_text['select_none'], command=lambda: select_all(False)).grid(row=0, column=2)

		# split
		paned = ttk.PanedWindow(main, orient=tk.VERTICAL); paned.grid(row=3, column=0, sticky='nsew', pady=(0, 8))
		list_container_local = ttk.Frame(paned, padding=0)
		ld = ttk.Label(list_container_local, text=ui_text['status_loading']); ld.pack(pady=20)
		paned.add(list_container_local, weight=3)

		problems_frame = ttk.LabelFrame(paned, text=ui_text['problems'], padding=8)
		problems_inner = ttk.Frame(problems_frame); problems_inner.pack(fill='both', expand=True)
		problems_area_local = tk.Text(problems_inner, wrap='word', height=6, state='disabled', font=('Segoe UI', 9), relief='solid', borderwidth=1)
		p_scroll = ttk.Scrollbar(problems_inner, orient='vertical', command=problems_area_local.yview)
		problems_area_local.configure(yscrollcommand=p_scroll.set)
		problems_area_local.pack(side='left', fill='both', expand=True); p_scroll.pack(side='right', fill='y')
		paned.add(problems_frame, weight=1)

		# log and controls
		log_frame_local = ttk.Frame(main, padding=0); log_frame_local.grid(row=4, column=0, sticky='nsew')
		log_area_local = tk.Text(log_frame_local, wrap='word', height=5, state='disabled', font=('Segoe UI', 9), relief='solid', borderwidth=1)
		l_scroll = ttk.Scrollbar(log_frame_local, orient='vertical', command=log_area_local.yview)
		log_area_local.configure(yscrollcommand=l_scroll.set)
		log_area_local.pack(side='left', fill='both', expand=True); l_scroll.pack(side='right', fill='y')
		log_area_local.tag_config('success', foreground='#008000')
		log_area_local.tag_config('error', foreground='#FF0000')
		log_area_local.tag_config('warning', foreground='#FFA500')
		log_area_local.tag_config('info')

		ctrls = ttk.Frame(main); ctrls.grid(row=5, column=0, sticky='ew'); ctrls.grid_columnconfigure(0, weight=1)
		opts = ttk.LabelFrame(ctrls, text=ui_text['options_frame'], padding=8); opts.grid(row=0, column=0, sticky='w')
		force_reinstall_local = tk.BooleanVar(value=False)
		upgrade_pip_local = tk.BooleanVar(value=False)
		if management_mode:
			ttk.Checkbutton(opts, text=ui_text['force_reinstall'], variable=force_reinstall_local).pack(side='left', padx=(0, 10))
		if allow_upgrade_pip:
			ttk.Checkbutton(opts, text=ui_text['upgrade_pip'], variable=upgrade_pip_local).pack(side='left')

		btns = ttk.Frame(ctrls); btns.grid(row=0, column=1, sticky='e')
		if management_mode:
			check_updates_button_local = ttk.Button(btns, text=ui_text['check_for_updates'], command=check_for_updates)
			check_updates_button_local.pack(side='left', padx=(0, 8))
		install_button_local = ttk.Button(btns, text=ui_text['install_button'], command=start_install); install_button_local.pack(side='left', padx=(0, 8))
		cancel_button_local = ttk.Button(btns, text=ui_text['cancel_button'], command=lambda: None); cancel_button_local.pack(side='left')
		close_button_local = ttk.Button(btns, text=ui_text['close_button'], command=on_close_request); close_button_local.pack(side='left', padx=(8, 0))

		progress_bar_local = ttk.Progressbar(main, mode='determinate'); progress_bar_local.grid(row=6, column=0, sticky='ew', pady=(8, 0))
		window_root.protocol('WM_DELETE_WINDOW', on_close_request)

		# capture refs into outer scope
		nonlocal list_container, problems_area, log_area, progress_bar, install_button, cancel_button, close_button, check_updates_button, filter_var, force_reinstall, upgrade_pip_var
		list_container = list_container_local
		problems_area = problems_area_local
		log_area = log_area_local
		progress_bar = progress_bar_local
		install_button = install_button_local
		cancel_button = cancel_button_local
		close_button = close_button_local
		check_updates_button = check_updates_button_local if management_mode else None
		filter_var = filter_var
		force_reinstall = force_reinstall_local
		upgrade_pip_var = upgrade_pip_local

		# populate envs and load
		def env_worker():
			vals = discover_envs()
			if vals:
				ui_call(lambda: populate_envs(vals))
		threading.Thread(target=env_worker, daemon=True).start()
		async_load_packages()

		# Center relative to parent
		try:
			window_root.update_idletasks()
			if parent:
				x = parent.winfo_rootx() + (parent.winfo_width() - window_root.winfo_width()) // 2
				y = parent.winfo_rooty() + (parent.winfo_height() - window_root.winfo_height()) // 3
				window_root.geometry(f'+{x}+{y}')
		except tk.TclError:
			pass

		# block without risking RuntimeError
		if owns_mainloop:
			window_root.mainloop()
		else:
			window_root.wait_window()

	# Ensure we create the UI on main thread to avoid RuntimeError
	if on_main_thread():
		# use an existing parent or create a temp hidden root
		if parent is None and getattr(tk, '_default_root', None) is None:
			temp_root = tk.Tk()
			temp_root.withdraw()
			parent = temp_root
			try:
				_build_and_run()
			finally:
				try:
					if temp_root and temp_root.winfo_exists():
						temp_root.destroy()
				except Exception:
					pass
		else:
			_build_and_run()
	else:
		# Marshal to main thread using an emergency hidden root
		temp_root = tk.Tk()
		temp_root.withdraw()
		def _start():
			nonlocal parent
			if parent is None:
				parent = temp_root
			_build_and_run()
			try:
				if temp_root and temp_root.winfo_exists():
					temp_root.destroy()
			except Exception:
				pass
		temp_root.after(0, _start)
		# run the loop synchronously on main thread context we just created
		temp_root.mainloop()

	return result_data
