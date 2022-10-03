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
import pandas

# window creation
root = Tk()
width = 1250
height = 830
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
placement_x = round((screen_width / 2) - (width / 2))
placement_y = round((screen_height / 2) - (height / 2))
root.geometry(f'{width}x{height}+{placement_x}+{placement_y}')
root.title('Egon Text editor')
root.resizable(False, False)

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
text_changed = False

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

# create toll tip, for the toolbar buttons (with shortcuts)
TOOL_TIP = Balloon(root)


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
        messagebox.showerror('error', 'File not found')


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
    if not x:
        selected = root.clipboard_get()
        if EgonTE.selection_get():
            # grab
            selected = EgonTE.selection_get()
            root.clipboard_clear()
            root.clipboard_append(selected)


# paste func
def paste(x):
    global selected
    if not x:
        selected = root.clipboard_get()
    else:
        if selected:
            EgonTE.insert(get_pos(), selected)


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
    if show_statusbar:
        status_bar.pack_forget()
        file_bar.pack_forget()
        root.geometry(f'{width}x{height - 10}')
        show_statusbar = False
    else:
        status_bar.pack(side=LEFT)
        file_bar.pack(side=RIGHT)
        root.geometry(f'{width}x{height}')
        show_statusbar = True


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


# WIP
def change_font_size(event=None):
    global chosen_size
    chosen_size = size_var.get()
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
    EgonTE.delete('sel.first', 'sel.last')
    EgonTE.insert(INSERT, text_content, "left")



# Align Center func
def align_center(event=None):
    if is_marked():
        text_content = EgonTE.get('sel.first', 'sel.last')
    else:
        EgonTE.tag_add('sel', 'insert linestart', 'insert lineend')
        text_content = EgonTE.get('insert linestart', 'insert lineend')
    EgonTE.tag_config("center", justify=CENTER)
    EgonTE.delete('sel.first', 'sel.last')
    EgonTE.insert(INSERT, text_content, "center")


# Align Right func
def align_right(event=None):
    if is_marked():
        text_content = EgonTE.get('sel.first', 'sel.last')
    else:
        EgonTE.tag_add('sel', 'insert linestart', 'insert lineend')
        text_content = EgonTE.get('insert linestart', 'insert lineend')
    EgonTE.tag_config("right", justify=RIGHT)
    EgonTE.delete('sel.first', 'sel.last')
    EgonTE.insert(INSERT, text_content, "right")


# get & display character and word count with status bar
def status(event=None):
    global text_changed
    if EgonTE.edit_modified():
        text_changed = True
        words = len(EgonTE.get(1.0, "end-1c").split())
        characters = len(EgonTE.get(1.0, "end-1c"))
        status_bar.config(text=f'Characters:{characters} Words: {words}')
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
        ttr = EgonTE.get(1.0, 'end')  # get EgonTE content
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
        global cpt_settings, by_characters
        text_data = EgonTE.get('1.0', END + '-1c')
        # by word/character settings
        if by_characters:
            pass
        else:
            text_data = text_data.split(' ')
        # capitalize settings
        if cpt_settings == 'unc':
            text_data_ = text_data.lower()
            entry_data = text_entry.get().lower()
            occurs = text_data_.count(entry_data)
            if text_data_.count(entry_data):
                search_label = messagebox.showinfo("EgonTE:", f"{entry_data} has {str(occurs)} occurrences")
            else:
                search_label = messagebox.showinfo("EgonTE:", "No match found")
        elif cpt_settings == 'c':
            occurs = text_data.count(text_entry.get())
            if text_data.count(text_entry.get()):
                search_label = messagebox.showinfo("EgonTE:", f"{text_entry.get()} has {str(occurs)} occurrences")
            else:
                search_label = messagebox.showinfo("EgonTE:", "No match found")

    # window
    search_text_root = Tk()
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


# insert mathematics calculation to the text box
def ins_calc():
    def enter_button():
        equation = clac_entry.get()
        try:
            equation = eval(equation)
        except SyntaxError:
            messagebox.showerror('error', 'didn\'t type valid characters')
        except NameError:
            messagebox.showerror('error', 'tool does not support variables')
        equation = str(equation) + ' '
        EgonTE.insert(get_pos(), equation)
        clac_root.destroy()

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


# insert the current date & time to the text box
def dt():
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
                messagebox.showerror('error', 'didn\'t type valid characters')
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


def copy_file_path(event=None):
    # global selected
    file_name_ = save_as(event='get name')
    root.clipboard_clear()
    root.clipboard_append(file_name_)


# change between the default and custom cursor
def custom_cursor():
    global cc
    if not cc:
        EgonTE.config(cursor='tcross')
        cc = True
    else:
        EgonTE.config(cursor='arrow')
        cc = False


# change between the default and custom style
def custom_style():
    global cs
    if not cs:
        style.theme_use('clam')
        EgonTE.config(relief=RIDGE)
        cs = True
    else:
        style.theme_use('vista')
        EgonTE.config(relief=FLAT)
        cs = False


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

    # window
    translate_root = Toplevel()
    translate_root.geometry('252x246')
    translate_root.resizable(False, False)
    # string variables
    auto_detect_string = StringVar()
    languages = StringVar()
    # combo box
    auto_detect = ttk.Combobox(translate_root, width=20, textvariable=auto_detect_string, state='readonly',
                               font=('arial', 10, 'bold'), )

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
    translate_box = Text(translate_root, width=30, height=10, borderwidth=5, relief=RIDGE)
    button_ = Button(translate_root, text="Translate", relief=FLAT, borderwidth=3, font=('arial', 10, 'bold'),
                     cursor='tcross',
                     command=button)
    # placing the objects in the window
    auto_detect.grid(row=0)
    choose_langauge.grid(row=1)
    translate_box.grid(row=2)
    button_.grid(row=3)


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
            messagebox.showerror('error', 'Please Paste an  invalid url')

    enter.config(command=shorter)


def font_helvetica():
    delete_tags()
    EgonTE.config(font=('Helvetica', 16))


def font_courier():
    delete_tags()
    EgonTE.config(font=('Courier', 16))


def font_times():
    delete_tags()
    EgonTE.config(font=('Times', 16))


def font_arial():
    delete_tags()
    EgonTE.config(font=('Arial', 16))


def font_corbel():
    delete_tags()
    EgonTE.config(font=('Corbel', 16))


def font_modern():
    delete_tags()
    EgonTE.config(font=('Modern', 16))


def font_marlett():
    delete_tags()
    EgonTE.config(font=('Marlett', 16))


def font_rod():
    delete_tags()
    EgonTE.config(font=('Rod', 16))


def font_symbol():
    delete_tags()
    EgonTE.config(font=('Symbol', 16))


def reverse_characters(event=None):
    content = EgonTE.get(1.0, END)
    reversed_content = content[::-1]
    EgonTE.delete(1.0, END)
    EgonTE.insert(1.0, reversed_content)


def reverse_words(event=None):
    content = EgonTE.get(1.0, END)
    words = content.split()
    reversed_words = words[::-1]
    EgonTE.delete(1.0, END)
    EgonTE.insert(1.0, reversed_words)


def join_words(event=None):
    content = EgonTE.get(1.0, END)
    words = content.split()
    joined_words = ''.join(words)
    EgonTE.delete(1.0, END)
    EgonTE.insert(1.0, joined_words)


def lower_upper(event=None):
    content = EgonTE.get(1.0, END)
    if content == content.upper():
        content = content.lower()
    else:
        content = content.upper()
    EgonTE.delete(1.0, END)
    EgonTE.insert(1.0, content)


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


def size_up_shortcut(event=None):
    global font_Size_c
    font_Size_c += 1
    try:
        font_size.current(font_Size_c)
        change_font_size()
    except Exception:
        messagebox.showerror('error', 'font size at maximum')


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
            EgonTE.config(bg=selected_second_color, fg=selected_text_color)
            toolbar_frame.config(bg=selected_main_color)


# checks if text in the main text box is being marked
def is_marked():
    if EgonTE.tag_ranges('sel'):
        return True
    else:
        return False


# tags and configurations of the same thing is clashing all the time \:
def delete_tags():
    EgonTE.tag_delete('bold', 'underline', 'italics', 'size', 'colored_txt')


def special_files_import(file_type):
    pandas.options.display.max_rows = 9999
    special_file = filedialog.askopenfilename(title='open \'special\' special_file', filetypes=(('excel', '*.xlsx'),
                                              ('json', '*.json'), ('xml', '*.xml'), ('csv', '*.csv')))
    if special_file:
        try:
            if file_type == 'excel':
                content = pandas.read_excel(special_file).to_string()
            elif file_type == 'csv':
                content = pandas.read_csv(special_file).to_string()
            elif file_type == 'json':
                content = pandas.read_json(special_file).to_string()
            elif file_type == 'xml':
                content = pandas.read_xml(special_file).to_string()
            EgonTE.insert('end', content)
        except:
            messagebox.showerror('error', 'wrong match between selected special_file to special_file\'s type')


# add custom style
style = ttk.Style()
style.theme_use('clam')
frame = Frame(root)
frame.pack(pady=5)
# create toolbar frame
toolbar_frame = Frame(frame)
toolbar_frame.pack(fill=X, anchor=W)

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

# create text box
EgonTE = Text(frame, width=100, height=30, font=('arial', 16), selectbackground='blue',
              selectforeground='white',
              undo=True,
              yscrollcommand=text_scroll.set, wrap=WORD, relief=RIDGE,
              cursor='tcross')
EgonTE.focus_set()
EgonTE.pack(fill=BOTH, expand=True)
# config scrollbar
text_scroll.config(command=EgonTE.yview)
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
edit_menu.add_separator()
edit_menu.add_command(label='Replace', accelerator='(ctrl+h)', command=replace)
edit_menu.add_separator()
edit_menu.add_command(label='Reverse characters', accelerator='(ctrl+shift+c)', command=reverse_characters)
edit_menu.add_command(label='Reverse words', accelerator='(ctrl+shift+r)', command=reverse_words)
edit_menu.add_command(label='Join words', accelerator='(ctrl+shift+j)', command=join_words)
edit_menu.add_command(label='Upper/Lower', accelerator='(ctrl+shift+u)', command=lower_upper)
# tools menu
tool_menu = Menu(menu, tearoff=False)
menu.add_cascade(label='Tools', menu=tool_menu)
tool_menu.add_command(label='Calculation', command=ins_calc)
tool_menu.add_command(label='Current datetime', command=dt)
tool_menu.add_command(label='Random number', command=ins_random)
tool_menu.add_command(label='Random name', command=ins_random_name)
tool_menu.add_command(label='Translate', command=translate)
tool_menu.add_command(label='Url shorter', command=url)
tool_menu.add_command(label='Generate sequence', command=generate)
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
# fonts menu
font_menu = Menu(menu, tearoff=False)
menu.add_cascade(label="Fonts", menu=font_menu)
helvetica = IntVar()
courier = IntVar()
font_menu.add_checkbutton(label="Arial", command=font_arial)
font_menu.add_checkbutton(label="Courier", command=font_courier)
font_menu.add_checkbutton(label="Helvetica", command=font_helvetica)
font_menu.add_checkbutton(label="Times New Roman", command=font_times)
font_menu.add_checkbutton(label="Corbel", command=font_corbel)
font_menu.add_checkbutton(label="Modern", command=font_modern)
font_menu.add_checkbutton(label="marlett", command=font_marlett)
font_menu.add_checkbutton(label="symbol", command=font_symbol)
# options menu
options_menu = Menu(menu, tearoff=False)
menu.add_cascade(label='Options', menu=options_menu)
# github page
github_menu = Menu(menu, tearoff=False)
menu.add_cascade(label='GitHub', command=github)
# add status bar
status_bar = Label(root, text='Characters:0 Words:0')
status_bar.pack(fill=X, side=LEFT, ipady=5)
# add file bar
file_bar = Label(root, text='')
file_bar.pack(fill=X, side=RIGHT, ipady=5)
# add shortcuts
root.bind("<Control-o>", open_file)
root.bind("<Control-O>", open_file)
root.bind('<Control-Key-x>', cut)
root.bind('<Control-Key-X>', cut)
root.bind('<Control-Key-v>', paste)
root.bind('<Control-Key-V>', paste)
root.bind('<Control-Key-c>', copy)
root.bind('<Control-Key-C>', copy)
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
# special events
root.bind('<<ComboboxSelected>>', change_font_size)
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

# boolean tk vars
show_statusbar = BooleanVar()
show_statusbar.set(True)

show_toolbar = BooleanVar()
show_toolbar.set(True)

night_mode = BooleanVar()

cc = BooleanVar()
cc.set(True)

cs = BooleanVar()
cs.set(True)

# check marks
options_menu.add_checkbutton(label="Night mode", onvalue=True, offvalue=False,
                             compound=LEFT, command=night)
options_menu.add_checkbutton(label="Status Bar", onvalue=True, offvalue=False,
                             variable=show_statusbar, compound=LEFT, command=hide_statusbars)
options_menu.add_checkbutton(label="Tool Bar", onvalue=True, offvalue=False,
                             variable=show_toolbar, compound=LEFT, command=hide_toolbar)
options_menu.add_checkbutton(label="Custom cursor", onvalue=True, offvalue=False,
                             compound=LEFT, command=custom_cursor, variable=cc)

options_menu.add_checkbutton(label="Custom style", onvalue=True, offvalue=False,
                             compound=LEFT, command=custom_style, variable=cs)

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
menus_components = [file_menu, edit_menu, tool_menu, color_menu, font_menu, options_menu]
other_components = [root, status_bar, file_bar, EgonTE, toolbar_frame]

root.mainloop()

# contact - reedit = arielo_o, discord - Arielp2#4011
