# find_replace_popup.py
import tkinter as tk
from tkinter import ttk
import re
from collections import Counter

def open_find_replace(app, event=None):
    '''+ the tool is a bit too advanced, so we will probably preserve somehow also the origianl one'''

    '''
    Unified Find & Replace dialog for app.EgonTE.

    Features:
      - Case sensitive, Regex, Wrap, Partial (characters) vs Whole word
      - In selection (stable snapshot), Highlight all
      - Live search, Popular terms (conditional), Auto focus editor
      - Prev/Next, Reset, All (tag all matches), Nothing (clear that tag)
      - Replace current / Replace All (regex backrefs supported)
      - Shortcuts: Enter=Next, Shift+Enter=Prev, Ctrl+Enter=Replace, Ctrl+Shift+Enter=Replace All, Esc=Close
      - Occurrences counter (current/total) between Prev and Next
    '''
    text = app.EgonTE

    # --- State container kept on app ---
    State = getattr(app, '_fr', None)
    if State is None:
        class _FR:
            pattern = ''
            replace = ''
            case = False
            regex = False
            partial = True  # True => "characters sensitive" (partial matches); False => whole word
            wrap = True
            in_selection = False
            highlight_all = True
            matches: list[tuple[str, str]] = []
            current = -1
            # Selection snapshot for "In selection"
            sel_start: str | None = None
            sel_end: str | None = None
            # Popular list cache
            popular: list[str] = []

        app._fr = _FR()
        State = app._fr

    # --- Popup creation (singleton behavior via name) ---
    root = app.make_pop_ups_window(function=app.find_replace, name='find_replace', title='Find & Replace')

    # --- Variables bound to UI ---
    find_var = tk.StringVar(value=State.pattern)
    repl_var = tk.StringVar(value=State.replace)
    case_var = tk.BooleanVar(value=State.case)
    regex_var = tk.BooleanVar(value=State.regex)
    partial_var = tk.BooleanVar(value=State.partial)
    wrap_var = tk.BooleanVar(value=State.wrap)
    in_sel_var = tk.BooleanVar(value=State.in_selection)
    all_var = tk.BooleanVar(value=State.highlight_all)

    # Attempt to use app-wide auto focus var if present
    try:
        auto_focus_var = app.auto_focus_v if isinstance(app.auto_focus_v, tk.BooleanVar) else tk.BooleanVar(False)
    except Exception:
        auto_focus_var = tk.BooleanVar(False)

    # --- Layout ---
    tk.Label(root, text='Find & Replace', font=('Segoe UI', 12, 'underline')).grid(
        row=0, column=0, columnspan=10, pady=(6, 2)
    )
    e_find = tk.Entry(root, textvariable=find_var, width=46)
    e_repl = tk.Entry(root, textvariable=repl_var, width=46)
    e_find.grid(row=1, column=0, columnspan=10, padx=8, pady=(6, 2), sticky='ew')
    e_repl.grid(row=2, column=0, columnspan=10, padx=8, pady=(0, 8), sticky='ew')

    # Options
    tk.Checkbutton(root, text='Case sensitive', variable=case_var).grid(row=3, column=0, sticky='w', padx=8)
    tk.Checkbutton(root, text='Regex', variable=regex_var).grid(row=3, column=1, sticky='w')
    tk.Checkbutton(root, text='Wrap', variable=wrap_var).grid(row=3, column=2, sticky='w')
    tk.Checkbutton(root, text='In selection', variable=in_sel_var).grid(row=3, column=3, sticky='w')
    tk.Checkbutton(root, text='Highlight all', variable=all_var).grid(row=3, column=4, sticky='w')

    # Matching mode and behavior
    tk.Checkbutton(root, text='Partial match (characters)', variable=partial_var).grid(
        row=4, column=0, sticky='w', padx=8
    )
    tk.Checkbutton(root, text='Auto focus editor', variable=auto_focus_var).grid(row=4, column=1, sticky='w')

    # Navigation and actions
    btn_prev = tk.Button(root, text='Prev')
    # Occurrences counter (current/total)
    occ_counter = tk.Label(root, text='0/0', width=8, anchor='center')
    btn_next = tk.Button(root, text='Next')
    btn_all_tag = tk.Button(root, text='All')
    btn_none_tag = tk.Button(root, text='Nothing')
    btn_reset = tk.Button(root, text='Reset')
    btn_replace = tk.Button(root, text='Replace')
    btn_replace_all = tk.Button(root, text='Replace All')

    # Row 5 layout with counter between Prev and Next
    btn_prev.grid(row=5, column=0, padx=4, pady=6, sticky='ew')
    occ_counter.grid(row=5, column=1, padx=2, pady=6, sticky='ew')
    btn_next.grid(row=5, column=2, padx=4, pady=6, sticky='ew')
    btn_all_tag.grid(row=5, column=3, padx=4, pady=6, sticky='ew')
    btn_none_tag.grid(row=5, column=4, padx=4, pady=6, sticky='ew')
    btn_reset.grid(row=5, column=5, padx=4, pady=6, sticky='ew')
    btn_replace.grid(row=6, column=3, padx=4, pady=(0, 8), sticky='ew')
    btn_replace_all.grid(row=6, column=4, padx=4, pady=(0, 8), sticky='ew')

    status = tk.Label(root, text='', anchor='w')
    status.grid(row=7, column=0, columnspan=10, sticky='ew', padx=8, pady=(2, 6))

    # Popular terms (conditionally visible)
    terms_frame = tk.Frame(root)
    terms_list = tk.Listbox(terms_frame, height=3, width=30)
    pt_scroll = ttk.Scrollbar(terms_frame, command=terms_list.yview)
    terms_list.configure(yscrollcommand=pt_scroll.set)
    pt_scroll.pack(side='right', fill='y')
    terms_list.pack(side='left', fill='both', expand=True)

    # Column weights
    for c in range(10):
        root.grid_columnconfigure(c, weight=1)

    # Tooltips if available
    try:
        if hasattr(app, 'ToolTip') and hasattr(app.ToolTip, 'bind_widget'):
            app.ToolTip.bind_widget(btn_prev, balloonmsg='Previous match (Shift+Enter)')
            app.ToolTip.bind_widget(btn_next, balloonmsg='Next match (Enter)')
            app.ToolTip.bind_widget(btn_all_tag, balloonmsg='Tag all matches')
            app.ToolTip.bind_widget(btn_none_tag, balloonmsg="Clear 'All' tag")
            app.ToolTip.bind_widget(btn_reset, balloonmsg='Clear inputs and tags')
            app.ToolTip.bind_widget(btn_replace, balloonmsg='Replace current (Ctrl+Enter)')
            app.ToolTip.bind_widget(btn_replace_all, balloonmsg='Replace all (Ctrl+Shift+Enter)')
    except Exception:
        pass

    # --- Tags ---
    TAG_ALL = 'fr_match_all'  # all matches
    TAG_CUR = 'fr_match_cur'  # current match
    TAG_SEL = 'fr_all_select'  # selection tag for 'All' button
    try:
        text.tag_configure(TAG_ALL, background='#ffe08a')
        text.tag_configure(TAG_CUR, background='#ffd24a')
        text.tag_configure(TAG_SEL, background='#ffe8b3')
    except Exception:
        pass

    def _clear_tags():
        try:
            text.tag_remove(TAG_ALL, '1.0', 'end')
            text.tag_remove(TAG_CUR, '1.0', 'end')
            text.tag_remove(TAG_SEL, '1.0', 'end')
        except Exception:
            pass

    # --- Helpers ---
    def _bounds():
        '''
        Respect a stable selection snapshot if 'In selection' is enabled.
        If no snapshot exists, try to create one from current selection; otherwise full range.
        '''
        if in_sel_var.get():
            # Establish or reuse stable snapshot
            if not State.sel_start or not State.sel_end:
                try:
                    State.sel_start = text.index('sel.first')
                    State.sel_end = text.index('sel.last')
                except Exception:
                    State.sel_start, State.sel_end = '1.0', 'end-1c'
            return State.sel_start, State.sel_end
        # When turning off 'In selection', discard snapshot
        State.sel_start, State.sel_end = None, None
        return '1.0', 'end-1c'

    def _to_tk_pattern(literal: str, partial: bool, allow_regex: bool) -> tuple[str, bool]:
        '''
        Returns (pattern, use_regex_flag) for Tk's Text.search.
        - partial=True: use literal or raw regex as-is
        - partial=False: enforce whole word with \m...\M
        '''
        if allow_regex:
            pat = literal
            if not partial:
                pat = fr'\m(?:{pat})\M'
            return pat, True
        if not partial:
            esc = re.escape(literal)
            return fr'\m{esc}\M', True
        return literal, False

    def _sync_state_from_ui():
        State.pattern = find_var.get()
        State.replace = repl_var.get()
        State.case = case_var.get()
        State.regex = regex_var.get()
        State.partial = partial_var.get()
        State.wrap = wrap_var.get()
        State.in_selection = in_sel_var.get()
        State.highlight_all = all_var.get()

    def _set_status_found(n: int):
        status.config(text=f"{n} match{'es' if n != 1 else ''}")

    def _set_status_not_found():
        status.config(text='No matches')

    def _update_counter():
        total = len(State.matches)
        if total == 0 or State.current < 0:
            occ_counter.configure(text='0/0')
        else:
            occ_counter.configure(text=f'{State.current + 1}/{total}')

    def _set_nav_enabled(enabled: bool):
        try:
            btn_prev.config(state='normal' if enabled else 'disabled')
            btn_next.config(state='normal' if enabled else 'disabled')
            btn_all_tag.config(state='normal' if enabled else 'disabled')
            btn_none_tag.config(state='normal' if enabled else 'disabled')
            btn_replace.config(state='normal' if enabled else 'disabled')
            btn_replace_all.config(state='normal' if enabled else 'disabled')
        except Exception:
            pass

    # --- Core: collect matches and highlight ---
    def _collect_matches():
        _sync_state_from_ui()
        _clear_tags()
        State.matches.clear()
        State.current = -1

        pat = State.pattern
        if not pat:
            status.config(text='Enter text to find')
            _update_counter()
            _set_nav_enabled(False)
            _update_terms()
            return

        start, stop = _bounds()
        pat_tk, use_regex = _to_tk_pattern(pat, State.partial, State.regex)

        options = {}
        if not State.case:
            options['nocase'] = 1
        if use_regex:
            options['regexp'] = 1

        idx = start
        count = tk.IntVar(value=0)
        cap = 40000  # safety cap

        while True:
            pos = text.search(pat_tk, idx, stopindex=stop, count=count, **options)
            if not pos:
                break
            length = count.get()
            if length <= 0:
                # avoid infinite loops on zero-length matches (e.g., empty regex)
                idx = text.index(f'{pos}+1c')
                continue
            end = text.index(f'{pos}+{length}c')
            State.matches.append((pos, end))
            idx = end
            if len(State.matches) >= cap:
                break

        # Highlight all and select first
        if State.highlight_all:
            for s, e in State.matches:
                text.tag_add(TAG_ALL, s, e)

        if State.matches:
            State.current = 0
            _focus_current()
            _set_status_found(len(State.matches))
            _set_nav_enabled(True)
        else:
            _set_status_not_found()
            _set_nav_enabled(False)

        _update_counter()
        _update_terms()

    def _focus_current():
        try:
            text.tag_remove(TAG_CUR, '1.0', 'end')
        except Exception:
            pass
        if 0 <= State.current < len(State.matches):
            s, e = State.matches[State.current]
            try:
                text.tag_add(TAG_CUR, s, e)
                text.see(s)
                text.mark_set('insert', s)
                if auto_focus_var.get():
                    text.focus_set()
            except Exception:
                pass
        _update_counter()

    def _goto(delta: int):
        if not State.matches:
            _collect_matches()
            if not State.matches:
                return
        nxt = State.current + delta
        if 0 <= nxt < len(State.matches):
            State.current = nxt
        else:
            if State.wrap and State.matches:
                State.current = nxt % len(State.matches)
            else:
                return
        _focus_current()

    def _tag_all_matches():
        try:
            text.tag_remove(TAG_SEL, '1.0', 'end')
        except Exception:
            pass
        for s, e in State.matches:
            text.tag_add(TAG_SEL, s, e)

    def _clear_all_tag():
        try:
            text.tag_remove(TAG_SEL, '1.0', 'end')
        except Exception:
            pass

    def _reset():
        find_var.set('')
        repl_var.set('')
        State.matches.clear()
        State.current = -1
        State.sel_start, State.sel_end = None, None
        _clear_tags()
        status.config(text='')
        _update_counter()
        _set_nav_enabled(False)
        _update_terms()

    # --- Replace operations ---
    def _replace_current():
        if not (0 <= State.current < len(State.matches)):
            return
        s, e = State.matches[State.current]
        try:
            frag = text.get(s, e)
        except Exception:
            _collect_matches()
            if not (0 <= State.current < len(State.matches)):
                return
            s, e = State.matches[State.current]
            frag = text.get(s, e)

        repl = State.replace
        if State.regex:
            try:
                flags = 0 if State.case else re.IGNORECASE
                compiled = re.compile(State.pattern, flags)
                new_frag = compiled.sub(repl, frag, count=1)
            except Exception:
                new_frag = repl
        else:
            new_frag = repl

        text.edit_separator()
        text.delete(s, e)
        text.insert(s, new_frag)
        text.edit_separator()

        _collect_matches()

    def _replace_all():
        if not State.matches:
            _collect_matches()
        if not State.matches:
            return

        compiled = None
        if State.regex:
            try:
                flags = 0 if State.case else re.IGNORECASE
                compiled = re.compile(State.pattern, flags)
            except Exception:
                compiled = None

        text.edit_separator()
        for s, e in reversed(State.matches):
            try:
                frag = text.get(s, e)
            except Exception:
                continue
            if compiled:
                new = compiled.sub(State.replace, frag)
            else:
                new = State.replace
            text.delete(s, e)
            text.insert(s, new)
        text.edit_separator()

        _collect_matches()

    # --- Popular terms ---
    def _tokenize_for_popular():
        full = text.get('1.0', 'end-1c')
        tokens = re.findall(r'\w+', full)
        if not case_var.get():
            tokens = [t.lower() for t in tokens]
        return tokens

    def _update_terms():
        try:
            terms_list.delete(0, tk.END)
        except Exception:
            return

        tokens = _tokenize_for_popular()
        if not tokens:
            terms_frame.grid_forget()
            return

        cnt = Counter(tokens)
        popular = [t for (t, _) in cnt.most_common(10)]
        State.popular = popular

        # Respect case option
        entry = find_var.get()
        entry_norm = entry if case_var.get() else entry.lower()
        popular_norm = popular if case_var.get() else [p.lower() for p in popular]

        for t in popular:
            terms_list.insert(tk.END, t)

        # Heuristics
        if not entry:
            show = len(popular) > 2
        else:
            show = len(popular) > 1 and entry_norm not in popular_norm

        if show:
            terms_frame.grid(row=8, column=0, columnspan=10, sticky='ew', padx=8, pady=(0, 6))
        else:
            terms_frame.grid_forget()

    def _fill_from_popular(_evt=None):
        try:
            sel = terms_list.curselection()
            if not sel:
                return
            term = terms_list.get(sel[0])
            find_var.set(term)
            e_find.icursor('end')
            _schedule()
        except Exception:
            pass

    # --- Debounced live search ---
    _pending = {'id': None}

    def _schedule(_evt=None):
        if _pending['id']:
            try:
                root.after_cancel(_pending['id'])
            except Exception:
                pass
        _pending['id'] = root.after(120, _collect_matches)

    # --- Bindings ---
    e_find.bind('<KeyRelease>', _schedule)
    terms_list.bind('<<ListboxSelect>>', _fill_from_popular)

    for var in (case_var, regex_var, partial_var, wrap_var, in_sel_var, all_var, auto_focus_var):
        var.trace_add('write', lambda *args: _schedule())

    btn_prev.configure(command=lambda: _goto(-1))
    btn_next.configure(command=lambda: _goto(+1))
    btn_all_tag.configure(command=_tag_all_matches)
    btn_none_tag.configure(command=_clear_all_tag)
    btn_reset.configure(command=_reset)
    btn_replace.configure(command=_replace_current)
    btn_replace_all.configure(command=_replace_all)

    # Keyboard shortcuts
    def _on_enter(evt=None):
        _goto(+1)
        return 'break'

    def _on_shift_enter(evt=None):
        _goto(-1)
        return 'break'

    def _on_ctrl_enter(evt=None):
        _replace_current()
        return 'break'

    def _on_ctrl_shift_enter(evt=None):
        _replace_all()
        return 'break'

    def _on_escape(evt=None):
        try:
            root.destroy()
        except Exception:
            pass
        return 'break'

    root.bind('<Return>', _on_enter)
    root.bind('<Shift-Return>', _on_shift_enter)
    root.bind('<Control-Return>', _on_ctrl_enter)
    root.bind('<Control-Shift-Return>', _on_ctrl_shift_enter)
    root.bind('<Escape>', _on_escape)

    # Seed from current selection if find is empty
    try:
        if not find_var.get() and text.tag_ranges('sel'):
            sel = text.get('sel.first', 'sel.last')
            if sel:
                find_var.set(sel)
    except Exception:
        pass

    # Initial compute
    _collect_matches()
    e_find.focus_set()
