from __future__ import annotations

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import (
    BOTH, RIGHT, Y, DISABLED,
    Text, Entry, Button, Label, Radiobutton, Checkbutton,
    messagebox, simpledialog, filedialog, StringVar, BooleanVar, IntVar,
)
from typing import Any, Optional, Tuple
import requests
from bs4 import BeautifulSoup


def open_web_scrapping_popup(app: Any) -> None:
    '''
    Web scrapping popup (refactored, safe, and polished).

    Key features:
    - Initial selector window with clearly labeled options:
      "Scrape website by link", "Scrape current editor (this file)", "Scrape a local HTML/TXT file".
    - For link scraping, opens a dedicated modal to capture a URL with validation and IDs.
    - Legal safety: a consolidated legal notice shown once per session; robots.txt compliance; size/content-type limits.
    - Security: HTTPS-only (toggle), block credentials in URL, block IP-literal/private hosts (anti-SSRF), same-origin redirects.
    - UI layout: main popup uses ttk.Notebook tabs (Filters & Return, Options, Safety & Legal) and a scrollable output panel.
    - Sanitization: strips scripts/iframes and inline handlers; blocks javascript: URLs in attributes.
    - Developer hooks: [handlers:validate_url], [handlers:after_link_ok], [handlers:on_selector_change], [handlers:on_selector_enter].
    '''

    # ---- helper to resolve Tk owner (must be defined before using tkinter Variables) ----
    def _tk_owner(app_: Any) -> tk.Misc:
        owner = getattr(app_, 'root', None) or getattr(app_, 'master', None)
        if isinstance(owner, tk.Misc):
            return owner
        return app_ if isinstance(app_, tk.Misc) else tk._get_default_root()


    owner = _tk_owner(app)

    # ---- constants / defaults ----
    sub_titles_font = 'arial 12 underline'
    UA_HEADERS = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'DNT': '1',
    }
    REQ_TIMEOUT = 10
    SEP_LINE = '\n\n' + ('-' * 30) + '\n\n'
    ALLOWED_CT = {'text/html', 'application/xhtml+xml', 'application/xml', 'text/xml', 'text/plain'}
    BLOCKED_TLDS = {'.onion'}  # extend as needed
    TERMS_PATHS = ('/terms', '/terms-of-service', '/tos', '/legal/terms', '/terms-and-conditions')

    # ---- reactive state ----
    state = {
        'connection': True,
        'via_internet': False,
        'chosen_init': 'link',
        'status_code': None,
        'title_text': 'file name:',
        'final_url': None,
        'last_host': None,
    }

    # app-bound working fields; initialize if missing
    app.wbs_auto_update = bool(getattr(app, 'wbs_auto_update', False))
    app.pre_bd_this = getattr(app, 'pre_bd_this', 1)
    app.pre_bd_link = getattr(app, 'pre_bd_link', 1)
    app.pre_bd_file = getattr(app, 'pre_bd_file', 1)

    # return type, default: prettified HTML
    return_type = StringVar(master=owner, value='html')

    # legality and UX controls
    respect_robots = BooleanVar(master=owner, value=True)
    limit_var = IntVar(master=owner, value=200)
    separator_var = BooleanVar(master=owner, value=True)

    # security controls
    https_only = BooleanVar(master=owner, value=True)
    block_credentials = BooleanVar(master=owner, value=True)
    block_ip_hosts = BooleanVar(master=owner, value=True)
    block_private_ip = BooleanVar(master=owner, value=True)
    same_origin_redirects = BooleanVar(master=owner, value=True)
    sanitize_html_v = BooleanVar(master=owner, value=True)
    max_kb_var = IntVar(master=owner, value=2048)  # 2MB

    # legal/TOS assist
    app._wbs_legal_ack = bool(getattr(app, '_wbs_legal_ack', False))
    legal_ack_var = BooleanVar(master=owner, value=False)
    warn_meta_robots = BooleanVar(master=owner, value=True)

    # UI captured widgets (holders)
    holders = {
        'ws_root': None,            # main popup root
        'file_name_output': None,
        'upload_btns': [],          # list[Button]
        'file_title': None,
        'tag_input': None,          # Entry
        'class_input': None,        # Entry
        'result_info': None,        # Label
        'output_frame': None,       # Frame
    }

    # ---- Event handler hooks (customization points) ----
    # [handlers:validate_url] -> replace or extend _basic_url_validator()
    # [handlers:after_link_ok] -> actions after user enters a valid URL in the modal
    # [handlers:on_selector_change] -> actions when the initial mode changes
    # [handlers:on_selector_enter] -> actions when Enter is pressed in initial window

    def _explain(subject: str):
        if subject == 'tag':
            explanation = 'HTML tags are simple instructions that tell a web browser how to format text'
            example = '<b> Bold Tag </b>'
        else:
            explanation = 'The HTML class attribute is used to specify a class for an HTML element'
            example = '<p class="ThisIsAClassName">HI</p>'
        messagebox.showinfo('web scrapping', f'Explanation:\n{explanation}.\nExample:\n{example}')

    def _reset_borders():
        app.pre_bd_file = app.pre_bd_link = app.pre_bd_this = 1

    def _set_border_for(via: str):
        if via == 'link':
            app.pre_bd_link = 2
        elif via == 'this':
            app.pre_bd_this = 2
        else:
            app.pre_bd_file = 2

    def _sanitize_html_fragment(html_str: str) -> str:
        try:
            soup = BeautifulSoup(html_str, 'html.parser')
            for tag in soup(['script', 'iframe', 'object', 'embed', 'style', 'link', 'meta']):
                tag.decompose()
            for el in soup.find_all(True):
                for attr in list(el.attrs.keys()):
                    if attr.lower().startswith('on'):
                        el.attrs.pop(attr, None)
                    elif attr.lower() in {'href', 'src'}:
                        val = str(el.attrs.get(attr, ''))
                        if val.strip().lower().startswith('javascript:'):
                            el.attrs.pop(attr, None)
            return soup.prettify()
        except Exception:
            return html_str

    def _render(el):
        mode = return_type.get()
        if mode == 'text':
            return el.get_text(strip=False)
        if mode == 'attrs':
            return str(el.attrs)
        if mode == 'content':
            raw = ''.join(map(str, el.contents))
            return _sanitize_html_fragment(raw) if sanitize_html_v.get() else raw
        html = el.prettify()
        return _sanitize_html_fragment(html) if sanitize_html_v.get() else html

    def _ensure_soup_from_editor() -> bool:
        try:
            app.soup = BeautifulSoup(app.EgonTE.get('1.0', 'end'), 'html.parser')
            return True
        except Exception:
            return False

    def _robots_allows(url: str) -> bool:
        try:
            from urllib.parse import urlsplit, urlunsplit
            import urllib.robotparser as robotparser
            parts = urlsplit(url if '://' in url else f'https://{url}')
            if not parts.netloc:
                return True
            robots_url = urlunsplit((parts.scheme or 'https', parts.netloc, '/robots.txt', '', ''))
            rp = robotparser.RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch(UA_HEADERS.get('User-Agent', '*'), urlunsplit(parts))
        except Exception:
            return True

    def _validate_url_policy(url: str) -> tuple[bool, Optional[str], Optional[str]]:
        try:
            from urllib.parse import urlparse
            import ipaddress, socket
            parsed = urlparse(url if '://' in url else f'https://{url}')
            scheme = (parsed.scheme or '').lower()
            host = (parsed.hostname or '').strip('[]') if parsed.hostname else ''
            if https_only.get() and scheme != 'https':
                return False, 'Only HTTPS connections are allowed (toggle in Safety).', host
            if any(host.endswith(b) for b in BLOCKED_TLDS):
                return False, 'Domain TLD is blocked by policy.', host
            if block_credentials.get() and (parsed.username or parsed.password):
                return False, 'Credentials in URL are blocked.', host

            def _is_ip_literal(h: str) -> bool:
                try:
                    import ipaddress as _ipa
                    _ipa.ip_address(h)
                    return True
                except Exception:
                    return False

            if block_ip_hosts.get() and _is_ip_literal(host):
                return False, 'Literal IP addresses are blocked.', host
            if block_private_ip.get() and host:
                try:
                    addrs = {ai[4][0] for ai in socket.getaddrinfo(host, None)}
                    for a in addrs:
                        try:
                            import ipaddress as _ipa2
                            ip = _ipa2.ip_address(a)
                            if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local or ip.is_multicast:
                                return False, 'Host resolves to a private/reserved address (blocked).', host
                        except Exception:
                            continue
                except Exception:
                    pass
            return True, None, host
        except Exception as e:
            return False, f'URL validation failed: {e}', None

    def _legal_disclaimer(host: Optional[str]) -> bool:
        '''Consolidated legal notice shown once per session.'''
        if app._wbs_legal_ack:
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
            ok = messagebox.askyesno('web scrapping - Legal', disclaimer)
        except Exception:
            ok = False
        if ok:
            app._wbs_legal_ack = True  # show once per session
        return ok

    def _offer_policy_links(host: str):
        '''Open robots.txt and offer opening a single Terms link (if available).'''
        try:
            import webbrowser
            import urllib.parse as _up
            base = f'https://{host}'
            webbrowser.open_new_tab(_up.urljoin(base, '/robots.txt'))
            terms_candidates = [base + p for p in TERMS_PATHS]
            open_terms = messagebox.askyesno('EgonTE', 'Open the site Terms page (if available)?')
            if not open_terms:
                return
            try:
                for t in terms_candidates:
                    try:
                        r = requests.head(t, headers=UA_HEADERS, timeout=3, allow_redirects=True)
                        if int(getattr(r, 'status_code', 0)) < 400:
                            webbrowser.open_new_tab(t)
                            break
                    except Exception:
                        continue
            except Exception:
                webbrowser.open_new_tab(terms_candidates[0])
        except Exception:
            pass

    def _check_meta_robots_and_warn():
        if not warn_meta_robots.get():
            return
        try:
            tag = app.soup.find('meta', attrs={'name': lambda v: v and v.lower() == 'robots'})
            if not tag:
                return
            content = (tag.get('content') or '').lower()
            flags = {s.strip() for s in content.split(',')}
            if {'noindex', 'nosnippet', 'noarchive'} & flags:
                messagebox.showwarning('EgonTE', 'Page indicates restrictive meta robots policy (e.g., noindex/nosnippet). Proceed responsibly.')
        except Exception:
            pass

    def _from_url(url: str) -> bool:
        if respect_robots.get() and not _robots_allows(url):
            messagebox.showerror('EgonTE', 'robots.txt disallows scraping this URL path.\nTo proceed anyway, uncheck "Respect robots.txt".')
            return False
        ok, err, host = _validate_url_policy(url)
        state['last_host'] = host
        if not ok:
            messagebox.showerror('EgonTE', err or 'URL blocked by policy.')
            return False
        # Note: legal notice handled once per session before calling _from_url
        try:
            sess = requests.Session()
            resp = sess.get(url, headers=UA_HEADERS, timeout=REQ_TIMEOUT, allow_redirects=True, stream=True)
            resp.raise_for_status()

            if same_origin_redirects.get() and resp.history:
                from urllib.parse import urlparse
                orig_host = (urlparse(url if '://' in url else f'https://{url}').hostname or '').lower()
                for h in resp.history:
                    redir_host = (urlparse(getattr(h, 'url', '')).hostname or '').lower()
                    if redir_host and redir_host != orig_host:
                        messagebox.showerror('EgonTE', 'Cross-origin redirect blocked by policy.')
                        return False

            ct = (resp.headers.get('Content-Type') or '').split(';', 1)[0].strip().lower()
            if ct and ct not in ALLOWED_CT:
                messagebox.showerror('EgonTE', f'Blocked by Content-Type policy: {ct}')
                return False

            max_bytes = max(1, int(max_kb_var.get() or 1)) * 1024
            chunks = []
            total = 0
            for chunk in resp.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                total += len(chunk)
                if total > max_bytes:
                    messagebox.showerror('EgonTE', f'Content exceeds size limit ({max_kb_var.get()} KB).')
                    return False
                chunks.append(chunk)
            data = b''.join(chunks)

            app.soup = BeautifulSoup(data, 'html.parser')
            state['status_code'] = getattr(resp, 'status_code', None)
            state['final_url'] = getattr(resp, 'url', url)

            _check_meta_robots_and_warn()
            return True
        except requests.exceptions.ConnectionError:
            messagebox.showerror('EgonTE', 'Device not connected to internet')
            state['connection'] = False
        except requests.exceptions.InvalidURL:
            messagebox.showerror('EgonTE', 'Invalid URL')
        except requests.exceptions.RequestException as e:
            messagebox.showerror('EgonTE', f'Error fetching URL: {e}')
        except Exception as e:
            messagebox.showerror('EgonTE', f'Unexpected error: {e}')
        return False

    def _from_file() -> bool:
        try:
            app.wbs_path = filedialog.askopenfilename(
                title='Open file to scrape',
                filetypes=(('HTML FILES', '*.html'), ('Text Files', '*.txt')),
            )
            if not app.wbs_path:
                return False
            with open(app.wbs_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            app.soup = BeautifulSoup(content, 'html.parser')
            return True
        except FileNotFoundError:
            messagebox.showerror('EgonTE', 'file not found')
        except Exception as e:
            messagebox.showerror('EgonTE', f'Failed to read/parse file: {e}')
        return False

    def _apply_editor_binding():
        if app.wbs_auto_update:
            _ensure_soup_from_editor()
        else:
            try:
                app.EgonTE.unbind('<KeyRelease>')
                app.EgonTE.bind('<KeyRelease>', app.emoji_detection)
            except Exception:
                pass

    # ---- core actions ----
    def comb_upload(via: str, initial_ws: bool = False):
        _reset_borders()
        content_ready = False
        state['via_internet'] = False

        if initial_ws:
            try:
                app.init_root.destroy()
            except Exception:
                pass

        if via == 'this':
            app.wbs_auto_update = True
            state['title_text'] = 'file name:'
            try:
                app.wbs_path = app.file_name
            except Exception:
                app.wbs_path = '(File is not named)'
            content_ready = _ensure_soup_from_editor()
            if not content_ready:
                messagebox.showerror('EgonTE', 'Failed to parse current buffer')
        elif via == 'link':
            app.wbs_auto_update = False
            state['title_text'] = 'website link:'
            link = simpledialog.askstring('EgonTE', 'Enter a path')
            if link:
                app.wbs_path = link
                # Consolidated legal notice (once per session)
                if not _legal_disclaimer(None):
                    return
                content_ready = _from_url(link)
                state['via_internet'] = content_ready
                if content_ready and state['last_host']:
                    _offer_policy_links(state['last_host'])
        else:
            app.wbs_auto_update = False
            state['title_text'] = 'file name:'
            content_ready = _from_file()

        _set_border_for(via)
        _apply_editor_binding()

        if initial_ws:
            if content_ready:
                # Open main UI; search will be triggered automatically if soup exists
                app.open_windows_control(main_ui)
            return

        try:
            if holders['file_name_output']:
                holders['file_name_output'].configure(text=app.wbs_path)
            for btn, bd in zip(holders['upload_btns'], (app.pre_bd_file, app.pre_bd_this, app.pre_bd_link)):
                try:
                    btn.configure(bd=bd)
                except Exception:
                    pass
            if holders['file_title']:
                holders['file_title'].configure(text=state['title_text'])
        except Exception:
            pass

        search()

    def search():
        _apply_editor_binding()

        if not holders['ws_root']:
            return

        try:
            if holders['output_frame'] and holders['output_frame'].winfo_exists():
                holders['output_frame'].destroy()
        except Exception:
            pass

        output_frame = tk.Frame(holders['ws_root'])
        holders['output_frame'] = output_frame
        text_frame = tk.Frame(output_frame)
        scroll = ttk.Scrollbar(text_frame)
        output_box = Text(text_frame)

        # expand with window (below notebook)
        try:
            holders['ws_root'].grid_rowconfigure(2, weight=1)
            holders['ws_root'].grid_columnconfigure(0, weight=1)
            holders['ws_root'].grid_columnconfigure(1, weight=1)
        except Exception:
            pass

        output_frame.grid(row=2, column=0, columnspan=2, sticky='nsew', pady=(2, 0), padx=6)
        text_frame.pack(fill=BOTH, expand=True)
        scroll.pack(side=RIGHT, fill=Y)
        output_box.pack(fill=BOTH, expand=True)
        scroll.config(command=output_box.yview)
        output_box.config(yscrollcommand=scroll.set)

        # actions row
        actions = tk.Frame(output_frame)
        actions.pack(fill='x', pady=(4, 0))

        def _copy_text():
            text = output_box.get('1.0', 'end')
            try:
                # prefer project-level copy if available
                copy(text)  # type: ignore[name-defined]
            except Exception:
                try:
                    holders['ws_root'].clipboard_clear()
                    holders['ws_root'].clipboard_append(text)
                except Exception:
                    pass

        Button(actions, text='Copy', command=_copy_text).pack(side='left', padx=4, pady=4)
        Button(actions, text='Insert', command=lambda: app.EgonTE.insert(app.get_pos(), output_box.get('1.0', 'end'))).pack(side='left', padx=4, pady=4)

        # queries and limits
        tag_q = holders['tag_input'].get().strip() if holders['tag_input'] and holders['tag_input'].get() else ''
        class_q = holders['class_input'].get().strip() if holders['class_input'] and holders['class_input'].get() else ''
        max_items = max(0, int(limit_var.get() or 0))
        use_sep = bool(separator_var.get())

        lines, total = [], 0
        try:
            if not hasattr(app, 'soup') or app.soup is None:
                raise RuntimeError('No content loaded')

            def _append(el):
                nonlocal total
                if max_items and len(lines) >= max_items:
                    return
                lines.append(_render(el))
                total += 1

            if tag_q and class_q:
                for el in app.soup.find_all(tag_q, class_=class_q):
                    _append(el)
            elif tag_q:
                for el in app.soup.find_all(tag_q):
                    _append(el)
            elif class_q:
                for el in app.soup.find_all(class_=class_q):
                    _append(el)
            else:
                lines.append(_render(app.soup))
                total = 1
        except Exception as e:
            lines = [f'Error while searching/parsing: {e}']
            total = 0

        content = (SEP_LINE if use_sep else '\n').join(lines) if lines else "Nothing found / the tool isn't support this type of search yet!"
        output_box.insert('end', str(content))
        output_box.configure(state=DISABLED)

        # update result info
        try:
            txt_len = len(content) if isinstance(content, str) else 0
            info = f'Results: {total}'
            if max_items and total >= max_items:
                info += f' (limited to {max_items})'
            info += f' | Characters: {txt_len}'
            if state['via_internet']:
                if state.get('status_code') is not None:
                    info += f' | HTTP: {state["status_code"]}'
                if state.get('final_url'):
                    info += ' | Redirected' if str(state['final_url']) != str(app.wbs_path) else ''
            if holders['result_info']:
                holders['result_info'].configure(text=info)
        except Exception:
            pass

    def main_ui():
        if not state['connection']:
            return

        # Create popup with reasonable geometry and resizable to avoid oversized UI issues
        ws_root = app.make_pop_ups_window(
            main_ui,
            'web scrapping',
            resizable=(True, True)
        )
        holders['ws_root'] = ws_root

        # --- header / info ---
        info_title = Label(ws_root, text='Quick information', font=getattr(app, 'titles_font', 'arial 12 bold'))
        holders['result_info'] = Label(ws_root, text='', font='arial 9')
        info_title.grid(row=0, column=0, sticky='w', padx=8, pady=(4, 0))
        holders['result_info'].grid(row=0, column=1, sticky='e', padx=8, pady=(4, 0))

        # Notebook to organize content: Filters/Return, Options, Safety/Legal
        notebook = ttk.Notebook(ws_root)
        notebook.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=6, pady=6)

        # Configure expansion to ensure internal scrollable area grows
        try:
            ws_root.grid_rowconfigure(1, weight=1)
            ws_root.grid_rowconfigure(2, weight=1)
            ws_root.grid_columnconfigure(0, weight=1)
            ws_root.grid_columnconfigure(1, weight=1)
        except Exception:
            pass

        # Tab 1: Filters & Return
        tab_filters = ttk.Frame(notebook)
        notebook.add(tab_filters, text='Filters & Return')

        file_title = Label(tab_filters, text=state['title_text'], font=sub_titles_font)
        file_name_output = Label(tab_filters, text=getattr(app, 'wbs_path', ''))
        holders['file_title'], holders['file_name_output'] = file_title, file_name_output

        upload_title = Label(tab_filters, text='Upload a new content', font=getattr(app, 'titles_font', 'arial 12 bold'))
        upload_file = Button(tab_filters, text='Upload via file', command=lambda: comb_upload('file'), bd=app.pre_bd_file)
        upload_this = Button(tab_filters, text='Upload this file', command=lambda: comb_upload('this'), bd=app.pre_bd_this)
        upload_link = Button(tab_filters, text='Upload via link', command=lambda: comb_upload('link'), bd=app.pre_bd_link)
        holders['upload_btns'] = [upload_file, upload_this, upload_link]

        identifiers_title = Label(tab_filters, text='Identifiers', font=getattr(app, 'titles_font', 'arial 12 bold'))
        tag_title = Label(tab_filters, text='tags:', font=sub_titles_font)
        tag_input = Entry(tab_filters)
        tag_ex = Button(tab_filters, text='?', command=lambda: _explain('tag'), bd=0)
        class_title = Label(tab_filters, text='classes:', font=sub_titles_font)
        class_input = Entry(tab_filters)
        class_ex = Button(tab_filters, text='?', command=lambda: _explain('class'), bd=0)
        holders['tag_input'], holders['class_input'] = tag_input, class_input

        return_title = Label(tab_filters, text='Return', font=getattr(app, 'titles_font', 'arial 12 bold'))
        html_rb = Radiobutton(tab_filters, text='HTML (prettified)', variable=return_type, value='html')
        text_rb = Radiobutton(tab_filters, text='Only text', variable=return_type, value='text')
        attrs_rb = Radiobutton(tab_filters, text='Only attributes', variable=return_type, value='attrs')
        content_rb = Radiobutton(tab_filters, text='Inner content', variable=return_type, value='content')

        search_button = Button(tab_filters, text='Search', command=search)

        # Layout for Tab 1
        file_title.grid(row=0, column=0, sticky='w', padx=6)
        file_name_output.grid(row=1, column=0, sticky='w', padx=6, pady=(0, 6))
        upload_title.grid(row=2, column=0, sticky='w', padx=6)
        upload_file.grid(row=3, column=0, padx=6, pady=2, sticky='w')
        upload_this.grid(row=3, column=1, padx=6, pady=2, sticky='w')
        upload_link.grid(row=3, column=2, padx=6, pady=2, sticky='w')

        identifiers_title.grid(row=4, column=0, sticky='w', padx=6, pady=(6, 0))
        tag_title.grid(row=5, column=0, sticky='w', padx=6)
        class_title.grid(row=5, column=2, sticky='w')
        tag_input.grid(row=6, column=0, padx=6, sticky='we')
        class_input.grid(row=6, column=2, padx=6, sticky='we')
        tag_ex.grid(row=7, column=0, sticky='w', padx=6, pady=(0, 4))
        class_ex.grid(row=7, column=2, sticky='w', padx=6, pady=(0, 4))

        return_title.grid(row=8, column=0, sticky='w', padx=6, pady=(4, 0))
        html_rb.grid(row=9, column=0, sticky='w', padx=6)
        text_rb.grid(row=9, column=1, sticky='w', padx=6)
        attrs_rb.grid(row=9, column=2, sticky='w', padx=6)
        content_rb.grid(row=10, column=1, sticky='w', padx=6)
        search_button.grid(row=11, column=1, pady=8)

        try:
            tab_filters.grid_columnconfigure(0, weight=1)
            tab_filters.grid_columnconfigure(1, weight=1)
            tab_filters.grid_columnconfigure(2, weight=1)
        except Exception:
            pass

        # Tab 2: Options
        tab_options = ttk.Frame(notebook)
        notebook.add(tab_options, text='Options')

        options_title = Label(tab_options, text='Options', font=getattr(app, 'titles_font', 'arial 12 bold'))
        respect_cb = Checkbutton(tab_options, text='Respect robots.txt', variable=respect_robots)
        sep_cb = Checkbutton(tab_options, text='Separator between items', variable=separator_var)
        limit_title = Label(tab_options, text='Limit results:', font='arial 10')
        limit_entry = Entry(tab_options, width=6)
        try:
            limit_entry.insert('end', str(limit_var.get()))
            limit_entry.bind('<KeyRelease>', lambda e: limit_var.set(int(limit_entry.get() or 0)) if limit_entry.get().isdigit() else None)
        except Exception:
            pass

        options_title.grid(row=0, column=0, sticky='w', padx=6, pady=(6, 0))
        respect_cb.grid(row=1, column=0, sticky='w', padx=6, pady=2)
        sep_cb.grid(row=1, column=1, sticky='w', padx=6, pady=2)
        limit_title.grid(row=2, column=0, sticky='e', padx=6, pady=2)
        limit_entry.grid(row=2, column=1, sticky='w', padx=6, pady=2)

        # Tab 3: Safety & Legal
        tab_safety = ttk.Frame(notebook)
        notebook.add(tab_safety, text='Safety & Legal')

        safety_title = Label(tab_safety, text='Safety', font=getattr(app, 'titles_font', 'arial 12 bold'))
        https_cb = Checkbutton(tab_safety, text='HTTPS only', variable=https_only)
        cred_cb = Checkbutton(tab_safety, text='Block credentials in URL', variable=block_credentials)
        iphost_cb = Checkbutton(tab_safety, text='Block IP-literal hosts', variable=block_ip_hosts)
        private_cb = Checkbutton(tab_safety, text='Block private/reserved hosts', variable=block_private_ip)
        sameorg_cb = Checkbutton(tab_safety, text='Same-origin redirects only', variable=same_origin_redirects)
        sanitize_cb = Checkbutton(tab_safety, text='Sanitize HTML', variable=sanitize_html_v)
        maxkb_title = Label(tab_safety, text='Max download (KB):', font='arial 10')
        maxkb_entry = Entry(tab_safety, width=8)
        try:
            maxkb_entry.insert('end', str(max_kb_var.get()))
            maxkb_entry.bind('<KeyRelease>', lambda e: max_kb_var.set(int(maxkb_entry.get() or 1)) if (maxkb_entry.get().isdigit() and int(maxkb_entry.get()) > 0) else None)
        except Exception:
            pass
        ct_label = Label(tab_safety, text='Allowed types: HTML/XHTML/XML/Text', font='arial 8')

        legal_title = Label(tab_safety, text='Legal compliance', font=getattr(app, 'titles_font', 'arial 12 bold'))
        legal_ack_cb = Checkbutton(
            tab_safety,
            text='I have authorization and accept all legal responsibility',
            variable=legal_ack_var,
            command=lambda: setattr(app, '_wbs_legal_ack', bool(legal_ack_var.get()))
        )
        meta_warn_cb = Checkbutton(tab_safety, text='Warn on restrictive meta robots', variable=warn_meta_robots)
        open_policies_btn = Button(
            tab_safety,
            text='Open robots.txt and Terms (select)',
            command=lambda: (_offer_policy_links(state['last_host']) if state['last_host'] else None)
        )

        safety_title.grid(row=0, column=0, sticky='w', padx=6, pady=(6, 0))
        https_cb.grid(row=1, column=0, sticky='w', padx=6)
        cred_cb.grid(row=1, column=1, sticky='w', padx=6)
        iphost_cb.grid(row=2, column=0, sticky='w', padx=6)
        private_cb.grid(row=2, column=1, sticky='w', padx=6)
        sameorg_cb.grid(row=3, column=0, sticky='w', padx=6)
        sanitize_cb.grid(row=3, column=1, sticky='w', padx=6)
        maxkb_title.grid(row=4, column=0, sticky='e', padx=6)
        maxkb_entry.grid(row=4, column=1, sticky='w', padx=6)
        ct_label.grid(row=4, column=2, sticky='w', padx=6)

        legal_title.grid(row=5, column=0, sticky='w', padx=6, pady=(10, 0))
        legal_ack_cb.grid(row=6, column=0, columnspan=3, sticky='w', padx=6)
        meta_warn_cb.grid(row=7, column=0, sticky='w', padx=6)
        open_policies_btn.grid(row=7, column=2, sticky='e', padx=6)

        # If content already loaded (initial selection path), run an initial search to populate output
        try:
            if hasattr(app, 'soup') and app.soup:
                search()
        except Exception:
            pass

    # ---- Validation and submission helpers for initial selector ----
    def _basic_url_validator(url: str) -> tuple[bool, str]:
        '''[handlers:validate_url] Basic URL validation hook.'''
        try:
            from urllib.parse import urlparse
            p = urlparse(url)
            if not p.scheme or not p.netloc:
                return False, 'Please enter a full URL, e.g., https://example.com'
            if p.scheme.lower() not in ('http', 'https'):
                return False, 'Only http/https schemes are allowed'
            if len(url) > 2048:
                return False, 'URL is too long'
            return True, ''
        except Exception as e:
            return False, f'Invalid URL: {e}'

    def _create_selector_only():

        # [handlers:on_selector_enter]
        def _enter(event=False):
            mode = state['chosen_init']
            if mode == 'link':
                # Open dedicated modal to gather URL
                url = app.link_entry.get().strip()
                ok, message = _basic_url_validator(url)
                if not ok:
                    url_error.configure(text=message)
                    return
                # [handlers:after_link_ok] Save and proceed
                state['chosen_init'] = 'link'
                app.wbs_path = url
                # Consolidated legal notice (once per session), then load and open main UI
                if not _legal_disclaimer(None):
                    return
                if _from_url(url):
                    state['via_internet'] = True
                    if state['last_host']:
                        _offer_policy_links(state['last_host'])
                    # Close initial selector if still open
                    try:
                        if getattr(app, 'init_root', None) and app.init_root.winfo_exists():
                            app.init_root.destroy()
                    except Exception:
                        pass

            elif mode == 'this':
                # Load editor content and open main UI
                app.wbs_auto_update = True
                state['title_text'] = 'file name:'
                try:
                    app.wbs_path = app.file_name
                except Exception:
                    app.wbs_path = '(File is not named)'
                if not _ensure_soup_from_editor():
                    messagebox.showerror('EgonTE', 'Failed to parse current buffer')
                    return
                try:
                    init_root.destroy()
                except Exception:
                    pass
            else:  # 'file'
                # Ask for a local file and open main UI if loaded
                try:
                    app.wbs_path = filedialog.askopenfilename(
                        title='Open file to scrape',
                        filetypes=(('HTML FILES', '*.html'), ('Text Files', '*.txt')),
                    )
                    if not app.wbs_path:
                        messagebox.showerror('EgonTE', 'No file selected')
                        return
                    with open(app.wbs_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    app.soup = BeautifulSoup(content, 'html.parser')
                except Exception as e:
                    messagebox.showerror('EgonTE', f'Failed to read/parse file: {e}')
                    return
                try:
                    init_root.destroy()
                except Exception:
                    pass
            app.open_windows_control(main_ui)


        '''Initial selector with clear labeled options and contextual popups.'''
        init_root = app.make_pop_ups_window(
            None,
            custom_title='web scrapping - Choose source',
            resizable=(False, False),
            modal=False,  # independent popup
            topmost=False
        )
        app.init_root = init_root

        # Title
        title_label = tk.Label(init_root, text='Select content source to scrape', font='arial 12 bold')
        title_label._wsp_id = 'selector_title_label'
        title_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 6), sticky='w')

        # Clear, labeled buttons
        link_btn = tk.Button(init_root, text='Scrape website by link', command=lambda: _change('link'))
        this_btn = tk.Button(init_root, text='Scrape current editor (this file)', command=lambda: _change('this'))
        file_btn = tk.Button(init_root, text='Scrape a local HTML/TXT file', command=lambda: _change('file'))
        enter_btn = tk.Button(init_root, text='Enter', font='arial 10 bold', command=_enter)

        # Hidden text entry, for entering links
        app.link_entry = tk.Entry(init_root, width=20, relief='flat')
        url_error = tk.Label(init_root, text='', fg='red', font='arial 9')
        app.link_entry.bind('<Return>', _enter)

        # Assign developer-friendly IDs
        link_btn._wsp_id = 'selector_link_button'
        this_btn._wsp_id = 'selector_this_button'
        file_btn._wsp_id = 'selector_file_button'
        enter_btn._wsp_id = 'selector_enter_button'
        app.link_entry._wsp_id = 'link_input_entry'
        url_error._wsp_id = 'link_error_label'

        # Mode hint
        hint_label = tk.Label(init_root, text='Mode selected: link', font='arial 9')
        hint_label._wsp_id = 'selector_mode_hint'

        # Internal selected mode state (reflect in hint)
        state['chosen_init'] = 'link'

        # [handlers:on_selector_change]
        def _change(mode: str):
            state['chosen_init'] = mode
            hint_label.configure(text=f'Mode selected: {mode}')
            if mode == 'link':
                app.link_entry.grid(row=3, padx=5)
                url_error.grid(row=4, padx=5, pady=5)
                app.link_entry.focus_set()
            else:
                app.link_entry.grid_forget()
                url_error.grid_forget()

        # Layout grid
        link_btn.grid(row=1, column=0, padx=10, pady=8, sticky='w')
        this_btn.grid(row=1, column=1, padx=10, pady=8, sticky='w')
        file_btn.grid(row=1, column=2, padx=10, pady=8, sticky='w')
        hint_label.grid(row=2, column=0, columnspan=2, padx=10, sticky='w')
        enter_btn.grid(row=2, column=2, padx=10, pady=10, sticky='e')

        # Make the window size adjusted to the widgets
        init_root.update_idletasks()
        init_root.geometry(f'{init_root.winfo_width() + 30}x{init_root.winfo_height()+ 60}')

        # Make dialog size consistent and centered
        try:
            init_root.grid_columnconfigure(0, weight=1)
            init_root.grid_columnconfigure(1, weight=1)
            init_root.grid_columnconfigure(2, weight=1)
            pr = init_root.master if init_root.master else init_root
            x = pr.winfo_rootx() + (pr.winfo_width() - init_root.winfo_width()) // 2
            y = pr.winfo_rooty() + (pr.winfo_height() - init_root.winfo_height()) // 3
            init_root.geometry(f'+{x}+{y}')
        except Exception:
            pass
        _change('link')

    # Launch: show the selector; main_ui opens after content is chosen
    _create_selector_only()
