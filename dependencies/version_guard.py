import sys
import webbrowser
from typing import Tuple

RECOMMENDED = (3, 10)
MAX_EXCLUSIVE = (3, 11)  # allow 3.10.x only

def version_in_range(
    ver: Tuple[int, int, int],
    min_inc: Tuple[int, int] = RECOMMENDED,
    max_exc: Tuple[int, int] = MAX_EXCLUSIVE,
) -> bool:
    return (ver[0], ver[1]) >= min_inc and (ver[0], ver[1]) < max_exc

def ensure_supported_python(
    min_inc: Tuple[int, int] = RECOMMENDED,
    max_exc: Tuple[int, int] = MAX_EXCLUSIVE,
    download_url: str = 'https://www.python.org/downloads/release/python-31013/',
    allow_continue: bool = True,
) -> bool:
    '''
    Returns True if OK to continue, False if the app should exit.
    Shows a small Tk prompt if GUI is available; otherwise prints to stderr.
    '''
    py = sys.version_info
    if version_in_range((py.major, py.minor, py.micro), min_inc, max_exc):
        return True

    msg = (
        f'This application is tested on Python {min_inc[0]}.{min_inc[1]}.\n'
        f'You are running {py.major}.{py.minor}.{py.micro}.\n\n'
        'Using another version may cause errors.'
    )

    # Try a small Tk dialog if possible
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()

        if allow_continue:
            user_choice = messagebox.askyesnocancel(
                title='Unsupported Python Version',
                message=msg + '\n\nYes = Continue anyway\nNo = Open download page\nCancel = Exit',
                icon=messagebox.WARNING,
            )
            if user_choice is True:   # Continue anyway
                root.destroy()
                return True
            elif user_choice is False:  # Open download page
                webbrowser.open(download_url)
                root.destroy()
                return False
            else:  # Cancel
                root.destroy()
                return False
        else:
            messagebox.showerror('Unsupported Python Version', msg + '\n\nExiting.')
            root.destroy()
            return False
    except Exception:
        # Headless or Tk not available: fallback to console
        sys.stderr.write(
            msg
            + f'\nDownload {min_inc[0]}.{min_inc[1]} from: {download_url}\n'
        )
        return allow_continue
