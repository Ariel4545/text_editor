import tkinter as tk
from tkinter import Toplevel, Frame, Button, Label
from string import ascii_uppercase, ascii_lowercase
from datetime import datetime
import os
from time import monotonic

try:
	from large_variables import characters_str, sym_n, syn_only
except Exception:
	characters_str = tuple('QWERTYUIOPASDFGHJKLZXCVBNM')
	sym_n = ()
	syn_only = ()


def make_owner_popup(app, title_text):
	try:
		return app.make_pop_ups_window(lambda: None, custom_title=title_text)
	except Exception:
		parent_widget = getattr(app, 'tk', None) or getattr(app, 'root', None)
		if not isinstance(parent_widget, tk.Misc):
			parent_widget = tk._get_default_root() or tk.Tk()
		popup_window = tk.Toplevel(parent_widget)
		popup_window.title(title_text)
		return popup_window


def open_virtual_keyboard(app):
	title_text = 'Virtual Keyboard'
	keyboard_root = make_owner_popup(app, title_text)

	# Keep original callback (so we can restore on close)
	_original_on_vk_settings_changed = getattr(app, 'on_vk_settings_changed', None)

	try:
		app.make_tm(keyboard_root)
	except Exception:
		pass

	try:
		keyboard_root.attributes('-alpha', app.st_value)
	except Exception:
		pass

	try:
		if app.limit_w_s.get():
			keyboard_root.resizable(False, False)
	except Exception:
		pass

	try:
		if app.night_mode.get():
			keyboard_root.configure(bg='black')
		else:
			keyboard_root.configure(bg='white')
	except Exception:
		keyboard_root.configure(bg='black')

	try:
		app.opened_windows.append(keyboard_root)
		if not getattr(app, 'vk_active', False) and keyboard_root in app.opened_windows:
			app.vk_active = True
	except Exception:
		pass

	# ---- Mode gate: compact (classic) vs advanced ----
	def is_advanced_mode() -> bool:
		'''
		Advanced mode is controlled by the main app.
		Priority:
		- callable app.is_vk_advanced_mode() -> bool
		- bool attr app.vk_advanced_mode
		- string attr app.vk_mode == 'advanced'
		Defaults to compact mode (False) if none exist.
		'''
		try:
			if callable(getattr(app, 'is_vk_advanced_mode', None)):
				return bool(app.is_vk_advanced_mode())
		except Exception:
			pass
		if hasattr(app, 'vk_advanced_mode'):
			try:
				return bool(app.vk_advanced_mode)
			except Exception:
				pass
		try:
			return str(getattr(app, 'vk_mode', '')).lower() == 'advanced'
		except Exception:
			return False

	# ---- Sticky configuration (from main app) ----
	def is_sticky_enabled() -> bool:
		'''
		Sticky is controlled by outer variables:
		Priority:
		- callable app.is_vk_sticky() -> bool
		- bool attr app.vk_sticky_modifiers
		- bool attr app.vk_sticky
		Defaults to False if none exist.
		'''
		try:
			if callable(getattr(app, 'is_vk_sticky', None)):
				return bool(app.is_vk_sticky())
		except Exception:
			pass
		for name in ('vk_sticky_modifiers', 'vk_sticky'):
			try:
				return bool(getattr(app, name))
			except Exception:
				continue
		return False

	# ---- Feedback (sound/haptic) configuration (from main app) ----
	def is_feedback_enabled() -> bool:
		'''
		Feedback is off by default.
		Priority:
		- callable app.is_vk_feedback() -> bool
		- any truthy in (app.vk_feedback, app.vk_feedback_enabled, app.vk_sound, app.vk_haptics)
		'''
		try:
			if callable(getattr(app, 'is_vk_feedback', None)):
				return bool(app.is_vk_feedback())
		except Exception:
			pass
		for name in ('vk_feedback', 'vk_feedback_enabled', 'vk_sound', 'vk_haptics'):
			try:
				if bool(getattr(app, name)):
					return True
			except Exception:
				continue
		return False

	# Gentle, de-spammed, charming click: try custom audio first, then light beep, finally tk bell
	def _load_soft_click():
		'''
		Try to load a soft click from either app.vk_sound_path or a default file.
		Returns an object playable by pydub.playback.play, or None.
		'''
		try:
			from pydub import AudioSegment  # type: ignore
		except Exception:
			return None

		# Candidate paths (first existing wins)
		candidates = []
		try:
			p = getattr(app, 'vk_sound_path', None)
			if p:
				candidates.append(str(p))
		except Exception:
			pass
		# Common project asset locations (best-guess, safe to fail)
		candidates.extend([
			'new_assests/sounds/vk_tap.wav',
			'new_assests/sounds/click_soft.wav',
			'assets/sounds/vk_tap.wav',
			'assets/click_soft.wav',
		])

		for path in candidates:
			try:
				if os.path.exists(path):
					seg = AudioSegment.from_file(path)
					# Lower volume for charm and reduce harshness
					try:
						gain_db = float(getattr(app, 'vk_sound_gain_db', -8.0))
					except Exception:
						gain_db = -8.0
					return seg.apply_gain(gain_db)
			except Exception:
				continue
		return None

	# Feedback state for debouncing and caching

	feedback_state = {
		'last_ts': 0.0,
		'min_interval': 0.07,  # 70ms global debounce to reduce spam
		'clip': None,  # cached pydub AudioSegment
	}
	# Use app-configured debounce and repeat cadence if present
	try:
		ms = int(getattr(app, 'vk_feedback_min_interval_ms', 70))
		feedback_state['min_interval'] = max(0, ms) / 1000.0
	except Exception:
		pass
	try:
		repeat_every = int(getattr(app, 'vk_repeat_feedback_every', 4))
	except Exception:
		repeat_every = 4
	if repeat_every <= 0:
		repeat_every = 1

	# Feedback state for debouncing and caching
	feedback_state = {
		'last_ts': 0.0,
		'min_interval': 0.07,  # 70ms global debounce to reduce spam
		'clip': None,  # cached pydub AudioSegment
	}

	def _play_soft_click():
		'''
		Best-effort playback:
		- pydub (if available and clip loaded)
		- Windows winsound beep (short, lower-ish freq)
		- final fallback: tk bell (still single, not repeated)
		'''
		try:
			# Debounce (global across all feedback kinds)
			now = monotonic()
			if now - feedback_state['last_ts'] < feedback_state['min_interval']:
				return
			feedback_state['last_ts'] = now
		except Exception:
			pass

		# Try custom clip (pydub)
		try:
			if feedback_state['clip'] is None:
				feedback_state['clip'] = _load_soft_click()
			if feedback_state['clip'] is not None:
				try:
					from pydub.playback import play  # type: ignore
					play(feedback_state['clip'])
					return
				except Exception:
					pass
		except Exception:
			pass

		# Try a very short, soft-ish system beep on Windows
		try:
			import sys
			if sys.platform.startswith('win'):
				import winsound  # type: ignore
				# 523Hz (C5), 25ms — short and less jarring than default bell
				winsound.Beep(523, 25)
				return
		except Exception:
			pass

		# Fallback: single Tk bell
		try:
			keyboard_root.bell()
		except Exception:
			pass

	def _feedback(kind: str, value: str = '', *, repeat: bool = False):
		'''
		Emits feedback if enabled.
		Tries app.on_vk_feedback(kind, value, repeat=False/True).
		If not present, plays a soft, de-spammed custom click (preferred) or a gentle beep.
		Notes:
		- Mode/mode-button actions (caps/sym/sym2/shift) are muted by design.
		- Repeat ticks are already throttled by the key-hold logic; we also debounce globally.
		'''
		if not is_feedback_enabled():
			return

		# Explicitly mute all mode-related feedback (caps, sym, sym2, shift, etc.)
		if kind == 'mode':
			return

		# Let host override first; if it doesn't play, we fall back to our sound
		try:
			cb = getattr(app, 'on_vk_feedback', None)
			if callable(cb):
				try:
					cb(kind, value, repeat=repeat)  # type: ignore[call-arg]
					return
				except TypeError:
					cb(kind, value)
					return
		except Exception:
			pass

		# Our own soft, charming, and de-spammed sound (single tick only)
		if repeat:
			# Additional guard: only every Nth repeat is allowed by the caller;
			# here we just ensure we don't stack too densely.
			_play_soft_click()
		else:
			_play_soft_click()

	# ---- Smart Tab/Indent ----
	def get_indent_unit() -> str:
		'''
		Resolve indent unit from main app.
		Priority:
		- callable app.get_indent_unit() -> str
		- if indent method is 'tab' -> '\t'
		- else spaces repeated N where N = app.vk_indent_size or app.indent_size or 4
		'''
		try:
			get_unit = getattr(app, 'get_indent_unit', None)
			if callable(get_unit):
				unit = str(get_unit())
				if unit:
					return unit
		except Exception:
			pass
		# Determine method
		try:
			method = getattr(app, 'indent_method', None)
			if method and callable(getattr(method, 'get', None)):
				method_val = method.get()
			else:
				method_val = str(method) if method else ''
		except Exception:
			method_val = ''
		if str(method_val).lower() == 'tab':
			return '\t'
		# spaces
		size = 4
		for attr in ('vk_indent_size', 'indent_size'):
			try:
				val = getattr(app, attr)
				if isinstance(val, int) and val > 0:
					size = val
					break
			except Exception:
				continue
		return ' ' * size

	# ---- Smart insert spacing (from main app) ----
	def is_smart_spacing_enabled() -> bool:
		'''
		Smart spacing is off by default.
		Priority:
		- callable app.is_vk_smart_spacing() -> bool
		- bool attr app.vk_smart_spacing
		'''
		try:
			if callable(getattr(app, 'is_vk_smart_spacing', None)):
				return bool(app.is_vk_smart_spacing())
		except Exception:
			pass
		try:
			return bool(getattr(app, 'vk_smart_spacing'))
		except Exception:
			return False

	def _smart_insert_text(text_value: str) -> bool:
		'''
		Apply smart spacing around punctuation when enabled.
		Returns True if it handled insertion manually (caller should NOT insert again),
		False if it didn't handle (caller should perform normal insert).
		'''
		if not is_smart_spacing_enabled():
			return False
		tw = _get_text_widget()
		if not tw or not text_value:
			return False

		# Sets
		trail_space_punct = {',', '.', ';', ':', '?', '!'}
		open_brackets = {'('}
		closing_set = {')', ']', '}'}
		whitespace = {' ', '\t', '\n'}

		try:
			# Handle only single-char insertions for smart rules
			if len(text_value) != 1:
				return False

			ch = text_value
			prev_char = ''
			next_char = ''
			try:
				prev_char = tw.get('insert -1c')
			except Exception:
				prev_char = ''
			try:
				next_char = tw.get('insert')
			except Exception:
				next_char = ''

			# Rule 1: For , . ; : ? ! -> ensure no space before, one space after
			if ch in trail_space_punct:
				# Remove space before
				if prev_char in whitespace:
					try:
						tw.delete('insert -1c')
					except Exception:
						pass
				# Insert the punctuation
				tw.insert('insert', ch)
				# Add a single trailing space if next is not whitespace/closing/newline or end
				if next_char and (next_char not in whitespace and next_char not in closing_set):
					tw.insert('insert', ' ')
				_focus_text()
				return True

			# Rule 2: Opening parenthesis -> add space before if previous is alnum/closing/quote
			if ch in open_brackets:
				if prev_char and (prev_char.isalnum() or prev_char in (')', ']', '}', '"', "'")):
					tw.insert('insert', ' ')
				tw.insert('insert', ch)
				_focus_text()
				return True

			# Rule 3: Closing parenthesis -> just insert, and if next is alnum, add a space
			if ch in closing_set:
				tw.insert('insert', ch)
				if next_char and next_char.isalnum():
					tw.insert('insert', ' ')
				_focus_text()
				return True

			# Default: not handled
			return False
		except Exception:
			return False

	last_alpha_mode = 'upper'
	app.sym_var1 = False
	app.sym_var2 = False

	# One-shot sticky state (auto-revert after a single text insertion)
	sticky_cfg = {'enabled': is_sticky_enabled()}
	sticky_state = {'pending': None, 'previous_mode': 'lower'}  # e.g., ('alpha', 'lower') or ('sym', 'upper')

	# Text helpers
	def _get_text_widget():
		return getattr(app, 'EgonTE', None)

	def _focus_text():
		try:
			_tw = _get_text_widget()
			if _tw:
				_tw.see('insert')
				_tw.focus_set()
		except Exception:
			pass

	def maybe_revert_sticky_after_insert():
		"""
				If sticky one-shot is active (alpha/sym), revert to the previous mode after a single
				non-mode key inserts text.
				"""
		if not sticky_state['pending']:
			return
		try:
			kind, prev_mode = sticky_state['pending'], sticky_state['previous_mode']
		except Exception:
			kind, prev_mode = None, None

		# First, if we armed a one-shot Shift, use the unified reset that restores
		# visuals + number-row + alpha mode to avoid partial state leftovers.
		try:
			reset_shift_callable = getattr(app, 'vk_shift_reset', None)
			if kind == 'alpha' and callable(reset_shift_callable):
				reset_shift_callable()
				sticky_state['pending'] = None
				return
		except Exception:
			pass

		# For other one-shot kinds (sym/sym2), restore previous mode
		if kind in ('alpha', 'sym', 'sym2'):
			try:
				if prev_mode in ('upper', 'lower'):
					set_keyboard_mode(prev_mode)
				else:
					set_keyboard_mode('lower')
			except Exception:
				pass

		# turn off visual highlight on shift toggles (if present)
		for btn_attr_name in ('vk_shift_left_button', 'vk_shift_right_button'):
			try:
				btn_ref = getattr(app, btn_attr_name, None)
				if btn_ref:
					_set_button_active(btn_ref, False)
			except Exception:
				pass

		# ensure number row mapping is restored and toggle state cleared after one‑shot shift
		try:
			reset_shift_callable = getattr(app, 'vk_shift_reset', None)
			if callable(reset_shift_callable):
				reset_shift_callable()
		except Exception:
			pass

		sticky_state['pending'] = None


	def insert_text(text_value):
		# Smart spacing path
		if _smart_insert_text(text_value):
			_feedback('text', text_value)
			maybe_revert_sticky_after_insert()
			return

		text_widget = _get_text_widget()
		if text_widget is None:
			return
		try:
			selection_ranges = text_widget.tag_ranges('sel')
			if selection_ranges:
				text_widget.delete(selection_ranges[0], selection_ranges[1])
				text_widget.mark_set('insert', selection_ranges[0])
		except Exception:
			pass
		try:
			insert_index = app.get_pos() if hasattr(app, 'get_pos') else 'insert'
			text_widget.insert(insert_index, text_value)
			_focus_text()
		except Exception:
			pass
		_feedback('text', text_value)
		maybe_revert_sticky_after_insert()

	def insert_tab():
		# Smart Tab/Indent
		insert_text(get_indent_unit())

	# Navigation and editing helpers (for advanced mode too)
	def move_cursor(chars=0, lines=0, to=''):
		tw = _get_text_widget()
		if not tw:
			return
		try:
			if to == 'linestart':
				tw.mark_set('insert', 'insert linestart')
			elif to == 'lineend':
				tw.mark_set('insert', 'insert lineend')
			else:
				if chars:
					direction = 'c' if chars >= 0 else 'c'
					tw.mark_set('insert', f'insert {chars:+d}{direction}')
				if lines:
					direction = 'l' if lines >= 0 else 'l'
					tw.mark_set('insert', f'insert {lines:+d}{direction}')
			_focus_text()
		except Exception:
			pass
		_feedback('nav', to or (f'chars={chars},lines={lines}'))

	def delete_backward():
		tw = _get_text_widget()
		if not tw:
			return
		try:
			if tw.tag_ranges('sel'):
				tw.delete('sel.first', 'sel.last')
			else:
				tw.delete('insert -1c')
			_focus_text()
		except Exception:
			pass
		_feedback('delete', 'backspace')

	def delete_forward():
		tw = _get_text_widget()
		if not tw:
			return
		try:
			if tw.tag_ranges('sel'):
				tw.delete('sel.first', 'sel.last')
			else:
				tw.delete('insert')
			_focus_text()
		except Exception:
			pass
		_feedback('delete', 'delete')

	shift_state = {'is_active': False, 'previous_mode': 'lower'}

	def shift_press(_event=None):
		if not shift_state['is_active']:
			shift_state['previous_mode'] = last_alpha_mode
			set_keyboard_mode('upper')
			shift_state['is_active'] = True
		# Mute sound for mode actions
		# _feedback('mode', 'shift-press')

	def shift_release(_event=None):
		if shift_state['is_active']:
			set_keyboard_mode(shift_state['previous_mode'])
			shift_state['is_active'] = False
		# Mute sound for mode actions
		# _feedback('mode', 'shift-release')

	# Frames
	buttons_frame = Frame(keyboard_root)
	extras_frame = Frame(keyboard_root)
	buttons_frame.pack()
	# extras_frame.pack()  # compact-only; see below

	button_width = 6

	# Helpers
	def make_letter_button(label_text):
		return Button(
			buttons_frame,
			text=label_text,
			width=button_width,
			command=(lambda fixed_text=label_text: insert_text(fixed_text))
		)

	def quick_grid(widget_list, row_number):
		for col_index, widget in enumerate(widget_list):
			widget.grid(row=row_number, column=col_index, ipady=10)

	# Lightweight helper: when in advanced layout, avoid duplicating number-row keys
	def _filtered_symbols(seq):
		try:
			adv = is_advanced_mode()
		except Exception:
			adv = False
		if not adv:
			return list(seq)
		dup = set('0123456789-=')  # provided by the advanced number row
		return [ch for ch in seq if ch not in dup]

	# Small UI helper for active/inactive visual states on toggle keys
	def _set_button_active(button, active: bool):
		try:
			hl = '#4a6fa5' if not app.night_mode.get() else '#0f3b64'
		except Exception:
			hl = '#4a6fa5'
		try:
			base = getattr(app, 'dynamic_button', 'gray')
			button.configure(bg=(hl if active else base))
		except Exception:
			pass

	# Letters (classic variable names and order)
	q_button, w_button, e_button, r_button, t_button, y_button, u_button, i_button, o_button, p_button, \
		a_button, s_button, d_button, f_button, g_button, h_button, j_button, k_button, l_button, \
		z_button, x_button, c_button, v_button, b_button, n_button, m_button = \
		[make_letter_button(button_label) for button_label in characters_str]

	# Symbols used on right segments (classic)
	symbol_values = ('{', '}', ';', '"', '<', '>', '/', '?', ',', '.')
	curly_open_button, curly_close_button, semicolon_button, double_quote_button, \
		less_than_button, greater_than_button, slash_button, question_mark_button, comma_button, period_button = [
		Button(buttons_frame, text=value, width=button_width, command=(lambda v=value: insert_text(v)))
		for value in symbol_values
	]

	# Extras/top row (classic)
	space_button = Button(extras_frame, text='Space', width=button_width, command=lambda: insert_text(' '))
	caps_button = Button(extras_frame, text='Caps', width=button_width)
	sym_mode_button = Button(extras_frame, text='1!*', width=button_width)
	sym_mode_2_button = Button(extras_frame, text='ƒ√€', width=button_width)
	enter_button = Button(extras_frame, text='Enter', width=button_width, command=lambda: insert_text('\n'))
	open_parenthesis_button = Button(extras_frame, text='(', width=button_width, command=lambda: insert_text('('))
	close_parenthesis_button = Button(extras_frame, text=')', width=button_width, command=lambda: insert_text(')'))
	tab_button = Button(extras_frame, text='Tab', width=button_width, command=insert_tab)

	# NOTE: Shift buttons were previously created but not placed.
	# They are omitted to avoid dead bindings and inconsistent layout. Hold-to-shift is still available via caps/shift state.

	# Optional: Shift keys (hold-to-shift)
	shift_left_button = Button(buttons_frame, text='Shift', width=button_width)
	shift_right_button = Button(buttons_frame, text='Shift', width=button_width)
	for shift_widget in (shift_left_button, shift_right_button):
		shift_widget.bind('<ButtonPress-1>', shift_press)
		shift_widget.bind('<ButtonRelease-1>', shift_release)

	# Placement – compact/advanced layouts share helpers; we fill after mode selection
	# Mode handling (caps/sym)
	def set_keyboard_mode(mode_name):
		nonlocal last_alpha_mode
		try:
			if app.night_mode.get():
				highlight_color = '#042f42' if app.nm_palette.get() == 'black' else '#051d29'
			else:
				highlight_color = 'light grey'
		except Exception:
			highlight_color = 'light grey'

		for button_to_reset in (caps_button, sym_mode_button, sym_mode_2_button):
			try:
				button_to_reset.configure(bg=getattr(app, 'dynamic_button', 'gray'))
			except Exception:
				pass

		if mode_name in ('upper', 'lower'):
			last_alpha_mode = mode_name
			sym_mode_button.configure(command=lambda: sym_mode_toggle())
			sym_mode_2_button.configure(command=lambda: sym2_mode_toggle())

		if mode_name == 'upper':
			for index_pos in range(len(ascii_uppercase)):
				letters_buttons[index_pos].configure(
					text=ascii_uppercase[index_pos],
					command=lambda fixed_index=index_pos: insert_text(ascii_uppercase[fixed_index])
				)
			caps_button.configure(command=lambda: caps_toggle())
			try:
				caps_button.configure(bg=highlight_color)
			except Exception:
				pass

		elif mode_name == 'lower':
			for index_pos in range(len(ascii_lowercase)):
				letters_buttons[index_pos].configure(
					text=ascii_lowercase[index_pos],
					command=lambda fixed_index=index_pos: insert_text(ascii_lowercase[fixed_index])
				)
			caps_button.configure(command=lambda: caps_toggle())

		if mode_name == 'sym':
			# Toggle behavior: if currently active, turn off and restore alpha layout
			if app.sym_var1:
				app.sym_var1 = False
				try:
					sym_mode_button.configure(bg=getattr(app, 'dynamic_button', 'gray'))
				except Exception:
					pass
				# advanced mode sym button highlight reset
				try:
					sym_adv_button.configure(bg=getattr(app, 'dynamic_button', 'gray'))  # type: ignore[name-defined]
				except Exception:
					pass
				# restore previous alpha mode (upper/lower) and advanced non-letter layer
				try:
					if callable(getattr(app, 'vk_apply_mode_layer', None)):
						app.vk_apply_mode_layer(last_alpha_mode if last_alpha_mode in ('upper', 'lower') else 'lower')  # type: ignore[misc]
					set_keyboard_mode(last_alpha_mode if last_alpha_mode in ('upper', 'lower') else 'lower')
				except Exception:
					pass
				return

			# Activating symbols layout (letters first, for immediate feedback)
			symbols = _filtered_symbols(sym_n)
			max_count = min(len(letters_buttons_by_order), len(symbols))
			for counter_index in range(max_count):
				symbol_value = symbols[counter_index]
				letters_buttons_by_order[counter_index].configure(
					text=symbol_value, command=lambda fixed_symbol=symbol_value: insert_text(fixed_symbol)
				)

			# Expand in advanced layout without duplicating sym2, and keeping number row intact if pool is insufficient.
			try:
				if callable(getattr(app, 'vk_apply_mode_layer', None)):
					app.vk_apply_mode_layer('sym')  # type: ignore[misc]
				else:
					# if helper missing, be safe about number row
					apply_number_row_shift(False)
				# ensure helper flag exists
				if not hasattr(app, 'vk_sym_numbers'):
					app.vk_sym_numbers = False  # type: ignore[attr-defined]
			except Exception:
				pass

			sym_mode_button.configure(command=lambda: sym_mode_toggle())
			try:
				sym_mode_button.configure(bg=highlight_color)
			except Exception:
				pass
			# advanced mode sym button highlight
			try:
				sym_adv_button.configure(bg=highlight_color)  # type: ignore[name-defined]
				sym2_adv_button.configure(bg=getattr(app, 'dynamic_button', 'gray'))  # type: ignore[name-defined]
			except Exception:
				pass
			if app.sym_var2:
				app.sym_var2 = False
				try:
					sym_mode_2_button.configure(
						bg=getattr(app, 'dynamic_button', 'gray'),
						command=lambda: sym2_mode_toggle()
					)
				except Exception:
					pass
			app.sym_var1 = True

		elif mode_name == 'sym2':
			# Toggle behavior: if currently active, turn off and restore alpha layout
			if app.sym_var2:
				app.sym_var2 = False
				try:
					sym_mode_2_button.configure(bg=getattr(app, 'dynamic_button', 'gray'))
				except Exception:
					pass
				# advanced mode sym2 button highlight reset
				try:
					sym2_adv_button.configure(bg=getattr(app, 'dynamic_button', 'gray'))  # type: ignore[name-defined]
				except Exception:
					pass
				# restore previous alpha mode (upper/lower) and advanced non-letter layer
				try:
					if callable(getattr(app, 'vk_apply_mode_layer', None)):
						app.vk_apply_mode_layer(last_alpha_mode if last_alpha_mode in ('upper', 'lower') else 'lower')  # type: ignore[misc]
					set_keyboard_mode(last_alpha_mode if last_alpha_mode in ('upper', 'lower') else 'lower')
				except Exception:
					pass
				return
			# Activating secondary symbols layout
			symbols2 = _filtered_symbols(syn_only)
			max_count = min(len(letters_buttons_by_order), len(symbols2))
			for counter_index in range(max_count):
				symbol_value = symbols2[counter_index]
				letters_buttons_by_order[counter_index].configure(
					text=symbol_value, command=lambda fixed_symbol=symbol_value: insert_text(fixed_symbol)
				)
			# As above, leave any extra letter spots unchanged
			sym_mode_2_button.configure(command=lambda: sym2_mode_toggle())
			try:
				sym_mode_2_button.configure(bg=highlight_color)
			except Exception:
				pass
			# advanced mode sym2 button highlight
			try:
				sym2_adv_button.configure(bg=highlight_color)  # type: ignore[name-defined]
				sym_adv_button.configure(bg=getattr(app, 'dynamic_button', 'gray'))  # type: ignore[name-defined]
			except Exception:
				pass
			if app.sym_var1:
				app.sym_var1 = False
				try:
					sym_mode_button.configure(
						bg=getattr(app, 'dynamic_button', 'gray'),
						text='1!*',
						command=lambda: sym_mode_toggle()
					)
				except Exception:
					pass
			app.sym_var2 = True

		if mode_name in ('upper', 'lower'):
			app.sym_var1 = False
			app.sym_var2 = False
			try:
				sym_mode_button.configure(command=lambda: sym_mode_toggle(),
										  bg=getattr(app, 'dynamic_button', 'gray'))
				sym_mode_2_button.configure(command=lambda: sym2_mode_toggle(),
											bg=getattr(app, 'dynamic_button', 'gray'))
			except Exception:
				pass
			# also reset advanced sym button highlights if present
			try:
				sym_adv_button.configure(bg=getattr(app, 'dynamic_button', 'gray'))  # type: ignore[name-defined]
				sym2_adv_button.configure(bg=getattr(app, 'dynamic_button', 'gray'))  # type: ignore[name-defined]
			except Exception:
				pass
			# Ensure any previously applied advanced layer restores non-letter targets only
			try:
				if callable(getattr(app, 'vk_apply_mode_layer', None)):
					app.vk_apply_mode_layer(mode_name)  # type: ignore[misc]
			except Exception:
				pass

	# --- Sticky-aware toggles (wrappers) ---
	def caps_toggle():
		if sticky_cfg['enabled']:
			prev = last_alpha_mode
			set_keyboard_mode('upper')
			sticky_state['previous_mode'] = prev
			sticky_state['pending'] = 'alpha'
		else:
			if last_alpha_mode == 'lower':
				set_keyboard_mode('upper')
			else:
				set_keyboard_mode('lower')

	def sym_mode_toggle():
		if sticky_cfg['enabled']:
			prev = last_alpha_mode
			set_keyboard_mode('sym')
			sticky_state['previous_mode'] = prev
			sticky_state['pending'] = 'sym'
		else:
			set_keyboard_mode('sym')

	def sym2_mode_toggle():
		if sticky_cfg['enabled']:
			prev = last_alpha_mode
			set_keyboard_mode('sym2')
			sticky_state['previous_mode'] = prev
			sticky_state['pending'] = 'sym2'
		else:
			set_keyboard_mode('sym2')

	# Hook caps/sym controls through wrappers
	caps_button.configure(command=lambda: caps_toggle())
	sym_mode_button.configure(command=lambda: sym_mode_toggle())
	sym_mode_2_button.configure(command=lambda: sym2_mode_toggle())

	# Collect buttons for theming and mode updates (base)
	letters_buttons = (
		a_button, b_button, c_button, d_button, e_button, f_button, g_button, h_button, i_button, j_button,
		k_button, l_button, m_button, n_button, o_button, p_button, q_button, r_button, s_button, t_button,
		u_button, v_button, w_button, x_button, y_button, z_button
	)
	letters_buttons_by_order = (
		q_button, w_button, e_button, r_button, t_button, y_button, u_button, i_button, o_button, p_button,
		a_button, s_button, d_button, f_button, g_button, h_button, j_button, k_button, l_button,
		z_button, x_button, c_button, v_button, b_button, n_button, m_button
	)
	base_symbol_buttons = (
		semicolon_button, curly_open_button, curly_close_button, double_quote_button,
		less_than_button, greater_than_button, slash_button, question_mark_button, comma_button, period_button,
		open_parenthesis_button, close_parenthesis_button
	)
	functional_buttons = (
		space_button, enter_button, tab_button, caps_button, sym_mode_button, sym_mode_2_button
	)

	# --- Build layout(s) ---
	# --- Build layout(s) ---
	advanced = is_advanced_mode()

	# In advanced mode, hide the extras frame entirely (it belongs to compact mode)
	if advanced:
		try:
			extras_frame.pack_forget()
		except Exception:
			pass

	# Compact layout (classic)
	if not advanced:
		try:
			extras_frame.pack()
		except Exception:
			pass

		# Extras row at the top (compact only)
		space_button.grid(row=0, column=1, ipadx=90, ipady=10)
		enter_button.grid(row=0, column=2, ipadx=14, ipady=10)
		open_parenthesis_button.grid(row=0, column=3, ipady=10)
		close_parenthesis_button.grid(row=0, column=4, ipady=10)
		tab_button.grid(row=0, column=5, ipady=10)
		caps_button.grid(row=0, column=6, ipady=10)
		sym_mode_button.grid(row=0, column=7, ipady=10)
		sym_mode_2_button.grid(row=0, column=8, ipady=10)

		# Row 1 letters/symbols
		row1_buttons = (
			q_button, w_button, e_button, r_button, t_button, y_button, u_button, i_button, o_button, p_button,
			curly_open_button, curly_close_button
		)
		quick_grid(row1_buttons, 1)

		# Row 2 letters/symbols
		row2_buttons = (
			a_button, s_button, d_button, f_button, g_button, h_button, j_button, k_button, l_button,
			semicolon_button, double_quote_button, period_button
		)
		quick_grid(row2_buttons, 2)

		# Row 3 letters/symbols
		row3_buttons = (
			z_button, x_button, c_button, v_button, b_button, n_button, m_button,
			less_than_button, greater_than_button, slash_button, question_mark_button, comma_button
		)
		quick_grid(row3_buttons, 3)

		symbol_buttons = base_symbol_buttons
		extra_nav_buttons = ()
	else:
		# Advanced: OSK-like layout with clear staggered rows and wider control keys (no extras_frame rows)
		def place_row(widgets_with_span, *, row: int, start_col: int = 0, ipady: int = 10):
			col = start_col
			for item in widgets_with_span:
				if isinstance(item, tuple):
					w, span = item
				else:
					w, span = item, 1
				w.grid(row=row, column=col, columnspan=span, ipady=ipady, sticky='we', padx=1, pady=1)
				col += span

		total_cols = 18
		try:
			for col_index in range(total_cols):
				buttons_frame.grid_columnconfigure(col_index, weight=1, uniform='vk')
		except Exception:
			pass

		# --- Smart Shift variants state (advanced layout) ---
		shift_locked = {'value': False}
		shift_oneshot_armed = {'value': False}
		shift_prev_alpha = {'mode': 'lower'}  # remember previous alpha mode to fully restore on reset

		# Timing thresholds (ms)
		shift_tap_timeout_ms = int(getattr(app, 'vk_shift_tap_timeout_ms', 300))   # double‑tap window
		shift_hold_threshold_ms = int(getattr(app, 'vk_shift_hold_threshold_ms', 220))  # press‑and‑hold threshold

		# Runtime timing state
		shift_press_time_s = {'value': 0.0}
		shift_last_tap_time_s = {'value': 0.0}
		shift_hold_timer_id = {'value': None}

		shift_toggle_enabled = bool(getattr(app, 'vk_shift_toggle_enabled', True))
		shift_enabled = bool(getattr(app, 'vk_shift_enabled', True))

		# Extra buttons to complete the OSK
		bracket_open_button = Button(buttons_frame, text='[', width=button_width, command=lambda: insert_text('['))
		bracket_close_button = Button(buttons_frame, text=']', width=button_width, command=lambda: insert_text(']'))
		backslash_button = Button(buttons_frame, text='\\', width=button_width, command=lambda: insert_text('\\'))
		minus_button = Button(buttons_frame, text='-', width=button_width, command=lambda: insert_text('-'))
		equal_button = Button(buttons_frame, text='=', width=button_width, command=lambda: insert_text('='))
		quote_button = Button(buttons_frame, text="'", width=button_width, command=lambda: insert_text("'"))
		comma_button_adv = Button(buttons_frame, text=',', width=button_width, command=lambda: insert_text(','))
		period_button_adv = Button(buttons_frame, text='.', width=button_width, command=lambda: insert_text('.'))
		slash_button_adv = Button(buttons_frame, text='/', width=button_width, command=lambda: insert_text('/'))

		# Number row (1..0 - =) + sym keys + Del + Backspace at the far right
		num_chars = ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0')
		num_shifted = ('!', '@', '#', '$', '%', '^', '&', '*', '(', ')')
		number_buttons = [Button(buttons_frame, text=v, width=button_width, command=(lambda vv=v: insert_text(vv))) for
						  v in
						  num_chars]
		backspace_button = Button(buttons_frame, text='Backspace', width=button_width + 2, command=delete_backward)
		delete_button = Button(buttons_frame, text='Del', width=button_width, command=delete_forward)

		# Advanced-mode Sym buttons (present in advanced layout)
		sym_adv_button = Button(buttons_frame, text='1!*', width=button_width, command=lambda: sym_mode_toggle())
		sym2_adv_button = Button(buttons_frame, text='ƒ√€', width=button_width, command=lambda: sym2_mode_toggle())


		def _apply_number_row_shift(active: bool):
			# digits
			for idx, btn in enumerate(number_buttons):
				if active:
					btn.configure(text=num_shifted[idx], command=(lambda ch=num_shifted[idx]: insert_text(ch)))
				else:
					btn.configure(text=num_chars[idx], command=(lambda ch=num_chars[idx]: insert_text(ch)))
			# - and =
			if active:
				minus_button.configure(text='_', command=lambda: insert_text('_'))
				equal_button.configure(text='+', command=lambda: insert_text('+'))
			else:
				minus_button.configure(text='-', command=lambda: insert_text('-'))
				equal_button.configure(text='=', command=lambda: insert_text('='))


		# snake_case alias (avoid leading underscore in callers we add)
		apply_number_row_shift = _apply_number_row_shift

		# Place number row: digits, '-', '=', 'Del', 'Backspace' (moved sym buttons to control row to free space)
		place_row(
			[*number_buttons, minus_button, equal_button, delete_button, (backspace_button, 2)],
			row=1, start_col=0
		)

		# Top letter row: Tab (wide), Q..P, [ ], \
		tab_wide = Button(buttons_frame, text='Tab', width=button_width + 2, command=insert_tab)
		place_row(
			[(tab_wide, 2), q_button, w_button, e_button, r_button, t_button, y_button, u_button, i_button, o_button,
			 p_button,
			 bracket_open_button, bracket_close_button, backslash_button],
			row=2, start_col=0
		)

		# Home row: Caps (wider), A..L, ; ' and wide Enter at end
		enter_wide = Button(buttons_frame, text='Enter', width=button_width + 3, command=lambda: insert_text('\n'))
		caps_wide = Button(buttons_frame, text='Caps', width=button_width + 2, command=lambda: caps_toggle())
		place_row(
			[(caps_wide, 2), a_button, s_button, d_button, f_button, g_button, h_button, j_button, k_button, l_button,
			 semicolon_button, quote_button, (enter_wide, 2)],
			row=3, start_col=0
		)

		# Shift: toggle-like behaviour (inspired by sym buttons) plus Smart Shift variants:
		# - Single quick tap: one‑shot shift (letters upper + number row symbols for the next insert)
		# - Double‑tap within window: toggle Caps (same as pressing Caps)
		# - Press‑and‑hold beyond threshold: while‑held uppercase + number‑row symbols, restores on release

		def _clear_shift_hold_timer():
			if shift_hold_timer_id['value'] is not None:
				try:
					keyboard_root.after_cancel(shift_hold_timer_id['value'])
				except Exception:
					pass
				shift_hold_timer_id['value'] = None

		def shift_set_active(active: bool, *, oneshot=False):
			# store previous alpha mode before forcing upper
			if active:
				try:
					shift_prev_alpha['mode'] = last_alpha_mode if last_alpha_mode in ('upper', 'lower') else 'lower'
				except Exception:
					shift_prev_alpha['mode'] = 'lower'
			shift_locked['value'] = active and not oneshot
			shift_oneshot_armed['value'] = active and oneshot

			# visual highlight similar to sym buttons
			_set_button_active(shift_left_wide, active)
			_set_button_active(shift_right_wide, active)

			# Update number row mapping for Shift
			apply_number_row_shift(active)

			# Letters to upper when active; when deactivating, restore exact previous alpha mode
			try:
				if active:
					set_keyboard_mode('upper')
				else:
					prev = shift_prev_alpha.get('mode', 'lower')
					set_keyboard_mode(prev if prev in ('upper', 'lower') else 'lower')
			except Exception:
				pass

		def _activate_hold_shift():
			shift_hold_timer_id['value'] = None
			shift_set_active(True, oneshot=False)

		def on_shift_press_event(_evt=None):
			if not shift_enabled:
				return 'break'
			_clear_shift_hold_timer()
			shift_press_time_s['value'] = monotonic()
			# schedule hold activation
			try:
				shift_hold_timer_id['value'] = keyboard_root.after(shift_hold_threshold_ms, _activate_hold_shift)
			except Exception:
				# fallback: immediate activation if timer fails
				shift_set_active(True, oneshot=False)
			return 'break'

		def on_shift_release_event(_evt=None):
			if not shift_enabled:
				return 'break'

			# If we never saw a press for this release/leave (spurious), ignore safely
			if shift_press_time_s['value'] == 0.0 and not shift_locked['value'] and not shift_oneshot_armed['value']:
				return 'break'

			now_s = monotonic()
			duration_ms = int((now_s - shift_press_time_s['value']) * 1000) if shift_press_time_s['value'] > 0.0 else 0
			was_hold = duration_ms >= shift_hold_threshold_ms
			_clear_shift_hold_timer()

			# reset press time to avoid reusing stale timestamps
			shift_press_time_s['value'] = 0.0

			if was_hold:
				# hold path: simply deactivate shift
				shift_set_active(False, oneshot=False)
				# clear sticky one‑shot if any
				sticky_state['pending'] = None
				return 'break'

			# quick tap path: check double‑tap
			last_tap_s = shift_last_tap_time_s['value']
			shift_last_tap_time_s['value'] = now_s
			if (now_s - last_tap_s) * 1000.0 <= shift_tap_timeout_ms:
				# double‑tap → toggle Caps
				try:
					# ensure shift visuals off
					_set_button_active(shift_left_wide, False)
					_set_button_active(shift_right_wide, False)
					apply_number_row_shift(False)
				except Exception:
					pass
				# Toggle caps like the Caps button
				caps_toggle()
				# reset tap window to avoid triple sequences
				shift_last_tap_time_s['value'] = 0.0
				# clear any pending one‑shot state
				shift_locked['value'] = False
				shift_oneshot_armed['value'] = False
				sticky_state['pending'] = None
				return 'break'

			# single quick tap → one‑shot shift
			shift_set_active(True, oneshot=True)
			# Arm sticky to auto‑revert after next insert
			sticky_state['previous_mode'] = last_alpha_mode if last_alpha_mode in ('upper', 'lower') else 'lower'
			sticky_state['pending'] = 'alpha'
			return 'break'

		def shift_toggle():
			if not shift_enabled:
				return
			# Toggle-lock like sym buttons; second press resets everything
			now_locked = shift_locked['value']
			shift_set_active(not now_locked, oneshot=False)
			if now_locked:
				# full reset path for consistency with modes: clear one-shot, visuals, and number row
				sticky_state['pending'] = None
				_set_button_active(shift_left_wide, False)
				_set_button_active(shift_right_wide, False)
				apply_number_row_shift(False)

		def shift_one_shot():
			if not shift_enabled:
				return
			# One-shot (arm until next text insert)
			sticky_state['previous_mode'] = last_alpha_mode if last_alpha_mode in ('upper', 'lower') else 'lower'
			sticky_state['pending'] = 'alpha'
			shift_set_active(True, oneshot=True)

		# Bottom row: Shift (left, wide), Z..M, , . /, Shift (right, wide)
		shift_left_wide = Button(buttons_frame, text='Shift', width=button_width + 2,
								 state=('normal' if shift_enabled else 'disabled'))
		shift_right_wide = Button(buttons_frame, text='Shift', width=button_width + 2,
								  state=('normal' if shift_enabled else 'disabled'))
		try:
			# publish in non-underscore style
			app.vk_shift_left_button = shift_left_wide
			app.vk_shift_right_button = shift_right_wide
		except Exception:
			pass

		# Bind Smart Shift variants to both Shift buttons
		for shift_btn in (shift_left_wide, shift_right_wide):
			try:
				shift_btn.bind('<ButtonPress-1>', on_shift_press_event, add='+')
				shift_btn.bind('<ButtonRelease-1>', on_shift_release_event, add='+')
				# On leave/escape, only cancel active hold/oneshot; avoid treating these as taps
				shift_btn.bind('<Leave>', lambda e: (_clear_shift_hold_timer(), None) and 'break', add='+')
				shift_btn.bind('<Escape>', lambda e: (_clear_shift_hold_timer(), None) and 'break', add='+')
			except Exception:
				pass

		place_row(
			[(shift_left_wide, 3),
			 z_button, x_button, c_button, v_button, b_button, n_button, m_button,
			 comma_button_adv, period_button_adv, slash_button_adv,
			 (shift_right_wide, 3)],
			row=4, start_col=0
		)

		# expose a reset callable for one‑shot revert and external resets to restore number row and visuals
		try:
			def vk_shift_reset_impl():
				# clear states
				shift_locked['value'] = False
				shift_oneshot_armed['value'] = False
				sticky_state['pending'] = None
				# visuals
				_set_button_active(shift_left_wide, False)
				_set_button_active(shift_right_wide, False)
				# restore number row and previous alpha mode
				apply_number_row_shift(False)
				prev = shift_prev_alpha.get('mode', 'lower')
				try:
					set_keyboard_mode(prev if prev in ('upper', 'lower') else 'lower')
				except Exception:
					pass
				# clear timing state
				_clear_shift_hold_timer()
				shift_press_time_s['value'] = 0.0
				shift_last_tap_time_s['value'] = 0.0
			app.vk_shift_reset = vk_shift_reset_impl
		except Exception:
			pass


		# Bottom control row: utilize the wide space row for mode controls (sym/sym2) + centered space
		def insert_space_smart():
			# Shift+Space -> non‑breaking space; otherwise normal space
			try:
				shift_active = bool(shift_locked.get('value')) or bool(shift_oneshot_armed.get('value'))
			except Exception:
				shift_active = False
			insert_text('\u00A0' if shift_active else ' ')

		space_wide = Button(buttons_frame, text='Space', width=button_width + 6, command=insert_space_smart)

		# Layout: [sym] [SPACE spans generously] [sym2]
		# Keep button sizes; only adjust column spans for better use of row space
		place_row(
			[sym_adv_button, (space_wide, 8), sym2_adv_button],
			row=5, start_col=4
		)

		# Navigation/edit cluster on the far right (Delete already on number row)
		home_button = Button(buttons_frame, text='Home', width=button_width,
							 command=lambda: move_cursor(to='linestart'))
		end_button = Button(buttons_frame, text='End', width=button_width, command=lambda: move_cursor(to='lineend'))
		left_button = Button(buttons_frame, text='←', width=button_width, command=lambda: move_cursor(chars=-1))
		up_button = Button(buttons_frame, text='↑', width=button_width, command=lambda: move_cursor(lines=-1))
		down_button = Button(buttons_frame, text='↓', width=button_width, command=lambda: move_cursor(lines=+1))
		right_button = Button(buttons_frame, text='→', width=button_width, command=lambda: move_cursor(chars=+1))

		nav_c = total_cols - 3
		home_button.grid(row=2, column=nav_c, columnspan=3, ipady=6, sticky='we', padx=(2, 0))
		end_button.grid(row=3, column=nav_c, columnspan=3, ipady=6, sticky='we', padx=(2, 0))
		up_button.grid(row=4, column=nav_c + 1, ipady=6, sticky='we', padx=(2, 0))
		left_button.grid(row=5, column=nav_c, ipady=6, sticky='we', padx=(2, 0))
		right_button.grid(row=5, column=nav_c + 2, ipady=6, sticky='we', padx=(0, 2))
		down_button.grid(row=5, column=nav_c + 1, ipady=6, sticky='we', padx=(2, 0))

		# Compose collections (include advanced sym buttons for theming and repeat rules)
		symbol_buttons = base_symbol_buttons + (
			bracket_open_button, bracket_close_button, backslash_button,
			minus_button, equal_button, quote_button,
			comma_button_adv, period_button_adv, slash_button_adv,
		)
		extra_nav_buttons = (
			*number_buttons, backspace_button, delete_button,
			shift_left_wide, shift_right_wide,
			home_button, end_button, left_button, up_button, down_button, right_button,
			space_wide, tab_wide, enter_wide, caps_wide,
			sym_adv_button, sym2_adv_button
		)

		# --- Advanced sym layer wiring: broaden sym to cover most typing buttons ---
		try:
			# Build target lists
			letter_targets = list(letters_buttons_by_order)
			number_targets = list(number_buttons)
			# Split punctuation by physical row location
			number_row_extras = [minus_button, equal_button]
			non_number_punct_targets = [
				bracket_open_button, bracket_close_button, backslash_button,
				quote_button, comma_button_adv, period_button_adv, slash_button_adv,
				semicolon_button,
			]
			full_targets = letter_targets + number_targets + number_row_extras + non_number_punct_targets
			non_letter_targets = number_targets + number_row_extras + non_number_punct_targets  # restore-only set
			no_number_targets = letter_targets + non_number_punct_targets

			# Map originals for safe restore
			original_labels_map = {}
			for target_button in full_targets:
				try:
					original_labels_map[target_button] = target_button.cget('text')
				except Exception:
					original_labels_map[target_button] = ''

			# Pools
			default_sym_pool = tuple('`~!@#$%^&*()_-+=[]{}|\\;:\'",.<>/?')

			# Filter helpers
			def filtered_chars(seq):
				return list(_filtered_symbols(seq))

			# Reserved characters for sym2 (avoid collisions)
			sym2_reserved_chars = set(filtered_chars(syn_only))

			# Build a de-duplicated, sufficiently long pool for sym
			def build_sym_pool():
				base_pool = [ch for ch in filtered_chars(sym_n) if ch not in sym2_reserved_chars]
				if len(base_pool) < len(no_number_targets):
					for ch in default_sym_pool:
						if ch in sym2_reserved_chars or ch in base_pool:
							continue
						base_pool.append(ch)
						if len(base_pool) >= len(no_number_targets):
							break
				if not base_pool:
					base_pool = [ch for ch in default_sym_pool if ch not in sym2_reserved_chars]
				seen_chars = set()
				unique_pool = []
				for ch in base_pool:
					if ch in seen_chars:
						continue
					seen_chars.add(ch)
					unique_pool.append(ch)
				return unique_pool

			# Decide target coverage
			def compute_sym_targets_and_layer():
				pool = build_sym_pool()
				if len(pool) >= len(full_targets):
					chosen_targets = full_targets
					chosen_layer = (pool + pool)[:len(chosen_targets)]
					remap_numbers = True
				else:
					chosen_targets = no_number_targets
					chosen_layer = (pool + pool)[:len(chosen_targets)]
					remap_numbers = False
				return chosen_targets, chosen_layer, remap_numbers

			def apply_mode_layer(mode_name_local: str):
				if mode_name_local == 'sym':
					targets, layer, remap_numbers = compute_sym_targets_and_layer()
					try:
						app.vk_sym_numbers = bool(remap_numbers)
					except Exception:
						pass
					for idx_button, target_button in enumerate(targets):
						try:
							char_to_set = layer[idx_button]
							target_button.configure(text=char_to_set, command=(lambda fixed=char_to_set: insert_text(fixed)))
						except Exception:
							continue
					if not remap_numbers:
						try:
							apply_number_row_shift(False)
						except Exception:
							pass
				else:
					# Restore only non-letter targets to avoid overwriting alpha case on letter keys.
					for target_button in non_letter_targets:
						try:
							original_text = original_labels_map.get(target_button, target_button.cget('text'))
							target_button.configure(text=original_text, command=(lambda fixed=original_text: insert_text(fixed)))
						except Exception:
							continue

					# IMPORTANT: Do NOT override Shift's control of number row.
					shift_is_active = False
					try:
						# shift_locked/shift_oneshot_armed are defined in the same advanced-layout scope
						shift_is_active = bool(shift_locked.get('value')) or bool(shift_oneshot_armed.get('value'))
					except Exception:
						shift_is_active = False

					if not shift_is_active:
						try:
							apply_number_row_shift(False)
						except Exception:
							pass

					try:
						app.vk_sym_numbers = False
					except Exception:
						pass

			# expose to set_keyboard_mode and other callers
			app.vk_apply_mode_layer = apply_mode_layer
		except Exception:
			pass


	# Theme list
	all_keyboard_buttons = letters_buttons_by_order + symbol_buttons + functional_buttons + extra_nav_buttons

	# Theming
	for keyboard_button in all_keyboard_buttons:
		try:
			keyboard_button.config(
				bg=getattr(app, 'dynamic_button', '#333333'),
				fg=getattr(app, 'dynamic_text', '#ffffff'),
				activebackground=getattr(app, 'dynamic_bg', '#444444'),
				activeforeground=getattr(app, 'dynamic_text', '#ffffff'),
			)
		except Exception:
			pass

	# Expose to app for night-mode refresh compatibility
	try:
		app.all_vk_buttons = list(all_keyboard_buttons)
	except Exception:
		pass

	# --- Key repeat (press-and-hold) ---
	def is_repeat_enabled() -> bool:
		'''
		Repeat is ON by default (slower than before).
		Priority:
		- callable app.is_vk_repeat_enabled() -> bool
		- bool attr app.vk_repeat_enabled
		'''
		try:
			if callable(getattr(app, 'is_vk_repeat_enabled', None)):
				return bool(app.is_vk_repeat_enabled())
		except Exception:
			pass
		try:
			return bool(getattr(app, 'vk_repeat_enabled'))
		except Exception:
			return True  # default ON

	def get_repeat_timings():
		'''
		Fetch repeat timings from main app if provided, otherwise use slower defaults.
		- app.vk_repeat_initial_delay_ms (int)
		- app.vk_repeat_interval_ms (int)
		Defaults: 550ms initial, 85ms interval (was 350/40).
		'''
		initial = 550
		interval = 85
		try:
			iv = getattr(app, 'vk_repeat_initial_delay_ms', None)
			if isinstance(iv, int) and iv >= 0:
				initial = iv
		except Exception:
			pass
		try:
			it = getattr(app, 'vk_repeat_interval_ms', None)
			if isinstance(it, int) and it > 0:
				interval = it
		except Exception:
			pass
		return initial, interval

	def _unbind_press_hold(widget):
		'''
		Remove previously attached press-hold handlers to avoid duplicate invokes on live re-bind.
		Safe for our own buttons (won't affect global app bindings).
		'''
		try:
			for ev in ('<ButtonPress-1>', '<ButtonRelease-1>', '<Leave>', '<Escape>'):
				widget.unbind(ev)
		except Exception:
			pass

	def _bind_press_hold(widget, invoke_callable, initial_delay=550, interval=85):
		'''
		Attach press-and-hold behavior to a Button:
		- single invoke on press (+ feedback)
		- after initial_delay, repeat invoke every interval ms until release/leave
		- throttled feedback on repeats (every few ticks)
		- brief visual flash on repeats (background pulse)
		'''
		# Ensure we don't stack multiple bindings on live updates
		_unbind_press_hold(widget)

		repeat_state = {'id': None, 'count': 0, 'orig_bg': None}

		def _cancel():
			if repeat_state['id'] is not None:
				try:
					widget.after_cancel(repeat_state['id'])
				except Exception:
					pass
				repeat_state['id'] = None
			repeat_state['count'] = 0
			try:
				if repeat_state['orig_bg'] is not None:
					widget.configure(bg=repeat_state['orig_bg'])
			except Exception:
				pass

		def _flash_once():
			try:
				if repeat_state['orig_bg'] is None:
					repeat_state['orig_bg'] = widget.cget('bg')
				pulse = getattr(app, 'dynamic_overall', '#555555')
				widget.configure(bg=pulse)
				widget.after(40, lambda: widget.configure(bg=repeat_state['orig_bg']))
			except Exception:
				pass

		def _do_repeat():
			try:
				invoke_callable()
			except Exception:
				pass
			repeat_state['count'] += 1
			# Throttle feedback: every 4th repeat tick (and globally debounced)
			if repeat_state['count'] % 4 == 0:
				try:
					label_text = widget.cget('text')
				except Exception:
					label_text = ''
				_feedback('text', label_text, repeat=True)
				_flash_once()
			repeat_state['id'] = widget.after(interval, _do_repeat)

		def _on_press(_e=None):
			_cancel()
			try:
				invoke_callable()
			except Exception:
				pass
			# Initial feedback (globally debounced)
			try:
				label_text = widget.cget('text')
			except Exception:
				label_text = ''
			_feedback('text', label_text, repeat=False)
			repeat_state['id'] = widget.after(initial_delay, _do_repeat)

		def _on_release(_e=None):
			_cancel()

		widget.bind('<ButtonPress-1>', _on_press, add='+')
		widget.bind('<ButtonRelease-1>', _on_release, add='+')
		widget.bind('<Leave>', _on_release, add='+')
		widget.bind('<Escape>', _on_release, add='+')


	# Bind press-and-hold only when enabled (otherwise default single-click behavior remains)
	repeat_enabled = is_repeat_enabled()
	repeat_initial, repeat_interval = get_repeat_timings()
	non_repeating = {caps_button, sym_mode_button, sym_mode_2_button, shift_left_button, shift_right_button}
	# Add advanced buttons that shouldn't repeat: shift toggles and advanced sym buttons (if present)
	try:
		for btn_attr_name in ('vk_shift_left_button', 'vk_shift_right_button'):
			btn_ref = getattr(app, btn_attr_name, None)
			if btn_ref:
				non_repeating.add(btn_ref)
	except Exception:
		pass
	try:
		non_repeating.add(sym_adv_button)  # type: ignore[name-defined]
		non_repeating.add(sym2_adv_button)  # type: ignore[name-defined]
	except Exception:
		pass
	if repeat_enabled:
		for btn in all_keyboard_buttons:
			if btn in non_repeating:
				continue
			try:
				_bind_press_hold(btn, btn.invoke, initial_delay=repeat_initial, interval=repeat_interval)
			except Exception:
				pass

	# --- Live updates (real-time from Options tab), including layout mode switch ---
	advanced_mode_state = advanced  # remember current

	def _rebind_repeat_all():
		nonlocal repeat_initial, repeat_interval, repeat_enabled
		repeat_enabled = is_repeat_enabled()
		repeat_initial, repeat_interval = get_repeat_timings()
		if repeat_enabled:
			for btn in all_keyboard_buttons:
				if btn in non_repeating:
					continue
				try:
					_bind_press_hold(btn, btn.invoke, initial_delay=repeat_initial, interval=repeat_interval)
				except Exception:
					pass
		else:
			# If repeat disabled later, ensure no lingering handlers
			for btn in all_keyboard_buttons:
				if btn in non_repeating:
					continue
				try:
					_bind_press_hold(btn, btn.invoke, initial_delay=repeat_initial, interval=repeat_interval)
				except Exception:
					pass

	def _apply_theme_all():
		for keyboard_button in all_keyboard_buttons:
			try:
				keyboard_button.config(
					bg=getattr(app, 'dynamic_button', '#333333'),
					fg=getattr(app, 'dynamic_text', '#ffffff'),
					activebackground=getattr(app, 'dynamic_bg', '#444444'),
					activeforeground=getattr(app, 'dynamic_text', '#ffffff'),
				)
			except Exception:
				pass

	def _apply_live_settings_from_app():
		nonlocal advanced_mode_state
		try:
			_rebind_repeat_all()
			_apply_theme_all()
			new_mode = is_advanced_mode()
			if new_mode != advanced_mode_state:
				advanced_mode_state = new_mode
				try:
					geo = keyboard_root.geometry()
				except Exception:
					geo = None
				_internal_close_keyboard()
				new_root = open_virtual_keyboard(app)
				try:
					if geo:
						new_root.geometry(geo)
				except Exception:
					pass
				return
		except Exception:
			pass

	def _wrapped_on_vk_settings_changed(*_a, **_kw):
		try:
			if callable(_original_on_vk_settings_changed):
				_original_on_vk_settings_changed(*_a, **_kw)
		except Exception:
			pass
		_apply_live_settings_from_app()

	# Install live-update hook while this window is open
	try:
		app.on_vk_settings_changed = _wrapped_on_vk_settings_changed
	except Exception:
		pass

	def _internal_close_keyboard():
		# Restore original callback
		try:
			app.on_vk_settings_changed = _original_on_vk_settings_changed
		except Exception:
			pass
		try:
			if keyboard_root in getattr(app, 'opened_windows', []):
				app.opened_windows.remove(keyboard_root)
		except Exception:
			pass
		try:
			app.vk_active = False
		except Exception:
			pass
		try:
			keyboard_root.destroy()
		except Exception:
			pass

	# Public close handler
	def close_keyboard():
		_internal_close_keyboard()

	keyboard_root.protocol('WM_DELETE_WINDOW', close_keyboard)

	# Geometry placement near main window bottom center
	keyboard_root.update_idletasks()
	try:
		window_width, window_height = keyboard_root.winfo_width(), keyboard_root.winfo_height()
		app_x, app_y = (app.winfo_x()), (app.winfo_y())
		app_width, app_height = app.winfo_width(), app.winfo_height()
		mid_x, mid_y = round(app_x + (app_width / 2) - (window_width / 2)), round(app_height + app_y - window_height)
		if abs(mid_y - app.winfo_screenheight()) <= 80:
			mid_y = app.winfo_screenheight() // 2
		keyboard_root.geometry(f'{window_width}x{window_height}+{mid_x}+{mid_y}')
	except Exception:
		pass

	try:
		if app.limit_w_s.get():
			keyboard_root.resizable(False, False)
	except Exception:
		pass

	# Initial mode
	set_keyboard_mode('lower')

	# Size tracking integration
	try:
		app.vk_sizes = keyboard_root.winfo_width(), keyboard_root.winfo_height()
		app.limit_list.append([keyboard_root, app.vk_sizes])
	except Exception:
		pass

	# Inform the main file (optional hook)
	try:
		if callable(getattr(app, 'on_vk_opened', None)):
			app.on_vk_opened('advanced' if advanced else 'compact')
	except Exception:
		pass

	# Record entry
	try:
		time_string = datetime.now().strftime('%H:%M:%S')
		app.record_list.append(f'> [{time_string}] - Virtual Keyboard tool window opened')
	except Exception:
		pass

	return keyboard_root
