import tkinter as tk
from tkinter import ttk
import time
import re
import unicodedata


def open_sort(app):
    '''
    Sort text with rich options in a compact, tabbed window.

    Tabs:
    - Input: source text box (+ editor helpers)
    - Options: clearly grouped sort settings
    - Preview: single "Result" panel with live update and status

    Features:
    - Granularity: characters, words, or lines
    - Mode: ascending / descending
    - Numeric-aware (lines): sort as numbers when possible
    - Alnum-only (chars): only letters/digits; preserve punctuation/whitespace positions
    - Sort selection only (if selection exists)
    - Deduplicate (stable) for words/lines
    - Case-insensitive and accent-insensitive comparisons
    - Natural sort: numeric chunks sorted as numbers (file2 < file10)
    - Lines: preserve original line endings (CRLF/LF)
    - Multi-key sort by columns with per-column direction: e.g., '2:desc,1:asc'
    - Ignore indentation when sorting lines (compare using lstrip)
    - Empty-lines placement: none/top/bottom
    - Undo (Ctrl+Z) inside the popup
    - Use/Replace editor selection helpers

    Shortcuts:
    - Enter: Sort
    - Ctrl+Enter / Cmd+Enter: Insert sorted content into editor
    - Ctrl+C: Copy sorted content (selection-aware)
    - Ctrl+L: Clear input
    - Ctrl+Z: Undo (within popup)
    - Esc/Ctrl+W: Close
    '''

    # -------- window and theme (use standardized app builders) --------
    sort_root = app.make_pop_ups_window(
        function=lambda: None,
        custom_title='Sort',
        parent=getattr(app, 'root', None),
        name='sort_popup',
        topmost=False,
        modal=False,
    )
    try:
        app.open_windows_control(sort_root)
    except Exception:
        pass
    try:
        if getattr(app, 'limit_w_s', None) and app.limit_w_s.get():
            sort_root.resizable(False, False)
    except Exception:
        pass

    text_color = getattr(app, 'dynamic_text', 'black')
    background_color = getattr(app, 'dynamic_bg', sort_root.cget('bg'))
    button_background_color = getattr(app, 'dynamic_button', background_color)
    overall_color = getattr(app, 'dynamic_overall', 'SystemButtonFace')

    # -------- variables --------
    sort_descending_variable = tk.BooleanVar(value=False)
    sort_granularity_variable = tk.StringVar(value='chars')  # 'chars' | 'words' | 'lines'
    numeric_aware_variable = tk.BooleanVar(value=True)
    alnum_only_chars_variable = tk.BooleanVar(value=True)
    selection_only_variable = tk.BooleanVar(value=False)
    live_preview_variable = tk.BooleanVar(value=True)
    deduplicate_variable = tk.BooleanVar(value=False)
    case_insensitive_variable = tk.BooleanVar(value=False)
    accent_insensitive_variable = tk.BooleanVar(value=False)
    natural_sort_variable = tk.BooleanVar(value=False)
    delimiter_variable = tk.StringVar(value=',')
    columns_variable = tk.StringVar(value='')
    ignore_indentation_variable = tk.BooleanVar(value=False)  # sort by content without leading indentation
    empty_lines_position_variable = tk.StringVar(value='none')  # 'none' | 'top' | 'bottom'

    # -------- title --------
    title_label = tk.Label(sort_root, text='Sort text', font='arial 12 underline', fg=text_color, bg=background_color)
    title_label.pack(fill='x', anchor='w', padx=8, pady=(6, 4))

    # -------- notebook (compact layout) --------
    notebook = ttk.Notebook(sort_root)
    notebook.pack(fill='both', expand=True, padx=8, pady=(0, 4))

    tab_input = tk.Frame(notebook, bg=background_color)
    tab_options = tk.Frame(notebook, bg=background_color)
    tab_preview = tk.Frame(notebook, bg=background_color)
    notebook.add(tab_input, text='Input')
    notebook.add(tab_options, text='Options')
    notebook.add(tab_preview, text='Preview')

    # ===== Tab: Input =====
    input_frame, input_text, _ys = app.make_rich_textbox(tab_input, size=[50, 15])
    input_frame.pack(fill='both', expand=True)

    editor_buttons_frame = tk.Frame(tab_input, bg=background_color)
    editor_buttons_frame.pack(fill='x', pady=(6, 0))
    use_editor_button = tk.Button(
        editor_buttons_frame, text='Use editor selection', bg=button_background_color, fg=text_color
    )
    replace_editor_button = tk.Button(
        editor_buttons_frame, text='Replace editor selection', bg=button_background_color, fg=text_color
    )
    use_editor_button.pack(side='left', padx=(0, 6))
    replace_editor_button.pack(side='left')

    # ===== Tab: Options =====
    # Group 1: Basic
    lf_basic = tk.LabelFrame(tab_options, text='Basic', fg=text_color, bg=background_color)
    lf_basic.pack(fill='x', pady=(8, 4))

    mode_button = tk.Button(lf_basic, text='Mode: ascending', bg=button_background_color, fg=text_color)

    def update_mode_button_label():
        mode_button.config(text=f"Mode: {'descending' if sort_descending_variable.get() else 'ascending'}")
        refresh_action_status()

    def toggle_sort_mode():
        sort_descending_variable.set(not sort_descending_variable.get())
        update_mode_button_label()

    mode_button.config(command=toggle_sort_mode)
    mode_button.pack(side='left', padx=(6, 12), pady=6)

    granularity_frame = tk.Frame(lf_basic, bg=background_color)
    granularity_frame.pack(side='left', padx=(0, 6), pady=6)
    tk.Label(granularity_frame, text='Granularity:', fg=text_color, bg=background_color).pack(side='left', padx=(0, 6))
    characters_radio = tk.Radiobutton(
        granularity_frame, text='Characters', value='chars',
        variable=sort_granularity_variable, fg=text_color, bg=background_color, selectcolor=background_color
    )
    words_radio = tk.Radiobutton(
        granularity_frame, text='Words', value='words',
        variable=sort_granularity_variable, fg=text_color, bg=background_color, selectcolor=background_color
    )
    lines_radio = tk.Radiobutton(
        granularity_frame, text='Lines', value='lines',
        variable=sort_granularity_variable, fg=text_color, bg=background_color, selectcolor=background_color
    )
    characters_radio.pack(side='left')
    words_radio.pack(side='left')
    lines_radio.pack(side='left')

    # Group 2: Comparison
    lf_compare = tk.LabelFrame(tab_options, text='Comparison', fg=text_color, bg=background_color)
    lf_compare.pack(fill='x', pady=4)
    case_insensitive_check = tk.Checkbutton(
        lf_compare, text='Case-insensitive', variable=case_insensitive_variable,
        fg=text_color, bg=background_color, selectcolor=background_color
    )
    accent_insensitive_check = tk.Checkbutton(
        lf_compare, text='Accent-insensitive', variable=accent_insensitive_variable,
        fg=text_color, bg=background_color, selectcolor=background_color
    )
    natural_sort_check = tk.Checkbutton(
        lf_compare, text='Natural sort', variable=natural_sort_variable,
        fg=text_color, bg=background_color, selectcolor=background_color
    )
    case_insensitive_check.pack(side='left', padx=8, pady=2)
    accent_insensitive_check.pack(side='left', padx=8, pady=2)
    natural_sort_check.pack(side='left', padx=8, pady=2)

    # Group 3: Scope & Character options
    lf_scope = tk.LabelFrame(tab_options, text='Scope & Character options', fg=text_color, bg=background_color)
    lf_scope.pack(fill='x', pady=4)
    selection_only_check = tk.Checkbutton(
        lf_scope, text='Sort selection only', variable=selection_only_variable,
        fg=text_color, bg=background_color, selectcolor=background_color
    )
    deduplicate_check = tk.Checkbutton(
        lf_scope, text='Deduplicate (stable)', variable=deduplicate_variable,
        fg=text_color, bg=background_color, selectcolor=background_color
    )
    alnum_only_check = tk.Checkbutton(
        lf_scope, text='Alnum-only (chars)', variable=alnum_only_chars_variable,
        fg=text_color, bg=background_color, selectcolor=background_color
    )
    selection_only_check.pack(side='left', padx=8, pady=2)
    deduplicate_check.pack(side='left', padx=8, pady=2)
    alnum_only_check.pack(side='left', padx=8, pady=2)

    # Group 4: Lines options
    lf_lines = tk.LabelFrame(tab_options, text='Lines options', fg=text_color, bg=background_color)
    lf_lines.pack(fill='x', pady=4)
    numeric_aware_check = tk.Checkbutton(
        lf_lines, text='Numeric-aware', variable=numeric_aware_variable,
        fg=text_color, bg=background_color, selectcolor=background_color
    )
    ignore_indent_check = tk.Checkbutton(
        lf_lines, text='Ignore indentation', variable=ignore_indentation_variable,
        fg=text_color, bg=background_color, selectcolor=background_color
    )
    empty_lines_label = tk.Label(lf_lines, text='Empty lines:', fg=text_color, bg=background_color)
    empty_lines_selector = ttk.Combobox(
        lf_lines, values=['none', 'top', 'bottom'], width=8, state='readonly',
        textvariable=empty_lines_position_variable
    )
    numeric_aware_check.pack(side='left', padx=8, pady=2)
    ignore_indent_check.pack(side='left', padx=8, pady=2)
    empty_lines_label.pack(side='left', padx=(12, 4), pady=2)
    empty_lines_selector.pack(side='left', padx=(0, 8), pady=2)

    # Group 5: Columns multi-key
    lf_columns = tk.LabelFrame(tab_options, text='Columns (per line)', fg=text_color, bg=background_color)
    lf_columns.pack(fill='x', pady=4)
    delimiter_label = tk.Label(lf_columns, text='Delimiter:', fg=text_color, bg=background_color)
    delimiter_entry = tk.Entry(lf_columns, textvariable=delimiter_variable, width=6)
    columns_label = tk.Label(lf_columns, text='Columns (e.g., 2:desc,1:asc):', fg=text_color, bg=background_color)
    columns_entry = tk.Entry(lf_columns, textvariable=columns_variable, width=24)
    delimiter_label.pack(side='left', padx=(8, 4), pady=2)
    delimiter_entry.pack(side='left', padx=(0, 12), pady=2)
    columns_label.pack(side='left', padx=(4, 4), pady=2)
    columns_entry.pack(side='left', padx=(0, 8), pady=2)
    # Quick delimiter helpers
    quick_delims = tk.Frame(lf_columns, bg=background_color)
    quick_delims.pack(side='left', padx=(8, 0), pady=2)
    def _set_delim(val): delimiter_variable.set(val)
    btn_tab = tk.Button(quick_delims, text='Tab', bg=button_background_color, fg=text_color, command=lambda: _set_delim('\\t'))
    btn_sp = tk.Button(quick_delims, text='Space', bg=button_background_color, fg=text_color, command=lambda: _set_delim(' '))
    btn_cm = tk.Button(quick_delims, text='Comma', bg=button_background_color, fg=text_color, command=lambda: _set_delim(','))
    btn_tab.pack(side='left', padx=(0, 4))
    btn_sp.pack(side='left', padx=(0, 4))
    btn_cm.pack(side='left')

    # Live preview toggle
    live_preview_toggle = tk.Checkbutton(
        tab_options, text='Live preview', variable=live_preview_variable,
        fg=text_color, bg=background_color, selectcolor=background_color
    )
    live_preview_toggle.pack(anchor='w', pady=(6, 4), padx=4)

    # ===== Tab: Preview =====
    preview_top_frame = tk.Frame(tab_preview, bg=background_color)
    preview_top_frame.pack(fill='both', expand=True)

    # Single result viewer (the input tab already shows "before")
    result_label = tk.Label(preview_top_frame, text='Result', fg=text_color, bg=background_color)
    result_label.pack(anchor='w', padx=(0, 2), pady=(4, 0))
    after_text = tk.Text(preview_top_frame, height=14, wrap='word', state='disabled')
    after_text.pack(fill='both', expand=True, padx=0, pady=(0, 0))

    # Status bar (in preview tab to keep the main window compact)
    status_frame = tk.Frame(tab_preview, bg=overall_color)
    status_frame.pack(fill='x', padx=0, pady=(4, 6))
    status_text_variable = tk.StringVar(value='')
    status_label = tk.Label(status_frame, textvariable=status_text_variable, fg=text_color, bg=overall_color, anchor='w')
    status_label.pack(fill='x', padx=6)

    # ===== Action bar (improved layout) =====
    buttons_frame = tk.Frame(sort_root, bg=background_color)
    buttons_frame.pack(fill='x', padx=8, pady=(0, 8))

    # Use grid with three clusters and a status summary at the right
    buttons_frame.grid_columnconfigure(0, weight=0)
    buttons_frame.grid_columnconfigure(1, weight=0)
    buttons_frame.grid_columnconfigure(2, weight=1)  # spacer
    buttons_frame.grid_columnconfigure(3, weight=0)

    left_cluster = tk.Frame(buttons_frame, bg=background_color)
    mid_cluster = tk.Frame(buttons_frame, bg=background_color)
    right_cluster = tk.Frame(buttons_frame, bg=background_color)

    left_cluster.grid(row=0, column=0, sticky='w')
    mid_cluster.grid(row=0, column=1, sticky='w', padx=(10, 0))
    right_cluster.grid(row=0, column=3, sticky='e')

    sort_button = tk.Button(left_cluster, text='Sort |(Enter)', bg=button_background_color, fg=text_color)
    preview_button = tk.Button(left_cluster, text='Preview', bg=button_background_color, fg=text_color)
    apply_result_button = tk.Button(left_cluster, text='Apply to Input', bg=button_background_color, fg=text_color)

    insert_button = tk.Button(mid_cluster, text='Insert |(Ctrl+Enter)', bg=button_background_color, fg=text_color)
    copy_button = tk.Button(mid_cluster, text='Copy |(Ctrl+C)', bg=button_background_color, fg=text_color)
    clear_button = tk.Button(mid_cluster, text='Clear |(Ctrl+L)', bg=button_background_color, fg=text_color)
    undo_button = tk.Button(mid_cluster, text='Undo |(Ctrl+Z)', bg=button_background_color, fg=text_color)
    close_button = tk.Button(mid_cluster, text='Close |(Esc)', bg=button_background_color, fg=text_color)

    # Action status on the right
    action_status_text = tk.StringVar(value='')
    action_status_label = tk.Label(right_cluster, textvariable=action_status_text, fg=text_color, bg=background_color, anchor='e')

    # Pack cluster buttons
    for b in (sort_button, preview_button, apply_result_button):
        b.pack(side='left', padx=(0, 6))
    for b in (insert_button, copy_button, clear_button, undo_button, close_button):
        b.pack(side='left', padx=(0, 6))
    action_status_label.pack(side='right', padx=(6, 0))

    def refresh_action_status():
        try:
            mode = 'DESC' if sort_descending_variable.get() else 'ASC'
            gran = sort_granularity_variable.get().capitalize()
            extra = []
            if selection_only_variable.get():
                extra.append('Selection')
            if deduplicate_variable.get():
                extra.append('Unique')
            joined = (' • '.join(extra)) if extra else ''
            action_status_text.set(f'{mode} • {gran}' + (f' • {joined}' if joined else ''))
        except Exception:
            pass

    # -------- tooltips via app helpers --------
    tooltip_items = [
        (mode_button, 'Toggle ascending/descending'),
        (characters_radio, 'Sort characters (see alnum-only option)'),
        (words_radio, 'Sort by words (space-separated tokens)'),
        (lines_radio, 'Sort by lines (preserves line endings)'),
        (live_preview_toggle, 'Toggle live preview and stats updates'),
        (use_editor_button, 'Load current editor selection (or all) into Input'),
        (replace_editor_button, 'Replace editor selection with the sorted result of it'),
        (sort_button, 'Sort the content (Enter)'),
        (preview_button, 'Recompute the Result preview'),
        (apply_result_button, 'Replace the Input text with the current Result'),
        (insert_button, 'Insert the current sorted content into the editor (Ctrl+Enter)'),
        (copy_button, 'Copy the current sorted selection or the whole sorted content (Ctrl+C)'),
        (clear_button, 'Clear the input (Ctrl+L)'),
        (undo_button, 'Undo last sort (Ctrl+Z) within this popup'),
        (close_button, 'Close this tool (Esc)'),
        (delimiter_entry, 'Delimiter for columns (default: comma). Use \\t for tab'),
        (columns_entry, 'Columns order; supports per-column direction like "2:desc,1:asc"'),
        (empty_lines_selector, 'Where to keep empty lines relative to sorted lines'),
        (btn_tab, 'Set delimiter to Tab (\\t)'),
        (btn_sp, 'Set delimiter to Space'),
        (btn_cm, 'Set delimiter to Comma (,)'),
    ]
    try:
        app.place_toolt(tooltip_items)
    except Exception:
        pass

    # -------- logic helpers --------
    digits_regex = re.compile(r'\d+')
    nonspace_word_regex = re.compile(r'\S+')

    undo_snapshot = {'text': None, 'selection': None}

    def try_cast_float(number_string):
        try:
            return float(number_string)
        except Exception:
            return None

    def normalize_for_compare(text_value):
        normalized = text_value
        if case_insensitive_variable.get():
            normalized = normalized.casefold()
        if accent_insensitive_variable.get():
            normalized = ''.join(
                char for char in unicodedata.normalize('NFKD', normalized)
                if not unicodedata.combining(char)
            )
        return normalized

    def natural_key_parts(text_value):
        text_chunks = digits_regex.split(text_value)
        number_chunks = digits_regex.findall(text_value)
        key_parts = []
        for index_position in range(max(len(text_chunks), len(number_chunks))):
            if index_position < len(text_chunks):
                text_part = text_chunks[index_position]
                if text_part != '':
                    key_parts.append(text_part)
            if index_position < len(number_chunks):
                number_part = number_chunks[index_position]
                try:
                    key_parts.append(int(number_part))
                except Exception:
                    key_parts.append(number_part)
        return key_parts

    def compare_key_for_string(text_value):
        base_value = normalize_for_compare(text_value)
        if natural_sort_variable.get():
            return natural_key_parts(base_value)
        return base_value

    def stable_deduplicate(sequence_values):
        seen_keys = set()
        output_values = []
        for sequence_item in sequence_values:
            compare_key = compare_key_for_string(sequence_item)
            if compare_key in seen_keys:
                continue
            seen_keys.add(compare_key)
            output_values.append(sequence_item)
        return output_values

    # -------- words --------
    def extract_words_from_text(text_value):
        return nonspace_word_regex.findall(text_value)

    def sort_by_words(text_value):
        words_list = extract_words_from_text(text_value)
        if not words_list:
            return text_value
        if deduplicate_variable.get():
            words_list = stable_deduplicate(words_list)
        sorted_words = sorted(words_list, key=compare_key_for_string, reverse=sort_descending_variable.get())
        return ' '.join(sorted_words)

    # -------- chars --------
    def sort_characters_stable_alnum(text_value):
        alnum_characters = [character for character in text_value if character.isalnum()]
        alnum_characters.sort(key=compare_key_for_string, reverse=sort_descending_variable.get())
        alnum_iter = iter(alnum_characters)
        output_characters = []
        for character in text_value:
            if character.isalnum():
                output_characters.append(next(alnum_iter, ''))
            else:
                output_characters.append(character)
        return ''.join(output_characters)

    def sort_characters_all(text_value):
        characters_list = list(text_value)
        characters_list.sort(key=compare_key_for_string, reverse=sort_descending_variable.get())
        return ''.join(characters_list)

    # -------- lines helpers --------
    def split_lines_with_endings(text_value):
        return text_value.splitlines(keepends=True)

    def split_content_and_ending(line_with_ending):
        if line_with_ending.endswith('\r\n'):
            return line_with_ending[:-2], '\r\n'
        if line_with_ending.endswith('\n') or line_with_ending.endswith('\r'):
            return line_with_ending[:-1], line_with_ending[-1]
        return line_with_ending, ''

    def parse_columns_configuration():
        '''
        Parse columns string. Supports:
          - '2,1' (all columns in a single global direction)
          - '2:desc,1:asc' (per-column directions)
        Returns: [{'index': int, 'direction': 'asc'|'desc'}]
        '''
        specs = []
        raw_columns = (columns_variable.get() or '').strip()
        if not raw_columns:
            return specs
        for column_piece in raw_columns.split(','):
            cleaned = column_piece.strip()
            if not cleaned:
                continue
            parts = cleaned.split(':', 1)
            index_text = parts[0].strip()
            direction_text = parts[1].strip().lower() if len(parts) > 1 else None
            if not index_text.isdigit():
                continue
            index_one_based = int(index_text)
            if index_one_based < 1:
                continue
            direction_value = 'asc'
            if direction_text in ('asc', 'desc'):
                direction_value = direction_text
            specs.append({'index': index_one_based - 1, 'direction': direction_value})
        return specs

    def resolve_column_delimiter():
        raw = delimiter_variable.get()
        if raw == '\\t' or raw == '\t':
            return '\t'
        if raw == '\\s' or raw == ' ':
            return ' '
        return raw if raw != '' else ','

    # -------- lines main --------
    def sort_by_lines(text_value):
        raw_lines_with_endings = split_lines_with_endings(text_value)
        if not raw_lines_with_endings:
            return text_value

        content_and_endings_all = [split_content_and_ending(line_item) for line_item in raw_lines_with_endings]
        empty_line_positions = [idx for idx, (c, _e) in enumerate(content_and_endings_all) if c.strip() == '']
        non_empty_lines = [(c, e) for (c, e) in content_and_endings_all if c.strip() != '']
        empty_lines = [(c, e) for (c, e) in content_and_endings_all if c.strip() == '']

        # deduplicate on non-empty lines if needed
        if deduplicate_variable.get():
            seen_line_keys = set()
            deduped_pairs = []
            for content_text, line_ending in non_empty_lines:
                key_text = content_text.lstrip() if ignore_indentation_variable.get() else content_text
                compare_key = compare_key_for_string(key_text)
                if compare_key in seen_line_keys:
                    continue
                seen_line_keys.add(compare_key)
                deduped_pairs.append((content_text, line_ending))
            non_empty_lines = deduped_pairs

        # columns multi-key (stable passes)
        columns_specs = parse_columns_configuration()
        if columns_specs:
            delimiter_value = resolve_column_delimiter()

            def column_key(content_text, column_index):
                fields_list = content_text.split(delimiter_value) if delimiter_value else [content_text]
                value = fields_list[column_index] if column_index < len(fields_list) else ''
                if ignore_indentation_variable.get():
                    value = value.lstrip()
                return compare_key_for_string(value)

            for spec in reversed(columns_specs):
                idx = spec['index']
                reverse_flag = (spec['direction'] == 'desc')
                non_empty_lines.sort(key=lambda pair: column_key(pair[0], idx), reverse=reverse_flag)

            only_indexes = all(s['direction'] == 'asc' for s in columns_specs)
            if only_indexes and sort_descending_variable.get():
                non_empty_lines.reverse()

        else:
            # numeric-aware
            contents_only = [c for c, _ in non_empty_lines]
            use_numeric_sort = False
            if numeric_aware_variable.get():
                all_numeric_lines = True
                for content_text in contents_only:
                    stripped = content_text.strip()
                    if stripped == '':
                        continue
                    if try_cast_float(stripped) is None:
                        all_numeric_lines = False
                        break
                use_numeric_sort = all_numeric_lines

            if use_numeric_sort:
                decorated_list = []
                for original_index, (content_text, line_ending) in enumerate(non_empty_lines):
                    stripped = content_text.strip()
                    numeric_key = try_cast_float(stripped) if stripped != '' else None
                    decorated_list.append((numeric_key, original_index, content_text, line_ending))
                decorated_list.sort(
                    key=lambda tup: (tup[0] is None, tup[0] if tup[0] is not None else 0.0),
                    reverse=sort_descending_variable.get()
                )
                non_empty_lines = [(content_text, line_ending) for _k, _i, content_text, line_ending in decorated_list]
            else:
                key_func = (lambda pair: compare_key_for_string(pair[0].lstrip())) if ignore_indentation_variable.get() \
                    else (lambda pair: compare_key_for_string(pair[0]))
                non_empty_lines.sort(key=key_func, reverse=sort_descending_variable.get())

        # reassemble according to empty-lines placement
        placement = empty_lines_position_variable.get()
        if placement == 'top':
            final_pairs = empty_lines + non_empty_lines
        elif placement == 'bottom':
            final_pairs = non_empty_lines + empty_lines
        else:
            total_count = len(content_and_endings_all)
            final_pairs = [None] * total_count
            for pos in empty_line_positions:
                final_pairs[pos] = empty_lines.pop(0) if empty_lines else ('', '')
            fill_iter = iter(non_empty_lines)
            for i in range(total_count):
                if final_pairs[i] is None:
                    final_pairs[i] = next(fill_iter, ('', ''))

        return ''.join(content_text + line_ending for content_text, line_ending in final_pairs)

    def sort_text_content(text_value):
        granularity_value = sort_granularity_variable.get()
        if granularity_value == 'lines':
            return sort_by_lines(text_value)
        if granularity_value == 'words':
            return sort_by_words(text_value)
        if alnum_only_chars_variable.get():
            return sort_characters_stable_alnum(text_value)
        return sort_characters_all(text_value)

    # -------- selection helpers --------
    def get_selection_range_in_text():
        try:
            return input_text.index('sel.first'), input_text.index('sel.last')
        except Exception:
            return None, None

    def get_target_text_and_range():
        if selection_only_variable.get():
            selection_start, selection_end = get_selection_range_in_text()
            if selection_start and selection_end:
                return input_text.get(selection_start, selection_end), selection_start, selection_end
            return '', None, None
        return input_text.get('1.0', 'end-1c'), '1.0', 'end-1c'

    def replace_text_range(range_start, range_end, new_text_value):
        if range_start is None or range_end is None:
            return
        input_text.delete(range_start, range_end)
        input_text.insert(range_start, new_text_value)

    # -------- preview and status --------
    def set_text_value(widget_text, value):
        widget_text.configure(state='normal')
        widget_text.delete('1.0', 'end')
        if value:
            widget_text.insert('1.0', value)
        widget_text.configure(state='disabled')

    def update_preview_text(event=None):
        raw_value, range_start, range_end = get_target_text_and_range()
        if range_start is None:
            set_text_value(after_text, '')
            return
        set_text_value(after_text, sort_text_content(raw_value))

    def get_safe_selection_range_for_status():
        try:
            return input_text.index('sel.first'), input_text.index('sel.last')
        except Exception:
            return None, None

    def update_status_bar(last_operation_ms=None):
        content_value = input_text.get('1.0', 'end-1c')
        characters_count = len(content_value)
        words_count = len(extract_words_from_text(content_value)) if content_value else 0
        lines_count = (content_value.count('\n') + (0 if content_value.endswith('\n') else 1)) if content_value else 0
        selection_start, selection_end = get_safe_selection_range_for_status()
        selection_info_text = f' | Sel: {selection_start}..{selection_end}' if selection_start and selection_end else ''
        timing_text = f' | Last: {last_operation_ms:.1f} ms' if last_operation_ms is not None else ''
        try:
            after_text.configure(state='normal')
            result_str = after_text.get('1.0', 'end-1c')
            after_text.configure(state='disabled')
            result_chars = len(result_str)
            result_lines = result_str.count('\n') + (0 if not result_str or result_str.endswith('\n') else 1)
            result_info_text = f' | Result: {result_chars} chars, {result_lines} lines'
        except Exception:
            result_info_text = ''
        status_text_variable.set(
            f'Input: {characters_count} chars, {words_count} words, {lines_count} lines{selection_info_text}{result_info_text}{timing_text}'
        )

    # -------- undo management --------
    def snapshot_before_mutation():
        text_before = input_text.get('1.0', 'end-1c')
        try:
            selection_tuple = (input_text.index('sel.first'), input_text.index('sel.last'))
        except Exception:
            selection_tuple = None
        undo_snapshot['text'] = text_before
        undo_snapshot['selection'] = selection_tuple

    def restore_undo_snapshot():
        previous_text = undo_snapshot.get('text')
        if previous_text is None:
            return
        input_text.delete('1.0', 'end')
        input_text.insert('1.0', previous_text)
        input_text.tag_remove('sel', '1.0', 'end')
        selection_tuple = undo_snapshot.get('selection')
        if selection_tuple:
            try:
                input_text.tag_add('sel', selection_tuple[0], selection_tuple[1])
            except Exception:
                pass
        update_preview_text()
        update_status_bar()

    # -------- actions --------
    def perform_sort():
        raw_value, range_start, range_end = get_target_text_and_range()
        if range_start is None:
            return
        snapshot_before_mutation()
        start_time = time.perf_counter()
        sorted_value = sort_text_content(raw_value)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        replace_text_range(range_start, range_end, sorted_value)
        if live_preview_variable.get():
            update_preview_text()
        update_status_bar(last_operation_ms=elapsed_ms)
        try:
            notebook.select(tab_preview)
        except Exception:
            pass

    def current_sorted_text():
        sel_text, start, end = get_target_text_and_range()
        if start is None:
            return ''
        return sort_text_content(sel_text)

    def insert_result_into_editor():
        try:
            content_value = current_sorted_text() or sort_text_content(input_text.get('1.0', 'end-1c'))
            if content_value and hasattr(app, 'EgonTE') and hasattr(app, 'get_pos'):
                app.EgonTE.insert(app.get_pos(), content_value)
        except Exception:
            pass

    def copy_result_to_clipboard():
        try:
            sorted_payload = current_sorted_text() or sort_text_content(input_text.get('1.0', 'end-1c'))
            if not sorted_payload:
                return
            sort_root.clipboard_clear()
            sort_root.clipboard_append(sorted_payload)
        except Exception:
            pass

    def clear_input_text():
        input_text.delete('1.0', 'end')
        if live_preview_variable.get():
            update_preview_text()
        update_status_bar()

    def undo_last_sort():
        restore_undo_snapshot()

    def use_editor_selection():
        try:
            editor = getattr(app, 'EgonTE', None)
            if editor is None:
                return
            try:
                selected = editor.get('sel.first', 'sel.last')
            except Exception:
                selected = editor.get('1.0', 'end-1c')
            input_text.delete('1.0', 'end')
            if selected:
                input_text.insert('1.0', selected)
            if live_preview_variable.get():
                update_preview_text()
            update_status_bar()
            try:
                notebook.select(tab_input)
            except Exception:
                pass
        except Exception:
            pass

    def replace_editor_selection():
        try:
            editor = getattr(app, 'EgonTE', None)
            if editor is None:
                return
            try:
                sel_first, sel_last = editor.index('sel.first'), editor.index('sel.last')
            except Exception:
                return
            to_sort = editor.get(sel_first, sel_last)
            if not to_sort:
                return
            sorted_value = sort_text_content(to_sort)
            editor.delete(sel_first, sel_last)
            editor.insert(sel_first, sorted_value)
            editor.see(sel_first)
            editor.focus_set()
        except Exception:
            pass

    # Apply Result -> Input
    def apply_result_to_input():
        try:
            after_text.configure(state='normal')
            result_value = after_text.get('1.0', 'end-1c')
            after_text.configure(state='disabled')
            if not result_value:
                raw_value, start_idx, end_idx = get_target_text_and_range()
                if start_idx is None:
                    return
                result_value = sort_text_content(raw_value)
            target_text, start_idx, end_idx = get_target_text_and_range()
            if start_idx is None:
                return
            snapshot_before_mutation()
            replace_text_range(start_idx, end_idx, result_value)
            update_preview_text()
            update_status_bar()
        except Exception:
            pass

    # -------- cleanup on destroy --------
    def on_window_destroy(event=None):
        try:
            app.unbind_group('sort_popup')
        except Exception:
            pass

    sort_root.bind('<Destroy>', on_window_destroy, add='+')

    # -------- wire buttons --------
    sort_button.config(command=perform_sort)
    insert_button.config(command=insert_result_into_editor)
    copy_button.config(command=copy_result_to_clipboard)
    clear_button.config(command=clear_input_text)
    undo_button.config(command=undo_last_sort)
    preview_button.config(command=update_preview_text)
    apply_result_button.config(command=apply_result_to_input)
    close_button.config(command=lambda: sort_root.destroy())
    update_mode_button_label()
    refresh_action_status()

    # -------- context menu for input_text --------
    context_menu = tk.Menu(sort_root, tearoff=False, bg=background_color, fg=text_color)

    def update_context_menu_states():
        has_any_text = bool(input_text.get('1.0', 'end-1c'))
        try:
            _ = input_text.get('sel.first', 'sel.last')
            has_selection = True
        except Exception:
            has_selection = False
        context_menu.entryconfig('Cut', state=('normal' if has_selection else 'disabled'))
        context_menu.entryconfig('Copy', state=('normal' if has_selection or has_any_text else 'disabled'))
        context_menu.entryconfig('Paste', state='normal')
        context_menu.entryconfig('Select All', state=('normal' if has_any_text else 'disabled'))
        context_menu.entryconfig('Clear', state=('normal' if has_any_text else 'disabled'))

    def show_context_menu(mouse_event):
        update_context_menu_states()
        try:
            context_menu.tk_popup(mouse_event.x_root, mouse_event.y_root)
        finally:
            try:
                context_menu.grab_release()
            except Exception:
                pass

    context_menu.add_command(label='Cut', command=lambda: input_text.event_generate('<<Cut>>'))
    context_menu.add_command(label='Copy', command=copy_result_to_clipboard)
    context_menu.add_command(label='Paste', command=lambda: input_text.event_generate('<<Paste>>'))
    context_menu.add_separator()
    context_menu.add_command(
        label='Select All',
        command=lambda: (input_text.tag_add('sel', '1.0', 'end-1c'), input_text.mark_set('insert', '1.0'))
    )
    context_menu.add_command(label='Clear', command=clear_input_text)

    input_text.bind('<Button-3>', show_context_menu)
    input_text.bind('<Control-Button-1>', show_context_menu)

    # -------- shortcuts (local to this popup) --------
    def handle_return_key(event=None):
        perform_sort()
        return 'break'

    def handle_ctrl_return_key(event=None):
        insert_result_into_editor()
        return 'break'

    def handle_ctrl_c_key(event=None):
        copy_result_to_clipboard()
        return 'break'

    def handle_ctrl_l_key(event=None):
        clear_input_text()
        return 'break'

    def handle_ctrl_z_key(event=None):
        undo_last_sort()
        return 'break'

    def handle_escape_key(event=None):
        try:
            sort_root.destroy()
        except Exception:
            pass
        return 'break'

    try:
        sort_root.bind('<Escape>', handle_escape_key, add='+')
        sort_root.bind('<Control-w>', handle_escape_key, add='+')
        sort_root.bind('<Control-Return>', handle_ctrl_return_key, add='+')
        sort_root.bind('<Command-Return>', handle_ctrl_return_key, add='+')
        sort_root.bind('<Control-l>', handle_ctrl_l_key, add='+')
        sort_root.bind('<Control-z>', handle_ctrl_z_key, add='+')
        input_text.bind('<Return>', handle_return_key, add='+')
        input_text.bind('<Control-c>', handle_ctrl_c_key, add='+')
    except Exception:
        pass

    # -------- live preview + status (debounced) --------
    preview_after_id = {'handle': None}

    def schedule_preview_and_status():
        if preview_after_id['handle'] is not None:
            try:
                sort_root.after_cancel(preview_after_id['handle'])
            except Exception:
                pass
        preview_after_id['handle'] = sort_root.after(120, lambda: (update_preview_text(), update_status_bar()))

    def update_preview_and_status_if_enabled(event=None):
        if live_preview_variable.get():
            schedule_preview_and_status()
        else:
            update_status_bar()

    input_text.bind('<KeyRelease>', update_preview_and_status_if_enabled)

    # Reactive updates for UI status label and preview
    def on_any_option_change(*_):
        refresh_action_status()
        update_preview_and_status_if_enabled()

    reactive_variables = (
        sort_granularity_variable, numeric_aware_variable, alnum_only_chars_variable, selection_only_variable,
        sort_descending_variable, live_preview_variable, deduplicate_variable, case_insensitive_variable,
        accent_insensitive_variable, natural_sort_variable, ignore_indentation_variable, empty_lines_position_variable
    )
    for tracked_var in reactive_variables:
        tracked_var.trace_add('write', on_any_option_change)

    delimiter_variable.trace_add('write', lambda *args: update_preview_and_status_if_enabled())
    columns_variable.trace_add('write', lambda *args: update_preview_and_status_if_enabled())

    # -------- initial paint --------
    update_preview_text()
    update_status_bar()
