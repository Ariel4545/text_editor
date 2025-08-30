import sys
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk
from typing import Optional, Any


def show_library_installer(
    parent: Optional[tk.Misc] = None,
    base_libraries: Optional[list[str]] = None,
    optional_libraries: Optional[list[str]] = None,
    allow_upgrade_pip: bool = True,
    allow_optional: bool = True,
    title: str = 'ETE - Install Required',
    *,
    alias_map: Optional[dict[str, str]] = None,
    blocklist: Optional[set[str]] = None,
    pins: Optional[dict[str, str]] = None,
    skip_installed: bool = True,
    restart_script: Optional[str] = 'EgonTE.py',
    restart_args: Optional[list[str]] = None,
    builders: Optional[Any] = None,
    app: Optional[Any] = None,
) -> dict:
    '''
    Show a minimal installer UI to install Python packages with pip.

    Returns:
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
    alias_map = {key.lower(): value for key, value in (alias_map or {}).items()}
    blocklist = {name.lower() for name in (blocklist or set())}
    pins = {key.lower(): value for key, value in (pins or {}).items()}

    def normalize_package_list(package_list: Optional[list[str]]) -> list[str]:
        if not package_list:
            return []
        seen_lower_names: set[str] = set()
        normalized: list[str] = []
        for raw_name in package_list:
            candidate = (raw_name or '').strip()
            if not candidate:
                continue
            lower_key = candidate.lower()
            if lower_key in blocklist:
                continue
            mapped = alias_map.get(lower_key, candidate)
            mapped_lower = mapped.lower()
            if '==' not in mapped and '>=' not in mapped and '<=' not in mapped and mapped_lower in pins:
                mapped = pins[mapped_lower]
                mapped_lower = mapped.lower()
            if mapped_lower not in seen_lower_names:
                seen_lower_names.add(mapped_lower)
                normalized.append(mapped)
        return normalized

    base_libraries = normalize_package_list(base_libraries)
    optional_libraries = normalize_package_list(optional_libraries)

    result_data = {
        'installed': 0,
        'failed': 0,
        'attempted': 0,
        'upgraded_pip': False,
        'extras_selected': False,
        'cancelled': False,
        'packages': [],
    }

    # Prefer UI builders for consistent theming/placement if available
    owns_mainloop = False
    use_builders = False
    active_builders = builders

    try:
        # Import lazily to avoid hard dependency if UI module is not present
        if active_builders is None and app is not None:
            from UI.ui_builders import UIBuilders  # type: ignore
            active_builders = UIBuilders(app)      # type: ignore
    except Exception:
        active_builders = None

    if active_builders is not None and hasattr(active_builders, 'make_pop_ups_window'):
        try:
            window_root = active_builders.make_pop_ups_window(
                function=show_library_installer,
                custom_title=title,
                parent=parent,
                modal=False,
                title=title,
            )
            use_builders = True
        except Exception:
            use_builders = False

    if not use_builders:
        if parent is None:
            try:
                default_root_widget = getattr(tk, '_default_root', None)
            except Exception:
                default_root_widget = None
            if default_root_widget is not None:
                window_root = tk.Toplevel(default_root_widget)
                window_root.transient(default_root_widget)
            else:
                window_root = tk.Tk()
                owns_mainloop = True
        else:
            window_root = tk.Toplevel(parent)
            window_root.transient(parent)
            try:
                window_root.grab_set()
            except Exception:
                pass
        window_root.title(title)
        window_root.resizable(False, False)

    running_lock = threading.Lock()
    running_flag = {'value': False}

    main_frame = ttk.Frame(window_root, padding=10)
    main_frame.pack(fill='both', expand=True)

    title_label = ttk.Label(
        main_frame,
        text='It seems that some required libraries are not installed',
        font=('Segoe UI', 10, 'underline'),
    )
    title_label.pack(anchor='w')

    status_label = ttk.Label(main_frame, text='', font=('Segoe UI', 9))
    status_label.pack(anchor='w', pady=(8, 4))

    options_frame = ttk.LabelFrame(main_frame, text='Additional Options')
    options_frame.pack(fill='x', pady=(6, 10))

    optional_var = tk.BooleanVar(value=False)
    upgrade_pip_var = tk.BooleanVar(value=False)
    option_checkbuttons: list[ttk.Checkbutton] = []

    options_column_index = 0
    if allow_optional and optional_libraries:
        optional_check = ttk.Checkbutton(options_frame, text='Install optional libraries', variable=optional_var)
        optional_check.grid(row=0, column=options_column_index, sticky='w', padx=6, pady=4)
        option_checkbuttons.append(optional_check)
        options_column_index += 1
    if allow_upgrade_pip:
        upgrade_check = ttk.Checkbutton(options_frame, text='Upgrade pip', variable=upgrade_pip_var)
        upgrade_check.grid(row=0, column=options_column_index, sticky='w', padx=6, pady=4)
        option_checkbuttons.append(upgrade_check)
        options_column_index += 1

    buttons_frame = ttk.Frame(main_frame)
    buttons_frame.pack(fill='x')

    install_button = ttk.Button(buttons_frame, text='Install')
    install_button.pack(side='left')

    cancel_button = ttk.Button(buttons_frame, text='Cancel')
    cancel_button.pack(side='left', padx=(8, 0))
    cancel_button.state(['disabled'])

    close_button = ttk.Button(buttons_frame, text='Close', command=window_root.destroy)
    close_button.pack(side='right')

    progress_bar = ttk.Progressbar(main_frame, mode='determinate')
    progress_bar.pack(fill='x', pady=(8, 0))

    python_executable = sys.executable
    stop_event = threading.Event()

    def window_is_alive() -> bool:
        try:
            return bool(window_root and window_root.winfo_exists())
        except Exception:
            return False

    def ui_call(callback, *args, **kwargs):
        if window_is_alive():
            try:
                window_root.after(0, callback, *args, **kwargs)
            except Exception:
                pass

    def set_status_text(text: str, color: str = ''):
        ui_call(status_label.configure, text=text, foreground=color or '')

    def set_progress_value(maximum: Optional[int] = None, value: Optional[int] = None):
        def apply_progress():
            try:
                if maximum is not None:
                    progress_bar.configure(maximum=maximum)
                if value is not None:
                    progress_bar.configure(value=value)
            except Exception:
                pass
        ui_call(apply_progress)

    def set_button_states(install_enabled: bool, cancel_enabled: bool, close_enabled: bool):
        def apply_states():
            try:
                install_button.state(['!disabled'] if install_enabled else ['disabled'])
                cancel_button.state(['!disabled'] if cancel_enabled else ['disabled'])
                close_button.state(['!disabled'] if close_enabled else ['disabled'])
                for option_button in option_checkbuttons:
                    option_button.state(['!disabled'] if install_enabled else ['disabled'])
            except Exception:
                pass
        ui_call(apply_states)

    def safe_check_call(command: list[str]) -> bool:
        try:
            subprocess.check_call(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            return True
        except Exception:
            return False

    def safe_check_output(command: list[str]) -> bool:
        try:
            subprocess.check_output(command, stderr=subprocess.STDOUT)
            return True
        except Exception:
            return False

    def resolve_restart_command() -> list[str]:
        if not restart_script:
            return [python_executable] + sys.argv
        candidate_paths: list[str] = []
        try:
            launch_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            candidate_paths.append(os.path.join(launch_dir, restart_script))
        except Exception:
            pass
        try:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            candidate_paths.append(os.path.join(module_dir, restart_script))
        except Exception:
            pass
        for script_path in candidate_paths:
            if os.path.isfile(script_path):
                extra_args = restart_args if isinstance(restart_args, list) else []
                return [python_executable, script_path, *extra_args]
        return [python_executable] + sys.argv

    def restart_program():
        command = resolve_restart_command()
        try:
            os.execv(command[0], command)
        except Exception:
            try:
                subprocess.Popen(command, close_fds=True)
            except Exception:
                pass
            if window_is_alive():
                try:
                    window_root.destroy()
                except Exception:
                    pass
            os._exit(0)

    def is_installed_fast(spec: str) -> bool:
        if any(op in spec for op in ('==', '>=', '<=')):
            return False
        base_name = spec.split('==')[0].split('>=')[0].split('<=')[0].strip()
        return safe_check_output([python_executable, '-m', 'pip', 'show', base_name])

    # Close handling:
    # - If using UI builders, do NOT override the close protocol the builder set.
    #   Instead, ensure we stop the worker if the window is being destroyed.
    # - If not using builders, set a protocol that cancels safely.
    def on_close_request():
        if running_flag['value']:
            stop_event.set()
            set_status_text('Cancelling...', 'orange')
            set_button_states(install_enabled=False, cancel_enabled=False, close_enabled=False)
            def poll_finish():
                if running_flag['value']:
                    window_root.after(100, poll_finish)
                else:
                    try:
                        window_root.destroy()
                    except Exception:
                        pass
            poll_finish()
        else:
            try:
                window_root.destroy()
            except Exception:
                pass

    if use_builders:
        # Respect builder's protocol; just ensure cancellation if the window gets destroyed
        try:
            def on_destroy_event(event=None):
                try:
                    if running_flag['value']:
                        stop_event.set()
                except Exception:
                    pass
            window_root.bind('<Destroy>', on_destroy_event, add='+')
        except Exception:
            pass
    else:
        try:
            window_root.protocol('WM_DELETE_WINDOW', on_close_request)
        except Exception:
            pass

    def install_thread_worker():
        try:
            with running_lock:
                if running_flag['value']:
                    return
                running_flag['value'] = True

            set_button_states(install_enabled=False, cancel_enabled=True, close_enabled=False)
            stop_event.clear()

            package_queue = list(base_libraries)
            if optional_var.get() and optional_libraries:
                package_queue.extend(optional_libraries)
                result_data['extras_selected'] = True

            set_status_text('Checking pip availability...', 'orange')
            if not safe_check_output([python_executable, '-m', 'pip', '--version']):
                set_status_text('pip is not available in this interpreter.', 'red')
                set_button_states(install_enabled=True, cancel_enabled=False, close_enabled=True)
                running_flag['value'] = False
                return

            total_count = len(package_queue)
            if total_count == 0:
                set_status_text('Nothing to install.', 'orange')
                set_button_states(install_enabled=True, cancel_enabled=False, close_enabled=True)
                running_flag['value'] = False
                return

            set_progress_value(maximum=total_count, value=0)

            if allow_upgrade_pip and upgrade_pip_var.get():
                set_status_text('Upgrading pip...', 'orange')
                upgraded_ok = safe_check_call([python_executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
                result_data['upgraded_pip'] = upgraded_ok
                if not upgraded_ok:
                    set_status_text('Failed to upgrade pip', 'red')

            for index_one_based, package_name in enumerate(package_queue, start=1):
                if stop_event.is_set():
                    result_data['cancelled'] = True
                    break

                set_progress_value(value=index_one_based - 1)
                set_status_text(f'Installing {package_name} ({index_one_based}/{total_count})...', 'orange')

                was_skipped = False
                install_ok = True

                if skip_installed and is_installed_fast(package_name):
                    was_skipped = True
                    set_status_text(f'Already installed: {package_name}', 'green')
                else:
                    install_ok = safe_check_output([python_executable, '-m', 'pip', 'install', package_name])

                result_data['attempted'] += 1
                result_data['packages'].append({'name': package_name, 'ok': install_ok, 'skipped': was_skipped})
                if install_ok:
                    result_data['installed'] += 1
                    if not was_skipped:
                        set_status_text(f'Installed {package_name}', 'green')
                else:
                    result_data['failed'] += 1
                    set_status_text(f'Failed to install {package_name}. Continuing...', 'red')

                set_progress_value(value=index_one_based)

            if result_data['cancelled']:
                set_status_text(
                    f"Cancelled (installed {result_data['installed']}/{result_data['attempted']}, "
                    f"failed {result_data['failed']}).",
                    'orange',
                )
            elif result_data['failed'] == 0:
                set_status_text(f"Completed. Installed {result_data['installed']} packages.", 'green')
            else:
                set_status_text(
                    f"Completed with {result_data['failed']} failures "
                    f"(installed {result_data['installed']}/{result_data['attempted']}).",
                    'red',
                )

            def prepare_restart_button():
                try:
                    install_button.configure(text='Restart program', command=restart_program)
                except Exception:
                    pass
                set_button_states(install_enabled=True, cancel_enabled=False, close_enabled=True)

            ui_call(prepare_restart_button)
        except Exception:
            set_status_text('Installer encountered an unexpected error.', 'red')
            set_button_states(install_enabled=True, cancel_enabled=False, close_enabled=True)
        finally:
            running_flag['value'] = False

    def start_install():
        with running_lock:
            if running_flag['value']:
                return
        worker_thread = threading.Thread(target=install_thread_worker, daemon=True)
        worker_thread.start()

    def cancel_install():
        stop_event.set()
        set_status_text('Cancelling...', 'orange')
        set_button_states(install_enabled=False, cancel_enabled=False, close_enabled=False)

    install_button.configure(command=start_install)
    cancel_button.configure(command=cancel_install)

    if not use_builders:
        try:
            window_root.update_idletasks()
            if parent is not None:
                x_position = parent.winfo_rootx() + (parent.winfo_width() - window_root.winfo_width()) // 2
                y_position = parent.winfo_rooty() + (parent.winfo_height() - window_root.winfo_height()) // 3
                window_root.geometry(f'+{x_position}+{y_position}')
        except Exception:
            pass

    if owns_mainloop:
        window_root.mainloop()
    else:
        window_root.wait_window()

    return result_data
