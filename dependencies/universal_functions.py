from tkinter import END, ANCHOR, messagebox
import webbrowser
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from ctypes import WinDLL

@staticmethod
def fill_by_click(ui_element, event, listbox):
    selected_item = listbox.get(ANCHOR)
    if selected_item:
        ui_element.delete(0, END)
        ui_element.insert(END, selected_item)



@staticmethod
def get_time() -> str:
    '''
    returns current time formated
    '''
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# def get_pos(self) -> str:
#     '''
#     return the index of your text pointer in the main text box
#     '''
#     return self.EgonTE.index(INSERT)

@staticmethod
def ex_links(mode: str = '', link : str = ''):
    '''
    opens the GitHub \ discord \ microsoft store pages on your browser
    '''
    if not link:
        if mode == 'g':
            link = 'https://github.com/Ariel4545/text_editor'
        elif mode == 'd':
            link = 'https://discord.gg/nnF3GvF42G'

    webbrowser.open(link)


def check_file_changes(file_name, content):
    '''+ beta function - need to be tested'''
    proceed = False
    if file_name:
        with open(file_name, 'r', encoding='utf-8') as fp:
            file_content = fp.read() + '\n'  # tkinter most often has an newline at the end

        # checking the precantage of identicality, we would consider 95% percent and above equal
        matcher = SequenceMatcher(None, file_content, content)
        similarity = matcher.ratio()
        if similarity >= 0.95:
            proceed = True
        else:
            if messagebox.askyesno('EgonTE', 'its seems that the current file is not saved\ndo you wish to proceed?'):
                proceed = True

    else:
        proceed = True
    return proceed


@staticmethod
def get_k_lang():
    '''
    this function gets the keyboard language in use by the current active window process.
    '''
    user32 = WinDLL('user32', use_last_error=True)

    # Get the current active window handle
    handle = user32.GetForegroundWindow()

    # Get the thread id from that window handle
    threadid = user32.GetWindowThreadProcessId(handle, 0)

    # Get the keyboard layout id from the threadid
    layout_id = user32.GetKeyboardLayout(threadid)

    # Extract the keyboard language id from the keyboard layout id
    language_id = layout_id & (2 ** 16 - 1)

    # Convert the keyboard language id from decimal to hexadecimal
    language_id_hex = hex(language_id)

    # Check if the hex value is in the dictionary.
    if language_id_hex in languages.keys():
        return languages[language_id_hex]
    else:
        return ['not found', False]