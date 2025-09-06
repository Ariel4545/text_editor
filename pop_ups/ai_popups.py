'''
AI popups: ChatGPT and DALL·E standalone popups.

- Unified OpenAI client (OpenAI and Azure).
- Key dialog with Azure/OpenAI modes and secret bypass mode (Ctrl+Shift+B).
- Chat: modern UI, streaming, presets, Stop button, token estimate, system prompt sidebar.
- DALL·E: prompt/options, progress, URLs/paths list, right-click actions, inline thumbnails, built‑in image viewer (zoom/fit), save/open helpers.
- Uses app.ui_builders.make_pop_ups_window and make_rich_textbox when available; falls back gracefully.

Conventions:
- Single quotes, snake_case, descriptive names.
- Imports are at the top.
'''

import os
import sys
import time
import base64
import webbrowser
import tempfile
import urllib.request
import subprocess
from io import BytesIO
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from threading import Thread, Event

# Optional: Pillow for inline image previews and viewer
try:
	from PIL import Image, ImageTk  # type: ignore
	PIL_AVAILABLE = True
except Exception:
	Image = None
	ImageTk = None
	PIL_AVAILABLE = False

# Optional: OpenAI client (OpenAI or Azure)
try:
	from openai import OpenAI
	OPENAI_AVAILABLE = True
except Exception:
	OpenAI = None
	OPENAI_AVAILABLE = False

from hashlib import sha256

# Updated model catalogs (note: Azure uses deployment name as 'model' param)
CHAT_MODEL_CATALOG = [
	'gpt-4o',
	'gpt-4o-mini',
	'gpt-4.1',
	'gpt-4.1-mini',
	'o3-mini',
]
IMAGE_MODEL_CATALOG = [
	'gpt-image-1',
	'dall-e-3',  # limited sizes/quality
]

# ------------------------------- Utilities --------------------------------- #

def make_popup_window(app, title):
	ui_builders = getattr(app, 'ui_builders', None)
	if ui_builders and hasattr(ui_builders, 'make_pop_ups_window'):
		try:
			return ui_builders.make_pop_ups_window(
				function=build_chat_ui,
				custom_title=title,
				parent=getattr(app, 'root', None),
				name='chatgpt_popup',
				topmost=False,
				modal=False,
			)
		except Exception:
			pass
	if hasattr(app, 'make_pop_ups_window') and callable(app.make_pop_ups_window):
		return app.make_pop_ups_window(lambda: None, title)
	popup_window = tk.Toplevel()
	popup_window.title(title)
	if hasattr(app, 'st_value'):
		try:
			popup_window.attributes('-alpha', app.st_value)
		except Exception:
			pass
	return popup_window


def make_named_popup_window(app, title, *, name, owner_func, parent=None):
	ui_builders = getattr(app, 'ui_builders', None)
	if ui_builders and hasattr(ui_builders, 'make_pop_ups_window'):
		try:
			return ui_builders.make_pop_ups_window(
				function=owner_func,
				custom_title=title,
				parent=parent or getattr(app, 'root', None),
				name=name,
				topmost=False,
				modal=False,
			)
		except Exception:
			pass
	popup_window = tk.Toplevel()
	popup_window.title(title)
	if hasattr(app, 'st_value'):
		try:
			popup_window.attributes('-alpha', app.st_value)
		except Exception:
			pass
	return popup_window


def open_external_link(url):
	webbrowser.open(url)


def open_key_dialog(app, after_open):
	# Prefer unified popup builder for consistent ownership, theming, and singleton behavior
	ui_builders = getattr(app, 'ui_builders', None)
	if ui_builders and hasattr(ui_builders, 'make_pop_ups_window'):
		login_window = ui_builders.make_pop_ups_window(
			function=lambda: open_key_dialog(app, after_open),
			custom_title=getattr(app, 'title_struct', '') + 'connect to OpenAI',
			parent=getattr(app, 'root', None),
			name='openai_key_dialog',
			topmost=False,
			modal=False,
		)
	else:
		login_window = tk.Toplevel()
		if hasattr(app, 'make_tm'):
			app.make_tm(login_window)
		if getattr(app, 'limit_w_s', None) and getattr(app.limit_w_s, 'get', lambda: False)():
			login_window.resizable(False, False)
		login_window.title(getattr(app, 'title_struct', '') + 'connect to OpenAI')

	app.service_type = tk.IntVar(value=getattr(app, '_last_service_type', 1))  # 0=Azure, 1=OpenAI
	app.end_entry_state = False

	form_frame = tk.Frame(login_window, padx=12, pady=10)
	form_frame.pack(fill=tk.BOTH, expand=True)

	title_label = tk.Label(form_frame, text='Connect to OpenAI services', font='arial 12')
	title_label.grid(row=0, column=0, columnspan=4, sticky='w')

	subtitle_label = tk.Label(
		form_frame,
		text='Your key is used only to call the API. It is not sent anywhere else.',
		fg='#a7aab0'
	)
	subtitle_label.grid(row=1, column=0, columnspan=4, sticky='w', pady=(0, 8))

	# Provider
	provider_label = tk.Label(form_frame, text='Provider', font='arial 10')
	provider_label.grid(row=2, column=0, sticky='w', pady=(2, 0))
	service_frame = tk.Frame(form_frame)
	service_frame.grid(row=2, column=1, columnspan=3, sticky='w', pady=(2, 0))
	azure_radio = tk.Radiobutton(service_frame, text='Azure', variable=app.service_type, value=0)
	openai_radio = tk.Radiobutton(service_frame, text='OpenAI', variable=app.service_type, value=1)
	azure_radio.grid(row=0, column=0, padx=(0, 8))
	openai_radio.grid(row=0, column=1)

	# Key entry row
	key_label = tk.Label(form_frame, text='API key', font='arial 10')
	key_label.grid(row=3, column=0, sticky='w', pady=(8, 0))
	key_entry = tk.Entry(form_frame, width=35, show='*')
	key_entry.grid(row=3, column=1, sticky='w', pady=(8, 0))

	# Key helpers
	helpers_frame = tk.Frame(form_frame)
	helpers_frame.grid(row=3, column=2, columnspan=2, sticky='w', pady=(8, 0))
	show_key_var = tk.BooleanVar(value=False)

	def toggle_show_key():
		key_entry.config(show='' if show_key_var.get() else '*')

	show_key_check = tk.Checkbutton(helpers_frame, text='Show', variable=show_key_var, command=toggle_show_key)
	show_key_check.grid(row=0, column=0, padx=(0, 8))

	def paste_from_clipboard():
		try:
			key_entry.delete(0, tk.END)
			key_entry.insert(0, login_window.clipboard_get())
		except Exception:
			pass

	paste_button = tk.Button(helpers_frame, text='Paste', relief=tk.FLAT, command=paste_from_clipboard)
	paste_button.grid(row=0, column=1, padx=(0, 8))

	def clear_key():
		key_entry.delete(0, tk.END)

	clear_button = tk.Button(helpers_frame, text='Clear', relief=tk.FLAT, command=clear_key)
	clear_button.grid(row=0, column=2)

	# Azure-only entries (appear when Azure is selected)
	endpoint_label = tk.Label(form_frame, text='Azure endpoint', font='arial 10')
	endpoint_entry = tk.Entry(form_frame, width=35)
	deployment_label = tk.Label(form_frame, text='Deployment name', font='arial 10')
	deployment_entry = tk.Entry(form_frame, width=35)

	# Help links (change with provider)
	help_link = tk.Label(form_frame, text='Where do I get a key?', fg='blue', font='arial 10 underline', cursor='hand2')
	help_link.grid(row=6, column=0, columnspan=4, sticky='w', pady=(8, 0))

	# Status row (separated from buttons; wrap text to avoid overlap)
	status_frame = tk.Frame(form_frame)
	status_frame.grid(row=7, column=0, columnspan=4, sticky='we', pady=(6, 0))
	status_label = tk.Label(status_frame, text='Not connected', fg='#a7aab0', anchor='w', justify='left')
	status_label.pack(side='left', fill='x', expand=True)
	try:
		status_label.config(wraplength=420)
	except Exception:
		pass
	tiny_progress = ttk.Progressbar(status_frame, mode='indeterminate', length=100)

	# Buttons row (keep everything in one frame to avoid grid-collisions)
	buttons_frame = tk.Frame(form_frame)
	buttons_frame.grid(row=8, column=0, columnspan=4, sticky='we', pady=(10, 0))
	# Back-compat 'Enter' is kept, but placed here to avoid fusing with status row
	enter_button = tk.Button(buttons_frame, text='Enter', relief=tk.FLAT)
	connect_button = tk.Button(buttons_frame, text='Connect', relief=tk.FLAT)
	test_button = tk.Button(buttons_frame, text='Test', relief=tk.FLAT)
	cancel_button = tk.Button(buttons_frame, text='Cancel', relief=tk.FLAT, command=lambda: login_window.destroy())
	# Order: Enter (legacy), Connect, Test, [spacer], Cancel
	enter_button.pack(side='left')
	connect_button.pack(side='left', padx=(8, 0))
	test_button.pack(side='left', padx=(8, 0))
	cancel_button.pack(side='right')

	# Dynamic provider UI toggle
	def update_provider_ui():
		if app.service_type.get() == 0:
			endpoint_label.grid(row=4, column=0, sticky='w', pady=(8, 0))
			endpoint_entry.grid(row=4, column=1, sticky='w', pady=(8, 0))
			deployment_label.grid(row=5, column=0, sticky='w', pady=(6, 0))
			deployment_entry.grid(row=5, column=1, sticky='w', pady=(6, 0))

			endpoint_entry.delete(0, tk.END)
			deployment_entry.delete(0, tk.END)
			endpoint_entry.insert(tk.END, 'https://<name>.openai.azure.com')
			deployment_entry.insert(tk.END, 'your-deployment-name')

			help_link.bind(
				'<Button-1>',
				lambda _e: open_external_link(
					'https://learn.microsoft.com/en-us/azure/ai-services/openai/quickstart?tabs=command-line%2Cpython&pivots=programming-language-python'
				),
			)
		else:
			try:
				endpoint_label.grid_forget()
				endpoint_entry.grid_forget()
				deployment_label.grid_forget()
				deployment_entry.grid_forget()
			except Exception:
				pass
			help_link.bind('<Button-1>', lambda _e: open_external_link('https://platform.openai.com/account/api-keys'))

	# Bind provider toggles
	azure_radio.config(command=update_provider_ui)
	openai_radio.config(command=update_provider_ui)
	update_provider_ui()

	# Backward-compatibility alias for older callers still referencing on_service_change()
	def on_service_change(*_args, **_kwargs):
		update_provider_ui()

	# Status helper
	def set_status(text, *, busy=False, ok=False, err=False):
		# If dialog is already closed, bail out safely
		try:
			if not (status_label and status_label.winfo_exists()):
				return
		except Exception:
			return
		try:
			status_label.config(text=text)
			if ok:
				status_label.config(fg='#98ffa8')
			elif err:
				status_label.config(fg='#ff9b9b')
			else:
				status_label.config(fg='#a7aab0')
		except Exception:
			# Widget might have been destroyed; ignore
			return
		# progress bar visibility
		try:
			if not tiny_progress or not tiny_progress.winfo_exists():
				return
		except Exception:
			return
		try:
			if busy:
				tiny_progress.pack(side='left', padx=(8, 0))
				tiny_progress.start(12)
			else:
				tiny_progress.stop()
				tiny_progress.pack_forget()
		except Exception:
			pass

	# Secret-bypass checker (supports env-configured secret; keeps UI unchanged)
	def _is_secret_bypass(input_text: str) -> bool:
		try:
			secret_plain = os.environ.get('EGON_BYPASS_CODE', '').strip()
			if secret_plain and input_text == secret_plain:
				return True
			secret_hash = os.environ.get('EGON_BYPASS_HASH', '').strip().lower()
			if secret_hash:
				digest = hashlib.sha256(input_text.encode('utf-8')).hexdigest().lower()
				if digest == secret_hash:
					return True
		except Exception:
			pass
		# Legacy phrase (still supported)
		return input_text.strip().lower() == 'bypass mode'

	# Create client from inputs
	def make_client_from_inputs():
		app.key = key_entry.get().strip()
		# Secret bypass code typed directly in API key field
		if _is_secret_bypass(app.key):
			# Signal the caller to stop further UI work and threads
			return 'BYPASS'
		if not OPENAI_AVAILABLE:
			raise RuntimeError('OpenAI client is not available in this environment')
		if app.service_type.get() == 0:
			endpoint_value = endpoint_entry.get().strip().rstrip('/')
			if not endpoint_value or not app.key:
				raise ValueError('Azure endpoint and key are required')
			app.deployment_name = deployment_entry.get().strip()
			if not app.deployment_name:
				raise ValueError('Azure deployment name is required')
			app.azure_api_version = '2024-08-01-preview'
			app.api_client = OpenAI(
				base_url=f'{endpoint_value}/openai/deployments/{app.deployment_name}?api-version={app.azure_api_version}',
				default_headers={'api-key': app.key},
			)
		else:
			if not app.key:
				raise ValueError('API key is required')
			app.api_client = OpenAI(api_key=app.key)
			app.azure_api_version = None
		return 'OK'

	# Test button
	def do_test_connection():
		try:
			set_status('Connecting…', busy=True)
			result = make_client_from_inputs()
			if result == 'BYPASS':
				# Activate bypass and exit without touching destroyed widgets
				secret_bypass()
				return

			def worker():
				ok = False
				err_msg = ''
				try:
					app.api_client.models.list()
					ok = True
				except Exception as exc:
					err_msg = str(exc) or 'Connection failed'
				finally:
					def finish():
						set_status('Connected ✓' if ok else f'Error: {err_msg}',
								   ok=ok, err=not ok, busy=False)

					try:
						login_window.after(0, finish)
					except Exception:
						pass

			# If window already closed, avoid starting threads that will touch UI
			try:
				if not login_window or not login_window.winfo_exists():
					return
			except Exception:
				return
			Thread(target=worker, daemon=True).start()
		except Exception as exc:
			set_status(f'Error: {exc}', err=True, busy=False)

	# Connect button
	def do_connect():
		try:
			set_status('Connecting…', busy=True)
			result = make_client_from_inputs()
			if result == 'BYPASS':
				# Activate bypass and exit without touching destroyed widgets
				secret_bypass()
				return

			def worker():
				ok = False
				err_msg = ''
				try:
					app.api_client.models.list()
					ok = True
				except Exception as exc:
					err_msg = str(exc) or 'Connection failed'
				finally:
					def finish():
						if ok:
							set_status('Connected ✓', ok=True, busy=False)
							try:
								app._last_service_type = int(app.service_type.get())
							except Exception:
								pass
							try:
								login_window.destroy()
							except Exception:
								pass
							setattr(app, 'openai_code', True)
							after_open()
						else:
							set_status(f'Error: {err_msg}', err=True, busy=False)

					try:
						login_window.after(0, finish)
					except Exception:
						pass

			# If window already closed, avoid starting threads that will touch UI
			try:
				if not login_window or not login_window.winfo_exists():
					return
			except Exception:
				return
			Thread(target=worker, daemon=True).start()
		except Exception as exc:
			set_status(f'Error: {exc}', err=True, busy=False)

	# Wire buttons (Enter mirrors Connect for backward compatibility)
	connect_button.config(command=do_connect)
	enter_button.config(command=do_connect)
	test_button.config(command=do_test_connection)

	# Secret bypass and shortcuts
	def secret_bypass(_=None):
		setattr(app, '_gpt_bypass', True)
		try:
			# stop progress UI safely before destroy
			set_status('', busy=False)
		except Exception:
			pass
		try:
			login_window.destroy()
		except Exception:
			pass
		setattr(app, 'openai_code', False)
		after_open()

	login_window.bind('<Control-Shift-b>', secret_bypass)

	# Shortcuts
	def on_return(_e=None):
		do_connect()
		return 'break'

	login_window.bind('<Return>', on_return)
	login_window.bind('<Escape>', lambda _e: (login_window.destroy(), 'break'))

	# Autofocus
	try:
		key_entry.focus_set()
	except Exception:
		pass

	# Tooltips via ui_builders, when available
	try:
		if ui_builders and hasattr(ui_builders, 'place_toolt'):
			ui_builders.place_toolt([
				(enter_button, 'Same as Connect (legacy)'),
				(connect_button, 'Connect and validate the API setup'),
				(test_button, 'Test connection without closing this dialog'),
				(paste_button, 'Paste key from clipboard'),
				(clear_button, 'Clear the key field'),
				(show_key_check, 'Toggle key visibility'),
			])
	except Exception:
		pass

	# Ensure initial provider state for legacy callers using on_service_change()
	on_service_change()

	# Center and raise
	try:
		if ui_builders:
			ui_builders._center_on_parent(login_window)
		login_window.lift()
		login_window.focus_force()
	except Exception:
		pass

# ------------------------------- ChatGPT ----------------------------------- #

def open_chatgpt(app):
	def open_ui():
		build_chat_ui(app)

	if getattr(app, '_gpt_bypass', False):
		open_ui()
		return

	if OPENAI_AVAILABLE and getattr(app, 'openai_code', False):
		open_ui()
	elif OPENAI_AVAILABLE:
		open_key_dialog(app, open_ui)
	else:
		open_ui()


def build_chat_ui(app):
	window = make_popup_window(app, 'ChatGPT')
	try:
		if getattr(app, 'gpt_image', None):
			window.tk.call('wm', 'iconphoto', window._w, app.gpt_image)
	except Exception:
		pass

	background_color = '#1f1f24'
	background_alt_color = '#2a2a31'
	foreground_color = '#EAECEE'
	accent_color = '#4f8cff'
	accent_dark_color = '#3a69c7'

	window.configure(bg=background_color)
	outer_frame = tk.Frame(window, bg=background_color)
	outer_frame.pack(fill=tk.BOTH, expand=True)

	# Header
	header_frame = tk.Frame(outer_frame, bg=background_alt_color, padx=10, pady=8)
	header_frame.pack(fill=tk.X)

	model_values = CHAT_MODEL_CATALOG[:]
	if not hasattr(app, 'gpt_model') or not app.gpt_model:
		app.gpt_model = 'gpt-4o-mini'
	app._gpt_stream = getattr(app, '_gpt_stream', True)
	app._gpt_temp = getattr(app, '_gpt_temp', 0.7)

	model_label = tk.Label(header_frame, text='Model', bg=background_alt_color, fg=foreground_color)
	model_label.pack(side='left')

	model_combobox = ttk.Combobox(header_frame, values=model_values, state='readonly', width=16)
	model_combobox.set(app.gpt_model)
	model_combobox.pack(side='left', padx=(6, 12))

	temperature_label = tk.Label(header_frame, text='Temperature', bg=background_alt_color, fg=foreground_color)
	temperature_label.pack(side='left')

	temperature_scale = ttk.Scale(
		header_frame,
		from_=0.0,
		to=1.5,
		orient='horizontal',
		length=160,
		command=lambda value: setattr(app, '_gpt_temp', float(value)),
	)
	temperature_scale.set(app._gpt_temp)
	temperature_scale.pack(side='left', padx=(6, 16))

	stream_var = tk.BooleanVar(value=app._gpt_stream)

	def sync_stream_flag():
		app._gpt_stream = bool(stream_var.get())

	stream_checkbox = ttk.Checkbutton(header_frame, text='Stream', variable=stream_var, command=sync_stream_flag)
	stream_checkbox.pack(side='left', padx=(0, 12))

	style_label = tk.Label(header_frame, text='Style', bg=background_alt_color, fg=foreground_color)
	style_label.pack(side='left', padx=(8, 4))

	style_combobox = ttk.Combobox(header_frame, values=['Default', 'Concise', 'Detailed', 'Code'], state='readonly', width=12)
	style_combobox.set('Default')
	style_combobox.pack(side='left', padx=(0, 8))

	def style_to_system_prompt(style_name):
		if style_name == 'Concise':
			return 'You are concise. Prefer short answers without losing critical details.'
		if style_name == 'Detailed':
			return 'You are thorough and explanatory. Provide step-by-step reasoning when helpful.'
		if style_name == 'Code':
			return 'You respond with code-first answers when appropriate, including brief explanations.'
		return ''

	def apply_preset():
		selected_style = style_combobox.get()
		prompt_text = style_to_system_prompt(selected_style)
		system_prompt_text.delete('1.0', tk.END)
		system_prompt_text.insert('1.0', prompt_text)
		app.gpt_system = prompt_text
		if not hasattr(app, 'gpt_messages') or not isinstance(getattr(app, 'gpt_messages'), list):
			app.gpt_messages = []
		if app.gpt_messages and app.gpt_messages[0].get('role') == 'system':
			app.gpt_messages[0]['content'] = app.gpt_system
		elif app.gpt_system:
			app.gpt_messages.insert(0, {'role': 'system', 'content': app.gpt_system})

	button_style = dict(bg=accent_color, fg='white', activebackground=accent_dark_color, activeforeground='white', relief=tk.FLAT, padx=10, pady=5)
	apply_button = tk.Button(header_frame, text='Apply', command=apply_preset, **button_style)
	apply_button.pack(side='left', padx=(0, 12))

	if not hasattr(app, '_gpt_bypass'):
		app._gpt_bypass = False
	bypass_label = tk.Label(header_frame, text='Bypass: OFF', bg=background_alt_color, fg='#a7aab0')
	bypass_label.pack(side='left', padx=(6, 6))

	def render_bypass_label():
		text_value = 'Bypass: ON' if app._gpt_bypass else 'Bypass: OFF'
		color_value = '#98ffa8' if app._gpt_bypass else '#a7aab0'
		bypass_label.config(text=text_value, fg=color_value)

	def toggle_bypass(_=None):
		app._gpt_bypass = not app._gpt_bypass
		render_bypass_label()

	window.bind('<Control-Shift-b>', toggle_bypass)
	render_bypass_label()

	streaming_hint = tk.Label(header_frame, text='Streaming off', bg=background_alt_color, fg='#a7aab0')
	streaming_hint.pack(side='left', padx=(10, 0))

	def update_streaming_hint(*_a):
		streaming_hint.config(text='Streaming on' if stream_var.get() else 'Streaming off')

	stream_var.trace_add('write', lambda *_: update_streaming_hint())
	update_streaming_hint()

	# Header actions
	def clear_chat():
		app.gpt_messages = []
		chat_text.configure(state=tk.NORMAL)
		chat_text.delete('1.0', tk.END)
		chat_text.configure(state=tk.DISABLED)
		update_token_counter()

	def copy_last():
		last_text_value = ''
		for message in reversed(getattr(app, 'gpt_messages', [])):
			if message['role'] == 'assistant':
				last_text_value = message['content']
				break
		if last_text_value:
			window.clipboard_clear()
			window.clipboard_append(last_text_value)

	def save_transcript():
		path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Text', '*.txt')])
		if not path:
			return
		with open(path, 'w', encoding='utf-8') as file_handle:
			for message in getattr(app, 'gpt_messages', []):
				tag = message['role'].upper()
				file_handle.write(f'[{tag}] {message["content"]}\n\n')

	clear_button = tk.Button(header_frame, text='Clear', command=clear_chat, **button_style)
	save_button = tk.Button(header_frame, text='Save', command=save_transcript, **button_style)
	copy_last_button = tk.Button(header_frame, text='Copy last', command=copy_last, **button_style)
	clear_button.pack(side='right', padx=(8, 0))
	save_button.pack(side='right', padx=8)
	copy_last_button.pack(side='right', padx=8)

	# Body split
	body_frame = tk.Frame(outer_frame, bg=background_color)
	body_frame.pack(fill=tk.BOTH, expand=True)

	# Sidebar: system prompt
	sidebar_frame = tk.Frame(body_frame, bg=background_color, padx=10, pady=10)
	sidebar_frame.pack(side='left', fill=tk.Y)
	system_label = tk.Label(sidebar_frame, text='System prompt', bg=background_color, fg=foreground_color)
	system_label.pack(anchor='w')

	ui_builders = getattr(app, 'ui_builders', None)
	if ui_builders and hasattr(ui_builders, 'make_rich_textbox'):
		sys_container, system_prompt_text, _sys_scroll = ui_builders.make_rich_textbox(
			parent_container=sidebar_frame,
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
		sys_container = tk.Frame(sidebar_frame, bg=background_color)
		sys_container.pack(fill=tk.Y)
		system_prompt_text = tk.Text(sys_container, height=6, width=32, bg=background_alt_color, fg=foreground_color, insertbackground=foreground_color, wrap='word', relief=tk.FLAT)
		system_prompt_text.pack(fill=tk.Y)

	if not hasattr(app, 'gpt_system'):
		app.gpt_system = ''
	system_prompt_text.insert('1.0', app.gpt_system)
	system_prompt_text.bind('<FocusOut>', lambda event: setattr(app, 'gpt_system', system_prompt_text.get('1.0', tk.END).strip()))

	# Chat area
	center_frame = tk.Frame(body_frame, bg=background_color, padx=0, pady=10)
	center_frame.pack(side='left', fill=tk.BOTH, expand=True)

	if ui_builders and hasattr(ui_builders, 'make_rich_textbox'):
		chat_container, chat_text, chat_scroll = ui_builders.make_rich_textbox(
			parent_container=center_frame,
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
		chat_container = tk.Frame(center_frame, bg=background_color)
		chat_container.pack(fill=tk.BOTH, expand=True)
		chat_scroll = ttk.Scrollbar(chat_container)
		chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
		chat_text = tk.Text(
			chat_container,
			bg=background_color,
			fg=foreground_color,
			font='Helvetica 13',
			width=60,
			yscrollcommand=chat_scroll.set,
			undo=True,
			wrap='word',
			state=tk.DISABLED,
			relief=tk.FLAT,
			insertbackground=foreground_color,
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
	footer_frame = tk.Frame(center_frame, bg=background_alt_color, padx=10, pady=10)
	footer_frame.pack(fill=tk.X)
	input_text = tk.Text(footer_frame, height=3, bg='#2C3E50', fg=foreground_color, font='Helvetica 13', wrap='word', insertbackground=foreground_color, relief=tk.FLAT)
	input_text.pack(side='left', fill=tk.BOTH, expand=True, padx=(0, 10))

	stop_event = Event()

	send_button = tk.Button(
		footer_frame,
		text='Send',
		bg=accent_color,
		fg='white',
		activebackground=accent_dark_color,
		activeforeground='white',
		relief=tk.FLAT,
		padx=10,
		pady=5,
		command=lambda: Thread(target=ask_and_stream, args=(app, window, chat_text, input_text, model_combobox, stream_var, stop_event), daemon=True).start(),
	)
	send_button.pack(side='left')

	stop_button = tk.Button(
		footer_frame,
		text='Stop',
		bg='#b84a4a',
		fg='white',
		activebackground='#8f3838',
		activeforeground='white',
		relief=tk.FLAT,
		padx=10,
		pady=5,
		command=stop_event.set,
	)
	stop_button.pack(side='left', padx=(10, 0))

	# Status
	status_bar = tk.Frame(outer_frame, bg=background_color, padx=10, pady=6)
	status_bar.pack(fill=tk.X)
	token_label = tk.Label(status_bar, text='Tokens: 0', bg=background_color, fg='#a7aab0')
	token_label.pack(side='left')

	app._chat_widgets = dict(
		root_window=window,
		chat_text=chat_text,
		input_text=input_text,
		token_label=token_label,
		model_combobox=model_combobox,
		stream_var=stream_var,
		stop_event=stop_event,
		style_combobox=style_combobox,
	)

	if not hasattr(app, 'gpt_messages') or not isinstance(getattr(app, 'gpt_messages'), list):
		app.gpt_messages = []
	if app.gpt_system:
		if not app.gpt_messages or app.gpt_messages[0].get('role') != 'system':
			app.gpt_messages.insert(0, {'role': 'system', 'content': app.gpt_system})

	def update_token_counter():
		word_count = 0
		for message in app.gpt_messages:
			word_count += len(str(message.get('content', '')).split())
		token_count = max(1, int(word_count / 0.75))
		token_label.config(text=f'Tokens: {token_count}')

	def on_return_key(event):
		if event.keysym == 'Return' and not (event.state & 0x0001):
			Thread(target=ask_and_stream, args=(app, window, chat_text, input_text, model_combobox, stream_var, stop_event), daemon=True).start()
			return 'break'

	input_text.bind('<KeyPress-Return>', on_return_key)

	def set_style(style_value):
		style_combobox.set(style_value)
		apply_preset()

	window.bind('<Control-1>', lambda event: set_style('Concise'))
	window.bind('<Control-2>', lambda event: set_style('Detailed'))
	window.bind('<Control-3>', lambda event: set_style('Code'))

	update_token_counter()
# ---- Chat helpers (fix unresolved references: insert_bubble, append_stream_chunk) ----
def insert_bubble(chat_text: tk.Text, role: str, content: str) -> None:
	'''
	Insert a chat 'bubble' for the given role into the chat_text widget.
	Expected tag names are configured in build_chat_ui():
	  - role headers: 'role', 'role_user', 'role_ai', 'role_sys'
	  - bubble bodies: 'bubble', 'bubble_user', 'bubble_ai', 'bubble_sys'
	'''
	if not content:
		return
	try:
		chat_text.configure(state=tk.NORMAL)
		chat_text.insert(tk.END, '\n')
		role_lower = (role or 'system').strip().lower()
		if role_lower == 'user':
			chat_text.insert(tk.END, 'You\n', ('role', 'role_user'))
			chat_text.insert(tk.END, content.strip() + '\n', ('bubble', 'bubble_user'))
		elif role_lower == 'assistant':
			chat_text.insert(tk.END, 'AI\n', ('role', 'role_ai'))
			chat_text.insert(tk.END, content.strip() + '\n', ('bubble', 'bubble_ai'))
		else:
			chat_text.insert(tk.END, 'System\n', ('role', 'role_sys'))
			chat_text.insert(tk.END, content.strip() + '\n', ('bubble', 'bubble_sys'))
		chat_text.insert(tk.END, '\n')
		chat_text.see(tk.END)
	except Exception:
		pass
	finally:
		try:
			chat_text.configure(state=tk.DISABLED)
		except Exception:
			pass


def append_stream_chunk(chat_text: tk.Text, chunk_text: str) -> None:
	'''
	Append incremental streaming content into the last AI bubble.
	Assumes ask_and_stream started the AI bubble by inserting:
		'\nAI\n' (role tags) and then an empty '' with ('bubble', 'bubble_ai') tags.
	'''
	if not chunk_text:
		return
	try:
		chat_text.configure(state=tk.NORMAL)
		chat_text.insert(tk.END, chunk_text, ('bubble', 'bubble_ai'))
		chat_text.see(tk.END)
	except Exception:
		pass
	finally:
		try:
			chat_text.configure(state=tk.DISABLED)
		except Exception:
			pass


def ask_and_stream(app, window, chat_text, input_text, model_combobox, stream_var, stop_event):
	try:
		user_text_value = input_text.get('1.0', tk.END).strip()
		if not user_text_value:
			return
		input_text.delete('1.0', tk.END)
		stop_event.clear()

		app.gpt_model = model_combobox.get() or app.gpt_model
		use_stream = bool(stream_var.get())
		temperature_value = float(getattr(app, '_gpt_temp', 0.7))

		window.after(0, lambda: insert_bubble(chat_text, 'user', user_text_value))

		if not hasattr(app, 'gpt_messages') or not isinstance(app.gpt_messages, list):
			app.gpt_messages = []
		if not app.gpt_messages and getattr(app, 'gpt_system', ''):
			app.gpt_messages.append({'role': 'system', 'content': app.gpt_system})
		app.gpt_messages.append({'role': 'user', 'content': user_text_value})

		def start_ai_bubble():
			chat_text.configure(state=tk.NORMAL)
			chat_text.insert(tk.END, '\nAI\n', ('role', 'role_ai'))
			chat_text.insert(tk.END, '', ('bubble', 'bubble_ai'))
			chat_text.configure(state=tk.DISABLED)

		window.after(0, start_ai_bubble)

		accumulated = {'text': ''}

		if getattr(app, '_gpt_bypass', False):
			try:
				style_value = app._chat_widgets.get('style_combobox').get()
			except Exception:
				style_value = 'Default'

			def fake_answer(text_in):
				if style_value == 'Concise':
					return f'{text_in[:120]}... (concise UI test)'
				if style_value == 'Detailed':
					return f'This is a detailed UI test response for: \'{text_in}\'.\n\n1) Overview\n2) Steps\n3) Notes\n\nEnd of simulation.'
				if style_value == 'Code':
					return '```python\n# Simulated code block\nprint(\'UI test\')\n```\nExplanation: This is a fake response.'
				return f'Echo: {text_in}\n\n(This is a simulated response for UI testing.)'

			answer_text = fake_answer(user_text_value)
			if use_stream:
				for char in answer_text:
					if stop_event.is_set():
						break
					window.after(0, lambda c=char: append_stream_chunk(chat_text, c))
					time.sleep(0.01)
				window.after(0, lambda: append_stream_chunk(chat_text, '\n'))
			else:
				window.after(0, lambda: insert_bubble(chat_text, 'assistant', answer_text))
			accumulated['text'] = answer_text
		else:
			if not OPENAI_AVAILABLE or not getattr(app, 'api_client', None):
				fallback_text = f'Echo: {user_text_value}\n\n(This is a simulated response because no API client is configured.)'
				if use_stream:
					for char in fallback_text:
						if stop_event.is_set():
							break
						window.after(0, lambda c=char: append_stream_chunk(chat_text, c))
						time.sleep(0.01)
					window.after(0, lambda: append_stream_chunk(chat_text, '\n'))
				else:
					window.after(0, lambda: insert_bubble(chat_text, 'assistant', fallback_text))
				accumulated['text'] = fallback_text
			else:
				messages_payload = list(app.gpt_messages)
				model_param = app.deployment_name if getattr(app, 'service_type', tk.IntVar(value=1)).get() == 0 else app.gpt_model

				if bool(getattr(app, '_gpt_stream', True)):
					response_stream = app.api_client.chat.completions.create(
						model=model_param,
						messages=messages_payload,
						stream=True,
						temperature=temperature_value,
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
							window.after(0, lambda d=delta_content: append_stream_chunk(chat_text, d))
					window.after(0, lambda: append_stream_chunk(chat_text, '\n'))
				else:
					response_obj = app.api_client.chat.completions.create(
						model=model_param,
						messages=messages_payload,
						temperature=temperature_value,
					)
					answer_text = response_obj.choices[0].message.content
					window.after(0, lambda: insert_bubble(chat_text, 'assistant', answer_text))
					accumulated['text'] = answer_text or ''

		if accumulated['text']:
			app.gpt_messages.append({'role': 'assistant', 'content': accumulated['text']})

		if len(app.gpt_messages) > 40:
			system_messages = [m for m in app.gpt_messages if m['role'] == 'system'][:1]
			app.gpt_messages = (system_messages + app.gpt_messages[-38:]) if system_messages else app.gpt_messages[-38:]

		token_label = app._chat_widgets.get('token_label')
		if token_label:
			def update_token_counter():
				total_words = 0
				for message in app.gpt_messages:
					total_words += len(str(message.get('content', '')).split())
				total_tokens = max(1, int(total_words / 0.75))
				token_label.config(text=f'Tokens: {total_tokens}')
			window.after(0, update_token_counter)

	except Exception as exception:
		window.after(0, lambda: insert_bubble(chat_text, 'system', f'Error: {exception}'))


# -------------------------------- DALL·E ----------------------------------- #

def open_dalle(app):
	def open_ui():
		build_dalle_ui(app)

	if getattr(app, '_gpt_bypass', False):
		open_ui()
		return

	if OPENAI_AVAILABLE and getattr(app, 'openai_code', False):
		open_ui()
	elif OPENAI_AVAILABLE:
		open_key_dialog(app, open_ui)
	else:
		open_ui()

def build_dalle_ui(app):
	window = make_named_popup_window(app, 'DALL·E', name='dalle_popup', owner_func=build_dalle_ui)
	try:
		if getattr(app, 'gpt_image', None):
			window.tk.call('wm', 'iconphoto', window._w, app.gpt_image)
	except Exception:
		pass

	background_color = '#1f1f24'
	background_alt_color = '#2a2a31'
	foreground_color = '#EAECEE'
	accent_color = '#4f8cff'
	accent_dark_color = '#3a69c7'

	window.configure(bg=background_color)
	outer_frame = tk.Frame(window, bg=background_color)
	outer_frame.pack(fill=tk.BOTH, expand=True)

	# Header: prompt + options
	header_frame = tk.Frame(outer_frame, bg=background_alt_color, padx=10, pady=8)
	header_frame.pack(fill=tk.X)

	model_label = tk.Label(header_frame, text='Model', bg=background_alt_color, fg=foreground_color)
	model_label.pack(side='left')

	model_combobox = ttk.Combobox(header_frame, values=IMAGE_MODEL_CATALOG[:], state='readonly', width=16)
	model_combobox.set('gpt-image-1')
	model_combobox.pack(side='left', padx=(6, 12))

	prompt_label = tk.Label(header_frame, text='Prompt', bg=background_alt_color, fg=foreground_color)
	prompt_label.pack(side='left')

	prompt_entry = tk.Entry(header_frame, width=60, bg='#2C3E50', fg=foreground_color, insertbackground=foreground_color, relief=tk.FLAT)
	prompt_entry.pack(side='left', padx=(6, 12))
	prompt_entry.insert(0, getattr(app, 'dalle_prompt', 'An eco-friendly computer from the 90s in the style of vaporwave'))

	size_label = tk.Label(header_frame, text='Size', bg=background_alt_color, fg=foreground_color)
	size_label.pack(side='left')

	size_combobox = ttk.Combobox(header_frame, values=['256x256', '512x512', '1024x1024', '2048x2048'], state='readonly', width=12)
	size_combobox.set('1024x1024')
	size_combobox.pack(side='left', padx=(6, 12))

	count_label = tk.Label(header_frame, text='Count', bg=background_alt_color, fg=foreground_color)
	count_label.pack(side='left')

	count_combobox = ttk.Combobox(header_frame, values=[str(n) for n in range(1, 9)], state='readonly', width=4)
	count_combobox.set('1')
	count_combobox.pack(side='left', padx=(6, 12))

	quality_label = tk.Label(header_frame, text='Quality', bg=background_alt_color, fg=foreground_color)
	quality_label.pack(side='left')

	quality_combobox = ttk.Combobox(header_frame, values=['standard', 'hd'], state='readonly', width=10)
	quality_combobox.set('standard')
	quality_combobox.pack(side='left', padx=(6, 12))

	def on_image_model_change(_evt=None):
		model_name = model_combobox.get()
		if model_name == 'dall-e-3':
			size_combobox['values'] = ['1024x1024']
			if size_combobox.get() not in size_combobox['values']:
				size_combobox.set('1024x1024')
			quality_combobox['values'] = ['standard', 'hd']
		else:
			size_combobox['values'] = ['256x256', '512x512', '1024x1024', '2048x2048']
			if size_combobox.get() not in size_combobox['values']:
				size_combobox.set('1024x1024')
			quality_combobox['values'] = ['standard', 'hd']

	model_combobox.bind('<<ComboboxSelected>>', on_image_model_change)
	on_image_model_change()

	# View mode selector (Split / Gallery / Viewer / List)
	view_mode_label = tk.Label(header_frame, text='View', bg=background_alt_color, fg=foreground_color)
	view_mode_label.pack(side='left', padx=(8, 4))
	view_modes = ['Split', 'Gallery', 'Viewer', 'List']
	current_view_mode = getattr(app, '_dalle_view_mode', 'Split')
	if current_view_mode not in view_modes:
		current_view_mode = 'Split'
	view_mode_var = tk.StringVar(value=current_view_mode)
	view_mode_combobox = ttk.Combobox(header_frame, values=view_modes, state='readonly', width=10, textvariable=view_mode_var)
	view_mode_combobox.pack(side='left', padx=(0, 8))

	# Actions + progress
	action_bar_frame = tk.Frame(outer_frame, bg=background_color, padx=10, pady=8)
	action_bar_frame.pack(fill=tk.X)

	button_style = dict(bg=accent_color, fg='white', activebackground=accent_dark_color, activeforeground='white', relief=tk.FLAT, padx=10, pady=5)
	imagine_button = tk.Button(action_bar_frame, text='Imagine', **button_style)
	imagine_button.pack(side='left')

	open_urls_button = tk.Button(action_bar_frame, text='Open URL(s)', **button_style, state=tk.DISABLED)
	open_urls_button.pack(side='left', padx=(10, 0))

	save_button = tk.Button(action_bar_frame, text='Save image(s)...', **button_style, state=tk.DISABLED)
	save_button.pack(side='left', padx=(10, 0))

	progressbar = ttk.Progressbar(action_bar_frame, mode='indeterminate', length=160)
	progressbar.pack(side='right', padx=(10, 0))

	status_label = tk.Label(action_bar_frame, text='Ready', bg=background_color, fg='#a7aab0')
	status_label.pack(side='right')

	# Split main area with paned window
	split_paned = ttk.Panedwindow(outer_frame, orient=tk.HORIZONTAL)
	split_paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

	# Left: output list + thumbnails
	left_frame = tk.Frame(split_paned, bg=background_color)
	split_paned.add(left_frame, weight=1)

	output_container = tk.Frame(left_frame, bg=background_color)
	output_container.pack(fill=tk.BOTH, expand=True)

	output_scrollbar = ttk.Scrollbar(output_container, orient='vertical')
	output_text = tk.Text(
		output_container,
		bg=background_color,
		fg=foreground_color,
		wrap='none',
		font='Helvetica 11',
		relief=tk.FLAT,
		insertbackground=foreground_color,
		height=10,
		yscrollcommand=output_scrollbar.set,
	)
	output_scrollbar.config(command=output_text.yview)
	output_scrollbar.pack(side='right', fill='y')
	output_text.pack(side='left', fill='both', expand=True)
	output_text.configure(state=tk.DISABLED)

	context_menu = tk.Menu(window, tearoff=0)
	context_menu.add_command(label='Copy selection', command=lambda: copy_selected_text(window, output_text))
	context_menu.add_command(label='Open selection', command=lambda: open_selected_urls(output_text))

	def on_context_menu(event):
		try:
			context_menu.tk_popup(event.x_root, event.y_root)
		finally:
			context_menu.grab_release()

	output_text.bind('<Button-3>', on_context_menu)

	thumbs_group_frame = tk.LabelFrame(left_frame, text='Thumbnails', bg=background_color, fg=foreground_color)
	thumbs_group_frame.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

	thumbnails_canvas = tk.Canvas(thumbs_group_frame, bg=background_color, highlightthickness=0)
	thumbnails_v_scroll = ttk.Scrollbar(thumbs_group_frame, orient='vertical', command=thumbnails_canvas.yview)
	thumbnails_h_scroll = ttk.Scrollbar(thumbs_group_frame, orient='horizontal', command=thumbnails_canvas.xview)
	thumbnails_container = tk.Frame(thumbnails_canvas, bg=background_color)

	thumbnails_container.bind(
		'<Configure>',
		lambda event: thumbnails_canvas.configure(scrollregion=thumbnails_canvas.bbox('all'))
	)
	thumbnails_canvas.create_window((0, 0), window=thumbnails_container, anchor='nw')
	thumbnails_canvas.configure(yscrollcommand=thumbnails_v_scroll.set, xscrollcommand=thumbnails_h_scroll.set)

	thumbnails_canvas.grid(row=0, column=0, sticky='nsew')
	thumbnails_v_scroll.grid(row=0, column=1, sticky='ns')
	thumbnails_h_scroll.grid(row=1, column=0, sticky='ew')
	thumbs_group_frame.grid_rowconfigure(0, weight=1)
	thumbs_group_frame.grid_columnconfigure(0, weight=1)

	# Smooth scroll for thumbnails across platforms
	def thumbs_mousewheel(event):
		delta_units = 0
		if hasattr(event, 'delta') and event.delta:
			delta_units = -1 if event.delta > 0 else 1
		elif getattr(event, 'num', None) in (4, 5):
			delta_units = -1 if event.num == 4 else 1
		thumbnails_canvas.yview_scroll(delta_units, 'units')
		return 'break'

	thumbnails_canvas.bind('<MouseWheel>', thumbs_mousewheel)
	thumbnails_canvas.bind('<Button-4>', thumbs_mousewheel)
	thumbnails_canvas.bind('<Button-5>', thumbs_mousewheel)

	thumbnails_refs = []

	# Right: viewer
	viewer_frame = tk.Frame(split_paned, bg=background_color)
	split_paned.add(viewer_frame, weight=1)

	viewer_toolbar = tk.Frame(viewer_frame, bg=background_alt_color)
	viewer_toolbar.pack(fill=tk.X)
	viewer_title = tk.Label(viewer_toolbar, text='Viewer', bg=background_alt_color, fg=foreground_color)
	viewer_title.pack(side='left', padx=8)

	zoom_in_button = tk.Button(viewer_toolbar, text='Zoom +', **button_style)
	zoom_out_button = tk.Button(viewer_toolbar, text='Zoom -', **button_style)
	fit_button = tk.Button(viewer_toolbar, text='Fit', **button_style)
	zoom_in_button.pack(side='right', padx=4, pady=4)
	zoom_out_button.pack(side='right', padx=4, pady=4)
	fit_button.pack(side='right', padx=4, pady=4)

	viewer_container = tk.Frame(viewer_frame, bg=background_color)
	viewer_container.pack(fill=tk.BOTH, expand=True)

	viewer_canvas = tk.Canvas(viewer_container, bg=background_color, highlightthickness=0)
	viewer_v_scroll = ttk.Scrollbar(viewer_container, orient='vertical', command=viewer_canvas.yview)
	viewer_h_scroll = ttk.Scrollbar(viewer_container, orient='horizontal', command=viewer_canvas.xview)
	viewer_canvas.configure(yscrollcommand=viewer_v_scroll.set, xscrollcommand=viewer_h_scroll.set)

	viewer_canvas.grid(row=0, column=0, sticky='nsew')
	viewer_v_scroll.grid(row=0, column=1, sticky='ns')
	viewer_h_scroll.grid(row=1, column=0, sticky='ew')
	viewer_container.grid_rowconfigure(0, weight=1)
	viewer_container.grid_columnconfigure(0, weight=1)

	# Mouse wheel zoom (Ctrl + wheel)
	def viewer_mousewheel_zoom(event):
		# Control key: 0x0004 (platform dependent; this is standard Tk mask)
		if (event.state & 0x0004) == 0:
			return
		factor = 1.1 if getattr(event, 'delta', 0) > 0 or getattr(event, 'num', 0) == 4 else 0.9
		do_zoom(factor)
		return 'break'

	viewer_canvas.bind('<MouseWheel>', viewer_mousewheel_zoom)
	viewer_canvas.bind('<Button-4>', viewer_mousewheel_zoom)
	viewer_canvas.bind('<Button-5>', viewer_mousewheel_zoom)

	viewer_image_ref = {'pil': None, 'tk': None, 'scale': 1.0}
	last_paths_or_urls = []

	# Paned helpers
	def paned_has(frame_widget):
		try:
			return str(frame_widget) in split_paned.panes()
		except Exception:
			return False

	def ensure_added(frame_widget, weight=1):
		if not paned_has(frame_widget):
			split_paned.add(frame_widget, weight=weight)

	def ensure_removed(frame_widget):
		if paned_has(frame_widget):
			try:
				split_paned.forget(frame_widget)
			except Exception:
				pass

	def apply_view_mode():
		mode = view_mode_var.get()
		setattr(app, '_dalle_view_mode', mode)
		# Reset left frame packing
		try:
			for child in left_frame.pack_slaves():
				child.pack_forget()
		except Exception:
			pass

		if mode == 'Split':
			ensure_added(left_frame, weight=1)
			ensure_added(viewer_frame, weight=1)
			output_container.pack(fill=tk.BOTH, expand=True)
			thumbs_group_frame.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
		elif mode == 'Gallery':
			ensure_added(left_frame, weight=1)
			ensure_removed(viewer_frame)
			thumbs_group_frame.pack(fill=tk.BOTH, expand=True)
		elif mode == 'Viewer':
			ensure_removed(left_frame)
			ensure_added(viewer_frame, weight=1)
		elif mode == 'List':
			ensure_added(left_frame, weight=1)
			ensure_removed(viewer_frame)
			output_container.pack(fill=tk.BOTH, expand=True)

		try:
			window.update_idletasks()
		except Exception:
			pass

	view_mode_combobox.bind('<<ComboboxSelected>>', lambda _e: apply_view_mode())
	window.bind('<Alt-1>', lambda e: (view_mode_var.set('Split'), apply_view_mode(), 'break'))
	window.bind('<Alt-2>', lambda e: (view_mode_var.set('Gallery'), apply_view_mode(), 'break'))
	window.bind('<Alt-3>', lambda e: (view_mode_var.set('Viewer'), apply_view_mode(), 'break'))
	window.bind('<Alt-4>', lambda e: (view_mode_var.set('List'), apply_view_mode(), 'break'))

	# Default initial view mode
	apply_view_mode()

	def set_status(text_value):
		status_label.config(text=text_value)

	def set_busy(is_busy):
		if is_busy:
			progressbar.start(12)
			imagine_button.config(state=tk.DISABLED)
		else:
			progressbar.stop()
			imagine_button.config(state=tk.NORMAL)

	def set_result_buttons(enabled):
		state_value = tk.NORMAL if enabled else tk.DISABLED
		open_urls_button.config(state=state_value)
		save_button.config(state=state_value)

	def write_output(lines):
		output_text.configure(state=tk.NORMAL)
		output_text.delete('1.0', tk.END)
		for line_value in lines:
			output_text.insert(tk.END, line_value + '\n')
		output_text.configure(state=tk.DISABLED)

	def open_urls_in_browser():
		if not last_paths_or_urls:
			return
		for url_value in last_paths_or_urls:
			try:
				webbrowser.open(url_value)
			except Exception:
				pass

	def save_images_to_disk():
		if not last_paths_or_urls:
			return
		dest_dir = filedialog.askdirectory(title='Select folder to save image(s)')
		if not dest_dir:
			return
		ok_count = 0
		for index, src in enumerate(last_paths_or_urls, start=1):
			try:
				saved = download_or_copy_image(src, dest_dir, f'dalle_{index}.png')
				if saved:
					ok_count += 1
			except Exception as exc:
				print(f'Failed to save {src}: {exc}')
		set_status(f'Saved {ok_count}/{len(last_paths_or_urls)} image(s)')
		try:
			if ok_count and messagebox.askyesno('Open folder', 'Open the destination folder?'):
				open_folder(dest_dir)
		except Exception:
			pass

	open_urls_button.config(command=open_urls_in_browser)
	save_button.config(command=save_images_to_disk)

	def load_pil_for_view(source):
		if not PIL_AVAILABLE:
			return None
		data = fetch_image_bytes(source)
		if not data:
			return None
		try:
			return Image.open(BytesIO(data)).convert('RGBA')
		except Exception:
			return None

	def redraw_viewer():
		viewer_canvas.delete('all')
		tk_img = viewer_image_ref.get('tk')
		if tk_img is None:
			viewer_canvas.config(scrollregion=(0, 0, 0, 0))
			return
		canvas_width = max(1, viewer_canvas.winfo_width())
		canvas_height = max(1, viewer_canvas.winfo_height())
		x0 = max(0, (canvas_width - tk_img.width()) // 2)
		y0 = max(0, (canvas_height - tk_img.height()) // 2)
		viewer_canvas.create_image(x0, y0, anchor='nw', image=tk_img)
		viewer_canvas.config(scrollregion=(0, 0, tk_img.width(), tk_img.height()))

	def show_image_in_viewer(source):
		pil_img = load_pil_for_view(source)
		viewer_image_ref['pil'] = pil_img
		viewer_image_ref['scale'] = 1.0
		if pil_img is None:
			set_status('Unable to load image for viewer')
			viewer_image_ref['tk'] = None
			redraw_viewer()
			return
		if not PIL_AVAILABLE:
			set_status('Install Pillow for inline viewer')
			viewer_image_ref['tk'] = None
			redraw_viewer()
			return
		tk_img = ImageTk.PhotoImage(pil_img)
		viewer_image_ref['tk'] = tk_img
		redraw_viewer()

	def do_zoom(factor):
		pil_img = viewer_image_ref.get('pil')
		if not (PIL_AVAILABLE and pil_img):
			return
		viewer_image_ref['scale'] = max(0.1, min(6.0, viewer_image_ref['scale'] * factor))
		scale_value = viewer_image_ref['scale']
		try:
			target_width = max(1, int(pil_img.width * scale_value))
			target_height = max(1, int(pil_img.height * scale_value))
			resized = pil_img.resize((target_width, target_height), Image.LANCZOS)
			viewer_image_ref['tk'] = ImageTk.PhotoImage(resized)
			redraw_viewer()
		except Exception:
			pass

	def fit_to_screen():
		pil_img = viewer_image_ref.get('pil')
		if not (PIL_AVAILABLE and pil_img):
			return
		canvas_w = max(1, viewer_canvas.winfo_width())
		canvas_h = max(1, viewer_canvas.winfo_height())
		try:
			scale_w = canvas_w / pil_img.width
			scale_h = canvas_h / pil_img.height
			viewer_image_ref['scale'] = max(0.1, min(6.0, min(scale_w, scale_h)))
			do_zoom(1.0)
		except Exception:
			pass

	def on_viewer_resize(_evt=None):
		redraw_viewer()

	viewer_canvas.bind('<Configure>', on_viewer_resize)

	def on_output_double_click(_evt=None):
		try:
			line_index = output_text.index('insert linestart')
			line_end = output_text.index('insert lineend')
			target = output_text.get(line_index, line_end).strip()
			if target:
				show_image_in_viewer(target)
		except Exception:
			pass

	output_text.bind('<Double-Button-1>', on_output_double_click)

	def render_thumbnails(paths_or_urls):
		for child in thumbnails_container.winfo_children():
			child.destroy()
		thumbnails_refs.clear()
		if not PIL_AVAILABLE:
			info_label = tk.Label(thumbnails_container, text='Install Pillow for inline previews', bg=background_color, fg='#a7aab0')
			info_label.grid(row=0, column=0, sticky='w', padx=2, pady=2)
			return
		max_side = 160
		columns = 4
		for index, image_src in enumerate(paths_or_urls):
			try:
				image_bytes = fetch_image_bytes(image_src)
				if not image_bytes:
					continue
				pil_image = Image.open(BytesIO(image_bytes))
				pil_image.thumbnail((max_side, max_side))
				tk_image = ImageTk.PhotoImage(pil_image)
				thumbnails_refs.append(tk_image)

				def on_thumb_click(source=image_src):
					show_image_in_viewer(source)

				thumb_label = tk.Label(thumbnails_container, image=tk_image, bg=background_color, cursor='hand2')
				thumb_label.bind('<Button-1>', lambda event, s=image_src: on_thumb_click(s))
				row_index, col_index = divmod(index, columns)
				thumb_label.grid(row=row_index, column=col_index, padx=6, pady=6)
			except Exception:
				continue

	def imagine():
		nonlocal last_paths_or_urls
		prompt_value = prompt_entry.get().strip()
		if not prompt_value:
			set_status('Enter a prompt')
			window.bell()
			return

		model_value = model_combobox.get()
		size_value = size_combobox.get()
		try:
			images_count = int(count_combobox.get())
		except Exception:
			images_count = 1
		quality_value = quality_combobox.get()

		app.dalle_prompt = prompt_value
		set_result_buttons(False)
		write_output([])
		render_thumbnails([])
		set_busy(True)
		set_status('Generating...')

		def worker():
			try:
				if getattr(app, '_gpt_bypass', False) or not OPENAI_AVAILABLE or not getattr(app, 'api_client', None):
					fake_urls = [f'https://example.com/fake_image_{i}.png' for i in range(1, images_count + 1)]
					window.after(0, lambda: finish_images(fake_urls, 'Simulation complete'))
					return
				response_obj = app.api_client.images.generate(
					model=model_value,
					prompt=prompt_value,
					size=size_value,
					quality=quality_value,
					n=images_count,
				)
				results = []
				for item in getattr(response_obj, 'data', []) or []:
					url_value = getattr(item, 'url', None)
					if url_value:
						results.append(url_value)
						continue
					b64_value = getattr(item, 'b64_json', None)
					if b64_value:
						path_value = decode_and_write_temp_image(b64_value)
						if path_value:
							results.append('file://' + path_value)
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
			if paths:
				show_image_in_viewer(paths[0])

		def finish_error(exception):
			set_status(f'Error: {exception}')
			set_busy(False)

		Thread(target=worker, daemon=True).start()

	imagine_button.config(command=imagine)

	# Shortcuts
	window.bind('<Control-Return>', lambda event: (imagine(), 'break'))
	window.bind('<Control-s>', lambda event: (save_images_to_disk(), 'break'))
	window.bind('<Control-o>', lambda event: (open_urls_in_browser(), 'break'))
	prompt_entry.bind('<Return>', lambda event: (imagine(), 'break'))

# ------------------------------- Helpers ----------------------------------- #

def copy_selected_text(root_window, text_widget):
	try:
		selected_text = text_widget.selection_get()
		if selected_text:
			root_window.clipboard_clear()
			root_window.clipboard_append(selected_text)
	except Exception:
		pass


def open_selected_urls(text_widget):
	try:
		selection = text_widget.selection_get()
	except Exception:
		selection = ''
	if not selection:
		return
	for line_value in selection.splitlines():
		line_value = line_value.strip()
		if not line_value:
			continue
		try:
			webbrowser.open(line_value)
		except Exception:
			pass


def decode_and_write_temp_image(b64_data):
	try:
		binary = base64.b64decode(b64_data)
		fd_handle, path = tempfile.mkstemp(prefix='dalle_', suffix='.png')
		with os.fdopen(fd_handle, 'wb') as file_handle:
			file_handle.write(binary)
		return path
	except Exception:
		return None


def download_or_copy_image(src, dest_dir, filename):
	try:
		if src.startswith('file://'):
			src_path = src.replace('file://', '', 1)
			if not os.path.isfile(src_path):
				return False
			with open(src_path, 'rb') as file_source, open(os.path.join(dest_dir, filename), 'wb') as file_dest:
				file_dest.write(file_source.read())
			return True
		urllib.request.urlretrieve(src, os.path.join(dest_dir, filename))
		return True
	except Exception:
		return False


def fetch_image_bytes(src):
	try:
		if src.startswith('file://'):
			path = src.replace('file://', '', 1)
			with open(path, 'rb') as file_handle:
				return file_handle.read()
		with urllib.request.urlopen(src, timeout=20) as response:
			return response.read()
	except Exception:
		return None


def open_folder(path):
	try:
		if sys.platform.startswith('win'):
			os.startfile(path)  # type: ignore[attr-defined]
		elif sys.platform == 'darwin':
			subprocess.Popen(['open', path])
		else:
			subprocess.Popen(['xdg-open', path])
	except Exception:
		pass


def open_file_path(path):
	try:
		if sys.platform.startswith('win'):
			os.startfile(path)  # type: ignore[attr-defined]
		elif sys.platform == 'darwin':
			subprocess.Popen(['open', path])
		else:
			subprocess.Popen(['xdg-open', path])
	except Exception:
		pass
