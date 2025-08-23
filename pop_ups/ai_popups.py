'''
AI popups: ChatGPT and DALL·E standalone popups.

- Unified OpenAI client (OpenAI and Azure).
- Key dialog with Azure/OpenAI modes and secret bypass mode (Ctrl+Shift+B).
- Chat: modern UI, streaming, presets, Stop button, token estimate, system prompt sidebar.
- DALL·E: prompt/options, progress, URLs/paths list, right-click actions, optional thumbnails, save/open helpers.
- Uses app.ui_builders.make_pop_ups_window and make_rich_textbox when available; falls back gracefully.

All strings use single quotes and names are in snake_case.
'''

import time
import base64
import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk
from threading import Thread, Event

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except Exception:
    OpenAI = None
    _OPENAI_AVAILABLE = False


# ------------------------------- Utilities --------------------------------- #

def _make_popup_window(app, title):
    # Prefer enhanced builders if available
    builders = getattr(app, 'ui_builders', None)
    if builders and hasattr(builders, 'make_pop_ups_window'):
        try:
            return builders.make_pop_ups_window(
                function=_build_chat_ui,
                custom_title=title,
                parent=getattr(app, 'root', None),
                name='chatgpt_popup',
                topmost=False,
                modal=False,
            )
        except Exception:
            pass
    # Fallbacks
    if hasattr(app, 'make_pop_ups_window') and callable(app.make_pop_ups_window):
        return app.make_pop_ups_window(lambda: None, title)
    popup = tk.Toplevel()
    popup.title(title)
    if hasattr(app, 'st_value'):
        try:
            popup.attributes('-alpha', app.st_value)
        except Exception:
            pass
    return popup


def _make_named_popup_window(app, title, *, name, owner_func, parent=None):
    builders = getattr(app, 'ui_builders', None)
    if builders and hasattr(builders, 'make_pop_ups_window'):
        try:
            return builders.make_pop_ups_window(
                function=owner_func,
                custom_title=title,
                parent=parent or getattr(app, 'root', None),
                name=name,
                topmost=False,
                modal=False,
            )
        except Exception:
            pass
    popup = tk.Toplevel()
    popup.title(title)
    if hasattr(app, 'st_value'):
        try:
            popup.attributes('-alpha', app.st_value)
        except Exception:
            pass
    return popup


def _open_external_link(url):
    import webbrowser
    webbrowser.open(url)


def _open_key_dialog(app, after_open):
    login_window = tk.Toplevel()
    if hasattr(app, 'make_tm'):
        app.make_tm(login_window)
    if getattr(app, 'limit_w_s', None) and getattr(app.limit_w_s, 'get', lambda: False)():
        login_window.resizable(False, False)
    login_window.title(getattr(app, 'title_struct', '') + 'connect to OpenAI')

    app.service_type = tk.IntVar(value=1)  # 0=Azure, 1=OpenAI
    app.end_entry_state = False

    form_frame = tk.Frame(login_window)
    form_frame.pack(padx=12, pady=10)

    tk.Label(form_frame, text='Enter your OpenAI key to connect', font='arial 12').grid(row=0, column=0, columnspan=3, pady=(0, 6))
    tk.Label(form_frame, text='Key entry', font='arial 12 underline', width=60).grid(row=1, column=0, columnspan=3)
    key_entry = tk.Entry(form_frame, width=35, show='*')
    key_entry.grid(row=2, column=0, columnspan=3, pady=(2, 10))

    endpoint_entry = tk.Entry(form_frame, width=35)
    deployment_entry = tk.Entry(form_frame, width=35)

    def on_service_change():
        if app.service_type.get() == 0:
            if not app.end_entry_state:
                endpoint_entry.grid(row=3, column=0, columnspan=3)
                deployment_entry.grid(row=4, column=0, columnspan=3, pady=(0, 8))
                endpoint_entry.delete(0, tk.END)
                deployment_entry.delete(0, tk.END)
                endpoint_entry.insert(tk.END, 'Azure endpoint (https://<name>.openai.azure.com)')
                deployment_entry.insert(tk.END, 'Azure deployment name')
                app.end_entry_state = True
            get_key_label.bind('<Button-1>', lambda e: _open_external_link('https://learn.microsoft.com/en-us/azure/ai-services/openai/quickstart?tabs=command-line%2Cpython&pivots=programming-language-python'))
        else:
            if app.end_entry_state:
                endpoint_entry.grid_forget()
                deployment_entry.grid_forget()
                app.end_entry_state = False
            get_key_label.bind('<Button-1>', lambda e: _open_external_link('https://platform.openai.com/account/api-keys'))

    service_frame = tk.Frame(form_frame)
    service_frame.grid(row=5, column=0, columnspan=3, pady=(4, 6))
    rb_azure = tk.Radiobutton(service_frame, text='Azure key', variable=app.service_type, value=0, command=on_service_change)
    rb_openai = tk.Radiobutton(service_frame, text='OpenAI key', variable=app.service_type, value=1, command=on_service_change)
    rb_azure.grid(row=0, column=0)
    rb_openai.grid(row=0, column=1)

    get_key_label = tk.Label(form_frame, text='Don\'t have/forgot key?', fg='blue', font='arial 10 underline', cursor='hand2')
    get_key_label.grid(row=6, column=0, columnspan=3)
    get_key_label.bind('<Button-1>', lambda e: _open_external_link('https://platform.openai.com/account/api-keys'))

    def do_login():
        try:
            app.key = key_entry.get().strip()
            if not _OPENAI_AVAILABLE:
                tk.messagebox.showerror('EgonTE', 'OpenAI client is not available in this environment')
                return False
            if app.service_type.get() == 0:
                endpoint = endpoint_entry.get().strip().rstrip('/')
                app.deployment_name = deployment_entry.get().strip()
                app.azure_api_version = '2024-08-01-preview'
                app.api_client = OpenAI(
                    base_url=f'{endpoint}/openai/deployments/{app.deployment_name}?api-version={app.azure_api_version}',
                    default_headers={'api-key': app.key},
                )
            else:
                app.api_client = OpenAI(api_key=app.key)
                app.azure_api_version = None

            try:
                app.api_client.models.list()
            except Exception:
                tk.messagebox.showerror('Error', 'The OpenAI key or configuration is invalid')
                return False

            try:
                login_window.destroy()
            except Exception:
                pass
            setattr(app, 'openai_code', True)
            after_open()
            return True
        except Exception as exc:
            tk.messagebox.showerror('EgonTE', f'Authentication/Initialization error: {exc}')
            return False

    tk.Button(form_frame, text='Enter', font='arial 10 bold', command=do_login, relief=tk.FLAT).grid(row=7, column=0, columnspan=3, pady=(8, 2))

    def secret_bypass(_=None):
        setattr(app, '_gpt_bypass', True)
        try:
            login_window.destroy()
        except Exception:
            pass
        setattr(app, 'openai_code', False)
        after_open()

    login_window.bind('<Control-Shift-b>', secret_bypass)
    on_service_change()
    login_window.mainloop()


def _insert_bubble(chat_text, role, content):
    chat_text.configure(state=tk.NORMAL)
    chat_text.insert(tk.END, '\n')
    if role == 'user':
        chat_text.insert(tk.END, 'You\n', ('role', 'role_user'))
        chat_text.insert(tk.END, content.strip() + '\n', ('bubble', 'bubble_user'))
    elif role == 'assistant':
        chat_text.insert(tk.END, 'AI\n', ('role', 'role_ai'))
        chat_text.insert(tk.END, content.strip() + '\n', ('bubble', 'bubble_ai'))
    else:
        chat_text.insert(tk.END, 'System\n', ('role', 'role_sys'))
        chat_text.insert(tk.END, content.strip() + '\n', ('bubble', 'bubble_sys'))
    chat_text.insert(tk.END, '\n')
    chat_text.see(tk.END)
    chat_text.configure(state=tk.DISABLED)


def _append_stream_chunk(chat_text, chunk_text):
    if not chunk_text:
        return
    chat_text.configure(state=tk.NORMAL)
    chat_text.insert(tk.END, chunk_text, ('bubble', 'bubble_ai'))
    chat_text.see(tk.END)
    chat_text.configure(state=tk.DISABLED)


# ------------------------------- ChatGPT ----------------------------------- #

def open_chatgpt(app):
    '''
    Entry point to open the ChatGPT popup.
    '''
    def open_ui():
        _build_chat_ui(app)

    if getattr(app, '_gpt_bypass', False):
        open_ui()
        return

    if _OPENAI_AVAILABLE and getattr(app, 'openai_code', False):
        open_ui()
    elif _OPENAI_AVAILABLE:
        _open_key_dialog(app, open_ui)
    else:
        open_ui()


def _build_chat_ui(app):
    window = _make_popup_window(app, 'ChatGPT')
    try:
        if getattr(app, 'gpt_image', None):
            window.tk.call('wm', 'iconphoto', window._w, app.gpt_image)
    except Exception:
        pass

    bg = '#1f1f24'
    bg_alt = '#2a2a31'
    fg = '#EAECEE'
    accent = '#4f8cff'
    accent_dark = '#3a69c7'

    window.configure(bg=bg)
    outer_frame = tk.Frame(window, bg=bg)
    outer_frame.pack(fill=tk.BOTH, expand=True)

    # Header
    header = tk.Frame(outer_frame, bg=bg_alt, padx=10, pady=8)
    header.pack(fill=tk.X)

    models = ['gpt-4o-mini', 'gpt-4o', 'o3-mini']
    if not hasattr(app, 'gpt_model') or not app.gpt_model:
        app.gpt_model = 'gpt-4o-mini'
    app._gpt_stream = getattr(app, '_gpt_stream', True)
    app._gpt_temp = getattr(app, '_gpt_temp', 0.7)

    tk.Label(header, text='Model', bg=bg_alt, fg=fg).pack(side='left')
    model_box = ttk.Combobox(header, values=models, state='readonly', width=14)
    model_box.set(app.gpt_model)
    model_box.pack(side='left', padx=(6, 12))

    tk.Label(header, text='Temperature', bg=bg_alt, fg=fg).pack(side='left')
    temp_scale = ttk.Scale(
        header,
        from_=0.0,
        to=1.5,
        orient='horizontal',
        length=140,
        command=lambda v: setattr(app, '_gpt_temp', float(v)),
    )
    temp_scale.set(app._gpt_temp)
    temp_scale.pack(side='left', padx=(6, 16))

    stream_var = tk.BooleanVar(value=app._gpt_stream)
    def sync_stream_flag():
        app._gpt_stream = bool(stream_var.get())
    ttk.Checkbutton(header, text='Stream', variable=stream_var, command=sync_stream_flag).pack(side='left', padx=(0, 12))

    tk.Label(header, text='Style', bg=bg_alt, fg=fg).pack(side='left', padx=(8, 4))
    style_box = ttk.Combobox(header, values=['Default', 'Concise', 'Detailed', 'Code'], state='readonly', width=10)
    style_box.set('Default')
    style_box.pack(side='left', padx=(0, 8))

    def style_to_system_prompt(style_name):
        if style_name == 'Concise':
            return 'You are concise. Prefer short answers without losing critical details.'
        if style_name == 'Detailed':
            return 'You are thorough and explanatory. Provide step-by-step reasoning when helpful.'
        if style_name == 'Code':
            return 'You respond with code-first answers when appropriate, including brief explanations.'
        return ''

    # Apply preset button
    btn_style = dict(bg=accent, fg='white', activebackground=accent_dark, activeforeground='white', relief=tk.FLAT, padx=10, pady=5)
    def apply_preset():
        selected = style_box.get()
        prompt = style_to_system_prompt(selected)
        system_prompt_text.delete('1.0', tk.END)
        system_prompt_text.insert('1.0', prompt)
        app.gpt_system = prompt
        if not hasattr(app, 'gpt_messages') or not isinstance(getattr(app, 'gpt_messages'), list):
            app.gpt_messages = []
        if app.gpt_messages and app.gpt_messages[0].get('role') == 'system':
            app.gpt_messages[0]['content'] = app.gpt_system
        elif app.gpt_system:
            app.gpt_messages.insert(0, {'role': 'system', 'content': app.gpt_system})

    tk.Button(header, text='Apply', command=apply_preset, **btn_style).pack(side='left', padx=(0, 12))

    # Bypass indicator
    if not hasattr(app, '_gpt_bypass'):
        app._gpt_bypass = False
    bypass_label = tk.Label(header, text='Bypass: OFF', bg=bg_alt, fg='#a7aab0')
    bypass_label.pack(side='left', padx=(6, 6))
    def render_bypass_label():
        text = 'Bypass: ON' if app._gpt_bypass else 'Bypass: OFF'
        color = '#98ffa8' if app._gpt_bypass else '#a7aab0'
        bypass_label.config(text=text, fg=color)
    def toggle_bypass(_=None):
        app._gpt_bypass = not app._gpt_bypass
        render_bypass_label()
    window.bind('<Control-Shift-b>', toggle_bypass)
    render_bypass_label()

    # Header actions
    def clear_chat():
        app.gpt_messages = []
        chat_text.configure(state=tk.NORMAL)
        chat_text.delete('1.0', tk.END)
        chat_text.configure(state=tk.DISABLED)
        update_token_counter()
    def copy_last():
        last_text = ''
        for m in reversed(getattr(app, 'gpt_messages', [])):
            if m['role'] == 'assistant':
                last_text = m['content']
                break
        if last_text:
            window.clipboard_clear()
            window.clipboard_append(last_text)
    def save_transcript():
        import tkinter.filedialog as fd
        path = fd.asksaveasfilename(defaultextension='.txt', filetypes=[('Text', '*.txt')])
        if not path:
            return
        with open(path, 'w', encoding='utf-8') as fh:
            for m in getattr(app, 'gpt_messages', []):
                tag = m['role'].upper()
                fh.write(f'[{tag}] {m["content"]}\n\n')

    tk.Button(header, text='Clear', command=clear_chat, **btn_style).pack(side='right', padx=(8, 0))
    tk.Button(header, text='Save', command=save_transcript, **btn_style).pack(side='right', padx=8)
    tk.Button(header, text='Copy last', command=copy_last, **btn_style).pack(side='right', padx=8)

    # Body split
    body = tk.Frame(outer_frame, bg=bg)
    body.pack(fill=tk.BOTH, expand=True)

    # Sidebar: system prompt
    sidebar = tk.Frame(body, bg=bg, padx=10, pady=10)
    sidebar.pack(side='left', fill=tk.Y)
    tk.Label(sidebar, text='System prompt', bg=bg, fg=fg).pack(anchor='w')

    builders = getattr(app, 'ui_builders', None)
    if builders and hasattr(builders, 'make_rich_textbox'):
        sys_container, system_prompt_text, _ = builders.make_rich_textbox(
            parent_container=sidebar,
            place='pack_top',
            wrap=tk.WORD,
            font='Helvetica 12',
            size=(32, 6),
            selectbg='dark cyan',
            bd=0,
            relief='',
            format='txt',
        )
    else:
        sys_container = tk.Frame(sidebar, bg=bg)
        sys_container.pack(fill=tk.Y)
        system_prompt_text = tk.Text(sys_container, height=6, width=32, bg='#2a2a31', fg=fg, insertbackground=fg, wrap='word', relief=tk.FLAT)
        system_prompt_text.pack(fill=tk.Y)

    if not hasattr(app, 'gpt_system'):
        app.gpt_system = ''
    system_prompt_text.insert('1.0', app.gpt_system)
    system_prompt_text.bind('<FocusOut>', lambda e: setattr(app, 'gpt_system', system_prompt_text.get('1.0', tk.END).strip()))

    # Chat area
    center = tk.Frame(body, bg=bg, padx=0, pady=10)
    center.pack(side='left', fill=tk.BOTH, expand=True)

    if builders and hasattr(builders, 'make_rich_textbox'):
        chat_container, chat_text, chat_scroll = builders.make_rich_textbox(
            parent_container=center,
            place='pack_top',
            wrap=tk.WORD,
            font='Helvetica 13',
            size=None,
            selectbg='dark cyan',
            bd=0,
            relief='',
            format='txt',
        )
    else:
        chat_container = tk.Frame(center, bg=bg)
        chat_container.pack(fill=tk.BOTH, expand=True)
        chat_scroll = ttk.Scrollbar(chat_container)
        chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        chat_text = tk.Text(
            chat_container,
            bg=bg,
            fg=fg,
            font='Helvetica 13',
            width=60,
            yscrollcommand=chat_scroll.set,
            undo=True,
            wrap='word',
            state=tk.DISABLED,
            relief=tk.FLAT,
            insertbackground=fg,
            padx=14,
            pady=12,
        )
        chat_text.pack(fill=tk.BOTH, expand=True)
        chat_scroll.config(command=chat_text.yview)

    chat_text.tag_config('role', foreground='#a7aab0', spacing1=4, spacing3=6)
    chat_text.tag_config('role_user', foreground='#a7d1ff')
    chat_text.tag_config('role_ai', foreground='#ffd28a')
    chat_text.tag_config('role_sys', foreground='#98ffa8')
    chat_text.tag_config('bubble', lmargin1=10, lmargin2=10, rmargin=10, spacing1=2, spacing3=8)
    chat_text.tag_config('bubble_user', background='#263041')
    chat_text.tag_config('bubble_ai', background='#2f2f39')
    chat_text.tag_config('bubble_sys', background='#1c3a27')

    # Input bar
    footer = tk.Frame(center, bg=bg_alt, padx=10, pady=10)
    footer.pack(fill=tk.X)
    input_text = tk.Text(footer, height=3, bg='#2C3E50', fg=fg, font='Helvetica 13', wrap='word', insertbackground=fg, relief=tk.FLAT)
    input_text.pack(side='left', fill=tk.BOTH, expand=True, padx=(0, 10))

    stop_event = Event()
    tk.Button(
        footer,
        text='Send',
        bg=accent,
        fg='white',
        activebackground=accent_dark,
        activeforeground='white',
        relief=tk.FLAT,
        padx=10,
        pady=5,
        command=lambda: Thread(target=_ask_and_stream, args=(app, window, chat_text, input_text, model_box, stream_var, stop_event), daemon=True).start(),
    ).pack(side='left')
    tk.Button(
        footer,
        text='Stop',
        bg='#b84a4a',
        fg='white',
        activebackground='#8f3838',
        activeforeground='white',
        relief=tk.FLAT,
        padx=10,
        pady=5,
        command=stop_event.set,
    ).pack(side='left', padx=(10, 0))

    # Status
    status_bar = tk.Frame(outer_frame, bg=bg, padx=10, pady=6)
    status_bar.pack(fill=tk.X)
    token_label = tk.Label(status_bar, text='Tokens: 0', bg=bg, fg='#a7aab0')
    token_label.pack(side='left')

    # Attach state
    app._chat_widgets = dict(
        root_window=window,
        chat_text=chat_text,
        input_text=input_text,
        token_label=token_label,
        model_combobox=model_box,
        stream_var=stream_var,
        stop_event=stop_event,
        style_combobox=style_box,
    )

    if not hasattr(app, 'gpt_messages') or not isinstance(getattr(app, 'gpt_messages'), list):
        app.gpt_messages = []
    if app.gpt_system:
        if not app.gpt_messages or app.gpt_messages[0].get('role') != 'system':
            app.gpt_messages.insert(0, {'role': 'system', 'content': app.gpt_system})

    def update_token_counter():
        words = 0
        for message in app.gpt_messages:
            words += len(str(message.get('content', '')).split())
        tokens = max(1, int(words / 0.75))
        token_label.config(text=f'Tokens: {tokens}')

    def on_return_key(event):
        if event.keysym == 'Return' and not (event.state & 0x0001):
            Thread(target=_ask_and_stream, args=(app, window, chat_text, input_text, model_box, stream_var, stop_event), daemon=True).start()
            return 'break'

    input_text.bind('<KeyPress-Return>', on_return_key)

    def set_style(style_value):
        style_box.set(style_value)
        apply_preset()

    window.bind('<Control-1>', lambda e: set_style('Concise'))
    window.bind('<Control-2>', lambda e: set_style('Detailed'))
    window.bind('<Control-3>', lambda e: set_style('Code'))

    update_token_counter()


def _ask_and_stream(app, window, chat_text, input_text, model_combobox, stream_var, stop_event):
    try:
        user_text = input_text.get('1.0', tk.END).strip()
        if not user_text:
            return
        input_text.delete('1.0', tk.END)
        stop_event.clear()

        app.gpt_model = model_combobox.get() or app.gpt_model
        use_stream = bool(stream_var.get())
        temperature = float(getattr(app, '_gpt_temp', 0.7))

        window.after(0, lambda: _insert_bubble(chat_text, 'user', user_text))

        if not hasattr(app, 'gpt_messages') or not isinstance(app.gpt_messages, list):
            app.gpt_messages = []
        if not app.gpt_messages and getattr(app, 'gpt_system', ''):
            app.gpt_messages.append({'role': 'system', 'content': app.gpt_system})
        app.gpt_messages.append({'role': 'user', 'content': user_text})

        def start_ai_bubble():
            chat_text.configure(state=tk.NORMAL)
            chat_text.insert(tk.END, '\nAI\n', ('role', 'role_ai'))
            chat_text.insert(tk.END, '', ('bubble', 'bubble_ai'))
            chat_text.configure(state=tk.DISABLED)
        window.after(0, start_ai_bubble)

        accumulated = {'text': ''}

        # Bypass/simulation
        if getattr(app, '_gpt_bypass', False):
            style_value = 'Default'
            try:
                style_value = app._chat_widgets.get('style_combobox').get()
            except Exception:
                pass
            def fake_answer(text_in):
                if style_value == 'Concise':
                    return f'{text_in[:120]}... (concise UI test)'
                if style_value == 'Detailed':
                    return f'This is a detailed UI test response for: \'{text_in}\'.\n\n1) Overview\n2) Steps\n3) Notes\n\nEnd of simulation.'
                if style_value == 'Code':
                    return '```python\n# Simulated code block\nprint(\'UI test\')\n```\nExplanation: This is a fake response.'
                return f'Echo: {text_in}\n\n(This is a simulated response for UI testing.)'
            answer_text = fake_answer(user_text)
            if use_stream:
                for ch in answer_text:
                    if stop_event.is_set():
                        break
                    window.after(0, lambda c=ch: _append_stream_chunk(chat_text, c))
                    time.sleep(0.01)
                window.after(0, lambda: _append_stream_chunk(chat_text, '\n'))
            else:
                window.after(0, lambda: _insert_bubble(chat_text, 'assistant', answer_text))
            accumulated['text'] = answer_text
        else:
            # Real API
            if not _OPENAI_AVAILABLE or not getattr(app, 'api_client', None):
                fallback_text = f'Echo: {user_text}\n\n(This is a simulated response because no API client is configured.)'
                if use_stream:
                    for ch in fallback_text:
                        if stop_event.is_set():
                            break
                        window.after(0, lambda c=ch: _append_stream_chunk(chat_text, c))
                        time.sleep(0.01)
                    window.after(0, lambda: _append_stream_chunk(chat_text, '\n'))
                else:
                    window.after(0, lambda: _insert_bubble(chat_text, 'assistant', fallback_text))
                accumulated['text'] = fallback_text
            else:
                messages_payload = list(app.gpt_messages)
                model_param = app.deployment_name if getattr(app, 'service_type', tk.IntVar(value=1)).get() == 0 else app.gpt_model

                if bool(getattr(app, '_gpt_stream', True)):
                    response_stream = app.api_client.chat.completions.create(
                        model=model_param,
                        messages=messages_payload,
                        stream=True,
                        temperature=temperature,
                    )
                    for chunk in response_stream:
                        if stop_event.is_set():
                            break
                        try:
                            delta_content = chunk.choices[0].delta.content
                        except Exception:
                            delta_content = None
                        if delta_content:
                            accumulated['text'] += delta_content
                            window.after(0, lambda d=delta_content: _append_stream_chunk(chat_text, d))
                    window.after(0, lambda: _append_stream_chunk(chat_text, '\n'))
                else:
                    response = app.api_client.chat.completions.create(
                        model=model_param,
                        messages=messages_payload,
                        temperature=temperature,
                    )
                    answer_text = response.choices[0].message.content
                    window.after(0, lambda: _insert_bubble(chat_text, 'assistant', answer_text))
                    accumulated['text'] = answer_text or ''

        if accumulated['text']:
            app.gpt_messages.append({'role': 'assistant', 'content': accumulated['text']})

        if len(app.gpt_messages) > 40:
            system_messages = [m for m in app.gpt_messages if m['role'] == 'system'][:1]
            app.gpt_messages = (system_messages + app.gpt_messages[-38:]) if system_messages else app.gpt_messages[-38:]

        token_label = app._chat_widgets.get('token_label')
        if token_label:
            def update_token_counter():
                words = 0
                for message in app.gpt_messages:
                    words += len(str(message.get('content', '')).split())
                tokens = max(1, int(words / 0.75))
                token_label.config(text=f'Tokens: {tokens}')
            window.after(0, update_token_counter)

    except Exception as exc:
        window.after(0, lambda: _insert_bubble(chat_text, 'system', f'Error: {exc}'))


# -------------------------------- DALL·E ----------------------------------- #

def open_dalle(app):
    '''
    Entry point to open the DALL·E popup, mirroring chat flow.
    '''
    def open_ui():
        _build_dalle_ui(app)

    if getattr(app, '_gpt_bypass', False):
        open_ui()
        return

    if _OPENAI_AVAILABLE and getattr(app, 'openai_code', False):
        open_ui()
    elif _OPENAI_AVAILABLE:
        _open_key_dialog(app, open_ui)
    else:
        open_ui()


def _build_dalle_ui(app):
    window = _make_named_popup_window(app, 'DALL·E', name='dalle_popup', owner_func=_build_dalle_ui)
    try:
        if getattr(app, 'gpt_image', None):
            window.tk.call('wm', 'iconphoto', window._w, app.gpt_image)
    except Exception:
        pass

    bg = '#1f1f24'
    bg_alt = '#2a2a31'
    fg = '#EAECEE'
    accent = '#4f8cff'
    accent_dark = '#3a69c7'

    window.configure(bg=bg)
    outer_frame = tk.Frame(window, bg=bg)
    outer_frame.pack(fill=tk.BOTH, expand=True)

    # Header: prompt + options
    header = tk.Frame(outer_frame, bg=bg_alt, padx=10, pady=8)
    header.pack(fill=tk.X)

    tk.Label(header, text='Model', bg=bg_alt, fg=fg).pack(side='left')
    model_box = ttk.Combobox(header, values=['dall-e-3', 'gpt-image-1'], state='readonly', width=12)
    model_box.set('dall-e-3')
    model_box.pack(side='left', padx=(6, 12))

    tk.Label(header, text='Prompt', bg=bg_alt, fg=fg).pack(side='left')
    prompt_entry = tk.Entry(header, width=60, bg='#2C3E50', fg=fg, insertbackground=fg, relief=tk.FLAT)
    prompt_entry.pack(side='left', padx=(6, 12))
    prompt_entry.insert(0, getattr(app, 'dalle_prompt', 'An eco-friendly computer from the 90s in the style of vaporwave'))

    tk.Label(header, text='Size', bg=bg_alt, fg=fg).pack(side='left')
    size_box = ttk.Combobox(header, values=['256x256', '512x512', '1024x1024'], state='readonly', width=10)
    size_box.set('1024x1024')
    size_box.pack(side='left', padx=(6, 12))

    tk.Label(header, text='Count', bg=bg_alt, fg=fg).pack(side='left')
    count_box = ttk.Combobox(header, values=[str(n) for n in range(1, 5)], state='readonly', width=3)
    count_box.set('1')
    count_box.pack(side='left', padx=(6, 12))

    tk.Label(header, text='Quality', bg=bg_alt, fg=fg).pack(side='left')
    quality_box = ttk.Combobox(header, values=['standard', 'hd'], state='readonly', width=8)
    quality_box.set('standard')
    quality_box.pack(side='left', padx=(6, 12))

    # Actions + progress
    action_bar = tk.Frame(outer_frame, bg=bg, padx=10, pady=8)
    action_bar.pack(fill=tk.X)

    btn_style = dict(bg=accent, fg='white', activebackground=accent_dark, activeforeground='white', relief=tk.FLAT, padx=10, pady=5)
    imagine_btn = tk.Button(action_bar, text='Imagine', **btn_style)
    imagine_btn.pack(side='left')

    open_urls_btn = tk.Button(action_bar, text='Open URL(s)', **btn_style, state=tk.DISABLED)
    open_urls_btn.pack(side='left', padx=(10, 0))

    save_btn = tk.Button(action_bar, text='Save image(s)...', **btn_style, state=tk.DISABLED)
    save_btn.pack(side='left', padx=(10, 0))

    progress = ttk.Progressbar(action_bar, mode='indeterminate', length=140)
    progress.pack(side='right', padx=(10, 0))
    status_label = tk.Label(action_bar, text='Ready', bg=bg, fg='#a7aab0')
    status_label.pack(side='right')

    # Output area: URLs/paths list with right-click
    builders = getattr(app, 'ui_builders', None)
    if builders and hasattr(builders, 'make_rich_textbox'):
        out_container, output_text, _ = builders.make_rich_textbox(
            parent_container=outer_frame,
            place='pack_top',
            wrap=tk.NONE,
            font='Helvetica 11',
            size=None,
            selectbg='dark cyan',
            bd=0,
            relief='',
            format='txt',
        )
    else:
        out_container = tk.Frame(outer_frame, bg=bg)
        out_container.pack(fill=tk.BOTH, expand=True)
        output_text = tk.Text(out_container, bg=bg, fg=fg, wrap='none', font='Helvetica 11', relief=tk.FLAT, insertbackground=fg, height=12)
        output_text.pack(fill=tk.BOTH, expand=True)

    output_text.configure(state=tk.DISABLED)

    menu = tk.Menu(window, tearoff=0)
    menu.add_command(label='Copy selection', command=lambda: _copy_selected_text(window, output_text))
    menu.add_command(label='Open selection', command=lambda: _open_selected_urls(output_text))
    def on_context(event):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    output_text.bind('<Button-3>', on_context)

    # Thumbnails panel
    thumbs_frame = tk.Frame(outer_frame, bg=bg, padx=10, pady=6)
    thumbs_frame.pack(fill=tk.BOTH, expand=True)

    thumbs_canvas = tk.Canvas(thumbs_frame, bg=bg, highlightthickness=0)
    thumbs_scroll = ttk.Scrollbar(thumbs_frame, orient='vertical', command=thumbs_canvas.yview)
    thumbs_container = tk.Frame(thumbs_canvas, bg=bg)

    thumbs_container.bind('<Configure>', lambda e: thumbs_canvas.configure(scrollregion=thumbs_canvas.bbox('all')))
    thumbs_canvas.create_window((0, 0), window=thumbs_container, anchor='nw')
    thumbs_canvas.configure(yscrollcommand=thumbs_scroll.set)

    thumbs_canvas.pack(side='left', fill=tk.BOTH, expand=True)
    thumbs_scroll.pack(side='right', fill=tk.Y)

    thumbnails_refs = []

    def render_thumbnails(paths_or_urls):
        for child in thumbs_container.winfo_children():
            child.destroy()
        thumbnails_refs.clear()
        try:
            from PIL import Image, ImageTk  # type: ignore
        except Exception:
            info = tk.Label(thumbs_container, text='Install Pillow for inline previews', bg=bg, fg='#a7aab0')
            info.grid(row=0, column=0, sticky='w', padx=2, pady=2)
            return
        max_side = 160
        col_count = 4
        for idx, src in enumerate(paths_or_urls):
            try:
                img_bytes = _fetch_image_bytes(src)
                if not img_bytes:
                    continue
                from io import BytesIO
                pil_img = Image.open(BytesIO(img_bytes))
                pil_img.thumbnail((max_side, max_side))
                tk_img = ImageTk.PhotoImage(pil_img)
                thumbnails_refs.append(tk_img)
                def open_src(s=src):
                    if s.startswith('file://'):
                        _open_file_path(s.replace('file://', '', 1))
                    else:
                        import webbrowser
                        webbrowser.open(s)
                thumb_lbl = tk.Label(thumbs_container, image=tk_img, bg=bg, cursor='hand2')
                thumb_lbl.bind('<Button-1>', lambda e, s=src: open_src(s))
                r, c = divmod(idx, col_count)
                thumb_lbl.grid(row=r, column=c, padx=6, pady=6)
            except Exception:
                continue

    # State and helpers
    last_paths_or_urls = []

    def set_status(text):
        status_label.config(text=text)

    def set_busy(is_busy):
        if is_busy:
            progress.start(12)
            imagine_btn.config(state=tk.DISABLED)
        else:
            progress.stop()
            imagine_btn.config(state=tk.NORMAL)

    def set_result_buttons(enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        open_urls_btn.config(state=state)
        save_btn.config(state=state)

    def write_output(lines):
        output_text.configure(state=tk.NORMAL)
        output_text.delete('1.0', tk.END)
        for ln in lines:
            output_text.insert(tk.END, ln + '\n')
        output_text.configure(state=tk.DISABLED)

    def open_urls_in_browser():
        if not last_paths_or_urls:
            return
        import webbrowser
        for u in last_paths_or_urls:
            try:
                webbrowser.open(u)
            except Exception:
                pass

    def save_images_to_disk():
        if not last_paths_or_urls:
            return
        import tkinter.filedialog as fd
        from tkinter import messagebox

        dest_dir = fd.askdirectory(title='Select folder to save image(s)')
        if not dest_dir:
            return
        ok = 0
        for idx, src in enumerate(last_paths_or_urls, start=1):
            try:
                saved = _download_or_copy_image(src, dest_dir, f'dalle_{idx}.png')
                if saved:
                    ok += 1
            except Exception as exc:
                print(f'Failed to save {src}: {exc}')
        set_status(f'Saved {ok}/{len(last_paths_or_urls)} image(s)')
        try:
            if ok and messagebox.askyesno('Open folder', 'Open the destination folder?'):
                _open_folder(dest_dir)
        except Exception:
            pass

    open_urls_btn.config(command=open_urls_in_browser)
    save_btn.config(command=save_images_to_disk)

    def imagine():
        nonlocal last_paths_or_urls
        prompt = prompt_entry.get().strip()
        if not prompt:
            set_status('Enter a prompt')
            window.bell()
            return

        model = model_box.get()
        size_value = size_box.get()
        try:
            n_images = int(count_box.get())
        except Exception:
            n_images = 1
        quality_value = quality_box.get()

        app.dalle_prompt = prompt
        set_result_buttons(False)
        write_output([])
        render_thumbnails([])
        set_busy(True)
        set_status('Generating...')

        def worker():
            try:
                if getattr(app, '_gpt_bypass', False) or not _OPENAI_AVAILABLE or not getattr(app, 'api_client', None):
                    fake = [f'https://example.com/fake_image_{i}.png' for i in range(1, n_images + 1)]
                    window.after(0, lambda: finish_images(fake, 'Simulation complete'))
                    return
                resp = app.api_client.images.generate(
                    model=model,
                    prompt=prompt,
                    size=size_value,
                    quality=quality_value,
                    n=n_images,
                )
                results = []
                for item in getattr(resp, 'data', []) or []:
                    url = getattr(item, 'url', None)
                    if url:
                        results.append(url)
                        continue
                    b64 = getattr(item, 'b64_json', None)
                    if b64:
                        path = _decode_and_write_temp_image(b64)
                        if path:
                            results.append('file://' + path)
                if not results:
                    raise RuntimeError('No images returned')
                window.after(0, lambda: finish_images(results, 'Done'))
            except Exception as exc:
                window.after(0, lambda: finish_error(exc))

        def finish_images(paths, message):
            nonlocal last_paths_or_urls
            last_paths_or_urls = paths
            write_output(paths)
            render_thumbnails(paths)
            set_result_buttons(True)
            set_status(message)
            set_busy(False)

        def finish_error(exc):
            set_status(f'Error: {exc}')
            set_busy(False)

        Thread(target=worker, daemon=True).start()

    imagine_btn.config(command=imagine)

    # Shortcuts
    window.bind('<Control-Return>', lambda e: (imagine(), 'break'))
    window.bind('<Control-s>', lambda e: (save_images_to_disk(), 'break'))
    window.bind('<Control-o>', lambda e: (open_urls_in_browser(), 'break'))
    prompt_entry.bind('<Return>', lambda e: (imagine(), 'break'))


# ------------------------------- Helpers ----------------------------------- #

def _copy_selected_text(root_window, text_widget):
    try:
        sel = text_widget.selection_get()
        if sel:
            root_window.clipboard_clear()
            root_window.clipboard_append(sel)
    except Exception:
        pass


def _open_selected_urls(text_widget):
    try:
        selected = text_widget.selection_get()
    except Exception:
        selected = ''
    if not selected:
        return
    import webbrowser
    for line in selected.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            webbrowser.open(line)
        except Exception:
            pass


def _decode_and_write_temp_image(b64_data):
    try:
        binary = base64.b64decode(b64_data)
        import tempfile
        fd, path = tempfile.mkstemp(prefix='dalle_', suffix='.png')
        with os.fdopen(fd, 'wb') as f:
            f.write(binary)
        return path
    except Exception:
        return None


def _download_or_copy_image(src, dest_dir, filename):
    '''
    Save image from a URL or file:// path to dest_dir/filename.
    Returns True on success.
    '''
    try:
        if src.startswith('file://'):
            src_path = src.replace('file://', '', 1)
            if not os.path.isfile(src_path):
                return False
            with open(src_path, 'rb') as fsrc, open(os.path.join(dest_dir, filename), 'wb') as fdst:
                fdst.write(fsrc.read())
            return True
        import urllib.request
        urllib.request.urlretrieve(src, os.path.join(dest_dir, filename))
        return True
    except Exception:
        return False


def _fetch_image_bytes(src):
    '''
    Return bytes for an image source that is a URL or file:// path.
    '''
    try:
        if src.startswith('file://'):
            path = src.replace('file://', '', 1)
            with open(path, 'rb') as fh:
                return fh.read()
        import urllib.request
        with urllib.request.urlopen(src, timeout=20) as resp:
            return resp.read()
    except Exception:
        return None


def _open_folder(path):
    '''
    Cross-platform open folder in file manager.
    '''
    try:
        if sys.platform.startswith('win'):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', path])
        else:
            subprocess.Popen(['xdg-open', path])
    except Exception:
        pass


def _open_file_path(path):
    '''
    Cross-platform open file in default viewer.
    '''
    try:
        if sys.platform.startswith('win'):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', path])
        else:
            subprocess.Popen(['xdg-open', path])
    except Exception:
        pass
