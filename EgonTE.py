# default libraries
from tkinter import filedialog, colorchooser, font, ttk, messagebox, simpledialog
from tkinter import *
from tkinter.tix import *
import subprocess
from sys import exit as exit_
from sys import executable
import ssl
from socket import gethostname
from collections import Counter
from itertools import islice
import os
from random import choice, randint, random, shuffle, randrange
import time
from re import findall, sub
from re import search as reSearch
from re import split as reSplit
from json import dump, load, loads
from platform import system
from ctypes import WinDLL
from heapq import nlargest
from threading import Thread
from string import ascii_letters, digits, ascii_lowercase, ascii_uppercase, printable, punctuation
import smtplib
from datetime import datetime, timedelta
from io import BytesIO
import importlib
# import fast_autocomplete


def library_installer():
    global lib_index, dw_fails
    lib_index = 0
    dw_fails = 0

    def install_req():
        try:
            spec = importlib.util.find_spec('sys')
        except:
            spec = True
        if spec is not None:
            global lib_index, dw_fails
            end_msg.configure(text=f'Download in progress', fg='orange')
            library_list = ['bs4', 'email', 'emoji', 'keyboard', 'matplotlib', 'names', 'pandas', 'PIL',
                            'pyaudio', 'pydub', 'PyPDF2', 'nltk', 'pathlib', 'PyDictionary',
                            'pyperclip', 'pyshorteners', 'pytesseract', 'pyttsx3', 'pywin32', 'spacy',
                            'SpeechRecognition', ' ssl', 'win32print', 'fast-autocomplete[levenshtein]',
                            'textblob', 'urllib', 'webbrowser', 'wikipedia', 'win32api', 'requests']

            if pip_var.get():
                try:
                    subprocess.check_call([executable, 'python -m pip install --upgrade pip'])
                except:
                    end_msg.configure(text=f'Failded to upgrade pip', fg='red')

            try:
                for lib in library_list[lib_index::]:
                    reqs = subprocess.check_output([executable, '-m', 'pip', 'install', lib])
                    lib_index += 1
                    print(f'Installed {lib}')
                    end_msg.configure(text=f'Download {lib}', fg='orange')
                # installed_packages = [r.decode().split('==')[0] for r in reqs.split()]
                # print(f'installed this librarirs:\n{installed_packages}')

            except (ImportError, NameError, ModuleNotFoundError, subprocess.CalledProcessError) as e:
                print(e)
                dw_fails += 1
                lib_index += 1
                print('trying to continue with the next library')
                install_req()

            end_msg.configure(text=f'Download complete with {dw_fails} fails', fg='green')
        else:
            print('sys library is not defiend')

    install_root = Tk()
    install_root.title('ETE - install required')
    end_msg = Label(install_root, font='arial 8')
    pip_var = BooleanVar()
    install_root.resizable(False, False)
    title = Label(install_root, text='It\'s seems that some of the required libraries aren\'t installed')
    up_pip = Checkbutton(install_root, text='Upgrade pip', variable=pip_var)
    install_button = Button(install_root, text='Install', command=lambda: Thread(target=install_req).start())
    quit_button = Button(install_root, text='Quit', command=lambda: install_root.quit())
    title.pack()
    end_msg.pack()
    install_button.pack()
    quit_button.pack()
    install_root.mainloop()


# required libraries that aren't by default

req_lib = False
try:
    import pytesseract.pytesseract
    from win32print import GetDefaultPrinter  # install pywin32
    from win32api import ShellExecute, GetShortPathName
    from pyttsx3 import init as ttsx_init
    import pyaudio  # imported to make speech_recognition work
    from speech_recognition import Recognizer, Microphone, AudioFile  # install SpeechRecognition
    import webbrowser
    import names
    import urllib.request, urllib.error
    import requests
    # matplotlib (graphs library) in a way that suits tkinter
    import matplotlib

    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
    from pyshorteners import Shortener
    from email.message import EmailMessage
    import pandas
    from pyperclip import copy
    import emoji
    from wikipedia import summary, exceptions, page
    from wikipedia import search as wiki_search
    from difflib import Differ
    from textblob import TextBlob
    from PyPDF2 import PdfReader
    from bs4 import BeautifulSoup
    from spacy.matcher import Matcher
    from PIL import ImageGrab, Image, ImageTk
    import spacy  # download also en_core_web_sm - https://spacy.io/usage
    from pydub import AudioSegment
    from pathlib import Path
    from keyboard import is_pressed
    global translate_root, sort_root
    from spacy.cli import download as nlp_download
    from nltk.corpus import words
    from PyDictionary import PyDictionary

    # import autocomplete

    req_lib = True

except (ModuleNotFoundError) as e:
    print(e)
    RA = False
    library_installer()


'''the optional libreries that can add a lot of extra content to the editor'''
tes = ACTIVE
try:
    from pytesseract import image_to_string  # download https://github.com/UB-Mannheim/tesseract/wiki
except:
    tes = DISABLED
try:
    import YouTubeTranscriptApi

    yt_api = True
except (ImportError, AttributeError, ModuleNotFoundError) as e:
    yt_api = False
try:
    import openai

    openai_library = True
    chatgpt_2library = False
except (ImportError, AttributeError, ModuleNotFoundError) as e:
    openai_library = ''
    try:
        chatgpt_2library = True
        from pyChatGPT import Chat, Options
    except (ImportError, AttributeError, ModuleNotFoundError) as e:
        chatgpt_2library = False
        # second condition that if not met the user will not be able to try to use chatGPT here
try:
    from emoticons import emoticon, demoticon

    emoticons_library = ACTIVE
except (ImportError, AttributeError, ModuleNotFoundError) as e:
    emoticons_library = DISABLED

try:
    import polyglot

    RA = True
except (ImportError, ModuleNotFoundError) as e:
    RA = False

try:
    from googletrans import Translator  # req version 3.1.0a0

    google_trans = True
    deep_trans = ''
except (ImportError, AttributeError, ModuleNotFoundError) as e:
    google_trans = ''

try:
    import git.Repo

    gstate = ACTIVE
except (ImportError, AttributeError, ModuleNotFoundError) as e:
    gstate = DISABLED


# window creation
class Window(Tk):
    def __init__(self):
        global frame

        super().__init__()

        '''
        variables of the program that have connection to the a saving file of thier values
        '''
        # boolean tk vars
        self.bars_active = BooleanVar()
        self.show_statusbar = BooleanVar()
        self.show_toolbar = BooleanVar()
        self.night_mode = BooleanVar()
        self.cc = StringVar()
        self.cs = StringVar()
        self.ww = BooleanVar()
        self.rm = BooleanVar()
        self.aus = BooleanVar()
        # made also here (outside advance settings func) in order to make the usage of variables less wasteful
        self.status_ = True
        self.file_ = True
        self.aed = BooleanVar()
        self.dm = BooleanVar()
        self.sta = BooleanVar()
        self.lf = BooleanVar()
        self.tt_sc = BooleanVar()
        self.nm_palette = StringVar()
        self.autosave_by = IntVar()
        self.autosave_by.set(1)

        '''
        variables of the program that doesn't save when you close the program
        '''
        # don't inculuded in the saved settings
        self.sta.set(True)
        self.aed.set(True)
        self.dm.set(False)
        self.prefer_gpu = BooleanVar()
        # python file
        self.auto_cc = BooleanVar()
        self.auto_cc.set(True)
        self.sar = BooleanVar()
        self.call_n = 1
        self.ci_from = ''
        self.status_var = StringVar()
        self.status_var.set('Lines:1 Characters:0 Words:0')
        self.python_file = ''
        # variables of verious tools
        self.file_name = ''
        self.text_changed = False
        self.aul = False
        self.op_active = ''
        self.info_page_active = False
        self.vk_active = False
        open_status_name = ''
        self.key = ''
        self.fs_value = False
        self.tm_value = False
        self.wiki_var = IntVar()
        self.wiki_var.set(1)
        self.sr_supported_langs = {'English (US)' : 'en-US', 'English (UK)' : 'en-GB', 'Spanish (Spain)' : 'es-ES',
                                   'French': 'fr-FR', 'Russian' : 'ru', 'Arabic (Egypt)' : 'ar-EG' , 'Japanese' : 'ja',
                                   'Italian' : 'it-IT', 'Korean' : 'ko', 'Indonesian' : 'id', 'Hebrew' : 'he'
                                   }
        self.stt_chosen_lang = StringVar()
        self.stt_chosen_lang.set('English (US)')
        self.stt_lang_value = 'en-US'

        # opening the saved settings early can make us create some widgets with the settings initaly
        try:
            default_needed = self.saved_settings()
            ss_work = True
        except KeyError:
            ss_work = False
            if messagebox.askyesno('EgonTE',
                                   'There is key-error with the saved settings\ndo you wish to reset the file?'):
                if os.path.exists('EgonTE_settings.json'):
                    os.remove('EgonTE_settings.json')
                    print('Corrupted file has been reset - program needed to be closed for that')
                    self.exit_app()
        if ss_work:
            if default_needed:
                self.bars_active.set(True)
                self.show_statusbar.set(True)
                self.show_toolbar.set(True)
                self.cc.set('xterm')
                self.cs.set('clam')
                self.ww.set(True)
                self.aus.set(True)
                self.nm_palette.set('black')
                # pre-defined variables for the options of the program
                self.predefined_cursor = 'xterm'
                self.predefined_style = 'clam'
                self.predefined_relief = 'ridge'

        # default resolution & placenment of the window
        self.width = 1250
        self.height = 830
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        placement_x = round((screen_width / 2) - (self.width / 2))
        placement_y = round((screen_height / 2) - (self.height / 2))
        self.geometry(f'{self.width}x{self.height}+{placement_x}+{placement_y}')
        '''
        variables for the mains window UI 
        '''
        # window's title
        ver = '1.12.2+'
        self.title(f'Egon Text editor - {ver}')
        # function thats loads all the toolbar images
        self.load_images()
        # connecting the prees of the exit button the a custom exit function
        self.protocol("WM_DELETE_WINDOW", self.exit_app)
        # threads for a stopwatch function that works on advance option window and a function that loads images from the web
        Thread(target=self.stopwatch, daemon=True).start()
        Thread(target=self.load_links, daemon=True).start()
        # variables for the (UI) style of the program
        self.titles_font = '@Microsoft YaHei Light', 16, 'underline'
        self.title_struct = 'EgonTE - '
        self.style_combobox = ttk.Style(self)
        self.dynamic_overall = 'SystemButtonFace'
        self.dynamic_text = 'black'
        self.dynamic_bg = 'SystemButtonFace'
        self.dynamic_button = 'SystemButtonFace'

        # set of condition that check if you have the tesseract executable
        global tes
        if tes == ACTIVE:
            try:
                if not (os.path.exists(r'Tesseract-OCR\tesseract.exe')):
                    pytesseract.pytesseract.tesseract_cmd = (r'C:\Program Files\Tesseract-OCR\tesseract.exe')
                print('pytesseract - initial steps complated')
            except:
                tes = DISABLED

        # create toll tip, for the toolbar buttons (with shortcuts)
        TOOL_TIP = Balloon(self)

        # add custom style
        self.style = ttk.Style()
        self.style.theme_use(self.predefined_style)
        frame = Frame(self)
        frame.pack(expand=True, fill=BOTH, padx=15)
        # create toolbar frame
        self.toolbar_frame = Frame(frame)
        self.toolbar_frame.pack(fill=X, anchor=W, side=TOP)
        self.img_extensions = (('PNG', '*.png'), ('JPG', '*.jpg'))
        self.ex_tool = 'arial 9 bold'
        self.record_list = [f'> [{self.get_time()}] - Program opened']

        # font UI (combo box) and it's values
        font_tuple = font.families()
        self.font_family = StringVar()
        self.font_ui = ttk.Combobox(self.toolbar_frame, width=30, textvariable=self.font_family, state="readonly",
                                    style='TCombobox')
        self.font_ui['values'] = font_tuple
        self.font_ui.current(font_tuple.index('Arial'))
        self.font_ui.grid(row=0, column=4, padx=5)

        # font's size UI (combo box) and it's values
        self.size_var = IntVar()
        self.size_var.set(16)
        self.font_size = ttk.Combobox(self.toolbar_frame, width=5, textvariable=self.size_var, state="readonly",
                                      style='TCombobox')
        self.font_size["values"] = tuple(range(8, 80, 2))
        self.font_Size_c = 4
        self.font_size.current(self.font_Size_c)  # 16 is at index 4
        self.font_size.grid(row=0, column=5, padx=5)
        # create vertical scrollbar
        self.eFrame = Frame(frame)
        self.eFrame.pack(fill=BOTH, expand=True)
        self.text_scroll = ttk.Scrollbar(self.eFrame)
        self.text_scroll.pack(side=RIGHT, fill=Y)
        # horizontal scrollbar
        self.horizontal_scroll = ttk.Scrollbar(frame, orient='horizontal')
        # create text box
        self.EgonTE = Text(self.eFrame, width=100, height=1, font=('arial', 16), selectbackground='blue',
                           selectforeground='white',
                           undo=True,
                           yscrollcommand=self.text_scroll.set, wrap=WORD, relief=self.predefined_relief,
                           cursor=self.predefined_cursor)
        self.EgonTE.focus_set()
        self.EgonTE.pack(fill=BOTH, expand=True)
        # config scrollbars
        self.text_scroll.config(command=self.EgonTE.yview)
        self.EgonTE.config(xscrollcommand=self.horizontal_scroll.set)
        self.horizontal_scroll.config(command=self.EgonTE.xview)
        # create main menu's componenet
        self.app_menu = Menu(frame)
        self.config(menu=self.app_menu)

        self.create_menus(initial=True)

        # add status bar
        self.status_frame = Frame(frame, height=20)
        self.status_frame.pack(fill=BOTH, anchor=S, side=BOTTOM)
        self.status_bar = Label(self.status_frame, text=self.status_var.get(), pady=5)
        self.status_bar.pack(fill=Y, side=LEFT)
        # add file bar
        self.file_bar = Label(self.status_frame, text='')
        self.file_bar.pack(fill=Y, side=RIGHT)

        # checks if the last open file option is on and there is a file to insert when opening the program
        insert_lf = False
        if self.data['open_last_file']:
            self.lf.set(True)
            if isinstance(self.data['open_last_file'], str):
                if os.path.exists(self.data['open_last_file']):
                    self.open_file(event='initial')
                    insert_lf = True

        # conventional shortcuts for functions
        self.bind('<Control-o>', self.open_file)
        self.bind('<Control-O>', self.open_file)
        self.bind('<<Cut>>', lambda event: self.cut(True))
        self.bind('<<Copy>>', lambda event: self.copy(True))
        self.bind('<Control-Key-s>', self.save)
        self.bind('<Control-Key-S>', self.save)
        self.bind('<Control-Key-a>', self.select_all)
        self.bind('<Control-Key-A>', self.select_all)
        self.bind('<Control-Key-b>', self.bold)
        self.bind('<Control-Key-B>', self.bold)
        self.bind('<Control-Key-i>', self.italics)
        self.bind('<Control-Key-I>', self.italics)
        self.bind('<Control-Key-u>', self.underline)
        self.bind('<Control-Key-U>', self.underline)
        self.bind('<Control-Key-l>', self.align_left)
        self.bind('<Control-Key-L>', self.align_left)
        self.bind('<Control-Key-e>', self.align_center)
        self.bind('<Control-Key-E>', self.align_center)
        self.bind('<Control-Key-r>', self.align_right)
        self.bind('<Control-Key-R>', self.align_right)
        self.bind('<Control-Key-p>', self.print_file)
        self.bind('<Control-Key-P>', self.print_file)
        self.bind('<Control-Key-n>', self.new_file)
        self.bind('<Control-Key-N>', self.new_file)
        self.bind('<Control-Key-Delete>', self.clear)
        self.bind('<Control-Key-f>', self.find_text)
        self.bind('<Control-Key-F>', self.find_text)
        self.bind('<Control-Key-h>', self.replace)
        self.bind('<Control-Key-H>', self.replace)
        self.bind('<Control-Shift-Key-j>', self.join_words)
        self.bind('<Control-Shift-Key-J>', self.join_words)
        self.bind('<Control-Shift-Key-u>', self.lower_upper)
        self.bind('<Control-Shift-Key-U>', self.lower_upper)
        self.bind('<Alt-F4>', self.exit_app)
        self.bind('<Control-Shift-Key-r>', self.reverse_characters)
        self.bind('<Control-Shift-Key-R>', self.reverse_characters)
        self.bind('<Control-Shift-Key-c>', self.reverse_words)
        self.bind('<Control-Shift-Key-C>', self.reverse_words)
        self.bind('<Alt-Key-d>', self.copy_file_path)
        self.bind('<Alt-Key-D>', self.copy_file_path)
        self.bind('<Control-Key-plus>', self.size_up_shortcut)
        self.bind('<Control-Key-minus>', self.size_down_shortcut)
        self.bind('<F5>', self.dt)
        self.bind('<Control-Key-g>', self.goto)
        self.bind('<Control-Key-G>', self.goto)
        self.EgonTE.bind('<KeyPress>', self.emoji_detection)
        self.bind('<F11>', self.full_screen)
        # special events
        self.font_size.bind('<<ComboboxSelected>>', self.change_font_size)
        self.font_ui.bind('<<ComboboxSelected>>', self.change_font)
        self.bind('<<Modified>>', self.status)

        # buttons creation and placement
        bold_button = Button(self.toolbar_frame, image=self.BOLD_IMAGE, command=self.bold, relief=FLAT)
        bold_button.grid(row=0, column=0, sticky=W, padx=2)

        italics_button = Button(self.toolbar_frame, image=self.ITALICS_IMAGE, command=self.italics, relief=FLAT)
        italics_button.grid(row=0, column=1, sticky=W, padx=2)

        underline_button = Button(self.toolbar_frame, image=self.UNDERLINE_IMAGE, command=self.underline, relief=FLAT)
        underline_button.grid(row=0, column=2, sticky=W, padx=2)

        color_button = Button(self.toolbar_frame, image=self.COLORS_IMAGE, command=self.text_color, relief=FLAT)
        color_button.grid(row=0, column=3, padx=5)

        align_left_button = Button(self.toolbar_frame, image=self.ALIGN_LEFT_IMAGE, relief=FLAT,
                                   command=self.align_left)
        align_left_button.grid(row=0, column=6, padx=5)

        align_center_button = Button(self.toolbar_frame, image=self.ALIGN_CENTER_IMAGE, relief=FLAT,
                                     command=self.align_center)
        align_center_button.grid(row=0, column=7, padx=5)

        align_right_button = Button(self.toolbar_frame, image=self.ALIGN_RIGHT_IMAGE, relief=FLAT,
                                    command=self.align_right)
        align_right_button.grid(row=0, column=8, padx=5)

        tts_button = Button(self.toolbar_frame, image=self.TTS_IMAGE, relief=FLAT,
                            command=lambda: Thread(target=self.text_to_speech).start(),
                            )
        tts_button.grid(row=0, column=9, padx=5)

        talk_button = Button(self.toolbar_frame, image=self.STT_IMAGE, relief=FLAT,
                             command=lambda: Thread(target=self.speech_to_text).start())
        talk_button.grid(row=0, column=10, padx=5)

        v_keyboard_button = Button(self.toolbar_frame, image=self.KEY_IMAGE, relief=FLAT,
                                   command=lambda: Thread(target=self.virtual_keyboard()).start())

        v_keyboard_button.grid(row=0, column=11, padx=5)
        dtt_button = Button(self.toolbar_frame, image=self.DTT_IMAGE, relief=FLAT,
                            command=self.handwriting)
        dtt_button.grid(row=0, column=12, padx=5)

        calc_button = Button(self.toolbar_frame, image=self.CALC_IMAGE, relief=FLAT,
                             command=self.ins_calc)
        calc_button.grid(row=0, column=13, padx=5)

        # opening sentence that will be inserted if there is no last opened file option
        if not (insert_lf):
            op_msgs = ('Hello world!', '^-^', 'What a beautiful day!', 'Welcome!', '', 'Believe in yourself!',
                       'If I did it you can do way more than that', 'Don\'t give up!',
                       'I\'m glad that you are using my Text editor (:', 'Feel free to send feedback',
                       f'hi {gethostname()}')

            msg_from_web = choice([True, False])
            if msg_from_web:
                try:
                    op_insp_msg = self.insp_quote(op_msg=True)
                    if op_insp_msg:
                        print(op_insp_msg)
                        final_op_msg = op_insp_msg
                    else:
                        raise
                except:
                    final_op_msg = choice(op_msgs)
            else:
                final_op_msg = choice(op_msgs)
            self.EgonTE.insert('1.0', final_op_msg)

        # tooltips to the toolbar's buttons
        TOOL_TIP.bind_widget(bold_button, balloonmsg='Bold (ctrl+b)')
        TOOL_TIP.bind_widget(italics_button, balloonmsg='Italics (ctrl+i)')
        TOOL_TIP.bind_widget(color_button, balloonmsg='Change colors')
        TOOL_TIP.bind_widget(underline_button, balloonmsg='Underline (ctrl+u)')
        TOOL_TIP.bind_widget(align_left_button, balloonmsg='Align left (ctrl+l)')
        TOOL_TIP.bind_widget(align_center_button, balloonmsg='Align center (ctrl+e)')
        TOOL_TIP.bind_widget(align_right_button, balloonmsg='Align right (ctrl+r)')
        TOOL_TIP.bind_widget(tts_button, balloonmsg='Text to speech')
        TOOL_TIP.bind_widget(talk_button, balloonmsg='Speech to text')
        TOOL_TIP.bind_widget(self.font_size, balloonmsg='upwards - (ctrl+plus) \n downwards - (ctrl+minus)')
        TOOL_TIP.bind_widget(v_keyboard_button, balloonmsg='Virtual keyboard')
        TOOL_TIP.bind_widget(dtt_button, balloonmsg='Draw to text')

        # ui tuples (and list) to make management of some UI events (like night mode) easier
        self.toolbar_components = (bold_button, italics_button, color_button, underline_button, align_left_button,
                                   align_center_button, align_right_button, tts_button, talk_button, self.font_size,
                                   v_keyboard_button, dtt_button, calc_button)
        self.menus_components = [self.file_menu, self.edit_menu, self.tool_menu, self.color_menu, self.options_menu, \
                                 self.nlp_menu]
        self.other_components = self, self.status_bar, self.file_bar, self.EgonTE, self.toolbar_frame

    def load_images(self):
        '''
        loads UI's local images (for toolbar buttons) and assigning them to variables
        '''

        # icons - size=32x32
        self.BOLD_IMAGE = PhotoImage(file='new_assests/bold.png', master=self)
        self.UNDERLINE_IMAGE = PhotoImage(file='new_assests/underline.png', master=self)
        self.ITALICS_IMAGE = PhotoImage(file='new_assests/italics.png', master=self)
        self.COLORS_IMAGE = PhotoImage(file='new_assests/colors.png', master=self)
        self.ALIGN_LEFT_IMAGE = PhotoImage(file='new_assests/left_align.png', master=self)
        self.ALIGN_CENTER_IMAGE = PhotoImage(file='new_assests/center_align.png', master=self)
        self.ALIGN_RIGHT_IMAGE = PhotoImage(file='new_assests/right_align.png', master=self)
        self.TTS_IMAGE = PhotoImage(file='new_assests/tts.png', master=self)
        self.STT_IMAGE = PhotoImage(file='new_assests/stt.png', master=self)
        self.KEY_IMAGE = PhotoImage(file='new_assests/keyboard.png', master=self)
        self.DTT_IMAGE = PhotoImage(file='new_assests/drawToText_icon.png', master=self)
        self.CALC_IMAGE = PhotoImage(file='new_assests/calc_icon.png', master=self)

        # adding program logo icon
        try:
            LOGO = PhotoImage(file='ETE_icon.png')
            self.iconphoto(False, LOGO)
        except TclError:
            pass

    def load_links(self):
        '''
        loads images from the web for some extra tools the program have to offer
        '''
        global gpt_image
        gpt_url = 'https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fwww.modify.in.th%2Fwp-content%2Fuploads%2FChatGPT-logo-326x245.gif&f=1&nofb=1&ipt=f0164b4a83aeec7a81f2081b87f90a9d99c04f3d822980e3290ce974fc33e4ae&ipo=images'
        try:
            with urllib.request.urlopen(gpt_url) as u:
                gpt_image_raw_data = u.read()
            gpt_image_ = Image.open(BytesIO(gpt_image_raw_data))
            self.gpt_image = ImageTk.PhotoImage(gpt_image_)


        except (urllib.error.URLError, AttributeError) as e:
            print(e)

        weather_url = 'https://cdn-icons-png.flaticon.com/512/1555/1555512.png'
        try:
            with urllib.request.urlopen(weather_url) as u:
                weather_image_raw_data = u.read()
            weather_image_ = Image.open(BytesIO(weather_image_raw_data))
            self.weather_image = ImageTk.PhotoImage(weather_image_)

        except (urllib.error.URLError, AttributeError) as e:
            print(e)

    def create_menus(self, initial):
        '''
        a function that creates the UI's menus and helps to manage them because it's option to create specific
        menus after some are deleted beacuse of its initial paramater
        '''
        if initial:
            # file menu
            self.file_menu = Menu(self.app_menu, tearoff=False)
            self.app_menu.add_cascade(label='File', menu=self.file_menu)
            self.file_menu.add_command(label='New', accelerator='(ctrl+n)', command=self.new_file)
            self.file_menu.add_command(label='Open', accelerator='(ctrl+o)', command=self.open_file)
            self.file_menu.add_command(label='Save', command=self.save, accelerator='(ctrl+s)')
            self.file_menu.add_command(label='Save As', command=self.save_as)
            self.file_menu.add_command(label='Delete', command=self.delete_file)
            self.file_menu.add_command(label='New window', command=lambda: new_window(Window), state=ACTIVE)
            self.file_menu.add_command(label='Screenshot',
                                       command=lambda: self.save_images(self.EgonTE, self, self.toolbar_frame, 'main'))
            self.file_menu.add_separator()
            self.file_menu.add_command(label='File\'s Info', command=self.file_info)
            self.file_menu.add_command(label='Content\'s stats', command=self.content_stats, font=self.ex_tool)
            self.file_menu.add_command(label='File\'s comparison', command=self.compare)
            self.file_menu.add_command(label='Merge files', command=self.merge_files)
            self.file_menu.add_separator()
            self.file_menu.add_command(label='Print file', accelerator='(ctrl+p)', command=self.print_file)
            self.file_menu.add_separator()
            self.file_menu.add_command(label='Copy path', accelerator='(alt+d)', command=self.copy_file_path)
            self.file_menu.add_separator()
            self.file_menu.add_command(label='Import local file', command=self.special_files_import, font=self.ex_tool)
            self.file_menu.add_command(label='Import global file', command=lambda: self.special_files_import('link'))
            self.file_menu.add_separator()
            self.file_menu.add_command(label='Exit', accelerator='(alt+f4)', command=self.exit_app)
            # edit menu
            self.edit_menu = Menu(self.app_menu, tearoff=True)
            self.app_menu.add_cascade(label='Edit', menu=self.edit_menu)
            self.edit_menu.add_command(label='Cut', accelerator='(ctrl+x)', command=lambda: self.cut(x=True))
            self.edit_menu.add_command(label='Copy', accelerator='(ctrl+c)', command=lambda: self.copy())
            self.edit_menu.add_command(label='Paste', accelerator='(ctrl+v)', command=lambda: self.paste())
            self.edit_menu.add_separator()
            self.edit_menu.add_command(label='Correct writing', command=self.corrector)
            self.edit_menu.add_command(label='Organize writing', command=self.organize, state=DISABLED)
            # self.edit_menu.add_command(label='Autocomplete', command=self.auto_complete)
            self.edit_menu.add_separator()
            self.edit_menu.add_command(label='Undo', accelerator='(ctrl+z)', command=self.EgonTE.edit_undo)
            self.edit_menu.add_command(label='Redo', accelerator='(ctrl+y)', command=self.EgonTE.edit_redo)
            self.edit_menu.add_separator()
            self.edit_menu.add_command(label='Select all', accelerator='(ctrl+a)',
                                       command=lambda: self.select_all('nothing'))
            self.edit_menu.add_command(label='Clear all', accelerator='(ctrl+del)', command=self.clear)
            self.edit_menu.add_separator()
            self.edit_menu.add_command(label='Find Text', accelerator='(ctrl+f)', command=self.find_text)
            self.edit_menu.add_command(label='Replace', accelerator='(ctrl+h)', command=self.replace)
            self.edit_menu.add_command(label='Go to', accelerator='(ctrl+g)', command=self.goto)
            self.edit_menu.add_separator()
            self.edit_menu.add_command(label='Reverse characters', accelerator='(ctrl+shift+c)',
                                       command=self.reverse_characters)
            self.edit_menu.add_command(label='Reverse words', accelerator='(ctrl+shift+r)', command=self.reverse_words)
            self.edit_menu.add_command(label='Join words', accelerator='(ctrl+shift+j)', command=self.join_words)
            self.edit_menu.add_command(label='Upper/Lower', accelerator='(ctrl+shift+u)', command=self.lower_upper)
            self.edit_menu.add_command(label='Sort by characters', command=self.sort_by_characters)
            self.edit_menu.add_command(label='Sort by words', command=self.sort_by_words)
        # tools menu
        self.tool_menu = Menu(self.app_menu, tearoff=False)
        self.app_menu.add_cascade(label='Tools', menu=self.tool_menu)
        self.tool_menu.add_command(label='Current datetime', accelerator='(F5)', command=self.dt)
        self.tool_menu.add_command(label='Random number', command=self.ins_random)
        self.tool_menu.add_command(label='Random name', command=self.ins_random_name)
        if google_trans:
            self.tool_menu.add_command(label='Translate', command=self.translate)
        self.tool_menu.add_command(label='Url shorter', command=self.url)
        self.tool_menu.add_command(label='Generate sequence', command=self.generate)
        self.tool_menu.add_command(label='Search online', command=self.search_www)
        self.tool_menu.add_command(label='Sort', command=self.sort)
        self.tool_menu.add_command(label='Dictionary',
                                   command=lambda: Thread(target=self.knowledge_window('dict')).start())
        self.tool_menu.add_command(label='Wikipedia',
                                   command=lambda: Thread(target=self.knowledge_window('wiki')).start(),
                                   font=self.ex_tool)
        self.tool_menu.add_command(label='Web scrapping', command=self.web_scrapping, font=self.ex_tool)
        self.tool_menu.add_command(label='Text decorators', command=lambda: Thread(target=(self.text_decorators)).start())
        self.tool_menu.add_command(label='Inspirational quote', command=self.insp_quote)
        self.tool_menu.add_command(label='Get weather', command=self.get_weather)
        self.tool_menu.add_command(label='Send Email', command=self.send_email)
        if chatgpt_2library or openai_library:
            self.tool_menu.add_command(label='Use ChatGPT', command=self.chatGPT)
        self.tool_menu.add_command(label='Use DallE', command=self.dallE)
        self.tool_menu.add_command(label='Transcript', command=self.transcript)
        self.tool_menu.add_command(label='Symbols translator', command=self.emojicons_hub)
        # nlp menu
        self.nlp_menu = Menu(self.app_menu, tearoff=False)
        self.app_menu.add_cascade(label='NLP', menu=self.nlp_menu)
        self.nlp_menu.add_command(label='Get noun', command=lambda: self.natural_language_process(function='nouns'))
        self.nlp_menu.add_command(label='Get verb', command=lambda: self.natural_language_process(function='verbs'))
        self.nlp_menu.add_command(label='Get adjectives', command=lambda: self.natural_language_process(
            function='adjective'))
        self.nlp_menu.add_command(label='Get adverbs',
                                  command=lambda: self.natural_language_process(function='adverbs'))
        self.nlp_menu.add_command(label='Get pronouns', command=lambda: self.natural_language_process(
            function='pronouns'))
        self.nlp_menu.add_command(label='get stop words', command=lambda: self.natural_language_process(
            function='stop words'))
        self.nlp_menu.add_command(label='Get names', command=lambda: self.natural_language_process(
            function='names'))
        self.nlp_menu.add_command(label='Get phone numbers', command=lambda: self.natural_language_process(
            function='phone numbers'))
        self.nlp_menu.add_separator()
        self.nlp_menu.add_command(label='Entity recognition',
                                  command=lambda: self.natural_language_process(function='entity recognition'))
        self.nlp_menu.add_command(label='Dependency tree', command=lambda: self.natural_language_process(
            function='dependency'))
        self.nlp_menu.add_command(label='Lemmatization', command=lambda: self.natural_language_process(
            function='lemmatization'))
        self.nlp_menu.add_command(label='Most common words',
                                  command=lambda: self.natural_language_process(function='most common words'))

        # color menu
        self.color_menu = Menu(self.app_menu, tearoff=False)
        self.app_menu.add_cascade(label='Colors+', menu=self.color_menu)
        self.color_menu.add_command(label='Whole text', command=lambda: self.custom_ui_colors(components='text'))
        self.color_menu.add_command(label='Background', command=lambda: self.custom_ui_colors(components='background'))
        self.color_menu.add_command(label='Highlight', command=self.highlight_color)
        self.color_menu.add_separator()
        self.color_menu.add_command(label='Buttons color',
                                    command=lambda: self.custom_ui_colors(components='buttons'))
        self.color_menu.add_command(label='Menus colors', command=lambda: self.custom_ui_colors(components='menus'))
        self.color_menu.add_command(label='App colors', command=lambda: self.custom_ui_colors(components='app'))
        self.color_menu.add_separator()
        self.color_menu.add_command(label='Info page colors',
                                    command=lambda: self.custom_ui_colors(components='info_page'))
        self.color_menu.add_command(label='Virtual keyboard colors',
                                    command=lambda: self.custom_ui_colors(components='v_keyboard'))
        # options menu
        self.options_menu = Menu(self.app_menu, tearoff=False)
        self.app_menu.add_cascade(label='Options', menu=self.options_menu)
        # check marks
        self.options_menu.add_checkbutton(label='Night mode', onvalue=True, offvalue=False,
                                          compound=LEFT, command=self.night)
        self.options_menu.add_checkbutton(label='Status Bars', onvalue=True, offvalue=False,
                                          variable=self.show_statusbar, compound=LEFT, command=self.hide_statusbars)
        self.options_menu.add_checkbutton(label='Tool Bar', onvalue=True, offvalue=False,
                                          variable=self.show_toolbar, compound=LEFT, command=self.hide_toolbar)
        self.options_menu.add_checkbutton(label='Custom cursor', onvalue='tcross', offvalue='xterm',
                                          compound=LEFT, command=self.custom_cursor)
        self.options_menu.add_checkbutton(label='Custom style', onvalue='vista', offvalue='clam',
                                          compound=LEFT, command=self.custom_style)
        self.options_menu.add_checkbutton(label='Word wrap', onvalue=True, offvalue=False,
                                          compound=LEFT, command=self.word_wrap, variable=self.ww)
        self.options_menu.add_checkbutton(label='Reader mode', onvalue=True, offvalue=False,
                                          compound=LEFT, command=self.reader_mode)
        self.options_menu.add_checkbutton(label='Auto save', onvalue=True, offvalue=False,
                                          compound=LEFT, variable=self.aus)
        self.options_menu.add_checkbutton(label='Top most', onvalue=True, offvalue=False,
                                          compound=LEFT, command=self.topmost)
        self.options_menu.add_checkbutton(label='Automatic Emoji detection', compound=LEFT, variable=self.aed)
        self.options_menu.add_checkbutton(label='Dev Mode', command=lambda: self.manage_menus(mode='dev'))
        self.options_menu.add_checkbutton(label='Special tools', command=lambda: self.manage_menus(mode='tools'),
                                          variable=self.sta)
        self.options_menu.add_separator()
        self.options_menu.add_command(label='Advance options', command=self.call_settings)
        # help page
        self.app_menu.add_cascade(label='Help', command=lambda: self.info_page('help.txt'))
        # patch notes page
        self.app_menu.add_cascade(label='Patch notes', command=lambda: self.info_page('patch_notes.txt'))
        # github page
        self.app_menu.add_cascade(label='GitHub', command=self.github)

    def get_time(self):
        '''
        returns current time formated
        '''
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def get_pos(self):
        '''
        return the index of your text pointer in the main text box
        '''
        return self.EgonTE.index(INSERT)

    def github(self):
        '''
        opens the GitHub page on your browser
        '''
        webbrowser.open('https://github.com/Ariel4545/text_editor')

    def undo(self):
        return self.EgonTE.edit_undo()

    def new_file(self, event=None):
        '''
        creates blank workspace (without file)
        '''
        self.file_name = ''
        self.file_bar.config(text='New file')
        self.EgonTE.delete('1.0', END)

        global open_status_name
        open_status_name = False

    def open_file(self, event=None):
        '''
        opens file, have special support also for html and python files
        '''
        content = self.EgonTE.get('1.0', 'end')
        if not (event == 'initial'):
            self.text_name = filedialog.askopenfilename(title='Open file',
                                                        filetypes=(('Text Files', '*.txt'), ('HTML Files', '*.html'),
                                                                   ('Python Files', '*.py')))
        else:
            self.text_name = self.data['open_last_file']

        self.EgonTE.delete('1.0', END)
        if self.text_name:
            try:
                global open_status_name
                open_status_name = self.text_name
                self.file_name = self.text_name
                self.file_bar.config(text=f'Opened file: {GetShortPathName(self.file_name)}')
                self.file_name.replace('C:/EgonTE/', '')
                self.file_name.replace('C:/users', '')
                text_file = open(self.text_name, 'r')
                stuff = text_file.read()
                # disable python IDE if python functionalities are on
                if self.python_file:
                    self.python_file = ''
                    self.outputFrame.destroy()
                    self.app_menu.delete('Run')
                    self.app_menu.delete('Clear console')
                    self.options_menu.delete('Auto clear console')
                    self.options_menu.delete('Save by running')
                    if self.dm.get():
                        self.options_menu.delete(15)
                    else:
                        self.options_menu.delete(14)
                # make the html files formatted when opened
                if self.file_name.endswith('.html'):
                    self.soup = BeautifulSoup(stuff, 'html')
                    stuff = self.soup.prettify()
                # adds functiomality to compile python in EgonTE
                elif self.file_name.endswith('.py'):
                    self.python_file = True

                    self.outputFrame = Frame(frame)
                    self.outputFrame.pack(fill=BOTH, expand=True)
                    self.output_scroll = ttk.Scrollbar(self.outputFrame)
                    self.output_scroll.pack(side=RIGHT, fill=Y)
                    self.output_box = Text(self.outputFrame, width=100, height=1, font=('arial', 12),
                                           selectbackground='blue',
                                           selectforeground='white',
                                           yscrollcommand=self.output_scroll.set, wrap=None,
                                           relief=self.predefined_relief,
                                           cursor=self.predefined_cursor)
                    self.output_box.pack(fill=BOTH, expand=True)
                    self.output_scroll.config(command=self.output_box.yview)
                    self.output_box.configure(state='disabled')

                self.manage_menus(mode='python')

                self.EgonTE.insert(END, stuff)
                text_file.close()

                if self.data['open_last_file']:
                    self.save_last_file()

                self.record_list = [f'> [{self.get_time()}] - Opened {self.file_name}']

            except UnicodeDecodeError:
                messagebox.showerror(self.title_struct + 'error', 'File contains not supported characters')
        else:
            messagebox.showerror(self.title_struct + 'error', 'File not found / selected')
            self.EgonTE.insert('1.0', content)

    # save file as function
    def save_as(self, event=None):
        '''
        saves file by new location that the user will give it
        '''
        if event == None:
            text_file = filedialog.asksaveasfilename(defaultextension='.*', initialdir='C:/EgonTE', title='Save File',
                                                     filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html'),
                                                                ('Python Files', '*.py')))
            if text_file:
                self.file_name = text_file
                self.file_name = self.file_name.replace('C:/EgonTE', '')
                self.file_bar.config(text=f'Saved: {self.file_name} - {self.get_time()}')

                text_file = open(text_file, 'w')
                text_file.write(self.EgonTE.get(1.0, END))
                text_file.close()

                if self.data['open_last_file']:
                    self.save_last_file()

                self.record_list = [f'> [{self.get_time()}] - Saved {text_file}']

        if event == 'get name':
            try:
                return self.file_name
            except NameError:
                messagebox.showerror(self.title_struct + 'error',
                                     'You cant copy a file name if you doesn\'t use a file ')

    # save function
    def save(self, event=None):
        '''
        saves file in its existing location (if its have one)
        '''
        global open_status_name
        if open_status_name:
            text_file = open(open_status_name, 'w')
            text_file.write(self.EgonTE.get(1.0, END))
            text_file.close()
            self.file_bar.config(text=f'Saved: {self.file_name} - {self.get_time()}')
            self.record_list = [f'> [{self.get_time()}] - Saved {self.file_name}']
        else:
            self.save_as(event=None)

    def cut(self, x):
        if self.is_marked():
            # grab the content
            self.selected = self.EgonTE.selection_get()
            # delete the content that selected and add it to clipboard
            self.EgonTE.delete('sel.first', 'sel.last')
            self.clipboard_clear()
            self.clipboard_append(self.selected)

    def copy(self, event=None):
        if self.is_marked():
            # grab
            self.clipboard_clear()
            self.clipboard_append(self.EgonTE.selection_get())
            self.update()

    def paste(self, event=None):
        try:
            self.EgonTE.insert(self.get_pos(), self.clipboard_get())
        except BaseException:
            pass

    def bold(self, event=None):
        '''
        bold font typeface, if the content isnt marked it will choose to apply it for all the text (can undo it as well)
        '''
        # create bold font
        bold_font = font.Font(self.EgonTE, self.EgonTE.cget('font'))
        bold_font.configure(weight='bold')
        # config
        self.EgonTE.tag_configure('bold', font=bold_font)
        current_tags = self.EgonTE.tag_names('1.0')
        if 'bold' in current_tags:
            if self.is_marked():
                self.EgonTE.tag_remove('bold', 'sel.first', 'sel.last')
            else:
                self.EgonTE.tag_remove('bold', '1.0', 'end')
        else:
            if self.is_marked():
                self.EgonTE.tag_add('bold', 'sel.first', 'sel.last')
            else:
                self.EgonTE.tag_add('bold', '1.0', 'end')

    def italics(self, event=None):
        '''
        italics font typeface, if the content isnt marked it will choose to apply it for all the text (can undo it as well)
        '''
        # create italics font
        italics_font = font.Font(self.EgonTE, self.EgonTE.cget('font'))
        italics_font.configure(slant='italic')
        # config
        self.EgonTE.tag_configure('italics', font=italics_font)
        current_tags = self.EgonTE.tag_names('1.0', END)
        if 'italics' in current_tags:
            if self.is_marked():
                self.EgonTE.tag_remove('italics', 'sel.first', 'sel.last')
            else:
                self.EgonTE.tag_remove('italics', '1.0', 'end')
        else:
            if self.is_marked():
                self.EgonTE.tag_add('italics', 'sel.first', 'sel.last')
            else:
                self.EgonTE.tag_add('italics', '1.0', 'end')

    def underline(self, event=None):
        '''
        underline font typeface, if the content isnt marked it will choose to apply it for all the text (can undo it as well)
        '''
        # create underline font
        underline_font = font.Font(self.EgonTE, self.EgonTE.cget('font'))
        underline_font.configure(underline=True)
        # configure with tags
        self.EgonTE.tag_configure('underline', font=underline_font)
        current_tags = self.EgonTE.tag_names('1.0')
        if 'underline' in current_tags:
            if self.is_marked():
                self.EgonTE.tag_remove('underline', 'sel.first', 'sel.last')
            else:
                self.EgonTE.tag_remove('underline', '1.0', 'end')
        else:
            if self.is_marked():
                self.EgonTE.tag_add('underline', 'sel.first', 'sel.last')
            else:
                self.EgonTE.tag_add('underline', '1.0', 'end')

    def text_color(self):
        '''
        texts color, if the content isnt marked it will choose to apply it for all the text
        '''
        # choose custom color
        selected_color = colorchooser.askcolor(title='Text color')[1]
        if selected_color:
            # create the color font
            color_font = font.Font(self.EgonTE, self.EgonTE.cget('font'))
            # configure with tags
            self.EgonTE.tag_configure('colored_txt', font=color_font, foreground=selected_color)
            current_tags = self.EgonTE.tag_names('1.0')
            if 'underline' in current_tags:
                if self.is_marked():
                    self.EgonTE.tag_remove('colored_txt', 'sel.first', 'sel.last')
                else:
                    self.EgonTE.tag_remove('colored_txt', '1.0', 'end')
            else:
                if self.is_marked():
                    self.EgonTE.tag_add('colored_txt', 'sel.first', 'sel.last')
                else:
                    self.EgonTE.tag_add('colored_txt', '1.0', 'end')

    def highlight_color(self):
        color = colorchooser.askcolor(title='Highlight color')[1]
        if color:
            self.EgonTE.config(selectbackground=color)

    def custom_ui_colors(self, components):
        '''
        custom UI colors for all of the main windows components, and for the "knowledge" (wiki/dictionary) window,
        for the help / patch notes window, and for the virtual keyboard
        '''
        if not (self.night_mode):
            if not (messagebox.askyesno('EgonTE', 'Night mode is on, still want to procced?')):
                return
        if components == 'buttons':
            selected_color = colorchooser.askcolor(title='Buttons background color')[1]
            if selected_color:
                self.record_list.append(f'> [{self.get_time()}] - Buttons color changed to {selected_color}')
                for toolbar_button in self.toolbar_components:
                    toolbar_button.config(background=selected_color)

        elif components == 'menus':
            selected_main_color = colorchooser.askcolor(title='Menu color')[1]
            selected_text_color = colorchooser.askcolor(title='Menu text color')[1]
            if selected_main_color and selected_text_color:
                self.record_list.append(
                    f'> [{self.get_time()}] - Menu color changed to {selected_main_color}\n Menu text color'
                    f'changed to {selected_text_color}')
                for menu_ in self.menus_components:
                    menu_.config(background=selected_main_color, foreground=selected_text_color)
        elif components == 'app':
            selected_main_color = colorchooser.askcolor(title='Frames color')[1]
            selected_second_color = colorchooser.askcolor(title='Text box color')[1]
            selected_text_color = colorchooser.askcolor(title='Text color')[1]
            if selected_main_color and selected_second_color and selected_text_color:
                self.config(bg=selected_main_color)
                self.status_frame.configure(bg=selected_main_color)
                self.status_bar.config(bg=selected_main_color, fg=selected_text_color)
                self.file_bar.config(bg=selected_main_color, fg=selected_text_color)
                self.EgonTE.config(bg=selected_second_color)
                self.toolbar_frame.config(bg=selected_main_color)
                self.record_list.append(
                    f'> [{self.get_time()}] - App\'s color changed to {selected_main_color}\n  '
                    f'App\'s secondary color changed'
                    f' to {selected_second_color}\n  App\'s text color changed to {selected_text_color}')

        # background custom color
        elif components == 'background':
            selected_color = colorchooser.askcolor(title='Background color')[1]
            if selected_color:
                self.EgonTE.config(bg=selected_color)

        # entire custom text color
        elif components == 'text':
            color = colorchooser.askcolor(title='Text color')[1]
            if color:
                self.EgonTE.config(fg=color)

        elif components == 'info_page':
            if self.info_page_active:
                bg_color = colorchooser.askcolor(title='Backgrounds color')[1]
                text_color = colorchooser.askcolor(title='Text color')[1]
                self.info_page_text.config(bg=bg_color, fg=text_color)
                self.info_page_title.config(bg=bg_color, fg=text_color)
            else:
                messagebox.showerror('EgonTE', 'Information window isn\'t opened')

        elif components == 'v_keyboard':
            if self.vk_active:
                bg_color = colorchooser.askcolor(title='Backgrounds color')[1]
                text_color = colorchooser.askcolor(title='Text color')[1]
                for vk_btn in self.all_vk_buttons:
                    vk_btn.config(bg=bg_color, fg=text_color)
            else:
                messagebox.showerror('EgonTE', 'Virtual keyboard window isn\'t opened')

    def print_file(self, event=None):
        '''
        old function that aims to print your file
        '''
        file2p = filedialog.askopenfilename(initialdir='C:/EgonTE/', title='Open file',
                                            filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html'),
                                                       ('Python Files', '*.py')))
        if system().lower() == 'windows':
            printer_name = GetDefaultPrinter()
            if file2p:
                if messagebox.askquestion('EgonTE', f'are you wish to print with {printer_name}?'):
                    ShellExecute(0, 'print', file2p, None, '.', 0)
        else:
            printer_name = simpledialog.askstring('EgonTE - Print', 'What is your printer name?')
            if printer_name and file2p:
                os.system(f'lpr -P f{printer_name} f{file2p}')

    # select all text function
    def select_all(self, event=None):
        self.EgonTE.tag_add('sel', '1.0', 'end')

    # clear all text function
    def clear(self, event=None):
        self.EgonTE.delete('1.0', END)

    def hide_statusbars(self):
        '''
        option to hide all of the informative text in the bottom of the program (file bar, status bar)
        '''
        if not (self.show_statusbar.get()):
            self.status_bar.pack_forget()
            self.file_bar.pack_forget()
            self.geometry(f'{self.width}x{self.height - 30}')
            self.show_statusbar.set(False)
            self.bars_active = False
        else:
            self.status_bar.pack(side=LEFT)
            self.file_bar.pack(side=RIGHT)
            self.geometry(f'{self.width}x{self.height - 20}')
            self.show_statusbar.set(True)
            self.bars_active = True

    # hide tool bar function
    def hide_toolbar(self):
        if self.show_toolbar:
            self.toolbar_frame.pack_forget()
            self.height = 770
            self.geometry(f'{self.width}x{self.height}')
            self.show_toolbar = False
        else:
            self.EgonTE.focus_displayof()
            self.EgonTE.pack_forget()
            self.text_scroll.pack_forget()
            self.eFrame.pack_forget()
            self.toolbar_frame.pack(fill=X, anchor=W)
            self.text_scroll.pack(side=RIGHT, fill=Y)
            self.eFrame.pack(fill=BOTH, expand=True)
            self.EgonTE.pack(fill=BOTH, expand=True, side=BOTTOM)
            self.EgonTE.focus_set()
            self.height = 805
            self.geometry(f'{self.width}x{self.height}')
            show_toolbar = True
        self.data['toolbar'] = self.show_toolbar

    def night(self):
        '''
        night mode function - have 2 types of night mode, night mode works of all the things that the UI custom colors
        function works on
        '''
        if self.night_mode:
            if self.nm_palette.get() == 'black':
                # black palette night mode
                main_color = '#110022'
                second_color = '#373737'
                third_color = '#27374D'
                _text_color = 'green'
            else:
                # blue palette night mode
                main_color = '#041C32'
                second_color = '#04293A'
                third_color = '#064663'
                _text_color = '#ECB365'
            self.record_list.append(f'> [{self.get_time()}] - Night mode activated')
            self.night_mode = False
            self.data['night_mode'] = True
        else:
            main_color = 'SystemButtonFace'
            second_color = 'SystemButtonFace'
            third_color = 'SystemButtonFace'
            _text_color = 'black'
            self.night_mode = True
            self.data['night_mode'] = False
            self.record_list.append(f'> [{self.get_time()}] - Night mode disabled')

        self.dynamic_overall = main_color
        self.dynamic_text = _text_color
        self.dynamic_bg = second_color
        self.dynamic_button = third_color

        self.config(bg=main_color)
        self.status_bar.config(bg=main_color, fg=_text_color)
        self.status_frame.configure(bg=main_color)
        self.file_bar.config(bg=main_color, fg=_text_color)
        self.EgonTE.config(bg=second_color, fg=_text_color)
        self.toolbar_frame.config(bg=main_color)
        # toolbar buttons
        for toolbar_button in self.toolbar_components:
            toolbar_button.config(background=third_color)
        # file menu colors
        for menu_ in self.menus_components:
            menu_.config(background=second_color, foreground=_text_color)
        # help & patch notes
        if self.info_page_active:
            self.info_page_text.config(bg=second_color, fg=_text_color)
            self.info_page_title.config(bg=second_color, fg=_text_color)
        if self.vk_active:
            for vk_btn in self.all_vk_buttons:
                vk_btn.config(bg=second_color, fg=_text_color)

        self.style_combobox.configure('TCombobox', background=second_color, foreground=_text_color)

    def change_font(self, event):
        '''
        change the font of the main text box
        '''
        global chosen_font
        chosen_font = self.font_family.get()
        self.delete_tags()
        self.EgonTE.configure(font=(chosen_font, 16))

        self.change_font_size()
        self.record_list.append(f'> [{self.get_time()}] - font changed to {chosen_font}')

    def change_font_size(self, event=None):
        '''
        change the fonts size of the main text box
        '''
        self.chosen_size = self.size_var.get()
        self.font_Size_c = (self.chosen_size - 8) // 2
        self.font_size.current(self.font_Size_c)
        size = font.Font(self.EgonTE, self.EgonTE.cget('font'))
        size.configure(size=self.chosen_size)
        # config tags to switch font size
        self.EgonTE.tag_configure('size', font=size)
        current_tags = self.EgonTE.tag_names('1.0')
        if not 'size' in current_tags:
            if self.font_size.get() == '4':
                self.EgonTE.tag_remove('size', '1.0', END)
            else:
                self.EgonTE.tag_add('size', '1.0', END)

        self.record_list.append(f'> [{self.get_time()}] - font size changed to {self.chosen_size}')

    def replace(self, event=None):
        '''
        function that takes user input to change some terms with the thing that you will write
        '''
        # window creation
        replace_root = Toplevel()
        replace_root.resizable(False, False)
        # ui components
        replace_text = Label(replace_root, text='Enter the word that you wish to replace')
        find_input = Entry(replace_root, width=20)
        replace_input = Entry(replace_root, width=20)
        by_text = Label(replace_root, text='by')
        replace_button = Button(replace_root, text='Replace', pady=3)
        replace_text.grid(row=0, sticky=NSEW, column=0, columnspan=1)
        find_input.grid(row=1, column=0)
        by_text.grid(row=2)
        replace_input.grid(row=3, column=0)
        replace_button.grid(row=4, column=0, pady=5)

        # replacing functionality
        def rep_button(self):
            find_ = find_input.get()
            replace_ = replace_input.get()
            content = self.EgonTE.get(1.0, END)

            new_content = content.replace(find_, replace_)
            self.EgonTE.delete(1.0, END)
            self.EgonTE.insert(1.0, new_content)

        replace_button.config(command=rep_button)

    'align the main boxes text specifically if you marker, and all if you dont'

    def align_left(self, event=None):
        if self.is_marked():
            text_content = self.EgonTE.get('sel.first', 'sel.last')
        else:
            self.EgonTE.tag_add('sel', 'insert linestart', 'insert lineend')
            text_content = self.EgonTE.get('insert linestart', 'insert lineend')
        self.EgonTE.tag_config('left', justify=LEFT)
        try:
            self.EgonTE.delete('sel.first', 'sel.last')
            self.EgonTE.insert(INSERT, text_content, 'left')
        except:
            messagebox.showerror(self.title_struct + 'error', 'choose a content')

    def align_center(self, event=None):
        if self.is_marked():
            text_content = self.EgonTE.get('sel.first', 'sel.last')
        else:
            self.EgonTE.tag_add('sel', 'insert linestart', 'insert lineend')
            text_content = self.EgonTE.get('insert linestart', 'insert lineend')
        self.EgonTE.tag_config('center', justify=CENTER)
        try:
            self.EgonTE.delete('sel.first', 'sel.last')
            self.EgonTE.insert(INSERT, text_content, 'center')
        except:
            messagebox.showerror(self.title_struct + 'error', 'choose a content')

    def align_right(self, event=None):
        if self.is_marked():
            text_content = self.EgonTE.get('sel.first', 'sel.last')
        else:
            self.EgonTE.tag_add('sel', 'insert linestart', 'insert lineend')
            text_content = self.EgonTE.get('insert linestart', 'insert lineend')
        self.EgonTE.tag_config('right', justify=RIGHT)
        try:
            self.EgonTE.delete('sel.first', 'sel.last')
            self.EgonTE.insert(INSERT, text_content, 'right')
        except:
            messagebox.showerror(self.title_struct + 'error', 'choose a content')

    def status(self, event=None):
        ''' get & display character and word count for the status bar '''
        global lines, words
        if self.EgonTE.edit_modified():
            self.text_changed = True
            words = len(self.EgonTE.get(1.0, 'end-1c').split())
            characters = len(self.EgonTE.get(1.0, 'end-1c'))
            lines = int((self.EgonTE.index(END)).split('.')[0]) - 1
            self.status_var.set(f'Lines:{lines} Characters:{characters} Words:{words}')
            self.status_bar.config(text=self.status_var.get())
        self.EgonTE.edit_modified(False)

    def text_to_speech(self):
        '''
        AI narrator will read the selected text from the text box, and if you didnt mark some text it will read
        everything that is written
        '''
        global tts
        tts = ttsx_init()
        try:
            content = self.EgonTE.get('sel.first', 'sel.last')
        except BaseException:
            content = self.EgonTE.get('1.0', 'end')
        tts.say(content)
        tts.runAndWait()

    # AI narrator will read the given text for other functions
    def read_text(self, **kwargs):
        global engine
        engine = ttsx_init()
        if 'text' in kwargs:
            ttr = kwargs['text']
        else:
            ttr = self.EgonTE.get(1.0, 'end')
        engine.say(ttr)
        engine.runAndWait()
        engine.stop()

    def text_formatter(self, phrase):
        '''
        function to make the narrator voice more convincing with capitalisation of question words
        '''
        interrogatives = ('how', 'why', 'what', 'when', 'who', 'where', 'is', 'do you', 'whom', 'whose')
        capitalized = phrase.capitalize()
        if phrase.startswith(interrogatives):
            return f'{capitalized}?'
        else:
            return f'{capitalized}.'

    def speech_to_text(self):
        '''
        advanced speech to text function that work for english speaking only (but more is planned)
        '''
        error_sentences = ['I don\'t know what you mean!', 'can you say that again?', 'please speak more clear']
        error_sentence = choice(error_sentences)
        error_msg = f'Excuse me, {error_sentence}'
        recolonize = Recognizer()  # initialize the listener
        mic = Microphone()
        with mic as source:  # set listening device to microphone
            self.read_text(text='Please say the message you would like to the text editor!')
            recolonize.pause_threshold = 1
            audio = recolonize.listen(source)
        try:
            query = recolonize.recognize_google(audio, language=self.stt_lang_value)  # listen to audio
            query = self.text_formatter(query)
        except Exception:
            self.read_text(text=error_msg)
            if messagebox.askyesno('EgonTE', 'are you want to try again?'):
                query = self.speech_to_text()
            else:
                gb_sentences = ['ok', 'goodbye', 'sorry', 'my bad']
                gb_sentence = choice(gb_sentences)
                self.read_text(text=f'{gb_sentence}, I will try to do my best next time!')
        self.EgonTE.insert(INSERT, query, END)
        return query

    # force the app to quit, warn user if file data is about to be lost
    def exit_app(self, event=None):
        '''
        exit function to warn the user if theres a potential for content to be lost, save the settings that are intendent
        for it, and make sure that everything closes
        '''
        self.saved_settings(sm='save')
        if self.file_name:
            text_file = open(self.text_name, 'r')
            stuff = text_file.read()
            if self.text_changed and (self.EgonTE.get('1.0', 'end')) != stuff:
                if messagebox.askyesno(self.title_struct + 'Quit',
                                       'Some changes  warn\'t saved, do you wish to save first?'):
                    self.save()
        self.quit()
        exit_()
        quit()
        exit()
        raise Exception('Close')

    def find_text(self, event=None):
        '''
        find text in the main text box, with some options, and with navigation
        '''
        global cpt_settings, by_characters

        def match_by_capitalization():
            global cpt_settings

            def disable():
                global cpt_settings
                cpt_settings = 'c'
                capitalize_button.config(command=match_by_capitalization, text='by capitalization ✓')

            cpt_settings = 'unc'
            capitalize_button.config(text='by capitalization ✖', command=disable)

        def match_by_word():
            global by_characters

            def disable():
                global by_characters
                by_word.config(command=match_by_word, text='by characters ✓')
                by_characters = True

            by_word.config(text='by words ✓', command=disable)
            by_characters = False

        def enter():
            global cpt_settings, by_characters, offset, starting_index, ending_index
            text_data = self.EgonTE.get('1.0', END + '-1c')
            # by word/character settings
            if not by_characters:
                text_data = text_data.split(' ')

            # capitalize settings
            if cpt_settings == 'unc':
                text_data = str(text_data).lower()
                entry_data = (text_entry.get()).lower()
            elif cpt_settings == 'c':
                text_data = str(text_data)
                entry_data = text_entry.get()
            occurs = text_data.count(entry_data)

            # check if text occurs
            if occurs:
                search_label = messagebox.showinfo('EgonTE:', f'{entry_data} has {str(occurs)} occurrences')

                # select first match
                starting_index = self.EgonTE.search(entry_data, '1.0', END)
                if starting_index:
                    offset = '+%dc' % len(entry_data)
                    ending_index = starting_index + offset
                    self.EgonTE.tag_add(SEL, starting_index, ending_index)

                if int(occurs) > 1:
                    # navigation window

                    def down(si, ei):
                        global ending_index, starting_index
                        self.EgonTE.tag_remove(SEL, '1.0', END)
                        starting_index = self.EgonTE.search(entry_data, ei, END)
                        if si:
                            offset = '+%dc' % len(entry_data)
                            ending_index = starting_index + offset
                            print(f'str:{starting_index} end:{ending_index}')
                            self.EgonTE.tag_add(SEL, starting_index, ending_index)
                            starting_index = ending_index
                        button_up.config(state=ACTIVE)

                    def up(si, ei):
                        global starting_index, ending_index
                        self.EgonTE.tag_remove(SEL, '1.0', END)
                        starting_index = self.EgonTE.search(entry_data, '1.0', si)
                        if si:
                            offset = '+%dc' % len(entry_data)
                            ending_index = starting_index + offset
                            print(f'str:{starting_index} end:{ending_index}')
                            self.EgonTE.tag_add(SEL, starting_index, ending_index)
                            ending_index = starting_index

                    search_text_root.destroy()
                    nav_root = Toplevel()
                    nav_root.resizable(False, False)
                    # title label
                    title = Label(nav_root, text=f'navigate trough the {str(occurs)} occurrences of \'{entry_data}\'',
                                  font='arial 12 underline')
                    # buttons ↑↓
                    button_up = Button(nav_root, text='Reset', command=lambda: up(starting_index, ending_index),
                                       width=5, state=DISABLED)
                    button_down = Button(nav_root, text='↓', command=lambda: down(starting_index, ending_index),
                                         width=5)
                    # placing widgets
                    title.grid(row=0, padx=5)
                    button_up.grid(row=1)
                    button_down.grid(row=2)

            else:
                search_label = messagebox.showinfo('EgonTE:', 'No match found')

        # window creation
        search_text_root = Toplevel()
        search_text_root.resizable(False, False)
        search_text_root.attributes('-alpha', '0.95')
        # variables
        cpt_settings = 'c'
        by_characters = True
        # buttons creation and placement
        text = Label(search_text_root, text='Search text', font='arial 14 underline')
        text_entry = Entry(search_text_root)
        enter_button = Button(search_text_root, command=enter, text='Enter')
        capitalize_button = Button(search_text_root, command=match_by_capitalization, text='by capitalization ✓')
        by_word = Button(search_text_root, command=match_by_word, text='by characters ✓', state=ACTIVE)
        text.grid(row=0, column=1)
        text_entry.grid(row=1, column=1)
        enter_button.grid(row=2, column=1)
        capitalize_button.grid(row=2, column=0, pady=6, padx=5)
        by_word.grid(row=2, column=2, padx=10)

        if self.is_marked():
            text_entry.insert('end', self.EgonTE.get('sel.first', 'sel.last'))

    def ins_calc(self):
        '''
        a claculator using eval that gives the user option to see his equation, and an option to paste the result to
        the text editor
        '''
        self.ins_equation = ''

        def calculate_button():
            self.ins_equation = calc_entry.get()

            last_calc.configure(state='normal')
            last_calc.delete(0, END)
            last_calc.insert(0, self.ins_equation)
            last_calc.configure(state='readonly')

            try:
                self.ins_equation = eval(self.ins_equation)

                calc_entry.delete(0, END)
                calc_entry.insert(0, self.ins_equation)

            except SyntaxError:
                messagebox.showerror(self.title_struct + 'error', 'typed some  invalid characters')
            except NameError:
                messagebox.showerror(self.title_struct + 'error', 'calculation tool support only arithmetics & modulus')
            self.ins_equation = str(self.ins_equation)

        def insert_eq():
            if self.ins_equation:
                eq = f'{self.ins_equation} '
                self.EgonTE.insert(self.get_pos(), eq)

        def show_oper():

            show_op.config(text='hide operations', command=hide_oper)
            op_frame.pack()

        def hide_oper():
            op_frame.pack_forget()
            show_op.config(text='show operations', command=show_oper)

        clac_root = Toplevel(relief=FLAT)
        clac_root.resizable(False, False)
        clac_root.attributes('-alpha', '0.95')
        title = Label(clac_root, text='Calculator', font=self.titles_font, padx=2, pady=3)
        introduction_text = Label(clac_root, text='Enter a equation below:', font='arial 10 underline', padx=2, pady=3)
        enter = Button(clac_root, text='Calculate', command=calculate_button, borderwidth=1, font='arial 10 bold')
        copy_button = Button(clac_root, text='Copy', command=lambda: copy(str(self.ins_equation)), borderwidth=1,
                             font='arial 10')
        insert_button = Button(clac_root, text='Insert', command=insert_eq, borderwidth=1, font='arial 10')
        last_calc = Entry(clac_root, relief=RIDGE, justify='center', width=25, state='readonly')
        calc_entry = Entry(clac_root, relief=RIDGE, justify='center', width=25)
        show_op = Button(clac_root, text='Show operators', relief=FLAT, command=show_oper)
        title.pack(padx=10)
        introduction_text.pack(padx=10)
        last_calc.pack()
        calc_entry.pack()
        enter.pack(pady=3)
        copy_button.pack(pady=1)
        insert_button.pack(pady=1)
        show_op.pack()

        op_frame = Frame(clac_root)
        add_sub = Label(op_frame, text='+ addition, - subtraction')
        mul_div = Label(op_frame, text='* multiply, / deviation')
        pow_ = Label(op_frame, text='** power, % modulus')

        add_sub.pack()
        mul_div.pack()
        pow_.pack()

        if self.is_marked():
            if str(self.EgonTE.get('sel.first', 'sel.last')).isnumeric():
                calc_entry.insert('end', self.EgonTE.get('sel.first', 'sel.last'))

        self.record_list.append(f'> [{self.get_time()}] - calculation tool window opened')

    def dt(self, event=None):
        '''
        insert the current date/time to where the pointer of your text are
        '''
        self.EgonTE.insert(self.get_pos(), self.get_time() + ' ')

    def ins_random(self):
        '''
        insert random numbers - random int / random decimal (between 0-1) to the text editor.
        the random int is based on your input but also has random range when you open it.
        there is also quick random int that is self explanatory
        '''

        def enter_button_custom():
            global num_1, num_2
            try:
                try:
                    num_1 = int(number_entry1.get())
                    num_2 = int(number_entry2.get())
                except ValueError:
                    messagebox.showerror(self.title_struct + 'error', 'didn\'t typed valid characters')
                rand = randint(num_1, num_2)
                rand = str(rand) + ' '
                self.EgonTE.insert(self.get_pos(), rand)
            except NameError:
                pass

        def enter_button_quick_float():
            random_float = str(random()) + ' '
            self.EgonTE.insert(self.get_pos(), random_float)

        def enter_button_quick_int():
            random_float = random()
            random_exp = len(str(random_float))
            random_round = randint(50, 1000)
            random_int = int(random_float * 10 ** random_exp)
            random_int //= random_round
            random_int = str(random_int) + ' '
            self.EgonTE.insert(self.get_pos(), random_int)

        ran_num_root = Toplevel()
        ran_num_root.resizable(False, False)
        ran_num_root.attributes('-alpha', '0.95')
        title = Label(ran_num_root, text='Random numbers:', justify='center',
                      font=self.titles_font)
        introduction_text = Label(ran_num_root, text='Enter numbers below:', justify='center',
                                  font='arial 10 underline')
        sub_c = Button(ran_num_root, text='submit custom', command=enter_button_custom, relief=FLAT)
        sub_qf = Button(ran_num_root, text='submit quick float', command=enter_button_quick_float, relief=FLAT)
        sub_qi = Button(ran_num_root, text='submit quick int', command=enter_button_quick_int, relief=FLAT)
        number_entry1 = Entry(ran_num_root, relief=RIDGE, justify='center', width=25)
        number_entry2 = Entry(ran_num_root, relief=RIDGE, justify='center', width=25)
        bt_text = Label(ran_num_root, text='     Between', font='arial 10 bold')
        title.grid(row=0, column=1)
        introduction_text.grid(row=1, column=1, padx=5)
        number_entry1.grid(row=2, column=0, padx=10)
        bt_text.grid(row=2, column=1)
        number_entry2.grid(row=2, column=2, padx=10)
        sub_c.grid(row=3, column=1)
        sub_qf.grid(row=4, column=0)
        sub_qi.grid(row=4, column=2)

        if self.is_marked():
            ran_numbers = self.EgonTE.get('sel.first', 'sel.last')
            numbers_separation = ran_numbers.split(' ')
            if str(ran_numbers[0]).isnumeric():
                print(numbers_separation)
                number_entry1.insert('end', numbers_separation[0])
            try:
                number_entry2.insert('end', numbers_separation[1])
            except IndexError:
                pass
        else:
            number_entry1.insert('end', str(randint(1, 10)))
            number_entry2.insert('end', str(randint(10, 1000)))

        self.record_list.append(f'> [{self.get_time()}] - random number tool window opened')

    def copy_file_path(self, event=None):
        '''
        if your using a file, it will copy to your clipboard its location
        '''
        if self.file_name:
            file_name_ = self.save_as(event='get name')
            self.clipboard_clear()
            self.clipboard_append(file_name_)
        else:
            messagebox.showerror(self.title_struct + 'error', 'you are not using a file')

    def custom_cursor(self):
        '''
        change between regular cursor (xterm) to a more unique one (tcross)
        '''
        if self.cc.get() == 'tcross':
            self.cc.set('xterm')
        else:
            self.cc.set('tcross')

        self.predefined_cursor = self.cc.get()
        self.data['cursor'] = self.predefined_cursor
        self.EgonTE.config(cursor=self.predefined_cursor)
        try:
            sort_input.config(cursor=self.predefined_cursor)
            translate_box.config(cursor=self.predefined_cursor)
        except BaseException:
            pass

        if self.op_active:
            self.change_button_color('cursors', self.predefined_cursor)

        self.record_list.append(f'> [{self.get_time()}] - cursor changed to {self.cc}')

    def custom_style(self):
        '''
        change between regular style (clam) to a more unique one (vista)
        '''
        if self.cs.get() == 'vista':
            self.cs.set('clam')
        else:
            self.cs.set('vista')

        self.predefined_style = self.cs.get()
        self.data['style'] = self.predefined_style
        self.style.theme_use(self.predefined_style)

        if self.op_active:
            self.change_button_color('styles', self.predefined_style)

        self.record_list.append(f'> [{self.get_time()}] - style changed to {self.cs}')

    def word_wrap(self):
        '''
        when pressed initialy disabling word wrap and adding an vertical scrollbar
        '''
        if not self.ww:
            self.EgonTE.config(wrap=WORD)
            self.geometry(f'{self.width}x{self.height - 10}')
            self.horizontal_scroll.pack_forget()
            self.ww = True
            self.data['word_wrap'] = False
            self.record_list.append(f'> [{self.get_time()}] - Word wrap is activated')
        else:
            self.geometry(f'{self.width}x{self.height + 10}')
            self.horizontal_scroll.pack(side=BOTTOM, fill=X)
            self.EgonTE.config(wrap=NONE)
            self.ww = False
            self.data['word_wrap'] = True
            self.record_list.append(f'> [{self.get_time()}] - Word wrap is disabled')

    def reader_mode(self):
        if not self.rm:
            self.EgonTE.configure(state=NORMAL)
            self.rm = True
            self.data['reader_mode'] = False
            self.record_list.append(f'> [{self.get_time()}] - Reader mode is disabled')
        else:
            self.EgonTE.configure(state=DISABLED)
            self.rm = False
            self.data['reader_mode'] = True
            self.record_list.append(f'> [{self.get_time()}] - Reader mode is activated')

    def ins_random_name(self):
        '''
        the function is generating random names (with some gender and parts od name options),
        and there is an option to paste the random generated to the main text box
        '''
        global random_name

        # insert the random name into the text box
        def button():
            global random_name
            self.EgonTE.insert(self.get_pos(), random_name + ' ')

        # basic name roll
        def roll():
            global random_name
            random_name = names.get_full_name()
            rand_name.config(text=random_name)

        # UI & values
        def adv_option():
            global gender, types
            type_string = StringVar()
            gender_string = StringVar()
            gender = ttk.Combobox(name_root, width=13, textvariable=gender_string, state='readonly',
                                  font=('arial', 10, 'bold'), )
            types = ttk.Combobox(name_root, width=13, textvariable=type_string, state='readonly',
                                 font=('arial', 10, 'bold'), )
            gender['values'] = ('Male', 'Female')
            types['values'] = ('Full Name', 'First Name', 'Last Name')
            gender.grid(row=6, column=0)
            types.grid(row=7, column=0)
            adv_options.grid_forget()

            # advance name roll
            def adv_random_name():
                global random_name
                gender_value = gender.get()
                type_value = types.get()
                if gender_value == 'Male' and type_value == 'Full Name':
                    random_name = names.get_full_name(gender='male')
                    rand_name.config(text=random_name)
                elif gender_value == 'Male' and type_value == 'First Name':
                    random_name = names.get_first_name()
                    rand_name.config(text=random_name)
                elif gender_value == 'Male' and type_value == 'Last Name':
                    random_name = names.get_last_name()
                    rand_name.config(text=random_name)

                elif gender_value == 'Female' and type_value == 'Full Name':
                    random_name = names.get_full_name(gender='female')
                    rand_name.config(text=random_name)
                elif gender_value == 'Female' and type_value == 'First Name':
                    random_name = names.get_first_name()
                    rand_name.config(text=random_name)
                elif gender_value == 'Female' and type_value == 'Last Name':
                    random_name = names.get_last_name()
                    rand_name.config(text=random_name)

            re_roll.config(command=adv_random_name)

        name_root = Toplevel()
        name_root.resizable(False, False)
        name_root.attributes('-alpha', '0.95')
        random_name = names.get_full_name()
        text = Label(name_root, text='Random name that generated:', font='arial 10 underline')
        rand_name = Label(name_root, text=random_name)
        enter = Button(name_root, text='Submit', command=button, relief=RIDGE)
        re_roll = Button(name_root, text='Re-roll', command=roll, relief=RIDGE)
        adv_options = Button(name_root, text='Advance options', command=adv_option, state=ACTIVE, relief=RIDGE)
        copy_b = Button(name_root, text='Copy', command=lambda: copy(str(random_name)), width=10, relief=RIDGE)
        text.grid(row=0, padx=10)
        rand_name.grid(row=1)
        enter.grid(row=2)
        re_roll.grid(row=3)
        adv_options.grid(row=4)
        copy_b.grid(row=5)

        self.record_list.append(f'> [{self.get_time()}] - Random name tool window opened')

    def translate(self):
        '''
        simply an old translate tool using google translate API,
        support auto detect, and have a UI that remiend most of the translate tools UI
        with input and output so the translation doesnt paste automatically to the main text box
        '''
        global translate_root

        def translate_content():
            to_translate = self.translate_box.get('1.0', 'end-1c')
            cl = chosen_language.get()

            if to_translate == '':
                messagebox.showerror(self.title_struct + 'error', 'Please fill the box')
            else:
                translator = Translator()
                self.translate_output = translator.translate(to_translate, dest=cl)
                self.translate_resultbox.configure(state=NORMAL)
                self.translate_resultbox.delete('1.0', END)
                self.translate_resultbox.insert('1.0', self.translate_output.text)
                self.translate_resultbox.configure(state=DISABLED)

        def copy_from_file():
            if self.is_marked():
                self.translate_box.insert('end', self.EgonTE.get('sel.first', 'sel.last'))
            else:
                self.translate_box.insert('end', self.EgonTE.get('1.0', 'end'))

        def paste_to_ete():
            content = self.translate_resultbox.get('1.0', END)
            if content:
                self.EgonTE.insert(self.get_pos(), content)

        # window creation
        translate_root = Toplevel()
        translate_root.attributes('-alpha', '0.95')
        boxes_frame = Frame(translate_root)
        combo_frame = Frame(translate_root)
        button_frame = Frame(translate_root)
        # string variables
        auto_detect_string = StringVar()
        languages = StringVar()
        # combo-box creation
        auto_detect = ttk.Combobox(combo_frame, width=20, textvariable=auto_detect_string, state='readonly',
                                   font='arial 10 bold')

        chosen_language = ttk.Combobox(combo_frame, width=20, textvariable=languages, state='readonly', font='arial 10')

        auto_detect['values'] = ('Auto Detect',)
        auto_detect.current(0)


        chosen_language['values'] = (
            'Afrikaans', 'Albanian', 'Arabic', 'Armenian', ' Azerbaijani', 'Basque', 'Belarusian', 'Bengali', 'Bosnian',
            'Bulgarian', ' Catalan', 'Cebuano', 'Chichewa', 'Chinese', 'Corsican', 'Croatian', ' Czech', 'Danish',
            'Dutch',
            'English', 'Esperanto', 'Estonian', 'Filipino', 'Finnish', 'French', 'Frisian', 'Galician', 'Georgian',
            'German', 'Greek', 'Gujarati', 'Haitian Creole', 'Hausa', 'Hawaiian', 'Hebrew', 'Hindi', 'Hmong',
            'Hungarian',
            'Icelandic', 'Igbo', 'Indonesian', 'Irish', 'Italian', 'Japanese', 'Javanese', 'Kannada', 'Kazakh', 'Khmer',
            'Kinyarwanda', 'Korean', 'Kurdish', 'Kyrgyz', 'Lao', 'Latin', 'Latvian', 'Lithuanian', 'Luxembourgish',
            'Macedonian', 'Malagasy', 'Malay', 'Malayalam', 'Maltese', 'Maori', 'Marathi', 'Mongolian', 'Myanmar',
            'Nepali',
            'Norwegian''Odia', 'Pashto', 'Persian', 'Polish', 'Portuguese', 'Punjabi', 'Romanian', 'Russian', 'Samoan',
            'Scots Gaelic', 'Serbian', 'Sesotho', 'Shona', 'Sindhi', 'Sinhala', 'Slovak', 'Slovenian', 'Somali',
            'Spanish',
            'Sundanese', 'Swahili', 'Swedish', 'Tajik', 'Tamil', 'Tatar', 'Telugu', 'Thai', 'Turkish', 'Turkmen',
            'Ukrainian', 'Urdu', 'Uyghur', 'Uzbek', 'Vietnamese', 'Welsh', 'Xhosa''Yiddish', 'Yoruba', 'Zulu',
        )

        lng_lenght = len(chosen_language['values'])
        lng_index = randint(0, lng_lenght - 1)
        chosen_language.current(lng_index)

        # translate box & button
        title = Label(translate_root, text='Translation tool', font='arial 12 underline')
        self.translate_box = Text(boxes_frame, width=30, height=10, borderwidth=1, cursor=self.predefined_cursor,
                             relief=self.predefined_relief)
        self.translate_resultbox = Text(boxes_frame, width=30, height=10, borderwidth=1, cursor=self.predefined_cursor,
                             relief=self.predefined_relief, state=DISABLED)
        translate_button = Button(button_frame, text='Translate', bd=1, borderwidth=2, font='arial 10 bold',
                         command=translate_content)
        copy_from = Button(button_frame, text='Copy from file', bd=1, command=copy_from_file)
        paste_translation = Button(button_frame, text='Paste to ete', command=paste_to_ete, width=10, bd=1)
        # placing the objects in the window
        title.pack()
        combo_frame.pack()
        auto_detect.pack(side='left', fill=X, expand=True)
        chosen_language.pack(side='right', fill=X, expand=True)
        boxes_frame.pack(fill=BOTH, expand=True)
        self.translate_box.pack(fill=BOTH, expand=True, side='left')
        self.translate_resultbox.pack(fill=BOTH, expand=True, side='right')
        button_frame.pack(pady=5)
        copy_from.grid(row=0, column=0, columnspan=1, padx=2)
        translate_button.grid(row=0, column=1, padx=2)
        paste_translation.grid(row=0, column=2, padx=2)

        self.record_list.append(f'> [{self.get_time()}] - Translate tool window opened')

    def url(self):
        '''
        a simple tool that takes an input of url and inserts a shorter version
        '''
        # window creation
        url_root = Toplevel()
        url_root.title(self.title_struct + 'Url shorter')
        url_root.resizable(False, False)
        url_root.attributes('-alpha', '0.95')
        # ui components creation & placement
        url_text = Label(url_root, text='Enter url below:', font='arial 10 underline')
        url_entry = Entry(url_root, relief=GROOVE, width=40)
        enter = Button(url_root, relief=FLAT, text='Enter')
        url_text.grid(row=0)
        url_entry.grid(row=1, padx=10)
        enter.grid(row=2)

        def shorter():
            try:
                urls = url_entry.get()
                s = Shortener()
                short_url = s.tinyurl.short(urls)
                self.EgonTE.insert(self.get_pos(), short_url)
            except requests.exceptions.ConnectionError:
                messagebox.showerror('EgonTE', 'Device not connected to internet')
            except:
                messagebox.showerror(self.title_struct + 'error', 'Please Paste a valid url')

        enter.config(command=shorter)

        if self.is_marked():
            url_entry.insert('end', self.EgonTE.get('sel.first', 'sel.last'))

        self.record_list.append(f'> [{self.get_time()}] - Url shorter tool window opened')

    def get_indexes(self):
        '''
        if text is marked will return the selected indexes, and if not return the whole index of the text box
        '''
        if not (self.is_marked()):
            self.text_index = 1.0, END
            self.first_index, self.last_index = self.text_index[0], self.text_index[1]
        else:
            self.text_index = 'sel.first', 'sel.last'
            self.first_index, self.last_index = self.EgonTE.index(self.text_index[0]), self.EgonTE.index(
                self.text_index[1])

    def reverse_characters(self, event=None):
        self.get_indexes()
        content = self.EgonTE.get(*self.text_index)
        n = ''

        if self.tt_sc.get():
            content = content.replace(' ', '')

        if '\n' in content:
            content, newline = content.split('\n', maxsplit=1)
            content = content.replace('\n', '')
            if self.tt_sc.get():
                n = ''
            else:
                n = '\n'
            print(content)
        content = ''.join(content)
        reversed_content = content[::-1] + n

        self.EgonTE.delete(*self.text_index)
        self.EgonTE.insert(self.first_index, reversed_content)

    def reverse_words(self, event=None):
        self.get_indexes()

        content = self.EgonTE.get(*self.text_index)
        words = content.split()
        reversed_words = words[::-1]
        self.EgonTE.delete(*self.text_index)
        self.EgonTE.insert(self.first_index, reversed_words)

    def join_words(self, event=None):
        self.get_indexes()

        content = self.EgonTE.get(*self.text_index)

        if self.tt_sc.get():
            content = content.replace(' ', '').replace('\n', '')

        words = content.split()
        joined_words = ''.join(words)
        self.EgonTE.delete(*self.text_index)
        self.EgonTE.insert(self.first_index, joined_words)

    def lower_upper(self, event=None):
        self.get_indexes()
        content = self.EgonTE.get(*self.text_index)

        if content == content.upper():
            content = content.lower()
        else:
            content = content.upper()

        self.EgonTE.delete(*self.text_index)
        self.EgonTE.insert(self.first_index, content)

    def sort_by_characters(self, event=None):
        # need some work still
        content = (self.EgonTE.get(1.0, END))

        if self.tt_sc.get():
            content = content.replace(' ', '').replace('\n', '')

        sorted_content = ''.join(sorted(content))
        # if the content is already sorted it will sort it reversed
        if content == sorted_content:
            sorted_content = ''.join(sorted(sorted_content, reverse=True))
            if self.tt_sc.get():
                sorted_content.replace(' ', '').replace('\n', '')
        self.EgonTE.delete(1.0, END)
        self.EgonTE.insert(1.0, sorted_content)

    def sort_by_words(self, event=None):
        self.get_indexes()
        content = (self.EgonTE.get(*self.text_index))
        content = content.split(' ')

        sorted_words = sorted(content)
        if content == sorted_words:
            sorted_words = sorted(sorted_words, reverse=True)
        self.EgonTE.delete(*self.text_index)
        self.EgonTE.insert(self.first_index, sorted_words)

    def generate(self):
        '''
        insert a random generated string in the length that you decide, containts regular english characters and numbers,
        and also can contain many coomon symbols if you active its option
        '''
        global sym
        generate_root = Toplevel()
        generate_root.resizable(False, False)
        generate_root.attributes('-alpha', '0.95')
        characters = list(ascii_letters + digits)
        intro_text = Label(generate_root, text='Generate a random sequence', font=self.titles_font)
        length_entry = Entry(generate_root, width=15)
        sym_text = Label(generate_root, text='induce symbols?')
        sym_button = Button(generate_root, text='✖')
        enter_button = Button(generate_root, text='Enter', width=8, height=1, bd=1)
        length_text = Label(generate_root, text='length', padx=10)
        intro_text.grid(row=0, column=1)
        length_text.grid(row=1, column=0, padx=10, columnspan=1)
        length_entry.grid(row=2, column=0, padx=3)
        sym_text.grid(row=1, column=2, padx=10)
        sym_button.grid(row=2, column=2, padx=10)
        enter_button.grid(row=2, column=1, padx=10, pady=8)
        sym = False

        def symbols():
            global sym
            sym_button.config(text='✓')
            sym = True
            sym_button.config(command=disable_symbols)

        def disable_symbols():
            global sym
            sym_button.config(text='✖')
            sym = False
            sym_button.config(command=symbols)

        sym_button.config(command=symbols)

        def generate_sequence():
            global sym, sym_char
            try:
                length = int(length_entry.get())
            except ValueError:
                messagebox.showerror(self.title_struct + 'error', 'didn\'t write the length')
            if length < 25000:
                approved = True
            else:
                if messagebox.askyesno('EgonTE', '25000 characters or more will cause lag,'
                                                 ' are you sure you want to proceed?'):
                    approved = True
                else:
                    approved = False
            if approved:
                sym_char = '!', '@', '#', '$', '%', '^', '&', '*', '(', ')'
                if sym:
                    for character in sym_char:
                        characters.append(character)
                else:
                    if sym_char:
                        try:
                            characters.remove('!'), characters.remove('@'), characters.remove('#'), characters.remove(
                                '$'),
                            characters.remove('%'), characters.remove('^'), characters.remove('&'), characters.remove(
                                '*'),
                            characters.remove('('), characters.remove(')')
                        except ValueError:
                            pass
                shuffle(characters)
                sequence = []
                for i in range(length):
                    sequence.append(choice(characters))
                self.EgonTE.insert(self.get_pos(), "".join(sequence))

        enter_button.config(command=generate_sequence)

        self.record_list.append(f'> [{self.get_time()}] - sequence generator tool window opened')

    # font size up by 1 iteration
    def size_up_shortcut(self, event=None):
        '''
        a shortcut to increase the font size, its increasing it by 1 iteration of the values tuple
        '''
        try:
            self.font_size.current(self.font_Size_c + 1)
            self.font_Size_c += 1
            self.change_font_size()
        except Exception:
            messagebox.showerror(self.title_struct + 'error', 'font size at maximum')

    # font size down by 1 iteration
    def size_down_shortcut(self, event=None):
        '''
        a shortcut to decrease the font size, its decreasing it by 1 iteration of the values tuple
        '''
        try:
            self.font_size.current(self.font_Size_c - 1)
            self.font_Size_c -= 1
            self.change_font_size()
        except Exception:
            messagebox.showerror(self.title_struct + 'error', 'font size at minimum')

    def is_marked(self):
        '''
        checks if text in the main text box is being marked, and returns the result in a boolean value
        '''
        if self.EgonTE.tag_ranges('sel'):
            return True
        else:
            return False

    # tags and configurations of the same thing is clashing all the time \:
    def delete_tags(self):
        self.EgonTE.tag_delete('bold', 'underline', 'italics', 'size', 'colored_txt')

    def special_files_import(self, via='file'):
        '''
        a tool that is used to import other fike types to your current text file,
        supports xml, html, csv, excel and pdf
        support also the import of files via link
        '''
        # to make the functions write the whole file even if its huge
        pandas.options.display.max_rows = 9999
        content = ''

        if via == 'file':
            special_file = filedialog.askopenfilename(title='open file',
                                                      filetypes=(('excel', '*.xlsx'), ('csv', '*.csv'), ('pdf', '*.pdf')
                                                                 , ('json', '*.json'), ('xml', '*.xml'),
                                                                 ('all', '*.*')))
        else:
            special_file = simpledialog.askstring('EgonTE', 'enter the link to the file')

        try:
            # identify file types
            if special_file.endswith('.xml'):
                content = pandas.read_xml(special_file).to_string()
            elif special_file.endswith('.csv'):
                content = pandas.read_csv(special_file).to_string()
            elif special_file.endswith('.json'):
                content = pandas.read_json(special_file).to_string()
            elif special_file.endswith('.xlsx'):
                content = pandas.read_excel(special_file).to_string()
            elif special_file.endswith('.pdf'):
                file = PdfReader(special_file)
                pages_number = len(file.pages)
                content = []
                for i in range(pages_number):
                    page = (file.pages[i]).extract_text()
                    content.append(page)
                content = ''.join(content)
            else:
                messagebox.showerror(self.title_struct + 'error', 'nothing found / unsupported file type')

            self.EgonTE.insert(self.get_pos(), content)
            starts = os.path.splitext(special_file)[0]
            ends = os.path.splitext(special_file)[-1][1:]
            self.record_list.append(f'> [{self.get_time()}] - Special file ({ends}) imported;\n  the files name is'
                                    f' {starts}\n   and the file was imported via {via}')
        except AttributeError:
            messagebox.showerror(self.title_struct + 'error', 'please enter a valid domain')

    # a window that have explanations confusing features
    def info_page(self, path):
        occurs = False
        '''
        the UI for the help and patch notes pages
        '''

        def quit_page():
            self.info_page_active = False
            info_root.destroy()

        # window creation
        self.info_page_active = True
        info_root = Toplevel()
        info_root.config(bg='white')
        info_root.protocol("WM_DELETE_WINDOW", quit_page)

        # putting the lines in order
        def place_lines():
            self.info_page_text.delete('1.0', END)
            with open(path) as ht:
                for line in ht:
                    self.info_page_text.insert('end', line)

        def find_content(event=False):
            global occurs, entry_content, starting_index, ending_index, offset
            '''+
            some problems that was fixed
            shows only one of its matches
            does
            '''
            print(entry.get())
            occurs = False
            entry_content = entry.get().lower()
            data = self.info_page_text.get('1.0', END).lower()

            # this condition is made to hide to result of blank \ white space characters
            if entry_content and not(entry_content == ' '):
                occurs = data.count(entry_content)
            else:
                occurs = False
                found_label.configure(text='')

            # display the times that the term is in the text
            if occurs:
                found_label.configure(text=f'{str(occurs)} occurrences')
            else:
                found_label.configure(text='0 occurrences')


            untag_all_matches()

            if occurs:
                # Thread(target=place_tags).start()
                starting_index = self.info_page_text.search(entry_content, '1.0', END)
                if starting_index:
                    offset = '+%dc' % len(entry_content)
                    ending_index = starting_index + offset
                    self.info_page_text.tag_add(SEL, starting_index, ending_index)
                    self.info_page_text.tag_add('highlight_all_result', starting_index, ending_index)


        # def place_tags():
        #     more_matches = True
        #     while more_matches:
        #         starting_index = self.info_page_text.search(entry_content, '1.0', END)
        #         if starting_index:
        #             new_st_index = self.info_page_text.search(entry_content, starting_index, END)
        #             starting_index = new_st_index # new addition to fix the problems
        #             offset = '+%dc' % len(entry_content)
        #             ending_index = starting_index + offset
        #             if ending_index == starting_index or ending_index == self.info_page_text.index('end'): # old conditon ending_index == info_page_text.index('end')
        #                 more_matches = False
        #
        #             else:
        #                 self.info_page_text.tag_add('highlight_all_result', starting_index, ending_index)
        #                 starting_index = ending_index

        def tag_all_matches():
            global occurs, starting_index, ending_index
            find_upper()
            for i in range(occurs):
                starting_index = self.info_page_text.search(entry_content, ending_index, END)
                if starting_index:
                    offset = '+%dc' % len(entry_content)
                    ending_index = starting_index + offset
                    print(f'str:{starting_index} end:{ending_index}')
                    self.info_page_text.tag_add('highlight_all_result', starting_index, ending_index)
                    starting_index = ending_index

        def untag_all_matches():
            self.info_page_text.tag_remove('highlight_all_result', 1.0, END)
            self.info_page_text.tag_config('highlight_all_result', background='yellow', foreground='black')


        def find_lower():
            global ending_index, starting_index, occurs
            if int(occurs) > 1:
                    try:
                        starting_index = self.info_page_text.search(entry_content, ending_index, END)
                    except Exception:
                        pass
                    if starting_index and starting_index != "":
                        self.info_page_text.tag_remove('highlight_all_result', '1.0', starting_index)
                        offset = '+%dc' % len(entry_content)
                        ending_index = starting_index + offset
                        print(f'str:{starting_index} end:{ending_index}')
                        self.info_page_text.tag_add('highlight_all_result', starting_index, ending_index)
                        starting_index = ending_index

        def find_upper():
            global ending_index, starting_index, occurs
            if int(occurs) > 1:
                # experimental_ei = f'{starting_index}-{len()}c'
                try:
                    starting_index = self.info_page_text.search(entry_content, '1.0', starting_index)
                except Exception:
                    pass
                if starting_index and starting_index != "":
                    offset = '+%dc' % len(entry_content)
                    ending_index = starting_index + offset
                    self.info_page_text.tag_remove('highlight_all_result', ending_index, END)
                    print(f'str:{starting_index} end:{ending_index}')
                    self.info_page_text.tag_add('highlight_all_result', starting_index, ending_index)
                    ending_index = starting_index

        #
        info_root_frame = Frame(info_root)
        info_root_frame.pack()
        title_frame = Frame(info_root_frame)
        title_frame.pack()
        help_text_scroll = ttk.Scrollbar(info_root_frame)
        # labels
        self.info_page_title = Label(title_frame, text='Help', font='arial 16 bold underline', justify='left',
                                     fg=self.dynamic_text, bg=self.dynamic_bg)
        self.info_page_text = Text(info_root_frame, font='arial 10', borderwidth=3, bg=self.dynamic_bg, state='normal',
                                   yscrollcommand=help_text_scroll.set, relief=RIDGE, wrap=WORD, fg=self.dynamic_text)

        if path == 'patch_notes.txt':
            self.info_page_title.configure(text='Patch notes')

        self.info_page_text.focus_set()
        # add lines
        place_lines()
        self.info_page_text.config(state='disabled')
        # placing
        info_root_frame.pack()
        self.info_page_title.pack(fill=X, anchor=W)
        help_text_scroll.pack(side=RIGHT, fill=Y)
        self.info_page_text.pack(fill=BOTH, expand=True)
        help_text_scroll.config(command=self.info_page_text.yview)

        find_frame = Frame(info_root, relief=FLAT, background='white')
        entry = Entry(find_frame, relief=FLAT, background='SystemButtonFace')
        button_up = Button(find_frame, text='Reset', relief=FLAT, command=find_upper, background='white', bd=1)
        button_down = Button(find_frame, text='↓', relief=FLAT, command=find_lower, background='white', bd=1)
        tag_all_button = Button(find_frame, text='Highlight all', relief=FLAT, command=tag_all_matches, background='white')
        untag_all_button = Button(find_frame, text='Lowlight all', relief=FLAT, command=untag_all_matches, background='white')
        found_label = Label(find_frame, text='', background='white')
        find_frame.pack(side='left')
        entry.grid(row=0, column=0, padx=3, ipady=button_up.winfo_height())
        button_down.grid(row=0, column=1, padx=3)
        button_up.grid(row=0, column=2)
        tag_all_button.grid(row=0, column=3, padx=3)
        untag_all_button.grid(row=0, column=4, padx=3)
        found_label.grid(row=0, column=5, padx=3)
        # entry.configure(height=button_up.winfo_height())

        # place window in the middle of ETE - if it's not too low
        info_root.update_idletasks()
        win_w, win_h = info_root.winfo_width(), info_root.winfo_height()
        ete_x, ete_y = (self.winfo_x()), (self.winfo_y())
        ete_w, ete_h = self.winfo_width(), self.winfo_height()
        mid_x, mid_y = (round(ete_x + (ete_w / 2) - (win_w / 2))), (round(ete_y + (ete_h / 2) - (win_h / 2)))
        # if the window will appear out of bounds, we will jsut change it to the middle of the screen
        # bug if using your second dislay
        if abs(mid_y - self.winfo_screenheight()) <= 80:
            mid_y = (self.winfo_screenheight() // 2)
            print(mid_y)
        info_root.geometry(f'{win_w}x{win_h}+{mid_x}+{mid_y}')
        info_root.resizable(False, False)

        entry.bind('<KeyRelease>', find_content)

    def right_align_language_support(self):
        if self.EgonTE.get('1.0', 'end'):
            lan = polyglot.Text(self.EgonTE.get('1.0', 'end')).language.name
            if lan == 'Arabic' or 'Hebrew' or 'Persian' or 'Pashto' or 'Urdu' or 'Kashmiri' or 'Sindhi':
                self.align_right()

    def search_www(self):
        '''
        this tool is a shortcut for web usage, you can also choose some brower beside the default one,
        and choose session type
        '''
        ser_root = Toplevel()
        ser_root.resizable(False, False)
        ser_root.attributes('-alpha', '0.95')

        def enter():
            if not (str(br_modes.get()) == 'default'):
                if entry_box.get() != '':
                    try:
                        b = webbrowser.get(using=br_modes.get())
                        if entry_box.get() != '':
                            if ser_var.get() == 'current tab':
                                b.open(entry_box.get())
                            else:
                                b.open_new_tab(entry_box.get())
                    except webbrowser.Error:
                        messagebox.showerror(self.title_struct + 'error', 'browser was not found')
                    except IndexError:
                        messagebox.showerror(self.title_struct + 'error', 'internet connection / general problems')
            else:
                if entry_box.get() != '':
                    if str(ser_var.get()) == 'current tab':
                        webbrowser.open(entry_box.get())
                    else:
                        webbrowser.open_new_tab(entry_box.get())

        def copy_from_file():
            if self.is_marked():
                entry_box.insert('end', self.EgonTE.get('sel.first', 'sel.last'))
            else:
                entry_box.insert('end', self.EgonTE.get('1.0', 'end'))

        title = Label(ser_root, text='Search Online', font=self.titles_font)
        entry_box = Entry(ser_root, relief=GROOVE, width=40)
        enter_button = Button(ser_root, relief=FLAT, command=enter, text='Enter')
        from_text_button = Button(ser_root, relief=FLAT, command=copy_from_file, text='Copy from text')

        title.grid(row=0, column=1, padx=10, pady=3)
        entry_box.grid(row=1, column=1, padx=10)
        enter_button.grid(row=2, column=1)
        from_text_button.grid(row=3, column=1, pady=5)

        self.record_list.append(f'> [{self.get_time()}] - Search tool window opened')

        # advance options of the search function
        def adv():
            # ui changes
            adv_button.grid_forget()
            tab_title.grid(row=4, column=0)
            tab_modes.grid(row=5, column=0)
            browser_title.grid(row=4, column=2)
            br_modes.grid(row=5, column=2)

            # browser register to select
            chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'
            webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))

            firefox_path = 'C:/Program Files/Mozilla Firefox/firefox.exe'
            webbrowser.register('firefox', None, webbrowser.BackgroundBrowser(firefox_path))

            opera_path = f'C:/Users/{gethostname()}/AppData/Local/Programs/Opera/opera.exe'
            webbrowser.register('opera', None, webbrowser.BackgroundBrowser(opera_path))

            edge_path = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
            webbrowser.register('edge', None, webbrowser.BackgroundBrowser(edge_path))

        adv_button = Button(ser_root, text='Advance options', command=adv, relief=FLAT)

        tab_title = Label(ser_root, text='Tabs options', font='arial 10 underline')
        ser_var = StringVar()
        tab_modes = ttk.Combobox(ser_root, width=10, textvariable=ser_var, state='readonly')
        tab_modes['values'] = ['current tab', 'new tab']
        tab_modes.current(0)

        browser_title = Label(ser_root, text='Browser options', font='arial 10 underline')
        br_var = StringVar()
        br_modes = ttk.Combobox(ser_root, width=10, textvariable=br_var, state='readonly')
        br_modes['values'] = ['default', 'firefox', 'chrome', 'opera', 'edge']
        br_modes.current(0)

        adv_button.grid(row=4, column=1)

        if self.is_marked():
            entry_box.insert('end', self.EgonTE.get('sel.first', 'sel.last'))

    def advance_options(self):
        '''
        this tool allow you to customize the UI with more option and have also a ton of option regarding many fields
        of the program itself

        UI options:
        6 different cursors: pencil, fleur, xterm, tcross, arrow, crosshair
        3 diffrenet window styles: clam, vista, classic
        3 different reliefs: groove, flat, ridge
        2 night modes: dracula, midnight blue

        In between:
        1. change if the informative labels on the bottom will be shawn (status bar and file bar)
        2. main window transparency (0-90 precent)

        functional options:
        1. speech to text languages
        2. open (when program is starting) last used file
        3. restore saved settings to default
        4. remove newlines and spaces in some text twisters functions
        5. auto save method

        '''
        global tcross_button, arrow_button, crosshair_button, pencil_button, fleur_button, xterm_button
        global style_clam, style_vista, style_classic
        global relief_groove, relief_flat, relief_ridge

        def exit_op():
            self.op_active = ''
            opt_root.destroy()

        def adv_custom_cursor(cursor):
            self.EgonTE.config(cursor=cursor)
            self.data['cursor'] = cursor

            if cursor == 'tcross':
                self.cc.set('tcross')
            elif cursor == 'xterm':
                self.cc.set('xterm')

            try:
                sort_input.config(cursor=cursor)
                self.translate_box.config(cursor=cursor)
                self.translate_resultbox.config(cursor=cursor)
            except BaseException:
                pass
            self.change_button_color('cursors', cursor)
            self.predefined_cursor = cursor
            self.record_list.append(f'> [{self.get_time()}] - Cursor changed to {cursor}')

        def hide_(bar):
            if bar == 'statusbar':
                if self.status_:
                    self.status_bar.pack_forget()
                    self.geometry(f'{self.width}x{self.height - 30}')
                    self.status_ = False
                else:
                    self.status_bar.pack(side=LEFT)
                    self.geometry(f'{self.width}x{self.height - 20}')
                    self.status_ = True
                self.data['status_bar'] = self.status_
            elif bar == 'filebar':
                if self.file_:
                    self.file_bar.pack_forget()
                    self.geometry(f'{self.width}x{self.height - 30}')
                    self.file_ = False
                else:
                    self.file_bar.pack(side=RIGHT)
                    self.geometry(f'{self.width}x{self.height - 20}')
                    self.file_ = True
                self.data['file_bar'] = self.file_
            print(self.status_, self.file_)
            # link to the basic options
            if self.status_ and self.file_:
                self.show_statusbar.set(True)
                self.bars_active = True
            elif not (self.status_ and self.file_):
                self.show_statusbar.set(False)
                self.bars_active = False
            # the elif statement replacing the else one, is because the conditions need to be precise as possible here

        def change_style(style_):
            self.style.theme_use(style_)
            self.change_button_color('styles', style_)
            if style_ == 'vista':
                self.cs.set('vista')
            elif style_ == 'clam':
                self.cs.set('clam')
            self.predefined_style = style_
            self.data['style'] = style_
            self.record_list.append(f'> [{self.get_time()}] - Style changed to {style_}')

        def change_relief(relief_):
            self.EgonTE.config(relief=relief_)
            try:
                sort_input.config(relief=relief_)
                self.translate_box.config(relief=relief_)
                self.translate_resultbox.config(relief=relief_)
            except BaseException:
                pass
            self.change_button_color('relief', relief_)
            self.predefined_relief = relief_
            self.data['relief'] = relief_
            self.record_list.append(f'> [{self.get_time()}] - Relief changed to {relief_}')

        def change_transparency(event=False):
            tranc = int(transparency_config.get()) / 100
            self.attributes('-alpha', tranc)
            self.data['transparency'] = tranc
            self.record_list.append(f'> [{self.get_time()}] - Transparency changed to {tranc}')

        def change_lof():
            if self.lf.get():
                if self.file_name:
                    self.save_last_file()
                else:
                    self.data['open_last_file'] = True

            else:
                self.data['open_last_file'] = ''

        # window creation and some settings
        global opt_root
        opt_root = Toplevel()
        opt_root.resizable(False, False)
        self.op_active = True
        opt_root.protocol('WM_DELETE_WINDOW', exit_op)
        self.usage_time = Label(opt_root)

        def predefined_checkbuttons():
            if self.bars_active:
                self.status_ = True
                self.file_ = False
                self.show_statusbar = BooleanVar()
                self.show_statusbar.set(True)
                self.def_val1.set(1)
                self.def_val2.set(1)
            else:
                self.status_ = False
                self.file_ = False
                self.show_statusbar = BooleanVar()
                self.show_statusbar.set(False)
                self.def_val1.set(0)
                self.def_val2.set(0)

                # the assignment of the builtin boolean values is important to make the file & status bar work well

        def tt_save():
            self.data['text_twisters'] = self.tt_sc.get()

        def nt_save():
            self.data['night_type'] = self.nm_palette.get()

        def restore_defaults():

            if messagebox.askyesno(self.title_struct + 'reset settings',
                                   'Are you sure you want to reset all your current\nand saved settings?'):
                self.data = {'night_mode': False, 'status_bar': True, 'file_bar': True, 'cursor': 'xterm',
                             'style': 'clam',
                             'word_wrap': True, 'reader_mode': False, 'auto_save': True, 'relief': 'ridge',
                             'transparency': 100, 'toolbar': True, 'open_last_file': '', 'text_twisters': False,
                             'night_type': 'black'}

                self.rm.set(self.data['reader_mode'])
                self.bars_active.set(self.data['status_bar'] and self.data['file_bar'])
                self.show_statusbar.set(self.bars_active.get())
                self.status_ = self.data['status_bar']
                self.file_ = self.data['file_bar']
                self.show_toolbar.set(self.data['toolbar'])
                self.night_mode.set(self.data['night_mode'])
                self.tt_sc.set(self.data['text_twisters'])
                self.nm_palette.set(self.data['night_type'])
                self.cs.set(self.data['style'])
                self.cc.set(self.data['cursor'])
                self.ww.set(self.data['word_wrap'])
                self.aus.set(self.data['auto_save'])

                self.bars_active.set(True)
                self.show_statusbar.set(True)
                self.show_toolbar.set(True)
                self.cc.set('xterm')
                self.cs.set('clam')
                self.ww.set(True)
                self.aus.set(True)
                self.rm.set(False)
                self.predefined_cursor = 'xterm'
                self.predefined_style = 'clam'
                self.predefined_relief = 'ridge'

        def stt_key(event=False):
            self.stt_lang_value = self.sr_supported_langs[self.stt_chosen_lang.get()]
            self.record_list.append(f'> [{self.get_time()}] - Speech to text language changed to: {self.stt_lang_value}')

        def autosave_changes():
            if self.autosave_by.get() == 0:
                self.EgonTE.bind('<KeyRelease>', self.auto_save_press)
                self.record_list.append(
                    f'> [{self.get_time()}] - AutoSave methond changed: save by pressing')
            else:
                self.EgonTE.unbind('<KeyRelease>')
                self.record_list.append(
                    f'> [{self.get_time()}] - AutoSave methond changed: save by waiting 30 seconds')


        # default values for the check buttons
        self.def_val1 = IntVar()
        self.def_val2 = IntVar()

        # self.nm_val = IntVar()

        # expreninting with tabs
        settings_tabs = ttk.Notebook(opt_root)
        styles_frame = Frame(settings_tabs)
        functional_frame = Frame(settings_tabs)

        button_width = 8
        font_ = 'arial 10 underline'
        night_frame = Frame(styles_frame)
        bar_frame = Frame(functional_frame)
        predefined_checkbuttons()
        # creating adv-options window UI
        opt_title = Label(opt_root, text='Advance Options', font='calibri 16 bold')
        cursor_title = Label(styles_frame, text='Advance Cursor configuration', font=font_)
        tcross_button = Button(styles_frame, text='tcross', command=lambda: adv_custom_cursor('tcross'), width=button_width)
        arrow_button = Button(styles_frame, text='arrow', command=lambda: adv_custom_cursor('arrow'), width=button_width)
        crosshair_button = Button(styles_frame, text='crosshair',
                                  command=lambda: adv_custom_cursor('crosshair'), width=button_width)
        pencil_button = Button(styles_frame, text='pencil', command=lambda: adv_custom_cursor('pencil'), width=button_width)
        fleur_button = Button(styles_frame, text='fleur', command=lambda: adv_custom_cursor('fleur'), width=button_width)
        xterm_button = Button(styles_frame, text='xterm', command=lambda: adv_custom_cursor('xterm'), width=button_width)
        hide_title = Label(functional_frame, text='Advance hide status & file bar', font=font_)
        filebar_check = Checkbutton(bar_frame, text='filebar', command=lambda: hide_('filebar'), variable=self.def_val1)
        statusbar_check = Checkbutton(bar_frame, text='statusbar', command=lambda: hide_('statusbar'),
                                      variable=self.def_val2)
        style_title = Label(styles_frame, text='Advance style configuration', font=font_)
        style_clam = Button(styles_frame, text='clam', command=lambda: change_style('clam'), width=button_width)
        style_classic = Button(styles_frame, text='classic', command=lambda: change_style('classic'), width=button_width)
        style_vista = Button(styles_frame, text='vista', command=lambda: change_style('vista'), width=button_width)
        relief_title = Label(styles_frame, text='Advance relief configuration', font=font_)
        relief_flat = Button(styles_frame, text='flat', command=lambda: change_relief('flat'), width=button_width)
        relief_ridge = Button(styles_frame, text='ridge', command=lambda: change_relief('ridge'), width=button_width)
        relief_groove = Button(styles_frame, text='groove', command=lambda: change_relief('groove'), width=button_width)

        # the new night mode palettes settings!
        nm_title = Label(styles_frame, text='Choose night mode type', font=font_)
        nm_black_checkbox = Radiobutton(night_frame, text='Dracula', variable=self.nm_palette, value='black',
                                        command=nt_save)
        nm_blue_checkbox = Radiobutton(night_frame, text='MidNight\nBlue', variable=self.nm_palette, value='blue',
                                       command=nt_save)

        stt_title = Label(functional_frame, text='Speech to text language', font=font_)
        stt_lang = ttk.Combobox(functional_frame, width=15, textvariable=self.stt_chosen_lang, state='readonly', style='TCombobox')
        stt_lang['values'] = list(self.sr_supported_langs.keys())

        last_file_title = Label(functional_frame, text='Open the last file you used when starting', font=font_)
        last_file_checkbox = Checkbutton(functional_frame, text='last file setting', variable=self.lf, command=change_lof)

        transparency_title = Label(styles_frame, text='Transparency configuration', font=font_)
        transparency_config = Scale(styles_frame, from_=10, to=100, orient='horizontal', command=change_transparency)
        transparency_config.set(100)
        # transparency_set = Button(styles_frame, text='Change transparency', command=change_transparency)

        title_other = Label(functional_frame, text='Others', font=font_)
        reset_button = Button(functional_frame, text='Restore default', command=restore_defaults)
        tt_checkbox = Checkbutton(functional_frame, text='Text twisters\nremove special characters', variable=self.tt_sc,
                                  command=tt_save)

        auto_save_frame = Frame(functional_frame)
        auto_save_title = Label(functional_frame, text='Auto save method', font=font_)
        by_time_rb = Radiobutton(auto_save_frame, text='By time', variable=self.autosave_by, value=1, command=autosave_changes)
        by_press_rb = Radiobutton(auto_save_frame, text='By pressing', variable=self.autosave_by, value=0, command=autosave_changes)

        # placing all the widgets
        opt_title.pack(pady=5)

        settings_tabs.pack()
        styles_frame.pack(expand=True, fill=BOTH)
        functional_frame.pack(expand=True, fill=BOTH)
        settings_tabs.add(styles_frame, text='Styles')
        settings_tabs.add(functional_frame, text='Functions')

        # styles widgets
        cursor_title.grid(row=1, column=1)
        tcross_button.grid(row=2, column=0, padx=2)
        arrow_button.grid(row=2, column=1)
        crosshair_button.grid(row=2, column=2, padx=2)
        pencil_button.grid(row=3, column=0)
        fleur_button.grid(row=3, column=1)
        xterm_button.grid(row=3, column=2)
        style_title.grid(row=4, column=1)
        style_clam.grid(row=5, column=0)
        style_classic.grid(row=5, column=1)
        style_vista.grid(row=5, column=2)
        relief_title.grid(row=6, column=1)
        relief_flat.grid(row=7, column=0)
        relief_ridge.grid(row=7, column=1)
        relief_groove.grid(row=7, column=2, pady=3)
        nm_title.grid(row=8, column=1)
        night_frame.grid(row=9, column=1)
        nm_black_checkbox.grid(row=1, column=0)
        nm_blue_checkbox.grid(row=1, column=2)
        transparency_title.grid(row=10, column=1)
        transparency_config.grid(row=11, column=1)
        # transparency_set.grid(row=12, column=1)

        # functional widgets
        hide_title.pack()
        bar_frame.pack()
        filebar_check.grid(row=1, column=0)
        statusbar_check.grid(row=1, column=2)
        stt_title.pack()
        stt_lang.pack()
        last_file_title.pack()
        last_file_checkbox.pack()
        title_other.pack()
        reset_button.pack()
        tt_checkbox.pack()
        auto_save_title.pack()
        auto_save_frame.pack()
        by_time_rb.grid(row=0, column=0)
        by_press_rb.grid(row=0, column=2)


        self.usage_time.pack()
        # creating buttons list
        self.adv_cursor_bs = tcross_button, arrow_button, crosshair_button, pencil_button, fleur_button, xterm_button
        self.adv_style_bs = style_clam, style_vista, style_classic
        self.adv_reliefs_bs = relief_groove, relief_flat, relief_ridge
        # change button colors
        if self.predefined_cursor or self.predefined_style or self.predefined_relief:
            self.change_button_color('cursors', self.predefined_cursor)
            self.change_button_color('styles', self.predefined_style)
            self.change_button_color('relief', self.predefined_relief)

        stt_lang.bind('<<ComboboxSelected>>', stt_key)

        self.record_list.append(f'> [{self.get_time()}] - advanced option window opened')

    def change_button_color(self, button_family, button):
        '''
        changes the colors of the buttons that are related to the customization of the program,
        to emphasize the choosen option
        light - not active
        light grey - active

        :param button_family:
        :param button:
        '''
        if self.op_active:
            if button_family == 'cursors':
                for adv_cursor_b in self.adv_cursor_bs:
                    adv_cursor_b.config(bg='SystemButtonFace')
                if button == 'arrow':
                    arrow_button.config(bg='grey')
                elif button == 'tcross':
                    tcross_button.config(bg='grey')
                elif button == 'fleur':
                    fleur_button.config(bg='grey')
                elif button == 'pencil':
                    pencil_button.config(bg='grey')
                elif button == 'crosshair':
                    crosshair_button.config(bg='grey')
                elif button == 'xterm':
                    xterm_button.config(bg='grey')
            elif button_family == 'styles':
                for adv_style_b in self.adv_style_bs:
                    adv_style_b.config(bg='SystemButtonFace')
                if button == 'clam':
                    style_clam.config(bg='grey')
                elif button == 'vista':
                    style_vista.config(bg='grey')
                elif button == 'classic':
                    style_classic.config(bg='grey')
            elif button_family == 'relief':
                for adv_reliefs_b in self.adv_reliefs_bs:
                    adv_reliefs_b.config(bg='SystemButtonFace')
                if button == 'ridge':
                    relief_ridge.config(bg='grey')
                elif button == 'groove':
                    relief_groove.config(bg='grey')
                elif button == 'flat':
                    relief_flat.config(bg='grey')

    def goto(self, event=None):
        '''
        this function will point you to the word that you typed (if its exists)
        '''

        def enter():
            word = goto_input.get()
            starting_index = self.EgonTE.search(word, '1.0', END)
            offset = '+%dc' % len(word)
            if starting_index:
                ending_index = starting_index + offset
                index = self.EgonTE.search(word, ending_index, END)
            self.EgonTE.mark_set('insert', ending_index)
            self.EgonTE.focus_set()

        # window creation
        goto_root = Toplevel()
        goto_root.resizable(False, False)
        # UI components
        goto_text = Label(goto_root, text='Enter the word that you wish to go to:', font='arial 10 underline')
        goto_input = Entry(goto_root, width=20)
        goto_button = Button(goto_root, text='Go to', pady=3, command=enter)
        goto_text.grid(row=0, sticky=NSEW, column=0, padx=3)
        goto_input.grid(row=3, column=0)
        goto_button.grid(row=4, column=0, pady=5)

    def sort(self):
        '''
        this function sorts the input you put in it with ascending and descending orders,
        and if you put characters it will use their ASCII values
        '''
        global mode_, sort_data_sorted, str_loop, sort_rot, sort_input

        def sort_():
            global mode_, sort_data_sorted, str_loop
            sort_data = sort_input.get('1.0', 'end')
            sort_data_sorted = (sorted(sort_data))
            sort_input.delete('1.0', 'end')
            if mode_ == 'dec':
                for num in range(str_loop, len(sort_data_sorted) - end_loop, 1):
                    sort_input.insert('insert linestart', f'{sort_data_sorted[num]}')
            else:
                for num in range(str_loop, len(sort_data_sorted) - end_loop, 1):
                    sort_input.insert('insert lineend', f'{sort_data_sorted[num]}')

        def mode():
            global mode_, str_loop, end_loop
            if mode_ == 'asc':
                mode_ = 'dec'
                mode_button.config(text='Mode: descending')
                str_loop = 0
                end_loop = 1
            else:
                mode_ = 'asc'
                mode_button.config(text='Mode: ascending')
                str_loop = 1
                end_loop = 0

        def enter():
            for character in list(str(sort_input.get('1.0', 'end'))):
                if str(character).isdigit():
                    self.EgonTE.insert(self.get_pos(), sort_input.get('1.0', 'end'))
                    break

        # window creation
        sort_root = Toplevel()
        sort_root.resizable(False, False)
        sort_root.attributes('-alpha', '0.95')
        # variables
        mode_ = 'asc'
        str_loop = 1
        end_loop = 0
        # UI components
        sort_frame = Frame(sort_root)
        sort_scroll = ttk.Scrollbar(sort_frame)
        sort_text = Label(sort_root, text='Enter the numbers/characters you wish to sort:', font='arial 10 bold')
        sort_input = Text(sort_frame, width=30, height=15, yscrollcommand=sort_scroll.set, wrap=WORD,
                          cursor=self.predefined_cursor, relief=self.predefined_relief)

        sort_button = Button(sort_root, text='Sort', command=sort_)
        mode_button = Button(sort_root, text='Mode: ascending', command=mode)
        sort_insert = Button(sort_root, text='Insert', command=enter)
        sort_text.pack(fill=X, anchor=W, padx=3)
        sort_frame.pack(pady=3)
        sort_scroll.pack(side=RIGHT, fill=Y)
        sort_input.pack(fill=BOTH, expand=True)
        sort_scroll.config(command=sort_input.yview)
        sort_button.pack(pady=2)
        mode_button.pack(pady=2)
        sort_insert.pack(pady=2)

    def knowledge_window(self, mode):
        '''
        the window for the dictionary and wikipedia tools
        '''

        def search():
            meaning_box.configure(state=NORMAL)
            paste_b.configure(state=DISABLED)
            output_ready = True
            if mode == 'dict':
                try:
                    dict_ = PyDictionary()
                    self.def_ = dict_.meaning(par_entry.get())
                    meaning_box.delete('1.0', 'end')
                    for key, value in self.def_.items():
                        meaning_box.insert(END, key + '\n\n')
                        for values in value:
                            meaning_box.insert(END, f'-{values}\n\n')
                except AttributeError:
                    messagebox.showerror(self.title_struct + 'error', 'check your internet / your search!')
                    output_ready = False
            else:
                try:
                    if self.wiki_var.get() == 1:
                        wiki_ = summary(par_entry.get())
                    elif self.wiki_var.get() == 2:
                        arcticles = wiki_search(par_entry.get())
                        arcticles = list(arcticles)
                        if arcticles:
                            meaning_box.delete('1.0', 'end')
                            for line, article in enumerate(arcticles):
                                meaning_box.insert(f'{line}.0', article + '\n')
                        else:
                            output_ready = False
                    elif self.wiki_var.get() == 3:
                        wiki_page = page(par_entry.get())
                        wiki_ = f'{wiki_page.title}\n{wiki_page.content}'
                    elif self.wiki_var.get() == 4:
                        wiki_page = page(par_entry.get())
                        wiki_ = wiki_page.images

                    if not (self.wiki_var.get() == 2):
                        meaning_box.delete('1.0', 'end')
                        meaning_box.insert('1.0', wiki_)
                except requests.exceptions.ConnectionError:
                    messagebox.showerror(self.title_struct + 'error', 'check your internet connection')
                    output_ready = False
                except exceptions.DisambiguationError:
                    messagebox.showerror(self.title_struct + 'error', 'check your searched term')
                    output_ready = False
                except exceptions.PageError:
                    messagebox.showerror(self.title_struct + 'error', 'Invalid page ID')
                    output_ready = False

            if output_ready:
                paste_b.configure(state=ACTIVE)
            else:
                paste_b.configure(state=DISABLED)
            meaning_box.configure(state=DISABLED)

        def paste():
            content_to_paste = meaning_box.get('1.0', 'end')
            self.EgonTE.insert(self.get_pos(), content_to_paste)

        par_root = Toplevel()
        par_root.resizable(False, False)
        par_root.attributes('-alpha', '0.95')
        par_entry = Entry(par_root, width=35)
        par_search = Button(par_root, text='Search definition', command=search)
        if mode == 'wiki':
            par_search.configure(text='Search - Wikipedia')
        meaning_box = Text(par_root, height=15, width=50, wrap=WORD)
        meaning_box.configure(state=DISABLED)
        paste_b = Button(par_root, text='Paste to ETE', command=paste)
        paste_b.configure(state=DISABLED)

        par_entry.grid(row=1, column=1, pady=3)
        par_search.grid(row=2, column=1, pady=3)
        meaning_box.grid(row=3, column=1)
        paste_b.grid(row=6, column=1)

        if mode == 'wiki':
            radio_frame = Frame(par_root)
            return_summery = Radiobutton(radio_frame, text='Summery', variable=self.wiki_var, value=1)
            return_related_articles = Radiobutton(radio_frame, text='Related articles', variable=self.wiki_var, value=2)
            return_content = Radiobutton(radio_frame, text='Content', variable=self.wiki_var, value=3)
            return_images = Radiobutton(radio_frame, text='Images', variable=self.wiki_var, value=4)

            radio_frame.grid(row=4, column=1)

            return_summery.grid(row=0, column=0)
            return_related_articles.grid(row=0, column=2)
            return_content.grid(row=1, column=0)
            return_images.grid(row=1, column=2)

        if mode == 'wiki':
            self.record_list.append(f'> [{self.get_time()}] - Wikipedia tool window opened')
        else:
            self.record_list.append(f'> [{self.get_time()}] - Dictionary tool window opened')

    def virtual_keyboard(self):
        '''
        virtual keyboard tool, that have most of the important functionalities:
        tab, symbols, caps, numbers, and english characters in the qwert organization
        '''

        def close():
            keyboard_root.destroy()
            self.vk_active = False

        global last_abc
        # window creation and settings
        keyboard_root = Toplevel()
        keyboard_root.attributes('-alpha', '0.90')
        keyboard_root.resizable(False, False)
        keyboard_root.configure(bg='black')
        keyboard_root.protocol("WM_DELETE_WINDOW", close)
        self.vk_active = True
        sym_n = ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
                 '+', '-', '*', '^', '=', '<', '>', '[', ']',
                 '#', '!', '&', '*', ':', '/', '~')

        ### unused: '`' '_' '|' '$'

        last_abc = 'upper'
        exp = ' '  # global variable

        def press(num):
            global exp
            self.EgonTE.insert(self.get_pos(), num)

        def tab():
            exp = '    '
            self.EgonTE.insert(self.get_pos(), exp)

        def modes(mode):
            global last_abc
            modes_buttons = caps, sym_button

            if not (self.night_mode):
                if self.nm_palette.get() == 'black':
                    highlighted_color = '#042f42'
                else:
                    highlighted_color = '#051d29'
            else:
                highlighted_color = 'light grey'

            for mode_button in modes_buttons:
                mode_button.configure(bg=self.dynamic_button)

            if mode == 'upper' or mode == 'lower':
                last_abc = mode
                sym_button.configure(command=lambda: modes('sym'), text='1!*')

            if mode == 'upper':
                for asc in range(len(ascii_uppercase)):
                    characters[asc].configure(text=ascii_uppercase[asc],
                                              command=lambda i=asc: press(ascii_uppercase[i]))
                    caps.configure(command=lambda: modes('lower'))
                    caps.configure(bg=highlighted_color)
            elif mode == 'lower':
                for asc in range(len(ascii_lowercase)):
                    characters[asc].configure(text=ascii_lowercase[asc],
                                              command=lambda i=asc: press(ascii_lowercase[i]))
                    caps.configure(command=lambda: modes('upper'))
            elif mode == 'sym':
                for counter, sn in enumerate(sym_n):
                    characters_by_order[counter].configure(text=sn,
                                                           command=lambda i=sn: press(i))
                sym_button.configure(command=lambda: modes('abc'), text='ABC')
                sym_button.configure(bg=highlighted_color)
            else:
                sym_button.configure(command=lambda: modes('sym'), text='1!*')
                modes(last_abc)

        btn_frame = Frame(keyboard_root)
        extras_frame = Frame(keyboard_root)
        btn_frame.pack()
        extras_frame.pack()

        Q = Button(btn_frame, text='Q', width=6, command=lambda: press('Q'))
        Q.grid(row=1, column=0, ipady=10)

        W = Button(btn_frame, text='W', width=6, command=lambda: press('W'))
        W.grid(row=1, column=1, ipady=10)

        E = Button(btn_frame, text='E', width=6, command=lambda: press('E'))
        E.grid(row=1, column=2, ipady=10)

        R = Button(btn_frame, text='R', width=6, command=lambda: press('R'))
        R.grid(row=1, column=3, ipady=10)

        T = Button(btn_frame, text='T', width=6, command=lambda: press('T'))
        T.grid(row=1, column=4, ipady=10)

        Y = Button(btn_frame, text='Y', width=6, command=lambda: press('Y'))
        Y.grid(row=1, column=5, ipady=10)

        U = Button(btn_frame, text='U', width=6, command=lambda: press('U'))
        U.grid(row=1, column=6, ipady=10)

        I = Button(btn_frame, text='I', width=6, command=lambda: press('I'))
        I.grid(row=1, column=7, ipady=10)

        O = Button(btn_frame, text='O', width=6, command=lambda: press('O'))
        O.grid(row=1, column=8, ipady=10)

        P = Button(btn_frame, text='P', width=6, command=lambda: press('P'))
        P.grid(row=1, column=9, ipady=10)

        cur = Button(btn_frame, text='{', width=6, command=lambda: press('{'))
        cur.grid(row=1, column=10, ipady=10)

        cur_c = Button(btn_frame, text='}', width=6, command=lambda: press('}'))
        cur_c.grid(row=1, column=11, ipady=10)

        back_slash = Button(btn_frame, text='\\', width=6, command=lambda: press('\\'))
        back_slash.grid(row=1, column=10, ipady=10)

        A = Button(btn_frame, text='A', width=6, command=lambda: press('A'))
        A.grid(row=2, column=0, ipady=10)

        S = Button(btn_frame, text='S', width=6, command=lambda: press('S'))
        S.grid(row=2, column=1, ipady=10)

        D = Button(btn_frame, text='D', width=6, command=lambda: press('D'))
        D.grid(row=2, column=2, ipady=10)

        F = Button(btn_frame, text='F', width=6, command=lambda: press('F'))
        F.grid(row=2, column=3, ipady=10)

        G = Button(btn_frame, text='G', width=6, command=lambda: press('G'))
        G.grid(row=2, column=4, ipady=10)

        H = Button(btn_frame, text='H', width=6, command=lambda: press('H'))
        H.grid(row=2, column=5, ipady=10)

        J = Button(btn_frame, text='J', width=6, command=lambda: press('J'))
        J.grid(row=2, column=6, ipady=10)

        K = Button(btn_frame, text='K', width=6, command=lambda: press('K'))
        K.grid(row=2, column=7, ipady=10)

        L = Button(btn_frame, text='L', width=6, command=lambda: press('L'))
        L.grid(row=2, column=8, ipady=10)

        semi_co = Button(btn_frame, text=';', width=6, command=lambda: press(';'))
        semi_co.grid(row=2, column=9, ipady=10)

        d_colon = Button(btn_frame, text='"', width=6, command=lambda: press('"'))
        d_colon.grid(row=2, column=10, ipady=10)

        Z = Button(btn_frame, text='Z', width=6, command=lambda: press('Z'))
        Z.grid(row=3, column=0, ipady=10)

        X = Button(btn_frame, text='X', width=6, command=lambda: press('X'))
        X.grid(row=3, column=1, ipady=10)

        C = Button(btn_frame, text='C', width=6, command=lambda: press('C'))
        C.grid(row=3, column=2, ipady=10)

        V = Button(btn_frame, text='V', width=6, command=lambda: press('V'))
        V.grid(row=3, column=3, ipady=10)

        B = Button(btn_frame, text='B', width=6, command=lambda: press('B'))
        B.grid(row=3, column=4, ipady=10)

        N = Button(btn_frame, text='N', width=6, command=lambda: press('N'))
        N.grid(row=3, column=5, ipady=10)

        M = Button(btn_frame, text='M', width=6, command=lambda: press('M'))
        M.grid(row=3, column=6, ipady=10)

        left = Button(btn_frame, text='<', width=6, command=lambda: press('<'))
        left.grid(row=3, column=7, ipady=10)

        right = Button(btn_frame, text='>', width=6, command=lambda: press('>'))
        right.grid(row=3, column=8, ipady=10)

        slas = Button(btn_frame, text='/', width=6, command=lambda: press('/'))
        slas.grid(row=3, column=9, ipady=10)

        q_mark = Button(btn_frame, text='?', width=6, command=lambda: press('?'))
        q_mark.grid(row=3, column=10, ipady=10)

        coma = Button(btn_frame, text=',', width=6, command=lambda: press(','))
        coma.grid(row=3, column=11, ipady=10)

        dot = Button(btn_frame, text='.', width=6, command=lambda: press('.'))
        dot.grid(row=2, column=11, ipady=10)

        space = Button(extras_frame, text='Space', width=6, command=lambda: press(' '))
        space.grid(row=0, column=1, ipadx=156, ipady=10)

        open_b = Button(extras_frame, text='(', width=6, command=lambda: press('('))
        open_b.grid(row=0, column=2, ipady=10)

        close_b = Button(extras_frame, text=')', width=6, command=lambda: press(')'))
        close_b.grid(row=0, column=3, ipady=10)

        tab = Button(extras_frame, text='Tab', width=6, command=tab)
        tab.grid(row=0, column=4, ipady=10)

        caps = Button(extras_frame, text='Caps', width=6, command=lambda: modes('lower'), background='light grey')
        caps.grid(row=0, column=5, ipady=10)

        sym_button = Button(extras_frame, text='1!*', width=6, command=lambda: modes('sym'))
        sym_button.grid(row=0, column=6, ipady=10)

        self.record_list.append(f'> [{self.get_time()}] - Virtual Keyboard tool window opened')

        characters = A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z
        characters_by_order = Q, W, E, R, T, Y, U, I, O, P, A, S, D, F, G, H, J, K, L, Z, X, C, V, B, N, M
        symbols = semi_co, cur, cur_c, back_slash, d_colon, left, right, slas, q_mark, coma, dot, open_b, close_b
        functional_buttons = space, tab, caps, sym_button
        self.all_vk_buttons = characters_by_order + symbols + functional_buttons

        for vk_btn in self.all_vk_buttons:
            vk_btn.config(bg=self.dynamic_button, fg=self.dynamic_text)

        keyboard_root.update_idletasks()
        win_w, win_h = keyboard_root.winfo_width(), keyboard_root.winfo_height()
        ete_x, ete_y = (self.winfo_x()), (self.winfo_y())
        ete_w, ete_h = self.winfo_width(), self.winfo_height()
        mid_x, mid_y = round(ete_x + (ete_w / 2) - (win_w / 2)), (round((ete_h) + ete_y - win_h))
        if abs(mid_y - self.winfo_screenheight()) <= 80:
            mid_y = self.winfo_screenheight() // 2
        keyboard_root.geometry(f'{win_w}x{win_h}+{mid_x}+{mid_y}')
        keyboard_root.resizable(False, False)

        modes('lower')

        keyboard_root.mainloop()  # using ending point

    def emoji_detection(self, event=None, via_settings=False, reverse=False):
        'detects emojis and replaces their identification mark with the emoji itself'
        # initial condition to not activate the function every interaction with the text box
        # peruse: not cause lag and prevent bugs
        active = False
        if via_settings:
            active = True
        elif active == False:
            keys = list(map(str, printable[:-22]))

            for key in keys:

                if is_pressed(key):
                    active = True
                    break
            if active == False:
                for key in keys:
                    try:
                        if key == self.EgonTE.get(1.0, self.EgonTE.index(CURRENT))[-1]:
                            active = True
                            break
                    except IndexError:
                        pass

        if active:
            if self.aed.get() or via_settings:
                fail_msg = ''
                lang = self.get_k_lang()[1]
                if not lang:
                    lang = 'en'
                print(lang)

                content = self.EgonTE.get(1.0, END).split(' ')
                print(content)
                new_content = []
                indexes = []
                rep_nl = False
                for index, word in enumerate(content):
                    if word != ' ' and word != '' and word != '\n':
                        # to make the detection more precise
                        if '\n' in word:
                            nl_index = word.find('\n')
                            word = word.replace('\n', '')
                            rep_nl = True
                        else:
                            rep_nl = False
                        if '\t' in word:
                            t_index = word.find('\t')
                            word = word.replace('\t', '')
                            rep_t = True
                        else:
                            rep_t = False

                        if reverse:
                            word = emoji.demojize(word, language=lang)
                        else:
                            word = emoji.emojize(word, language=lang)
                            indexes.append(index)

                    # detecting if word is emoji - only if it is the text will be replaced
                    if emoji.is_emoji(word):
                        replace_text = True
                        fail_msg = False
                        # a message for the manual use of the function about the result - positive
                        if via_settings:
                            messagebox.showinfo('EgonTE', 'emoji(s) found!')

                    else:
                        fail_msg = True
                        replace_text = False

                    # returning the character after it doesn't bother the detecting process
                    if rep_nl:
                        word = f'{word[:nl_index]}\n{word[nl_index:]}'
                    if rep_t:
                        word = f'{word[:t_index]}\t{word[t_index:]}'

                    new_content.append(word)

                # a message for the manual use of the function about the result - negative
                if fail_msg and via_settings:
                    messagebox.showinfo('EgonTE', 'emoji(s) didn\'t found!')

                # replacing text with a condition - to not spam it
                if replace_text:
                    new_content = ' '.join(new_content)
                    self.EgonTE.delete('1.0', 'end')
                    self.EgonTE.insert('end', new_content)

                # if the usage of the function is manual - it automatically will insert a space character after the emoji
                if via_settings:
                    self.EgonTE.insert(self.get_pos(), ' ')

    def e_list(self, mode):
        '''
        window that can show a formmated list of emojis, morse code, and roman numbers dependent on the function's parameter
        '''
        extra = ''

        if mode == 'emojis':
            ejc_list = emoji.get_emoji_unicode_dict('en')
        elif mode == 'morse':
            ejc_list = morse_code_dict
        elif mode == 'roman':
            ejc_list = (dict(islice(self.roman_dict.items(), 7)))

            extra = {}
            for key, value in self.roman_dict.items():
                if key not in ejc_list.keys():
                    extra[key] = value

        e_root = Toplevel()
        e_root.title(f'{self.title_struct}{mode} list')

        scroll = ttk.Scrollbar(e_root)
        sym_label = Text(e_root, yscrollcommand=scroll.set, cursor=self.predefined_cursor,
                         relief=self.predefined_relief)

        for sym_, sym_code_ in ejc_list.items():
            sym_label.insert('end', f'{sym_} - {sym_code_}\n')

        if extra:
            sym_label.insert('end', '\n')

            # roman extras is cobinitions of letters that form uniqe numbers when they are together!
            if mode == 'roman':
                sym_label.insert('end', 'popular combinations')

            sym_label.insert('end', '\n')

            for sym_, sym_code_ in extra.items():
                sym_label.insert('end', f'{sym_} - {sym_code_}\n')

        sym_label.configure(state=DISABLED)
        scroll.pack(side=RIGHT, fill=Y)
        sym_label.pack(fill=BOTH, expand=True)
        scroll.config(command=sym_label.yview)

    def file_info(self):
        '''
        basic and general statisics of any file, work on the file youre running in the program - and if you dont use
        a saved file it will ask for another file location
        '''
        res_font = 'consolas 14'

        if self.file_name:
            file_info_name = self.file_name

        else:
            file_info_name = filedialog.askopenfilename(title='Open file to get info about',
                                                        filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html'),
                                                                   ('Python Files', '*.py')))

        try:
            stat = os.stat(file_info_name)
            # getting the actual file info
            file_size = os.path.getsize(file_info_name)

            if system().lower() == 'windows':
                creation_time = datetime.fromtimestamp((os.path.getctime(file_info_name)))
                modified_time = datetime.fromtimestamp((os.path.getmtime(file_info_name)))
            else:
                try:
                    creation_time = stat.st_birthtime
                    modified_time = stat.st_mtime
                except AttributeError:
                    pass

            # creating the window
            root = Toplevel()
            root.title(self.title_struct + 'File information')
            root.resizable(False, False)
            # creating the widgets
            access_time = datetime.fromtimestamp(stat.st_atime)
            file_type = os.path.splitext(file_info_name)[-1][1:]
            lib_path = Path(file_info_name)
            try:
                owner = f'{lib_path.owner()} : {lib_path.group()}'
            except:
                owner = ''
            # attaching info to labels
            size_label = Label(root, text=f'file size - {file_size} bytes', font=res_font)
            modified_time_label = Label(root, text=f'file modified time - {modified_time}', font=res_font)
            creation_time_label = Label(root, text=f'file creation time - {creation_time}', font=res_font)
            access_time_label = Label(root, text=f'file accessed time - {access_time}', font=res_font)
            file_type_label = Label(root, text=f'file type - {file_type}', font=res_font)
            if owner:
                owner_label = Label(root, text=f'file owner - {owner}', font=res_font)

            size_label.pack(expand=True)
            modified_time_label.pack(expand=True)
            creation_time_label.pack(expand=True)
            access_time_label.pack(expand=True)
            file_type_label.pack(expand=True)
            if owner:
                owner_label.pack(expand=True)

        except NameError:
            messagebox.showerror(self.title_struct + 'error', 'you aren\'nt using a file!')
        except PermissionError:
            messagebox.showerror(self.title_struct + 'error', 'you are not using a file!')

        self.record_list.append(f'> [{self.get_time()}] - File\'s Info tool window opened')

    def auto_save_time(self):
        if self.autosave_by.get() == 1:
            t = 300
            while self.aus.get():
                while t:
                    mins, secs = divmod(t, 60)
                    timer = '{:02d}:{:02d}'.format(mins, secs)
                    time.sleep(1)
                    t -= 1
                if self.file_name:
                    self.save()
        else:
            if self.file_name:
                self.save()
        # Thread(target=self.auto_save()).start()

    def auto_save_press(self, event=False):
        if self.file_name and self.aus.get() and self.autosave_by.get() == 0:
            self.save()

    def auto_lists(self):
        '''
        W.I.P fucnction that the vision with it is to make that if you write any kind of something that organizes
        the content like a list (numeric, dotted) it will automaticly will write the next kind of this item
        in the next line
        '''
        if self.aul:
            # boolean variables to identify if there is a list
            numeric_list = False
            dotted_list = False
            indexes = []
            content = self.EgonTE.get('1.0', 'end').split(' ')
            numerics = []
            numerics_iterate = [numerics.append(f'{i}.') for i in range(100)]
            # checking if there are list's key components in the text
            for num in numerics:
                if num in content:
                    numeric_list = True
                    last_num = int(num)
            if '*' in content:
                dotted_list = True
            # first steps if key components are found
            if numeric_list and dotted_list:
                pass
            elif numeric_list:
                list_prefix = str(last_num + 1)
            elif dotted_list:
                list_prefix = '*'
            insert_indexes = list(''.join(int(indexes[0]) + 1), indexes[1])
            # checking to not duplicate existing lists
            if self.EgonTE.index(insert_indexes[0] + 1) == list_prefix:
                self.EgonTE.insert(insert_indexes, list_prefix)

    def compare(self):
        '''
        function that is comparing the file that you are using to other selected file from your computer,
        in a plain way - basic numeric statstic and content difference
        '''
        file_content = self.EgonTE.get('1.0', 'end').splitlines()
        another_file = filedialog.askopenfilename(initialdir=os.getcwd(), title='Open file to compare',
                                                  filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html'),
                                                             ('Python Files', '*.py')))
        if another_file:
            try:
                another_file = open(another_file, 'r')
                another_fc = another_file.read()
                # warning about possible lag
                if len(another_fc) > 400:
                    if not (
                    messagebox.askyesno('EgonTE', 'This file is pretty big\nare you sure you want to compere it?')):
                        compare_root.destroy()
                        return
                # window creation
                compare_root = Toplevel()
                compare_root.title(self.title_struct + '2 files compression')
                # the precise diffrence in content between files with the Differ function
                difference = Differ()
                c_diffrence_frame = Frame(compare_root)
                c_difference_title = Label(c_diffrence_frame, text='Content diffrence', font='arial 14 underline')
                files_diffrence = ''.join(difference.compare(file_content, another_fc))
                content_diffrence = Label(c_diffrence_frame, text=files_diffrence, font='arial 12')

                # the diffrence in the count of : words, lines, characters, spaces
                def counts_file(file):
                    num_words = 0
                    num_lines = 0
                    num_charc = 0
                    num_spaces = 0
                    for line in file:
                        num_lines += 1
                        word = 'Y'
                        for letter in line:
                            if (letter != ' ' and word == 'Y'):
                                num_words += 1
                                word = 'N'
                            elif (letter == ' '):
                                num_spaces += 1
                                word = 'Y'
                            for i in letter:
                                if (i != ' ' and i != '\n'):
                                    num_charc += 1
                    formatted_count = f'number of words: {num_words}\nnumber of lines: {num_lines}\n' \
                                      f'number of characters: {num_charc}\nnumber of spaces: {num_spaces}'
                    return formatted_count

                count_frame = Frame(compare_root)
                file_1_frame = Frame(count_frame, bd=1, relief='groove')
                file_2_frame = Frame(count_frame, bd=1, relief='groove')
                file_counts_title = Label(count_frame, text='File stats', font='arial 14 underline')
                fc_title1 = Label(file_1_frame, text='Your first file', font='arial 10 underline')
                fc_title2 = Label(file_2_frame, text='Your second file', font='arial 10 underline')
                file_1_count = Label(file_1_frame, text=counts_file(file_content))
                file_2_count = Label(file_2_frame, text=counts_file(another_fc))

                c_diffrence_frame.pack()
                c_difference_title.pack()
                content_diffrence.pack(expand=True, fill=BOTH)

                count_frame.pack(expand=True, fill=BOTH)
                file_counts_title.grid(row=0, column=1)
                file_1_frame.grid(row=1, column=0)
                file_2_frame.grid(row=1, column=2)

                fc_title1.pack(expand=True, fill=BOTH)
                fc_title2.pack(expand=True, fill=BOTH)
                file_1_count.pack(expand=True, fill=BOTH)
                file_2_count.pack(expand=True, fill=BOTH)

                another_file.close()

            except UnicodeDecodeError:
                messagebox.showerror(self.title_struct + 'error', 'unsupported characters')
                compare_root.destroy()

        self.record_list.append(f'> [{self.get_time()}] - File\'s comparison tool window opened')

    def corrector(self):
        content = self.EgonTE.get('1.0', 'end')
        corrected_content = TextBlob(content).correct()
        self.EgonTE.delete('1.0', 'end')
        self.EgonTE.insert('1.0', corrected_content)

    def organize(self):
        '''
        (not for the developer) need to remake this function
        '''

        split_word = False
        # split special characters a new index for themself - try to seek answer in content's stats
        content = self.EgonTE.get('1.0', 'end').split()
        special_characters = printable[62:]
        print(special_characters)
        content_phase_1 = []
        for word in content:
            for character in special_characters:
                if character in word:
                    split_word = True
                    break

            if not (split_word):
                print('if')
                content_phase_1.append(word)
            else:
                print('else')
                for character in special_characters:
                    # for line in all_lines:
                    if character in word:
                        content_phase_1.extend([e + character for e in word.split(character) if e])

        print(content_phase_1)

        content_phase_2 = []
        for word in content:
            print(0)
            print(word)
            if word.isalpha():  # first problem
                print('1')
                if reSearch('\w*[A-Z]\w*[A-Z]\w*', word):
                    words = findall('[A-Z][^A-Z]*', word)
                    print('word' + words)
                    if words in words.words():
                        print('hi')
                        content_phase_2.extend(words)
                        continue
            content_phase_2.append(word)

        print(content_phase_2)

        # content = content.split(' ')
        # part 1: separate connected words (identifying via capital letters)
        words = findall('[A-Z][a-z]*', content)
        print(words)

        # Change first letter of each word into lower case words[0] = words[0][0].capitalize()
        for i in range(0, len(words)):
            # need to add a condition
            if findall('^[A-Z]', content):
                words[i] = words[i][0].capitalize() + words[i][1:]  # lower() ?
        corrected_content = (''.join(words))

        print(corrected_content)

        # part 2: make capital letters

        # pattern = '[A-Z]+[a-z]+$'
        # searching pattern
        # if not(reSearch(pattern, corrected_content)):
        #     pass # change it to capital letter
        # corrected_list = list(corrected_content.words)
        # if isinstance(corrected_list[0], str):
        #     corrected_list = corrected_list[0].captilaize()

        # print(type(corrected_content))
        # pattern = findall('\\b[a-zA-Z]', corrected_content)
        # for i in range(0, len(pattern)):
        #     pattern[0] = pattern[0].capitalize()
        # corrected_content = (' '.join(pattern))

        self.EgonTE.delete('1.0', 'end')
        self.EgonTE.insert('1.0', corrected_content)

    def web_scrapping(self):
        '''
        web scrapping tool allows you to scrape a website, your workspace, and a local file.
        the return types are: all, text and attributes
        you can filter more precisely with specific classes and attributes
        '''
        global chosen_init
        sub_titles_font = 'arial 12 underline'
        return_type = StringVar()
        return_type.set('text')
        connection = True
        file_via_internet = False
        limit = None
        self.wbs_auto_update = False
        self.pre_bd_this, self.pre_bd_link, self.pre_bd_file = 1, 1, 1
        chosen_init = 'link'

        def ex(subject):
            if subject == 'tag':
                explenation = 'HTML tags are simple instructions that tell a web browser how to format text'
                example = '<b> Bold Tag </b>'
            else:
                explenation = 'The HTML class attribute is used to specify a class for an HTML element'
                example = '<p class="ThisIsAClassName">HI</p>'

            messagebox.showinfo(self.title_struct + 'web scrapping',
                                f'Explenation:\n{explenation}.\nExample:\n{example}')

        def get_html_web():
            try:
                web_url = urllib.request.Request(self.wbs_path, headers={'User-Agent': 'Mozilla/5.0'})
                content = urllib.request.urlopen(web_url).read()
                return content
            except urllib.error.HTTPError as e:
                messagebox.showerror(self.title_struct + 'error', str(e))

        def comb_upload(via, initial_ws=False):
            global file_via_internet, connection, response, chosen_init, title_text
            file_ready = False

            bd_list = [self.pre_bd_file, self.pre_bd_link, self.pre_bd_this]

            for pre_bd in bd_list:
                pre_bd = 1

            if initial_ws:
                init_root.destroy()

            if via == 'this':
                file_via_internet = False
                self.wbs_auto_update = True
                self.pre_bd_this = 2
                try:
                    self.wbs_path = self.file_name
                except NameError:
                    self.wbs_path = '(File is not named)'
                try:
                    self.soup = BeautifulSoup(self.EgonTE.get('1.0', 'end'), 'html.parser')
                    file_ready = True
                except:
                    pass
            elif via == 'link':
                self.wbs_path = simpledialog.askstring('EgonTE', 'Enter a path')
                if self.wbs_path:
                    messagebox.showinfo('EgonTE', 'web scrapping can be problematic because of the website\'s policy \n'
                                                  'be sure to check it up and be careful!\nit\'s your resposbility')
                    try:
                        response = requests.get(self.wbs_path)
                        file_type = response.headers['content-type']
                        file_type = file_type.split(';')[0].split('/')[1]
                        self.soup = BeautifulSoup(get_html_web(), f'{file_type}.parser')
                        file_ready = True
                        self.wbs_auto_update = False
                        file_via_internet = True
                        self.pre_bd_link = 2
                    except requests.exceptions.ConnectionError:
                        messagebox.showerror('EgonTE', 'Device not connected to internet')
                        connection = False
                    except requests.exceptions.InvalidSchema:
                        messagebox.showerror('EgonTE', 'Invalid link')
                        connection = False
                    except requests.exceptions.InvalidURL:
                        messagebox.showerror('EgonTE', 'Invalid URL')
                    except requests.exceptions.MissingSchema:  # not works all the time
                        try:
                            response = requests.get(f'http://{self.wbs_path}')
                            self.soup = BeautifulSoup(get_html_web(), 'html.parser')
                        except:
                            messagebox.showerror('EgonTE', 'congrats you got an unique error without explenation')
            else:
                file_via_internet = False
                try:
                    self.wbs_path = filedialog.askopenfilename(title='Open file to scrape',
                                                               filetypes=(
                                                               ('HTML FILES', '*.html'), ('Text Files', '*.txt')))
                    if self.wbs_path:
                        file = open(self.wbs_path).read()
                        self.soup = BeautifulSoup(file, 'html.parser')
                        self.pre_bd_file = 2
                        self.wbs_auto_update = False
                        file_ready = True
                    else:
                        raise FileNotFoundError
                except FileNotFoundError:
                    messagebox.showerror('EgonTE', 'file not found')

            if initial_ws:

                if not (via == 'link'):
                    title_text = 'file name:'
                else:
                    title_text = 'website link:'

                if file_ready:
                    main_ui()
            else:
                file_name_output.configure(text=self.wbs_path)

                for index, btn in enumerate(upload_btns):
                    btn.configure(bd=bd_list[index])

                if not (via == 'link'):
                    file_title.configure(text='file name:')
                else:
                    file_title.configure(text='website link:')

            au()
            search()

        def au():
            if self.wbs_auto_update:
                self.soup = BeautifulSoup(self.EgonTE.get('1.0', 'end'), 'html.parser')
            else:
                self.EgonTE.unbind('<KeyRelease>')
                self.EgonTE.bind('<KeyRelease>', self.emoji_detection)

        def search():
            global file_via_internet
            au()
            output_frame = Frame(self.ws_root)
            text_frame = Frame(output_frame)
            scroll = ttk.Scrollbar(text_frame)
            output_box = Text(text_frame)

            output_frame.grid(row=100, column=1)
            text_frame.pack(fill=BOTH, expand=True)
            scroll.pack(side=RIGHT, fill=Y)
            output_box.pack(fill=BOTH, expand=True)
            scroll.config(command=output_box.yview)
            output_box.config(yscrollcommand=scroll.set)

            # adding copy & insert functions
            copy_button = Button(output_frame, text='Copy', command=lambda: copy(output_box.get('1.0', 'end')))
            copy_button.pack()
            insert_button = Button(output_frame, text='Insert', command=lambda: self.EgonTE.insert(self.get_pos(),
                                                                                                   output_box.get('1.0',
                                                                                                                  'end')))
            insert_button.pack()

            output_content = 'Nothing found / the tool isn\'t support this type of search yet!'
            # work on these conditions!
            if tag_input.get() and class_input.get():
                scraped_content = self.soup.find_all(tag_input.get(), class_=class_input.get())
                output_content = scraped_content

            elif tag_input.get() and not (class_input.get()):
                html_tags = self.soup.find_all(tag_input.get())
                for html_tag in html_tags:
                    if return_type.get() == 'text':
                        output_content = html_tag.text
                    elif return_type.get() == 'attrs':
                        output_content = html_tag.attrs
                    else:
                        output_content = html_tag

            elif class_input.get() and not (tag_input.get()):  ### check this
                class_list = set()
                tags = {tag.name for tag in self.soup.find_all()}
                for tag in tags:
                    # find all element of tag
                    for i in self.soup.find_all(tag):
                        # if tag has attribute of class
                        if i.has_attr('class'):
                            if len(i['class']) != 0:
                                class_list.add(' '.join(i['class']))
                output_content = ''.join(class_list)
            else:
                if return_type.get() == 'text':
                    output_content = self.soup.text
                elif return_type.get() == 'attrs':
                    output_content = self.soup.attrs
                elif return_type.get() == 'content':
                    output_content = self.soup.contents
                else:
                    output_content = self.soup.prettify()

            output_box.insert('end', output_content)

            output_box.configure(state=DISABLED)

        def main_ui():
            global tag_input, file_name_output, file_via_internet, chosen_init, class_input, upload_btns, file_title
            if connection:
                self.ws_root = Toplevel()
                self.ws_root.title(self.title_struct + 'Scrapping')
                self.ws_root.resizable(False, False)
                info_title = Label(self.ws_root, text='Quick information', font=self.titles_font)
                file_title = Label(self.ws_root, text=title_text, font=sub_titles_font)
                file_name_output = Label(self.ws_root, text=self.wbs_path)

                upload_title = Label(self.ws_root, text='Upload a new content', font=self.titles_font)
                upload_file = Button(self.ws_root, text='Upload via file', command=lambda: comb_upload(via='file'),
                                     bd=self.pre_bd_file)
                upload_this = Button(self.ws_root, text='Upload this file', command=lambda: comb_upload(via='this'),
                                     bd=self.pre_bd_this)
                upload_link = Button(self.ws_root, text='Upload via link', command=lambda: comb_upload(via='link'),
                                     bd=self.pre_bd_link)
                identifiers_title = Label(self.ws_root, text='Identifiers', font=self.titles_font)
                tag_title = Label(self.ws_root, text='tags:', font=sub_titles_font)
                tag_input = Entry(self.ws_root)
                tag_ex = Button(self.ws_root, text='?', command=lambda: ex('tag'), bd=0)
                class_title = Label(self.ws_root, text='classes:', font=sub_titles_font)
                class_input = Entry(self.ws_root)
                class_ex = Button(self.ws_root, text='?', command=lambda: ex('class'), bd=0)
                return_title = Label(self.ws_root, text='Return', font=self.titles_font)
                only_text_rb = Radiobutton(self.ws_root, text='Only text', variable=return_type, value='text')
                only_attrs_rb = Radiobutton(self.ws_root, text='Only attributes', variable=return_type, value='attrs')
                only_cntn_rb = Radiobutton(self.ws_root, text='All content', variable=return_type, value='content')
                search_button = Button(self.ws_root, text='Search', command=search)

                upload_btns = [upload_file, upload_this, upload_link]

                try:
                    if file_via_internet:
                        if len(self.wbs_path) > 50:
                            quotient, remainder = divmod(len(self.wbs_path), 2)
                            res_first = self.wbs_path[:quotient + remainder]
                            res_second = self.wbs_path[quotient + remainder:]
                            self.wbs_path = f'{res_first}\n{res_second}'

                        file_name_output.configure(text=self.wbs_path)
                        code_title = Label(self.ws_root, text='Status code:', font=sub_titles_font)
                        status_code = Label(self.ws_root, text=response.status_code)
                        file_title.grid(row=1, column=0)
                        file_name_output.grid(row=2, column=0)
                        code_title.grid(row=1, column=2)
                        status_code.grid(row=2, column=2)
                    else:
                        file_title.grid(row=1, column=1)
                        file_name_output.grid(row=2, column=1)

                    info_title.grid(row=0, column=1)
                    upload_title.grid(row=3, column=1)
                    upload_file.grid(row=4, column=0)
                    upload_this.grid(row=4, column=1)
                    upload_link.grid(row=4, column=2)
                    identifiers_title.grid(row=5, column=1)
                    tag_title.grid(row=6, column=0)
                    class_title.grid(row=6, column=2)
                    tag_input.grid(row=7, column=0)
                    class_input.grid(row=7, column=2)
                    tag_ex.grid(row=8, column=0)
                    class_ex.grid(row=8, column=2)
                    return_title.grid(row=9, column=1)
                    only_cntn_rb.grid(row=10, column=0)
                    only_text_rb.grid(row=10, column=1)
                    only_attrs_rb.grid(row=10, column=2)
                    search_button.grid(row=11, column=1)
                except NameError as e:
                    self.ws_root.destroy()
                    messagebox.showerror('EgonTE', 'the program had an error')

        def change_initial_mode(mode):
            global chosen_init
            for b in init_b_list:
                b.configure(background='SystemButtonFace')
            if mode == 't':
                this_button.configure(background='light grey')
                chosen_init = 'this'
            elif mode == 'w':
                web_button.configure(background='light grey')
                chosen_init = 'link'
            else:
                loc_button.configure(background='light grey')
                chosen_init = 'file'

        # init window to not delay / limit users
        init_root = Toplevel()
        init_root.title(self.title_struct + 'web scrapping')
        title_label = Label(init_root, text='What you would like to scrape?', font='arial 10 underline')
        web_button = Button(init_root, text='A website', command=lambda: change_initial_mode('w'))
        this_button = Button(init_root, text='This file', command=lambda: change_initial_mode('t'))
        loc_button = Button(init_root, text='A Local file', command=lambda: change_initial_mode('l'))
        enter_button = Button(init_root, text='Enter', command=lambda: comb_upload(chosen_init, True),
                              font='arial 10 bold')
        ### skip_button = ?
        title_label.grid(row=1, column=1)
        web_button.grid(row=2, column=0, padx=5)
        this_button.grid(row=2, column=1)
        loc_button.grid(row=2, column=2, padx=5)
        enter_button.grid(row=3, column=1, pady=5)

        init_b_list = [web_button, loc_button, this_button]

        if self.file_name.endswith('.html'):
            this_button = Button(init_root, text='This file', command=lambda: change_initial_mode('t'))
            init_b_list = init_b_list + [this_button]
            this_button.grid(row=2, column=1)

        self.record_list.append(f'> [{self.get_time()}] - Web scrapping tool window opened')

    def handwriting(self):
        '''
        the handwriting tool allows you to draw on a pretty rich canvas (with most basic canvas option except shapes
        and colors), and allows you to convert to text, upload and save the thing that you draw
        '''
        global current_tool
        global previous_point, current_point
        previous_point = [0, 0]
        current_point = [0, 0]
        self.convert_output = ''
        img_array = ''
        self.convert_image = ''
        color = StringVar()
        color.set('black')
        width = IntVar()
        width.set(1)
        lines_list, images_list = [], []
        # I'm making the y axis with a low value because it's exapnds to the size of the window - and by using this
        # size Its will serve me because this will be the size that the canvas will take the other widgets' space
        canvas_x, canvas_y = 500, 10
        self.pnc_width, self.ers_width = IntVar(), IntVar()  # values
        self.pnc_width.set(2)
        self.ers_width.set(5)
        current_tool = 'pencil'
        self.ers_current, self.pnc_current = 1, 1  # index
        tool_c = BooleanVar()
        mw_shortcut = BooleanVar()
        mw_shortcut.set(True)

        def paint(event):
            global previous_point, current_point
            x = event.x
            y = event.y
            current_point = [x, y]
            if previous_point != [0, 0]:
                line = self.draw_canvas.create_line(previous_point[0], previous_point[1], current_point[0],
                                                    current_point[1],
                                                    fill=color.get(), width=width.get())
                lines_list.append(line)
            previous_point = current_point
            if event.type == '5':
                previous_point = [0, 0]

        def move(key, event=None):
            if key == 'left':
                move_x = -10
                move_y = 0
            elif key == 'right':
                move_x = 10
                move_y = 0
            elif key == 'up':
                move_x = 0
                move_y = -10
            elif key == 'down':
                move_x = 0
                move_y = 10
            for l in lines_list:
                self.draw_canvas.move(l, move_x, move_y)
            for img in images_list:
                self.draw_canvas.move(img, move_x, move_y)

        def cords(event):
            pos_x, pos_y = event.x, event.y
            cords_label.configure(text=f'X coordinates:{pos_x} | Y coordinates:{pos_y}')

        def upload():
            # tkinter garbage collector have problems with images, to solve that we need to make all of them, global
            global img_array, image, image_tk
            # load image into the canvas
            self.convert_image = filedialog.askopenfilename(filetypes=self.img_extensions)
            if self.convert_image:
                image = Image.open(self.convert_image)
                image_tk = PhotoImage(file=self.convert_image)
                image_x = (self.draw_canvas.winfo_width() // 2) - (image.width // 2)
                image_y = (self.draw_canvas.winfo_height() // 2) - (image.height // 2)
                canvas_image = self.draw_canvas.create_image(image_x, image_y, image=image_tk, anchor=NW)
                images_list.append(canvas_image)
                self.ci_from = 'upload'

        def save():

            self.convert_image = self.save_images(self.draw_canvas, hw_root, buttons_frame)
            self.ci_from = 'save'

        def erase():
            global current_tool
            current_tool = 'eraser'
            color.set('white')
            update_sizes()
            self.draw_canvas.configure(cursor='target')
            eraser.configure(bg='light gray'), pencil.configure(bg='SystemButtonFace')

        def pencil_():
            global current_tool
            current_tool = 'pencil'
            update_sizes()
            color.set('black')
            self.draw_canvas.configure(cursor='pencil')
            pencil.configure(bg='light gray'), eraser.configure(bg='SystemButtonFace')

        def update_sizes(scrollwheel_event=False):
            if current_tool == 'pencil':
                size = self.pnc_width.get()
                pencil_list = list(map(int, list(self.pencil_size['values'])))
                self.pnc_current = pencil_list.index(size)
                self.pencil_size.current(pencil_list.index(size))
                print(self.pencil_size.get())
                width.set(size)
            else:

                size = self.ers_width.get()
                eraser_list = list(map(int, list(self.eraser_size['values'])))

                self.ers_current = eraser_list.index(size)
                self.eraser_size.current(eraser_list.index(size))
                print(self.eraser_size.get())
                width.set(size)

        def sizes_shortcus(event):
            if mw_shortcut.get():
                if event.num == 5 or event.delta == -120:
                    value = -1
                    # type = 'n'
                elif event.num == 4 or event.delta == 120:
                    value = 1
                    # type = 'p'
            else:
                if event == 'up':
                    value = 1
                else:
                    value = -1

            try:

                if current_tool == 'pencil':
                    self.pencil_size.current(self.pnc_current + value)
                    self.pnc_current += value

                else:
                    self.eraser_size.current(self.ers_current + value)
                    self.ers_current += value

                update_sizes()
            except Exception as e:
                print(e)

        def custom_size(event=False):
            if current_tool == 'pencil':
                if isinstance(self.pnc_width.get(), int):
                    self.pnc_width.set(self.pencil_size.get())

            else:
                if isinstance(self.ers_width.get(), int):
                    self.ers_width.set(self.eraser_size.get())
                    try:
                        fixed_values_list = list(map(int, list(self.eraser_size['values'])))
                        self.eraser_size.current(fixed_values_list.index(self.ers_width.get()))  # (pencil_size.get()
                    except ValueError:
                        pass

        def convert():
            if not (self.convert_image):
                save()

            # saving gives you the name
            if self.ci_from == 'save':
                image_txt = Image.open(self.convert_image)  # upload gives you this
                image_txt = self.convert_image
            else:
                image_txt = image

            if image_txt:
                text = image_to_string(image_txt)
            if self.convert_output:
                self.convert_output.destroy()
                pass
            if text:
                self.convert_output = Text(hw_root)
                self.convert_output.insert('1.0', text)
                self.convert_output.configure(relief='flat', state=DISABLED, height=5)
                self.convert_output.pack()

        def move_image(event):
            x, y = event.x, event.y
            if None:
                pass

        def cord_opt():

            def lt_cords(event):
                if tool_c.get():
                    pos_x, pos_y = event.x, event.y
                    tool_lc.configure(text=f'{current_tool} coordinates:{pos_x} | {current_tool} coordinates:{pos_y}')

            if tool_c.get():
                cords_label.pack_forget()
                cords_label.grid(row=1, column=0)
                tool_lc.grid(row=1, column=2)
                hw_root.bind('<B1-Motion>', lt_cords)

            else:
                tool_lc.grid_forget()
                cords_label.grid_forget()
                cords_label.pack(fill=BOTH)
                hw_root.unbind('<B1-Motion>')
                self.draw_canvas.bind('<B1-Motion>', paint)

        def information():
            draw_info_root = Toplevel()
            draw_info_root.title(f'{self.title_struct} Handwriting bonuses')

            arrows_desc = 'with the arrows keys, you can move the entire content \nof the canvas to the direction that' \
                          'you want'
            keybind_dict = {'🡡': 'up', '🡣': 'down', '🡢': 'right', '🡠': 'left'}
            btn_up, btn_down, btn_right, btn_left = Label(draw_info_root), Label(draw_info_root), Label(
                draw_info_root), Label(draw_info_root)
            keybind_exp = btn_up, btn_down, btn_right, btn_left

            keybind_title = Label(draw_info_root, text='Keybinds', font=self.titles_font)
            arrows_description = Label(draw_info_root, text=arrows_desc, font='arial 8')
            for index, arr in enumerate(keybind_dict.keys()):
                keybind_exp[index].configure(text=f'{keybind_dict[arr]} : {arr}')

            keybind_title.grid(row=0, column=1)

            arrows_description.grid(row=1, column=1)
            btn_up.grid(row=2, column=0)
            btn_down.grid(row=2, column=2)
            btn_right.grid(row=3, column=0)
            btn_left.grid(row=3, column=2)

            scroll_wheel_up, scroll_wheel_down = '🖱🡡', '🖱🡣'
            scroll_wheel_desc = 'With your mouse scrollwheel you can change the\nthickness of the tool your using'

            scroll_up, scroll_down = Label(draw_info_root, text=f'more thickness : {scroll_wheel_up}'), \
                Label(draw_info_root, text=f'less thickness : {scroll_wheel_down}')
            scroll_wheel_description = Label(draw_info_root, text=scroll_wheel_desc, font='arial 8')

            scroll_wheel_description.grid(row=4, column=1)
            scroll_up.grid(row=5, column=0)
            scroll_down.grid(row=5, column=2)

            settings_label = Label(draw_info_root, text='Settings', font=self.titles_font)
            check_frame = Frame(draw_info_root)
            last_tool_cords = Checkbutton(check_frame, text='Tool cords', variable=tool_c, command=cord_opt)
            spin_shortcut = Checkbutton(check_frame, text='Mouse wheel\nshortcut', variable=mw_shortcut,
                                        command=switch_sc)

            settings_label.grid(row=6, column=1)
            check_frame.grid(row=7, column=1)
            last_tool_cords.grid(row=1, column=0)
            spin_shortcut.grid(row=1, column=2)

        def switch_sc():
            if mw_shortcut.get():
                self.draw_canvas.bind('<MouseWheel>', sizes_shortcus)
                self.draw_canvas.unbind('<Control-Key-.>')
                self.draw_canvas.unbind('<Control-Key-,>')
            else:
                self.draw_canvas.unbind('<MouseWheel>')
                self.draw_canvas.bind('<Control-Key-.>', lambda event: sizes_shortcus('up'))
                self.draw_canvas.bind('<Control-Key-,>', lambda event: sizes_shortcus('down'))

        # drawing board
        hw_root = Toplevel()
        hw_root.geometry('600x350')
        hw_root.title(self.title_struct + 'Draw and convert')
        draw_frame = Frame(hw_root)
        buttons_frame = Frame(hw_root)
        self.draw_canvas = Canvas(draw_frame, width=canvas_x, height=canvas_y, bg='white', cursor='pencil')
        self.draw_canvas.bind('<B1-Motion>', paint)
        self.draw_canvas.bind('<ButtonRelease-1>', paint)
        pencil = Button(buttons_frame, text='Pencil', command=pencil_, borderwidth=1)
        eraser = Button(buttons_frame, text='Eraser', command=erase, borderwidth=1)
        seperator = Label(buttons_frame, text='|')
        save_png = Button(buttons_frame, text='Save as png', command=save, borderwidth=1)
        upload_writing = Button(buttons_frame, text='Upload', command=upload, state=tes, borderwidth=1)
        convert_to_writing = Button(buttons_frame, text='Convert to writing', command=convert,
                                    borderwidth=1)  # convert)
        erase_all = Button(buttons_frame, text='Erase all', command=lambda: self.draw_canvas.delete('all'),
                           borderwidth=1)
        seperator_2 = Label(buttons_frame, text='|')
        info_button = Button(buttons_frame, text='i', command=information)

        self.pencil_size = ttk.Combobox(buttons_frame, width=10, textvariable=self.pnc_width, state='normal')
        self.pencil_size['values'] = (1, 2, 3, 4, 6, 8)
        self.pencil_size.current(self.pnc_current)
        self.eraser_size = ttk.Combobox(buttons_frame, width=10, textvariable=self.ers_width, state='normal')
        self.eraser_size['values'] = (3, 5, 8, 10, 12, 15)
        self.eraser_size.current(self.ers_current)

        cords_frame = Frame(hw_root)
        tool_lc = Label(cords_frame, text='')
        cords_label = Label(cords_frame, text='')

        buttons_frame.pack()
        draw_frame.pack(fill=BOTH, expand=True)
        pencil.grid(row=0, column=0, padx=2)
        self.pencil_size.grid(row=0, column=1, padx=2)
        eraser.grid(row=0, column=2, padx=2)
        self.eraser_size.grid(row=0, column=3, padx=2)
        seperator.grid(row=0, column=4)
        erase_all.grid(row=0, column=5, padx=2)
        save_png.grid(row=0, column=6, padx=2)
        upload_writing.grid(row=0, column=7, padx=2)
        convert_to_writing.grid(row=0, column=8, padx=2)
        seperator_2.grid(row=0, column=9, padx=2)
        info_button.grid(row=0, column=10, padx=2)
        self.draw_canvas.pack(fill=BOTH, expand=True)

        cords_frame.pack(fill=BOTH)
        cords_label.pack(fill=BOTH)

        pencil_()
        hw_root.bind('<Left>', lambda e: move(key='left'))
        hw_root.bind('<Right>', lambda e: move(key='right'))
        hw_root.bind('<Up>', lambda e: move(key='up'))
        hw_root.bind('<Down>', lambda e: move(key='down'))
        hw_root.bind('<Motion>', cords)
        hw_root.bind('<B2-Motion>', move_image)
        self.pencil_size.bind('<<ComboboxSelected>>', lambda event: update_sizes())
        self.eraser_size.bind('<<ComboboxSelected>>', lambda event: update_sizes())
        self.draw_canvas.bind('<MouseWheel>', sizes_shortcus)
        # existing file to writing

        self.record_list.append(f'> [{self.get_time()}] - Hand writing tool window opened')

    def natural_language_process(self, function):
        '''
        the NLP function will return you the thing that you are looked for with it that is found on the content
        of the main text box,
        It have also some more unique things that it can output (like phone numbers),
        and the output will be in a nice and organized window, that will let you decide what to do with the content
        (copy ,etc.)
        '''
        try:
            nlp = spacy.load('en_core_web_sm')
        except OSError as e:
            messagebox.showinfo('EgonTE', 'natural language package isn\'t found.\nthe program now will pause to try to'
                                          'download the package for you')
            nlp_download('en_core_web_sm')
            nlp = spacy.load('en_core_web_sm')

        try:

            if self.prefer_gpu.get():
                spacy.prefer_gpu()

            nlp_root = Toplevel()
            result_frame = Frame(nlp_root)
            nlp_root.title(self.title_struct + 'natural language processor')
            text = self.EgonTE.get('1.0', 'end')
            doc = nlp(text)
            def_result = True
            result_text = '(No matches found!)'
            if function == 'verbs':
                # ccontent = doc.verb
                verbs = []
                for token in doc:
                    if token.pos_ == 'VERB':
                        verbs.append(token)
                result_text = ', '.join(str(e) for e in verbs)

            elif function == 'nouns':
                nouns = []
                for token in doc:
                    if token.pos_ == 'NOUN':
                        nouns.append(token)
                if nouns:
                    result_text = ', '.join(str(e) for e in nouns)

            elif function == 'adjectives':
                adjectives = []
                for token in doc:
                    if token.pos_ == 'ADJ':
                        adjectives.append(token)
                if adjectives:
                    result_text = ', '.join(str(e) for e in adjectives)

            elif function == 'adverbs':
                adverbs = []
                for token in doc:
                    if token.pos_ == 'ADV':
                        adverbs.append(token)
                if adverbs:
                    result_text = ', '.join(str(e) for e in adverbs)

            elif function == 'pronouns':
                pronouns = []
                for token in doc:
                    if token.pos_ == 'PRON':
                        pronouns.append(token)
                if pronouns:
                    result_text = ', '.join(str(e) for e in pronouns)


            elif function == 'dependency':
                def_result = False
                columns = ('word', 'dependency')
                result = ttk.Treeview(result_frame, columns=columns, show='headings')
                result.heading('word', text='Words')
                result.heading('dependency', text='Dependency')
                content = {}
                for token in doc:
                    content[token.text] = token.dep_
                    result.insert('', END, value=[token, content[token.text]])

                str_res = ''
                for res in content.keys():
                    str_res += f'{res} - {content[res]}, '
                result_text = str_res



            elif function == 'entity recognition':
                def_result = False
                columns = ('entity', 'recognition')
                result = ttk.Treeview(result_frame, columns=columns, show='headings')
                result.heading('entity', text='Entity')
                result.heading('recognition', text='Data')

                content = {}
                for ent in doc.ents:
                    content[ent.text] = ent.label_
                    result.insert('', END, value=[ent, content[ent.text]])

                str_res = ''
                for res in content.keys():
                    str_res += f'{res} - {content[res]}, '
                result_text = str_res


            elif function == 'stop words':
                stop_words = []
                stopwords = list(spacy.lang.en.stop_words.STOP_WORDS)
                for token in doc:
                    print(f'token : {token}')
                    if str(token) in stopwords:
                        stop_words.append(token)

                if stop_words:
                    result_text = ', '.join(str(e) for e in stop_words)

            elif function == 'lemmatization':
                def_result = False
                columns = ('original', 'altered')
                result = ttk.Treeview(result_frame, columns=columns, show='headings')
                result.heading('original', text='Original')
                result.heading('altered', text='Altered')

                res = ''
                for token in doc:
                    if str(token) != str(token.lemma_):
                        res += (f'{str(token):>20} : {str(token.lemma_)}\n')
                        result.insert('', END, value=[f'{str(token):>20}', str(token.lemma_)])
                    result_text = res

            elif function == 'most common words':
                def_result = False
                columns = ('top_word', 'number_of_occurrences')
                result = ttk.Treeview(result_frame, columns=columns, show='headings')
                result.heading('top_word', text='Words')
                result.heading('number_of_occurrences', text='Occurrences')

                words = [
                    token.text
                    for token in doc
                    if not token.is_stop and not token.is_punct
                ]
                result_text = text = Counter(words).most_common(10)  # !!!
                print(result_text)

                for res in result_text:
                    result.insert('', END, value=res)

                str_res = ''
                for res in result_text:
                    str_res += f'{res[0]} - {res[1]}, '
                result_text = str_res

            elif function == 'names':
                names = []
                matcher = Matcher(nlp.vocab)
                # defining a rule
                pattern = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]
                # adding a rule
                matcher.add('FULL_NAME', [pattern])
                matches = matcher(doc)
                for _, start, end in matches:
                    span = doc[start:end]
                    names.append(span.text)

                if names:
                    result_text = ', '.join(str(e) for e in names)

            #         yield span.text
            #
            elif function == 'phone numbers':
                phones = []
                pattern = [
                    {'ORTH': '('},
                    {'SHAPE': 'ddd'},
                    {'ORTH': ')'},
                    {'SHAPE': 'ddd'},
                    {'ORTH': '-', 'OP': '?'},
                    {'SHAPE': 'dddd'}
                ]
                matcher = Matcher(nlp.vocab)
                matcher.add('PHONE_NUMBER', [pattern])
                matches = matcher(doc)
                for match_id, start, end in matches:
                    span = doc[start:end]
                    phones.append(span.text)

                if phones:
                    result_text = ', '.join(str(e) for e in phones)

            if function != 'most common words':
                title = Label(nlp_root, text=f'{function.capitalize()}:')
            else:
                title = Label(nlp_root, text='Top 10 most common words:')

            title.configure(font=self.titles_font)
            copy_button = Button(nlp_root, text='Copy', bd=1, command=lambda: copy(result_text))
            title.pack()
            result_frame.pack(fill=BOTH, expand=True)
            if def_result:

                result = Text(result_frame)

                result_text = result_text.split(' ')
                it = iter(result_text)
                result_lists = list(iter(lambda: tuple(islice(it, 10)), ()))
                result_text = ''
                for index, result_list in enumerate(result_lists):
                    if index > 0:
                        result_text += '\n'
                    for result_word in result_list:
                        result_text += f'{result_word} '

                result.insert('end', result_text)
                result.configure(state=DISABLED)

            nlp_scroll = ttk.Scrollbar(result_frame)
            nlp_scroll.pack(side=RIGHT, fill=Y)
            result.configure(yscrollcommand=self.text_scroll.set)
            nlp_scroll.config(command=self.EgonTE.yview)

            result.pack(fill=BOTH, expand=True)
            copy_button.pack()



        except OSError as e:
            messagebox.showerror('EgonTE', 'Can\'t find the language model!')

    def saved_settings(self, sm=None):
        '''
        the saved settings function managed a huge portion of the functionality of the saved variables,
        likes assigning them, check if the file exists, have the default dictionary of the files values,
        save the file, etc.
        '''
        file_name = 'EgonTE_settings.json'

        if sm == 'save':
            os.remove(file_name)
            with open(file_name, 'w') as f:
                dump(self.data, f)
                print('save 1', self.data)

            if self.data['open_last_file']:
                self.save_last_file()

        else:

            if os.path.exists(file_name):
                print('file exist')
                with open(file_name, 'r') as f:
                    self.data = load(f)
                    print(self.data)

                self.rm.set(self.data['reader_mode'])
                self.bars_active.set(self.data['status_bar'] and self.data['file_bar'])
                self.show_statusbar.set(self.bars_active.get())
                self.status_ = self.data['status_bar']
                self.file_ = self.data['file_bar']

                self.show_toolbar.set(self.data['toolbar'])
                self.night_mode.set(self.data['night_mode'])
                self.tt_sc.set(self.data['text_twisters'])
                self.nm_palette.set(self.data['night_type'])
                # maybe need to be deleted
                self.cs.set(self.data['style'])
                self.cc.set(self.data['cursor'])
                # ------------------------------
                self.ww.set(self.data['word_wrap'])
                self.aus.set(self.data['auto_save'])

                self.predefined_cursor = self.cc.get()
                self.predefined_style = self.cs.get()
                self.predefined_relief = self.data['relief']

                if self.lf.get():
                    self.file_name = self.data['open_last_file']

                return False

            else:
                print('settings file doesn\'t exist')
                self.data = {'night_mode': False, 'status_bar': True, 'file_bar': True, 'cursor': 'xterm',
                             'style': 'clam',
                             'word_wrap': True, 'reader_mode': False, 'auto_save': True, 'relief': 'ridge',
                             'transparency': 100, 'toolbar': True, 'open_last_file': '', 'text_twisters': False,
                             'night_type': 'black'}

                with open(file_name, 'w') as f:
                    dump(self.data, f)
                # self.data = load(file_name)
                # print(self.data)

                return True

    def text_decorators(self):
        '''
        the text decoration function is a window that let you make a bigger style of text with many symbols.
        there is 3 styles and the text can be outputted horizontally and verticly.
        also there is a UI for the process that make you manage it very easialy

        (for the developer) astrick broken
        '''
        global chosen_decorator, result_box
        chosen_decorator = 1
        inline = False
        result_box = ''

        def enter():
            if chosen_decorator == 1:
                a = '..######..\n..#....#..\n..######..\n..#....#..\n..#....#..\n\n'
                b = '..######..\n..#....#..\n..#####...\n..#....#..\n..######..\n\n'
                c = '..######..\n..#.......\n..#.......\n..#.......\n..######..\n\n'
                d = '..#####...\n..#....#..\n..#....#..\n..#....#..\n..#####...\n\n'
                e = '..######..\n..#.......\n..#####...\n..#.......\n..######..\n\n'
                f = '..######..\n..#.......\n..#####...\n..#.......\n..#.......\n\n'
                g = '..######..\n..#.......\n..#####...\n..#....#..\n..#####...\n\n'
                h = '..#....#..\n..#....#..\n..######..\n..#....#..\n..#....#..\n\n'
                i = '..######..\n....##....\n....##....\n....##....\n..######..\n\n'
                j = '..######..\n....##....\n....##....\n..#.##....\n..####....\n\n'
                k = '..#...#...\n..#..#....\n..##......\n..#..#....\n..#...#...\n\n'
                l = '..#.......\n..#.......\n..#.......\n..#.......\n..######..\n\n'
                m = '..#....#..\n..##..##..\n..#.##.#..\n..#....#..\n..#....#..\n\n'
                n = '..#....#..\n..##...#..\n..#.#..#..\n..#..#.#..\n..#...##..\n\n'
                o = '..######..\n..#....#..\n..#....#..\n..#....#..\n..######..\n\n'
                p = '..######..\n..#....#..\n..######..\n..#.......\n..#.......\n\n'
                q = '..######..\n..#....#..\n..#.#..#..\n..#..#.#..\n..######..\n\n'
                r = '..######..\n..#....#..\n..#.##....\n..#...#...\n..#....#..\n\n'
                s = '..######..\n..#.......\n..######..\n.......#..\n..######..\n\n'
                t = '..######..\n....##....\n....##....\n....##....\n....##....\n\n'
                u = '..#....#..\n..#....#..\n..#....#..\n..#....#..\n..######..\n\n'
                v = '..#....#..\n..#....#..\n..#....#..\n...#..#...\n....##....\n\n'
                w = '..#....#..\n..#....#..\n..#.##.#..\n..##..##..\n..#....#..\n\n'
                x = '..#....#..\n...#..#...\n....##....\n...#..#...\n..#....#..\n\n'
                y = '..#....#..\n...#..#...\n....##....\n....##....\n....##....\n\n'
                z = '..######..\n......#...\n.....#....\n....#.....\n..######..\n\n'
                sp = '&&&&&&\n&&&&&&\n&&&&&&\n&&&&&&\n\n'
                dot = '----..----\n\n'
                self.ascii_alph = (a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z,
                                   sp, dot)
                self.ascii_dict = {'a': a, 'b': b, 'c': c, 'd': d, 'e': e, 'f': f, 'g': g, 'h': h, 'i': i, 'j': j,
                                   'k': k, 'l': l,
                                   'm': m, 'n': n, 'o': o, 'p': p, 'q': q, 'r': r, 's': s, 't': t, 'u': u, 'v': v,
                                   'w': w, 'x': x,
                                   'y': y, 'z': z, ' ': sp, '.': dot}

                newline_n = 5

            elif chosen_decorator == 2:
                a = (
                    '000000000000\n000111111000\n011000000110\n011000000110\n011111111110\n011000000110\n011000000110\n011000000110\n\n')
                b = (
                    '000000000000\n011111111000\n011000000110\n011000000110\n011111111000\n011000000110\n011000000110\n011111111000\n\n')
                c = (
                    '000000000000\n000111111000\n011000000110\n011000000000\n011000000000\n011000000000\n011000000110\n000111111000\n\n')
                d = (
                    '000000000000\n011111111000\n011000000110\n011000000110\n011000000110\n011000000110\n011000000110\n011111111000\n\n')
                e = (
                    '000000000000\n011111111110\n011000000000\n011000000000\n011111111100\n011000000000\n011000000000\n011111111110\n\n')
                f = (
                    '000000000000\n011111111110\n011000000000\n011000000000\n011111111100\n011000000000\n011000000000\n011000000000\n\n')
                g = (
                    '000000000000\n000111111000\n011000000110\n011000000000\n011000000000\n011000011110\n011000000110\n000111111000\n\n')
                h = (
                    '000000000000\n011000000110\n011000000110\n011000000110\n011111111110\n011000000110\n011000000110\n011000000110\n\n')
                i = (
                    '000000000000\n000111111000\n000001100000\n000001100000\n000001100000\n000001100000\n000001100000\n000111111000\n\n')
                j = (
                    '000000000000\n000001111110\n000000011000\n000000011000\n000000011000\n000000011000\n011000011000\n000111100000\n\n')
                k = (
                    '000000000000\n011000000110\n011000011000\n011001100000\n011110000000\n011001100000\n011000011000\n011000000110\n\n')
                l = (
                    '000000000000\n011000000000\n011000000000\n011000000000\n011000000000\n011000000000\n011000000000\n011111111110\n\n')
                m = (
                    '000000000000\n011000000110\n011110011110\n011001100110\n011001100110\n011000000110\n011000000110\n011000000110\n\n')
                n = (
                    '000000000000\n011000000110\n011000000110\n011110000110\n011001100110\n011000011110\n011000000110\n011000000110\n\n')
                o = (
                    '000000000000\n000111111000\n011000000110\n011000000110\n011000000110\n011000000110\n011000000110\n000111111000\n\n')
                p = (
                    '000000000000\n011111111000\n011000000110\n011000000110\n011111111000\n011000000000\n011000000000\n011000000000\n\n')
                q = (
                    '000000000000\n000111111000\n011000000110\n011000000110\n011000000110\n011001100110\n011000011000\n000111100110\n\n')
                r = (
                    '000000000000\n011111111000\n011000000110\n011000000110\n011111111000\n011001100000\n011000011000\n011000000110\n\n')
                s = (
                    '000000000000\n000111111110\n011000000000\n011000000000\n000111111000\n000000000110\n000000000110\n011111111000\n\n')
                t = (
                    '000000000000\n011111111110\n000001100000\n000001100000\n000001100000\n000001100000\n000001100000\n000001100000\n\n')
                u = (
                    '000000000000\n011000000110\n011000000110\n011000000110\n011000000110\n011000000110\n011000000110\n000111111000\n\n')
                v = (
                    '000000000000\n011000000110\n011000000110\n011000000110\n011000000110\n000110011000\n000110011000\n000001100000\n\n')
                w = (
                    '000000000000\n011000000110\n011000000110\n011000000110\n011001100110\n011001100110\n011001100110\n000110011000\n\n')
                x = (
                    '000000000000\n011000000110\n011000000110\n000110011000\n000001100000\n000110011000\n011000000110\n011000000110\n\n')
                y = (
                    '000000000000\n011000000110\n011000000110\n000110011000\n000001100000\n000001100000\n000001100000\n000001100000\n\n')
                z = (
                    '000000000000\n011111111110\n000000000110\n000000011000\n000001100000\n000110000000\n011000000000\n011111111110\n\n')
                sp = (
                    '000000000000\n000000000000\n000000000000\n000000000000\n000000000000\n000000000000\n000000000000\n000000000000\n\n')
                n0 = (
                    '000000000000\n000111111000\n011000000110\n011000011110\n011001100110\n011110000110\n011000000110\n000111111000\n\n')
                n1 = (
                    '000000000000\n000001100000\n000111100000\n000001100000\n000001100000\n000001100000\n000001100000\n000111111000\n\n')
                n2 = (
                    '000000000000\n000111111000\n011000000110\n000000000110\n000000011000\n000001100000\n000110000000\n011111111110\n\n')
                n3 = (
                    '000000000000\n011111111110\n000000011000\n000001100000\n000000011000\n000000000110\n011000000110\n000111111000\n\n')
                n4 = (
                    '000000000000\n000000011000\n000001111000\n000110011000\n011000011000\n011111111110\n000000011000\n000000011000\n\n')
                n5 = (
                    '000000000000\n011111111110\n011000000000\n011111111000\n000000000110\n000000000110\n011000000110\n000111111000\n\n')
                n6 = (
                    '000000000000\n000001111000\n000110000000\n011000000000\n011111111000\n011000000110\n011000000110\n000111111000\n\n')
                n7 = (
                    '000000000000\n011111111110\n000000000110\n000000011000\n000001100000\n000110000000\n000110000000\n000110000000\n\n')
                n8 = (
                    '000000000000\n000111111000\n011000000110\n011000000110\n000111111000\n011000000110\n011000000110\n000111111000\n\n')
                n9 = (
                    '000000000000\n000111111000\n011000000110\n011000000110\n000111111110\n000000000110\n000000011000\n000111100000\n\n')
                s0 = (
                    '000000000000\n000111111000\n011000000110\n000000000110\n000000011000\n000001100000\n000000000000\n000001100000\n\n')
                s1 = (
                    '000000000000\n000001100000\n000001100000\n000001100000\n000001100000\n000001100000\n000000000000\n000001100000\n\n')
                s2 = (
                    '000000000000\n000000000000\n000000000000\n000000000000\n000000000000\n000000000000\n000001100000\n000001100000\n\n')
                s3 = (
                    '000000000000\n000000000000\n000000000000\n000000000000\n000000000000\n000000000000\n000000000000\n000001100000\n\n')
                s4 = (
                    '000000000000\n000000000000\n000000000000\n000000000000\n001111111100\n000000000000\n000000000000\n000000000000\n\n')
                s5 = (
                    '000000000000\n000000000000\n000001100000\n000001100000\n011111111110\n000001100000\n000001100000\n000000000000\n\n')

                self.ascii_alph = (a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z,
                                   sp, n0, n1, n2, n3, n4, n5, n6, n7, n8, n9,
                                   s0, s1, s2, s3, s4, s5, s5)
                # add
                self.ascii_dict = {'a': a, 'b': b, 'c': c, 'd': d, 'e': e, 'f': f, 'g': g, 'h': h, 'i': i, 'j': j,
                                   'k': k, 'l': l, 'm': m, 'n': n, 'o': o, 'p': p, 'q': q, 'r': r, 's': s, 't': t,
                                   'u': u,
                                   'v': v, 'w': w, 'x': x, 'y': y, 'z': z, ' ': sp, '0': n0, '1': n1, '2': n2, '3': n3,
                                   '4': n4,
                                   '5': n5, '6': n6, '7': n7, '8': n8, '9': n9, '?': s0, '!': s1, ',': s2, '.': s3,
                                   '-': s4, '#': s5}

                newline_n = 8


            elif chosen_decorator == 4:
                a = ('  ******  \n  *    *  \n  ******  \n  *    *  \n  *    *  \n\n')
                b = ('  ******  \n  *     * \n  ******  \n  *     * \n  ******  \n\n')
                c = ('  ******  \n  *       \n  *       \n  *       \n  ******  \n\n')
                d = ('  *****   \n  *    *  \n  *    *  \n  *    *  \n  *****   \n\n')
                e = ('  ******  \n  *       \n  *****   \n  *       \n  ******  \n\n')
                f = ('  ******  \n  *       \n  *****   \n  *       \n  *       \n\n')
                g = ('  *******  \n  *        \n  *   ***  \n  *      * \n  *******  \n\n')
                h = ('  *     *  \n  *     *  \n  *******  \n  *     *  \n  *     *  \n\n')
                i = ('  **   \n  **   \n  **   \n  **   \n  **   \n\n')
                j = ('  ******  \n      **  \n      **  \n  **  **  \n  ******  \n\n')
                k = ('  *   *  \n  *  *   \n  * *    \n  *  *   \n  *   *  \n\n')
                l = ('  *     \n  *     \n  *     \n  *     \n  ******\n\n')
                m = ('  *       *\n  **     **\n  *  *  * *\n  *   **  *\n  *       *\n\n')
                n = ('  **   *  \n  **   *  \n  * *  *  \n  *  * *  \n  *   **  \n\n')
                o = ('   *****   \n  *     *  \n  *     *  \n  *     *  \n   *****   \n\n')
                p = ('  ******  \n  *     * \n  ******  \n  *       \n  *       \n\n')
                q = ('   ******  \n  *      * \n   ******  \n        *  \n        *  \n\n')
                r = ('  ******  \n  *     * \n  * ***   \n  *  *    \n  *    *  \n\n')
                s = ('  ******  \n  *       \n  ******  \n       *  \n  ******  \n\n')
                t = ('  ******\n    **  \n    **  \n    **  \n    **  \n\n')
                u = ('  *     *  \n  *     *  \n  *     *  \n  *     *  \n   *****   \n\n')
                v = ('  *    *  \n  *    *  \n  *    *  \n   *  *   \n    **    \n\n')
                w = ('  *       *  \n  *  * *  *  \n  * *   * *  \n  **     **  \n  **     **  \n\n')
                x = ('  *     *  \n   *   *   \n    * *    \n   *   *   \n  *     *  \n\n')
                y = ('  *     * \n   *  *   \n    **    \n    **    \n    **    \n\n')
                z = ('   ******\n       **\n    ***  \n  **     \n  ****** \n\n')
                sp = ('..........\n..........\n..........\n..........\n\n')
                dot = ('....\n....\n....\n.....\n\n')

                self.ascii_alph = (a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z, sp,
                                   dot)
                self.ascii_dict = {'a': a, 'b': b, 'c': c, 'd': d, 'e': e, 'f': f, 'g': g, 'h': h, 'i': i, 'j': j,
                                   'k': k, 'l': l,
                                   'm': m, 'n': n, 'o': o, 'p': p, 'q': q, 'r': r, 's': s, 't': t, 'u': u, 'v': v,
                                   'w': w, 'x': x,
                                   'y': y, 'z': z, ' ': sp, '.': dot}

                newline_n = 5

            alphabet = 'abcdefghijklmnopqrstuvwxyz 0123456789?!,.-+'
            decorator_input = text_box.get('1.0', END).lower()

            if decorator_input:
                try:
                    if self.dec_plc.get() == 'ver':
                        nl_list = ['\n', '\n', '\n', '\n', '\n', '\n', '\n']
                        modified_ascii_dict = {}
                        for key, value in self.ascii_dict.items():
                            v_count = value.count('\n') - 1
                            if v_count < newline_n:
                                nl_needed = newline_n - v_count
                                newlines = ''.join(nl_list[0:nl_needed])
                                value = f'{newlines}{value}'
                            modified_ascii_dict[key] = value

                        res = ''
                        word_list = []
                        devided_list = []

                        for asc_value in self.ascii_alph:
                            asc_value = list(asc_value)
                            asc_value[-1], asc_value[-2] = '    ', '    '
                            asc_value = ''.join(asc_value)

                        for word in decorator_input:
                            if word in modified_ascii_dict.keys():
                                word_list.append(modified_ascii_dict[word])

                        print(word_list)

                        for word in word_list:
                            devided_list.append(word.split('\n'))

                        print(devided_list)

                        for index in range(newline_n):
                            for line in devided_list:
                                try:
                                    res += ''.join(line[index])
                                    res += '    '
                                except IndexError:
                                    pass
                            res += '\n'

                        print(res)


                    else:
                        res = ''
                        for char in decorator_input:
                            if alphabet.find(char) != -1:
                                if char in list(self.ascii_dict.keys()):
                                    res += self.ascii_dict[char]


                    # UI for result
                    global result_box, result_frame
                    if result_box:
                        result_frame.destroy()

                    paste_to_text.configure(state=ACTIVE)
                    result_frame = Frame(td_root)
                    if self.dec_plc.get() == 'hrz':
                        result_scroll = ttk.Scrollbar(result_frame)
                        result_box = Text(result_frame, yscrollcommand=result_scroll.set)
                        result_scroll.config(command=result_box.yview)
                        result_scroll.pack(side=RIGHT, fill=Y)
                        result_box.configure(wrap=WORD)
                    elif self.dec_plc.get() == 'ver':
                        result_scroll = ttk.Scrollbar(result_frame, orient='horizontal')
                        result_box = Text(result_frame, xscrollcommand=result_scroll.set)
                        result_scroll.config(command=result_box.xview)
                        result_scroll.pack(side=BOTTOM, fill=X)
                        result_box.configure(wrap=NONE)

                    result_box.insert('1.0', res)
                    result_box.configure(state=DISABLED)
                    result_frame.pack(expand=True, fill=BOTH)
                    result_box.pack(fill=BOTH, expand=True)
                except ValueError:
                    messagebox.showerror('EgonTE', 'there isn\'t a single character from the alphabet')
            else:
                messagebox.showerror('EgonTE', 'text box is empty')

        def change_style(s):
            global chosen_decorator
            chosen_decorator = s
            for style in styles:
                style.configure(bg='SystemButtonFace')
            if s == 1:
                bash_style.configure(bg='light grey')
            elif s == 2:
                binary_style.configure(bg='light grey')
            elif s == 4:
                asterisk_style.configure(bg='light grey')

        def cft():
            content = self.EgonTE.get('1.0', 'end')
            text_box.insert('end', content)

        def ptt():
            content = result_box.get('1.0', 'end')
            self.EgonTE.insert('end', '\n')
            self.EgonTE.insert('end', content)

        # settings variables
        self.dec_plc = StringVar()
        self.dec_plc.set('hrz')
        # window and it's widgets
        td_root = Toplevel()
        # td_root.resizable(False, False)
        td_root.minsize(355, 311)
        td_root.title(self.title_struct + 'text decorators')
        b_frame = Frame(td_root)
        t_frame = Frame(td_root)
        action_frame = Frame(b_frame)
        text_box = Text(t_frame, height=10, width=40, borderwidth=3)
        actions_title = Label(b_frame, text='Actions', font='arial 10 underline')
        enter_button = Button(b_frame, text='Enter', command=enter)
        copy_from_text = Button(b_frame, text='Copy from EgonTE', command=cft)
        paste_to_text = Button(b_frame, text='Paste to EgonTE', command=ptt, state=DISABLED)
        # setting
        settings_title = Label(b_frame, text='Settings', font='arial 10 underline')
        settings_frame = Frame(b_frame)
        vertical_radio = Radiobutton(settings_frame, text='Vertical', variable=self.dec_plc, value='ver')
        horizontal_radio = Radiobutton(settings_frame, text='Horizontal', variable=self.dec_plc, value='hrz')
        # text decorator styles
        styles_title = Label(b_frame, text='Styles', font='arial 10 underline')
        bash_style = Button(b_frame, text='bash (#)', command=lambda: change_style(1))
        binary_style = Button(b_frame, text='binary (10)', command=lambda: change_style(2))
        asterisk_style = Button(b_frame, text='asterisk (*)', command=lambda: change_style(4))

        t_frame.pack(expand=True, fill=BOTH)
        b_frame.pack()

        text_box.pack(expand=True, fill=BOTH)

        settings_title.grid(row=0, column=1)
        settings_frame.grid(row=1, column=1)
        vertical_radio.grid(row=1, column=0)
        horizontal_radio.grid(row=1, column=2)

        actions_title.grid(row=2, column=1)
        copy_from_text.grid(row=3, column=0)
        enter_button.grid(row=3, column=1)
        paste_to_text.grid(row=3, column=2)

        styles_title.grid(row=4, column=1)
        bash_style.grid(row=5, column=0)
        binary_style.grid(row=5, column=1)
        asterisk_style.grid(row=5, column=2)

        styles = [bash_style, binary_style, asterisk_style]
        change_style(1)

        self.record_list.append(f'> [{self.get_time()}] - Text decorators tool window opened')
        td_root.update_idletasks()
        print(td_root.winfo_width(), td_root.winfo_height())

    def stopwatch(self):
        start_time = time.time()
        while True:
            time.sleep(0.5)
            self.ut = timedelta(seconds=int(time.time() - start_time))
            if self.op_active:
                self.usage_time.configure(text=f' Usage time: {self.ut}')

    def merge_files(self):
        '''
        this function created a shared content from the content that on the main text box and from a content of
        another file
        '''
        data = ''

        def outport_data(where):
            ask_op_root.destroy()
            if where == 'new':
                save_file_name = filedialog.asksaveasfilename(title='Save merged file',
                                                              filetypes=(
                                                                  ('Text Files', '*.txt'), ('HTML FILES', '*.html'),
                                                                  ('Python Files', '*.py')))
                if save_file_name:
                    with open(save_file_name, 'w') as fp:
                        fp.write(data)
            else:
                self.EgonTE.delete('1.0', 'end')
                self.EgonTE.insert('1.0', data)
                if messagebox.askquestion('EgonTE', 'Would you like to save the changes right away'):
                    self.save()

        # saving the content from the text box
        data_1 = self.EgonTE.get('1.0', 'end')
        # getting a file name to merge the content with another file
        file_name = filedialog.askopenfilename(title='Open file to merge',
                                               filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html')))

        # Reading the file and combining the content
        if file_name:
            with open(file_name) as fp:
                data2 = fp.read()

            data = data_1 + '\n' + data2

            ask_op_root = Toplevel()
            ask_op_root.title(self.title_struct + 'merge files')
            q_label = Label(ask_op_root, text='where you would like to put the merged data?')
            this_file = Button(ask_op_root, text='In this file', command=lambda: outport_data('this'))
            new_file = Button(ask_op_root, text='In new file', command=lambda: outport_data('new'))

            q_label.grid(row=1, column=1)
            this_file.grid(row=2, column=0)
            new_file.grid(row=2, column=2)

    def delete_file(self):
        if self.file_name:
            if messagebox.askyesno('EgonTE', 'Are tou sure you want to delete this file?'):
                self.EgonTE.delete('1.0', 'end')
                os.remove(self.file_name)
                self.file_bar.configure(text=f'deleted {self.file_name}')
                self.file_name = ''
        else:
            messagebox.showerror(self.title_struct + 'error', 'you are not using a file')

    def insp_quote(self, op_msg=False):
        '''
        This function is outputting a formated text of a quote with the name of its owner with API
        '''
        # consider making the function a thread
        try:
            # making the get request
            response = requests.get('https://zenquotes.io/api/random')
            if response.status_code == 200:
                # extracting the core data
                json_data = loads(response.text)
                quote = json_data[0]['q'] + ' -' + json_data[0]['a']
            else:
                messagebox.showerror(self.title_struct + 'error', 'Error while getting quote')
        except:
            try:
                alt_response = requests.get('https://api-ninjas.com/api/quotes')
                json_data = alt_response.json()
                data = json_data['data']
                quote = data[0]['quoteText']
            except:
                if op_msg == False:
                    messagebox.showerror(self.title_struct + 'error', 'Something went wrong!')

        if quote:
            if op_msg:
                return quote
            else:
                self.EgonTE.insert('1.0', '\n')
                self.EgonTE.insert('1.0', quote)

    def save_images(self, widget_name, root_name, upper_name=False, sp_mode=False):
        '''
        this function saves an images with the info that its get from its paramaters via taking screenshot of it,
        it used to save the main text box content as an Image, and to take image for the handwriting tool of your
        canvas

        :param widget_name:
        :param root_name:
        :param upper_name:
        :param sp_mode:
        :return:
        '''
        screenshot_image = filedialog.asksaveasfilename() + '.png'
        root_name.attributes('-topmost', True)
        sp_x = 0
        if sp_mode == 'main':
            sp_x = (self.eFrame.winfo_width() - self.EgonTE.winfo_width())
            print(sp_x)
        print(sp_x)
        x = root_name.winfo_rootx() + widget_name.winfo_x() + sp_x
        if upper_name:
            y = root_name.winfo_rooty() + widget_name.winfo_y() + upper_name.winfo_height()
        else:
            y = root_name.winfo_rooty() + widget_name.winfo_y()
        x1 = x + widget_name.winfo_width()
        y1 = y + widget_name.winfo_height()
        image = ImageGrab.grab().crop((x, y, x1, y1))
        image.save(screenshot_image)
        root_name.attributes('-topmost', False)
        return screenshot_image

    def get_weather(self):
        '''
        this function will get you the info about the weather of the city you wrote via google
        '''

        def activate_weather():

            city_name = city_entry.get()

            ask_w.destroy()

            city_name = city_name.replace(' ', '+')
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
            try:
                # create url
                url = 'https://www.google.com/search?q=' + 'weather' + city_name
                html = requests.get(url).content
                location = city_name
                soup = BeautifulSoup(html, 'html.parser')
                temperature = soup.find('div', attrs={'class': 'BNeawe iBp4i AP7Wnd'}).text

                # this contains time and sky description
                string = soup.find('div', attrs={'class': 'BNeawe tAd8D AP7Wnd'}).text

                # format the data
                data = string.split('\n')
                time = data[0]
                info = data[1]

                # getting all div tag
                listdiv = soup.findAll('div', attrs={'class': 'BNeawe s3v9rd AP7Wnd'})
                strd = listdiv[5].text

                # getting other required data
                pos = strd.find('Wind')
                other_data = strd[pos:]
                working = True
            except:
                try:
                    res = requests.get(
                        f'https://www.google.com/search?q={city_name}&oq={city_name}&aqs=chrome.0.35i39l2j0l4j46j69i60.6128j1j7&sourceid=chrome&ie=UTF-8',
                        headers=headers)
                    soup = BeautifulSoup(res.text, 'html.parser')
                    location = soup.select('#wob_loc')[0].getText().strip()
                    time = soup.select('#wob_dts')[0].getText().strip()
                    info = soup.select('#wob_dc')[0].getText().strip()
                    temperature = soup.select('#wob_tm')[0].getText().strip()
                    working = True
                except:
                    messagebox.showerror('EgonTE', 'Please enter a valid city name')
                    working = False

            if working:
                weather_root = Toplevel()
                weather_root.title(self.title_struct + 'Weather')
                weather_root.tk.call('wm', 'iconphoto', weather_root._w, self.weather_image)
                w_font = 'arial 10'

                if '+' in location:
                    location = location.replace('+', ' ')

                loc_text = ('Location: ' + location)
                temp_text = ('Temperature: ' + temperature + '&deg;C')
                time_text = ('Time: ' + time)
                desc = ('Weather Description: ' + info)

                loc = Label(weather_root, text=loc_text, font=w_font)
                temp = Label(weather_root, text=temp_text, font=w_font)
                tim = Label(weather_root, text=time_text, font=w_font)
                des = Label(weather_root, text=desc, font=w_font)
                copy_button = Button(weather_root, text='Copy', command=copy_paste_weather, pady=2, bd=1)
                paste_button = Button(weather_root, text='Paste to ETE', command=lambda: copy_paste_weather('p')
                                      , pady=2, bd=1)

                loc.pack(fill="none", expand=True)
                temp.pack(fill="none", expand=True)
                tim.pack(fill="none", expand=True)
                des.pack(fill="none", expand=True)
                copy_button.pack(fill="none", expand=True)
                paste_button.pack(fill="none", expand=True)

        city_list = ['Agra', 'Aires', 'Amsterdam', 'Angeles', 'Antalya', 'Athens', 'Atlanta', 'Auckland', 'Bali',
                     'Bangkok', 'Barcelona', 'Beijing', 'Berlin', 'Bogotá', 'Boston', 'Brussels', 'Bucharest',
                     'Budapest', 'Buenos', 'Cairo', 'Cana', 'Cancún', 'Cape', 'Chennai', 'Chí', 'Chicago', 'City',
                     'Copenhagen', 'D.C.', 'Dallas', 'de', 'Delhi', 'Diego', 'Dubai', 'Dublin', 'Edinburgh', 'Edirne',
                     'el - Sheikh', 'Florence', 'Francisco', 'Guangzhou', 'Hà', 'Hồ', 'Hong', 'Honolulu', 'Houston',
                     'Istanbul', 'Jakarta', 'Janeiro', 'Jerusalem', 'Johannesburg', 'Kiev']

        def copy_paste_weather(m='copy'):
            all_content = f'{loc_text}\n{temp_text}\n{time_text}\n{desc}'
            if m == 'copy':
                copy(all_content)
            else:
                self.EgonTE.insert('end', '\n')
                self.EgonTE.insert('end', all_content)

        def rand_city():
            choosen_city = choice(city_list)
            print(choosen_city)
            city_entry.delete(0, END)
            city_entry.insert(0, choosen_city)

        # a more advanced window to select the city
        ask_w = Toplevel()
        ask_w.title(self.title_struct + 'city selector')
        ask_w.resizable(False, False)

        ask_title = Label(ask_w, text='Select city', font=self.titles_font)
        desc = Label(ask_w, text='What is the name of the city\n you want to get the weather for')
        city_entry = Entry(ask_w)
        random_city = Button(ask_w, text='Random known city', command=rand_city, bd=1)
        enter_city = Button(ask_w, text='Enter', command=activate_weather, bd=1)

        ask_title.grid(row=0, column=1, pady=3)
        desc.grid(row=1, column=1)
        city_entry.grid(row=2, column=1)
        random_city.grid(row=3, column=1, pady=3)
        enter_city.grid(row=4, column=1, pady=5)

    def send_email(self):
        global custom_text

        file_type = 'external'
        custom_text = False

        def file_mode(mode):
            global file_type, custom_box, custom_text
            if mode == 't':
                file_type = 'this'
                loc_button.configure(bg='SystemButtonFace')
                custom_button.configure(bg='SystemButtonFace')
                th_button.configure(bg='light grey')
                if custom_text:
                    custom_box.destroy()
                    custom_text = False
            elif mode == 'c':
                custom_button.configure(bg='light grey')
                loc_button.configure(bg='SystemButtonFace')
                th_button.configure(bg='SystemButtonFace')
                file_type = 'none'
                custom_box = Text(email_root)
                custom_box.grid(row=9, column=1)
                custom_text = True
            else:
                file_type = 'local'
                loc_button.configure(bg='light grey')
                custom_button.configure(bg='SystemButtonFace')
                th_button.configure(bg='SystemButtonFace')
                if custom_text:
                    custom_box.destroy()
                    custom_text = False

        def content():
            global file_name, file_type
            if file_type == 'local':
                try:
                    file_name = filedialog.askopenfilename()
                    if file_name:
                        with open(file_name) as fp:
                            file_content = fp.read()
                except UnicodeDecodeError:
                    messagebox.showerror('EgonTE', 'file contains unsupported characters')
            elif file_type == 'this':
                file_name = self.file_name
                file_content = self.EgonTE.get('1.0', 'end')
            else:
                file_name = f'A message from {sender_box.get()}'
                if custom_box:
                    file_content = custom_box.get('1.0', 'end')

            return file_content

        def send():
            # initialize the library
            msg = EmailMessage()

            # email's content
            if subject_box.get():
                msg['Subject'] = subject_box.get()
            else:
                try:
                    msg['Subject'] = f'The contents of {file_name}'
                except NameError:
                    msg['Subject'] = 'An email'
            msg['From'] = sender_box.get()
            msg['To'] = receiver_box.get()
            msg.set_content(content())
            # adding a layer of security
            context = ssl.create_default_context()
            # Send the message via our own SMTP server.
            with smtplib.SMTP_SSL('smpt.gamil.com', 465, context=context) as mail:
                mail.login(sender_box.get(), password=password_box.get())
                mail.sendmail(sender_box.get(), receiver_box.get(), msg.as_string())

            # s = smtplib.SMTP('localhost')
            # s.send_message(msg)
            # s.quit()

        messagebox.showinfo('EgonTE', 'you might cannot use this function\n if you have 2 step verification')
        email_root = Toplevel()
        email_root.title(self.title_struct + 'send emails')
        req = Label(email_root, text='Requirements', font='arial 12 underline')
        sender_title = Label(email_root, text='Your Email:')
        password_title = Label(email_root, text='Your Password:')
        receiver_title = Label(email_root, text='Receiver Email:')
        sender_box = Entry(email_root, width=25)
        password_box = Entry(email_root, width=25, show='*')
        receiver_box = Entry(email_root, width=25)
        content_title = Label(email_root, text='Content:', font='arial 12 underline')
        subject_title = Label(email_root, text='subject:')
        subject_box = Entry(email_root, width=25)

        files_title = Label(email_root, text='Body:')
        loc_button = Button(email_root, text='Local file', command=lambda: file_mode('l'), borderwidth=1)
        custom_button = Button(email_root, text='Custom', command=lambda: file_mode('c'), borderwidth=1)
        th_button = Button(email_root, text='This file', command=lambda: file_mode('t'), borderwidth=1)
        send_button = Button(email_root, text='Send', command=send, font='arial 10 bold')

        req.grid(row=0, column=1, pady=2)
        sender_title.grid(row=1, column=0)
        password_title.grid(row=1, column=1)
        receiver_title.grid(row=1, column=2)
        sender_box.grid(row=2, column=0, padx=5)
        password_box.grid(row=2, column=1)
        receiver_box.grid(row=2, column=2, padx=5)
        content_title.grid(row=3, column=1, pady=2)
        subject_title.grid(row=4, column=1)
        subject_box.grid(row=5, column=1, padx=5)
        files_title.grid(row=6, column=1)
        loc_button.grid(row=7, column=0)
        custom_button.grid(row=7, column=1)
        th_button.grid(row=7, column=2, pady=4)
        send_button.grid(row=10, column=1, pady=2)

        self.record_list.append(f'> [{self.get_time()}] - Email tool window opened')
        file_mode('t')

    def chatGPT(self):
        '''
        this function attempts to create a chatGPT workspace like the website via the text editor
        note: this function wasnt tested properly so its probably isnt good
        '''
        working = True

        def active_bot():
            global working

            # requirements for the openAI official API
            if openai_library:
                try:
                    self.key_page(active_ui)

                # simple error handling for the main login function (openAI library - via keys)
                except:
                    messagebox.showerror('EgonTE', 'Some error has occurred in the login process')

            # requirements for third-party library
            else:
                try:
                    global login_root

                    # sign in function
                    def enter():
                        options = Options()
                        options.record = True
                        options.track = True
                        options.proxies = 'http://localhost:8080'
                        self.alt_chat = Chat(email=email_entry.get(), password=password_entry.get(), options=options)
                        login_root.destroy()
                        active_ui()

                    # custom login interface exclusively for this library
                    login_root = Toplevel()
                    login_root.resizable(False, False)
                    login_root.title(self.title_struct + 'sign to ChatGPT')
                    email_title = Label(login_root, text='username:')
                    email_entry = Entry(login_root, width=25)
                    password_title = Label(login_root, text='password:')
                    password_entry = Entry(login_root, width=25, show='*')
                    enter_button = Button(login_root, text='Enter', command=enter)

                    email_title.grid(row=1, column=1)
                    email_entry.grid(row=2, column=1, padx=10)
                    password_title.grid(row=3, column=1)
                    password_entry.grid(row=4, column=1)
                    enter_button.grid(row=6, column=1, pady=5)


                # error handling for the custom library
                except Exception as gpt_expection:
                    working = False
                    e_label = Label(login_root, text=str(gpt_expection), fg='red')
                    e_label.grid(row=5, column=1)
                    print(gpt_expection)
                    print(working)

        def active_ui():
            global txt
            gpt_root = Toplevel()
            gpt_root.title(self.title_struct + 'ChatGPT')
            gpt_root.tk.call('wm', 'iconphoto', gpt_root._w, self.gpt_image)
            BG_GRAY = '#ABB2B9'
            BG_COLOR = '#444454'
            TEXT_COLOR = '#EAECEE'
            FONT = 'Helvetica 14'
            FONT_BOLD = 'Helvetica 13 bold'

            interact_frame = Frame(gpt_root)

            text_frame = Frame(gpt_root)
            text_frame.pack(fill=BOTH, expand=True)
            scroll = ttk.Scrollbar(text_frame)
            scroll.pack(side=RIGHT, fill=Y)

            # title_gpt = Label(gpt_root, bg=BG_COLOR, fg=TEXT_COLOR, text='ChatGPT', font='Helvetica 13 bold',
            #                  pady=10, width=20, height=1)
            txt = Text(text_frame, bg=BG_COLOR, fg=TEXT_COLOR, font=FONT, width=60, yscrollcommand=scroll.set,
                       undo=True, wrap=WORD, cursor=self.predefined_cursor, state=DISABLED)
            txt.pack(fill=BOTH, expand=True)
            scroll.config(command=txt.yview)

            self.gpt_entry = Entry(interact_frame, bg='#2C3E50', fg=TEXT_COLOR, font=FONT, width=55)
            send = Button(interact_frame, text='Send', font=FONT_BOLD, bg=BG_GRAY, command=ask_gpt)
            interact_frame.pack()

            self.gpt_entry.grid(row=0, column=0)
            send.grid(row=0, column=1)
            # title_gpt.grid(row=0)
            # txt.grid(row=1, column=0, columnspan=2)
            # self.gpt_entry.grid(row=2, column=0)
            # send.grid(row=2, column=1)

            gpt_root.bind('<Return>', ask_gpt)

            # trying to make the image not crash
            # self.update()
            # gpt_root.mainloop()

            self.record_list.append(f'> [{self.get_time()}] - ChatGPT tool window opened')

        def ask_gpt(event=None):
            txt.configure(state=NORMAL)
            try:
                if openai_library:
                    openai.api_key = self.key  # os.getenv(self.key)
                    completion = openai.ChatCompletion.create(
                        model='gpt-3.5-turbo',
                        messages=[
                            {'role': 'user',
                             'content': self.gpt_entry.get()}
                        ]
                    )
                    answer = (completion.choices[0].message.content)

                else:
                    answer = self.alt_chat.ask(self.gpt_entry.get())
                txt.insert(END, '\n' + answer)
            except openai.error.RateLimitError:
                messagebox.showerror('OpenAI',
                                     'You exceeded your current quota, please check your plan and billing details')
            txt.configure(state=DISABLED)

        # checking multiple libraries / keys to find the most effective window
        if openai_library:
            if self.key:
                active_ui()
            else:
                active_bot()
        else:
            active_bot()

    def dallE(self):
        '''
        rhis function will try to return you the result of a simple DallE prompt with some options
        note: this function wasnt tested properly so its probably isnt good
        '''
        PROMPT = 'An eco-friendly computer from the 90s in the style of vaporwave'
        im_size_var = StringVar()
        im_size_var.set('256x256')

        def imagine():
            global PROMPT
            if prompt_entry.get():
                PROMPT = prompt_entry.get()
            try:
                response = openai.Image.create(prompt=PROMPT, n=1, size=im_size_var.get())
                result = (response['data'][0]['url'])
                label = Label(dallE_root, text=result)
            except openai.error.RateLimitError:
                messagebox.showerror('OpenAI',
                                     'You exceeded your current quota, please check your plan and billing details')
            label.grid(row=5)

        def ui():
            global prompt_entry, dallE_root
            dallE_root = Toplevel()
            dallE_root.title(self.title_struct + 'DallE')
            prompt_title = Label(dallE_root, text='Enter the prompt here', font='arial 10 underline')
            prompt_entry = Entry(dallE_root, width=30)
            size_title = Label(dallE_root, text='Size of output', font='arial 10 underline')
            size_256 = Radiobutton(dallE_root, variable=im_size_var, value='256x256', text='256x256')
            size_512 = Radiobutton(dallE_root, variable=im_size_var, value='512x512', text='512x512')
            size_1024 = Radiobutton(dallE_root, variable=im_size_var, value='1024x1024', text='1024x1024')
            size_1536 = Radiobutton(dallE_root, variable=im_size_var, value='1536x1536', text='1536x1536')
            size_2048 = Radiobutton(dallE_root, variable=im_size_var, value='2048x2048', text='2048x2048')

            imagine_button = Button(dallE_root, text='Imagine', command=imagine, font='arial 10 bold')

            prompt_title.grid(row=1, column=1)
            prompt_entry.grid(row=2, column=1)
            size_title.grid(row=3, column=1)
            size_256.grid(row=4, column=0)
            size_512.grid(row=4, column=1)
            size_1024.grid(row=4, column=2)
            size_1536.grid(row=5, column=0)
            size_2048.grid(row=5, column=2)
            imagine_button.grid(row=6, column=1, pady=4)

            self.record_list.append(f'> [{self.get_time()}] - Dall-E tool window opened')

        if not self.key:
            self.key_page(ui)
        else:
            ui()

    def key_page(self, after_func=None):
        '''
        this function will get your OpenAI key to make the usage of chatGPT and DallE possible via the program

        :param after_func:
        '''

        def enter():
            try:
                self.key = key_entry.get()
                openai.api_key = self.key
                login_root.destroy()

                if after_func:
                    after_func()

                return True
            except openai.error.AuthenticationError:
                messagebox.showerror('EgonTE', 'Error not provided/Incorrect key')
                return False

        def key_link(url):
            webbrowser.open_new(url)

        login_root = Toplevel()
        login_root.resizable(False, False)
        login_root.geometry('350x120')
        login_root.title(self.title_struct + 'connect to OpenAI')

        login_title = Label(login_root, text='Enter your OpenAI key to connect', font='arial 12')
        key_title = Label(login_root, text='Key entry', font='arial 12 underline')
        key_entry = Entry(login_root, width=35, show='*')
        get_key = Label(login_root, text='Dosen\'t have/forget key?', fg='blue', font='arial 10 underline')
        enter_button = Button(login_root, text='Enter', font='arial 10 bold', command=enter, relief=FLAT)

        login_title.pack()
        key_title.pack(expand=True, fill='none')
        key_entry.pack(expand=True, fill='none')
        get_key.pack(expand=True, fill='none')
        enter_button.pack(expand=True, fill='none')

        get_key.bind('<Button-1>', lambda e: key_link('https://platform.openai.com/account/api-keys'))

        self.record_list.append(f'> [{self.get_time()}] - OpenAI API login page opened')

        login_root.mainloop()

    def full_screen(self, event=None):
        self.fs_value = not (self.fs_value)
        self.attributes('-fullscreen', self.fs_value)

    def topmost(self):
        self.tm_value = not (self.tm_value)
        self.attributes('-topmost', self.tm_value)

    def transcript(self):
        '''
        this function will attempt to return you the transcript of a youtube video or a wav file
        note: wasnt tested because of venv errors
        '''

        def youtube():
            tr_root = Toplevel()
            tr_root.title(self.title_struct + 'youtube transcript')
            video_id = simpledialog.askstring('EgonTE', 'please enter the video ID')
            if video_id:
                tr = YouTubeTranscriptApi.get_transcript(video_id)
                tr_str = ''
                for t in tr:
                    tr_str += f'text: {t["text"]}, starting: {t["start"]}\n'

                text_frame = Frame(tr_root)
                scroll = ttk.Scrollbar(text_frame)
                tr_text = Text(text_frame, cursor=self.predefined_cursor, yscrollcommand=scroll.set)
                tr_text.insert('1.0', tr_str)
                tr_text.configure(state=DISABLED)
                scroll.config(command=tr_text.yview)
                copy_button = Button(tr_root, text='Copy', command=lambda: copy(tr_str))
                text_frame.pack(expand=True, fill=BOTH)
                scroll.pack(side=RIGHT, fill=Y)
                tr_text.pack(expand=True, fill=BOTH)
                copy_button.pack()

        def file_trans():
            file_name = filedialog.askopenfilename(title='Open file to Transcribe', filetypes=[('mp3 file', '*.mp3')])
            if file_name:
                sound = AudioSegment.from_mp3(file_name)
                pre, ext = os.path.splitext(file_name)
                os.rename(file_name, pre + '.wav')
                sound.export(file_name, format='wav')

                # transcribe audio file
                AUDIO_FILE = f'{pre}.wav'

                # use the audio file as the audio source
                r = Recognizer()
                with AudioFile(AUDIO_FILE) as source:
                    audio = r.record(source)  # read the entire audio file

                    content = r.recognize_google(audio)

                file_trans_root = Toplevel()
                file_trans_root.title(self.title_struct + 'file transcript')
                transcript = Text(file_trans_root)
                transcript.insert('1.0', content)
                transcript.configure(state=DISABLED)

        if yt_api:
            trans_option = Toplevel()
            op_label = Label(trans_option, text='Where you want to take the content from', font='arial 12')
            youtube_button = Button(trans_option, text='Youtube', command=youtube)
            file_button = Button(trans_option, text='File')
            op_label.grid(row=1, column=1)
            youtube_button.grid(row=2, column=0)
            file_button.grid(row=2, column=2)
        else:
            file_trans()

    def content_stats(self):
        '''
        This function will output you the stats of the content of the file,
        many numeric values, presentation in a table about the usage of words and characters, and more
        '''

        res_font = 'arial 10'
        special_characters = list(printable[62:])
        print(special_characters)

        stats_root = Toplevel()
        stats_root.title(self.title_struct + 'Content statistics')

        content = self.EgonTE.get('1.0', 'end')
        lines_, characters, words_ = self.status_var.get().split(' ')

        symbols = 0

        m_special_characters = ''.join(special_characters)
        m_special_characters = m_special_characters.replace(' ', '')
        m_special_characters = m_special_characters.replace('\n', '')

        print(m_special_characters)
        for i in range(len(content)):
            # checking if any special character is present in given string or not
            if content[i] in m_special_characters:
                symbols += 1

        numbers = len(findall(r'\d+', content))
        # set can contain duplicate values so by checking the length we can see the number of diffrent characters
        different_characters = len(set(content.lower()))
        # if we split the content to a list by whitespace we can do the same thing for words
        different_words = len(set((content.lower()).split(' ')))
        # calculate the alphabets character count using loop and a condition
        alphabets_count = 0
        for i in content:
            if i.isalpha():
                alphabets_count += 1

        temp_file = open('temp_EgonTE.txt', 'w')
        temp_file.write(content)
        temp_file.close()
        paragraph = 0
        content_lines = open('temp_EgonTE.txt', 'r').readlines()

        for idx, c_line in enumerate(content_lines):
            if not c_line == '\n':
                m = reSearch(r'\w', c_line)
                if m is not None:
                    string = m.group(0)
                else:
                    raise messagebox.showerror('Error', 'an error has occurred')

            try:
                # if the line is a newline, and the previous line has a str in it, then
                # count it as a paragraph.
                if c_line == '\n' and string in content_lines[idx - 1]:
                    paragraph += 1
            except:
                pass

        if content_lines[-1] != '\n':  # if the last line is not a new line, count a paragraph.
            paragraph += 1

        temp_file.close()
        del temp_file

        # ratios
        try:
            words_per_lines = round(len(content.split(' ')) / lines, 2)
        except ZeroDivisionError:
            words_per_lines = 0
        try:
            characters_per_words = round(alphabets_count / words, 2)
        except ZeroDivisionError:
            characters_per_words = 0
        try:
            lines_per_paragraphs = round(lines / paragraph, 2)
        except ZeroDivisionError:
            lines_per_paragraphs = 0

        # count the specific word / character in the text

        words_per_line = reSplit('; |, |\*|\n', content)

        print(f'splited content: {words_per_line}')

        m_words_per_line = []
        for word in words_per_line:
            if ' ' in word:
                word = word.split(' ')
            m_words_per_line.extend(word)

        words_per_line = m_words_per_line
        print(f'splited content: {words_per_line}')

        words_per_line = dict(Counter(words_per_line))
        words_value, words_number = words_per_line.keys(), words_per_line.values()

        # making a clear content (only alphabetic characters) to make the words' graph more accurate and clean
        cleared_content_list = []
        del_count = []
        for count, word_value in enumerate(words_value, 0):
            for special_character in special_characters:

                if special_character in word_value:
                    word_value = word_value.replace(special_character, '')

            cleared_content_list.append(word_value)
            if word_value.isdigit():
                del_count.append(word_value)
        if '' in cleared_content_list:
            cleared_content_list.remove('')
        print(f'clear content list: {cleared_content_list}')
        # cleared_content = cleared_content[-1]

        # making the dictionary without symbols to advance the cleaning process
        cleared_words_per_line = {}
        for i, cc in enumerate(cleared_content_list):
            cleared_words_per_line[cc] = list(words_number)[i]
        print(cleared_words_per_line)

        # deletion loop - deleting from the dictionary the numbers
        for d in del_count:
            del cleared_words_per_line[d]

        print(f'clear dictionary: {cleared_words_per_line}')

        cleared_content = ' '.join(cleared_content_list)
        print(f'clear string: {cleared_content}')

        top_word_list = (nlargest(8, cleared_words_per_line.items(), key=lambda x: x[1]))
        top_dictionary = {}
        for key, value in top_word_list:
            top_dictionary[key] = value

        print(f'top dictionary: {top_dictionary}')

        top_words_value, top_words_number = top_dictionary.keys(), top_dictionary.values()

        w_frame = Frame(stats_root)
        word_figure = Figure(figsize=(5, 3), dpi=100)
        word_figure_canvas = FigureCanvasTkAgg(word_figure, w_frame)
        NavigationToolbar2Tk(word_figure_canvas, w_frame)
        word_axes = word_figure.add_subplot()
        word_axes.bar(top_words_value, top_words_number)
        word_axes.set_ylabel('Frequency')
        word_axes.set_xlabel('Words')

        word_c = Counter(findall(r"[a-z']+", sub(r" '+ ", " ", content.lower())))

        character_count = {}
        for letter in printable[10:36]:
            character_count[letter] = (content.lower()).count(letter)
        characters_value, characters_number = character_count.keys(), character_count.values()

        c_frame = Frame(stats_root)
        character_figure = Figure(figsize=(5, 3), dpi=100)
        character_figure_canvas = FigureCanvasTkAgg(character_figure, c_frame)
        NavigationToolbar2Tk(character_figure_canvas, c_frame)
        character_axes = character_figure.add_subplot()
        character_axes.bar(characters_value, characters_number)
        character_axes.set_ylabel('Frequency')
        character_axes.set_xlabel('Characters')

        label_frame = Frame(stats_root)
        char_label = Label(label_frame, text=f'{characters}', font=res_font)
        alpha_label = Label(label_frame, text=f'Alphabet characters {alphabets_count}')
        words_label = Label(label_frame, text=f'{words_}', font=res_font)
        lines_label = Label(label_frame, text=f'{lines_}', font=res_font)
        nums_label = Label(label_frame, text=f'Numbers: {numbers}', font=res_font)
        sym_label = Label(label_frame, text=f'Symbols: {symbols}', font=res_font)
        diff_c_label = Label(label_frame, text=f'Different characters: {different_characters}', font=res_font)
        diff_w_label = Label(label_frame, text=f'Different words: {different_words}', font=res_font)
        wpl_label = Label(label_frame, text=f'Words per lines: {words_per_lines}', font=res_font)
        cpw_label = Label(label_frame, text=f'Characters per words: {characters_per_words}', font=res_font)
        para_label = Label(label_frame, text=f'Paragraphs: {paragraph}', font=res_font)
        lpp_label = Label(label_frame, text=f'Lines per paragraphs: {lines_per_paragraphs}', font=res_font)

        word_tt = Label(w_frame, text='Top words', font=self.titles_font)
        word_tl = word_figure_canvas.get_tk_widget()

        characters_tt = Label(c_frame, text='Top characters', font=self.titles_font)
        characters_tl = character_figure_canvas.get_tk_widget()

        label_frame.pack()
        char_label.grid(row=1, column=0)
        alpha_label.grid(row=1, column=2)
        words_label.grid(row=2, column=0)
        lines_label.grid(row=2, column=2)
        para_label.grid(row=3, column=0)
        nums_label.grid(row=3, column=2)
        sym_label.grid(row=4, column=0)
        diff_c_label.grid(row=4, column=2)
        diff_w_label.grid(row=5, column=0)
        wpl_label.grid(row=5, column=2)
        cpw_label.grid(row=6, column=0)
        lpp_label.grid(row=6, column=2)

        w_frame.pack(expand=True, fill=BOTH)
        word_tt.pack(fill=X)
        word_tl.pack(expand=True, fill=BOTH)

        c_frame.pack(expand=True, fill=BOTH)
        characters_tt.pack(fill=X)
        characters_tl.pack(expand=True, fill=BOTH)

        self.record_list.append(f'> [{self.get_time()}] - Content\'s statistics tool window opened')

    def record_(self):
        '''
        the ability to use this function is activated when you active developer mode via options menu.
        this function captures all / most the main events that happened in the program and writes them
        in order with the time of the occurrence
        '''

        def close():
            self.record_window = False
            log_root.destroy()

        log_root = Toplevel()
        log_root.title(self.title_struct + 'events\' record')
        self.record_window = True
        log_root.protocol("WM_DELETE_WINDOW", close)

        scrollbar = ttk.Scrollbar(log_root)
        record_tb = Text(log_root, cursor=self.predefined_cursor, relief=self.predefined_relief,
                         yscrollcommand=scrollbar.set)
        for record in self.record_list:
            record_tb.insert('end', record + '\n')

        scrollbar.pack(side=RIGHT, fill=Y)
        record_tb.pack(fill=BOTH, expand=True)
        scrollbar.config(command=record_tb.yview)
        record_tb.configure(state=DISABLED)

        while self.record_window:
            time.sleep(1)
            if self.record_window:
                # condition is important if we want the tool to be a lot smoother, but it's also fine without it
                record_string = ''.join(self.record_list).replace('\n', '')
                record_textbox = record_tb.get(1.0, END).replace('\n', '')
                if record_string != record_textbox:
                    record_tb.configure(state=NORMAL)
                    record_tb.delete(1.0, END)
                    for record in self.record_list:
                        record_tb.insert('end', record + '\n')
                    record_tb.configure(state=DISABLED)

    def manage_menus(self, mode):
        '''
        this window mannage the diffrent menu modes that the program heve, is can delete menus, call the create menus
        function, change / add things to capture the mode that the user selected for the program
        '''
        if mode == 'dev':
            if self.dm.get():
                self.app_menu.delete('Record')
                self.app_menu.delete('Git')
                self.options_menu.delete('prefer gpu')
                try:
                    self.menus_components.remove(self.git_menu)
                except:
                    self.menus_components.pop(-1)
            else:
                self.app_menu.add_cascade(label='Record', command=lambda: Thread(target=self.record_).start())
                self.options_menu.add_checkbutton(label='prefer gpu', variable=self.prefer_gpu)

                self.git_menu = Menu(self.app_menu, tearoff=False)
                self.app_menu.add_cascade(label='Git', menu=self.git_menu)
                self.git_menu.add_command(label='Pull', command=lambda: gitp('pull'))
                self.git_menu.add_command(label='Push', command=lambda: gitp('push'))
                self.git_menu.add_command(label='Commit', command=lambda: gitp('commit'))
                self.git_menu.add_command(label='Add', command=lambda: gitp('add'))
                self.git_menu.add_separator()
                self.git_menu.add_command(label='Clone', state=gstate, command=lambda: gitp('clone'))
                self.git_menu.add_command(label='Commit data', state=gstate, command=lambda: gitp('c.d'))
                self.git_menu.add_command(label='Repository Information', state=gstate, command=lambda: gitp('r.i'))
                self.git_menu.add_separator()
                self.git_menu.add_command(label='Custom command', command=lambda: gitp('excute'))

                self.menus_components.append(self.git_menu)

            self.dm.set(not (self.dm.get()))
        elif mode == 'tools':
            if not (self.sta.get()):
                self.app_menu.delete('Colors+')
                self.app_menu.delete('Tools')
            else:

                self.app_menu.delete('NLP')
                self.app_menu.delete('Options')
                self.app_menu.delete('Help')
                self.app_menu.delete('Patch notes')
                self.app_menu.delete('GitHub')

                if self.dm.get():
                    self.app_menu.delete('Record')
                    self.app_menu.delete('Git')
                    self.options_menu.delete('prefer gpu')

                self.create_menus(initial=False)

                if self.dm.get():
                    self.app_menu.add_cascade(label='Record', command=lambda: Thread(target=self.record_).start())
        elif mode == 'python':
            # python menu
            if self.python_file:
                self.app_menu.add_cascade(label='Run', command=self.run_code)
                self.app_menu.add_cascade(label='Clear console', command=self.clear_console)

                self.options_menu.add_separator()
                self.options_menu.add_checkbutton(label='Auto clear console', variable=self.auto_cc)
                self.options_menu.add_checkbutton(label='Save by running', variable=self.sar)

            # self.sta.set(not(self.sta.get()))

    def get_k_lang(self):
        '''
        this function gets the keyboard language in use by the current active window process.
        '''

        languages = {
            '0x409': ['English - United States', 'en'], '0x809': ['English - United Kingdom', 'en'],
            '0x0c09': ['English - Australia', 'en'], '0x2809': ['English - Belize', 'en'],
            '0x1009': ['English - Canada', 'en'], '0x2409': ['English - Caribbean', 'en'],
            '0x3c09': ['English - Hong Kong SAR', 'en'],
            '0x4009': ['English - India', 'en'], '0x3809': ['English - Indonesia', 'en'],
            '0x1809': ['English - Ireland', 'en'], '0x2009': ['English - Jamaica', 'en'],
            '0x4409': ['English - Malaysia', 'en'],
            '0x040c': ['French - France', 'fr'], '0x080c': ['French - Belgium', 'fr'],
            '0x407': ['German - Germany', 'de'], '0x0c07': ['German - Austria', 'de'],
            '0x1407': ['German - Liechtenstein', 'de'],
            '0x1007': ['German - Luxembourg', 'de'], '0x807': ['German - Switzerland', 'de'],
            '0x410': ['Italian - Italy', 'it'], '0x810': ['Italian - Switzerland', 'it'],
            '0x816': ['Portuguese - Portugal', 'pt'], '0x429': ['Farsi', 'fa'],
            '0x0c0a': ['Spanish - Spain (Modern Sort)', 'es'], '0x040a': ['Spanish - Spain (Traditional Sort)', 'es'],
        }

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

    def emoticons(self, reverse):
        content = self.EgonTE.get('1.0', 'end').split(' ')
        new_content = []
        for word in content:
            if reverse:
                word = demoticon(word)
            else:
                word = emoticon(word)
            new_content.append(word)
        ' '.join(new_content)
        self.EgonTE.delete('1.0', 'end')
        self.EgonTE.insert('1.0', new_content)

    def emojicons_hub(self):
        '''
        this function is used the connect all the operation with emojis, emoticons and roman numbers
        its a UI for the detection and the via verse process, for the lists and for a random output of item
        from the selected set of characters (emojis, emoticons, roman numbers)
        '''
        global morse_code_dict
        self.spc_mode = 'emojis'

        morse_code_dict = {'A': '.-', 'B': '-...',
                           'C': '-.-.', 'D': '-..', 'E': '.',
                           'F': '..-.', 'G': '--.', 'H': '....',
                           'I': '..', 'J': '.---', 'K': '-.-',
                           'L': '.-..', 'M': '--', 'N': '-.',
                           'O': '---', 'P': '.--.', 'Q': '--.-',
                           'R': '.-.', 'S': '...', 'T': '-',
                           'U': '..-', 'V': '...-', 'W': '.--',
                           'X': '-..-', 'Y': '-.--', 'Z': '--..',
                           '1': '.----', '2': '..---', '3': '...--',
                           '4': '....-', '5': '.....', '6': '-....',
                           '7': '--...', '8': '---..', '9': '----.',
                           '0': '-----', ', ': '--..--', '.': '.-.-.-',
                           '?': '..--..', '/': '-..-.', '-': '-....-',
                           '(': '-.--.', ')': '-.--.-', ' ': '/'
                           # ,'Á': '.--.-', 'Ä': '.-.-', 'É': '..-..', 'Ñ': '- - . - -',
                           # 'Ö': '- - - .', 'Ü': '. . - -'
                           }
        self.roman_dict = {
            'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000,
            'IV': 4, 'IX': 9, 'XL': 40, 'XC': 90, 'CD': 400, 'CM': 900}

        def change_mode(b='j'):
            for button in b_mode_list:
                button.configure(background='SystemButtonFace')

            if b == 'j':
                self.spc_mode = 'emojis'
                emojis.configure(background='light gray')
            elif b == 'm':
                self.spc_mode = 'morse'
                morse_c.configure(background='light gray')
            elif b == 'r':
                self.spc_mode = 'roman'
                roman_numbers.configure(background='light gray')
            else:
                self.spc_mode = 'emoticons'
                emoticons.configure(background='light gray')

            list_of.configure(text=f'List of {self.spc_mode}')
            transform.configure(text=f'Transform to {self.spc_mode}')
            random_e.configure(text=f'Random {self.spc_mode}')

            print(self.spc_mode)

        def transf(reverse=False):
            if self.spc_mode == 'emojis':
                self.emoji_detection(via_settings=True, reverse=reverse)
            elif self.spc_mode == 'morse':
                self.morse_c_translator(reverse=reverse)
            elif self.spc_mode == 'roman':
                self.roman_numbers_translator(reverse=reverse)
            else:
                self.emoticons(reverse=reverse)

        def random_ejc():

            if self.spc_mode == 'emojis':
                ejc_list = emoji.get_emoji_unicode_dict('en')
                rdm_e = ejc_list.values()
            elif self.spc_mode == 'morse':
                rdm_e = morse_code_dict.values()
            elif self.spc_mode == 'roman':
                rdm_e = self.roman_dict.values()

            if rdm_e:
                rdm_e = choice(list(rdm_e)) + ' '
                self.EgonTE.insert('end', rdm_e)

        ejc_root = Toplevel()
        ejc_root.resizable(False, False)
        ejc_root.title(self.title_struct + 'Symbols translator')
        m_title = Label(ejc_root, text='Choose a mode', font=self.titles_font)
        emojis = Button(ejc_root, text='Emojis', command=lambda: change_mode('j'), borderwidth=1)
        emoticons = Button(ejc_root, text='Emoticons', command=lambda: change_mode('c'), borderwidth=1,
                           state=emoticons_library)
        morse_c = Button(ejc_root, text='Morse Code', command=lambda: change_mode('m'), borderwidth=1)
        roman_numbers = Button(ejc_root, text='Roman numbers', command=lambda: change_mode('r'), borderwidth=1)
        f_title = Label(ejc_root, text='Functions', font=self.titles_font)
        transform = Button(ejc_root, text=f'Transform to {self.spc_mode}', borderwidth=1, command=transf)
        return_to_text = Button(ejc_root, text='Return to normal', borderwidth=1, command=lambda: transf(True))
        list_of = Button(ejc_root, text=f'List of {self.spc_mode}', borderwidth=1,
                         command=lambda: self.e_list(mode=self.spc_mode))
        random_e = Button(ejc_root, text=f'Random {self.spc_mode}', borderwidth=1, command=random_ejc)

        m_title.grid(row=0, column=1, pady=10)
        emojis.grid(row=1, column=0)
        morse_c.grid(row=1, column=1)
        emoticons.grid(row=1, column=2)
        roman_numbers.grid(row=2, column=1, pady=3)
        f_title.grid(row=3, column=1, pady=10)
        transform.grid(row=4, column=0, padx=5)
        list_of.grid(row=4, column=1)
        return_to_text.grid(row=4, column=2, padx=5)
        random_e.grid(row=5, column=1, pady=5)

        b_mode_list = emojis, emoticons, morse_c, roman_numbers
        b_func_list = transform, list_of, random_e
        change_mode()

    # according to the morse code chart
    def morse_c_translator(self, reverse=False):
        '''
        translator of morse code and vice versa

        :param reverse:
        '''
        if not (reverse):
            content = reSplit('; |, |\*|\n', self.EgonTE.get('1.0', 'end'))
            print(content)
        else:
            content = reSplit('[^.-]|\s', self.EgonTE.get('1.0', 'end'))
            print(content)
        new_content = []
        new_word = ''
        if reverse:
            reverse_morse_dict = {}
            for key, value in morse_code_dict.items():
                reverse_morse_dict[value] = key
            reverse_morse_dict[''] = ' '

        for word in content:

            if new_word:
                new_content.append(new_word)
                new_word = ''

            if not reverse:
                for character in word:
                    if character.upper() in morse_code_dict.keys():
                        if morse_code_dict[character.upper()] == '/' or word == content[-1]:
                            spc = ''
                        else:
                            spc = ' '
                        new_word += morse_code_dict[character.upper()] + spc


            else:

                print(new_content)
                if word in morse_code_dict.values() or word == '':
                    # accessing the keys using their values (reverse of encryption)
                    new_word += reverse_morse_dict[word]

        # output
        if reverse:
            new_content = ''.join(new_content).lower().capitalize()
        else:
            new_content = ' '.join(new_content)
        self.EgonTE.delete('1.0', 'end')
        self.EgonTE.insert('1.0', new_content)

    def roman_numbers_translator(self, reverse=False):
        '''
        translator of roman numbers and vice versa
        :param reverse:
        '''
        # reverse:false - roman to arabic, reverse:true - vice versa
        content = self.EgonTE.get(1.0, 'end')
        new_content = []
        # converting roman numbers arabic numbers
        if reverse:
            print('roman to arabic')
            content = content.replace('IV', 'IIII').replace('IX', 'VIIII')
            content = content.replace('XL', 'XXXX').replace('XC', 'LXXXX')
            content = content.replace('CD', 'CCCC').replace('CM', 'DCCCC')
            print(content)

            content = reSplit('; |, |\*|\n', content)  # reSplit('; |, |\*|\n', content)
            content = ''.join(content)
            content = content.split(' ')

            print(content)
            for roman_value in content:
                word_value = 0
                if roman_value.isalpha():
                    if len(roman_value) > 1:
                        for separated_roman_value in roman_value:
                            print(separated_roman_value)
                            if separated_roman_value.upper() in self.roman_dict.keys():
                                word_value += self.roman_dict[separated_roman_value.upper()]
                            else:
                                new_content.append(roman_value)

                        # value of an entire word full of roman numbers values
                        new_content.append(str(word_value))

                    else:
                        if roman_value.upper() in self.roman_dict.keys():
                            new_content.append(str(self.roman_dict[roman_value.upper()]))
                        else:
                            new_content.append(roman_value)

                    new_content.append(' ')

        # converting arabic numbers to roman numbers
        else:
            # works on a really limited list of numbers !!
            print('arabic to roman')
            rev_roman_dict = {}
            for key, value in self.roman_dict.items():
                rev_roman_dict[value] = key
            print(rev_roman_dict)

            print(content)

            content = reSplit('; |, |\*|\n', content)  # reSplit('; |, |\*|\n', content)
            content = ''.join(content)
            content = content.split(' ')

            print(content)
            for word in content:
                if word.isdigit():
                    word = int(word)
                    if word in rev_roman_dict.keys():
                        new_content.append(rev_roman_dict[word])
                    else:
                        new_content.append(word)
                else:
                    new_content.append(word)

                if word == content[-1]:
                    if word != ' ':
                        new_content.append(' ')
                else:
                    new_content.append(' ')

        # outputing the results
        new_content = ''.join(new_content)
        self.EgonTE.delete(1.0, 'end')
        self.EgonTE.insert('1.0', new_content)

    def run_code(self):
        '''
        function that can be used while using a pyhton file

        used to run python file and write its output
        '''
        if self.file_name:

            if self.sar.get():
                self.save()

            if self.auto_cc.get():
                self.clear_console()

            self.output_box.configure(state=NORMAL)
            command = f'python "{self.text_name}"'
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output, error = process.communicate()
            self.output_box.insert('1.0', output)
            self.output_box.insert('1.0', error)
            self.output_box.configure(state=DISABLED)

    def clear_console(self):
        try:
            if self.output_box:
                self.output_box.configure(state=NORMAL)
                self.output_box.delete('1.0', 'end')
                self.output_box.configure(state=READONLY)
        except NameError:
            pass

    def save_last_file(self):
        if self.file_name:
            if os.path.exists(self.file_name):
                self.data['open_last_file'] = os.path.abspath(self.file_name)

    def gitp(self, action):
        '''
        for this function you need to activate dev mode
        collection of git actions that can be used from the program

        :param action:
        '''

        ui = False
        if (action == 'r.i') and (action == 'c.d'):
            ui = True
            git_root = Toplevel()
            git_root.title(self.title_struct + 'Git window')
            title = Label(git_root, text='', font='arial 14 bold')
            desc = Text(git_root)

            # repo = simpledialog.askstring('Git', 'enter the repo link')
            repo = self.text_name = filedialog.askopenfilename(title='Open repo')
            repo = Repo(repo)

        if action == 'r.i':
            title.configure(text='Respiratory information')
            status = repo.git.status()
            repo_description = repo.description
            active_branch = repo.active_branch

            desc.insert('1.0',
                        f'Status:\n{status}\nDescription:\n{repo_description}\nActive branch:\n{active_branch}\nRemotes:\n')

            remote_dict = {}
            for remote in repo.remotes:
                remote_dict[remote] = remote.url

            for remote, url in remote_dict.items():
                insert.insert('end', f'{remote} - {url}\n')

            last_commit = str(repo.head.commit.hexsha)

            desc.insert('end', f'Last commit:\n{last_commit}')

        elif action == 'clone':
            link = simpledialog.askstring('EgonTE', 'please enter the repo\'s link')
            file_location = filedialog.asksaveasfilename(title='Where do you want to save the repo?')
            git.Repo.clone_from(link, file_location)

        elif action == 'c.d':
            title.configure(text='Commit data')
            commit = str(commit.hexsha)
            by = f'\"{commit.summary}\" by {commit.author.name} ({commit.author.email})'
            date_time = str(commit.authored_datetime)
            count_size = str(f'count: {commit.count()} and size: {commit.size}')

            desc.insert('1.0',
                        f'Commit:\n{commit}\nSummery & author:\n{by}\nDate/time:\n{date_time}\nCount & size:\n{count_size}')


        elif action == 'excute':
            command = simpledialog.askstring('Git', 'enter custom command')
            repo.git.excute(command)  # used to excute git command on repo object

        elif action == 'pull':
            repo.git.pull()

        elif action == 'add':
            repo.git.add(all=True)

        elif action == 'commit':
            def commit_enter():
                try:
                    message, author_ = message_entry.get(), author_entry.get()
                    if message and author:
                        repo.git.commit(m=message, author=author_)
                    elif message or author_:
                        if message:
                            repo.git.commit(m=message)
                        elif author_:
                            repo.git.commit(author=author_)
                    else:
                        repo.git.commit()
                    commit_window.destroy()
                except:
                    messagebox.showerror(self.title_struct + 'git', 'an error has occurred')

            commit_window = Toplevel()
            commit_window.title(self.title_struct + 'Git commit window')
            message_title = Label(commit_window, text='Message:', font='arial 10 underline')
            message_entry = Entry(commit_window)
            author_title = Label(commit_window, text='Author:', font='arial 10 underline')
            author_entry = Entry(commit_window)
            enter = Button(commit_window, text='Commit', command=commit_enter)

            message_title.pack()
            message_entry.pack()
            author_title.pack()
            author_entry.pack()
            enter.pack()

        if ui:
            title.pack()
            desc.pack(expand=True, fill=BOTH)

    def call_settings(self):
        if not self.op_active:
            self.settings_object = self.advance_options
            Thread(target=self.settings_object).start()
        else:
            opt_root.attributes('-topmost', True)
            opt_root.attributes('-topmost', False)

    if RA:
        right_align_language_support()


def new_window(app):
    appX = app()
    appX.mainloop()


if __name__ == '__main__':
    if req_lib:
        app = Window()
        app.mainloop()
    else:
        if messagebox.askyesno('EgonTE', 'some of the required libraries aren\'t installed\ndo you want to open the '
                                         'libraries installer again?'):
            library_installer()
