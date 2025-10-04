# Full-featured Calculator popup, modeled after encryption_popup.py style:
# - Input validation (length, allowed names/chars, balanced parentheses)
# - Robust error handling (NumExpr, ZeroDivisionError, etc.)
# - Constants (pi, e) and trig support with optional degrees mode
# - Debounced auto-calc, keyboard shortcuts, inline status messages
# - History (list + Up/Down recall + double-click reuse)
# - Toggleable keypad and operator panel, selection-aware insert

import math
import re
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import base64
import hashlib
import urllib.parse
import json
import os

# from dependencies.universal_functions import *

try:
	import numexpr as ne
except Exception:
	ne = None


def open_calculator(app, mode='advanced'):
	'''
	Open the Calculator popup window.
	'app' is your main application instance.
	'mode' can be 'basic' or 'advanced' to control the UI layout.
	'''
	if ne is None:
		messagebox.showerror(getattr(app, 'title_struct', '') + ' error',
							 'NumExpr is not available. Please install "numexpr".')
		return

	# Reduce threads for UI responsiveness
	try:
		ne.set_num_threads(1)
	except Exception:
		pass

	# ---------------- config ----------------
	MAX_LEN = 200
	CONFIG_FILE = 'calc_state.json'
	ALLOWED_FUNCTIONS = {
		'sin', 'cos', 'tan', 'sqrt', 'log', 'exp',
		'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh',
		'asinh', 'acosh', 'atanh', 'log10', 'log1p',
		'abs', 'ceil', 'floor', 'rad2deg', 'deg2rad', 'round', 'where'
	}
	ALLOWED_CONSTS = {'pi', 'e', 'M'}
	# This will be updated dynamically with user variables
	ALLOWED_NAMES = ALLOWED_FUNCTIONS | ALLOWED_CONSTS
	
	# --- Button Styles ---
	MODERN_BTN_STYLE = {'relief': tk.FLAT, 'bd': 1}
	CLASSIC_BTN_STYLE = {'relief': tk.RAISED, 'bd': 2, 'bg': '#E0E0E0', 'activebackground': '#C0C0C0'}
	SPECIAL_BTN_STYLE = {'relief': tk.RAISED, 'bd': 2, 'bg': '#F3B664', 'activebackground': '#E0A050'}
	COPY_BTN_STYLE = {'relief': tk.FLAT, 'bd': 1, 'fg': 'blue'}


	# ---------------- helpers ----------------
	def owner_popup():
		custom_title = 'Calculator'
		if hasattr(app, 'make_pop_ups_window') and callable(getattr(app, 'make_pop_ups_window')):
			return app.make_pop_ups_window(open_calculator, custom_title=custom_title)
		parent = getattr(app, 'root', None)
		if not isinstance(parent, tk.Misc):
			parent = tk._get_default_root()
		if not isinstance(parent, tk.Misc):
			parent = tk.Tk()
		t = tk.Toplevel(parent)
		t.title(custom_title)
		return t

	def set_status(msg, ok=False, duration=3000):
		status_var.set(msg)
		status_label.config(fg='green' if ok else 'red')
		if duration:
			status_label.after(duration, clear_status)

	def clear_status():
		status_var.set('')
		status_label.config(fg='grey')

	def balanced_parens(s: str) -> bool:
		count = 0
		for ch in s:
			if ch == '(':
				count += 1
			elif ch == ')':
				count -= 1
			if count < 0:
				return False
		return count == 0

	def degrees_wrap(expr: str) -> str:
		# Replace trig functions with their degree-based equivalents
		# sin(x) -> sin(deg2rad(x)), asin(x) -> rad2deg(asin(x))
		expr = expr.replace('sin(', 'sin(deg2rad(')
		expr = expr.replace('cos(', 'cos(deg2rad(')
		expr = expr.replace('tan(', 'tan(deg2rad(')
		# Inverse functions
		expr = expr.replace('asin(', 'rad2deg(asin(')
		expr = expr.replace('acos(', 'rad2deg(acos(')
		expr = expr.replace('atan(', 'rad2deg(atan(')
		return expr

	def validate_expr(expr: str) -> bool:
		# Now checks against dynamic ALLOWED_NAMES
		if not expr.strip():
			set_status('Empty expression')
			return False
		if len(expr) > MAX_LEN:
			messagebox.showwarning(getattr(app, 'title_struct', '') + ' warning',
								   f'Expression too long (>{MAX_LEN} chars)')
			return False
		if not re.fullmatch(r"[0-9\s\+\-\*/%\.,\(\)A-Za-z_]*", expr):
			messagebox.showerror(getattr(app, 'title_struct', '') + ' error',
								 'Unsupported characters in expression')
			return False
		names = re.findall(r"[A-Za-z_]+", expr)
		# Update allowed names with current variables
		current_allowed = ALLOWED_NAMES
		if mode == 'advanced':
			current_allowed = current_allowed | set(user_variables.keys())
		unknown = [n for n in names if n not in current_allowed]
		if unknown:
			messagebox.showerror(getattr(app, 'title_struct', '') + ' error',
								 f'Unknown name(s): {", ".join(sorted(set(unknown)))}')
			return False
		if not balanced_parens(expr):
			messagebox.showerror(getattr(app, 'title_struct', '') + ' error',
								 'Unbalanced parentheses')
			return False
		return True

	# ---------------- state ----------------
	app.ins_equation = ''
	app.extra_calc_ui = False
	history = []
	hist_index = [-1]
	_debounce_id = {'id': None}
	user_variables = {}
	memory_value = [0.0]

	# ---------------- UI build ----------------
	calc_root = owner_popup()

	# Main layout frames
	left_frame = tk.Frame(calc_root)
	left_frame.pack(side='left', fill='both', expand=True)

	# --- Notebook for tabs ---
	notebook = ttk.Notebook(left_frame)
	notebook.pack(expand=True, fill='both', padx=5, pady=5)

	calculator_tab = ttk.Frame(notebook)
	history_tab = ttk.Frame(notebook)
	notebook.add(calculator_tab, text='Calculator')

	if mode == 'advanced':
		programmer_tab = ttk.Frame(notebook)
		converter_tab = ttk.Frame(notebook)
		datetime_tab = ttk.Frame(notebook)
		vars_tab = ttk.Frame(notebook)
		notebook.add(programmer_tab, text='Programmer')
		notebook.add(converter_tab, text='Converter')
		notebook.add(datetime_tab, text='Date & Time')
		notebook.add(vars_tab, text='Variables')
	
	notebook.add(history_tab, text='History')

	# Local fallbacks for copy/link
	def copy_text(text: str):
		try:
			if hasattr(app, 'copy') and callable(getattr(app, 'copy')):
				app.copy(text)
			else:
				calc_root.clipboard_clear()
				calc_root.clipboard_append(text)
			set_status("Copied to clipboard", ok=True)
		except Exception:
			pass

	def open_link(url: str):
		try:
			if hasattr(app, 'ex_links') and callable(getattr(app, 'ex_links')):
				app.ex_links(link=url)
				return
		except Exception:
			pass
		try:
			import webbrowser
			webbrowser.open(url)
		except Exception:
			pass

	# Editor insertion helpers
	def _editor_has_selection() -> bool:
		try:
			app.EgonTE.index('sel.first')
			return True
		except Exception:
			return False

	def _editor_insert_at_caret(text: str):
		try:
			if hasattr(app, 'get_pos'):
				app.EgonTE.insert(app.get_pos(), text)
			else:
				app.EgonTE.insert('insert', text)
		except Exception:
			pass

	def _editor_replace_selection(text: str):
		try:
			app.EgonTE.delete('sel.first', 'sel.last')
			_editor_insert_at_caret(text)
		except Exception:
			_editor_insert_at_caret(text)

	def insert_into_editor(text: str, *, replace_if_selected: bool = True, add_space: bool = True,
						   add_newline: bool = False):
		if not text:
			return
		suffix = (' ' if add_space else '') + ('\n' if add_newline else '')
		try:
			if replace_if_selected and _editor_has_selection():
				_editor_replace_selection(text + suffix)
			else:
				_editor_insert_at_caret(text + suffix)
		except Exception:
			pass

	# --- Calculator Tab ---
	calc_content_frame = tk.Frame(calculator_tab)
	calc_content_frame.pack(padx=10, pady=10)

	title = tk.Label(calc_content_frame, text='Calculator', font=getattr(app, 'titles_font', 'arial 12 bold'))
	introduction_text = tk.Label(calc_content_frame, text='Enter an expression below:', font='arial 10 underline')
	last_calc = tk.Entry(calc_content_frame, relief=tk.RIDGE, justify='center', width=30, state='readonly')
	calc_entry = tk.Entry(calc_content_frame, relief=tk.RIDGE, justify='center', width=30)
	status_var = tk.StringVar(value='')
	status_label = tk.Label(calc_content_frame, textvariable=status_var, fg='grey')

	# --- Control Frames ---
	actions_frame = tk.Frame(calc_content_frame)
	settings_frame = tk.Frame(calc_content_frame)
	view_frame = tk.Frame(calc_content_frame)

	enter = tk.Button(actions_frame, text='Calculate', font='arial 10 bold', **MODERN_BTN_STYLE) # Tooltip: "Calculate the expression (Enter)"
	copy_button = tk.Button(actions_frame, text='Copy', **MODERN_BTN_STYLE) # Tooltip: "Copy the last result to the clipboard"
	insert_button = tk.Button(actions_frame, text='Insert...', **MODERN_BTN_STYLE) # Tooltip: "Insert result into editor (Ctrl+I). Right-click for options (Ctrl+E)"
	enter.pack(side=tk.LEFT, padx=5)
	copy_button.pack(side=tk.LEFT, padx=5)
	insert_button.pack(side=tk.LEFT, padx=5)

	degrees_mode = tk.BooleanVar(value=False)
	degrees_cb = tk.Checkbutton(settings_frame, text='Degrees', variable=degrees_mode) # Tooltip: "Use degrees for trigonometric functions"
	auto_calc = tk.BooleanVar(value=True)
	auto_cb = tk.Checkbutton(settings_frame, text='Auto-calc', variable=auto_calc) # Tooltip: "Automatically calculate result while typing"
	degrees_cb.pack(side=tk.LEFT)
	auto_cb.pack(side=tk.LEFT, padx=10)

	show_op = tk.Button(view_frame, text='Show Functions', **MODERN_BTN_STYLE) # Tooltip: "Toggle the advanced functions panel"
	calc_ui = tk.Button(view_frame, text='Show Keypad', **MODERN_BTN_STYLE) # Tooltip: "Toggle the numeric keypad"
	show_op.pack(side=tk.LEFT, padx=5)
	calc_ui.pack(side=tk.LEFT, padx=5)

	# --- Advanced Calculator Features (only in 'advanced' mode) ---
	if mode == 'advanced':
		adv_frame = tk.Frame(calc_content_frame)
		adv_frame.pack(pady=10)

		# Memory controls
		mem_frame = tk.Frame(adv_frame)
		mem_frame.pack(pady=5)
		mem_display_var = tk.StringVar(value="M = 0.0")
		tk.Label(mem_frame, textvariable=mem_display_var, fg='#555').pack(side=tk.LEFT, padx=5)
		
		def update_mem_display():
			mem_display_var.set(f"M = {memory_value[0]:g}")

		def mem_clear():
			memory_value[0] = 0.0
			update_mem_display()

		def mem_recall():
			insert_token('M')

		def mem_add():
			try:
				val = float(calc_entry.get())
				memory_value[0] += val
				update_mem_display()
			except (ValueError, IndexError):
				set_status("Invalid number for M+")

		def mem_sub():
			try:
				val = float(calc_entry.get())
				memory_value[0] -= val
				update_mem_display()
			except (ValueError, IndexError):
				set_status("Invalid number for M-")

		tk.Button(mem_frame, text="MC", command=mem_clear, **CLASSIC_BTN_STYLE, width=4).pack(side=tk.LEFT, padx=2)
		tk.Button(mem_frame, text="MR", command=mem_recall, **CLASSIC_BTN_STYLE, width=4).pack(side=tk.LEFT, padx=2)
		tk.Button(mem_frame, text="M+", command=mem_add, **CLASSIC_BTN_STYLE, width=4).pack(side=tk.LEFT, padx=2)
		tk.Button(mem_frame, text="M-", command=mem_sub, **CLASSIC_BTN_STYLE, width=4).pack(side=tk.LEFT, padx=2)

		# Developer result display
		dev_display_frame = tk.Frame(adv_frame)
		dev_display_frame.pack(pady=5)
		hex_var = tk.StringVar()
		bin_var = tk.StringVar()
		tk.Label(dev_display_frame, text="Hex:").pack(side=tk.LEFT)
		tk.Entry(dev_display_frame, textvariable=hex_var, state='readonly', width=15).pack(side=tk.LEFT, padx=5)
		tk.Label(dev_display_frame, text="Bin:").pack(side=tk.LEFT)
		tk.Entry(dev_display_frame, textvariable=bin_var, state='readonly', width=20).pack(side=tk.LEFT, padx=5)

	# --- History Tab ---
	hist_list_frame = tk.Frame(history_tab)
	hist_list_frame.pack(fill='both', expand=True, padx=5, pady=5)
	hist_scroll = tk.Scrollbar(hist_list_frame, orient=tk.VERTICAL)
	hist_listbox = tk.Listbox(hist_list_frame, selectmode=tk.EXTENDED, yscrollcommand=hist_scroll.set)
	hist_scroll.config(command=hist_listbox.yview)
	hist_scroll.pack(side=tk.RIGHT, fill=tk.Y)
	hist_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
	
	hist_buttons_frame = tk.Frame(history_tab)
	hist_buttons_frame.pack(fill='x', padx=5, pady=(0, 5))
	delete_hist_button = tk.Button(hist_buttons_frame, text='Delete Selected', **MODERN_BTN_STYLE) # Tooltip: "Delete the selected history items (Delete)"
	delete_hist_button.pack(side=tk.LEFT, expand=True, fill='x', padx=(0,2))
	clear_hist_button = tk.Button(hist_buttons_frame, text='Clear All History', **MODERN_BTN_STYLE) # Tooltip: "Clear all saved history items"
	clear_hist_button.pack(side=tk.LEFT, expand=True, fill='x', padx=(2,0))

	if mode == 'advanced':
		# --- Programmer Tab ---
		prog_content_frame = tk.Frame(programmer_tab)
		prog_content_frame.pack(padx=10, pady=10, fill='both', expand=True)

		prog_entry = tk.Entry(prog_content_frame, relief=tk.RIDGE, justify='right', font='monospace 12')
		prog_entry.pack(fill='x', pady=(0, 5))

		prog_btns_frame = tk.Frame(prog_content_frame)
		prog_btns_frame.pack(fill='x', pady=5)

		prog_ops_frame = tk.Frame(prog_btns_frame)
		prog_ops_frame.pack(side=tk.LEFT, fill='x', expand=True)

		prog_prefix_frame = tk.Frame(prog_btns_frame)
		prog_prefix_frame.pack(side=tk.LEFT, padx=(10,0))

		def prog_insert(token, spaces=True):
			try:
				s, e = prog_entry.index('sel.first'), prog_entry.index('sel.last')
				prog_entry.delete(s, e)
			except Exception:
				pass
			insert_text = f' {token} ' if spaces else token
			prog_entry.insert(tk.INSERT, insert_text)
			prog_entry.focus_set()

		prog_ops = [('<<', '<<'), ('>>', '>>'), ('&', '&'), ('|', '|'), ('^', '^'), ('~', '~'), ('(', '('), (')', ')')]
		for i, (label, tok) in enumerate(prog_ops):
			r, c = divmod(i, 4)
			is_unary = tok in ['~', '(', ')']
			tk.Button(prog_ops_frame, text=label, command=lambda t=tok, s=not is_unary: prog_insert(t, s)).grid(row=r, column=c, padx=1, pady=1, sticky='ew')

		tk.Button(prog_prefix_frame, text="0x", command=lambda: prog_insert('0x', False)).pack(fill='x') # Tooltip: "Insert hex prefix"
		tk.Button(prog_prefix_frame, text="0b", command=lambda: prog_insert('0b', False)).pack(fill='x') # Tooltip: "Insert binary prefix"
		tk.Button(prog_prefix_frame, text="0o", command=lambda: prog_insert('0o', False)).pack(fill='x') # Tooltip: "Insert octal prefix"
		tk.Button(prog_prefix_frame, text="C", command=lambda: prog_entry.delete(0, tk.END), **SPECIAL_BTN_STYLE).pack(fill='x', pady=(5,0))

		results_frame = tk.Frame(prog_content_frame)
		results_frame.pack(pady=10, fill='both', expand=True)
		
		results_vars = {
			'HEX': tk.StringVar(value='0'), 'DEC': tk.StringVar(value='0'),
			'OCT': tk.StringVar(value='0'), 'BIN': tk.StringVar(value='0'),
			'QWORD': tk.StringVar(value='0'), 'DWORD': tk.StringVar(value='0'),
			'WORD': tk.StringVar(value='0'), 'BYTE': tk.StringVar(value='0'),
		}

		for i, base in enumerate(['HEX', 'DEC', 'OCT', 'BIN']):
			f = tk.Frame(results_frame)
			f.pack(fill='x', pady=2)
			tk.Label(f, text=f'{base: <3}', font='monospace 10', width=4, anchor='w').pack(side='left')
			entry = tk.Entry(f, textvariable=results_vars[base], state='readonly', font='monospace 11', relief=tk.FLAT, justify='right')
			entry.pack(side='left', fill='x', expand=True)
			tk.Button(f, text="Copy", command=lambda v=results_vars[base]: copy_text(v.get()), **COPY_BTN_STYLE).pack(side='left', padx=(5,0))

		tk.Frame(results_frame, height=1, bg="#ccc").pack(fill='x', pady=5)

		for i, size in enumerate(['QWORD', 'DWORD', 'WORD', 'BYTE']):
			f = tk.Frame(results_frame)
			f.pack(fill='x', pady=2)
			tk.Label(f, text=f'{size: <5}', font='monospace 10', width=6, anchor='w').pack(side='left')
			entry = tk.Entry(f, textvariable=results_vars[size], state='readonly', font='monospace 11', relief=tk.FLAT, justify='right')
			entry.pack(side='left', fill='x', expand=True)
			tk.Button(f, text="Copy", command=lambda v=results_vars[size]: copy_text(v.get()), **COPY_BTN_STYLE).pack(side='left', padx=(5,0))

		prog_status_var = tk.StringVar()
		prog_status_label = tk.Label(prog_content_frame, textvariable=prog_status_var, fg='red', wraplength=300)
		prog_status_label.pack(fill='x')

		_prog_debounce_id = {'id': None}

		def prog_recalculate(*_):
			prog_status_var.set('')
			expr = prog_entry.get().strip()
			if not expr:
				for v in results_vars.values(): v.set('0')
				return

			try:
				eval_expr = re.sub(r'0b([01]+)', lambda m: str(int(m.group(1), 2)), expr, flags=re.IGNORECASE)
				eval_expr = re.sub(r'0o([0-7]+)', lambda m: str(int(m.group(1), 8)), eval_expr, flags=re.IGNORECASE)
				
				# Add user variables to the evaluation context
				local_ns = user_variables.copy()
				result = ne.evaluate(eval_expr, local_dict=local_ns).item()
				result = int(result)

				results_vars['HEX'].set(hex(result).upper().replace('X', 'x'))
				results_vars['DEC'].set(str(result))
				results_vars['OCT'].set(oct(result).upper().replace('O', 'o'))
				results_vars['BIN'].set(bin(result).upper().replace('B', 'b'))

				# Integer sizes
				results_vars['QWORD'].set(str(result & 0xFFFFFFFFFFFFFFFF))
				results_vars['DWORD'].set(str(result & 0xFFFFFFFF))
				results_vars['WORD'].set(str(result & 0xFFFF))
				results_vars['BYTE'].set(str(result & 0xFF))

			except Exception as e:
				prog_status_var.set(f'Error: {e}')

		def schedule_prog_eval(*_):
			if _prog_debounce_id['id']:
				try: prog_entry.after_cancel(_prog_debounce_id['id'])
				except Exception: pass
			_prog_debounce_id['id'] = prog_entry.after(300, prog_recalculate)

		prog_entry.bind('<KeyRelease>', schedule_prog_eval)

		# --- Variables Tab ---
		vars_content_frame = tk.Frame(vars_tab, padx=10, pady=10)
		vars_content_frame.pack(fill='both', expand=True)

		vars_list_frame = tk.Frame(vars_content_frame)
		vars_list_frame.pack(fill='both', expand=True, pady=5)
		vars_scroll = tk.Scrollbar(vars_list_frame, orient=tk.VERTICAL)
		vars_listbox = tk.Listbox(vars_list_frame, selectmode=tk.SINGLE, yscrollcommand=vars_scroll.set)
		vars_scroll.config(command=vars_listbox.yview)
		vars_scroll.pack(side=tk.RIGHT, fill=tk.Y)
		vars_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

		vars_edit_frame = tk.Frame(vars_content_frame)
		vars_edit_frame.pack(fill='x', pady=5)

		var_name_entry = tk.Entry(vars_edit_frame, width=15)
		var_val_entry = tk.Entry(vars_edit_frame, width=15)
		var_name_entry.pack(side=tk.LEFT, padx=(0, 5), fill='x', expand=True)
		var_val_entry.pack(side=tk.LEFT, fill='x', expand=True)

		vars_btn_frame = tk.Frame(vars_content_frame)
		vars_btn_frame.pack(fill='x')

		def on_var_select(evt):
			try:
				idx = vars_listbox.curselection()[0]
				name = vars_listbox.get(idx).split('=')[0].strip()
				val = user_variables[name]
				var_name_entry.delete(0, tk.END)
				var_name_entry.insert(0, name)
				var_val_entry.delete(0, tk.END)
				var_val_entry.insert(0, val)
			except IndexError:
				pass # No selection

		def refresh_vars_listbox():
			vars_listbox.delete(0, tk.END)
			for name, val in sorted(user_variables.items()):
				vars_listbox.insert(tk.END, f' {name} = {val}')

		def save_variable():
			name = var_name_entry.get().strip()
			val_str = var_val_entry.get().strip()
			if not re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*', name):
				messagebox.showerror('Invalid Name', 'Variable name must be a valid identifier (letters, numbers, underscores, not starting with a number).')
				return
			if name in ALLOWED_FUNCTIONS or name in ALLOWED_CONSTS:
				messagebox.showerror('Invalid Name', f'"{name}" is a reserved function/constant name.')
				return
			try:
				# Try to evaluate the value to store it as a number
				val = ne.evaluate(val_str).item()
				user_variables[name] = val
				refresh_vars_listbox()
				var_name_entry.delete(0, tk.END)
				var_val_entry.delete(0, tk.END)
			except Exception as e:
				messagebox.showerror('Invalid Value', f'Could not evaluate value: {e}')

		def remove_variable():
			name = var_name_entry.get().strip()
			if name in user_variables:
				if messagebox.askyesno('Confirm', f'Are you sure you want to remove variable "{name}"?'):
					del user_variables[name]
					refresh_vars_listbox()
					var_name_entry.delete(0, tk.END)
					var_val_entry.delete(0, tk.END)
			else:
				messagebox.showwarning('Not Found', 'Variable not found or name does not match selection.')

		vars_listbox.bind('<<ListboxSelect>>', on_var_select)
		tk.Button(vars_btn_frame, text='Save', command=save_variable, **MODERN_BTN_STYLE).pack(side=tk.LEFT, fill='x', expand=True, padx=(0, 2))
		tk.Button(vars_btn_frame, text='Remove', command=remove_variable, **MODERN_BTN_STYLE).pack(side=tk.LEFT, fill='x', expand=True, padx=(2, 0))

		# --- Converter Tab ---
		UNIT_CATEGORIES = {
			"Data Size": {
				"Bytes": 1,
				"Kilobytes (10³ B)": 10**3,
				"Kibibytes (2¹⁰ B)": 2**10,
				"Megabytes (10⁶ B)": 10**6,
				"Mebibytes (2²⁰ B)": 2**20,
				"Gigabytes (10⁹ B)": 10**9,
				"Gibibytes (2³⁰ B)": 2**30,
				"Terabytes (10¹² B)": 10**12,
				"Tebibytes (2⁴⁰ B)": 2**40,
			},
			"Length": {
				"Meters": 1.0,
				"Kilometers": 1000.0,
				"Centimeters": 0.01,
				"Millimeters": 0.001,
				"Miles": 1609.34,
				"Yards": 0.9144,
				"Feet": 0.3048,
				"Inches": 0.0254,
				"Nautical Miles": 1852.0,
			},
			"Mass": {
				"Grams": 1.0,
				"Kilograms": 1000.0,
				"Milligrams": 0.001,
				"Pounds (lb)": 453.592,
				"Ounces (oz)": 28.3495,
			},
			"Speed": {
				"Meters/sec (m/s)": 1.0,
				"Kilometers/hr (km/h)": 0.277778,
				"Miles/hr (mph)": 0.44704,
				"Feet/sec (ft/s)": 0.3048,
			},
			"Time": {
				"Nanoseconds": 1 / 1e9,
				"Microseconds": 1 / 1e6,
				"Milliseconds": 1 / 1e3,
				"Seconds": 1.0,
				"Minutes": 60.0,
				"Hours": 3600.0,
				"Days": 86400.0,
				"Weeks": 604800.0,
			},
			"Temperature": {
				"Celsius": None, "Fahrenheit": None, "Kelvin": None
			}
		}

		converter_content_frame = tk.Frame(converter_tab, padx=10, pady=10)
		converter_content_frame.pack(fill='both', expand=True)

		tk.Label(converter_content_frame, text="Select a category to begin conversion.", font='arial 10').pack(pady=5)
		
		category_var = tk.StringVar()
		category_menu = ttk.Combobox(converter_content_frame, textvariable=category_var, values=list(UNIT_CATEGORIES.keys()), state='readonly')
		category_menu.pack(fill='x', pady=5)

		conversion_frame = tk.Frame(converter_content_frame)
		conversion_frame.pack(fill='both', expand=True, pady=10)

		from_frame = tk.Frame(conversion_frame)
		from_frame.pack(fill='x', pady=5)
		from_val_var = tk.StringVar()
		from_entry = tk.Entry(from_frame, textvariable=from_val_var)
		from_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
		from_unit_var = tk.StringVar()
		from_unit_menu = ttk.Combobox(from_frame, textvariable=from_unit_var, state='readonly', width=15)
		from_unit_menu.pack(side='left')

		swap_btn = tk.Button(conversion_frame, text="Swap", **MODERN_BTN_STYLE) # Tooltip: "Swap the from and to units"
		swap_btn.pack()

		to_frame = tk.Frame(conversion_frame)
		to_frame.pack(fill='x', pady=5)
		to_val_var = tk.StringVar()
		to_entry = tk.Entry(to_frame, textvariable=to_val_var)
		to_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
		to_unit_var = tk.StringVar()
		to_unit_menu = ttk.Combobox(to_frame, textvariable=to_unit_var, state='readonly', width=15)
		to_unit_menu.pack(side='left')
		tk.Button(to_frame, text="Copy", command=lambda: copy_text(to_val_var.get()), **COPY_BTN_STYLE).pack(side='left', padx=(5,0))

		_conv_debounce_id = {'id': None}
		_last_active_entry = {'widget': from_entry}

		def on_category_select(*_):
			category = category_var.get()
			units = list(UNIT_CATEGORIES.get(category, {}).keys())
			from_unit_menu['values'] = units
			to_unit_menu['values'] = units
			if units:
				from_unit_var.set(units[0])
				to_unit_var.set(units[1] if len(units) > 1 else units[0])
			from_val_var.set('1')
			schedule_conversion()

		def convert_units():
			try:
				category = category_var.get()
				active_entry = _last_active_entry['widget']
				
				if active_entry == from_entry:
					val_str, from_unit, to_unit = from_val_var.get(), from_unit_var.get(), to_unit_var.get()
					target_var = to_val_var
				else: # to_entry is active
					val_str, from_unit, to_unit = to_val_var.get(), to_unit_var.get(), from_unit_var.get()
					target_var = from_val_var

				val = float(val_str)
				
				if category == "Temperature":
					if from_unit == to_unit: new_val = val
					# To Celsius
					elif from_unit == "Fahrenheit" and to_unit == "Celsius": new_val = (val - 32) * 5/9
					elif from_unit == "Kelvin" and to_unit == "Celsius": new_val = val - 273.15
					# From Celsius
					elif from_unit == "Celsius" and to_unit == "Fahrenheit": new_val = (val * 9/5) + 32
					elif from_unit == "Celsius" and to_unit == "Kelvin": new_val = val + 273.15
					# Other
					elif from_unit == "Fahrenheit" and to_unit == "Kelvin": new_val = (val - 32) * 5/9 + 273.15
					elif from_unit == "Kelvin" and to_unit == "Fahrenheit": new_val = (val - 273.15) * 9/5 + 32
					else: new_val = val # Should not happen
					target_var.set(f'{new_val:g}')
					return

				units = UNIT_CATEGORIES.get(category)
				if not units: return
				base_val = val * units[from_unit]
				new_val = base_val / units[to_unit]
				target_var.set(f'{new_val:g}')

			except (ValueError, ZeroDivisionError, KeyError):
				to_val_var.set('')
				from_val_var.set('')
			except Exception:
				pass

		def schedule_conversion(*_):
			if _conv_debounce_id['id']:
				try: calc_root.after_cancel(_conv_debounce_id['id'])
				except Exception: pass
			_conv_debounce_id['id'] = calc_root.after(250, convert_units)

		def swap_units():
			from_u, to_u = from_unit_var.get(), to_unit_var.get()
			from_v, to_v = from_val_var.get(), to_val_var.get()
			from_unit_var.set(to_u)
			to_unit_var.set(from_u)
			from_val_var.set(to_v)
			to_val_var.set(from_v)
			schedule_conversion()

		swap_btn.config(command=swap_units)
		from_entry.bind('<FocusIn>', lambda e: _last_active_entry.update({'widget': from_entry}))
		to_entry.bind('<FocusIn>', lambda e: _last_active_entry.update({'widget': to_entry}))

		from_val_var.trace_add('write', schedule_conversion)
		to_val_var.trace_add('write', schedule_conversion)
		from_unit_var.trace_add('write', schedule_conversion)
		to_unit_var.trace_add('write', schedule_conversion)
		category_var.trace_add('write', on_category_select)

		category_menu.set(list(UNIT_CATEGORIES.keys())[0])

		# --- Date & Time Tab ---
		dt_content = tk.Frame(datetime_tab, padx=10, pady=10)
		dt_content.pack(fill='both', expand=True)

		# Timestamp converter
		ts_frame = ttk.LabelFrame(dt_content, text="Unix Timestamp Converter", padding=10)
		ts_frame.pack(fill='x', pady=5)
		ts_from_frame = tk.Frame(ts_frame)
		ts_from_frame.pack(fill='x', pady=2)
		tk.Label(ts_from_frame, text="Timestamp", width=10).pack(side='left')
		ts_var = tk.StringVar()
		ts_entry = tk.Entry(ts_from_frame, textvariable=ts_var)
		ts_entry.pack(fill='x', expand=True, side='left')
		tk.Button(ts_from_frame, text="Now", command=lambda: ts_var.set(str(datetime.now().timestamp())), **COPY_BTN_STYLE).pack(side='left', padx=5)

		ts_to_frame = tk.Frame(ts_frame)
		ts_to_frame.pack(fill='x', pady=2)
		tk.Label(ts_to_frame, text="UTC Date", width=10).pack(side='left')
		dt_var = tk.StringVar()
		dt_entry = tk.Entry(ts_to_frame, textvariable=dt_var)
		dt_entry.pack(fill='x', expand=True, side='left')
		tk.Button(ts_to_frame, text="Copy", command=lambda: copy_text(dt_var.get()), **COPY_BTN_STYLE).pack(side='left', padx=5)

		_ts_debounce_id = {'id': None}
		_last_ts_entry = {'widget': ts_entry}

		def convert_timestamp():
			try:
				if _last_ts_entry['widget'] == ts_entry:
					ts = float(ts_var.get())
					dt = datetime.utcfromtimestamp(ts)
					dt_var.set(dt.strftime('%Y-%m-%d %H:%M:%S'))
				else:
					dt_str = dt_var.get()
					dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
					ts_var.set(str(dt.timestamp()))
			except Exception:
				if _last_ts_entry['widget'] == ts_entry: dt_var.set('Invalid Timestamp')
				else: ts_var.set('Invalid Date Format')

		def schedule_ts_conversion(*_):
			if _ts_debounce_id['id']:
				try: calc_root.after_cancel(_ts_debounce_id['id'])
				except Exception: pass
			_ts_debounce_id['id'] = calc_root.after(300, convert_timestamp)

		ts_entry.bind('<FocusIn>', lambda e: _last_ts_entry.update({'widget': ts_entry}))
		dt_entry.bind('<FocusIn>', lambda e: _last_ts_entry.update({'widget': dt_entry}))
		ts_var.trace_add('write', schedule_ts_conversion)
		dt_var.trace_add('write', schedule_ts_conversion)

		# Date calculator
		add_frame = ttk.LabelFrame(dt_content, text="Add/Subtract Time", padding=10)
		add_frame.pack(fill='x', pady=5)
		add_start_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
		add_res_var = tk.StringVar()

		add_start_frame = tk.Frame(add_frame)
		add_start_frame.pack(fill='x')
		tk.Label(add_start_frame, text="Start Date", width=10).pack(side='left')
		tk.Entry(add_start_frame, textvariable=add_start_date_var).pack(fill='x', expand=True, side='left')
		tk.Button(add_start_frame, text="Now", command=lambda: add_start_date_var.set(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), **COPY_BTN_STYLE).pack(side='left', padx=5)

		add_op_frame = tk.Frame(add_frame)
		add_op_frame.pack(fill='x', pady=5)
		add_days_var = tk.StringVar(value="0")
		add_hours_var = tk.StringVar(value="0")
		add_mins_var = tk.StringVar(value="0")
		tk.Label(add_op_frame, text="Days:").grid(row=0, column=0, sticky='w')
		tk.Spinbox(add_op_frame, from_=-10000, to=10000, textvariable=add_days_var, width=7).grid(row=0, column=1)
		tk.Label(add_op_frame, text="Hours:").grid(row=0, column=2, sticky='w', padx=(10,0))
		tk.Spinbox(add_op_frame, from_=-1000, to=1000, textvariable=add_hours_var, width=7).grid(row=0, column=3)
		tk.Label(add_op_frame, text="Mins:").grid(row=0, column=4, sticky='w', padx=(10,0))
		tk.Spinbox(add_op_frame, from_=-1000, to=1000, textvariable=add_mins_var, width=7).grid(row=0, column=5)
		def clear_deltas():
			add_days_var.set("0")
			add_hours_var.set("0")
			add_mins_var.set("0")
		tk.Button(add_op_frame, text="Clear", command=clear_deltas, **MODERN_BTN_STYLE).grid(row=0, column=6, padx=(10,0))

		def calc_add_sub(subtract=False):
			try:
				start_dt = datetime.strptime(add_start_date_var.get(), '%Y-%m-%d %H:%M:%S')
				days = int(add_days_var.get() or 0)
				hours = int(add_hours_var.get() or 0)
				mins = int(add_mins_var.get() or 0)
				delta = timedelta(days=days, hours=hours, minutes=mins)
				final_dt = start_dt - delta if subtract else start_dt + delta
				add_res_var.set(final_dt.strftime('%Y-%m-%d %H:%M:%S'))
			except Exception as e:
				add_res_var.set(f"Error: {e}")

		add_btn_frame = tk.Frame(add_frame)
		add_btn_frame.pack(fill='x')
		tk.Button(add_btn_frame, text="Add", command=lambda: calc_add_sub(False), **MODERN_BTN_STYLE).pack(side=tk.LEFT, expand=True, fill='x', padx=(0,2))
		tk.Button(add_btn_frame, text="Subtract", command=lambda: calc_add_sub(True), **MODERN_BTN_STYLE).pack(side=tk.LEFT, expand=True, fill='x')

		add_res_frame = tk.Frame(add_frame)
		add_res_frame.pack(fill='x', pady=5)
		tk.Label(add_res_frame, text="Result", width=10).pack(side='left')
		tk.Entry(add_res_frame, textvariable=add_res_var, state='readonly').pack(fill='x', expand=True, side='left')
		tk.Button(add_res_frame, text="Copy", command=lambda: copy_text(add_res_var.get()), **COPY_BTN_STYLE).pack(side='left', padx=5)


	def on_hist_reuse(_evt=None):
		try:
			idxs = hist_listbox.curselection()
			if not idxs:
				return
			idx = idxs[0]
			expr, _res = history[idx]
			calc_entry.delete(0, tk.END)
			calc_entry.insert(0, expr)
			calc_entry.icursor(tk.END)
			hist_index[0] = idx
			notebook.select(calculator_tab)
		except Exception:
			pass

	# Layout for Calculator Tab
	title.pack(pady=(0, 5))
	introduction_text.pack()
	last_calc.pack(pady=2, fill='x', expand=True)
	calc_entry.pack(pady=2, fill='x', expand=True)
	status_label.pack(pady=(2, 5))
	actions_frame.pack(pady=4)
	settings_frame.pack(pady=4)
	view_frame.pack(pady=4)

	# --- Logic for Keypad and Operators ---
	def insert_token(token):
		try:
			s, e = calc_entry.index('sel.first'), calc_entry.index('sel.last')
			calc_entry.delete(s, e)
		except Exception:
			pass
		calc_entry.insert(tk.INSERT, str(token))
		clear_status()

	def safe_delete():
		try:
			sel_first = calc_entry.index('sel.first')
			sel_last = calc_entry.index('sel.last')
			calc_entry.delete(sel_first, sel_last)
			return
		except Exception:
			pass
		try:
			i = calc_entry.index(tk.INSERT)
			if int(i) > 0:
				calc_entry.delete(i - 1)
		except Exception:
			pass

	# --- UI Panels (Keypad and Functions) ---

	# Operators panel
	op_frame = tk.Frame(calc_content_frame)
	ops = [
		('sin', 'sin('), ('cos', 'cos('), ('tan', 'tan('), ('asin', 'asin('), ('acos', 'acos('), ('atan', 'atan('),
		('sinh', 'sinh('), ('cosh', 'cosh('), ('tanh', 'tanh('), ('asinh', 'asinh('), ('acosh', 'acosh('), ('atanh', 'atanh('),
		('sqrt', 'sqrt('), ('log', 'log('), ('log10', 'log10('), ('exp', 'exp('), ('abs', 'abs('), ('ceil', 'ceil('),
		('floor', 'floor('), ('round', 'round('), ('where', 'where('), ('pi', 'pi'), ('e', 'e'), ('pow', '**')
	]
	for i, (label, tok) in enumerate(ops):
		r, c = divmod(i, 6)
		tk.Button(op_frame, text=label, command=lambda t=tok: insert_token(t), **CLASSIC_BTN_STYLE).grid(row=r, column=c, padx=1, pady=1, sticky='ew')

	numexpr_link = 'https://numexpr.readthedocs.io/en/latest/user_guide.html'
	numexpr_tutorial = tk.Button(calc_content_frame, text='NumExpr tutorial',
								 command=lambda: open_link(numexpr_link),
								 relief=tk.FLAT, fg='blue', font='arial 10 underline')

	# Keypad frame (managed separately to the right)
	extra_frame = tk.Frame(calc_root)
	btn_props = {'height': 2, 'width': 4}

	# Top row: Controls
	tk.Button(extra_frame, text='(', command=lambda: insert_token('('), **CLASSIC_BTN_STYLE, **btn_props).grid(row=0, column=0, padx=1, pady=1)
	tk.Button(extra_frame, text=')', command=lambda: insert_token(')'), **CLASSIC_BTN_STYLE, **btn_props).grid(row=0, column=1, padx=1, pady=1)
	tk.Button(extra_frame, text='DEL', command=safe_delete, **SPECIAL_BTN_STYLE, **btn_props).grid(row=0, column=2, padx=1, pady=1)
	tk.Button(extra_frame, text='C', command=lambda: (calc_entry.delete(0, tk.END), clear_status()), **SPECIAL_BTN_STYLE, **btn_props).grid(row=0, column=3, padx=1, pady=1)

	# Number and operator rows
	keypad_buttons = [
		('7', '8', '9', '/'),
		('4', '5', '6', '*'),
		('1', '2', '3', '-'),
	]
	for r, row_buttons in enumerate(keypad_buttons, start=1):
		for c, text in enumerate(row_buttons):
			cmd = lambda t=text: insert_token(f' {t} ' if t in '/*-+' else t)
			tk.Button(extra_frame, text=text, command=cmd, **CLASSIC_BTN_STYLE, **btn_props).grid(row=r, column=c, padx=1, pady=1)

	# Bottom row
	tk.Button(extra_frame, text='0', command=lambda: insert_token('0'), **CLASSIC_BTN_STYLE, **btn_props).grid(row=4, column=0, columnspan=2, padx=1, pady=1, sticky='ew')
	tk.Button(extra_frame, text='.', command=lambda: insert_token('.'), **CLASSIC_BTN_STYLE, **btn_props).grid(row=4, column=2, padx=1, pady=1)
	tk.Button(extra_frame, text='+', command=lambda: insert_token(' + '), **CLASSIC_BTN_STYLE, **btn_props).grid(row=4, column=3, padx=1, pady=1)

	# Prefill from selection if numeric
	try:
		if hasattr(app, 'is_marked') and app.is_marked():
			sel = app.EgonTE.get('sel.first', 'sel.last')
			try:
				float(sel)
				calc_entry.insert('end', sel)
			except Exception:
				pass
	except Exception:
			pass

	# ---------------- logic ----------------
	def toggle_keypad():
		if not getattr(app, 'extra_calc_ui', False):
			extra_frame.pack(side='right', fill='y', padx=(0, 5), pady=5)
			calc_ui.config(text='Hide Keypad')
		else:
			extra_frame.pack_forget()
			calc_ui.config(text='Show Keypad')
		app.extra_calc_ui = not getattr(app, 'extra_calc_ui', False)

	def show_oper():
		show_op.config(text='Hide Functions', command=hide_oper)
		op_frame.pack(pady=(5,0))
		numexpr_tutorial.pack(pady=(0,5))

	def hide_oper():
		op_frame.pack_forget()
		numexpr_tutorial.pack_forget()
		show_op.config(text='Show Functions', command=show_oper)

	def _format_hist_item(expr, result, max_len=46):
		s = f"{expr} = {result}"
		return s if len(s) <= max_len else s[:max_len - 1] + '…'

	def push_history(expr: str, result) -> None:
		history.append((expr, str(result)))
		hist_listbox.insert(tk.END, _format_hist_item(expr, str(result)))
		hist_listbox.see(tk.END)
		hist_index[0] = len(history)
	
	def delete_selected_history(_=None):
		selected_indices = hist_listbox.curselection()
		if not selected_indices: return
		if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {len(selected_indices)} selected history item(s)?"):
			return
		# Iterate backwards to avoid index shifting issues
		for i in sorted(selected_indices, reverse=True):
			hist_listbox.delete(i)
			del history[i]
		hist_index[0] = len(history)

	def clear_history():
		if not history: return
		if messagebox.askyesno("Confirm Clear", "Are you sure you want to permanently clear the calculation history?"):
			history.clear()
			hist_listbox.delete(0, tk.END)
			hist_index[0] = -1


	def recall_history(delta: int):
		if not history:
			return
		idx = hist_index[0] + delta
		idx = max(0, min(len(history) - 1, idx))
		hist_index[0] = idx
		expr, _res = history[idx]
		calc_entry.delete(0, tk.END)
		calc_entry.insert(0, expr)
		calc_entry.icursor(tk.END)

	# Debounced auto-calc
	def schedule_eval(*_):
		clear_status()
		if not auto_calc.get():
			return
		if _debounce_id['id']:
			try:
				calc_entry.after_cancel(_debounce_id['id'])
			except Exception:
				pass
		_debounce_id['id'] = calc_entry.after(400, calculate_button)

	def calculate_button():
		expr = calc_entry.get()
		last_calc.configure(state='normal')
		last_calc.delete(0, tk.END)
		last_calc.insert(0, expr)
		last_calc.configure(state='readonly')

		if not validate_expr(expr):
			return

		eval_expr = degrees_wrap(expr) if degrees_mode.get() else expr
		try:
			# Combine built-in constants and user variables
			local_ns = {'pi': math.pi, 'e': math.e, 'deg2rad': math.radians, 'rad2deg': math.degrees}
			if mode == 'advanced':
				local_ns['M'] = memory_value[0]
				local_ns.update(user_variables)
			result = ne.evaluate(eval_expr, local_dict=local_ns)
			calc_entry.delete(0, tk.END)
			calc_entry.insert(0, str(result))
			app.ins_equation = str(result)
			push_history(expr, result)
			set_status('OK', ok=True)
			if mode == 'advanced':
				try:
					int_res = int(result)
					hex_var.set(hex(int_res))
					bin_var.set(bin(int_res))
				except Exception:
					hex_var.set('')
					bin_var.set('')
		except ZeroDivisionError:
			messagebox.showerror(getattr(app, 'title_struct', '') + ' error', 'Division by zero')
			set_status('Division by zero')
		except ne.NumExprError as e:
			messagebox.showerror(getattr(app, 'title_struct', '') + ' error', f'NumExpr error: {e}')
			set_status('NumExpr error')
		except Exception as e:
			messagebox.showerror(getattr(app, 'title_struct', '') + ' error', f'Invalid expression: {e}')
			set_status('Invalid expression')

	def insert_eq():
		eq = getattr(app, 'ins_equation', '')
		if eq:
			insert_into_editor(f'{eq}', replace_if_selected=True, add_space=True, add_newline=False)

	# Insert button context menu
	insert_menu_opts = {
		'add_space': tk.BooleanVar(value=True),
		'add_newline': tk.BooleanVar(value=False),
	}

	def _open_insert_menu(event=None):
		menu = tk.Menu(insert_button, tearoff=False)
		eq = getattr(app, 'ins_equation', '')
		expr = calc_entry.get()

		def do_insert_result(replace=True):
			if eq:
				insert_into_editor(eq, replace_if_selected=replace,
								   add_space=insert_menu_opts['add_space'].get(),
								   add_newline=insert_menu_opts['add_newline'].get())

		def do_insert_expr_eq():
			if eq and expr:
				insert_into_editor(f'{expr} = {eq}', replace_if_selected=False,
								   add_space=insert_menu_opts['add_space'].get(),
								   add_newline=insert_menu_opts['add_newline'].get())

		menu.add_command(label='Insert result at caret', command=lambda: do_insert_result(replace=False))
		menu.add_command(label='Replace selection with result', command=lambda: do_insert_result(replace=True))
		menu.add_command(label='Insert "expr = result"', command=do_insert_expr_eq)
		menu.add_separator()
		menu.add_checkbutton(label='Trailing space', variable=insert_menu_opts['add_space'])
		menu.add_checkbutton(label='New line', variable=insert_menu_opts['add_newline'])
		try:
			if event is not None:
				menu.tk_popup(event.x_root, event.y_root)
			else:
				x = insert_button.winfo_rootx()
				y = insert_button.winfo_rooty() + insert_button.winfo_height()
				menu.tk_popup(x, y)
		finally:
			menu.grab_release()

	# --- Persistence ---
	def save_state():
		try:
			state = {
				'history': history,
			}
			if mode == 'advanced':
				state['variables'] = user_variables
				state['memory'] = memory_value[0]
			with open(CONFIG_FILE, 'w') as f:
				json.dump(state, f, indent=4)
		except Exception:
			pass # Silently fail

	def load_state():
		if not os.path.exists(CONFIG_FILE): return
		try:
			with open(CONFIG_FILE, 'r') as f:
				state = json.load(f)
				history.extend(state.get('history', []))
				if mode == 'advanced':
					user_variables.update(state.get('variables', {}))
					memory_value[0] = state.get('memory', 0.0)
					update_mem_display()
				# Refresh UI
				for expr, res in history:
					hist_listbox.insert(tk.END, _format_hist_item(expr, res))
				hist_listbox.see(tk.END)
				hist_index[0] = len(history)
				if mode == 'advanced':
					refresh_vars_listbox()
		except Exception:
			pass # Silently fail on corrupt file

	def on_close():
		save_state()
		calc_root.destroy()

	# wire commands
	enter.configure(command=calculate_button)
	copy_button.configure(command=lambda: copy_text(str(getattr(app, 'ins_equation', ''))))
	insert_button.configure(command=insert_eq)
	insert_button.bind('<Button-3>', _open_insert_menu)
	show_op.configure(command=show_oper)
	calc_ui.configure(command=toggle_keypad)
	delete_hist_button.configure(command=delete_selected_history)
	clear_hist_button.configure(command=clear_history)


	# --- History connectivity ---
	def _hist_insert_result(_evt=None):
		try:
			idxs = hist_listbox.curselection()
			if not idxs: return
			_, res = history[idxs[0]]
			insert_into_editor(res, replace_if_selected=True,
							   add_space=insert_menu_opts['add_space'].get(),
							   add_newline=insert_menu_opts['add_newline'].get())
		except Exception:
			pass

	def _hist_compute_and_insert(_evt=None):
		on_hist_reuse()
		calculate_button()
		insert_eq()

	def _hist_insert_expr_eq():
		try:
			idxs = hist_listbox.curselection()
			if not idxs: return
			expr, res = history[idxs[0]]
			insert_into_editor(f'{expr} = {res}', replace_if_selected=False,
							   add_space=insert_menu_opts['add_space'].get(),
							   add_newline=insert_menu_opts['add_newline'].get())
		except Exception:
			pass
			
	def _hist_copy(which='both'):
		try:
			idxs = hist_listbox.curselection()
			if not idxs: return
			expr, res = history[idxs[0]]
			copy_text(expr if which == 'expr' else res if which == 'res' else f'{expr} = {res}')
		except Exception:
			pass

	def _hist_context_menu(event):
		menu = tk.Menu(hist_listbox, tearoff=False)
		menu.add_command(label='Reuse (load expression)', command=on_hist_reuse)
		menu.add_command(label='Compute and insert', command=_hist_compute_and_insert)
		menu.add_separator()
		menu.add_command(label='Insert result', command=_hist_insert_result)
		menu.add_command(label='Insert "expr = result"', command=_hist_insert_expr_eq)
		menu.add_separator()
		menu.add_command(label='Copy expr', command=lambda: _hist_copy('expr'))
		menu.add_command(label='Copy result', command=lambda: _hist_copy('res'))
		menu.add_command(label='Copy both', command=lambda: _hist_copy('both'))
		menu.add_separator()
		menu.add_command(label='Delete Selected', command=delete_selected_history)
		try:
			menu.tk_popup(event.x_root, event.y_root)
		finally:
			menu.grab_release()

	# Bind history interactions
	hist_listbox.bind('<Double-1>', on_hist_reuse)
	hist_listbox.bind('<Return>', lambda e: (_hist_compute_and_insert(), 'break'))
	hist_listbox.bind('<Button-3>', _hist_context_menu)
	hist_listbox.bind('<Delete>', delete_selected_history)

	# Keyboard ergonomics
	def on_return(_e=None):
		calculate_button()
		return 'break'

	def on_escape(_e=None):
		try:
			calc_root.destroy()
		except Exception:
			pass
		return 'break'

	calc_root.bind('<Return>', on_return)
	calc_root.bind('<Escape>', on_escape)
	calc_entry.bind('<BackSpace>', lambda e: (safe_delete(), 'break'))
	calc_root.bind('<Control-i>', lambda e: (insert_eq(), 'break'))
	calc_root.bind('<Control-e>', lambda e: (_open_insert_menu(), 'break'))
	calc_entry.bind('<KeyRelease>', schedule_eval)
	calc_entry.bind('<Up>', lambda e: (recall_history(-1), 'break'))
	calc_entry.bind('<Down>', lambda e: (recall_history(1), 'break'))

	# Final setup
	load_state()
	calc_root.protocol("WM_DELETE_WINDOW", on_close)

	# Focus the entry on open
	try:
		calc_entry.focus_set()
		calc_entry.icursor(tk.END)
	except Exception:
		pass
