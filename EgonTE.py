from tkinter import filedialog, colorchooser, font, ttk, messagebox
from tkinter import *
from tkinter.tix import *
from win32print import GetDefaultPrinter
from win32api import ShellExecute, GetShortPathName
import pyttsx3
from threading import Thread
import pyaudio  # imported to make speech_recognition work
from random import choice, randint, random, shuffle
from speech_recognition import Recognizer, Microphone
from sys import exit as exit_
from datetime import datetime
import webbrowser
import names
from googletrans import Translator  # req version 3.1.0a0
from pyshorteners import Shortener
from os import getcwd
import string
import pandas
from socket import gethostname
from  PyDictionary import PyDictionary
from pyperclip import copy
import emoji
import wikipedia

try:
    import polyglot

    RA = True
except ImportError:
    RA = False

global translate_root, sort_root


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
        ver = '1.10.0'
        self.title(f'Egon Text editor - {ver}')
        #self.resizable(False, True)
        # self.minsize(1250, 830)
        # self.maxsize(1250, 930)
        self.load_images()
        self.protocol("WM_DELETE_WINDOW", self.exit_app)
        self.file_name = ''
        self.text_changed = False

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
        font_Size_c = 4
        self.font_size.current(font_Size_c)  # 16 is at index 5
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
        file_menu.add_command(label='New window', command=lambda: new_window(Window), state=DISABLED)
        file_menu.add_separator()
        file_menu.add_command(label='Print file', accelerator='(ctrl+p)', command=self.print_file)
        file_menu.add_separator()
        file_menu.add_command(label='Copy path', accelerator='(alt+d)', command=self.copy_file_path)
        file_menu.add_separator()
        file_menu.add_command(label='Import file', command=self.special_files_import)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', accelerator='(alt+f4)', command=self.exit_app)
        # edit menu
        edit_menu = Menu(menu, tearoff=True)
        menu.add_cascade(label='Edit', menu=edit_menu)
        edit_menu.add_command(label='Cut', accelerator='(ctrl+x)', command=lambda: self.cut(x=True))
        edit_menu.add_command(label='Copy', accelerator='(ctrl+c)', command=lambda: self.copy())
        edit_menu.add_command(label='Paste', accelerator='(ctrl+v)', command=lambda: self.paste())
        edit_menu.add_separator()
        edit_menu.add_command(label='Undo', accelerator='(ctrl+z)', command=self.EgonTE.edit_undo)
        edit_menu.add_command(label='Redo', accelerator='(ctrl+y)', command=self.EgonTE.edit_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label='Select All', accelerator='(ctrl+a)', command=lambda: self.select_all('nothing'))
        edit_menu.add_command(label='Clear all', accelerator='(ctrl+del)', command=self.clear)
        edit_menu.add_separator()
        edit_menu.add_command(label="Find Text", accelerator='(ctrl+f)', command=self.find_text)
        edit_menu.add_command(label='Replace', accelerator='(ctrl+h)', command=self.replace)
        edit_menu.add_command(label='Go to', accelerator='(ctrl+g)', command=self.goto)
        edit_menu.add_separator()
        edit_menu.add_command(label='Reverse characters', accelerator='(ctrl+shift+c)', command=self.reverse_characters)
        edit_menu.add_command(label='Reverse words', accelerator='(ctrl+shift+r)', command=self.reverse_words)
        edit_menu.add_command(label='Join words', accelerator='(ctrl+shift+j)', command=self.join_words)
        edit_menu.add_command(label='Upper/Lower', accelerator='(ctrl+shift+u)', command=self.lower_upper)
        edit_menu.add_command(label='Sort by characters', accelerator='', command=self.sort_by_characters)
        edit_menu.add_command(label='Sort by words', accelerator='', command=self.sort_by_words)
        # tools menu
        tool_menu = Menu(menu, tearoff=False)
        menu.add_cascade(label='Tools', menu=tool_menu)
        tool_menu.add_command(label='Calculation', command=self.ins_calc)
        tool_menu.add_command(label='Current datetime', accelerator='(F5)', command=self.dt)
        tool_menu.add_command(label='Random number', command=self.ins_random)
        tool_menu.add_command(label='Random name', command=self.ins_random_name)
        tool_menu.add_command(label='Translate', command=self.translate)
        tool_menu.add_command(label='Url shorter', command=self.url)
        tool_menu.add_command(label='Generate sequence', command=self.generate)
        tool_menu.add_command(label='Search online', command=self.search_www)
        tool_menu.add_command(label='Sort numbers', command=self.sort)
        tool_menu.add_command(label='Dictionary', command=lambda: Thread(target=self.dictionary('dict')).start())
        tool_menu.add_command(label='Wikipedia', command=lambda: Thread(target=self.dictionary('wiki')).start())
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

        self.cc = BooleanVar()
        self.cc.set(False)

        self.cs = BooleanVar()
        self.cs.set(True)

        self.ww = BooleanVar()
        self.ww.set(True)

        # made also here in order to make the usage of variables less wasteful
        self.status_ = True
        self.file_ = True

        # check marks
        options_menu.add_checkbutton(label="Night mode", onvalue=True, offvalue=False,
                                     compound=LEFT, command=self.night)
        options_menu.add_checkbutton(label="Status Bars", onvalue=True, offvalue=False,
                                     variable=self.show_statusbar, compound=LEFT, command=self.hide_statusbars)
        options_menu.add_checkbutton(label="Tool Bar", onvalue=True, offvalue=False,
                                     variable=self.show_toolbar, compound=LEFT, command=self.hide_toolbar)
        options_menu.add_checkbutton(label="Custom cursor", onvalue=True, offvalue=False,
                                     compound=LEFT, command=self.custom_cursor)
        options_menu.add_checkbutton(label="Custom style", onvalue=True, offvalue=False,
                                     compound=LEFT, command=self.custom_style, variable=self.cs)
        options_menu.add_checkbutton(label="Word warp", onvalue=True, offvalue=False,
                                     compound=LEFT, command=self.word_warp, variable=self.ww)
        options_menu.add_command(label='Detect emojis', command=lambda: self.emoji_detection(via_settings=True))
        options_menu.add_separator()
        options_menu.add_command(label='Advance options', command=self.advance_options)
        # help page
        menu.add_cascade(label='Help', command=self.e_help)
        # github page
        menu.add_cascade(label='GitHub', command=self.github)
        # add status bar
        status_frame = Frame(frame, height=20)
        status_frame.pack(fill=BOTH, anchor=S, side=BOTTOM)
        self.status_bar = Label(status_frame, text='Lines:1 Characters:0 Words:0', pady=5)
        self.status_bar.pack(fill=Y, side=LEFT)
        # add file bar
        self.file_bar = Label(status_frame, text='')
        self.file_bar.pack(fill=Y, side=RIGHT)
        # add shortcuts
        self.bind("<Control-o>", self.open_file)
        self.bind("<Control-O>", self.open_file)
        # self.bind('<Control-Key-x>', lambda event: self.cut(True))
        self.bind('<<Cut>>', lambda event: self.cut(True))
        # self.bind('<Control-Key-v>', lambda event: self.paste())
        #self.bind('<<Paste>>', self.paste)
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
        # self.bind('<space>', self.emoji_detection)
        # special events
        self.font_size.bind('<<ComboboxSelected>>', self.change_font_size)
        font_ui.bind("<<ComboboxSelected>>", self.change_font)
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

        align_left_button = Button(self.toolbar_frame, image=ALIGN_LEFT_IMAGE, relief=FLAT)
        align_left_button.grid(row=0, column=6, padx=5)

        # align center button
        align_center_button = Button(self.toolbar_frame, image=ALIGN_CENTER_IMAGE, relief=FLAT)
        align_center_button.grid(row=0, column=7, padx=5)

        # align right button
        align_right_button = Button(self.toolbar_frame, image=ALIGN_RIGHT_IMAGE, relief=FLAT)
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

        vKeyboard_button = Button(self.toolbar_frame, image=KEY_IMAGE, relief=FLAT,
                             command=lambda: Thread(target=self.virtual_keyboard()).start())

        vKeyboard_button.grid(row=0, column=11, padx=5)

        # buttons config
        align_left_button.configure(command=self.align_left)
        align_center_button.configure(command=self.align_center)
        align_right_button.configure(command=self.align_right)

        # opening sentence
        op_msgs = ['Hello world!', '^-^', 'What a beautiful day!', 'Welcome!', '', 'Believe in yourself!',
                   'If I did it you can do way more than that', 'Don\'t give up!',
                   'I\'m glad that you are using my Text editor (:', 'Feel free to send feedback', f'hi {gethostname()}']
        op_msg = choice(op_msgs)
        self.EgonTE.insert('1.0', op_msg)

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

        # ui lists
        self.toolbar_components = [bold_button, italics_button, color_button, underline_button, align_left_button,
                                   align_center_button, align_right_button, tts_button, talk_button, self.font_size]
        self.menus_components = [file_menu, edit_menu, tool_menu, color_menu, options_menu]
        self.other_components = [self, self.status_bar, self.file_bar, self.EgonTE, self.toolbar_frame]

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
        STT_IMAGE = PhotoImage(file="assets/speech-icon-19(1).png")
        KEY_IMAGE = PhotoImage(file='assets/key(1).png')

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
        self.EgonTE.delete("1.0", END)
        self.file_bar.config(text='New file')

        global open_status_name
        open_status_name = False

    # open file func
    def open_file(self, event=None):
        self.EgonTE.delete("1.0", END)
        text_file = filedialog.askopenfilename(initialdir=getcwd(), title='Open file',
                                               filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html'),
                                                          ('Python Files', '*.py')))
        if text_file:
            global open_status_name
            open_status_name = text_file
            self.file_name = text_file
            self.file_bar.config(text=f'Opened file: {GetShortPathName(self.file_name)}')
            self.file_name.replace('C:/EgonTE/', '')
            self.file_name.replace('C:/users', '')
            text_file = open(text_file, 'r')
            stuff = text_file.read()
            self.EgonTE.insert(END, stuff)
            text_file.close()
        else:
            messagebox.showerror('error', 'File not found / selected')

    # save as func
    def save_as(self, event=None):
        if event == None:
            text_file = filedialog.asksaveasfilename(defaultextension=".*", initialdir='C:/EgonTE', title='Save File',
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
        printer_name = GetDefaultPrinter()
        file2p = filedialog.askopenfilename(initialdir='C:/EgonTE/', title='Open file',
                                            filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html'),
                                                       ('Python Files', '*.py')))
        if file2p:
            if messagebox.askquestion('EgonTE', f'are you wish to print with {printer_name}?'):
                ShellExecute(0, 'print', file2p, None, '.', 0)

    # select all func
    def select_all(self, event=None):
        self.EgonTE.tag_add('sel', '1.0', 'end')

    # clear func
    def clear(self, event=None):
        self.EgonTE.delete('1.0', END)

    # hide file bar & status bar func
    def hide_statusbars(self):
        if not(self.show_statusbar.get()):
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

    # night on func
    def night(self):
        if self.night_mode:
            main_color = '#110022'
            second_color = '#373737'
            third_color = '#280137'
            _text_color = 'green'
            self.config(bg=main_color)
            self.status_bar.config(bg=main_color, fg=_text_color)
            self.file_bar.config(bg=main_color, fg=_text_color)
            self.EgonTE.config(bg=second_color, fg=_text_color)
            self.toolbar_frame.config(bg=main_color)
            # toolbar buttons
            for toolbar_button in self.toolbar_components:
                toolbar_button.config(background=third_color)
            # file menu colors
            for menu_ in self.menus_components:
                menu_.config(background=second_color, foreground=_text_color)
            self.night_mode = False
        else:
            main_color = 'SystemButtonFace'
            second_color = 'SystemButtonFace'
            _text_color = 'black'
            self.config(bg=main_color)
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
            self.night_mode = True

    def change_font(self, event):
        global chosen_font
        chosen_font = self.font_family.get()
        self.delete_tags()
        self.EgonTE.configure(font=(chosen_font, 16))

    def change_font_size(self, event=None):
        global chosen_size, font_Size_c
        chosen_size = self.size_var.get()
        font_Size_c = (chosen_size - 8) // 2
        # font_Size_c = font_size.get()
        # print(font_Size_c)
        self.font_size.current(font_Size_c)
        # EgonTE.configure(font=(chosen_font, chosen_dot_size))

        size = font.Font(self.EgonTE, self.EgonTE.cget('font'))
        size.configure(size=chosen_size)
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
        self.EgonTE.tag_config("left", justify=LEFT)
        try:
            self.EgonTE.delete('sel.first', 'sel.last')
            self.EgonTE.insert(INSERT, text_content, "left")
        except:
            messagebox.showerror('error', 'choose a line_var content')

    # Align Center func
    def align_center(self, event=None):
        if self.is_marked():
            text_content = self.EgonTE.get('sel.first', 'sel.last')
        else:
            self.EgonTE.tag_add('sel', 'insert linestart', 'insert lineend')
            text_content = self.EgonTE.get('insert linestart', 'insert lineend')
        self.EgonTE.tag_config("center", justify=CENTER)
        try:
            self.EgonTE.delete('sel.first', 'sel.last')
            self.EgonTE.insert(INSERT, text_content, "center")
        except:
            messagebox.showerror('error', 'choose a line_var with content')

    # Align Right func
    def align_right(self, event=None):
        if self.is_marked():
            text_content = self.EgonTE.get('sel.first', 'sel.last')
        else:
            self.EgonTE.tag_add('sel', 'insert linestart', 'insert lineend')
            text_content = self.EgonTE.get('insert linestart', 'insert lineend')
        self.EgonTE.tag_config("right", justify=RIGHT)
        try:
            self.EgonTE.delete('sel.first', 'sel.last')
            self.EgonTE.insert(INSERT, text_content, "right")
        except:
            messagebox.showerror('error', 'choose a line_var with content')

    # get & display character and word count with status bar
    def status(self, event=None):
        global lines
        if self.EgonTE.edit_modified():
            self.text_changed = True
            words = len(self.EgonTE.get(1.0, "end-1c").split())
            characters = len(self.EgonTE.get(1.0, "end-1c"))
            lines = int((self.EgonTE.index(END)).split('.')[0]) - 1
            self.status_bar.config(text=f'Lines:{lines} Characters:{characters} Words:{words}')
        self.EgonTE.edit_modified(False)

    # AI narrator will read the selected text from the text box
    def text_to_speech(self):
        global tts
        tts = pyttsx3.init()
        try:
            content = self.EgonTE.get('sel.first', 'sel.last')
        except:
            content = self.EgonTE.get('1.0', 'end')
        tts.say(content)
        tts.runAndWait()

    # AI narrator will read the given text for other functions
    def read_text(self, **kwargs):
        global engine
        engine = pyttsx3.init()
        if 'text' in kwargs:
            ttr = kwargs['text']
        else:
            ttr = self.EgonTE.get(1.0, 'end')
        engine.say(ttr)
        engine.runAndWait()
        engine.stop()

    # to make the narrator voice more convincing
    def text_formatter(self, phrase):
        interrogatives = ('how', 'why', 'what', 'when', 'who', 'where', 'is', 'do you', "whom", "whose")
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
                else:
                    self.quit()
                    exit_()
                    quit()
                    exit()
            else:
                self.quit()
                exit_()
                quit()
                exit()

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
                search_label = messagebox.showinfo("EgonTE:", f"{entry_data} has {str(occurs)} occurrences")

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
                    title = Label(nav_root, text=f'navigate trough the {str(occurs)} occurrences of "{entry_data}"',
                                  font='arial 12 underline')
                    # buttons ↑
                    button_up = Button(nav_root, text='Reset', command=lambda: up(starting_index, ending_index), width=5
                                       , state=DISABLED)
                    button_down = Button(nav_root, text='↓', command=lambda: down(starting_index, ending_index),
                                         width=5)
                    # placing
                    title.grid(row=0, padx=5)
                    button_up.grid(row=1)
                    button_down.grid(row=2)


            else:
                search_label = messagebox.showinfo("EgonTE:", "No match found")

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
            clac_root.geometry('150x155')
            show_op.config(text='hide operations', command=hide_oper)
            add_sub = Label(clac_root, text='+ addition, - subtraction')
            mul_div = Label(clac_root, text='* multiply, / deviation')
            pow_ = Label(clac_root, text='** power, % modulus')
            add_sub.grid(row=4)
            mul_div.grid(row=5)
            pow_.grid(row=6)

        def hide_oper():
            clac_root.geometry('150x90')
            add_sub.grid_forget()
            mul_div.grid_forget()
            pow_.grid_forget()
            show_op.config(text='show operations', command=show_oper)

        clac_root = Toplevel(relief=FLAT)
        clac_root.resizable(False, False)
        clac_root.attributes('-alpha', '0.95')
        clac_root.geometry('150x90')
        introduction_text = Label(clac_root, text='Enter equation below:', font='arial 10 underline')
        enter = Button(clac_root, text='Enter', command=enter_button, relief=FLAT)
        clac_entry = Entry(clac_root, relief=RIDGE, justify='center')
        show_op = Button(clac_root, text='Show operators', relief=FLAT, command=show_oper)
        introduction_text.grid(row=0, padx=10)
        clac_entry.grid(row=1)
        enter.grid(row=2)
        show_op.grid(row=3)

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
        file_name_ = self.save_as(event='get name')
        self.clipboard_clear()
        self.clipboard_append(file_name_)

    # change between the default and custom cursor
    def custom_cursor(self):
        if self.cc:
            self.predefined_cursor = 'tcross'
            self.EgonTE.config(cursor=self.predefined_cursor)
            try:
                sort_input.config(cursor=self.predefined_cursor)
                translate_box.config(cursor=self.predefined_cursor)
            except BaseException:
                pass
            self.cc = False
        else:
            self.predefined_cursor = 'xterm'
            self.EgonTE.config(cursor=self.predefined_cursor)
            try:
                sort_input.config(cursor=self.predefined_cursor)
                translate_box.config(cursor=self.predefined_cursor)
            except BaseException:
                pass
            self.cc = True

    # change between the default and custom style
    def custom_style(self):
        if not self.cs:
            self.predefined_style = 'clam'
            self.style.theme_use(self.predefined_style)
            self.cs = True
        else:
            self.predefined_style = 'vista'
            self.style.theme_use(self.predefined_style)
            self.cs = False

    def word_warp(self):
        if not self.ww:
            self.EgonTE.config(wrap=WORD)
            self.geometry(f'{self.width}x{self.height - 10}')
            self.horizontal_scroll.pack_forget()
            self.ww = True
        else:
            self.geometry(f'{self.width}x{self.height + 10}')
            self.horizontal_scroll.pack(side=BOTTOM, fill=X)
            self.EgonTE.config(wrap=NONE)

            self.ww = False

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
                if gender_value == 'Male' and type_value == "Full Name":
                    random_name = names.get_full_name(gender="male")
                    rand_name.config(text=random_name)
                elif gender_value == 'Male' and type_value == "First Name":
                    random_name = names.get_first_name()
                    rand_name.config(text=random_name)
                elif gender_value == 'Male' and type_value == "Last Name":
                    random_name = names.get_last_name()
                    rand_name.config(text=random_name)

                elif gender_value == 'Female' and type_value == "Full Name":
                    random_name = names.get_full_name(gender="female")
                    rand_name.config(text=random_name)
                elif gender_value == 'Female' and type_value == "First Name":
                    random_name = names.get_first_name()
                    rand_name.config(text=random_name)
                elif gender_value == 'Female' and type_value == "Last Name":
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
        copy_b = Button(name_root, text='Copy',command=lambda:copy(str(random_name)), width=10,  relief=RIDGE)
        text.grid(row=0, padx=10)
        rand_name.grid(row=1)
        enter.grid(row=2)
        re_roll.grid(row=3)
        adv_options.grid(row=4)
        copy_b.grid(row=5)

    def translate(self):
        global translate_root, translate_box

        def button():
            to_translate = translate_box.get("1.0", "end-1c")
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
        button_ = Button(translate_root, text="Translate", relief=FLAT, borderwidth=3, font=('arial', 10, 'bold'),
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
            self.EgonTE.delete("end-2l", "end-1l")
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
        characters = list(string.ascii_letters + string.digits)
        intro_text = Label(generate_root, text='Generate a random sequence', font='arial 10 underline')
        length_entry = Entry(generate_root, width=10)
        sym_text = Label(generate_root, text='induce symbols?')
        sym_button = Button(generate_root, text='✖')
        enter_button = Button(generate_root, text='Enter', width=8, height=2)
        length_text = Label(generate_root, text='length', padx=10)
        intro_text.grid(row=0, column=1)
        length_text.grid(row=1, column=0, padx=10, columnspan=1)
        length_entry.grid(row=2, column=0)
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
                sym_char = "!", "@", "#", "$", "%", "^", "&", "*", "(", ")"
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
        global font_Size_c
        font_Size_c += 1
        try:
            self.font_size.current(font_Size_c)
            self.change_font_size()
        except Exception:
            messagebox.showerror('error', 'font size at maximum')

    # font size down by 1 iterations
    def size_down_shortcut(self, event=None):
        global font_Size_c
        font_Size_c -= 1
        try:
            self.font_size.current(font_Size_c)
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
        global font_Size_c
        self.EgonTE.tag_delete('bold', 'underline', 'italics', 'size', 'colored_txt')
        font_Size_c = 4
        self.font_size.current(font_Size_c)

    def special_files_import(self, file_type=None):
        # to make the functions write the whole file even if its huge
        pandas.options.display.max_rows = 9999
        content = ''

        special_file = filedialog.askopenfilename(title='open file',
                                                      filetypes=(('excel', '*.xlsx'),('csv', '*.csv'),
                                                                 ('json', '*.json'),('xml', '*.xml'), ('all', '*.*')))
        if special_file.endswith('xml'):
            content = pandas.read_xml(special_file).to_string()
        elif special_file.endswith('csv'):
            content = pandas.read_csv(special_file).to_string()
        elif special_file.endswith('json'):
            content = pandas.read_json(special_file).to_string()
        elif special_file.endswith('xlsx'):
            content = pandas.read_excel(special_file).to_string()
        # elif special_file.endswith(''):
        #     content = pandas.read_sas(special_file).to_string()

        self.EgonTE.insert(self.get_pos(), content)

    # a window that have explanations confusing features
    def e_help(self):
        # window
        help_root = Toplevel()
        help_root.resizable(False, False)
        help_root.config(bg='white')

        # putting the lines in order
        def place_lines():
            lines = []
            text.delete('1.0', END)
            with open('help.txt') as ht:
                for line in ht:
                    text.insert('end', line)

        # lines = str(lines)
        # lines.remove('{')
        # lines.remove('}')
        #
        help_root_frame = Frame(help_root)
        help_root_frame.pack(pady=5)
        title_frame = Frame(help_root_frame)
        title_frame.pack()
        help_text_scroll = ttk.Scrollbar(help_root_frame)
        # labels
        title = Label(title_frame, text='Help', font='arial 16 bold underline', justify='left')
        text = Text(help_root_frame, font='arial 10', borderwidth=3, bg='light grey', state='normal',
                    yscrollcommand=help_text_scroll.set, relief=RIDGE, wrap=WORD)
        text.focus_set()
        # add lines
        place_lines()
        text.config(state='disabled')
        # placing
        help_root_frame.pack(pady=3)
        title.pack(fill=X, anchor=W)
        help_text_scroll.pack(side=RIGHT, fill=Y)
        text.pack(fill=BOTH, expand=True)
        help_text_scroll.config(command=text.yview)

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
            chrome_path = "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
            webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))

            firefox_path = "C:/Program Files/Mozilla Firefox/firefox.exe"
            webbrowser.register('firefox', None, webbrowser.BackgroundBrowser(firefox_path))
            
            opera_path = f"C:/Users/{gethostname()}/AppData/Local/Programs/Opera/opera.exe"
            webbrowser.register('opera', None, webbrowser.BackgroundBrowser(opera_path))

            edge_path = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
            webbrowser.register('edge', None, webbrowser.BackgroundBrowser(edge_path))

        adv_button = Button(ser_root, text='Advance options', command=adv, relief=FLAT)

        tab_title = Label(ser_root, text='Tabs options', font='arial 10 underline')
        ser_var = StringVar()
        tab_modes = ttk.Combobox(ser_root, width=10, textvariable=ser_var, state="readonly")
        tab_modes['values'] = ['current tab', 'new tab']
        tab_modes.current(0)

        browser_title = Label(ser_root, text='Browser options', font='arial 10 underline')
        br_var = StringVar()
        br_modes = ttk.Combobox(ser_root, width=10, textvariable=br_var, state="readonly")
        br_modes['values'] = ['default', 'firefox', 'chrome', 'opera', 'edge']
        br_modes.current(0)

        adv_button.grid(row=4, column=1)

        if self.is_marked():
            entry_box.insert('end', self.EgonTE.get('sel.first', 'sel.last'))

    def advance_options(self):
        # self.file_ = False
        # self.status_ = False

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
                else:
                    self.status_bar.pack(side=LEFT)
                    self.geometry(f'{self.width}x{self.height - 20}')
                    self.status_ = True
            elif bar == 'filebar':
                if self.file_:
                    self.file_bar.pack_forget()
                    self.geometry(f'{self.width}x{self.height - 30}')
                    self.file_ = False
                else:
                    self.file_bar.pack(side=RIGHT)
                    self.geometry(f'{self.width}x{self.height - 20}')
                    self.file_ = True
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

        def change_relief(relief_):
            self.EgonTE.config(relief=relief_)
            try:
                sort_input.config(relief=relief_)
                translate_box.config(relief=relief_)
            except BaseException:
                pass
            change_button_color('relief', relief_)
            self.predefined_relief = relief_

        def change_transparency():
            tranc = int(transparency_config.get()) / 100
            self.attributes('-alpha', tranc)

        # window
        opt_root = Toplevel()
        opt_root.resizable(False, False)

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
        # buttons list
        adv_cursor_bs = [tcross_button, arrow_button, crosshair_button, pencil_button, fleur_button, xterm_button]
        adv_style_bs = [style_clam, style_vista, style_classic]
        adv_reliefs_bs = [relief_groove, relief_flat, relief_ridge]
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
            self.EgonTE.mark_set("insert", ending_index)

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
        sort_text = Label(sort_root, text='Enter the numbers you wish to sort:', font='arial 10 underline')
        sort_input = Text(sort_frame, width=20, height=15, yscrollcommand=sort_scroll.set, wrap=WORD,
                          cursor=self.predefined_cursor, relief=self.predefined_relief)

        sort_button = Button(sort_root, text='Sort', command=sort_)
        mode_button = Button(sort_root, text='Mode: ascending', command=mode)
        sort_insert = Button(sort_root, text='Insert', command=enter)
        sort_text.pack(fill=X, anchor=W)
        sort_frame.pack(pady=3)
        sort_scroll.pack(side=RIGHT, fill=Y)
        sort_input.pack(fill=BOTH, expand=True)
        sort_scroll.config(command=sort_input.yview)
        sort_button.pack()
        mode_button.pack()
        sort_insert.pack()
        # sort_text.grid(row=0, sticky=NSEW, column=0, padx=3)
        # sort_input.grid(row=1, column=0)
        # sort_frame.grid(row=1)
        # sort_scroll.grid(row=1, column=1)
        # sort_button.grid(row=2, column=0)
        # mode_button.grid(row=3, column=0)
        # sort_insert.grid(row=4, column=0, pady=5)

    def dictionary(self, mode):
        def search():
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
            else:
                wiki_ = wikipedia.summary(par_entry.get())
                meaning_box.insert(self.get_pos(), wiki_)
            paste_b.configure(state=ACTIVE)
        def paste():
            if mode == 'dict':
                for key, value in self.def_.items():
                    self.EgonTE.insert(self.get_pos(), key + '\n\n')
                    for values in value:
                        self.EgonTE.insert(self.get_pos(), f'-{values}\n\n')
            else:
                wiki_ = wikipedia.summary(par_entry.get())
                self.EgonTE.insert(self.get_pos(), wiki_)

        par_root = Toplevel()
        par_root.resizable(False, False)
        par_root.attributes('-alpha', '0.95')
        par_entry = Entry(par_root)
        par_search = Button(par_root, text='Search meaning', command=search)
        meaning_box = Text(par_root,  height=15, width=50, wrap=WORD)
        meaning_box.configure(state=DISABLED)
        paste_b = Button(par_root, text='Paste to ETE', command=paste)
        paste_b.configure(state=DISABLED)

        par_entry.grid(row=1)
        par_search.grid(row=2)
        meaning_box.grid(row=3)
        paste_b.grid(row=4)

    def virtual_keyboard(self):
        key = Toplevel()  # key window name
        key.attributes('-alpha', '0.90')
        # key.iconbitmap('add icon link And Directory name')    # icon add

        # function coding start

        exp = " "  # global variable

        # showing all data in display

        def press(num):
            global exp
            self.EgonTE.insert(self.get_pos(), num)

        def tab():
            exp = "    "
            self.EgonTE.insert(self.get_pos(), exp)

        # Size window size
        key.geometry('630x200')  # normal size
        key.resizable(False, False)
        # end window size

        key.configure(bg='black')  # add background color
        q = ttk.Button(key, text='Q', width=6, command=lambda: press('Q'))
        q.grid(row=1, column=0, ipady=10)

        w = ttk.Button(key, text='W', width=6, command=lambda: press('W'))
        w.grid(row=1, column=1, ipady=10)

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
            self.EgonTE.insert(self.get_pos(), " ")


    if RA:
        right_align_language_support()

def new_window(app):
    appX = app()
    appX.mainloop()

if __name__ == '__main__':
    app = Window()
    app.mainloop()

# contact - reedit = arielo_o, discord - Arielp2#4011
