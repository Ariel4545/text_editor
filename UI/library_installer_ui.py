# python
# library_installer_ui.py
import sys
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk
from typing import Optional


def show_library_installer(
    parent: Optional[tk.Misc] = None,
    base_libraries: Optional[list[str]] = None,
    optional_libraries: Optional[list[str]] = None,
    allow_upgrade_pip: bool = True,
    allow_optional: bool = True,
    title: str = 'ETE - Install Required',
    *,
    alias_map: Optional[dict[str, str]] = None,   # lowercased name -> canonical/pinned spec
    blocklist: Optional[set[str]] = None,         # lowercased names to skip
    pins: Optional[dict[str, str]] = None,        # lowercased canonical name -> pinned spec
    skip_installed: bool = True,                  # quick check to skip already-installed packages
    # New: control what to restart
    restart_script: Optional[str] = 'egon_droplets.py',
    restart_args: Optional[list[str]] = None,
) -> dict:
    '''
    Show a minimal installer UI to install Python packages with pip.

    Returns a dict:
      {
        'installed': int,
        'failed': int,
        'attempted': int,
        'upgraded_pip': bool,
        'extras_selected': bool,
        'cancelled': bool,
        'packages': list[{'name': str, 'ok': bool, 'skipped': bool}]
      }
    '''
    alias_map = {k.lower(): v for k, v in (alias_map or {}).items()}
    blocklist = {k.lower() for k in (blocklist or set())}
    pins = {k.lower(): v for k, v in (pins or {}).items()}

    def _normalize(items: Optional[list[str]]) -> list[str]:
        if not items:
            return []
        seen = set()
        out = []
        for s in items:
            name = (s or '').strip()
            if not name:
                continue
            key = name.lower()
            if key in blocklist:
                continue
            mapped = alias_map.get(key, name)
            mkey = mapped.lower()
            if '==' not in mapped and '>=' not in mapped and '<=' not in mapped and mkey in pins:
                mapped = pins[mkey]
            if mapped.lower() not in seen:
                seen.add(mapped.lower())
                out.append(mapped)
        return out

    base_libraries = _normalize(base_libraries)
    optional_libraries = _normalize(optional_libraries)

    result = {
        'installed': 0,
        'failed': 0,
        'attempted': 0,
        'upgraded_pip': False,
        'extras_selected': False,
        'cancelled': False,
        'packages': [],
    }

    own_root = False
    if parent is None:
        root = tk.Tk()
        own_root = True
    else:
        root = tk.Toplevel(parent)
        root.transient(parent)
        try:
            root.grab_set()
        except Exception:
            pass

    root.title(title)
    root.resizable(False, False)

    running_lock = threading.Lock()
    running_flag = {'value': False}

    frm = ttk.Frame(root, padding=10)
    frm.pack(fill='both', expand=True)

    ttk.Label(
        frm,
        text='It seems that some required libraries are not installed',
        font=('Segoe UI', 10, 'underline'),
    ).pack(anchor='w')

    lbl_status = ttk.Label(frm, text='', font=('Segoe UI', 9))
    lbl_status.pack(anchor='w', pady=(8, 4))

    # Options (hide optional checkbox if not useful)
    opt_frame = ttk.LabelFrame(frm, text='Additional Options')
    opt_frame.pack(fill='x', pady=(6, 10))

    opt_optional = tk.BooleanVar(value=False)
    opt_upgrade_pip = tk.BooleanVar(value=False)
    opt_widgets: list[ttk.Checkbutton] = []

    col = 0
    if allow_optional and optional_libraries:
        cb_opt = ttk.Checkbutton(opt_frame, text='Install optional libraries', variable=opt_optional)
        cb_opt.grid(row=0, column=col, sticky='w', padx=6, pady=4)
        opt_widgets.append(cb_opt)
        col += 1

    if allow_upgrade_pip:
        cb_up = ttk.Checkbutton(opt_frame, text='Upgrade pip', variable=opt_upgrade_pip)
        cb_up.grid(row=0, column=col, sticky='w', padx=6, pady=4)
        opt_widgets.append(cb_up)
        col += 1

    # Buttons
    btns = ttk.Frame(frm)
    btns.pack(fill='x')
    btn_install = ttk.Button(btns, text='Install')
    btn_install.pack(side='left')
    btn_cancel = ttk.Button(btns, text='Cancel')
    btn_cancel.pack(side='left', padx=(8, 0))
    btn_close = ttk.Button(btns, text='Close', command=root.destroy)
    btn_close.pack(side='right')

    btn_cancel.state(['disabled'])

    progress = ttk.Progressbar(frm, mode='determinate')
    progress.pack(fill='x', pady=(8, 0))

    exe = sys.executable
    stop_event = threading.Event()

    # Thread-safe UI helpers
    def _window_alive() -> bool:
        try:
            return bool(root and root.winfo_exists())
        except Exception:
            return False

    def _ui(fn, *args, **kwargs):
        if _window_alive():
            try:
                root.after(0, fn, *args, **kwargs)
            except Exception:
                pass

    def _set_status(text: str, color: str = ''):
        _ui(lbl_status.configure, text=text, foreground=color or '')

    def _set_progress(maximum: Optional[int] = None, value: Optional[int] = None):
        def _apply():
            try:
                if maximum is not None:
                    progress.configure(maximum=maximum)
                if value is not None:
                    progress.configure(value=value)
            except Exception:
                pass
        _ui(_apply)

    def _set_buttons(install_enabled: bool, cancel_enabled: bool, close_enabled: bool):
        def _apply():
            try:
                btn_install.state(['!disabled'] if install_enabled else ['disabled'])
                btn_cancel.state(['!disabled'] if cancel_enabled else ['disabled'])
                btn_close.state(['!disabled'] if close_enabled else ['disabled'])
                # Lock/unlock the option checkboxes too
                for w in opt_widgets:
                    w.state(['!disabled'] if install_enabled else ['disabled'])
            except Exception:
                pass
        _ui(_apply)

    def _safe_check_call(cmd: list[str]) -> bool:
        try:
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            return True
        except Exception:
            return False

    def _safe_check(cmd: list[str]) -> bool:
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            return True
        except Exception:
            return False

    def _resolve_restart_command() -> list[str]:
        '''
        Build the restart command to run egon_droplets.py (or a custom script).
        Tries:
          1) Path next to the current launcher (sys.argv[0])
          2) Path next to this module (__file__)
          3) Falls back to re-running the current interpreter with current argv
        '''
        # Default: re-run the current program if no script is specified
        if not restart_script:
            return [exe] + sys.argv

        # Compute candidate roots
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

        # First existing script wins
        for script_path in candidates:
            if os.path.isfile(script_path):
                args = restart_args if isinstance(restart_args, list) else []
                return [exe, script_path, *args]

        # Fallback: re-run whatever started us
        return [exe] + sys.argv

    def _restart_program():
        # More robust restart: execv preferred, falls back to spawn+exit
        cmd = _resolve_restart_command()
        try:
            os.execv(cmd[0], cmd)
        except Exception:
            try:
                subprocess.Popen(cmd, close_fds=True)
            except Exception:
                pass
            if _window_alive():
                try:
                    root.destroy()
                except Exception:
                    pass
            os._exit(0)

    def _is_installed_fast(spec: str) -> bool:
        '''
        Quick skip check:
        - If spec is pinned (e.g., 'foo==1.2'), we still try pip (to enforce upgrade/downgrade).
        - If spec is bare (e.g., 'foo'), we try 'pip show foo' to skip if present.
        '''
        if any(op in spec for op in ('==', '>=', '<=')):
            return False
        name = spec.split('==')[0].split('>=')[0].split('<=')[0].strip()
        return _safe_check([exe, '-m', 'pip', 'show', name])

    # Handle window close during install
    def _on_close():
        if running_flag['value']:
            stop_event.set()
            _set_status('Cancelling...', 'orange')
            _set_buttons(install_enabled=False, cancel_enabled=False, close_enabled=False)
            def _poll_finish():
                if running_flag['value']:
                    root.after(100, _poll_finish)
                else:
                    try:
                        root.destroy()
                    except Exception:
                        pass
            _poll_finish()
        else:
            try:
                root.destroy()
            except Exception:
                pass

    try:
        root.protocol('WM_DELETE_WINDOW', _on_close)
    except Exception:
        pass

    def _install_thread():
        try:
            with running_lock:
                if running_flag['value']:
                    return
                running_flag['value'] = True

            _set_buttons(install_enabled=False, cancel_enabled=True, close_enabled=False)
            stop_event.clear()

            libs = list(base_libraries)
            if opt_optional.get() and optional_libraries:
                libs.extend(optional_libraries)
                result['extras_selected'] = True

            # Preflight pip
            _set_status('Checking pip availability...', 'orange')
            if not _safe_check([exe, '-m', 'pip', '--version']):
                _set_status('pip is not available in this interpreter.', 'red')
                _set_buttons(install_enabled=True, cancel_enabled=False, close_enabled=True)
                running_flag['value'] = False
                return

            total = len(libs)
            if total == 0:
                _set_status('Nothing to install.', 'orange')
                _set_buttons(install_enabled=True, cancel_enabled=False, close_enabled=True)
                running_flag['value'] = False
                return

            _set_progress(maximum=total, value=0)

            # Optional pip upgrade (determinate bar, one conceptual step)
            if opt_upgrade_pip.get():
                _set_status('Upgrading pip...', 'orange')
                ok = _safe_check_call([exe, '-m', 'pip', 'install', '--upgrade', 'pip'])
                result['upgraded_pip'] = ok
                if not ok:
                    _set_status('Failed to upgrade pip', 'red')

            # Install loop (determinate progress only)
            for idx, lib in enumerate(libs, start=1):
                if stop_event.is_set():
                    result['cancelled'] = True
                    break

                _set_progress(value=idx - 1)
                _set_status(f'Installing {lib} ({idx}/{total})...', 'orange')

                skipped = False
                ok = True

                if skip_installed and _is_installed_fast(lib):
                    skipped = True
                    _set_status(f'Already installed: {lib}', 'green')
                else:
                    ok = _safe_check([exe, '-m', 'pip', 'install', lib])

                result['attempted'] += 1
                result['packages'].append({'name': lib, 'ok': ok, 'skipped': skipped})
                if ok:
                    result['installed'] += 1
                    if not skipped:
                        _set_status(f'Installed {lib}', 'green')
                else:
                    result['failed'] += 1
                    _set_status(f'Failed to install {lib}. Continuing...', 'red')

                _set_progress(value=idx)

            # Final state and restart button
            if result['cancelled']:
                _set_status(
                    f"Cancelled (installed {result['installed']}/{result['attempted']}, failed {result['failed']}).",
                    'orange',
                )
            elif result['failed'] == 0:
                _set_status(f"Completed. Installed {result['installed']} packages.", 'green')
            else:
                _set_status(
                    f"Completed with {result['failed']} failures "
                    f"(installed {result['installed']}/{result['attempted']}).",
                    'red',
                )

            def _to_restart():
                try:
                    btn_install.configure(text='Restart program', command=_restart_program)
                except Exception:
                    pass
                _set_buttons(install_enabled=True, cancel_enabled=False, close_enabled=True)

            _ui(_to_restart)
        except Exception:
            _set_status('Installer encountered an unexpected error.', 'red')
            _set_buttons(install_enabled=True, cancel_enabled=False, close_enabled=True)
        finally:
            running_flag['value'] = False

    def _start_install():
        with running_lock:
            if running_flag['value']:
                return
        t = threading.Thread(target=_install_thread, daemon=True)
        t.start()

    def _cancel_install():
        stop_event.set()
        _set_status('Cancelling...', 'orange')
        _set_buttons(install_enabled=False, cancel_enabled=False, close_enabled=False)

    btn_install.configure(command=_start_install)
    btn_cancel.configure(command=_cancel_install)

    # Position relative to parent
    try:
        root.update_idletasks()
        if parent is not None:
            x = parent.winfo_rootx() + (parent.winfo_width() - root.winfo_width()) // 2
            y = parent.winfo_rooty() + (parent.winfo_height() - root.winfo_height()) // 3
            root.geometry(f'+{x}+{y}')
    except Exception:
        pass

    # Mainloop handling
    if own_root:
        root.mainloop()
    else:
        root.wait_window()

    return result
