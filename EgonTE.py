from tkinter import filedialog, colorchooser, font, ttk, messagebox, simpledialog
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
from webbrowser import open as open_
import names
from googletrans import Translator  # req version 3.1.0a0
from pyshorteners import Shortener
from os import getcwd
import string
import pandas, numpy

try:
    import polyglot

    RA = True
except ImportError:
    RA = False


# window creation
def window(moa):
    global root, text_changed, predefined_cursor, predefined_style, bars_active, TOOL_TIP, width, height, EgonTE, \
        file_bar, status_bar, text_scroll, toolbar_frame, toolbar_components, menus_components, font_family, size_var, \
        font_style, font_size, style, frame, predefined_relief, night_mode, other_components, font_Size_c, \
        show_statusbar, ww, horizontal_scroll, show_toolbar
    global BOLD_IMAGE, UNDERLINE_IMAGE, ITALICS_IMAGE, COLORS_IMAGE, ALIGN_LEFT_IMAGE, ALIGN_CENTER_IMAGE, \
        ALIGN_RIGHT_IMAGE, TTS_IMAGE, STT_IMAGE
    root = Tk()
    width = 1250
    height = 830
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    placement_x = round((screen_width / 2) - (width / 2))
    placement_y = round((screen_height / 2) - (height / 2))
    root.geometry(f'{width}x{height}+{placement_x}+{placement_y}')
    ver = '1.0.9'
    root.title(f'Egon Text editor - {ver}')
    root.resizable(False, True)
    root.maxsize(1250, 930)
    load_images()

    if moa == 'main':
        # add and use logo
        LOGO = PhotoImage(file='ETE_icon.png')
        root.iconphoto(False, LOGO)

    # basic settings for the code
    global open_status_name
    open_status_name = False
    global selected
    global cc
    text_changed = False
    global random_name, types, gender
    global file_name
    global engine, tts
    selected = False
    predefined_cursor, predefined_style = '', ''
    bars_active = True

    # create toll tip, for the toolbar buttons (with shortcuts)
    TOOL_TIP = Balloon(root)

    # pre-defined options
    predefined_cursor = 'xterm'
    predefined_style = 'clam'
    predefined_relief = 'ridge'
    # add custom style
    style = ttk.Style()
    style.theme_use(predefined_style)
    frame = Frame(root)
    frame.pack(pady=5)
    # create toolbar frame
    toolbar_frame = Frame(frame)
    toolbar_frame.pack(fill=X, anchor=W)

    # font
    font_tuple = font.families()
    font_family = StringVar()
    font_ui = ttk.Combobox(toolbar_frame, width=30, textvariable=font_family, state="readonly")
    font_ui["values"] = font_tuple
    font_ui.current(font_tuple.index("Arial"))
    font_ui.grid(row=0, column=4, padx=5)

    # Size Box
    size_var = IntVar()
    size_var.set(16)
    font_size = ttk.Combobox(toolbar_frame, width=5, textvariable=size_var, state="readonly")
    font_size["values"] = tuple(range(8, 80, 2))
    font_Size_c = 4
    font_size.current(font_Size_c)  # 16 is at index 5
    font_size.grid(row=0, column=5, padx=5)
    # create vertical scrollbar
    text_scroll = ttk.Scrollbar(frame)
    text_scroll.pack(side=RIGHT, fill=Y)
    # horizontal scrollbar
    horizontal_scroll = ttk.Scrollbar(frame, orient='horizontal')
    # create text box
    EgonTE = Text(frame, width=100, height=30, font=('arial', 16), selectbackground='blue',
                  selectforeground='white',
                  undo=True,
                  yscrollcommand=text_scroll.set, wrap=WORD, relief=predefined_relief,
                  cursor=predefined_cursor)
    EgonTE.focus_set()
    EgonTE.pack(fill=BOTH, expand=True)
    # config scrollbars
    text_scroll.config(command=EgonTE.yview)
    EgonTE.config(xscrollcommand=horizontal_scroll.set)
    horizontal_scroll.config(command=EgonTE.xview)
    # create menu
    menu = Menu(frame)
    root.config(menu=menu)
    # file menu
    file_menu = Menu(menu, tearoff=False)
    menu.add_cascade(label='File', menu=file_menu)
    file_menu.add_command(label='New', accelerator='(ctrl+n)', command=new_file)
    file_menu.add_command(label='Open', accelerator='(ctrl+o)', command=open_file)
    file_menu.add_command(label='Save', command=save, accelerator='(ctrl+s)')
    file_menu.add_command(label='Save As', command=save_as)
    file_menu.add_command(label='New window', command=lambda: window('alt'), state=DISABLED)
    file_menu.add_separator()
    file_menu.add_command(label='Print file', accelerator='(ctrl+p)', command=print_file)
    file_menu.add_separator()
    file_menu.add_command(label='Copy path', accelerator='(alt+d)', command=copy_file_path)
    file_menu.add_separator()
    file_menu.add_command(label='Import EXCEL file', accelerator='', command=lambda: special_files_import('excel'))
    file_menu.add_command(label='Import CSV file', accelerator='', command=lambda: special_files_import('csv'))
    file_menu.add_command(label='Import JSON file', accelerator='', command=lambda: special_files_import('json'))
    file_menu.add_command(label='Import XML file', accelerator='', command=lambda: special_files_import('xml'))
    file_menu.add_separator()
    file_menu.add_command(label='Exit', accelerator='(alt+f4)', command=exit_app)
    # edit menu
    edit_menu = Menu(menu, tearoff=True)
    menu.add_cascade(label='Edit', menu=edit_menu)
    edit_menu.add_command(label='Cut', accelerator='(ctrl+x)', command=lambda: cut(True))
    edit_menu.add_command(label='Copy', accelerator='(ctrl+c)', command=lambda: copy(True))
    edit_menu.add_command(label='Paste', accelerator='(ctrl+v)', command=lambda: paste(True))
    edit_menu.add_separator()
    edit_menu.add_command(label='Undo', accelerator='(ctrl+z)', command=EgonTE.edit_undo)
    edit_menu.add_command(label='Redo', accelerator='(ctrl+y)', command=EgonTE.edit_redo)
    edit_menu.add_separator()
    edit_menu.add_command(label='Select All', accelerator='(ctrl+a)', command=lambda: select_all('nothing'))
    edit_menu.add_command(label='Clear all', accelerator='(ctrl+del)', command=clear)
    edit_menu.add_separator()
    edit_menu.add_command(label="Find Text", accelerator='(ctrl+f)', command=find_text)
    edit_menu.add_command(label='Replace', accelerator='(ctrl+h)', command=replace)
    edit_menu.add_command(label='Go to', accelerator='(ctrl+g)', command=goto)
    edit_menu.add_separator()
    edit_menu.add_command(label='Reverse characters', accelerator='(ctrl+shift+c)', command=reverse_characters)
    edit_menu.add_command(label='Reverse words', accelerator='(ctrl+shift+r)', command=reverse_words)
    edit_menu.add_command(label='Join words', accelerator='(ctrl+shift+j)', command=join_words)
    edit_menu.add_command(label='Upper/Lower', accelerator='(ctrl+shift+u)', command=lower_upper)
    # tools menu
    tool_menu = Menu(menu, tearoff=False)
    menu.add_cascade(label='Tools', menu=tool_menu)
    tool_menu.add_command(label='Calculation', command=ins_calc)
    tool_menu.add_command(label='Current datetime', accelerator='(F5)', command=dt)
    tool_menu.add_command(label='Random number', command=ins_random)
    tool_menu.add_command(label='Random name', command=ins_random_name)
    tool_menu.add_command(label='Translate', command=translate)
    tool_menu.add_command(label='Url shorter', command=url)
    tool_menu.add_command(label='Generate sequence', command=generate)
    tool_menu.add_command(label='Search online', command=search_www)
    tool_menu.add_command(label='Sort numbers', command=sort)
    # color menu
    color_menu = Menu(menu, tearoff=False)
    menu.add_cascade(label='Colors+', menu=color_menu)
    color_menu.add_command(label='Whole text', command=all_txt_color)
    color_menu.add_command(label='Background', command=bg_color)
    color_menu.add_command(label='Highlight', command=hl_color)
    color_menu.add_separator()
    color_menu.add_command(label='Buttons color', command=lambda: custom_ui_colors('buttons'))
    color_menu.add_command(label='Menus colors', command=lambda: custom_ui_colors('menus'))
    color_menu.add_command(label='App colors', command=lambda: custom_ui_colors('app'))
    # options menu
    options_menu = Menu(menu, tearoff=False)
    menu.add_cascade(label='Options', menu=options_menu)
    # boolean tk vars
    show_statusbar = BooleanVar()
    show_statusbar.set(True)

    show_toolbar = BooleanVar()
    show_toolbar.set(True)

    night_mode = BooleanVar()

    cc = BooleanVar()
    cc.set(False)

    cs = BooleanVar()
    cs.set(True)

    ww = BooleanVar()
    ww.set(True)

    # check marks
    options_menu.add_checkbutton(label="Night mode", onvalue=True, offvalue=False,
                                 compound=LEFT, command=night)
    options_menu.add_checkbutton(label="Status Bars", onvalue=True, offvalue=False,
                                 variable=show_statusbar, compound=LEFT, command=hide_statusbars)
    options_menu.add_checkbutton(label="Tool Bar", onvalue=True, offvalue=False,
                                 variable=show_toolbar, compound=LEFT, command=hide_toolbar)
    options_menu.add_checkbutton(label="Custom cursor", onvalue=True, offvalue=False,
                                 compound=LEFT, command=custom_cursor)
    options_menu.add_checkbutton(label="Custom style", onvalue=True, offvalue=False,
                                 compound=LEFT, command=custom_style, variable=cs)
    options_menu.add_checkbutton(label="Word warp", onvalue=True, offvalue=False,
                                 compound=LEFT, command=word_warp, variable=ww)
    options_menu.add_separator()
    options_menu.add_command(label='Advance options', command=advance_options)
    # help page
    menu.add_cascade(label='Help', command=e_help)
    # github page
    menu.add_cascade(label='GitHub', command=github)
    # add status bar
    status_bar = Label(root, text='Lines:1 Characters:0 Words:0')
    status_bar.pack(fill=X, side=LEFT, ipady=5)
    # add file bar
    file_bar = Label(root, text='')
    file_bar.pack(fill=X, side=RIGHT, ipady=5)
    # add shortcuts
    root.bind("<Control-o>", open_file)
    root.bind("<Control-O>", open_file)
    root.bind('<Control-Key-x>', lambda event: cut(True))
    root.bind('<Control-Key-X>', lambda event: cut(True))
    root.bind('<Control-Key-v>', lambda event: paste(True))
    root.bind('<Control-Key-V>', lambda event: paste(True))
    root.bind('<Control-Key-c>', lambda event: copy(True))
    root.bind('<Control-Key-C>', lambda event: copy(True))
    root.bind('<Control-Key-s>', save)
    root.bind('<Control-Key-S>', save)
    root.bind('<Control-Key-a>', select_all)
    root.bind('<Control-Key-A>', select_all)
    root.bind('<Control-Key-b>', bold)
    root.bind('<Control-Key-B>', bold)
    root.bind('<Control-Key-i>', italics)
    root.bind('<Control-Key-I>', italics)
    root.bind('<Control-Key-u>', underline)
    root.bind('<Control-Key-U>', underline)
    root.bind('<Control-Key-l>', align_left)
    root.bind('<Control-Key-L>', align_left)
    root.bind('<Control-Key-e>', align_center)
    root.bind('<Control-Key-E>', align_center)
    root.bind('<Control-Key-r>', align_right)
    root.bind('<Control-Key-R>', align_right)
    root.bind('<Control-Key-p>', print_file)
    root.bind('<Control-Key-P>', print_file)
    root.bind('<Control-Key-n>', new_file)
    root.bind('<Control-Key-N>', new_file)
    root.bind('<Control-Key-Delete>', clear)
    root.bind('<Control-Key-f>', find_text)
    root.bind('<Control-Key-F>', find_text)
    root.bind('<Control-Key-h>', replace)
    root.bind('<Control-Key-H>', replace)
    root.bind('<Control-Shift-Key-j>', join_words)
    root.bind('<Control-Shift-Key-J>', join_words)
    root.bind('<Control-Shift-Key-u>', lower_upper)
    root.bind('<Control-Shift-Key-U>', lower_upper)
    root.bind('<Alt-F4>', exit_app)
    root.bind('<Control-Shift-Key-r>', reverse_characters)
    root.bind('<Control-Shift-Key-R>', reverse_characters)
    root.bind('<Control-Shift-Key-c>', reverse_words)
    root.bind('<Control-Shift-Key-C>', reverse_words)
    root.bind('<Alt-Key-d>', copy_file_path)
    root.bind('<Alt-Key-D>', copy_file_path)
    root.bind('<Control-Key-plus>', size_up_shortcut)
    root.bind('<Control-Key-minus>', size_down_shortcut)
    root.bind('<F5>', dt)
    root.bind('<Control-Key-g>', goto)
    root.bind('<Control-Key-G>', goto)
    # special events
    font_size.bind('<<ComboboxSelected>>', change_font_size)
    font_ui.bind("<<ComboboxSelected>>", change_font)
    root.bind('<<Modified>>', status)
    # buttons creation and placement
    bold_button = Button(toolbar_frame, image=BOLD_IMAGE, command=bold, relief=FLAT)
    bold_button.grid(row=0, column=0, sticky=W, padx=2)

    italics_button = Button(toolbar_frame, image=ITALICS_IMAGE, command=italics, relief=FLAT)
    italics_button.grid(row=0, column=1, sticky=W, padx=2)

    underline_button = Button(toolbar_frame, image=UNDERLINE_IMAGE, command=underline, relief=FLAT)
    underline_button.grid(row=0, column=2, sticky=W, padx=2)

    color_button = Button(toolbar_frame, image=COLORS_IMAGE, command=text_color, relief=FLAT)
    color_button.grid(row=0, column=3, padx=5)

    align_left_button = Button(toolbar_frame, image=ALIGN_LEFT_IMAGE, relief=FLAT)
    align_left_button.grid(row=0, column=6, padx=5)

    # align center button
    align_center_button = Button(toolbar_frame, image=ALIGN_CENTER_IMAGE, relief=FLAT)
    align_center_button.grid(row=0, column=7, padx=5)

    # align right button
    align_right_button = Button(toolbar_frame, image=ALIGN_RIGHT_IMAGE, relief=FLAT)
    align_right_button.grid(row=0, column=8, padx=5)

    # tts button
    tts_button = Button(toolbar_frame, image=TTS_IMAGE, relief=FLAT,
                        command=lambda: Thread(target=text_to_speech).start(),
                        )
    tts_button.grid(row=0, column=9, padx=5)

    # talk button
    talk_button = Button(toolbar_frame, image=STT_IMAGE, relief=FLAT,
                         command=lambda: Thread(target=speech_to_text).start())
    talk_button.grid(row=0, column=10, padx=5)

    # buttons config
    align_left_button.configure(command=align_left)
    align_center_button.configure(command=align_center)
    align_right_button.configure(command=align_right)

    # opening sentence
    op_msgs = ['Hello world!', '^-^', 'What a beautiful day!', 'Welcome!', '', 'Believe in yourself!',
               'If I did it you can do way more than that', 'Don\'t give up!',
               'I\'m glad that you are using my Text editor (:', 'Feel free to send feedback']
    op_msg = choice(op_msgs)
    EgonTE.insert('1.0', op_msg)

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
    TOOL_TIP.bind_widget(font_size, balloonmsg='upwards - (ctrl+plus) \n downwards - (ctrl+minus)')

    # ui lists
    toolbar_components = [bold_button, italics_button, color_button, underline_button, align_left_button,
                          align_center_button, align_right_button, tts_button, talk_button, font_size]
    menus_components = [file_menu, edit_menu, tool_menu, color_menu, options_menu]
    other_components = [root, status_bar, file_bar, EgonTE, toolbar_frame]


def load_images():
    global BOLD_IMAGE, UNDERLINE_IMAGE, ITALICS_IMAGE, ALIGN_LEFT_IMAGE, ALIGN_CENTER_IMAGE, \
        ALIGN_RIGHT_IMAGE, TTS_IMAGE, STT_IMAGE, COLORS_IMAGE
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


# current time for the file bar
def get_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_pos():
    return EgonTE.index(INSERT)


# open the GitHub page
def github():
    open_('https://github.com/Ariel4545/text_editor')


def undo():
    return EgonTE.edit_undo()


# create file func
def new_file(event=None):
    global file_name
    file_name = ''
    EgonTE.delete("1.0", END)
    file_bar.config(text='New file')

    global open_status_name
    open_status_name = False


# open file func
def open_file(event=None):
    global file_name
    EgonTE.delete("1.0", END)
    text_file = filedialog.askopenfilename(initialdir=getcwd(), title='Open file',
                                           filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html'),
                                                      ('Python Files', '*.py')))
    if text_file:
        global open_status_name
        open_status_name = text_file
        file_name = text_file
        file_bar.config(text=f'Opened file: {GetShortPathName(file_name)}')
        file_name.replace('C:/EgonTE/', '')
        file_name.replace('C:/users', '')
        text_file = open(text_file, 'r')
        stuff = text_file.read()
        EgonTE.insert(END, stuff)
        text_file.close()
    else:
        messagebox.showerror('error', 'File not found / selected')


# save as func
def save_as(event=None):
    global file_name
    if event == None:
        text_file = filedialog.asksaveasfilename(defaultextension=".*", initialdir='C:/EgonTE', title='Save File',
                                                 filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html'),
                                                            ('Python Files', '*.py')))
        if text_file:
            file_name = text_file
            file_name = file_name.replace('C:/EgonTE', '')
            file_bar.config(text=f'Saved: {file_name} - {get_time()}')

            text_file = open(text_file, 'w')
            text_file.write(EgonTE.get(1.0, END))
            text_file.close()
    if event == 'get name':
        try:
            return file_name
        except NameError:
            messagebox.showerror('error', 'You cant copy a file name if you doesn\'t use a file ')


# save func
def save(event=None):
    global open_status_name, file_name
    if open_status_name:
        text_file = open(open_status_name, 'w')
        text_file.write(EgonTE.get(1.0, END))
        text_file.close()
        file_bar.config(text=f'Saved: {file_name} - {get_time()}')
    else:
        save_as(None)


# cut func
def cut(x):
    global selected
    if not x:
        selected = root.clipboard_get()
    else:
        if is_marked():
            # grab
            selected = EgonTE.selection_get()
            # del
            EgonTE.delete('sel.first', 'sel.last')
            root.clipboard_clear()
            root.clipboard_append(selected)


# copy func
def copy(x):
    global selected
    if is_marked():
        # grab
        root.clipboard_clear()
        root.clipboard_append(EgonTE.selection_get())


# paste func
def paste(x):
    global selected
    if selected:
        EgonTE.insert(get_pos(), root.clipboard_get())


# bold text func
def bold(event=None):
    # create

    bold_font = font.Font(EgonTE, EgonTE.cget('font'))
    bold_font.configure(weight='bold')
    # config
    EgonTE.tag_configure('bold', font=bold_font)
    current_tags = EgonTE.tag_names('1.0')
    if 'bold' in current_tags:
        if is_marked():
            EgonTE.tag_remove('bold', 'sel.first', 'sel.last')
        else:
            EgonTE.tag_remove('bold', '1.0', 'end')
    else:
        if is_marked():
            EgonTE.tag_add('bold', 'sel.first', 'sel.last')
        else:
            EgonTE.tag_add('bold', '1.0', 'end')


# italics text func
def italics(event=None):
    # create
    italics_font = font.Font(EgonTE, EgonTE.cget('font'))
    italics_font.configure(slant='italic')
    # config
    EgonTE.tag_configure('italics', font=italics_font)
    current_tags = EgonTE.tag_names('1.0')
    if 'italics' in current_tags:
        if is_marked():
            EgonTE.tag_remove('italics', 'sel.first', 'sel.last')
        else:
            EgonTE.tag_remove('italics', '1.0', 'end')
    else:
        if is_marked():
            EgonTE.tag_add('italics', 'sel.first', 'sel.last')
        else:
            EgonTE.tag_add('italics', '1.0', 'end')


# make the text underline func
def underline(event=None):
    # create
    underline_font = font.Font(EgonTE, EgonTE.cget('font'))
    underline_font.configure(underline=True)
    # config
    EgonTE.tag_configure('underline', font=underline_font)
    current_tags = EgonTE.tag_names('1.0')
    if 'underline' in current_tags:
        if is_marked():
            EgonTE.tag_remove('underline', 'sel.first', 'sel.last')
        else:
            EgonTE.tag_remove('underline', '1.0', 'end')
    else:
        if is_marked():
            EgonTE.tag_add('underline', 'sel.first', 'sel.last')
        else:
            EgonTE.tag_add('underline', '1.0', 'end')


# text color func
def text_color():
    # color pick
    selected_color = colorchooser.askcolor(title='Text color')[1]
    if selected_color:
        # create
        color_font = font.Font(EgonTE, EgonTE.cget('font'))
        # config
        EgonTE.tag_configure('colored_txt', font=color_font, foreground=selected_color)
        current_tags = EgonTE.tag_names('1.0')
        if 'underline' in current_tags:
            if is_marked():
                EgonTE.tag_remove('colored_txt', 'sel.first', 'sel.last')
            else:
                EgonTE.tag_remove('colored_txt', '1.0', 'end')
        else:
            if is_marked():
                EgonTE.tag_add('colored_txt', 'sel.first', 'sel.last')
            else:
                EgonTE.tag_add('colored_txt', '1.0', 'end')


# background color func
def bg_color():
    selected_color = colorchooser.askcolor(title='Background color')[1]
    if selected_color:
        EgonTE.config(bg=selected_color)


# all color txt func
def all_txt_color(event=None):
    color = colorchooser.askcolor(title='Text color')[1]
    if color:
        EgonTE.config(fg=color)


# highlight color func
def hl_color():
    color = colorchooser.askcolor(title='Highlight color')[1]
    if color:
        EgonTE.config(selectbackground=color)


# print file func
def print_file(event=None):
    printer_name = GetDefaultPrinter()
    file2p = filedialog.askopenfilename(initialdir='C:/EgonTE/', title='Open file',
                                        filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html'),
                                                   ('Python Files', '*.py')))
    if file2p:
        if messagebox.askquestion('EgonTE', f'are you wish to print with {printer_name}?'):
            ShellExecute(0, 'print', file2p, None, '.', 0)


# select all func
def select_all(event=None):
    EgonTE.tag_add('sel', '1.0', 'end')


# clear func
def clear(event=None):
    EgonTE.delete('1.0', END)


# hide file bar & status bar func
def hide_statusbars():
    global show_statusbar
    global bars_active
    if show_statusbar:
        status_bar.pack_forget()
        file_bar.pack_forget()
        root.geometry(f'{width}x{height - 30}')
        show_statusbar = False
        bars_active = False
    else:
        status_bar.pack(side=LEFT)
        file_bar.pack(side=RIGHT)
        root.geometry(f'{width}x{height - 20}')
        show_statusbar = True
        bars_active = True


#  hide tool bar func
def hide_toolbar():
    global show_toolbar, height, width
    if show_toolbar:
        toolbar_frame.pack_forget()
        height = 770
        root.geometry(f'{width}x{height}')
        show_toolbar = False
    else:
        EgonTE.focus_displayof()
        EgonTE.pack_forget()
        text_scroll.pack_forget()
        toolbar_frame.pack(fill=X, anchor=W)
        text_scroll.pack(side=RIGHT, fill=Y)
        EgonTE.pack(fill=BOTH, expand=True, side=BOTTOM)
        EgonTE.focus_set()
        height = 805
        root.geometry(f'{width}x{height}')
        show_toolbar = True


# night on func
def night():
    global night_mode
    if night_mode:
        main_color = '#110022'
        second_color = '#373737'
        third_color = '#280137'
        _text_color = 'green'
        root.config(bg=main_color)
        status_bar.config(bg=main_color, fg=_text_color)
        file_bar.config(bg=main_color, fg=_text_color)
        EgonTE.config(bg=second_color, fg=_text_color)
        toolbar_frame.config(bg=main_color)
        # toolbar buttons
        for toolbar_button in toolbar_components:
            toolbar_button.config(background=third_color)
        # file menu colors
        for menu_ in menus_components:
            menu_.config(background=second_color, foreground=_text_color)
        night_mode = False
    else:
        main_color = 'SystemButtonFace'
        second_color = 'SystemButtonFace'
        _text_color = 'black'
        root.config(bg=main_color)
        status_bar.config(bg=main_color, fg=_text_color)
        file_bar.config(bg=main_color, fg=_text_color)
        EgonTE.config(bg='white', fg=_text_color)
        toolbar_frame.config(bg=main_color)
        # toolbar buttons
        for toolbar_button in toolbar_components:
            toolbar_button.config(background=second_color)
        # file menu colors
        for menu_ in menus_components:
            menu_.config(background=second_color, foreground=_text_color)
        night_mode = True


def change_font(event):
    global chosen_font
    chosen_font = font_family.get()
    delete_tags()
    EgonTE.configure(font=(chosen_font, 16))


def change_font_size(event=None):
    global chosen_size, font_Size_c
    chosen_size = size_var.get()
    font_Size_c = (chosen_size - 8) // 2
    # font_Size_c = font_size.get()
    # print(font_Size_c)
    font_size.current(font_Size_c)
    # EgonTE.configure(font=(chosen_font, chosen_size))

    size = font.Font(EgonTE, EgonTE.cget('font'))
    size.configure(size=chosen_size)
    # config
    EgonTE.tag_configure('size', font=size)
    current_tags = EgonTE.tag_names('1.0')
    if not 'size' in current_tags:
        if font_size.get() == '4':
            EgonTE.tag_remove('size', '1.0', END)
        else:
            EgonTE.tag_add('size', '1.0', END)


def replace(event=None):
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
    def rep_button():
        find_ = find_input.get()
        replace_ = replace_input.get()
        content = EgonTE.get(1.0, END)

        new_content = content.replace(find_, replace_)
        EgonTE.delete(1.0, END)
        EgonTE.insert(1.0, new_content)

    replace_button.config(command=rep_button)


# align Left func
def align_left(event=None):
    if is_marked():
        text_content = EgonTE.get('sel.first', 'sel.last')
    else:
        EgonTE.tag_add('sel', 'insert linestart', 'insert lineend')
        text_content = EgonTE.get('insert linestart', 'insert lineend')
    EgonTE.tag_config("left", justify=LEFT)
    try:
        EgonTE.delete('sel.first', 'sel.last')
        EgonTE.insert(INSERT, text_content, "left")
    except:
        messagebox.showerror('error', 'choose a line content')


# Align Center func
def align_center(event=None):
    if is_marked():
        text_content = EgonTE.get('sel.first', 'sel.last')
    else:
        EgonTE.tag_add('sel', 'insert linestart', 'insert lineend')
        text_content = EgonTE.get('insert linestart', 'insert lineend')
    EgonTE.tag_config("center", justify=CENTER)
    try:
        EgonTE.delete('sel.first', 'sel.last')
        EgonTE.insert(INSERT, text_content, "center")
    except:
        messagebox.showerror('error', 'choose a line with content')


# Align Right func
def align_right(event=None):
    if is_marked():
        text_content = EgonTE.get('sel.first', 'sel.last')
    else:
        EgonTE.tag_add('sel', 'insert linestart', 'insert lineend')
        text_content = EgonTE.get('insert linestart', 'insert lineend')
    EgonTE.tag_config("right", justify=RIGHT)
    try:
        EgonTE.delete('sel.first', 'sel.last')
        EgonTE.insert(INSERT, text_content, "right")
    except:
        messagebox.showerror('error', 'choose a line with content')


# get & display character and word count with status bar
def status(event=None):
    global text_changed, lines
    if EgonTE.edit_modified():
        text_changed = True
        words = len(EgonTE.get(1.0, "end-1c").split())
        characters = len(EgonTE.get(1.0, "end-1c"))
        lines = int((EgonTE.index(END)).split('.')[0]) - 1
        status_bar.config(text=f'Lines:{lines} Characters:{characters} Words:{words}')
    EgonTE.edit_modified(False)


# AI narrator will read the selected text from the text box
def text_to_speech():
    global tts
    tts = pyttsx3.init()
    try:
        content = EgonTE.get('sel.first', 'sel.last')
    except:
        content = EgonTE.get('1.0', 'end')
    tts.say(content)
    tts.runAndWait()


# AI narrator will read the given text for other functions
def read_text(**kwargs):
    global engine
    engine = pyttsx3.init()
    if 'text' in kwargs:
        ttr = kwargs['text']
    else:
        ttr = EgonTE.get(1.0, 'end')
    engine.say(ttr)
    engine.runAndWait()
    engine.stop()


# to make the narrator voice more convincing
def text_formatter(phrase):
    interrogatives = ('how', 'why', 'what', 'when', 'who', 'where', 'is', 'do you', "whom", "whose")
    capitalized = phrase.capitalize()
    if phrase.startswith(interrogatives):
        return f'{capitalized}?'
    else:
        return f'{capitalized}.'


# advanced speech to text function
def speech_to_text():
    error_sentences = ['I don\'t know what you mean!', 'can you say that again?', 'please speak more clear']
    error_sentence = choice(error_sentences)
    error_msg = f'Excuse me, {error_sentence}'
    recolonize = Recognizer()  # initialize the listener
    mic = Microphone()
    with mic as source:  # set listening device to microphone
        read_text(text='Please say the message you would like to the text editor!')
        recolonize.pause_threshold = 1
        audio = recolonize.listen(source)
    try:
        query = recolonize.recognize_google(audio, language='en-UK')  # listen to audio
        query = text_formatter(query)
    except Exception:
        read_text(text=error_msg)
        if messagebox.askyesno('EgonTE', 'are you want to try again?'):
            query = speech_to_text()
        else:
            gb_sentences = ['ok', 'goodbye', 'sorry', 'my bad']
            gb_sentence = choice(gb_sentences)
            read_text(text=f'{gb_sentence}, I will try to do my best next time!')
    EgonTE.insert(INSERT, query, END)
    return query


# force the app to quit, warn user if file data is about to be lost
def exit_app(event=None):
    global text_changed
    if text_changed:
        if messagebox.askyesno('Quit', 'Some changes  warn\'t saved, do you wish to save first?'):
            save()
            root.quit()
            exit_()
            quit()
            exit()
        else:
            root.quit()
            exit_()
            quit()
            exit()
    else:
        root.quit()
        exit_()
        quit()
        exit()


# find if text exists in the specific file
def find_text(event=None):
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
        text_data = EgonTE.get('1.0', END + '-1c')
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
            starting_index = EgonTE.search(entry_data, '1.0', END)
            if starting_index:
                offset = '+%dc' % len(entry_data)
                ending_index = starting_index + offset
                EgonTE.tag_add(SEL, starting_index, ending_index)

            if int(occurs) > 1:
                # navigation window

                def down(si, ei):
                    global ending_index, starting_index
                    EgonTE.tag_remove(SEL, '1.0', END)
                    starting_index = EgonTE.search(entry_data, ei, END)
                    if si:
                        offset = '+%dc' % len(entry_data)
                        ending_index = starting_index + offset
                        print(f'str:{starting_index} end:{ending_index}')
                        EgonTE.tag_add(SEL, starting_index, ending_index)
                        starting_index = ending_index
                    button_up.config(state=ACTIVE)

                def up(si, ei):
                    global starting_index, ending_index
                    EgonTE.tag_remove(SEL, '1.0', END)
                    starting_index = EgonTE.search(entry_data, '1.0', si)
                    if si:
                        offset = '+%dc' % len(entry_data)
                        ending_index = starting_index + offset
                        print(f'str:{starting_index} end:{ending_index}')
                        EgonTE.tag_add(SEL, starting_index, ending_index)
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
                button_down = Button(nav_root, text='↓', command=lambda: down(starting_index, ending_index), width=5)
                # placing
                title.grid(row=0, padx=5)
                button_up.grid(row=1)
                button_down.grid(row=2)


        else:
            search_label = messagebox.showinfo("EgonTE:", "No match found")

    # window
    search_text_root = Toplevel()
    search_text_root.resizable(False, False)
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

    if is_marked():
        text_entry.insert('end', EgonTE.get('sel.first', 'sel.last'))


# insert mathematics calculation to the text box
def ins_calc():
    def enter_button():
        equation = clac_entry.get()
        try:
            equation = eval(equation)
        except SyntaxError:
            messagebox.showerror('error', 'typed some  invalid characters')
        except NameError:
            messagebox.showerror('error', 'calculation tool support only arithmetics & modulus')
        equation = str(equation) + ' '
        EgonTE.insert(get_pos(), equation)

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
    clac_root.geometry('150x90')
    introduction_text = Label(clac_root, text='Enter equation below:', font='arial 10 underline')
    enter = Button(clac_root, text='Enter', command=enter_button, relief=FLAT)
    clac_entry = Entry(clac_root, relief=RIDGE, justify='center')
    show_op = Button(clac_root, text='Show operators', relief=FLAT, command=show_oper)
    introduction_text.grid(row=0, padx=10)
    clac_entry.grid(row=1)
    enter.grid(row=2)
    show_op.grid(row=3)

    if is_marked():
        if str(EgonTE.get('sel.first', 'sel.last')).isnumeric():
            clac_entry.insert('end', EgonTE.get('sel.first', 'sel.last'))


# insert the current date & time to the text box
def dt(event=None):
    EgonTE.insert(get_pos(), get_time() + ' ')


# insert a randon number to the text box
def ins_random():
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
            EgonTE.insert(get_pos(), rand)
        except NameError:
            pass

    def enter_button_quick_float():
        random_float = str(random()) + ' '
        EgonTE.insert(get_pos(), random_float)

    def enter_button_quick_int():
        random_float = random()
        random_exp = len(str(random_float))
        random_round = randint(50, 1000)
        random_int = int(random_float * 10 ** random_exp)
        random_int //= random_round
        random_int = str(random_int) + ' '
        EgonTE.insert(get_pos(), random_int)

    ran_num_root = Toplevel()
    ran_num_root.resizable(False, False)
    introduction_text = Label(ran_num_root, text='Enter numbers below:', justify='center', font='arial 10 underline')
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

    if is_marked():
        ran_numbers = EgonTE.get('sel.first', 'sel.last')
        numbers_separation = ran_numbers.split(' ')
        if str(ran_numbers[0]).isnumeric():
            print(numbers_separation)
            number_entry1.insert('end', numbers_separation[0])
        try:
            number_entry2.insert('end', numbers_separation[1])
        except IndexError:
            pass
    else:
        number_entry1.insert('end', randint(1, 10))
        number_entry2.insert('end', randint(10, 1000))


def copy_file_path(event=None):
    # global selected
    file_name_ = save_as(event='get name')
    root.clipboard_clear()
    root.clipboard_append(file_name_)


# change between the default and custom cursor
def custom_cursor():
    global cc, predefined_cursor
    if cc:
        predefined_cursor = 'tcross'
        EgonTE.config(cursor=predefined_cursor)
        cc = False
    else:
        predefined_cursor = 'xterm'
        EgonTE.config(cursor=predefined_cursor)
        cc = True


# change between the default and custom style
def custom_style():
    global cs, predefined_style
    if not cs:
        predefined_style = 'clam'
        style.theme_use(predefined_style)
        cs = True
    else:
        predefined_style = 'vista'
        style.theme_use(predefined_style)
        cs = False


def word_warp():
    global ww, horizontal_scroll
    if not ww:
        EgonTE.config(wrap=WORD)
        root.geometry(f'{width}x{height - 10}')
        horizontal_scroll.pack_forget()
        ww = True
    else:
        root.geometry(f'{width}x{height + 10}')
        horizontal_scroll.pack(side=BOTTOM, fill=X)
        EgonTE.config(wrap=NONE)

        ww = False


def ins_random_name():
    global random_name

    # insert the random name into the text box
    def button():
        global random_name
        EgonTE.insert(get_pos(), random_name + ' ')

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
    random_name = names.get_full_name()
    text = Label(name_root, text='Random name that generated:', font='arial 10 underline')
    rand_name = Label(name_root, text=random_name)
    enter = Button(name_root, text='Submit', command=button, relief=RIDGE)
    re_roll = Button(name_root, text='Re-roll', command=roll, relief=RIDGE)
    adv_options = Button(name_root, text='Advance options', command=adv_option, state=ACTIVE, relief=RIDGE)
    text.grid(row=0, padx=10)
    rand_name.grid(row=1)
    enter.grid(row=2)
    re_roll.grid(row=3)
    adv_options.grid(row=4)


def translate():
    def button():
        to_translate = translate_box.get("1.0", "end-1c")
        cl = choose_langauge.get()

        if to_translate == '':
            messagebox.showerror('Error', 'Please fill the box')
        else:
            translator = Translator()
            output = translator.translate(to_translate, dest=cl)
            EgonTE.insert(get_pos(), output.text)

    def copy_from_file():
        if is_marked():
            translate_box.insert('end', EgonTE.get('sel.first', 'sel.last'))
        else:
            translate_box.insert('end', EgonTE.get('1.0', 'end'))

    # window
    translate_root = Toplevel()
    translate_root.resizable(False, False)
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
        'Bulgarian', ' Catalan', 'Cebuano', 'Chichewa', 'Chinese', 'Corsican', 'Croatian', ' Czech', 'Danish', 'Dutch',
        'English', 'Esperanto', 'Estonian', 'Filipino', 'Finnish', 'French', 'Frisian', 'Galician', 'Georgian',
        'German', 'Greek', 'Gujarati', 'Haitian Creole', 'Hausa', 'Hawaiian', 'Hebrew', 'Hindi', 'Hmong', 'Hungarian',
        'Icelandic', 'Igbo', 'Indonesian', 'Irish', 'Italian', 'Japanese', 'Javanese', 'Kannada', 'Kazakh', 'Khmer',
        'Kinyarwanda', 'Korean', 'Kurdish', 'Kyrgyz', 'Lao', 'Latin', 'Latvian', 'Lithuanian', 'Luxembourgish',
        'Macedonian', 'Malagasy', 'Malay', 'Malayalam', 'Maltese', 'Maori', 'Marathi', 'Mongolian', 'Myanmar', 'Nepali',
        'Norwegian''Odia', 'Pashto', 'Persian', 'Polish', 'Portuguese', 'Punjabi', 'Romanian', 'Russian', 'Samoan',
        'Scots Gaelic', 'Serbian', 'Sesotho', 'Shona', 'Sindhi', 'Sinhala', 'Slovak', 'Slovenian', 'Somali', 'Spanish',
        'Sundanese', 'Swahili', 'Swedish', 'Tajik', 'Tamil', 'Tatar', 'Telugu', 'Thai', 'Turkish', 'Turkmen',
        'Ukrainian', 'Urdu', 'Uyghur', 'Uzbek', 'Vietnamese', 'Welsh', 'Xhosa''Yiddish', 'Yoruba', 'Zulu',
    )
    # translate box & button
    translate_box = Text(translate_root, width=30, height=10, borderwidth=5)
    button_ = Button(translate_root, text="Translate", relief=FLAT, borderwidth=3, font=('arial', 10, 'bold'),
                     cursor=predefined_cursor,
                     command=button)
    copy_from = Button(translate_root, text='Copy from file', relief=FLAT, command=copy_from_file)
    # placing the objects in the window
    auto_detect.grid(row=0)
    choose_langauge.grid(row=1)
    translate_box.grid(row=2)
    button_.grid(row=3)
    copy_from.grid(row=4)


def url():
    # window
    url_root = Toplevel()
    url_root.resizable(False, False)
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
            EgonTE.insert(get_pos(), short_url)
        except:
            messagebox.showerror('error', 'Please Paste a valid url')

    enter.config(command=shorter)

    if is_marked():
        url_entry.insert('end', EgonTE.get('sel.first', 'sel.last'))


def reverse_characters(event=None):
    content = EgonTE.get(1.0, END)
    reversed_content = content[::-1]
    EgonTE.delete(1.0, END)
    EgonTE.insert(1.0, reversed_content)
    unacceptable_line_removal(type='characters')


def reverse_words(event=None):
    content = EgonTE.get(1.0, END)
    words = content.split()
    reversed_words = words[::-1]
    EgonTE.delete(1.0, END)
    unacceptable_line_removal()
    EgonTE.insert(1.0, reversed_words)

def join_words(event=None):
    content = EgonTE.get(1.0, END)
    words = content.split()
    joined_words = ''.join(words)
    EgonTE.delete(1.0, END)
    unacceptable_line_removal()
    EgonTE.insert(1.0, joined_words)


def lower_upper(event=None):
    content = EgonTE.get(1.0, END)
    if content == content.upper():
        content = content.lower()
    else:
        content = content.upper()
    EgonTE.delete(1.0, END)
    unacceptable_line_removal(content, 'upper_lower')
    EgonTE.insert(1.0, content)


# a function to fix random appeared bug
def unacceptable_line_removal(content=None, type=None):
            if lines < 2:
                EgonTE.delete("end-2l", "end-1l")
            else:
                EgonTE.delete(1.0, 2.0)


def generate():
    global sym
    generate_root = Toplevel()
    generate_root.resizable(False, False)
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
                        characters.remove('!'), characters.remove('@'), characters.remove('#'), characters.remove('$'),
                        characters.remove('%'), characters.remove('^'), characters.remove('&'), characters.remove('*'),
                        characters.remove('('), characters.remove(')')
                    except ValueError:
                        pass
            shuffle(characters)
            sequence = []
            for i in range(length):
                sequence.append(choice(characters))
            EgonTE.insert(get_pos(), "".join(sequence))

    enter_button.config(command=generate_sequence)


# font size up by 1 iterations
def size_up_shortcut(event=None):
    global font_Size_c
    font_Size_c += 1
    try:
        font_size.current(font_Size_c)
        change_font_size()
    except Exception:
        messagebox.showerror('error', 'font size at maximum')


# font size down by 1 iterations
def size_down_shortcut(event=None):
    global font_Size_c
    font_Size_c -= 1
    try:
        font_size.current(font_Size_c)
        change_font_size()
    except Exception:
        messagebox.showerror('error', 'font size at minimum')


def custom_ui_colors(components):
    if components == 'buttons':
        selected_color = colorchooser.askcolor(title='Buttons background color')[1]
        if selected_color:
            for toolbar_button in toolbar_components:
                toolbar_button.config(background=selected_color)
    elif components == 'menus':
        selected_main_color = colorchooser.askcolor(title='Menu color')[1]
        selected_text_color = colorchooser.askcolor(title='Menu text color')[1]
        if selected_main_color and selected_text_color:
            for menu_ in menus_components:
                menu_.config(background=selected_main_color, foreground=selected_text_color)
    elif components == 'app':
        selected_main_color = colorchooser.askcolor(title='Frames color')[1]
        selected_second_color = colorchooser.askcolor(title='Text box color')[1]
        selected_text_color = colorchooser.askcolor(title='Text color')[1]
        if selected_main_color and selected_second_color and selected_text_color:
            root.config(bg=selected_main_color)
            status_bar.config(bg=selected_main_color, fg=selected_text_color)
            file_bar.config(bg=selected_main_color, fg=selected_text_color)
            EgonTE.config(bg=selected_second_color)
            toolbar_frame.config(bg=selected_main_color)


# checks if text in the main text box is being marked
def is_marked():
    if EgonTE.tag_ranges('sel'):
        return True
    else:
        return False


# tags and configurations of the same thing is clashing all the time \:
def delete_tags():
    global font_Size_c
    EgonTE.tag_delete('bold', 'underline', 'italics', 'size', 'colored_txt')
    font_Size_c = 4
    font_size.current(font_Size_c)


def special_files_import(file_type):
    # to make the functions write the whole file even if its huge
    pandas.options.display.max_rows = 9999
    content = ''
    if file_type == 'excel':
        special_file = filedialog.askopenfilename(title='open excel file',
                                                  filetypes=(('excel', '*.xlsx'), ('all', '*.*')))
        if special_file:
            content = pandas.read_excel(special_file).to_string()
    elif file_type == 'csv':
        special_file = filedialog.askopenfilename(title='open csv file',
                                                  filetypes=(('csv', '*.csv'), ('all', '*.*')))
        if special_file:
            content = pandas.read_csv(special_file).to_string()
    elif file_type == 'json':
        special_file = filedialog.askopenfilename(title='open json file',
                                                  filetypes=(('json', '*.json'), ('all', '*.*')))
        if special_file:
            content = pandas.read_json(special_file).to_string()
    elif file_type == 'xml':
        special_file = filedialog.askopenfilename(title='open xml file',
                                                  filetypes=(('xml', '*.xml'), ('all', '*.*')))
        if special_file:
            content = pandas.read_xml(special_file).to_string()

    EgonTE.insert(get_pos(), content)


# a window that have explanations confusing features
def e_help():
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
    frame.pack(pady=5)
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


def right_align_language_support():
    if EgonTE.get('1.0', 'end'):
        lan = polyglot.Text(EgonTE.get('1.0', 'end')).language.name
        if lan == 'Arabic' or 'Hebrew' or 'Persian' or 'Pashto' or 'Urdu' or 'Kashmiri' or 'Sindhi':
            align_right()


def search_www():
    ser_root = Toplevel()
    ser_root.resizable(False, False)

    def enter():
        if entry_box.get() != '':
            open_(entry_box.get())

    def copy_from_file():
        if is_marked():
            entry_box.insert('end', EgonTE.get('sel.first', 'sel.last'))
        else:
            entry_box.insert('end', EgonTE.get('1.0', 'end'))

    title = Label(ser_root, text='Search with google', font='arial 14 underline')
    entry_box = Entry(ser_root, relief=GROOVE, width=40)
    enter_button = Button(ser_root, relief=FLAT, command=enter, text='Enter')
    from_text_button = Button(ser_root, relief=FLAT, command=copy_from_file, text='Copy from text')

    title.grid(row=0, column=0, padx=10, pady=3)
    entry_box.grid(row=1, column=0, padx=10)
    enter_button.grid(row=2, column=0)
    from_text_button.grid(row=3, column=0, pady=5)

    if is_marked():
        entry_box.insert('end', EgonTE.get('sel.first', 'sel.last'))


def advance_options():
    global file_, status_, bars_active, show_statusbar
    global predefined_cursor, predefined_style

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
        global predefined_cursor
        EgonTE.config(cursor=cursor)
        change_button_color('cursors', cursor)
        predefined_cursor = cursor

    def hide_(bar):
        global file_, status_, show_statusbar, bars_active
        if bar == 'statusbar':
            if status_:
                status_bar.pack_forget()
                root.geometry(f'{width}x{height - 30}')
                status_ = False
            else:
                status_bar.pack(side=LEFT)
                root.geometry(f'{width}x{height - 20}')
                status_ = True
        elif bar == 'filebar':
            if file_:
                file_bar.pack_forget()
                root.geometry(f'{width}x{height - 30}')
                file_ = False
            else:
                file_bar.pack(side=RIGHT)
                root.geometry(f'{width}x{height - 20}')
                file_ = True
        # link to the basic options
        if status_ and file_:
            show_statusbar = True
            bars_active = True
        else:
            show_statusbar = False
            bars_active = False

    def change_style(style_):
        global predefined_style
        style.theme_use(style_)
        change_button_color('styles', style_)
        predefined_style = style_

    def change_relief(relief_):
        global predefined_relief
        EgonTE.config(relief=relief_)
        change_button_color('relief', relief_)
        predefined_relief = relief_

    # window
    opt_root = Toplevel()
    opt_root.resizable(False, False)

    def predefined_checkbuttons():
        global file_, status_, show_statusbar
        if bars_active:
            status_ = BooleanVar()
            status_.set(True)
            file_ = BooleanVar()
            file_.set(True)
            show_statusbar = BooleanVar()
            show_statusbar.set(True)
            show_statusbar = True
        else:
            status_ = BooleanVar()
            status_.set(False)
            file_ = BooleanVar()
            file_.set(False)
            show_statusbar = BooleanVar()
            show_statusbar.set(False)
            show_statusbar = False
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
    filebar_check = Checkbutton(opt_root, text='filebar', command=lambda: hide_('filebar'), variable=status_)
    statusbar_check = Checkbutton(opt_root, text='statusbar', command=lambda: hide_('statusbar'), variable=file_)
    style_title = Label(opt_root, text='Advance style configuration', font=font_)
    style_clam = Button(opt_root, text='clam', command=lambda: change_style('clam'), width=button_width)
    style_classic = Button(opt_root, text='classic', command=lambda: change_style('classic'), width=button_width)
    style_vista = Button(opt_root, text='vista', command=lambda: change_style('vista'), width=button_width)
    relief_title = Label(opt_root, text='Advance relief configuration', font=font_)
    relief_flat = Button(opt_root, text='flat', command=lambda: change_relief('flat'), width=button_width)
    relief_ridge = Button(opt_root, text='ridge', command=lambda: change_relief('ridge'), width=button_width)
    relief_groove = Button(opt_root, text='groove', command=lambda: change_relief('groove'), width=button_width)

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
    # buttons list
    adv_cursor_bs = [tcross_button, arrow_button, crosshair_button, pencil_button, fleur_button, xterm_button]
    adv_style_bs = [style_clam, style_vista, style_classic]
    adv_reliefs_bs = [relief_groove, relief_flat, relief_ridge]
    # button
    if predefined_cursor or predefined_style or predefined_relief:
        change_button_color('cursors', predefined_cursor)
        change_button_color('styles', predefined_style)
        change_button_color('relief', predefined_relief)


def goto(event=None):
    def enter():
        word = goto_input.get()
        starting_index = EgonTE.search(word, '1.0', END)
        offset = '+%dc' % len(word)
        if starting_index:
            ending_index = starting_index + offset
            index = EgonTE.search(word, ending_index, END)
        EgonTE.mark_set("insert", ending_index)

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


def sort():
    def sort_():
        sort_data = sort_input.get('1.0', 'end')
        sort_data_sorted = (sorted(sort_data)) # if I can use .sort prop the bug will be fixed
        # sort_data_sorted = (''.join(str(sorted((sort_data.split(' '))))).replace(('['), ' '))
        # sort_data_sorted = sort_data_sorted.replace(']', '')
        # sort_data_sorted = sort_data_sorted.replace('\'', '')
        # sort_data_sorted = sort_data_sorted.replace('\n', '')
        sort_input.delete('1.0', 'end')
        print(sort_data_sorted)
        for num in range(1,len(sort_data_sorted)):
            if num and num != ' ':
                sort_input.insert('insert lineend',f'{sort_data_sorted[num]}')


    def enter():
        for character in list(str(sort_input.get('1.0', 'end'))):
            if str(character).isdigit():
                EgonTE.insert(get_pos(), sort_input.get('1.0', 'end'))
                break

    # window
    sort_root = Toplevel()
    sort_root.resizable(False, False)
    # ui components
    sort_text = Label(sort_root, text='Enter the numbers you wish to sort:', font='arial 10 underline')
    sort_input = Text(sort_root, width=20, height=10)
    sort_button = Button(sort_root, text='Sort', command=sort_)
    sort_insert = Button(sort_root, text='Insert', command=enter)
    sort_text.grid(row=0, sticky=NSEW, column=0, padx=3)
    sort_input.grid(row=1, column=0)
    sort_button.grid(row=2, column=0)
    sort_insert.grid(row=3, column=0, pady=5)


if __name__ == '__main__':
    window('main')

if RA:
    right_align_language_support()

root.mainloop()

# contact - reedit = arielo_o, discord - Arielp2#4011
