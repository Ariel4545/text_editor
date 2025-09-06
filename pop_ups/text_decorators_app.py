import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
from typing import Dict, List, Tuple, Optional

from large_variables import characters_dict


def open_text_decorators(app) -> None:
	'''
	Text Decorators popup (drop-in update).

	UI
	- Top controls are organized in a ttk.Notebook (tabs: Style, Layout, Preview, Options, Tools, Transforms, Outport, Window).
	- Main content uses a ttk.Notebook (tabs: Input, Output).
	- Output tab has dedicated vertical + horizontal scrollbars (no orientation flipping).

	Stability / UX
	- Input/Output widgets are created up-front (no lazy creation).
	- Min window size can be locked/unlocked from the Window tab.
	- Live preview is debounced and guarded (prevents recursion and race conditions).
	- No duplicate buttons outside tab controls (everything is inside the tabs).
	'''

	# ---------- initial state and caches ----------
	available_styles = tuple(characters_dict.keys())
	chosen_style = 'bash' if 'bash' in available_styles else available_styles[0]
	styles_validated = False
	style_cache_map: Dict[str, Dict[str, object]] = {}
	render_cache_map: Dict[Tuple[str, str, str, int], str] = {}

	# widgets
	result_container_frame: Optional[tk.Frame] = None
	result_text_widget: Optional[tk.Text] = None
	result_scrollbar_widget: Optional[ttk.Scrollbar] = None
	result_hscroll_widget: Optional[ttk.Scrollbar] = None

	text_input_frame: Optional[tk.Frame] = None
	text_input_textbox: Optional[tk.Text] = None
	text_input_scrollbar: Optional[ttk.Scrollbar] = None

	# guards
	updating_ui: bool = False

	# ---------- validation ----------
	def validate_styles_once() -> None:
		nonlocal styles_validated
		if styles_validated:
			return
		issues_list: List[str] = []
		for style_name, style_triple in characters_dict.items():
			try:
				style_ascii_dict, style_alphabet, style_height = style_triple
			except Exception:
				issues_list.append(f'{style_name}: invalid style triple structure')
				continue

			try:
				if hasattr(style_alphabet, '__len__') and hasattr(style_ascii_dict, 'keys'):
					if len(style_ascii_dict.keys()) != len(style_alphabet):
						issues_list.append(f'{style_name}: dict/alphabet length mismatch ({len(style_ascii_dict)} vs {len(style_alphabet)})')
			except Exception:
				pass

			for char_key, glyph_text in getattr(style_ascii_dict, 'items', lambda: [])():
				try:
					glyph_lines = str(glyph_text).split('\n')
					while glyph_lines and glyph_lines[-1] == '':
						glyph_lines.pop()
					if isinstance(style_height, int) and style_height >= 0 and len(glyph_lines) != style_height:
						issues_list.append(f'{style_name}: glyph "{char_key}" has {len(glyph_lines)} lines, expected {style_height}')
				except Exception:
					continue

		if issues_list:
			try:
				messagebox.showwarning('EgonTE (developer)', 'Text decorator style issues detected:\n- ' + '\n- '.join(issues_list))
			except Exception:
				pass
		styles_validated = True

	# ---------- glyph helpers ----------
	def _clean_and_measure_glyph(raw_glyph: str) -> List[str]:
		lines = str(raw_glyph).split('\n')
		while lines and lines[-1] == '':
			lines.pop()
		lines = [line.expandtabs(4) for line in lines]
		return lines

	def _left_trim_common(lines: List[str]) -> List[str]:
		if not lines:
			return lines
		def leading_spaces(s: str) -> int:
			i = 0
			while i < len(s) and s[i] == ' ':
				i += 1
			return i if i < len(s) else len(s)
		non_blank = [ls for ls in lines if ls.strip()]
		if not non_blank:
			return lines
		min_lead = min(leading_spaces(ls) for ls in non_blank)
		if min_lead <= 0:
			return lines
		return [ls[min_lead:] if len(ls) >= min_lead else '' for ls in lines]

	def _center_pad_rect(lines: List[str], target_width: int, target_height: int) -> List[str]:
		trimmed = [ls.rstrip(' ') for ls in lines]
		centered = []
		for ls in trimmed:
			ln = len(ls)
			if ln >= target_width:
				centered.append(ls[:target_width])
			else:
				left = (target_width - ln) // 2
				right = target_width - ln - left
				centered.append((' ' * left) + ls + (' ' * right))
		if len(centered) >= target_height:
			return centered[:target_height]
		top = (target_height - len(centered)) // 2
		bottom = target_height - len(centered) - top
		return ([' ' * target_width] * top) + centered + ([' ' * target_width] * bottom)

	# ---------- per-style cache ----------
	def prepare_style_cache(style_name: str) -> Dict[str, object]:
		if style_name in style_cache_map:
			return style_cache_map[style_name]
		style_ascii_dict, _style_alphabet_unused, declared_height = characters_dict[style_name]

		preprocessed: Dict[str, List[str]] = {}
		per_glyph_max_widths: Dict[str, int] = {}
		per_glyph_heights: Dict[str, int] = {}

		for char_key, glyph_text in style_ascii_dict.items():
			lines = _clean_and_measure_glyph(glyph_text)
			lines = _left_trim_common(lines)
			preprocessed[char_key] = lines
			per_glyph_heights[char_key] = len(lines)
			per_glyph_max_widths[char_key] = max((len(ls.rstrip(' ')) for ls in lines), default=0)

		true_max_width = max(per_glyph_max_widths.values() or [1])
		true_max_height = max(per_glyph_heights.values() or [1])

		declared_height_int = int(declared_height) if isinstance(declared_height, int) else 0
		target_height = max(true_max_height, declared_height_int if declared_height_int > 0 else 0)
		target_width = max(1, true_max_width)

		split_map: Dict[str, List[str]] = {}
		for char_key, lines in preprocessed.items():
			rect = _center_pad_rect(lines, target_width=target_width, target_height=target_height)
			split_map[char_key] = rect

		info_dict = {'split': split_map, 'height': target_height, 'width': target_width}
		style_cache_map[style_name] = info_dict
		return info_dict


	def render_vertical_join(blocks_lines: List[List[str]], target_height: int, spacing_size: int) -> str:
		if not blocks_lines:
			return ''
		max_height = max(target_height, *(len(lines_list) for lines_list in blocks_lines))
		normalized_blocks: List[List[str]] = []
		for glyph_lines in blocks_lines:
			if len(glyph_lines) < max_height:
				# Be defensive if an empty list accidentally appears
				line_width = len(glyph_lines[0]) if (glyph_lines and glyph_lines[0] is not None) else 0
				padding = [' ' * line_width] * (max_height - len(glyph_lines))
				glyph_lines = glyph_lines + padding
			normalized_blocks.append(glyph_lines)
		# Clamp spacing to a reasonable range to avoid extreme memory/output growth
		separator_string = ' ' * max(0, min(32, int(spacing_size)))
		return '\n'.join(
			separator_string.join(block[row_index] for block in normalized_blocks) for row_index in range(max_height)
		)

	def render_vertical_stack(blocks_lines: List[List[str]], target_width: int, spacing_size: int) -> str:
		# Stack glyph rectangles top-to-bottom, inserting spacing_size blank rows between glyphs.
		# spacing_size==0 => tight stack (original behavior)
		if not blocks_lines:
			return ''
		blank_row = ' ' * max(1, int(target_width))
		# Clamp spacing to a reasonable range to avoid extreme tall outputs
		sep = [blank_row] * max(0, min(32, int(spacing_size)))
		lines: List[str] = []
		last_index = len(blocks_lines) - 1
		for idx, rect_lines in enumerate(blocks_lines):
			lines.extend(rect_lines)
			if idx != last_index and sep:
				lines.extend(sep)
		return '\n'.join(lines)


	def resolve_char_key(input_char: str, split_map: Dict[str, List[str]]) -> Optional[str]:
		if input_char in split_map:
			return input_char
		lower_char = input_char.lower()
		upper_char = input_char.upper()
		if lower_char in split_map:
			return lower_char
		if upper_char in split_map:
			return upper_char
		if input_char == ' ':
			for candidate_key in ('sp', 'space'):
				if candidate_key in split_map:
					return candidate_key
			if ' ' in split_map:
				return ' '
		if input_char == '.':
			for candidate_key in ('dot', '.'):
				if candidate_key in split_map:
					return candidate_key
		if input_char == '\t':
			for candidate_key in ('sp', 'space', ' '):
				if candidate_key in split_map:
					return candidate_key
			return None
		if input_char in ('\n', '\r'):
			for candidate_key in ('sp', 'space', ' '):
				if candidate_key in split_map:
					return candidate_key
			return None
		return None


	def render_ascii(input_text: str, style_name: str, placement_mode: str, spacing_size: int) -> str:
		cache_key = (style_name, placement_mode, input_text, spacing_size)
		if cache_key in render_cache_map:
			return render_cache_map[cache_key]
		style_cache = prepare_style_cache(style_name)
		split_map: Dict[str, List[str]] = style_cache['split']  # type: ignore[assignment]
		target_height = style_cache['height']  # type: ignore[assignment]

		glyph_blocks: List[List[str]] = []
		for input_char in input_text:
			resolved_key = resolve_char_key(input_char, split_map)
			if resolved_key is None:
				continue
			try:
				glyph_blocks.append(split_map[resolved_key])
			except Exception:
				continue

		if not glyph_blocks:
			render_cache_map[cache_key] = ''
			return ''

		# Clamp spacing defensively
		_safe_spacing = max(0, min(32, int(spacing_size)))

		if placement_mode == 'vertical':
			# New: apply vertical spacing (blank rows) between stacked glyphs
			target_width = int(style_cache.get('width', 1))  # type: ignore[arg-type]
			rendered_text = render_vertical_stack(
				glyph_blocks,
				target_width=target_width,
				spacing_size=_safe_spacing
			)
			render_cache_map[cache_key] = rendered_text
			return rendered_text
		else:
			final_target_height = int(target_height) if isinstance(target_height, int) else 0
			rendered_text = render_vertical_join(glyph_blocks, final_target_height, _safe_spacing)
			render_cache_map[cache_key] = rendered_text
			return rendered_text

	def compute_auto_spacing(style_name: str) -> int:
		style_cache = prepare_style_cache(style_name)
		style_width_value = max(1, int(style_cache.get('width', 1)))  # type: ignore[arg-type]
		auto_value = max(1, min(6, style_width_value // 4))
		return int(auto_value)

	def set_scale_silently(scale: ttk.Scale, setter, value: int) -> None:
		nonlocal updating_ui
		try:
			updating_ui = True
			orig = scale.cget('command')
			scale.configure(command=None)
			scale.set(value)
			setter(value)
		finally:
			scale.configure(command=orig)
			updating_ui = False

	# ---------- popup window ----------
	if hasattr(app, 'make_pop_ups_window') and callable(app.make_pop_ups_window):
		decorators_root = app.make_pop_ups_window(lambda: None, custom_title=(getattr(app, 'title_struct', '') + 'Text decorators'))
	else:
		decorators_root = tk.Toplevel(getattr(app, 'root', None) or getattr(app, 'tk', None))
		decorators_root.title(getattr(app, 'title_struct', '') + 'Text decorators')

	decorators_root.minsize(860, 600)
	decorators_root.grid_columnconfigure(0, weight=1)
	decorators_root.grid_rowconfigure(2, weight=1)
	validate_styles_once()

	# ---------- top controls (ttk.Notebook with tabs) ----------
	top_controls_frame = tk.Frame(decorators_root)
	top_controls_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=(8, 0))
	top_controls_frame.grid_columnconfigure(0, weight=1)

	placement_mode_var = tk.StringVar(value='horizontal')
	spacing_size_var = tk.IntVar(value=2)
	live_preview_var = tk.BooleanVar(value=True)
	auto_spacing_var = tk.BooleanVar(value=True)
	focus_output_after_render_var = tk.BooleanVar(value=True)

	# Options (text rendering)
	preserve_case_var = tk.BooleanVar(value=False)
	auto_replace_unsupported_var = tk.BooleanVar(value=False)
	expand_tabs_var = tk.BooleanVar(value=True)
	tab_size_var = tk.IntVar(value=4)
	wrap_output_var = tk.BooleanVar(value=False)

	# Window/layout controls (avoid global app options like transparency / global topmost here)
	window_lock_min_size_var = tk.BooleanVar(value=True)
	window_lock_resizable_var = tk.BooleanVar(value=True)
	window_compact_var = tk.BooleanVar(value=False)

	# live helpers (defined early so later callbacks can use them safely)
	live_after_id: Optional[str] = None
	# Use an indirection so we don't capture render_now before it's defined.
	render_callable = (lambda: None)


	def schedule_live_render() -> None:
		nonlocal live_after_id
		if not live_preview_var.get() or updating_ui:
			return
		try:
			if live_after_id:
				decorators_root.after_cancel(live_after_id)
		except Exception:
			pass
		decorators_root.after_cancel(live_after_id) if live_after_id else None
		# Schedule the current render callback (bound after render_now is defined)
		live_after_id = decorators_root.after(120, render_callable)


	def render_live_if_needed(_event=None) -> None:
		if updating_ui or text_input_textbox is None:
			return
		current_input_text = text_input_textbox.get('1.0', tk.END)
		if len(current_input_text) <= 160 and live_preview_var.get():
			# Call through the indirection so we don't reference render_now before it exists
			render_callable()
		else:
			schedule_live_render()

	ctrl_nb = ttk.Notebook(top_controls_frame)
	ctrl_nb.grid(row=0, column=0, sticky='ew')

	# Build tabs
	style_tab = tk.Frame(ctrl_nb)
	layout_tab = tk.Frame(ctrl_nb)
	preview_tab = tk.Frame(ctrl_nb)
	options_tab = tk.Frame(ctrl_nb)
	tools_tab = tk.Frame(ctrl_nb)
	transforms_tab = tk.Frame(ctrl_nb)
	outport_tab = tk.Frame(ctrl_nb)
	window_tab = tk.Frame(ctrl_nb)

	for t in (style_tab, layout_tab, preview_tab, options_tab, tools_tab, transforms_tab, outport_tab, window_tab):
		t.grid_columnconfigure(0, weight=1)

	ctrl_nb.add(style_tab, text='Style')
	ctrl_nb.add(layout_tab, text='Layout')
	ctrl_nb.add(preview_tab, text='Preview')
	ctrl_nb.add(options_tab, text='Options')
	ctrl_nb.add(tools_tab, text='Tools')
	ctrl_nb.add(transforms_tab, text='Transforms')
	ctrl_nb.add(outport_tab, text='Outport')
	ctrl_nb.add(window_tab, text='Window')

	# --- Style tab (grouped) ---
	style_group = ttk.LabelFrame(style_tab, text='Font Style')
	style_group.grid(row=0, column=0, sticky='ew', padx=8, pady=8)
	for c in range(6):
		style_group.grid_columnconfigure(c, weight=0)
	style_group.grid_columnconfigure(5, weight=1)

	style_label = ttk.Label(style_group, text='Style:')
	style_combo = ttk.Combobox(style_group, values=available_styles, state='readonly', width=22)
	style_combo.set(chosen_style)

	def change_style_ui(_evt=None) -> None:
		nonlocal chosen_style
		chosen_style = style_combo.get()
		render_cache_map.clear()
		if auto_spacing_var.get():
			try:
				new_auto = compute_auto_spacing(chosen_style)
				set_scale_silently(spacing_scale_widget, spacing_size_var.set, new_auto)
			except Exception:
				pass
		render_live_if_needed()

	style_combo.bind('<<ComboboxSelected>>', change_style_ui)

	def prefer_builder_make_rich(parent) -> Tuple[tk.Frame, tk.Text, ttk.Scrollbar]:
		if hasattr(app, 'ui_builders') and hasattr(app.ui_builders, 'make_rich_textbox'):
			return app.ui_builders.make_rich_textbox(parent)
		if hasattr(app, 'make_rich_textbox'):
			return app.make_rich_textbox(parent)
		container_frame = tk.Frame(parent)
		text_widget = tk.Text(container_frame)
		y_scrollbar = ttk.Scrollbar(container_frame, orient='vertical', command=text_widget.yview)
		text_widget.configure(yscrollcommand=y_scrollbar.set)
		y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		text_widget.pack(fill=tk.BOTH, expand=True)
		container_frame.pack(fill=tk.BOTH, expand=True)
		return container_frame, text_widget, y_scrollbar

	def show_supported_characters() -> None:
		# Open the combined preview window focused on "Chars" tab
		preview_style_both(initial_tab='Chars')

	def preview_style_alphabet() -> None:
		# Open the combined preview window focused on "Alphabet" tab
		preview_style_both(initial_tab='Alphabet')

	def preview_style_both(initial_tab: str = 'Alphabet') -> None:
		# Combined preview window with two tabs: Alphabet and Chars
		style_ascii_dict, _alph, _h = characters_dict[chosen_style]

		# Build a best-effort “alphabet” string (single-char keys first)
		single_keys = [k for k in style_ascii_dict.keys() if isinstance(k, str) and len(k) == 1]
		all_chars_source = ''.join(single_keys) if single_keys else ' '.join(map(str, style_ascii_dict.keys()))

		# Build a clean, sorted keys list for the "Chars" tab
		keys_sorted = sorted(style_ascii_dict.keys(), key=lambda k: (len(str(k)) > 1, str(k)))
		chars_text_source = ', '.join(map(str, keys_sorted)) if keys_sorted else '(no keys)'

		# Window
		top = tk.Toplevel(decorators_root)
		try:
			top.title(getattr(app, 'title_struct', '') + f'{chosen_style} preview')
		except Exception:
			top.title(f'{chosen_style} preview')
		top.minsize(720, 480)
		top.grid_columnconfigure(0, weight=1)
		top.grid_rowconfigure(2, weight=1)  # 0=controls, 1=tabs, 2=status

		# Controls row (shared)
		ctrl = ttk.Frame(top)
		ctrl.grid(row=0, column=0, sticky='ew', padx=8, pady=(8, 4))
		for i in range(12):
			ctrl.grid_columnconfigure(i, weight=0)
		ctrl.grid_columnconfigure(11, weight=1)

		# Tabs container
		nb = ttk.Notebook(top)
		nb.grid(row=1, column=0, sticky='nsew', padx=8, pady=(0, 8))

		tab_alpha = ttk.Frame(nb)
		tab_chars = ttk.Frame(nb)
		for t in (tab_alpha, tab_chars):
			t.grid_columnconfigure(0, weight=1)
			t.grid_rowconfigure(0, weight=1)

		nb.add(tab_alpha, text='Alphabet')
		nb.add(tab_chars, text='Chars')

		# Alphabet viewer with scrollbars
		alpha_view = ttk.Frame(tab_alpha)
		alpha_view.grid(row=0, column=0, sticky='nsew')
		alpha_view.grid_columnconfigure(0, weight=1)
		alpha_view.grid_rowconfigure(0, weight=1)

		alpha_text = tk.Text(alpha_view, wrap=tk.NONE)
		alpha_vbar = ttk.Scrollbar(alpha_view, orient='vertical', command=alpha_text.yview)
		alpha_hbar = ttk.Scrollbar(alpha_view, orient='horizontal', command=alpha_text.xview)
		alpha_text.configure(yscrollcommand=alpha_vbar.set, xscrollcommand=alpha_hbar.set, font=('Courier New', 10))
		alpha_text.grid(row=0, column=0, sticky='nsew')
		alpha_vbar.grid(row=0, column=1, sticky='ns')
		alpha_hbar.grid(row=1, column=0, sticky='ew')

		# Chars viewer with scrollbars
		chars_view = ttk.Frame(tab_chars)
		chars_view.grid(row=0, column=0, sticky='nsew')
		chars_view.grid_columnconfigure(0, weight=1)
		chars_view.grid_rowconfigure(0, weight=1)

		chars_text = tk.Text(chars_view, wrap=tk.WORD)
		chars_vbar = ttk.Scrollbar(chars_view, orient='vertical', command=chars_text.yview)
		chars_hbar = ttk.Scrollbar(chars_view, orient='horizontal', command=chars_text.xview)
		chars_text.configure(yscrollcommand=chars_vbar.set, xscrollcommand=chars_hbar.set, font=('Courier New', 10))
		chars_text.grid(row=0, column=0, sticky='nsew')
		chars_vbar.grid(row=0, column=1, sticky='ns')
		chars_hbar.grid(row=1, column=0, sticky='ew')

		# Shared controls
		font_family_var = tk.StringVar(value='Courier New')
		font_size_var = tk.IntVar(value=10)
		placement_var = tk.StringVar(value='horizontal')  # or 'vertical'
		wrap_alpha_var = tk.BooleanVar(value=False)
		wrap_chars_var = tk.BooleanVar(value=True)
		spacing_var = tk.IntVar(
			value=compute_auto_spacing(chosen_style) if auto_spacing_var.get() else max(0, int(spacing_size_var.get())))
		auto_local_spacing_var = tk.BooleanVar(value=True)

		ttk.Label(ctrl, text='Font:').grid(row=0, column=0, padx=(0, 6))
		fonts = ['Courier New', 'Consolas', 'Fira Code', 'DejaVu Sans Mono', 'Lucida Console']
		font_combo = ttk.Combobox(ctrl, values=fonts, state='readonly', width=16, textvariable=font_family_var)
		font_combo.grid(row=0, column=1, padx=(0, 12))

		ttk.Label(ctrl, text='Size:').grid(row=0, column=2, padx=(0, 6))
		size_spin = ttk.Spinbox(ctrl, from_=8, to=24, width=5, textvariable=font_size_var)
		size_spin.grid(row=0, column=3, padx=(0, 12))

		ttk.Label(ctrl, text='Place:').grid(row=0, column=4, padx=(0, 6))
		place_h = ttk.Radiobutton(ctrl, text='Horiz', variable=placement_var, value='horizontal')
		place_v = ttk.Radiobutton(ctrl, text='Vert', variable=placement_var, value='vertical')
		place_h.grid(row=0, column=5, padx=(0, 4))
		place_v.grid(row=0, column=6, padx=(0, 12))

		ttk.Label(ctrl, text='Spacing:').grid(row=0, column=7, padx=(0, 6))
		space_spin = ttk.Spinbox(ctrl, from_=0, to=10, width=4, textvariable=spacing_var)
		space_spin.grid(row=0, column=8, padx=(0, 6))
		auto_btn = ttk.Checkbutton(ctrl, text='Auto', variable=auto_local_spacing_var)
		auto_btn.grid(row=0, column=9, padx=(0, 6))

		wrap_alpha_btn = ttk.Checkbutton(ctrl, text='Wrap (Alphabet)', variable=wrap_alpha_var)
		wrap_alpha_btn.grid(row=0, column=10, padx=(6, 6))
		wrap_chars_btn = ttk.Checkbutton(ctrl, text='Wrap (Chars)', variable=wrap_chars_var)
		wrap_chars_btn.grid(row=0, column=11, padx=(0, 6), sticky='e')

		# Action buttons row 2
		ctrl2 = ttk.Frame(top)
		ctrl2.grid(row=2, column=0, sticky='ew', padx=8, pady=(0, 8))
		for i in range(6):
			ctrl2.grid_columnconfigure(i, weight=0)
		ctrl2.grid_columnconfigure(5, weight=1)

		copy_btn = ttk.Button(ctrl2, text='Copy current')
		save_btn = ttk.Button(ctrl2, text='Save .txt (current)')
		refresh_btn = ttk.Button(ctrl2, text='Refresh')
		status = ttk.Label(ctrl2, text='', anchor='w')

		copy_btn.grid(row=0, column=0, padx=(0, 6))
		save_btn.grid(row=0, column=1, padx=(0, 6))
		refresh_btn.grid(row=0, column=2, padx=(0, 6))
		status.grid(row=0, column=5, sticky='ew')

		def _apply_text_style(widget: tk.Text, wrap_word: bool):
			try:
				widget.configure(
					font=(font_family_var.get(), max(6, int(font_size_var.get()))),
					wrap=(tk.WORD if wrap_word else tk.NONE)
				)
			except Exception:
				pass

		def _compute_spacing():
			sp = spacing_var.get()
			if auto_local_spacing_var.get():
				try:
					return compute_auto_spacing(chosen_style)
				except Exception:
					return sp
			return sp

		def _regenerate_alpha():
			sp = _compute_spacing()
			placement = placement_var.get()
			text = render_ascii(all_chars_source, chosen_style, placement, max(0, int(sp)))
			try:
				alpha_text.configure(state=tk.NORMAL)
				alpha_text.delete('1.0', tk.END)
				_apply_text_style(alpha_text, wrap_alpha_var.get())
				alpha_text.insert('1.0', text.rstrip('\n'))
				alpha_text.see('1.0')
				alpha_text.configure(state=tk.DISABLED)
			except Exception:
				pass
			lines = text.count('\n') + (1 if text else 0)
			status.configure(text=f'Alphabet | Chars: {len(all_chars_source)} | Lines: {lines} | Spacing: {sp} | Placement: {placement}')

		def _regenerate_chars():
			# Show a formatted list of keys; when placement is vertical, show one key per line; else comma-separated
			sp = _compute_spacing()
			placement = placement_var.get()
			if placement == 'vertical':
				txt = '\n'.join(map(str, keys_sorted))
			else:
				txt = ', '.join(map(str, keys_sorted))
			try:
				chars_text.configure(state=tk.NORMAL)
				chars_text.delete('1.0', tk.END)
				_apply_text_style(chars_text, wrap_chars_var.get())
				chars_text.insert('1.0', txt)
				chars_text.see('1.0')
				chars_text.configure(state=tk.DISABLED)
			except Exception:
				pass
			lines = txt.count('\n') + (1 if txt else 0)
			status.configure(text=f'Chars | Keys: {len(keys_sorted)} | Lines: {lines} | Placement: {placement}')

		def _active_is_alpha():
			try:
				return nb.index(nb.select()) == 0
			except Exception:
				return True

		def regenerate_current():
			if _active_is_alpha():
				_regenerate_alpha()
			else:
				_regenerate_chars()

		def do_copy_current():
			try:
				w = alpha_text if _active_is_alpha() else chars_text
				content = w.get('1.0', 'end-1c')
				if not content:
					return
				top.clipboard_clear()
				top.clipboard_append(content)
			except Exception:
				pass

		def do_save_current():
			try:
				w = alpha_text if _active_is_alpha() else chars_text
				content = w.get('1.0', 'end-1c')
				if not content:
					return
				path = filedialog.asksaveasfilename(
					parent=top,
					defaultextension='.txt',
					filetypes=(('Text Files', '*.txt'), ('All Files', '*.*'))
				)
				if path:
					with open(path, 'w', encoding='utf-8') as f:
						f.write(content)
			except Exception:
				pass

		# Wire controls
		for w in (font_combo, size_spin, place_h, place_v, space_spin, auto_btn, wrap_alpha_btn, wrap_chars_btn):
			if hasattr(w, 'configure') and 'command' in w.configure():
				w.configure(command=regenerate_current)
			else:
				try:
					w.bind('<<ComboboxSelected>>', lambda _e=None: regenerate_current())
					w.bind('<KeyRelease>', lambda _e=None: regenerate_current())
				except Exception:
					pass

		copy_btn.configure(command=do_copy_current)
		save_btn.configure(command=do_save_current)
		refresh_btn.configure(command=regenerate_current)
		nb.bind('<<NotebookTabChanged>>', lambda _e=None: regenerate_current())

		# Initial render and tab select
		if (initial_tab or '').lower().startswith('char'):
			try:
				nb.select(tab_chars)
			except Exception:
				pass
		else:
			try:
				nb.select(tab_alpha)
			except Exception:
				pass

		regenerate_current()

	supported_btn = ttk.Button(style_group, text='Chars', command=show_supported_characters)
	preview_btn = ttk.Button(style_group, text='Alphabet', command=preview_style_alphabet)
	style_label.grid(row=0, column=0, padx=(0, 6), pady=4, sticky='w')
	style_combo.grid(row=0, column=1, padx=(0, 16), pady=4, sticky='w')
	supported_btn.grid(row=0, column=2, padx=(0, 10), pady=4)
	preview_btn.grid(row=0, column=3, padx=(0, 10), pady=4)

	# --- Layout tab (grouped) ---
	layout_group = ttk.LabelFrame(layout_tab, text='Placement & Spacing')
	layout_group.grid(row=0, column=0, sticky='ew', padx=8, pady=8)
	for c in range(10):
		layout_group.grid_columnconfigure(c, weight=0)
	layout_group.grid_columnconfigure(9, weight=1)

	placement_label = ttk.Label(layout_group, text='Place:')
	horiz_rb = ttk.Radiobutton(layout_group, text='Horiz', variable=placement_mode_var, value='horizontal')
	vert_rb = ttk.Radiobutton(layout_group, text='Vert', variable=placement_mode_var, value='vertical')

	spacing_label = ttk.Label(layout_group, text='Spacing:')
	def scale_cmd(v: str) -> None:
		if updating_ui:
			return
		try:
			spacing_size_var.set(int(float(v)))
		except Exception:
			return
		if live_preview_var.get():
			schedule_live_render()

	spacing_scale_widget = ttk.Scale(layout_group, from_=0, to=6, length=200, orient='horizontal', command=scale_cmd)
	spacing_scale_widget.set(spacing_size_var.get())
	auto_spacing_cb = ttk.Checkbutton(layout_group, text='Auto', variable=auto_spacing_var, command=render_live_if_needed)

	placement_label.grid(row=0, column=0, padx=(0, 6), pady=4, sticky='w')
	horiz_rb.grid(row=0, column=1, padx=(0, 8), pady=4, sticky='w')
	vert_rb.grid(row=0, column=2, padx=(0, 12), pady=4, sticky='w')
	spacing_label.grid(row=0, column=3, padx=(0, 6), pady=4, sticky='w')
	spacing_scale_widget.grid(row=0, column=4, padx=(0, 10), pady=4, sticky='w')
	auto_spacing_cb.grid(row=0, column=5, padx=(0, 6), pady=4, sticky='w')

	# --- Preview tab ---
	preview_group = ttk.LabelFrame(preview_tab, text='Preview Options')
	preview_group.grid(row=0, column=0, sticky='ew', padx=8, pady=8)
	for c in range(6):
		preview_group.grid_columnconfigure(c, weight=0)
	preview_group.grid_columnconfigure(5, weight=1)

	live_cb = ttk.Checkbutton(preview_group, text='Live', variable=live_preview_var)
	focus_output_cb = ttk.Checkbutton(preview_group, text='Focus Output after render',
									  variable=focus_output_after_render_var)
	render_button = ttk.Button(preview_group, text='Render')

	live_cb.grid(row=0, column=0, padx=(0, 12), pady=4, sticky='w')
	focus_output_cb.grid(row=0, column=1, padx=(0, 12), pady=4, sticky='w')
	render_button.grid(row=0, column=2, padx=(0, 10), pady=4)

# --- Options tab (text rendering) ---
	options_group = ttk.LabelFrame(options_tab, text='Text & Parsing Options')
	options_group.grid(row=0, column=0, sticky='ew', padx=8, pady=8)
	for c in range(8):
		options_group.grid_columnconfigure(c, weight=0)
	options_group.grid_columnconfigure(7, weight=1)

	cb_preserve = ttk.Checkbutton(options_group, text='Preserve case (don’t lowercase input)', variable=preserve_case_var, command=render_live_if_needed)
	cb_autorepl = ttk.Checkbutton(options_group, text='Auto-replace unsupported chars with space', variable=auto_replace_unsupported_var, command=render_live_if_needed)
	cb_wrap_output = ttk.Checkbutton(options_group, text='Wrap Output', variable=wrap_output_var, command=lambda: result_text_widget and result_text_widget.configure(wrap=tk.WORD if wrap_output_var.get() else tk.NONE))
	cb_expand_tabs = ttk.Checkbutton(options_group, text='Expand tabs', variable=expand_tabs_var, command=render_live_if_needed)
	tab_size_label = ttk.Label(options_group, text='Tab size:')
	tab_size_spin = ttk.Spinbox(options_group, from_=2, to=8, increment=1, textvariable=tab_size_var, width=4, command=render_live_if_needed)

	cb_preserve.grid(row=0, column=0, padx=(0, 14), pady=4, sticky='w')
	cb_autorepl.grid(row=0, column=1, padx=(0, 14), pady=4, sticky='w')
	cb_wrap_output.grid(row=0, column=2, padx=(0, 14), pady=4, sticky='w')
	cb_expand_tabs.grid(row=1, column=0, padx=(0, 14), pady=4, sticky='w')
	tab_size_label.grid(row=1, column=1, padx=(0, 6), pady=4, sticky='e')
	tab_size_spin.grid(row=1, column=2, padx=(0, 14), pady=4, sticky='w')

	# --- Tools tab (quick actions) ---
	tools_group = ttk.LabelFrame(tools_tab, text='Quick Input/Output Actions')
	tools_group.grid(row=0, column=0, sticky='ew', padx=8, pady=8)
	for c in range(10):
		tools_group.grid_columnconfigure(c, weight=0)
	tools_group.grid_columnconfigure(9, weight=1)

	def tools_clear_input():
		if text_input_textbox:
			text_input_textbox.delete('1.0', tk.END)
			render_live_if_needed()

	def tools_clear_output():
		if result_text_widget:
			result_text_widget.configure(state=tk.NORMAL)
			result_text_widget.delete('1.0', tk.END)
			result_text_widget.configure(state=tk.DISABLED)

	def tools_use_current():
		if text_input_textbox is None:
			return
		editor_text = ''
		try:
			editor_text = app.EgonTE.get('1.0', 'end-1c')
		except Exception:
			editor_text = ''
		text_input_textbox.delete('1.0', 'end')
		if editor_text:
			text_input_textbox.insert('end', editor_text)
		render_live_if_needed()

	def tools_normalize_spaces():
		if text_input_textbox is None:
			return
		content = text_input_textbox.get('1.0', tk.END)
		lines = [ln.rstrip() for ln in content.splitlines()]
		normalized = '\n'.join(lines)
		text_input_textbox.delete('1.0', tk.END)
		text_input_textbox.insert('1.0', normalized)
		render_live_if_needed()

	def tools_swap_case():
		if text_input_textbox is None:
			return
		content = text_input_textbox.get('1.0', tk.END)
		text_input_textbox.delete('1.0', tk.END)
		text_input_textbox.insert('1.0', content.swapcase())
		render_live_if_needed()

	btn_use_current = ttk.Button(tools_group, text='Use current', command=tools_use_current)
	btn_clear_input = ttk.Button(tools_group, text='Clear input', command=tools_clear_input)
	btn_clear_output = ttk.Button(tools_group, text='Clear output', command=tools_clear_output)
	btn_norm_spaces = ttk.Button(tools_group, text='Trim trailing spaces', command=tools_normalize_spaces)
	btn_swap_case = ttk.Button(tools_group, text='Swap case', command=tools_swap_case)

	btn_use_current.grid(row=0, column=0, padx=(0, 8), pady=4, sticky='w')
	btn_clear_input.grid(row=0, column=1, padx=(0, 8), pady=4, sticky='w')
	btn_clear_output.grid(row=0, column=2, padx=(0, 8), pady=4, sticky='w')
	btn_norm_spaces.grid(row=0, column=3, padx=(0, 8), pady=4, sticky='w')
	btn_swap_case.grid(row=0, column=4, padx=(0, 8), pady=4, sticky='w')

	# --- Transforms tab (apply simple text operations to Input/Output) ---
	tf_group = ttk.LabelFrame(transforms_tab, text='Apply transforms')
	tf_group.grid(row=0, column=0, sticky='ew', padx=8, pady=8)
	for c in range(8):
		tf_group.grid_columnconfigure(c, weight=0)
	tf_group.grid_columnconfigure(7, weight=1)

	target_var = tk.StringVar(value='input')
	ttk.Label(tf_group, text='Target:').grid(row=0, column=0, padx=(0, 8), pady=4, sticky='w')
	ttk.Radiobutton(tf_group, text='Input', variable=target_var, value='input', command=lambda: None).grid(row=0, column=1, pady=4, sticky='w')
	ttk.Radiobutton(tf_group, text='Output', variable=target_var, value='output', command=lambda: None).grid(row=0, column=2, padx=(6, 12), pady=4, sticky='w')

	def _get_target_widget() -> Optional[tk.Text]:
		if target_var.get() == 'output':
			return result_text_widget
		return text_input_textbox

	def _set_text(widget: tk.Text, new_text: str) -> None:
		state = widget.cget('state') if hasattr(widget, 'cget') else 'normal'
		try:
			widget.configure(state=tk.NORMAL)
			widget.delete('1.0', tk.END)
			widget.insert('1.0', new_text)
		finally:
			try:
				widget.configure(state=state)
			except Exception:
				pass

	def tf_reverse_chars():
		tw = _get_target_widget()
		if not tw:
			return
		txt = tw.get('1.0', 'end-1c')
		_set_text(tw, txt[::-1])
		render_live_if_needed()

	def tf_reverse_words():
		tw = _get_target_widget()
		if not tw:
			return
		words = tw.get('1.0', 'end-1c').split()
		_set_text(tw, ' '.join(words[::-1]))
		render_live_if_needed()

	def tf_join_words():
		tw = _get_target_widget()
		if not tw:
			return
		joined = ''.join(tw.get('1.0', 'end-1c').split())
		_set_text(tw, joined)
		render_live_if_needed()

	def tf_toggle_case():
		tw = _get_target_widget()
		if not tw:
			return
		content = tw.get('1.0', 'end-1c')
		newc = content.lower() if content == content.upper() else content.upper()
		_set_text(tw, newc)
		render_live_if_needed()

	def tf_sort_chars():
		tw = _get_target_widget()
		if not tw:
			return
		content = tw.get('1.0', 'end-1c')
		sorted_content = ''.join(sorted(content))
		if content == sorted_content:
			sorted_content = ''.join(sorted(sorted_content, reverse=True))
		_set_text(tw, sorted_content)
		render_live_if_needed()

	def tf_sort_words():
		tw = _get_target_widget()
		if not tw:
			return
		words = tw.get('1.0', 'end-1c').split(' ')
		sorted_words = sorted(words)
		if words == sorted_words:
			sorted_words = sorted(sorted_words, reverse=True)
		_set_text(tw, ' '.join(sorted_words))
		render_live_if_needed()

	def tf_insert_tab():
		tw = _get_target_widget()
		if not tw:
			return
		try:
			spaces_mode = bool(getattr(app, 'indent_method').get() == 'space')  # type: ignore[attr-defined]
		except Exception:
			spaces_mode = False
		tw.insert(tw.index('insert'), ('    ' if spaces_mode else '\t'))
		render_live_if_needed()

	btn_rev_chars = ttk.Button(tf_group, text='Reverse chars', command=tf_reverse_chars)
	btn_rev_words = ttk.Button(tf_group, text='Reverse words', command=tf_reverse_words)
	btn_join_words = ttk.Button(tf_group, text='Join words', command=tf_join_words)
	btn_toggle_case = ttk.Button(tf_group, text='Toggle lower/UPPER', command=tf_toggle_case)
	btn_sort_chars = ttk.Button(tf_group, text='Sort chars', command=tf_sort_chars)
	btn_sort_words = ttk.Button(tf_group, text='Sort words', command=tf_sort_words)
	btn_insert_tab = ttk.Button(tf_group, text='Insert TAB', command=tf_insert_tab)

	btn_rev_chars.grid(row=1, column=0, padx=4, pady=6, sticky='w')
	btn_rev_words.grid(row=1, column=1, padx=4, pady=6, sticky='w')
	btn_join_words.grid(row=1, column=2, padx=4, pady=6, sticky='w')
	btn_toggle_case.grid(row=1, column=3, padx=4, pady=6, sticky='w')
	btn_sort_chars.grid(row=1, column=4, padx=4, pady=6, sticky='w')
	btn_sort_words.grid(row=1, column=5, padx=4, pady=6, sticky='w')
	btn_insert_tab.grid(row=1, column=6, padx=4, pady=6, sticky='w')

	# --- Outport tab (Email / File generator) ---
	op_group = ttk.LabelFrame(outport_tab, text='Send / Export')
	op_group.grid(row=0, column=0, sticky='ew', padx=8, pady=8)
	for c in range(6):
		op_group.grid_columnconfigure(c, weight=0)
	op_group.grid_columnconfigure(5, weight=1)

	out_hint = ttk.Label(op_group, text='Send or export the rendered Output')
	out_insert_first = tk.BooleanVar(value=True)
	cb_insert_first = ttk.Checkbutton(op_group, text='Insert into editor first', variable=out_insert_first)

	def insert_result_at_cursor() -> None:
		if result_text_widget is None:
			return
		content = result_text_widget.get('1.0', 'end-1c')
		if not content:
			return
		try:
			app.EgonTE.insert(app.EgonTE.index('insert'), content)
		except Exception:
			pass

	def copy_result_to_clipboard() -> None:
		if result_text_widget is None:
			return
		content = result_text_widget.get('1.0', 'end-1c')
		if not content:
			return
		try:
			decorators_root.clipboard_clear()
			decorators_root.clipboard_append(content)
		except Exception:
			pass

	def save_result_to_file() -> None:
		if result_text_widget is None:
			return
		content = result_text_widget.get('1.0', 'end-1c')
		if not content:
			return
		try:
			path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=(('Text Files', '*.txt'), ('All Files', '*.*')))
			if path:
				with open(path, 'w', encoding='utf-8') as f:
					f.write(content)
		except Exception:
			pass

	def out_to_email():
		if out_insert_first.get():
			insert_result_at_cursor()
		try:
			app.send_email()
		except Exception:
			copy_result_to_clipboard()

	def out_to_filegen():
		if out_insert_first.get():
			insert_result_at_cursor()
		try:
			app.file_template_generator()
		except Exception:
			save_result_to_file()

	btn_out_email = ttk.Button(op_group, text='Open Email tool', command=out_to_email)
	btn_out_file = ttk.Button(op_group, text='Open File generator', command=out_to_filegen)

	out_hint.grid(row=0, column=0, padx=(0, 12), pady=4, sticky='w')
	cb_insert_first.grid(row=0, column=1, padx=(0, 12), pady=4, sticky='w')
	btn_out_email.grid(row=1, column=0, padx=(0, 10), pady=6, sticky='w')
	btn_out_file.grid(row=1, column=1, padx=(0, 10), pady=6, sticky='w')

	# --- Window tab (window layout & behavior) ---
	win_group = ttk.LabelFrame(window_tab, text='Window & Layout Options (local)')
	win_group.grid(row=0, column=0, sticky='ew', padx=8, pady=8)
	for c in range(10):
		win_group.grid_columnconfigure(c, weight=0)
	win_group.grid_columnconfigure(9, weight=1)

	def apply_min_size_lock():
		try:
			if window_lock_min_size_var.get():
				decorators_root.update_idletasks()
				w, h = decorators_root.winfo_width(), decorators_root.winfo_height()
				if w > 1 and h > 1:
					decorators_root.minsize(w, h)
			else:
				decorators_root.minsize(1, 1)
		except Exception:
			pass

	def apply_resizable():
		try:
			flag = bool(window_lock_resizable_var.get())
			decorators_root.resizable(flag, flag)
		except Exception:
			pass

	def center_window():
		try:
			decorators_root.update_idletasks()
			w = decorators_root.winfo_width()
			h = decorators_root.winfo_height()
			sw = decorators_root.winfo_screenwidth()
			sh = decorators_root.winfo_screenheight()
			x = max(0, (sw - w) // 2)
			y = max(0, (sh - h) // 2)
			decorators_root.geometry(f'+{x}+{y}')
		except Exception:
			pass

	def swap_input_output_tabs():
		try:
			tabs = nb.tabs()
			if len(tabs) >= 2:
				titles = [nb.tab(t, 'text') for t in tabs]
				if titles and titles[0] == 'Input':
					nb.insert(0, tabs[1])
				else:
					nb.insert(0, tabs[1])  # toggle again puts Input first
		except Exception:
			pass

	def apply_compact():
		pad = (2 if window_compact_var.get() else 8)
		try:
			for group in (style_group, layout_group, preview_group, options_group, tools_group, tf_group, op_group, win_group):
				group.grid_configure(padx=pad, pady=pad)
		except Exception:
			pass

	cb_lock_min = ttk.Checkbutton(win_group, text='Lock min size to current', variable=window_lock_min_size_var, command=apply_min_size_lock)
	cb_resizable = ttk.Checkbutton(win_group, text='Lock resizable (both axes)', variable=window_lock_resizable_var, command=apply_resizable)
	cb_compact = ttk.Checkbutton(win_group, text='Compact mode (reduced padding)', variable=window_compact_var, command=apply_compact)
	btn_center = ttk.Button(win_group, text='Center window', command=center_window)
	btn_swap_tabs = ttk.Button(win_group, text='Swap Input/Output tabs', command=swap_input_output_tabs)
	# New: layout mode (stacked tabs vs side-by-side)
	layout_mode_var = tk.StringVar(value='stack')  # 'stack' or 'side'

	# Remember where content normally lives (so we can restore cleanly)
	# These are the inner containers that actually hold the widgets.
	original_input_container = None
	original_output_container = None

	def apply_layout_mode():
		nonlocal layout_mode_var, original_input_container, original_output_container, text_input_textbox, result_text_widget
		mode = layout_mode_var.get()
		try:
			# Ensure we have the inner containers (original NB ones)
			if original_input_container is None:
				original_input_container = nb_input_frame
			if original_output_container is None:
				original_output_container = nb_output_frame

			if mode == 'side':
				# Hide Notebook
				try:
					nb.grid_remove()
				except Exception:
					pass

				# Sync side widgets with NB content
				try:
					# Input content
					side_input_text.configure(state=tk.NORMAL)
					side_input_text.delete('1.0', 'end')
					side_input_text.insert('1.0', nb_input_text.get('1.0', 'end-1c'))
					# Output content
					side_output_text.configure(state=tk.NORMAL)
					side_output_text.delete('1.0', 'end')
					side_output_text.insert('1.0', nb_output_text.get('1.0', 'end-1c'))
					side_output_text.configure(state=tk.DISABLED)
				except Exception:
					pass

				# Place holders in two equal columns (holders use grid; their children use pack internally)
				main_content_frame.grid_columnconfigure(0, weight=1)
				main_content_frame.grid_columnconfigure(1, weight=1)
				main_content_frame.grid_rowconfigure(0, weight=1)
				try:
					side_input_holder.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
					side_output_holder.grid(row=0, column=1, sticky='nsew', padx=(5, 0))
				except Exception:
					pass

				# Ensure inner packed frames are visible inside holders
				try:
					side_input_frame.pack(fill=tk.BOTH, expand=True)
				except Exception:
					pass
				try:
					side_output_frame.pack(fill=tk.BOTH, expand=True)
				except Exception:
					pass

				# Switch active references to side widgets
				text_input_textbox = side_input_text
				result_text_widget = side_output_text
				_bind_input_textbox(text_input_textbox)

			else:
				# Restore stacked mode

				# Hide side holders
				try:
					side_input_holder.grid_forget()
				except Exception:
					pass
				try:
					side_output_holder.grid_forget()
				except Exception:
					pass

				# Before switching back, sync content from side → stacked
				try:
					# Input (side → NB)
					nb_input_text.delete('1.0', 'end')
					nb_input_text.insert('1.0', side_input_text.get('1.0', 'end-1c'))
				except Exception:
					pass
				try:
					# Output (side → NB)
					_side_was = side_output_text.cget('state') if hasattr(side_output_text, 'cget') else 'normal'
					side_output_text.configure(state=tk.NORMAL)
					nb_output_text.configure(state=tk.NORMAL)
					nb_output_text.delete('1.0', 'end')
					nb_output_text.insert('1.0', side_output_text.get('1.0', 'end-1c'))
					nb_output_text.configure(state=tk.DISABLED)
					# restore side state
					try:
						side_output_text.configure(state=_side_was)
					except Exception:
						side_output_text.configure(state=tk.DISABLED)
				except Exception:
					pass

				# Ensure notebook host expands and is visible
				main_content_frame.grid_columnconfigure(0, weight=1)
				main_content_frame.grid_columnconfigure(1, weight=0)
				main_content_frame.grid_rowconfigure(0, weight=1)
				nb.grid(row=0, column=0, sticky='nsew')

				# Switch active references back to NB widgets
				text_input_textbox = nb_input_text
				result_text_widget = nb_output_text
				_bind_input_textbox(text_input_textbox)

			# Final layout pass
			try:
				decorators_root.update_idletasks()
			except Exception:
				pass
		except Exception:
			pass


	ttk.Label(win_group, text='Editor layout:').grid(row=2, column=0, padx=(0, 10), pady=4, sticky='w')
	layout_rb_stack = ttk.Radiobutton(win_group, text='Stacked (tabs)', variable=layout_mode_var, value='stack',
									  command=apply_layout_mode)
	layout_rb_side = ttk.Radiobutton(win_group, text='Side by side', variable=layout_mode_var, value='side',
									 command=apply_layout_mode)
	layout_rb_stack.grid(row=2, column=1, padx=(0, 6), pady=4, sticky='w')
	layout_rb_side.grid(row=2, column=2, padx=(0, 10), pady=4, sticky='w')

	cb_lock_min.grid(row=0, column=0, padx=(0, 10), pady=4, sticky='w')
	cb_resizable.grid(row=0, column=1, padx=(0, 10), pady=4, sticky='w')
	cb_compact.grid(row=0, column=2, padx=(0, 10), pady=4, sticky='w')
	btn_center.grid(row=0, column=3, padx=(0, 10), pady=4, sticky='w')
	btn_swap_tabs.grid(row=0, column=4, padx=(0, 10), pady=4, sticky='w')

	# ---------- main content notebook ----------
	main_content_frame = tk.Frame(decorators_root)
	main_content_frame.grid(row=2, column=0, sticky='nsew', padx=10, pady=10)
	main_content_frame.grid_columnconfigure(0, weight=1)
	main_content_frame.grid_rowconfigure(0, weight=1)

	nb = ttk.Notebook(main_content_frame)
	nb.grid(row=0, column=0, sticky='nsew')

	input_tab = tk.Frame(nb)
	output_tab = tk.Frame(nb)
	for t in (input_tab, output_tab):
		t.grid_columnconfigure(0, weight=1)
		t.grid_rowconfigure(0, weight=1)
	nb.add(input_tab, text='Input')
	nb.add(output_tab, text='Output')

	# Input tab widgets
	text_input_frame, text_input_textbox, text_input_scrollbar = prefer_builder_make_rich(input_tab)
	text_input_textbox.configure(font=('Courier New', 10))
	# The fallback builder may have used pack() on the returned container; cancel it before using grid().
	try:
		text_input_frame.pack_forget()
	except Exception:
		pass
	text_input_frame.grid(row=0, column=0, sticky='nsew')

	# Keep NB (stacked) references so we can switch back and forth
	nb_input_frame = text_input_frame
	nb_input_text = text_input_textbox


	# Live typing/paste bindings (debounced)
	def _on_input_key(_e=None):
		# Debounce frequent typing; guard against programmatic updates
		if not live_preview_var.get() or updating_ui:
			return
		schedule_live_render()


	def _on_input_edit(_e=None):
		# For edits that don't emit KeyRelease (e.g., paste via menu)
		if not live_preview_var.get() or updating_ui:
			return
		# Use a very short defer to ensure widget text is updated first
		try:
			decorators_root.after(1, render_live_if_needed)
		except Exception:
			pass


	def _bind_input_textbox(widget: tk.Text):
		try:
			widget.bind('<KeyRelease>', _on_input_key)
			for virtual_event in ('<<Paste>>', '<<Cut>>', '<<Undo>>', '<<Redo>>'):
				widget.bind(virtual_event, _on_input_edit)
			widget.bind('<ButtonRelease-2>', _on_input_edit)
			# QoL: Enter to render when Live is off
			widget.bind('<Return>', lambda _e=None: (not live_preview_var.get()) and render_now())
		except Exception:
			pass


	_bind_input_textbox(text_input_textbox)

	try:
		# Key typing
		text_input_textbox.bind('<KeyRelease>', _on_input_key)
		# Clipboard and edit operations
		for virtual_event in ('<<Paste>>', '<<Cut>>', '<<Undo>>', '<<Redo>>'):
			text_input_textbox.bind(virtual_event, _on_input_edit)
		# Middle-click paste on X11, and drop actions often end with ButtonRelease
		text_input_textbox.bind('<ButtonRelease-2>', _on_input_edit)
	except Exception:
		pass
	# Output tab widgets
	result_container_frame, result_text_widget, result_scrollbar_widget = prefer_builder_make_rich(output_tab)
	# The fallback builder may have used pack() on the returned container; cancel it before using grid().
	try:
		result_container_frame.pack_forget()
	except Exception:
		pass
	result_container_frame.grid(row=0, column=0, sticky='nsew')
	result_text_widget.configure(font=('Courier New', 10), wrap=tk.NONE)
	try:
		result_scrollbar_widget.config(orient='vertical', command=result_text_widget.yview)
		result_text_widget.configure(yscrollcommand=result_scrollbar_widget.set)
	except Exception:
		pass
	result_hscroll_widget = ttk.Scrollbar(result_container_frame, orient='horizontal', command=result_text_widget.xview)
	try:
		result_text_widget.configure(xscrollcommand=result_hscroll_widget.set)
		result_hscroll_widget.pack(side=tk.BOTTOM, fill=tk.X)
	except Exception:
		pass

	# Keep NB (stacked) references so we can switch back and forth
	nb_output_frame = result_container_frame
	nb_output_text = result_text_widget

	# --- Dedicated side-by-side containers (safe with geometry managers) ---
	# Holders are gridded in main_content_frame; inside each holder, the builder will pack the inner container.
	side_input_holder = tk.Frame(main_content_frame)
	side_output_holder = tk.Frame(main_content_frame)

	# Build Input (side) inside its holder (builder may pack within holder – that's OK)
	side_input_frame, side_input_text, side_input_scroll = prefer_builder_make_rich(side_input_holder)
	try:
		side_input_frame.pack_forget()  # in case builder auto-packed; we'll let it pack again when visible
	except Exception:
		pass
	side_input_text.configure(font=('Courier New', 10))

	# Build Output (side) inside its holder
	side_output_frame, side_output_text, side_output_vscroll = prefer_builder_make_rich(side_output_holder)
	try:
		side_output_frame.pack_forget()
	except Exception:
		pass
	side_output_text.configure(font=('Courier New', 10), wrap=tk.NONE)
	try:
		side_output_hscroll = ttk.Scrollbar(side_output_frame, orient='horizontal', command=side_output_text.xview)
		side_output_text.configure(xscrollcommand=side_output_hscroll.set)
		side_output_hscroll.pack(side=tk.BOTTOM, fill=tk.X)
	except Exception:
		pass


	# lock min size after layout (initial)
	def set_initial_minsize() -> None:
		try:
			decorators_root.update_idletasks()
			w, h = decorators_root.winfo_width(), decorators_root.winfo_height()
			if w > 1 and h > 1 and window_lock_min_size_var.get():
				decorators_root.minsize(w, h)
		except Exception:
			pass
	decorators_root.after(150, set_initial_minsize)

	# ---------- live & render logic ----------
	def set_result_actions_state(_enabled: bool) -> None:
		# No outside-of-tabs buttons to toggle; left as a stub for compatibility.
		return

	def copy_from_editor_to_input() -> None:
		if text_input_textbox is None:
			return
		editor_text = ''
		try:
			editor_text = app.EgonTE.get('1.0', 'end-1c')
		except Exception:
			editor_text = ''
		text_input_textbox.delete('1.0', 'end')
		if editor_text:
			text_input_textbox.insert('end', editor_text)
		render_live_if_needed()

	def _get_input_text_processed() -> str:
		# raw input
		raw = text_input_textbox.get('1.0', tk.END)
		# expand tabs if requested
		if expand_tabs_var.get():
			try:
				tabw = max(1, int(tab_size_var.get()))
			except Exception:
				tabw = 4
			raw = raw.expandtabs(tabw)
		# strip trailing newline used by tk
		raw = raw.rstrip('\n')
		# preserve or normalize case
		return raw if preserve_case_var.get() else raw.lower()


	def render_now() -> None:
		nonlocal updating_ui
		if text_input_textbox is None or result_text_widget is None:
			return

		raw_input_text = text_input_textbox.get('1.0', tk.END).strip('\n')
		# Allow empty input: clear output and disable actions (no error)
		if raw_input_text == '':
			try:
				updating_ui = True
				result_text_widget.configure(state=tk.NORMAL)
				result_text_widget.delete('1.0', tk.END)
				result_text_widget.configure(state=tk.DISABLED)
			finally:
				updating_ui = False
			set_result_actions_state(False)
			return

		normalized_text = _get_input_text_processed()

		try:
			if len(normalized_text) > 12000:
				if not messagebox.askyesno('EgonTE', 'Input is very large and may be slow to render.\nProceed?', icon='warning'):
					return
		except Exception:
			pass

		current_style_cache = prepare_style_cache(chosen_style)
		split_map: Dict[str, List[str]] = current_style_cache['split']  # type: ignore[assignment]

		unsupported_chars: List[str] = []
		for ch in normalized_text:
			if resolve_char_key(ch, split_map) is None:
				unsupported_chars.append(ch)

		if unsupported_chars:
			if auto_replace_unsupported_var.get():
				normalized_text = ''.join(ch if resolve_char_key(ch, split_map) is not None else ' ' for ch in normalized_text)
			else:
				try:
					msg = 'Unsupported characters found:\n' + ', '.join(sorted(set(unsupported_chars))) + '\n\nReplace them with spaces and continue?'
					if not messagebox.askyesno('EgonTE', msg):
						return
				except Exception:
					return
				normalized_text = ''.join(ch if resolve_char_key(ch, split_map) is not None else ' ' for ch in normalized_text)

		if auto_spacing_var.get():
			try:
				set_scale_silently(spacing_scale_widget, spacing_size_var.set, compute_auto_spacing(chosen_style))
			except Exception:
				pass
		char_spacing = max(0, int(spacing_size_var.get()))
		placement = placement_mode_var.get()

		rendered = render_ascii(normalized_text, chosen_style, placement, char_spacing)
		if not rendered:
			try:
				updating_ui = True
				result_text_widget.configure(state=tk.NORMAL)
				result_text_widget.delete('1.0', tk.END)
				result_text_widget.configure(state=tk.DISABLED)
			finally:
				updating_ui = False
			set_result_actions_state(False)
			return

		# Only auto-focus Output when Live is OFF and when stacked (tabs) layout is active
		if focus_output_after_render_var.get() and (not live_preview_var.get()):
			try:
				if layout_mode_var.get() == 'stack':
					nb.select(output_tab)
			except Exception:
				pass

		try:
			updating_ui = True
			result_text_widget.configure(state=tk.NORMAL)
			result_text_widget.delete('1.0', tk.END)
			result_text_widget.configure(wrap=(tk.WORD if wrap_output_var.get() else tk.NONE))
			result_text_widget.insert('1.0', rendered.rstrip('\n'))
			result_text_widget.see('1.0')
			result_text_widget.configure(state=tk.DISABLED)
		finally:
			updating_ui = False


		set_result_actions_state(True)

	# Bind the indirection to the real renderer now that it exists
	render_callable = render_now

	# wiring (tab-contained controls only)
	render_button.configure(command=render_now)
	# Helper: enable/disable "Focus Output" while Live is toggled
	def _sync_focus_option_state():
		try:
			focus_output_cb.configure(state=('disabled' if live_preview_var.get() else 'normal'))
		except Exception:
			pass

	# preview updates
	horiz_rb.configure(command=render_live_if_needed)
	vert_rb.configure(command=render_live_if_needed)
	auto_spacing_cb.configure(command=render_live_if_needed)
	live_cb.configure(command=lambda: (_sync_focus_option_state(), render_live_if_needed()))

	# quality-of-life: Enter to render when Live is off
	def on_return(_e=None):
		if not live_preview_var.get():
			render_now()
	# text_input_textbox.bind('<Return>', on_return)

	# re-render on tab size spinbox manual edits (if typing)
	def on_tab_size_key(_e=None):
		schedule_live_render()
	tab_size_spin.bind('<KeyRelease>', on_tab_size_key)

	# refresh output wrap toggle
	def on_wrap_toggle():
		try:
			result_text_widget.configure(wrap=(tk.WORD if wrap_output_var.get() else tk.NONE))
		except Exception:
			pass
	cb_wrap_output.configure(command=lambda: (on_wrap_toggle(), render_live_if_needed()))

	# apply initial window layout settings (local)
	apply_min_size_lock()
	apply_resizable()
	apply_compact()
	apply_layout_mode()
	_sync_focus_option_state()

	# Initial render to initialize Output in stacked mode (so side-by-side has content to mirror)
	try:
		decorators_root.after(10, render_now)
	except Exception:
		pass

	# initial min-size after layout if requested
	decorators_root.update_idletasks()
