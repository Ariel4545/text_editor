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
from tkinter import messagebox
# from dependencies.universal_functions import *

try:
	import numexpr as ne
except Exception:
	ne = None


def open_calculator(app):
	'''
	Open the Calculator popup window.
	'app' is your main application instance, used for:
	  - app.make_pop_ups_window (if available) to create the toplevel
	  - app.EgonTE, app.is_marked(), app.get_pos() for editor interactions (if available)
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
	ALLOWED_FUNCTIONS = {'sin', 'cos', 'tan', 'sqrt', 'log', 'exp'}
	ALLOWED_CONSTS = {'pi', 'e'}
	ALLOWED_NAMES = ALLOWED_FUNCTIONS | ALLOWED_CONSTS

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

	def set_status(msg, ok=False):
		status_var.set(msg)
		status_label.config(fg='green' if ok else 'red')

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
		# Replace sin(x) -> sin((pi/180)*x), etc.
		return (expr
				.replace('sin(', 'sin((pi/180)*')
				.replace('cos(', 'cos((pi/180)*')
				.replace('tan(', 'tan((pi/180)*'))

	def validate_expr(expr: str) -> bool:
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
		unknown = [n for n in names if n not in ALLOWED_NAMES]
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

	# ---------------- UI build ----------------
	calc_root = owner_popup()

	# Local fallbacks for copy/link (avoid importing main app here)
	def copy_text(text: str):
		try:
			if hasattr(app, 'copy') and callable(getattr(app, 'copy')):
				app.copy(text)
				return
		except Exception:
			pass
		try:
			calc_root.clipboard_clear()
			calc_root.clipboard_append(text)
		except Exception:
			pass


	def open_link(url: str):
		# Prefer app.ex_links if available; fallback to webbrowser
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


	# Editor insertion helpers (define here to avoid unresolved reference)
	def _editor_has_selection() -> bool:
		try:
			app.EgonTE.index('sel.first')  # raises if no selection
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


	left_frame = tk.Frame(calc_root)
	title = tk.Label(left_frame, text='Calculator', font=getattr(app, 'titles_font', 'arial 12 bold'), padx=2, pady=3)
	introduction_text = tk.Label(left_frame, text='Enter an expression below:', font='arial 10 underline', padx=2, pady=3)
	last_calc = tk.Entry(left_frame, relief=tk.RIDGE, justify='center', width=30, state='readonly')
	calc_entry = tk.Entry(left_frame, relief=tk.RIDGE, justify='center', width=30)

	status_var = tk.StringVar(value='')
	status_label = tk.Label(left_frame, textvariable=status_var, fg='grey')

	enter = tk.Button(left_frame, text='Calculate', borderwidth=1, font='arial 10 bold')
	b_frame = tk.Frame(left_frame)
	copy_button = tk.Button(b_frame, text='Copy', bd=1, font='arial 10')
	insert_button = tk.Button(b_frame, text='Insert', bd=1, font='arial 10')  # context menu added below
	show_op = tk.Button(left_frame, text='Show operators', bd=1)
	calc_ui = tk.Button(left_frame, text='Show keypad', bd=1)

	degrees_mode = tk.BooleanVar(value=False)
	degrees_cb = tk.Checkbutton(left_frame, text='Degrees (sin/cos/tan)', variable=degrees_mode)
	auto_calc = tk.BooleanVar(value=True)
	auto_cb = tk.Checkbutton(left_frame, text='Auto-calc', variable=auto_calc)

	# History UI
	hist_label = tk.Label(left_frame, text='History')
	hist_frame = tk.Frame(left_frame)
	hist_scroll = tk.Scrollbar(hist_frame, orient=tk.VERTICAL)
	hist_listbox = tk.Listbox(hist_frame, selectmode=tk.SINGLE, height=4, yscrollcommand=hist_scroll.set)
	hist_scroll.config(command=hist_listbox.yview)
	hist_scroll.pack(side=tk.RIGHT, fill=tk.Y)
	hist_listbox.pack(side=tk.LEFT, fill=tk.BOTH)

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
		except Exception:
			pass

	# Layout (unchanged)
	left_frame.pack(side='left')
	title.pack(padx=10)
	introduction_text.pack(padx=10)
	last_calc.pack()
	calc_entry.pack()
	status_label.pack(pady=(2, 0))
	enter.pack(pady=3)
	b_frame.pack(pady=3)
	copy_button.grid(row=0, column=0, padx=2)
	insert_button.grid(row=0, column=2, padx=2)
	degrees_cb.pack()
	auto_cb.pack()
	hist_label.pack(pady=(6, 0))
	hist_frame.pack(fill='x', padx=4)
	show_op.pack(pady=(6, 0))
	calc_ui.pack()

	# Operators panel (unchanged list, connects into insert_token)
	op_frame = tk.Frame(left_frame)
	ops = [
		('+ addition', ' + '),
		('- subtraction', ' - '),
		('* multiplication', ' * '),
		('/ division', ' / '),
		('** power', ' ** '),
		('% modulus', ' % '),
		('sin(', 'sin('),
		('cos(', 'cos('),
		('tan(', 'tan('),
		('sqrt(', 'sqrt('),
		('log(', 'log('),
		('exp(', 'exp('),
		('pi', 'pi'),
		('e', 'e'),
		(')', ')'),
	]
	oper_buttons = [
		tk.Button(op_frame, text=label, command=lambda t=tok: insert_token(t), relief=tk.FLAT)
		for (label, tok) in ops
	]
	for idx, btn in enumerate(oper_buttons):
		r, c = divmod(idx, 3)
		btn.grid(row=r, column=c, padx=2, pady=1)

	numexpr_link = 'https://numexpr.readthedocs.io/en/latest/user_guide.html'
	numexpr_tutorial = tk.Button(left_frame, text='NumExpr tutorial',
								 command=lambda: open_link(numexpr_link),
								 relief=tk.FLAT, fg='blue', font='arial 10 underline')

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

	# Keypad frame (unchanged)
	ex_color = '#B0A695'
	button_height, button_width = 3, 5
	padx_b, pady_b = 1, 1
	extra_frame = tk.Frame(calc_root, bg=ex_color)
	b0, b1, b2, b3, b4, b5, b6, b7, b8, b9 = [
		tk.Button(extra_frame, text=f'{num}', command=lambda num=num: insert_token(num),
				  padx=padx_b, pady=pady_b, relief=tk.FLAT, bg=ex_color, height=button_height, width=button_width)
		for num in range(10)
	]
	clear_b = tk.Button(extra_frame, text='C',
						command=lambda: (calc_entry.delete(0, tk.END), clear_status()),
						pady=pady_b, relief=tk.FLAT, bg='#F3B664', height=button_height, width=button_width)
	del_b = tk.Button(extra_frame, text='DEL', command=lambda: safe_delete(), pady=pady_b,
					  relief=tk.FLAT, bg='#F3B664', height=button_height, width=button_width)

	pack_list, row_, column_ = [b1, b2, b3, b4, b5, b6, b7, b8, b9, clear_b, b0, del_b], 0, 0
	for widget in pack_list:
		widget.grid(row=row_, column=column_)
		column_ += 1
		if column_ == 3:
			row_, column_ = 1 + row_, 0

	# ---------------- logic ----------------
	def insert_token(token):
		try:
			s, e = calc_entry.index('sel.first'), calc_entry.index('sel.last')
			calc_entry.delete(s, e)
		except Exception:
			pass
		calc_entry.insert(tk.INSERT, str(token))
		clear_status()

	def toggle_keypad():
		if not getattr(app, 'extra_calc_ui', False):
			extra_frame.pack(side='right', fill=tk.Y)
			calc_ui.config(text='Hide keypad')
		else:
			extra_frame.pack_forget()
			calc_ui.config(text='Show keypad')
		app.extra_calc_ui = not getattr(app, 'extra_calc_ui', False)

	def show_oper():
		show_op.config(text='Hide operators', command=hide_oper)
		op_frame.pack()
		numexpr_tutorial.pack()

	def hide_oper():
		op_frame.pack_forget()
		numexpr_tutorial.pack_forget()
		show_op.config(text='Show operators', command=show_oper)

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

	def _format_hist_item(expr, result, max_len=46):
		s = f"{expr} = {result}"
		return s if len(s) <= max_len else s[:max_len - 1] + '…'

	def push_history(expr: str, result) -> None:
		history.append((expr, str(result)))
		hist_listbox.insert(tk.END, _format_hist_item(expr, str(result)))
		hist_listbox.see(tk.END)
		hist_index[0] = len(history)

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
			local_ns = {'pi': math.pi, 'e': math.e}
			result = ne.evaluate(eval_expr, local_dict=local_ns)
			calc_entry.delete(0, tk.END)
			calc_entry.insert(0, result)
			app.ins_equation = str(result)
			push_history(expr, result)
			set_status('OK', ok=True)
		except ZeroDivisionError:
			messagebox.showerror(getattr(app, 'title_struct', '') + ' error', 'Division by zero')
			set_status('Division by zero')
		except ne.NumExprError as e:
			messagebox.showerror(getattr(app, 'title_struct', '') + ' error', f'NumExpr error: {e}')
			set_status('NumExpr error')
		except Exception as e:
			messagebox.showerror(getattr(app, 'title_struct', '') + ' error', f'Invalid expression: {e}')
			set_status('Invalid expression')

	# Existing Insert now uses smarter editor insertion
	def insert_eq():
		eq = getattr(app, 'ins_equation', '')
		if eq:
			insert_into_editor(f'{eq}', replace_if_selected=True, add_space=True, add_newline=False)

	# ---- Insert button context menu (new) ----
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
				# fallback near the button
				x = insert_button.winfo_rootx()
				y = insert_button.winfo_rooty() + insert_button.winfo_height()
				menu.tk_popup(x, y)
		finally:
			menu.grab_release()

	# wire commands
	enter.configure(command=calculate_button)
	copy_button.configure(command=lambda: copy_text(str(getattr(app, 'ins_equation', ''))))
	insert_button.configure(command=insert_eq)
	insert_button.bind('<Button-3>', _open_insert_menu)  # right-click for options
	show_op.configure(command=show_oper)
	calc_ui.configure(command=toggle_keypad)
	hist_listbox.bind('<Double-1>', on_hist_reuse)

	# --- History connectivity (new) ---
	def _hist_insert_result(_evt=None):
		try:
			idxs = hist_listbox.curselection()
			if not idxs:
				return
			i = idxs[0]
			expr, res = history[i]
			insert_into_editor(res, replace_if_selected=True,
							   add_space=insert_menu_opts['add_space'].get(),
							   add_newline=insert_menu_opts['add_newline'].get())
		except Exception:
			pass

	def _hist_compute_and_insert(_evt=None):
		on_hist_reuse()
		calculate_button()
		insert_eq()

	def _hist_context_menu(event):
		menu = tk.Menu(hist_listbox, tearoff=False)
		menu.add_command(label='Reuse (load expression)', command=on_hist_reuse)
		menu.add_command(label='Compute and insert', command=_hist_compute_and_insert)
		menu.add_separator()
		menu.add_command(label='Insert result', command=_hist_insert_result)
		menu.add_command(label='Replace selection with result', command=lambda: _hist_insert_result(None))
		menu.add_command(label='Insert "expr = result"',
						 command=lambda: (_hist_insert_expr_eq()))
		menu.add_separator()
		menu.add_command(label='Copy expr', command=lambda: _hist_copy('expr'))
		menu.add_command(label='Copy result', command=lambda: _hist_copy('res'))
		menu.add_command(label='Copy both', command=lambda: _hist_copy('both'))
		try:
			menu.tk_popup(event.x_root, event.y_root)
		finally:
			menu.grab_release()

	def _hist_copy(which='both'):
		try:
			idxs = hist_listbox.curselection()
			if not idxs:
				return
			i = idxs[0]
			expr, res = history[i]
			if which == 'expr':
				copy_text(expr)
			elif which == 'res':
				copy_text(res)
			else:
				copy_text(f'{expr} = {res}')
		except Exception:
			pass

	def _hist_insert_expr_eq():
		try:
			idxs = hist_listbox.curselection()
			if not idxs:
				return
			i = idxs[0]
			expr, res = history[i]
			insert_into_editor(f'{expr} = {res}', replace_if_selected=False,
							   add_space=insert_menu_opts['add_space'].get(),
							   add_newline=insert_menu_opts['add_newline'].get())
		except Exception:
			pass

	# Bind history interactions
	hist_listbox.bind('<<ListboxSelect>>', lambda e: on_hist_reuse())
	hist_listbox.bind('<Return>', lambda e: (_hist_compute_and_insert(), 'break'))
	hist_listbox.bind('<Button-3>', _hist_context_menu)        # Right-click menu
	hist_listbox.bind('<Button-2>', _hist_context_menu)        # macOS middle/right
	hist_listbox.bind('<Button-1>', lambda e: None)            # keep default
	hist_listbox.bind('<Button-2>', _hist_context_menu)
	hist_listbox.bind('<ButtonRelease-2>', lambda e: None)
	hist_listbox.bind('<ButtonRelease-1>', lambda e: None)
	hist_listbox.bind('<Button-1>', lambda e: None, add='+')
	hist_listbox.bind('<Button-2>', lambda e: _hist_insert_result())  # middle-click quick insert

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

	def on_backspace(_e=None):
		safe_delete()
		return 'break'

	def on_ctrl_i(_e=None):
		insert_eq()
		return 'break'

	def on_ctrl_shift_i(_e=None):
		eq = getattr(app, 'ins_equation', '')
		if eq:
			insert_into_editor(eq, replace_if_selected=True, add_space=True, add_newline=False)
		return 'break'

	def on_ctrl_e(_e=None):
		expr = calc_entry.get()
		eq = getattr(app, 'ins_equation', '')
		if expr and eq:
			insert_into_editor(f'{expr} = {eq}', replace_if_selected=False, add_space=True, add_newline=False)
		return 'break'

	calc_root.bind('<Return>', on_return)
	calc_root.bind('<Escape>', on_escape)
	calc_entry.bind('<BackSpace>', on_backspace)
	calc_root.bind('<Control-i>', on_ctrl_i)
	calc_root.bind('<Control-I>', on_ctrl_shift_i)
	calc_root.bind('<Control-e>', on_ctrl_e)
	calc_entry.bind('<KeyRelease>', lambda _e: schedule_eval())
	calc_entry.bind('<Up>', lambda e: (recall_history(-1), 'break'))
	calc_entry.bind('<Down>', lambda e: (recall_history(+1), 'break'))

	# Focus the entry on open
	try:
		calc_entry.focus_set()
		calc_entry.icursor(tk.END)
	except Exception:
		pass
