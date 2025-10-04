# Standalone Ultimate Crypto/Encoding Tool:
# - Symmetric (Fernet, AES-GCM)
# - Asymmetric (RSA Hybrid with PyCryptodome, or basic RSA with 'rsa' library)
# - Digital Signatures (RSA-PSS)
# - Hashing (SHA-256, SHA-512, MD5)
# - Encoding (Base64, Hex, URL)

import base64
import binascii
import hashlib
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from urllib.parse import quote, unquote

# Optional dependencies; features auto-disable if missing
try:
    from cryptography.fernet import Fernet, InvalidToken

    _FERNET_OK = True
except ImportError:
    Fernet, InvalidToken = None, None
    _FERNET_OK = False

try:
    import rsa

    _RSA_LIB_OK = True
except ImportError:
    rsa = None
    _RSA_LIB_OK = False

try:
    from Crypto.Cipher import AES
    from Crypto.Hash import SHA256, SHA512
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Random import get_random_bytes
    from Crypto.Signature import pss
    from Crypto.PublicKey import RSA as PyCryptoRSA

    _PYCRYPTODOME_OK = True
except ImportError:
    AES, SHA256, SHA512, PBKDF2, get_random_bytes, pss, PyCryptoRSA = [None] * 7
    _PYCRYPTODOME_OK = False


class Tooltip:
    """Create a tooltip for a given widget."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind('<Enter>', self.show_tooltip)
        self.widget.bind('<Leave>', self.hide_tooltip)

    def show_tooltip(self, _event):
        try:
            bbox = self.widget.bbox('insert')
            if bbox:
                x, y, _, _ = bbox
                x += self.widget.winfo_rootx() + 25
                y += self.widget.winfo_rooty() + 25
            else:
                x = self.widget.winfo_rootx() + 25
                y = self.widget.winfo_rooty() + 25
        except Exception:
            x = self.widget.winfo_rootx() + 25
            y = self.widget.winfo_rooty() + 25

        self.hide_tooltip(None)
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f'+{x}+{y}')

        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                         background='#ffffe0', relief='solid', borderwidth=1,
                         font=('Segoe UI', 8, 'normal'))
        label.pack(ipadx=1)

    def hide_tooltip(self, _event):
        if self.tooltip_window:
            try:
                self.tooltip_window.destroy()
            except tk.TclError:
                pass
        self.tooltip_window = None


def to_bytes(s): return s.encode('utf-8') if isinstance(s, str) else s


def to_text(b): return b.decode('utf-8', errors='replace') if isinstance(b, (bytes, bytearray)) else b


def b64_encode(b): return base64.urlsafe_b64encode(b).decode('ascii')


def _b64_fix_padding(s):
    if isinstance(s, bytes): s = s.decode('ascii', errors='ignore')
    s = s.strip().replace('\n', '').replace('\r', '')
    missing = (-len(s)) % 4
    return s + ('=' * missing)


def b64_decode(s):
    try:
        fixed = _b64_fix_padding(s)
        return base64.urlsafe_b64decode(to_bytes(fixed))
    except (binascii.Error, ValueError, TypeError):
        return b''


def open_encryption(app):
    '''Open the Ultimate Crypto/Encoding popup window.'''
    # Services
    try:
        from encryption_service import Symmetric as svc_sym, Asymmetric as svc_asym, Hashing as svc_hash, \
            Encoding as svc_enc
        from encryption_service import Validators as svc_val
    except Exception:
        svc_sym = svc_asym = svc_hash = svc_enc = None

        class _NV:
            @staticmethod
            def is_base64(s): return True

            @staticmethod
            def is_hex(s): return True

            @staticmethod
            def is_base32(s): return True

            @staticmethod
            def is_base85(s): return True

        svc_val = _NV

    # ---------- Utilities ----------
    def show_error(title, message):
        parent = enc_root if isinstance(enc_root, tk.Misc) else None
        full_title = f"{getattr(app, 'title_struct', '')}{title}"
        try:
            messagebox.showerror(full_title, message, parent=parent)
        except Exception:
            pass
        update_status(f'{title.capitalize()} failed', is_error=True)

    def show_info(title, message):
        parent = enc_root if isinstance(enc_root, tk.Misc) else None
        full_title = f"{getattr(app, 'title_struct', '')}{title}"
        try:
            messagebox.showinfo(full_title, message, parent=parent)
        except Exception:
            pass
        update_status(message, is_error=False)

    def owner_popup():
        custom_title = 'Ultimate Crypto & Encoding Tool'
        # Use the app-exposed standard builders (no conditions)
        return app.make_pop_ups_window(open_encryption, custom_title=custom_title, parent=getattr(app, 'root', None))

    def _parented_dialog(func, *args, **kwargs):
        if 'parent' not in kwargs:
            kwargs['parent'] = enc_root if isinstance(enc_root, tk.Misc) else None
        return func(*args, **kwargs)

    def set_ui_busy(is_busy=True):
        try:
            if is_busy:
                progress_bar.start()
            else:
                progress_bar.stop()
            enc_root.update_idletasks()
        except tk.TclError:
            pass

    def write_output_only(text):
        try:
            app.output_box_.configure(state='normal')
            app.output_box_.delete('1.0', tk.END)
            if text:
                app.output_box_.insert('1.0', text)
        except tk.TclError:
            pass

    def update_status(message, is_error=False):
        try:
            status_label.configure(text=message, foreground='red' if is_error else 'black')
        except tk.TclError:
            pass

    # ---------- State & Constants ----------
    MIN_RSA_BITS, MAX_RSA_BITS = 2048, 8192
    NONCE_LEN_GCM = 16
    TAG_LEN_GCM = 16

    # ---------- UI String Constants ----------
    LABEL_PLAINTEXT = '--- Plaintext ---'
    LABEL_CIPHERTEXT_B64 = '--- Ciphertext (B64) ---'
    LABEL_MESSAGE = '--- Message ---'
    LABEL_SIGNATURE_B64 = '--- Signature (B64) ---'
    LABEL_SIGNATURE_TO_VERIFY_B64 = '--- Signature to Verify (B64) ---'
    LABEL_DATA_TO_HASH = '--- Data to Hash ---'
    LABEL_SHA256_HASH_HEX = '--- SHA-256 Hash (Hex) ---'
    LABEL_SHA512_HASH_HEX = '--- SHA-512 Hash (Hex) ---'
    LABEL_MD5_HASH_HEX = '--- MD5 Hash (Hex) ---'
    LABEL_RAW_DATA = '--- Raw Data ---'
    LABEL_BASE64_OUTPUT = '--- Base64 Output ---'
    LABEL_BASE64_INPUT = '--- Base64 Input ---'
    LABEL_HEX_OUTPUT = '--- Hex Output ---'
    LABEL_HEX_INPUT = '--- Hex Input ---'
    LABEL_URL_COMPONENT = '--- URL Component ---'
    LABEL_URL_ENCODED_OUTPUT = '--- URL-Encoded Output ---'
    LABEL_URL_ENCODED_INPUT = '--- URL-Encoded Input ---'
    LABEL_CONCEPTUAL_DATA = '--- Data ---'
    LABEL_QUANTUM_SAFE_CIPHERTEXT = '--- Quantum-Safe Ciphertext ---'
    LABEL_SECRET_DATA = '--- Secret Data ---'
    LABEL_COVER_FILE = '--- Cover File (e.g., Image) ---'
    LABEL_DATA_TO_ERASE = '--- Data to Erase ---'
    LABEL_ERASED_CONCEPTUAL = '--- Erased (Not Really) ---'
    LABEL_BASE32_OUTPUT = '--- Base32 Output ---'
    LABEL_BASE32_INPUT = '--- Base32 Input ---'
    LABEL_BASE85_OUTPUT = '--- Base85 Output ---'
    LABEL_BASE85_INPUT = '--- Base85 Input ---'
    LABEL_SHA1_HASH_HEX = '--- SHA-1 Hash (Hex - Insecure) ---'
    LABEL_BLAKE2B_HASH_HEX = '--- BLAKE2b Hash (Hex) ---'

    # --- Categorized Methods ---
    METHODS = {
        '--- Symmetric Encryption ---': [],
        'Symmetric (Fernet)': _FERNET_OK,
        'Symmetric (AES-GCM)': _PYCRYPTODOME_OK,
        'Symmetric (ChaCha20-Poly1305)': _PYCRYPTODOME_OK,
        '--- Asymmetric ---': [],
        'Asymmetric (RSA)': _PYCRYPTODOME_OK or _RSA_LIB_OK,
        'Digital Signature (RSA-PSS)': _PYCRYPTODOME_OK,
        '--- Hashing/Checksums ---': [],
        'Hash (SHA-256)': True,
        'Hash (SHA-512)': True,
        'Hash (MD5 - Insecure)': True,
        'Hash (SHA-1 - Insecure)': True,
        'Hash (BLAKE2b)': True,
        '--- Encoding/Decoding ---': [],
        'Encode/Decode (Base64)': True,
        'Encode/Decode (Base32)': True,
        'Encode/Decode (Base85)': True,
        'Encode/Decode (Hex)': True,
        'Encode/Decode (URL)': True,
        '--- Over-The-Top ---': [],
        'Quantum-Resistant (Conceptual)': True,
        'Steganography (Conceptual)': True,
        'Secure Erase (Conceptual)': True,
    }

    # Filter methods based on availability and ensure separators only if needed
    app.encryption_methods = []
    method_keys = list(METHODS.keys())
    for i, (k, v) in enumerate(METHODS.items()):
        if k.startswith('---'):
            next_methods_exist = False
            for j in range(i + 1, len(method_keys)):
                next_k = method_keys[j]
                if next_k.startswith('---'): break
                if METHODS.get(next_k) is True:
                    next_methods_exist = True
                    break
            if next_methods_exist: app.encryption_methods.append(k)
        elif v is True:
            app.encryption_methods.append(k)

    if not any(v for k, v in METHODS.items() if v is True and not k.startswith('---')):
        return show_error('Initialization',
                          'No crypto/encoding methods are available. Please install required libraries.')

    app.enc_methods_var = tk.StringVar(
        value=next((m for m in app.encryption_methods if '---' not in m), app.encryption_methods[0]))
    app.mode_var = tk.BooleanVar(value=True)  # Primary/Secondary mode
    app.private_key_in_session = None
    app.public_key_in_session = None
    app.symmetric_key_in_session = None

    # Dynamic UI Variables
    app.operation_type = tk.StringVar(value='Encrypt')
    app.input_label_var = tk.StringVar(value='--- Plaintext ---')
    app.output_label_var = tk.StringVar(value='--- Ciphertext ---')
    app.primary_mode_label = tk.StringVar(value='Encrypt')
    app.secondary_mode_label = tk.StringVar(value='Decrypt')

    # ---------- UI Setup ----------
    enc_root = owner_popup()
    style = ttk.Style(enc_root)
    try:
        if 'vista' in style.theme_names(): style.theme_use('vista')
    except tk.TclError:
        pass
    style.configure('.', font=('Segoe UI', 10))
    style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'))
    style.configure('TButton', padding=5)
    style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'))
    style.map('Error.TEntry', fieldbackground=[('!disabled', '#FFCDD2')])
    style.configure('Dynamic.TLabel', font=('Segoe UI', 8, 'italic'), foreground='grey')

    main_frame = ttk.Frame(enc_root, padding=10)
    main_frame.grid(row=0, column=0, sticky='nsew')
    enc_root.grid_rowconfigure(0, weight=1)
    enc_root.grid_columnconfigure(0, weight=1)

    # --- Main Content Area (use app.make_rich_textbox) ---
    io_frame = ttk.Frame(main_frame)
    io_frame.grid(row=1, column=0, columnspan=2, sticky='nsew')
    io_frame.grid_columnconfigure(0, weight=1)
    io_frame.grid_columnconfigure(1, weight=1)
    main_frame.grid_rowconfigure(1, weight=1)

    ttk.Label(io_frame, textvariable=app.input_label_var, style='Dynamic.TLabel').grid(row=0, column=0, sticky='w',
                                                                                       padx=5)
    ttk.Label(io_frame, textvariable=app.output_label_var, style='Dynamic.TLabel').grid(row=0, column=1, sticky='w',
                                                                                        padx=5)

    # Small X-padding with tiny border for text boxes
    left_container, left_text, _ys = app.make_rich_textbox(
        io_frame, place=(1, 0), wrap=tk.WORD, font=('Segoe UI', 10),
        size=(40, 12), show_xscroll=False, bd=1, relief='solid'
    )
    right_container, right_text, _ys2 = app.make_rich_textbox(
        io_frame, place=(1, 1), wrap=tk.WORD, font=('Segoe UI', 10),
        size=(40, 12), show_xscroll=False, bd=1, relief='solid'
    )
    # Ensure containers expand within grid
    try:
        left_container.grid_configure(row=1, column=0, sticky='nsew', padx=4)
        right_container.grid_configure(row=1, column=1, sticky='nsew', padx=4)
        io_frame.grid_rowconfigure(1, weight=1)
        io_frame.grid_columnconfigure(0, weight=1)
        io_frame.grid_columnconfigure(1, weight=1)
    except Exception:
        pass

    app.input_box = left_text
    app.output_box_ = right_text
    app.output_box_.configure(state='disabled')

    title_label = ttk.Label(main_frame, text='Ultimate Crypto & Encoding Tool', style='Header.TLabel', anchor='center')
    title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky='ew')

    actions_frame = ttk.Frame(main_frame)
    actions_frame.grid(row=2, column=0, columnspan=2, pady=5)
    app.paste_button = ttk.Button(actions_frame, text='Paste')
    app.clear_button = ttk.Button(actions_frame, text='Clear All')
    app.run_button = ttk.Button(actions_frame, textvariable=app.operation_type, style='Accent.TButton')
    app.copy_button = ttk.Button(actions_frame, text='Copy')
    app.swap_button = ttk.Button(actions_frame, text='Swap I/O')
    app.paste_button.pack(side='left', padx=5)
    app.clear_button.pack(side='left', padx=5)
    app.run_button.pack(side='left', padx=5)
    app.copy_button.pack(side='left', padx=5)
    app.swap_button.pack(side='left', padx=5)

    # --- Settings Area ---
    controls_frame = ttk.Labelframe(main_frame, text='Settings', padding=10)
    controls_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=5)
    controls_frame.grid_columnconfigure(1, weight=1)

    mode_label = ttk.Label(controls_frame, text='Mode:')
    mode_frame = ttk.Frame(controls_frame)
    app.primary_radio = ttk.Radiobutton(mode_frame, textvariable=app.primary_mode_label, variable=app.mode_var,
                                        value=True)
    app.secondary_radio = ttk.Radiobutton(mode_frame, textvariable=app.secondary_mode_label, variable=app.mode_var,
                                          value=False)
    app.primary_radio.grid(row=0, column=0, sticky='w')
    app.secondary_radio.grid(row=0, column=1, sticky='w', padx=(5, 0))

    method_label = ttk.Label(controls_frame, text='Method:')
    app.enc_methods_combo = ttk.Combobox(controls_frame, textvariable=app.enc_methods_var, state='readonly',
                                         values=app.encryption_methods, width=30)

    mode_label.grid(row=0, column=0, sticky='w', pady=(0, 5))
    mode_frame.grid(row=0, column=1, sticky='w', pady=(0, 5))
    method_label.grid(row=1, column=0, sticky='w')
    app.enc_methods_combo.grid(row=1, column=1, sticky='ew')

    # --- Dynamic Key/Settings Frame ---
    key_frame = ttk.Frame(controls_frame)
    key_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(10, 0))
    key_frame.grid_columnconfigure(1, weight=1)

    app.key_label = ttk.Label(key_frame, text='Key:')
    app.key_entry = ttk.Entry(key_frame)
    app.key_action_button = ttk.Button(key_frame)

    app.password_label = ttk.Label(key_frame, text='Password:')
    app.password_entry = ttk.Entry(key_frame, show='*')
    app.salt_label = ttk.Label(key_frame, text='Salt (Base64):')
    app.salt_entry = ttk.Entry(key_frame)
    app.generate_salt_button = ttk.Button(key_frame, text='New Salt')

    # Symmetric Key I/O
    app.sym_key_io_frame = ttk.Frame(key_frame)
    app.load_sym_key_button = ttk.Button(app.sym_key_io_frame, text='Load Key...')
    app.save_sym_key_button = ttk.Button(app.sym_key_io_frame, text='Save Key...')
    app.load_sym_key_button.pack(side='left', padx=(0, 5))
    app.save_sym_key_button.pack(side='left')

    # Asymmetric Key I/O
    app.asym_key_io_frame = ttk.Frame(key_frame)
    app.load_priv_key_button = ttk.Button(app.asym_key_io_frame, text='Load Private Key...')
    app.save_priv_key_button = ttk.Button(app.asym_key_io_frame, text='Save Private Key...')
    app.load_pub_key_button = ttk.Button(app.asym_key_io_frame, text='Load Public Key...')
    app.save_pub_key_button = ttk.Button(app.asym_key_io_frame, text='Save Public Key...')
    app.load_priv_key_button.pack(side='left', padx=(0, 5))
    app.save_priv_key_button.pack(side='left', padx=(0, 5))
    app.load_pub_key_button.pack(side='left', padx=(0, 5))
    app.save_pub_key_button.pack(side='left')

    # Conceptual Key Storage
    app.key_storage_label = ttk.Label(controls_frame, text='Key Storage:')
    app.key_storage_var = tk.StringVar(value='Local Session')
    app.key_storage_options = ttk.Combobox(controls_frame, textvariable=app.key_storage_var, state='readonly',
                                           values=['Local Session', 'HSM (Conceptual)', 'Key Vault (Conceptual)',
                                                   'Blockchain (Conceptual)'], width=30)
    app.key_storage_label.grid(row=4, column=0, sticky='w', pady=(5, 0))
    app.key_storage_options.grid(row=4, column=1, sticky='ew', pady=(5, 0))

    # --- Status Bar ---
    status_frame = ttk.Frame(main_frame, padding=(0, 5, 0, 0))
    status_frame.grid(row=4, column=0, columnspan=2, sticky='ew')
    status_frame.grid_columnconfigure(0, weight=1)
    status_label = ttk.Label(status_frame, text='Ready', anchor='w')
    status_label.grid(row=0, column=0, sticky='ew')
    progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
    progress_bar.grid(row=0, column=1, sticky='e')

    # -------- Helpers offloading to service --------
    def _derive_key_from_ui():
        if svc_sym is None:
            raise ImportError('encryption_service is not available.')
        password = app.password_entry.get()
        if not password:
            raise ValueError('Password cannot be empty.')
        salt_b = b64_decode(app.salt_entry.get())
        if not salt_b:
            raise ValueError('Salt is invalid or empty.')
        return svc_sym.generate_aes_key_from_password(password, salt_b)

    def _ensure_symmetric_key():
        if app.symmetric_key_in_session:
            return app.symmetric_key_in_session
        key = _derive_key_from_ui()
        app.symmetric_key_in_session = key
        return key

    # ---------- Logic & Event Handlers ----------
    def clear_fields():
        app.input_box.delete('1.0', tk.END)
        write_output_only('')
        app.key_entry.delete(0, tk.END)
        app.password_entry.delete(0, tk.END)
        app.salt_entry.delete(0, tk.END)
        app.private_key_in_session = None
        app.public_key_in_session = None
        app.symmetric_key_in_session = None
        update_mode_ui()
        update_status('All fields cleared')

    def paste_from_clipboard_or_editor():
        content = ''
        try:
            content = enc_root.clipboard_get()
        except (tk.TclError, AttributeError):
            try:
                if hasattr(app, 'EgonTE'): content = app.EgonTE.get('sel.first', 'sel.last')
            except (tk.TclError, AttributeError):
                pass
        if content:
            app.input_box.delete('1.0', tk.END)
            app.input_box.insert('1.0', content)
            update_status('Pasted content')
        validate_inputs()

    def copy_to_clipboard_or_editor():
        content = app.output_box_.get('1.0', tk.END).strip()
        if not content: return
        try:
            enc_root.clipboard_clear()
            enc_root.clipboard_append(content)
            update_status('Copied to clipboard')
        except (tk.TclError, AttributeError):
            try:
                if hasattr(app, 'EgonTE'):
                    pos = getattr(app, 'get_pos', lambda: tk.INSERT)()
                    app.EgonTE.insert(pos, content)
                    update_status('Pasted to editor')
            except (tk.TclError, AttributeError):
                pass

    def swap_input_output():
        in_text = app.input_box.get('1.0', tk.END)
        out_text = app.output_box_.get('1.0', tk.END)
        app.input_box.delete('1.0', tk.END)
        app.input_box.insert('1.0', out_text.strip())
        write_output_only(in_text.strip())
        update_status('Swapped input and output')
        validate_inputs()

    # --- Key Generation & Management ---
    def generate_fernet_key():
        if not _FERNET_OK: return show_error('Key Gen', 'Fernet library not available.')
        key = Fernet.generate_key()
        app.symmetric_key_in_session = key
        app.key_entry.delete(0, tk.END)
        app.key_entry.insert(0, to_text(key))
        update_status('New Fernet key generated and stored in session')
        validate_inputs()

    def generate_aes_key_from_password():
        if not _PYCRYPTODOME_OK: return show_error('Key Gen', 'PyCryptodome not available.')
        password = app.password_entry.get()
        if not password: return show_error('Key Derivation', 'Password cannot be empty.')
        if not app.salt_entry.get(): generate_salt()
        salt = b64_decode(app.salt_entry.get())
        try:
            key = PBKDF2(to_bytes(password), salt, dkLen=32, count=100000, hmac_hash_module=SHA256)
            app.symmetric_key_in_session = key
            app.key_entry.delete(0, tk.END)
            app.key_entry.insert(0, b64_encode(key))
            update_status('Key derived from password and stored in session')
        except Exception as e:
            show_error('Key Derivation', f'Failed to derive key: {e}')
        validate_inputs()

    def generate_salt():
        if not _PYCRYPTODOME_OK: return show_error('Salt Gen', 'PyCryptodome not available.')
        salt = get_random_bytes(16)
        app.salt_entry.delete(0, tk.END)
        app.salt_entry.insert(0, b64_encode(salt))
        update_status('New random salt generated')
        validate_inputs()

    def generate_rsa_keys():
        def worker():
            err_msg, success_msg = '', ''
            try:
                bits = int(app.key_entry.get())
                if _PYCRYPTODOME_OK:
                    key = PyCryptoRSA.generate(bits)
                    app.private_key_in_session = key
                    app.public_key_in_session = key.public_key()
                elif _RSA_LIB_OK:
                    pub, priv = rsa.newkeys(bits)
                    app.private_key_in_session = priv
                    app.public_key_in_session = pub
                else:
                    raise Exception('No RSA library available.')
                success_msg = f'New {bits}-bit RSA key pair generated and stored in session.'
            except Exception as ex:
                err_msg = f'Error during key generation: {ex}'

            def apply_result():
                if err_msg:
                    show_error('RSA Generation', err_msg)
                else:
                    update_status(success_msg)
                set_ui_busy(False)
                update_mode_ui()

            try:
                enc_root.after(0, apply_result)
            except tk.TclError:
                pass

        set_ui_busy(True)
        update_status('Generating RSA keys...')
        threading.Thread(target=worker, daemon=True).start()

    def file_handler(mode, filetypes, title, action_func):
        if mode == 'save':
            path = _parented_dialog(filedialog.asksaveasfilename, filetypes=filetypes, title=title)
        else:
            path = _parented_dialog(filedialog.askopenfilename, filetypes=filetypes, title=title)
        if not path: return
        try:
            action_func(path)
        except Exception as e:
            show_error('File Error', f'Failed to {mode} file: {e}')
        validate_inputs()

    def save_key_to_file(path, key_data, success_msg):
        with open(path, 'wb') as f: f.write(key_data)
        update_status(success_msg)

    def save_private_key():
        if not app.private_key_in_session: return show_error('Save Key', 'No private key in session.')
        key_format = 'PEM'
        if _PYCRYPTODOME_OK and isinstance(app.private_key_in_session, PyCryptoRSA._RSAobj):
            key_data = app.private_key_in_session.export_key(key_format)
        elif _RSA_LIB_OK and isinstance(app.private_key_in_session, rsa.PrivateKey):
            key_data = app.private_key_in_session.save_pkcs1(format=key_format)
        else:
            return show_error('Save Key', 'Unsupported private key format in session.')
        file_handler('save', [('PEM files', '*.pem')], 'Save Private Key',
                     lambda p: save_key_to_file(p, key_data, 'Private key saved.'))

    def save_public_key():
        if not app.public_key_in_session: return show_error('Save Key', 'No public key in session.')
        key_format = 'PEM'
        if _PYCRYPTODOME_OK and isinstance(app.public_key_in_session, PyCryptoRSA.RsaKey):
            key_data = app.public_key_in_session.export_key(key_format)
        elif _RSA_LIB_OK and isinstance(app.public_key_in_session, rsa.PublicKey):
            key_data = app.public_key_in_session.save_pkcs1(format=key_format)
        else:
            return show_error('Save Key', 'Unsupported public key format in session.')
        file_handler('save', [('PEM files', '*.pem')], 'Save Public Key',
                     lambda p: save_key_to_file(p, key_data, 'Public key saved.'))

    def save_symmetric_key():
        if not app.symmetric_key_in_session: return show_error('Save Key', 'No symmetric key in session.')
        file_handler('save', [('Key files', '*.key'), ('All files', '*.*')], 'Save Symmetric Key',
                     lambda p: save_key_to_file(p, app.symmetric_key_in_session, 'Symmetric key saved.'))

    def load_key_from_file(path, action_func):
        with open(path, 'rb') as f: content = f.read()
        action_func(content)

    def load_private_key():
        def action(content):
            if _PYCRYPTODOME_OK:
                try:
                    key = PyCryptoRSA.import_key(content)
                    app.private_key_in_session = key
                    app.public_key_in_session = key.public_key()
                except (ValueError, IndexError, TypeError) as e:
                    if not _RSA_LIB_OK: raise e
            if not app.private_key_in_session and _RSA_LIB_OK:
                key = rsa.PrivateKey.load_pkcs1(content)
                app.private_key_in_session = key
                app.public_key_in_session = rsa.PublicKey(key.n, key.e)
            if not app.private_key_in_session: raise Exception('Could not load key with any available library.')
            app.key_entry.delete(0, tk.END)
            app.key_entry.insert(0, to_text(content))
            update_status('Private key loaded and stored in session.')

        file_handler('load', [('PEM files', '*.pem')], 'Load Private Key', action)

    def load_public_key():
        def action(content):
            if _PYCRYPTODOME_OK:
                try:
                    app.public_key_in_session = PyCryptoRSA.import_key(content)
                except (ValueError, IndexError, TypeError) as e:
                    if not _RSA_LIB_OK: raise e
            if not app.public_key_in_session and _RSA_LIB_OK:
                app.public_key_in_session = rsa.PublicKey.load_pkcs1(content)
            if not app.public_key_in_session: raise Exception('Could not load key with any available library.')
            app.key_entry.delete(0, tk.END)
            app.key_entry.insert(0, to_text(content))
            update_status('Public key loaded and stored in session.')

        file_handler('load', [('PEM files', '*.pem')], 'Load Public Key', action)

    def load_symmetric_key():
        def action(content):
            app.symmetric_key_in_session = content
            app.key_entry.delete(0, tk.END)
            try:
                if len(b64_decode(content)) == 32:
                    app.key_entry.insert(0, to_text(content))
                else:
                    app.key_entry.insert(0, b64_encode(content))
            except Exception:
                app.key_entry.insert(0, to_text(content))
            update_status('Symmetric key loaded and stored in session.')

        file_handler('load', [('Key files', '*.key'), ('All files', '*.*')], 'Load Symmetric Key', action)

    # ---------- UI State Machine ----------
    UI_STATES = {
        'Symmetric (Fernet)': {
            'primary': ('Encrypt', LABEL_PLAINTEXT, LABEL_CIPHERTEXT_B64),
            'secondary': ('Decrypt', LABEL_CIPHERTEXT_B64, LABEL_PLAINTEXT),
            'key_label': 'Fernet Key:', 'key_action_text': 'Generate', 'key_action_cmd': generate_fernet_key,
            'show_sym_io': True,
            'out_editable_secondary': False,
        },
        'Symmetric (AES-GCM)': {
            'primary': ('Encrypt', LABEL_PLAINTEXT, LABEL_CIPHERTEXT_B64),
            'secondary': ('Decrypt', LABEL_CIPHERTEXT_B64, LABEL_PLAINTEXT),
            'key_label': 'Derived AES Key (B64):', 'key_action_text': 'Derive',
            'key_action_cmd': generate_aes_key_from_password,
            'show_password_salt': True, 'show_sym_io': True,
            'out_editable_secondary': False,
        },
        'Symmetric (ChaCha20-Poly1305)': {
            'primary': ('Encrypt', LABEL_PLAINTEXT, LABEL_CIPHERTEXT_B64),
            'secondary': ('Decrypt', LABEL_CIPHERTEXT_B64, LABEL_PLAINTEXT),
            'key_label': 'Derived ChaCha20 Key (B64):', 'key_action_text': 'Derive',
            'key_action_cmd': generate_aes_key_from_password,
            'show_password_salt': True, 'show_sym_io': True,
            'out_editable_secondary': False,
        },
        'Asymmetric (RSA)': {
            'primary': ('Encrypt', LABEL_PLAINTEXT, LABEL_CIPHERTEXT_B64),
            'secondary': ('Decrypt', LABEL_CIPHERTEXT_B64, LABEL_PLAINTEXT),
            'key_label': 'Key Length / PEM:', 'key_action_text': 'Generate Pair', 'key_action_cmd': generate_rsa_keys,
            'entry_val': str(MIN_RSA_BITS), 'show_asym_io': True,
            'out_editable_secondary': False,
        },
        'Digital Signature (RSA-PSS)': {
            'primary': ('Sign', LABEL_MESSAGE, LABEL_SIGNATURE_B64),
            'secondary': ('Verify', LABEL_MESSAGE, LABEL_SIGNATURE_TO_VERIFY_B64),
            'key_label': 'RSA Key (PEM):', 'show_asym_io': True,
            'out_editable_secondary': True,
        },
        'Hash (SHA-256)': {'primary': ('Hash', LABEL_DATA_TO_HASH, LABEL_SHA256_HASH_HEX)},
        'Hash (SHA-512)': {'primary': ('Hash', LABEL_DATA_TO_HASH, LABEL_SHA512_HASH_HEX)},
        'Hash (MD5 - Insecure)': {'primary': ('Hash', LABEL_DATA_TO_HASH, LABEL_MD5_HASH_HEX)},
        'Hash (SHA-1 - Insecure)': {'primary': ('Hash', LABEL_DATA_TO_HASH, LABEL_SHA1_HASH_HEX)},
        'Hash (BLAKE2b)': {'primary': ('Hash', LABEL_DATA_TO_HASH, LABEL_BLAKE2B_HASH_HEX)},
        'Encode/Decode (Base64)': {'primary': ('Encode', LABEL_RAW_DATA, LABEL_BASE64_OUTPUT),
                                   'secondary': ('Decode', LABEL_BASE64_INPUT, LABEL_RAW_DATA)},
        'Encode/Decode (Base32)': {'primary': ('Encode', LABEL_RAW_DATA, LABEL_BASE32_OUTPUT),
                                   'secondary': ('Decode', LABEL_BASE32_INPUT, LABEL_RAW_DATA)},
        'Encode/Decode (Base85)': {'primary': ('Encode', LABEL_RAW_DATA, LABEL_BASE85_OUTPUT),
                                   'secondary': ('Decode', LABEL_BASE85_INPUT, LABEL_RAW_DATA)},
        'Encode/Decode (Hex)': {'primary': ('Encode', LABEL_RAW_DATA, LABEL_HEX_OUTPUT),
                                'secondary': ('Decode', LABEL_HEX_INPUT, LABEL_RAW_DATA)},
        'Encode/Decode (URL)': {'primary': ('Encode', LABEL_URL_COMPONENT, LABEL_URL_ENCODED_OUTPUT),
                                'secondary': ('Decode', LABEL_URL_ENCODED_INPUT, LABEL_URL_COMPONENT)},
        'Quantum-Resistant (Conceptual)': {
            'primary': ('Engage Quantum Shield', LABEL_CONCEPTUAL_DATA, LABEL_QUANTUM_SAFE_CIPHERTEXT),
            'secondary': ('Disengage Shield', LABEL_QUANTUM_SAFE_CIPHERTEXT, LABEL_CONCEPTUAL_DATA),
            'key_label': 'Post-Quantum Algorithm:', 'entry_val': 'CRYSTALS-Dilithium',
            'out_editable_secondary': False,
        },
        'Steganography (Conceptual)': {'primary': ('Embed', LABEL_SECRET_DATA, LABEL_COVER_FILE),
                                       'secondary': ('Extract', LABEL_COVER_FILE, LABEL_SECRET_DATA),
                                       'key_label': 'Cover File Path:'},
        'Secure Erase (Conceptual)': {'primary': ('Erase', LABEL_DATA_TO_ERASE, LABEL_ERASED_CONCEPTUAL),
                                      'secondary': ('Erase (Confirm)', LABEL_DATA_TO_ERASE, LABEL_ERASED_CONCEPTUAL),
                                      'key_label': 'Erasure Method:', 'entry_val': 'Gutmann 35-Pass'},
    }

    def get_current_method():
        selected = app.enc_methods_var.get()
        return selected if '---' not in selected else None

    def update_mode_ui(*_args):
        write_output_only('')
        app.key_entry.configure(style='TEntry')
        method = get_current_method()
        if not method: return

        is_primary = app.mode_var.get()
        state = UI_STATES.get(method, {})

        primary_cfg = state.get('primary', ('Primary', '--- Input ---', '--- Output ---'))
        secondary_cfg = state.get('secondary')

        app.primary_mode_label.set(primary_cfg[0])
        if secondary_cfg:
            app.secondary_mode_label.set(secondary_cfg[0])
            app.secondary_radio.grid()
        else:
            app.secondary_radio.grid_remove()
            if not is_primary: app.mode_var.set(True)

        active_cfg = primary_cfg if is_primary else secondary_cfg
        if active_cfg:
            app.operation_type.set(active_cfg[0])
            app.input_label_var.set(active_cfg[1])
            app.output_label_var.set(active_cfg[2])

        if not is_primary and state.get('out_editable_secondary'):
            app.output_box_.configure(state='normal')
        else:
            app.output_box_.configure(state='disabled')

        for widget in [app.key_label, app.key_entry, app.key_action_button,
                       app.password_label, app.password_entry, app.salt_label, app.salt_entry, app.generate_salt_button,
                       app.sym_key_io_frame, app.asym_key_io_frame]:
            widget.grid_remove()

        current_row = 0
        if state.get('key_label'):
            app.key_label.configure(text=state['key_label'])
            app.key_label.grid(row=current_row, column=0, sticky='w')
            app.key_entry.grid(row=current_row, column=1, sticky='ew', padx=5)
            if state.get('key_action_text'):
                app.key_action_button.configure(text=state['key_action_text'], command=state.get('key_action_cmd'))
                app.key_action_button.grid(row=current_row, column=2, sticky='e')
            current_row += 1

        if state.get('show_password_salt'):
            app.password_label.grid(row=current_row, column=0, sticky='w', pady=(5, 0))
            app.password_entry.grid(row=current_row, column=1, columnspan=2, sticky='ew', padx=5, pady=(5, 0))
            current_row += 1
            app.salt_label.grid(row=current_row, column=0, sticky='w', pady=(5, 0))
            app.salt_entry.grid(row=current_row, column=1, sticky='ew', padx=5, pady=(5, 0))
            app.generate_salt_button.grid(row=current_row, column=2, sticky='e', pady=(5, 0))
            current_row += 1

        if state.get('show_sym_io'):
            app.sym_key_io_frame.grid(row=current_row, column=0, columnspan=3, sticky='w', pady=(5, 0))

        if state.get('show_asym_io'):
            app.asym_key_io_frame.grid(row=current_row, column=0, columnspan=3, sticky='w', pady=(5, 0))

        app.key_entry.delete(0, tk.END)
        if method == 'Asymmetric (RSA)':
            if not is_primary and app.private_key_in_session:
                if _PYCRYPTODOME_OK and isinstance(app.private_key_in_session, PyCryptoRSA._RSAobj):
                    app.key_entry.insert(0, to_text(app.private_key_in_session.export_key('PEM')))
                elif _RSA_LIB_OK and isinstance(app.private_key_in_session, rsa.PrivateKey):
                    app.key_entry.insert(0, to_text(app.private_key_in_session.save_pkcs1('PEM')))
                update_status('Loaded private key from session')
            elif is_primary and app.public_key_in_session:
                if _PYCRYPTODOME_OK and isinstance(app.public_key_in_session, PyCryptoRSA.RsaKey):
                    app.key_entry.insert(0, to_text(app.public_key_in_session.export_key('PEM')))
                elif _RSA_LIB_OK and isinstance(app.public_key_in_session, rsa.PublicKey):
                    app.key_entry.insert(0, to_text(app.public_key_in_session.save_pkcs1('PEM')))
                update_status('Loaded public key from session')
            elif state.get('entry_val'):
                app.key_entry.insert(0, state['entry_val'])
        elif method == 'Digital Signature (RSA-PSS)':
            key_to_show = app.private_key_in_session if is_primary else app.public_key_in_session
            if key_to_show and _PYCRYPTODOME_OK:
                if isinstance(key_to_show, (PyCryptoRSA._RSAobj, PyCryptoRSA.RsaKey)):
                    app.key_entry.insert(0, to_text(key_to_show.export_key('PEM')))
                    update_status(f'Loaded {"private" if is_primary else "public"} key from session')
        elif 'Symmetric' in method and app.symmetric_key_in_session:
            key_text = b64_encode(app.symmetric_key_in_session)
            app.key_entry.insert(0, key_text)
            update_status('Loaded symmetric key from session')
        elif state.get('entry_val'):
            app.key_entry.insert(0, state['entry_val'])

        validate_inputs()

    def validate_inputs(*_args):
        is_valid, error_msg = True, 'Ready'
        method = get_current_method()
        if not method:
            is_valid, error_msg = False, 'Select a valid method.'

        if not is_valid:
            app.run_button.configure(state='disabled')
            update_status(error_msg, is_error=True)
            return

        input_val = app.input_box.get('1.0', tk.END).strip()
        key_val = app.key_entry.get().strip()
        password_val = app.password_entry.get().strip()
        salt_val = app.salt_entry.get().strip()
        is_primary = app.mode_var.get()

        for entry in [app.key_entry, app.password_entry, app.salt_entry]:
            entry.configure(style='TEntry')

        # Require input for hashing/enc/dec/signing/verify where appropriate
        needs_input = method not in ['Symmetric (Fernet)', 'Asymmetric (RSA)']
        if needs_input and not input_val:
            is_valid, error_msg = False, 'Input cannot be empty.'

        elif method == 'Symmetric (Fernet)':
            if not is_primary and not input_val:
                is_valid, error_msg = False, 'Ciphertext (Base64) required to decrypt.'
            if not key_val and not is_primary:
                is_valid, error_msg = False, 'Symmetric key cannot be empty.'
                app.key_entry.configure(style='Error.TEntry')
            elif key_val:
                try:
                    if len(b64_decode(key_val)) != 32: raise ValueError('Invalid key length')
                except Exception:
                    is_valid, error_msg = False, 'Invalid Fernet key format.'
                    app.key_entry.configure(style='Error.TEntry')

        elif method in ('Symmetric (AES-GCM)', 'Symmetric (ChaCha20-Poly1305)'):
            if not is_primary and not input_val:
                is_valid, error_msg = False, 'Ciphertext (Base64) required to decrypt.'
            if not password_val:
                is_valid, error_msg = False, 'Password cannot be empty for symmetric encryption.'
                app.password_entry.configure(style='Error.TEntry')
            elif not salt_val:
                is_valid, error_msg = False, 'Salt cannot be empty.'
                app.salt_entry.configure(style='Error.TEntry')
            else:
                try:
                    if not b64_decode(salt_val):
                        raise ValueError('Invalid salt')
                except Exception:
                    is_valid, error_msg = False, 'Invalid Salt format (must be Base64).'
                    app.salt_entry.configure(style='Error.TEntry')

        elif method == 'Asymmetric (RSA)':
            if is_primary:
                # allow either bit-length or preloaded public key
                if key_val:
                    try:
                        bits = int(key_val)
                        if not (MIN_RSA_BITS <= bits <= MAX_RSA_BITS): raise ValueError()
                    except ValueError:
                        is_valid, error_msg = False, f'Key length must be {MIN_RSA_BITS}-{MAX_RSA_BITS} or load a public key.'
                        app.key_entry.configure(style='Error.TEntry')
                elif not app.public_key_in_session:
                    is_valid, error_msg = False, 'Provide key length or load a public key.'
                    app.key_entry.configure(style='Error.TEntry')
                if not input_val:
                    is_valid, error_msg = False, 'Plaintext required to encrypt.'
            else:
                if not input_val:
                    is_valid, error_msg = False, 'Ciphertext (Base64) required to decrypt.'
                if not key_val and not app.private_key_in_session:
                    is_valid, error_msg = False, 'Private key cannot be empty.'
                    app.key_entry.configure(style='Error.TEntry')

        elif method == 'Digital Signature (RSA-PSS)':
            if is_primary:
                if not input_val:
                    is_valid, error_msg = False, 'Message is required to sign.'
                if not key_val and not app.private_key_in_session:
                    is_valid, error_msg = False, 'Private key (PEM) is required to sign.'
                    app.key_entry.configure(style='Error.TEntry')
            else:
                if not input_val:
                    is_valid, error_msg = False, 'Message is required to verify.'
                if not key_val and not app.public_key_in_session:
                    is_valid, error_msg = False, 'Public key (PEM) is required to verify.'
                    app.key_entry.configure(style='Error.TEntry')
                elif not app.output_box_.get('1.0', tk.END).strip():
                    is_valid, error_msg = False, 'Paste Base64 signature into Output box to verify.'

        elif method == 'Encode/Decode (Base64)' and not is_primary and input_val:
            try:
                base64.urlsafe_b64decode(_b64_fix_padding(input_val).encode('ascii'))
            except Exception:
                is_valid, error_msg = False, 'Input is not valid Base64.'
        elif method == 'Encode/Decode (Base32)' and not is_primary and input_val:
            try:
                base64.b32decode(_b64_fix_padding(input_val), casefold=True)
            except Exception:
                is_valid, error_msg = False, 'Input is not valid Base32.'
        elif method == 'Encode/Decode (Base85)' and not is_primary and input_val:
            try:
                base64.a85decode(input_val, adobe=False, ignorechars=' \t\r\n')
            except Exception:
                is_valid, error_msg = False, 'Input is not valid Base85.'
        elif method == 'Encode/Decode (Hex)' and not is_primary and input_val:
            try:
                bytes.fromhex(input_val)
            except Exception:
                is_valid, error_msg = False, 'Input is not valid Hex.'

        elif method == 'Quantum-Resistant (Conceptual)':
            if not input_val:
                is_valid, error_msg = False, 'Data is required.'

        elif method == 'Steganography (Conceptual)':
            if is_primary:
                if not input_val:
                    is_valid, error_msg = False, 'Secret data required to embed.'
                if not key_val:
                    is_valid, error_msg = False, 'Cover file path is required.'
                    app.key_entry.configure(style='Error.TEntry')
            else:
                if not input_val and not key_val:
                    is_valid, error_msg = False, 'Provide cover file path (in input or key).'

        elif method == 'Secure Erase (Conceptual)':
            if not input_val:
                is_valid, error_msg = False, 'Data to erase is required.'
            if not key_val:
                is_valid, error_msg = False, 'Erasure method is required.'
                app.key_entry.configure(style='Error.TEntry')

        app.run_button.configure(state='normal' if is_valid else 'disabled')
        update_status(error_msg, is_error=not is_valid)

    # ---------- Operation Handlers ----------
    def run_operation():
        method = get_current_method()
        is_primary = app.mode_var.get()

        handler_map = {
            'Symmetric (Fernet)': handle_fernet_encrypt if is_primary else handle_fernet_decrypt,
            'Symmetric (AES-GCM)': handle_aes_encrypt if is_primary else handle_aes_decrypt,
            'Symmetric (ChaCha20-Poly1305)': handle_chacha_encrypt if is_primary else handle_chacha_decrypt,
            'Asymmetric (RSA)': handle_rsa_encrypt if is_primary else handle_rsa_decrypt,
            'Digital Signature (RSA-PSS)': handle_rsa_sign if is_primary else handle_rsa_verify,
            'Hash (SHA-256)': lambda: handle_hash(hashlib.sha256),
            'Hash (SHA-512)': lambda: handle_hash(hashlib.sha512),
            'Hash (MD5 - Insecure)': lambda: handle_hash(hashlib.md5),
            'Hash (SHA-1 - Insecure)': handle_hash_sha1,
            'Hash (BLAKE2b)': handle_hash_blake2b,
            'Encode/Decode (Base64)': lambda: handle_encode_decode('b64', 'b64', is_primary, text_only=False),
            'Encode/Decode (Base32)': lambda: handle_encode_decode('b32', 'b32', is_primary, text_only=False),
            'Encode/Decode (Base85)': lambda: handle_encode_decode('b85', 'b85', is_primary, text_only=False),
            'Encode/Decode (Hex)': lambda: handle_encode_decode('hex', 'hex', is_primary, text_only=False),
            'Encode/Decode (URL)': lambda: handle_encode_decode('url', 'url', is_primary, text_only=True),
            'Quantum-Resistant (Conceptual)': handle_pqc_shield_primary if is_primary else handle_pqc_shield_secondary,
            'Steganography (Conceptual)': handle_steg_embed if is_primary else handle_steg_extract,
            'Secure Erase (Conceptual)': handle_secure_erase,
        }

        handler = handler_map.get(method)
        if not handler:
            return show_error('Error', 'Operation not implemented for this mode.')

        set_ui_busy(True)
        update_status(f'{app.operation_type.get()}ing...')
        threading.Thread(target=handler, daemon=True).start()

    enc_root.bind('<Escape>', lambda _e: enc_root.destroy(), add='+')

    update_mode_ui()

    def op_worker(func, success_msg, error_title):
        output, err = None, None
        try:
            output = func()
        except Exception as e:
            err = e

        def complete():
            if err:
                show_error(error_title, str(err))
            else:
                write_output_only(output)
                update_status(success_msg)
            set_ui_busy(False)

        try:
            if enc_root and enc_root.winfo_exists():
                enc_root.after(0, complete)
        except tk.TclError:
            pass

    def handle_fernet_encrypt():
        def task():
            key_text = app.key_entry.get().strip()
            if not key_text:
                enc_root.after(0, generate_fernet_key)
                raise Exception('Key was missing. A new key has been generated. Please try again.')
            fernet = Fernet(to_bytes(key_text))
            return b64_encode(fernet.encrypt(to_bytes(app.input_box.get('1.0', tk.END).strip())))

        op_worker(task, 'Fernet encryption successful', 'Fernet Encrypt')

    def handle_fernet_decrypt():
        def task():
            fernet = Fernet(to_bytes(app.key_entry.get().strip()))
            data_b64 = app.input_box.get('1.0', tk.END).strip()
            try:
                return to_text(fernet.decrypt(b64_decode(data_b64)))
            except InvalidToken:
                raise Exception('Fernet decryption failed: invalid token or wrong key.')

        op_worker(task, 'Fernet decryption successful', 'Fernet Decrypt')

    def handle_aes_encrypt():
        def task():
            if not app.symmetric_key_in_session:
                enc_root.after(0, generate_aes_key_from_password)
                raise Exception('No AES key in session. A new key has been derived. Please try again.')
            cipher = AES.new(app.symmetric_key_in_session, AES.MODE_GCM)
            ciphertext, tag = cipher.encrypt_and_digest(to_bytes(app.input_box.get('1.0', tk.END).strip()))
            return b64_encode(cipher.nonce + tag + ciphertext)

        op_worker(task, 'AES-GCM encryption successful', 'AES-GCM Encrypt')

    def handle_aes_decrypt():
        def task():
            if not app.symmetric_key_in_session:
                enc_root.after(0, generate_aes_key_from_password)
                raise Exception('No AES key in session. A new key has been derived. Please try again.')
            decoded_data = b64_decode(app.input_box.get('1.0', tk.END).strip())
            if len(decoded_data) < (NONCE_LEN_GCM + TAG_LEN_GCM):
                raise Exception('Ciphertext too short.')
            nonce, tag, ciphertext = decoded_data[:NONCE_LEN_GCM], decoded_data[
                NONCE_LEN_GCM:NONCE_LEN_GCM + TAG_LEN_GCM], decoded_data[NONCE_LEN_GCM + TAG_LEN_GCM:]
            cipher = AES.new(app.symmetric_key_in_session, AES.MODE_GCM, nonce=nonce)
            return to_text(cipher.decrypt_and_verify(ciphertext, tag))

        op_worker(task, 'AES-GCM decryption successful', 'AES-GCM Decrypt')

    def handle_chacha_encrypt():
        def task():
            if not app.symmetric_key_in_session:
                enc_root.after(0, generate_aes_key_from_password)
                raise Exception('No ChaCha20 key in session. A new key has been derived. Please try again.')
            try:
                from Crypto.Cipher import ChaCha20_Poly1305
            except Exception:
                raise Exception('ChaCha20-Poly1305 not available.')
            cipher = ChaCha20_Poly1305.new(key=app.symmetric_key_in_session)
            ciphertext, tag = cipher.encrypt_and_digest(to_bytes(app.input_box.get('1.0', tk.END).strip()))
            return b64_encode(cipher.nonce + tag + ciphertext)

        op_worker(task, 'ChaCha20-Poly1305 encryption successful', 'ChaCha20 Encrypt')

    def handle_chacha_decrypt():
        def task():
            if not app.symmetric_key_in_session:
                enc_root.after(0, generate_aes_key_from_password)
                raise Exception('No ChaCha20 key in session. A new key has been derived. Please try again.')
            try:
                from Crypto.Cipher import ChaCha20_Poly1305
            except Exception:
                raise Exception('ChaCha20-Poly1305 not available.')
            decoded_data = b64_decode(app.input_box.get('1.0', tk.END).strip())
            if len(decoded_data) < (12 + 16):
                raise Exception('Ciphertext too short.')
            nonce, tag, ciphertext = decoded_data[:12], decoded_data[12:28], decoded_data[28:]
            cipher = ChaCha20_Poly1305.new(key=app.symmetric_key_in_session, nonce=nonce)
            return to_text(cipher.decrypt_and_verify(ciphertext, tag))

        op_worker(task, 'ChaCha20-Poly1305 decryption successful', 'ChaCha20 Decrypt')

    def handle_rsa_encrypt():
        def task():
            pub_key = app.public_key_in_session
            if not pub_key: raise Exception('No public key in session. Generate or load a key pair.')
            plain_bytes = to_bytes(app.input_box.get('1.0', tk.END).strip())
            if _PYCRYPTODOME_OK and isinstance(pub_key, PyCryptoRSA.RsaKey):
                from Crypto.Cipher import PKCS1_OAEP
                session_key = get_random_bytes(32)
                cipher_aes = AES.new(session_key, AES.MODE_GCM)
                ciphertext, tag = cipher_aes.encrypt_and_digest(plain_bytes)
                cipher_rsa = PKCS1_OAEP.new(pub_key, hashAlgo=SHA256)
                enc_session_key = cipher_rsa.encrypt(session_key)
                return b64_encode(enc_session_key + cipher_aes.nonce + tag + ciphertext)
            elif _RSA_LIB_OK and isinstance(pub_key, rsa.PublicKey):
                max_len = rsa.common.byte_size(pub_key.n) - 11
                if len(plain_bytes) > max_len:
                    raise Exception(
                        f'Content too large for basic RSA (max: {max_len} bytes). Install PyCryptodome for hybrid encryption.')
                return b64_encode(rsa.encrypt(plain_bytes, pub_key))
            else:
                raise Exception('Unsupported public key type or no suitable RSA library available.')

        op_worker(task, 'RSA encryption successful', 'RSA Encrypt')

    def handle_rsa_decrypt():
        def task():
            priv_key = app.private_key_in_session
            if not priv_key: raise Exception('No private key in session. Generate or load a key pair.')
            decoded_data = b64_decode(app.input_box.get('1.0', tk.END).strip())
            if _PYCRYPTODOME_OK and isinstance(priv_key, PyCryptoRSA._RSAobj):
                from Crypto.Cipher import PKCS1_OAEP
                rsa_key_size_bytes = priv_key.size_in_bytes()
                min_len = rsa_key_size_bytes + NONCE_LEN_GCM + TAG_LEN_GCM
                if len(decoded_data) < min_len:
                    raise Exception('Ciphertext too short or wrong key.')
                enc_session_key = decoded_data[:rsa_key_size_bytes]
                nonce = decoded_data[rsa_key_size_bytes:rsa_key_size_bytes + NONCE_LEN_GCM]
                tag = decoded_data[rsa_key_size_bytes + NONCE_LEN_GCM:rsa_key_size_bytes + NONCE_LEN_GCM + TAG_LEN_GCM]
                ciphertext = decoded_data[rsa_key_size_bytes + NONCE_LEN_GCM + TAG_LEN_GCM:]
                cipher_rsa = PKCS1_OAEP.new(priv_key, hashAlgo=SHA256)
                session_key = cipher_rsa.decrypt(enc_session_key)
                cipher_aes = AES.new(session_key, AES.MODE_GCM, nonce=nonce)
                return to_text(cipher_aes.decrypt_and_verify(ciphertext, tag))
            elif _RSA_LIB_OK and isinstance(priv_key, rsa.PrivateKey):
                return to_text(rsa.decrypt(decoded_data, priv_key))
            else:
                raise Exception('Unsupported private key type or no suitable RSA library available.')

        op_worker(task, 'RSA decryption successful', 'RSA Decrypt')

    def handle_rsa_sign():
        def task():
            if not _PYCRYPTODOME_OK: raise Exception('PyCryptodome not available for signatures.')
            priv_key = app.private_key_in_session
            if not priv_key or not isinstance(priv_key, PyCryptoRSA._RSAobj):
                raise Exception('A private key from PyCryptodome is required to sign.')
            h = SHA256.new(to_bytes(app.input_box.get('1.0', tk.END).strip()))
            return b64_encode(pss.new(priv_key).sign(h))

        op_worker(task, 'Message signed successfully', 'RSA Sign')

    def handle_rsa_verify():
        def task():
            if not _PYCRYPTODOME_OK: raise Exception('PyCryptodome not available for verification.')
            pub_key = app.public_key_in_session
            if not pub_key or not isinstance(pub_key, PyCryptoRSA.RsaKey):
                raise Exception('A public key from PyCryptodome is required to verify.')
            h = SHA256.new(to_bytes(app.input_box.get('1.0', tk.END).strip()))
            signature_b64 = app.output_box_.get('1.0', tk.END).strip()
            signature = b64_decode(signature_b64)
            if not signature:
                raise Exception('No signature in output box to verify or invalid Base64.')
            verifier = pss.new(pub_key)
            try:
                verifier.verify(h, signature)
                return 'SIGNATURE VERIFIED: The signature is authentic.'
            except (ValueError, TypeError):
                raise Exception('VERIFICATION FAILED: The signature is not authentic.')

        op_worker(task, 'Verification complete', 'RSA Verify')

    def handle_hash(hash_algo):
        def task():
            h = hash_algo()
            h.update(to_bytes(app.input_box.get('1.0', tk.END).strip()))
            return h.hexdigest()

        op_worker(task, 'Hashing successful', 'Hash')

    def handle_hash_sha1():
        return handle_hash(hashlib.sha1)

    def handle_hash_blake2b():
        return handle_hash(hashlib.blake2b)

    def handle_encode_decode(mode_enc, mode_dec, is_encode, text_only=False):
        def task():
            data = app.input_box.get('1.0', tk.END).strip()
            if mode_enc == 'b64':
                return (b64_encode(to_bytes(data)) if is_encode else to_text(b64_decode(data)))
            if mode_enc == 'b32':
                return (base64.b32encode(to_bytes(data)).decode('ascii') if is_encode else to_text(
                    base64.b32decode(_b64_fix_padding(data), casefold=True)))
            if mode_enc == 'b85':
                return (base64.a85encode(to_bytes(data)).decode('ascii') if is_encode else to_text(
                    base64.a85decode(data, adobe=False, ignorechars=' \t\r\n')))
            if mode_enc == 'hex':
                return (to_bytes(data).hex() if is_encode else to_text(bytes.fromhex(data)))
            if mode_enc == 'url':
                return (quote(data, safe='') if is_encode else unquote(data))
            return data

        op_worker(task, f'{"Encoding" if is_encode else "Decoding"} successful', 'Encode/Decode')

    # ---------- Conceptual Methods (Completed Implementations) ----------
    def handle_pqc_shield_primary():
        def task():
            # Simulate PQC: hash data and wrap with a marker
            data = app.input_box.get('1.0', tk.END).strip().encode('utf-8')
            if not data:
                raise Exception('No data to protect.')
            digest = hashlib.sha512(data).digest()
            header = b'PQ-SHIELD|ALG=' + app.key_entry.get().strip().encode('utf-8') or b'CRYSTALS-Dilithium'
            payload = base64.urlsafe_b64encode(digest + b'|' + data)
            return to_text(base64.urlsafe_b64encode(header + b'::' + payload))
        op_worker(task, 'Quantum shield engaged', 'Quantum Shield')

    def handle_pqc_shield_secondary():
        def task():
            blob_b64 = app.input_box.get('1.0', tk.END).strip()
            raw = b64_decode(blob_b64)
            if b'::' not in raw:
                raise Exception('Invalid quantum-safe package.')
            header, payload_b64 = raw.split(b'::', 1)
            try:
                inner = base64.urlsafe_b64decode(payload_b64)
            except Exception:
                raise Exception('Corrupted quantum-safe payload.')
            if b'|' not in inner:
                raise Exception('Invalid quantum-safe payload format.')
            digest, original = inner.split(b'|', 1)
            if hashlib.sha512(original).digest() != digest:
                raise Exception('Integrity check failed.')
            return to_text(original)
        op_worker(task, 'Quantum shield disengaged', 'Quantum Shield')

    def handle_steg_embed():
        def task():
            secret = app.input_box.get('1.0', tk.END).strip()
            cover = app.key_entry.get().strip()
            if not secret or not cover:
                raise Exception('Secret and cover path are required.')
            # Conceptual: produce a token that references the cover path and embeds the data
            token = {
                'cover': cover,
                'data': b64_encode(secret.encode('utf-8'))
            }
            return b64_encode(to_bytes(str(token)))
        op_worker(task, 'Steganography embed simulated', 'Steganography')

    def handle_steg_extract():
        def task():
            token_b64 = app.input_box.get('1.0', tk.END).strip()
            if not token_b64:
                raise Exception('Provide the conceptual stego token.')
            raw = b64_decode(token_b64)
            s = to_text(raw)
            # Very simple extraction (since conceptual): parse dict-like string
            if "'data':" not in s:
                raise Exception('Invalid stego token.')
            try:
                data_part = s.split("'data':", 1)[1].split('}', 1)[0].strip().strip("'").strip('"')
                return to_text(b64_decode(data_part))
            except Exception:
                raise Exception('Failed to extract conceptual data.')
        op_worker(task, 'Steganography extract simulated', 'Steganography')

    def handle_secure_erase():
        def task():
            data = app.input_box.get('1.0', tk.END)
            method = app.key_entry.get().strip() or 'Gutmann 35-Pass'
            if not data:
                raise Exception('No data to erase.')
            passes = 3
            if 'Gutmann' in method: passes = 7
            elif 'DoD' in method: passes = 3
            # Simulate overwrite passes and return a report
            report = [f'Erase method: {method}', f'Passes: {passes}', 'Result: Data overwritten (conceptual).']
            return '\n'.join(report)
        op_worker(task, 'Secure erase simulated', 'Secure Erase')

    # ---------- Bindings & Initial State ----------
    app.mode_var.trace_add('write', update_mode_ui)
    app.key_entry.bind('<KeyRelease>', validate_inputs)
    app.password_entry.bind('<KeyRelease>', validate_inputs)
    app.salt_entry.bind('<KeyRelease>', validate_inputs)
    app.input_box.bind('<KeyRelease>', validate_inputs)

    app.clear_button.configure(command=clear_fields)
    app.paste_button.configure(command=paste_from_clipboard_or_editor)
    app.copy_button.configure(command=copy_to_clipboard_or_editor)
    app.swap_button.configure(command=swap_input_output)
    app.run_button.configure(command=run_operation)
    app.generate_salt_button.configure(command=generate_salt)

    app.load_sym_key_button.configure(command=load_symmetric_key)
    app.save_sym_key_button.configure(command=save_symmetric_key)
    app.load_priv_key_button.configure(command=load_private_key)
    app.save_priv_key_button.configure(command=save_private_key)
    app.load_pub_key_button.configure(command=load_public_key)
    app.save_pub_key_button.configure(command=save_public_key)

    Tooltip(app.key_entry, 'Key or parameter. For RSA: PEM or bit length. For symmetric: base64 key or derive.')
    Tooltip(app.password_entry, 'Password for key derivation (PBKDF2-HMAC-SHA256).')
    Tooltip(app.salt_entry, 'Base64 salt for PBKDF2. Click "New Salt" to generate.')
    Tooltip(app.enc_methods_combo, 'Choose a cryptography or encoding method.')

    enc_root.bind('<Escape>', lambda _e: enc_root.destroy(), add='+')

    def on_combo_select(event):
        selected_value = app.enc_methods_var.get()
        if '---' in selected_value:
            enc_root.after(10, lambda: app.enc_methods_combo.set(previous_method[0]))

    def on_combo_change(*_args):
        current_value = app.enc_methods_var.get()
        if '---' not in current_value:
            previous_method[0] = current_value
        update_mode_ui()

    previous_method = [app.enc_methods_var.get()]
    app.enc_methods_combo.bind('<<ComboboxSelected>>', on_combo_select)
    app.enc_methods_var.trace_add('write', on_combo_change)

    update_mode_ui()
