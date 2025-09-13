from tkinter import (
    Toplevel, Entry, Text, Frame, Label, Button, Radiobutton, Scrollbar, IntVar,
    Checkbutton, Spinbox, StringVar, BooleanVar
)
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk, UnidentifiedImageError
from io import BytesIO
import urllib.request
import threading
import webbrowser
import requests
from queue import Queue
from wikipedia import page, summary, search as wiki_search, exceptions
from PyDictionary import PyDictionary
from urllib.parse import urlparse
from threading import Thread
import re

def open_knowledge_popup(app, mode: str):
	'''
	Knowledge popup for Dictionary and Wikipedia, with:
	- Tabs per tool (Search / Results; + Images for wiki) and balanced min-size per tool
	- Smooth resizing and stable centering (window center stays fixed on size changes)
	- Non-blocking network calls (background threads) with run-id to discard stale results
	- Robust images handling (1:1 URL <-> PIL <-> PhotoImage) with image info and actions
	- Polished text output (normalized spacing) + copy/paste integration
	- Mode switching and bridging between Dictionary and Wikipedia (reduced collision)
	  + Options: auto-search (both), auto-pick suggestion (wiki), max images (wiki), copy result, auto-bridge (dict)
	- Wiki mode radios + Ctrl+1..4 switching; keyboard shortcuts for bridging
	- Safer URL opens and sanitized search terms
	- Responsive images loading (parallel and incremental)
	'''
	# ---------- Tunables ----------
	image_max_initial = 600
	image_scale_step = 2
	http_timeout_s = 8.0            # network timeout for image fetches
	wiki_default_max_images = 24    # safety cap to keep UI responsive
	wiki_user_agent = 'Mozilla/5.0 (EgonTE Knowledge Tool)'
	search_debounce_ms = 2600        # slower to prevent premature searches while typing
	image_workers = 6               # parallel fetchers for images (soft cap)
	min_chars_for_autosearch = 3    # don't auto-search on very short inputs

	# ---------- Popup ----------
	popup_window = app.make_pop_ups_window(
		function=open_knowledge_popup,
		custom_title=('Wikipedia' if mode == 'wiki' else 'Dictionary'),
		name='knowledge_window',
		topmost=False,
		modal=False,
	)

	# Helper: common min-size per tool (ratio-optimized)
	try:
		if mode == 'wiki':
			popup_window.minsize(900, 560)
		else:
			popup_window.minsize(720, 460)
	except Exception:
		pass

	# ---------- Tabs (Notebook) ----------
	notebook = ttk.Notebook(popup_window)
	tab_search = Frame(notebook)
	tab_results = Frame(notebook)

	# Always present tabs
	notebook.add(tab_search, text='Search')
	notebook.add(tab_results, text='Results')

	# Images tab only for wiki
	tab_images = None
	if mode == 'wiki':
		tab_images = Frame(notebook)
		notebook.add(tab_images, text='Images')

	notebook.pack(fill='both', expand=True, padx=8, pady=8)

	# Helper to switch tabs
	def _select_tab(name: str):
		try:
			mapping = {'search': tab_search, 'results': tab_results}
			if tab_images is not None:
				mapping['images'] = tab_images
			notebook.select(mapping.get(name, tab_results))
		except Exception:
			pass

	# ---------- Header (Search tab) ----------
	header_text = 'Wikipedia' if mode == 'wiki' else 'Dictionary'
	header_label = Label(tab_search, text=header_text, font='arial 13 bold')
	header_label.grid(row=0, column=0, sticky='w')

	mode_feedback = Label(tab_search, text='', font='arial 9')
	mode_feedback.grid(row=1, column=0, pady=(2, 6), sticky='w')

	# ---------- Controls row (Search tab) ----------
	controls_frame = Frame(tab_search)
	controls_frame.grid(row=2, column=0, pady=(2, 2), sticky='ew')
	controls_frame.grid_columnconfigure(0, weight=0)
	controls_frame.grid_columnconfigure(1, weight=1)
	controls_frame.grid_columnconfigure(2, weight=0)

	search_label = Label(controls_frame, text='Search term')
	search_entry = Entry(controls_frame, width=35)
	search_button = Button(controls_frame, text='Search')

	search_label.grid(row=0, column=0, padx=(0, 6), sticky='w')
	search_entry.grid(row=0, column=1, padx=(0, 6), sticky='ew')
	search_button.grid(row=0, column=2, padx=(6, 0), sticky='e')

	status_label = Label(tab_search, text='Ready', font='arial 9')
	status_label.grid(row=3, column=0, pady=(4, 8), sticky='w')
	# removed old length label from the Search tab

	# ---------- Options (Search tab, right side; optimized by tool) ----------
	opts_row = Frame(tab_search)
	opts_row.grid(row=4, column=0, sticky='ew')
	# left spacer to push the options to the right
	Frame(opts_row).pack(side='left', fill='x', expand=True)
	opts_inner = Frame(opts_row)
	opts_inner.pack(side='right', anchor='e')

	# Persist options across opens (soft)
	_opts = getattr(app, '_knowledge_opts', None)
	if not isinstance(_opts, dict):
		_opts = {}
		try:
			app._knowledge_opts = _opts
		except Exception:
			pass

	# Shared
	auto_search_var = BooleanVar(value=bool(_opts.get('auto_search', True)))
	# Dict-only
	auto_bridge_var = BooleanVar(value=bool(_opts.get('auto_bridge', True)))
	# Wiki-only
	auto_pick_var = BooleanVar(value=bool(_opts.get('auto_pick', False)))
	max_images_var = StringVar(value=str(_opts.get('max_images', wiki_default_max_images)))

	# Build options by tool
	col = 0
	cb_auto_search = Checkbutton(opts_inner, text='Auto-search', variable=auto_search_var, onvalue=True, offvalue=False)
	cb_auto_search.grid(row=0, column=col, padx=(0, 6)); col += 1

	if mode == 'wiki':
		cb_auto_pick = Checkbutton(opts_inner, text='Auto-pick', variable=auto_pick_var, onvalue=True, offvalue=False)
		cb_auto_pick.grid(row=0, column=col, padx=(0, 6)); col += 1
		Label(opts_inner, text='Max images:').grid(row=0, column=col, padx=(8, 0), sticky='e'); col += 1
		max_images_spin = Spinbox(opts_inner, from_=4, to=60, width=4, textvariable=max_images_var)
		max_images_spin.grid(row=0, column=col, padx=(2, 6)); col += 1
	else:
		cb_auto_bridge = Checkbutton(opts_inner, text='Bridge if empty', variable=auto_bridge_var, onvalue=True, offvalue=False)
		cb_auto_bridge.grid(row=0, column=col, padx=(0, 6)); col += 1

	copy_result_btn = Button(opts_inner, text='Copy result')
	copy_result_btn.grid(row=0, column=col, padx=(6, 0)); col += 1

	# ---------- Results tab ----------
	tab_results.grid_rowconfigure(0, weight=1)
	tab_results.grid_columnconfigure(0, weight=1)

	meaning_container = Frame(tab_results)
	meaning_container.grid(row=0, column=0, sticky='nsew')

	meaning_frame = Frame(meaning_container, borderwidth=1, relief='groove')
	meaning_scrollbar = Scrollbar(meaning_container)
	meaning_text_box = Text(meaning_frame, height=20, width=72, wrap='word')
	meaning_text_box.configure(state='disabled')
	meaning_text_box.grid(row=0, column=0, padx=6, pady=6, sticky='nsew')
	meaning_frame.grid(row=0, column=0, sticky='nsew')
	meaning_scrollbar.grid(row=0, column=1, sticky='ns')
	meaning_frame.grid_columnconfigure(0, weight=1)
	meaning_frame.grid_rowconfigure(0, weight=1)
	meaning_text_box.configure(yscrollcommand=meaning_scrollbar.set)
	meaning_scrollbar.configure(command=meaning_text_box.yview)

	# Beautiful, durable stats row under the output text-box
	length_row = Frame(tab_results)
	length_row.grid(row=1, column=0, sticky='ew', padx=8, pady=(0, 6))
	try:
		length_row.grid_columnconfigure(0, weight=1)
	except Exception:
		pass
	length_label = Label(
		length_row,
		text='',
		font='arial 9',
		fg='#555555',
		anchor='w',
		justify='left'
	)
	length_label.grid(row=0, column=0, sticky='w')

	# Footer (Results tab)
	footer_frame = Frame(tab_results)
	footer_frame.grid(row=2, column=0, pady=(2, 2), sticky='ew')
	for i in range(6):
		try:
			footer_frame.grid_columnconfigure(i, weight=0)
		except Exception:
			pass
	app.paste_b_info = Button(footer_frame, text='Paste to ETE', bd=1, state='disabled')
	app.paste_b_info.grid(row=0, column=0, padx=4, sticky='w')
	app.wiki_open_btn = Button(footer_frame, text='Open page', bd=1, state='disabled')
	app.wiki_open_btn.grid(row=0, column=1, padx=4, sticky='w')
	app.wiki_copy_url_btn = Button(footer_frame, text='Copy URL', bd=1, state='disabled')
	app.wiki_copy_url_btn.grid(row=0, column=2, padx=4, sticky='w')
	bridge_to_dict_btn = Button(footer_frame, text='Define (Dict)')
	bridge_to_wiki_btn = Button(footer_frame, text='Wiki summary')
	bridge_to_dict_btn.grid(row=0, column=4, padx=6, sticky='e')
	bridge_to_wiki_btn.grid(row=0, column=5, padx=2, sticky='e')

	# ---------- Images tab (wiki only) ----------
	if tab_images is not None:
		tab_images.grid_rowconfigure(0, weight=1)
		tab_images.grid_columnconfigure(0, weight=1)

		images_outer = Frame(tab_images)
		images_outer.grid(row=0, column=0, sticky='nsew')
		images_outer.grid_rowconfigure(0, weight=1)
		images_outer.grid_columnconfigure(0, weight=1)

		# Scaled images are navigated one-by-one; we still provide a vertical scrollbar if needed later
		images_canvas = Frame(images_outer)
		images_canvas.grid(row=0, column=0, sticky='nsew')
		images_scrollbar = Scrollbar(images_outer, orient='vertical')
		images_scrollbar.grid(row=0, column=1, sticky='ns')

		app.wiki_img_frame = Frame(images_canvas, width=35, height=40, borderwidth=1, relief='groove')
		try:
			app.wiki_img_frame.grid_columnconfigure(0, weight=1)
			for r in (0, 1, 2, 3, 4):
				app.wiki_img_frame.grid_rowconfigure(r, weight=1 if r == 0 else 0)
		except Exception:
			pass
		app.wiki_image_label = Label(app.wiki_img_frame)
		app.wiki_nav_frame = Frame(app.wiki_img_frame)
		app.wiki_nav_backwards = Button(app.wiki_nav_frame, text='<<')
		app.wiki_nav_forward = Button(app.wiki_nav_frame, text='>>')
		app.wiki_image_info = Label(app.wiki_img_frame, text='', font='arial 9')
		images_hint_label = Label(app.wiki_img_frame, text='Tip: Ctrl+.(next) / Ctrl+,(prev) • Click image to open', font='arial 9')
		img_actions = Frame(app.wiki_img_frame)
		img_copy_url_btn = Button(img_actions, text='Copy URL')
		img_open_btn = Button(img_actions, text='Open')

		app.wiki_img_frame.grid(row=0, column=0, padx=4, pady=4, sticky='nsew')
	else:
		# Stubs to avoid NameErrors when mode='dict'
		app.wiki_img_frame = Frame(popup_window)
		app.wiki_image_label = Label(app.wiki_img_frame)
		app.wiki_nav_frame = Frame(app.wiki_img_frame)
		app.wiki_nav_backwards = Button(app.wiki_nav_frame)
		app.wiki_nav_forward = Button(app.wiki_nav_frame)
		app.wiki_image_info = Label(app.wiki_img_frame)
		images_hint_label = Label(app.wiki_img_frame)
		img_actions = Frame(app.wiki_img_frame)
		img_copy_url_btn = Button(img_actions)
		img_open_btn = Button(img_actions)

	# ---------- State ----------
	app.last_wiki_image = False
	app.wiki_request_text = ''
	app.wiki_request_images = []     # filtered URLs (1:1 with images)
	app.wiki_img_list = []           # list[PhotoImage]
	app._wiki_images_meta = []       # list[{'size': (w,h)}]
	app.image_selected_index = 0
	app._wiki_current_url = ''       # resolved page url for summary/content
	_search_seq = {'id': 0}          # run id to drop stale results
	_debounce_handle = {'h': None}
	_center_state = {'cx': None, 'cy': None, 'w': None, 'h': None, 'lock': False}

	# ---------- Security helpers ----------
	def _is_safe_url(url: str, *, allow_wiki_only: bool = False) -> bool:
		try:
			p = urlparse((url or '').strip())
			if p.scheme not in ('http', 'https'):
				return False
			if not p.netloc:
				return False
			if allow_wiki_only:
				host = p.netloc.lower()
				return (host.endswith('.wikipedia.org') or host.endswith('.wikimedia.org'))
			return True
		except Exception:
			return False

	def _sanitize_term(raw: str) -> str:
		try:
			term = (raw or '').strip()
			term = ' '.join(term.split())
			if len(term) > 256:
				term = term[:256]
			return term
		except Exception:
			return (raw or '').strip()

	# ---------- Centering and resize ----------
	def _center_on_parent():
		try:
			popup_window.update_idletasks()
			parent = app
			pw = popup_window.winfo_width()
			ph = popup_window.winfo_height()
			try:
				ax, ay = parent.winfo_x(), parent.winfo_y()
				aw, ah = parent.winfo_width(), parent.winfo_height()
			except Exception:
				sw, sh = popup_window.winfo_screenwidth(), popup_window.winfo_screenheight()
				x = max(0, (sw - pw) // 2)
				y = max(0, (sh - ph) // 2)
				popup_window.geometry(f'{pw}x{ph}+{x}+{y}')
				_center_state.update({'cx': x + pw // 2, 'cy': y + ph // 2, 'w': pw, 'h': ph})
				return
			x = max(0, ax + (aw // 2) - (pw // 2))
			y = max(0, ay + (ah // 2) - (ph // 2))
			popup_window.geometry(f'{pw}x{ph}+{x}+{y}')
			_center_state.update({'cx': x + pw // 2, 'cy': y + ph // 2, 'w': pw, 'h': ph})
		except Exception:
			pass

	def _on_configure(event=None):
		if _center_state['lock']:
			return
		try:
			w, h = popup_window.winfo_width(), popup_window.winfo_height()
			x, y = popup_window.winfo_x(), popup_window.winfo_y()
			cx, cy = x + w // 2, y + h // 2
			prev_w, prev_h = _center_state.get('w'), _center_state.get('h')
			prev_cx, prev_cy = _center_state.get('cx'), _center_state.get('cy')
			if None in (prev_w, prev_h, prev_cx, prev_cy):
				_center_state.update({'w': w, 'h': h, 'cx': cx, 'cy': cy})
				return
			if (w != prev_w) or (h != prev_h):
				_center_state['lock'] = True
				try:
					new_x = max(0, int(prev_cx - w / 2))
					new_y = max(0, int(prev_cy - h / 2))
					popup_window.geometry(f'{w}x{h}+{new_x}+{new_y}')
				finally:
					popup_window.after_idle(lambda: _center_state.update({'lock': False}))
				_center_state.update({'w': w, 'h': h})
			else:
				_center_state.update({'w': w, 'h': h, 'cx': cx, 'cy': cy})
		except Exception:
			pass

	# ---------- Options/state helpers ----------
	def _save_opts():
		try:
			app._knowledge_opts = {
				'auto_search': bool(auto_search_var.get()),
				'auto_pick': bool(auto_pick_var.get()) if mode == 'wiki' else False,
				'auto_bridge': bool(auto_bridge_var.get()) if mode != 'wiki' else app._knowledge_opts.get('auto_bridge', True),
				'max_images': int(max_images_var.get() or wiki_default_max_images) if mode == 'wiki' else app._knowledge_opts.get('max_images', wiki_default_max_images),
			}
		except Exception:
			pass

	def set_paste_enabled(is_enabled: bool):
		app.paste_b_info.configure(state=('normal' if is_enabled else 'disabled'))

	def set_open_page_enabled(url: str | None):
		# Enable only for wiki pages; for dict always disabled
		if mode != 'wiki':
			app.wiki_open_btn.configure(state='disabled')
			app.wiki_copy_url_btn.configure(state='disabled')
			return
		is_ok = bool(url and isinstance(url, str))
		app.wiki_open_btn.configure(state=('normal' if is_ok else 'disabled'))
		app.wiki_copy_url_btn.configure(state=('normal' if is_ok else 'disabled'))

	def _sharpen_text_output(text_value: str) -> str:
		if not text_value:
			return text_value
		s = text_value.replace('\r\n', '\n').replace('\r', '\n')
		lines = [ln.rstrip() for ln in s.split('\n')]
		polished = []
		last_blank = False
		for ln in lines:
			blank = (ln.strip() == '')
			if blank:
				if last_blank:
					continue
				last_blank = True
				polished.append('')
			else:
				last_blank = False
				polished.append(ln)
		return '\n'.join(polished).strip()


	def set_text_box_state(is_enabled: bool):
		meaning_text_box.configure(state=('normal' if is_enabled else 'disabled'))

	def set_text_box_content(text_value: str):
		set_text_box_state(True)
		try:
			meaning_text_box.delete('1.0', 'end')
			if text_value:
				meaning_text_box.insert('1.0', _sharpen_text_output(text_value))
		finally:
			set_text_box_state(False)
		set_paste_enabled(bool(text_value and text_value.strip()))

	def _wiki_mode_label(code: int) -> str:
		return {1: 'Summary', 2: 'Related', 3: 'Content', 4: 'Images'}.get(int(code or 0), 'Summary')

	# Text length/stats helpers (durable and detailed; robust to any chars)
	def _summarize_text_stats(text_value: str | None) -> str:
		try:
			if not text_value:
				return ''
			txt = str(text_value)
			total_chars = len(txt)
			non_space_chars = sum(1 for c in txt if not c.isspace())
			words = [w for w in txt.split() if w.strip()]
			word_count = len(words)
			lines = txt.splitlines()
			line_count = len(lines) if txt else 0
			# paragraphs = non-empty blocks separated by blank lines
			paragraphs = 0
			block_has_text = False
			for ln in (lines or ([] if not txt else [''])):
				if ln.strip():
					block_has_text = True
				else:
					if block_has_text:
						paragraphs += 1
						block_has_text = False
			if block_has_text:
				paragraphs += 1
			# rough sentence count (handles many chars gracefully)
			sentences = re.findall(r'[^\s].*?[.!?]+(?=\s|$)', txt, flags=re.DOTALL)
			sentence_count = len(sentences)

			parts = [
				f'Length: {total_chars} chars',
				f'{non_space_chars} non-space',
				f'~{word_count} words',
				f'{line_count} lines',
				f'{paragraphs} paragraphs',
				f'{sentence_count} sentences',
			]
			return ' • '.join(parts)
		except Exception:
			return ''

	def _set_length_label_from_text(text_value: str | None):
		try:
			length_label.configure(text=_summarize_text_stats(text_value))
		except Exception:
			try:
				length_label.configure(text='')
			except Exception:
				pass

	def _refresh_mode_feedback():
		if mode == 'wiki':
			try:
				mode_feedback.configure(text=f'Mode: {_wiki_mode_label(app.wiki_var.get())}')
			except Exception:
				mode_feedback.configure(text='Mode: —')
		else:
			mode_feedback.configure(text='')

	def set_busy(is_busy: bool, message: str = None):
		search_button.configure(state=('disabled' if is_busy else 'normal'))
		if message is None:
			if is_busy:
				if mode == 'wiki':
					try:
						message = f"Searching {_wiki_mode_label(app.wiki_var.get())}..."
					except Exception:
						message = 'Searching...'
				else:
					message = 'Searching...'
			else:
				message = 'Ready'
		status_label.configure(text=message)

	def show_error_dialog(title_suffix: str, message_text: str):
		try:
			messagebox.showerror(getattr(app, 'title_struct', '') + title_suffix, message_text)
		finally:
			set_busy(False, 'Error')
			try:
				popup_window.after(1500, lambda: set_busy(False, 'Ready'))
			except Exception:
				pass

	def scale_pil_image(pil_image_obj):
		'''
		Coarsely clamp an image size so it's not absurdly large when it arrives.
		Uses integer halving (image_scale_step) to keep it fast, then stops.
		'''
		width_value, height_value = getattr(pil_image_obj, 'size', (None, None))
		if not width_value or not height_value:
			return pil_image_obj

		# Coarse, fast downscale loop to cap huge assets
		scale_counter = 1
		while width_value > image_max_initial * scale_counter or height_value > image_max_initial * scale_counter:
			width_value = max(1, width_value // image_scale_step)
			height_value = max(1, height_value // image_scale_step)
			try:
				# Use LANCZOS when available for better quality
				try:
					pil_image_obj = pil_image_obj.resize((width_value, height_value), Image.LANCZOS)
				except Exception:
					pil_image_obj = pil_image_obj.resize((width_value, height_value))
			except Exception:
				break
			scale_counter += 1
		return pil_image_obj

	def fetch_pil_image(image_url: str):
		'''
		Fetch bytes -> PIL image with a friendly User-Agent and timeout.
		Returns (pil_image, original_size) or (None, None) on failure.
		Performs a coarse scale to keep giant assets manageable.
		'''
		try:
			req = urllib.request.Request(image_url, headers={'User-Agent': wiki_user_agent})
			with urllib.request.urlopen(req, timeout=http_timeout_s) as http_response:
				image_bytes = http_response.read()
		except Exception:
			return None, None

		try:
			pil_image_obj = Image.open(BytesIO(image_bytes))
			orig_size = getattr(pil_image_obj, 'size', (None, None))
		except UnidentifiedImageError:
			return None, None
		except Exception:
			return None, None

		# Normalize mode when possible (some formats are 'P' or 'LA' which render oddly)
		try:
			if pil_image_obj.mode not in ('RGB', 'RGBA'):
				# Prefer RGBA to keep transparency if present
				pil_image_obj = pil_image_obj.convert('RGBA' if 'A' in pil_image_obj.getbands() else 'RGB')
		except Exception:
			# If conversion fails, continue with whatever mode we have
			pass

		try:
			# Coarse size clamp; a finer, container-aware clamp happens at display time
			pil_image_obj = scale_pil_image(pil_image_obj)
			return pil_image_obj, orig_size
		except Exception:
			return None, None

	def _fit_pil_to_frame(pil_img):
		'''
		Fit the given PIL image to the current images container so it won't exceed the layout.
		This is a second, precise clamp that runs on the UI thread right before creating PhotoImage.
		- Uses app.wiki_img_frame when available (preferred).
		- Falls back to popup_window dimensions if the frame hasn't been laid out yet.
		- Leaves some vertical room for navigation, info and action buttons.
		- Only scales down (never scales up).
		'''
		try:
			# Make sure layout measurements are current
			popup_window.update_idletasks()
		except Exception:
			pass

		try:
			# Prefer the inner frame (most accurate)
			container_w = app.wiki_img_frame.winfo_width() or 0
			container_h = app.wiki_img_frame.winfo_height() or 0

			# If frame is not yet sized (first image), fallback to popup size with margins
			if not container_w or not container_h:
				container_w = max(320, popup_window.winfo_width() - 80)
				container_h = max(240, popup_window.winfo_height() - 220)

			# Horizontal padding around the image
			pad_w = 32
			# Reserve vertical space for nav buttons + labels + hints
			reserved_h = 180

			max_w = max(240, int(container_w - pad_w))
			max_h = max(240, int(container_h - reserved_h))

			w, h = getattr(pil_img, 'size', (None, None))
			if not w or not h:
				return pil_img

			scale = min(max_w / float(w), max_h / float(h))
			if scale >= 1.0:
				# The image fits already
				return pil_img

			new_w = max(1, int(w * scale))
			new_h = max(1, int(h * scale))
			try:
				return pil_img.resize((new_w, new_h), Image.LANCZOS)
			except Exception:
				return pil_img.resize((new_w, new_h))
		except Exception:
			# On any failure, keep the original (already coarsely clamped) image
			return pil_img

	# ---------- Layout switchers ----------
	def switch_to_text_mode():
		app.last_wiki_image = False
		_select_tab('results')

	def switch_to_images_mode():
		if mode != 'wiki':
			return
		# NOTE: Do NOT auto-switch to Images tab on mode change or typing.
		# Only switch when at least one image is successfully loaded.
		app.last_wiki_image = True
		app.wiki_image_label.grid(row=0, column=0, padx=8, pady=8)
		app.wiki_nav_frame.grid(row=1, column=0, pady=(0, 4))
		app.wiki_nav_backwards.grid(row=0, column=0, padx=8)
		app.wiki_nav_forward.grid(row=0, column=1, padx=8)
		img_actions.grid(row=2, column=0, pady=(0, 2))
		img_copy_url_btn.grid(row=0, column=0, padx=(0, 6))
		img_open_btn.grid(row=0, column=1)
		app.wiki_image_info.grid(row=3, column=0, pady=(0, 4))
		images_hint_label.grid(row=4, column=0, pady=(0, 8))

	# ---------- Images nav ----------
	def _update_image_info():
		try:
			total = len(app.wiki_img_list)
			idx = app.image_selected_index + 1 if total else 0
			size_text = ''
			if total and 0 <= app.image_selected_index < len(app._wiki_images_meta):
				meta = app._wiki_images_meta[app.image_selected_index]
				w, h = meta.get('size', (None, None))
				if w and h:
					size_text = f' • {w}×{h}'
			app.wiki_image_info.configure(text=f'Image {idx}/{total}{size_text} • Click to open source')
		except Exception:
			try:
				app.wiki_image_info.configure(text='Image 0/0')
			except Exception:
				pass

	def _sync_nav_buttons():
		state = 'normal' if len(app.wiki_img_list) > 1 else 'disabled'
		try:
			app.wiki_nav_forward.configure(state=state)
			app.wiki_nav_backwards.configure(state=state)
		except Exception:
			pass

	def navigate_images(navigation_mode: str, event=None):
		if mode != 'wiki':
			return
		if getattr(app, 'wiki_var', None) and app.wiki_var.get() != 4:
			show_error_dialog('wiki', 'You are not in images mode.')
			return
		if not app.wiki_img_list:
			show_error_dialog('wiki', 'No images to display.')
			return

		if navigation_mode in ('f', 'b'):
			images_count = len(app.wiki_img_list)
			app.image_selected_index = (app.image_selected_index + (1 if navigation_mode == 'f' else -1)) % images_count
		else:
			app.image_selected_index = 0
			app.wiki_image_label.grid(row=0, column=0, padx=8, pady=8)

		try:
			app.wiki_image_label.unbind('<ButtonRelease-1>')
			app.wiki_image_label.grid_forget()
		except Exception:
			pass

		current_photo_image = app.wiki_img_list[app.image_selected_index]
		app.wiki_image_label.configure(image=current_photo_image)
		app.wiki_image_label.grid(row=0, column=0, padx=8, pady=8)

		def open_image_in_browser(evt=None):
			try:
				url = app.wiki_request_images[app.image_selected_index]
				if _is_safe_url(url):
					webbrowser.open_new(url)
			except Exception:
				pass

		app.wiki_image_label.bind('<ButtonRelease-1>', open_image_in_browser)
		_update_image_info()
		_sync_nav_buttons()

	popup_window.bind('<Control-Key-.>', lambda e: navigate_images('f', event=e))
	popup_window.bind('<Control-Key-,>', lambda e: navigate_images('b', event=e))
	app.wiki_nav_forward.configure(command=lambda: navigate_images('f'))
	app.wiki_nav_backwards.configure(command=lambda: navigate_images('b'))

	# ---------- Clipboard actions ----------
	def paste_result_to_editor():
		try:
			text_to_paste = meaning_text_box.get('1.0', 'end')
			app.EgonTE.insert(app.get_pos(), text_to_paste)
		except Exception:
			pass

	app.paste_b_info.configure(command=paste_result_to_editor)

	def _open_current_page():
		try:
			url = (app._wiki_current_url or '').strip()
			if _is_safe_url(url, allow_wiki_only=True):
				webbrowser.open_new(url)
		except Exception:
			pass

	def _copy_current_url():
		try:
			url = (app._wiki_current_url or '').strip()
			if _is_safe_url(url, allow_wiki_only=True):
				popup_window.clipboard_clear()
				popup_window.clipboard_append(url)
		except Exception:
			pass

	app.wiki_open_btn.configure(command=_open_current_page)
	app.wiki_copy_url_btn.configure(command=_copy_current_url)

	def _img_copy_url():
		try:
			if app.wiki_request_images:
				url = (app.wiki_request_images[app.image_selected_index] or '').strip()
				if _is_safe_url(url):
					popup_window.clipboard_clear()
					popup_window.clipboard_append(url)
		except Exception:
			pass

	def _img_open_url():
		try:
			if app.wiki_request_images:
				url = (app.wiki_request_images[app.image_selected_index] or '').strip()
				if _is_safe_url(url):
					webbrowser.open_new(url)
		except Exception:
			pass

	img_copy_url_btn.configure(command=_img_copy_url)
	img_open_btn.configure(command=_img_open_url)

	def _copy_result_to_clipboard():
		try:
			text_to_copy = meaning_text_box.get('1.0', 'end')
			popup_window.clipboard_clear()
			popup_window.clipboard_append(text_to_copy)
		except Exception:
			pass

	copy_result_btn.configure(command=_copy_result_to_clipboard)

	# ---------- Render helpers ----------
	def render_text_result_async(text_value: str, *, run_id: int):
		if run_id != _search_seq['id']:
			return
		def _apply():
			switch_to_text_mode()
			set_text_box_content(text_value or '')
			_set_length_label_from_text(text_value or '')
			set_busy(False, 'Ready')
		popup_window.after(0, _apply)

	def render_related_articles_async(articles_list, *, run_id: int):
		if run_id != _search_seq['id']:
			return

		def write_related():
			if run_id != _search_seq['id']:
				return
			switch_to_text_mode()
			set_text_box_state(True)
			try:
				meaning_text_box.delete('1.0', 'end')
				if articles_list:
					meaning_text_box.insert('end', 'Related articles:\n\n')
					for i, article_title in enumerate(articles_list, 1):
						meaning_text_box.insert('end', f'{i}. {article_title}\n')
					meaning_text_box.insert('end', '\nTip: copy a title into the search box and press Enter.\n')
			finally:
				set_text_box_state(False)
			_set_length_label_from_text(None)
			set_paste_enabled(bool(articles_list))
			set_open_page_enabled(None)
			set_busy(False, 'Ready')
		popup_window.after(0, write_related)

	def _filter_image_urls(urls):
		# Keep only http(s), common raster formats, safe hosts (prefer wiki*), and drop SVG
		allowed_ext = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff')
		seen = set()
		filtered = []
		for u in (urls or []):
			try:
				url = (u or '').strip()
				if not url:
					continue
				if not _is_safe_url(url):
					continue
				low = url.lower()
				if low.endswith('.svg') or '.svg' in low:
					continue
				if not low.endswith(allowed_ext):
					host = urlparse(url).netloc.lower()
					if not (host.endswith('.wikipedia.org') or host.endswith('.wikimedia.org')):
						continue
				if url in seen:
					continue
				seen.add(url)
				filtered.append(url)
			except Exception:
				continue
		return filtered

	def render_images_incremental_async(image_urls_list, *, run_id: int):
		# Reset state
		app.wiki_request_images = []
		app.wiki_img_list = []
		app._wiki_images_meta = []
		app.image_selected_index = 0

		def build_incremental():
			try:
				cap = int(max(4, min(60, int(max_images_var.get() or wiki_default_max_images))))
			except Exception:
				cap = wiki_default_max_images

			# Filter/dedupe upfront to avoid many failures and SVGs
			urls = _filter_image_urls(list(image_urls_list or []))[:cap]
			if not urls:
				popup_window.after(0, lambda: show_error_dialog('wiki', 'No images found for this page.') if run_id ==
																											 _search_seq[
																												 'id'] else None)
				popup_window.after(0, lambda: set_busy(False, 'Ready'))
				return

			# Don't switch tab yet; wait until first image is actually ready
			_sync_nav_buttons()
			_update_image_info()
			set_busy(True, 'Loading images...')

			q = Queue()

			# Fill the queue BEFORE starting workers to avoid early thread exit
			for u in urls:
				q.put(u)

			# Track remaining workers to finalize exactly once
			worker_count = max(1, min(image_workers, len(urls)))
			remaining_workers = {'n': worker_count}

			def worker():
				while True:
					try:
						u = q.get_nowait()
					except Exception:
						break
					try:
						pil_img, orig_size = fetch_pil_image(u)
						if pil_img is not None and run_id == _search_seq['id']:
							def place_one():
								if run_id != _search_seq['id']:
									# ... existing code ...
									return
								# Ensure current layout metrics then fit image to frame
								try:
									popup_window.update_idletasks()
								except Exception:
									pass
								fit_img = _fit_pil_to_frame(pil_img)

								app.wiki_request_images.append(u)
								app._wiki_images_meta.append({'size': (orig_size or (None, None))})
								try:
									app.wiki_img_list.append(ImageTk.PhotoImage(fit_img))
								except Exception:
									try:
										app.wiki_request_images.pop()
										app._wiki_images_meta.pop()
									except Exception:
										pass
									return
								# Switch to images tab only when the first image is ready
								if len(app.wiki_img_list) == 1:
									_select_tab('images')
									switch_to_images_mode()
									navigate_images('initial')
								else:
									_update_image_info()
									_sync_nav_buttons()

							popup_window.after(0, place_one)
					except Exception:
						pass
				# Finalize exactly once when all workers are done and run_id still current
				if run_id == _search_seq['id']:
					def maybe_finalize():
						remaining_workers['n'] -= 1
						if remaining_workers['n'] == 0:
							if not app.wiki_img_list:
								show_error_dialog('wiki', 'No images found for this page.')
							set_busy(False, 'Ready')

					popup_window.after(0, maybe_finalize)

			for _ in range(worker_count):
				Thread(target=worker, daemon=True).start()

		threading.Thread(target=build_incremental, daemon=True).start()

	# ---------- Formatters ----------
	def _format_summary_block(title: str, url: str | None, summary_text: str) -> str:
		lines = []
		if summary_text:
			lines.append(summary_text.strip())
		return '\n'.join(lines).strip()

	def _format_content_block(title: str, url: str | None, content_text: str, sections: list[str] | None) -> str:
		lines = []
		if sections:
			lines.append('Sections:')
			for s in sections[:20]:
				lines.append(f' - {s}')
		if content_text:
			if sections:
				lines.append('')
			lines.append(content_text.strip())
		return '\n'.join(lines).strip()

	# ---------- Dictionary pipeline ----------
	def _dictionary_plus(client: PyDictionary, term: str) -> str:
		out = []
		meanings_map = None
		try:
			meanings_map = client.meaning(term)
		except Exception:
			meanings_map = None

		if meanings_map:
			for part_of_speech in sorted(meanings_map.keys(), key=str.casefold):
				definitions_list = meanings_map.get(part_of_speech) or []
				clean_defs = []
				seen = set()
				for d in definitions_list:
					txt = (d or '').strip()
					if txt and txt not in seen:
						seen.add(txt)
						clean_defs.append(txt)
				if clean_defs:
					out.append(f'{part_of_speech.capitalize()} ({len(clean_defs)} definitions)\n')
					for definition_text in clean_defs:
						out.append(f'• {definition_text}')
					out.append('')
		try:
			syns = client.synonym(term) or []
			syns = [s for s in syns if s and isinstance(s, str)]
			if syns:
				out.append('Synonyms:')
				out.append(', '.join(sorted(set(syns), key=str.casefold)))
				out.append('')
		except Exception:
			pass
		try:
			ants = client.antonym(term) or []
			ants = [a for a in ants if a and isinstance(a, str)]
			if ants:
				out.append('Antonyms:')
				out.append(', '.join(sorted(set(ants), key=str.casefold)))
				out.append('')
		except Exception:
			pass

		if not out:
			out.append('(No definitions found)')
		return '\n'.join(out).strip()

	def run_dictionary_search(search_term: str, *, run_id: int):
		if not search_term:
			render_text_result_async('', run_id=run_id)
			_set_length_label_from_text(None)
			return
		try:
			dictionary_client = PyDictionary()
			block = _dictionary_plus(dictionary_client, search_term)
			set_open_page_enabled(None)
			# Dictionary blocks are heterogeneous; omit stats to avoid confusion
			_set_length_label_from_text(None)
			if '(No definitions found)' in block and bool(auto_bridge_var.get()):
				popup_window.after(0, lambda: _start_run(run_wikipedia_search))
			else:
				render_text_result_async(block, run_id=run_id)
		except AttributeError:
			if run_id == _search_seq['id']:
				show_error_dialog('error', 'Check your internet / your search!')
		except Exception:
			if run_id == _search_seq['id']:
				show_error_dialog('error', 'Dictionary error')

		# ---------- Wikipedia pipeline ----------
	def run_wikipedia_search(search_term: str, *, run_id: int):
		if not search_term:
			render_text_result_async('', run_id=run_id)
			return

		try:
			if getattr(app, 'last_wiki_image', False) and app.wiki_var.get() != 4:
				popup_window.after(0, switch_to_text_mode)
			app.last_wiki_image = False
			set_open_page_enabled(None)
			app._wiki_current_url = ''
			_refresh_mode_feedback()

			set_busy(True, f"Searching {_wiki_mode_label(app.wiki_var.get())}...")

			wiki_page_obj = None
			if app.wiki_var.get() in (1, 3, 4):
				try:
					wiki_page_obj = page(search_term)
				except exceptions.DisambiguationError:
					wiki_page_obj = None
				except Exception:
					wiki_page_obj = None

			if app.wiki_var.get() == 1:
				text_summary = ''
				try:
					text_summary = summary(search_term)
				except exceptions.DisambiguationError as de:
					raise de
				except Exception:
					text_summary = ''
				title = getattr(wiki_page_obj, 'title', search_term)
				url = getattr(wiki_page_obj, 'url', None)
				app._wiki_current_url = (url or '') if _is_safe_url(url or '', allow_wiki_only=True) else ''
				set_open_page_enabled(app._wiki_current_url)
				_set_length_label_from_text(text_summary)
				result_block = _format_summary_block(title, url, text_summary)
				render_text_result_async(result_block, run_id=run_id)

			elif app.wiki_var.get() == 2:
				related_articles_list = list(wiki_search(search_term))
				render_related_articles_async(related_articles_list, run_id=run_id)
				_set_length_label_from_text(None)
				if related_articles_list and bool(auto_pick_var.get()):
					try:
						best = related_articles_list[0]
						search_entry.delete(0, 'end')
						search_entry.insert(0, best)
						_queue_search_now()
					except Exception:
						pass

			elif app.wiki_var.get() == 3:
				page_title = getattr(wiki_page_obj, 'title', search_term)
				page_content = getattr(wiki_page_obj, 'content', '')
				url = getattr(wiki_page_obj, 'url', None)
				sections = list(getattr(wiki_page_obj, 'sections', []) or [])
				app._wiki_current_url = (url or '') if _is_safe_url(url or '', allow_wiki_only=True) else ''
				set_open_page_enabled(app._wiki_current_url)
				_set_length_label_from_text(page_content)
				result_block = _format_content_block(page_title, url, page_content, sections)
				render_text_result_async(result_block, run_id=run_id)

			elif app.wiki_var.get() == 4:
				app.last_wiki_image = True
				_set_length_label_from_text(None)
				images_attr = list(getattr(wiki_page_obj, 'images', []) or []) if wiki_page_obj else []
				render_images_incremental_async(images_attr, run_id=run_id)



		except requests.exceptions.ConnectionError:
			if run_id == _search_seq['id']:
				show_error_dialog('error', 'Check your internet connection')
		except exceptions.DisambiguationError as disambiguation_error:
			def handle_disambiguation():
				if run_id != _search_seq['id']:
					return
				set_open_page_enabled(None)
				try:
					opts = list(getattr(disambiguation_error, 'options', []) or [])
				except Exception:
					opts = []
				switch_to_text_mode()
				set_text_box_state(True)
				try:
					meaning_text_box.delete('1.0', 'end')
					meaning_text_box.insert('end', 'Ambiguous term. Possible matches:\n\n')
					for i, opt in enumerate(opts[:25], 1):
						meaning_text_box.insert('end', f'{i}. {opt}\n')
					meaning_text_box.insert('end', '\nTip: copy a title into the search box and press Enter.\n')
				finally:
					set_text_box_state(False)
				try:
					candidate = ''
					if opts:
						lowered = (search_term or '').strip().lower()
						candidate = next((o for o in opts if lowered and lowered in o.lower()), opts[0])
					if candidate:
						search_entry.delete(0, 'end')
						search_entry.insert(0, candidate)
						if bool(auto_pick_var.get()):
							_queue_search_now()
				except Exception:
					pass
				set_paste_enabled(False)
				set_busy(False, 'Ready')
			popup_window.after(0, handle_disambiguation)
		except exceptions.PageError:
			if run_id == _search_seq['id']:
				show_error_dialog('error', 'Invalid page ID')
		except Exception:
			if run_id == _search_seq['id']:
				show_error_dialog('error', 'Unexpected Wikipedia error')

	# ---------- Runners, debounced ----------
	def _start_run(target_callable):
		_search_seq['id'] += 1
		run_id = _search_seq['id']
		set_paste_enabled(False)
		set_open_page_enabled(None)
		set_text_box_state(True)
		try:
			term_value = _sanitize_term(search_entry.get())
			search_entry.delete(0, 'end')
			search_entry.insert(0, term_value)
			meaning_text_box.delete('1.0', 'end')
			meaning_text_box.insert('1.0', 'Searching...')
		finally:
			set_text_box_state(False)
		set_busy(True)
		term_value = search_entry.get().strip()

		def worker_thread():
			try:
				target_callable(term_value, run_id=run_id)
			finally:
				try:
					popup_window.after(100, lambda: set_busy(False, 'Ready'))
				except Exception:
					pass

		threading.Thread(target=worker_thread, daemon=True).start()

	def redirect_search():
		_save_opts()
		# Avoid triggering searches for empty/whitespace-only terms
		try:
			current_term = _sanitize_term(search_entry.get())
		except Exception:
			current_term = (search_entry.get() or '').strip()
		if not current_term:
			return

		if mode == 'wiki':
			_start_run(run_wikipedia_search)
		else:
			_start_run(run_dictionary_search)

	def _cancel_debounce():
		h = _debounce_handle.get('h')
		if h is not None:
			try:
				popup_window.after_cancel(h)
			except Exception:
				pass
			_debounce_handle['h'] = None

	def _debounced_search():
		# Never auto-search while in Wikipedia Images mode
		if mode == 'wiki':
			try:
				if int(app.wiki_var.get()) == 4:
					return
			except Exception:
				pass
		# Require a minimum number of characters before auto-search
		try:
			term_now = (search_entry.get() or '').strip()
			if len(term_now) < min_chars_for_autosearch:
				_cancel_debounce()
				return
		except Exception:
			pass
		_cancel_debounce()
		if bool(auto_search_var.get()):
			_debounce_handle['h'] = popup_window.after(search_debounce_ms, redirect_search)

	def _queue_search_now():
		_cancel_debounce()
		redirect_search()

	search_button.configure(command=_queue_search_now)
	search_entry.bind('<Return>', lambda e: _queue_search_now())
	search_entry.bind('<KeyRelease>', lambda e: _debounced_search())

	# Smooth mode switching: Ctrl+1..4 and radio commands trigger re-search if term present
	def _switch_mode_and_search(new_value: int):
		try:
			app.wiki_var.set(new_value)
		except Exception:
			pass
		_refresh_mode_feedback()

		# While in Images mode (4): NEVER auto-search and NEVER auto-switch tabs.
		if mode == 'wiki' and new_value == 4:
			app.wiki_request_images = []
			app.wiki_img_list = []
			app._wiki_images_meta = []
			_sync_nav_buttons()
			_update_image_info()
			try:
				status_label.configure(text='Images mode: type a term and press Search to load images')
			except Exception:
				pass
			try:
				cb_auto_search.configure(state='disabled')
			except Exception:
				pass
			# Stay on current tab (usually Search) until images actually load
			return
		else:
			try:
				cb_auto_search.configure(state='normal')
			except Exception:
				pass

		current_term = search_entry.get().strip()
		if current_term:
			_queue_search_now()
		else:
			switch_to_text_mode()

	if mode == 'wiki':
		popup_window.bind('<Control-Key-1>', lambda e: _switch_mode_and_search(1))
		popup_window.bind('<Control-Key-2>', lambda e: _switch_mode_and_search(2))
		popup_window.bind('<Control-Key-3>', lambda e: _switch_mode_and_search(3))
		popup_window.bind('<Control-Key-4>', lambda e: _switch_mode_and_search(4))

	# ---------- Bridge actions (wire buttons + shortcuts) ----------
	def _bridge_to_dictionary():
		try:
			search_value = _sanitize_term(search_entry.get())
			search_entry.delete(0, 'end')
			search_entry.insert(0, search_value)
		except Exception:
			search_value = (search_entry.get() or '').strip()
		# Skip if no term to avoid empty searches
		if not search_value:
			return
		try:
			_start_run(run_dictionary_search)
		except Exception:
			pass

	def _bridge_to_wikipedia_summary():
		try:
			if not hasattr(app, 'wiki_var') or app.wiki_var is None:
				app.wiki_var = IntVar(value=1)
			else:
				app.wiki_var.set(1)
		except Exception:
			pass
		try:
			search_value = _sanitize_term(search_entry.get())
			search_entry.delete(0, 'end')
			search_entry.insert(0, search_value)
		except Exception:
			search_value = (search_entry.get() or '').strip()
		# Skip if no term to avoid empty searches
		if not search_value:
			return
		try:
			_start_run(run_wikipedia_search)
		except Exception:
			pass

	try:
		bridge_to_dict_btn.configure(command=_bridge_to_dictionary)
		bridge_to_wiki_btn.configure(command=_bridge_to_wikipedia_summary)
	except Exception:
		pass
	try:
		popup_window.bind('<Control-Shift-D>', lambda e: _bridge_to_dictionary())
		popup_window.bind('<Control-Shift-W>', lambda e: _bridge_to_wikipedia_summary())
	except Exception:
		pass

	# ---------- Mode radios (Search tab, wiki only) ----------
	if mode == 'wiki':
		try:
			if not hasattr(app, 'wiki_var') or app.wiki_var is None:
				app.wiki_var = IntVar(value=1)
			else:
				current = 0
				try:
					current = int(app.wiki_var.get())
				except Exception:
					current = 0
				if current not in (1, 2, 3, 4):
					app.wiki_var.set(1)
		except Exception:
			try:
				app.wiki_var = IntVar(value=1)
			except Exception:
				pass

		radio_frame = Frame(tab_search)
		radio_summary = Radiobutton(radio_frame, text='Summary', variable=app.wiki_var, value=1,
									command=lambda: _switch_mode_and_search(1))
		radio_related = Radiobutton(radio_frame, text='Related', variable=app.wiki_var, value=2,
									command=lambda: _switch_mode_and_search(2))
		radio_content = Radiobutton(radio_frame, text='Content', variable=app.wiki_var, value=3,
									command=lambda: _switch_mode_and_search(3))
		radio_images = Radiobutton(radio_frame, text='Images', variable=app.wiki_var, value=4,
								   command=lambda: _switch_mode_and_search(4))

		radio_frame.grid(row=5, column=0, pady=(8, 0), sticky='ew')
		for i, w in enumerate((radio_summary, radio_related, radio_content, radio_images)):
			try:
				radio_frame.grid_columnconfigure(i, weight=1, uniform='modes')
			except Exception:
				pass
			w.grid(row=0, column=i, padx=4, sticky='ew')

		try:
			if int(app.wiki_var.get()) == 1:
				radio_summary.select()
		except Exception:
			pass
		_select_tab('search')
		_refresh_mode_feedback()
	else:
		try:
			app.record_list.append(f'> [{app.get_time()}] - Dictionary tool window opened')
		except Exception:
			pass
		_select_tab('search')
		mode_feedback.configure(text='')

	# ---------- Final touches ----------
	try:
		if getattr(app, 'EgonTE', None):
			sel = app.EgonTE.get('sel.first', 'sel.last')
			sel = (sel or '').strip()
			if sel:
				search_entry.delete(0, 'end')
				search_entry.insert(0, sel[:256])
	except Exception:
		pass

	try:
		popup_window.update_idletasks()
		_center_on_parent()
		popup_window.bind('<Configure>', _on_configure)
	except Exception:
		pass
	try:
		search_entry.focus_set()
	except Exception:
		pass
