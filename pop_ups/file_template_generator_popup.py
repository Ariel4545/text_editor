# file_template_generator_popup.py
from __future__ import annotations

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
from collections import Counter  # might be handy for future enhancements


def open_document_template_generator(app, event=None):
    '''
    Document Template Generator popup.

    Features:
    - Output format: PDF | WORD | JINJA
    - Subject presets: resume | personal info | computer stats | letter
    - Optional: Use docxtpl with a provided .docx template file
    - Edit placeholders before generating (dynamic context form)
    - Actions: Generate, Open Folder, Open File, Copy Path, Close
    '''
    text_widget = app.EgonTE

    # ---------------- Validation / import helpers ----------------
    def require_python_docx():
        '''
        Ensure the correct 'python-docx' package is installed (not the legacy 'docx').
        Returns: (Document, Pt)
        '''
        try:
            import docx  # provided by python-docx
            from docx import Document
            from docx.shared import Pt
        except ImportError as e:
            raise RuntimeError(
                "Word generation requires the 'python-docx' package.\n"
                'Install it using:\n'
                '  pip install python-docx'
            ) from e

        looks_legacy = False
        if not hasattr(docx, 'Document'):
            looks_legacy = True
        else:
            try:
                from docx import shared  # noqa: F401
                _ = Pt  # ensure available
            except Exception:
                looks_legacy = True

        if looks_legacy:
            raise RuntimeError(
                "It looks like the legacy 'docx' package is installed instead of 'python-docx'.\n"
                'Please run:\n'
                '  pip uninstall -y docx\n'
                '  pip install python-docx'
            )
        return Document, Pt

    def require_fpdf():
        try:
            from fpdf import FPDF
            return FPDF
        except ImportError as e:
            raise RuntimeError(
                "PDF generation requires the 'fpdf' package.\n"
                'Install it using:\n'
                '  pip install fpdf'
            ) from e

    def require_jinja2_template():
        try:
            from jinja2 import Template
            return Template
        except ImportError as e:
            raise RuntimeError(
                "Jinja rendering requires the 'jinja2' package.\n"
                'Install it using:\n'
                '  pip install jinja2'
            ) from e

    def require_docxtpl():
        try:
            from docxtpl import DocxTemplate
            return DocxTemplate
        except ImportError as e:
            raise RuntimeError(
                "Using a .docx template requires the 'docxtpl' package.\n"
                'Install it using:\n'
                '  pip install docxtpl'
            ) from e

    # ---------------- Content / generation helpers ----------------
    def get_default_context_for_subject(subject_key: str) -> tuple[str, dict]:
        if subject_key == 'resume':
            return 'Resume', {
                'full_name': '<FULL_NAME>',
                'title': '<JOB_TITLE>',
                'email': '<EMAIL>',
                'phone': '<PHONE>',
                'summary': '<ONE_SENTENCE_SUMMARY>',
                'skills': '<SKILL_1>, <SKILL_2>, <SKILL_3>',
            }
        if subject_key == 'personal info':
            return 'Personal Information', {
                'full_name': '<FULL_NAME>',
                'address': '<ADDRESS_LINE>',
                'city': '<CITY>',
                'country': '<COUNTRY>',
                'email': '<EMAIL>',
                'phone': '<PHONE>',
                'dob': '<YYYY-MM-DD>',
            }
        if subject_key == 'computer stats':
            return 'Computer Stats', {
                'os': '<OS_NAME_VERSION>',
                'cpu': '<CPU_MODEL>',
                'ram': '<RAM_GB> GB',
                'storage': '<STORAGE_TOTAL_GB> GB',
                'gpu': '<GPU_MODEL>',
                'python': '<PYTHON_VERSION>',
            }
        if subject_key == 'letter':
            return 'Letter', {
                'date': '<YYYY-MM-DD>',
                'recipient_name': '<RECIPIENT_NAME>',
                'recipient_company': '<RECIPIENT_COMPANY>',
                'greeting': 'Dear <RECIPIENT_NAME>,',
                'body': '<LETTER_BODY>',
                'closing': 'Sincerely,',
                'sender_name': '<SENDER_NAME>',
            }
        return subject_key.title(), {'note': '<PLACEHOLDER>'}

    def ensure_output_dir() -> Path:
        out_path = Path('outputs')
        out_path.mkdir(parents=True, exist_ok=True)
        return out_path

    def build_output_filename(prefix: str, ext: str) -> Path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_prefix = str(prefix).replace(' ', '_').lower()
        return ensure_output_dir() / f'{safe_prefix}_{timestamp}.{ext}'

    def generate_pdf_document(title: str, context: dict) -> str:
        FPDF = require_fpdf()
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, txt=title, ln=True)
        pdf.ln(4)
        pdf.set_font('Arial', size=12)
        for key, value in context.items():
            pdf.multi_cell(0, 8, f'{key.replace("_", " ").title()}: {value}')
        path = build_output_filename(title, 'pdf')
        pdf.output(str(path))
        return str(path)

    def generate_word_document(title: str, context: dict) -> str:
        Document, Pt = require_python_docx()
        doc = Document()
        heading = doc.add_heading(title, level=1)
        for run in heading.runs:
            try:
                run.font.size = Pt(18)
            except Exception:
                pass
        for key, value in context.items():
            p = doc.add_paragraph()
            p.add_run(f'{key.replace("_", " ").title()}: ').bold = True
            p.add_run(str(value))
        path = build_output_filename(title, 'docx')
        doc.save(str(path))
        return str(path)

    def generate_docx_from_jinja(title: str, context: dict) -> str:
        Template = require_jinja2_template()
        Document, _Pt = require_python_docx()

        template_text = (
            '{{ title }}\n'
            '{% for _ in range(title|length) %}={% endfor %}\n\n'
            "{% for k, v in context.items() %}{{ k.replace('_',' ') | title }}: {{ v }}\n{% endfor %}"
        )
        rendered = Template(template_text).render(title=title, context=context)

        doc = Document()
        lines = rendered.splitlines()
        if lines:
            doc.add_heading(lines[0], level=1)
            body = '\n'.join(lines[2:]) if len(lines) > 2 else ''
        else:
            body = rendered
        for line in body.split('\n'):
            doc.add_paragraph(line)

        path = build_output_filename(title, 'docx')
        doc.save(str(path))
        return str(path)

    def render_docxtpl_with_template(title: str, context: dict, template_path: str) -> str:
        DocxTemplate = require_docxtpl()
        template_file = Path(template_path)
        if not template_file.exists():
            raise FileNotFoundError(f'Template file not found:\n{template_file}')
        doc = DocxTemplate(str(template_file))
        render_context = {'title': title, **context}
        doc.render(render_context)
        path = build_output_filename(title, 'docx')
        doc.save(str(path))
        return str(path)

    def generate_document(
        output_format: str,
        subject_key: str,
        use_docxtpl: bool,
        template_path: str,
        context_override: dict | None = None,
    ) -> str:
        allowed_formats = {'PDF', 'WORD', 'JINJA'}
        allowed_subjects = {'resume', 'personal info', 'computer stats', 'letter'}
        if output_format not in allowed_formats:
            raise ValueError(f'Output format must be one of {sorted(allowed_formats)}')
        if subject_key not in allowed_subjects:
            raise ValueError(f'Subject must be one of {sorted(allowed_subjects)}')

        title, context = get_default_context_for_subject(subject_key)
        if context_override:
            context = {**context, **context_override}

        if use_docxtpl:
            if not template_path:
                raise ValueError("Please select a .docx template file or turn off 'Use docxtpl'.")
            return render_docxtpl_with_template(title, context, template_path)

        if output_format == 'PDF':
            return generate_pdf_document(title, context)
        if output_format == 'WORD':
            return generate_word_document(title, context)
        return generate_docx_from_jinja(title, context)

    # ---------------- UI ----------------
    root = app.make_pop_ups_window(function=app.file_template_generator, title='Document Template Generator')

    # State variables
    output_format_var = tk.StringVar(value='WORD')
    subject_choice_var = tk.StringVar(value='resume')
    use_docxtpl_var = tk.BooleanVar(value=False)
    template_path_var = tk.StringVar(value='')
    generated_path_var = tk.StringVar(value='')
    status_text_var = tk.StringVar(value='Select options and click Generate')

    # Choices
    output_format_options = ('PDF', 'WORD', 'JINJA')
    subject_options = ('resume', 'personal info', 'computer stats', 'letter')

    # Dynamic context fields state
    context_field_vars: dict[str, tk.StringVar] = {}

    # Layout frames
    options_frame = ttk.Frame(root)
    options_frame.grid(row=0, column=0, sticky='nsew', padx=8, pady=8)
    context_frame = ttk.Frame(root)
    context_frame.grid(row=1, column=0, sticky='nsew', padx=8, pady=(0, 8))
    actions_frame = ttk.Frame(root)
    actions_frame.grid(row=2, column=0, sticky='ew', padx=8, pady=(0, 8))
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=1)

    # Options: format and subject
    ttk.Label(options_frame, text='Output format:').grid(row=0, column=0, sticky='w', padx=(0, 6))
    format_combo = ttk.Combobox(options_frame, textvariable=output_format_var, values=output_format_options, state='readonly', width=10)
    format_combo.grid(row=0, column=1, sticky='w', padx=(0, 12))

    ttk.Label(options_frame, text='Subject:').grid(row=0, column=2, sticky='w', padx=(0, 6))
    subject_combo = ttk.Combobox(options_frame, textvariable=subject_choice_var, values=subject_options, state='readonly', width=18)
    subject_combo.grid(row=0, column=3, sticky='w', padx=(0, 12))

    # docxtpl toggle + template path
    docxtpl_check = ttk.Checkbutton(options_frame, text='Use docxtpl (.docx template)', variable=use_docxtpl_var)
    docxtpl_check.grid(row=1, column=0, columnspan=2, sticky='w', pady=(6, 0))

    ttk.Label(options_frame, text='Template path (.docx):').grid(row=1, column=2, sticky='e', padx=(12, 6), pady=(6, 0))
    template_entry = ttk.Entry(options_frame, textvariable=template_path_var, width=36)
    template_entry.grid(row=1, column=3, sticky='we', pady=(6, 0))
    browse_template_btn = ttk.Button(options_frame, text='Browse...')
    browse_template_btn.grid(row=1, column=4, sticky='w', padx=(6, 0), pady=(6, 0))
    options_frame.grid_columnconfigure(3, weight=1)

    # Context header and dynamic content fields
    def rebuild_context_fields(*_):
        # Clear existing widgets
        for w in context_frame.grid_slaves():
            w.destroy()
        context_field_vars.clear()

        _title, default_ctx = get_default_context_for_subject(subject_choice_var.get())
        ttk.Label(context_frame, text='Placeholders (editable):', font=('Segoe UI', 9, 'bold')).grid(
            row=0, column=0, columnspan=2, sticky='w', padx=2, pady=(0, 4)
        )

        row_idx = 1
        for key, default_value in default_ctx.items():
            ttk.Label(context_frame, text=key.replace('_', ' ').title() + ':').grid(row=row_idx, column=0, sticky='e', padx=4, pady=2)
            sv = tk.StringVar(value=default_value)
            context_field_vars[key] = sv
            ttk.Entry(context_frame, textvariable=sv, width=40).grid(row=row_idx, column=1, sticky='we', padx=4, pady=2)
            row_idx += 1

        context_frame.grid_columnconfigure(1, weight=1)

    rebuild_context_fields()
    subject_choice_var.trace_add('write', lambda *_: rebuild_context_fields())

    # Actions: Generate and result row
    generate_button = ttk.Button(actions_frame, text='Generate')

    ttk.Label(actions_frame, text='Result path:').grid(row=0, column=1, sticky='e', padx=(12, 6))
    result_entry = ttk.Entry(actions_frame, textvariable=generated_path_var, state='readonly')
    result_entry.grid(row=0, column=2, sticky='ew')
    copy_path_button = ttk.Button(actions_frame, text='Copy Path', state='disabled')
    copy_path_button.grid(row=0, column=3, sticky='w', padx=(6, 0))
    actions_frame.grid_columnconfigure(2, weight=1)

    open_folder_button = ttk.Button(actions_frame, text='Open Folder', state='disabled')
    open_file_button = ttk.Button(actions_frame, text='Open File', state='disabled')
    close_button = ttk.Button(actions_frame, text='Close')

    generate_button.grid(row=0, column=0, sticky='w', padx=(0, 8))
    open_folder_button.grid(row=1, column=0, sticky='w', pady=(6, 0))
    open_file_button.grid(row=1, column=1, sticky='w', padx=(8, 0), pady=(6, 0))
    close_button.grid(row=1, column=3, sticky='e', pady=(6, 0))

    # Status label
    status_label = ttk.Label(root, textvariable=status_text_var, anchor='w')
    status_label.grid(row=3, column=0, sticky='ew', padx=8, pady=(0, 8))

    # ---------------- Callbacks ----------------
    def on_browse_template():
        path = filedialog.askopenfilename(
            title='Select .docx template',
            filetypes=[('Word Template', '*.docx'), ('All Files', '*.*')],
        )
        if path:
            template_path_var.set(path)

    def on_generate(event=None):
        fmt = output_format_var.get()
        subj = subject_choice_var.get()
        use_tpl = bool(use_docxtpl_var.get())
        tpl_path = template_path_var.get().strip()
        try:
            # Context overrides from UI
            overrides = {k: sv.get() for k, sv in context_field_vars.items()}
            path = generate_document(fmt, subj, use_tpl, tpl_path, context_override=overrides)
            generated_path_var.set(str(path))
            status_text_var.set('Generated successfully.')
            open_folder_button.config(state=tk.NORMAL)
            open_file_button.config(state=tk.NORMAL)
            copy_path_button.config(state=tk.NORMAL)
            result_entry.configure(state='normal')
            result_entry.select_range(0, tk.END)
            result_entry.configure(state='readonly')
        except Exception as e:
            status_text_var.set('Generation failed.')
            messagebox.showerror('Generation error', str(e))

    def on_open_folder():
        p = generated_path_var.get()
        if not p:
            return
        folder = str(Path(p).resolve().parent)
        try:
            if os.name == 'nt':
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', folder])
            else:
                subprocess.Popen(['xdg-open', folder])
        except Exception as e:
            messagebox.showwarning('Open Folder', f'Could not open folder:\n{e}')

    def on_open_file():
        p = generated_path_var.get()
        if not p:
            return
        file_path = str(Path(p).resolve())
        try:
            if os.name == 'nt':
                os.startfile(file_path)  # type: ignore[attr-defined]
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', file_path])
            else:
                subprocess.Popen(['xdg-open', file_path])
        except Exception as e:
            messagebox.showwarning('Open File', f'Could not open file:\n{e}')

    def on_copy_path():
        p = generated_path_var.get()
        if not p:
            return
        try:
            root.clipboard_clear()
            root.clipboard_append(p)
            status_text_var.set('Path copied to clipboard.')
        except Exception:
            pass

    def on_close():
        try:
            root.destroy()
        except Exception:
            pass

    # Wire callbacks
    browse_template_btn.configure(command=on_browse_template)
    generate_button.configure(command=on_generate)
    open_folder_button.configure(command=on_open_folder)
    open_file_button.configure(command=on_open_file)
    copy_path_button.configure(command=on_copy_path)
    close_button.configure(command=on_close)

    # Keyboard shortcuts
    root.bind('<Return>', on_generate)
    root.bind('<Escape>', lambda *_: on_close())

    # Seed template path from selection if relevant (optional nicety)
    try:
        if text_widget.tag_ranges('sel'):
            selection = text_widget.get('sel.first', 'sel.last')
            if selection and selection.strip().lower().endswith('.docx'):
                template_path_var.set(selection.strip())
    except Exception:
        pass

    # Focus
    format_combo.focus_set()
