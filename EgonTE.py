from tkinter import filedialog, colorchooser, font, ttk, messagebox, simpledialog
from tkinter import *
from tkinter.tix import *

import pytesseract.pytesseract
from win32print import GetDefaultPrinter
from win32api import ShellExecute, GetShortPathName
from pyttsx3 import init as ttsx_init
from threading import Thread
import pyaudio  # imported to make speech_recognition work
from random import choice, randint, random, shuffle, randrange
from speech_recognition import Recognizer, Microphone, AudioFile
from sys import exit as exit_
from datetime import datetime, timedelta
import webbrowser
import names
import urllib.request, urllib.error
import ssl

try:
    from googletrans import Translator  # req version 3.1.0a0

    google_trans = True
    deep_trans = ''
except (ImportError, AttributeError, ModuleNotFoundError) as e:
    google_trans = ''
    # try:
    #     from deep_translator import GoogleTranslator
    #     deep_trans = True
    # except (ImportError, AttributeError, ModuleNotFoundError) as e:
    #     pass
from pyshorteners import Shortener
import smtplib
from email.message import EmailMessage
import os
from string import ascii_letters, digits, ascii_lowercase, ascii_uppercase
import pandas
from socket import gethostname
from PyDictionary import PyDictionary
from pyperclip import copy
import emoji
from wikipedia import summary, exceptions, page
from wikipedia import search as wiki_search
import time
from difflib import Differ
from textblob import TextBlob
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup
from collections import Counter
from spacy.matcher import Matcher
from PIL import Image, ImageTk, ImageGrab
from platform import system
import requests
# import cv2
# import handprint
from re import findall
# from re import search as reSearch
from json import dump, load, loads
# import pdf2image
# import keras
import spacy  # download also en_core_web_sm - https://spacy.io/usage

try:
    from pytesseract import image_to_string  # download https://github.com/UB-Mannheim/tesseract/wiki

    tes = ACTIVE
except:
    tes = DISABLED
from io import BytesIO

try:
    import YouTubeTranscriptApi

    yt_api = True
except (ImportError, AttributeError, ModuleNotFoundError) as e:
    yt_api = False
# from csv import reader
try:
    import openai

    openai_library = True
except (ImportError, AttributeError, ModuleNotFoundError) as e:
    openai_library = ''
    from pyChatGPT import Chat, Options

from pydub import AudioSegment

try:
    import polyglot

    RA = True
except ImportError:
    RA = False

global translate_root, sort_root


def MainMenu():
    def new_file():
        loading_screen()
        root.destroy()

    def open_file():
        app = Window()
        app.mainloop()

        root.destroy()

    def exit_():
        root.quit()

    root = Tk()
    root.width = 500
    root.height = 400
    root.geometry(f'{root.width}x{root.height}')
    root.title('')
    title = Label(root, text='Egon Text editor - Main menu')
    b_height, b_width = 5, 10
    new_button_image = None
    open_button_image = None
    exit_button_image = None
    new_file_button = Button(root, height=b_height, width=b_width, command=new_file, text='new')
    open_file_button = Button(root, height=b_height, width=b_width, command=open_file, text='open')
    exit_button = Button(root, height=b_height, width=b_width, command=exit_, text='exit')

    # try packing with filling and with tk.left etc. (sides)
    title.grid(row=0, column=1)
    new_file_button.grid(row=1, column=0, pady=20, padx=50)
    # open_file_button.grid(row=1, column=1, padx=5)
    exit_button.grid(row=1, column=2, padx=5)

    root.mainloop()


# window creation
class Window(Tk):
    def __init__(self):
        super().__init__()
        self.width = 1250
        self.height = 830
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        placement_x = round((screen_width / 2) - (self.width / 2))
        placement_y = round((screen_height / 2) - (self.height / 2))
        self.geometry(f'{self.width}x{self.height}+{placement_x}+{placement_y}')
        ver = '1.11.0'
        self.title(f'Egon Text editor - {ver}')
        self.load_images()
        self.protocol("WM_DELETE_WINDOW", self.exit_app)
        self.file_name = ''
        self.text_changed = False
        self.aul = False
        self.op_active = ''
        self.info_page_activated = False
        open_status_name = ''
        self.key = ''
        self.fs_value = False
        self.tm_value = False
        Thread(target=self.stopwatch, daemon=True).start()
        Thread(target=self.load_links, daemon=True).start()
        # Thread(target=self.counter).start()
        try:
            pytesseract.pytesseract.tesseract_cmd = (r'C:\Program Files\Tesseract-OCR\tesseract.exe')
            print(os.path.abspath(r'Program Files\Tesseract-OCR\tesseract.exe'))
        except:
            global tes
            tes = DISABLED

        LOGO = PhotoImage(file='ETE_icon.png')
        self.iconphoto(False, LOGO)

        # create toll tip, for the toolbar buttons (with shortcuts)
        TOOL_TIP = Balloon(self)

        # pre-defined options
        self.predefined_cursor = 'xterm'
        self.predefined_style = 'clam'
        self.predefined_relief = 'ridge'
        # add custom style
        self.style = ttk.Style()
        self.style.theme_use(self.predefined_style)
        frame = Frame(self)
        frame.pack(expand=True, fill=BOTH, padx=15)
        # create toolbar frame
        self.toolbar_frame = Frame(frame)
        self.toolbar_frame.pack(fill=X, anchor=W, side=TOP)
        self.img_extensions = (('PNG', '*.png'), ('JPG', '*.jpg'))

        # font
        font_tuple = font.families()
        self.font_family = StringVar()
        font_ui = ttk.Combobox(self.toolbar_frame, width=30, textvariable=self.font_family, state="readonly")
        font_ui["values"] = font_tuple
        font_ui.current(font_tuple.index("Arial"))
        font_ui.grid(row=0, column=4, padx=5)

        # Size Box
        self.size_var = IntVar()
        self.size_var.set(16)
        self.font_size = ttk.Combobox(self.toolbar_frame, width=5, textvariable=self.size_var, state="readonly")
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
        # create menu
        menu = Menu(frame)
        self.config(menu=menu)

        # file menu
        file_menu = Menu(menu, tearoff=False)
        menu.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='New', accelerator='(ctrl+n)', command=self.new_file)
        file_menu.add_command(label='Open', accelerator='(ctrl+o)', command=self.open_file)
        file_menu.add_command(label='Save', command=self.save, accelerator='(ctrl+s)')
        file_menu.add_command(label='Save As', command=self.save_as)
        file_menu.add_command(label='Delete', command=self.delete_file)
        file_menu.add_command(label='New window', command=lambda: new_window(Window), state=DISABLED)
        file_menu.add_command(label='Screenshot', command=lambda: self.save_images(self.EgonTE, self))
        file_menu.add_separator()
        file_menu.add_command(label='File\'s Info', command=self.file_info)
        file_menu.add_command(label='File\'s comparison', command=self.compare)
        file_menu.add_command(label='Merge files', command=self.merge_files)
        file_menu.add_separator()
        file_menu.add_command(label='Print file', accelerator='(ctrl+p)', command=self.print_file)
        file_menu.add_separator()
        file_menu.add_command(label='Copy path', accelerator='(alt+d)', command=self.copy_file_path)
        file_menu.add_separator()
        file_menu.add_command(label='Import local file', command=self.special_files_import)
        file_menu.add_command(label='Import global file', command=lambda: self.special_files_import('web'))
        file_menu.add_separator()
        file_menu.add_command(label='Exit', accelerator='(alt+f4)', command=self.exit_app)
        # edit menu
        edit_menu = Menu(menu, tearoff=True)
        menu.add_cascade(label='Edit', menu=edit_menu)
        edit_menu.add_command(label='Cut', accelerator='(ctrl+x)', command=lambda: self.cut(x=True))
        edit_menu.add_command(label='Copy', accelerator='(ctrl+c)', command=lambda: self.copy())
        edit_menu.add_command(label='Paste', accelerator='(ctrl+v)', command=lambda: self.paste())
        edit_menu.add_separator()
        edit_menu.add_command(label='Correct writing', command=self.corrector)
        edit_menu.add_command(label='Organize writing', command=self.organize)
        edit_menu.add_separator()
        edit_menu.add_command(label='Undo', accelerator='(ctrl+z)', command=self.EgonTE.edit_undo)
        edit_menu.add_command(label='Redo', accelerator='(ctrl+y)', command=self.EgonTE.edit_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label='Select all', accelerator='(ctrl+a)', command=lambda: self.select_all('nothing'))
        edit_menu.add_command(label='Clear all', accelerator='(ctrl+del)', command=self.clear)
        edit_menu.add_separator()
        edit_menu.add_command(label='Find Text', accelerator='(ctrl+f)', command=self.find_text)
        edit_menu.add_command(label='Replace', accelerator='(ctrl+h)', command=self.replace)
        edit_menu.add_command(label='Go to', accelerator='(ctrl+g)', command=self.goto)
        edit_menu.add_separator()
        edit_menu.add_command(label='Reverse characters', accelerator='(ctrl+shift+c)', command=self.reverse_characters)
        edit_menu.add_command(label='Reverse words', accelerator='(ctrl+shift+r)', command=self.reverse_words)
        edit_menu.add_command(label='Join words', accelerator='(ctrl+shift+j)', command=self.join_words)
        edit_menu.add_command(label='Upper/Lower', accelerator='(ctrl+shift+u)', command=self.lower_upper)
        edit_menu.add_command(label='Sort by characters', command=self.sort_by_characters)
        edit_menu.add_command(label='Sort by words', command=self.sort_by_words)
        # tools menu
        tool_menu = Menu(menu, tearoff=False)
        menu.add_cascade(label='Tools', menu=tool_menu)
        tool_menu.add_command(label='Calculation', command=self.ins_calc)
        tool_menu.add_command(label='Current datetime', accelerator='(F5)', command=self.dt)
        tool_menu.add_command(label='Random number', command=self.ins_random)
        tool_menu.add_command(label='Random name', command=self.ins_random_name)
        if google_trans:
            tool_menu.add_command(label='Translate', command=self.translate)
        tool_menu.add_command(label='Url shorter', command=self.url)
        tool_menu.add_command(label='Generate sequence', command=self.generate)
        tool_menu.add_command(label='Search online', command=self.search_www)
        tool_menu.add_command(label='Sort', command=self.sort)
        tool_menu.add_command(label='Dictionary', command=lambda: Thread(target=self.knowledge_window('dict')).start())
        tool_menu.add_command(label='Wikipedia', command=lambda: Thread(target=self.knowledge_window('wiki')).start())
        tool_menu.add_command(label='Scrapping (beta)', command=self.web_scrapping)
        tool_menu.add_command(label='Drawing ➡ writing (beta)', command=self.handwriting)
        tool_menu.add_command(label='Text decorators', command=self.text_decorators)
        tool_menu.add_command(label='Inspirational quote', command=self.insp_quote)
        tool_menu.add_command(label='Get weather', command=self.get_weather)
        tool_menu.add_command(label='Send Email', command=self.send_email)
        tool_menu.add_command(label='Use ChatGPT', command=self.chatGPT, font='arial 10 bold')
        tool_menu.add_command(label='Use DallE', command=self.dallE, font='arial 10 bold')
        tool_menu.add_command(label='Transcript', command=self.transcript)
        # nlp menu
        nlp_menu = Menu(menu, tearoff=False)
        menu.add_cascade(label='NLP', menu=nlp_menu)
        nlp_menu.add_command(label='Get noun', command=lambda: self.natural_language_process(function='nouns'))
        nlp_menu.add_command(label='Get verb', command=lambda: self.natural_language_process(function='verbs'))
        nlp_menu.add_command(label='Get adjectives', command=lambda: self.natural_language_process(
            function='adjective'))
        nlp_menu.add_command(label='Get adverbs', command=lambda: self.natural_language_process(function='adverbs'))
        nlp_menu.add_command(label='Get pronouns', command=lambda: self.natural_language_process(
            function='pronouns'))
        nlp_menu.add_command(label='get stop words', command=lambda: self.natural_language_process(
            function='stop words'))
        nlp_menu.add_separator()
        nlp_menu.add_command(label='Entity recognition',
                             command=lambda: self.natural_language_process(function='entity recognition'))
        nlp_menu.add_command(label='Dependency tree', command=lambda: self.natural_language_process(
            function='dependency'))
        nlp_menu.add_command(label='Lemmatization', command=lambda: self.natural_language_process(
            function='lemmatization'))
        nlp_menu.add_command(label='Most common words',
                             command=lambda: self.natural_language_process(function='most common words'))

        # color menu
        color_menu = Menu(menu, tearoff=False)
        menu.add_cascade(label='Colors+', menu=color_menu)
        color_menu.add_command(label='Whole text', command=self.all_txt_color)
        color_menu.add_command(label='Background', command=self.bg_color)
        color_menu.add_command(label='Highlight', command=self.hl_color)
        color_menu.add_separator()
        color_menu.add_command(label='Buttons color', command=lambda: self.custom_ui_colors(components='buttons'))
        color_menu.add_command(label='Menus colors', command=lambda: self.custom_ui_colors(components='menus'))
        color_menu.add_command(label='App colors', command=lambda: self.custom_ui_colors(components='app'))
        # options menu
        options_menu = Menu(menu, tearoff=False)
        menu.add_cascade(label='Options', menu=options_menu)
        # boolean tk vars
        self.bars_active = BooleanVar()
        self.bars_active.set(True)

        self.show_statusbar = BooleanVar()
        self.show_statusbar.set(True)

        self.show_toolbar = BooleanVar()
        self.show_toolbar.set(True)

        self.night_mode = BooleanVar()

        self.cc = StringVar()
        self.cc.set('xterm')

        self.cs = StringVar()
        self.cs.set('clam')

        self.ww = BooleanVar()
        self.ww.set(True)

        self.rm = BooleanVar()
        self.rm.set(False)

        self.aus = BooleanVar()
        self.aus.set(True)

        # made also here in order to make the usage of variables less wasteful
        self.status_ = True
        self.file_ = True

        # check marks
        options_menu.add_checkbutton(label='Night mode', onvalue=True, offvalue=False,
                                     compound=LEFT, command=self.night)
        options_menu.add_checkbutton(label='Status Bars', onvalue=True, offvalue=False,
                                     variable=self.show_statusbar, compound=LEFT, command=self.hide_statusbars)
        options_menu.add_checkbutton(label='Tool Bar', onvalue=True, offvalue=False,
                                     variable=self.show_toolbar, compound=LEFT, command=self.hide_toolbar)
        options_menu.add_checkbutton(label='Custom cursor', onvalue=True, offvalue=False,
                                     compound=LEFT, command=self.custom_cursor)
        options_menu.add_checkbutton(label='Custom style', onvalue=True, offvalue=False,
                                     compound=LEFT, command=self.custom_style)
        options_menu.add_checkbutton(label='Word warp', onvalue=True, offvalue=False,
                                     compound=LEFT, command=self.word_warp, variable=self.ww)
        options_menu.add_checkbutton(label='Reader mode', onvalue=True, offvalue=False,
                                     compound=LEFT, command=self.reader_mode)
        options_menu.add_checkbutton(label='Auto save', onvalue=True, offvalue=False,
                                     compound=LEFT, variable=self.aus)
        options_menu.add_checkbutton(label='Top most', onvalue=True, offvalue=False,
                                     compound=LEFT, command=self.topmost)
        options_menu.add_separator()
        options_menu.add_command(label='Detect emojis', command=lambda: self.emoji_detection(via_settings=True))
        options_menu.add_command(label='Emojis list', command=self.emoji_list)
        options_menu.add_separator()
        options_menu.add_command(label='Advance options', command=lambda: Thread(target=self.advance_options).start())
        # help page
        menu.add_cascade(label='Help', command=lambda: self.info_page('help.txt'))
        # patch notes page
        menu.add_cascade(label='Patch notes', command=lambda: self.info_page('patch_notes.txt'))
        # github page
        menu.add_cascade(label='GitHub', command=self.github)
        # add status bar
        self.status_frame = Frame(frame, height=20)
        self.status_frame.pack(fill=BOTH, anchor=S, side=BOTTOM)
        self.status_bar = Label(self.status_frame, text='Lines:1 Characters:0 Words:0', pady=5)
        self.status_bar.pack(fill=Y, side=LEFT)
        # add file bar
        self.file_bar = Label(self.status_frame, text='')
        self.file_bar.pack(fill=Y, side=RIGHT)
        # add shortcuts
        self.bind('<Control-o>', self.open_file)
        self.bind('<Control-O>', self.open_file)
        # self.bind('<Control-Key-x>', lambda event: self.cut(True))
        self.bind('<<Cut>>', lambda event: self.cut(True))
        # self.bind('<Control-Key-v>', lambda event: self.paste())
        # self.bind('<<Paste>>', self.paste)
        self.bind('<<Copy>>', lambda event: self.copy(True))
        # self.bind('<Control-Key-C>', lambda event: self.copy(True))
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
        self.bind('<F11>', self.full_screen)
        # self.bind('<space>', self.emoji_detection)
        # special events
        self.font_size.bind('<<ComboboxSelected>>', self.change_font_size)
        font_ui.bind('<<ComboboxSelected>>', self.change_font)
        self.bind('<<Modified>>', self.status)
        # buttons creation and placement
        bold_button = Button(self.toolbar_frame, image=BOLD_IMAGE, command=self.bold, relief=FLAT)
        bold_button.grid(row=0, column=0, sticky=W, padx=2)

        italics_button = Button(self.toolbar_frame, image=ITALICS_IMAGE, command=self.italics, relief=FLAT)
        italics_button.grid(row=0, column=1, sticky=W, padx=2)

        underline_button = Button(self.toolbar_frame, image=UNDERLINE_IMAGE, command=self.underline, relief=FLAT)
        underline_button.grid(row=0, column=2, sticky=W, padx=2)

        color_button = Button(self.toolbar_frame, image=COLORS_IMAGE, command=self.text_color, relief=FLAT)
        color_button.grid(row=0, column=3, padx=5)

        align_left_button = Button(self.toolbar_frame, image=ALIGN_LEFT_IMAGE, relief=FLAT, command=self.align_left)
        align_left_button.grid(row=0, column=6, padx=5)

        # align center button
        align_center_button = Button(self.toolbar_frame, image=ALIGN_CENTER_IMAGE, relief=FLAT,
                                     command=self.align_center)
        align_center_button.grid(row=0, column=7, padx=5)

        # align right button
        align_right_button = Button(self.toolbar_frame, image=ALIGN_RIGHT_IMAGE, relief=FLAT, command=self.align_right)
        align_right_button.grid(row=0, column=8, padx=5)

        # tts button
        tts_button = Button(self.toolbar_frame, image=TTS_IMAGE, relief=FLAT,
                            command=lambda: Thread(target=self.text_to_speech).start(),
                            )
        tts_button.grid(row=0, column=9, padx=5)

        # talk button
        talk_button = Button(self.toolbar_frame, image=STT_IMAGE, relief=FLAT,
                             command=lambda: Thread(target=self.speech_to_text).start())
        talk_button.grid(row=0, column=10, padx=5)

        v_keyboard_button = Button(self.toolbar_frame, image=KEY_IMAGE, relief=FLAT,
                                   command=lambda: Thread(target=self.virtual_keyboard()).start())

        v_keyboard_button.grid(row=0, column=11, padx=5)

        # opening sentence
        op_msgs = ('Hello world!', '^-^', 'What a beautiful day!', 'Welcome!', '', 'Believe in yourself!',
                   'If I did it you can do way more than that', 'Don\'t give up!',
                   'I\'m glad that you are using my Text editor (:', 'Feel free to send feedback',
                   f'hi {gethostname()}')
        op_msg = choice(op_msgs)
        try:
            op_insp_msg = self.insp_quote(op_msg=True)
            if op_insp_msg:
                print(op_insp_msg)
                final_op_msg = choice([op_msg, op_insp_msg])
            else:
                raise
        except:
            final_op_msg = op_msg
        self.EgonTE.insert('1.0', final_op_msg)

        # add tooltips to the buttons
        TOOL_TIP.bind_widget(bold_button, balloonmsg='Bold (ctrl+b)')
        TOOL_TIP.bind_widget(italics_button, balloonmsg='Italics (ctrl+i)')
        TOOL_TIP.bind_widget(color_button, balloonmsg='Change colors')
        TOOL_TIP.bind_widget(underline_button, balloonmsg='Underline (ctrl+u)')
        TOOL_TIP.bind_widget(align_left_button, balloonmsg='Align left (ctrl+l)')
        TOOL_TIP.bind_widget(align_center_button, balloonmsg='Align center (ctrl+e)')
        TOOL_TIP.bind_widget(align_right_button, balloonmsg='Align right (ctrl+r)')
        TOOL_TIP.bind_widget(tts_button, balloonmsg='Text to speach')
        TOOL_TIP.bind_widget(talk_button, balloonmsg='Speach to talk')
        TOOL_TIP.bind_widget(self.font_size, balloonmsg='upwards - (ctrl+plus) \n downwards - (ctrl+minus)')

        # ui tuples
        self.toolbar_components = (bold_button, italics_button, color_button, underline_button, align_left_button,
                                   align_center_button, align_right_button, tts_button, talk_button, self.font_size,
                                   v_keyboard_button)
        self.menus_components = file_menu, edit_menu, tool_menu, color_menu, options_menu, nlp_menu
        self.other_components = self, self.status_bar, self.file_bar, self.EgonTE, self.toolbar_frame

        self.saved_settings()
        # messagebox.showinfo('EgonTE', 'This is a beta/alpha version of ETE V1.11\ntake into account that some things\n might not be ready yet, but still available')

    def load_images(self):
        global BOLD_IMAGE, UNDERLINE_IMAGE, ITALICS_IMAGE, ALIGN_LEFT_IMAGE, ALIGN_CENTER_IMAGE, \
            ALIGN_RIGHT_IMAGE, TTS_IMAGE, STT_IMAGE, COLORS_IMAGE, KEY_IMAGE
        # icons - size=32x32
        BOLD_IMAGE = PhotoImage(file='assets/bold.png')
        UNDERLINE_IMAGE = PhotoImage(file='assets/underlined-text.png')
        ITALICS_IMAGE = PhotoImage(file='assets/italics.png')
        COLORS_IMAGE = PhotoImage(file='assets/edition.png')
        ALIGN_LEFT_IMAGE = PhotoImage(file='assets/left-align.png')
        ALIGN_CENTER_IMAGE = PhotoImage(file=f'assets/center-align.png')
        ALIGN_RIGHT_IMAGE = PhotoImage(file='assets/right-align.png')
        TTS_IMAGE = PhotoImage(file='assets/tts(1).png')
        STT_IMAGE = PhotoImage(file='assets/speech-icon-19(1).png')
        KEY_IMAGE = PhotoImage(file='assets/key(1).png')

    def load_links(self):
        global gpt_image
        # a function to load images from the web to use them later in the GUI
        with urllib.request.urlopen('https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fwww.modify.in.th%2Fwp-'
                                    'content%2Fuploads%2FChatGPT-logo-326x245.gif&f=1&nofb=1&ipt=f0164b4a83aeec7a81f2081'
                                    'b87f90a9d99c04f3d822980e3290ce974fc33e4ae&ipo=images') as u:
            gpt_image_raw_data = u.read()
        gpt_image_ = Image.open(BytesIO(gpt_image_raw_data))
        gpt_image = ImageTk.PhotoImage(gpt_image_)

    # current time for the file bar
    def get_time(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def get_pos(self):
        return self.EgonTE.index(INSERT)

    # open the GitHub page
    def github(self):
        webbrowser.open('https://github.com/Ariel4545/text_editor')

    def undo(self):
        return self.EgonTE.edit_undo()

    # create file func
    def new_file(self, event=None):
        self.file_name = ''
        self.EgonTE.delete('1.0', END)
        self.file_bar.config(text='New file')

        global open_status_name
        open_status_name = False

    # open file func
    def open_file(self, event=None):
        self.EgonTE.delete('1.0', END)
        text_name = filedialog.askopenfilename(initialdir=os.getcwd(), title='Open file',
                                               filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html'),
                                                          ('Python Files', '*.py')))
        if text_name:
            try:
                global open_status_name
                open_status_name = text_name
                self.file_name = text_name
                self.file_bar.config(text=f'Opened file: {GetShortPathName(self.file_name)}')
                self.file_name.replace('C:/EgonTE/', '')
                self.file_name.replace('C:/users', '')
                text_file = open(text_name, 'r')
                stuff = text_file.read()
                # make the html files formatted when opened
                if self.file_name.endswith('html'):
                    self.soup = BeautifulSoup(stuff, 'html')
                    stuff = self.soup.prettify()
                # end
                self.EgonTE.insert(END, stuff)
                text_file.close()
            except UnicodeDecodeError:
                messagebox.showerror('error', 'File contains not supported characters')
        else:
            messagebox.showerror('error', 'File not found / selected')

    # save as func
    def save_as(self, event=None):
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
        if event == 'get name':
            try:
                return self.file_name
            except NameError:
                messagebox.showerror('error', 'You cant copy a file name if you doesn\'t use a file ')

    # save func
    def save(self, event=None):
        global open_status_name
        if open_status_name:
            text_file = open(open_status_name, 'w')
            text_file.write(self.EgonTE.get(1.0, END))
            text_file.close()
            self.file_bar.config(text=f'Saved: {self.file_name} - {self.get_time()}')
        else:
            self.save_as(event=None)

    # cut func
    def cut(self, x):
        # if not x:
        #     self.selected = self.clipboard_get()
        # else:
        if self.is_marked():
            # grab
            self.selected = self.EgonTE.selection_get()
            # del
            self.EgonTE.delete('sel.first', 'sel.last')
            self.clipboard_clear()
            self.clipboard_append(self.selected)

    # copy func
    def copy(self, event=None):
        if self.is_marked():
            # grab
            self.clipboard_clear()
            self.clipboard_append(self.EgonTE.selection_get())

    # paste func
    def paste(self, event=None):
        try:
            self.EgonTE.insert(self.get_pos(), self.clipboard_get())
        except BaseException:
            pass

    # bold text func
    def bold(self, event=None):
        # create

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

    # italics text func
    def italics(self, event=None):
        # create
        italics_font = font.Font(self.EgonTE, self.EgonTE.cget('font'))
        italics_font.configure(slant='italic')
        # config
        self.EgonTE.tag_configure('italics', font=italics_font)
        current_tags = self.EgonTE.tag_names('1.0')
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

    # make the text underline func
    def underline(self, event=None):
        # create
        underline_font = font.Font(self.EgonTE, self.EgonTE.cget('font'))
        underline_font.configure(underline=True)
        # config
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

    # text color func
    def text_color(self):
        # color pick
        selected_color = colorchooser.askcolor(title='Text color')[1]
        if selected_color:
            # create
            color_font = font.Font(self.EgonTE, self.EgonTE.cget('font'))
            # config
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

    # background color func
    def bg_color(self):
        selected_color = colorchooser.askcolor(title='Background color')[1]
        if selected_color:
            self.EgonTE.config(bg=selected_color)

    # all color txt func
    def all_txt_color(self, event=None):
        color = colorchooser.askcolor(title='Text color')[1]
        if color:
            self.EgonTE.config(fg=color)

    # highlight color func
    def hl_color(self):
        color = colorchooser.askcolor(title='Highlight color')[1]
        if color:
            self.EgonTE.config(selectbackground=color)

    # print file func
    def print_file(self, event=None):
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

    # select all func
    def select_all(self, event=None):
        self.EgonTE.tag_add('sel', '1.0', 'end')

    # clear func
    def clear(self, event=None):
        self.EgonTE.delete('1.0', END)

    # hide file bar & status bar func
    def hide_statusbars(self):
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

    #  hide tool bar func
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
            self.toolbar_frame.pack(fill=X, anchor=W)
            self.text_scroll.pack(side=RIGHT, fill=Y)
            self.EgonTE.pack(fill=BOTH, expand=True, side=BOTTOM)
            self.EgonTE.focus_set()
            self.height = 805
            self.geometry(f'{self.width}x{self.height}')
            show_toolbar = True
        self.data['toolbar'] = self.show_toolbar

    # night on func
    def night(self):
        if self.night_mode:
            main_color = '#110022'
            second_color = '#373737'
            third_color = '#280137'
            _text_color = 'green'
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
            if self.info_page_activated:
                self.info_page_text.config(bg=second_color, fg=_text_color)
                self.info_page_title.config(bg=second_color, fg=_text_color)

            self.night_mode = False
            self.data['night_mode'] = True
        else:
            main_color = 'SystemButtonFace'
            second_color = 'SystemButtonFace'
            _text_color = 'black'
            self.config(bg=main_color)
            self.status_frame.configure(bg=main_color)
            self.status_bar.config(bg=main_color, fg=_text_color)
            self.file_bar.config(bg=main_color, fg=_text_color)
            self.EgonTE.config(bg='white', fg=_text_color)
            self.toolbar_frame.config(bg=main_color)
            # toolbar buttons
            for toolbar_button in self.toolbar_components:
                toolbar_button.config(background=second_color)
            # file menu colors
            for menu_ in self.menus_components:
                menu_.config(background=second_color, foreground=_text_color)
            # help & patch notes
            if self.info_page_activated:
                self.info_page_text.config(bg=second_color, fg=_text_color)
                self.info_page_title.config(bg=second_color, fg=_text_color)

            self.night_mode = True
            self.data['night_mode'] = False

    def change_font(self, event):
        global chosen_font
        chosen_font = self.font_family.get()
        # !!!
        self.delete_tags()
        self.EgonTE.configure(font=(chosen_font, 16))

        self.change_font_size()

    def change_font_size(self, event=None):

        self.chosen_size = self.size_var.get()
        self.font_Size_c = (self.chosen_size - 8) // 2
        # self.font_Size_c = font_size.get()
        # print(self.font_Size_c)
        self.font_size.current(self.font_Size_c)
        # EgonTE.configure(font=(chosen_font, chosen_dot_size))

        size = font.Font(self.EgonTE, self.EgonTE.cget('font'))
        size.configure(size=self.chosen_size)
        # config
        self.EgonTE.tag_configure('size', font=size)
        current_tags = self.EgonTE.tag_names('1.0')
        if not 'size' in current_tags:
            if self.font_size.get() == '4':
                self.EgonTE.tag_remove('size', '1.0', END)
            else:
                self.EgonTE.tag_add('size', '1.0', END)

    def replace(self, event=None):
        # window
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

        # replacing
        def rep_button(self):
            find_ = find_input.get()
            replace_ = replace_input.get()
            content = self.EgonTE.get(1.0, END)

            new_content = content.replace(find_, replace_)
            self.EgonTE.delete(1.0, END)
            self.EgonTE.insert(1.0, new_content)

        replace_button.config(command=rep_button)

    # align Left func
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
            messagebox.showerror('error', 'choose a content')

    # Align Center func
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
            messagebox.showerror('error', 'choose a content')

    # Align Right func
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
            messagebox.showerror('error', 'choose a content')

    # get & display character and word count with status bar
    def status(self, event=None):
        global lines
        if self.EgonTE.edit_modified():
            self.text_changed = True
            words = len(self.EgonTE.get(1.0, 'end-1c').split())
            characters = len(self.EgonTE.get(1.0, 'end-1c'))
            lines = int((self.EgonTE.index(END)).split('.')[0]) - 1
            self.status_bar.config(text=f'Lines:{lines} Characters:{characters} Words:{words}')
        self.EgonTE.edit_modified(False)

    # AI narrator will read the selected text from the text box
    def text_to_speech(self):
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

    # to make the narrator voice more convincing
    def text_formatter(self, phrase):
        interrogatives = ('how', 'why', 'what', 'when', 'who', 'where', 'is', 'do you', 'whom', 'whose')
        capitalized = phrase.capitalize()
        if phrase.startswith(interrogatives):
            return f'{capitalized}?'
        else:
            return f'{capitalized}.'

    # advanced speech to text function
    def speech_to_text(self):
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
            query = recolonize.recognize_google(audio, language='en-UK')  # listen to audio
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
        if self.text_changed or (self.EgonTE.get('1.0', 'end')):
            if self.file_name:
                if messagebox.askyesno('Quit', 'Some changes  warn\'t saved, do you wish to save first?'):
                    self.save()
                    self.quit()
                    exit_()
                    quit()
                    exit()

                    self.saved_settings(sm='save')

                    raise Exception('Close')
                    # fine mechanic - fix bug ^
                else:
                    self.quit()
                    exit_()
                    quit()
                    exit()

                    self.saved_settings(sm='save')

                    raise Exception('Close')
            else:
                self.quit()
                exit_()
                quit()
                exit()

                self.saved_settings(sm='save')

                raise Exception('Close')

    # find if text exists in the specific file
    def find_text(self, event=None):
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
                occurs = str(text_data.count(text_entry.get())).lower()
            elif cpt_settings == 'c':
                text_data = str(text_data)
                entry_data = text_entry.get()
                occurs = text_data.count(text_entry.get())

            # check if text occurs
            if text_data.count(entry_data):
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
                    # title
                    title = Label(nav_root, text=f'navigate trough the {str(occurs)} occurrences of \'{entry_data}\'',
                                  font='arial 12 underline')
                    # buttons ↑
                    button_up = Button(nav_root, text='Reset', command=lambda: up(starting_index, ending_index),
                                       width=5, state=DISABLED)
                    button_down = Button(nav_root, text='↓', command=lambda: down(starting_index, ending_index),
                                         width=5)
                    # placing
                    title.grid(row=0, padx=5)
                    button_up.grid(row=1)
                    button_down.grid(row=2)

            else:
                search_label = messagebox.showinfo('EgonTE:', 'No match found')

        # window
        search_text_root = Toplevel()
        search_text_root.resizable(False, False)
        search_text_root.attributes('-alpha', '0.95')
        # var
        cpt_settings = 'c'
        by_characters = True
        # buttons
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

    # insert mathematics calculation to the text box
    def ins_calc(self):
        def enter_button():
            equation = clac_entry.get()
            try:
                equation = eval(equation)
            except SyntaxError:
                messagebox.showerror('error', 'typed some  invalid characters')
            except NameError:
                messagebox.showerror('error', 'calculation tool support only arithmetics & modulus')
            equation = str(equation) + ' '
            self.EgonTE.insert(self.get_pos(), equation)

        def show_oper():
            global add_sub, mul_div, pow_
            clac_root.geometry('165x160')
            show_op.config(text='hide operations', command=hide_oper)
            add_sub = Label(clac_root, text='+ addition, - subtraction')
            mul_div = Label(clac_root, text='* multiply, / deviation')
            pow_ = Label(clac_root, text='** power, % modulus')
            add_sub.pack()
            mul_div.pack()
            pow_.pack()

        def hide_oper():
            clac_root.geometry('165x95')
            add_sub.grid_forget()
            mul_div.grid_forget()
            pow_.grid_forget()
            show_op.config(text='show operations', command=show_oper)

        clac_root = Toplevel(relief=FLAT)
        clac_root.resizable(False, False)
        clac_root.attributes('-alpha', '0.95')
        clac_root.geometry('165x95')
        introduction_text = Label(clac_root, text='Enter equation below:', font='arial 10 underline', padx=2, pady=3)
        enter = Button(clac_root, text='Enter', command=enter_button, borderwidth=1, font='arial 10 bold')
        clac_entry = Entry(clac_root, relief=RIDGE, justify='center', width=25)
        show_op = Button(clac_root, text='Show operators', relief=FLAT, command=show_oper)
        introduction_text.pack(padx=10)
        clac_entry.pack()
        enter.pack(pady=3)
        show_op.pack()

        if self.is_marked():
            if str(self.EgonTE.get('sel.first', 'sel.last')).isnumeric():
                clac_entry.insert('end', self.EgonTE.get('sel.first', 'sel.last'))

    # insert the current date & time to the text box
    def dt(self, event=None):
        self.EgonTE.insert(self.get_pos(), self.get_time() + ' ')

    # insert a randon number to the text box
    def ins_random(self):
        def enter_button_custom():
            global num_1, num_2
            try:
                try:
                    num_1 = int(number_entry1.get())
                    num_2 = int(number_entry2.get())
                except ValueError:
                    messagebox.showerror('error', 'didn\'t typed valid characters')
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
        introduction_text = Label(ran_num_root, text='Enter numbers below:', justify='center',
                                  font='arial 10 underline')
        sub_c = Button(ran_num_root, text='submit custom', command=enter_button_custom, relief=FLAT)
        sub_qf = Button(ran_num_root, text='submit quick float', command=enter_button_quick_float, relief=FLAT)
        sub_qi = Button(ran_num_root, text='submit quick int', command=enter_button_quick_int, relief=FLAT)
        number_entry1 = Entry(ran_num_root, relief=RIDGE, justify='center', width=25)
        number_entry2 = Entry(ran_num_root, relief=RIDGE, justify='center', width=25)
        bt_text = Label(ran_num_root, text='     Between', font='arial 10 bold')
        introduction_text.grid(row=0, column=1, columnspan=1)
        number_entry1.grid(row=1, column=0, padx=10)
        bt_text.grid(row=1, column=1)
        number_entry2.grid(row=1, column=2, padx=10)
        sub_c.grid(row=2, column=1)
        sub_qf.grid(row=3, column=0)
        sub_qi.grid(row=3, column=2)

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

    def copy_file_path(self, event=None):
        # global selected
        if self.file_name:
            file_name_ = self.save_as(event='get name')
            self.clipboard_clear()
            self.clipboard_append(file_name_)
        else:
            messagebox.showerror('Error', 'you are not using a file')

    # change between the default and custom cursor
    def custom_cursor(self):
        if self.cc.get() == 'tcross':
            self.cc.set('xterm')
        else:
            self.cc.set('tcross')

        self.data['cursor'] = self.predefined_cursor
        self.predefined_cursor = self.cc.get()
        self.EgonTE.config(cursor=self.predefined_cursor)
        try:
            sort_input.config(cursor=self.predefined_cursor)
            translate_box.config(cursor=self.predefined_cursor)
        except BaseException:
            pass

    # change between the default and custom style
    def custom_style(self):
        if self.cs.get() == 'vista':
            self.cs.set('clam')
        else:
            self.cs.set('vista')

        self.predefined_style = self.cs.get()
        self.data['style'] = self.predefined_style
        self.style.theme_use(self.predefined_style)

    def word_warp(self):
        if not self.ww:
            self.EgonTE.config(wrap=WORD)
            self.geometry(f'{self.width}x{self.height - 10}')
            self.horizontal_scroll.pack_forget()
            self.ww = True
            self.data['word_warp'] = False
        else:
            self.geometry(f'{self.width}x{self.height + 10}')
            self.horizontal_scroll.pack(side=BOTTOM, fill=X)
            self.EgonTE.config(wrap=NONE)
            self.ww = False
            self.data['word_warp'] = True

    def reader_mode(self):
        if not self.rm:
            self.EgonTE.configure(state=NORMAL)
            self.rm = True
            self.data['reader_mode'] = False
        else:
            self.EgonTE.configure(state=DISABLED)
            self.rm = False
            self.data['reader_mode'] = True

    def ins_random_name(self):
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

    def translate(self):
        global translate_root, translate_box

        def button():
            to_translate = translate_box.get('1.0', 'end-1c')
            cl = choose_langauge.get()

            if to_translate == '':
                messagebox.showerror('Error', 'Please fill the box')
            else:
                translator = Translator()
                self.translate_output = translator.translate(to_translate, dest=cl)
                self.EgonTE.insert(self.get_pos(), self.translate_output.text)

        def copy_from_file():
            if self.is_marked():
                translate_box.insert('end', self.EgonTE.get('sel.first', 'sel.last'))
            else:
                translate_box.insert('end', self.EgonTE.get('1.0', 'end'))

        # window
        translate_root = Toplevel()
        translate_root.resizable(False, False)
        translate_root.attributes('-alpha', '0.95')
        # string variables
        auto_detect_string = StringVar()
        languages = StringVar()
        # combo box
        auto_detect = ttk.Combobox(translate_root, width=20, textvariable=auto_detect_string, state='readonly',
                                   font=('arial', 10, 'bold'))

        choose_langauge = ttk.Combobox(translate_root, width=20, textvariable=languages, state='readonly',
                                       font=('arial', 10, 'bold'))
        # combo box values
        auto_detect['values'] = (
            'Auto Detect',
        )

        choose_langauge['values'] = (
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
        # translate box & button
        translate_box = Text(translate_root, width=30, height=10, borderwidth=5, cursor=self.predefined_cursor,
                             relief=self.predefined_relief)
        button_ = Button(translate_root, text='Translate', relief=FLAT, borderwidth=3, font=('arial', 10, 'bold'),
                         command=button)
        copy_from = Button(translate_root, text='Copy from file', relief=FLAT, command=copy_from_file)
        copy_translation = Button(translate_root, text='Copy', command=lambda: copy(button()
                                                                                    ), width=10, relief=FLAT)
        # placing the objects in the window
        auto_detect.grid(row=0)
        choose_langauge.grid(row=1)
        translate_box.grid(row=2)
        button_.grid(row=3)
        copy_from.grid(row=4)
        copy_translation.grid(row=5)

    def url(self):
        # window
        url_root = Toplevel()
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
                messagebox.showerror('error', 'Please Paste a valid url')

        enter.config(command=shorter)

        if self.is_marked():
            url_entry.insert('end', self.EgonTE.get('sel.first', 'sel.last'))

    def reverse_characters(self, event=None):
        content = self.EgonTE.get(1.0, END)
        reversed_content = content[::-1]
        self.EgonTE.delete(1.0, END)
        self.EgonTE.insert(1.0, reversed_content)
        self.unacceptable_line_removal(type='characters')

    def reverse_words(self, event=None):
        content = self.EgonTE.get(1.0, END)
        words = content.split()
        reversed_words = words[::-1]
        self.EgonTE.delete(1.0, END)
        self.unacceptable_line_removal()
        self.EgonTE.insert(1.0, reversed_words)

    def join_words(self, event=None):
        content = self.EgonTE.get(1.0, END)
        words = content.split()
        joined_words = ''.join(words)
        self.EgonTE.delete(1.0, END)
        self.unacceptable_line_removal()
        self.EgonTE.insert(1.0, joined_words)

    def lower_upper(self, event=None):
        content = self.EgonTE.get(1.0, END)
        if content == content.upper():
            content = content.lower()
        else:
            content = content.upper()
        self.EgonTE.delete(1.0, END)
        self.unacceptable_line_removal(content, content='upper_lower')
        self.EgonTE.insert(1.0, content)

    # a function to fix random appeared bug
    def unacceptable_line_removal(self, content=None):
        if lines < 2:
            self.EgonTE.delete('end-2l', 'end-1l')
        else:
            self.EgonTE.delete(1.0, 2.0)

    def sort_by_characters(self, event=None):
        # need some work still
        content = (self.EgonTE.get(1.0, END))
        sorted_content = ''.join(sorted(content))
        # if the content is already sorted it will sort it reversed
        if content == sorted_content:
            sorted_content = sorted(sorted_content, reverse=True)
        # if isinstance(sorted_content, list):
        if ' ' in sorted_content:
            sorted_content.replace(' ', '')
            # sorted_content.pop(0)
        self.EgonTE.delete(1.0, END)
        self.EgonTE.insert(1.0, sorted_content)

    def sort_by_words(self, event=None):
        content = (self.EgonTE.get(1.0, END)).split()
        sorted_words = sorted(content)
        if content == sorted_words:
            sorted_words = sorted(sorted_words, reverse=True)
        self.EgonTE.delete(1.0, END)
        self.EgonTE.insert(1.0, sorted_words)

    def generate(self):
        global sym
        generate_root = Toplevel()
        generate_root.resizable(False, False)
        generate_root.attributes('-alpha', '0.95')
        characters = list(ascii_letters + digits)
        intro_text = Label(generate_root, text='Generate a random sequence', font='arial 10 underline')
        length_entry = Entry(generate_root, width=15)
        sym_text = Label(generate_root, text='induce symbols?')
        sym_button = Button(generate_root, text='✖')
        enter_button = Button(generate_root, text='Enter', width=8, height=1)
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
                messagebox.showerror('error', 'didn\'t write the length')
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

    # font size up by 1 iterations
    def size_up_shortcut(self, event=None):
        self.font_Size_c += 1
        try:
            self.font_size.current(self.font_Size_c)
            self.change_font_size()
        except Exception:
            messagebox.showerror('error', 'font size at maximum')

    # font size down by 1 iterations
    def size_down_shortcut(self, event=None):
        self.font_Size_c -= 1
        try:
            self.font_size.current(self.font_Size_c)
            self.change_font_size()
        except Exception:
            messagebox.showerror('error', 'font size at minimum')

    def custom_ui_colors(self, components):
        if components == 'buttons':
            selected_color = colorchooser.askcolor(title='Buttons background color')[1]
            if selected_color:
                for toolbar_button in self.toolbar_components:
                    toolbar_button.config(background=selected_color)
        elif components == 'menus':
            selected_main_color = colorchooser.askcolor(title='Menu color')[1]
            selected_text_color = colorchooser.askcolor(title='Menu text color')[1]
            if selected_main_color and selected_text_color:
                for menu_ in self.menus_components:
                    menu_.config(background=selected_main_color, foreground=selected_text_color)
        elif components == 'app':
            selected_main_color = colorchooser.askcolor(title='Frames color')[1]
            selected_second_color = colorchooser.askcolor(title='Text box color')[1]
            selected_text_color = colorchooser.askcolor(title='Text color')[1]
            if selected_main_color and selected_second_color and selected_text_color:
                self.config(bg=selected_main_color)
                self.status_bar.config(bg=selected_main_color, fg=selected_text_color)
                self.file_bar.config(bg=selected_main_color, fg=selected_text_color)
                self.EgonTE.config(bg=selected_second_color)
                self.toolbar_frame.config(bg=selected_main_color)

    # checks if text in the main text box is being marked
    def is_marked(self):
        if self.EgonTE.tag_ranges('sel'):
            return True
        else:
            return False

    # tags and configurations of the same thing is clashing all the time \:
    def delete_tags(self):
        self.EgonTE.tag_delete('bold', 'underline', 'italics', 'size', 'colored_txt')
        # self.font_Size_c = 4
        # self.font_size.current(self.font_Size_c)

    def special_files_import(self, via='file'):
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
            if special_file.endswith('xml'):
                content = pandas.read_xml(special_file).to_string()
            elif special_file.endswith('csv'):
                content = pandas.read_csv(special_file).to_string()
            elif special_file.endswith('json'):
                content = pandas.read_json(special_file).to_string()
            elif special_file.endswith('xlsx'):
                content = pandas.read_excel(special_file).to_string()
            elif special_file.endswith('pdf'):
                file = PdfReader(special_file)
                pages_number = len(file.pages)
                content = []
                for i in range(pages_number):
                    page = (file.pages[i]).extract_text()
                    content.append(page)
                content = ''.join(content)
            else:
                messagebox.showerror('error', 'nothing found / unsupported file type')
            self.EgonTE.insert(self.get_pos(), content)
        except AttributeError:
            messagebox.showerror('error', 'please enter a valid domain')

    # a window that have explanations confusing features
    def info_page(self, path):
        # window
        self.info_page_activated = True
        info_root = Toplevel()
        info_root.resizable(False, False)
        info_root.config(bg='white')

        # putting the lines in order
        def place_lines():
            self.info_page_text.delete('1.0', END)
            with open(path) as ht:
                for line in ht:
                    self.info_page_text.insert('end', line)

        # lines = str(lines)
        # lines.remove('{')
        # lines.remove('}')
        #
        info_root_frame = Frame(info_root)
        info_root_frame.pack(pady=5)
        title_frame = Frame(info_root_frame)
        title_frame.pack()
        help_text_scroll = ttk.Scrollbar(info_root_frame)
        # labels
        self.info_page_title = Label(title_frame, text='Help', font='arial 16 bold underline', justify='left')
        self.info_page_text = Text(info_root_frame, font='arial 10', borderwidth=3, bg='light grey', state='normal',
                                   yscrollcommand=help_text_scroll.set, relief=RIDGE, wrap=WORD)

        if path == 'patch_notes.txt':
            self.info_page_title.configure(text='Patch notes')

        self.info_page_text.focus_set()
        # add lines
        place_lines()
        self.info_page_text.config(state='disabled')
        # placing
        info_root_frame.pack(pady=3)
        self.info_page_title.pack(fill=X, anchor=W)
        help_text_scroll.pack(side=RIGHT, fill=Y)
        self.info_page_text.pack(fill=BOTH, expand=True)
        help_text_scroll.config(command=self.info_page_text.yview)

    def right_align_language_support(self):
        if self.EgonTE.get('1.0', 'end'):
            lan = polyglot.Text(self.EgonTE.get('1.0', 'end')).language.name
            if lan == 'Arabic' or 'Hebrew' or 'Persian' or 'Pashto' or 'Urdu' or 'Kashmiri' or 'Sindhi':
                self.align_right()

    def search_www(self):
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
                        messagebox.showerror('Error', 'browser was not found')
                    except IndexError:
                        messagebox.showerror('Error', 'internet connection / general problems')
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

        title = Label(ser_root, text='Search with google', font='arial 14 underline')
        entry_box = Entry(ser_root, relief=GROOVE, width=40)
        enter_button = Button(ser_root, relief=FLAT, command=enter, text='Enter')
        from_text_button = Button(ser_root, relief=FLAT, command=copy_from_file, text='Copy from text')

        title.grid(row=0, column=1, padx=10, pady=3)
        entry_box.grid(row=1, column=1, padx=10)
        enter_button.grid(row=2, column=1)
        from_text_button.grid(row=3, column=1, pady=5)

        # advance options
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
        # self.file_ = False
        # self.status_ = False

        def exit_op():
            self.op_active = ''
            opt_root.destroy()

        def change_button_color(button_family, button):
            if button_family == 'cursors':
                for adv_cursor_b in adv_cursor_bs:
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
                for adv_style_b in adv_style_bs:
                    adv_style_b.config(bg='SystemButtonFace')
                if button == 'clam':
                    style_clam.config(bg='grey')
                elif button == 'vista':
                    style_vista.config(bg='grey')
                elif button == 'classic':
                    style_classic.config(bg='grey')
            elif button_family == 'relief':
                for adv_reliefs_b in adv_reliefs_bs:
                    adv_reliefs_b.config(bg='SystemButtonFace')
                if button == 'ridge':
                    relief_ridge.config(bg='grey')
                elif button == 'groove':
                    relief_groove.config(bg='grey')
                elif button == 'flat':
                    relief_flat.config(bg='grey')

        def adv_custom_cursor(cursor):
            self.EgonTE.config(cursor=cursor)
            self.data['cursor'] = cursor
            try:
                sort_input.config(cursor=cursor)
                translate_box.config(cursor=cursor)
            except BaseException:
                pass
            change_button_color('cursors', cursor)
            self.predefined_cursor = cursor

        def hide_(bar):
            if bar == 'statusbar':
                if self.status_:
                    self.status_bar.pack_forget()
                    self.geometry(f'{self.width}x{self.height - 30}')
                    self.status_ = False
                    self.data['status_bar'] = self.status_
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
                    self.data['file_bar'] = self.file_
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
            change_button_color('styles', style_)
            self.predefined_style = style_
            self.data['style'] = style_

        def change_relief(relief_):
            self.EgonTE.config(relief=relief_)
            try:
                sort_input.config(relief=relief_)
                translate_box.config(relief=relief_)
            except BaseException:
                pass
            change_button_color('relief', relief_)
            self.predefined_relief = relief_
            self.data['relief'] = relief_

        def change_transparency():
            tranc = int(transparency_config.get()) / 100
            self.attributes('-alpha', tranc)
            self.data['transparency'] = tranc

        # window
        global opt_root
        opt_root = Toplevel()
        opt_root.resizable(False, False)
        self.op_active = True
        opt_root.protocol('WM_DELETE_WINDOW', exit_op)

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

        # default values for the check buttons
        self.def_val1 = IntVar()
        self.def_val2 = IntVar()

        button_width = 8
        font_ = 'arial 10 underline'
        predefined_checkbuttons()
        # ui
        opt_title = Label(opt_root, text='Advance Options', font='calibri 16 bold')
        cursor_title = Label(opt_root, text='Advance Cursor configuration', font=font_)
        tcross_button = Button(opt_root, text='tcross', command=lambda: adv_custom_cursor('tcross'), width=button_width)
        arrow_button = Button(opt_root, text='arrow', command=lambda: adv_custom_cursor('arrow'), width=button_width)
        crosshair_button = Button(opt_root, text='crosshair',
                                  command=lambda: adv_custom_cursor('crosshair'), width=button_width)
        pencil_button = Button(opt_root, text='pencil', command=lambda: adv_custom_cursor('pencil'), width=button_width)
        fleur_button = Button(opt_root, text='fleur', command=lambda: adv_custom_cursor('fleur'), width=button_width)
        xterm_button = Button(opt_root, text='xterm', command=lambda: adv_custom_cursor('xterm'), width=button_width)
        hide_title = Label(opt_root, text='Advance hide status & file bar', font=font_)
        filebar_check = Checkbutton(opt_root, text='filebar', command=lambda: hide_('filebar'), variable=self.def_val1)
        statusbar_check = Checkbutton(opt_root, text='statusbar', command=lambda: hide_('statusbar'),
                                      variable=self.def_val2)
        style_title = Label(opt_root, text='Advance style configuration', font=font_)
        style_clam = Button(opt_root, text='clam', command=lambda: change_style('clam'), width=button_width)
        style_classic = Button(opt_root, text='classic', command=lambda: change_style('classic'), width=button_width)
        style_vista = Button(opt_root, text='vista', command=lambda: change_style('vista'), width=button_width)
        relief_title = Label(opt_root, text='Advance relief configuration', font=font_)
        relief_flat = Button(opt_root, text='flat', command=lambda: change_relief('flat'), width=button_width)
        relief_ridge = Button(opt_root, text='ridge', command=lambda: change_relief('ridge'), width=button_width)
        relief_groove = Button(opt_root, text='groove', command=lambda: change_relief('groove'), width=button_width)

        transparency_title = Label(opt_root, text='Transparency configuration', font=font_)
        transparency_config = Scale(opt_root, from_=10, to=100, orient='horizontal')
        transparency_config.set(100)
        transparency_set = Button(opt_root, text='Change transparency', command=change_transparency)
        self.usage_time = Label(opt_root)

        # placing
        opt_title.grid(row=0, column=1, pady=5)
        cursor_title.grid(row=1, column=1)
        tcross_button.grid(row=2, column=0)
        arrow_button.grid(row=2, column=1)
        crosshair_button.grid(row=2, column=2, padx=3)
        pencil_button.grid(row=3, column=0)
        fleur_button.grid(row=3, column=1)
        xterm_button.grid(row=3, column=2)
        hide_title.grid(row=4, column=1)
        filebar_check.grid(row=5, column=0)
        statusbar_check.grid(row=5, column=2)
        style_title.grid(row=6, column=1)
        style_clam.grid(row=7, column=0)
        style_classic.grid(row=7, column=1)
        style_vista.grid(row=7, column=2)
        relief_title.grid(row=8, column=1)
        relief_flat.grid(row=9, column=0)
        relief_ridge.grid(row=9, column=1)
        relief_groove.grid(row=9, column=2, pady=3)
        transparency_title.grid(row=10, column=1)
        transparency_config.grid(row=11, column=1)
        transparency_set.grid(row=12, column=1)
        self.usage_time.grid(row=20, column=1)
        # buttons list
        adv_cursor_bs = tcross_button, arrow_button, crosshair_button, pencil_button, fleur_button, xterm_button
        adv_style_bs = style_clam, style_vista, style_classic
        adv_reliefs_bs = relief_groove, relief_flat, relief_ridge
        # button
        if self.predefined_cursor or self.predefined_style or self.predefined_relief:
            change_button_color('cursors', self.predefined_cursor)
            change_button_color('styles', self.predefined_style)
            change_button_color('relief', self.predefined_relief)

    def goto(self, event=None):
        def enter():
            word = goto_input.get()
            starting_index = self.EgonTE.search(word, '1.0', END)
            offset = '+%dc' % len(word)
            if starting_index:
                ending_index = starting_index + offset
                index = self.EgonTE.search(word, ending_index, END)
            self.EgonTE.mark_set('insert', ending_index)

        # window
        goto_root = Toplevel()
        goto_root.resizable(False, False)
        # ui components
        goto_text = Label(goto_root, text='Enter the word that you wish to go to:', font='arial 10 underline')
        goto_input = Entry(goto_root, width=20)
        goto_button = Button(goto_root, text='Go to', pady=3, command=enter)
        goto_text.grid(row=0, sticky=NSEW, column=0, padx=3)
        goto_input.grid(row=3, column=0)
        goto_button.grid(row=4, column=0, pady=5)

    def sort(self):
        global mode_, sort_data_sorted, str_loop, sort_rot, sort_input

        def sort_():
            global mode_, sort_data_sorted, str_loop
            sort_data = sort_input.get('1.0', 'end')
            sort_data_sorted = (sorted(sort_data))
            # sort_data_sorted = (''.join(str(sorted((sort_data.split(' '))))).replace(('['), ' '))
            # sort_data_sorted = sort_data_sorted.replace(']', '')
            # sort_data_sorted = sort_data_sorted.replace('\'', '')
            # sort_data_sorted = sort_data_sorted.replace('\n', '')
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

        # window
        sort_root = Toplevel()
        sort_root.resizable(False, False)
        sort_root.attributes('-alpha', '0.95')
        # variable
        mode_ = 'asc'
        str_loop = 1
        end_loop = 0
        # ui components
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
        # sort_text.grid(row=0, sticky=NSEW, column=0, padx=3)
        # sort_input.grid(row=1, column=0)
        # sort_frame.grid(row=1)
        # sort_scroll.grid(row=1, column=1)
        # sort_button.grid(row=2, column=0)
        # mode_button.grid(row=3, column=0)
        # sort_insert.grid(row=4, column=0, pady=5)

    def knowledge_window(self, mode):
        def search():
            try:
                meaning_box.configure(state=NORMAL)
                meaning_box.delete('1.0', 'end')
                if mode == 'dict':
                    dict_ = PyDictionary()
                    self.def_ = dict_.meaning(par_entry.get())

                    for key, value in self.def_.items():
                        meaning_box.insert(END, key + '\n\n')
                        for values in value:
                            meaning_box.insert(END, f'-{values}\n\n')
                    meaning_box.configure(state=DISABLED)
            except AttributeError:
                messagebox.showerror('Error', 'check your internet / your search!')
            else:
                try:
                    if wiki_var.get() == 1:
                        wiki_ = summary(par_entry.get())
                    elif wiki_var.get() == 2:
                        wiki_ = wiki_search(par_entry.get())
                    elif wiki_var.get() == 3:
                        wiki_page = page(par_entry.get())
                        wiki_ = f'{wiki_page.title}\n{wiki_page.content}'
                    elif wiki_var.get() == 4:
                        wiki_page = page(par_entry.get())
                        wiki_ = wiki_page.images
                    meaning_box.insert(self.get_pos(), wiki_)
                    paste_b.configure(state=ACTIVE)
                except requests.exceptions.ConnectionError:
                    messagebox.showerror('Error', 'check your internet connection')
                except exceptions.DisambiguationError:
                    messagebox.showerror('Error', 'check your searched term')
                except exceptions.PageError:
                    messagebox.showerror('Error', 'Invalid page ID')

        def paste():
            if mode == 'dict':
                for key, value in self.def_.items():
                    self.EgonTE.insert(self.get_pos(), key + '\n\n')
                    for values in value:
                        self.EgonTE.insert(self.get_pos(), f'-{values}\n\n')
            else:
                if wiki_var.get() == 1:
                    wiki_ = summary(par_entry.get())
                elif wiki_var.get() == 2:
                    wiki_ = wiki_search(par_entry.get())
                elif wiki_var.get() == 3:
                    wiki_page = page(par_entry.get())
                    wiki_ = f'{wiki_page.title}\n{wiki_page.content}'
                elif wiki_var.get() == 4:
                    wiki_page = page(par_entry.get())
                    wiki_ = wiki_page.images
                self.EgonTE.insert(self.get_pos(), wiki_)

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
            wiki_var = IntVar()
            wiki_var.set(1)
            radio_frame = Frame(par_root)
            return_summery = Radiobutton(radio_frame, text='Summery', variable=wiki_var, value=1)
            return_related_articles = Radiobutton(radio_frame, text='Related articles', variable=wiki_var, value=2)
            return_content = Radiobutton(radio_frame, text='Content', variable=wiki_var, value=3)
            return_images = Radiobutton(radio_frame, text='Images', variable=wiki_var, value=4)

            radio_frame.grid(row=4, column=1)

            return_summery.grid(row=0, column=0)
            return_related_articles.grid(row=0, column=2)
            return_content.grid(row=1, column=0)
            return_images.grid(row=1, column=2)

    def virtual_keyboard(self):
        key = Toplevel()  # key window name
        key.attributes('-alpha', '0.90')
        # key.iconbitmap('add icon link And Directory name')    # icon add

        # function coding start

        exp = ' '  # global variable

        # showing all data in display

        def press(num):
            global exp
            self.EgonTE.insert(self.get_pos(), num)

        def tab():
            exp = '    '
            self.EgonTE.insert(self.get_pos(), exp)

        def modes(mode):
            characters = [A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z]
            if mode == 'upper':
                for asc in range(len(ascii_uppercase)):
                    characters[asc].configure(text=ascii_uppercase[asc],
                                              command=lambda i=asc: press(ascii_uppercase[i]))
                    caps.configure(command=lambda: modes('lower'))
            else:
                for asc in range(len(ascii_lowercase)):
                    characters[asc].configure(text=ascii_lowercase[asc],
                                              command=lambda i=asc: press(ascii_lowercase[i]))
                    caps.configure(command=lambda: modes('upper'))

        # Size window size
        key.geometry('630x200')  # normal size
        key.resizable(False, False)
        # end window size

        key.configure(bg='black')  # add background color

        Q = ttk.Button(key, text='Q', width=6, command=lambda: press('Q'))
        Q.grid(row=1, column=0, ipady=10)

        W = ttk.Button(key, text='W', width=6, command=lambda: press('W'))
        W.grid(row=1, column=1, ipady=10)

        E = ttk.Button(key, text='E', width=6, command=lambda: press('E'))
        E.grid(row=1, column=2, ipady=10)

        R = ttk.Button(key, text='R', width=6, command=lambda: press('R'))
        R.grid(row=1, column=3, ipady=10)

        T = ttk.Button(key, text='T', width=6, command=lambda: press('T'))
        T.grid(row=1, column=4, ipady=10)

        Y = ttk.Button(key, text='Y', width=6, command=lambda: press('Y'))
        Y.grid(row=1, column=5, ipady=10)

        U = ttk.Button(key, text='U', width=6, command=lambda: press('U'))
        U.grid(row=1, column=6, ipady=10)

        I = ttk.Button(key, text='I', width=6, command=lambda: press('I'))
        I.grid(row=1, column=7, ipady=10)

        O = ttk.Button(key, text='O', width=6, command=lambda: press('O'))
        O.grid(row=1, column=8, ipady=10)

        P = ttk.Button(key, text='P', width=6, command=lambda: press('P'))
        P.grid(row=1, column=9, ipady=10)

        cur = ttk.Button(key, text='{', width=6, command=lambda: press('{'))
        cur.grid(row=1, column=10, ipady=10)

        cur_c = ttk.Button(key, text='}', width=6, command=lambda: press('}'))
        cur_c.grid(row=1, column=11, ipady=10)

        back_slash = ttk.Button(key, text='\\', width=6, command=lambda: press('\\'))
        back_slash.grid(row=1, column=10, ipady=10)

        A = ttk.Button(key, text='A', width=6, command=lambda: press('A'))
        A.grid(row=2, column=0, ipady=10)

        S = ttk.Button(key, text='S', width=6, command=lambda: press('S'))
        S.grid(row=2, column=1, ipady=10)

        D = ttk.Button(key, text='D', width=6, command=lambda: press('D'))
        D.grid(row=2, column=2, ipady=10)

        F = ttk.Button(key, text='F', width=6, command=lambda: press('F'))
        F.grid(row=2, column=3, ipady=10)

        G = ttk.Button(key, text='G', width=6, command=lambda: press('G'))
        G.grid(row=2, column=4, ipady=10)

        H = ttk.Button(key, text='H', width=6, command=lambda: press('H'))
        H.grid(row=2, column=5, ipady=10)

        J = ttk.Button(key, text='J', width=6, command=lambda: press('J'))
        J.grid(row=2, column=6, ipady=10)

        K = ttk.Button(key, text='K', width=6, command=lambda: press('K'))
        K.grid(row=2, column=7, ipady=10)

        L = ttk.Button(key, text='L', width=6, command=lambda: press('L'))
        L.grid(row=2, column=8, ipady=10)

        semi_co = ttk.Button(key, text=';', width=6, command=lambda: press(';'))
        semi_co.grid(row=2, column=9, ipady=10)

        d_colon = ttk.Button(key, text='"', width=6, command=lambda: press('"'))
        d_colon.grid(row=2, column=10, ipady=10)

        Z = ttk.Button(key, text='Z', width=6, command=lambda: press('Z'))
        Z.grid(row=3, column=0, ipady=10)

        X = ttk.Button(key, text='X', width=6, command=lambda: press('X'))
        X.grid(row=3, column=1, ipady=10)

        C = ttk.Button(key, text='C', width=6, command=lambda: press('C'))
        C.grid(row=3, column=2, ipady=10)

        V = ttk.Button(key, text='V', width=6, command=lambda: press('V'))
        V.grid(row=3, column=3, ipady=10)

        B = ttk.Button(key, text='B', width=6, command=lambda: press('B'))
        B.grid(row=3, column=4, ipady=10)

        N = ttk.Button(key, text='N', width=6, command=lambda: press('N'))
        N.grid(row=3, column=5, ipady=10)

        M = ttk.Button(key, text='M', width=6, command=lambda: press('M'))
        M.grid(row=3, column=6, ipady=10)

        left = ttk.Button(key, text='<', width=6, command=lambda: press('<'))
        left.grid(row=3, column=7, ipady=10)

        right = ttk.Button(key, text='>', width=6, command=lambda: press('>'))
        right.grid(row=3, column=8, ipady=10)

        slas = ttk.Button(key, text='/', width=6, command=lambda: press('/'))
        slas.grid(row=3, column=9, ipady=10)

        q_mark = ttk.Button(key, text='?', width=6, command=lambda: press('?'))
        q_mark.grid(row=3, column=10, ipady=10)

        coma = ttk.Button(key, text=',', width=6, command=lambda: press(','))
        coma.grid(row=3, column=11, ipady=10)

        dot = ttk.Button(key, text='.', width=6, command=lambda: press('.'))
        dot.grid(row=2, column=11, ipady=10)

        space = ttk.Button(key, text='Space', width=6, command=lambda: press(' '))
        space.grid(row=4, columnspan=7, ipadx=160, ipady=10)

        open_b = ttk.Button(key, text='(', width=6, command=lambda: press('('))
        open_b.grid(row=4, column=7, ipady=10)

        close_b = ttk.Button(key, text=')', width=6, command=lambda: press(')'))
        close_b.grid(row=4, column=8, ipady=10)

        tap = ttk.Button(key, text='Tab', width=6, command=tab)
        tap.grid(row=4, column=9, ipady=10)

        caps = ttk.Button(key, text='Caps', width=6, command=lambda: modes('lower'))
        caps.grid(row=4, column=10, ipady=10)

        key.mainloop()  # using ending point

    def emoji_detection(self, event=None, via_settings=False):
        content = self.EgonTE.get(1.0, END).split(' ')
        content[-1] = content[-1].strip('\n')
        new_content = []
        for word in content:
            word = emoji.emojize(word)
            new_content.append(emoji.emojize(word))
            if emoji.is_emoji(word):
                if via_settings:
                    messagebox.showinfo('', 'emoji(s) found!')
                    fail_msg = False
            else:
                fail_msg = True
        if fail_msg:
            messagebox.showinfo('', 'emoji(s) didn\'t found!')
        self.EgonTE.delete('1.0', 'end')
        self.EgonTE.insert('1.0', new_content)
        if via_settings == False:
            self.EgonTE.insert(self.get_pos(), ' ')

    def emoji_list(self):
        emoji_root = Toplevel()
        e_list = emoji.get_emoji_unicode_dict('en')
        scroll = ttk.Scrollbar(emoji_root)
        emoji_label = Text(emoji_root, yscrollcommand=scroll.set, cursor=self.predefined_cursor,
                           relief=self.predefined_relief)
        for emj, emj_code in e_list.items():
            emoji_label.insert('end', f'{emj} - {emj_code}\n')
        emoji_label.configure(state=DISABLED)
        scroll.pack(side=RIGHT, fill=Y)
        emoji_label.pack(fill=BOTH, expand=True)
        scroll.config(command=emoji_label.yview)

    def file_info(self):
        if self.file_name:
            try:
                root = Toplevel()
                root.title('File information')
                # getting file info
                file_size = os.path.getsize(self.file_name)
                modified_time = datetime.fromtimestamp((os.path.getmtime(self.file_name)))
                creation_time = datetime.fromtimestamp((os.path.getctime(self.file_name)))
                file_type = os.path.splitext(self.file_name)[-1]
                # attaching info to labels
                size_label = Label(root, text=f'file size - {file_size} bytes', font='arial 14 bold')
                modified_time_label = Label(root, text=f'file modified time - {modified_time}', font='arial 14 bold')
                creation_time_label = Label(root, text=f'file creation time - {creation_time}', font='arial 14 bold')
                file_type_label = Label(root, text=f'file type - {file_type}', font='arial 14 bold')
                # packing
                size_label.pack(expand=True)
                modified_time_label.pack(expand=True)
                creation_time_label.pack(expand=True)
                file_type_label.pack(expand=True)
                root.resizable(False, False)
            except NameError:
                messagebox.showerror('error', 'you aren\'nt using a file!')
            except PermissionError:
                messagebox.showerror('error', 'you are not using a file!')
        else:
            messagebox.showerror('error', 'you are not using a file!')

    def auto_save(self):
        t = 300
        while self.aus:
            while t:
                mins, secs = divmod(t, 60)
                timer = '{:02d}:{:02d}'.format(mins, secs)
                print(timer)
                time.sleep(1)
                t -= 1
            if self.file_name:
                self.save()
        # Thread(target=self.auto_save()).start()

    def auto_lists(self):
        if self.aul:
            # boolean vars to identify if there's a list
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
        file_content = self.EgonTE.get('1.0', 'end').splitlines()
        another_file = filedialog.askopenfilename(initialdir=os.getcwd(), title='Open file to compare',
                                                  filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html'),
                                                             ('Python Files', '*.py')))
        if another_file:
            try:
                compare_root = Toplevel()
                compare_root.title('compression between 2 files')
                another_file = open(another_file, 'r')
                another_fc = another_file.read()
                # the precise diffrence in content
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
                    formatted_count = f'number of words{num_words}\nnumber of lines{num_lines}\n' \
                                      f'number of characters{num_charc}\nnumber of spaces{num_spaces}'
                    return formatted_count

                count_frame = Frame(compare_root)
                file_counts_title = Label(count_frame, text='File Counts', font='arial 14 underline bold')
                fc_title1 = Label(count_frame, text='Your first file', font='arial 10 underline')
                fc_title2 = Label(count_frame, text='Your second file', font='arial 10 underline')
                file_1_count = Label(count_frame, text=counts_file(file_content))
                file_2_count = Label(count_frame, text=counts_file(another_fc))

                c_diffrence_frame.pack()
                c_difference_title.pack()
                content_diffrence.pack()

                count_frame.pack()
                file_counts_title.grid(row=0, column=1)
                fc_title1.grid(row=1, column=0)
                fc_title2.grid(row=1, column=2)
                file_1_count.grid(row=2, column=0)
                file_2_count.grid(row=2, column=2)

                another_file.close()

            except UnicodeDecodeError:
                messagebox.showerror('Error', 'unsupported characters')

    def corrector(self):
        content = self.EgonTE.get('1.0', 'end')
        corrected_content = TextBlob(content).correct()
        self.EgonTE.delete('1.0', 'end')
        self.EgonTE.insert('1.0', corrected_content)

    def organize(self):
        '''

        '''
        content = self.EgonTE.get('1.0', 'end')  # .split(' ')
        # content = content.split(' ')

        # part 1: separate connected words (identifying via capital letters)
        words = findall('[A-Z][a-z]*', content)

        # Change first letter of each word into lower case words[0] = words[0][0].capitalize()
        for i in range(0, len(words)):
            # need to add a condition
            if findall('^[A-Z]', content):
                words[i] = words[i][0].capitalize() + words[i][1:]  # lower() ?
        corrected_content = (' '.join(words))

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
        # fix requests returning mostly only text - (content)?
        main_titles_font = 'arial 14 underline'
        sub_titles_font = 'arial 12 underline'
        return_type = StringVar()
        return_type.set('text')
        connection = True
        file_via_internet = False
        limit = None

        def get_html_web():
            try:
                web_url = urllib.request.Request(path, headers={'User-Agent': 'Mozilla/5.0'})
                content = urllib.request.urlopen(web_url).read()
                return content
            except urllib.error.HTTPError as e:
                messagebox.showerror('Error', str(e))

        def upload(via):
            if via == 'file':
                try:
                    path = filedialog.askopenfilename(title='Open file to scrape',
                                                      filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html')))
                    with open(path, 'r') as content:
                        lines = content.readlines()
                    self.soup = BeautifulSoup(lines, 'html')
                except FileNotFoundError:
                    messagebox.showerror('EgonTE', 'file not found')
            else:
                path = simpledialog.askstring('EgonTE', 'Enter a path')
                # content = requests.get(path).content
                self.soup = BeautifulSoup(get_html_web(), 'html')
            file_name_output.configure(text=path)

        def search():
            global file_via_internet
            # output_root = Toplevel()
            output_frame = Frame(ws_root)
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

            # work on these conditions!
            if tag_input.get() and class_input.get():
                scraped_content = self.soup.find_all(tag_input.get(), class_=class_input.get())
                output_box.insert('1.0', scraped_content)

            elif tag_input.get():
                html_tags = self.soup.find_all(tag_input.get())
                for html_tag in html_tags:
                    if return_type == 'text':
                        output_box.insert('end', html_tag.text)
                    elif return_type == 'attrs':
                        output_box.insert('end', html_tag.attrs)
                    else:
                        output_box.insert('end', html_tag)
            elif class_input.get():
                # class_r = self.soup.find_all(class_=class_input.get())
                # for cls in class_r:
                #     pass
                class_list = set()
                tags = {tag.name for tag in self.soup.find_all()}
                for tag in tags:

                    # find all element of tag

                    for i in self.soup.find_all(tag):

                        # if tag has attribute of class

                        if i.has_attr('class'):

                            if len(i['class']) != 0:
                                class_list.add(' '.join(i['class']))
                output_box.insert('1.0', ''.join(class_list))
            else:
                if return_type == 'text':
                    output_box.insert('end', self.soup.text)
                elif return_type == 'attrs':
                    output_box.insert('end', self.soup.attrs)
                elif return_type == 'cntn':
                    output_box.insert('end', self.soup.contents)
                else:
                    output_box.insert('end', self.soup.prettify())
            output_box.configure(state=DISABLED)

        def main_ui():
            global ws_root, tag_input, file_name_output, file_via_internet, chosen_init, class_input
            if connection:
                ws_root = Toplevel()
                ws_root.title('Scrapping')
                ws_root.resizable(False, False)
                info_title = Label(ws_root, text='Quick information', font=main_titles_font)
                file_title = Label(ws_root, text='file name:', font=sub_titles_font)
                file_name_output = Label(ws_root, text=path)

                upload_title = Label(ws_root, text='Upload a new content', font=main_titles_font)
                upload_file = Button(ws_root, text='Upload via file', command=lambda: upload('file'))
                upload_link = Button(ws_root, text='Upload via link', command=lambda: upload('link'))
                identifiers_title = Label(ws_root, text='Identifiers', font=main_titles_font)
                tag_title = Label(ws_root, text='tags:', font=sub_titles_font)
                tag_input = Entry(ws_root)
                class_title = Label(ws_root, text='classes:', font=sub_titles_font)
                class_input = Entry(ws_root)
                return_title = Label(ws_root, text='Return', font=main_titles_font)
                only_text_rb = Radiobutton(ws_root, text='Only text', variable=return_type, value='text')
                only_attrs_rb = Radiobutton(ws_root, text='Only attributes', variable=return_type, value='attrs')
                only_cntn_rb = Radiobutton(ws_root, text='All content', variable=return_type, value='ctnt')
                search_button = Button(ws_root, text='Search', command=search)

                try:
                    if file_via_internet:
                        file_name_output.configure(text=Shortener().tinyurl.short(path))
                        code_title = Label(ws_root, text='Status code:', font=sub_titles_font)
                        status_code = Label(ws_root, text=response.status_code)
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
                    upload_link.grid(row=4, column=2)
                    identifiers_title.grid(row=5, column=1)
                    tag_title.grid(row=6, column=0)
                    class_title.grid(row=6, column=2)
                    tag_input.grid(row=7, column=0)
                    class_input.grid(row=7, column=2)
                    return_title.grid(row=8, column=1)
                    only_cntn_rb.grid(row=9, column=0)
                    only_text_rb.grid(row=9, column=1)
                    only_attrs_rb.grid(row=9, column=2)
                    search_button.grid(row=10, column=1)
                except NameError:
                    ws_root.destroy()
                    messagebox.showerror('EgonTE', 'the program had an error')

        def active():
            global file_via_internet, path, connection, response, chosen_init
            init_root.destroy()
            # take content from your machine or from the web
            if chosen_init == 'this':
                file_via_internet = False
                path = self.file_name
                # if messagebox.askquestion('EgonTE', 'what you wish to scrape'):
                self.soup = BeautifulSoup(self.EgonTE.get('1.0', 'end'), 'html.parser')
            elif chosen_init == 'web':
                path = simpledialog.askstring('EgonTE', 'Enter a path')
                if path:
                    messagebox.showinfo('EgonTE', 'web scrapping can be problematic because of the website\'s policy \n'
                                                  'be sure to check it up ')
                    try:
                        file_via_internet = True
                        response = requests.get(path)
                        # returns only text!!!!!!!
                        self.soup = BeautifulSoup(get_html_web(), 'html.parser')
                    except requests.exceptions.ConnectionError:
                        messagebox.showerror('EgonTE', 'Device not connected to internet')
                        connection = False
                    except requests.exceptions.MissingSchema:
                        response = requests.get(f'http://{path}')
                        self.soup = BeautifulSoup(get_html_web(), 'html.parser')
                    except requests.exceptions.InvalidSchema:
                        messagebox.showerror('EgonTE', 'Invalid link')
                        connection = False
                    except requests.exceptions.InvalidURL:
                        messagebox.showerror('EgonTE', 'Invalid URL')

            elif chosen_init == 'local':
                file_via_internet = False
                path = filedialog.askopenfilename(title='Open file to scrape', filetypes=[('HTML FILES', '*.html')])
                file = open(path).read()
                self.soup = BeautifulSoup(file, 'html.parser')

            main_ui()

        def change_initial_mode(mode):
            global chosen_init
            for b in init_b_list:
                b.configure(background='SystemButtonFace')
            if mode == 't':
                this_button.configure(background='light grey')
                chosen_init = 'this'
            elif mode == 'w':
                web_button.configure(background='light grey')
                chosen_init = 'web'
            else:
                loc_button.configure(background='light grey')
                chosen_init = 'local'

        # init window to not delay / limit users
        chosen_init = 'web'
        init_root = Toplevel()
        init_root.title('EgonTE - web scrapping')
        title_label = Label(init_root, text='What you would like to scrape?', font='arial 10 underline')
        web_button = Button(init_root, text='A website', command=lambda: change_initial_mode('w'))
        loc_button = Button(init_root, text='A Local file', command=lambda: change_initial_mode('l'))
        enter_button = Button(init_root, text='Enter', command=active, font='arial 10 bold')
        title_label.grid(row=1, column=1)
        web_button.grid(row=2, column=0, padx=5)
        loc_button.grid(row=2, column=2, padx=5)
        enter_button.grid(row=3, column=1, pady=5)

        init_b_list = [web_button, loc_button]

        if self.file_name.endswith('html'):
            this_button = Button(init_root, text='This file', command=lambda: change_initial_mode('t'))
            init_b_list = init_b_list + [this_button]
            this_button.grid(row=2, column=1)

    def handwriting(self):
        global previous_point, current_point
        previous_point = [0, 0]
        current_point = [0, 0]
        img_array = ''
        image_name = ''
        color = StringVar()
        color.set('black')
        width = IntVar()
        width.set(1)
        lines_list, images_list = [], []
        canvas_x, canvas_y = 500, 300

        def paint(event):
            global previous_point, current_point
            x = event.x
            y = event.y
            current_point = [x, y]
            # canvas.create_oval(x, y, x+10, y+10, fill='black')
            if previous_point != [0, 0]:
                line = canvas.create_line(previous_point[0], previous_point[1], current_point[0], current_point[1],
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
                canvas.move(l, move_x, move_y)
            for img in images_list:
                canvas.move(img, move_x, move_y)

        def cords(event):
            pos_x, pos_y = event.x, event.y
            cords_label.configure(text=f'X coordinates:{pos_x} | Y coordinates:{pos_y}')

        def upload():
            # tkinter garbage collector have problems with images, to solve that we need to make all of them, global
            global img_array, image, image_tk, image_name
            # load image into the canvas
            image_name = filedialog.askopenfilename(filetypes=self.img_extensions)
            if image_name:
                image = Image.open(image_name)
                # image_tk = ImageTk.PhotoImage(image)
                image_tk = PhotoImage(file=image_name)
                image_x = (canvas_x // 2) - (image.width // 2)
                image_y = (canvas_y // 2) - (image.height // 2)
                canvas_image = canvas.create_image(image_x, image_y, image=image_tk, anchor=NW)
                images_list.append(canvas_image)
                # save modified image later
                # img_array = numpy.asarray(image)

        def save():
            global image_name

            # if image_name and img_array:
            #     img_array.save(image_name)
            image_name = self.save_images(canvas, hw_root)

        def erase():
            color.set('white')
            width.set(5)
            canvas.configure(cursor='target')
            eraser.configure(bg='light gray'), pencil.configure(bg='SystemButtonFace')

        def pencil_():
            width.set(2)
            color.set('black')
            canvas.configure(cursor='pencil')
            pencil.configure(bg='light gray'), eraser.configure(bg='SystemButtonFace')

        def convert():
            if not (image_name):
                save()

            image_txt = Image.open(image_name)
            # Convert the image to grayscale
            # image = image.convert('L')
            # Use Tesseract to extract the text from the image
            if image:
                text = image_to_string(image_txt)
            if text:
                tl = Label(hw_root, text=text)
                tl.pack()

        # drawing board
        hw_root = Toplevel()
        hw_root.title('Draw and convert')
        draw_frame = Frame(hw_root)
        buttons_frame = Frame(hw_root)
        canvas = Canvas(draw_frame, width=canvas_x, height=canvas_y, bg='white', cursor='pencil')
        canvas.bind('<B1-Motion>', paint)
        canvas.bind('<ButtonRelease-1>', paint)
        pencil = Button(buttons_frame, text='Pencil', command=pencil_, borderwidth=1)
        eraser = Button(buttons_frame, text='Eraser', command=erase, borderwidth=1)
        seperator = Label(buttons_frame, text='|')
        save_png = Button(buttons_frame, text='Save as png', command=save, borderwidth=1)
        upload_writing = Button(buttons_frame, text='Upload', command=upload, state=tes, borderwidth=1)
        convert_to_writing = Button(buttons_frame, text='Convert to writing', command=convert,
                                    borderwidth=1)  # convert)
        erase_all = Button(buttons_frame, text='Erase all', command=lambda: canvas.delete('all'), borderwidth=1)
        cords_label = Label(hw_root, text='')
        buttons_frame.pack()
        draw_frame.pack(fill=BOTH, expand=True)
        pencil.grid(row=0, column=0, padx=2)
        eraser.grid(row=0, column=1, padx=2)
        seperator.grid(row=0, column=2)
        erase_all.grid(row=0, column=3, padx=2)
        save_png.grid(row=0, column=4, padx=2)
        upload_writing.grid(row=0, column=5, padx=2)
        convert_to_writing.grid(row=0, column=6, padx=2)
        canvas.pack(fill=BOTH, expand=True)
        cords_label.pack()

        pencil_()
        hw_root.bind('<Left>', lambda e: move(key='left'))
        hw_root.bind('<Right>', lambda e: move(key='right'))
        hw_root.bind('<Up>', lambda e: move(key='up'))
        hw_root.bind('<Down>', lambda e: move(key='down'))
        hw_root.bind('<Motion>', cords)
        # existing file to writing

    def natural_language_process(self, function):
        nlp_root = Toplevel()
        nlp_root.title('EgonTE - natural language processor')
        text = self.EgonTE.get('1.0', 'end')
        nlp = spacy.load('en_core_web_sm')
        # nlp = spacy.load('en')
        doc = spacy.nlp(text)
        if function == 'verbs':
            # ccontent = doc.verb
            verbs = []
            for token in doc:
                if token.pos_ == 'VERB':
                    verbs.append(token)
            result = Label(nlp_root, text=', '.join(str(e) for e in verbs))

        elif function == 'nouns':
            nouns = []
            for token in doc:
                if token.pos_ == 'NOUN':
                    nouns.append(token)
            result = Label(nlp_root, text=', '.join(str(e) for e in nouns))

        elif function == 'adjectives':
            adjectives = []
            for token in doc:
                if token.pos_ == 'ADJ':
                    adjectives.append(token)
            result = Label(nlp_root, text=', '.join(str(e) for e in adjectives))

        elif function == 'adverbs':
            adverbs = []
            for token in doc:
                if token.pos_ == 'ADV':
                    adverbs.append(token)
            result = Label(nlp_root, text=', '.join(str(e) for e in adverbs))

        elif function == 'pronouns':
            pronouns = []
            for token in doc:
                if token.pos_ == 'PRON':
                    pronouns.append(token)
            result = Label(nlp_root, text=', '.join(str(e) for e in pronouns))


        elif function == 'dependency':
            content = {}
            for token in doc:
                content[token.text] = token.dep_
            result = Label(nlp_root, text=content)

        elif function == 'entity recognition':
            content = {}
            for ent in doc.ents:
                content[ent.text] = ent.label_
                result = Label(nlp_root, text=content)


        elif function == 'stop words':
            result = Text(nlp_root)
            spacy_stopwords = spacy.lang.en.stop_words.STOP_WORDS
            # len(spacy_stopwords)
            for stop_word in list(spacy_stopwords):
                result.insert('end', stop_word)
            result.configure(DISABLED)

        elif function == 'lemmatization':
            for token in doc:
                if str(token) != str(token.lemma_):
                    res = (f'{str(token):>20} : {str(token.lemma_)}')
                    result = Label(nlp_root, text=res)

        elif function == 'most common words':
            words = [
                token.text
                for token in doc
                if not token.is_stop and not token.is_punct
            ]
            result = Label(nlp_root, text=Counter(words).most_common(10))  # !!!

        elif function == 'names':
            names = ''
            matcher = Matcher(nlp.vocab)
            # defining a rule
            pattern = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]
            # adding a rule
            matcher.add('FULL_NAME', [pattern])
            matches = matcher(doc)
            for _, start, end in matches:
                span = doc[start:end]
                names += span.text
            result = Label(nlp_root, text=names)

        #         yield span.text
        #
        elif function == 'phone numbers':
            phones = ''
            pattern = [
                {'ORTH': '('},
                {'SHAPE': 'ddd'},
                {'ORTH': ')'},
                {'SHAPE': 'ddd'},
                {'ORTH': '-', 'OP': '?'},
                {'SHAPE': 'dddd'},
            ]
            matcher = Matcher(nlp.vocab)
            matcher.add('PHONE_NUMBER', None, pattern)
            matches = matcher(doc)
            for match_id, start, end in matches:
                span = doc[start:end]
                phones += span.text
                result = Label(nlp_root, text=phones)

        if function != 'most common words':
            title = Label(nlp_root, text=f'{function.capitalize()}:')
        else:
            title = Label(nlp_root, text='Top 10 most common words:')
        title.pack()
        result.pack()

    def saved_settings(self, sm=None):
        '''
        fix the bugs and improve the algo - not ready yet
        '''
        file_name = 'EgonTE_settings.json'
        if os.path.exists(file_name):
            print('file exist')
            with open(file_name, 'r') as f:
                self.data = load(f)
                print(self.data)

            self.rm.set(self.data['reader_mode'])
            self.predefined_cursor = (self.data['cursor'])
            # self.bars_active.set(self.data[])
            self.show_statusbar.set(self.data['status_bar'])
            self.show_toolbar.set(self.data['toolbar'])
            self.night_mode.set(self.data['night_mode'])
            self.cc.set(self.data['cursor'])
            self.cs.set(self.data['style'])
            self.ww.set(self.data['word_warp'])
            self.aus.set(self.data['auto_save'])

        else:
            print('file doesn\'t exist')
            self.data = {'night_mode': False, 'status_bar': True, 'file_bar': True, 'cursor': 'xterm', 'style': 'calm',
                         'word_warp': True, 'reader_mode': False, 'auto_save': True, 'relief': 'ridge',
                         'transparency': 100,
                         'toolbar': True}

            with open(file_name, 'w') as f:
                self.data = dump(self.data, f)
                print(self.data)

        if sm == 'save':
            with open(file_name, 'w') as f:
                self.data = dump(self.data, f)

    def text_decorators(self):
        global chosen_decorator
        # add vertical / horizontal options

        chosen_decorator = 1
        inline = False

        def enter():
            if chosen_decorator == 1:
                a = ('..######..\n..#....#..\n..######..\n..#....#..\n..#....#..\n\n')
                b = ('..######..\n..#....#..\n..#####...\n..#....#..\n..######..\n\n')
                c = ('..######..\n..#.......\n..#.......\n..#.......\n..######..\n\n')
                d = ('..#####...\n..#....#..\n..#....#..\n..#....#..\n..#####...\n\n')
                e = ('..######..\n..#.......\n..#####...\n..#.......\n..######..\n\n')
                f = ('..######..\n..#.......\n..#####...\n..#.......\n..#.......\n\n')
                g = ('..######..\n..#.......\n..#####...\n..#....#..\n..#####...\n\n')
                h = ('..#....#..\n..#....#..\n..######..\n..#....#..\n..#....#..\n\n')
                i = ('..######..\n....##....\n....##....\n....##....\n..######..\n\n')
                j = ('..######..\n....##....\n....##....\n..#.##....\n..####....\n\n')
                k = ('..#...#...\n..#..#....\n..##......\n..#..#....\n..#...#...\n\n')
                l = ('..#.......\n..#.......\n..#.......\n..#.......\n..######..\n\n')
                m = ('..#....#..\n..##..##..\n..#.##.#..\n..#....#..\n..#....#..\n\n')
                n = ('..#....#..\n..##...#..\n..#.#..#..\n..#..#.#..\n..#...##..\n\n')
                o = ('..######..\n..#....#..\n..#....#..\n..#....#..\n..######..\n\n')
                p = ('..######..\n..#....#..\n..######..\n..#.......\n..#.......\n\n')
                q = ('..######..\n..#....#..\n..#.#..#..\n..#..#.#..\n..######..\n\n')
                r = ('..######..\n..#....#..\n..#.##...\n..#...#...\n..#....#..\n\n')
                s = ('..######..\n..#.......\n..######..\n.......#..\n..######..\n\n')
                t = ('..######..\n....##....\n....##....\n....##....\n....##....\n\n')
                u = ('..#....#..\n..#....#..\n..#....#..\n..#....#..\n..######..\n\n')
                v = ('..#....#..\n..#....#..\n..#....#..\n...#..#...\n....##....\n\n')
                w = ('..#....#..\n..#....#..\n..#.##.#..\n..##..##..\n..#....#..\n\n')
                x = ('..#....#..\n...#..#...\n....##....\n...#..#...\n..#....#..\n\n')
                y = ('..#....#..\n...#..#...\n....##....\n....##....\n....##....\n\n')
                z = ('..######..\n......#...\n.....#....\n....#.....\n..######..\n\n')
                sp = ('..........\n..........\n..........\n..........\n\n')
                dot = ('----..----\n\n')
                self.ascii_alph = (a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z,
                                   sp, dot)
                self.ascii_dict = {'a': a, 'b': b, 'c': c, 'd': d, 'e': e, 'f': f, 'g': g, 'h': h, 'i': i, 'j': j,
                                   'k': k, 'l': l,
                                   'm': m, 'n': n, 'o': o, 'p': p, 'q': q, 'r': r, 's': s, 't': t, 'u': u, 'v': v,
                                   'w': w, 'x': x,
                                   'y': y, 'z': z, ' ': sp, '.': dot}

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

            elif chosen_decorator == 4:
                a = ('  ******  \n  *	   *  \n  ******  \n  *	   *  \n  *	   * \n\n')
                b = ('  ******  \n  *	    *  \n  ******   \n  *	    *  \n  ******  \n\n')
                c = ('  ******   \n  *  \n  *	   \n  *	   \n  ******  \n\n')
                d = ('  *****   \n  *	   *  \n  *	   *  \n  *	   *  \n  *****   \n\n')
                e = ('  ******  \n  *	   \n  *****   \n  *	   \n  ******  \n\n')
                f = ('  ******  \n  *	   \n  *****   \n  *	   \n  *	   \n\n')
                g = ('  *******  \n  *	   \n  *   ***   \n  *	    *  \n  *******  \n\n')
                h = ('  *     *  \n  *     *  \n  *******   \n  *     *  \n  *     * \n\n')
                i = ('  **     \n  **  \n  ** \n  **   \n  **   \n\n')
                j = ('  ******  \n	**	\n	**	\n  * **  \n  ****	\n\n')
                k = ('  *   *   \n  *  *  \n  * *   \n  *  *      \n  *   *   \n\n')
                l = ('  *	  \n  *				  \n  *	   \n  *	   \n  ******  \n\n')
                m = ('  *	     *   \n  **    **  \n  *  **  *\n  *	 **  * \n  *	     *  \n\n')
                n = ('  **   *\n  **   *  \n  * *  *  \n  *  * *  \n  *   **  \n\n')
                o = ('   *****   \n  *     *  \n  *     *  \n  *     *  \n   *****  \n\n')
                p = ('  ******  \n  *	    *  \n  ******  \n  *	   \n  *	   \n\n')
                q = ('   ******  \n  *	    *  \n   ******  \n        *	   \n        *	   \n\n')
                r = ('  ******  \n  *	   * \n  * ***   \n  *  *   \n  *	  *  \n\n')
                s = ('  ******	\n  *	  \n  ******  \n	   *  \n  ******   \n\n')
                t = ('  ******  \n	**	 \n	**	\n	**	\n	**	 \n\n')
                u = ('  *	    *  \n  *	    *   \n  *	    *	\n  *	    *	\n   *****   \n\n')
                v = ('  *	   *  \n  *	   *  \n  *	   *  \n   *  *   \n	**	\n\n')
                w = ('  *	     *   \n  *	 **  *   \n  *  **  *\n  **    **  \n  **	**  \n\n')
                x = ('  *	   *  \n   *  *   \n	**	\n   *  *   \n  *	   *  \n\n')
                y = ('  *	   *  \n   *  *   \n	**	\n	**	\n	**	\n\n')
                z = ('   ******   \n     **  \n    **\n   **       \n  ******""  \n\n')
                sp = ('..........\n..........\n..........\n..........\n\n')

                dot = ('----..----\n\n')
                self.ascii_alph = (a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z, sp,
                                   dot)
                self.ascii_dict = {'a': a, 'b': b, 'c': c, 'd': d, 'e': e, 'f': f, 'g': g, 'h': h, 'i': i, 'j': j,
                                   'k': k, 'l': l,
                                   'm': m, 'n': n, 'o': o, 'p': p, 'q': q, 'r': r, 's': s, 't': t, 'u': u, 'v': v,
                                   'w': w, 'x': x,
                                   'y': y, 'z': z, ' ': sp, '.': dot}

            alphabet = 'abcdefghijklmnopqrstuvwxyz 0123456789?!,.-+'
            text_input = text_box.get('1.0', 'end')
            if text_input:
                try:
                    res = ''
                    for char in text_input.lower():
                        if alphabet.find(char) != -1:
                            if char in self.ascii_dict:
                                res += self.ascii_dict[char]

                    # UI for result
                    global result_box
                    paste_to_text.configure(state=ACTIVE)
                    result_frame = Frame(td_root)
                    result_scroll = ttk.Scrollbar(result_frame)
                    result_box = Text(result_frame, yscrollcommand=result_scroll.set)
                    result_box.insert('1.0', res)
                    result_box.configure(state=DISABLED)
                    result_frame.grid(row=3)
                    result_scroll.pack(side=RIGHT, fill=Y)
                    result_box.pack(fill=BOTH, expand=True)
                    result_scroll.config(command=result_box.yview)
                    # ------------
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

        # UI
        td_root = Toplevel()
        td_root.resizable(False, False)
        td_root.title('text decorators')
        b_frame = Frame(td_root)
        t_frame = Frame(td_root)
        text_box = Text(t_frame, height=10, width=40, borderwidth=3)
        enter_button = Button(b_frame, text='Enter', command=enter)
        copy_from_text = Button(b_frame, text='Copy from EgonTE', command=cft)
        paste_to_text = Button(b_frame, text='Paste to EgonTE', command=ptt, state=DISABLED)
        # text decorator styles
        bash_style = Button(b_frame, text='bash (#)', command=lambda: change_style(1))
        binary_style = Button(b_frame, text='binary (10)', command=lambda: change_style(2))
        asterisk_style = Button(b_frame, text='asterisk (*)', command=lambda: change_style(4))

        t_frame.grid(row=1)
        b_frame.grid(row=2)

        text_box.pack(expand=True, fill=BOTH)

        copy_from_text.grid(row=2, column=0)
        enter_button.grid(row=2, column=1)
        paste_to_text.grid(row=2, column=2)

        bash_style.grid(row=4, column=0)
        binary_style.grid(row=4, column=2)

        asterisk_style.grid(row=5, column=2)

        styles = [bash_style, binary_style, asterisk_style]
        change_style(1)

    def stopwatch(self):
        start_time = time.time()
        while True:
            time.sleep(0.5)
            output = timedelta(seconds=round(time.time() - start_time))
            if self.op_active:
                self.usage_time.configure(text=f' Usage time: {output}')

    def merge_files(self):
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

        data_1 = self.EgonTE.get('1.0', 'end')

        # Reading data from file1
        file_name = filedialog.askopenfilename(initialdir=os.getcwd(), title='Open file to merge',
                                               filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html')))

        # Reading data from file2
        if file_name:
            with open(file_name) as fp:
                data2 = fp.read()

            data = data_1 + '\n' + data2

            ask_op_root = Toplevel()
            ask_op_root.title('EgonTE - merge files')
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
            messagebox.showerror('Error', 'you are not using a file')

    def insp_quote(self, op_msg=False):
        # consider making the function a thread
        try:
            # making the get request
            response = requests.get('https://zenquotes.io/api/random')
            if response.status_code == 200:
                # extracting the core data
                json_data = loads(response.text)
                quote = json_data[0]['q'] + ' -' + json_data[0]['a']
            else:
                messagebox.showerror('Error', 'Error while getting quote')
        except:
            try:
                alt_response = requests.get('https://api-ninjas.com/api/quotes')
                json_data = alt_response.json()
                data = json_data['data']
                quote = data[0]['quoteText']
            except:
                if op_msg == False:
                    messagebox.showerror('Error', 'Something went wrong!')

        if quote:
            if op_msg:
                return quote
            else:
                self.EgonTE.insert('1.0', '\n')
                self.EgonTE.insert('1.0', quote)

    def save_images(self, widget_name, root_name):
        image_name = filedialog.asksaveasfilename() + '.png'
        x = root_name.winfo_rootx() + widget_name.winfo_x()
        y = root_name.winfo_rooty() + widget_name.winfo_y()
        x1 = x + widget_name.winfo_width()
        y1 = y + widget_name.winfo_height()
        image = ImageGrab.grab().crop((x, y, x1, y1))
        image.save(image_name)
        return image_name

    def get_weather(self):
        def copy_weather():
            all_content = f'{loc_text}\n{temp_text}\n{time_text}\n{desc}'
            copy(all_content)

        city_name = simpledialog.askstring('EgonTE - Weather',
                                           'What is the name of the city\n you want to get the weather for')
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
            weather_root.title('EgonTE - Weather')
            weather_root.geometry('265x130')

            loc_text = ('Location: ' + location)
            temp_text = ('Temperature: ' + temperature + '&deg;C')
            time_text = ('Time: ' + time)
            desc = ('Weather Description: ' + info)

            loc = Label(weather_root, text=loc_text)
            temp = Label(weather_root, text=temp_text)
            tim = Label(weather_root, text=time_text)
            des = Label(weather_root, text=desc)
            copy_button = Button(weather_root, text='Copy', command=copy_weather, pady=2)

            loc.pack(fill="none", expand=True)
            temp.pack(fill="none", expand=True)
            tim.pack(fill="none", expand=True)
            des.pack(fill="none", expand=True)
            copy_button.pack(fill="none", expand=True)

    def send_email(self):
        file_type = 'external'
        custom_box = ''

        def file_mode(mode):
            global file_type, custom_box
            if mode == 't':
                file_type = 'this'
                loc_button.configure(bg='SystemButtonFace')
                custom_button.configure(bg='SystemButtonFace')
                th_button.configure(bg='light grey')
                if custom_box:
                    custom_box.destroy()
            elif mode == 'c':
                custom_button.configure(bg='light grey')
                loc_button.configure(bg='SystemButtonFace')
                th_button.configure(bg='SystemButtonFace')
                file_type = 'none'
                custom_box = Text(email_root)
                custom_box.grid(row=9, column=1)
            else:
                file_type = 'local'
                loc_button.configure(bg='light grey')
                custom_button.configure(bg='SystemButtonFace')
                th_button.configure(bg='SystemButtonFace')
                if custom_box:
                    custom_box.destroy()

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
                msg['Subject'] = f'The contents of {file_name}'
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
        email_root.title('EgonTE - send emails')
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

    def chatGPT(self):
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

                    # singing function
                    def enter():
                        options = Options()
                        options.log = True
                        options.track = True
                        options.proxies = 'http://localhost:8080'
                        self.alt_chat = Chat(email=email_entry.get(), password=password_entry.get(), options=options)
                        login_root.destroy()
                        active_ui()

                    # custom login interface exclusively for this library
                    login_root = Toplevel()
                    login_root.resizable(False, False)
                    login_root.title('EgonTE - sign to ChatGPT')
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
            global txt, gpt_image
            gpt_root = Toplevel()
            gpt_root.title('EgonTE - ChatGPT')
            # gpt_root.iconbitmap(gpt_image)
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
        PROMPT = 'An eco-friendly computer from the 90s in the style of vaporwave'
        size_var = StringVar()
        size_var.set('256x256')

        def imagine():
            global PROMPT
            if prompt_entry.get():
                PROMPT = prompt_entry.get()
            try:
                response = openai.Image.create(prompt=PROMPT, n=1, size=size_var.get())
                result = (response['data'][0]['url'])
                label = Label(dallE_root, text=result)
            except openai.error.RateLimitError:
                messagebox.showerror('OpenAI',
                                     'You exceeded your current quota, please check your plan and billing details')
            label.grid(row=5)

        def ui():
            global prompt_entry, dallE_root
            dallE_root = Toplevel()
            dallE_root.title('EgonTE - DallE')
            prompt_title = Label(dallE_root, text='Enter the prompt here', font='arial 10 underline')
            prompt_entry = Entry(dallE_root, width=30)
            size_title = Label(dallE_root, text='Size of output', font='arial 10 underline')
            size_256 = Radiobutton(dallE_root, variable=size_var, value='256x256', text='256x256')
            size_512 = Radiobutton(dallE_root, variable=size_var, value='512x512', text='512x512')
            size_1024 = Radiobutton(dallE_root, variable=size_var, value='1024x1024', text='1024x1024')
            size_1536 = Radiobutton(dallE_root, variable=size_var, value='1536x1536', text='1536x1536')
            size_2048 = Radiobutton(dallE_root, variable=size_var, value='2048x2048', text='2048x2048')

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

        if not self.key:
            self.key_page(ui)
        else:
            ui()

    def key_page(self, after_func=None):
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
        login_root.title('EgonTE - connect to OpenAI')

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

        login_root.mainloop()

    def full_screen(self, event=None):
        self.fs_value = not (self.fs_value)
        self.attributes('-fullscreen', self.fs_value)

    def topmost(self):
        self.tm_value = not (self.tm_value)
        self.attributes('-topmost', self.tm_value)

    def transcript(self):
        def youtube():
            tr_root = Toplevel()
            tr_root.title('EgonTE - youtube transcript')
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
                file_trans_root.title('EgonTE - file transcript')
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

    if RA:
        right_align_language_support()


def new_window(app):
    appX = app()
    appX.mainloop()


def loading_screen():
    def active():
        loading_bar.start(25)
        for loading_iter in range(loading_count):
            loading_bar['value'] += loading_value
            lr.update_idletasks()
            time.sleep(1)
            # loading_value += 25

            # if loading_bar['value'] >= length:
        else:
            loading_bar.stop()
            time.sleep(0.5)
            # loading = False
            lr.destroy()
            application = Window()
            application.mainloop()

    # loading = True
    loading_value = 25
    length = 400
    loading_count = length // loading_value
    lr = Tk()
    loading_bar = ttk.Progressbar(lr, orient=HORIZONTAL, length=length, mode='determinate')
    text = Label(lr, text='Loading:', font='arial 12 bold')

    text.pack()
    loading_bar.pack(padx=10, pady=10)

    active()

    lr.mainloop()


if __name__ == '__main__':
    # Thread(target=loading_screen(), daemon=True).start()
    app = Window()
    app.mainloop()
    # m = MainMenu()
    # m.mainloop()

# contact - discord - Arielp2#4011 / Jinx Ariel#3368
