import tkinter as tk
from tkinter import (
    Label, Entry, Button, Checkbutton, Listbox, Scrollbar, messagebox, filedialog
)
from email.message import EmailMessage
from smtplib import SMTP_SSL
import ssl


def open_email(owner):
    """
    Open the enhanced Send Email pop-up.

    owner is expected to be your main window instance that provides:
      - make_pop_ups_window(callable)
      - make_rich_textbox(parent, place=[row, col]) -> (frame, text_widget, scroll)
      - Optional: a dict-like `data` for persisting last email fields
      - Optional: access to owner.EgonTE and owner.file_name for "This file" mode
    """
    # Simple availability gate (compatible with your existing pattern)
    email_tool = True
    if not email_tool:
        messagebox.showerror('EgonTE', 'Email tool is not available on this environment.')
        return

    file_type = 'external'
    custom_text_active = False
    custom_box = None
    email_c_frame = None
    file_name = ''
    attachments = []

    messagebox.showinfo('EgonTE', 'Tip: If you use 2‑step verification, create an app password to send mail.')
    email_root = owner.make_pop_ups_window(open_email)

    # UI (kept close to original style with light polish)
    req = Label(email_root, text='Requirements', font='arial 12 underline')
    sender_title = Label(email_root, text='Your Email:')
    password_title = Label(email_root, text='Your Password:')
    receiver_title = Label(email_root, text='Receiver Email:')
    sender_box = Entry(email_root, width=25)
    password_box = Entry(email_root, width=25, show='*')
    receiver_box = Entry(email_root, width=25)

    content_title = Label(email_root, text='Content:', font='arial 12 underline')
    subject_title = Label(email_root, text='Subject:')
    subject_box = Entry(email_root, width=25)

    cc_title = Label(email_root, text='CC:')
    cc_box = Entry(email_root, width=25)
    bcc_title = Label(email_root, text='BCC:')
    bcc_box = Entry(email_root, width=25)

    files_title = Label(email_root, text='Body:')
    stats_label = Label(email_root, text='', fg='grey')

    loc_button = Button(email_root, text='Local file', borderwidth=1)
    custom_button = Button(email_root, text='Custom', borderwidth=1)
    th_button = Button(email_root, text='This file', borderwidth=1)

    attach_title = Label(email_root, text='Attachments:', font='arial 10 underline')
    attach_list = Listbox(email_root, height=3, width=40, exportselection=False)
    attach_scroll = Scrollbar(email_root, orient='vertical', command=attach_list.yview)
    attach_list.config(yscrollcommand=attach_scroll.set)
    add_attach_btn = Button(email_root, text='Add...', borderwidth=1)
    remove_attach_btn = Button(email_root, text='Remove selected', borderwidth=1)
    clear_attach_btn = Button(email_root, text='Clear', borderwidth=1)
    attach_status = Label(email_root, text='0 attachment(s)', fg='grey')

    copy_self_var = tk.BooleanVar(value=False)
    copy_self_chk = Checkbutton(email_root, text='Send me a copy', variable=copy_self_var)
    remember_var = tk.BooleanVar(value=True)
    remember_chk = Checkbutton(email_root, text='Remember fields', variable=remember_var)

    send_button = Button(email_root, text='Send', font='arial 10 bold')
    test_btn = Button(email_root, text='Test login', borderwidth=1)

    show_pwd_var = tk.BooleanVar(value=False)
    show_pwd_btn = Checkbutton(email_root, text='Show', variable=show_pwd_var)
    pwd_hint = Label(email_root, text='Use an app password if 2FA is enabled.', fg='grey')
    status_label = Label(email_root, text='', fg='grey')

    # Layout
    req.grid(row=0, column=1, pady=2)

    sender_title.grid(row=1, column=0)
    password_title.grid(row=1, column=1)
    receiver_title.grid(row=1, column=2)

    sender_box.grid(row=2, column=0, padx=5)
    password_box.grid(row=2, column=1, sticky='w')
    show_pwd_btn.grid(row=2, column=1, sticky='e', padx=5)
    receiver_box.grid(row=2, column=2, padx=5)

    pwd_hint.grid(row=3, column=1, pady=(0, 2))

    content_title.grid(row=4, column=1, pady=2)

    subject_title.grid(row=5, column=1)
    subject_box.grid(row=6, column=1, padx=5)

    cc_title.grid(row=5, column=0)
    cc_box.grid(row=6, column=0, padx=5)

    bcc_title.grid(row=5, column=2)
    bcc_box.grid(row=6, column=2, padx=5)

    files_title.grid(row=7, column=1)
    stats_label.grid(row=7, column=2, sticky='w')
    loc_button.grid(row=8, column=0, pady=(0, 2))
    custom_button.grid(row=8, column=1, pady=(0, 2))
    th_button.grid(row=8, column=2, pady=(0, 4))

    attach_title.grid(row=9, column=1, pady=(6, 0))
    attach_list.grid(row=10, column=0, columnspan=2, sticky='ew', padx=(5, 0))
    attach_scroll.grid(row=10, column=2, sticky='nsw', padx=(0, 5))
    add_attach_btn.grid(row=11, column=0, pady=(2, 0))
    remove_attach_btn.grid(row=11, column=1, pady=(2, 0))
    clear_attach_btn.grid(row=11, column=2, pady=(2, 0))
    attach_status.grid(row=12, column=1, pady=(0, 4))

    copy_self_chk.grid(row=13, column=0)
    remember_chk.grid(row=13, column=2)

    test_btn.grid(row=14, column=0, pady=(2, 0))
    send_button.grid(row=14, column=1, pady=(2, 0))
    status_label.grid(row=15, column=1, pady=(0, 2))

    # Helpers
    def validate_email(addr: str) -> bool:
        addr = addr.strip()
        return bool(addr and '@' in addr and '.' in addr)

    def update_attach_status():
        count = attach_list.size()
        attach_status.config(text=f'{count} attachment(s)')

    def update_body_stats():
        try:
            text = ''
            if file_type == 'none' and custom_box:
                text = custom_box.get('1.0', 'end-1c')
            elif file_type == 'this':
                text = owner.EgonTE.get('1.0', 'end-1c')
            stats_label.config(text=f'{len(text)} characters')
        except Exception:
            stats_label.config(text='')

    def file_mode(mode: str):
        nonlocal file_type, custom_box, email_c_frame, custom_text_active
        file_type = mode
        for button in email_button_dict.values():
            button.configure(bg='SystemButtonFace')
        email_button_dict[mode].configure(bg='light grey')
        if mode == 'none':
            email_c_frame, custom_box, _email_scroll = owner.make_rich_textbox(email_root, place=[16, 0])
            custom_text_active = True
            try:
                custom_box.bind('<KeyRelease>', lambda e: update_body_stats())
            except Exception:
                pass
            update_body_stats()
        else:
            if custom_text_active and email_c_frame is not None:
                email_c_frame.destroy()
                custom_text_active = False
            update_body_stats()

    def get_body():
        nonlocal file_name
        if file_type == 'local':
            try:
                local_name = filedialog.askopenfilename(parent=email_root)
                if local_name:
                    file_name = local_name
                    with open(local_name, 'r', encoding='utf-8', errors='replace') as fp:
                        return fp.read()
                return None
            except Exception as e:
                messagebox.showerror('EgonTE', f'Failed to read the selected file.\n{e}')
                return None
        elif file_type == 'this':
            file_name = getattr(owner, 'file_name', '') or 'current document'
            try:
                return owner.EgonTE.get('1.0', 'end-1c')
            except Exception:
                return ''
        else:
            file_name = f'A message from {sender_box.get().strip() or "EgonTE user"}'
            if custom_box:
                try:
                    return custom_box.get('1.0', 'end-1c')
                except Exception:
                    return ''
        return ''

    def validate_inputs():
        from_addr = sender_box.get().strip()
        to_addr = receiver_box.get().strip()
        cc = cc_box.get().strip()
        bcc = bcc_box.get().strip()
        pwd = password_box.get()

        if not validate_email(from_addr):
            return False, 'Please enter a valid sender email address.'
        if not validate_email(to_addr):
            return False, 'Please enter a valid receiver email address.'
        for field, label in ((cc, 'CC'), (bcc, 'BCC')):
            if field:
                for part in [p.strip() for p in field.split(',') if p.strip()]:
                    if not validate_email(part):
                        return False, f'Invalid address in {label}: {part}'
        if not pwd:
            return False, 'Please enter your email password or app password.'
        return True, ''

    def add_attachments():
        nonlocal attachments
        try:
            files = filedialog.askopenfilenames(parent=email_root)
            if not files:
                return
            added = 0
            for f in files:
                if f and f not in attachments:
                    attachments.append(f)
                    attach_list.insert('end', f)
                    added += 1
            update_attach_status()
            if added == 0:
                status_label.config(text='No new attachments added.', fg='grey')
        except Exception as e:
            messagebox.showerror('EgonTE', f'Failed adding attachments.\n{e}')

    def remove_selected_attachment():
        nonlocal attachments
        sel = attach_list.curselection()
        if not sel:
            return
        for index in reversed(sel):
            try:
                path = attach_list.get(index)
                attach_list.delete(index)
                if path in attachments:
                    attachments.remove(path)
            except Exception:
                pass
        update_attach_status()

    def clear_attachments():
        nonlocal attachments
        attachments = []
        attach_list.delete(0, 'end')
        update_attach_status()

    def save_prefs():
        try:
            if hasattr(owner, 'data') and isinstance(owner.data, dict) and remember_var.get():
                owner.data['last_email_from'] = sender_box.get().strip()
                owner.data['last_email_to'] = receiver_box.get().strip()
                owner.data['last_email_subject'] = subject_box.get().strip()
                owner.data['last_email_cc'] = cc_box.get().strip()
                owner.data['last_email_bcc'] = bcc_box.get().strip()
        except Exception:
            pass

    def restore_prefs():
        try:
            if hasattr(owner, 'data') and isinstance(owner.data, dict):
                if owner.data.get('last_email_from'):
                    sender_box.insert(0, owner.data['last_email_from'])
                if owner.data.get('last_email_to'):
                    receiver_box.insert(0, owner.data['last_email_to'])
                if owner.data.get('last_email_subject'):
                    subject_box.insert(0, owner.data['last_email_subject'])
                if owner.data.get('last_email_cc'):
                    cc_box.insert(0, owner.data['last_email_cc'])
                if owner.data.get('last_email_bcc'):
                    bcc_box.insert(0, owner.data['last_email_bcc'])
        except Exception:
            pass

    def do_send():
        ok, vmsg = validate_inputs()
        if not ok:
            messagebox.showerror('EgonTE', vmsg)
            return

        body_preview = get_body()
        if body_preview is None:
            status_label.config(text='Cancelled file selection.', fg='grey')
            return
        if not body_preview.strip():
            if not messagebox.askyesno('EgonTE', 'Body is empty. Send anyway?'):
                return

        send_button.config(state='disabled')
        status_label.config(text='Sending...', fg='blue')
        email_root.update_idletasks()

        try:
            msg = EmailMessage()
            subject = subject_box.get().strip()
            if subject:
                msg['Subject'] = subject
            else:
                try:
                    msg['Subject'] = f'The contents of {file_name or "your message"}'
                except Exception:
                    msg['Subject'] = 'Your message'

            from_addr = sender_box.get().strip()
            to_addr = receiver_box.get().strip()
            cc = cc_box.get().strip()
            bcc = bcc_box.get().strip()

            msg['From'] = from_addr
            msg['To'] = to_addr
            cc_targets = []
            if cc:
                msg['Cc'] = cc
                cc_targets.extend([p.strip() for p in cc.split(',') if p.strip()])

            if copy_self_var.get() and from_addr not in cc_targets and from_addr != to_addr:
                cc_targets.append(from_addr)
                if 'Cc' in msg:
                    msg.replace_header('Cc', msg['Cc'] + ', ' + from_addr)
                else:
                    msg['Cc'] = from_addr

            msg.set_content(body_preview or '')

            total_bytes = 0
            for path in attachments:
                try:
                    with open(path, 'rb') as fp:
                        data = fp.read()
                    total_bytes += len(data)
                    if total_bytes > 20 * 1024 * 1024:
                        messagebox.showerror('EgonTE', 'Attachments are too large (over ~20 MB). Please remove some files.')
                        send_button.config(state='normal')
                        status_label.config(text='Too large attachments.', fg='red')
                        return
                    name = path.split('/')[-1].split('\\')[-1]
                    msg.add_attachment(data, maintype='application', subtype='octet-stream', filename=name)
                except Exception as e:
                    messagebox.showerror('EgonTE', f'Failed to attach file:\n{path}\n{e}')
                    send_button.config(state='normal')
                    status_label.config(text='Failed attaching file.', fg='red')
                    return

            rcpt = [to_addr]
            rcpt.extend([p.strip() for p in cc_targets if p.strip()])
            if bcc:
                rcpt.extend([p.strip() for p in bcc.split(',') if p.strip()])

            context = ssl.create_default_context()
            with SMTP_SSL('smtp.gmail.com', 465, context=context, timeout=20) as mail:
                mail.login(from_addr, password=password_box.get())
                mail.send_message(msg, from_addr=from_addr, to_addrs=rcpt)

            status_label.config(text='Email sent.', fg='green')
            messagebox.showinfo('EgonTE', 'Email sent successfully.')
            password_box.delete(0, 'end')
            save_prefs()

        except Exception as e:
            status_label.config(text='Failed.', fg='red')
            messagebox.showerror('EgonTE', f'Failed to send email.\n{e}')
        finally:
            send_button.config(state='normal')

    def test_login():
        ok, vmsg = validate_inputs()
        if not ok:
            messagebox.showerror('EgonTE', vmsg)
            return
        test_btn.config(state='disabled')
        status_label.config(text='Testing login...', fg='blue')
        email_root.update_idletasks()
        try:
            context = ssl.create_default_context()
            with SMTP_SSL('smtp.gmail.com', 465, context=context, timeout=20) as mail:
                mail.login(sender_box.get().strip(), password=password_box.get())
            status_label.config(text='Login OK.', fg='green')
            messagebox.showinfo('EgonTE', 'Login succeeded.')
        except Exception as e:
            status_label.config(text='Login failed.', fg='red')
            messagebox.showerror('EgonTE', f'Login failed.\n{e}')
        finally:
            test_btn.config(state='normal')

    def toggle_password():
        if show_pwd_var.get():
            password_box.config(show='')
        else:
            password_box.config(show='*')

    # Wire commands
    add_attach_btn.config(command=add_attachments)
    remove_attach_btn.config(command=remove_selected_attachment)
    clear_attach_btn.config(command=clear_attachments)
    show_pwd_btn.config(command=toggle_password)
    test_btn.config(command=test_login)
    send_button.config(command=do_send)

    email_button_dict = {'this': th_button, 'none': custom_button, 'local': loc_button}
    loc_button.config(command=lambda: file_mode('local'))
    custom_button.config(command=lambda: file_mode('none'))
    th_button.config(command=lambda: file_mode('this'))

    # Restore and defaults
    restore_prefs()
    file_mode('this')
    update_attach_status()

    # Shortcuts and focus
    email_root.bind('<Return>', lambda e: do_send())
    email_root.bind('<Control-Return>', lambda e: do_send())
    email_root.bind('<Escape>', lambda e: email_root.destroy())
    sender_box.focus_set()
