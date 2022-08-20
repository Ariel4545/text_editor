import tkinter.messagebox
from tkinter import filedialog, colorchooser, font, ttk, PhotoImage
from tkinter import *
from tkinter.tix import *
import win32print
import win32api
import pyttsx3
import threading
import pyaudio
import random
import speech_recognition

root = Tk()
width = 1250
height = 830
screen_width = root.winfo_width()
screen_height = root.winfo_height()
placement_x = abs((screen_width // 2) - (width // 2))
placement_y = abs((screen_height // 2) - (height // 2))
root.geometry(f'{width}x{height}+{placement_x}+{placement_y}')
root.title('Egon Text editor')
root.resizable(False, False)

logo = PhotoImage(file='ETE_icon.png')
root.iconphoto(False, logo)

global open_status_name
global chosen_font
global selected

text_changed = False

chosen_font = 'arial'
chosen_size = 16

# icons - size=32x32
bold_img = PhotoImage(file='assets/bold.png')
underline_img = PhotoImage(file='assets/underlined-text.png')
italics_img = PhotoImage(file='assets/italics.png')
colors_img = PhotoImage(file='assets/edition.png')
align_left_img = PhotoImage(file='assets/left-align.png')
align_center_img = PhotoImage(file=f'assets/center-align.png')
align_right_img = PhotoImage(file='assets/right-align.png')
tts_img = PhotoImage(file='assets/tts(1).png')
talk_img = PhotoImage(file="assets/speech-icon-19(1).png")

# create toll tip
tip = Balloon(root)


# create file func
def new_file():
    EgonTE.delete("1.0", END)
    root.title('New file - Egon Text editor')
    status_bar.config(text='New file')

    global open_status_name
    open_status_name = False


# open file func
def open_file(event=None):
    EgonTE.delete("1.0", END)
    text_file = filedialog.askopenfilename(initialdir='C:/EgonTE/', title='Open file'
                                           , filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html'),
                                                        ('Python Files', '*.py')))
    if text_file:
        global open_status_name
        open_status_name = text_file
    name = text_file
    status_bar.config(text=f'{name}        ')
    name.replace('C:/EgonTE/', '')
    name.replace('C:/users', '')
    root.title(f'{name} - Egon Text editor')
    text_file = open(text_file, 'r')
    stuff = text_file.read()
    EgonTE.insert(END, stuff)
    text_file.close()


# save as func
def save_as(event=None):
    text_file = filedialog.asksaveasfilename(defaultextension=".*", initialdir='C:/EgonTE', title='Save File',
                                             filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html'),
                                                        ('Python Files', '*.py')))
    if text_file:
        name = text_file
        name = name.replace('C:/EgonTE', '')
        root.title(f'{name} - Egon Text editor')
        status_bar.config(text=f'Saved: {name}        ')

        text_file = open(text_file, 'w')
        text_file.write(EgonTE.get(1.0, END))
        text_file.close()


# save func
def save(event=None):
    global open_status_name
    if open_status_name:
        text_file = open(open_status_name, 'w')
        text_file.write(EgonTE.get(1.0, END))
        text_file.close()
        status_bar.config(text=f'Saved: {open_status_name}        ')
    else:
        save_as()


# cut func
def cut(x):
    global selected
    if x:
        selected = root.clipboard_get()
    else:
        if EgonTE.selection_get():
            # grab
            selected = EgonTE.selection_get()
            # del
            EgonTE.delete('sel.first', 'sel.last')
            root.clipboard_clear()
            root.clipboard_append(selected)


# copy func
def copy(x):
    global selected
    if x:
        selected = root.clipboard_get()
    if EgonTE.selection_get():
        # grab
        selected = EgonTE.selection_get()
        root.clipboard_clear()
        root.clipboard_append(selected)


# paste func
def paste(x):
    global selected
    if x:
        selected = root.clipboard_get()
    else:
        if selected:
            position = EgonTE.index(INSERT)
            EgonTE.insert(position, selected)


# bold text func
def bold(event=None):
    # create
    bold_font = font.Font(EgonTE, EgonTE.cget('font'))
    bold_font.configure(weight='bold')
    # config
    EgonTE.tag_configure('bold', font=bold_font)
    current_tags = EgonTE.tag_names('sel.first')
    if 'bold' in current_tags:
        EgonTE.tag_remove('bold', 'sel.first', 'sel.last')
    else:
        EgonTE.tag_add('bold', 'sel.first', 'sel.last')


# italics text func
def italics(event=None):
    # create
    italics_font = font.Font(EgonTE, EgonTE.cget('font'))
    italics_font.configure(slant='italic')
    # config
    EgonTE.tag_configure('italics', font=italics_font)
    current_tags = EgonTE.tag_names('sel.first')
    if 'italics' in current_tags:
        EgonTE.tag_remove('italics', 'sel.first', 'sel.last')
    else:
        EgonTE.tag_add('italics', 'sel.first', 'sel.last')


def underline(event=None):
    # create
    underline_font = font.Font(EgonTE, EgonTE.cget('font'))
    underline_font.configure(underline=True)
    # config+
    EgonTE.tag_configure('underline', font=underline_font)
    current_tags = EgonTE.tag_names('sel.first')
    if 'underline' in current_tags:
        EgonTE.tag_remove('underline', 'sel.first', 'sel.last')
    else:
        EgonTE.tag_add('underline', 'sel.first', 'sel.last')


# text color func
def text_color():
    # color pick
    selected_color = colorchooser.askcolor()[1]
    if selected_color:
        # create
        color_font = font.Font(EgonTE, EgonTE.cget('font'))
        # config
        EgonTE.tag_configure('colored_txt', font=color_font, foreground=selected_color)
        current_tags = EgonTE.tag_names('sel.first')
        if 'colored_txt' in current_tags:
            EgonTE.tag_remove('colored_txt', 'sel.first', 'sel.last')

        else:
            EgonTE.tag_add('colored_txt', 'sel.first', 'sel.last')


# background color func
def bg_color():
    selected_color = colorchooser.askcolor()[1]
    if selected_color:
        EgonTE.config(bg=selected_color)


# all color txt func
def all_txt_color():
    color = colorchooser.askcolor()[1]
    if color:
        EgonTE.config(fg=color)


# highlight color func
def hl_color():
    color = colorchooser.askcolor()[1]
    if color:
        EgonTE.config(selectbackground=color)


# print file func
def print_file():
    printer_name = win32print.GetDefaultPrinter()
    file2p = filedialog.askopenfilename(initialdir='C:/EgonTE/', title='Open file'
                                        , filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html'),
                                                     ('Python Files', '*.py')))
    if file2p:
        if tkinter.messagebox.askquestion('EgonTE', f'are you wish to print with {printer_name}?'):
            win32api.ShellExecute(0, 'print', file2p, None, '.', 0)


# select all func
def select_all(event=None):
    EgonTE.tag_add('sel', '1.0', 'end')


# clear func
def clear():
    EgonTE.delete('1.0', END)


def hide_statusbar():
    global show_statusbar
    if show_statusbar:
        status_bar.pack_forget()
        show_statusbar = False
    else:
        status_bar.pack(side=BOTTOM)
        show_statusbar = True


def hide_toolbar():
    global show_toolbar
    if show_toolbar:
        toolbar_frame.pack_forget()
        show_toolbar = False
    else:
        EgonTE.pack_forget()
        status_bar.pack_forget()
        toolbar_frame.pack(fill=X)
        EgonTE.pack(fill=BOTH, expand=True)
        status_bar.pack(side=BOTTOM)
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
        EgonTE.config(bg=second_color, fg=_text_color)
        toolbar_frame.config(bg=main_color)
        # toolbar buttons
        bold_button.config(bg=third_color, fg=_text_color)
        italics_button.config(bg=third_color, fg=_text_color)
        color_button.config(bg=third_color, fg=_text_color)
        underline_button.config(bg=third_color, fg=_text_color)
        align_left_button.config(bg=third_color, fg=_text_color)
        align_center_button.config(bg=third_color, fg=_text_color)
        align_right_button.config(bg=third_color, fg=_text_color)
        tts_button.config(bg=third_color, fg=_text_color)
        talk_button.config(bg=third_color, fg=_text_color)
        # file menu colors
        file_menu.config(bg=second_color, fg=_text_color)
        edit_menu.config(bg=second_color, fg=_text_color)
        color_menu.config(bg=second_color, fg=_text_color)
        options_menu.config(bg=second_color, fg=_text_color)
        night_mode = False
    else:
        main_color = 'SystemButtonFace'
        second_color = 'SystemButtonFace'
        _text_color = 'black'
        root.config(bg=main_color)
        status_bar.config(bg=main_color, fg=_text_color)
        EgonTE.config(bg='white', fg=_text_color)
        toolbar_frame.config(bg=main_color)
        # toolbar buttons
        bold_button.config(bg=second_color, fg=_text_color)
        italics_button.config(bg=second_color, fg=_text_color)
        color_button.config(bg=second_color, fg=_text_color)
        underline_button.config(bg=second_color, fg=_text_color)
        align_left_button.config(bg=second_color, fg=_text_color)
        align_center_button.config(bg=second_color, fg=_text_color)
        align_right_button.config(bg=second_color, fg=_text_color)
        tts_button.config(bg=second_color, fg=_text_color)
        talk_button.config(bg=second_color, fg=_text_color)
        # file menu colors
        file_menu.config(bg=second_color, fg=_text_color)
        edit_menu.config(bg=second_color, fg=_text_color)
        color_menu.config(bg=second_color, fg=_text_color)
        options_menu.config(bg=second_color, fg=_text_color)
        night_mode = True
    # text_scroll.config(bg=third_color)


def change_font(event=None):
    global chosen_font
    chosen_font = font_family.get()
    # wb font tuple
    sfont = font.Font(EgonTE, EgonTE.cget('font'))
    # config
    EgonTE.config(font=sfont)
    EgonTE.tag_configure('font', font=chosen_font)


def change_font_size(event=None):
    global chosen_size
    chosen_size = size_var.get()
    # EgonTE.configure(font=(chosen_font, chosen_size))

    size = font.Font(EgonTE, EgonTE.cget('font'))
    size.configure(size=chosen_size)
    # config
    EgonTE.tag_configure('size', font=size)
    current_tags = EgonTE.tag_names('sel.first')
    EgonTE.tag_add('size', 'sel.first', 'sel.last')

    # EgonTE.tag_delete('size')


# align Left func
def align_left(event=None):
    text_content = EgonTE.get('sel.first', 'sel.last')
    EgonTE.tag_config("left", justify=LEFT)
    EgonTE.delete('sel.first', 'sel.last')
    EgonTE.insert(INSERT, text_content, "left")


# Align Center func
def align_center(event=None):
    text_content = EgonTE.get('sel.first', 'sel.last')
    EgonTE.tag_config("center", justify=CENTER)
    EgonTE.delete('sel.first', 'sel.last')
    EgonTE.insert(INSERT, text_content, "center")


# Align Right func
def align_right(event=None):
    text_content = EgonTE.get('sel.first', 'sel.last')
    EgonTE.tag_config("right", justify=RIGHT)
    EgonTE.delete('sel.first', 'sel.last')
    EgonTE.insert(INSERT, text_content, "right")


def status(event=None):
    global text_changed
    if EgonTE.edit_modified():
        text_changed = True
        words = len(EgonTE.get(1.0, "end-1c").split())
        characters = len(EgonTE.get(1.0, "end-1c"))
        status_bar.config(text=f'Characters:{characters} Words: {words}')
    EgonTE.edit_modified(False)


def text_to_speech():
    global tts
    tts = pyttsx3.init()
    content = EgonTE.get('sel.first', 'sel.last')
    tts.say(content)
    tts.runAndWait()


def read_text(**kwargs):
    global engine
    if 'EgonTE' in kwargs:
        ttr = kwargs['EgonTE']
    else:
        ttr = EgonTE.get(1.0, 'end')  # get EgonTE content
    engine = pyttsx3.init()
    engine.say(ttr)
    engine.runAndWait()
    engine.stop()


def text_formatter(phrase):
    interrogatives = ('how', 'why', 'what', 'when', 'who', 'where', 'is', 'do you', "whom", "whose")
    capitalized = phrase.capitalize()
    if phrase.startswith(interrogatives):
        return f'{capitalized}?'
    else:
        return f'{capitalized}.'


def speech_to_text():
    error_msg = "Excuse me, I don't know what you mean!"
    recolonize = speech_recognition.Recognizer()  # initialize the listener
    mic = speech_recognition.Microphone()
    with mic as source:  # set listening device to microphone
        read_text(text='Please say the message you would like to the EgonTE editor!')
        recolonize.pause_threshold = 1
        audio = recolonize.listen(source)
    try:
        query = recolonize.recognize_google(audio, language='en-UK')  # listen to audio
        query = text_formatter(query)
    except Exception:
        read_text(text=error_msg)
        if tkinter.messagebox.askyesno('EgonTE', 'are you want to try again?'):
            query = speech_to_text()
        else:
            read_text(text='ok, I will try to do my best next time!')
    EgonTE.insert(INSERT, query, END)
    return query


def exit_app():
    if tkinter.messagebox.askyesno('Quit', 'Are you wish to exit?'):
        root.quit()
        engine.stop()
        tts.stop()
        exit()

def find_text():
    search_text = tkinter.simpledialog.askstring("Find","Enter Text")
    text_data = EgonTE.get('1.0',END+'-1c')
    occurs = text_data.lower().count(search_text.lower())
    if text_data.lower().count(search_text.lower()):
        search_label = tkinter.messagebox.showinfo("Result:", f"{search_text} has {str(occurs)} occurrences")
    else:
        search_label = tkinter.messagebox.showinfo("Result:", "No match found")

# create toolbar frame
toolbar_frame = Frame(root)
toolbar_frame.pack(fill=X)
# create main frame
frame = Frame(root)
frame.pack(pady=5)
# Font Box
font_tuple = font.families()
font_family = StringVar()
font_box = ttk.Combobox(toolbar_frame, width=30, textvariable=font_family, state="readonly")
font_box["values"] = font_tuple
font_box.current(font_tuple.index("Arial"))
font_box.grid(row=0, column=4, padx=5)

# Size Box
size_var = IntVar()
size_var.set(16)
font_size = ttk.Combobox(toolbar_frame, width=5, textvariable=size_var, state="readonly")
font_size["values"] = tuple(range(8, 80, 2))
font_size.current(4)  # 16 is at index 5
font_size.grid(row=0, column=5, padx=5)
# create scrollbar for the EgonTE box
text_scroll = Scrollbar(frame)
text_scroll.pack(side=RIGHT, fill=Y)
# horizontal scrollbar
horizontal_scroll = Scrollbar(frame, orient='horizontal')
horizontal_scroll.pack(side=BOTTOM, fill=X)
# create EgonTE box
# chosen font?
EgonTE = Text(frame, width=100, height=30, font=(chosen_font, chosen_size), selectbackground='blue',
              selectforeground='white',
              undo=True
              , yscrollcommand=text_scroll.set, xscrollcommand=horizontal_scroll.set, wrap=WORD, relief=FLAT, cursor=
              'tcross')
EgonTE.focus_set()
EgonTE.pack(fill=BOTH, expand=True)
# config scrollbar
text_scroll.config(command=EgonTE.yview)
horizontal_scroll.config(command=EgonTE.xview)
# create menu
menu = Menu(frame)
root.config(menu=menu)
# file menu
file_menu = Menu(menu, tearoff=False)
menu.add_cascade(label='File', menu=file_menu)
file_menu.add_command(label='New', command=new_file)
file_menu.add_command(label='Open', accelerator='ctrl+o', command=open_file)
file_menu.add_command(label='Save', command=save, accelerator='ctrl+s')
file_menu.add_command(label='Save As', command=save_as)
file_menu.add_separator()
file_menu.add_command(label='Print file', command=print_file)
file_menu.add_separator()
file_menu.add_command(label='Exit', command=exit_app)
# edit menu
edit_menu = Menu(menu, tearoff=False)
menu.add_cascade(label='Edit', menu=edit_menu)
edit_menu.add_command(label='Cut', accelerator='ctrl+x', command=lambda: cut('nothing'))
edit_menu.add_command(label='Copy', accelerator='ctrl+c', command=lambda: copy('nothing'))
edit_menu.add_command(label='Paste', accelerator='ctrl+v', command=lambda: paste('nothing'))
edit_menu.add_separator()
edit_menu.add_command(label='Undo', accelerator='ctrl+z', command=EgonTE.edit_undo)
edit_menu.add_command(label='Redo', accelerator='ctrl+y', command=EgonTE.edit_redo)
edit_menu.add_separator()
edit_menu.add_command(label='Select All', accelerator='ctrl+a', command=lambda: select_all('nothing'))
edit_menu.add_command(label='Clear', accelerator='', command=clear)
edit_menu.add_separator()
edit_menu.add_command(label="Find Text", command=find_text)

# color menu
color_menu = Menu(menu, tearoff=False)
menu.add_cascade(label='colors', menu=color_menu)
color_menu.add_command(label='change selected text', command=text_color)
color_menu.add_command(label='change all text', command=all_txt_color)
color_menu.add_separator()
color_menu.add_command(label='background', command=bg_color)
color_menu.add_command(label='highlight', command=hl_color)
# options menu
options_menu = Menu(menu, tearoff=False)
menu.add_cascade(label='options', menu=options_menu)

# add status bar to bottom add
status_bar = Label(root, text='Ready')
status_bar.pack(fill=X, side=BOTTOM, ipady=5)

# edit keybindings
root.bind("<Control-o>", open_file)
root.bind('<Control-Key-x>', cut)
root.bind('<Control-Key-v>', paste)
root.bind('<Control-Key-c>', copy)
root.bind('<Control-Key-s>', save)
root.bind('<Control-Key-a>', select_all)
root.bind('<Control-Key-b>', bold)
root.bind('<Control-Key-i>', italics)
root.bind('<Control-Key-u>', underline)
root.bind('<Control-Key-l>', align_left)
root.bind('<Control-Key-e>', align_center)
root.bind('<Control-Key-r>', align_right)

root.bind("<<ComboboxSelected>>", change_font)
root.bind("<<ComboboxSelected>>", change_font_size)
root.bind("<<Modified>>", status)
# buttons creation and placement
bold_button = Button(toolbar_frame, image=bold_img, command=bold, relief=FLAT)
bold_button.grid(row=0, column=0, sticky=W, padx=2)

italics_button = Button(toolbar_frame, image=italics_img, command=italics, relief=FLAT)
italics_button.grid(row=0, column=1, sticky=W, padx=2)

underline_button = Button(toolbar_frame, image=underline_img, command=underline, relief=FLAT)
underline_button.grid(row=0, column=2, sticky=W, padx=2)

color_button = Button(toolbar_frame, image=colors_img, command=text_color, relief=FLAT)
color_button.grid(row=0, column=3, padx=5)

align_left_button = Button(toolbar_frame, image=align_left_img, relief=FLAT)
align_left_button.grid(row=0, column=6, padx=5)

# align center button
align_center_button = Button(toolbar_frame, image=align_center_img, relief=FLAT)
align_center_button.grid(row=0, column=7, padx=5)

# align right button
align_right_button = Button(toolbar_frame, image=align_right_img, relief=FLAT)
align_right_button.grid(row=0, column=8, padx=5)

# tts button
tts_button = Button(toolbar_frame, image=tts_img, relief=FLAT,
                    command=lambda: threading.Thread(target=text_to_speech).start(),
                    )
tts_button.grid(row=0, column=9, padx=5)

# boolean tk vars
show_statusbar = BooleanVar()
show_statusbar.set(True)

show_toolbar = BooleanVar()
show_toolbar.set(True)

night_mode = BooleanVar()

# check marks
options_menu.add_checkbutton(label="night mode", onvalue=True, offvalue=False,
                             variable=night_mode, compound=LEFT, command=night)
options_menu.add_checkbutton(label="Status Bar", onvalue=True, offvalue=False,
                             variable=show_statusbar, compound=LEFT, command=hide_statusbar)
options_menu.add_checkbutton(label="Tool Bar", onvalue=True, offvalue=False,
                             variable=show_toolbar, compound=LEFT, command=hide_toolbar)

# talk button
talk_button = Button(toolbar_frame, image=talk_img, relief=FLAT,
                     command=lambda: threading.Thread(target=speech_to_text).start())
talk_button.grid(row=0, column=10, padx=5)

# buttons config
align_left_button.configure(command=align_left)
align_center_button.configure(command=align_center)
align_right_button.configure(command=align_right)

# opening sentence
op_msgs = ['hello world!', '^-^', 'what a beautiful day!', 'welcome!', '', 'believe in yourself!',
           'if I did it you can do way more than that', 'don\'t give up!']
op_msg = random.choice(op_msgs)
EgonTE.insert(END, op_msg)

# bind and make tooltips
tip.bind_widget(bold_button, balloonmsg='Bold (ctrl+u)')
tip.bind_widget(italics_button, balloonmsg='italics (ctrl+i)')
tip.bind_widget(underline_button, balloonmsg='underline (ctrl+u)')
tip.bind_widget(align_left_button, balloonmsg='align left (ctrl+l)')
tip.bind_widget(align_center_button, balloonmsg='align center (ctrl+e)')
tip.bind_widget(align_right_button, balloonmsg='align right (ctrl+r)')

root.mainloop()

# contact - reedit = arielo_o
