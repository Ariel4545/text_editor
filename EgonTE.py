from tkinter import filedialog, colorchooser, font, ttk, messagebox, simpledialog
from tkinter import *
from tkinter.tix import *
from win32print import GetDefaultPrinter
from win32api import ShellExecute, GetShortPathName
import pyttsx3
from threading import Thread
import pyaudio  # imported to make speech_recognition work
from random import choice, randint, random
from speech_recognition import Recognizer, Microphone
from sys import exit as exit_
from datetime import datetime
from webbrowser import open as open_
import names
from googletrans import Translator  # req version 3.1.0a0

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

LOGO = PhotoImage(file='ETE_icon.png')
root.iconphoto(False, LOGO)

global open_status_name
open_status_name = False
global chosen_font
global selected
global cc
text_changed = False
chosen_font = ('arial', 16)

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
    EgonTE.delete("1.0", END)
    file_bar.config(text='New file')

    global open_status_name
    open_status_name = False


# open file func
def open_file(event=None):
    global name
    EgonTE.delete("1.0", END)
    text_file = filedialog.askopenfilename(initialdir='C:/EgonTE/', title='Open file'
                                           , filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html'),
                                                        ('Python Files', '*.py')))
    if text_file:
        global open_status_name
        open_status_name = text_file
    name = text_file
    file_bar.config(text=f'Opened file: {GetShortPathName(name)}')
    name.replace('C:/EgonTE/', '')
    name.replace('C:/users', '')
    text_file = open(text_file, 'r')
    stuff = text_file.read()
    EgonTE.insert(END, stuff)
    text_file.close()


# save as func
def save_as(event=None):
    global name
    if event == None:
        text_file = filedialog.asksaveasfilename(defaultextension=".*", initialdir='C:/EgonTE', title='Save File',
                                                 filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html'),
                                                            ('Python Files', '*.py')))
        if text_file:
            name = text_file
            name = name.replace('C:/EgonTE', '')
            file_bar.config(text=f'Saved: {name} - {get_time()}')

            text_file = open(text_file, 'w')
            text_file.write(EgonTE.get(1.0, END))
            text_file.close()
    if event == 'get name':
        try:
            return name
        except NameError:
            messagebox.showerror('error', 'You cant copy a file name if you doesn\'t use a file ')


# save func
def save(event=None):
    global open_status_name, name
    if open_status_name:
        text_file = open(open_status_name, 'w')
        text_file.write(EgonTE.get(1.0, END))
        text_file.close()
        file_bar.config(text=f'Saved: {(name)} - {get_time()}')
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


# make the text underline func
def underline(event=None):
    # create
    underline_font = font.Font(EgonTE, EgonTE.cget('font'))
    underline_font.configure(underline=True)
    # config
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
        try:
            current_tags = EgonTE.tag_names('sel.first')
            if 'colored_txt' in current_tags:
                EgonTE.tag_remove('colored_txt', 'sel.first', 'sel.last')

            else:
                EgonTE.tag_add('colored_txt', 'sel.first', 'sel.last')
        except:
            messagebox.showerror('error', 'didn\'t selected text')


# background color func
def bg_color():
    selected_color = colorchooser.askcolor()[1]
    if selected_color:
        EgonTE.config(bg=selected_color)


# all color txt func
def all_txt_color(event=None):
    color = colorchooser.askcolor()[1]
    if color:
        EgonTE.config(fg=color)


# highlight color func
def hl_color():
    color = colorchooser.askcolor()[1]
    if color:
        EgonTE.config(selectbackground=color)


# print file func
def print_file(event=None):
    printer_name = GetDefaultPrinter()
    file2p = filedialog.askopenfilename(initialdir='C:/EgonTE/', title='Open file'
                                        , filetypes=(('Text Files', '*.txt'), ('HTML FILES', '*.html'),
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
        horizontal_scroll.pack_forget()
        text_scroll.pack_forget()
        toolbar_frame.pack(fill=X, anchor=W)
        text_scroll.pack(side=RIGHT, fill=Y)
        horizontal_scroll.pack(side=BOTTOM, fill=X)
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
        font_box.config(foreground=_text_color)
        font_size.config(foreground=_text_color)
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
        font_box.config(foreground=_text_color)
        font_size.config(foreground=_text_color)
        night_mode = True


# WIP
def change_font(event=None):
    global chosen_font
    chosen_font = font_family.get()
    # # wb font tuple
    # # config
    EgonTE.configure(font=chosen_font)
    # EgonTE.config(font=sfont)
    # EgonTE.tag_configure('font', font=chosen_font)
    # EgonTE.tag_config(font=(chosen_font, font_size))


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
        EgonTE.tag_add('size', '1.0', END)


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


# get & display character and word count with status bar
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


# force the app to quit
def exit_app():
    if messagebox.askyesno('Quit', 'Are you wish to exit?'):
        root.quit()
        exit_()
        quit()
        exit()


# find if text exists in the specific file
def find_text(event=None):
    search_text = simpledialog.askstring("Find", "Enter Text")
    text_data = EgonTE.get('1.0', END + '-1c')
    occurs = text_data.lower().count(search_text.lower())
    if text_data.lower().count(search_text.lower()):
        search_label = messagebox.showinfo("EgonTE:", f"{search_text} has {str(occurs)} occurrences")
    else:
        search_label = messagebox.showinfo("EgonTE:", "No match found")


def ins_calc():
    def enter_button():
        equation = Ce.get()
        try:
            equation = eval(equation)
        except:
            messagebox.showerror('error', 'didn\'t type valid characters')
        equation = str(equation) + ' '
        EgonTE.insert(get_pos(), equation)
        Croot.destroy()

    def show_oper():
        global add_sub, mul_div, pow_
        Croot.geometry('150x155')
        show_op.config(text='hide operations', command=hide_oper)
        add_sub = Label(Croot, text='+ addition, - subtraction')
        mul_div = Label(Croot, text='* multiply, / deviation')
        pow_ = Label(Croot, text='** power, % modulus')
        add_sub.grid(row=4)
        mul_div.grid(row=5)
        pow_.grid(row=6)

    def hide_oper():
        Croot.geometry('150x90')
        add_sub.grid_forget()
        mul_div.grid_forget()
        pow_.grid_forget()
        show_op.config(text='show operations', command=show_oper)

    Croot = Toplevel(relief=FLAT)
    Croot.resizable(False, False)
    Croot.geometry('150x90')
    introduction_text = Label(Croot, text='Enter equation below:')
    enter = Button(Croot, text='Enter', command=enter_button, relief=FLAT)
    Ce = Entry(Croot, relief=RIDGE, justify='center')
    show_op = Button(Croot, text='Show operators', relief=FLAT, command=show_oper)
    introduction_text.grid(row=0)
    Ce.grid(row=1)
    enter.grid(row=2)
    show_op.grid(row=3)


def dt():
    EgonTE.insert(get_pos(), get_time() + ' ')


def ins_random():
    def enter_button_custom():
        global num_1, num_2
        try:
            try:
                num_1 = int(Ce1.get())
                num_2 = int(Ce2.get())
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

    Croot = Toplevel()
    Croot.resizable(False, False)
    Croot.geometry('300x100')
    introduction_text = Label(Croot, text='Enter numbers below:', justify='center')
    sub_c = Button(Croot, text='submit custom', command=enter_button_custom, relief=FLAT)
    sub_qf = Button(Croot, text='submit quick float', command=enter_button_quick_float, relief=FLAT)
    sub_qi = Button(Croot, text='submit quick int', command=enter_button_quick_int, relief=FLAT)
    Ce1 = Entry(Croot, relief=RIDGE, justify='center')
    Ce2 = Entry(Croot, relief=RIDGE, justify='center')
    bt_text = Label(Croot, text='<->')
    introduction_text.grid(row=0, columnspan=1)
    Ce1.grid(row=1, column=0, columnspan=2)
    bt_text.grid(row=1, column=1)
    Ce2.grid(row=1, column=2)
    sub_c.grid(row=2, column=0, columnspan=1)
    sub_qf.grid(row=3, column=0, columnspan=2)
    sub_qi.grid(row=3, column=1, columnspan=2)


def copy_file_path():
    # global selected
    file_name = save_as(event='get name')
    root.clipboard_clear()
    root.clipboard_append(file_name)


def custom_cursor():
    global cc
    if not cc:
        EgonTE.config(cursor='tcross')
        cc = True
    else:
        EgonTE.config(cursor='arrow')
        cc = False


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


# still W.I.P
def ins_random_name():
    global random_name

    def button():
        global random_name
        EgonTE.insert(get_pos(), random_name + ' ')

    def roll(event):
        global random_name
        if event == 'simple':
            random_name = names.get_full_name()
        elif event == 'advance':
            pass
        name.config(text=random_name)

    # UI
    def adv_option():
        global gender, types, random_name
        adv_frame = Frame(Nroot)
        t = StringVar()
        g = StringVar()
        gender = ttk.Combobox(Nroot, width=13, textvariable=g, state='readonly', font=('arial', 10, 'bold'), )
        gender['values'] = ('Male', 'Female')
        types = ttk.Combobox(Nroot, width=13, textvariable=t, state='readonly', font=('arial', 10, 'bold'), )
        types['values'] = ('Full Name', 'First Name', 'Last Name')
        # does get to the types
        print(types['values'], gender['values'])
        gender.grid(row=6, column=0)
        types.grid(row=7, column=0)
        adv_options.grid_forget()

        # mechanical function
        def adv_random_name():
            re_roll.config(command=lambda: roll('advance'))
            # not getting into the func! / check more about ['values']
            Gender = gender.get()
            Type = types.get()
            print(Type, Gender)
            # not getting into the conditions
            if Gender == 'Male' and Type == "Full Name":
                random_name = names.get_full_name(gender="male")
                print(random_name)
                return random_name
            elif Gender == 'Male' and Type == "First Name":
                random_name = names.get_first_name()
                return random_name
            elif Gender == 'Male' and Type == "Last Name":
                random_name = names.get_last_name()
                return random_name

            elif Gender == 'Female' and Type == "Full Name":
                random_name = names.get_full_name(gender="female")
                return random_name
            elif Gender == 'Female' and Type == "First Name":
                random_name = names.get_first_name()
                return random_name
            elif Gender == 'Female' and Type == "Last Name":
                random_name = names.get_last_name()
                return random_name

        random_name = adv_random_name()
        print(random_name)

    Nroot = Toplevel()
    Nroot.resizable(False, False)
    bs_frame = Frame(Nroot)
    random_name = names.get_full_name()
    text = Label(Nroot, text='Random name that generated:')
    name = Label(Nroot, text=random_name)
    enter = Button(Nroot, text='Submit', command=button)
    re_roll = Button(Nroot, text='Re-roll', command=lambda: roll('simple'))
    adv_options = Button(Nroot, text='Advance options', command=adv_option, state=DISABLED)
    text.grid(row=1)
    name.grid(row=2)
    enter.grid(row=3)
    re_roll.grid(row=4)
    adv_options.grid(row=5)


def translate():
    def button():
        to_translate = t1.get("1.0", "end-1c")
        cl = choose_langauge.get()

        if to_translate == '':
            messagebox.showerror('Error', 'Please fill the box')
        else:
            translator = Translator()
            output = translator.translate(to_translate, dest=cl)
            EgonTE.insert(get_pos(), output.text)

    Lroot = Toplevel()
    Lroot.geometry('252x246')
    Lroot.resizable(False, False)
    a = StringVar()
    auto_detect = ttk.Combobox(Lroot, width=20, textvariable=a, state='readonly', font=('arial', 10, 'bold'), )

    auto_detect['values'] = (
        'Auto Detect',
    )
    l = StringVar()
    choose_langauge = ttk.Combobox(Lroot, width=20, textvariable=l, state='readonly', font=('arial', 10, 'bold'))
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

    t1 = Text(Lroot, width=30, height=10, borderwidth=5, relief=RIDGE)
    button_ = Button(Lroot, text="Translate", relief=FLAT, borderwidth=3, font=('arial', 10, 'bold'), cursor='tcross',
                     command=button)
    auto_detect.grid(row=0)
    choose_langauge.grid(row=1)
    t1.grid(row=2)
    button_.grid(row=3)


# classic styled
style = ttk.Style()
style.theme_use('clam')
frame = Frame(root)
frame.pack(pady=5)
# create toolbar frame
toolbar_frame = Frame(frame)
toolbar_frame.pack(fill=X, anchor=W)
# Font Box
font_tuple = font.families()
font_family = StringVar()
font_box = ttk.Combobox(toolbar_frame, width=30, textvariable=font_family, state=DISABLED)
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
# create vertical scrollbar
text_scroll = ttk.Scrollbar(frame)
text_scroll.pack(side=RIGHT, fill=Y)
# create horizontal scrollbar
horizontal_scroll = ttk.Scrollbar(frame, orient='horizontal')
horizontal_scroll.pack(side=BOTTOM, fill=X)
# create EgonTE box
# ( chosen font - testing W.I.P )
EgonTE = Text(frame, width=100, height=30, font=chosen_font, selectbackground='blue',
              selectforeground='white',
              undo=True
              , yscrollcommand=text_scroll.set, xscrollcommand=horizontal_scroll.set, wrap=WORD, relief=RIDGE, cursor=
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
file_menu.add_command(label='New', accelerator='(ctrl+n)', command=new_file)
file_menu.add_command(label='Open', accelerator='(ctrl+o)', command=open_file)
file_menu.add_command(label='Save', command=save, accelerator='(ctrl+s)')
file_menu.add_command(label='Save As', command=save_as)
file_menu.add_separator()
file_menu.add_command(label='Print file', accelerator='(ctrl+p)', command=print_file)
file_menu.add_separator()
file_menu.add_command(label='Copy path', command=copy_file_path)
file_menu.add_separator()
file_menu.add_command(label='Exit', command=exit_app)
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
edit_menu.add_command(label='Clear', accelerator='(ctrl+del)', command=clear)
edit_menu.add_separator()
edit_menu.add_command(label="Find Text", accelerator='(ctrl+f)', command=find_text)
# tools menu
tool_menu = Menu(menu, tearoff=False)
menu.add_cascade(label='tools', menu=tool_menu)
tool_menu.add_command(label='Calculation', command=ins_calc)
tool_menu.add_command(label='Current datetime', command=dt)
tool_menu.add_command(label='Random number', command=ins_random)
tool_menu.add_command(label='Random name', command=ins_random_name)
tool_menu.add_command(label='Translate', command=translate)
# color menu
color_menu = Menu(menu, tearoff=False)
menu.add_cascade(label='colors', menu=color_menu)
color_menu.add_command(label='Change selected text', command=text_color)
color_menu.add_command(label='Change all text', command=all_txt_color)
color_menu.add_separator()
color_menu.add_command(label='Background', command=bg_color)
color_menu.add_command(label='Highlight', command=hl_color)
# options menu
options_menu = Menu(menu, tearoff=False)
menu.add_cascade(label='options', menu=options_menu)
# github page
github_menu = Menu(menu, tearoff=False)
menu.add_cascade(label='GitHub', command=github)
# add status bar to bottom add
status_bar = Label(root, text='Characters:0 Words:0')
status_bar.pack(fill=X, side=LEFT, ipady=5)
# add file bar
file_bar = Label(root, text='')
file_bar.pack(fill=X, side=RIGHT, ipady=5)
# edit keybindings
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
root.bind("<<ComboboxSelected>>", change_font)
root.bind("<<ComboboxSelected>>", change_font_size)
root.bind("<<Modified>>", status)
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
options_menu.add_checkbutton(label="Custom cursor", onvalue=True, offvalue=False
                             , compound=LEFT, command=custom_cursor, variable=cc)

options_menu.add_checkbutton(label="Custom style", onvalue=True, offvalue=False
                             , compound=LEFT, command=custom_style, variable=cs)

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

# bind and make tooltips
TOOL_TIP.bind_widget(bold_button, balloonmsg='Bold (ctrl+b)')
TOOL_TIP.bind_widget(italics_button, balloonmsg='Italics (ctrl+i)')
TOOL_TIP.bind_widget(color_button, balloonmsg='Change colors')
TOOL_TIP.bind_widget(underline_button, balloonmsg='Underline (ctrl+u)')
TOOL_TIP.bind_widget(align_left_button, balloonmsg='Align left (ctrl+l)')
TOOL_TIP.bind_widget(align_center_button, balloonmsg='Align center (ctrl+e)')
TOOL_TIP.bind_widget(align_right_button, balloonmsg='Align right (ctrl+r)')
TOOL_TIP.bind_widget(tts_button, balloonmsg='Text to speach')
TOOL_TIP.bind_widget(talk_button, balloonmsg='Speach to talk')
root.mainloop()

# contact - reedit = arielo_o, discord - Arielp2#4011
