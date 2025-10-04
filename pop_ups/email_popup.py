import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import tkinter.font as tkFont
from email.message import EmailMessage
from smtplib import SMTP_SSL, SMTPException
import ssl
import json
import re
from datetime import datetime
import os
import webbrowser
import tempfile
import html
import time
from services.security_service import SecurityService


# CollapsibleFrame provides a custom widget that can expand or collapse to show/hide its content.
class CollapsibleFrame(ttk.Frame):
    '''A collapsible frame widget for tkinter.'''
    def __init__(self, parent, text='', padding=10):
        super().__init__(parent, padding=padding)
        self.text = text
        self.columnconfigure(0, weight=1)

        # The toggle button shows the frame's title and controls its state.
        self.toggle_button = ttk.Button(self, text=f'- {self.text}', command=self.toggle, style='Link.TButton')
        self.toggle_button.grid(row=0, column=0, sticky='w')

        # The sub_frame holds the content of the collapsible section.
        self.sub_frame = ttk.Frame(self, padding=(10, 5, 10, 10))
        self.sub_frame.grid(row=1, column=0, sticky='nsew')

        self.is_collapsed = False

    def toggle(self):
        '''Toggles the visibility of the sub_frame.'''
        self.is_collapsed = not self.is_collapsed
        if self.is_collapsed:
            self.sub_frame.grid_remove()
            self.toggle_button.configure(text=f'+ {self.text}')
        else:
            self.sub_frame.grid()
            self.toggle_button.configure(text=f'- {self.text}')


def open_email(owner):
    '''
    Initializes and displays the main email client window.
    This function sets up the entire UI and handles all the logic for the email tool.
    'owner' is expected to be an object with a 'data' attribute for storing preferences.
    '''
    if not hasattr(owner, 'data'):
        messagebox.showerror('EgonTE', 'Email tool requires a data store on the owner object.')
        return

    # --- Main Window Setup ---
    email_root = owner.make_pop_ups_window(open_email)
    email_root.title('EgonTE Email Client')
    email_root.columnconfigure(0, weight=1)
    email_root.rowconfigure(0, weight=1)

    # --- Security Service ---
    security_service = SecurityService()

    # --- State Variables ---
    file_type = 'this'
    custom_text_active = False
    custom_box = None
    email_c_frame = None
    file_name = ''
    attachments = []
    contacts = {}
    templates = {}
    drafts = {}
    lockout_timer_id = None

    # --- UI Component Variables ---
    receiver_box = cc_box = bcc_box = reply_to_box = subject_box = None
    loc_button = custom_button = th_button = email_button_dict = None
    stats_label = attach_list = add_attach_btn = remove_attach_btn = clear_attach_btn = None
    attach_status = test_btn = preview_btn = send_button = status_label = progress_bar = None
    contact_search_entry = contact_search_clear_btn = contact_tree = None
    contact_to_btn = contact_cc_btn = contact_bcc_btn = contact_name_entry = None
    contact_email_entry = add_contact_btn = remove_contact_btn = None
    template_search_entry = template_search_clear_btn = template_list = None
    load_template_btn = delete_template_btn = template_name_entry = save_template_btn = None
    drafts_list = load_draft_btn = save_draft_btn = delete_draft_btn = None
    sender_box = password_box = show_pwd_var = show_pwd_btn = smtp_server_box = None
    smtp_port_box = copy_self_var = copy_self_chk = signature_box = None
    store_credentials_var = store_contacts_var = store_templates_var = store_drafts_var = clear_drafts_on_exit_var = None
    security_log_box = password_strength_label = strict_sanitization_var = None
    brute_force_protection_var = pgp_encryption_var = network_anomaly_detection_var = None
    encryption_password_entry = encryption_password_frame = None
    decryption_password_entry = decrypt_input_box = decrypt_output_box = None

    # --- Styling ---
    style = ttk.Style(email_root)
    style.configure('Link.TButton', font=('sans-serif', 10, 'underline'), foreground='blue')
    style.configure('Accent.TButton', font=('sans-serif', 10, 'bold'))
    style.configure('Danger.TButton', font=('sans-serif', 10), foreground='red')

    # --- Main UI: Notebook (Tabs) ---
    notebook = ttk.Notebook(email_root)
    notebook.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

    compose_tab = ttk.Frame(notebook, padding=10)
    contacts_tab = ttk.Frame(notebook, padding=10)
    templates_tab = ttk.Frame(notebook, padding=10)
    drafts_tab = ttk.Frame(notebook, padding=10)
    decrypt_tab = ttk.Frame(notebook, padding=10)
    settings_tab = ttk.Frame(notebook, padding=10)
    privacy_tab = ttk.Frame(notebook, padding=10)
    security_tab = ttk.Frame(notebook, padding=10)

    notebook.add(compose_tab, text='Compose')
    notebook.add(contacts_tab, text='Contacts')
    notebook.add(templates_tab, text='Templates')
    notebook.add(drafts_tab, text='Drafts')
    notebook.add(decrypt_tab, text='Decrypt')
    notebook.add(settings_tab, text='Settings')
    notebook.add(privacy_tab, text='Privacy')
    notebook.add(security_tab, text='Security')

    # =====================================================================================
    # --- LOGIC AND HELPERS --- #
    # =====================================================================================
    def log_security_event(message, level='INFO'):
        '''Adds a timestamped message to the security log with a severity level.'''
        if security_log_box:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            full_message = f'[{timestamp}] [{level}] {message}\n'
            security_log_box.config(state='normal')
            security_log_box.insert('1.0', full_message)
            if level == 'HIGH' or level == 'CRITICAL':
                tag_name = f'sev_{level}_{time.time()}'  # Unique tag
                security_log_box.tag_add(tag_name, '1.0', '1.end')
                security_log_box.tag_config(tag_name, foreground='red', font=('sans-serif', 8, 'bold'))
            security_log_box.config(state='disabled')

    def update_password_strength(event=None):
        '''Callback to update the password strength indicator.'''
        password = password_box.get()
        strength, color = security_service.check_password_strength(password)
        if password_strength_label:
            password_strength_label.config(text=f'Strength: {strength}' if strength else '', foreground=color or 'grey')

    def _start_lockout_timer(duration, is_global=False):
        '''Starts a countdown timer for login lockout.'''
        nonlocal lockout_timer_id
        if lockout_timer_id: email_root.after_cancel(lockout_timer_id)

        remaining_time = duration
        if remaining_time <= 0:
            _end_lockout_timer()
            return

        lockout_msg = f'Login locked out for {remaining_time}s...'
        if is_global: lockout_msg = f'Global lockout for {remaining_time}s due to anomalous activity...'

        status_label.config(text=lockout_msg, foreground='red')
        test_btn.config(state='disabled')
        send_button.config(state='disabled')
        lockout_timer_id = email_root.after(1000, lambda: _start_lockout_timer(duration - 1, is_global))

    def _end_lockout_timer():
        '''Ends the login lockout and re-enables buttons.'''
        nonlocal lockout_timer_id
        if lockout_timer_id: email_root.after_cancel(lockout_timer_id)
        security_service.reset_lockout()
        status_label.config(text='', foreground='grey')
        test_btn.config(state='normal')
        send_button.config(state='normal')
        log_security_event('Login lockout ended. Buttons re-enabled.')

    def _update_login_buttons_state():
        '''Updates the state of login-related buttons based on lockout status.'''
        is_locked, remaining_time = security_service.is_login_locked_out()
        if is_locked:
            test_btn.config(state='disabled')
            send_button.config(state='disabled')
            _start_lockout_timer(remaining_time)
        else:
            test_btn.config(state='normal')
            send_button.config(state='normal')

    # =====================================================================================
    # --- UI CREATION --- #
    # =====================================================================================
    def _create_compose_tab():
        '''Creates and lays out all widgets for the 'Compose' tab.'''
        nonlocal receiver_box, cc_box, bcc_box, reply_to_box, subject_box, loc_button, custom_button, th_button, email_button_dict, stats_label, attach_list, add_attach_btn, remove_attach_btn, clear_attach_btn, attach_status, test_btn, preview_btn, send_button, status_label, progress_bar, pgp_encryption_var, encryption_password_entry, encryption_password_frame
        compose_tab.columnconfigure(0, weight=1)

        # Recipients section with fields for To, CC, BCC, and Reply-To.
        recipients_frame = CollapsibleFrame(compose_tab, 'Recipients')
        recipients_frame.grid(row=0, column=0, sticky='ew', pady=5)
        recipients_frame.sub_frame.columnconfigure(1, weight=1)
        receiver_title = ttk.Label(recipients_frame.sub_frame, text='To:')
        receiver_box = ttk.Entry(recipients_frame.sub_frame)
        cc_title = ttk.Label(recipients_frame.sub_frame, text='CC:')
        cc_box = ttk.Entry(recipients_frame.sub_frame)
        bcc_title = ttk.Label(recipients_frame.sub_frame, text='BCC:')
        bcc_box = ttk.Entry(recipients_frame.sub_frame)
        reply_to_title = ttk.Label(recipients_frame.sub_frame, text='Reply-To:')
        reply_to_box = ttk.Entry(recipients_frame.sub_frame)
        receiver_title.grid(row=0, column=0, sticky='w', pady=2, padx=2)
        receiver_box.grid(row=0, column=1, sticky='ew', pady=2)
        cc_title.grid(row=1, column=0, sticky='w', pady=2, padx=2)
        cc_box.grid(row=1, column=1, sticky='ew', pady=2)
        bcc_title.grid(row=2, column=0, sticky='w', pady=2, padx=2)
        bcc_box.grid(row=2, column=1, sticky='ew', pady=2)
        reply_to_title.grid(row=3, column=0, sticky='w', pady=2, padx=2)
        reply_to_box.grid(row=3, column=1, sticky='ew', pady=2)

        # Content section for the email subject.
        content_frame = CollapsibleFrame(compose_tab, 'Content')
        content_frame.grid(row=1, column=0, sticky='ew', pady=5)
        content_frame.sub_frame.columnconfigure(1, weight=1)
        subject_title = ttk.Label(content_frame.sub_frame, text='Subject:')
        subject_box = ttk.Entry(content_frame.sub_frame)
        subject_title.grid(row=0, column=0, sticky='w', pady=2, padx=2)
        subject_box.grid(row=0, column=1, sticky='ew', pady=2)

        # Encryption Frame
        encryption_password_frame = ttk.Frame(content_frame.sub_frame)
        encryption_password_frame.grid(row=1, column=1, sticky='ew', padx=2, pady=5)
        encryption_password_frame.columnconfigure(1, weight=1)
        pgp_encryption_var = tk.BooleanVar(value=False)
        pgp_check = ttk.Checkbutton(encryption_password_frame, text='Enable Encryption', variable=pgp_encryption_var, command=lambda: toggle_encryption_widgets())
        pgp_check.grid(row=0, column=0, sticky='w')
        encryption_password_entry = ttk.Entry(encryption_password_frame, show='*', width=20)
        encryption_password_entry.grid(row=0, column=1, sticky='ew', padx=5)
        ttk.Label(encryption_password_frame, text='(WARNING: Basic, non-secure encryption for demonstration only)', font=('sans-serif', 7, 'italic'), foreground='orange').grid(row=1, column=1, sticky='w', padx=5)

        # Body section with options for content source and character count.
        body_frame = CollapsibleFrame(compose_tab, 'Body')
        body_frame.grid(row=2, column=0, sticky='ew', pady=5)
        body_frame.sub_frame.columnconfigure(0, weight=1)
        body_btn_frame = ttk.Frame(body_frame.sub_frame)
        body_btn_frame.grid(row=0, column=0, sticky='ew')
        body_btn_frame.columnconfigure((0, 1, 2), weight=1)
        loc_button = ttk.Button(body_btn_frame, text='Local file')
        custom_button = ttk.Button(body_btn_frame, text='Custom Text')
        th_button = ttk.Button(body_btn_frame, text='This File')
        email_button_dict = {'this': th_button, 'none': custom_button, 'local': loc_button}
        loc_button.grid(row=0, column=0, sticky='ew', padx=2)
        custom_button.grid(row=0, column=1, sticky='ew', padx=2)
        th_button.grid(row=0, column=2, sticky='ew', padx=2)
        stats_label = ttk.Label(body_frame.sub_frame, text='', foreground='grey')
        stats_label.grid(row=1, column=0, sticky='w', pady=(5, 0))

        # Attachments section for adding and managing files.
        attach_frame = CollapsibleFrame(compose_tab, 'Attachments')
        attach_frame.grid(row=3, column=0, sticky='ew', pady=5)
        attach_frame.sub_frame.columnconfigure(0, weight=1)
        attach_list = tk.Listbox(attach_frame.sub_frame, height=4, exportselection=False)
        attach_scroll = ttk.Scrollbar(attach_frame.sub_frame, orient='vertical', command=attach_list.yview)
        attach_list.config(yscrollcommand=attach_scroll.set)
        attach_btn_frame = ttk.Frame(attach_frame.sub_frame)
        attach_btn_frame.columnconfigure((0, 1, 2), weight=1)
        add_attach_btn = ttk.Button(attach_btn_frame, text='Add...')
        remove_attach_btn = ttk.Button(attach_btn_frame, text='Remove Selected')
        clear_attach_btn = ttk.Button(attach_btn_frame, text='Clear All')
        attach_list.grid(row=0, column=0, sticky='nsew'); attach_scroll.grid(row=0, column=1, sticky='ns')
        attach_btn_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=5)
        add_attach_btn.grid(row=0, column=0, sticky='ew', padx=2)
        remove_attach_btn.grid(row=0, column=1, sticky='ew', padx=2)
        clear_attach_btn.grid(row=0, column=2, sticky='ew', padx=2)
        attach_status = ttk.Label(attach_frame.sub_frame, text='0 attachment(s)', foreground='grey')
        attach_status.grid(row=2, column=0, columnspan=2, sticky='w', pady=(5, 0))

        # Action buttons for sending, previewing, and testing.
        action_frame = ttk.Frame(compose_tab, padding=10)
        action_frame.grid(row=4, column=0, sticky='ew', pady=(10, 0))
        action_frame.columnconfigure(1, weight=1)
        test_btn = ttk.Button(action_frame, text='Test Login')
        preview_btn = ttk.Button(action_frame, text='Preview')
        send_button = ttk.Button(action_frame, text='Send', style='Accent.TButton')
        status_label = ttk.Label(action_frame, text='', foreground='grey')
        progress_bar = ttk.Progressbar(action_frame, mode='indeterminate')
        test_btn.grid(row=0, column=0, sticky='w')
        preview_btn.grid(row=0, column=1, sticky='e')
        send_button.grid(row=0, column=2, sticky='e')
        status_label.grid(row=1, column=0, columnspan=3, sticky='ew', pady=5)
        progress_bar.grid(row=2, column=0, columnspan=3, sticky='ew', pady=5)
        progress_bar.grid_remove()

        toggle_encryption_widgets()  # Set initial state

    def toggle_encryption_widgets():
        '''Shows or hides the encryption password field based on the checkbox.'''
        if pgp_encryption_var.get():
            encryption_password_frame.grid()
        else:
            encryption_password_frame.grid_remove()

    def _create_contacts_tab():
        '''Creates and lays out all widgets for the 'Contacts' tab.'''
        nonlocal contact_search_entry, contact_search_clear_btn, contact_tree, contact_to_btn, contact_cc_btn, contact_bcc_btn, contact_name_entry, contact_email_entry, add_contact_btn, remove_contact_btn
        contacts_tab.columnconfigure(0, weight=1); contacts_tab.rowconfigure(0, weight=1)
        # Frame for displaying and searching the contact list.
        contacts_frame = ttk.LabelFrame(contacts_tab, text='Contact List', padding=10)
        contacts_frame.grid(row=0, column=0, sticky='nsew'); contacts_frame.columnconfigure(0, weight=1); contacts_frame.rowconfigure(1, weight=1)
        contact_search_frame = ttk.Frame(contacts_frame)
        contact_search_frame.grid(row=0, column=0, sticky='ew', pady=(0, 5)); contact_search_frame.columnconfigure(0, weight=1)
        contact_search_entry = ttk.Entry(contact_search_frame)
        contact_search_entry.grid(row=0, column=0, sticky='ew', padx=(0, 2))
        contact_search_clear_btn = ttk.Button(contact_search_frame, text='X', width=3)
        contact_search_clear_btn.grid(row=0, column=1)
        contact_cols = ('Name', 'Email'); contact_tree = ttk.Treeview(contacts_frame, columns=contact_cols, show='headings', height=5)
        for col in contact_cols: contact_tree.heading(col, text=col)
        contact_tree.grid(row=1, column=0, sticky='nsew')
        contact_btn_frame = ttk.Frame(contacts_frame); contact_btn_frame.grid(row=2, column=0, sticky='ew', pady=5); contact_btn_frame.columnconfigure((0, 1, 2), weight=1)
        contact_to_btn = ttk.Button(contact_btn_frame, text='Insert to \'To\''); contact_cc_btn = ttk.Button(contact_btn_frame, text='Insert to \'CC\''); contact_bcc_btn = ttk.Button(contact_btn_frame, text='Insert to \'BCC\'')
        contact_to_btn.grid(row=0, column=0, padx=2, sticky='ew'); contact_cc_btn.grid(row=0, column=1, padx=2, sticky='ew'); contact_bcc_btn.grid(row=0, column=2, padx=2, sticky='ew')
        # Frame for adding or removing contacts.
        add_contact_frame = ttk.LabelFrame(contacts_tab, text='Add/Remove Contact', padding=10)
        add_contact_frame.grid(row=1, column=0, sticky='ew', pady=10); add_contact_frame.columnconfigure(1, weight=1)
        contact_name_label = ttk.Label(add_contact_frame, text='Name:'); contact_name_entry = ttk.Entry(add_contact_frame)
        contact_email_label = ttk.Label(add_contact_frame, text='Email:'); contact_email_entry = ttk.Entry(add_contact_frame)
        add_contact_btn = ttk.Button(add_contact_frame, text='Add Contact'); remove_contact_btn = ttk.Button(add_contact_frame, text='Remove Selected')
        contact_name_label.grid(row=0, column=0, padx=2, pady=2, sticky='w'); contact_name_entry.grid(row=0, column=1, padx=2, pady=2, sticky='ew')
        contact_email_label.grid(row=1, column=0, padx=2, pady=2, sticky='w'); contact_email_entry.grid(row=1, column=1, padx=2, pady=2, sticky='ew')
        add_contact_btn.grid(row=2, column=1, sticky='e', pady=5, padx=2); remove_contact_btn.grid(row=0, column=2, rowspan=2, sticky='se', pady=5, padx=2)

    def _create_templates_tab():
        '''Creates and lays out all widgets for the 'Templates' tab.'''
        nonlocal template_search_entry, template_search_clear_btn, template_list, load_template_btn, delete_template_btn, template_name_entry, save_template_btn
        templates_tab.columnconfigure(0, weight=1); templates_tab.rowconfigure(0, weight=1)
        # Frame for managing saved email templates.
        templates_frame = ttk.LabelFrame(templates_tab, text='Saved Templates', padding=10)
        templates_frame.grid(row=0, column=0, sticky='nsew'); templates_frame.columnconfigure(0, weight=1); templates_frame.rowconfigure(1, weight=1)
        template_search_frame = ttk.Frame(templates_frame); template_search_frame.grid(row=0, column=0, sticky='ew', pady=(0, 5)); template_search_frame.columnconfigure(0, weight=1)
        template_search_entry = ttk.Entry(template_search_frame); template_search_entry.grid(row=0, column=0, sticky='ew', padx=(0, 2))
        template_search_clear_btn = ttk.Button(template_search_frame, text='X', width=3); template_search_clear_btn.grid(row=0, column=1)
        template_list = tk.Listbox(templates_frame, height=6, exportselection=False); template_list.grid(row=1, column=0, sticky='nsew')
        template_btn_frame = ttk.Frame(templates_frame); template_btn_frame.grid(row=2, column=0, sticky='ew', pady=5); template_btn_frame.columnconfigure((0, 1), weight=1)
        load_template_btn = ttk.Button(template_btn_frame, text='Load Selected Template'); delete_template_btn = ttk.Button(template_btn_frame, text='Delete Selected')
        load_template_btn.grid(row=0, column=0, padx=2, sticky='ew'); delete_template_btn.grid(row=0, column=1, padx=2, sticky='ew')
        # Frame for saving the current email as a new template.
        save_template_frame = ttk.LabelFrame(templates_tab, text='Save Current Email as Template', padding=10)
        save_template_frame.grid(row=1, column=0, sticky='ew', pady=10); save_template_frame.columnconfigure(1, weight=1)
        template_name_label = ttk.Label(save_template_frame, text='Template Name:'); template_name_entry = ttk.Entry(save_template_frame)
        save_template_btn = ttk.Button(save_template_frame, text='Save Template')
        template_name_label.grid(row=0, column=0, padx=2, pady=2, sticky='w'); template_name_entry.grid(row=0, column=1, padx=2, pady=2, sticky='ew'); save_template_btn.grid(row=1, column=1, sticky='e', pady=5, padx=2)
        # Add a label to inform users about dynamic placeholders.
        placeholder_info = ttk.Label(save_template_frame, text='Use {name} for dynamic recipient name.', foreground='grey', font=('sans-serif', 8, 'italic'))
        placeholder_info.grid(row=2, column=1, sticky='w', pady=(0, 5), padx=2)

    def _create_drafts_tab():
        '''Creates and lays out all widgets for the 'Drafts' tab.'''
        nonlocal drafts_list, load_draft_btn, save_draft_btn, delete_draft_btn
        drafts_tab.columnconfigure(0, weight=1); drafts_tab.rowconfigure(0, weight=1)
        # Frame for managing saved email drafts.
        drafts_frame = ttk.LabelFrame(drafts_tab, text='Saved Drafts', padding=10)
        drafts_frame.grid(row=0, column=0, sticky='nsew'); drafts_frame.columnconfigure(0, weight=1); drafts_frame.rowconfigure(0, weight=1)
        drafts_list = tk.Listbox(drafts_frame, height=8, exportselection=False)
        drafts_list.grid(row=0, column=0, sticky='nsew')
        draft_btn_frame = ttk.Frame(drafts_frame); draft_btn_frame.grid(row=1, column=0, sticky='ew', pady=5)
        draft_btn_frame.columnconfigure((0, 1, 2), weight=1)
        load_draft_btn = ttk.Button(draft_btn_frame, text='Load Selected Draft'); save_draft_btn = ttk.Button(draft_btn_frame, text='Save Current as Draft'); delete_draft_btn = ttk.Button(draft_btn_frame, text='Delete Selected')
        load_draft_btn.grid(row=0, column=0, padx=2, sticky='ew'); save_draft_btn.grid(row=0, column=1, padx=2, sticky='ew'); delete_draft_btn.grid(row=0, column=2, padx=2, sticky='ew')

    def _create_decrypt_tab():
        '''Creates and lays out all widgets for the 'Decrypt' tab.'''
        nonlocal decryption_password_entry, decrypt_input_box, decrypt_output_box
        decrypt_tab.columnconfigure(0, weight=1)
        decrypt_tab.rowconfigure(2, weight=1)

        decrypt_frame = ttk.LabelFrame(decrypt_tab, text='Decrypt Message', padding=10)
        decrypt_frame.grid(row=0, column=0, sticky='ew', pady=5)
        decrypt_frame.columnconfigure(1, weight=1)

        ttk.Label(decrypt_frame, text='Password:').grid(row=0, column=0, sticky='w', padx=2, pady=2)
        decryption_password_entry = ttk.Entry(decrypt_frame, show='*', width=30)
        decryption_password_entry.grid(row=0, column=1, sticky='ew', padx=2, pady=2)

        ttk.Label(decrypt_tab, text='Encrypted Message:').grid(row=1, column=0, sticky='w', padx=10, pady=(10, 0))
        decrypt_input_box = tk.Text(decrypt_tab, height=6, wrap='word')
        decrypt_input_box.grid(row=2, column=0, sticky='nsew', padx=10, pady=5)

        ttk.Button(decrypt_tab, text='Decrypt', command=lambda: perform_decryption()).grid(row=3, column=0, sticky='e', padx=10, pady=5)

        ttk.Label(decrypt_tab, text='Decrypted Message:').grid(row=4, column=0, sticky='w', padx=10, pady=(10, 0))
        decrypt_output_box = tk.Text(decrypt_tab, height=6, wrap='word', state='disabled')
        decrypt_output_box.grid(row=5, column=0, sticky='nsew', padx=10, pady=5)

    def perform_decryption():
        '''Decrypts the content from the input box and shows it in the output box.'''
        encrypted_message = decrypt_input_box.get('1.0', 'end-1c').strip()
        password = decryption_password_entry.get()
        if not encrypted_message or not password:
            messagebox.showwarning('Input Required', 'Please provide the encrypted message and the password.', parent=email_root)
            return

        decrypted_message = security_service.decrypt_body(encrypted_message, password)
        decrypt_output_box.config(state='normal')
        decrypt_output_box.delete('1.0', 'end')
        decrypt_output_box.insert('1.0', decrypted_message)
        decrypt_output_box.config(state='disabled')
        log_security_event('Decryption performed.')

    def _create_settings_tab():
        '''Creates and lays out all widgets for the 'Settings' tab.'''
        nonlocal sender_box, password_box, show_pwd_var, show_pwd_btn, smtp_server_box, smtp_port_box, copy_self_var, copy_self_chk, signature_box, password_strength_label
        settings_tab.columnconfigure(0, weight=1)
        # Credentials frame for email and password.
        cred_frame = ttk.LabelFrame(settings_tab, text='Credentials', padding=10); cred_frame.grid(row=0, column=0, sticky='ew'); cred_frame.columnconfigure(1, weight=1)
        sender_title = ttk.Label(cred_frame, text='Your Email:'); sender_box = ttk.Entry(cred_frame, width=30)
        password_title = ttk.Label(cred_frame, text='Your Password:'); password_box = ttk.Entry(cred_frame, width=30, show='*')
        show_pwd_var = tk.BooleanVar(value=False); show_pwd_btn = ttk.Checkbutton(cred_frame, text='Show', variable=show_pwd_var)
        password_strength_label = ttk.Label(cred_frame, text='', font=('sans-serif', 8))

        sender_title.grid(row=0, column=0, sticky='w', pady=2, padx=2); sender_box.grid(row=0, column=1, sticky='ew', pady=2)
        password_title.grid(row=1, column=0, sticky='w', pady=2, padx=2); password_box.grid(row=1, column=1, sticky='ew', pady=2); show_pwd_btn.grid(row=1, column=2, sticky='w', padx=5)
        password_strength_label.grid(row=2, column=1, sticky='w', padx=2, pady=(0, 5))

        # SMTP server settings.
        smtp_frame = ttk.LabelFrame(settings_tab, text='SMTP Server', padding=10); smtp_frame.grid(row=1, column=0, sticky='ew', pady=10); smtp_frame.columnconfigure(1, weight=1)
        smtp_server_title = ttk.Label(smtp_frame, text='Server Address:'); smtp_server_box = ttk.Entry(smtp_frame, width=30)
        smtp_port_title = ttk.Label(smtp_frame, text='Port:'); smtp_port_box = ttk.Entry(smtp_frame, width=15)
        smtp_server_title.grid(row=0, column=0, sticky='w', pady=2, padx=2); smtp_server_box.grid(row=0, column=1, sticky='ew', pady=2)
        smtp_port_title.grid(row=1, column=0, sticky='w', pady=2, padx=2); smtp_port_box.grid(row=1, column=1, sticky='w', pady=2)
        # General preferences.
        prefs_frame = ttk.LabelFrame(settings_tab, text='Preferences', padding=10); prefs_frame.grid(row=2, column=0, sticky='ew'); prefs_frame.columnconfigure(1, weight=1)
        copy_self_var = tk.BooleanVar(value=False); copy_self_chk = ttk.Checkbutton(prefs_frame, text='Send me a copy of every email', variable=copy_self_var)
        copy_self_chk.grid(row=0, column=0, columnspan=2, sticky='w', pady=2)
        # Email signature editor.
        signature_frame = ttk.LabelFrame(settings_tab, text='Email Signature', padding=10); signature_frame.grid(row=3, column=0, sticky='ew', pady=10); signature_frame.columnconfigure(0, weight=1)
        signature_box = tk.Text(signature_frame, height=4, wrap='word'); signature_box.grid(row=0, column=0, sticky='ew')

    def _create_privacy_tab():
        '''Creates and lays out all widgets for the 'Privacy' tab.'''
        nonlocal store_credentials_var, store_contacts_var, store_templates_var, store_drafts_var, clear_drafts_on_exit_var
        privacy_tab.columnconfigure(0, weight=1)

        # --- Data Storage Settings ---
        storage_frame = ttk.LabelFrame(privacy_tab, text='Data Storage Options', padding=10)
        storage_frame.grid(row=0, column=0, sticky='ew', pady=5)
        storage_frame.columnconfigure(0, weight=1)

        store_credentials_var = tk.BooleanVar(value=True)
        store_contacts_var = tk.BooleanVar(value=True)
        store_templates_var = tk.BooleanVar(value=True)
        store_drafts_var = tk.BooleanVar(value=True)
        clear_drafts_on_exit_var = tk.BooleanVar(value=False)

        def on_privacy_change(option_name, value):
            log_security_event(f'Privacy setting \'{option_name}\' changed to: {value}')
            save_prefs()

        ttk.Checkbutton(storage_frame, text='Remember credentials and server settings', variable=store_credentials_var, command=lambda: on_privacy_change('Store Credentials', store_credentials_var.get())).grid(row=0, column=0, sticky='w')
        ttk.Checkbutton(storage_frame, text='Store contacts locally', variable=store_contacts_var, command=lambda: on_privacy_change('Store Contacts', store_contacts_var.get())).grid(row=1, column=0, sticky='w')
        ttk.Checkbutton(storage_frame, text='Store templates locally', variable=store_templates_var, command=lambda: on_privacy_change('Store Templates', store_templates_var.get())).grid(row=2, column=0, sticky='w')
        ttk.Checkbutton(storage_frame, text='Store drafts locally', variable=store_drafts_var, command=lambda: on_privacy_change('Store Drafts', store_drafts_var.get())).grid(row=3, column=0, sticky='w')
        ttk.Checkbutton(storage_frame, text='Automatically clear drafts on exit', variable=clear_drafts_on_exit_var, command=lambda: on_privacy_change('Clear Drafts on Exit', clear_drafts_on_exit_var.get())).grid(row=4, column=0, sticky='w', pady=(5, 0))

        # --- Data Management ---
        management_frame = ttk.LabelFrame(privacy_tab, text='Data Management', padding=10)
        management_frame.grid(row=1, column=0, sticky='ew', pady=10)
        management_frame.columnconfigure((0, 1), weight=1)

        ttk.Button(management_frame, text='Import Data...', command=lambda: import_data()).grid(row=0, column=0, sticky='ew', padx=2, pady=2)
        ttk.Button(management_frame, text='Export Data...', command=lambda: export_data()).grid(row=0, column=1, sticky='ew', padx=2, pady=2)
        ttk.Button(management_frame, text='Clear Contacts', command=lambda: clear_contacts()).grid(row=1, column=0, sticky='ew', padx=2, pady=2)
        ttk.Button(management_frame, text='Clear Templates', command=lambda: clear_templates()).grid(row=1, column=1, sticky='ew', padx=2, pady=2)
        ttk.Button(management_frame, text='Clear Drafts', command=lambda: clear_drafts()).grid(row=2, column=0, sticky='ew', padx=2, pady=2)
        ttk.Button(management_frame, text='Clear Stored Credentials', command=lambda: clear_credentials()).grid(row=2, column=1, sticky='ew', padx=2, pady=2)
        ttk.Button(management_frame, text='Clear All Stored Data', command=lambda: clear_all_data(), style='Danger.TButton').grid(row=3, column=0, columnspan=2, sticky='ew', pady=(10, 0))

        # --- Disclaimer ---
        disclaimer_text = 'This tool stores data locally in your project\'s settings. Passwords are not stored, but your email address and server settings can be remembered for convenience. No data is sent to external servers, except when you send an email.'
        disclaimer_label = ttk.Label(privacy_tab, text=disclaimer_text, wraplength=450, justify='left', foreground='grey')
        disclaimer_label.grid(row=2, column=0, sticky='ew', pady=15, padx=10)

    def _create_security_tab():
        '''Creates and lays out all widgets for the 'Security' tab.'''
        nonlocal security_log_box, strict_sanitization_var, brute_force_protection_var, network_anomaly_detection_var
        security_tab.columnconfigure(0, weight=1)
        security_tab.rowconfigure(1, weight=1)

        def on_security_setting_change(option_name, value):
            log_security_event(f'Security setting \'{option_name}\' changed to: {value}')
            if option_name == 'Brute-Force Protection': security_service.brute_force_protection_enabled = value
            if option_name == 'Login Anomaly Detection': security_service.anomaly_detection_enabled = value
            save_prefs()
            _update_login_buttons_state()

        # --- Advanced Security Features ---
        adv_sec_frame = ttk.LabelFrame(security_tab, text='Advanced Security Features', padding=10)
        adv_sec_frame.grid(row=0, column=0, sticky='ew', pady=5)
        adv_sec_frame.columnconfigure(1, weight=1)

        # Input Sanitization (Anti-Injection)
        strict_sanitization_var = tk.BooleanVar(value=True)
        sanitization_check = ttk.Checkbutton(adv_sec_frame, text='Enable Strict Input Sanitization (Blocks potentially malicious characters)', variable=strict_sanitization_var, command=lambda: on_security_setting_change('Strict Sanitization', strict_sanitization_var.get()))
        sanitization_check.grid(row=0, column=0, columnspan=2, sticky='w', padx=2, pady=2)

        # Brute-Force Login Protection
        brute_force_protection_var = tk.BooleanVar(value=True)
        brute_force_check = ttk.Checkbutton(adv_sec_frame, text='Enable Brute-Force Login Protection (Lockout after 5 failed attempts)', variable=brute_force_protection_var, command=lambda: on_security_setting_change('Brute-Force Protection', brute_force_protection_var.get()))
        brute_force_check.grid(row=1, column=0, columnspan=2, sticky='w', padx=2, pady=2)

        # Network Anomaly Detection (Placeholder)
        network_anomaly_detection_var = tk.BooleanVar(value=False)
        net_anomaly_check = ttk.Checkbutton(adv_sec_frame, text='Enable Login Anomaly Detection (Detects password spraying)', variable=network_anomaly_detection_var, command=lambda: on_security_setting_change('Login Anomaly Detection', network_anomaly_detection_var.get()))
        net_anomaly_check.grid(row=2, column=0, columnspan=2, sticky='w', padx=2, pady=2)

        # --- Security Log ---
        log_frame = ttk.LabelFrame(security_tab, text='Security Log', padding=10)
        log_frame.grid(row=1, column=0, sticky='nsew', pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        security_log_box = tk.Text(log_frame, height=8, wrap='word', state='disabled', font=('sans-serif', 8))
        log_scroll = ttk.Scrollbar(log_frame, orient='vertical', command=security_log_box.yview)
        security_log_box.config(yscrollcommand=log_scroll.set)
        security_log_box.grid(row=0, column=0, sticky='nsew')
        log_scroll.grid(row=0, column=1, sticky='ns')

        # --- Security Recommendations ---
        reco_frame = ttk.LabelFrame(security_tab, text='Recommendations', padding=10)
        reco_frame.grid(row=2, column=0, sticky='ew', pady=5)
        reco_frame.columnconfigure(0, weight=1)

        reco_text = '• Use App Passwords: If your email provider supports it, use a unique \'app password\' instead of your main password.\n• Phishing Awareness: Never enter your password after clicking a link in an email you don\'t trust.\n• Data Storage: Be mindful of what you store in contacts, templates, and drafts.'
        ttk.Label(reco_frame, text=reco_text, wraplength=450, justify='left').grid(row=0, column=0, sticky='w')

    # Initialize all UI tabs.
    _create_compose_tab()
    _create_contacts_tab()
    _create_templates_tab()
    _create_drafts_tab()
    _create_decrypt_tab()
    _create_settings_tab()
    _create_privacy_tab()
    _create_security_tab()

    def export_data():
        '''Exports contacts and templates to a JSON file.'''
        file_path = filedialog.asksaveasfilename(parent=email_root, title='Export Data', defaultextension='.json', filetypes=[('JSON files', '*.json')])
        if not file_path: return
        try:
            data_to_export = {
                'contacts': contacts if store_contacts_var.get() else {},
                'templates': templates if store_templates_var.get() else {}
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_export, f, indent=4)
            status_label.config(text=f'Data exported to {os.path.basename(file_path)}', foreground='green')
            log_security_event(f'Data exported to {os.path.basename(file_path)}')
        except Exception as e:
            messagebox.showerror('Export Error', f'Failed to export data.\n{e}', parent=email_root)

    def import_data():
        '''Imports contacts and templates from a JSON file.'''
        nonlocal contacts, templates
        file_path = filedialog.askopenfilename(parent=email_root, title='Import Data', filetypes=[('JSON files', '*.json')])
        if not file_path: return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)

            if messagebox.askyesno('Confirm Import', 'This will merge imported contacts and templates with your current data. Continue?', parent=email_root):
                log_security_event(f'Starting data import from {os.path.basename(file_path)}')
                if 'contacts' in imported_data and store_contacts_var.get():
                    contacts.update(imported_data['contacts'])
                    _populate_contacts()
                if 'templates' in imported_data and store_templates_var.get():
                    templates.update(imported_data['templates'])
                    _populate_templates()
                save_prefs()
                status_label.config(text='Data imported successfully.', foreground='green')
                log_security_event('Data import successful.')

        except Exception as e:
            log_security_event(f'Data import failed: {e}')
            messagebox.showerror('Import Error', f'Failed to import data. Make sure it is a valid JSON file.\n{e}', parent=email_root)

    def clear_credentials():
        if messagebox.askyesno('Confirm', 'Clear stored email, and server settings? This action cannot be undone.', parent=email_root, icon='warning'):
            log_security_event('User initiated credential clearing.')
            for key in ['last_email_from', 'last_smtp_server', 'last_smtp_port']:
                if key in owner.data: del owner.data[key]
            sender_box.delete(0, 'end')
            smtp_server_box.delete(0, 'end')
            smtp_port_box.delete(0, 'end')
            status_label.config(text='Credentials cleared.', foreground='green')
            log_security_event('Stored credentials cleared.')

    def clear_contacts():
        if messagebox.askyesno('Confirm', 'Clear all stored contacts?', parent=email_root):
            contacts.clear()
            if 'email_contacts' in owner.data: del owner.data['email_contacts']
            _populate_contacts()
            status_label.config(text='Contacts cleared.', foreground='green')
            log_security_event('All contacts cleared.')

    def clear_templates():
        if messagebox.askyesno('Confirm', 'Clear all stored templates?', parent=email_root):
            templates.clear()
            if 'email_templates' in owner.data: del owner.data['email_templates']
            _populate_templates()
            status_label.config(text='Templates cleared.', foreground='green')
            log_security_event('All templates cleared.')

    def clear_drafts():
        if messagebox.askyesno('Confirm', 'Clear all stored drafts?', parent=email_root):
            drafts.clear()
            if 'email_drafts' in owner.data: del owner.data['email_drafts']
            _populate_drafts()
            status_label.config(text='Drafts cleared.', foreground='green')
            log_security_event('All drafts cleared.')

    def clear_all_data():
        '''Clears all stored user data.'''
        if messagebox.askyesno('Confirm Deletion', 'Are you sure you want to delete ALL stored credentials, contacts, templates, and drafts? This action is irreversible.', parent=email_root, icon='warning'):
            log_security_event('User initiated clearing of ALL data.', level='HIGH')
            clear_credentials()
            clear_contacts()
            clear_templates()
            clear_drafts()
            if 'email_signature' in owner.data: del owner.data['email_signature']
            signature_box.delete('1.0', 'end')
            status_label.config(text='All data has been cleared.', foreground='green')
            log_security_event('All user data has been cleared from storage.')

    def validate_email(addr: str) -> bool:
        '''Validates an email address using a regular expression.'''
        if not addr:
            return False
        # A robust regex for email validation.
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.fullmatch(regex, addr) is not None

    def update_attach_status():
        '''Updates the label showing the number and total size of attachments, with a warning for large sizes.'''
        total_size_mb = 0
        if attachments:
            try:
                # Calculate the total size of all attached files in bytes.
                total_size_bytes = sum(os.path.getsize(f) for f in attachments)
                total_size_mb = total_size_bytes / (1024 * 1024)
            except FileNotFoundError as e:
                # Handle cases where a file might have been moved or deleted after being attached.
                status_label.config(text='Attachment error: {} not found.'.format(os.path.basename(e.filename)), foreground='red')
                attachments.remove(e.filename)
                attach_list.delete(0, 'end')
                for f in attachments: attach_list.insert('end', os.path.basename(f))
                update_attach_status()
                return

        count_text = f'{len(attachments)} attachment(s)'
        size_text = f'{total_size_mb:.2f} MB'
        full_text = f'{count_text} | Total size: {size_text}'

        attach_status.config(text=full_text, foreground='red' if total_size_mb > 20 else 'grey')

    def update_body_stats():
        '''Updates the character count for the email body.'''
        try:
            text = ''
            if file_type == 'this':
                text = owner.EgonTE.get('1.0', 'end-1c')
            elif custom_box:
                text = custom_box.get('1.0', 'end-1c')
            stats_label.config(text=f'{len(text)} characters')
        except Exception:
            stats_label.config(text='')

    def _toggle_style(tag):
        '''Toggles text formatting (bold, italic, underline) in the custom text box.'''
        if not custom_box: return
        try:
            current_tags = custom_box.tag_names(tk.SEL_FIRST)
            if tag in current_tags:
                custom_box.tag_remove(tag, tk.SEL_FIRST, tk.SEL_LAST)
            else:
                custom_box.tag_add(tag, tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass  # Ignore if no text is selected.

    def file_mode(mode: str):
        '''
        Switches the source of the email body.
        'mode' can be 'this' (current file), 'local' (a file from disk), or 'none' (custom text).
        '''
        nonlocal file_type, custom_box, email_c_frame, custom_text_active
        file_type = mode
        # Update button styles to indicate the active mode.
        for btn in email_button_dict.values(): btn.state(['!pressed'])
        email_button_dict[mode].state(['pressed'])
        # Destroy the custom text frame if it exists.
        if custom_text_active and email_c_frame:
            email_c_frame.destroy()
            custom_text_active = False
            custom_box = None
        # Create the custom text box if 'none' mode is selected.
        if mode == 'none':
            email_c_frame = ttk.Frame(body_frame.sub_frame)
            email_c_frame.grid(row=2, column=0, sticky='nsew', pady=5)
            body_frame.sub_frame.rowconfigure(2, weight=1)
            email_c_frame.columnconfigure(0, weight=1)
            # Toolbar for text formatting.
            format_toolbar = ttk.Frame(email_c_frame)
            format_toolbar.grid(row=0, column=0, sticky='w', pady=(0, 2))
            text_container = ttk.Frame(email_c_frame)
            text_container.grid(row=1, column=0, sticky='nsew')
            text_container.rowconfigure(0, weight=1)
            text_container.columnconfigure(0, weight=1)
            custom_box = tk.Text(text_container, wrap='word', undo=True, height=10)
            v_scroll = ttk.Scrollbar(text_container, orient='vertical', command=custom_box.yview)
            custom_box.configure(yscrollcommand=v_scroll.set)
            v_scroll.grid(row=0, column=1, sticky='ns')
            custom_box.grid(row=0, column=0, sticky='nsew')
            # Configure fonts for text styling.
            default_font = tkFont.nametofont(custom_box.cget('font'))
            bold_font = tkFont.Font(family=default_font.cget('family'), size=default_font.cget('size'), weight='bold')
            italic_font = tkFont.Font(family=default_font.cget('family'), size=default_font.cget('size'), slant='italic')
            underline_font = tkFont.Font(family=default_font.cget('family'), size=default_font.cget('size'), underline=True)
            custom_box.tag_configure('bold', font=bold_font)
            custom_box.tag_configure('italic', font=italic_font)
            custom_box.tag_configure('underline', font=underline_font)
            ttk.Button(format_toolbar, text='B', width=3, command=lambda: _toggle_style('bold')).grid(row=0, column=0, padx=(0, 2))
            ttk.Button(format_toolbar, text='I', width=3, command=lambda: _toggle_style('italic')).grid(row=0, column=1, padx=2)
            ttk.Button(format_toolbar, text='U', width=3, command=lambda: _toggle_style('underline')).grid(row=0, column=2, padx=2)
            custom_text_active = True
            custom_box.bind('<KeyRelease>', lambda e: update_body_stats())
            # Automatically append the signature.
            signature = signature_box.get('1.0', 'end-1c').strip()
            if signature:
                custom_box.insert('end', '\n\n--\n' + signature)
        update_body_stats()

    def get_body():
        '''
        Retrieves the email body content based on the selected file_mode.
        Returns the content as a string, or None if a file dialog is cancelled.
        '''
        nonlocal file_name
        if file_type == 'local':
            try:
                local_name = filedialog.askopenfilename(parent=email_root)
                if not local_name: return None
                file_name = local_name
                with open(local_name, 'r', encoding='utf-8', errors='replace') as fp:
                    return fp.read()
            except Exception as e:
                messagebox.showerror('EgonTE', 'Failed to read file.\n' + str(e))
                return None
        elif file_type == 'this':
            file_name = getattr(owner, 'file_name', '') or 'current document'
            return owner.EgonTE.get('1.0', 'end-1c')
        elif custom_box:
            file_name = 'A message from {}'.format(sender_box.get().strip() or 'EgonTE user')
            return custom_box.get('1.0', 'end-1c')
        return ''

    def get_body_as_html():
        '''Converts the content of the custom text box to HTML for rich text emails.'''
        if not custom_box: return ''
        html_content = ''
        # The .dump() method provides a description of the text content, including tags.
        for key, value, index in custom_box.dump('1.0', 'end-1c'):
            if key == 'text':
                html_content += html.escape(value)
            elif key == 'tagon':
                if value == 'bold': html_content += '<b>'
                elif value == 'italic': html_content += '<i>'
                elif value == 'underline': html_content += '<u>'
            elif key == 'tagoff':
                if value == 'bold': html_content += '</b>'
                elif value == 'italic': html_content += '</i>'
                elif value == 'underline': html_content += '</u>'
        return '<html><body>{}</body></html>'.format(html_content.replace('\n', '<br>'))

    def validate_inputs():
        '''
        Validates all required fields before sending an email.
        Checks for security issues like header injection.
        Returns a tuple (bool, str) indicating success and an error message if any.
        '''
        # --- Field Values ---
        from_addr = sender_box.get().strip()
        pwd = password_box.get()
        to_addrs = receiver_box.get().strip()
        cc_addrs = cc_box.get().strip()
        bcc_addrs = bcc_box.get().strip()
        reply_to_addrs = reply_to_box.get().strip()
        subject = subject_box.get()  # Don't strip subject, whitespace may be intentional
        smtp_server = smtp_server_box.get().strip()
        smtp_port_str = smtp_port_box.get().strip()

        # --- Security Validations ---
        fields_to_check = {
            'From': from_addr, 'To': to_addrs, 'CC': cc_addrs,
            'BCC': bcc_addrs, 'Reply-To': reply_to_addrs, 'Subject': subject
        }

        for field_name, field_value in fields_to_check.items():
            # 1. Prevent Header Injection (Always On)
            if '\n' in field_value or '\r' in field_value:
                return False, f'Header injection attempt detected in \'{field_name}\' field. Newlines are not allowed.'
            # 2. Strict Sanitization (Optional)
            if strict_sanitization_var.get() and security_service.contains_malicious_chars(field_value):
                return False, f'Potentially malicious characters (e.g., ;, |, <, >) detected in \'{field_name}\' field.'

        # 3. Basic Field Presence
        if not from_addr: return False, 'Sender email required in Settings.'
        if not pwd: return False, 'Password required in Settings.'
        if not to_addrs: return False, '\'To\' address required.'
        if not smtp_server: return False, 'SMTP server required in Settings.'
        if not smtp_port_str: return False, 'SMTP port required in Settings.'

        # 4. Email Address Syntax Validation
        if not validate_email(from_addr): return False, 'Valid sender email required in Settings.'

        for addrs, label in [(to_addrs, 'To'), (cc_addrs, 'CC'), (bcc_addrs, 'BCC'), (reply_to_addrs, 'Reply-To')]:
            if addrs and not all(validate_email(p.strip()) for p in addrs.split(',') if p.strip()):
                return False, f'One or more invalid email addresses in \'{label}\' field.'

        # 5. Port Validation
        try:
            port = int(smtp_port_str)
            if not (1 <= port <= 65535):
                return False, 'SMTP port must be a number between 1 and 65535.'
        except ValueError:
            return False, 'SMTP port must be a valid number.'

        # 6. Encryption Password Check
        if pgp_encryption_var.get() and not encryption_password_entry.get():
            return False, 'Encryption is enabled, but no encryption password is provided.'

        return True, ''

    def add_attachments():
        '''Opens a file dialog to select and add attachments, with a size warning.'''
        nonlocal attachments
        old_size_bytes = sum(os.path.getsize(f) for f in attachments) if attachments else 0

        files = filedialog.askopenfilenames(parent=email_root)
        if not files: return

        added_count = 0
        for f_path in files:
            if f_path and f_path not in attachments:
                attachments.append(f_path)
                attach_list.insert('end', os.path.basename(f_path))
                added_count += 1

        if added_count > 0:
            new_size_bytes = sum(os.path.getsize(f) for f in attachments)
            if new_size_bytes / (1024 * 1024) > 20 and old_size_bytes / (1024 * 1024) <= 20:
                messagebox.showwarning('Attachment Size Warning',
                                       'Total attachment size ({:.2f} MB) exceeds the recommended 20 MB limit.'.format(new_size_bytes / (1024 * 1024)),
                                       parent=email_root)
        else:
            status_label.config(text='No new attachments added (already in list).')

        update_attach_status()

    def remove_selected_attachment():
        '''Removes the selected attachment from the list.'''
        nonlocal attachments
        sel = attach_list.curselection()
        if not sel: return
        # Iterate in reverse to avoid index shifting issues.
        for index in reversed(sel):
            del attachments[index]
            attach_list.delete(index)
        update_attach_status()

    def clear_attachments():
        '''Removes all attachments.'''
        nonlocal attachments
        attachments = []
        attach_list.delete(0, 'end')
        update_attach_status()

    def _populate_contacts(query=''):
        '''Populates the contact list, optionally filtering by a search query.'''
        for i in contact_tree.get_children(): contact_tree.delete(i)
        for name, email in contacts.items():
            if query.lower() in name.lower() or query.lower() in email.lower():
                contact_tree.insert('', 'end', values=(name, email))

    def add_contact():
        '''Adds a new contact to the list and saves preferences.'''
        name = contact_name_entry.get().strip()
        email = contact_email_entry.get().strip()
        if not name or not validate_email(email):
            messagebox.showwarning('Invalid Input', 'Please enter a valid name and email.', parent=email_root)
            return
        contacts[name] = email
        _populate_contacts()
        contact_name_entry.delete(0, 'end')
        contact_email_entry.delete(0, 'end')
        save_prefs()

    def remove_contact():
        '''Removes the selected contact from the list.'''
        selected_item = contact_tree.selection()
        if not selected_item: return
        name = contact_tree.item(selected_item[0])['values'][0]
        if name in contacts:
            del contacts[name]
        _populate_contacts()
        save_prefs()

    def insert_contact(field_box):
        '''Inserts the selected contact's email into a specified recipient field.'''
        selected_item = contact_tree.selection()
        if not selected_item: return
        email = contact_tree.item(selected_item[0])['values'][1]
        current_text = field_box.get()
        field_box.insert('end', f', {email}' if current_text else email)
        notebook.select(compose_tab)  # Switch back to the compose tab.

    def _populate_templates(query=''):
        '''Populates the template list, optionally filtering by a search query.'''
        template_list.delete(0, 'end')
        for name in sorted(templates.keys()):
            if query.lower() in name.lower():
                template_list.insert('end', name)

    def save_template():
        '''Saves the current email content as a template.'''
        name = template_name_entry.get().strip()
        if not name:
            messagebox.showwarning('Input Required', 'Please enter a name for the template.', parent=email_root)
            return
        body = get_body() if file_type != 'local' else ''
        if file_type == 'local':
            messagebox.showinfo('Info', 'Cannot save body from a local file.', parent=email_root)
        templates[name] = {
            'subject': subject_box.get(),
            'body': body,
            'body_tags': custom_box.dump('1.0', 'end-1c') if custom_box else []
        }
        _populate_templates()
        template_name_entry.delete(0, 'end')
        save_prefs()

    def load_template():
        '''
        Loads a selected template, replacing placeholders like {name}
        with the recipient\'s name if found in contacts.
        '''
        sel = template_list.curselection()
        if not sel: return
        template_name = template_list.get(sel[0])
        template = templates.get(template_name)
        if not template: return

        # --- Dynamic Placeholder Replacement ---
        recipient_email = receiver_box.get().strip().split(',')[0]  # Use the first recipient
        recipient_name = 'recipient'  # default value

        # Find recipient's name from contacts based on email
        if recipient_email:
            for name, email in contacts.items():
                if email == recipient_email:
                    recipient_name = name.split()[0]  # Use first name
                    break

        template_subject = template.get('subject', '').replace('{name}', recipient_name)

        # --- Load into UI ---
        subject_box.delete(0, 'end')
        subject_box.insert(0, template_subject)

        file_mode('none')  # Templates always use the custom text box.

        if custom_box:
            # To preserve rich text formatting, we must modify the 'text' values
            # within the list of tags and text provided by the .dump() method.
            body_tags = template.get('body_tags', [])
            new_body_tags = []
            for key, value, index in body_tags:
                if key == 'text':
                    # Replace placeholder in each text segment
                    new_body_tags.append((key, value.replace('{name}', recipient_name), index))
                else:
                    new_body_tags.append((key, value, index))

            custom_box.delete('1.0', 'end')
            for tag in ['bold', 'italic', 'underline']:
                custom_box.tag_remove(tag, '1.0', 'end')

            # Insert the modified content with tags.
            for key, value, index in new_body_tags:
                custom_box.insert(index, value, key)

        update_body_stats()
        notebook.select(compose_tab)

    def delete_template():
        '''Deletes the selected template.'''
        sel = template_list.curselection()
        if not sel: return
        name = template_list.get(sel[0])
        if name in templates:
            del templates[name]
        _populate_templates()
        save_prefs()

    def _populate_drafts():
        '''Populates the list of saved drafts.'''
        drafts_list.delete(0, 'end')
        for name in sorted(drafts.keys()):
            drafts_list.insert('end', name)

    def save_draft():
        '''Saves the current state of the email as a draft.'''
        nonlocal attachments
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        draft_name = f'Draft - {timestamp}'
        drafts[draft_name] = {
            'to': receiver_box.get(), 'cc': cc_box.get(), 'bcc': bcc_box.get(), 'reply_to': reply_to_box.get(),
            'subject': subject_box.get(), 'body': get_body(), 'attachments': list(attachments),
            'body_tags': custom_box.dump('1.0', 'end-1c') if custom_box else [], 'file_type': file_type
        }
        _populate_drafts()
        save_prefs()
        status_label.config(text=f'Saved \'{draft_name}\'')

    def load_draft():
        '''Loads a selected draft, restoring all fields and attachments.'''
        nonlocal attachments
        sel = drafts_list.curselection()
        if not sel: return
        draft = drafts.get(drafts_list.get(sel[0]))
        if not draft: return
        # Restore all recipient and subject fields.
        receiver_box.delete(0, 'end'); receiver_box.insert(0, draft.get('to', ''))
        cc_box.delete(0, 'end'); cc_box.insert(0, draft.get('cc', ''))
        bcc_box.delete(0, 'end'); bcc_box.insert(0, draft.get('bcc', ''))
        reply_to_box.delete(0, 'end'); reply_to_box.insert(0, draft.get('reply_to', ''))
        subject_box.delete(0, 'end'); subject_box.insert(0, draft.get('subject', ''))
        # Restore body and its format.
        file_mode(draft.get('file_type', 'this'))
        if draft.get('file_type') == 'none' and custom_box:
            custom_box.delete('1.0', 'end')
            for tag in ['bold', 'italic', 'underline']:
                custom_box.tag_remove(tag, '1.0', 'end')
            for key, value, index in draft.get('body_tags', []):
                custom_box.insert(index, value, key)
        # Restore attachments.
        attachments = draft.get('attachments', [])
        attach_list.delete(0, 'end')
        for f in attachments: attach_list.insert('end', os.path.basename(f))
        update_attach_status()
        update_body_stats()
        notebook.select(compose_tab)

    def delete_draft():
        '''Deletes the selected draft.'''
        sel = drafts_list.curselection()
        if not sel: return
        name = drafts_list.get(sel[0])
        if name in drafts:
            del drafts[name]
        _populate_drafts()
        save_prefs()

    def save_prefs():
        '''Saves user preferences based on privacy and security settings.'''
        try:
            # Save privacy and security settings
            owner.data['email_store_credentials'] = store_credentials_var.get()
            owner.data['email_store_contacts'] = store_contacts_var.get()
            owner.data['email_store_templates'] = store_templates_var.get()
            owner.data['email_store_drafts'] = store_drafts_var.get()
            owner.data['email_clear_drafts_on_exit'] = clear_drafts_on_exit_var.get()
            owner.data['email_strict_sanitization'] = strict_sanitization_var.get()
            owner.data['email_brute_force_protection'] = brute_force_protection_var.get()
            owner.data['email_pgp_encryption'] = pgp_encryption_var.get()
            owner.data['email_network_anomaly_detection'] = network_anomaly_detection_var.get()

            # Save or delete credentials
            if store_credentials_var.get():
                owner.data['last_email_from'] = sender_box.get().strip()
                owner.data['last_smtp_server'] = smtp_server_box.get().strip()
                owner.data['last_smtp_port'] = smtp_port_box.get().strip()
            else:
                for key in ['last_email_from', 'last_smtp_server', 'last_smtp_port']:
                    if key in owner.data: del owner.data[key]

            # Save or delete contacts
            if store_contacts_var.get():
                owner.data['email_contacts'] = json.dumps(contacts)
            elif 'email_contacts' in owner.data:
                del owner.data['email_contacts']

            # Save or delete templates
            if store_templates_var.get():
                owner.data['email_templates'] = json.dumps(templates)
            elif 'email_templates' in owner.data:
                del owner.data['email_templates']

            # Save or delete drafts
            if store_drafts_var.get():
                owner.data['email_drafts'] = json.dumps(drafts)
            elif 'email_drafts' in owner.data:
                del owner.data['email_drafts']

            owner.data['email_signature'] = signature_box.get('1.0', 'end-1c')

        except Exception as e:
            log_security_event(f'Error saving preferences: {e}', level='HIGH')
            print(f'Error saving prefs: {e}')

    def restore_prefs():
        '''Loads user preferences when the application starts.'''
        nonlocal contacts, templates, drafts
        try:
            # Restore privacy and security settings first
            store_credentials_var.set(owner.data.get('email_store_credentials', True))
            store_contacts_var.set(owner.data.get('email_store_contacts', True))
            store_templates_var.set(owner.data.get('email_store_templates', True))
            store_drafts_var.set(owner.data.get('email_store_drafts', True))
            clear_drafts_on_exit_var.set(owner.data.get('email_clear_drafts_on_exit', False))
            strict_sanitization_var.set(owner.data.get('email_strict_sanitization', True))
            brute_force_protection_var.set(owner.data.get('email_brute_force_protection', True))
            pgp_encryption_var.set(owner.data.get('email_pgp_encryption', False))
            network_anomaly_detection_var.set(owner.data.get('email_network_anomaly_detection', True))

            security_service.brute_force_protection_enabled = brute_force_protection_var.get()
            security_service.anomaly_detection_enabled = network_anomaly_detection_var.get()

            if store_credentials_var.get():
                sender_box.insert(0, owner.data.get('last_email_from', ''))
                smtp_server_box.insert(0, owner.data.get('last_smtp_server', 'smtp.gmail.com'))
                smtp_port_box.insert(0, owner.data.get('last_smtp_port', '465'))

            signature_box.insert('1.0', owner.data.get('email_signature', ''))

            if store_contacts_var.get():
                contacts = json.loads(owner.data.get('email_contacts', '{}'))
                _populate_contacts()

            if store_templates_var.get():
                templates = json.loads(owner.data.get('email_templates', '{}'))
                _populate_templates()

            if store_drafts_var.get():
                drafts = json.loads(owner.data.get('email_drafts', '{}'))
                _populate_drafts()
            log_security_event('User preferences and data restored.')
        except Exception as e:
            log_security_event(f'Error restoring preferences: {e}', level='HIGH')
            print(f'Error restoring prefs: {e}')
            # Set default SMTP values if restoration fails.
            if not smtp_server_box.get(): smtp_server_box.insert(0, 'smtp.gmail.com')
            if not smtp_port_box.get(): smtp_port_box.insert(0, '465')

    def show_preview():
        '''Generates and opens an interactive HTML preview of the email in a web browser.'''
        # --- Construct HTML Content ---
        from_addr = sender_box.get().strip()
        to_addr = receiver_box.get().strip()
        cc_addr = cc_box.get().strip()
        reply_to_addr = reply_to_box.get().strip()
        subject = subject_box.get().strip()

        if pgp_encryption_var.get():
            subject = f'[Encrypted] {subject}'

        # Get body content
        body_content = get_body() or ''
        if pgp_encryption_var.get():
            enc_pass = encryption_password_entry.get()
            body_content = security_service.encrypt_body(body_content, enc_pass)

        body_content_html = f'<html><body><pre>{html.escape(body_content)}</pre></body></html>'

        # Add signature to the body
        signature = signature_box.get('1.0', 'end-1c').strip()
        if signature and not pgp_encryption_var.get():  # Don't add signature to encrypted mail
            signature_html = html.escape(signature).replace('\n', '<br>')
            body_content_html = body_content_html.replace('</body>', '<p>--<br>{}</p></body>'.format(signature_html))

        # Extract only the content within <body> tags
        body_inner_html_match = re.search(r'<body.*?>(.*)</body>', body_content_html, re.DOTALL)
        body_inner_html = body_inner_html_match.group(1) if body_inner_html_match else ''

        # Create list of attachments
        attachment_list_html = ''
        if attachments:
            for f in attachments:
                attachment_list_html += f'<li>{os.path.basename(f)}</li>'

        attachments_html = '<ul>{}</ul>'.format(attachment_list_html) if attachments else '<p>None</p>'

        # --- Full HTML Document Template ---
        html_template = '''\
        <!DOCTYPE html>
        <html lang='en'>
        <head>
            <meta charset='UTF-8'>
            <meta http-equiv='Content-Security-Policy' content='default-src \'none\'; style-src \'unsafe-inline\';'>
            <title>Email Preview</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 2em; background-color: #f7f7f7; }}
                .container {{ max-width: 800px; margin: auto; background-color: #fff; border: 1px solid #ddd; border-radius: 5px; }}
                .header {{ padding: 20px; border-bottom: 1px solid #ddd; background-color: #f0f0f0; }}
                .header-item {{ margin-bottom: 8px; font-size: 14px; color: #333; }}
                .header-item strong {{ display: inline-block; width: 90px; color: #555; }}
                .body-content {{ padding: 20px; font-size: 16px; line-height: 1.6; }}
                .attachments {{ padding: 20px; border-top: 1px solid #ddd; background-color: #f0f0f0; }}
                ul {{ padding-left: 20px; }}
            </style>
        </head>
        <body>
            <div class='container'>
                <div class='header'>
                    <div class='header-item'><strong>From:</strong> {from_addr}</div>
                    <div class='header-item'><strong>To:</strong> {to_addr}</div>
                    <div class='header-item'><strong>CC:</strong> {cc_addr}</div>
                    <div class='header-item'><strong>Reply-To:</strong> {reply_to_addr}</div>
                    <div class='header-item'><strong>Subject:</strong> {subject}</div>
                </div>
                <div class='body-content'>
                    {body_inner_html}
                </div>
                <div class='attachments'>
                    <h4>Attachments:</h4>
                    {attachments_html}
                </div>
            </div>
        </body>
        </html>
        '''.format(
            from_addr=from_addr,
            to_addr=to_addr,
            cc_addr=cc_addr or 'N/A',
            reply_to_addr=reply_to_addr or 'N/A',
            subject=subject,
            body_inner_html=body_inner_html,
            attachments_html=attachments_html
        )

        # --- Write to temp file and open in browser ---
        try:
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as tmp:
                tmp.write(html_template)
                webbrowser.open('file://' + os.path.realpath(tmp.name))
            status_label.config(text='Preview opened in browser.', foreground='green')
        except Exception as e:
            messagebox.showerror('Preview Error', 'Could not open preview in browser.\n' + str(e), parent=email_root)

    def do_send():
        '''
        Validates inputs, constructs the email, and sends it via SMTP.
        '''
        is_locked, time_left = security_service.is_login_locked_out()
        if is_locked:
            messagebox.showwarning('Login Locked', f'Too many failed login attempts. Please wait {time_left} seconds.', parent=email_root)
            log_security_event(f'Send attempt blocked due to login lockout.', level='HIGH')
            return

        password = password_box.get()
        strength, _ = security_service.check_password_strength(password)
        if strength == 'Weak':
            if not messagebox.askyesno('Weak Password Warning', 'Your password appears to be weak. Are you sure you want to continue?', icon='warning', parent=email_root):
                return

        ok, vmsg = validate_inputs()
        if not ok:
            messagebox.showerror('Validation Error', vmsg, parent=email_root)
            log_security_event(f'Input validation failed: {vmsg}')
            return
        body_preview = get_body()
        if body_preview is None: return
        if not body_preview.strip() and not attachments:
            if not messagebox.askyesno('Confirm', 'Send email with empty body and no attachments?', parent=email_root):
                return

        send_button.config(state='disabled'); preview_btn.config(state='disabled')
        progress_bar.grid(); progress_bar.start()
        status_label.config(text='Sending...', foreground='blue')
        email_root.update_idletasks()

        from_addr = sender_box.get().strip()
        to_addrs_list = [p.strip() for p in receiver_box.get().strip().split(',') if p.strip()]

        try:
            msg = EmailMessage()
            subject_text = subject_box.get().strip() or 'The contents of {}'.format(file_name or 'your message')
            if pgp_encryption_var.get():
                subject_text = f'[Encrypted] {subject_text}'

            msg['Subject'] = subject_text
            cc = cc_box.get().strip(); bcc = bcc_box.get().strip(); reply_to = reply_to_box.get().strip()
            msg['From'] = from_addr
            msg['To'] = ', '.join(to_addrs_list)
            if reply_to: msg['Reply-To'] = reply_to
            cc_targets = [p.strip() for p in cc.split(',') if p.strip()] if cc else []
            if cc: msg['Cc'] = cc
            if copy_self_var.get() and from_addr not in cc_targets and from_addr not in to_addrs_list:
                cc_targets.append(from_addr)
                msg['Cc'] = ', '.join(cc_targets)

            signature = signature_box.get('1.0', 'end-1c').strip()
            plain_body = body_preview.rstrip()

            if pgp_encryption_var.get():
                enc_pass = encryption_password_entry.get()
                plain_body = security_service.encrypt_body(plain_body, enc_pass)
                log_security_event('Email body encrypted using simple symmetric cipher.', level='HIGH')
            elif signature:
                plain_body += '\n\n--\n' + signature

            msg.set_content(plain_body)

            for i, path in enumerate(attachments):
                try:
                    with open(path, 'rb') as fp:
                        data = fp.read()
                    msg.add_attachment(data, maintype='application', subtype='octet-stream', filename=os.path.basename(path))
                except Exception as e:
                    raise RuntimeError('Failed to attach file: ' + os.path.basename(path) + '\n' + str(e))

            rcpt = to_addrs_list + cc_targets
            if bcc: rcpt.extend([p.strip() for p in bcc.split(',') if p.strip()])
            context = ssl.create_default_context()
            server = smtp_server_box.get().strip()
            port = int(smtp_port_box.get().strip())
            with SMTP_SSL(server, port, context=context, timeout=30) as mail:
                mail.login(from_addr, password)
                mail.send_message(msg, from_addr=from_addr, to_addrs=rcpt)

            status_label.config(text='Email sent successfully.', foreground='green')
            log_security_event(f'Email sent successfully to: {msg["To"]}')
            messagebox.showinfo('Success', 'Email sent successfully.', parent=email_root)
            security_service.reset_lockout()
            save_prefs()
        except (SMTPException, RuntimeError, ValueError) as e:
            status_label.config(text='Failed to send.', foreground='red')
            log_security_event(f'Email send failed: {e}', level='HIGH')
            anomaly_detected, unique_sources = security_service.register_failed_login(from_addr)
            if anomaly_detected:
                log_security_event(f'Potential password spraying attack detected from {unique_sources} unique sources.', level='CRITICAL')
                messagebox.showwarning('Security Alert', 'Anomalous login activity detected. Login has been temporarily disabled.', parent=email_root)

            is_locked, time_left = security_service.is_login_locked_out()
            if is_locked:
                log_security_event(f'Login lockout initiated for {time_left} seconds.', level='HIGH')
                _start_lockout_timer(time_left, is_global=anomaly_detected)

            messagebox.showerror('Error', 'Failed to send email.\n\n' + str(e), parent=email_root)
        finally:
            password_box.delete(0, 'end')
            update_password_strength()
            send_button.config(state='normal'); preview_btn.config(state='normal')
            progress_bar.stop(); progress_bar.grid_remove()
            _update_login_buttons_state()

    def test_login():
        '''
        Tests the SMTP login credentials.
        '''
        is_locked, time_left = security_service.is_login_locked_out()
        if is_locked:
            messagebox.showwarning('Login Locked', f'Too many failed login attempts. Please wait {time_left} seconds.', parent=email_root)
            log_security_event(f'Test login attempt blocked due to login lockout.', level='HIGH')
            return

        from_addr = sender_box.get().strip(); pwd = password_box.get()
        if not validate_email(from_addr) or not pwd or not smtp_server_box.get() or not smtp_port_box.get():
            messagebox.showerror('Input Error', 'Please fill in your email, password, and server info in the Settings tab first.', parent=email_root)
            return

        test_btn.config(state='disabled'); progress_bar.grid(); progress_bar.start()
        status_label.config(text='Testing login...', foreground='blue'); email_root.update_idletasks()
        log_security_event(f'Attempting SMTP login for {from_addr}...')
        try:
            context = ssl.create_default_context()
            server = smtp_server_box.get().strip()
            port = int(smtp_port_box.get().strip())
            with SMTP_SSL(server, port, context=context, timeout=20) as mail:
                mail.login(from_addr, pwd)
            status_label.config(text='Login successful.', foreground='green')
            log_security_event('SMTP login successful.')
            messagebox.showinfo('Success', 'Login succeeded.', parent=email_root)
            security_service.reset_lockout()
        except SMTPException as e:
            status_label.config(text='Login failed.', foreground='red')
            log_security_event(f'SMTP login failed: {e}', level='HIGH')
            anomaly_detected, unique_sources = security_service.register_failed_login(from_addr)
            if anomaly_detected:
                log_security_event(f'Potential password spraying attack detected from {unique_sources} unique sources.', level='CRITICAL')
                messagebox.showwarning('Security Alert', 'Anomalous login activity detected. Login has been temporarily disabled.', parent=email_root)

            is_locked, time_left = security_service.is_login_locked_out()
            if is_locked:
                log_security_event(f'Login lockout initiated for {time_left} seconds.', level='HIGH')
                _start_lockout_timer(time_left, is_global=anomaly_detected)

            messagebox.showerror('Login Failed', 'Login failed.\n\n' + str(e), parent=email_root)
        except ValueError:
            status_label.config(text='Login failed.', foreground='red')
            log_security_event('SMTP login failed due to invalid port.', level='HIGH')
            messagebox.showerror('Input Error', 'The provided port is not a valid number.', parent=email_root)
        finally:
            test_btn.config(state='normal'); progress_bar.stop(); progress_bar.grid_remove()
            password_box.delete(0, 'end')
            update_password_strength()
            _update_login_buttons_state()

    def toggle_password():
        '''Toggles the visibility of the password field.'''
        password_box.config(show='' if show_pwd_var.get() else '*')

    def safe_exit():
        '''Saves preferences and handles auto-clearing of drafts before closing.'''
        log_security_event('Email client closing.')
        if lockout_timer_id: email_root.after_cancel(lockout_timer_id)
        if clear_drafts_on_exit_var.get():
            drafts.clear()
            if 'email_drafts' in owner.data:
                del owner.data['email_drafts']
            log_security_event('Automatically cleared drafts on exit.')
        save_prefs()
        email_root.destroy()

    # --- Wire Commands ---
    add_attach_btn.config(command=add_attachments)
    remove_attach_btn.config(command=remove_selected_attachment)
    clear_attach_btn.config(command=clear_attachments)
    show_pwd_btn.config(command=toggle_password)
    test_btn.config(command=test_login)
    send_button.config(command=do_send)
    preview_btn.config(command=show_preview)
    loc_button.config(command=lambda: file_mode('local'))
    custom_button.config(command=lambda: file_mode('none'))
    th_button.config(command=lambda: file_mode('this'))
    add_contact_btn.config(command=add_contact)
    remove_contact_btn.config(command=remove_contact)
    contact_to_btn.config(command=lambda: insert_contact(receiver_box))
    contact_cc_btn.config(command=lambda: insert_contact(cc_box))
    contact_bcc_btn.config(command=lambda: insert_contact(bcc_box))
    save_template_btn.config(command=save_template)
    load_template_btn.config(command=load_template)
    delete_template_btn.config(command=delete_template)
    load_draft_btn.config(command=load_draft)
    save_draft_btn.config(command=save_draft)
    delete_draft_btn.config(command=delete_draft)
    contact_search_entry.bind('<KeyRelease>', lambda e: _populate_contacts(contact_search_entry.get()))
    contact_search_clear_btn.config(command=lambda: (contact_search_entry.delete(0, 'end'), _populate_contacts()))
    template_search_entry.bind('<KeyRelease>', lambda e: _populate_templates(template_search_entry.get()))
    template_search_clear_btn.config(command=lambda: (template_search_entry.delete(0, 'end'), _populate_templates()))
    password_box.bind('<KeyRelease>', update_password_strength)

    # --- Final Setup ---
    log_security_event('Email client initialized.')
    restore_prefs()
    file_mode('this')
    update_attach_status()
    _update_login_buttons_state()
    email_root.protocol('WM_DELETE_WINDOW', safe_exit)
    sender_box.focus_set()
    messagebox.showinfo('Tip', 'If you use 2-step verification, create an app password to send mail.', parent=email_root)
