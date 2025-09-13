import tkinter as tk
import tkinter.ttk as ttk
from typing import Any, Optional, Tuple, Callable, Union, Iterable, Hashable
try:
    from tkhtmlview import HTMLText
except ModuleNotFoundError:
    pass

class UIBuilders:
    def __init__(self, app: Any) -> None:
        self.app = app
        self._registry = {}

    def _resolve_owner(self, parent_widget: Optional[tk.Misc]) -> tk.Misc:
        '''
        Return a Tkinter widget suitable to be the owner of a Toplevel.
        Avoids touching low-level .tk attributes and handles common app layouts.
        '''
        if isinstance(parent_widget, tk.Misc):
            return parent_widget

        # Common candidates on the app
        candidates = [
            getattr(self.app, 'root', None),
            getattr(self.app, 'master', None),
            getattr(self.app, '_root', None),
            self.app,  # if the app itself is a widget (e.g., subclass of Tk/Frame)
        ]
        for candidate in candidates:
            if isinstance(candidate, tk.Misc):
                return candidate

        # Fallback: use the default root if available
        default_root = tk._get_default_root()
        if isinstance(default_root, tk.Misc):
            return default_root

        raise RuntimeError('No valid Tkinter owner widget found for popup creation')

    def make_pop_ups_window(
            self,
            function=None,
            custom_title: bool | str = False,
            external_variable: bool = False,
            *,
            parent: Optional[tk.Misc] = None,
            geometry: Optional[str] = None,
            resizable: Optional[Tuple[bool, bool]] = None,
            modal: bool = False,
            topmost: bool = False,
            name: Optional[str] = None,
            title: Optional[str] = None,
    ) -> tk.Toplevel:
        # 1) Resolve a valid owner widget (fixes the tkapp .tk issue)
        owner_widget = self._resolve_owner(parent)

        # 2) Title logic (derived title if not given)
        derived_name = None
        if function is not None:
            try:
                derived_name = (function.__name__.replace('_', ' ')).capitalize()
            except Exception:
                pass
        if custom_title and isinstance(custom_title, str) and custom_title.strip():
            derived_name = custom_title
        if title is None:
            title_prefix = getattr(self.app, 'title_struct', '')
            title = f'{title_prefix}{derived_name}' if derived_name else title_prefix

        # 3) Optional singleton behavior key
        allow_duplicate = bool(getattr(self.app, 'allow_duplicate', True))
        singleton_key = name or (function if function is not None else None)
        if singleton_key is not None and not allow_duplicate:
            existing = self._registry.get(singleton_key)
            if existing:
                try:
                    existing.deiconify()
                    existing.lift()
                    existing.focus_force()
                    return existing
                except tk.TclError:
                    self._registry.pop(singleton_key, None)

        # 4) Create the popup
        popup_window = tk.Toplevel(owner_widget)
        if title:
            popup_window.title(title)
        if geometry:
            popup_window.geometry(geometry)

        # Set resizable explicitly if requested; otherwise let app rules apply later
        if resizable is not None:
            try:
                popup_window.resizable(*resizable)
            except Exception:
                pass

        if topmost:
            try:
                popup_window.attributes('-topmost', True)
            except Exception:
                pass

        try:
            popup_window.transient(owner_widget)
        except Exception:
            pass

        # Optional icon from the app
        icon = getattr(self.app, 'iconphoto', None)
        if icon:
            try:
                popup_window.iconphoto(False, icon)
            except Exception:
                pass

        # Track open windows and map function -> window (if app uses these)
        if hasattr(self.app, 'opened_windows'):
            self.app.opened_windows.append(popup_window)
        if function is not None:
            func_map = getattr(self.app, 'func_window', None)
            if not isinstance(func_map, dict):
                self.app.func_window = {}
            self.app.func_window[function] = popup_window

        # Close protocol: delegate to app if external_variable is False
        if not external_variable and hasattr(self.app, 'close_pop_ups'):
            popup_window.protocol('WM_DELETE_WINDOW', lambda: self.app.close_pop_ups(popup_window))
        else:
            def on_close():
                try:
                    if hasattr(self.app, 'opened_windows'):
                        self.app.opened_windows = [w for w in self.app.opened_windows if w is not popup_window]
                    if singleton_key is not None and self._registry.get(singleton_key) is popup_window:
                        self._registry.pop(singleton_key, None)
                finally:
                    popup_window.destroy()

            popup_window.protocol('WM_DELETE_WINDOW', on_close)

        # Transparency (alpha) from app state
        alpha_value = getattr(self.app, 'st_value', None)
        if alpha_value is not None:
            try:
                popup_window.attributes('-alpha', alpha_value)
            except Exception:
                pass

        # Theming/time setup if app provides it
        apply_tm = getattr(self.app, 'make_tm', None)
        if callable(apply_tm):
            try:
                apply_tm(popup_window)
            except Exception:
                pass

        # App-driven non-resizable rule
        try:
            limit_flag = getattr(self.app, 'limit_w_s', None)
            if limit_flag and callable(getattr(limit_flag, 'get', None)) and limit_flag.get():
                popup_window.resizable(False, False)
        except Exception:
            pass

        # Optional modality
        if modal:
            try:
                popup_window.grab_set()
            except Exception:
                pass

        # Position and focus
        self._center_on_parent(popup_window)
        popup_window.focus_set()

        # Log entry
        try:
            now_fn = getattr(self.app, 'get_time', None)
            ts = now_fn() if callable(now_fn) else ''
            if hasattr(self.app, 'record_list') and derived_name:
                self.app.record_list.append(f'> [{ts}] - {derived_name} tool window opened')
        except Exception:
            pass

        # Remember singleton
        if singleton_key is not None and not allow_duplicate:
            self._registry[singleton_key] = popup_window

        # Popup bindings
        self._popup_binds(popup_window)
        return popup_window

    def _popup_binds(self, popup_window: tk.Toplevel) -> None:
        try:
            popup_window.bind('<Escape>', lambda e: popup_window.destroy(), add='+')
            popup_window.bind('<Control-w>', lambda e: popup_window.destroy(), add='+')
        except Exception:
            pass

    def _center_on_parent(self, popup_window: tk.Toplevel) -> None:
        try:
            popup_window.update_idletasks()
            owner = popup_window.master
            if not owner:
                return
            x = owner.winfo_rootx() + (owner.winfo_width() - popup_window.winfo_width()) // 2
            y = owner.winfo_rooty() + (owner.winfo_height() - popup_window.winfo_height()) // 3
            popup_window.geometry(f'+{x}+{y}')
        except Exception:
            pass

    def make_rich_textbox(
        self,
        parent_container: Optional[tk.Misc] = None,
        place: Union[str, Tuple[int, int], list] = 'pack_top',
        wrap: Any = tk.WORD,
        font: str = 'arial 10',
        size: Optional[Tuple[int, int]] = None,
        selectbg: str = 'dark cyan',
        bd: int = 0,
        relief: str = '',
        format: str = 'txt',
        *,
        # legacy alias to remain compatible with old calls/forwarders
        root: Optional[tk.Misc] = None,
    ) -> Tuple[tk.Frame, Any, ttk.Scrollbar]:
        '''
        Build a scrollable rich text box inside a container frame.

        Accepts either parent_container (preferred) or root (legacy alias).
        Supports format='txt' or format='html' (uses tkhtmlview.HTMLText if available; falls back to tk.Text otherwise).

        Returns:
            (container_frame, text_widget, y_scrollbar)
        '''
        # Use legacy alias if provided
        container = parent_container or root
        if container is None:
            raise ValueError('make_rich_textbox requires a parent_container (or legacy root) widget')

        final_relief = relief or getattr(self.app, 'predefined_relief', tk.FLAT)
        cursor_style = getattr(self.app, 'predefined_cursor', 'xterm')

        container_frame = tk.Frame(container)
        y_scrollbar = ttk.Scrollbar(container_frame, orient='vertical')

        # Choose the text-like class
        text_cls: Any = tk.Text
        if isinstance(format, str) and format.lower() == 'html':
            # Try to import HTMLText only when needed
            try:
                from tkhtmlview import HTMLText as _HTMLText
                text_cls = _HTMLText
            except Exception:
                # Fallback to Text if tkhtmlview is not installed/available
                text_cls = tk.Text

        # Create the text widget (HTMLText is a Text subclass, so most options are supported)
        text_widget = text_cls(
            container_frame,
            wrap=wrap,
            relief=final_relief,
            font=font,
            borderwidth=bd,
            cursor=cursor_style,
            yscrollcommand=y_scrollbar.set,
            undo=True,
            selectbackground=selectbg,
        )
        y_scrollbar.config(command=text_widget.yview)

        # Optional explicit size
        if size:
            try:
                text_widget.configure(width=size[0], height=size[1])
            except Exception:
                pass

        # Place container and children
        self._place_container(container_frame, place)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.pack(fill=tk.BOTH, expand=True)

        return (container_frame, text_widget, y_scrollbar)

    def _place_container(self, frame: tk.Frame, place: Union[str, Tuple[int, int], list]) -> None:
        '''
        Helper for placing the container frame.
        - If place is a string with 'pack' (e.g., 'pack_top', 'pack_left'), it uses pack with that side.
        - If place is a (row, col) tuple/list, it uses grid at that position.
        '''
        if not place:
            return

        if isinstance(place, (tuple, list)) and len(place) >= 2:
            row, col = place[0], place[1]
            frame.grid(row=row, column=col)
            return

        if isinstance(place, str) and 'pack' in place:
            # Expected patterns: 'pack_top', 'pack_left', 'pack_right', 'pack_bottom'
            side = 'top'
            parts = place.split('_', 1)
            if len(parts) == 2 and parts[1] in ('top', 'left', 'right', 'bottom'):
                side = parts[1]
            frame.pack(fill=tk.BOTH, expand=True, side=side)
            return

        # Fallback: sensible default
        frame.pack(fill=tk.BOTH, expand=True, side='top')

    def place_toolt(
        self,
        targets: Optional[Iterable[Tuple[tk.Widget, str]]] = None,
        *,
        prefer_external: bool = True,   # try tktooltip first
        allow_tix: bool = True,         # if external not found, try Tix
        delay_ms: int = 600,
        follow_mouse: bool = True,
        fg: Optional[str] = None,
        bg: Optional[str] = None,
    ) -> None:
        '''
        Initialize tooltips for toolbar buttons without backend collisions.

        Backends (mutually exclusive for the whole session):
          - 'external': tktooltip.ToolTip (preferred)
          - 'tix': tkinter.tix.Balloon
        '''
        # Resolve targets
        if targets is None:
            targets = self._collect_default_tooltip_targets()
        items = [(w, text) for (w, text) in targets if self._is_widget(w)]
        if not items:
            return

        # Decide and lock the backend only once to avoid collisions
        backend = getattr(self, '_tooltip_backend', None)
        if backend is None:
            backend = self._select_tooltip_backend(prefer_external=prefer_external, allow_tix=allow_tix)
            self._tooltip_backend = backend
            # Backend-level initialization
            if backend == 'tix':
                self._ensure_tix_balloon(delay_ms)
            # Initialize tracking
            self._tooltip_handles = {}         # widget -> handle (external)
            self._tooltip_bound_widgets = set()  # for tix bindings

        # Attach for chosen backend only
        if backend == 'external':
            self._attach_tooltips_external(items, delay_ms, follow_mouse, fg, bg)
        elif backend == 'tix':
            self._attach_tooltips_tix(items)
        else:
            # Neither external nor Tix is available; do nothing by design
            pass

    # ---------- Backend selection and guards ----------

    def _select_tooltip_backend(self, *, prefer_external: bool, allow_tix: bool) -> str:
        if prefer_external and self._external_available():
            return 'external'
        if allow_tix and self._tix_available():
            return 'tix'
        return 'none'

    def _external_available(self) -> bool:
        try:
            import tktooltip  # noqa: F401
            return True
        except Exception:
            return False

    def _tix_available(self) -> bool:
        try:
            import tkinter.tix as _  # noqa: F401
            return True
        except Exception:
            return False

    # ---------- External: tktooltip backend ----------

    def _attach_tooltips_external(
        self,
        items: Iterable[Tuple[tk.Widget, str]],
        delay_ms: int,
        follow_mouse: bool,
        fg: Optional[str],
        bg: Optional[str],
    ) -> None:
        from tktooltip import ToolTip as TkToolTip  # type: ignore
        handles = self._tooltip_handles  # type: ignore[attr-defined]

        for widget, text in items:
            if widget in handles:
                continue  # prevent double-binding

            handle = None
            # Try full-featured signature first
            try:
                handle = TkToolTip(widget, msg=text, delay=delay_ms, follow=follow_mouse, fg=fg, bg=bg)
            except TypeError:
                # Version variance: fall back to minimal supported signature
                handle = TkToolTip(widget, msg=text)
            except Exception:
                # Safety: minimal usage if even signature differs
                try:
                    handle = TkToolTip(widget, msg=text)
                except Exception:
                    handle = None
            if handle is not None:
                handles[widget] = handle

    # ---------- Tix: Balloon backend (single instance, shared delay) ----------

    def _ensure_tix_balloon(self, delay_ms: int) -> None:
        import tkinter.tix as tix
        # Ensure Tix package loaded; ignore errors if already present
        try:
            self.app.tk.eval('package require Tix')
        except Exception:
            pass
        self._tix_balloon = tix.Balloon(self.app)  # type: ignore[attr-defined]
        try:
            # Set global initial wait (milliseconds) for this balloon instance
            self._tix_balloon.configure(initwait=delay_ms)  # type: ignore[attr-defined]
        except Exception:
            pass

    def _attach_tooltips_tix(self, items: Iterable[Tuple[tk.Widget, str]]) -> None:
        balloon = getattr(self, '_tix_balloon', None)
        if balloon is None:
            return
        bound = self._tooltip_bound_widgets  # type: ignore[attr-defined]

        for widget, text in items:
            if widget in bound:
                continue
            try:
                balloon.bind_widget(widget, balloonmsg=text)
                bound.add(widget)
            except Exception:
                # If binding fails for this widget, skip it safely
                pass

    # ---------- Shared helpers ----------

    def _collect_default_tooltip_targets(self) -> Iterable[Tuple[tk.Widget, str]]:
        targets: list[Tuple[tk.Widget, str]] = []

        def add(name: str, text: str):
            widget = getattr(self.app, name, None)
            if self._is_widget(widget):
                targets.append((widget, text))


        '''+ optimaize with a loop which its content will come from the 'large variables file' '''
        add('bold_button', 'Bold (Ctrl+B)')
        add('italics_button', 'Italics (Ctrl+I)')
        add('underline_button', 'Underline (Ctrl+U)')
        add('align_left_button', 'Align left (Ctrl+L)')
        add('align_center_button', 'Align center (Ctrl+E)')
        add('align_right_button', 'Align right (Ctrl+R)')
        add('color_button', 'Change colors')
        add('tts_button', 'Text to speech')
        add('talk_button', 'Speech to text')
        add('font_size', 'Font size: Ctrl+Plus / Ctrl+Minus')
        add('v_keyboard_button', 'Virtual keyboard')
        add('dtt_button', 'Draw to text')
        add('calc_button', 'Calculator')
        add('translate_button', 'Translator')
        return targets

    def _is_widget(self, obj: Any) -> bool:
        return isinstance(obj, tk.Misc)

    def binds(self, mode: str = 'initial') -> None:
        '''
        Bind keyboard/mouse shortcuts.

        Modes:
          - 'initial' / 'reset': bind all groups (respecting binding_work flags)
          - group key: one of ['filea', 'typea', 'editf', 'textt', 'windf', 'autof', 'autol']
        This mirrors the original behavior and maintains app.bindings_dict compatibility.
        '''
        app = self.app

        # 1) Build handler maps (event name -> callable)
        handler_groups = self._build_handler_groups()

        # 2) Pattern groups pulled from app (matches your large variables)
        pattern_groups = self._build_pattern_groups()

        # 3) Management flags (BooleanVars) to enable/disable groups
        bind_flags = getattr(app, 'binding_work', {}) if isinstance(getattr(app, 'binding_work', {}), dict) else {}

        # 4) Choose which groups to process
        all_groups = ['filea', 'typea', 'editf', 'textt', 'windf', 'autof', 'autol']
        if mode in ('initial', 'reset'):
            target_groups = all_groups
        else:
            target_groups = [mode] if mode in all_groups else []

        # Initialize records
        if not hasattr(self, '_bound_by_mode'):
            self._bound_by_mode: dict[str, list[Tuple[tk.Misc, str]]] = {}

        # Before rebinding, clear previous bindings for the selected mode(s)
        if mode in ('initial', 'reset'):
            # Re-create all
            for g in target_groups:
                self.unbind_group(g)
        else:
            self.unbind_group(mode)

        # 5) Bind per group
        for group_key in target_groups:
            # Respect the toggle flag if present
            flag_var = bind_flags.get(group_key)
            if flag_var is not None:
                try:
                    if not bool(flag_var.get()):
                        continue
                except Exception:
                    pass

            target_widget = self._resolve_group_target(group_key)
            if target_widget is None:
                continue

            handlers_map = handler_groups.get(group_key, {}) or {}

            if group_key == 'autol':
                handler = handlers_map.get('KeyRelease')
                if callable(handler):
                    if self._safe_bind(target_widget, '<KeyRelease>', handler):
                        self._bound_by_mode.setdefault('autol', []).append((target_widget, '<KeyRelease>'))
                self._ensure_bindings_dict_shape(pattern_groups, autol_var=getattr(app, 'aul', None))
                continue

            patterns = pattern_groups.get(group_key, [])
            bound_any = False
            for pattern in patterns:
                ev_key = self._normalize_event_key(pattern)
                handler = handlers_map.get(ev_key) or self._pick_fallback_handler(ev_key, handler_groups)
                if not callable(handler):
                    continue
                # Ensure the actual bound sequence is bracketed
                bound_seq = self._ensure_bracketed_pattern(pattern)
                if self._safe_bind(target_widget, bound_seq, handler):
                    self._bound_by_mode.setdefault(group_key, []).append((target_widget, bound_seq))
                    bound_any = True
            self._ensure_bindings_dict_shape(pattern_groups)

        # 6) For compatibility with your original method: right-click on main text
        self._attach_right_click()

        # 7) Ensure Text 'modified' status updates (<<Modified>>) are bound
        try:
            tw = getattr(app, 'EgonTE', None)
            if isinstance(tw, tk.Misc):
                status_handler = getattr(app, 'status', None)
                if callable(status_handler):
                    tw.bind('<<Modified>>', status_handler, add='+')
        except Exception:
            pass

        # 8) Bind any "initial" one-off keys not present in pattern lists (e.g., F5, Alt+F4, Ctrl+Delete, Ctrl+D)
        try:
            target_widget = self._resolve_group_target('initial')
            if target_widget is not None:
                all_patterns = set()
                for plist in pattern_groups.values():
                    for pat in plist:
                        all_patterns.add(self._ensure_bracketed_pattern(pat))
                initial_handlers = handler_groups.get('initial', {}) or {}
                for key_name, handler in initial_handlers.items():
                    if not callable(handler):
                        continue
                    seq = self._ensure_bracketed_pattern(key_name)
                    if seq not in all_patterns:
                        self._safe_bind(target_widget, seq, handler)
                        self._bound_by_mode.setdefault('initial', []).append((target_widget, seq))
        except Exception:
            pass


    def unbind_group(self, mode: str) -> None:
        '''
        Unbind all patterns previously recorded for a group/mode.
        Updates app.bindings_dict[mode] to original shape.
        '''
        if not hasattr(self, '_bound_by_mode'):
            return
        records = self._bound_by_mode.get(mode, [])
        for widget, pattern in records:
            self._safe_unbind(widget, pattern)
        self._bound_by_mode[mode] = []

        # Reset bindings_dict entry to original shape
        if hasattr(self.app, 'bindings_dict') and isinstance(self.app.bindings_dict, dict):
            if mode == 'autol':
                self.app.bindings_dict['autol'] = getattr(self.app, 'aul', None)
            else:
                # Revert to the canonical pattern list for that group (from pattern groups)
                groups = self._build_pattern_groups()
                self.app.bindings_dict[mode] = groups.get(mode, [])

    def reset_binds(self) -> None:
        '''
        Unbind all recorded patterns for all modes and rebind everything.
        If app.binding_work exists (dict of BooleanVar flags), set all to True first.
        '''
        if hasattr(self, '_bound_by_mode'):
            for mode in list(self._bound_by_mode.keys()):
                self.unbind_group(mode)

        bw = getattr(self.app, 'binding_work', None)
        if isinstance(bw, dict):
            for var in bw.values():
                try:
                    var.set(True)
                except Exception:
                    pass

        self.binds(mode='reset')

    # ---------- internals ----------

    def _build_handler_groups(self) -> dict[str, dict[str, Any]]:
        app = self.app
        return {
            'initial': {
                'Modified': getattr(app, 'status', None),
                'Cut': (lambda e=None: app.cut(True)) if hasattr(app, 'cut') else None,
                'Copy': getattr(app, 'copy', None),
                'Control-Key-a': getattr(app, 'select_all', None),
                'Control-Key-l': (lambda e=None: app.align_text()) if hasattr(app, 'align_text') else None,
                'Control-Key-e': (lambda e=None: app.align_text('center')) if hasattr(app, 'align_text') else None,
                'Control-Key-r': (lambda e=None: app.align_text('right')) if hasattr(app, 'align_text') else None,
                'Alt-Key-c': getattr(app, 'clear', None),
                'Alt-F4': getattr(app, 'exit_app', None),
                'Control-Key-plus': getattr(app, 'sizes_shortcuts', None),
                'Control-Key-minus': (lambda e=None: app.sizes_shortcuts(-1)) if hasattr(app,
                                                                                         'sizes_shortcuts') else None,
                'F5': getattr(app, 'dt', None),
                'Alt-Key-r': (lambda e=None: app.exit_app(event='r')) if hasattr(app, 'exit_app') else None,
                # Added convenience bindings irrespective of pattern lists:
                'Control-Delete': getattr(app, 'clear', None),
                'Control-Key-d': getattr(app, 'copy_file_path', None),
            },
            'autof': {
                'KeyPress': getattr(app, 'emoji_detection', None),
                'KeyRelease': getattr(app, 'update_insert_image_list', None),
            },
            'autol': {
                'KeyRelease': getattr(app, 'aul_var', None) or getattr(app, 'aul_var', None) or getattr(app, 'aul',
                                                                                                        None),
            },
            'typea': {
                'Control-Key-b': (lambda e=None: app.typefaces(tf='weight-bold')) if hasattr(app,
                                                                                             'typefaces') else None,
                'Control-Key-i': (lambda e=None: app.typefaces(tf='slant-italic')) if hasattr(app,
                                                                                              'typefaces') else None,
                'Control-Key-u': (lambda e=None: app.typefaces(tf='underline')) if hasattr(app, 'typefaces') else None,
            },
            'editf': {
                'Control-Key-f': getattr(app, 'find_text', None),
                'Control-Key-h': getattr(app, 'replace', None),
                'Control-Key-g': getattr(app, 'goto', None),
            },
            'filea': {
                'Control-o': getattr(app, 'open_file', None),
                'Control-Key-s': getattr(app, 'save', None),
                'Control-Key-n': getattr(app, 'new_file', None),
                'Control-Key-p': getattr(app, 'print_file', None),
                'Alt-Key-d': getattr(app, 'copy_file_path', None),
                # Keep Alt+D for backward compatibility
            },
            'textt': {
                'Control-Shift-Key-j': getattr(app, 'join_words', None),
                'Control-Shift-Key-u': getattr(app, 'lower_upper', None),
                'Control-Shift-Key-r': getattr(app, 'reverse_characters', None),
                'Control-Shift-Key-c': getattr(app, 'reverse_words', None),
            },
            'windf': {
                'F11': getattr(app, 'full_screen', None),
                'Control-Key-t': getattr(app, 'topmost', None),
            },
        }

    def _build_pattern_groups(self) -> dict[str, list[str]]:
        app = self.app
        # Prefer attributes if provided; otherwise fall back to app.bindings_dict (which the app initializes)
        bd = getattr(app, 'bindings_dict', None) if isinstance(getattr(app, 'bindings_dict', None), dict) else {}

        def _get_list(attr_name: str, dict_key: str) -> list[str]:
            vals = list(getattr(app, attr_name, [])) or []
            if not vals and bd:
                vals = list(bd.get(dict_key, [])) or []
            return vals

        filea = _get_list('filea_list', 'filea')
        typea = _get_list('typef_list', 'typea')
        editf = _get_list('editf_list', 'editf')
        textt = _get_list('textt_list', 'textt')
        windf = _get_list('win_list', 'windf')
        autof = _get_list('autof_list', 'autof')

        # Ensure app.bindings_dict precisely matches expected shape
        if not hasattr(app, 'bindings_dict') or not isinstance(app.bindings_dict, dict):
            app.bindings_dict = {}

        app.bindings_dict.update({
            'filea': filea,
            'typea': typea,
            'editf': editf,
            'textt': textt,
            'windf': windf,
            'autof': autof,
            'autol': getattr(app, 'aul', None),  # original: variable stored here (not pattern)
        })

        return {
            'filea': filea,
            'typea': typea,
            'editf': editf,
            'textt': textt,
            'windf': windf,
            'autof': autof,
            # autol handled specially in binds()
        }

    def _ensure_bindings_dict_shape(self, patterns: dict[str, list[str]], autol_var: Any = None) -> None:
        '''
        Re-assert the expected shape of app.bindings_dict after (re)binding.
        '''
        app = self.app
        app.bindings_dict['filea'] = patterns.get('filea', [])
        app.bindings_dict['typea'] = patterns.get('typea', [])
        app.bindings_dict['editf'] = patterns.get('editf', [])
        app.bindings_dict['textt'] = patterns.get('textt', [])
        app.bindings_dict['windf'] = patterns.get('windf', [])
        app.bindings_dict['autof'] = patterns.get('autof', [])
        if autol_var is not None:
            app.bindings_dict['autol'] = autol_var

    def _resolve_group_target(self, group_key: str) -> Optional[tk.Misc]:
        app = self.app
        # Prefer the main Text widget for all key bindings if available
        tw = getattr(app, 'EgonTE', None)
        if isinstance(tw, tk.Misc):
            return tw
        # Fallbacks
        if isinstance(app, tk.Misc):
            return app
        root = getattr(app, 'root', None)
        if isinstance(root, tk.Misc):
            return root
        dr = tk._get_default_root()
        return dr if isinstance(dr, tk.Misc) else None

    def _normalize_event_key(self, pattern: str) -> str:
        """Normalize incoming patterns like '<Control-Key-b>' / '<Control-b>' / 'Control-o'
        into a canonical comparison form and try to equalize Key presence."""
        raw = pattern[1:-1] if pattern.startswith('<') and pattern.endswith('>') else pattern
        # Canonicalize 'Control-Key-x' -> 'Control-Key-x'
        parts = raw.split('-')
        # If it's like Control-b, expand to Control-Key-b for lookups
        if len(parts) >= 2 and parts[-2] != 'Key' and len(parts[-1]) == 1:
            # Insert 'Key' before last segment
            parts.insert(-1, 'Key')
            raw = '-'.join(parts)
        return raw

    def _pick_fallback_handler(self, ev_key: str, handler_groups: dict[str, dict[str, Any]]) -> Optional[Any]:
        # Direct lookup
        for g in handler_groups.values():
            if ev_key in g and callable(g[ev_key]):
                return g[ev_key]
        # Try without the explicit 'Key' segment
        if '-Key-' in ev_key:
            no_key = ev_key.replace('-Key-', '-')
            for g in handler_groups.values():
                if no_key in g and callable(g[no_key]):
                    return g[no_key]
        else:
            with_key = ev_key.replace('-', '-Key-', 1) if '-' in ev_key else ev_key
            for g in handler_groups.values():
                if with_key in g and callable(g[with_key]):
                    return g[with_key]
        # Try case flip on the trailing character
        parts = ev_key.split('-')
        if len(parts) >= 2 and len(parts[-1]) == 1 and parts[-1].isalpha():
            flip = parts.copy()
            flip[-1] = parts[-1].lower() if parts[-1].isupper() else parts[-1].upper()
            alt_key = '-'.join(flip)
            for g in handler_groups.values():
                if alt_key in g and callable(g[alt_key]):
                    return g[alt_key]
            # Also try the 'no Key' variant
            if '-Key-' in alt_key:
                no_key_alt = alt_key.replace('-Key-', '-')
                for g in handler_groups.values():
                    if no_key_alt in g and callable(g[no_key_alt]):
                        return g[no_key_alt]
        return None

    def _ensure_bracketed_pattern(self, pattern: str) -> str:
        """Make sure pattern has angle brackets for Tkinter bind."""
        if pattern.startswith('<') and pattern.endswith('>'):
            return pattern
        return f'<{pattern}>'

    def _safe_bind(self, widget: tk.Misc, pattern: str, handler: Any) -> bool:
        try:
            # Always ensure a proper Tk pattern and do not clobber existing bindings
            widget.bind(self._ensure_bracketed_pattern(pattern), handler, add='+')
            return True
        except Exception:
            return False

    def _safe_unbind(self, widget: tk.Misc, pattern: str) -> None:
        try:
            widget.unbind(pattern)
        except Exception:
            pass

    def _attach_right_click(self) -> None:
        app = self.app
        text_widget = getattr(app, 'EgonTE', None)
        rc_handler = getattr(app, 'right_click_menu', None)
        if isinstance(text_widget, tk.Misc) and callable(rc_handler):
            try:
                text_widget.bind('<ButtonRelease-3>', rc_handler)
                text_widget.bind('<ButtonRelease>', rc_handler)
            except Exception:
                pass

    def open_windows_control(
        self,
        func: Callable[[], Any],
        *,
        tool_key: Optional[Hashable] = None,
        max_windows: Optional[int] = None,
        skip_warn: bool = False,
        allow_duplicates: Optional[bool] = None,
        bring_to_front: bool = True,
        dialog_title: str = 'EgonTE',
    ) -> None:
        '''
        Control opening of secondary tool windows:

        - If a window for the tool is already open and duplicates are disabled,
          bring it to front instead of opening a new one.
        - If too many windows are open, optionally warn the user before opening.
        - Otherwise, call `func()` to open the new window.

        Parameters:
            func: zero-arg callable that opens the target window (e.g., lambda: self.translate()).
            tool_key: optional logical key for the tool (useful when `func` is a lambda).
                      If not provided, the callable itself is used as the key.
            max_windows: override for the threshold after which a warning is shown;
                         defaults to 5 if not set.
            skip_warn: if True, skip the confirmation dialog even if count exceeds threshold.
            allow_duplicates: override the project's 'avoid duplicates' setting just for this call.
            bring_to_front: if True, deiconify/lift/focus existing window when found.
            dialog_title: title for the confirmation dialog.

        Relies on the app to track:
            - app.func_window: dict[Hashable, tk.Toplevel]
            - app.opened_windows: list[tk.Toplevel]
            - app.adw (BooleanVar/bool): allow duplicates (False => avoid duplicates)
            - app.all_tm_v (BooleanVar/bool): global 'top-most' preference for tool windows
            - app.win_count_warn (BooleanVar/bool): whether to show the warning on count
        '''
        app = self.app

        # Ensure storage exists
        if not isinstance(getattr(app, 'func_window', None), dict):
            app.func_window = {}
        if not isinstance(getattr(app, 'opened_windows', None), list):
            app.opened_windows = []

        func_window: dict = app.func_window
        opened_windows: list = app.opened_windows

        # Normalize settings
        def _get_bool(name: str, default: bool = False) -> bool:
            var = getattr(app, name, None)
            try:
                get = getattr(var, 'get', None)
                return bool(get()) if callable(get) else bool(var) if var is not None else default
            except Exception:
                return default

        project_allow_dupes = _get_bool('adw', False)  # legacy default: avoid duplicates
        project_topmost_all = _get_bool('all_tm_v', False)
        project_warn_on_count = _get_bool('win_count_warn', True)

        eff_allow_dupes = project_allow_dupes if allow_duplicates is None else bool(allow_duplicates)
        threshold = 5 if max_windows is None else int(max_windows)

        # Housekeeping: remove destroyed windows and stale mappings
        self._prune_closed_windows(opened_windows, func_window)

        # Resolve a stable key for this tool
        key: Hashable = tool_key if tool_key is not None else func

        # If a window is already open and duplicates are not allowed, show it
        if not eff_allow_dupes and key in func_window:
            existing = func_window.get(key)
            if isinstance(existing, tk.Misc) and self._is_open(existing):
                if bring_to_front:
                    self._bring_to_front(existing, project_topmost_all)
                return
            # stale entry
            func_window.pop(key, None)

        # Check count and warn if configured
        if not skip_warn and project_warn_on_count:
            try:
                open_count = sum(1 for w in opened_windows if self._is_open(w))
            except Exception:
                open_count = len(opened_windows)
            if open_count > threshold:
                # Local import to avoid global dependency if messagebox is not desired
                try:
                    from tkinter import messagebox
                    ok = messagebox.askyesno(
                        dialog_title,
                        f'You have {open_count} open windows.\nOpen another one?',
                        parent=self._owner_for_dialog(),
                    )
                    if not ok:
                        return
                except Exception:
                    # If dialog cannot be shown, proceed silently
                    pass

        # Open a new window
        try:
            func()
        except Exception:
            # Do not propagate: tools shouldn't crash the host UI
            pass

    # ----- helpers -----

    def _owner_for_dialog(self) -> Optional[tk.Misc]:
        # Try to use the app/root as dialog parent if available
        for attr in ('root', 'master'):
            w = getattr(self.app, attr, None)
            if isinstance(w, tk.Misc):
                return w
        return self.app if isinstance(self.app, tk.Misc) else None

    def _is_open(self, win: Any) -> bool:
        try:
            return bool(win and win.winfo_exists())
        except Exception:
            return False

    def _prune_closed_windows(self, opened_windows: list, func_window: dict) -> None:
        # Clean closed windows from the list
        try:
            opened_windows[:] = [w for w in opened_windows if self._is_open(w)]
        except Exception:
            pass
        # Clean stale func->window mappings
        stale_keys = []
        for k, w in func_window.items():
            if not self._is_open(w) or w not in opened_windows:
                stale_keys.append(k)
        for k in stale_keys:
            func_window.pop(k, None)

    def _bring_to_front(self, window: tk.Misc, topmost_all: bool) -> None:
        try:
            # Ensure visible
            try:
                window.deiconify()
            except Exception:
                pass
            try:
                window.lift()
            except Exception:
                pass
            try:
                window.focus_force()
            except Exception:
                pass
            # Brief topmost pulse to guarantee z-order, then restore global preference
            try:
                window.attributes('-topmost', True)
                window.attributes('-topmost', topmost_all)
            except Exception:
                pass
        except Exception:
            pass
