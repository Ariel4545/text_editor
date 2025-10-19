from __future__ import annotations

import os
import re
import tempfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox, END, BOTH, RIGHT, Y, DISABLED, HORIZONTAL, filedialog, W, E, EW, LEFT, INSERT, VERTICAL, NORMAL, NONE, Canvas, NW
from typing import Any, Dict, Optional, List

try:
    from PIL import Image, ImageTk, ImageGrab, ImageOps
except ImportError:
    ImageTk = None
    Image = None
    ImageGrab = None
    ImageOps = None

try:
    from wordcloud import WordCloud
except ImportError:
    WordCloud = None

from services.nlp_service import (
    ensure_nlp_pipeline, to_tsv, to_csv, wrap_text, normalize_key, analyze,
    NLP_FUNCTION_ITEMS, NLP_FUNCTION_MAP
)


# --------------------------------------------------------------------------
# Single entry point: call open_nlp(self[, preset_function])
# --------------------------------------------------------------------------
def open_nlp(app, preset_function: Optional[str] = None) -> None:
    '''
    Open the NLP popup (UI + logic), designed as a drop-in tool.
    Refinements include a more compact UI, consolidated action buttons,
    and improved quick access for recent functions.
    '''
    nlp_root = app.make_pop_ups_window(open_nlp, name='nlp_tool', title='Natural Language Processor', geometry='1250x700')

    # Add a custom style for more compact buttons in the left pane
    style = ttk.Style()
    style.configure('Compact.TButton', padding=(3, 3))
    style.configure('Placeholder.TLabel', foreground='grey')

    # --- Main layout frames ---
    top_frame = ttk.Frame(nlp_root)
    top_frame.pack(fill=BOTH, expand=True, padx=6, pady=(6, 0))
    bottom_frame = ttk.Frame(nlp_root)
    bottom_frame.pack(fill=tk.X, padx=6, pady=6)

    main_paned_window = ttk.PanedWindow(top_frame, orient=HORIZONTAL)
    main_paned_window.pack(fill=BOTH, expand=True)

    controls_main_frame = ttk.Frame(main_paned_window)
    main_paned_window.add(controls_main_frame, weight=1)
    controls_main_frame.columnconfigure(0, weight=1)

    # --- Right side: Input and Output Panes ---
    right_pane = ttk.PanedWindow(main_paned_window, orient=VERTICAL)
    main_paned_window.add(right_pane, weight=5)

    # --- Input Area ---
    input_frame = ttk.LabelFrame(right_pane, text='Input Text')
    right_pane.add(input_frame, weight=2)

    if hasattr(app, 'make_rich_textbox'):
        _, input_text_widget, _ = app.make_rich_textbox(
            parent_container=input_frame,
            wrap=tk.WORD,
            show_xscroll=False,
            auto_hide_scrollbars=False
        )
    else:
        input_text_widget = tk.Text(input_frame, wrap=tk.WORD)
        input_text_widget.pack(fill=BOTH, expand=True)

    # --- Output Area ---
    output_main_frame = ttk.LabelFrame(right_pane, text='Output')
    right_pane.add(output_main_frame, weight=3)

    # --- State Initialization ---
    if not hasattr(app, '_nlp_recent_functions'):
        app._nlp_recent_functions = []
    if not hasattr(app, '_nlp_favorite_functions'):
        app._nlp_favorite_functions = []

    _cancel_event = threading.Event()

    # --- Quick Access and Function Selection ---
    function_frame = ttk.LabelFrame(controls_main_frame, text='Analysis Function', padding=6)
    function_frame.grid(row=0, column=0, sticky=EW, pady=(0, 6))

    search_var = tk.StringVar()
    search_entry = ttk.Entry(function_frame, textvariable=search_var)
    search_entry.pack(fill=tk.X, pady=(0, 4))

    available_functions = list(NLP_FUNCTION_ITEMS) if NLP_FUNCTION_ITEMS else []
    function_combobox = ttk.Combobox(function_frame, values=available_functions, state='readonly')
    if available_functions:
        last_function = getattr(app, '_nlp_last_function', available_functions[0])
        function_combobox.set(last_function if last_function in available_functions else available_functions[0])
    function_combobox.pack(fill=tk.X)

    quick_access_view_var = tk.StringVar(value='recent')
    quick_access_frame = ttk.LabelFrame(controls_main_frame, text='Quick Access', padding=6)
    quick_access_frame.grid(row=1, column=0, sticky=EW, pady=(0, 6))

    toggle_frame = ttk.Frame(quick_access_frame)
    toggle_frame.pack(fill=tk.X, pady=(0, 5))

    quick_access_list_frame = ttk.Frame(quick_access_frame)
    quick_access_list_frame.pack(fill=tk.X)

    def populate_quick_access():
        for widget in quick_access_list_frame.winfo_children():
            widget.destroy()

        view_mode = quick_access_view_var.get()
        functions_to_show = []
        MAX_QUICK_ITEMS = 3  # Max items to show for a compact view

        if view_mode == 'recent':
            functions_to_show = app._nlp_recent_functions[:MAX_QUICK_ITEMS]
        elif view_mode == 'favorites':
            functions_to_show = app._nlp_favorite_functions[-MAX_QUICK_ITEMS:]  # Show most recent favorites

        if not functions_to_show:
            no_items_label = ttk.Label(quick_access_list_frame, text=f'No {view_mode} functions.', style='Placeholder.TLabel')
            no_items_label.pack(anchor=W, padx=2, pady=2)
            return

        # A more compact, horizontal layout
        for func in functions_to_show:
            btn_frame = ttk.Frame(quick_access_list_frame)
            btn_frame.pack(side=LEFT, anchor=W, padx=2, pady=1)

            is_fav = func in app._nlp_favorite_functions
            star_text = '★' if is_fav else '☆'
            fav_button = ttk.Button(btn_frame, text=star_text, command=lambda f=func: toggle_favorite(f), width=2, style='Compact.TButton')
            fav_button.pack(side=LEFT)

            func_button = ttk.Button(btn_frame, text=func, command=lambda f=func: function_combobox.set(f), style='Compact.TButton')
            func_button.pack(side=LEFT)

    recent_button = ttk.Radiobutton(toggle_frame, text='Recent', variable=quick_access_view_var, value='recent', command=populate_quick_access)
    recent_button.pack(side=LEFT, expand=True)
    favorites_button = ttk.Radiobutton(toggle_frame, text='Favorites', variable=quick_access_view_var, value='favorites', command=populate_quick_access)
    favorites_button.pack(side=LEFT, expand=True)

    def update_recent_functions(func_name):
        if func_name in app._nlp_recent_functions:
            app._nlp_recent_functions.remove(func_name)
        app._nlp_recent_functions.insert(0, func_name)
        app._nlp_recent_functions = app._nlp_recent_functions[:5]
        populate_quick_access()

    def toggle_favorite(func_name):
        MAX_FAVORITES = 5  # Max items to store
        if func_name in app._nlp_favorite_functions:
            app._nlp_favorite_functions.remove(func_name)
        else:
            app._nlp_favorite_functions.append(func_name)
            if len(app._nlp_favorite_functions) > MAX_FAVORITES:
                app._nlp_favorite_functions.pop(0)  # Remove the oldest favorite
        populate_quick_access()

    def filter_functions(*args):
        search_term = search_var.get().lower()
        filtered = [f for f in available_functions if search_term in f.lower()] if search_term else available_functions
        function_combobox['values'] = filtered
        if filtered:
            function_combobox.set(filtered[0])

    search_var.trace('w', filter_functions)

    # --- Options & Execution ---_exec_frame, text='Options & Execution', padding=6)
    options_exec_frame = ttk.LabelFrame(controls_main_frame, text='Options & Execution', padding=6)
    options_exec_frame.grid(row=2, column=0, sticky=EW, pady=(0, 6))
    options_exec_frame.columnconfigure(1, weight=1)

    # Define parameter widgets
    topn_variable = tk.IntVar(value=10)
    topn_label = ttk.Label(options_exec_frame, text='Top N:')
    topn_spinbox = ttk.Spinbox(options_exec_frame, from_=1, to=100, width=5, textvariable=topn_variable)

    ngram_min_var = tk.IntVar(value=2)
    ngram_min_label = ttk.Label(options_exec_frame, text='N-gram Min:')
    ngram_min_spinbox = ttk.Spinbox(options_exec_frame, from_=1, to=10, width=5, textvariable=ngram_min_var)

    ngram_max_var = tk.IntVar(value=3)
    ngram_max_label = ttk.Label(options_exec_frame, text='N-gram Max:')
    ngram_max_spinbox = ttk.Spinbox(options_exec_frame, from_=1, to=10, width=5, textvariable=ngram_max_var)

    summary_ratio_var = tk.DoubleVar(value=0.2)
    summary_ratio_label = ttk.Label(options_exec_frame, text='Sum. Ratio:')
    summary_ratio_scale = ttk.Scale(options_exec_frame, from_=0.05, to=1.0, orient=HORIZONTAL, variable=summary_ratio_var)

    query_label = ttk.Label(options_exec_frame, text='Query:')
    query_var = tk.StringVar()
    query_entry = ttk.Entry(options_exec_frame, textvariable=query_var, style='Placeholder.TEntry')

    placeholder_callbacks = {}
    def setup_placeholder(entry, placeholder_text):
        style = ttk.Style()
        style.configure('Placeholder.TEntry', foreground='grey')

        def on_focus_in(event):
            if entry.get() == placeholder_text:
                entry.delete(0, 'end')
                entry.config(style='TEntry')

        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder_text)
                entry.config(style='Placeholder.TEntry')

        entry.insert(0, placeholder_text)
        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)
        placeholder_callbacks[entry] = on_focus_out
        return on_focus_out

    reset_query_placeholder = setup_placeholder(query_entry, 'search term')

    value_label = ttk.Label(options_exec_frame, text='Cutoff:')
    value_var = tk.IntVar(value=80)
    value_spinbox = ttk.Spinbox(options_exec_frame, from_=0, to=100, width=5, textvariable=value_var)
    text_label = ttk.Label(options_exec_frame, text='Text 2:')
    text_var = tk.StringVar()
    text_entry = ttk.Entry(options_exec_frame, textvariable=text_var, style='Placeholder.TEntry')
    reset_text_placeholder = setup_placeholder(text_entry, '(optional) second text for comparison')

    # Define cleaning widgets
    cleaning_frame1 = ttk.Frame(options_exec_frame)
    clean_lowercase_var = tk.BooleanVar(value=False)
    clean_lowercase_check = ttk.Checkbutton(cleaning_frame1, text='Lower', variable=clean_lowercase_var)
    clean_lowercase_check.pack(side=LEFT)
    clean_punct_var = tk.BooleanVar(value=False)
    clean_punct_check = ttk.Checkbutton(cleaning_frame1, text='Punct', variable=clean_punct_var)
    clean_punct_check.pack(side=LEFT, padx=4)

    cleaning_frame2 = ttk.Frame(options_exec_frame)
    clean_stopwords_var = tk.BooleanVar(value=False)
    clean_stopwords_check = ttk.Checkbutton(cleaning_frame2, text='Stopwords', variable=clean_stopwords_var)
    clean_stopwords_check.pack(side=LEFT)
    lemmatize_var = tk.BooleanVar(value=False)
    lemmatize_check = ttk.Checkbutton(cleaning_frame2, text='Lemmatize', variable=lemmatize_var)
    lemmatize_check.pack(side=LEFT, padx=4)

    # Define execution widgets
    time_limit_variable = tk.DoubleVar(value=getattr(app, 'nlp_time_limit_s', 5.0))
    time_limit_label = ttk.Label(options_exec_frame, text='Time (s):')
    time_limit_spinbox = ttk.Spinbox(options_exec_frame, from_=0.5, to=30.0, increment=0.5, width=5, textvariable=time_limit_variable)
    auto_run_var = tk.BooleanVar(value=False)
    auto_run_check = ttk.Checkbutton(options_exec_frame, text='Auto-run', variable=auto_run_var)
    run_button = ttk.Button(options_exec_frame, text='Run Analysis')
    progress_bar = ttk.Progressbar(options_exec_frame, orient='horizontal', mode='indeterminate')

    # --- More Balanced 2-Column Layout ---
    topn_label.grid(row=0, column=0, sticky=W, pady=1)
    topn_spinbox.grid(row=0, column=1, sticky=EW, padx=2)

    value_label.grid(row=1, column=0, sticky=W, pady=1)
    value_spinbox.grid(row=1, column=1, sticky=EW, padx=2)

    ngram_min_label.grid(row=2, column=0, sticky=W, pady=1)
    ngram_min_spinbox.grid(row=2, column=1, sticky=EW, padx=2)

    ngram_max_label.grid(row=3, column=0, sticky=W, pady=1)
    ngram_max_spinbox.grid(row=3, column=1, sticky=EW, padx=2)

    summary_ratio_label.grid(row=4, column=0, sticky=W, pady=1)
    summary_ratio_scale.grid(row=4, column=1, sticky=EW, padx=2)

    query_label.grid(row=5, column=0, sticky=W, pady=1)
    query_entry.grid(row=5, column=1, sticky=EW, padx=2)

    text_label.grid(row=6, column=0, sticky=W, pady=1)
    text_entry.grid(row=6, column=1, sticky=EW, padx=2)

    cleaning_label = ttk.Label(options_exec_frame, text='Cleaning:')
    cleaning_label.grid(row=7, column=0, sticky=W, pady=(6, 2))
    cleaning_frame1.grid(row=7, column=1, sticky=W, pady=(6, 0))
    cleaning_frame2.grid(row=8, column=1, sticky=W, pady=(0, 2))

    ttk.Separator(options_exec_frame, orient=HORIZONTAL).grid(row=9, column=0, columnspan=2, sticky=EW, pady=4)

    time_limit_label.grid(row=10, column=0, sticky=W)
    time_limit_spinbox.grid(row=10, column=1, sticky=EW, padx=2)

    auto_run_check.grid(row=11, column=0, columnspan=2, sticky=W)

    run_button.grid(row=12, column=0, columnspan=2, sticky=EW, pady=(4, 0))
    progress_bar.grid(row=13, column=0, columnspan=2, sticky=EW, pady=4)

    # --- Actions Frame ---
    actions_frame = ttk.LabelFrame(controls_main_frame, text='Actions', padding=6)
    actions_frame.grid(row=3, column=0, sticky=EW, pady=(0, 6))
    actions_frame.columnconfigure((0, 1), weight=1)

    # --- Input Status Bar ---
    input_status_frame = ttk.Frame(controls_main_frame)
    input_status_frame.grid(row=4, column=0, sticky=EW, pady=(6, 0))
    input_status_label = ttk.Label(input_status_frame, text='Input: ...')
    input_status_label.pack(side=LEFT, padx=5)

    # --- Output Status Bar (in left panel) ---
    output_status_frame = ttk.Frame(controls_main_frame)
    output_status_frame.grid(row=5, column=0, sticky=EW, pady=(2, 0))
    output_status_label = ttk.Label(output_status_frame, text='Output: ...')
    output_status_label.pack(side=LEFT, padx=5)

    _auto_run_after_id = None
    def schedule_run(*args):
        nonlocal _auto_run_after_id
        if _auto_run_after_id:
            nlp_root.after_cancel(_auto_run_after_id)
        if auto_run_var.get():
            _auto_run_after_id = nlp_root.after(500, run_now)

    def enforce_min_pane_size(event=None):
        try:
            # One-time calculation for the right pane's minimum width.
            if last_image_data.get('min_actions_width') == 0:
                image_actions = output_widgets.get('image_actions_frame')
                if image_actions and image_actions.winfo_exists():
                    image_actions.update_idletasks()
                    width = image_actions.winfo_reqwidth()
                    if width > 1:
                        last_image_data['min_actions_width'] = width

            # The left pane's width can change, so we recalculate it each time.
            controls_main_frame.update_idletasks()
            min_left = controls_main_frame.winfo_reqwidth() + 20  # Padding

            # Use the calculated width, or a fallback. Add padding.
            min_right = (last_image_data.get('min_actions_width') or 450) + 40

            total_width = main_paned_window.winfo_width()

            # Don't enforce if the window is too small to accommodate both minimums
            if total_width < min_left + min_right:
                return

            sash_pos = main_paned_window.sashpos(0)

            if sash_pos < min_left:
                main_paned_window.sashpos(0, min_left)
            elif (total_width - sash_pos) < min_right:
                main_paned_window.sashpos(0, total_width - min_right)
        except (tk.TclError, KeyError):
            # Handles cases where widgets might not exist yet during initialization
            pass

    def on_function_change(event=None):
        schedule_run()
        selected_function = function_combobox.get()
        normalized_key = normalize_key(selected_function)

        param_keywords = {
            'top_n': {'top', 'nouns', 'verbs', 'adjectives', 'adverbs', 'entities', 'term', 'frequency'},
            'ngrams': {'ngrams', 'collocations'},
            'summary': {'summarize'},
            'query': {'fuzzy', 'regex', 'concordance', 'dep_path'},
            'value': {'fuzzy'},
            'text2': {'similarity'}
        }

        def check_usage(param_type):
            return any(keyword in normalized_key for keyword in param_keywords.get(param_type, set()))

        def toggle_widget_visibility(widgets, show):
            for widget in widgets:
                if show:
                    widget.grid()
                else:
                    widget.grid_remove()

        toggle_widget_visibility([topn_label, topn_spinbox], check_usage('top_n'))
        toggle_widget_visibility([ngram_min_label, ngram_min_spinbox, ngram_max_label, ngram_max_spinbox], check_usage('ngrams'))
        toggle_widget_visibility([summary_ratio_label, summary_ratio_scale], check_usage('summary'))

        show_query = check_usage('query')
        toggle_widget_visibility([query_label, query_entry], show_query)
        if show_query:
            if 'fuzzy' in normalized_key:
                query_label.config(text='Fuzzy Query:')
            elif 'regex' in normalized_key:
                query_label.config(text='Regex Pattern:')
            elif 'concordance' in normalized_key:
                query_label.config(text='Keyword:')
            elif 'dep_path' in normalized_key:
                query_label.config(text='Words (2):')

        show_value = check_usage('value')
        toggle_widget_visibility([value_label, value_spinbox], show_value)
        if show_value:
             value_label.config(text='Cutoff:')

        show_text2 = check_usage('text2')
        toggle_widget_visibility([text_label, text_entry], show_text2)
        if show_text2:
            text_label.config(text='Text 2:')

        # Schedule a call to enforce pane size after the UI updates
        nlp_root.after(10, enforce_min_pane_size)

    function_combobox.bind('<<ComboboxSelected>>', on_function_change)

    # --- Output Area (Tabbed) ---
    output_notebook = ttk.Notebook(output_main_frame)
    output_notebook.pack(fill=BOTH, expand=True, pady=(0, 6))

    last_table_data: Dict[str, Any] = {'columns': None, 'rows': None, 'all_item_ids': [], 'sort_by': [], 'sort_rev': {}}
    last_text_data: Dict[str, str] = {'display': ''}
    last_image_data: Dict[str, Any] = {'image': None, 'photo': None, 'zoom_factor': 1.0, 'rotation': 0, 'min_actions_width': 0}
    output_widgets: Dict[str, tk.Widget] = {}
    image_effect_vars = {'invert': tk.BooleanVar(value=False), 'grayscale': tk.BooleanVar(value=False)}
    show_checkerboard_var = tk.BooleanVar(value=True)
    table_filter_var = tk.StringVar()
    table_filter_case_sensitive = tk.BooleanVar(value=False)
    table_color_palette = tk.StringVar(value='Blues')

    # --- Image Canvas Functions ---
    def get_processed_image():
        original_image = last_image_data.get('image')
        if not original_image: return None

        processed_image = original_image
        if image_effect_vars['grayscale'].get():
            if processed_image.mode != 'L':
                processed_image = ImageOps.grayscale(processed_image).convert('RGB')

        if image_effect_vars['invert'].get():
            if processed_image.mode == 'RGBA':
                r, g, b, a = processed_image.split()
                rgb_image = Image.merge('RGB', (r, g, b))
                inverted_rgb = ImageOps.invert(rgb_image)
                r_inv, g_inv, b_inv = inverted_rgb.split()
                processed_image = Image.merge('RGBA', (r_inv, g_inv, b_inv, a))
            else:
                processed_image = ImageOps.invert(processed_image.convert('RGB'))

        return processed_image.rotate(last_image_data['rotation'], expand=True)

    def _update_image_display(zoom_factor_multiplier=None, fit_to_screen=False, rotate_angle_delta=0, set_zoom=None, set_rotation=None, toggle_effect=None):
        canvas = output_widgets.get('image_canvas')
        original_image = last_image_data.get('image')
        if not canvas or not original_image: return

        if toggle_effect:
            image_effect_vars[toggle_effect].set(not image_effect_vars[toggle_effect].get())

        if set_rotation is not None:
            last_image_data['rotation'] = set_rotation
        elif rotate_angle_delta:
            last_image_data['rotation'] = (last_image_data.get('rotation', 0) + rotate_angle_delta) % 360

        processed_image = get_processed_image()
        if not processed_image: return

        if set_zoom is not None:
            last_image_data['zoom_factor'] = set_zoom
        elif fit_to_screen:
            canvas_w, canvas_h = canvas.winfo_width(), canvas.winfo_height()
            img_w, img_h = processed_image.size
            if img_w > 0 and img_h > 0:
                last_image_data['zoom_factor'] = min(canvas_w / img_w, canvas_h / img_h)
        elif zoom_factor_multiplier:
            last_image_data['zoom_factor'] *= zoom_factor_multiplier

        new_w = int(processed_image.width * last_image_data['zoom_factor'])
        new_h = int(processed_image.height * last_image_data['zoom_factor'])

        if new_w < 1 or new_h < 1:
            if zoom_factor_multiplier: last_image_data['zoom_factor'] /= zoom_factor_multiplier
            return

        resized_img = processed_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(resized_img)
        last_image_data['photo'] = photo

        canvas.delete('all')
        if show_checkerboard_var.get():
            create_checkerboard(canvas, new_w if new_w > 2000 else 2000, new_h if new_h > 2000 else 2000)
        else:
            canvas.config(bg='white')

        canvas.create_image(0, 0, anchor=NW, image=photo)
        canvas.config(scrollregion=canvas.bbox(tk.ALL))

        dims = f'{original_image.width}x{original_image.height}'
        output_widgets['image_info_label'].config(text=f"Dims: {dims} | Zoom: {last_image_data['zoom_factor']:.0%}, Rot: {last_image_data['rotation']}°")

    def zoom_image(event):
        _update_image_display(zoom_factor_multiplier=1.1 if event.delta > 0 else 0.9)

    def rotate_image(angle):
        _update_image_display(rotate_angle_delta=angle)

    def reset_image_view():
        image_effect_vars['invert'].set(False)
        image_effect_vars['grayscale'].set(False)
        _update_image_display(set_zoom=1.0, set_rotation=0)

    def start_pan(event):
        canvas = output_widgets.get('image_canvas')
        if canvas: canvas.scan_mark(event.x, event.y)

    def do_pan(event):
        canvas = output_widgets.get('image_canvas')
        if canvas: canvas.scan_dragto(event.x, event.y, gain=1)

    def open_image_externally():
        processed_image = get_processed_image()
        if not processed_image: return
        try:
            fd, path = tempfile.mkstemp(suffix='.png')
            os.close(fd)
            processed_image.save(path)
            os.startfile(path)
        except Exception as e:
            messagebox.showerror('Error', f'Could not open image externally: {e}')

    def show_image_context_menu(event):
        canvas = output_widgets.get('image_canvas')
        if not canvas or not last_image_data.get('image'): return
        context_menu = tk.Menu(canvas, tearoff=0)

        file_menu = tk.Menu(context_menu, tearoff=0)
        file_menu.add_command(label='Open Externally...', command=open_image_externally)
        file_menu.add_command(label='Save Image As...', command=lambda: save_to_file('image'))
        file_menu.add_command(label='Copy Image', command=lambda: copy_output_to_clipboard('image'))
        context_menu.add_cascade(label='File', menu=file_menu)
        context_menu.add_separator()

        zoom_menu = tk.Menu(context_menu, tearoff=0)
        zoom_menu.add_command(label='Zoom In', command=lambda: _update_image_display(zoom_factor_multiplier=1.2))
        zoom_menu.add_command(label='Zoom Out', command=lambda: _update_image_display(zoom_factor_multiplier=0.8))
        zoom_menu.add_command(label='Zoom to Fit', command=lambda: _update_image_display(fit_to_screen=True))
        zoom_menu.add_command(label='Reset Zoom (100%)', command=lambda: _update_image_display(set_zoom=1.0))
        context_menu.add_cascade(label='Zoom', menu=zoom_menu)

        rotate_menu = tk.Menu(context_menu, tearoff=0)
        rotate_menu.add_command(label='Rotate Left', command=lambda: rotate_image(-90))
        rotate_menu.add_command(label='Rotate Right', command=lambda: rotate_image(90))
        context_menu.add_cascade(label='Rotate', menu=rotate_menu)

        effects_menu = tk.Menu(context_menu, tearoff=0)
        effects_menu.add_checkbutton(label='Invert Colors', variable=image_effect_vars['invert'], command=lambda: _update_image_display(toggle_effect='invert'))
        effects_menu.add_checkbutton(label='Grayscale', variable=image_effect_vars['grayscale'], command=lambda: _update_image_display(toggle_effect='grayscale'))
        effects_menu.add_checkbutton(label='Show Background', variable=show_checkerboard_var, command=_update_image_display)
        context_menu.add_cascade(label='Effects', menu=effects_menu)

        context_menu.add_separator()
        context_menu.add_command(label='Reset View', command=reset_image_view)
        context_menu.tk_popup(event.x_root, event.y_root)

    def create_checkerboard(canvas, width, height):
        canvas.config(bg='#f0f0f0')
        color1 = '#f0f0f0'
        color2 = '#dcdcdc'
        for y in range(0, height, 20):
            for x in range(0, width, 20):
                if (x // 20 + y // 20) % 2 == 0:
                    canvas.create_rectangle(x, y, x + 20, y + 20, fill=color1, outline='')
                else:
                    canvas.create_rectangle(x, y, x + 20, y + 20, fill=color2, outline='')

    def setup_output_tabs():
        # --- Image Tab Setup ---
        image_frame = ttk.Frame(output_notebook)
        output_notebook.add(image_frame, text='Image')
        output_widgets['image_frame'] = image_frame

        image_canvas_frame = ttk.Frame(image_frame)
        image_canvas_frame.pack(fill=BOTH, expand=True)

        v_scroll = ttk.Scrollbar(image_canvas_frame, orient=VERTICAL)
        h_scroll = ttk.Scrollbar(image_canvas_frame, orient=HORIZONTAL)
        v_scroll.pack(side=RIGHT, fill=Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        canvas = Canvas(image_canvas_frame, highlightthickness=0, yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        canvas.pack(fill=BOTH, expand=True)
        v_scroll.config(command=canvas.yview)
        h_scroll.config(command=canvas.xview)
        output_widgets['image_canvas'] = canvas
        output_widgets['image_canvas_no_img_text'] = canvas.create_text(1000, 1000, text='No image generated yet.', justify=tk.CENTER, anchor=tk.CENTER)

        actions_frame = ttk.Frame(image_frame)
        actions_frame.pack(fill=tk.X, pady=2)
        output_widgets['image_actions_frame'] = actions_frame

        output_widgets['image_info_label'] = ttk.Label(actions_frame, text='')
        output_widgets['image_info_label'].pack(side=tk.LEFT, padx=5)

        open_btn = ttk.Button(actions_frame, text='Open', command=open_image_externally)
        save_btn = ttk.Button(actions_frame, text='Save', command=lambda: save_to_file('image'))
        copy_btn = ttk.Button(actions_frame, text='Copy', command=lambda: copy_output_to_clipboard('image'))
        bg_btn = ttk.Button(actions_frame, text='BG', width=3, command=lambda: (show_checkerboard_var.set(not show_checkerboard_var.get()), _update_image_display()))
        grayscale_btn = ttk.Button(actions_frame, text='Grayscale', command=lambda: _update_image_display(toggle_effect='grayscale'))
        invert_btn = ttk.Button(actions_frame, text='Invert', command=lambda: _update_image_display(toggle_effect='invert'))
        rot_r_btn = ttk.Button(actions_frame, text='Rotate R', command=lambda: rotate_image(90))
        rot_l_btn = ttk.Button(actions_frame, text='Rotate L', command=lambda: rotate_image(-90))
        reset_btn = ttk.Button(actions_frame, text='Reset View', command=reset_image_view)
        fit_btn = ttk.Button(actions_frame, text='Zoom to Fit', command=lambda: _update_image_display(fit_to_screen=True))
        zoom_100_btn = ttk.Button(actions_frame, text='100%', command=lambda: _update_image_display(set_zoom=1.0))
        zoom_out_btn = ttk.Button(actions_frame, text='-', width=2, command=lambda: _update_image_display(zoom_factor_multiplier=0.8))
        zoom_in_btn = ttk.Button(actions_frame, text='+', width=2, command=lambda: _update_image_display(zoom_factor_multiplier=1.2))

        open_btn.pack(side=tk.RIGHT, padx=5)
        save_btn.pack(side=tk.RIGHT)
        copy_btn.pack(side=tk.RIGHT, padx=(5,0))
        ttk.Separator(actions_frame, orient=VERTICAL).pack(side=tk.RIGHT, fill=Y, padx=5)
        bg_btn.pack(side=tk.RIGHT, padx=5)
        grayscale_btn.pack(side=tk.RIGHT)
        invert_btn.pack(side=tk.RIGHT, padx=(5,0))
        ttk.Separator(actions_frame, orient=VERTICAL).pack(side=tk.RIGHT, fill=Y, padx=5)
        rot_r_btn.pack(side=tk.RIGHT, padx=5)
        rot_l_btn.pack(side=tk.RIGHT)
        ttk.Separator(actions_frame, orient=VERTICAL).pack(side=tk.RIGHT, fill=Y, padx=5)
        reset_btn.pack(side=tk.RIGHT, padx=5)
        fit_btn.pack(side=tk.RIGHT)
        zoom_100_btn.pack(side=tk.RIGHT, padx=(5,0))
        zoom_out_btn.pack(side=tk.RIGHT)
        zoom_in_btn.pack(side=tk.RIGHT)

        canvas.bind('<Control-MouseWheel>', zoom_image)
        canvas.bind('<ButtonPress-2>', start_pan)
        canvas.bind('<B2-Motion>', do_pan)
        canvas.bind('<Button-3>', show_image_context_menu)

        output_widgets['image_buttons'] = [open_btn, save_btn, copy_btn, bg_btn, grayscale_btn, invert_btn, rot_r_btn, rot_l_btn, reset_btn, fit_btn, zoom_100_btn, zoom_out_btn, zoom_in_btn]

        # --- Table Tab Setup ---
        table_frame = ttk.Frame(output_notebook)
        output_notebook.add(table_frame, text='Table')
        output_widgets['table_frame'] = table_frame

        toolbar = ttk.Frame(table_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=(2, 2))
        ttk.Label(toolbar, text='Filter:').pack(side=tk.LEFT, padx=(5, 2))
        filter_entry = ttk.Entry(toolbar, textvariable=table_filter_var)
        filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        case_btn = ttk.Checkbutton(toolbar, text='Case', variable=table_filter_case_sensitive, command=filter_table_rows)
        case_btn.pack(side=tk.LEFT, padx=(5,5))
        output_widgets['table_case_btn'] = case_btn

        palette_menu_btn = ttk.Menubutton(toolbar, text='Palette')
        palette_menu_btn.pack(side=tk.LEFT)
        palette_menu = tk.Menu(palette_menu_btn, tearoff=0)
        palette_menu_btn['menu'] = palette_menu

        palettes = {
            'Blues': ['#E1F5FE', '#B3E5FC', '#81D4FA', '#4FC3F7', '#29B6F6', '#03A9F4', '#039BE5', '#0288D1'],
            'Greens': ['#E8F5E9', '#C8E6C9', '#A5D6A7', '#81C784', '#66BB6A', '#4CAF50', '#43A047', '#388E3C'],
            'Reds': ['#FFEBEE', '#FFCDD2', '#EF9A9A', '#E57373', '#EF5350', '#F44336', '#E53935', '#D32F2F']
        }
        for p_name in list(palettes.keys()):
            palette_menu.add_radiobutton(label=p_name, variable=table_color_palette, value=p_name, command=lambda: update_ui(None, (last_table_data['columns'], last_table_data['rows']), None))
        palette_menu.add_separator()
        palette_menu.add_radiobutton(label='Disabled', variable=table_color_palette, value='Disabled', command=lambda: update_ui(None, (last_table_data['columns'], last_table_data['rows']), None))

        wc_button = ttk.Button(toolbar, text='Word Cloud', command=generate_word_cloud_from_table)
        wc_button.pack(side=tk.RIGHT, padx=(5, 5))
        output_widgets['wc_button'] = wc_button

        output_widgets['table_filter_entry'] = filter_entry

        tree_frame = ttk.Frame(table_frame)
        tree_frame.pack(fill=BOTH, expand=True)
        tree = ttk.Treeview(tree_frame, show='headings')
        output_widgets['tree'] = tree
        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=RIGHT, fill=Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        tree.pack(fill=BOTH, expand=True)
        output_widgets['table_no_data_label'] = ttk.Label(tree_frame, text='No table data generated yet.')

        tree.bind('<Button-3>', show_table_context_menu)

        # --- Text Tab Setup ---
        text_frame = ttk.Frame(output_notebook)
        output_notebook.add(text_frame, text='Text')
        output_widgets['text_frame'] = text_frame
        text_options_frame = ttk.Frame(text_frame)
        text_options_frame.pack(fill=tk.X, padx=5, pady=(5,0))
        wrap_text_var = tk.BooleanVar(value=True)
        wrap_check = ttk.Checkbutton(text_options_frame, text='Wrap Text', variable=wrap_text_var)
        wrap_check.pack(side=tk.RIGHT)
        output_widgets['wrap_check'] = wrap_check

        if hasattr(app, 'make_rich_textbox'):
            _, text_widget, _ = app.make_rich_textbox(parent_container=text_frame, wrap='word', show_xscroll=False, auto_hide_scrollbars=False)
            scratchpad_frame = ttk.Frame(output_notebook)
            output_notebook.add(scratchpad_frame, text='Scratchpad')
            _, scratchpad_widget, _ = app.make_rich_textbox(parent_container=scratchpad_frame, wrap='word', show_xscroll=False, auto_hide_scrollbars=False)
        else:
            text_widget = tk.Text(text_frame, wrap='word', height=18)
            text_widget.pack(fill=BOTH, expand=True, padx=5, pady=5)
            scratchpad_frame = ttk.Frame(output_notebook)
            output_notebook.add(scratchpad_frame, text='Scratchpad')
            scratchpad_widget = tk.Text(scratchpad_frame, wrap='word')
            scratchpad_widget.pack(fill=BOTH, expand=True)
        output_widgets['text'] = text_widget
        output_widgets['scratchpad'] = scratchpad_widget

        def toggle_text_wrap():
            if 'text' in output_widgets and output_widgets['text'].winfo_exists():
                wrap_mode = tk.WORD if wrap_text_var.get() else tk.NONE
                output_widgets['text'].configure(wrap=wrap_mode)
        wrap_check.configure(command=toggle_text_wrap)

    # --- Table Functions ---
    def show_table_context_menu(event):
        tree = output_widgets.get('tree')
        if not tree: return

        selection = tree.selection()
        if not selection: return

        item_id = selection[0]
        column_id_str = tree.identify_column(event.x)

        context_menu = tk.Menu(tree, tearoff=0)
        context_menu.add_command(label=f'Copy Cell Content', command=lambda: copy_table_cell(item_id, column_id_str))
        context_menu.add_command(label=f'Copy Row', command=lambda: copy_table_row(item_id))
        context_menu.add_command(label=f'Copy Column', command=lambda: copy_table_column(column_id_str))
        context_menu.tk_popup(event.x_root, event.y_root)

    def copy_table_cell(item_id, column_id_str):
        tree = output_widgets.get('tree')
        if not tree: return
        content = tree.set(item_id, column_id_str)
        app.copy(content)

    def copy_table_row(item_id):
        tree = output_widgets.get('tree')
        if not tree: return
        values = tree.item(item_id, 'values')
        app.copy('\t'.join(map(str, values)))

    def copy_table_column(column_id_str):
        tree = output_widgets.get('tree')
        if not tree: return

        all_item_ids = last_table_data.get('all_item_ids', [])
        values = [tree.set(item_id, column_id_str) for item_id in all_item_ids]
        app.copy('\n'.join(map(str, values)))

    def generate_word_cloud_from_table():
        if not WordCloud or not Image:
            messagebox.showwarning('Missing Library', "The 'wordcloud' library is required. Please install it: pip install wordcloud")
            return

        columns = last_table_data.get('columns')
        if not columns or not last_table_data.get('rows'):
            messagebox.showinfo('No Data', 'No table data available to generate a word cloud.')
            return

        term_col_idx, freq_col_idx = -1, -1
        for i, col in enumerate(columns):
            col_lower = str(col).lower()
            if any(k in col_lower for k in ['term', 'word', 'ngram', 'entity']):
                term_col_idx = i
            if any(k in col_lower for k in ['freq', 'count', 'score']):
                freq_col_idx = i

        if term_col_idx == -1: term_col_idx = 0
        if freq_col_idx == -1:
            if len(columns) > 1: freq_col_idx = 1
            else:
                messagebox.showerror('Invalid Data', 'Could not determine frequency column from table data.')
                return

        try:
            tree = output_widgets.get('tree')
            if tree and tree.get_children():
                visible_rows_data = [tree.item(item, 'values') for item in tree.get_children()]
                frequencies = {str(row[term_col_idx]): float(row[freq_col_idx]) for row in visible_rows_data}
            else:
                messagebox.showinfo('No Data', 'No visible rows in the table to generate a word cloud.')
                return
        except (ValueError, TypeError, IndexError) as e:
            messagebox.showerror('Data Error', f'Could not generate word cloud. Error: {e}')
            return

        if not frequencies:
            messagebox.showinfo('No Data', 'No valid frequency data found to generate a word cloud.')
            return

        def generation_thread():
            try:
                wc = WordCloud(width=1200, height=800, background_color='white', colormap='viridis').generate_from_frequencies(frequencies)
                img = wc.to_image()

                def ui_update():
                    last_image_data['image'] = img
                    output_widgets['image_canvas'].itemconfig(output_widgets['image_canvas_no_img_text'], text='')
                    _update_image_display(fit_to_screen=True)
                    for btn in output_widgets.get('image_buttons', []): btn.config(state=NORMAL)
                    output_notebook.select(output_widgets['image_frame'])
                    main_status_label.config(text='Word cloud generated.')
                
                if nlp_root.winfo_exists():
                    nlp_root.after(0, ui_update)

            except Exception as e_thread:
                def show_error():
                    messagebox.showerror('Word Cloud Error', f'An error occurred during generation: {e_thread}')
                    main_status_label.config(text='Error generating word cloud.')
                if nlp_root.winfo_exists():
                    nlp_root.after(0, show_error)
            finally:
                def stop_progress():
                    progress_bar.stop()
                if nlp_root.winfo_exists():
                    nlp_root.after(0, stop_progress)

        main_status_label.config(text='Generating word cloud...')
        progress_bar.start()
        threading.Thread(target=generation_thread, daemon=True).start()

    def filter_table_rows(*args):
        tree = output_widgets.get('tree')
        if not tree: return

        search_term = table_filter_var.get()

        # When the filter is cleared, re-apply the sort to show all items.
        if not search_term:
            sort_cols = last_table_data.get('sort_by', [])
            if sort_cols:
                primary_col = sort_cols[0]
                reverse = last_table_data.get('sort_rev', {}).get(primary_col, False)
                # Call sort, but prevent it from re-filtering to avoid a loop
                sort_table_column(tree, primary_col, reverse, re_filter=False)
            else:
                # No sort is active, just re-show all detached items.
                # Their order will be their original insertion order.
                all_items = {str(i) for i in last_table_data.get('all_item_ids', [])}
                visible_items = set(tree.get_children())
                hidden_items = all_items - visible_items
                for item in hidden_items:
                    if tree.exists(item):
                        tree.move(item, '', 'end')
            return

        # If there is a search term, detach items that don't match.
        if not table_filter_case_sensitive.get():
            search_term = search_term.lower()

        # Iterate over a copy of visible items, as we are modifying the tree
        for item_id in list(tree.get_children()):
            values = tree.item(item_id, 'values')
            row_values = [str(v) for v in values]
            if not table_filter_case_sensitive.get():
                row_values = [v.lower() for v in row_values]

            if not any(search_term in v for v in row_values):
                tree.detach(item_id)

    table_filter_var.trace('w', filter_table_rows)

    def sort_table_column(tree, col, reverse, re_filter=True):
        sort_cols = last_table_data['sort_by']
        sort_revs = last_table_data['sort_rev']

        if col in sort_revs:
            sort_revs[col] = not sort_revs[col]
        else:
            sort_revs[col] = reverse

        if col in sort_cols:
            sort_cols.remove(col)
        sort_cols.insert(0, col)

        all_item_ids = last_table_data.get('all_item_ids', [])
        l = [(tree.item(k, 'values'), k) for k in all_item_ids]

        def multisort_key(item):
            keys = []
            for c in sort_cols:
                try:
                    idx = tree['columns'].index(c)
                    val_str = item[0][idx]
                    keys.append(float(val_str))
                except (ValueError, TypeError, IndexError):
                    keys.append(str(item[0][idx]).lower() if idx < len(item[0]) else '')
            return tuple(keys)

        l.sort(key=multisort_key, reverse=sort_revs[col])

        for index, (values, k) in enumerate(l):
            tree.move(k, '', index)

        for c in last_table_data.get('columns', []):
            img = ''
            if c in sort_cols:
                arrow = img_down if sort_revs.get(c, False) else img_up
                img = arrow
            tree.heading(c, image=img, command=lambda c_in=c: sort_table_column(tree, c_in, not sort_revs.get(c_in, True)))
        
        if re_filter:
            filter_table_rows()

    img_up = tk.PhotoImage(name='img_up', data=b'R0lGODlhCgAFAJEDAAAAAP///wAAAP///////////////yH5BAEAAAIALAAAAAAKAAUAAAIElI8pGgA7')
    img_down = tk.PhotoImage(name='img_down', data=b'R0lGODlhCgAFAJEDAAAAAP///wAAAP///////////////yH5BAEAAAIALAAAAAAKAAUAAAIElI+pGgA7')

    def run_now_thread():
        analysis_cancelled = False
        run_button.config(text='Cancel', command=_cancel_event.set)
        progress_bar.start()
        main_status_label.config(text='Starting analysis...')
        try:
            app.nlp_time_limit_s = float(time_limit_variable.get())
            source_text = input_text_widget.get('1.0', 'end-1c')

            if clean_lowercase_var.get(): source_text = source_text.lower()
            if clean_punct_var.get(): source_text = re.sub(r'[^\w\s]', '', source_text)

            if clean_stopwords_var.get() or lemmatize_var.get():
                main_status_label.config(text='Performing advanced cleaning...')
                nlp = ensure_nlp_pipeline(app)
                doc = nlp(source_text)
                tokens = []
                for token in doc:
                    if _cancel_event.is_set(): return
                    if clean_stopwords_var.get() and token.is_stop:
                        continue
                    if lemmatize_var.get():
                        if not token.is_space:
                            tokens.append(token.lemma_)
                    else:
                        if not token.is_space:
                            tokens.append(token.text)
                source_text = ' '.join(tokens)

            if _cancel_event.is_set(): return

            selected_label = function_combobox.get()
            setattr(app, '_nlp_last_function', selected_label)
            update_recent_functions(selected_label)
            mapped_key = normalize_key(NLP_FUNCTION_MAP.get(selected_label, selected_label))

            main_status_label.config(text=f'Running: {selected_label}...')
            
            query_param_val = query_var.get()
            if query_param_val == 'search term':
                query_param_val = ''
            
            text_param_val = text_var.get()
            if text_param_val == '(optional) second text for comparison':
                text_param_val = ''

            display_text, table_tuple, image_obj = analyze(
                app=app, text_value=source_text, function_key=mapped_key,
                top_n=max(1, topn_variable.get()), ngram_sizes=(max(1, ngram_min_var.get()), max(1, ngram_max_var.get())),
                time_limit_seconds=getattr(app, 'nlp_time_limit_s', 5.0), summary_ratio=summary_ratio_var.get(),
                query_param=query_param_val, value_param=value_var.get(), text_param=text_param_val, cancel_event=_cancel_event
            )

            if _cancel_event.is_set():
                analysis_cancelled = True
                return

            if nlp_root.winfo_exists():
                main_status_label.config(text='Populating results...')
                nlp_root.after(100, lambda: update_ui(display_text, table_tuple, image_obj))
        except Exception as run_error:
            if nlp_root.winfo_exists():
                if not _cancel_event.is_set():
                    messagebox.showerror('EgonTE', f'NLP error: {run_error}')
                    main_status_label.config(text='An error occurred.')
                else:
                    analysis_cancelled = True
        finally:
            if nlp_root.winfo_exists():
                run_button.config(text='Run Analysis', command=run_now)
                progress_bar.stop()
                if analysis_cancelled or _cancel_event.is_set():
                    main_status_label.config(text='Status: Analysis cancelled.')

    def run_now():
        _cancel_event.clear()
        threading.Thread(target=run_now_thread, daemon=True).start()

    def update_ui(display_text, table_tuple, image_obj):
        clear_all(clear_scratchpad=False, clear_controls=False, full_reset=False)

        is_first_image = last_image_data.get('image') is None
        last_image_data['image'] = image_obj

        if image_obj and ImageTk:
            output_widgets['image_canvas'].itemconfig(output_widgets['image_canvas_no_img_text'], text='')
            if is_first_image:
                _update_image_display(fit_to_screen=True)
            else:
                _update_image_display()
            for btn in output_widgets.get('image_buttons', []): btn.config(state=NORMAL)

        if table_tuple:
            cols, rows = table_tuple
            last_table_data.update({'columns': cols, 'rows': rows, 'sort_by': [], 'sort_rev': {}})
            tree = output_widgets['tree']
            tree['columns'] = cols

            output_widgets['table_no_data_label'].place_forget()

            palette_name = table_color_palette.get()
            palettes = {
                'Blues': ['#E1F5FE', '#B3E5FC', '#81D4FA', '#4FC3F7', '#29B6F6', '#03A9F4', '#039BE5', '#0288D1'],
                'Greens': ['#E8F5E9', '#C8E6C9', '#A5D6A7', '#81C784', '#66BB6A', '#4CAF50', '#43A047', '#388E3C'],
                'Reds': ['#FFEBEE', '#FFCDD2', '#EF9A9A', '#E57373', '#EF5350', '#F44336', '#E53935', '#D32F2F']
            }
            heat_colors = palettes.get(palette_name, [])

            for i, color in enumerate(heat_colors):
                tree.tag_configure(f'heat_{i}', background=color)

            numeric_columns_stats = {}
            if rows and heat_colors:
                for i, col_name in enumerate(cols):
                    try:
                        col_values = [float(row[i]) for row in rows if isinstance(row[i], (int, float)) or (isinstance(row[i], str) and row[i].replace('.','',1).isdigit())]
                        if col_values:
                            min_val, max_val = min(col_values), max(val_values)
                            numeric_columns_stats[col_name] = (min_val, max_val)
                    except (ValueError, IndexError):
                        continue

            for col in cols:
                tree.heading(col, text=str(col).capitalize(), command=lambda c=col: sort_table_column(tree, c, False), image='')
                tree.column(col, stretch=True, width=120)

            all_item_ids = []
            for iid, row in enumerate(rows):
                display_values = list(row)
                tag_to_apply = ''
                if heat_colors:
                    for i, col_name in enumerate(cols):
                        if col_name in numeric_columns_stats:
                            min_val, max_val = numeric_columns_stats[col_name]
                            range_val = max_val - min_val
                            try:
                                val = float(row[i])
                                if range_val > 0:
                                    norm_val = (val - min_val) / range_val
                                    heat_index = int(norm_val * (len(heat_colors) - 1))
                                    tag_to_apply = f'heat_{heat_index}'
                                else:
                                    tag_to_apply = f'heat_{len(heat_colors) - 1}'
                            except (ValueError, IndexError):
                                pass
                            break
                item_id = tree.insert('', END, iid=iid, values=display_values, tags=(tag_to_apply,))
                all_item_ids.append(item_id)
            last_table_data['all_item_ids'] = all_item_ids

            filter_table_rows()

        if display_text:
            last_text_data['display'] = display_text
            text_widget = output_widgets['text']
            text_widget.configure(state=NORMAL)
            text_widget.delete('1.0', END)
            text_widget.insert(END, wrap_text(display_text, max_cols=100))
            text_widget.configure(state=DISABLED)

        if image_obj:
            output_notebook.select(output_widgets['image_frame'])
        elif table_tuple:
            output_notebook.select(output_widgets['table_frame'])
        elif display_text:
            output_notebook.select(output_widgets['text_frame'])

        update_status_bars()

    run_button.configure(command=run_now)

    # --- Action Button Functions ---
    def copy_input_to_clipboard():
        try:
            content = input_text_widget.get('1.0', 'end-1c')
            if content:
                if hasattr(app, 'copy'):
                    app.copy(content)
                else:
                    nlp_root.clipboard_clear()
                    nlp_root.clipboard_append(content)
                messagebox.showinfo('NLP Tool', 'Input text copied to clipboard.')
        except Exception as e:
            messagebox.showerror('NLP Tool', f'Error copying input text: {e}')

    def copy_output_to_clipboard(output_type='auto', as_csv=False):
        try:
            if output_type == 'image':
                processed_image = get_processed_image()
                if processed_image and ImageGrab:
                    ImageGrab.grabclipboard_set(processed_image)
                    messagebox.showinfo('NLP Tool', 'Image copied to clipboard.')
                return

            active_tab_text = output_notebook.tab(output_notebook.select(), 'text') if output_notebook.tabs() else ''
            content = None
            if active_tab_text == 'Table' and last_table_data['columns'] is not None:
                tree = output_widgets['tree']
                visible_rows = [tree.item(item, 'values') for item in tree.get_children()]
                if as_csv:
                    content = to_csv(last_table_data['columns'], visible_rows or ())
                else:
                    content = to_tsv(last_table_data['columns'], visible_rows or ())
            elif active_tab_text == 'Text':
                content = last_text_data['display'] or ''

            if content is not None:
                if hasattr(app, 'copy'):
                    app.copy(content)
                else:
                    nlp_root.clipboard_clear()
                    nlp_root.clipboard_append(content)
                messagebox.showinfo('EgonTE', f"{ 'CSV' if as_csv else 'TSV'} copied to clipboard.")
        except Exception as e:
            messagebox.showerror('EgonTE', f'Error copying: {e}')

    def save_to_file(output_type='auto'):
        try:
            if output_type == 'image':
                active_tab_text = 'Image'
            else:
                active_tab_text = output_notebook.tab(output_notebook.select(), 'text') if output_notebook.tabs() else ''

            if active_tab_text == 'Image' and last_image_data['image']:
                file_path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG files', '*.png'), ('All files', '*.*')] )
                if file_path:
                    processed_image = get_processed_image()
                    if processed_image:
                        processed_image.save(file_path)
                        messagebox.showinfo('Success', 'Image saved successfully.')
            elif active_tab_text == 'Table' and last_table_data['columns'] is not None:
                tree = output_widgets['tree']
                visible_rows = [tree.item(item, 'values') for item in tree.get_children()]
                file_path = filedialog.asksaveasfilename(filetypes=[('CSV files', '*.csv'), ('Excel files', '*.xlsx'), ('All files', '*.*')], defaultextension='.csv')
                if file_path:
                    if file_path.endswith('.xlsx'):
                        try:
                            import pandas as pd
                            df = pd.DataFrame(visible_rows, columns=last_table_data['columns'])
                            df.to_excel(file_path, index=False)
                            messagebox.showinfo('EgonTE', 'File saved successfully as Excel.')
                        except ImportError:
                            messagebox.showerror('EgonTE', 'Pandas library is required for Excel export. Please install it: pip install pandas openpyxl')
                        except Exception as e:
                            messagebox.showerror('EgonTE', f'Error saving as Excel: {e}')
                    else:
                        content = to_csv(last_table_data['columns'], visible_rows or ())
                        with open(file_path, 'w', encoding='utf-8', newline='') as f:
                            f.write(content)
                        messagebox.showinfo('EgonTE', 'File saved successfully as CSV.')
            elif active_tab_text == 'Text' and (last_text_data['display'] or ''):
                content = last_text_data['display']
                file_path = filedialog.asksaveasfilename(filetypes=[('Text files', '*.txt'), ('All files', '*.*')], defaultextension='.txt')
                if file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    messagebox.showinfo('EgonTE', 'File saved successfully.')
        except Exception as e:
            messagebox.showerror('EgonTE', f'Error saving file: {e}')

    def insert_output():
        try:
            active_tab_text = output_notebook.tab(output_notebook.select(), 'text') if output_notebook.tabs() else ''
            content_to_insert = None

            if active_tab_text == 'Table' and last_table_data['columns'] is not None:
                tree = output_widgets['tree']
                visible_rows = [tree.item(item, 'values') for item in tree.get_children()]
                content_to_insert = to_tsv(last_table_data['columns'], visible_rows or ())
            elif active_tab_text == 'Text':
                content_to_insert = last_text_data['display'] or ''

            if content_to_insert and hasattr(app, 'EgonTE'):
                app.EgonTE.insert(INSERT, content_to_insert)
        except Exception as e:
            messagebox.showerror('EgonTE', f'Error inserting text: {e}')

    def load_from_file():
        try:
            file_path = filedialog.askopenfilename()
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                input_text_widget.delete('1.0', END)
                input_text_widget.insert('1.0', content)
        except Exception as e:
            messagebox.showerror('EgonTE', f'Error loading file: {e}')

    def clear_all(clear_scratchpad=True, clear_controls=False, full_reset=True):
        # Clear Image tab content
        canvas = output_widgets.get('image_canvas')
        if canvas:
            canvas.delete('all')
            create_checkerboard(canvas, 2000, 2000)
            output_widgets['image_canvas_no_img_text'] = canvas.create_text(1000, 1000, text='No image generated yet.', justify=tk.CENTER, anchor=tk.CENTER)
            for btn in output_widgets.get('image_buttons', []): btn.config(state=DISABLED)
            output_widgets['image_info_label'].config(text='')

        # Clear Table tab content
        tree = output_widgets.get('tree')
        if tree:
            all_item_ids = last_table_data.get('all_item_ids', [])
            if all_item_ids:
                tree.delete(*all_item_ids)
            output_widgets['table_no_data_label'].place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            table_filter_var.set('')

        # Clear Text tab content
        text_widget = output_widgets['text']
        text_widget.configure(state=NORMAL)
        text_widget.delete('1.0', END)
        text_widget.insert(END, 'No text output generated yet.')
        text_widget.configure(state=DISABLED)

        if clear_scratchpad:
            scratchpad_widget = output_widgets['scratchpad']
            scratchpad_widget.delete('1.0', END)
            scratchpad_widget.insert(END, 'This is a scratchpad for your notes.')

        if clear_controls:
            search_var.set('')
            placeholder_callbacks.get(query_entry)(None)
            placeholder_callbacks.get(text_entry)(None)
            topn_variable.set(10)
            ngram_min_var.set(2)
            ngram_max_var.set(3)
            summary_ratio_var.set(0.2)
            value_var.set(80)
            clean_lowercase_var.set(False)
            clean_punct_var.set(False)
            clean_stopwords_var.set(False)
            lemmatize_var.set(False)
            function_combobox.set(available_functions[0] if available_functions else '')
            on_function_change()

        if full_reset:
            last_text_data['display'] = ''
            last_table_data.update({'columns': None, 'rows': None, 'all_item_ids': [], 'sort_by': [], 'sort_rev': {}})
            last_image_data.update({'image': None, 'photo': None})
            reset_image_view()

        update_status_bars()

    # --- Place Action Buttons in Controls Frame ---
    # Input Group
    load_button = ttk.Button(actions_frame, text='Load from File', command=load_from_file, style='Compact.TButton')
    load_button.grid(row=0, column=0, padx=2, pady=2, sticky=EW)
    copy_input_button = ttk.Button(actions_frame, text='Copy Input', command=copy_input_to_clipboard, style='Compact.TButton')
    copy_input_button.grid(row=0, column=1, padx=2, pady=2, sticky=EW)

    ttk.Separator(actions_frame, orient=HORIZONTAL).grid(row=1, column=0, columnspan=2, sticky=EW, pady=5)

    # Output Group
    save_button = ttk.Button(actions_frame, text='Save Output', command=lambda: save_to_file('auto'), style='Compact.TButton')
    save_button.grid(row=2, column=0, padx=2, pady=2, sticky=EW)
    insert_button = ttk.Button(actions_frame, text='Insert Output', command=insert_output, style='Compact.TButton')
    insert_button.grid(row=2, column=1, padx=2, pady=2, sticky=EW)
    copy_tsv_button = ttk.Button(actions_frame, text='Copy TSV', command=lambda: copy_output_to_clipboard(as_csv=False), style='Compact.TButton')
    copy_tsv_button.grid(row=3, column=0, padx=2, pady=2, sticky=EW)
    copy_csv_button = ttk.Button(actions_frame, text='Copy CSV', command=lambda: copy_output_to_clipboard(as_csv=True), style='Compact.TButton')
    copy_csv_button.grid(row=3, column=1, padx=2, pady=2, sticky=EW)

    ttk.Separator(actions_frame, orient=HORIZONTAL).grid(row=4, column=0, columnspan=2, sticky=EW, pady=5)

    # Window Group
    clear_button = ttk.Button(actions_frame, text='Clear Output', command=lambda: clear_all(clear_scratchpad=False, clear_controls=False), style='Compact.TButton')
    clear_button.grid(row=5, column=0, padx=2, pady=2, sticky=EW)
    full_reset_button = ttk.Button(actions_frame, text='Full Reset', command=lambda: clear_all(clear_scratchpad=True, clear_controls=True), style='Compact.TButton')
    full_reset_button.grid(row=5, column=1, padx=2, pady=2, sticky=EW)
    close_button = ttk.Button(actions_frame, text='Close', command=nlp_root.destroy, style='Compact.TButton')
    close_button.grid(row=6, column=0, columnspan=2, sticky=EW, padx=2, pady=(8,2))

    # --- Bottom Status Bar ---
    main_status_label = ttk.Label(bottom_frame, text='Status: Ready')
    main_status_label.pack(side=LEFT, padx=5, fill=tk.X, expand=True)

    def update_status_bars(event=None):
        try:
            text = input_text_widget.get('1.0', 'end-1c')
            char_count = len(text)
            word_count = len(re.findall(r'\w+', text))
            sent_count = len(re.findall(r'[^.!?]+[.!?]', text))
            input_status_label.config(text=f'Input: {char_count} Chars | {word_count} Words | {sent_count} Sents')
        except Exception:
            input_status_label.config(text='Input: ...')

        text = last_text_data.get('display', '')
        if text and text not in ['No text output generated yet.', 'Output cleared.']:
            char_count = len(text)
            word_count = len(re.findall(r'\w+', text))
            sent_count = len(re.findall(r'[^.!?]+[.!?]', text))
            output_status_label.config(text=f'Output: {char_count} Chars | {word_count} Words | {sent_count} Sents')
        else:
            output_status_label.config(text='Output: ...')

    output_notebook.bind('<<NotebookTabChanged>>', update_status_bars)
    input_text_widget.bind('<KeyRelease>', update_status_bars)

    # --- Final Setup ---
    setup_output_tabs()
    clear_all()
    update_status_bars()
    populate_quick_access()
    on_function_change()  # Set initial state

    # --- Asynchronous NLP Model Loading for UI Responsiveness ---
    def load_model_and_update_ui():
        try:
            # This is the potentially long-running operation.
            # It's memoized, so subsequent calls are fast.
            ensure_nlp_pipeline(app)
            # Once done, schedule UI updates to run on the main thread
            if nlp_root.winfo_exists():
                def enable_widgets():
                    main_status_label.config(text='Status: Ready')
                    run_button.config(state=NORMAL)
                    clean_stopwords_check.config(state=NORMAL)
                    lemmatize_check.config(state=NORMAL)
                nlp_root.after(0, enable_widgets)
        except Exception as e:
            if nlp_root.winfo_exists():
                def show_error():
                    messagebox.showerror('NLP Initialization Error', f'Could not load NLP model in the background: {e}')
                    main_status_label.config(text='Error: NLP model failed to load.')
                nlp_root.after(0, show_error)

    # Initially, disable widgets that depend on the NLP model and show a loading status.
    # This prevents the UI from freezing on the first run.
    main_status_label.config(text='Initializing NLP model...')
    run_button.config(state=DISABLED)
    clean_stopwords_check.config(state=DISABLED)
    lemmatize_check.config(state=DISABLED)

    # Start the loading process in a background thread
    threading.Thread(target=load_model_and_update_ui, daemon=True).start()

    main_paned_window.bind('<B1-Motion>', enforce_min_pane_size)
    nlp_root.bind('<Configure>', enforce_min_pane_size)

    for var in (topn_variable, ngram_min_var, ngram_max_var, summary_ratio_var, query_var, value_var, text_var, clean_lowercase_var, clean_punct_var, clean_stopwords_var, lemmatize_var):
        var.trace_add('write', schedule_run)

    nlp_root.protocol('WM_DELETE_WINDOW', nlp_root.destroy)

    tooltip_targets = [
        (search_entry, 'Filter the list of functions below.'),
        (topn_spinbox, 'Number of top results to display.'),
        (ngram_min_spinbox, 'Minimum size of n-grams to find.'),
        (ngram_max_spinbox, 'Maximum size of n-grams to find.'),
        (summary_ratio_scale, 'The ratio of sentences to include in the summary.'),
        (query_entry, 'The search term for the selected function.'),
        (value_spinbox, 'The cutoff value for the selected function.'),
        (text_entry, 'The second text for comparison.'),
        (clean_lowercase_check, 'Convert the text to lowercase before analysis.'),
        (clean_punct_check, 'Remove punctuation from the text before analysis.'),
        (clean_stopwords_check, 'Remove stopwords from the text before analysis.'),
        (lemmatize_check, 'Reduce words to their base form (lemma) before analysis.'),
        (time_limit_spinbox, 'The maximum time to allow for the analysis to run.'),
        (run_button, 'Run the selected analysis on the text.'),
        (auto_run_check, 'Automatically run analysis when parameters change.'),
        (load_button, 'Load text from a file into the input box.'),
        (copy_input_button, 'Copy the full text from the input editor.'),
        (save_button, 'Save the output to a file (CSV for tables, TXT for text, PNG for images).'),
        (copy_tsv_button, 'Copy table output to the clipboard as TSV.'),
        (copy_csv_button, 'Copy table output to the clipboard as CSV.'),
        (insert_button, 'Insert the output into the main editor at the cursor.'),
        (clear_button, 'Clears the content of the output tabs.'),
        (full_reset_button, 'Clears all output and resets all controls to default.'),
        (close_button, 'Close the NLP tool window.'),
        (output_widgets.get('wrap_check'), 'Toggle word wrapping for the text output.')
    ]
    if hasattr(app, 'place_toolt'):
        image_buttons = output_widgets.get('image_buttons', [])
        image_tooltips = [
            (image_buttons[12], 'Zoom in on the image.'),
            (image_buttons[11], 'Zoom out of the image.'),
            (image_buttons[10], 'Reset zoom to 100%.'),
            (image_buttons[9], 'Fit the image to the window.'),
            (image_buttons[8], 'Reset zoom, rotation, and effects.'),
            (image_buttons[7], 'Rotate the image 90 degrees left.'),
            (image_buttons[6], 'Rotate the image 90 degrees right.'),
            (image_buttons[5], 'Invert the image colors.'),
            (image_buttons[4], 'Convert the image to grayscale.'),
            (image_buttons[3], 'Toggle the background pattern.'),
            (image_buttons[2], 'Copy the current image view to the clipboard.'),
            (image_buttons[1], 'Save the current image view to a file.'),
            (image_buttons[0], 'Open the image in the default system viewer.')
        ]
        tooltip_targets.extend(image_tooltips)
        table_tooltips = [
            (output_widgets.get('table_filter_entry'), 'Filter the table rows by a search term.'),
            (output_widgets.get('table_case_btn'), 'Toggle case-sensitive filtering.'),
            (output_widgets.get('wc_button'), "Generate a word cloud from the current table data (requires 'wordcloud' library).")
        ]
        tooltip_targets.extend(table_tooltips)
        app.place_toolt(targets=tooltip_targets)

    # --- Preset Handling & Initial Text Population ---
    initial_text_populated = False
    if preset_function:
        normalized_preset = normalize_key(preset_function)
        reverse_map = {v: k for k, v in NLP_FUNCTION_MAP.items()}
        label_to_set = reverse_map.get(normalized_preset)
        if label_to_set:
            function_combobox.set(label_to_set)
            if hasattr(app, 'EgonTE'):
                initial_text = app.EgonTE.get('1.0', 'end-1c')
                if initial_text.strip():
                    input_text_widget.insert('1.0', initial_text)
                    initial_text_populated = True
            run_now()

    if not initial_text_populated and hasattr(app, 'EgonTE'):
        initial_text = app.EgonTE.get('1.0', 'end-1c')
        if initial_text.strip():
            input_text_widget.insert('1.0', initial_text)
