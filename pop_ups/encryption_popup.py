# Standalone encryption/decryption popup:
# - Symmetric (Fernet) output: ciphertext (Base64)
# - Asymmetric (RSA) output: ciphertext (Base64)
# Keeps original-style public variable names for compatibility:
#   enc_methods_var, is_enc, enc_entry, enc_pem_box, entry_title, enc_methods,
#   input_box, output_box_, copy_from_ete, enter_button, paste_to_ete

import threading
import tkinter as tk
from tkinter import ttk, messagebox

# Optional dependencies; features auto-disable if missing
try:
	from cryptography.fernet import Fernet
	_SYMMETRIC_OK = True
except Exception:
	Fernet = None
	_SYMMETRIC_OK = False

try:
	import rsa
	_ASYMMETRIC_OK = True
except Exception:
	rsa = None
	_ASYMMETRIC_OK = False


def open_encryption(app):
	'''
	Open the Encryption/Decryption popup window.
	'''

	# ---------- small utilities ----------
	def parse_int_or_default(text, default=2048):
		try:
			return int(str(text).strip())
		except Exception:
			return default

	def clamp_min(value, minimum=2048):
		try:
			return value if value >= minimum else minimum
		except Exception:
			return minimum

	def to_bytes(s):
		return s.encode() if isinstance(s, str) else s

	def to_text(b):
		return b.decode() if isinstance(b, (bytes, bytearray)) else b

	def b64_encode(b):
		try:
			import base64
			return to_text(base64.urlsafe_b64encode(b))
		except Exception:
			return ''

	def b64_decode(s):
		try:
			import base64
			return base64.urlsafe_b64decode(to_bytes(s))
		except Exception:
			return b''

	def pem_export(priv):
		try:
			return to_text(priv.save_pkcs1())
		except Exception:
			return ''

	def pem_import(pem_txt):
		try:
			return rsa.PrivateKey.load_pkcs1(to_bytes(pem_txt))
		except Exception:
			return None

	def rsa_max_plain_len(pubkey):
		try:
			return rsa.common.byte_size(pubkey.n) - 11  # PKCS#1 v1.5 padding overhead
		except Exception:
			return 0

	def owner_popup():
		custom_title = 'Encrypt and decrypt'
		if hasattr(app, 'make_pop_ups_window') and callable(getattr(app, 'make_pop_ups_window')):
			return app.make_pop_ups_window(open_encryption, custom_title=custom_title)
		parent = getattr(app, 'root', None)
		if not isinstance(parent, tk.Misc):
			parent = tk._get_default_root()
		if not isinstance(parent, tk.Misc):
			parent = tk.Tk()
		t = tk.Toplevel(parent)
		t.title(custom_title)
		return t

	def set_ui_busy(is_busy=True):
		try:
			app.enter_button.configure(state='disabled' if is_busy else 'normal')
			app.enc_methods.configure(state='disabled' if is_busy else 'readonly')
			enc_radio.configure(state='disabled' if is_busy else 'normal')
			dec_radio.configure(state='disabled' if is_busy else 'normal')
			enc_root.configure(cursor='watch' if is_busy else '')
			enc_root.update_idletasks()
		except Exception:
			pass

	def write_output_only(text):
		app.output_box_.configure(state='normal')
		app.output_box_.delete('1.0', tk.END)
		app.output_box_.insert('1.0', text)
		app.output_box_.configure(state='disabled')

	# ---------- capabilities -> list ----------
	app.encryption_methods = []
	if _SYMMETRIC_OK:
		app.encryption_methods.append('Symmetric key')
	if _ASYMMETRIC_OK:
		app.encryption_methods.append('Asymmetric key')

	if not app.encryption_methods:
		messagebox.showerror(getattr(app, 'title_struct', '') + 'encryption', 'No encryption methods are available.')
		return

	# ---------- state ----------
	app.enc_methods_var = tk.StringVar(value=app.encryption_methods[0])
	app.is_enc = tk.BooleanVar(value=True)

	app.private_key = ''           # RSA PEM or rsa.PrivateKey
	app.fernet = None              # Fernet object
	app.encrypted_message = None   # bytes

	# ---------- UI ----------
	enc_root = owner_popup()
	try:
		for col in (0, 1, 2):
			enc_root.grid_columnconfigure(col, weight=1)
		enc_root.grid_rowconfigure(2, weight=1)
	except Exception:
		pass

	title_label = tk.Label(enc_root, text='Encrypt and decrypt', font='arial 12 underline')
	content_frame = tk.Frame(enc_root)
	try:
		content_frame.grid_columnconfigure(0, weight=1)
		content_frame.grid_columnconfigure(2, weight=1)
		content_frame.grid_rowconfigure(2, weight=1)
	except Exception:
		pass

	input_label = tk.Label(content_frame, text='Input text', font='arial 10 underline')
	output_label = tk.Label(content_frame, text='Output text', font='arial 10 underline')

	method_label = tk.Label(enc_root, text='Method / key', font='arial 10 underline')
	method_frame = tk.Frame(enc_root)
	app.enc_methods = ttk.Combobox(method_frame, textvariable=app.enc_methods_var, state='readonly')
	app.enc_methods['values'] = app.encryption_methods
	enc_radio = tk.Radiobutton(method_frame, text='Encrypt', variable=app.is_enc, value=True)
	dec_radio = tk.Radiobutton(method_frame, text='Decrypt', variable=app.is_enc, value=False)

	app.entry_title = tk.Label(enc_root, text='Key length:', font='arial 10 underline')
	app.enc_entry = tk.Entry(enc_root)                # RSA bits in encrypt mode
	app.enc_pem_box = tk.Text(enc_root, width=42, height=6)  # Private key PEM in decrypt mode

	buttons_frame = tk.Frame(enc_root)
	app.copy_from_ete = tk.Button(buttons_frame, text='Copy from', bd=1)
	app.enter_button = tk.Button(buttons_frame, text='Enter', bd=1)
	app.paste_to_ete = tk.Button(buttons_frame, text='Paste to', bd=1)

	# ---------- place static labels/frames ----------
	title_label.grid(row=0, column=1)
	content_frame.grid(row=2, column=1, sticky='nsew')
	method_label.grid(row=3, column=1)
	method_frame.grid(row=4, column=1)
	app.entry_title.grid(row=5, column=1)
	app.enc_entry.grid(row=6, column=1, sticky='ew')
	buttons_frame.grid(row=7, column=1)

	input_label.grid(row=1, column=0)
	output_label.grid(row=1, column=2)

	# ---------- use make_rich_textbox for input/output boxes ----------
	# Input box
	in_container, app.input_box, in_scroll = app.make_rich_textbox(
		root=content_frame,
		place=(2, 0),           # grid row/col for input
		wrap=tk.WORD,
		font='arial 10',
		size=(30, 15),
		selectbg='dark cyan',
		bd=0,
		relief='',
		format='txt',
	)
	try:
		in_container.grid_configure(sticky='nsew')
	except Exception:
		pass

	# Output box
	out_container, app.output_box_, out_scroll = app.make_rich_textbox(
		root=content_frame,
		place=(2, 2),           # grid row/col for output
		wrap=tk.WORD,
		font='arial 10',
		size=(30, 15),
		selectbg='dark cyan',
		bd=0,
		relief='',
		format='txt',
	)
	try:
		out_container.grid_configure(sticky='nsew')
	except Exception:
		pass
	app.output_box_.configure(state='disabled')

	# Controls row
	enc_radio.grid(row=4, column=0)
	app.enc_methods.grid(row=4, column=1)
	dec_radio.grid(row=4, column=2)

	app.copy_from_ete.grid(row=4, column=0, padx=5)
	app.enter_button.grid(row=4, column=1, padx=5, pady=5)
	app.paste_to_ete.grid(row=4, column=2, padx=5)

	# ---------- logic ----------
	def resolve_method():
		app.enc_dec_method = ''
		choice = app.enc_methods_var.get()
		if choice == 'Symmetric key':
			app.enc_dec_method = 'symmetric'
		elif choice == 'Asymmetric key':
			app.enc_dec_method = 'asymmetric'

	def hide_key_inputs():
		app.entry_title.grid_forget()
		app.enc_entry.grid_forget()
		try:
			app.enc_pem_box.grid_forget()
		except Exception:
			pass

	def update_mode_ui(_evt=False):
		resolve_method()
		hide_key_inputs()
		if app.is_enc.get():
			if app.enc_dec_method == 'asymmetric':
				app.entry_title.configure(text='Key length:')
				app.enc_entry.configure(show='')
				app.entry_title.grid(row=5, column=1)
				app.enc_entry.grid(row=6, column=1)
		else:
			if app.enc_dec_method == 'asymmetric':
				app.entry_title.configure(text='Private Key\n(PEM):')
				app.entry_title.grid(row=5, column=1)
				app.enc_pem_box.grid(row=6, column=1, sticky='nsew')

	def handle_encrypt():
		resolve_method()
		plain_text = app.input_box.get('1.0', tk.END).rstrip('\n')
		if not (plain_text and app.enc_dec_method):
			return

		try:
			if app.enc_dec_method == 'symmetric':
				if not _SYMMETRIC_OK:
					messagebox.showerror(getattr(app, 'title_struct', '') + 'encryption', 'Symmetric encryption is not available.')
					return
				key_bytes = Fernet.generate_key()
				app.fernet = Fernet(key_bytes)
				app.encrypted_message = app.fernet.encrypt(to_bytes(plain_text))
				# Output: ciphertext only (base64)
				write_output_only(b64_encode(app.encrypted_message))

			elif app.enc_dec_method == 'asymmetric':
				if not _ASYMMETRIC_OK:
					messagebox.showerror(getattr(app, 'title_struct', '') + 'encryption', 'Asymmetric encryption is not available.')
					return

				def worker_rsa():
					err_msg, out_text = '', ''
					try:
						key_bits = clamp_min(parse_int_or_default(app.enc_entry.get() or 2048, 2048), 2048)
						# Optional: cap for responsiveness
						if key_bits > 8192:
							key_bits = 8192
						public_key, app.private_key = rsa.newkeys(key_bits)

						plain_bytes = to_bytes(plain_text)
						max_len = rsa_max_plain_len(public_key)
						if max_len and len(plain_bytes) > max_len:
							err_msg = (f'Content too large for RSA {key_bits}.\n'
									   f'Max bytes: {max_len}. Increase key length or use Symmetric key.')
						else:
							try:
                                # Encrypt and emit only Base64 ciphertext
								app.encrypted_message = rsa.encrypt(plain_bytes, public_key)
								out_text = b64_encode(app.encrypted_message)
							except OverflowError:
								err_msg = ('Content too large for direct RSA encryption.\n'
										   'Increase key length or use Symmetric key.')
					except Exception as ex:
						err_msg = f'Error: {ex}'

					def apply_result():
						set_ui_busy(False)
						if err_msg:
							messagebox.showerror(getattr(app, 'title_struct', '') + 'encryption', err_msg)
							return
						if out_text:
							write_output_only(out_text)

					try:
						enc_root.after(0, apply_result)
					except Exception:
						apply_result()

				set_ui_busy(True)
				threading.Thread(target=worker_rsa, daemon=True).start()

		except Exception as ex:
			set_ui_busy(False)
			messagebox.showerror(getattr(app, 'title_struct', '') + 'encryption', f'Error: {ex}')

	def handle_decrypt():
		resolve_method()
		plain_out = ''
		try:
			if app.enc_dec_method == 'symmetric':
				if not _SYMMETRIC_OK:
					messagebox.showerror(getattr(app, 'title_struct', '') + 'decryption', 'Symmetric decryption is not available.')
					return
				# Expect ciphertext (base64) in output or input; key from session (app.fernet)
				raw_cipher = app.output_box_.get('1.0', tk.END).strip() or app.input_box.get('1.0', tk.END).strip()
				if raw_cipher:
					if not getattr(app, 'fernet', None):
						messagebox.showerror(getattr(app, 'title_struct', '') + 'decryption', 'Missing symmetric key (encrypt first this session).')
						return
					try:
						plain_out = to_text(app.fernet.decrypt(b64_decode(raw_cipher)))
					except Exception:
						messagebox.showerror(getattr(app, 'title_struct', '') + 'decryption', 'Wrong key or damaged data.')
						return
				elif getattr(app, 'fernet', None) and getattr(app, 'encrypted_message', None):
					plain_out = to_text(app.fernet.decrypt(app.encrypted_message))
				else:
					return

			elif app.enc_dec_method == 'asymmetric':
				if not _ASYMMETRIC_OK:
					messagebox.showerror(getattr(app, 'title_struct', '') + 'decryption', 'Asymmetric decryption is not available.')
					return
				# Expect ciphertext (base64) and a valid private key
				raw_cipher = app.output_box_.get('1.0', tk.END).strip() or app.input_box.get('1.0', tk.END).strip()
				if not raw_cipher:
					return

				priv_pem_text = ''
				try:
					priv_pem_text = app.enc_pem_box.get('1.0', tk.END).strip()
				except Exception:
					priv_pem_text = ''

				priv_key_obj = None
				if priv_pem_text:
					priv_key_obj = pem_import(priv_pem_text)
				if not priv_key_obj and getattr(app, 'private_key', None):
					priv_key_obj = app.private_key if hasattr(app.private_key, 'n') else pem_import(app.private_key)

				if not priv_key_obj:
					messagebox.showerror(getattr(app, 'title_struct', '') + 'decryption', 'You don\'t have a valid private key!')
					return

				try:
					plain_out = to_text(rsa.decrypt(b64_decode(raw_cipher), priv_key_obj))
				except Exception:
					messagebox.showerror(getattr(app, 'title_struct', '') + 'decryption', 'Decryption failed. Check key and data.')
					return

			if plain_out:
				write_output_only(plain_out)

		except Exception as ex:
			messagebox.showerror(getattr(app, 'title_struct', '') + 'decryption', f'Error: {ex}')
		finally:
			set_ui_busy(False)

	def copy_from_editor():
		content = ''
		try:
			if hasattr(app, 'EgonTE'):
				try:
					content = app.EgonTE.get('sel.first', 'sel.last')
				except Exception:
					get_idx = getattr(app, 'get_indexes', None)
					if callable(get_idx):
						idx = get_idx()
						if isinstance(idx, (tuple, list)) and len(idx) >= 2:
							content = app.EgonTE.get(idx[0], idx[1])
		except Exception:
			content = ''
		if content:
			app.input_box.insert(tk.END, content)

	def paste_to_editor():
		try:
			content = app.output_box_.get('1.0', tk.END)
		except Exception:
			content = ''
		if content:
			try:
				get_pos = getattr(app, 'get_pos', None)
				if callable(get_pos):
					app.EgonTE.insert(get_pos(), content)
				else:
					app.EgonTE.insert(tk.INSERT, content)
			except Exception:
				pass

	# bindings
	app.enc_methods.bind('<<ComboboxSelected>>', update_mode_ui)
	enc_radio.configure(command=update_mode_ui)
	dec_radio.configure(command=update_mode_ui)

	app.copy_from_ete.configure(command=copy_from_editor)
	app.enter_button.configure(command=lambda: handle_encrypt() if app.is_enc.get() else handle_decrypt())
	app.paste_to_ete.configure(command=paste_to_editor)

	# keyboard niceties
	try:
		enc_root.bind('<Escape>', lambda _e: enc_root.destroy(), add='+')
		enc_root.bind('<Return>', lambda _e: (handle_encrypt() if app.is_enc.get() else handle_decrypt()), add='+')
	except Exception:
		pass

	# init UI
	update_mode_ui()
