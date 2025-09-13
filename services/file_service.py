from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any, Sequence
import os
import pathlib
import sys
from tkinter import END, filedialog, messagebox
from datetime import datetime

# optional HTML prettifier
try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:
    BeautifulSoup = None  # type: ignore

# Prefer canonical constants location first
try:
    from dependencies.large_variables import text_extensions  # type: ignore
except Exception:
    try:
        from large_variables import text_extensions  # type: ignore
    except Exception:
        text_extensions = (('Text Files', '*.txt'), ('HTML Files', '*.html'), ('Python Files', '*.py'))

# Time + unsaved changes prompt (try canonical path first)
try:
    from dependencies.universal_functions import get_time, check_file_changes  # type: ignore
except Exception:
    try:
        from universal_functions import get_time, check_file_changes  # type: ignore
    except Exception:
        from datetime import datetime as _dt

        def get_time() -> str:
            return _dt.now().strftime('%Y-%m-%d %H:%M:%S')

        def check_file_changes(file_name: str, content: str) -> bool:
            return True


@dataclass
class FileService:
    '''
    File operations service for the main app.
    - Reads/writes are utf-8 first, then fallback to legacy where possible.
    - Saves use buffer 'end-1c' to avoid saving tkinter's trailing newline.
    - Preserves existing UI behavior (file bar text, record_list).
    '''
    app: Any  # main Window-like object

    # ---------- helpers ----------
    def title_text(self, suffix: str = '') -> str:
        return f'{getattr(self.app, "title_struct", "")}{suffix}'

    def editor_get_all(self) -> str:
        '''
        Full buffer as used by legacy comparisons (keeps tkinter trailing newline).
        '''
        try:
            return self.app.EgonTE.get('1.0', 'end')
        except Exception:
            return ''

    def editor_get_all_for_write(self) -> str:
        '''
        Buffer without trailing newline, to avoid writing an extra line to files.
        '''
        try:
            return self.app.EgonTE.get('1.0', 'end-1c')
        except Exception:
            return ''

    def editor_set_all(self, text_value: str) -> None:
        try:
            self.app.EgonTE.delete('1.0', END)
            self.app.EgonTE.insert('1.0', text_value)
        except Exception:
            pass

    def append_record(self, message_text: str) -> None:
        try:
            self.app.record_list.append(message_text)
        except Exception:
            pass

    def update_file_bar(self, text_value: str) -> None:
        try:
            self.app.file_bar.config(text=text_value)
        except Exception:
            pass

    def show_error(self, message_text: str, suffix: str = 'error') -> None:
        try:
            messagebox.showerror(self.title_text(suffix), message_text)
        except Exception:
            pass

    def show_warning(self, message_text: str, suffix: str = ' warning') -> None:
        try:
            messagebox.showwarning(self.title_text(suffix), message_text)
        except Exception:
            pass

    # ---------- dialogs ----------
    def get_file(self, mode: str = 'open', message: str = '') -> str:
        '''
        Centralized file dialog helper.
        '''
        mode_lower = (mode or '').lower()
        if mode_lower == 'open':
            return filedialog.askopenfilename(
                title=f'{mode_lower}{message} file',
                filetypes=text_extensions
            ) or ''
        if mode_lower in ('new', 'save', 'saveas'):
            return filedialog.asksaveasfilename(
                defaultextension='.*',
                initialdir='C:/EgonTE',
                title='Save File',
                filetypes=text_extensions
            ) or ''
        # default -> open
        return filedialog.askopenfilename(
            title=f'open{message} file',
            filetypes=text_extensions
        ) or ''

    # ---------- commands ----------
    def new_file(self, event: Optional[object] = None) -> None:
        '''
        Create a blank workspace (no file path).
        '''
        if check_file_changes(getattr(self.app, 'file_name', ''), self.editor_get_all()):
            try:
                self.app.file_name = ''
                self.app.open_status_name = ''
            except Exception:
                pass
            self.editor_set_all('')
            self.update_file_bar('New file')
            self.append_record(f'> [{get_time()}] - New blank file opened')

    def open_file(self, event: Optional[object] = None) -> None:
        '''
        Open a file; prettify HTML and prepare Python console if needed.
        '''
        prior_content = self.editor_get_all()

        # Resolve target path
        if event == 'initial':
            try:
                text_name = self.app.data.get('open_last_file', '') or ''
            except Exception:
                text_name = ''
        else:
            text_name = self.get_file('open')

        if not check_file_changes(getattr(self.app, 'file_name', ''), self.editor_get_all()):
            return

        if not text_name:
            self.show_error('File not found / selected')
            return

        # Try utf-8 first, fallback to permissive open
        try:
            with open(text_name, 'r', encoding='utf-8') as file_pointer:
                file_content = file_pointer.read()
        except UnicodeDecodeError:
            try:
                with open(text_name, 'r', errors='replace') as file_pointer:
                    file_content = file_pointer.read()
            except Exception:
                self.show_error('File contains not supported characters')
                self.editor_set_all(prior_content)
                return
        except Exception:
            self.show_error('Could not open file')
            self.editor_set_all(prior_content)
            return

        # Disable legacy python console if switching types
        try:
            if getattr(self.app, 'python_file', False):
                self.app.python_file = ''
                # destroy output frame if it exists (support both historic names)
                try:
                    if hasattr(self.app, 'output_frame') and self.app.output_frame:
                        self.app.output_frame.destroy()
                except Exception:
                    pass
                try:
                    if hasattr(self.app, 'outputFrame') and self.app.outputFrame:  # type: ignore[attr-defined]
                        self.app.outputFrame.destroy()  # type: ignore[attr-defined]
                except Exception:
                    pass
                try:
                    self.app.app_menu.delete('Run')
                    self.app.app_menu.delete('Clear console')
                    self.app.options_menu.delete('Auto clear console')
                    self.app.options_menu.delete('Save by running')
                    if self.app.dev_mode.get():
                        self.app.options_menu.delete(15)
                    else:
                        self.app.options_menu.delete(14)
                except Exception:
                    pass
        except Exception:
            pass

        # HTML prettify (best effort)
        try:
            if text_name.endswith('.html') and BeautifulSoup is not None:
                try:
                    soup = BeautifulSoup(file_content, 'html.parser')  # type: ignore
                    file_content = soup.prettify()
                    self.app.soup = soup
                except Exception:
                    pass
        except Exception:
            pass

        # Python file – mark and try setting up output box
        try:
            if text_name.endswith('.py'):
                self.app.python_file = True
                try:
                    parent_frame = getattr(self.app, 'editor_container_frame', None) or getattr(self.app, 'root', None)
                    result_tuple = self.app.make_rich_textbox(
                        parent_frame, size=[100, 1], selectbg='blue', wrap=None, font='arial 12', bd=2
                    )
                    if isinstance(result_tuple, tuple) and len(result_tuple) >= 3:
                        self.app.output_frame, self.app.output_box, self.app.output_scroll = result_tuple[:3]
                        try:
                            self.app.output_box.configure(state='disabled')
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

        # Update state and UI
        try:
            self.app.EgonTE.delete('1.0', END)
        except Exception:
            pass

        try:
            self.app.text_name = text_name
            self.app.open_status_name = text_name
            self.app.file_name = text_name
        except Exception:
            pass

        shown_name = os.path.basename(text_name)
        self.update_file_bar(f'Opened file: {shown_name}')

        try:
            # benign even if not a Python file; menu logic checks python_file flag
            self.app.manage_menus(mode='python')
        except Exception:
            pass

        self.editor_set_all(file_content)

        # Persist 'open last file'
        try:
            if self.app.data.get('open_last_file'):
                self.app.save_last_file()
        except Exception:
            pass

        self.append_record(f'> [{get_time()}] - Opened {getattr(self.app, "file_name", text_name)}')

    def save_as(self, event: Optional[object] = None) -> Optional[str]:
        '''
        Save current buffer into a new file path; returns the resolved path or None.
        - event == 'get name' keeps legacy behavior: return current file name if available.
        '''
        if event == 'get name':
            file_name = getattr(self.app, 'file_name', '')
            if file_name:
                return file_name
            self.show_error('You cannot copy a file path if there is no active file')
            return None

        text_file_path = filedialog.asksaveasfilename(
            defaultextension='.*',
            initialdir='C:/EgonTE',
            title='Save File',
            filetypes=text_extensions
        )
        if not text_file_path:
            return None

        content = self.editor_get_all_for_write()
        try:
            with open(text_file_path, 'w', encoding='utf-8') as file_pointer:
                file_pointer.write(content)
        except Exception:
            try:
                with open(text_file_path, 'w') as file_pointer:
                    file_pointer.write(content)
            except Exception:
                self.show_error('Failed to save file')
                return None

        # Update state and status bar
        try:
            self.app.file_name = text_file_path
            self.app.open_status_name = text_file_path
        except Exception:
            pass

        # Preserve legacy attempt to hide initial path, fallback to basename
        try:
            safe_name = self.app.file_name.replace('C:/EgonTE', '')
            if not safe_name:
                safe_name = os.path.basename(text_file_path)
        except Exception:
            safe_name = os.path.basename(text_file_path)

        self.update_file_bar(f'Saved: {safe_name} - {get_time()}')

        try:
            if self.app.data.get('open_last_file'):
                self.app.save_last_file()
        except Exception:
            pass

        self.append_record(f'> [{get_time()}] - Saved {text_file_path}')
        return text_file_path

    def save(self, event: Optional[object] = None) -> bool:
        '''
        Save current buffer into the existing file path, or fallback to save_as.
        '''
        open_status_name = getattr(self.app, 'open_status_name', '')
        if open_status_name:
            content = self.editor_get_all_for_write()
            try:
                with open(open_status_name, 'w', encoding='utf-8') as file_pointer:
                    file_pointer.write(content)
            except Exception:
                try:
                    with open(open_status_name, 'w') as file_pointer:
                        file_pointer.write(content)
                except Exception:
                    self.show_error('Failed to save file')
                    return False

            file_name = getattr(self.app, 'file_name', open_status_name)
            self.update_file_bar(f'Saved: {file_name} - {get_time()}')
            self.append_record(f'> [{get_time()}] - Saved {file_name}')
            return True

        # No existing path -> Save As
        return bool(self.save_as(event=None))

    def print_file(self) -> bool:
        '''
        Best-effort print for the current file (Windows supports os.startfile(..., 'print')).
        Returns True if successfully initiated, else False.
        '''
        path_value = getattr(self.app, 'open_status_name', '') or getattr(self.app, 'file_name', '')
        if not path_value:
            self.show_error('No file to print')
            return False
        if not os.path.exists(path_value):
            self.show_error('File path is invalid or no longer exists')
            return False
        try:
            if sys.platform.startswith('win'):
                os.startfile(path_value, 'print')  # type: ignore[attr-defined]
                self.append_record(f'> [{get_time()}] - Print command sent: {path_value}')
                return True
            # Fallback: open with default app (user can print from there)
            if sys.platform.startswith('darwin'):
                os.system(f'open "{path_value}"')
            else:
                os.system(f'xdg-open "{path_value}"')
            self.append_record(f'> [{get_time()}] - Opened for printing: {path_value}')
            return True
        except Exception:
            self.show_error('Print is not supported on this system')
            return False

    def merge_files(self, paths: Optional[Sequence[str]] = None, separator: str = '\n') -> bool:
        '''
        Merge the content of provided files (or ask via dialog if None) into the editor buffer.
        '''
        try:
            selected_paths = list(paths or filedialog.askopenfilenames(
                title='Choose files to merge', filetypes=text_extensions
            ) or [])
        except Exception:
            selected_paths = []
        if not selected_paths:
            return False

        parts: list[str] = []
        for path_item in selected_paths:
            try:
                with open(path_item, 'r', encoding='utf-8') as file_pointer:
                    parts.append(file_pointer.read())
            except Exception:
                try:
                    with open(path_item, 'r') as file_pointer:
                        parts.append(file_pointer.read())
                except Exception:
                    parts.append('')
        merged_text = separator.join(parts)
        try:
            prepend_text = (separator if self.editor_get_all_for_write().strip() else '')
            self.app.EgonTE.insert('end', prepend_text + merged_text)
            self.append_record(f'> [{get_time()}] - Merged {len(selected_paths)} files')
            return True
        except Exception:
            return False

    def delete_file(self, path: Optional[str] = None, custom: Optional[str] = None) -> bool:
        '''
        Delete the given path or the currently open file; asks for confirmation.
        Note: 'custom' is accepted for backward compatibility with older call sites.
        '''
        target_path = path or custom or getattr(self.app, 'open_status_name', '') or getattr(self.app, 'file_name', '')
        if not target_path:
            self.show_warning('No file to delete')
            return False
        try:
            base_name = os.path.basename(target_path)
            if not messagebox.askyesno(self.title_text(''), f'Delete file:\n{base_name}?'):
                return False
            os.remove(target_path)
        except Exception:
            self.show_error('Could not delete file')
            return False
        # Clear editor state if it was the current file
        try:
            if getattr(self.app, 'open_status_name', '') == target_path or getattr(self.app, 'file_name', '') == target_path:
                self.app.open_status_name = ''
                self.app.file_name = ''
                self.update_file_bar('New file')
        except Exception:
            pass
        self.append_record(f'> [{get_time()}] - Deleted {target_path}')
        return True

    def file_info(self, path: Optional[str] = None) -> dict:
        '''
        Return file stats (and optionally show a small summary via status bar).
        '''
        target_path = path or getattr(self.app, 'open_status_name', '') or getattr(self.app, 'file_name', '')
        info: dict = {}
        if not target_path:
            return info
        path_object = pathlib.Path(target_path)
        try:
            stat_info = path_object.stat()
            info = {
                'name': path_object.name,
                'path': str(path_object),
                'size_bytes': stat_info.st_size,
                'modified': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'created': datetime.fromtimestamp(stat_info.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                'suffix': path_object.suffix,
                'parent': str(path_object.parent),
            }
            # optional UI hint
            self.update_file_bar(f'File: {path_object.name} • {info["size_bytes"]} bytes')
        except Exception:
            pass
        return info
