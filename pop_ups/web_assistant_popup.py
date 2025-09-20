from __future__ import annotations

import re
import threading
import tkinter as tk
import tkinter.ttk as ttk
from typing import Any
from tkinter import messagebox
import os
import subprocess
import tempfile

try:
	import requests  # Optional for title preview; handled gracefully if missing
except Exception:
	requests = None  # type: ignore
# Optional QR dependencies (inline rendering). If missing, we’ll gracefully fall back.
try:
	import qrcode  # type: ignore
	_QR_AVAILABLE = True
except Exception:
	_QR_AVAILABLE = False

try:
	from PIL import Image, ImageTk  # type: ignore
	_PIL_AVAILABLE = True
except Exception:
	_PIL_AVAILABLE = False

from urllib.parse import quote_plus  # imports must be top-level (project convention)
import webbrowser  # imports must be top-level (project convention)

# Additional imports or code can go here if needed

def open_web_tools(app: Any) -> None:
	'''
	Open the Web Tools popup for the given app.

	The app can optionally provide:
	  - make_pop_ups_window(callable, custom_title=...) -> tk.Toplevel
	  - dynamic_bg, dynamic_text, dynamic_button (for theming)
	  - EgonTE (tk.Text) + is_marked() + get_pos() for editor integration
	  - data (dict-like) for persisting history between uses
	'''
	# ---- helpers: owner window, edit/clipboard, theme ----
	def make_owner_popup_window(title_text: str) -> tk.Toplevel:
		make_window_callable = getattr(app, 'make_pop_ups_window', None)
		if callable(make_window_callable):
			try:
				return make_window_callable(lambda: None, custom_title=title_text)
			except Exception:
				pass
		parent_widget = getattr(app, 'tk', None) or getattr(app, 'root', None)
		if not isinstance(parent_widget, tk.Misc):
			parent_widget = tk._get_default_root() or tk.Tk()
		popup_window = tk.Toplevel(parent_widget)
		popup_window.title(getattr(app, 'title_struct', '') + title_text)
		return popup_window

	def resolve_theme_background(widget: tk.Misc) -> str:
		try:
			return getattr(app, 'dynamic_bg', widget.cget('bg'))
		except Exception:
			return widget.cget('bg')

	def resolve_theme_foreground(default_text_color: str = 'black') -> str:
		try:
			return getattr(app, 'dynamic_text', default_text_color)
		except Exception:
			return default_text_color

	def resolve_theme_button_background(default_button_color: str = 'SystemButtonFace') -> str:
		try:
			return getattr(app, 'dynamic_button', default_button_color)
		except Exception:
			return default_button_color

	def get_editor_selection_text() -> str:
		try:
			if hasattr(app, 'is_marked') and app.is_marked():
				return app.EgonTE.get('sel.first', 'sel.last')
		except Exception:
			pass
		return ''

	def insert_text_into_editor(text_value: str) -> None:
		text_value = text_value or ''
		if not text_value:
			return
		try:
			if hasattr(app, 'get_pos'):
				app.EgonTE.insert(app.get_pos(), text_value)
			else:
				app.EgonTE.insert('insert', text_value)
		except Exception:
			pass

	def copy_text_to_clipboard(text_value: str) -> None:
		try:
			popup_root.clipboard_clear()
			popup_root.clipboard_append(text_value)
		except Exception:
			pass

	# ---- url and query utils ----
	url_scheme_regex = re.compile(r'^[a-z]+://', re.I)
	domain_regex = re.compile(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$')

	def looks_like_domain(text_value: str) -> bool:
		return bool(domain_regex.match(text_value.strip()))

	def is_probable_url(text_value: str) -> bool:
		text_value = (text_value or '').strip()
		if not text_value:
			return False
		if url_scheme_regex.match(text_value):
			return True
		return looks_like_domain(text_value) or text_value.lower().startswith('www.')

	def normalize_url(text_value: str) -> str:
		text_value = (text_value or '').strip()
		if not text_value:
			return text_value
		# bare domain / www -> add https://
		if looks_like_domain(text_value) or text_value.lower().startswith('www.'):
			if not url_scheme_regex.match(text_value):
				text_value = 'https://' + text_value
		# fallback: ensure scheme
		if not url_scheme_regex.match(text_value):
			text_value = 'https://' + text_value
		return text_value

	search_engines_map = {
		'Google': 'https://www.google.com/search?q={}',
		'DuckDuckGo': 'https://duckduckgo.com/?q={}',
		'Bing': 'https://www.bing.com/search?q={}',
		'Brave': 'https://search.brave.com/search?q={}',
		'Startpage': 'https://www.startpage.com/do/search?q={}',
	}

	# Custom engines storage helpers (persisted)
	def _get_custom_engines() -> dict[str, str]:
		try:
			store = getattr(app, 'data', None)
			if isinstance(store, dict):
				ce = store.get('web_tools_custom_engines', {})
				return dict(ce) if isinstance(ce, dict) else {}
		except Exception:
			pass
		return {}

	def _set_custom_engines(engines: dict[str, str]) -> None:
		try:
			store = getattr(app, 'data', None)
			if isinstance(store, dict):
				store['web_tools_custom_engines'] = dict(engines)
		except Exception:
			pass

	def _get_all_engines() -> dict[str, str]:
		engines = dict(search_engines_map)
		engines.update(_get_custom_engines())
		return engines

	# Bangs map for engine-aware features (extendable)
	bangs_map = {
		'!g': 'Google',
		'!google': 'Google',
		'!d': 'DuckDuckGo',
		'!ddg': 'DuckDuckGo',
		'!b': 'Bing',
		'!bing': 'Bing',
		'!br': 'Brave',
		'!brave': 'Brave',
		'!s': 'Startpage',
		'!sp': 'Startpage',
		'!startpage': 'Startpage',
	}

	def _try_parse_bang(query_text: str, engines: dict[str, str]) -> tuple[str | None, str]:
		"""
		If query starts with a bang like '!g', switch engine accordingly and strip the bang.
		Also supports '!enginename' where enginename matches lowercased engine key without spaces.
		Returns (engine_name_or_None, stripped_query)
		"""
		q = (query_text or '').lstrip()
		if not q.startswith('!'):
			return None, query_text
		first = q.split(None, 1)
		token = first[0]  # e.g. !g, !google, !my
		rest = q[len(token):].lstrip()
		# direct bang alias
		eng = bangs_map.get(token.lower())
		if eng and eng in engines:
			return eng, rest or ''
		# match against engine names normalized
		norm = token[1:].lower()
		for name in engines.keys():
			if norm == name.lower().replace(' ', ''):
				return name, rest or ''
		return None, query_text

	def _apply_engine_operators(engine_name: str, query_text: str) -> str:
		"""
		Minimal normalization layer for common operators across engines.
		Current engines accept site:, filetype:, -term, "exact phrase" as-is, so we mostly pass-through.
		This hook can be extended per-engine if needed.
		"""
		# Example future translations per engine can go here.
		return query_text

	def build_search_url(engine_name: str, query_text: str, safe_search: bool) -> str:
		engines = _get_all_engines()
		# Engine-aware: allow bangs to override engine
		bang_engine, stripped = _try_parse_bang(query_text, engines)
		if bang_engine:
			engine_name = bang_engine
			query_text = stripped
		# Apply per-engine operator normalization (currently passthrough)
		query_text = _apply_engine_operators(engine_name, query_text)

		# Template resolution: supports {q} or {} as placeholder
		template = engines.get(engine_name, search_engines_map['Google'])
		encoded = quote_plus(query_text)
		if '{q}' in template:
			final_url = template.replace('{q}', encoded)
		else:
			# backward compatibility for {}-style
			try:
				final_url = template.format(encoded)
			except Exception:
				final_url = template + encoded  # last resort

		# Safe search toggles
		if engine_name == 'Google' and safe_search:
			return final_url + '&safe=active'
		if engine_name == 'Bing' and safe_search:
			return final_url + '&adlt=strict'
		if engine_name == 'DuckDuckGo' and safe_search:
			return final_url + '&kp=1'
		# others: leave as-is
		return final_url

	# ---- browser helpers (detection + custom command) ----
	def _detect_browsers() -> list[str]:
		"""
		Probe a small set of known names; include only those resolvable by webbrowser.get.
		Always include 'default' and 'Custom…' entry.
		"""
		names = ['default']
		candidates = ['firefox', 'chrome', 'edge', 'opera', 'brave']
		for n in candidates:
			try:
				webbrowser.get(n)  # raises if not available
				names.append(n)
			except Exception:
				continue
		names.append('Custom…')
		return names

	def _get_custom_browser_cmd() -> str:
		try:
			ds = getattr(app, 'data', None)
			if isinstance(ds, dict):
				return str(ds.get('web_tools_custom_browser_cmd', '') or '')
		except Exception:
			pass
		return ''

	def _set_custom_browser_cmd(cmd_tpl: str) -> None:
		try:
			ds = getattr(app, 'data', None)
			if isinstance(ds, dict):
				ds['web_tools_custom_browser_cmd'] = cmd_tpl
		except Exception:
			pass

	def _prompt_custom_browser():
		dlg = tk.Toplevel(popup_root)
		dlg.title('Custom browser command')
		tk.Label(dlg, text='Command template (use {url} placeholder):').grid(row=0, column=0, padx=8, pady=(8, 4), sticky='w')
		var = tk.StringVar(value=_get_custom_browser_cmd() or '')
		ent = tk.Entry(dlg, textvariable=var, width=54)
		ent.grid(row=1, column=0, padx=8, sticky='we')
		info = tk.Label(dlg, text='Examples:\n- "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe" {url}\n- /usr/bin/brave-browser {url}', fg='#666', justify='left')
		info.grid(row=2, column=0, padx=8, pady=(4, 6), sticky='w')
		btns = tk.Frame(dlg)
		btns.grid(row=3, column=0, padx=8, pady=(0, 8), sticky='e')
		def _save():
			tpl = var.get().strip()
			if '{url}' not in tpl:
				messagebox.showerror(getattr(app, 'title_struct', '') + 'error', 'Template must contain {url}.')
				return
			_set_custom_browser_cmd(tpl)
			# Keep UI selection on "Custom…" entry
			browser_string_var.set('Custom…')
			dlg.destroy()
		tk.Button(btns, text='Save', command=_save).pack(side='left', padx=(0, 4))
		tk.Button(btns, text='Cancel', command=dlg.destroy).pack(side='left')
		dlg.grid_columnconfigure(0, weight=1)
		try:
			dlg.transient(popup_root)
		except Exception:
			pass

	def _open_with_custom_command(url: str) -> None:
		tpl = _get_custom_browser_cmd()
		if not tpl or '{url}' not in tpl:
			_prompt_custom_browser()
			tpl = _get_custom_browser_cmd()
			if not tpl:
				return
		cmd = tpl.replace('{url}', url)
		try:
			if os.name == 'nt':
				subprocess.Popen(cmd, shell=True)
			else:
				import shlex
				subprocess.Popen(shlex.split(cmd))
		except Exception as e:
			messagebox.showerror(getattr(app, 'title_struct', '') + 'error', f'Failed to run custom command.\n{e}')

	# ---- QR helpers (local generation with fallback) ----
	def _have_qrcode():
		try:
			import qrcode  # noqa: F401
			return True
		except Exception:
			return False

	def _open_path_with_system(path_text: str) -> None:
		try:
			if os.name == 'nt':
				os.startfile(path_text)  # type: ignore[attr-defined]
			elif 'darwin' in os.popen('uname').read().lower():
				subprocess.Popen(['open', path_text])
			else:
				subprocess.Popen(['xdg-open', path_text])
		except Exception:
			try:
				webbrowser.open('file://' + path_text)
			except Exception:
				pass

	# persisted QR size (pixels), defaults to 280
	def _get_qr_size() -> int:
		try:
			ds = getattr(app, 'data', None)
			if isinstance(ds, dict):
				v = int(ds.get('web_tools_qr_size', 280))
				return max(120, min(640, v))
		except Exception:
			pass
		return 280

	def _set_qr_size(px: int) -> None:
		try:
			ds = getattr(app, 'data', None)
			if isinstance(ds, dict):
				ds['web_tools_qr_size'] = int(px)
		except Exception:
			pass

	# ---- async title preview ----
	def fetch_title_preview_async(target_url: str) -> None:
		if not requests:
			title_preview_string_var.set('')
			return

		def request_worker():
			page_title_text = ''
			try:
				http_response = requests.get(target_url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
				if 200 <= http_response.status_code < 400:
					html_text = http_response.text or ''
					title_match = re.search(r'<title[^>]*>(.*?)</title>', html_text, re.I | re.S)
					if title_match:
						raw_title = title_match.group(1)
						page_title_text = re.sub(r'\s+', ' ', raw_title).strip()
			except Exception:
				page_title_text = ''
			finally:
				try:
					popup_root.after(0, lambda: title_preview_string_var.set(page_title_text))
				except Exception:
					pass

		title_thread = threading.Thread(target=request_worker, daemon=True)
		title_thread.start()

	def save_preferences() -> None:
		try:
			data_store = getattr(app, 'data', None)
			if isinstance(data_store, dict):
				data_store['web_tools_engine'] = search_engine_string_var.get()
				data_store['web_tools_safe'] = bool(safe_search_boolean_var.get())
				# Normalize 'Custom…' to 'custom' in stored prefs
				browser_pref = browser_string_var.get()
				data_store['web_tools_browser'] = 'custom' if browser_pref == 'Custom…' else browser_pref
				data_store['web_tools_tab'] = tab_mode_string_var.get()
		except Exception:
			pass

	def load_preferences() -> dict[str, Any]:
		try:
			data_store = getattr(app, 'data', None)
			if isinstance(data_store, dict):
				return {
					'engine': data_store.get('web_tools_engine', 'Google'),
					'safe': data_store.get('web_tools_safe', True),
					'browser': data_store.get('web_tools_browser', 'default'),
					'tab': data_store.get('web_tools_tab', 'new'),
				}
		except Exception:
			pass
		return {}

	# ===== Enhanced history storage (entries with timestamp/pin) =====
	# entry = {'value': str, 'ts': int, 'pinned': bool}
	def _now_ts() -> int:
		try:
			import time
			return int(time.time())
		except Exception:
			return 0

	def _normalize_hist_value(s: str) -> str:
		return (s or '').strip()

	def _domain_of(s: str) -> str:
		try:
			from urllib.parse import urlparse
			u = urlparse(s if '://' in s else f'https://{s}')
			return (u.hostname or '').lower() or ''
		except Exception:
			return ''

	def _load_raw_history() -> Any:
		try:
			ds = getattr(app, 'data', None)
			if isinstance(ds, dict):
				return ds.get('web_tools_history', [])
		except Exception:
			return []
		return []

	def _save_raw_history(obj: Any) -> None:
		try:
			ds = getattr(app, 'data', None)
			if isinstance(ds, dict):
				ds['web_tools_history'] = obj
		except Exception:
			pass

	def get_history_entries() -> list[dict]:
		raw = _load_raw_history()
		entries: list[dict] = []
		try:
			if raw and isinstance(raw, list):
				if raw and isinstance(raw[0], str):
					# migrate from plain string list
					for v in raw:
						val = _normalize_hist_value(str(v))
						if val:
							entries.append({'value': val, 'ts': _now_ts(), 'pinned': False})
					_save_raw_history(entries)
				else:
					# already new format; filter minimal validity
					for item in raw:
						if isinstance(item, dict) and 'value' in item:
							val = _normalize_hist_value(str(item.get('value', '')))
							if val:
								ts = int(item.get('ts', _now_ts()))
								pin = bool(item.get('pinned', False))
								entries.append({'value': val, 'ts': ts, 'pinned': pin})
		except Exception:
			entries = []
		return entries

	def set_history_entries(entries: list[dict]) -> None:
		# keep max 300 items, pinned first then recency
		try:
			entries = [e for e in entries if isinstance(e, dict) and _normalize_hist_value(e.get('value', ''))]
			entries.sort(key=lambda e: (not bool(e.get('pinned', False)), -int(e.get('ts', 0))))
			_save_raw_history(entries[:300])
		except Exception:
			pass

	def add_item_to_history(value_text: str) -> None:
		val = _normalize_hist_value(value_text)
		if not val:
			return
		entries = get_history_entries()
		# dedup case-insensitively
		lo = val.lower()
		entries = [e for e in entries if str(e.get('value', '')).lower() != lo]
		entries.insert(0, {'value': val, 'ts': _now_ts(), 'pinned': False})
		set_history_entries(entries)
		refresh_history_listbox()

	# Back-compat helpers used elsewhere
	def get_history_list() -> list[str]:
		return [e.get('value', '') for e in get_history_entries()]

	def set_history_list(items_list: list[str]) -> None:
		entries = []
		now = _now_ts()
		for v in items_list:
			val = _normalize_hist_value(v)
			if val:
				entries.append({'value': val, 'ts': now, 'pinned': False})
		set_history_entries(entries)

	# ---- browser openers ----
	def open_in_browser(target_url: str, *, browser_name: str, tab_mode: str) -> None:
		try:
			# Normalize "Custom…" selection and aliases
			name = (browser_name or '').strip()
			if name.lower().startswith('custom'):
				_open_with_custom_command(target_url)
				return
			if name in ('Custom…', 'Custom...'):
				_open_with_custom_command(target_url)
				return

			if name == 'default':
				if tab_mode == 'current':
					webbrowser.open(target_url)
				else:
					webbrowser.open_new_tab(target_url)
			else:
				browser_controller = webbrowser.get(name)
				if tab_mode == 'current':
					browser_controller.open(target_url)
				else:
					browser_controller.open_new_tab(target_url)
		except webbrowser.Error:
			messagebox.showerror(getattr(app, 'title_struct', '') + 'error', f'Browser "{browser_name}" was not found')
		except Exception as open_error_exception:
			messagebox.showerror(getattr(app, 'title_struct', '') + 'error', f'Failed to open.\n{open_error_exception}')

	# ---- UI build ----
	popup_root = make_owner_popup_window('Web tools')
	try:
		popup_root.attributes('-alpha', getattr(app, 'st_value', popup_root.attributes('-alpha')))
	except Exception:
		pass
	try:
		if getattr(app, 'limit_w_s', None) and app.limit_w_s.get():
			popup_root.resizable(False, False)
	except Exception:
		pass

	# overall layout weights
	try:
		popup_root.grid_columnconfigure(0, weight=1)
		popup_root.grid_rowconfigure(1, weight=1)
	except Exception:
		pass

	# title
	title_label_widget = tk.Label(
		popup_root,
		text='Web tools',
		font=getattr(app, 'titles_font', 'arial 12 underline'),
		fg=resolve_theme_foreground(),
		bg=resolve_theme_background(popup_root),
		anchor='w',
	)
	title_label_widget.grid(row=0, column=0, padx=8, pady=(6, 4), sticky='ew')

	# notebook with sub-topics
	notebook = ttk.Notebook(popup_root)
	notebook.grid(row=1, column=0, padx=8, pady=(0, 8), sticky='nsew')

	# tabs
	tab_search = ttk.Frame(notebook)
	tab_shorten = ttk.Frame(notebook)
	tab_qr = ttk.Frame(notebook)
	tab_history = ttk.Frame(notebook)
	notebook.add(tab_search, text='Search')
	notebook.add(tab_shorten, text='Shorten')
	notebook.add(tab_qr, text='QR')
	notebook.add(tab_history, text='History')

	for tab in (tab_search, tab_shorten, tab_qr, tab_history):
		try:
			tab.grid_columnconfigure(0, weight=0)
			tab.grid_columnconfigure(1, weight=1)
			tab.grid_columnconfigure(2, weight=0)
			tab.grid_columnconfigure(3, weight=0)
			tab.grid_rowconfigure(99, weight=1)
		except Exception:
			pass

	# ===== Search tab =====
	input_label_widget = tk.Label(
		tab_search,
		text='URL or search query:',
		fg=resolve_theme_foreground(),
		bg=resolve_theme_background(popup_root),
	)
	input_label_widget.grid(row=0, column=0, padx=4, pady=(6, 2), sticky='w')

	query_entry_string_var = tk.StringVar(value='')
	query_entry_widget = tk.Entry(tab_search, textvariable=query_entry_string_var, width=52, relief=tk.GROOVE)
	query_entry_widget.grid(row=0, column=1, columnspan=2, padx=6, pady=(6, 2), sticky='we')

	# helpers (Paste / From selection)
	input_helpers_frame = tk.Frame(tab_search, bg=resolve_theme_background(popup_root))
	input_helpers_frame.grid(row=0, column=3, padx=0, pady=(6, 2), sticky='e')
	paste_from_clipboard_button = tk.Button(
		input_helpers_frame,
		text='Paste',
		bd=1,
		bg=resolve_theme_button_background(),
		fg=resolve_theme_foreground(),
		command=lambda: query_entry_string_var.set(
			((popup_root.clipboard_get() if hasattr(popup_root, 'clipboard_get') else '') or '').strip()
		),
	)
	paste_from_clipboard_button.pack(side='left', padx=(0, 4))
	fill_from_selection_button = tk.Button(
		input_helpers_frame,
		text='From selection',
		bd=1,
		bg=resolve_theme_button_background(),
		fg=resolve_theme_foreground(),
		command=lambda: query_entry_string_var.set(get_editor_selection_text().strip() or query_entry_string_var.get()),
	)
	fill_from_selection_button.pack(side='left')

	# engine row
	search_engine_string_var = tk.StringVar(value='Google')
	safe_search_boolean_var = tk.BooleanVar(value=True)
	engine_label_widget = tk.Label(
		tab_search, text='Engine:', fg=resolve_theme_foreground(), bg=resolve_theme_background(popup_root)
	)
	engine_label_widget.grid(row=1, column=0, sticky='e', padx=4, pady=(6, 2))

	engine_combobox_widget = ttk.Combobox(
		tab_search,
		textvariable=search_engine_string_var,
		state='readonly',
		width=18,
		values=tuple(search_engines_map.keys()),
	)
	engine_combobox_widget.grid(row=1, column=1, sticky='w', pady=(6, 2))

	def _refresh_engine_combobox():
		try:
			all_names = tuple(_get_all_engines().keys())
			engine_combobox_widget.configure(values=all_names)
			# Ensure current value is valid, otherwise fall back to the first engine
			cur = search_engine_string_var.get()
			if cur not in all_names:
				search_engine_string_var.set(all_names[0] if all_names else 'Google')
		except Exception:
			pass

	# Refresh available engines right after creation (so custom engines appear immediately)
	_refresh_engine_combobox()

	# Manage Custom Engines (restored)
	def _open_manage_custom_engines():
		mgr = tk.Toplevel(popup_root)
		mgr.title('Manage search engines')
		try:
			mgr.transient(popup_root)
		except Exception:
			pass

		listbox = tk.Listbox(mgr, height=6, exportselection=False)
		scroll = ttk.Scrollbar(mgr, command=listbox.yview)
		listbox.config(yscrollcommand=scroll.set)
		name_var = tk.StringVar()
		url_var = tk.StringVar()
		name_entry = tk.Entry(mgr, textvariable=name_var, width=26)
		url_entry = tk.Entry(mgr, textvariable=url_var, width=48)
		info = tk.Label(mgr, text='Template must contain {q} (or {}), e.g. https://example.com/?s={q}', fg='#666')

		def load_selected(_e=None):
			sel = listbox.curselection()
			if not sel:
				return
			n = listbox.get(sel[0])
			ce = _get_custom_engines()
			name_var.set(n)
			url_var.set(ce.get(n, ''))

		def save_engine():
			n = (name_var.get() or '').strip()
			u = (url_var.get() or '').strip()
			if not n or not u:
				messagebox.showerror(getattr(app, 'title_struct', '') + 'error', 'Name and template are required.')
				return
			if '{q}' not in u and '{}' not in u:
				messagebox.showerror(getattr(app, 'title_struct', '') + 'error', 'Template must contain {q} or {} placeholder.')
				return
			ce = _get_custom_engines()
			ce[n] = u
			_set_custom_engines(ce)
			_refresh_list()
			_refresh_engine_combobox()

		def delete_engine():
			sel = listbox.curselection()
			if not sel:
				return
			n = listbox.get(sel[0])
			ce = _get_custom_engines()
			if n in ce:
				del ce[n]
				_set_custom_engines(ce)
				_refresh_list()
				_refresh_engine_combobox()

		def _refresh_list():
			listbox.delete(0, tk.END)
			for n in sorted(_get_custom_engines().keys(), key=str.lower):
				listbox.insert(tk.END, n)

		# layout
		tk.Label(mgr, text='Custom engines').grid(row=0, column=0, sticky='w', padx=8, pady=(8, 2))
		listbox.grid(row=1, column=0, rowspan=4, padx=(8, 0), pady=4, sticky='ns')
		scroll.grid(row=1, column=1, rowspan=4, sticky='ns', pady=4, padx=(0, 8))
		tk.Label(mgr, text='Name:').grid(row=1, column=2, sticky='w', padx=6)
		name_entry.grid(row=1, column=3, sticky='we', padx=(0, 8))
		tk.Label(mgr, text='Template:').grid(row=2, column=2, sticky='w', padx=6)
		url_entry.grid(row=2, column=3, sticky='we', padx=(0, 8))
		info.grid(row=3, column=2, columnspan=2, sticky='w', padx=6, pady=(2, 6))
		btn_row = tk.Frame(mgr)
		btn_row.grid(row=4, column=2, columnspan=2, sticky='e', padx=6, pady=(0, 8))
		tk.Button(btn_row, text='Save', command=save_engine).pack(side='left', padx=4)
		tk.Button(btn_row, text='Delete', command=delete_engine).pack(side='left', padx=4)
		tk.Button(btn_row, text='Close', command=mgr.destroy).pack(side='left')
		for c in (3,):
			mgr.grid_columnconfigure(c, weight=1)
		_refresh_list()
		listbox.bind('<<ListboxSelect>>', load_selected)

	manage_engines_button = tk.Button(
		tab_search,
		text='Manage…',
		bd=1,
		bg=resolve_theme_button_background(),
		fg=resolve_theme_foreground(),
		command=_open_manage_custom_engines,
	)
	manage_engines_button.grid(row=1, column=1, sticky='e', padx=(0, 96), pady=(6, 2))

	safe_search_checkbutton = tk.Checkbutton(
		tab_search,
		text='Safe search',
		variable=safe_search_boolean_var,
		bg=resolve_theme_background(popup_root),
		fg=resolve_theme_foreground(),
	)
	safe_search_checkbutton.grid(row=1, column=2, sticky='w', pady=(6, 2))

	open_action_button = tk.Button(
		tab_search, text='Open', bd=1, bg=resolve_theme_button_background(), fg=resolve_theme_foreground()
	)
	open_action_button.grid(row=1, column=3, padx=6, pady=(6, 2), sticky='e')

	# title preview
	title_preview_string_var = tk.StringVar(value='')
	title_preview_label_widget = tk.Label(
		tab_search,
		textvariable=title_preview_string_var,
		fg='#666',
		bg=resolve_theme_background(popup_root),
		wraplength=520,
		justify='left',
	)
	title_preview_label_widget.grid(row=2, column=0, columnspan=4, padx=4, pady=(8, 4), sticky='we')

	# Open options (moved from Browser tab)
	open_options_frame = ttk.LabelFrame(tab_search, text='Open options')
	open_options_frame.grid(row=3, column=0, columnspan=4, padx=4, pady=(4, 6), sticky='ew')
	try:
		open_options_frame.grid_columnconfigure(0, weight=0)
		open_options_frame.grid_columnconfigure(1, weight=1)
		open_options_frame.grid_columnconfigure(2, weight=0)
		open_options_frame.grid_columnconfigure(3, weight=0)
	except Exception:
		pass

	tk.Label(open_options_frame, text='Browser:', bg=resolve_theme_background(popup_root),
			 fg=resolve_theme_foreground()).grid(row=0, column=0, sticky='e', padx=4, pady=(6, 2))

	browser_string_var = tk.StringVar(value='default')
	browser_combobox_widget = ttk.Combobox(
		open_options_frame, textvariable=browser_string_var, state='readonly', width=18, values=tuple(_detect_browsers())
	)
	browser_combobox_widget.grid(row=0, column=1, sticky='w', pady=(6, 2))

	def _on_browser_selected(_e=None):
		if browser_string_var.get() == 'Custom…':
			_prompt_custom_browser()

	browser_combobox_widget.bind('<<ComboboxSelected>>', _on_browser_selected)
	# Ensure a valid initial selection if stored value is no longer available
	try:
		if browser_string_var.get() not in browser_combobox_widget.cget('values'):
			browser_string_var.set('default')
	except Exception:
		pass

	tk.Label(open_options_frame, text='Tab:', bg=resolve_theme_background(popup_root),
			 fg=resolve_theme_foreground()).grid(row=0, column=2, sticky='e', padx=(12, 4), pady=(6, 2))

	tab_mode_string_var = tk.StringVar(value='new')
	tab_mode_combobox_widget = ttk.Combobox(
		open_options_frame, textvariable=tab_mode_string_var, state='readonly', width=12, values=('current', 'new')
	)
	tab_mode_combobox_widget.grid(row=0, column=3, sticky='w', padx=6, pady=(6, 2))

	# ===== Shorten & QR tab =====
	shorten_label_widget = tk.Label(
		tab_shorten, text='Shorten:', fg=resolve_theme_foreground(), bg=resolve_theme_background(popup_root)
	)
	shorten_label_widget.grid(row=0, column=0, sticky='e', padx=4, pady=(10, 2))

	# Shortener provider selector
	shortener_provider_var = tk.StringVar(value='TinyURL')
	shortener_provider_combo = ttk.Combobox(
		tab_shorten,
		textvariable=shortener_provider_var,
		state='readonly',
		width=16,
		values=('TinyURL', 'is.gd', 'Bitly'),
	)
	shortener_provider_combo.grid(row=0, column=1, sticky='w', pady=(10, 2))

	# Token management (for Bitly)
	def _get_bitly_token() -> str:
		try:
			ds = getattr(app, 'data', None)
			if isinstance(ds, dict):
				return str(ds.get('web_tools_bitly_token', '') or '')
		except Exception:
			pass
		return ''

	def _set_bitly_token(t: str) -> None:
		try:
			ds = getattr(app, 'data', None)
			if isinstance(ds, dict):
				ds['web_tools_bitly_token'] = t
		except Exception:
			pass

	def _prompt_bitly_token():
		dlg = tk.Toplevel(popup_root)
		dlg.title('Set Bitly token')
		tk.Label(dlg, text='Enter Bitly Generic Access Token:').grid(row=0, column=0, padx=8, pady=(8, 4), sticky='w')
		var = tk.StringVar(value=_get_bitly_token())
		ent = tk.Entry(dlg, textvariable=var, width=48, show='*')
		ent.grid(row=1, column=0, padx=8, sticky='we')
		show = tk.BooleanVar(value=False)
		def _toggle():
			ent.config(show='' if show.get() else '*')
		tk.Checkbutton(dlg, text='Show', variable=show, command=_toggle).grid(row=1, column=1, padx=(0, 8), sticky='w')
		btns = tk.Frame(dlg)
		btns.grid(row=2, column=0, columnspan=2, padx=8, pady=(6, 8), sticky='e')
		def _save():
			_set_bitly_token(var.get().strip())
			dlg.destroy()
		tk.Button(btns, text='Save', command=_save).pack(side='left', padx=(0, 4))
		tk.Button(btns, text='Cancel', command=dlg.destroy).pack(side='left')
		try:
			dlg.transient(popup_root)
			dlg.grab_set()
		except Exception:
			pass

	shorten_action_button = tk.Button(
		tab_shorten, text='Shorten', bd=1, bg=resolve_theme_button_background(), fg=resolve_theme_foreground()
	)
	shorten_action_button.grid(row=0, column=2, sticky='w', pady=(10, 2), padx=(6, 0))

	expand_action_button = tk.Button(
		tab_shorten, text='Expand', bd=1, bg=resolve_theme_button_background(), fg=resolve_theme_foreground()
	)
	expand_action_button.grid(row=0, column=3, sticky='w', pady=(10, 2), padx=(6, 0))

	manage_token_button = tk.Button(
		tab_shorten, text='Token…', bd=1, bg=resolve_theme_button_background(), fg=resolve_theme_foreground(),
		command=_prompt_bitly_token
	)
	# Only visible when Bitly is selected
	def _update_token_button(*_):
		try:
			if shortener_provider_var.get() == 'Bitly':
				manage_token_button.grid(row=0, column=4, sticky='w', pady=(10, 2), padx=(6, 0))
			else:
				manage_token_button.grid_forget()
		except Exception:
			pass
	shortener_provider_combo.bind('<<ComboboxSelected>>', _update_token_button)
	_update_token_button()

	shortened_url_string_var = tk.StringVar(value='')
	shortened_url_output_entry = tk.Entry(
		tab_shorten, textvariable=shortened_url_string_var, width=52, relief=tk.GROOVE, state='readonly'
	)
	shortened_url_output_entry.grid(row=1, column=0, columnspan=3, padx=4, pady=(4, 2), sticky='we')

	shortener_utils_frame = tk.Frame(tab_shorten, bg=resolve_theme_background(popup_root))
	shortener_utils_frame.grid(row=1, column=3, sticky='w', pady=(4, 2))
	copy_shortened_button = tk.Button(
		shortener_utils_frame, text='Copy', bd=1, bg=resolve_theme_button_background(), fg=resolve_theme_foreground()
	)
	insert_shortened_button = tk.Button(
		shortener_utils_frame, text='Insert', bd=1, bg=resolve_theme_button_background(), fg=resolve_theme_foreground()
	)
	copy_shortened_button.pack(side='left', padx=(0, 4))
	insert_shortened_button.pack(side='left', padx=(0, 4))

	# The inline QR UI and helpers are defined once in the dedicated "QR" tab below.
	# They were previously duplicated here and referenced a non-existent `qr_panel`.
	# The QR code features now live exclusively under the "QR" tab.
	# ... existing code ...
	# ===== QR tab (dedicated) =====
	qr_helper_row = tk.Frame(tab_qr, bg=resolve_theme_background(popup_root))
	qr_helper_row.grid(row=0, column=0, columnspan=4, padx=4, pady=(8, 4), sticky='ew')

	tk.Label(qr_helper_row, text='Make QR for:', bg=resolve_theme_background(popup_root),
			 fg=resolve_theme_foreground()).pack(side='left', padx=(0, 6))
	show_qr_button = tk.Button(
		qr_helper_row, text='Open QR in browser', bd=1, bg=resolve_theme_button_background(),
		fg=resolve_theme_foreground()
	)
	show_qr_button.pack(side='left')

	def _open_qr_menu(event=None):
		m = tk.Menu(show_qr_button, tearoff=False)
		size_var = tk.IntVar(value=_get_qr_size())
		for px in (180, 280, 360, 480):
			m.add_radiobutton(label=f'{px}px', value=px, variable=size_var, command=lambda v=px: _set_qr_size(v))
		if _have_qrcode():
			m.add_separator()
			m.add_command(label='Use local generator (qrcode)', state='disabled')
		try:
			if event is not None:
				m.tk_popup(event.x_root, event.y_root)
			else:
				x = show_qr_button.winfo_rootx()
				y = show_qr_button.winfo_rooty() + show_qr_button.winfo_height()
				m.tk_popup(x, y)
		finally:
			m.grab_release()

	show_qr_button.bind('<Button-3>', _open_qr_menu)
	show_qr_button.bind('<Button-2>', _open_qr_menu)

	# Inline QR Panel
	qr_panel = ttk.LabelFrame(tab_qr, text='QR code')
	qr_panel.grid(row=1, column=0, columnspan=4, padx=6, pady=(6, 4), sticky='ew')

	qr_enabled = bool(_QR_AVAILABLE and _PIL_AVAILABLE)
	qr_canvas = tk.Label(qr_panel)
	qr_canvas.grid(row=0, column=0, rowspan=3, padx=6, pady=6, sticky='w')

	qr_size_var = tk.IntVar(value=_get_qr_size())
	qr_fg_var = tk.StringVar(value='#000000')
	qr_bg_var = tk.StringVar(value='#ffffff')
	qr_ecc_var = tk.StringVar(value='M')  # L, M, Q, H

	tk.Label(qr_panel, text='Size:').grid(row=0, column=1, sticky='e')
	qr_size_spin = tk.Spinbox(qr_panel, from_=120, to=640, increment=20, width=6, textvariable=qr_size_var)
	qr_size_spin.grid(row=0, column=2, sticky='w', padx=(4, 10))

	tk.Label(qr_panel, text='FG:').grid(row=0, column=3, sticky='e')
	qr_fg_entry = tk.Entry(qr_panel, width=10, textvariable=qr_fg_var)
	qr_fg_entry.grid(row=0, column=4, sticky='w', padx=(4, 10))

	tk.Label(qr_panel, text='BG:').grid(row=0, column=5, sticky='e')
	qr_bg_entry = tk.Entry(qr_panel, width=10, textvariable=qr_bg_var)
	qr_bg_entry.grid(row=0, column=6, sticky='w', padx=(4, 10))

	tk.Label(qr_panel, text='ECC:').grid(row=0, column=7, sticky='e')
	qr_ecc_combo = ttk.Combobox(qr_panel, width=3, state='readonly', values=('L', 'M', 'Q', 'H'), textvariable=qr_ecc_var)
	qr_ecc_combo.grid(row=0, column=8, sticky='w')

	qr_status_var = tk.StringVar(value='' if qr_enabled else 'Inline QR disabled (install "qrcode" and "Pillow").')
	qr_status = tk.Label(qr_panel, textvariable=qr_status_var, fg='#666')
	qr_status.grid(row=1, column=1, columnspan=8, sticky='w', padx=(0, 6))

	qr_buttons_frame = tk.Frame(qr_panel)
	qr_buttons_frame.grid(row=2, column=1, columnspan=8, sticky='w', pady=(4, 6))

	qr_img_cache = {'photo': None}  # keep reference to avoid GC

	def _ecc_map(code: str):
		try:
			import qrcode.constants as C
			return {
				'L': C.ERROR_CORRECT_L,
				'M': C.ERROR_CORRECT_M,
				'Q': C.ERROR_CORRECT_Q,
				'H': C.ERROR_CORRECT_H,
			}.get(code.upper(), C.ERROR_CORRECT_M)
		except Exception:
			return None

	def _qr_text_source() -> str:
		# Prefer shortened URL if present; otherwise current query
		val = shortened_url_string_var.get().strip() or query_entry_string_var.get().strip()
		return normalize_url(val) if val else ''

	def _render_qr_inline():
		if not qr_enabled:
			return
		target = _qr_text_source()
		if not target:
			qr_status_var.set('Enter or shorten a URL first.')
			return
		try:
			size = max(120, min(640, int(qr_size_var.get() or 280)))
		except Exception:
			size = 280
			qr_size_var.set(size)
		_set_qr_size(size)  # persist shared size preference
		try:
			ecc = _ecc_map(qr_ecc_var.get() or 'M')
		except Exception:
			ecc = _ecc_map('M')
		fg, bg = (qr_fg_var.get() or '#000'), (qr_bg_var.get() or '#fff')
		try:
			qr_obj = qrcode.QRCode(
				version=None,
				error_correction=ecc,
				box_size=max(2, size // 50),
				border=2,
			)
			qr_obj.add_data(target)
			qr_obj.make(fit=True)
			img = qr_obj.make_image(fill_color=fg, back_color=bg).convert('RGB')
			# Pillow compatibility for older versions
			try:
				resample_method = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
			except Exception:
				resample_method = Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.BICUBIC
			img = img.resize((size, size), resample_method)
			photo = ImageTk.PhotoImage(img)
			qr_img_cache['photo'] = photo
			qr_canvas.configure(image=photo)
			qr_status_var.set('Ready.')
		except Exception as e:
			qr_status_var.set(f'QR error: {e}')

	def _save_qr_png():
		if not qr_enabled:
			return
		target = _qr_text_source()
		if not target:
			qr_status_var.set('Nothing to save.')
			return
		try:
			from tkinter import filedialog
			path = filedialog.asksaveasfilename(
				parent=popup_root,
				defaultextension='.png',
				filetypes=(('PNG Image', '*.png'),),
				title='Save QR code as PNG'
			)
			if not path:
				return
			ecc = _ecc_map(qr_ecc_var.get() or 'M')
			size = max(120, min(640, int(qr_size_var.get() or 280)))
			qr_obj = qrcode.QRCode(error_correction=ecc, box_size=max(2, size // 50), border=2)
			qr_obj.add_data(target)
			qr_obj.make(fit=True)
			img = qr_obj.make_image(fill_color=qr_fg_var.get() or '#000', back_color=qr_bg_var.get() or '#fff').convert('RGB')
			img.save(path, format='PNG')
			qr_status_var.set(f'Saved: {os.path.basename(path)}')
		except Exception as e:
			qr_status_var.set(f'Save failed: {e}')

	def _copy_qr_image():
		# Copy as PNG bytes to clipboard is platform-specific; provide a fallback note.
		try:
			qr_status_var.set('Copying QR as image is not supported on all platforms.')
		except Exception:
			pass

	tk.Button(qr_buttons_frame, text='Generate', command=_render_qr_inline, bd=1,
			  bg=resolve_theme_button_background(), fg=resolve_theme_foreground()).pack(side='left', padx=(0, 4))
	tk.Button(qr_buttons_frame, text='Save PNG', command=_save_qr_png, bd=1,
			  bg=resolve_theme_button_background(), fg=resolve_theme_foreground()).pack(side='left', padx=(0, 4))
	tk.Button(qr_buttons_frame, text='Copy image', command=_copy_qr_image, bd=1,
			  bg=resolve_theme_button_background(), fg=resolve_theme_foreground()).pack(side='left', padx=(0, 4))
	tk.Button(qr_buttons_frame, text='Copy URL', command=lambda: copy_text_to_clipboard(_qr_text_source()), bd=1,
			  bg=resolve_theme_button_background(), fg=resolve_theme_foreground()).pack(side='left', padx=(0, 4))

	# Disable inline QR panel if libs are missing (only here, after the panel is created)
	if not qr_enabled:
		try:
			for child in qr_panel.winfo_children():
				if child not in (qr_status,):
					child.configure(state='disabled')
		except Exception:
			pass


	# Apply saved preferences now that widgets exist
	try:
		prefs_dict = load_preferences()
		_refresh_engine_combobox()
		all_engines_now = _get_all_engines()
		if prefs_dict.get('engine') in all_engines_now:
			search_engine_string_var.set(prefs_dict['engine'])
		if isinstance(prefs_dict.get('safe'), bool):
			safe_search_boolean_var.set(bool(prefs_dict['safe']))
		# Browser preference handling with dynamic list and custom mapping
		detected = tuple(_detect_browsers())
		stored_browser = prefs_dict.get('browser')
		if stored_browser == 'custom' and 'Custom…' in detected:
			browser_string_var.set('Custom…')
		elif stored_browser in detected:
			browser_string_var.set(stored_browser)
		else:
			browser_string_var.set('default')
		if prefs_dict.get('tab') in ('current', 'new'):
			tab_mode_string_var.set(prefs_dict['tab'])
	except Exception:
		pass

	# ===== History tab =====
	history_frame = tk.Frame(tab_history, bg=resolve_theme_background(popup_root))
	history_frame.grid(row=0, column=0, columnspan=4, padx=4, pady=(8, 4), sticky='nsew')
	try:
		tab_history.grid_rowconfigure(0, weight=1)
		tab_history.grid_columnconfigure(0, weight=1)
	except Exception:
		pass

	history_title_label = tk.Label(
		history_frame, text='History', fg=resolve_theme_foreground(), bg=resolve_theme_background(popup_root)
	)
	history_title_label.pack(anchor='w')


	# ===== Browser tab =====
	# (Removed – browser controls are now within the Search tab's "Open options" frame)
	try:
		tab_history.grid_rowconfigure(0, weight=1)
		tab_history.grid_columnconfigure(0, weight=1)
	except Exception:
		pass

	history_title_label = tk.Label(
		history_frame, text='History', fg=resolve_theme_foreground(), bg=resolve_theme_background(popup_root)
	)
	history_title_label.pack(anchor='w')

	# Toolbar (filter + actions)
	toolbar_row = tk.Frame(history_frame, bg=resolve_theme_background(popup_root))
	toolbar_row.pack(fill='x', padx=0, pady=(2, 4))

	filter_var = tk.StringVar(value='')
	tk.Label(toolbar_row, text='Filter:', fg=resolve_theme_foreground(), bg=resolve_theme_background(popup_root)).pack(side='left', padx=(0, 4))
	filter_entry = tk.Entry(toolbar_row, textvariable=filter_var, width=28, relief=tk.GROOVE)
	filter_entry.pack(side='left', padx=(0, 8))

	purge_days_var = tk.StringVar(value='90')
	tk.Label(toolbar_row, text='Purge > days:', fg=resolve_theme_foreground(), bg=resolve_theme_background(popup_root)).pack(side='left', padx=(8, 4))
	purge_days_entry = tk.Entry(toolbar_row, textvariable=purge_days_var, width=5, relief=tk.GROOVE)
	purge_days_entry.pack(side='left')

	export_button = tk.Button(toolbar_row, text='Export…', bd=1, bg=resolve_theme_button_background(), fg=resolve_theme_foreground())
	import_button = tk.Button(toolbar_row, text='Import…', bd=1, bg=resolve_theme_button_background(), fg=resolve_theme_foreground())
	export_button.pack(side='right', padx=(4, 0))
	import_button.pack(side='right')

	history_toolbar_frame = tk.Frame(history_frame, bg=resolve_theme_background(popup_root))
	history_toolbar_frame.pack(fill='x', padx=0, pady=(0, 2))
	clear_history_button = tk.Button(
		history_toolbar_frame, text='Clear history', bd=1, bg=resolve_theme_button_background(), fg=resolve_theme_foreground()
	)
	clear_selected_button = tk.Button(
		history_toolbar_frame, text='Delete selected', bd=1, bg=resolve_theme_button_background(), fg=resolve_theme_foreground()
	)
	pin_toggle_button = tk.Button(
		history_toolbar_frame, text='Pin/Unpin', bd=1, bg=resolve_theme_button_background(), fg=resolve_theme_foreground()
	)
	purge_button = tk.Button(
		history_toolbar_frame, text='Purge', bd=1, bg=resolve_theme_button_background(), fg=resolve_theme_foreground()
	)
	clear_history_button.pack(side='right', padx=(4, 0))
	clear_selected_button.pack(side='right', padx=(4, 0))
	purge_button.pack(side='right', padx=(4, 0))
	pin_toggle_button.pack(side='right', padx=(4, 0))

	# List
	history_listbox = tk.Listbox(history_frame, height=10)
	history_scrollbar = ttk.Scrollbar(history_frame, command=history_listbox.yview)
	history_listbox.config(yscrollcommand=history_scrollbar.set)
	history_listbox.pack(side='left', fill='both', expand=True)
	history_scrollbar.pack(side='right', fill='y')

	# In-memory view for mapping listbox -> entries
	_history_view: list[dict] = []

	def _format_history_entry(entry: dict) -> str:
		# [*] 2025-09-15 example.com - raw text
		val = str(entry.get('value', ''))
		pin = '★ ' if bool(entry.get('pinned', False)) else '  '
		try:
			import datetime as _dt
			d = _dt.datetime.utcfromtimestamp(int(entry.get('ts', 0)) or 0)
			iso = d.strftime('%Y-%m-%d')
		except Exception:
			iso = ''
		dom = _domain_of(val)
		prefix = f"{pin}{iso} {dom}" if dom else f"{pin}{iso}"
		prefix = prefix.strip()
		return f"{prefix} - {val}" if prefix else val

	def refresh_history_listbox():
		try:
			flt = (filter_var.get() or '').strip().lower()
		except Exception:
			flt = ''
		entries = get_history_entries()
		# sort pinned first, then newest
		try:
			entries.sort(key=lambda e: (not bool(e.get('pinned', False)), -int(e.get('ts', 0))))
		except Exception:
			pass
		# filter by substring over value/domain
		def _match(e: dict) -> bool:
			if not flt:
				return True
			val = str(e.get('value', ''))
			if flt in val.lower():
				return True
			dom = _domain_of(val)
			return bool(dom and flt in dom)
		view = [e for e in entries if _match(e)]
		_history_view.clear()
		_history_view.extend(view)
		history_listbox.delete(0, tk.END)
		for e in view:
			try:
				history_listbox.insert(tk.END, _format_history_entry(e))
			except Exception:
				history_listbox.insert(tk.END, str(e.get('value', '')))

	def delete_selected_history_item():
		sel = history_listbox.curselection()
		if not sel:
			return
		try:
			selected = _history_view[sel[0]]
		except Exception:
			return
		entries = get_history_entries()
		# Prefer exact match by (value, ts), fallback to value-only if needed
		val = str(selected.get('value', ''))
		ts = int(selected.get('ts', 0))
		pruned = []
		removed = False
		for e in entries:
			if not removed and str(e.get('value', '')) == val and int(e.get('ts', 0)) == ts:
				removed = True
				continue
			pruned.append(e)
		if not removed:
			pruned = [e for e in pruned if str(e.get('value', '')) != val]
		set_history_entries(pruned)
		refresh_history_listbox()

	def clear_all_history_items():
		set_history_entries([])
		refresh_history_listbox()

	def _toggle_pin_selected():
		sel = history_listbox.curselection()
		if not sel:
			return
		try:
			selected = _history_view[sel[0]]
		except Exception:
			return
		entries = get_history_entries()
		for e in entries:
			if e.get('ts') == selected.get('ts') and str(e.get('value', '')) == str(selected.get('value', '')):
				e['pinned'] = not bool(e.get('pinned', False))
				break
		set_history_entries(entries)
		refresh_history_listbox()

	def _purge_older_than_days():
		try:
			days = int((purge_days_var.get() or '0').strip())
		except Exception:
			days = 0
		if days <= 0:
			return
		try:
			import time
			cut = int(time.time()) - days * 86400
		except Exception:
			cut = 0
		entries = get_history_entries()
		# keep pinned regardless of age
		entries = [e for e in entries if bool(e.get('pinned', False)) or int(e.get('ts', 0)) >= cut]
		set_history_entries(entries)
		refresh_history_listbox()

	def _export_history():
		try:
			from tkinter import filedialog
			path = filedialog.asksaveasfilename(
				parent=popup_root,
				defaultextension='.json',
				filetypes=(('JSON', '*.json'),),
				title='Export history'
			)
			if not path:
				return
			import json
			with open(path, 'w', encoding='utf-8') as f:
				json.dump(get_history_entries(), f, ensure_ascii=False, indent=2)
			messagebox.showinfo(getattr(app, 'title_struct', '') + 'info', 'History exported.')
		except Exception as e:
			messagebox.showerror(getattr(app, 'title_struct', '') + 'error', f'Export failed.\n{e}')

	def _import_history():
		try:
			from tkinter import filedialog
			path = filedialog.askopenfilename(
				parent=popup_root,
				filetypes=(('JSON', '*.json'), ('All files', '*.*')),
				title='Import history'
			)
			if not path:
				return
			import json
			with open(path, 'r', encoding='utf-8') as f:
				data = json.load(f)
			# merge safely, dedup case-insensitively, prefer pinned/newer
			cur = get_history_entries()
			by_key: dict[str, dict] = {}
			for e in cur:
				key = str(e.get('value', '')).lower()
				by_key[key] = e
			if isinstance(data, list):
				for item in data:
					if isinstance(item, str):
						entry = {'value': _normalize_hist_value(item), 'ts': _now_ts(), 'pinned': False}
					elif isinstance(item, dict) and 'value' in item:
						entry = {'value': _normalize_hist_value(item.get('value', '')),
								 'ts': int(item.get('ts', _now_ts())),
								 'pinned': bool(item.get('pinned', False))}
					else:
						continue
					if not entry['value']:
						continue
					key = entry['value'].lower()
					if key not in by_key:
						by_key[key] = entry
					else:
						# merge: keep pinned or newer ts
						old = by_key[key]
						if entry['pinned'] and not old.get('pinned', False):
							by_key[key] = entry
						elif bool(entry['pinned']) == bool(old.get('pinned', False)) and entry['ts'] > int(old.get('ts', 0)):
							by_key[key] = entry
			set_history_entries(list(by_key.values()))
			refresh_history_listbox()
			messagebox.showinfo(getattr(app, 'title_struct', '') + 'info', 'History imported.')
		except Exception as e:
			messagebox.showerror(getattr(app, 'title_struct', '') + 'error', f'Import failed.\n{e}')

	# Wire history actions
	def on_history_activate(event=None):
		selected_indices = history_listbox.curselection()
		if not selected_indices:
			return
		try:
			selected_entry = _history_view[selected_indices[0]]
			selected_value = selected_entry.get('value', '')
		except Exception:
			selected_value = None
		if not selected_value:
			return
		query_entry_string_var.set(selected_value)
		try:
			query_entry_widget.icursor('end')
			query_entry_widget.focus_set()
		except Exception:
			pass

	# realtime filter
	def _on_filter_key(_e=None):
		refresh_history_listbox()

	filter_entry.bind('<KeyRelease>', _on_filter_key)

	# context menu
	def open_history_context_menu(event_obj):
		menu_widget = tk.Menu(history_listbox, tearoff=False)
		menu_widget.add_command(label='Use item', command=lambda: on_history_activate())
		menu_widget.add_command(label='Pin/Unpin', command=_toggle_pin_selected)
		menu_widget.add_separator()
		menu_widget.add_command(label='Delete selected', command=delete_selected_history_item)
		menu_widget.add_command(label='Clear all', command=clear_all_history_items)
		try:
			menu_widget.tk_popup(event_obj.x_root, event_obj.y_root)
		finally:
			menu_widget.grab_release()

	# wire buttons (history)
	clear_selected_button.configure(command=delete_selected_history_item)
	clear_history_button.configure(command=clear_all_history_items)
	pin_toggle_button.configure(command=_toggle_pin_selected)
	purge_button.configure(command=_purge_older_than_days)
	export_button.configure(command=_export_history)
	import_button.configure(command=_import_history)

	history_listbox.bind('<Double-1>', on_history_activate)
	history_listbox.bind('<Return>', on_history_activate)
	history_listbox.bind('<Button-3>', open_history_context_menu)
	history_listbox.bind('<Button-2>', open_history_context_menu)

	# initial fill
	refresh_history_listbox()

	# ---- actions ----
	def open_action():
		raw_query_text = query_entry_string_var.get().strip()
		if not raw_query_text:
			messagebox.showerror(getattr(app, 'title_struct', '') + 'error', 'Please enter a URL or a search query.')
			return
		if is_probable_url(raw_query_text):
			final_url = normalize_url(raw_query_text)
		else:
			# Use possibly custom engine and bang-aware routing
			final_url = build_search_url(search_engine_string_var.get(), raw_query_text, safe_search_boolean_var.get())
		add_item_to_history(raw_query_text)
		# preview title if URL
		try:
			title_preview_string_var.set('')
			if final_url.startswith('http'):
				fetch_title_preview_async(final_url)
		except Exception:
			pass
		open_in_browser(final_url, browser_name=browser_string_var.get(), tab_mode=tab_mode_string_var.get())

	def shorten_action():
		raw_input_text = query_entry_string_var.get().strip()
		if not raw_input_text:
			messagebox.showerror(getattr(app, 'title_struct', '') + 'error', 'Please enter a URL to shorten.')
			return
		normalized_url = normalize_url(raw_input_text)

		provider = shortener_provider_var.get()
		# Prefer pyshorteners when available; fall back to simple-request methods where possible
		shortened = None
		error_text = None

		def _tinyurl_pyshorteners(url: str):
			try:
				from pyshorteners import Shortener  # optional
			except Exception:
				return None, 'pyshorteners is required for TinyURL (install "pyshorteners").'
			try:
				return Shortener().tinyurl.short(url), None
			except Exception as e:
				return None, str(e)

		def _bitly_pyshorteners(url: str):
			token = _get_bitly_token()
			if not token:
				return None, 'Bitly token not set. Click "Token…" to set your Generic Access Token.'
			try:
				from pyshorteners import Shortener  # optional
			except Exception:
				return None, 'pyshorteners is required for Bitly (install "pyshorteners").'
			try:
				return Shortener(api_key=token).bitly.short(url), None
			except Exception as e:
				return None, str(e)

		def _isgd_request(url: str):
			if not requests:
				return None, 'requests is required for is.gd.'
			try:
				resp = requests.get('https://is.gd/create.php', params={'format': 'simple', 'url': url}, timeout=8)
				if resp.status_code == 200 and resp.text:
					return resp.text.strip(), None
				return None, f'is.gd error: HTTP {resp.status_code}'
			except Exception as e:
				return None, f'is.gd error: {e}'

		if provider == 'TinyURL':
			shortened, error_text = _tinyurl_pyshorteners(normalized_url)
		elif provider == 'is.gd':
			shortened, error_text = _isgd_request(normalized_url)
		elif provider == 'Bitly':
			shortened, error_text = _bitly_pyshorteners(normalized_url)
		else:
			error_text = f'Unknown provider: {provider}'

		if shortened:
			shortened_url_string_var.set(shortened)
			add_item_to_history(normalized_url)
			# Auto-update QR inline if available
			try:
				_render_qr_inline()
			except Exception:
				pass
		else:
			messagebox.showerror(getattr(app, 'title_struct', '') + 'error',
								 f'Failed to shorten URL.\n{error_text or "Unknown error"}')


	def expand_action():
		# Follow redirects and return the final URL
		target = shortened_url_string_var.get().strip() or query_entry_string_var.get().strip()
		if not target:
			messagebox.showerror(getattr(app, 'title_struct', '') + 'error', 'Nothing to expand.')
			return
		if not requests:
			messagebox.showerror(getattr(app, 'title_struct', '') + 'error', 'requests package is required to expand URLs.')
			return
		try:
			# Use HEAD first; some providers need GET. Fall back to GET on failure.
			try:
				r = requests.head(target, allow_redirects=True, timeout=8)
				final = getattr(r, 'url', '') or target
			except Exception:
				r = requests.get(target, allow_redirects=True, timeout=8)
				final = getattr(r, 'url', '') or target
			shortened_url_string_var.set(final)
			add_item_to_history(final)
			try:
				_render_qr_inline()
			except Exception:
				pass
		except Exception as e:
			messagebox.showerror(getattr(app, 'title_struct', '') + 'error', f'Failed to expand.\n{e}')


	def copy_shortened_action():
		value_text = shortened_url_string_var.get().strip()
		if not value_text:
			return
		copy_text_to_clipboard(value_text)

	def insert_shortened_action():
		value_text = shortened_url_string_var.get().strip()
		if not value_text:
			messagebox.showerror(getattr(app, 'title_struct', '') + 'error', 'Nothing to insert. Shorten first.')
			return
		insert_text_into_editor(value_text + ' ')

	def show_qr_action():
		value_text = shortened_url_string_var.get().strip() or query_entry_string_var.get().strip()
		if not value_text:
			return
		try:
			normalized_value = normalize_url(value_text)
			qr_url = f'https://chart.googleapis.com/chart?cht=qr&chs={_get_qr_size()}x{_get_qr_size()}&chl={quote_plus(normalized_value)}'
			open_in_browser(qr_url, browser_name=browser_string_var.get(), tab_mode='new')
		except Exception:
			pass

	# Note: removed duplicate on_history_activate and open_history_context_menu definitions here to avoid
	# unintended overrides and multiple bindings. The enhanced versions are defined above in the History section.

	# save preferences on close
	open_action_button.configure(command=open_action)
	shorten_action_button.configure(command=shorten_action)
	expand_action_button.configure(command=expand_action)
	copy_shortened_button.configure(command=copy_shortened_action)
	insert_shortened_button.configure(command=insert_shortened_action)
	show_qr_button.configure(command=show_qr_action)

	# prefill from selection
	try:
		selection_text = get_editor_selection_text().strip()
		if selection_text:
			query_entry_string_var.set(selection_text)
	except Exception:
		pass

	# keys
	popup_root.bind('<Return>', lambda _e: open_action())
	popup_root.bind('<Control-Return>', lambda _e: shorten_action())
	popup_root.bind('<Escape>', lambda _e: popup_root.destroy())
	popup_root.bind('<Control-l>', lambda _e: (query_entry_widget.focus_set(), query_entry_widget.icursor('end')))
	popup_root.bind('<Control-k>', lambda _e: (query_entry_string_var.set('')))
	popup_root.bind('<Delete>', lambda _e: delete_selected_history_item())

	# save preferences on close
	def on_close_window():
		try:
			save_preferences()
		except Exception:
			pass
		try:
			popup_root.destroy()
		except Exception:
			pass

	try:
		popup_root.protocol('WM_DELETE_WINDOW', on_close_window)
	except Exception:
		pass

	try:
		query_entry_widget.focus_set()
		query_entry_widget.icursor('end')
	except Exception:
		pass
