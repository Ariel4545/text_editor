# This version focuses on the core handwriting-to-text purpose, removing shapes and layers,
# and adding a full-featured, contextual text editing tool.
import os
import json
import re
import tempfile
import tkinter as tk
import webbrowser
from tkinter import ttk, filedialog as fd, colorchooser, simpledialog, font
from tkinter import messagebox
from threading import Thread

from UI.canvas_builder import RichCanvas
from dependencies import large_variables as lv
from services import OCR_service
from services.theme_service import ThemeService

def _get_session_path():
    """Returns the path to the session file."""
    return os.path.join(tempfile.gettempdir(), 'ete_handwriting_session.json')


# --- Find/Replace Dialog ---
class FindReplaceDialog(tk.Toplevel):
    """A dialog for finding and replacing text in a text widget."""

    def __init__(self, parent, text_widget):
        super().__init__(parent)
        self.transient(parent)
        self.title("Find and Replace")
        self.text_widget = text_widget

        self.find_what = tk.StringVar()
        self.replace_with = tk.StringVar()
        self.match_case = tk.BooleanVar()

        body = ttk.Frame(self, padding="10 10 10 10")
        self.initial_focus = self.create_widgets(body)
        body.pack(fill=tk.BOTH, expand=True)

        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.grab_set()  # Modal
        if self.initial_focus:
            self.initial_focus.focus_set()
        self.wait_window(self)

    def create_widgets(self, parent):
        """Creates the widgets for the find and replace dialog."""
        ttk.Label(parent, text="Find what:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        find_entry = ttk.Entry(parent, textvariable=self.find_what, width=30)
        find_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=2)

        ttk.Label(parent, text="Replace with:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        replace_entry = ttk.Entry(parent, textvariable=self.replace_with, width=30)
        replace_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=2)

        case_check = ttk.Checkbutton(parent, text="Match case", variable=self.match_case)
        case_check.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(button_frame, text="Find Next", command=self.find_next).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Replace", command=self.replace).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Replace All", command=self.replace_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.cancel).pack(side=tk.LEFT, padx=5)

        return find_entry

    def find_next(self):
        """Finds the next occurrence of the search string."""
        self.text_widget.tag_remove('found', '1.0', tk.END)
        find_str = self.find_what.get()
        if not find_str: return

        start_pos = self.text_widget.index(tk.INSERT)
        pos = self.text_widget.search(find_str, start_pos, stopindex=tk.END, nocase=not self.match_case.get())

        if not pos:
            pos = self.text_widget.search(find_str, "1.0", stopindex=tk.END, nocase=not self.match_case.get())

        if pos:
            end_pos = f"{pos}+{len(find_str)}c"
            self.text_widget.tag_add('found', pos, end_pos)
            self.text_widget.mark_set(tk.INSERT, end_pos)
            self.text_widget.see(pos)
            self.text_widget.focus_set()

    def replace(self):
        """Replaces the currently selected occurrence."""
        if self.text_widget.tag_ranges('found'):
            start, end = self.text_widget.tag_ranges('found')
            self.text_widget.delete(start, end)
            self.text_widget.insert(start, self.replace_with.get())
            self.find_next()

    def replace_all(self):
        """Replaces all occurrences of the search string."""
        find_str = self.find_what.get()
        replace_str = self.replace_with.get()
        if not find_str: return

        content = self.text_widget.get('1.0', tk.END)
        new_content = content.replace(find_str, replace_str) if self.match_case.get() else re.sub(re.escape(find_str),
                                                                                                  replace_str, content,
                                                                                                  flags=re.IGNORECASE)

        self.text_widget.delete('1.0', tk.END)
        self.text_widget.insert('1.0', new_content)

    def cancel(self, event=None):
        """Closes the dialog."""
        self.text_widget.tag_remove('found', '1.0', tk.END)
        self.parent.focus_set()
        self.destroy()


# --- Main Entry Point ---
def open_handwriting(app):
    """Initializes and opens the handwriting tool window."""
    if hasattr(app, 'hw_root') and app.hw_root.winfo_exists():
        app.hw_root.lift()
        return

    try:
        app.hw_root = app.make_pop_ups_window(function=open_handwriting, title="Handwriting to Text",
                                              geometry='900x700')
    except AttributeError:
        messagebox.showerror("Initialization Error",
                             "UI Builder is not available in the app. Cannot open handwriting tool.")
        return

    # --- State Variables ---
    app.pnc_width, app.ers_width = tk.IntVar(value=3), tk.IntVar(value=20)
    app.current_tool, app.current_color = tk.StringVar(value='pencil'), tk.StringVar(value='black')
    app.grid_size, app.ocr_lang = tk.StringVar(value='Off'), tk.StringVar(value='eng')
    app.show_grid = tk.BooleanVar(value=True)
    app.auto_copy_ocr = tk.BooleanVar(value=True)
    app.ocr_on_selection = tk.BooleanVar(value=False)
    app.mw_width_change = tk.BooleanVar(value=False)
    app.live_ocr_after_id = None
    app.previous_color = 'black'
    app.custom_colors = []
    app.remote_ocr_langs = []
    app.lang_install_progress = {}
    app.drag_data = {"item": None, "x": 0, "y": 0}

    app.text_font_family = tk.StringVar(value='Arial')
    app.text_font_size = tk.IntVar(value=12)
    app.text_font_bold = tk.BooleanVar(value=False)
    app.text_font_italic = tk.BooleanVar(value=False)
    app.text_alignment = tk.StringVar(value='center')

    app.ocr_confidence_threshold = tk.IntVar(value=70)
    app.ocr_psm = tk.StringVar(value='6')
    app.ocr_psm_display = tk.StringVar()
    app.ocr_invert_colors = tk.BooleanVar(value=False)
    app.ocr_binarize_threshold = tk.IntVar(value=160)
    app.ocr_install_progress = tk.DoubleVar(value=0.0)

    app.shortcuts_enabled = {
        'file': tk.BooleanVar(value=True),
        'edit': tk.BooleanVar(value=True),
        'tools': tk.BooleanVar(value=True),
        'view': tk.BooleanVar(value=True),
    }

    ui = {}

    TOOL_CONFIGS = {
        'select': {'label': 'Select', 'shortcut': 's', 'cursor': 'crosshair'},
        'pencil': {'label': 'Pencil', 'shortcut': 'p', 'cursor': 'pencil', 'width_var': app.pnc_width},
        'line': {'label': 'Line', 'shortcut': 'l', 'cursor': 'crosshair', 'width_var': app.pnc_width},
        'text': {'label': 'Text', 'shortcut': 't', 'cursor': 'xterm'},
        'eraser': {'label': 'Eraser', 'shortcut': 'e', 'cursor': 'dotbox', 'width_var': app.ers_width},
    }

    # --- UI Setup Functions ---
    def _create_main_layout():
        main_paned_window = ttk.PanedWindow(app.hw_root, orient=tk.HORIZONTAL)
        main_paned_window.pack(fill=tk.BOTH, expand=True)
        ui['left_pane'] = ttk.Frame(main_paned_window, width=lv.HW_LEFT_PANE_WIDTH)
        ui['right_pane'] = ttk.Frame(main_paned_window)
        main_paned_window.add(ui['left_pane'], weight=0)
        main_paned_window.add(ui['right_pane'], weight=1)
        app.hw_root.after(100, lambda: main_paned_window.sashpos(0, lv.HW_LEFT_PANE_WIDTH))

    def _create_canvas_area():
        right_pane = ui['right_pane']
        ui['top_frame'] = ttk.Frame(right_pane, style='TFrame')
        ui['top_frame'].pack(fill='x', padx=5, pady=(2, 0))

        draw_frame = ttk.Frame(right_pane, style='TFrame')
        draw_frame.pack(fill='both', expand=True, padx=5, pady=5)

        status_bar = ttk.Frame(right_pane, style='TFrame', relief='solid', borderwidth=1)
        status_bar.pack(fill='x', side='bottom', ipady=2)

        # Create status bar labels
        ui['status_label'] = ttk.Label(status_bar, text='Tool: Pencil', anchor='w')
        ui['status_label'].pack(side='left', padx=5)
        ui['width_label'] = ttk.Label(status_bar, text='Width: 3', anchor='w')
        ui['width_label'].pack(side='left', padx=5)
        ui['message_label'] = ttk.Label(status_bar, text='', anchor='w')
        ui['message_label'].pack(side='left', padx=5)
        ui['coords_label'] = ttk.Label(status_bar, text='X: 0, Y: 0', anchor='center')
        ui['coords_label'].pack(side='left', expand=True, fill='x')
        ui['ocr_status_label'] = ttk.Label(status_bar, text='OCR: Initializing...', anchor='e')
        ui['ocr_status_label'].pack(side='right', padx=5)
        ui['zoom_label'] = ttk.Label(status_bar, text='Zoom: 100%', anchor='e')
        ui['zoom_label'].pack(side='right', padx=10)

        def on_width_adjust(tool, width):
            var = TOOL_CONFIGS[tool].get('width_var')
            if var:
                var.set(width)
            update_width_display()

        # Create rich canvas using the builder
        canvas_frame = RichCanvas(
            master=draw_frame,
            app=app,
            bg=UI_COLORS['CANVAS_BG'],
            enable_undo=True,
            enable_zoom=True,
            enable_grid=True,
            enable_selection=True,
            enable_text=True,
            initial_tool=app.current_tool.get(),
            pencil_color=app.current_color.get(),
            pencil_width=app.pnc_width.get(),
            eraser_width=app.ers_width.get(),
            line_width=app.pnc_width.get(),
            enable_mouse_wheel_width=app.mw_width_change.get(),
            on_width_adjust=on_width_adjust
        )
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        ui['canvas_frame'] = canvas_frame
        ui['canvas'] = canvas_frame.get_canvas()
        
        canvas_frame.on_undo_redo_update(lambda can_undo, can_redo: _update_undo_redo_buttons(can_undo, can_redo))


    def show_status_message(message, duration=2000):
        ui['message_label'].config(text=message)
        if duration > 0:
            app.hw_root.after(duration, lambda: ui['message_label'].config(text=''))

    def _post_process_text(action):
        text_widget = ui['live_ocr_text']
        current_text = text_widget.get('1.0', 'end-1c')
        if not current_text and action != 'find_replace': return

        if action == 'upper': new_text = current_text.upper()
        elif action == 'lower': new_text = current_text.lower()
        elif action == 'clean_space':
            new_text = re.sub(r'[ 	]+', ' ', current_text)
            new_text = re.sub(r'\n+', '\n', new_text).strip()
        elif action == 'find_replace':
            FindReplaceDialog(app.hw_root, text_widget)
            return
        else: return

        text_widget.delete('1.0', tk.END)
        text_widget.insert('1.0', new_text)
        trigger_live_ocr(delay=False)

    def _create_left_pane_widgets():
        left_pane = ui['left_pane']
        notebook = ttk.Notebook(left_pane, padding=5)
        notebook.pack(fill='both', expand=True)
        ui['left_pane_notebook'] = notebook

        # OCR Output Tab
        output_tab = ttk.Frame(notebook, padding=(5, 5, 5, 0))
        notebook.add(output_tab, text='Live OCR')

        ocr_text_frame, ocr_text_widget, _ = app.make_rich_textbox(
            output_tab, font=('Segoe UI', 8), wrap=tk.WORD, bd=1, relief='solid'
        )
        ui['live_ocr_text'] = ocr_text_widget
        ui['live_ocr_text'].tag_configure("low_conf", foreground="red", underline=True)
        ui['live_ocr_text'].tag_configure("found", background="yellow", foreground="black")

        _create_ocr_install_manager(output_tab)

        post_process_frame = ttk.Frame(output_tab)
        post_process_frame.pack(fill='x', pady=(0, 5))
        btn_defs = [('Upper', 'upper'), ('Lower', 'lower'), ('Clean Space', 'clean_space'), ('Find & Replace', 'find_replace')]
        for i, (text, cmd) in enumerate(btn_defs):
            btn = ttk.Button(post_process_frame, text=text, command=lambda c=cmd: _post_process_text(c))
            btn.pack(side='left', expand=True, fill='x', padx=(0 if i == 0 else 2, 2 if i < len(btn_defs)-1 else 0))
            ui[f'post_proc_{cmd}'] = btn

        action_buttons_frame = ttk.Frame(output_tab)
        action_buttons_frame.pack(fill='x')
        ui['ocr_button'] = ttk.Button(action_buttons_frame, text='Append to Editor', command=append_to_editor)
        ui['ocr_button'].pack(side='left', fill='x', expand=True, padx=(0, 2))
        ui['copy_ocr_button'] = ttk.Button(action_buttons_frame, text='Copy', command=lambda: copy_to_clipboard(ui['live_ocr_text'].get('1.0', 'end-1c')))
        ui['copy_ocr_button'].pack(side='left', fill='x', expand=True, padx=(2, 0))

        # Settings Tab
        settings_tab = ttk.Frame(notebook, padding=5)
        notebook.add(settings_tab, text='Settings')
        _create_settings_tab_content(settings_tab)

        # Language Manager Tab
        lang_tab = ttk.Frame(notebook, padding=5)
        notebook.add(lang_tab, text='Languages')
        _create_language_manager_tab(lang_tab)

        # Shortcuts Tab
        shortcuts_tab = ttk.Frame(notebook, padding=5)
        notebook.add(shortcuts_tab, text='Shortcuts')
        _create_shortcuts_tab(shortcuts_tab)

    def _toggle_mouse_wheel_width_binding():
        if ui.get('canvas_frame'):
            ui['canvas_frame'].enable_mouse_wheel_width = app.mw_width_change.get()

    def _create_settings_tab_content(settings_tab):
        # OCR Settings
        ocr_settings_frame = ttk.LabelFrame(settings_tab, text="OCR Engine", padding=5)
        ocr_settings_frame.pack(fill='x', pady=(0, 5), anchor='n')
        ui['rerun_ocr_button'] = ttk.Button(ocr_settings_frame, text='Re-run OCR', command=lambda: trigger_live_ocr(delay=False))
        ui['rerun_ocr_button'].pack(fill='x', pady=(0, 5))

        # Language Selector
        lang_frame = ttk.Frame(ocr_settings_frame)
        lang_frame.pack(fill='x', pady=2, expand=True)
        ttk.Label(lang_frame, text='Language(s):').pack(side='left')
        ui['ocr_lang_label'] = ttk.Label(lang_frame, text="eng", wraplength=150, justify=tk.LEFT)
        ui['ocr_lang_label'].pack(side='left', padx=5, expand=True, fill='x')
        ui['ocr_lang_select_button'] = ttk.Button(lang_frame, text="Select...", command=_open_language_selection_dialog)
        ui['ocr_lang_select_button'].pack(side='right')

        # PSM Mode
        psm_frame = ttk.Frame(ocr_settings_frame)
        psm_frame.pack(fill='x', pady=2, expand=True)
        ttk.Label(psm_frame, text='Mode:').pack(side='left')
        psm_combo = ttk.Combobox(psm_frame, textvariable=app.ocr_psm_display, values=list(lv.HW_OCR_PSM_MODES.keys()), width=12)
        psm_combo.pack(side='right')
        psm_combo.bind('<<ComboboxSelected>>', lambda e: on_psm_change())
        ui['ocr_psm_combo'] = psm_combo
        initial_psm_name = [k for k, v in lv.HW_OCR_PSM_MODES.items() if v == app.ocr_psm.get()]
        app.ocr_psm_display.set(initial_psm_name[0] if initial_psm_name else 'Single Block')

        # Confidence Slider
        conf_frame = ttk.Frame(ocr_settings_frame)
        conf_frame.pack(fill='x', pady=2, expand=True)
        conf_label_text = tk.StringVar(value=f"Confidence: {app.ocr_confidence_threshold.get()}%")
        ttk.Label(conf_frame, textvariable=conf_label_text).pack(side='left')
        conf_slider = ttk.Scale(conf_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=app.ocr_confidence_threshold, command=lambda v: on_conf_change(v, conf_label_text))
        conf_slider.pack(side='right', fill='x', expand=True, padx=(8, 0))
        ui['ocr_conf_slider'] = conf_slider

        # Pre-processing
        pre_proc_frame = ttk.LabelFrame(settings_tab, text="Image Pre-processing", padding=5)
        pre_proc_frame.pack(fill='x', pady=5, anchor='n')
        ui['ocr_invert_check'] = ttk.Checkbutton(pre_proc_frame, text='Invert Colors', variable=app.ocr_invert_colors, command=lambda: trigger_live_ocr(delay=False))
        ui['ocr_invert_check'].pack(anchor='w', pady=2)
        bin_frame = ttk.Frame(pre_proc_frame)
        bin_frame.pack(fill='x', pady=2, expand=True)
        bin_label_text = tk.StringVar(value=f"Binarize: {app.ocr_binarize_threshold.get()}")
        ttk.Label(bin_frame, textvariable=bin_label_text).pack(side='left')
        bin_slider = ttk.Scale(bin_frame, from_=0, to=255, orient=tk.HORIZONTAL, variable=app.ocr_binarize_threshold, command=lambda v: on_bin_change(v, bin_label_text))
        bin_slider.pack(side='right', fill='x', expand=True, padx=(8, 0))
        ui['ocr_bin_slider'] = bin_slider

        # Color Scheme
        color_scheme_frame = ttk.LabelFrame(settings_tab, text="Color Scheme", padding=5)
        color_scheme_frame.pack(fill='x', pady=5, anchor='n')
        custom_color_header = ttk.Frame(color_scheme_frame)
        custom_color_header.pack(fill='x')
        ttk.Label(custom_color_header, text="Custom Colors").pack(side='left', anchor='w')
        custom_color_buttons = ttk.Frame(custom_color_header)
        custom_color_buttons.pack(side='right', anchor='e')
        ttk.Button(custom_color_buttons, text='+', width=3, command=_add_custom_color).pack(side='left')
        ui['remove_color_button'] = ttk.Button(custom_color_buttons, text='-', width=3, command=_remove_custom_color)
        ui['remove_color_button'].pack(side='left')
        ui['custom_color_frame'] = ttk.Frame(color_scheme_frame)
        ui['custom_color_frame'].pack(fill='x', pady=(2, 0))
        _update_color_widgets()

        # General Settings
        general_settings_frame = ttk.LabelFrame(settings_tab, text="General", padding=5)
        general_settings_frame.pack(fill='x', pady=5, anchor='n')
        ui['auto_copy_check'] = ttk.Checkbutton(general_settings_frame, text='Auto-copy to Clipboard', variable=app.auto_copy_ocr)
        ui['auto_copy_check'].pack(anchor='w', pady=2)
        ui['ocr_selection_check'] = ttk.Checkbutton(general_settings_frame, text='OCR Only Selection', variable=app.ocr_on_selection, command=lambda: trigger_live_ocr(delay=False))
        ui['ocr_selection_check'].pack(anchor='w', pady=2)
        ttk.Checkbutton(general_settings_frame, text='Show Grid', variable=app.show_grid, command=update_grid).pack(anchor='w', pady=2)
        ttk.Checkbutton(general_settings_frame, text='Mouse Wheel to Change Width', variable=app.mw_width_change, command=_toggle_mouse_wheel_width_binding).pack(anchor='w', pady=2)

        # Shortcuts Settings
        shortcuts_frame = ttk.LabelFrame(settings_tab, text="Shortcuts", padding=5)
        shortcuts_frame.pack(fill='x', pady=5, anchor='n')
        for key, var in app.shortcuts_enabled.items():
            ttk.Checkbutton(shortcuts_frame, text=f"Enable {key.title()} Shortcuts", variable=var, command=_bind_events).pack(anchor='w')

    def _create_shortcuts_tab(shortcuts_tab):
        tree = ttk.Treeview(shortcuts_tab, columns=('Action', 'Shortcut'), show='headings')
        tree.heading('Action', text='Action')
        tree.heading('Shortcut', text='Shortcut')
        tree.column('Action', width=120)
        tree.column('Shortcut', width=120)
        tree.pack(expand=True, fill='both', padx=5, pady=5)

        shortcut_groups = {
            'File': [('Save Canvas', 'Ctrl + S'), ('Upload Image', 'Ctrl + O')],
            'Edit': [
                ('Undo', 'Ctrl + Z'), ('Redo', 'Ctrl + Y'), ('Copy Selection', 'Ctrl + C'),
                ('Paste Selection', 'Ctrl + V'), ('Delete Selection', 'Delete'),
                ('Move Selection (Fine)', 'Arrow Keys'),
                ('Move Selection (Coarse)', 'Shift + Arrow Keys'),
            ],
            'View': [('Zoom', 'Ctrl + Mouse Wheel'), ('Pan', 'Middle/Right-click Drag')],
            'Tools': [
                (f"Tool: {cfg['label']}", cfg['shortcut'].upper()) for cfg in TOOL_CONFIGS.values() if cfg.get('shortcut')
            ],
            'General': [
                ('Change Tool Width', 'Mouse Wheel (when enabled)'),
            ]
        }

        tree.tag_configure('category', font=('Segoe UI', 8, 'bold'))
        for category, shortcuts in shortcut_groups.items():
            tree.insert('', 'end', values=(category, ''), tags=('category',))
            for action, key in shortcuts:
                tree.insert('', 'end', values=(action, key))

    def _create_ocr_install_manager(parent):
        ui['ocr_install_manager_frame'] = ttk.Frame(parent, padding=10)
        ui['ocr_install_main_label'] = ttk.Label(ui['ocr_install_manager_frame'], text="Tesseract OCR Not Found", font=("Segoe UI", 10, "bold"))
        ui['ocr_install_main_label'].pack(pady=(0, 10))

        auto_frame = ttk.LabelFrame(ui['ocr_install_manager_frame'], text="Automatic Install", padding=10)
        auto_frame.pack(fill='x', pady=5)
        ui['ocr_install_button'] = ttk.Button(auto_frame, text="Install Tesseract", command=_install_ocr_service)
        ui['ocr_install_button'].pack(fill='x', ipady=5)
        ui['ocr_progress_bar'] = ttk.Progressbar(auto_frame, orient='horizontal', mode='determinate', variable=app.ocr_install_progress)
        ui['ocr_install_status_label'] = ttk.Label(auto_frame, wraplength=lv.HW_LEFT_PANE_WIDTH - 60, justify=tk.CENTER)

        manual_frame = ttk.LabelFrame(ui['ocr_install_manager_frame'], text="Manual Install", padding=10)
        manual_frame.pack(fill='x', pady=5)
        ttk.Label(manual_frame, text="If auto-install fails, download the file and place it in the correct folder.", wraplength=lv.HW_LEFT_PANE_WIDTH-60).pack(pady=(0,10))
        ttk.Label(manual_frame, text="Download URL:", font=("Segoe UI", 8, "bold")).pack(anchor='w')
        url_entry = ttk.Entry(manual_frame, state='readonly')
        url_entry.insert(0, OCR_service.TESSERACT_PORTABLE_URL)
        url_entry.pack(fill='x', pady=(0, 5))
        btn_frame = ttk.Frame(manual_frame)
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text="Copy URL", command=lambda: copy_to_clipboard(OCR_service.TESSERACT_PORTABLE_URL, "URL")).pack(side='left', expand=True, fill='x', padx=(0,2))
        ttk.Button(btn_frame, text="Open Folder", command=lambda: os.startfile(OCR_service.get_tesseract_zip_path())).pack(side='left', expand=True, fill='x', padx=(2,0))
        ttk.Button(manual_frame, text="Refresh Installation Status", command=lambda: OCR_service.init_ocr_async_service(set_state_callback=_update_ocr_status)).pack(pady=(10,0), fill='x')

    def _create_language_manager_tab(parent_tab):
        container = ttk.Frame(parent_tab)
        container.pack(fill='both', expand=True)
        header_frame = ttk.Frame(container)
        header_frame.pack(fill='x', pady=(0, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(header_frame, textvariable=search_var)
        search_entry.pack(fill='x', side='left', expand=True, padx=(0, 5))
        search_entry.bind('<KeyRelease>', lambda e: _populate_language_list(search_var.get()))
        ui['lang_refresh_button'] = ttk.Button(header_frame, text="Refresh", command=lambda: _populate_language_list(force_remote=True))
        ui['lang_refresh_button'].pack(side='right')

        tree_frame = ttk.Frame(container)
        tree_frame.pack(fill='both', expand=True)
        tree = ttk.Treeview(tree_frame, columns=('lang', 'status', 'action'), show='headings')
        tree.heading('lang', text='Language', anchor='w')
        tree.heading('status', text='Status', anchor='center')
        tree.heading('action', text='', anchor='center')
        tree.column('lang', width=100, anchor='w')
        tree.column('status', width=80, anchor='center')
        tree.column('action', width=60, anchor='center')
        ui['lang_tree'] = tree
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree.bind('<Button-1>', _on_lang_tree_click)

    def _populate_language_list(search_query=None, force_remote=False):
        tree = ui['lang_tree']
        for item in tree.get_children():
            if tree.exists(item): tree.delete(item)
        app.lang_install_progress.clear()

        def fetch_and_populate():
            remote_langs = OCR_service.get_remote_language_packs(force_refresh=force_remote)
            if remote_langs is None:
                tree.insert('', 'end', values=("Error fetching list", "", ""), tags=('error',))
                return
            app.remote_ocr_langs = remote_langs
            installed_langs = OCR_service.get_available_languages(force_refresh=True)
            filtered_langs = [l for l in app.remote_ocr_langs if not search_query or search_query.lower() in l.lower()]

            for lang_code in filtered_langs:
                status, action_text = ("✓", "Remove") if lang_code in installed_langs and lang_code not in ['eng', 'osd'] else ("-", "Install")
                if lang_code in installed_langs and lang_code in ['eng', 'osd']: action_text = ""
                item_id = tree.insert('', 'end', values=(lang_code, status, action_text), tags=(status.replace(' ', ''),))
                app.lang_install_progress[lang_code] = {"id": item_id, "progress_bar": None}

            for tag, color in [('✓', 'green'), ('-', '#555'), ('Downloading', 'blue'), ('Removing', 'orange'), ('error', 'red')]:
                tree.tag_configure(tag, foreground=color)

        Thread(target=fetch_and_populate, daemon=True).start()

    def _on_lang_tree_click(event):
        tree = ui['lang_tree']
        if tree.identify("region", event.x, event.y) != "cell" or tree.identify_column(event.x) != "#3": return
        item_id = tree.identify_row(event.y)
        lang_code, _, action = tree.item(item_id, "values")
        if action == "Install": _install_language(lang_code, item_id)
        elif action == "Remove": _uninstall_language(lang_code, item_id)

    def _update_language_op(lang_code, item_id, status, action, tag):
        tree = ui['lang_tree']
        if not tree.exists(item_id): return
        progress_bar = app.lang_install_progress[lang_code].get("progress_bar")
        if progress_bar: progress_bar.destroy()
        tree.set(item_id, 'status', status)
        tree.set(item_id, 'action', action)
        tree.item(item_id, tags=(tag,))

    def _install_language(lang_code, item_id):
        tree = ui['lang_tree']
        progress_bar = ttk.Progressbar(tree, orient='horizontal', mode='determinate')
        app.lang_install_progress[lang_code]["progress_bar"] = progress_bar
        _update_language_op(lang_code, item_id, 'Downloading', '', 'Downloading')
        tree.window_create(item_id, window=progress_bar, column="#3")

        def install_thread():
            success = OCR_service.install_language_pack(lang_code, lambda lc, p: progress_bar.config(value=p) if lc == lang_code else None, lambda msg: show_status_message(msg, 4000))
            app.hw_root.after(0, lambda: _on_install_complete(lang_code, item_id, success))
        Thread(target=install_thread, daemon=True).start()

    def _uninstall_language(lang_code, item_id):
        _update_language_op(lang_code, item_id, 'Removing', '', 'Removing')
        def uninstall_thread():
            success = OCR_service.uninstall_language_pack(lang_code)
            app.hw_root.after(0, lambda: _on_uninstall_complete(lang_code, item_id, success))
        Thread(target=uninstall_thread, daemon=True).start()

    def _on_install_complete(lang_code, item_id, success):
        if success:
            _update_language_op(lang_code, item_id, '✓', 'Remove', '✓')
            _update_main_language_selector()
        else: _update_language_op(lang_code, item_id, 'Error', 'Install', 'error')

    def _on_uninstall_complete(lang_code, item_id, success):
        if success:
            _update_language_op(lang_code, item_id, '-', 'Install', '-')
            _update_main_language_selector()
        else: _update_language_op(lang_code, item_id, 'Error', 'Remove', 'error')

    def _open_language_selection_dialog():
        dialog = tk.Toplevel(app.hw_root)
        dialog.title("Select OCR Languages")
        dialog.transient(app.hw_root)
        dialog.grab_set()
        installed_langs = OCR_service.get_available_languages()
        selected_langs = app.ocr_lang.get().split('+')
        vars = {lang: tk.BooleanVar(value=(lang in selected_langs)) for lang in installed_langs}
        for lang, var in vars.items():
            ttk.Checkbutton(dialog, text=lang, variable=var).pack(anchor='w', padx=10, pady=2)

        def on_ok():
            new_langs = [lang for lang, var in vars.items() if var.get()] or ['eng']
            app.ocr_lang.set('+'.join(new_langs))
            ui['ocr_lang_label'].config(text=app.ocr_lang.get())
            trigger_live_ocr(delay=False)
            dialog.destroy()
        ttk.Button(dialog, text="OK", command=on_ok).pack(pady=10)

    def _update_main_language_selector():
        installed_langs = OCR_service.get_available_languages(force_refresh=True)
        valid_selection = [lang for lang in app.ocr_lang.get().split('+') if lang in installed_langs] or ['eng']
        app.ocr_lang.set('+'.join(valid_selection))
        ui['ocr_lang_label'].config(text=app.ocr_lang.get())

    def _upload_image():
        path = fd.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")], parent=app.hw_root)
        if path:
            show_status_message(f"Loaded image: {os.path.basename(path)}")
            ui['canvas_frame'].load_image(path)
            trigger_live_ocr(delay=False)

    def _update_color_widgets():
        frame = ui.get('custom_color_frame')
        if not frame: return

        for widget in frame.winfo_children():
            widget.destroy()

        tooltip_targets = []
        for i, color in enumerate(app.custom_colors):
            swatch = tk.Frame(frame, bg=color, width=20, height=20, relief='raised', borderwidth=1)
            swatch.grid(row=i // 8, column=i % 8, padx=1, pady=1)
            swatch.bind('<Button-1>', lambda e, c=color: on_color_change(c))
            swatch.bind('<Double-1>', lambda e, c=color: copy_to_clipboard(c, "Color"))
            swatch.bind('<Button-3>', lambda e, index=i: _edit_custom_color(index))
            tooltip_targets.append((swatch, color))
            swatch.bind("<B1-Motion>", lambda e, index=i: _drag_color(e, index))
            swatch.bind("<ButtonRelease-1>", _drop_color)

        if hasattr(app, 'place_toolt'):
            app.place_toolt(tooltip_targets)

        all_colors = lv.HW_DEFAULT_COLOR_OPTIONS + app.custom_colors
        if ui.get('color_combo'):
            ui['color_combo']['values'] = all_colors + ['Add New...']
        _update_remove_button_state()

    def _drag_color(event, index):
        app.drag_data["item"] = index
        app.drag_data["x"] = event.x_root
        app.drag_data["y"] = event.y_root

    def _drop_color(event):
        if app.drag_data["item"] is None: return

        x, y = event.x_root, event.y_root
        target_widget = event.widget.winfo_containing(x, y)

        if target_widget and isinstance(target_widget, tk.Frame) and target_widget in ui['custom_color_frame'].winfo_children():
            to_index = target_widget.grid_info()["column"] + target_widget.grid_info()["row"] * 8
            from_index = app.drag_data["item"]

            if from_index != to_index:
                color = app.custom_colors.pop(from_index)
                app.custom_colors.insert(to_index, color)
                _update_color_widgets()
                save_session()

        app.drag_data["item"] = None

    def _edit_custom_color(index):
        color_to_edit = app.custom_colors[index]
        new_color = colorchooser.askcolor(parent=app.hw_root, title=f'Edit color {color_to_edit}', initialcolor=color_to_edit)[1]
        if new_color and new_color != color_to_edit:
            app.custom_colors[index] = new_color
            _update_color_widgets()
            on_color_change(new_color)
            save_session()

    def copy_to_clipboard(content, content_type="Text"):
        app.hw_root.clipboard_clear()
        app.hw_root.clipboard_append(content)
        show_status_message(f"{content_type} copied to clipboard")

    def _add_custom_color():
        new_color = colorchooser.askcolor(parent=app.hw_root, title='Choose a color', initialcolor=app.previous_color)[1]
        if new_color and new_color not in app.custom_colors:
            app.custom_colors.append(new_color)
            _update_color_widgets()
            on_color_change(new_color)
            save_session()

    def _remove_custom_color():
        color_to_remove = app.current_color.get()
        if color_to_remove in app.custom_colors:
            app.custom_colors.remove(color_to_remove)
            _update_color_widgets()
            on_color_change('black')
            save_session()

    def _update_remove_button_state():
        if ui.get('remove_color_button'):
            is_custom = app.current_color.get() in app.custom_colors and app.current_color.get() not in lv.HW_DEFAULT_COLOR_OPTIONS
            ui['remove_color_button'].config(state=tk.NORMAL if is_custom else tk.DISABLED)

    def _create_toolbars():
        ui['tool_buttons'] = {}
        top_frame = ui['top_frame']
        toolbar_notebook = ttk.Notebook(top_frame, style='Tool.TNotebook')
        toolbar_notebook.pack(fill='x', pady=(0, 2))
        ui['toolbar_notebook'] = toolbar_notebook

        tabs = {'Tools': None, 'Options': None, 'View': None, 'Actions': None}
        for name in tabs: tabs[name] = ttk.Frame(toolbar_notebook, padding=5)
        for name, frame in tabs.items(): toolbar_notebook.add(frame, text=name)

        # Tools Tab
        for i, (tool_id, config) in enumerate(TOOL_CONFIGS.items()):
            btn = ttk.Button(tabs['Tools'], text=config['label'], command=lambda m=tool_id: set_tool(m))
            btn.grid(row=0, column=i, padx=2)
            ui['tool_buttons'][tool_id] = btn

        # Options Tab
        options_grid = ttk.Frame(tabs['Options'])
        options_grid.pack(fill='x')
        ttk.Label(options_grid, text="Color:").grid(row=0, column=0, sticky='w', padx=(0, 5), pady=2)
        ui['color_combo'] = ttk.Combobox(options_grid, textvariable=app.current_color, width=12, state=['readonly'])
        ui['color_combo'].grid(row=0, column=1, sticky='w', pady=2)
        ui['color_combo'].bind('<<ComboboxSelected>>', lambda e: on_color_change(app.current_color.get()))
        ttk.Label(options_grid, text="Width:").grid(row=0, column=2, sticky='w', padx=(15, 5), pady=2)
        ui['width_combo'] = ttk.Combobox(options_grid, width=8, values=lv.HW_WIDTH_OPTIONS)
        ui['width_combo'].grid(row=0, column=3, sticky='w', pady=2)
        ui['width_combo'].bind('<<ComboboxSelected>>', on_width_change)
        ui['width_combo'].bind('<Return>', on_width_change)
        _update_color_widgets()

        # View Tab
        ttk.Button(tabs['View'], text='Zoom In', command=lambda: ui['canvas_frame'].zoom_in()).grid(row=0, column=0, padx=2)
        ttk.Button(tabs['View'], text='Zoom Out', command=lambda: ui['canvas_frame'].zoom_out()).grid(row=0, column=1, padx=2)
        ttk.Button(tabs['View'], text='Reset Zoom', command=lambda: ui['canvas_frame'].reset_zoom()).grid(row=0, column=2, padx=2)
        ttk.Label(tabs['View'], text="Grid:").grid(row=0, column=3, padx=(10, 2))
        ui['grid_combo'] = ttk.Combobox(tabs['View'], textvariable=app.grid_size, width=8, values=list(lv.HW_GRID_CONFIG.keys()), state=['readonly'])
        ui['grid_combo'].grid(row=0, column=4, padx=2)
        ui['grid_combo'].bind('<<ComboboxSelected>>', update_grid)

        # Actions Tab
        actions_grid = ttk.Frame(tabs['Actions'])
        actions_grid.pack(anchor='w')
        ui['undo_button'] = ttk.Button(actions_grid, text='Undo', command=undo_action, state=tk.DISABLED)
        ui['undo_button'].grid(row=0, column=0, padx=1, pady=1)
        ui['redo_button'] = ttk.Button(actions_grid, text='Redo', command=redo_action, state=tk.DISABLED)
        ui['redo_button'].grid(row=0, column=1, padx=1, pady=1)
        ttk.Button(actions_grid, text='Copy', command=copy_selection).grid(row=1, column=0, padx=1, pady=1)
        ttk.Button(actions_grid, text='Paste', command=paste_selection).grid(row=1, column=1, padx=1, pady=1)
        ttk.Button(actions_grid, text='Save', command=save_canvas).grid(row=0, column=2, padx=(10, 1), pady=1)
        ttk.Button(actions_grid, text='Upload', command=_upload_image).grid(row=0, column=3, padx=1, pady=1)
        ttk.Button(actions_grid, text='Clear', command=_clear_canvas).grid(row=1, column=2, columnspan=2, sticky='ew', padx=(10, 1), pady=1)

        # Contextual Text Toolbar
        ui['text_toolbar'] = ttk.Frame(top_frame, padding=(5, 0, 0, 0))
        _create_text_toolbar(ui['text_toolbar'])

    def _create_text_toolbar(parent):
        controls = ttk.Frame(parent)
        controls.pack()
        ttk.Label(controls, text="Font:").grid(row=0, column=0, padx=(0, 2))
        ui['font_family_combo'] = ttk.Combobox(controls, textvariable=app.text_font_family, width=15, values=sorted(font.families()), state=['readonly'])
        ui['font_family_combo'].grid(row=0, column=1, padx=2)
        ui['font_family_combo'].bind('<<ComboboxSelected>>', _update_selected_text_style)

        ttk.Label(controls, text="Size:").grid(row=0, column=2, padx=(5, 2))
        ui['font_size_combo'] = ttk.Combobox(controls, textvariable=app.text_font_size, width=5, values=lv.HW_FONT_SIZES, state='normal')
        ui['font_size_combo'].grid(row=0, column=3, padx=2)
        ui['font_size_combo'].bind('<<ComboboxSelected>>', _update_selected_text_style)
        ui['font_size_combo'].bind('<Return>', _update_selected_text_style)

        ui['bold_button'] = ttk.Button(controls, text='B', width=3, style='Toggle.TButton', command=lambda: _toggle_text_style('bold'))
        ui['bold_button'].grid(row=0, column=4, padx=2)
        ui['italic_button'] = ttk.Button(controls, text='I', width=3, style='Toggle.TButton', command=lambda: _toggle_text_style('italic'))
        ui['italic_button'].grid(row=0, column=5, padx=2)

        ttk.Label(controls, text="Align:").grid(row=0, column=6, padx=(5, 2))
        align_buttons = {'w': 'Left', 'center': 'Center', 'e': 'Right'}
        for i, (align, text) in enumerate(align_buttons.items()):
            btn = ttk.Button(controls, text=text, width=len(text), style='Toggle.TButton', command=lambda a=align: _set_text_alignment(a))
            btn.grid(row=0, column=7 + i, padx=1)
            ui[f'align_{align}_button'] = btn

    def _initialize_state():
        load_session()
        set_tool(app.current_tool.get())
        update_grid()
        _update_ocr_status(OCR_service.INITIALIZING)
        OCR_service.init_ocr_async_service(set_state_callback=_update_ocr_status, print_fn=lambda msg: show_status_message(msg, duration=4000))

    def _bind_events():
        app.hw_root.protocol('WM_DELETE_WINDOW', on_close)
        app.hw_root.unbind_all('<Control-z>')
        app.hw_root.unbind_all('<Control-y>')

        bindings = {
            'file': {'<Control-s>': lambda e: save_canvas(), '<Control-o>': lambda e: _upload_image()},
            'edit': {
                '<Control-z>': undo_action, '<Control-y>': redo_action, '<Delete>': delete_selection,
                '<Control-c>': copy_selection, '<Control-v>': paste_selection,
                '<Up>': lambda e: ui['canvas_frame'].move_selection(0, -1),
                '<Down>': lambda e: ui['canvas_frame'].move_selection(0, 1),
                '<Left>': lambda e: ui['canvas_frame'].move_selection(-1, 0),
                '<Right>': lambda e: ui['canvas_frame'].move_selection(1, 0),
                '<Shift-Up>': lambda e: ui['canvas_frame'].move_selection(0, -10),
                '<Shift-Down>': lambda e: ui['canvas_frame'].move_selection(0, 10),
                '<Shift-Left>': lambda e: ui['canvas_frame'].move_selection(-10, 0),
                '<Shift-Right>': lambda e: ui['canvas_frame'].move_selection(10, 0),
            },
            'tools': {f'<{cfg["shortcut"]}>': (lambda e, t=tool_id: set_tool(t)) for tool_id, cfg in TOOL_CONFIGS.items() if cfg.get('shortcut')}
        }

        for group, b_map in bindings.items():
            if app.shortcuts_enabled[group].get():
                for seq, cmd in b_map.items():
                    app.hw_root.bind(seq, cmd)
            else:
                for seq in b_map: app.hw_root.unbind(seq)

    def update_status_bar():
        tool_name = app.current_tool.get().replace('_', ' ').title()
        ui['status_label'].config(text=f"Tool: {tool_name}")
        zoom_level = ui['canvas_frame'].get_zoom() if ui.get('canvas_frame') else 1.0
        ui['zoom_label'].config(text=f"Zoom: {int(zoom_level * 100)}%")
        update_width_status()

    def update_width_status():
        tool = app.current_tool.get()
        width_var = TOOL_CONFIGS[tool].get('width_var')
        if width_var:
            ui['width_label'].config(text=f"Width: {width_var.get()}")
        else:
            ui['width_label'].config(text="")

    def update_grid(*_args):
        if not ui.get('canvas_frame'): return
    
        # This function can be called by either the checkbutton or the combobox.
        # We need to sync the two widgets and then update the canvas.
        # The `_args` can tell us who the caller was. The checkbutton passes none.
        source_is_combo = bool(_args)
    
        if source_is_combo:
            # Called from the combobox, which is now the source of truth.
            size = app.grid_size.get()
            is_on = (size != 'Off')
            if app.show_grid.get() != is_on:
                app.show_grid.set(is_on)
        else: # Called from the checkbutton
            is_on = app.show_grid.get()
            if is_on:
                # If grid was just turned on, but size is 'Off', pick a default.
                if app.grid_size.get() == 'Off':
                    app.grid_size.set('Medium')
            else:
                # If grid was turned off, set size to 'Off'.
                app.grid_size.set('Off')
    
        # Now that the state variables are synchronized, apply them.
        final_size = app.grid_size.get()
        final_is_on = final_size != 'Off'
    
        ui['canvas_frame'].toggle_grid(final_is_on)
        ui['canvas_frame'].set_grid_size(final_size)
    
        # Make sure the combobox reflects the current state (e.g., if checkbutton turned it off)
        if ui.get('grid_combo') and ui['grid_combo'].get() != final_size:
            ui['grid_combo'].set(final_size)

    def set_tool(mode='pencil'):
        app.current_tool.set(mode)
        if ui.get('canvas_frame'): ui['canvas_frame'].set_tool(mode)
        for name, btn in ui['tool_buttons'].items():
            btn.configure(style='Selected.TButton' if name == mode else 'TButton')
        update_width_display()
        update_status_bar()
        _update_contextual_toolbar()

    def delete_selection(_event=None):
        if ui.get('canvas_frame'):
            ui['canvas_frame'].delete_selection()
            trigger_live_ocr()

    def copy_selection(_event=None):
        if ui.get('canvas_frame'):
            ui['canvas_frame'].copy_selection()
            show_status_message("Selection copied")

    def paste_selection(_event=None):
        if ui.get('canvas_frame'):
            ui['canvas_frame'].paste_selection()
            trigger_live_ocr()
            show_status_message("Pasted from clipboard")

    def update_width_display():
        tool = app.current_tool.get()
        var = TOOL_CONFIGS[tool].get('width_var')
        width_combo = ui['width_combo']
        if not var:
            width_combo.set('')
            width_combo.state(['disabled'])
            return
        width_combo.state(['!disabled'])
        width_combo.configure(textvariable=var)
        if not var.get(): var.set(3)
        update_width_status()

    def on_width_change(*_args):
        try:
            width = int(ui['width_combo'].get())
            tool = app.current_tool.get()
            var = TOOL_CONFIGS[tool].get('width_var')
            if var: var.set(width)
            if ui.get('canvas_frame'): ui['canvas_frame'].set_width(width, tool)
            update_width_status()
        except (ValueError, tk.TclError): pass

    def on_color_change(color, *_args):
        if color == 'Add New...':
            _add_custom_color()
            return
        app.current_color.set(color)
        app.previous_color = color
        if ui.get('canvas_frame'): ui['canvas_frame'].set_color(color)
        _update_selected_text_style()
        _update_remove_button_state()

    def _toggle_text_style(style):
        var_map = {'bold': app.text_font_bold, 'italic': app.text_font_italic}
        var = var_map.get(style)
        if var: var.set(not var.get())
        _update_selected_text_style()

    def _set_text_alignment(align):
        app.text_alignment.set(align)
        _update_selected_text_style()

    def _update_selected_text_style(*_args):
        if not ui.get('canvas_frame'): return
        # Update internal canvas text tool font settings
        ui['canvas_frame'].set_font((app.text_font_family.get(), app.text_font_size.get(), f"{'bold' if app.text_font_bold.get() else ''} {'italic' if app.text_font_italic.get() else ''}".strip()))
        # Update any selected text items
        # This logic is now internal to the rich_canvas, triggered by on_selection_change
        _update_contextual_toolbar()

    def _update_contextual_toolbar(selected_ids=None):
        text_toolbar = ui.get('text_toolbar')
        if not text_toolbar or not ui.get('canvas'): return
        canvas = ui['canvas']
        if selected_ids is None: selected_ids = ui['canvas_frame'].get_selected_items()

        is_text_tool = app.current_tool.get() == 'text'
        is_single_text_selection = len(selected_ids) == 1 and canvas.type(selected_ids[0]) == 'text'
        show_toolbar = is_text_tool or is_single_text_selection

        if show_toolbar:
            text_toolbar.pack(fill='x', pady=(0, 2))
            if is_single_text_selection:
                item_id = selected_ids[0]
                try:
                    font_str = canvas.itemcget(item_id, 'font')
                    actual_font = font.Font(font=font_str)
                    app.text_font_family.set(actual_font.actual('family'))
                    app.text_font_size.set(actual_font.actual('size'))
                    app.text_font_bold.set(actual_font.actual('weight') == 'bold')
                    app.text_font_italic.set(actual_font.actual('slant') == 'italic')
                    app.current_color.set(canvas.itemcget(item_id, 'fill'))
                    app.text_alignment.set(canvas.itemcget(item_id, 'anchor'))
                except (tk.TclError, ValueError): pass
        else:
            text_toolbar.pack_forget()

        ui['bold_button'].state(['selected'] if app.text_font_bold.get() else ['!selected'])
        ui['italic_button'].state(['selected'] if app.text_font_italic.get() else ['!selected'])
        for align, name in [('w', 'left'), ('center', 'center'), ('e', 'right')]:
            if f'align_{align}_button' in ui:
                ui[f'align_{align}_button'].state(['selected'] if app.text_alignment.get() == align else ['!selected'])

    def save_canvas():
        path = fd.asksaveasfilename(defaultextension='.png', filetypes=[('PNG Image', '*.png'), ('All Files', '*.*')], parent=app.hw_root)
        if path and ui.get('canvas_frame'):
            ui['canvas_frame'].save_canvas(path)
            show_status_message(f"Saved to {os.path.basename(path)}")

    def trigger_live_ocr(delay=True):
        if not OCR_service.is_tesseract_installed(): return
        if app.live_ocr_after_id: app.hw_root.after_cancel(app.live_ocr_after_id)
        app.live_ocr_after_id = app.hw_root.after(lv.HW_OCR_TRIGGER_DELAY_MS if delay else 0, perform_live_ocr)

    def perform_live_ocr():
        live_ocr_text = ui.get('live_ocr_text')
        if not live_ocr_text or not live_ocr_text.winfo_exists() or not OCR_service.is_tesseract_installed(): return

        live_ocr_text.config(state=tk.NORMAL)
        yview = live_ocr_text.yview()
        live_ocr_text.delete('1.0', tk.END)

        canvas = ui['canvas']
        bbox = canvas.bbox(lv.HW_TAG_SELECTED_ITEM) if app.ocr_on_selection.get() else canvas.bbox(lv.HW_TAG_ALL)

        data = OCR_service.recognize_text_from_canvas(canvas, bbox, lang=app.ocr_lang.get(), psm=app.ocr_psm.get(), invert=app.ocr_invert_colors.get(), binarize_threshold=app.ocr_binarize_threshold.get())

        if 'error' in data: live_ocr_text.insert('1.0', data['error'])
        elif 'conf' not in data: live_ocr_text.insert('1.0', ' '.join(data.get('text', [])))
        else:
            words_by_line = {}
            for i, word_text in enumerate(data['text']):
                if not word_text.strip(): continue
                line_key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
                if line_key not in words_by_line: words_by_line[line_key] = []
                words_by_line[line_key].append({'text': word_text, 'conf': int(float(data['conf'][i])) if data['conf'][i] != '-1' else -1})

            for line_key in sorted(words_by_line.keys()):
                for word_info in words_by_line[line_key]:
                    start_index = live_ocr_text.index("end-1c")
                    live_ocr_text.insert(tk.END, word_info['text'] + " ")
                    if word_info['conf'] != -1 and word_info['conf'] < app.ocr_confidence_threshold.get():
                        live_ocr_text.tag_add("low_conf", start_index, live_ocr_text.index("end-2c"))
                live_ocr_text.insert(tk.END, "\n")

            final_text = live_ocr_text.get('1.0', 'end-1c').strip()
            if app.auto_copy_ocr.get() and final_text:
                copy_to_clipboard(final_text)

        live_ocr_text.yview_moveto(yview[0])

    def append_to_editor():
        text = ui['live_ocr_text'].get('1.0', 'end-1c')
        if text:
            try: app.EgonTE.insert(tk.INSERT, text)
            except (AttributeError, tk.TclError) as e: messagebox.showerror("Error", f"Failed to append text: {e}", parent=app.hw_root)

    def save_session():
        if not ui.get('canvas_frame'): return False
        session_data = {
            'canvas_data': ui['canvas_frame'].serialize(),
            lv.HW_KEY_OCR_SETTINGS: {
                'lang': app.ocr_lang.get(), 'psm': app.ocr_psm.get(), 'conf': app.ocr_confidence_threshold.get(),
                'auto_copy': app.auto_copy_ocr.get(), 'ocr_selection': app.ocr_on_selection.get(),
                'invert': app.ocr_invert_colors.get(), 'binarize': app.ocr_binarize_threshold.get(),
                'text_align': app.text_alignment.get(),
                'mw_width_change': app.mw_width_change.get(),
            },
            lv.HW_KEY_CUSTOM_COLORS: app.custom_colors,
            lv.HW_KEY_SHORTCUTS: {k: v.get() for k, v in app.shortcuts_enabled.items()}
        }
        try:
            with open(_get_session_path(), 'w') as f: json.dump(session_data, f)
            return True
        except (IOError, TypeError) as e:
            print(f'Failed to save session: {e}')
            return False

    def load_session():
        path = _get_session_path()
        if not os.path.exists(path) or not ui.get('canvas_frame'): return
        try:
            with open(path, 'r') as f: session_data = json.load(f)

            canvas_data = session_data.get('canvas_data', {})
            if canvas_data:
                ui['canvas_frame'].load(canvas_data)

            ocr = session_data.get(lv.HW_KEY_OCR_SETTINGS, {})
            if ocr:
                app.ocr_lang.set(ocr.get('lang', 'eng'))
                app.ocr_psm.set(ocr.get('psm', '6'))
                app.ocr_confidence_threshold.set(ocr.get('conf', 70))
                app.auto_copy_ocr.set(ocr.get('auto_copy', True))
                app.ocr_on_selection.set(ocr.get('ocr_selection', False))
                app.ocr_invert_colors.set(ocr.get('invert', False))
                app.ocr_binarize_threshold.set(ocr.get('binarize', 160))
                app.text_alignment.set(ocr.get('text_align', 'center'))
                app.mw_width_change.set(ocr.get('mw_width_change', False))
                _toggle_mouse_wheel_width_binding()
                psm_name = [k for k, v in lv.HW_OCR_PSM_MODES.items() if v == app.ocr_psm.get()]
                if psm_name: app.ocr_psm_display.set(psm_name[0])

            shortcuts = session_data.get(lv.HW_KEY_SHORTCUTS, {})
            for key, value in shortcuts.items():
                if key in app.shortcuts_enabled: app.shortcuts_enabled[key].set(value)

            app.custom_colors = session_data.get(lv.HW_KEY_CUSTOM_COLORS, [])
            _update_color_widgets()
            update_status_bar()

        except (json.JSONDecodeError, IOError, tk.TclError) as e:
            print(f'Failed to load session: {e}')

    def on_close():
        if not save_session():
            if not messagebox.askyesno("Save Failed", "Could not save session. Close anyway?", parent=app.hw_root): return
        if app.live_ocr_after_id: app.hw_root.after_cancel(app.live_ocr_after_id)
        if hasattr(app, 'hw_shortcuts_root') and app.hw_shortcuts_root.winfo_exists(): app.hw_shortcuts_root.destroy()
        app.hw_root.destroy()
        if hasattr(app, 'hw_root'): delattr(app, 'hw_root')

    def _clear_canvas():
        if messagebox.askyesno('Clear Canvas', 'Are you sure?', parent=app.hw_root) and ui.get('canvas_frame'):
            ui['canvas_frame'].clear()
            trigger_live_ocr(delay=False)

    def undo_action(_event=None):
        if ui.get('canvas_frame'): ui['canvas_frame'].undo()
        trigger_live_ocr(delay=False)

    def redo_action(_event=None):
        if ui.get('canvas_frame'): ui['canvas_frame'].redo()
        trigger_live_ocr(delay=False)

    def _update_undo_redo_buttons(can_undo, can_redo):
        if ui.get('undo_button'): ui['undo_button'].config(state=tk.NORMAL if can_undo else tk.DISABLED)
        if ui.get('redo_button'): ui['redo_button'].config(state=tk.NORMAL if can_redo else tk.DISABLED)

    def _install_ocr_service():
        OCR_service.manual_install_tesseract(set_state_callback=_update_ocr_status, progress_callback=lambda p: app.ocr_install_progress.set(p), print_fn=lambda msg: show_status_message(msg, duration=5000))
        ui['ocr_install_button'].config(state=tk.DISABLED)

    def _update_ocr_status(state_data):
        if not (hasattr(app, 'hw_root') and app.hw_root.winfo_exists()): return
        state, error_msg = (state_data, None) if not isinstance(state_data, tuple) else state_data
        status_label = ui.get('ocr_status_label')
        if not status_label: return

        status_map = {OCR_service.ACTIVE: 'OCR: Active', OCR_service.DISABLED: 'OCR: Not Found', OCR_service.INITIALIZING: 'OCR: Initializing...', OCR_service.DOWNLOADING: 'OCR: Downloading...', OCR_service.EXTRACTING: 'OCR: Extracting...', OCR_service.ERROR: 'OCR: Error'}
        status_label.config(text=status_map.get(state), foreground=UI_COLORS['OCR_STATUS_COLORS'][state])

        is_active = (state == OCR_service.ACTIVE)
        widget_state, combo_state = (tk.NORMAL, 'readonly') if is_active else (tk.DISABLED, 'disabled')
        
        for w_name in ['rerun_ocr_button', 'ocr_conf_slider', 'ocr_invert_check', 'ocr_bin_slider', 'auto_copy_check', 'ocr_selection_check', 'ocr_button', 'copy_ocr_button', 'post_proc_upper', 'post_proc_lower', 'post_proc_clean', 'post_proc_find', 'lang_refresh_button', 'ocr_lang_select_button']:
            if ui.get(w_name): ui[w_name].config(state=widget_state)
        if ui.get('ocr_psm_combo'): ui['ocr_psm_combo'].config(state=combo_state)

        install_manager_frame = ui['ocr_install_manager_frame']
        live_ocr_text_frame = ui['live_ocr_text'].master
        if is_active:
            install_manager_frame.pack_forget()
            live_ocr_text_frame.pack(fill='both', expand=True, pady=(0, 5))
            _update_main_language_selector()
            _populate_language_list()
            trigger_live_ocr(delay=False)
        else:
            live_ocr_text_frame.pack_forget()
            install_manager_frame.pack(fill='both', expand=True, pady=5)
            is_installing = state in [OCR_service.DOWNLOADING, OCR_service.EXTRACTING]
            ui['ocr_progress_bar'].pack(fill='x', padx=10, pady=5) if is_installing else ui['ocr_progress_bar'].pack_forget()
            ui['ocr_install_status_label'].pack(pady=5) if is_installing or state == OCR_service.ERROR else ui['ocr_install_status_label'].pack_forget()
            ui['ocr_install_button'].config(state=tk.DISABLED if is_installing else tk.NORMAL)
            if is_installing: ui['ocr_install_status_label'].config(text=f"Tesseract is {state.lower()}...")
            elif state == OCR_service.ERROR: 
                ui['ocr_install_main_label'].config(text="Installation Failed")
                ui['ocr_install_status_label'].config(text=error_msg)

    def on_psm_change():
        app.ocr_psm.set(lv.HW_OCR_PSM_MODES[app.ocr_psm_display.get()])
        trigger_live_ocr(delay=False)

    def on_conf_change(value, label_var):
        val = int(float(value))
        app.ocr_confidence_threshold.set(val)
        label_var.set(f"Confidence: {val}%")
        trigger_live_ocr(delay=False)

    def on_bin_change(value, label_var):
        val = int(float(value))
        app.ocr_binarize_threshold.set(val)
        label_var.set(f"Binarize: {val}")
        trigger_live_ocr(delay=False)

    # --- Main Execution ---
    if not (hasattr(app, 'hw_root') and app.hw_root.winfo_exists()): return
    theme_service = ThemeService(app)
    UI_COLORS = theme_service.apply_handwriting_style(app.hw_root)
    _create_main_layout()
    _create_canvas_area()
    if not (hasattr(app, 'hw_root') and app.hw_root.winfo_exists()): return
    _create_left_pane_widgets()
    _create_toolbars()
    _bind_events()
    _initialize_state()
