from __future__ import annotations

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import (
    BOTH, RIGHT, Y, DISABLED, NORMAL, END,
    Text, messagebox, simpledialog, filedialog, StringVar, BooleanVar, IntVar,
)
from typing import Any, Optional, List, Dict
from bs4 import BeautifulSoup
import webbrowser
from urllib.parse import urlparse, urlsplit, urlunsplit, urljoin
import csv
import json

from services.security_service import SecurityService


def open_web_scrapping_popup(app: Any) -> None:
    '''
    Web scrapping popup with simple and structured scraping modes.
    '''

    # ---- constants / defaults ----
    MAIN_TITLE = 'Web Scraper'
    FONT_FAMILY = "Segoe UI"
    TITLES_FONT = (FONT_FAMILY, 11, 'bold')
    SUB_TITLES_FONT = (FONT_FAMILY, 9, 'bold')
    BODY_FONT = (FONT_FAMILY, 9)
    INFO_FONT = (FONT_FAMILY, 8)
    SMALL_FONT = (FONT_FAMILY, 7)
    PLACEHOLDER_FG = 'grey'
    PRIMARY_COLOR = '#0078D4'

    SEP_LINE = '\n\n' + ('-' * 30) + '\n\n'
    RETURN_FORMAT_OPTIONS = ['Text Only', 'HTML', 'Attributes', 'Inner Content']

    # ---- helper to resolve Tk owner ----
    def _tk_owner(app_: Any) -> tk.Misc:
        owner = getattr(app_, 'root', None) or getattr(app_, 'master', None)
        if isinstance(owner, tk.Misc):
            return owner
        return app_ if isinstance(app_, tk.Misc) else tk._get_default_root()

    owner = _tk_owner(app)

    # ---- reactive state ----
    state = {
        'connection': True,
        'via_internet': False,
        'status_code': None,
        'final_url': None,
        'last_host': None,
        'last_results_simple': [],
        'last_results_structured': [],
        'column_entries': [],
    }

    # app-bound working fields
    app.wbs_auto_update = bool(getattr(app, 'wbs_auto_update', False))

    # UI state variables
    scraping_mode = StringVar(master=owner, value='simple')
    simple_return_type = StringVar(master=owner, value='Text Only')
    respect_robots = BooleanVar(master=owner, value=True)
    limit_var = IntVar(master=owner, value=200)
    separator_var = BooleanVar(master=owner, value=True)
    https_only = BooleanVar(master=owner, value=True)
    block_credentials = BooleanVar(master=owner, value=True)
    block_ip_hosts = BooleanVar(master=owner, value=True)
    block_private_ip = BooleanVar(master=owner, value=True)
    same_origin_redirects = BooleanVar(master=owner, value=True)
    sanitize_html_v = BooleanVar(master=owner, value=True)
    max_kb_var = IntVar(master=owner, value=2048)
    app._wbs_legal_ack = bool(getattr(app, '_wbs_legal_ack', False))
    legal_ack_var = BooleanVar(master=owner, value=app._wbs_legal_ack)
    warn_meta_robots = BooleanVar(master=owner, value=True)
    paginate_var = BooleanVar(master=owner, value=False)
    max_pages_var = IntVar(master=owner, value=5)

    # UI captured widgets (holders)
    holders = {
        'ws_root': None,
        'file_name_output': None,
        'file_title': None,
        'status_label': None,
        'progress_bar': None,
        'simple_output_box': None,
        'structured_results_tree': None,
        'custom_headers_input': None,
        'row_selector_input': None,
        'pagination_selector_input': None,
        'tag_input': None,
        'class_input': None,
        'simple_controls_frame': None,
        'structured_controls_frame': None,
        'simple_output_frame': None,
        'structured_output_frame': None,
    }

    # ---- Security Service Integration ----
    def _log_security_event(message: str, level: str = "INFO"):
        """Log security events to the status bar or a message box."""
        text = f"Security: {message}"
        if level in ("ERROR", "WARNING"):
            messagebox.showwarning(f"Security {level}", message)
        
        if holders.get('status_label'):
            try:
                holders['status_label'].configure(text=text)
            except tk.TclError:
                pass

    security_service = SecurityService(
        log_callback=_log_security_event,
        app_data=getattr(app, 'app_data', {})
    )

    def _update_security_service_config():
        """Syncs UI settings to the security service instance."""
        security_service.https_only = https_only.get()
        security_service.block_credentials_in_url = block_credentials.get()
        security_service.block_ip_hosts = block_ip_hosts.get()
        security_service.block_private_ip = block_private_ip.get()
        security_service.same_origin_redirects = same_origin_redirects.get()
        security_service.sanitize_html = sanitize_html_v.get()
        security_service.respect_robots_txt = respect_robots.get()
        security_service.max_kb_download = max_kb_var.get()
        security_service.warn_meta_robots = warn_meta_robots.get()
        if legal_ack_var.get():
            security_service.acknowledge_legal_disclaimer()

    def _render(el, mode: str, attr_name: str = None):
        if mode == 'Text Only':
            return el.get_text(strip=True)
        if mode == 'Attributes':
            if attr_name:
                return el.get(attr_name, '')
            return str(el.attrs)
        if mode == 'HTML':
            return el.prettify()
        if mode == 'Inner Content':
            raw = ''.join(map(str, el.contents))
            return security_service.sanitize_html_fragment(raw) if sanitize_html_v.get() else raw
        return el.get_text(strip=True)

    def _ensure_soup_from_editor() -> bool:
        try:
            app.soup = BeautifulSoup(app.EgonTE.get('1.0', 'end'), 'html.parser')
            return True
        except Exception:
            return False

    def _legal_disclaimer(host: Optional[str]) -> bool:
        '''Consolidated legal notice shown once per session.'''
        if security_service._wbs_legal_ack:
            return True
        host_disp = host or 'the target site'
        disclaimer = (
            'Legal notice and user responsibility\n\n'
            f'- You must have permission to access, process, and reproduce content from {host_disp}.\n'
            '- Respect the website’s Terms of Service (ToS), robots.txt, and applicable copyright laws.\n'
            '- Do not scrape personal data or prohibited content.\n'
            '- This tool is provided as-is. The authors and distributors disclaim all liability for misuse.\n\n'
            'By clicking "Yes", you confirm:\n'
            '1) You are legally authorized to access and process the requested content;\n'
            '2) You will comply with applicable laws and site policies;\n'
            '3) You accept that all responsibility lies with you, not the tool’s creators or distributors.'
        )
        try:
            ok = messagebox.askyesno(f'{MAIN_TITLE} - Legal', disclaimer)
        except tk.TclError:
            ok = False
        if ok:
            security_service.acknowledge_legal_disclaimer()
            legal_ack_var.set(True)
        return ok

    def _offer_policy_links(host: str):
        '''Open robots.txt and offer opening a single Terms link (if available).'''
        try:
            base = f'https://{host}'
            webbrowser.open_new_tab(urljoin(base, '/robots.txt'))
            # This part can be improved by using the service's methods in the future
            open_terms = messagebox.askyesno('EgonTE', 'Open the site Terms page (if available)?')
            if open_terms:
                 webbrowser.open_new_tab(urljoin(base, '/terms'))
        except Exception:
            pass

    def _from_url(url: str) -> bool:
        _update_security_service_config()

        original_headers = security_service.UA_HEADERS.copy()
        headers = original_headers.copy()
        if holders.get('custom_headers_input'):
            try:
                custom_headers_str = holders['custom_headers_input'].get('1.0', 'end').strip()
                if custom_headers_str:
                    for line in custom_headers_str.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            headers[key.strip()] = value.strip()
                    security_service.UA_HEADERS = headers
            except Exception as e:
                messagebox.showwarning("Header Error", f"Could not parse custom headers: {e}")
                return False

        try:
            host = urlparse(url if '://' in url else f'https://{url}').hostname
        except Exception:
            host = None
        state['last_host'] = host

        if not security_service.legal_disclaimer(host):
            if not _legal_disclaimer(host):
                return False

        soup, err = security_service.fetch_url_securely(url)
        security_service.UA_HEADERS = original_headers

        if err:
            if "Legal disclaimer" not in err:
                messagebox.showerror('EgonTE', err)
            return False

        if soup:
            app.soup = soup
            state['status_code'] = '200'  # Placeholder
            state['final_url'] = url  # Placeholder
            return True
        
        return False

    def _from_file() -> bool:
        try:
            path = filedialog.askopenfilename(
                title='Open file to scrape',
                filetypes=(('HTML FILES', '*.html'), ('Text Files', '*.txt')),
            )
            if not path:
                return False
            app.wbs_path = path
            with open(app.wbs_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            app.soup = BeautifulSoup(content, 'html.parser')
            return True
        except FileNotFoundError:
            messagebox.showerror('EgonTE', 'File not found.')
        except (IOError, OSError) as e:
            messagebox.showerror('EgonTE', f'Failed to read file: {e}')
        except Exception as e:
            messagebox.showerror('EgonTE', f'Failed to parse file: {e}')
        return False

    def _apply_editor_binding():
        if app.wbs_auto_update:
            _ensure_soup_from_editor()
        else:
            try:
                app.EgonTE.unbind('<KeyRelease>')
                app.EgonTE.bind('<KeyRelease>', app.emoji_detection)
            except tk.TclError:
                pass

    def _update_main_ui_after_upload():
        try:
            if holders['file_name_output']:
                holders['file_name_output'].configure(text=app.wbs_path)
            if holders['file_title']:
                holders['file_title'].configure(text=state['title_text'])
        except tk.TclError:
            pass

    # ---- core actions ----
    def _load_new_content(via: str):
        content_ready = False
        state['via_internet'] = False

        if via == 'this':
            app.wbs_auto_update = True
            state['title_text'] = 'File Name:'
            try:
                app.wbs_path = app.file_name
            except AttributeError:
                app.wbs_path = '(File is not named)'
            content_ready = _ensure_soup_from_editor()
            if not content_ready:
                messagebox.showerror('EgonTE', 'Failed to parse current buffer')
        elif via == 'link':
            app.wbs_auto_update = False
            state['title_text'] = 'Website Link:'
            link = simpledialog.askstring('EgonTE', 'Enter a URL')
            if link:
                app.wbs_path = link
                content_ready = _from_url(link)
                state['via_internet'] = content_ready
                if content_ready and state['last_host']:
                    _offer_policy_links(state['last_host'])
        else:  # 'file'
            app.wbs_auto_update = False
            state['title_text'] = 'File Name:'
            content_ready = _from_file()

        _apply_editor_binding()

        _update_main_ui_after_upload()
        if content_ready:
            search()

    def search():
        _apply_editor_binding()
        if scraping_mode.get() == 'simple':
            _search_simple()
        else:
            _search_structured()

    def _search_simple():
        output_box = holders.get('simple_output_box')
        if not output_box or not output_box.winfo_exists(): return

        output_box.configure(state=NORMAL, fg='black')
        output_box.delete('1.0', END)

        tag_q = holders['tag_input'].get().strip()
        class_q = holders['class_input'].get().strip()
        max_items = limit_var.get()
        use_sep = separator_var.get()

        lines = []
        total = 0
        try:
            if not hasattr(app, 'soup') or app.soup is None: raise RuntimeError('No content loaded')

            elements = []
            if tag_q and class_q:
                elements = app.soup.find_all(tag_q, class_=class_q, limit=max_items)
            elif tag_q:
                elements = app.soup.find_all(tag_q, limit=max_items)
            elif class_q:
                elements = app.soup.find_all(class_=class_q, limit=max_items)
            else:
                elements = [app.soup]

            lines = [_render(el, simple_return_type.get()) for el in elements]
            total = len(lines)

        except Exception as e:
            lines = [f'Error while searching/parsing: {e}']

        state['last_results_simple'] = lines
        content = (SEP_LINE if use_sep else '\n').join(lines) if lines else "Nothing found."
        output_box.insert('1.0', content)
        output_box.configure(state=DISABLED)
        _update_status_info(total, len(content))

    def _search_structured():
        tree = holders.get('structured_results_tree')
        if not tree or not tree.winfo_exists(): return

        for i in tree.get_children(): tree.delete(i)

        row_selector = holders['row_selector_input'].get().strip()
        column_defs = []
        for col_entry in state['column_entries']:
            name = col_entry['name_var'].get().strip()
            selector = col_entry['selector_var'].get().strip()
            fmt = col_entry['format_var'].get()
            attr = col_entry['attr_var'].get().strip()
            if name and selector:
                column_defs.append({'name': name, 'selector': selector, 'format': fmt, 'attribute': attr})

        if not row_selector or not column_defs:
            messagebox.showinfo("Schema Incomplete", "Please define a Row Selector and at least one Column.")
            return

        tree['columns'] = [col['name'] for col in column_defs]
        for col in column_defs:
            tree.heading(col['name'], text=col['name'])
            tree.column(col['name'], width=120, anchor='w')

        all_results = []
        current_url = getattr(app, 'wbs_path', None)
        page_count = 0
        max_pages = max_pages_var.get() if paginate_var.get() else 1

        progress_bar = holders['progress_bar']
        progress_bar.grid(row=0, column=1, sticky='ew', padx=5)
        progress_bar.start()
        holders['ws_root'].update_idletasks()

        try:
            while page_count < max_pages:
                page_count += 1
                _update_status_info(len(all_results), page_count=page_count, scraping=True)
                holders['ws_root'].update_idletasks()

                if not hasattr(app, 'soup') or app.soup is None:
                    if page_count > 1: break
                    messagebox.showerror("Error", "No content loaded.")
                    return

                try:
                    rows = app.soup.select(row_selector)
                    for row_element in rows:
                        if len(all_results) >= limit_var.get(): break
                        result_item = {}
                        for col_def in column_defs:
                            cell_element = row_element.select_one(col_def['selector'])
                            result_item[col_def['name']] = _render(cell_element, col_def['format'],
                                                                   col_def['attribute']) if cell_element else ""
                        all_results.append(result_item)
                    if len(all_results) >= limit_var.get(): break
                except Exception as e:
                    messagebox.showerror("Scraping Error", f"An error on page {page_count}: {e}")
                    break

                if page_count >= max_pages: break
                pagination_selector = holders['pagination_selector_input'].get().strip()
                if not pagination_selector: break

                next_page_el = app.soup.select_one(pagination_selector)
                if not next_page_el or not next_page_el.get('href'): break

                next_page_url = urljoin(current_url, next_page_el.get('href'))
                if not _from_url(next_page_url):
                    messagebox.showwarning("Pagination", f"Could not load next page: {next_page_url}")
                    break
                current_url = state['final_url']
        finally:
            progress_bar.stop()
            progress_bar.grid_forget()

        for item in all_results:
            tree.insert('', END, values=list(item.values()))

        state['last_results_structured'] = all_results
        _update_status_info(len(all_results), page_count=page_count if paginate_var.get() and page_count > 1 else 0)

    def _update_status_info(total_results: int, total_chars: int = 0, page_count: int = 0, scraping: bool = False):
        try:
            if scraping:
                holders['status_label'].configure(text=f"Scraping page {page_count}...")
                return

            if total_results == 0 and total_chars == 0:
                holders['status_label'].configure(text="Ready.")
                return

            info = f'Results: {total_results}'
            if total_results >= limit_var.get():
                info += f' (limited to {limit_var.get()})'
            if total_chars > 0:
                info += f' | Characters: {total_chars}'
            if page_count > 1:
                info += f' | Pages: {page_count}'
            if state['via_internet']:
                if state.get('status_code') is not None:
                    info += f' | HTTP: {state["status_code"]}'
            holders['status_label'].configure(text=info)
        except tk.TclError:
            pass

    def _setup_styles():
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=BODY_FONT)
        style.configure('Title.TLabel', font=TITLES_FONT, background='#f0f0f0', foreground='#333333')
        style.configure('Subtitle.TLabel', font=SUB_TITLES_FONT, background='#f0f0f0', foreground='#555555')
        style.configure('TButton', font=BODY_FONT, padding=[8, 4], background='#e0e0e0', foreground='#333333')
        style.map('TButton', background=[('active', PRIMARY_COLOR)], foreground=[('active', 'white')])
        style.configure('Accent.TButton', font=BODY_FONT, padding=[8, 4], background=PRIMARY_COLOR, foreground='white')
        style.map('Accent.TButton', background=[('active', '#005a9e')])
        style.configure('Tool.TButton', font=BODY_FONT, padding=0, relief='flat', foreground='#cc0000')
        style.map('Tool.TButton', foreground=[('active', '#ff0000')])
        style.configure('TRadiobutton', background='#f0f0f0', font=BODY_FONT)
        style.configure('TCheckbutton', background='#f0f0f0', font=BODY_FONT)
        style.configure('TNotebook', background='#f0f0f0', borderwidth=0)
        style.configure('TNotebook.Tab', font=BODY_FONT, padding=[8, 4], background='#e0e0e0', foreground='#333333')
        style.map('TNotebook.Tab', background=[('selected', PRIMARY_COLOR)], foreground=[('selected', 'white')])
        style.configure('TEntry', font=BODY_FONT, fieldbackground='white', borderwidth=1, relief='solid')
        style.configure('StatusBar.TFrame', background='#e0e0e0')
        style.configure('StatusBar.TLabel', background='#e0e0e0', font=INFO_FONT)

    def _build_source_tab(tab: ttk.Frame):
        file_title = ttk.Label(tab, text="Current Source", style='Subtitle.TLabel')
        file_name_output = ttk.Label(tab, text="(None)", font=BODY_FONT, wraplength=400)
        holders['file_title'], holders['file_name_output'] = file_title, file_name_output

        upload_title = ttk.Label(tab, text='Load New Content', style='Title.TLabel')
        upload_file = ttk.Button(tab, text='From File', command=lambda: _load_new_content('file'))
        upload_this = ttk.Button(tab, text='From This Editor', command=lambda: _load_new_content('this'))
        upload_link = ttk.Button(tab, text='From Link', command=lambda: _load_new_content('link'))

        file_title.grid(row=0, column=0, columnspan=3, sticky='w', padx=5, pady=(5, 1))
        file_name_output.grid(row=1, column=0, columnspan=3, sticky='w', padx=5, pady=(0, 5))
        ttk.Separator(tab, orient='horizontal').grid(row=2, columnspan=3, sticky='ew', padx=5, pady=5)
        upload_title.grid(row=3, column=0, columnspan=3, sticky='w', padx=5, pady=2)
        upload_file.grid(row=4, column=0, padx=5, pady=2, sticky='ew')
        upload_this.grid(row=4, column=1, padx=5, pady=2, sticky='ew')
        upload_link.grid(row=4, column=2, padx=5, pady=2, sticky='ew')
        tab.grid_columnconfigure((0, 1, 2), weight=1)

    def _build_scrape_tab(tab: ttk.Frame):
        mode_frame = ttk.Frame(tab)
        mode_frame.pack(fill='x', pady=(5, 10))
        mode_title = ttk.Label(mode_frame, text='Scraping Mode:', style='Title.TLabel')
        simple_rb = ttk.Radiobutton(mode_frame, text='Simple', variable=scraping_mode, value='simple',
                                    command=_toggle_scraping_mode)
        structured_rb = ttk.Radiobutton(mode_frame, text='Structured', variable=scraping_mode, value='structured',
                                        command=_toggle_scraping_mode)
        mode_title.pack(side='left', padx=(5, 10))
        simple_rb.pack(side='left', padx=5)
        structured_rb.pack(side='left', padx=5)

        # --- Simple Controls ---
        simple_controls = ttk.Frame(tab)
        holders['simple_controls_frame'] = simple_controls

        s_identifiers_title = ttk.Label(simple_controls, text='Identifiers', style='Title.TLabel')
        s_tag_title = ttk.Label(simple_controls, text='By Tag:', style='Subtitle.TLabel')
        s_tag_input = ttk.Entry(simple_controls)
        s_class_title = ttk.Label(simple_controls, text='By Class:', style='Subtitle.TLabel')
        s_class_input = ttk.Entry(simple_controls)
        holders['tag_input'], holders['class_input'] = s_tag_input, s_class_input

        s_return_title = ttk.Label(simple_controls, text='Return Format', style='Title.TLabel')
        s_html_rb = ttk.Radiobutton(simple_controls, text='HTML (prettified)', variable=simple_return_type,
                                    value='HTML')
        s_text_rb = ttk.Radiobutton(simple_controls, text='Text Only', variable=simple_return_type, value='Text Only')
        s_attrs_rb = ttk.Radiobutton(simple_controls, text='Attributes', variable=simple_return_type,
                                     value='Attributes')
        s_content_rb = ttk.Radiobutton(simple_controls, text='Inner Content', variable=simple_return_type,
                                       value='Inner Content')

        s_sep_cb = ttk.Checkbutton(simple_controls, text='Separator between items', variable=separator_var)
        s_search_button = ttk.Button(simple_controls, text='Scrape', command=search, style='Accent.TButton')

        s_identifiers_title.grid(row=0, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        s_tag_title.grid(row=1, column=0, sticky='w', padx=5)
        s_class_title.grid(row=1, column=1, sticky='w', padx=5)
        s_tag_input.grid(row=2, column=0, padx=5, sticky='ew')
        s_class_input.grid(row=2, column=1, padx=5, sticky='ew')
        ttk.Separator(simple_controls, orient='horizontal').grid(row=3, columnspan=2, sticky='ew', padx=5, pady=8)
        s_return_title.grid(row=4, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        s_html_rb.grid(row=5, column=0, sticky='w', padx=5)
        s_text_rb.grid(row=5, column=1, sticky='w', padx=5)
        s_attrs_rb.grid(row=6, column=0, sticky='w', padx=5)
        s_content_rb.grid(row=6, column=1, sticky='w', padx=5)
        ttk.Separator(simple_controls, orient='horizontal').grid(row=7, columnspan=2, sticky='ew', padx=5, pady=8)
        s_sep_cb.grid(row=8, column=0, columnspan=2, sticky='w', padx=5)
        s_search_button.grid(row=9, column=0, columnspan=2, pady=10)
        simple_controls.grid_columnconfigure((0, 1), weight=1)

        # --- Structured Controls ---
        structured_controls = ttk.Frame(tab)
        holders['structured_controls_frame'] = structured_controls

        row_selector_title = ttk.Label(structured_controls, text='Row Selector', style='Title.TLabel')
        row_selector_input = ttk.Entry(structured_controls)
        holders['row_selector_input'] = row_selector_input
        row_selector_title.grid(row=0, column=0, columnspan=3, sticky='w', padx=5, pady=2)
        row_selector_input.grid(row=1, column=0, columnspan=3, sticky='ew', padx=5)

        ttk.Separator(structured_controls, orient='horizontal').grid(row=2, columnspan=3, sticky='ew', padx=5, pady=8)

        columns_title = ttk.Label(structured_controls, text='Columns', style='Title.TLabel')
        columns_frame = ttk.Frame(structured_controls)
        columns_title.grid(row=3, column=0, columnspan=3, sticky='w', padx=5, pady=2)
        columns_frame.grid(row=4, column=0, columnspan=3, sticky='ew', padx=5)
        state['column_entries_frame'] = columns_frame

        def add_column_entry(name="", selector="", fmt="Text Only", attr=""):
            frame = state['column_entries_frame']
            col_frame = ttk.Frame(frame)
            col_frame.pack(fill='x', pady=1)

            name_var = StringVar(value=name)
            selector_var = StringVar(value=selector)
            format_var = StringVar(value=fmt)
            attr_var = StringVar(value=attr)

            name_label = ttk.Label(col_frame, text='Name:')
            name_entry = ttk.Entry(col_frame, textvariable=name_var, width=10)
            selector_label = ttk.Label(col_frame, text='Selector:')
            selector_entry = ttk.Entry(col_frame, textvariable=selector_var, width=15)
            format_label = ttk.Label(col_frame, text='Format:')
            format_combo = ttk.Combobox(col_frame, textvariable=format_var, values=RETURN_FORMAT_OPTIONS, width=10,
                                        state="readonly")
            attr_label = ttk.Label(col_frame, text='Attribute:')
            attr_entry = ttk.Entry(col_frame, textvariable=attr_var, width=8)
            remove_btn = ttk.Button(col_frame, text='x', width=2, style="Tool.TButton",
                                    command=lambda f=col_frame: _remove_column_entry(f))

            def on_format_change(*args):
                if format_var.get() == 'Attributes':
                    attr_label.pack(side='left', padx=(5, 2))
                    attr_entry.pack(side='left', padx=2)
                else:
                    attr_label.pack_forget()
                    attr_entry.pack_forget()

            format_var.trace_add('write', on_format_change)

            name_label.pack(side='left', padx=(0, 2))
            name_entry.pack(side='left', padx=2)
            selector_label.pack(side='left', padx=(5, 2))
            selector_entry.pack(side='left', padx=2, fill='x', expand=True)
            format_label.pack(side='left', padx=(5, 2))
            format_combo.pack(side='left', padx=2)
            remove_btn.pack(side='right', padx=2)
            on_format_change()
            name_entry.focus_set()

            entry_data = {'frame': col_frame, 'name_var': name_var, 'selector_var': selector_var,
                          'format_var': format_var, 'attr_var': attr_var}
            state['column_entries'].append(entry_data)

        _build_scrape_tab.add_column_entry = add_column_entry

        def _remove_column_entry(frame_to_remove):
            frame_to_remove.destroy()
            state['column_entries'] = [entry for entry in state['column_entries'] if entry['frame'].winfo_exists()]

        add_column_btn = ttk.Button(structured_controls, text='Add Column', command=add_column_entry)
        add_column_btn.grid(row=5, column=0, columnspan=3, pady=2)

        st_search_button = ttk.Button(structured_controls, text='Scrape', command=search, style='Accent.TButton')
        st_search_button.grid(row=6, column=0, columnspan=3, pady=10)

        add_column_entry()  # Start with one

    def _build_advanced_tab(tab: ttk.Frame):
        # Pagination
        pagination_title = ttk.Label(tab, text='Pagination (Structured Mode Only)', style='Title.TLabel')
        pagination_cb = ttk.Checkbutton(tab, text='Follow pagination', variable=paginate_var)
        pagination_selector_label = ttk.Label(tab, text='"Next Page" Selector:')
        pagination_selector_input = ttk.Entry(tab)
        holders['pagination_selector_input'] = pagination_selector_input
        max_pages_frame = ttk.Frame(tab)
        max_pages_label = ttk.Label(max_pages_frame, text='Max pages to scrape:')
        max_pages_entry = ttk.Entry(max_pages_frame, width=4, textvariable=max_pages_var)

        pagination_title.grid(row=0, column=0, columnspan=2, sticky='w', padx=5, pady=(5, 2))
        pagination_cb.grid(row=1, column=0, columnspan=2, sticky='w', padx=5)
        pagination_selector_label.grid(row=2, column=0, sticky='w', padx=5, pady=(5, 0))
        pagination_selector_input.grid(row=3, column=0, columnspan=2, sticky='ew', padx=5)
        max_pages_frame.grid(row=4, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        max_pages_label.pack(side='left', padx=(0, 2))
        max_pages_entry.pack(side='left')

        ttk.Separator(tab, orient='horizontal').grid(row=5, columnspan=2, sticky='ew', padx=5, pady=8)

        # Network
        network_title = ttk.Label(tab, text='Network', style='Title.TLabel')
        limit_frame = ttk.Frame(tab)
        limit_title = ttk.Label(limit_frame, text='Limit total results:')
        limit_entry = ttk.Entry(limit_frame, width=6, textvariable=limit_var)
        maxkb_frame = ttk.Frame(tab)
        maxkb_title = ttk.Label(maxkb_frame, text='Max download per page (KB):')
        maxkb_entry = ttk.Entry(maxkb_frame, width=6, textvariable=max_kb_var)

        network_title.grid(row=6, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        limit_frame.grid(row=7, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        limit_title.pack(side='left', padx=(0, 2))
        limit_entry.pack(side='left')
        maxkb_frame.grid(row=8, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        maxkb_title.pack(side='left', padx=(0, 2))
        maxkb_entry.pack(side='left')

        ttk.Separator(tab, orient='horizontal').grid(row=9, columnspan=2, sticky='ew', padx=5, pady=8)

        # Headers
        headers_title = ttk.Label(tab, text='Custom Headers', style='Title.TLabel')
        headers_input = Text(tab, height=4, width=40, font=BODY_FONT, relief='solid', borderwidth=1)
        default_header = f"User-Agent: {security_service.UA_HEADERS['User-Agent']}"
        headers_input.insert('1.0', default_header)
        holders['custom_headers_input'] = headers_input

        headers_title.grid(row=10, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        headers_input.grid(row=11, column=0, columnspan=2, sticky='ew', padx=5, pady=1)

        tab.grid_columnconfigure(0, weight=1)

    def _build_policy_tab(tab: ttk.Frame):
        legal_title = ttk.Label(tab, text='Legal & Site Policy', style='Title.TLabel')
        respect_cb = ttk.Checkbutton(tab, text='Respect robots.txt', variable=respect_robots)
        meta_warn_cb = ttk.Checkbutton(tab, text='Warn on restrictive meta robots', variable=warn_meta_robots)
        open_policies_btn = ttk.Button(
            tab,
            text='Open robots.txt and Terms',
            command=lambda: (_offer_policy_links(state['last_host']) if state['last_host'] else None)
        )

        ack_title = ttk.Label(tab, text='User Acknowledgement', style='Title.TLabel')
        legal_ack_cb = ttk.Checkbutton(
            tab,
            text='I have authorization and accept all legal responsibility',
            variable=legal_ack_var,
            command=lambda: security_service.acknowledge_legal_disclaimer() if legal_ack_var.get() else None
        )

        legal_title.grid(row=0, column=0, columnspan=2, sticky='w', padx=5, pady=(5, 2))
        respect_cb.grid(row=1, column=0, sticky='w', padx=5, pady=1)
        meta_warn_cb.grid(row=2, column=0, sticky='w', padx=5, pady=1)
        open_policies_btn.grid(row=3, column=0, columnspan=2, sticky='ew', padx=5, pady=2)

        ttk.Separator(tab, orient='horizontal').grid(row=4, columnspan=2, sticky='ew', padx=5, pady=8)

        ack_title.grid(row=5, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        legal_ack_cb.grid(row=6, column=0, columnspan=2, sticky='w', padx=5, pady=1)
        tab.grid_columnconfigure(0, weight=1)

    def _get_save_path(title: str, defaultextension: str, filetypes: list[tuple[str, str]]) -> Optional[str]:
        return filedialog.asksaveasfilename(
            title=title,
            defaultextension=defaultextension,
            filetypes=filetypes,
        )

    def _save_simple_results():
        output_box = holders.get('simple_output_box')
        if not output_box: return
        content = output_box.get('1.0', 'end-1c')
        if not content or output_box.cget('fg') == PLACEHOLDER_FG: return messagebox.showwarning('EgonTE',
                                                                                                 'There is no content to save.')

        file_path = _get_save_path('Save Results As', '.txt', [('Text Files', '*.txt'), ('All Files', '*.*')])
        if not file_path: return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo('EgonTE', 'Results saved successfully.')
        except (IOError, OSError) as e:
            messagebox.showerror('EgonTE', f'Error saving file: {e}')

    def _export_to_csv():
        results = state.get('last_results_structured')
        if not results: return messagebox.showwarning('EgonTE', 'There are no results to export.')

        file_path = _get_save_path('Export Results as CSV', '.csv', [('CSV Files', '*.csv')])
        if not file_path: return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                if not results: return
                headers = results[0].keys()
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(results)
            messagebox.showinfo('EgonTE', 'Results exported to CSV successfully.')
        except (IOError, OSError) as e:
            messagebox.showerror('EgonTE', f'Error exporting to CSV: {e}')

    def _export_to_json():
        results = state.get('last_results_structured')
        if not results: return messagebox.showwarning('EgonTE', 'There are no results to export.')

        file_path = _get_save_path('Export Results as JSON', '.json', [('JSON Files', '*.json')])
        if not file_path: return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=4)
            messagebox.showinfo('EgonTE', 'Results exported to JSON successfully.')
        except (IOError, OSError) as e:
            messagebox.showerror('EgonTE', f'Error exporting to JSON: {e}')

    def _save_profile():
        _update_security_service_config()
        profile = {
            'scraping_mode': scraping_mode.get(),
            'tag_q': holders['tag_input'].get(),
            'class_q': holders['class_input'].get(),
            'row_selector': holders['row_selector_input'].get(),
            'columns': [],
            'simple_return_type': simple_return_type.get(),
            'separator': separator_var.get(),
            'paginate': paginate_var.get(),
            'max_pages': max_pages_var.get(),
            'pagination_selector': holders['pagination_selector_input'].get(),
            'limit_results': limit_var.get(),
            'custom_headers': holders['custom_headers_input'].get('1.0', END),
            'respect_robots': security_service.respect_robots_txt,
            'warn_meta_robots': security_service.warn_meta_robots,
            'https_only': security_service.https_only,
            'block_credentials': security_service.block_credentials_in_url,
            'block_ip_hosts': security_service.block_ip_hosts,
            'block_private_ip': security_service.block_private_ip,
            'same_origin_redirects': security_service.same_origin_redirects,
            'sanitize_html': security_service.sanitize_html,
            'max_kb': security_service.max_kb_download,
        }
        for col_entry in state['column_entries']:
            profile['columns'].append({
                'name': col_entry['name_var'].get(),
                'selector': col_entry['selector_var'].get(),
                'format': col_entry['format_var'].get(),
                'attribute': col_entry['attr_var'].get(),
            })

        file_path = _get_save_path('Save Scraper Profile', '.json', [('JSON Profile', '*.json')])
        if not file_path: return
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=4)
            messagebox.showinfo("Profile Saved", "Scraper profile saved successfully.")
        except (IOError, OSError) as e:
            messagebox.showerror("Error", f"Could not save profile: {e}")

    def _load_profile():
        file_path = filedialog.askopenfilename(title='Load Scraper Profile', filetypes=[('JSON Profile', '*.json')])
        if not file_path: return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)

            scraping_mode.set(profile.get('scraping_mode', 'simple'))

            holders['tag_input'].delete(0, END);
            holders['tag_input'].insert(0, profile.get('tag_q', ''))
            holders['class_input'].delete(0, END);
            holders['class_input'].insert(0, profile.get('class_q', ''))
            holders['row_selector_input'].delete(0, END);
            holders['row_selector_input'].insert(0, profile.get('row_selector', ''))

            for entry in state['column_entries']:
                entry['frame'].destroy()
            state['column_entries'].clear()
            for col in profile.get('columns', []):
                _build_scrape_tab.add_column_entry(col.get('name', ''), col.get('selector', ''),
                                                   col.get('format', 'Text Only'), col.get('attribute', ''))

            simple_return_type.set(profile.get('simple_return_type', 'Text Only'))
            separator_var.set(profile.get('separator', True))
            paginate_var.set(profile.get('paginate', False))
            max_pages_var.set(profile.get('max_pages', 5))
            holders['pagination_selector_input'].delete(0, END);
            holders['pagination_selector_input'].insert(0, profile.get('pagination_selector', ''))
            limit_var.set(profile.get('limit_results', 200))
            holders['custom_headers_input'].delete('1.0', END);
            holders['custom_headers_input'].insert('1.0', profile.get('custom_headers', ''))
            
            respect_robots.set(profile.get('respect_robots', True))
            warn_meta_robots.set(profile.get('warn_meta_robots', True))
            https_only.set(profile.get('https_only', True))
            block_credentials.set(profile.get('block_credentials', True))
            block_ip_hosts.set(profile.get('block_ip_hosts', True))
            block_private_ip.set(profile.get('block_private_ip', True))
            same_origin_redirects.set(profile.get('same_origin_redirects', True))
            sanitize_html_v.set(profile.get('sanitize_html', True))
            max_kb_var.set(profile.get('max_kb', 2048))

            _update_security_service_config()
            _toggle_scraping_mode()
            messagebox.showinfo("Profile Loaded", "Scraper profile loaded successfully.")
        except (IOError, OSError, json.JSONDecodeError, KeyError) as e:
            messagebox.showerror("Error",
                                 f"Could not load profile. It may be invalid or from an older version.\n\nError: {e}")

    def _toggle_scraping_mode():
        mode = scraping_mode.get()
        is_simple = mode == 'simple'

        # Clear results and reset status when mode changes
        holders['simple_output_box'].configure(state=NORMAL, fg=PLACEHOLDER_FG)
        holders['simple_output_box'].delete('1.0', END)
        holders['simple_output_box'].insert('1.0', 'Scraped content will appear here.')
        holders['simple_output_box'].configure(state=DISABLED)
        for i in holders['structured_results_tree'].get_children():
            holders['structured_results_tree'].delete(i)
        _update_status_info(0)

        if is_simple:
            holders['structured_controls_frame'].pack_forget()
            holders['simple_controls_frame'].pack(fill='x', expand=True, padx=5, pady=5)
            holders['structured_output_frame'].grid_forget()
            holders['simple_output_frame'].grid(row=0, column=0, sticky='nsew')
        else:
            holders['simple_controls_frame'].pack_forget()
            holders['structured_controls_frame'].pack(fill='x', expand=True, padx=5, pady=5)
            holders['simple_output_frame'].grid_forget()
            holders['structured_output_frame'].grid(row=0, column=0, sticky='nsew')

    def main_ui():
        if not state['connection']:
            return

        ws_root = app.make_pop_ups_window(main_ui, MAIN_TITLE, resizable=(True, True))
        holders['ws_root'] = ws_root
        ws_root.geometry("700x600")
        ws_root.configure(background='#f0f0f0')

        _setup_styles()

        menu = tk.Menu(ws_root)
        ws_root.config(menu=menu)
        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Profile...", command=_save_profile)
        file_menu.add_command(label="Load Profile...", command=_load_profile)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=ws_root.destroy)

        notebook = ttk.Notebook(ws_root)
        notebook.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        tab_source = ttk.Frame(notebook, padding=5)
        tab_scrape = ttk.Frame(notebook, padding=5)
        tab_advanced = ttk.Frame(notebook, padding=5)
        tab_policy = ttk.Frame(notebook, padding=5)

        _build_source_tab(tab_source)
        _build_scrape_tab(tab_scrape)
        _build_advanced_tab(tab_advanced)
        _build_policy_tab(tab_policy)

        notebook.add(tab_source, text='Source')
        notebook.add(tab_scrape, text='Scrape')
        notebook.add(tab_advanced, text='Request & Pagination')
        notebook.add(tab_policy, text='Policy')

        output_frame = ttk.Frame(ws_root)
        output_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=(0, 5))
        output_frame.grid_rowconfigure(0, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        # Simple output
        simple_output_frame = ttk.Frame(output_frame);
        holders['simple_output_frame'] = simple_output_frame
        simple_output_box = Text(simple_output_frame, font=BODY_FONT, relief='solid', borderwidth=1)
        holders['simple_output_box'] = simple_output_box
        simple_output_box.pack(fill=BOTH, expand=True)
        simple_actions = ttk.Frame(simple_output_frame)
        ttk.Button(simple_actions, text='📋 Copy', command=lambda: holders['simple_output_box'].clipboard_append(
            holders['simple_output_box'].get('1.0', 'end-1c'))).pack(side='left', padx=2)
        ttk.Button(simple_actions, text='📄 Insert', command=lambda: app.EgonTE.insert(app.get_pos(),
                                                                                    holders['simple_output_box'].get(
                                                                                        '1.0', 'end-1c'))).pack(
            side='left', padx=2)
        ttk.Button(simple_actions, text='💾 Save As...', command=_save_simple_results).pack(side='left', padx=2)
        simple_actions.pack(fill='x', pady=2)

        # Structured output
        structured_output_frame = ttk.Frame(output_frame);
        holders['structured_output_frame'] = structured_output_frame
        tree_scroll_y = ttk.Scrollbar(structured_output_frame, orient='vertical')
        tree_scroll_x = ttk.Scrollbar(structured_output_frame, orient='horizontal')
        tree = ttk.Treeview(structured_output_frame, yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set,
                            show='headings')
        tree_scroll_y.config(command=tree.yview);
        tree_scroll_x.config(command=tree.xview)
        tree_scroll_y.pack(side=RIGHT, fill=Y);
        tree_scroll_x.pack(side='bottom', fill='x');
        tree.pack(fill=BOTH, expand=True)
        holders['structured_results_tree'] = tree
        structured_actions = ttk.Frame(structured_output_frame)
        ttk.Button(structured_actions, text='📋 Export as CSV', command=_export_to_csv).pack(side='left', padx=2)
        ttk.Button(structured_actions, text='📋 Export as JSON', command=_export_to_json).pack(side='left', padx=2)
        structured_actions.pack(fill='x', pady=2)

        # Context menu for treeview
        tree_menu = tk.Menu(tree, tearoff=0)

        def copy_cell():
            cur_item = tree.focus()
            if not cur_item: return
            col_id = tree.identify_column(holders['ws_root'].winfo_pointerx() - tree.winfo_rootx())
            cell_value = tree.set(cur_item, col_id)
            holders['ws_root'].clipboard_clear()
            holders['ws_root'].clipboard_append(cell_value)

        def copy_row():
            cur_item = tree.focus()
            if not cur_item: return
            row_values = tree.item(cur_item, 'values')
            holders['ws_root'].clipboard_clear()
            holders['ws_root'].clipboard_append('\t'.join(map(str, row_values)))

        tree_menu.add_command(label="Copy Cell Value", command=copy_cell)
        tree_menu.add_command(label="Copy Row", command=copy_row)

        def show_tree_menu(event):
            if tree.identify_row(event.y):
                tree.focus(tree.identify_row(event.y))
                tree_menu.post(event.x_root, event.y_root)

        tree.bind("<Button-3>", show_tree_menu)

        status_bar = ttk.Frame(ws_root, style='StatusBar.TFrame', padding=2)
        status_bar.grid(row=2, column=0, sticky='ew')
        status_label = ttk.Label(status_bar, text='Ready.', style='StatusBar.TLabel')
        status_label.grid(row=0, column=0, sticky='w')
        holders['status_label'] = status_label
        progress_bar = ttk.Progressbar(status_bar, mode='indeterminate')
        holders['progress_bar'] = progress_bar
        status_bar.grid_columnconfigure(1, weight=1)


        ws_root.grid_rowconfigure(1, weight=1)
        ws_root.grid_columnconfigure(0, weight=1)

        _toggle_scraping_mode()

        if hasattr(app, 'soup') and app.soup:
            search()

    def _show_source_selector():
        def _handle_link_source():
            url = app.link_entry.get().strip()
            _update_security_service_config()
            ok, message, host = security_service.validate_url_policy(url)
            if not ok:
                url_error.configure(text=message or "Invalid URL")
                return False
            
            app.wbs_path = url
            if not _legal_disclaimer(host): return False
            
            content_ready = _from_url(url)
            if content_ready:
                state['via_internet'] = True
                if state['last_host']:
                    _offer_policy_links(state['last_host'])
            return content_ready

        def _handle_this_source():
            app.wbs_auto_update = True
            state['title_text'] = 'File Name:'
            try:
                app.wbs_path = app.file_name
            except AttributeError:
                app.wbs_path = '(File is not named)'
            content_ready = _ensure_soup_from_editor()
            if not content_ready:
                messagebox.showerror('EgonTE', 'Failed to parse current buffer')
            return content_ready

        def _handle_file_source():
            app.wbs_auto_update = False
            state['title_text'] = 'File Name:'
            return _from_file()

        def _enter(event=False):
            mode = state['chosen_init']
            content_ready = False
            if mode == 'link':
                content_ready = _handle_link_source()
            elif mode == 'this':
                content_ready = _handle_this_source()
            else:
                content_ready = _handle_file_source()

            if content_ready:
                try:
                    if getattr(app, 'init_root', None) and app.init_root.winfo_exists():
                        app.init_root.destroy()
                except tk.TclError:
                    pass
                app.open_windows_control(main_ui)

        init_root = app.make_pop_ups_window(None, custom_title=f'{MAIN_TITLE} - Choose Source',
                                            resizable=(False, False), modal=False, topmost=False)
        app.init_root = init_root
        init_root.geometry("450x250")
        init_root.configure(background='#f0f0f0')
        _setup_styles()

        title_label = ttk.Label(init_root, text='Select Content Source to Scrape', style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky='w')

        link_btn = ttk.Button(init_root, text='Scrape website by link', command=lambda: _change('link'))
        this_btn = ttk.Button(init_root, text='Scrape current editor', command=lambda: _change('this'))
        file_btn = ttk.Button(init_root, text='Scrape a local file', command=lambda: _change('file'))
        enter_btn = ttk.Button(init_root, text='Enter', command=_enter, style='Accent.TButton')

        app.link_entry = ttk.Entry(init_root, width=30)
        url_error = ttk.Label(init_root, text='', foreground='red', font=INFO_FONT)
        app.link_entry.bind('<Return>', _enter)

        hint_label = ttk.Label(init_root, text='Mode selected: link', font=INFO_FONT)

        def _change(mode: str):
            state['chosen_init'] = mode
            hint_label.configure(text=f'Mode selected: {mode.capitalize()}')
            if mode == 'link':
                app.link_entry.grid(row=3, column=0, columnspan=3, padx=5, pady=2, sticky='ew')
                url_error.grid(row=4, column=0, columnspan=3, padx=5, pady=(0, 2), sticky='w')
                app.link_entry.focus_set()
            else:
                app.link_entry.grid_remove()
                url_error.grid_remove()

        link_btn.grid(row=1, column=0, padx=(5, 2), pady=4, sticky='ew')
        this_btn.grid(row=1, column=1, padx=2, pady=4, sticky='ew')
        file_btn.grid(row=1, column=2, padx=(2, 5), pady=4, sticky='ew')
        hint_label.grid(row=2, column=0, columnspan=2, padx=5, sticky='w')
        enter_btn.grid(row=2, column=2, padx=(2, 5), pady=5, sticky='e')

        init_root.grid_columnconfigure((0, 1, 2), weight=1)

        try:
            init_root.update_idletasks()
            pr = init_root.master if init_root.master else init_root
            x = pr.winfo_rootx() + (pr.winfo_width() - init_root.winfo_width()) // 2
            y = pr.winfo_rooty() + (pr.winfo_height() - init_root.winfo_height()) // 3
            init_root.geometry(f'+{x}+{y}')
        except tk.TclError:
            pass
        _change('link')

    _show_source_selector()
