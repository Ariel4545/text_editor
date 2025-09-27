# - TXT/HTML rendering
# - Auto-hiding scrollbars and smooth scrolling via UI builders when available
# - Robust bottom action row (Copy/Insert/Export/Print/Top/Bottom)
# - Enhanced bottom search bar:
#     * Prev/Next navigation with wrap feedback
#     * Case, Whole word, Regex, Diacritics-insensitive, Selection-only toggles
#     * Debounced retagging and resilient error handling
#     * Accurate match tagging using index offsets (works in TXT and HTML modes)
# - Per-page search state + yview + geometry persistence
# - Theme forwarder

from tkinter import (
	Toplevel, Frame, Label, Button, Entry, END, RIDGE, WORD, FLAT
)
from tkinter import messagebox, ttk

import re
import unicodedata
import os
from pathlib import Path


def open_info(app, path: str):
	popup_name = f'info_page:{path}'
	title_suffix = 'Patch notes' if path == 'patch_notes' else 'Help'
	title_text = f'{getattr(app, "title_struct", "")}{title_suffix}'

	# Create window
	created_via_helper = False
	try:
		info_root = app.make_pop_ups_window(
			function=(lambda: open_info(app, path)),
			custom_title=title_text,
			parent=app,
			modal=False,
			topmost=False,
			name=popup_name,
		)
		created_via_helper = True
	except Exception:
		info_root = Toplevel(app)
		try:
			info_root.title(title_text)
			info_root.attributes('-alpha', getattr(app, 'st_value', 0.95))
			if hasattr(app, 'make_tm'):
				app.make_tm(info_root)
		except Exception:
			pass
		try:
			if hasattr(app, 'opened_windows'):
				app.opened_windows.append(info_root)
		except Exception:
			pass

	# Track by stable key
	try:
		if not isinstance(getattr(app, 'func_window', None), dict):
			app.func_window = {}
		app.func_window[popup_name] = info_root
	except Exception:
		pass

	# Root visuals/layout
	try:
		info_root.config(bg=getattr(app, 'dynamic_bg', 'white'))
		info_root.grid_columnconfigure(0, weight=1)
		info_root.grid_rowconfigure(1, weight=0)  # tools row
		info_root.grid_rowconfigure(2, weight=1)  # content area
		info_root.grid_rowconfigure(4, weight=0)  # bottom bar
	except Exception:
		pass

	# Resolve content mode (txt/html)
	def _resolve_content_mode():
		pref = ''
		try:
			pref = (app.content_preference_v.get() or '').strip().lower()
		except Exception:
			pass
		if pref in ('txt', 'html'):
			if pref == 'html':
				try:
					from tkhtmlview import HTMLText as _html_text  # noqa
					return 'html'
				except Exception:
					return 'txt'
			return 'txt'
		try:
			from tkhtmlview import HTMLText as _html_text  # noqa
			return 'html'
		except Exception:
			return 'txt'

	content_mode = _resolve_content_mode()
	try:
		app.content_mode = content_mode
	except Exception:
		pass

	# Title
	title_label = Label(
		info_root,
		text=title_suffix,
		font='arial 16 bold underline',
		justify='left',
		anchor='w',
		fg=getattr(app, 'dynamic_text', 'black'),
		bg=getattr(app, 'dynamic_bg', 'white'),
	)
	title_label.grid(row=0, column=0, padx=8, pady=(8, 6), sticky='ew')

	# Separator between title and content
	try:
		sep_top = ttk.Separator(info_root, orient='horizontal')
		sep_top.grid(row=1, column=0, sticky='ew')
	except Exception:
		pass

	# ---------- Top tools row (copy/insert/export/print/navigation) ----------
	tools_row = Frame(info_root, bg=getattr(app, 'dynamic_overall', 'SystemButtonFace'))
	tools_row.grid(row=2, column=0, sticky='ew', padx=8, pady=(6, 0))
	try:
		for c in range(12):
			tools_row.grid_columnconfigure(c, weight=0)
		tools_row.grid_columnconfigure(11, weight=1)  # spacer
	except Exception:
		pass
	btn_copy = Button(tools_row, text='Copy', bd=1, relief=FLAT,
					  bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
					  fg=getattr(app, 'dynamic_text', 'black'))
	btn_insert = Button(tools_row, text='Insert', bd=1, relief=FLAT,
						bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
						fg=getattr(app, 'dynamic_text', 'black'))
	btn_export = Button(tools_row, text='Export…', bd=1, relief=FLAT,
						bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
						fg=getattr(app, 'dynamic_text', 'black'))
	btn_print = Button(tools_row, text='Print', bd=1, relief=FLAT,
					   bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
					   fg=getattr(app, 'dynamic_text', 'black'))
	btn_top = Button(tools_row, text='Top', bd=1, relief=FLAT,
					 bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
					 fg=getattr(app, 'dynamic_text', 'black'))
	btn_bottom = Button(tools_row, text='Bottom', bd=1, relief=FLAT,
						bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
						fg=getattr(app, 'dynamic_text', 'black'))
	# place
	btn_copy.grid(row=0, column=0, padx=(0, 4), pady=2)
	btn_insert.grid(row=0, column=1, padx=4, pady=2)
	btn_export.grid(row=0, column=2, padx=4, pady=2)
	btn_print.grid(row=0, column=3, padx=4, pady=2)
	btn_top.grid(row=0, column=4, padx=(12, 4), pady=2)
	btn_bottom.grid(row=0, column=5, padx=4, pady=2)

	# Content frame with scroll container
	content_frame = Frame(info_root, bg=getattr(app, 'dynamic_bg', 'white'))
	content_frame.grid(row=3, column=0, padx=8, pady=(6, 4), sticky='nsew')
	try:
		content_frame.grid_columnconfigure(0, weight=1)
		content_frame.grid_rowconfigure(0, weight=1)
	except Exception:
		pass

	# Build rich textbox via UIBuilders (auto scrollbars, wheel, page keys, HTML refreshes)
	builder = getattr(app, '_popup', None)
	text_root_frame, text_widget, y_scroll = None, None, None
	if builder and hasattr(builder, 'make_rich_textbox') and callable(builder.make_rich_textbox):
		try:
			text_root_frame, text_widget, y_scroll = builder.make_rich_textbox(
				parent_container=content_frame,
				place='pack_top',
				wrap=WORD,
				font='arial 10',
				bd=3,
				relief='ridge',
				format=content_mode,
				show_xscroll=True,
				auto_hide_scrollbars=True,
				enable_mousewheel=True,
				initial_refresh_delays=(100, 220),
			)
		except Exception:
			text_root_frame, text_widget, y_scroll = None, None, None
	# Fallback if builders not available
	if text_widget is None:
		from tkinter import Text
		text_widget = Text(content_frame, wrap=WORD, relief=RIDGE, font='arial 10', borderwidth=3,
						   undo=True, selectbackground='dark cyan')
		y_scroll = ttk.Scrollbar(content_frame, orient='vertical', command=text_widget.yview)
		text_widget.config(yscrollcommand=y_scroll.set)
		text_widget.grid(row=0, column=0, sticky='nsew')
		y_scroll.grid(row=0, column=1, sticky='ns')

	# Forward to app for color tools
	try:
		app.info_page_title = title_label
		app.info_page_text = text_widget
		app.info_page_active = True
	except Exception:
		pass

	# ------- helpers: editor insert / copy / export / print / navigation -------
	def _get_all_text_plain() -> str:
		try:
			return text_widget.get('1.0', 'end-1c')
		except Exception:
			return ''

	def _copy_all():
		text_value = _get_all_text_plain()
		if not text_value:
			return
		try:
			info_root.clipboard_clear()
			info_root.clipboard_append(text_value)
		except Exception:
			pass

	def _insert_into_editor():
		text_value = _get_all_text_plain()
		if not text_value:
			return
		try:
			target = getattr(app, 'EgonTE', None)
			if target is None:
				return
			if hasattr(app, 'is_marked') and app.is_marked():
				target.delete('sel.first', 'sel.last')
			pos = app.get_pos() if hasattr(app, 'get_pos') else 'insert'
			target.insert(pos, text_value + '\n')
			try:
				target.see(pos)
				target.focus_set()
			except Exception:
				pass
		except Exception:
			pass

	def _export_view():
		try:
			from tkinter import filedialog
			default_ext = '.html' if content_mode == 'html' else '.txt'
			ft = (('HTML', '*.html'),) if content_mode == 'html' else (('Text', '*.txt'),)
			path = filedialog.asksaveasfilename(parent=info_root, defaultextension=default_ext, filetypes=ft, title='Export view')
			if not path:
				return
			payload = _get_all_text_plain()
			with open(path, 'w', encoding='utf-8') as f:
				f.write(payload)
		except Exception:
			pass

	def _print_view():
		try:
			fs = getattr(app, 'file_service', None)
			payload = _get_all_text_plain()
			if not payload:
				return
			if fs and hasattr(app, 'print_file'):
				import tempfile, os
				with tempfile.NamedTemporaryFile('w', delete=False, suffix='.txt', encoding='utf-8') as tf:
					tf.write(payload)
					tmp_path = tf.name
				try:
					app.file_ = tmp_path  # type: ignore[attr-defined]
					app.print_file()
				finally:
					try:
						os.unlink(tmp_path)
					except Exception:
						pass
			else:
				import tempfile, os, webbrowser
				with tempfile.NamedTemporaryFile('w', delete=False, suffix='.txt', encoding='utf-8') as tf:
					tf.write(payload)
					tmp_path = tf.name
				try:
					if os.name == 'nt':
						os.startfile(tmp_path)  # type: ignore[attr-defined]
					else:
						webbrowser.open('file://' + tmp_path)
				except Exception:
					pass
		except Exception:
			pass

	def _scroll_top():
		try:
			if text_root_frame and hasattr(text_root_frame, 'scroll_to_top'):
				text_root_frame.scroll_to_top()
			else:
				text_widget.yview_moveto(0.0)
		except Exception:
			pass

	def _scroll_bottom():
		try:
			if text_root_frame and hasattr(text_root_frame, 'scroll_to_bottom'):
				text_root_frame.scroll_to_bottom()
			else:
				text_widget.yview_moveto(1.0)
		except Exception:
			pass

	# Wire tools
	btn_copy.configure(command=_copy_all)
	btn_insert.configure(command=_insert_into_editor)
	btn_export.configure(command=_export_view)
	btn_print.configure(command=_print_view)
	btn_top.configure(command=_scroll_top)
	btn_bottom.configure(command=_scroll_bottom)

	# Content loader with robust encoding + HTML set + state restore (yview, geometry)
	# Persist state in app.data
	try:
		if not hasattr(app, 'data') or not isinstance(app.data, dict):
			app.data = {}
		if 'info_window_state' not in app.data or not isinstance(app.data['info_window_state'], dict):
			app.data['info_window_state'] = {}
	except Exception:
		pass

	def _restore_state_after_load():
		try:
			state = app.data.get('info_window_state', {}).get(popup_name, {})
			yfrac = state.get('yview', None)
			if yfrac is not None:
				try:
					text_widget.yview_moveto(float(yfrac))
				except Exception:
					pass
		except Exception:
			pass

	def place_lines():
		nonlocal content_mode  # ensure declared before any use inside this function
		try:
			text_widget.config(state='normal')
		except Exception:
			pass

		file_path = fr'content_msgs\{path}.{content_mode}'
		def _read_file_text(p):
			try:
				with open(p, 'r', encoding='utf-8') as f:
					return f.read()
			except UnicodeDecodeError:
				with open(p, 'r', encoding='cp1252', errors='replace') as f:
					return f.read()

		try:
			if content_mode == 'txt':
				content = _read_file_text(file_path)
				if content.startswith('\ufeff'):
					content = content.lstrip('\ufeff')
				if text_root_frame and hasattr(text_root_frame, 'set_text_safe'):
					text_root_frame.set_text_safe(content)
				else:
					try:
						text_widget.delete('1.0', END)
						text_widget.insert('end', content)
					except Exception:
						pass
			else:
				html = _read_file_text(file_path)
				if html.startswith('\ufeff'):
					html = html.lstrip('\ufeff')
				if text_root_frame and hasattr(text_root_frame, 'set_html_safe'):
					text_root_frame.set_html_safe(html)
				else:
					# Fallback: show stripped text when HTML renderer not available
					stripped = _strip_html(html)
					try:
						text_widget.delete('1.0', END)
						text_widget.insert('end', stripped)
					except Exception:
						pass
		except FileNotFoundError:
			# Smart fallback: try the alternate extension if the preferred one is missing
			try:
				base = Path('content_msgs') / path
				alt = None
				if content_mode == 'html' and (base.with_suffix('.txt')).exists():
					alt = str(base.with_suffix('.txt'))
					content_mode = 'txt'
				elif content_mode == 'txt' and (base.with_suffix('.html')).exists():
					alt = str(base.with_suffix('.html'))
					content_mode = 'html'
				else:
					alt = None
				if alt:
					# Update app’s soft memory about mode
					try:
						app.content_mode = content_mode  # type: ignore
					except Exception:
						pass
					# Re-read and render using the alternate file
					if content_mode == 'txt':
						content = _read_file_text(alt)
						if content.startswith('\ufeff'):
							content = content.lstrip('\ufeff')
						if text_root_frame and hasattr(text_root_frame, 'set_text_safe'):
							text_root_frame.set_text_safe(content)
						else:
							text_widget.delete('1.0', END)
							text_widget.insert('end', content)
					else:
						html = _read_file_text(alt)
						if html.startswith('\ufeff'):
							html = html.lstrip('\ufeff')
						if text_root_frame and hasattr(text_root_frame, 'set_html_safe'):
							text_root_frame.set_html_safe(html)
						else:
							stripped = _strip_html(html)
							text_widget.delete('1.0', END)
							text_widget.insert('end', stripped)
				else:
					try:
						messagebox.showwarning(
							f'{getattr(app, "title_struct", "")} warning',
							f'Content file not found:\n{file_path}'
						)
					except Exception:
						pass
			except Exception:
				pass
		except Exception as e:
			try:
				messagebox.showerror(
					f'{getattr(app, "title_struct", "")} error',
					f'Could not load content:\n{e}'
				)
			except Exception:
				pass
		finally:
			try:
				text_widget.config(state='disabled')
			except Exception:
				pass
			try:
				if text_root_frame and hasattr(text_root_frame, 'content_changed'):
					text_root_frame.content_changed()
			except Exception:
				pass
			# Restore y-view after initial content
			info_root.after(120, _restore_state_after_load)

	# Persist & close
	def quit_page():
		try:
			if hasattr(app, 'opened_windows'):
				app.opened_windows = [w for w in app.opened_windows if w is not info_root]
		except Exception:
			pass
		try:
			app.info_page_active = False
		except Exception:
			pass
		# Persist last search state and view
		try:
			if not hasattr(app, '_info_state') or not isinstance(app._info_state, dict):
				app._info_state = {}
			q = entry.get() if entry else ''
			c = bool(case_var.get()) if case_var else False
			w = bool(word_var.get()) if word_var else False
			r = bool(regex_var.get()) if regex_var else False
			d = bool(diacritics_var.get()) if diacritics_var else False
			s = bool(sel_only_var.get()) if sel_only_var else False
			o = bool(overlap_var.get()) if overlap_var else False
			app._info_state[popup_name] = {'query': q, 'case': c, 'word': w, 'regex': r, 'diacr': d, 'sel': s,
										   'overlap': o}
		except Exception:
			pass
		# Persist window size, position and yview to app.data
		try:
			if not hasattr(app, 'data') or not isinstance(app.data, dict):
				app.data = {}
			if 'info_window_state' not in app.data or not isinstance(app.data['info_window_state'], dict):
				app.data['info_window_state'] = {}
			y0 = 0.0
			try:
				y0, _ = text_widget.yview()
			except Exception:
				pass
			app.data['info_window_state'][popup_name] = {
				'w': info_root.winfo_width(),
				'h': info_root.winfo_height(),
				'x': info_root.winfo_x(),
				'y': info_root.winfo_y(),
				'yview': y0,
				'mode': content_mode,
			}
			if hasattr(app, 'saved_settings'):
				try:
					app.saved_settings(special_mode='save')
				except Exception:
					pass
		except Exception:
			pass
		# Unregister forwarder
		try:
			if hasattr(app, 'ui_forwarders'):
				app.ui_forwarders.pop(popup_name, None)
		except Exception:
			pass
		# Ensure this window is not tracked in any size-limiting list
		try:
			if isinstance(getattr(app, 'limit_list', None), list):
				app.limit_list = [entry for entry in app.limit_list if not (isinstance(entry, (list, tuple)) and entry and entry[0] is info_root)]
		except Exception:
			pass
		# Cancel pending timers (resize/save/wrap/pulse) to avoid posting to destroyed window
		try:
			for holder in (_retag_after, _resize_after, _persist_after, _wrap_blink, _pulse):
				_id = holder.get('id') if isinstance(holder, dict) else None
				if _id:
					info_root.after_cancel(_id)
		except Exception:
			pass
		try:
			info_root.destroy()
		except Exception:
			pass

	try:
		info_root.protocol('WM_DELETE_WINDOW', quit_page)
	except Exception:
		pass

	# ---------------------------- Search/highlight logic ----------------------------
	highlight_bg, highlight_fg = getattr(app, 'highlight_search_c', ('yellow', 'black'))
	oc_color = (
		getattr(app, 'dynamic_overall', 'SystemButtonFace')
		if getattr(app, 'night_mode', None) and getattr(app.night_mode, 'get', lambda: False)()
		else 'SystemButtonFace'
	)
	_search_state = {'matches': [], 'current': -1}
	_wrap_blink = {'id': None}

	# --- color helpers for better visuals ---
	def _blend_hex(c1: str, c2: str, p: float) -> str:
		try:
			c1 = c1.lstrip('#');
			c2 = c2.lstrip('#')
			r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
			r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
			r, g, b = int(r1 * (1 - p) + r2 * p), int(g1 * (1 - p) + g2 * p), int(b1 * (1 - p) + b2 * p)
			return f'#{r:02x}{g:02x}{b:02x}'
		except Exception:
			return '#cccc66'  # safe fallback

	def _resolve_palette():
		# Base colors; if non-hex names are used, blending falls back safely
		base_bg = getattr(app, 'dynamic_bg', '#ffffff')
		base_fg = getattr(app, 'dynamic_text', '#000000')
		hi_bg, hi_fg = getattr(app, 'highlight_search_c', ('#ffeb3b', '#101010'))
		all_bg = _blend_hex(hi_bg, base_bg, 0.55)
		all_fg = base_fg
		cur_bg = _blend_hex(hi_bg, '#ff7043', 0.35)
		cur_fg = '#ffffff' if (
				getattr(app, 'night_mode', None) and getattr(app.night_mode, 'get', lambda: False)()) else '#111111'
		line_bg = _blend_hex(hi_bg, base_bg, 0.80)
		return all_bg, all_fg, cur_bg, cur_fg, line_bg

	def configure_search_tags():
		try:
			all_bg, all_fg, cur_bg, cur_fg, line_bg = _resolve_palette()
			text_widget.tag_config('highlight_all_result', background=all_bg, foreground=all_fg, underline=1)
			text_widget.tag_config('current_match', background=cur_bg, foreground=cur_fg, underline=1, overstrike=0)
			text_widget.tag_config('current_line', background=line_bg)
			try:
				text_widget.tag_lower('highlight_all_result')
				text_widget.tag_raise('current_line', 'highlight_all_result')
				text_widget.tag_raise('current_match', 'current_line')
			except Exception:
				pass
		except Exception:
			pass

	def clear_all_tags():
		try:
			text_widget.tag_remove('highlight_all_result', '1.0', END)
			text_widget.tag_remove('current_match', '1.0', END)
			text_widget.tag_remove('current_line', '1.0', END)
		except Exception:
			pass

	# HTML stripper for fallback or prefiltering when needed
	_html_re = re.compile(r'(<!--.*?-->)|(<[^>]*>)', re.DOTALL)

	def _strip_html(s: str) -> str:
		return _html_re.sub('', s or '')

	# Diacritics normalization with mapping (normalized index -> original index)
	def _normalize_with_maps(s: str):
		norm_chars = []
		norm_to_orig = []
		for i, ch in enumerate(s):
			d = unicodedata.normalize('NFD', ch)
			for sub in d:
				if unicodedata.category(sub) != 'Mn':
					norm_chars.append(sub)
					norm_to_orig.append(i)
		norm_to_orig.append(len(s))
		return ''.join(norm_chars), norm_to_orig

	def _scope_bounds(sel_only: bool):
		if sel_only:
			try:
				start_idx = text_widget.index('sel.first')
				end_idx = text_widget.index('sel.last')
				return start_idx, end_idx
			except Exception:
				pass
		return '1.0', 'end-1c'

	def _get_scope_text(start_idx: str, end_idx: str) -> str:
		try:
			return text_widget.get(start_idx, end_idx)
		except Exception:
			return ''

	def _apply_highlights(matches):
		clear_all_tags()
		for s, e in matches:
			try:
				text_widget.tag_add('highlight_all_result', s, e)
			except Exception:
				pass

	def _blink_wrap():
		# briefly append "(wrapped)" to label
		try:
			base = found_label.cget('text')
			if '(wrapped)' in base:
				return
			found_label.config(text=f'{base} (wrapped)')
			if _wrap_blink['id']:
				info_root.after_cancel(_wrap_blink['id'])
			_wrap_blink['id'] = info_root.after(900, lambda: found_label.config(text=base))
		except Exception:
			pass

	# soft pulse for the current match to draw eye attention
	_pulse = {'id': None, 'phase': 0}

	def _pulse_current_once(idx_start: str, idx_end: str):
		try:
			if _pulse['id']:
				info_root.after_cancel(_pulse['id'])
		except Exception:
			pass

		def step(phase=0):
			try:
				all_bg, all_fg, cur_bg, cur_fg, _ = _resolve_palette()
				if phase % 2 == 0:
					text_widget.tag_config('current_match', background=cur_bg, foreground=cur_fg, underline=1)
				else:
					text_widget.tag_config('current_match', background=_blend_hex(cur_bg, all_bg, 0.25),
										   foreground=cur_fg,
										   underline=1)
				if phase < 3:
					_pulse['id'] = info_root.after(120, lambda: step(phase + 1))
				else:
					text_widget.tag_config('current_match', background=cur_bg, foreground=cur_fg, underline=1)
					_pulse['id'] = None
			except Exception:
				pass

		step(0)

	def _set_current(index: int, *, wrapped=False):
		try:
			text_widget.tag_remove('current_match', '1.0', END)
			text_widget.tag_remove('current_line', '1.0', END)
		except Exception:
			pass
		if not _search_state['matches']:
			_search_state['current'] = -1
			try:
				found_label.config(text='0 of 0')
			except Exception:
				pass
			return
		n = len(_search_state['matches'])
		idx = (index % n + n) % n
		wrapped = wrapped or (index != idx)
		_search_state['current'] = idx
		s, e = _search_state['matches'][idx]
		try:
			text_widget.tag_add('current_match', s, e)
			line_start = text_widget.index(f'{s} linestart')
			line_end = text_widget.index(f'{s} lineend')
			text_widget.tag_add('current_line', line_start, line_end)
			text_widget.see(s)
			text_widget.mark_set('insert', e)
			found_label.config(text=f'{idx + 1} of {n}')
			if wrapped:
				_blink_wrap()
			_pulse_current_once(s, e)
		except Exception:
			pass

	# Debounced retag for responsiveness
	_retag_after = {'id': None}

	def _debounced_retag(term: str, delay=120):
		if _retag_after['id']:
			try:
				info_root.after_cancel(_retag_after['id'])
			except Exception:
				pass
		_retag_after['id'] = info_root.after(delay, lambda: retag_all(term))

	def _build_regex(term: str, *, use_regex: bool, whole_word: bool, case_sensitive: bool):
		if not use_regex:
			pat = re.escape(term)
			if whole_word and term:
				pat = r'(?<!\w)' + pat + r'(?!\w)'
		else:
			pat = term
			if whole_word and term:
				pat = r'(?<!\w)(?:' + pat + r')(?!\w)'
		flags = 0 if case_sensitive else re.IGNORECASE
		try:
			rx = re.compile(pat, flags)
			return rx, pat, flags, None
		except Exception as e:
			return None, None, None, str(e)

	def _overlap_finditer(pat: str, flags: int, text: str):
		# Overlapping matches via lookahead; fallback to non-overlapping if needed
		try:
			rx_ol = re.compile(r'(?=(' + pat + r'))', flags)
			for m in rx_ol.finditer(text):
				g = m.group(1)
				if not g:
					continue
				start = m.start(1)
				end = start + len(g)
				yield start, end
		except Exception:
			try:
				rx = re.compile(pat, flags)
				for m in rx.finditer(text):
					a, b = m.span()
					if a != b:
						yield a, b
			except Exception:
				return

	def retag_all(term: str):
		# Read toggles first
		case_sensitive = bool(case_var.get())
		whole_word = bool(word_var.get())
		use_regex = bool(regex_var.get())
		diacr = bool(diacritics_var.get())
		sel_only = bool(sel_only_var.get())
		overlap = bool(overlap_var.get())

		term = (term or '')
		# Empty input: clear
		if not term.strip():
			_search_state['matches'] = []
			_apply_highlights([])
			try:
				found_label.config(text='')
				status_label.config(text='')
			except Exception:
				pass
			return

		rx, pat, flags, rx_err = _build_regex(term, use_regex=use_regex, whole_word=whole_word,
											  case_sensitive=case_sensitive)
		if rx is None or pat is None:
			try:
				status_label.config(text=f'Regex error: {rx_err}')
			except Exception:
				pass
			return
		else:
			try:
				status_label.config(text='')
			except Exception:
				pass

		# Get scope text and anchor
		scope_start_idx, scope_end_idx = _scope_bounds(sel_only)
		base_text = _get_scope_text(scope_start_idx, scope_end_idx)

		# Diacritics normalization (map back to original char offsets)
		if diacr:
			norm_text, norm_to_orig = _normalize_with_maps(base_text)
			haystack = norm_text
		else:
			haystack = base_text

		# Find matches
		matches_offsets = []
		try:
			if overlap:
				for a, b in _overlap_finditer(pat, flags, haystack):
					matches_offsets.append((a, b))
			else:
				for m in rx.finditer(haystack):
					a, b = m.span()
					if a != b:
						matches_offsets.append((a, b))
		except Exception as e:
			try:
				status_label.config(text=f'Search error: {e}')
			except Exception:
				pass
			return

		# Convert offsets to widget indices and tag
		matches_idx = []
		for a, b in matches_offsets:
			if diacr:
				try:
					a0 = norm_to_orig[a]
					b0 = norm_to_orig[b] if b < len(norm_to_orig) else len(base_text)
				except Exception:
					a0, b0 = a, b
			else:
				a0, b0 = a, b
			try:
				s_idx = text_widget.index(f'{scope_start_idx}+{a0}c')
				e_idx = text_widget.index(f'{scope_start_idx}+{b0}c')
				matches_idx.append((s_idx, e_idx))
			except Exception:
				continue

		_search_state['matches'] = matches_idx
		_apply_highlights(matches_idx)
		if matches_idx:
			_set_current(0)
		else:
			try:
				found_label.config(text='0 of 0')
			except Exception:
				pass

	def goto_next():
		if not _search_state['matches']:
			return
		_set_current(_search_state['current'] + 1, wrapped=True)

	def goto_prev():
		if not _search_state['matches']:
			return
		_set_current(_search_state['current'] - 1, wrapped=True)

	# --------------------------- Bottom separator + search bar ---------------------------
	try:
		sep_bottom = ttk.Separator(info_root, orient='horizontal')
		sep_bottom.grid(row=4, column=0, sticky='ew')
	except Exception:
		pass

	bottom_bar = Frame(info_root, relief=FLAT, bg=getattr(app, 'dynamic_overall', 'SystemButtonFace'))
	bottom_bar.grid(row=5, column=0, sticky='ew')
	try:
		for c in range(20):
			bottom_bar.grid_columnconfigure(c, weight=0)
		# entry expands
		bottom_bar.grid_columnconfigure(2, weight=1)
		# spacer pushes status to the right
		bottom_bar.grid_columnconfigure(15, weight=1)
	except Exception:
		pass

	# Widgets
	find_label = Label(bottom_bar, text='Find:', bg=getattr(app, 'dynamic_overall', 'SystemButtonFace'),
					   fg=getattr(app, 'dynamic_text', 'black'))
	entry = Entry(bottom_bar, relief=FLAT, bg=getattr(app, 'dynamic_bg', 'white'),
				  fg=getattr(app, 'dynamic_text', 'black'))
	clear_btn = Button(bottom_bar, text='×', relief=FLAT, bd=1,
					   bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
					   fg=getattr(app, 'dynamic_text', 'black'))

	button_prev = Button(bottom_bar, text='Prev', relief=FLAT, bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
						 bd=1, fg=getattr(app, 'dynamic_text', 'black'), command=goto_prev)
	button_next = Button(bottom_bar, text='Next', relief=FLAT, bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
						 bd=1, fg=getattr(app, 'dynamic_text', 'black'), command=goto_next)

	# Persisted toggles
	def _mk_boolvar(default=False):
		try:
			from tkinter import BooleanVar
			return BooleanVar(value=default)
		except Exception:
			class _F:
				def __init__(self, v): self._v = bool(v)
				def get(self): return self._v
				def set(self, v): self._v = bool(v)
			return _F(default)

	case_var = getattr(app, '_info_case_sensitive', None) or _mk_boolvar(False)
	word_var = getattr(app, '_info_whole_word', None) or _mk_boolvar(False)
	regex_var = getattr(app, '_info_regex', None) or _mk_boolvar(False)
	diacritics_var = getattr(app, '_info_diacritics', None) or _mk_boolvar(False)
	sel_only_var = getattr(app, '_info_sel_only', None) or _mk_boolvar(False)
	overlap_var = getattr(app, '_info_overlap', None) or _mk_boolvar(False)
	try:
		app._info_case_sensitive = case_var
		app._info_whole_word = word_var
		app._info_regex = regex_var
		app._info_diacritics = diacritics_var
		app._info_sel_only = sel_only_var
		app._info_overlap = overlap_var
	except Exception:
		pass

	# Toggle buttons
	case_cb = Button(bottom_bar, text='Aa', relief=FLAT, bd=1,
					 bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
					 fg=getattr(app, 'dynamic_text', 'black'),
					 command=lambda: (case_var.set(not bool(case_var.get())), _save_state_and_retag()))
	word_cb = Button(bottom_bar, text='W', relief=FLAT, bd=1,
					 bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
					 fg=getattr(app, 'dynamic_text', 'black'),
					 command=lambda: (word_var.set(not bool(word_var.get())), _save_state_and_retag()))
	regex_cb = Button(bottom_bar, text='.*', relief=FLAT, bd=1,
					  bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
					  fg=getattr(app, 'dynamic_text', 'black'),
					  command=lambda: (regex_var.set(not bool(regex_var.get())), _save_state_and_retag()))
	diacr_cb = Button(bottom_bar, text='≈', relief=FLAT, bd=1,
					  bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
					  fg=getattr(app, 'dynamic_text', 'black'),
					  command=lambda: (diacritics_var.set(not bool(diacritics_var.get())), _save_state_and_retag()))
	sel_cb = Button(bottom_bar, text='Sel', relief=FLAT, bd=1,
					bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
					fg=getattr(app, 'dynamic_text', 'black'),
					command=lambda: (sel_only_var.set(not bool(sel_only_var.get())), _save_state_and_retag()))
	ov_cb = Button(bottom_bar, text='Ov', relief=FLAT, bd=1,
				   bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
				   fg=getattr(app, 'dynamic_text', 'black'),
				   command=lambda: (overlap_var.set(not bool(overlap_var.get())), _save_state_and_retag()))
	tag_all_button = Button(bottom_bar, text='Highlight all', relief=FLAT,
							bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
							fg=getattr(app, 'dynamic_text', 'black'), command=lambda: _save_state_and_retag())
	untag_all_button = Button(bottom_bar, text='Lowlight all', relief=FLAT,
							  bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
							  fg=getattr(app, 'dynamic_text', 'black'), command=clear_all_tags)

	found_label = Label(bottom_bar, text='', bg=oc_color, fg=getattr(app, 'dynamic_text', 'black'), anchor='e')
	status_label = Label(bottom_bar, text='', bg=getattr(app, 'dynamic_overall', 'SystemButtonFace'),
						 fg='#888', anchor='w')

	# Grid bottom widgets
	find_label.grid(row=0, column=0, padx=(8, 4), pady=6, sticky='w')
	entry.grid(row=0, column=1, padx=(0, 0), pady=6, sticky='ew', ipady=1)
	clear_btn.grid(row=0, column=2, padx=(6, 10), pady=6)

	button_prev.grid(row=0, column=3, padx=2, pady=6)
	button_next.grid(row=0, column=4, padx=2, pady=6)

	case_cb.grid(row=0, column=5, padx=(10, 2), pady=6)
	word_cb.grid(row=0, column=6, padx=2, pady=6)
	regex_cb.grid(row=0, column=7, padx=2, pady=6)
	diacr_cb.grid(row=0, column=8, padx=2, pady=6)
	sel_cb.grid(row=0, column=9, padx=2, pady=6)
	ov_cb.grid(row=0, column=10, padx=(6, 2), pady=6)

	tag_all_button.grid(row=0, column=11, padx=(12, 2), pady=6)
	untag_all_button.grid(row=0, column=12, padx=2, pady=6)

	status_label.grid(row=0, column=13, padx=(12, 4), pady=6, sticky='w')
	found_label.grid(row=0, column=19, padx=(10, 8), pady=6, sticky='e')

	# Save-state + retag wiring
	def _save_state():
		try:
			if not hasattr(app, '_info_state') or not isinstance(app._info_state, dict):
				app._info_state = {}
			app._info_state[popup_name] = {
				'query': entry.get(),
				'case': bool(case_var.get()),
				'word': bool(word_var.get()),
				'regex': bool(regex_var.get()),
				'diacr': bool(diacritics_var.get()),
				'sel': bool(sel_only_var.get()),
				'overlap': bool(overlap_var.get()),
			}
		except Exception:
			pass

	def _save_state_and_retag():
		_save_state()
		_debounced_retag(entry.get())

	def on_query_change(_evt=None):
		_save_state_and_retag()

	entry.bind('<KeyRelease>', on_query_change)
	# Enter -> next, Shift+Enter -> prev
	try:
		entry.bind('<Return>', lambda e: (goto_next(), 'break'), add='+')
		entry.bind('<Shift-Return>', lambda e: (goto_prev(), 'break'), add='+')
	except Exception:
		pass
	clear_btn.configure(command=lambda: (entry.delete(0, END), _save_state_and_retag()))

	try:
		text_widget.bind('<F3>', lambda e: (goto_next(), 'break'))
		text_widget.bind('<Shift-F3>', lambda e: (goto_prev(), 'break'))
		info_root.bind('<Control-f>', lambda e: (entry.focus_set(), entry.selection_range(0, 'end'), 'break'))
		info_root.bind('<Control-l>', lambda e: (entry.focus_set(), entry.selection_range(0, 'end'), 'break'), add='+')
		info_root.bind('<Escape>', lambda e: (entry.delete(0, END), _save_state_and_retag(), 'break'), add='+')
		info_root.bind('<Control-w>', lambda e: (quit_page(), 'break'), add='+')  # quick close
		# Quick toggles
		info_root.bind('<Alt-a>', lambda e: (case_var.set(not bool(case_var.get())), _save_state_and_retag(), 'break'))
		info_root.bind('<Alt-w>', lambda e: (word_var.set(not bool(word_var.get())), _save_state_and_retag(), 'break'))
		info_root.bind('<Alt-r>',
					   lambda e: (regex_var.set(not bool(regex_var.get())), _save_state_and_retag(), 'break'))
		info_root.bind('<Alt-i>',
					   lambda e: (diacritics_var.set(not bool(diacritics_var.get())), _save_state_and_retag(), 'break'))
		info_root.bind('<Alt-s>',
					   lambda e: (sel_only_var.set(not bool(sel_only_var.get())), _save_state_and_retag(), 'break'))
		info_root.bind('<Alt-o>',
					   lambda e: (overlap_var.set(not bool(overlap_var.get())), _save_state_and_retag(), 'break'))
	except Exception:
		pass

	# Tooltips (if available)
	try:
		if builder and hasattr(builder, 'place_toolt'):
			builder.place_toolt(targets=[
				(btn_copy, 'Copy current page to clipboard'),
				(btn_insert, 'Insert page into editor'),
				(btn_export, 'Export page to file'),
				(btn_print, 'Print (or open in default app)'),
				(btn_top, 'Scroll to top'),
				(btn_bottom, 'Scroll to bottom'),
				(entry, 'Type to search (Ctrl+F/L to focus)'),
				(clear_btn, 'Clear search'),
				(button_prev, 'Previous match (Shift+F3)'),
				(button_next, 'Next match (F3)'),
				(case_cb, 'Case sensitive (Aa) [Alt+A]'),
				(word_cb, 'Whole word (W) [Alt+W]'),
				(regex_cb, 'Regex (.*) [Alt+R]'),
				(diacr_cb, 'Diacritics-insensitive (≈) [Alt+I]'),
				(sel_cb, 'Search in selection only [Alt+S]'),
				(ov_cb, 'Allow overlapping matches [Alt+O]'),
				(tag_all_button, 'Highlight all matches'),
				(untag_all_button, 'Lowlight all'),
			], delay_ms=600, follow_mouse=True)
	except Exception:
		pass

	# Theme forwarder
	def apply_theme():
		try:
			title_label.config(fg=getattr(app, 'dynamic_text', 'black'), bg=getattr(app, 'dynamic_bg', 'white'))
			try:
				tools_row.config(bg=getattr(app, 'dynamic_overall', 'SystemButtonFace'))
				for b in (btn_copy, btn_insert, btn_export, btn_print, btn_top, btn_bottom):
					b.config(bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
							 fg=getattr(app, 'dynamic_text', 'black'))
			except Exception:
				pass
			try:
				content_frame.config(bg=getattr(app, 'dynamic_bg', 'white'))
			except Exception:
				pass
			entry.config(bg=getattr(app, 'dynamic_bg', 'white'), fg=getattr(app, 'dynamic_text', 'black'))
			bottom_bar.config(bg=getattr(app, 'dynamic_overall', 'SystemButtonFace'))
			for btn in (button_prev, button_next, case_cb, word_cb, regex_cb, diacr_cb, sel_cb, ov_cb, tag_all_button,
						untag_all_button, clear_btn):
				btn.config(bg=getattr(app, 'dynamic_button', 'SystemButtonFace'),
						   fg=getattr(app, 'dynamic_text', 'black'))
			found_label.config(
				bg=(getattr(app, 'dynamic_overall', 'SystemButtonFace')
					if getattr(app, 'night_mode', None) and getattr(app.night_mode, 'get', lambda: False)()
					else 'SystemButtonFace'),
				fg=getattr(app, 'dynamic_text', 'black')
			)
			status_label.config(bg=getattr(app, 'dynamic_overall', 'SystemButtonFace'), fg='#888')
			try:
				text_widget.config(bg=getattr(app, 'dynamic_bg', 'white'), fg=getattr(app, 'dynamic_text', 'black'))
			except Exception:
				pass
			# Recompute tag colors on theme change
			configure_search_tags()
		except Exception:
			pass

	try:
		if not hasattr(app, 'ui_forwarders') or not isinstance(app.ui_forwarders, dict):
			app.ui_forwarders = {}
		app.ui_forwarders[popup_name] = apply_theme
	except Exception:
		pass

	# Finalize content
	configure_search_tags()
	place_lines()
	try:
		# Restore geometry if we persisted it earlier
		saved_geo = app.data.get('info_window_state', {}).get(popup_name, {}) if isinstance(getattr(app, 'data', {}), dict) else {}
		if saved_geo and isinstance(saved_geo, dict):
			w = int(saved_geo.get('w') or 0)
			h = int(saved_geo.get('h') or 0)
			x = saved_geo.get('x')
			y = saved_geo.get('y')
			if w > 100 and h > 100:
				if isinstance(x, int) and isinstance(y, int):
					info_root.geometry(f'{w}x{h}+{x}+{y}')
				else:
					info_root.geometry(f'{w}x{h}')
	except Exception:
		pass
	try:
		text_widget.focus_set()
	except Exception:
		pass

	# --- Responsive/resizable window setup ---
	def _apply_grid_weights():
		try:
			# Ensure the content area (row=3) expands, others stay compact
			info_root.grid_columnconfigure(0, weight=1)
			# tools row (2), separators (1,4), bottom (5) don't expand
			info_root.grid_rowconfigure(0, weight=0)
			info_root.grid_rowconfigure(1, weight=0)
			info_root.grid_rowconfigure(2, weight=0)
			info_root.grid_rowconfigure(3, weight=1)  # main content
			info_root.grid_rowconfigure(4, weight=0)
			info_root.grid_rowconfigure(5, weight=0)
			# Inside the content frame, make its inner grid expand
			content_frame.grid_columnconfigure(0, weight=1)
			content_frame.grid_rowconfigure(0, weight=1)
		except Exception:
			pass

	# Central policy: honor the host's "limit window sizes" toggle.
	# If limit_w_s is truthy -> lock; otherwise allow resizing.
	def _apply_resizable_policy():
		allow = True
		try:
			var = getattr(app, 'limit_w_s', None)
			if var is not None:
				get = getattr(var, 'get', None)
				if callable(get):
					allow = not bool(get())
				else:
					allow = not bool(var)
		except Exception:
			pass
		try:
			info_root.resizable(allow, allow)
		except Exception:
			pass
		# Sync with the main app's limiter list for consistency with other tools
		try:
			if not hasattr(app, 'limit_list') or not isinstance(app.limit_list, list):
				app.limit_list = []
			if allow:
				# remove any limiter record for this window
				app.limit_list = [rec for rec in app.limit_list if not (isinstance(rec, (list, tuple)) and rec and rec[0] is info_root)]
			else:
				# add/update a limiter record for this window (stores current size as baseline)
				size_tuple = (info_root.winfo_width(), info_root.winfo_height())
				# replace existing entry if present
				updated = False
				for i, rec in enumerate(list(app.limit_list)):
					if isinstance(rec, (list, tuple)) and rec and rec[0] is info_root:
						app.limit_list[i] = [info_root, size_tuple]
						updated = True
						break
				if not updated:
					app.limit_list.append([info_root, size_tuple])
		except Exception:
			pass
		return allow

	# React to runtime changes of the host's flag, if it is a Tk variable
	try:
		_lw = getattr(app, 'limit_w_s', None)
		if hasattr(_lw, 'trace_add'):
			_lw.trace_add('write', lambda *_: _apply_resizable_policy())
	except Exception:
		pass

	_size_state = {'w': 0, 'h': 0}
	_resize_after = {'id': None}
	_persist_after = {'id': None}

	def _persist_geometry_throttled():
		if _persist_after['id']:
			try:
				info_root.after_cancel(_persist_after['id'])
			except Exception:
				pass

		def _do_persist():
			try:
				if not hasattr(app, 'data') or not isinstance(app.data, dict):
					app.data = {}
				if 'info_window_state' not in app.data or not isinstance(app.data['info_window_state'], dict):
					app.data['info_window_state'] = {}
				app.data['info_window_state'][popup_name] = {
					'w': info_root.winfo_width(),
					'h': info_root.winfo_height(),
					'x': info_root.winfo_x(),
					'y': info_root.winfo_y(),
					'yview': (text_widget.yview()[0] if hasattr(text_widget, 'yview') else 0.0),
					'mode': content_mode,
				}
				if hasattr(app, 'saved_settings'):
					try:
						app.saved_settings(special_mode='save')
					except Exception:
						pass
			except Exception:
				pass
			finally:
				_persist_after['id'] = None

		_persist_after['id'] = info_root.after(300, _do_persist)

	def _on_window_resize(_evt=None):
		if _resize_after['id']:
			try:
				info_root.after_cancel(_resize_after['id'])
			except Exception:
				pass

		def _do_resize():
			try:
				w, h = max(0, info_root.winfo_width()), max(0, info_root.winfo_height())
				if (w, h) == (_size_state['w'], _size_state['h']):
					return
				_size_state['w'], _size_state['h'] = w, h
				# Keep labels tidy during width changes
				width = max(0, bottom_bar.winfo_width() - 40)
				try:
					status_label.config(wraplength=width)
				except Exception:
					pass
				try:
					found_label.config(wraplength=max(120, width // 3))
				except Exception:
					pass
				_apply_grid_weights()
				try:
					if text_root_frame and hasattr(text_root_frame, 'content_changed'):
						text_root_frame.content_changed()
				except Exception:
					pass
				_persist_geometry_throttled()
			except Exception:
				pass
			finally:
				_resize_after['id'] = None

		_resize_after['id'] = info_root.after(24, _do_resize)

	def _enable_resizable_with_min_from_current():
		try:
			info_root.update_idletasks()
			# If resizing is allowed, set a sensible minimum size; otherwise lock to current
			allow = _apply_resizable_policy()
			try:
				if allow:
					# Minimal but readable baseline to allow shrinking
					info_root.minsize(420, 300)
				else:
					cur_w, cur_h = info_root.winfo_width(), info_root.winfo_height()
					if cur_w > 0 and cur_h > 0:
						info_root.minsize(cur_w, cur_h)
			except Exception:
				pass
			_apply_grid_weights()
			# First sizing pass and live binding
			_on_window_resize()
			try:
				info_root.bind('<Configure>', _on_window_resize, add='+')
			except Exception:
				pass
			return allow
		except Exception:
			return _apply_resizable_policy()


	# Activate resizability after initial paint/restore to capture the correct minimum size
	try:
		info_root.after(120, _enable_resizable_with_min_from_current)
	except Exception:
		_enable_resizable_with_min_from_current()

	# Restore last search state for this page, if available
	try:
		saved = getattr(app, '_info_state', {}).get(popup_name, None)
		if isinstance(saved, dict):
			if isinstance(saved.get('query'), str):
				entry.delete(0, END)
				entry.insert(0, saved['query'])
			if 'case' in saved:
				case_var.set(bool(saved['case']))
			if 'word' in saved:
				word_var.set(bool(saved['word']))
			if 'regex' in saved:
				regex_var.set(bool(saved['regex']))
			if 'diacr' in saved:
				diacritics_var.set(bool(saved['diacr']))
			if 'sel' in saved:
				sel_only_var.set(bool(saved['sel']))
			if 'overlap' in saved:
				overlap_var.set(bool(saved['overlap']))
			_debounced_retag(entry.get(), delay=10)
	except Exception:
		pass

	# Center/size if helper wasn't used
	if not created_via_helper:
		try:
			info_root.update_idletasks()
			win_w, win_h = info_root.winfo_width(), info_root.winfo_height()
			ete_x, ete_y = (app.winfo_x()), (app.winfo_y())
			ete_w, ete_h = app.winfo_width(), app.winfo_height()
			mid_x = round(ete_x + (ete_w / 2) - (win_w / 2))
			mid_y = round(ete_y + (ete_h / 2) - (win_h / 2))
			if abs(mid_y - app.winfo_screenheight()) <= 80:
				mid_y = (app.winfo_screenheight() // 2)
			if getattr(app, 'open_middle_s', None) and getattr(app.open_middle_s, 'get', lambda: False)():
				info_root.geometry(f'{win_w}x{win_h}+{mid_x}+{mid_y}')
			# Respect the global policy here too (no unconditional locking)
			_apply_resizable_policy()
		except Exception:
			pass
