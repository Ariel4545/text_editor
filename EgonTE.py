# default libraries
from dependencies.large_variables import *
from dependencies.universal_functions import *
from UI import ui_builders
from pop_ups.handwriting_popup import open_handwriting
from pop_ups.encryption_popup import open_encryption
from pop_ups.find_replace_popup import open_find_replace
from pop_ups.file_template_generator_popup import open_document_template_generator
from pop_ups.git_tool_popup import open_git_tool
from pop_ups.web_scrapping_popup import open_web_scrapping_popup
from pop_ups.nlp_popup import open_nlp
from pop_ups.email_popup import open_email
from pop_ups.ai_popups import open_chatgpt, open_dalle
from UI.library_installer_ui import show_library_installer
from tkinter import filedialog, colorchooser, font, messagebox, simpledialog
from tkinter import *
import tkinter.ttk as ttk
import subprocess
from sys import exit as exit_
import sys
from sys import executable, argv
import ssl
from socket import gethostname
from collections import Counter
from itertools import islice
import os
from random import choice, randint, random, shuffle
import time
from re import findall, sub, compile, IGNORECASE, escape
from re import search as reSearch
from re import split as reSplit
from json import dump, load, loads
from platform import system
from ctypes import windll, c_int, byref, sizeof
from heapq import nlargest
from threading import Thread
from string import ascii_letters, digits, ascii_lowercase, ascii_uppercase, printable, punctuation
from smtplib import SMTP_SSL
from datetime import datetime, timedelta
from io import BytesIO
from importlib import util
from pathlib import Path
import queue

def library_installer(parent: Misc | None = None) -> dict:
	"""
	Top-level installer entry point.
	- parent: optional Tk widget to parent the dialog; pass a window or frame if you have one.
			  If None, the installer will create its own root (standalone mode).
	Returns the result dict from show_library_installer.
	"""
	# Use a copy so we never mutate module-level lists
	required = list(library_list)
	optional = list(library_optional)

	# If no parent was provided, try to use the default Tk root if one exists.
	# Otherwise the installer will create its own root window.
	if parent is None:
		try:
			parent = _get_default_root()
		except Exception:
			parent = None

	return show_library_installer(
		parent=parent if isinstance(parent, Misc) else None,
		base_libraries=required,
		optional_libraries=optional,
		allow_upgrade_pip=True,
		allow_optional=bool(optional),
		title='ETE - Install Required',
		# Normalization + checks (all data lives in large_variables.py)
		alias_map=library_alias_map,
		blocklist=library_blocklist,
		pins=library_pins,
		skip_installed=True,
	)



# required libraries that aren't by default

req_lib = False
try:
	import pytesseract.pytesseract
	from win32print import GetDefaultPrinter  # install pywin32
	from win32api import ShellExecute, GetShortPathName
	from pyttsx3 import init as ttsx_init
	import pyaudio  # imported to make speech_recognition work
	from speech_recognition import Recognizer, Microphone, AudioFile, WaitTimeoutError # install SpeechRecognition
	import webbrowser
	import names
	import urllib.request, urllib.error
	from urllib.parse import urlparse
	import requests
	# matplotlib (graphs library) in a way that suits tkinter
	import matplotlib

	matplotlib.use('TkAgg')
	from matplotlib.figure import Figure
	from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
	import pandas
	from pyperclip import copy
	import emoji
	from wikipedia import summary, exceptions, page
	from wikipedia import search as wiki_search
	from difflib import Differ, SequenceMatcher
	from textblob import TextBlob
	from PyPDF2 import PdfReader
	from bs4 import BeautifulSoup
	from spacy.matcher import Matcher
	from PIL import ImageGrab, Image, ImageTk, UnidentifiedImageError
	import spacy  # download also en_core_web_sm - https://spacy.io/usage
	from pydub import AudioSegment
	from keyboard import is_pressed

	global translate_root, sort_root
	from spacy.cli import download as nlp_download
	from nltk.corpus import words
	from PyDictionary import PyDictionary
	import numexpr
	# import autocomplete
	from fast_autocomplete import AutoComplete

	req_lib = True

except (ModuleNotFoundError) as e:
	print(e)
	library_installer()

'''the optional libraries that can add a lot of extra content to the editor'''
tes = ACTIVE
try:
	from pytesseract import image_to_string  # download https://github.com/UB-Mannheim/tesseract/wiki
except:
	tes = DISABLED
try:
	from youtube_transcript_api import YouTubeTranscriptApi

	yt_api = True
except (ImportError, AttributeError, ModuleNotFoundError) as e:
	yt_api = False
try:
	from emoticon import emoticon, demoticon

	emoticons_library = ACTIVE
except (ImportError, AttributeError, ModuleNotFoundError) as e:
	emoticons_library = DISABLED

try:
	from polyglot.text import Text as poly_text

	RA = True
except (ImportError, ModuleNotFoundError) as e:
	RA = False

try:
	from googletrans import Translator  # req version 3.1.0a0

	google_trans = True
	deep_trans = ''
except (ImportError, AttributeError, ModuleNotFoundError) as e:
	google_trans = ''


symmetric_dec = True
try:
	from cryptography.fernet import Fernet
except (ImportError, AttributeError, ModuleNotFoundError) as e:
	symmetric_dec = False

asymmetric_dec = True
try:
	import rsa
except (ImportError, AttributeError, ModuleNotFoundError) as e:
	asymmetric_dec = False

enc_tool = symmetric_dec or asymmetric_dec

try:
	from pyshorteners import Shortener

	short_links = True
except (ImportError, AttributeError, ModuleNotFoundError) as e:
	short_links = False

try:
	from tktooltip import ToolTip
	neo_tt = True
except:
	neo_tt = False
	import tkinter.tix as tkt

try:
	from tkhtmlview import HTMLText, RenderHTML
	html_infop = 'html'
except:
	html_infop = 'txt'

try:
	from docx.shared import Mm
	from docxtpl import DocxTemplate, InlineImage
except:
	pass

# window creation
class Window(Tk):
	def __init__(self):
		global frame

		super().__init__()

		'''
		variables of the program that have connection to the a saving file of their values
		'''
		# advance settings main variables
		self.bars_active = BooleanVar()
		self.show_statusbar, self.show_toolbar = BooleanVar(), BooleanVar()
		self.night_mode = BooleanVar()
		self.custom_cursor_v = StringVar()
		self.cs = StringVar()
		self.word_wrap_v = BooleanVar()
		self.reader_mode_v = BooleanVar()
		self.auto_save_v = BooleanVar()
		self.corrector_check_changes = BooleanVar()
		self.usage_report_v = BooleanVar()
		self.check_ver_v = BooleanVar()
		self.check_ver_v.set(True)
		self.win_count_warn = BooleanVar()
		self.win_count_warn.set(True)
		self.adw = BooleanVar()
		self.fun_numbers = BooleanVar()
		self.fun_numbers.set(True)
		self.all_tm_v = BooleanVar()
		self.status_ = True
		self.file_ = True
		self.last_file_v = BooleanVar()
		self.textwist_special_chars = BooleanVar()
		self.nm_palette = StringVar()
		# auto save methods
		self.autosave_by_p = BooleanVar()
		self.autosave_by_t = BooleanVar()
		self.autosave_by_p.set(True), self.autosave_by_t.set(True)
		'''
		variables of the program that doesn't save when you close the program
		'''
		# don't included in the saved settings
		self.sta, self.automatic_emojis_v = BooleanVar(), BooleanVar()
		self.sta.set(True), self.automatic_emojis_v.set(True)
		# dev variables
		self.prefer_gpu, self.python_file, self.auto_clear_c, self.sar = BooleanVar(), '', BooleanVar(), BooleanVar()
		self.dev_mode = BooleanVar()
		self.auto_clear_c.set(True), self.dev_mode.set(False)
		# basic file variables
		self.file_name, self.open_status_name = '', ''
		self.text_changed = False
		self.egon_dir = BooleanVar()
		# OpenAI's tools variables (mainly GPT but also dall-e)
		self.openai_code, self.gpt_model, self.key = False, 'gpt-3.5-turbo', ''
		# handwriting
		self.cimage_from = ''
		# search/find text variables
		self.auto_focus_v = BooleanVar()
		self.highlight_search_c = 'blue', 'white'
		# bottom frame
		self.status_var = StringVar()
		self.status_var.set('Lines:1 Characters:0 Words:0')
		# variables based on if windows are opened or not to prevent errors while using settings
		self.info_page_active, self.vk_active, self.search_active, self.record_active = False, False, False, False
		self.hw_active, self.op_active, self.ins_images_open, self.hw_bonus_root = False, False, False, None
		# wiki and dictionary variables
		self.wiki_var = IntVar()
		self.wiki_var.set(1)
		# speech to text variables
		self.stt_chosen_lang = StringVar()
		self.stt_chosen_lang.set('English (US)')
		self.stt_lang_value = 'en-US'
		# background variables (not used that much)
		self.bg_count = 1
		self.save_bg = BooleanVar()
		# insert image
		self.image_name = ''
		self.in_images_list_n, self.in_images_dict = [], {}
		# window management
		self.limit_w_s, self.open_middle_s = BooleanVar(), BooleanVar()
		self.limit_w_s.set(True), self.open_middle_s.set(True)
		self.fs_value, self.tm_value, self.st_value = False, False, 0.95
		self.opened_windows, self.limit_list, self.func_window = [], [], {}
		# draw to text variables
		self.line_group, self.line_groups, self.last_items, self.line, self.lgs_dict, self.lg_dict = [], [], [], '', {}, {}
		self.move_dict = {'right': [10, 0], 'left': [-10, 0], 'up': [0, -10], 'down': [0, 10]}
		self.mw_shortcut, self.draw_tool_cords = BooleanVar(), BooleanVar()
		self.mw_shortcut.set(True)
		# shortcuts vars
		self.bindings_dict = {'filea': filea_list, 'typea': typef_list, 'editf': editf_list, 'textt': textt_list,
							  'windf': win_list, 'autof': autof_list}
		self.file_actions_v, self.typefaces_actions_v, self.edit_functions_v, self.texttwisters_functions_v, self.win_actions_v, self.auto_functions, \
			self.aul = [BooleanVar() for x in range(7)]
		self.file_actions_v.set(True), self.typefaces_actions_v.set(True), self.edit_functions_v.set(True)
		self.texttwisters_functions_v.set(True), self.win_actions_v.set(True), self.auto_functions.set(True)
		self.binding_work = {'textt': self.texttwisters_functions_v, 'filea': self.file_actions_v,
							 'typea': self.typefaces_actions_v,
							 'editf': self.edit_functions_v, 'windf': self.win_actions_v, 'autof': self.auto_functions,
							 'autol': self.aul}
		# other tools
		self.del_previous_file = BooleanVar()
		self.chosen_text_decorator = 'bash'
		self.fnt_sz_var = IntVar()
		self.tab_type = 'spaces'
		self.capital_opt, self.by_characters = BooleanVar(), BooleanVar()
		self.capital_opt.set(True), self.by_characters.set(True)
		self.indent_method = StringVar()
		self.indent_method.set('tab')
		self.find_tool_searched = BooleanVar()
		self.menu_pop = BooleanVar()
		self.content_preference_v = StringVar()
		self.content_preference_v.set('html')
		# opening the saved settings early can make us create some widgets with the settings initially
		try:
			self.default_needed = self.saved_settings()
			saved_settings_viable = True
		except KeyError:
			saved_settings_viable = False
			if messagebox.askyesno('EgonTE',
								   'There is key-error with the saved settings\ndo you wish to reset the file?'):
				if os.path.exists('EgonTE_settings.json'):
					os.remove('EgonTE_settings.json')
					print('Corrupted file has been reset - program needed to be closed for that')
					self.exit_app()
		if saved_settings_viable:
			if self.default_needed:
				self.bars_active.set(True), self.show_statusbar.set(True), self.show_toolbar.set(True)
				self.custom_cursor_v.set('xterm'), self.cs.set('clam')
				self.word_wrap_v.set(True)
				self.auto_save_v.set(True)
				self.nm_palette.set('black')
				# pre-defined variables for the options of the program
				self.predefined_cursor, self.predefined_style, self.predefined_relief = 'xterm', 'clam', 'ridge'

		self.last_cursor = 'cursors', self.custom_cursor_v.get()
		self.last_style = 'styles', self.cs.get()
		self.last_r = 'relief', self.predefined_relief

		# default resolution & placement of the window
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
		self.ver = '1.13.2'
		self.title(f'Egon Text editor - {self.ver}')
		# function thats loads all the toolbar images
		self.load_images()
		# connecting the prees of the exit button the a custom exit function
		self.protocol('WM_DELETE_WINDOW', self.exit_app)
		# threads for a stopwatch function that works on advance option window and a function that loads images from the web
		self.start_stopwatch()
		# Thread(target=self.load_links, daemon=True).start()
		self.load_links()
		# variables for the (UI) style of the program
		self.titles_font = '@Microsoft YaHei Light', 16, 'underline'
		self.title_struct = 'EgonTE - '
		self.style_combobox = ttk.Style(self)

		# set of condition that check if you have the tesseract executable
		global tes
		if tes == ACTIVE:
			try:
				if not (os.path.exists(r'Tesseract-OCR\tesseract.exe')):
					pytesseract.pytesseract.tesseract_cmd = (r'C:\Program Files\Tesseract-OCR\tesseract.exe')
				print('pytesseract - initial steps completed')
			except:
				tes = DISABLED

		# create toll tip, for the toolbar buttons (with shortcuts)
		# TOOL_TIP = Balloon(self)

		# add custom style
		self.style = ttk.Style()
		self.style.theme_use(self.predefined_style)
		frame = Frame(self)
		frame.pack(expand=True, fill=BOTH, padx=15)

		# create toolbar frame
		self.toolbar_frame = Frame(frame)
		self.toolbar_frame.pack(fill=X, anchor=W, side=TOP)
		self.ex_tool = 'arial 9 bold'
		self.record_list = [f'> [{get_time()}] - Program opened']

		# font UI (combo box) and it's values
		font_tuple = font.families()
		self.font_family = StringVar()
		self.font_ui = ttk.Combobox(self.toolbar_frame, width=30, textvariable=self.font_family, state='readonly',
									style='TCombobox', values=font_tuple)
		self.font_ui.current(font_tuple.index('Arial'))
		# font's size UI (combo box) and it's values
		self.size_var = IntVar()
		self.size_var.set(16)
		self.font_size = ttk.Combobox(self.toolbar_frame, width=5, textvariable=self.size_var, state='readonly',
									  style='TCombobox', values=tuple(reversed(range(8, 80, 2))))
		self.font_Size_c = 31
		self.font_size.current(self.font_Size_c)  # 16 is at index 31
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
						   cursor=self.predefined_cursor, xscrollcommand=self.horizontal_scroll.set)
		self.EgonTE.focus_set()
		self.EgonTE.pack(fill=BOTH, expand=True)
		# config scrollbars
		self.text_scroll.config(command=self.EgonTE.yview)
		self.horizontal_scroll.config(command=self.EgonTE.xview)
		# create main menu's component
		self.app_menu = Menu(frame)
		self.config(menu=self.app_menu)

		self._popup = ui_builders.UIBuilders(self)
		self.make_pop_ups_window = self._popup.make_pop_ups_window

		self.load_function_links()
		self.menu_assests()
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
			self.last_file_v.set(True)
			if isinstance(self.data['open_last_file'], str):
				if os.path.exists(self.data['open_last_file']):
					self.open_file(event='initial')
					insert_lf = True

		'''+
		add to function
		add the same thing for light mode
		add a conditions to prevent os error
		'''

		# buttons creation and placement
		buttons_list = ((self.BOLD_IMAGE, lambda: self.typefaces(tf='weight-bold')),
						(self.ITALICS_IMAGE, lambda: self.typefaces(tf='slant-italic')),
						(self.UNDERLINE_IMAGE, lambda: self.typefaces(tf='underline')),
						(self.COLORS_IMAGE, self.text_color),
						(self.ALIGN_LEFT_IMAGE, self.align_text),
						(self.ALIGN_CENTER_IMAGE, lambda: self.align_text('center')),
						(self.ALIGN_RIGHT_IMAGE, lambda: self.align_text('right')),
						(self.TTS_IMAGE, lambda: Thread(target=self.text_to_speech).start()),
						(self.STT_IMAGE, lambda: self.after(0, self.start_speech_to_text)),
						(self.KEY_IMAGE, lambda: Thread(target=self.virtual_keyboard()).start()),
						(self.DTT_IMAGE, lambda: self.open_windows_control(self.handwriting)),
						(self.CALC_IMAGE, lambda: self.open_windows_control(self.ins_calc)))
		self.bold_button, self.italics_button, self.underline_button, self.color_button, self.align_left_button, \
			self.align_center_button, self.align_right_button, self.tts_button, self.talk_button, self.v_keyboard_button, \
			self.dtt_button, self.calc_button = [
			Button(self.toolbar_frame, image=b_image, command=b_command, relief=FLAT)
			for b_image, b_command in buttons_list]
		# ui tuples (and list) to make management of some UI events (like night mode) easier
		self.toolbar_components = [
			self.bold_button, self.italics_button, self.underline_button, self.color_button, self.font_ui,
			self.font_size,
			self.align_left_button, self.align_center_button, self.align_right_button, self.tts_button,
			self.talk_button,
			self.v_keyboard_button, self.dtt_button, self.calc_button]
		pdx, r = 5, 0
		for index, button in enumerate(self.toolbar_components):
			padx, sticky = 2, W
			if index > 2:
				padx, sticky = 5, ''
			button.grid(row=0, column=index, sticky=sticky, padx=padx)

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

		# ui tuples (and list) to make management of some UI events (like night mode) easier
		self.menus_components = [self.file_menu, self.edit_menu, self.tool_menu, self.color_menu, self.options_menu, \
								 self.nlp_menu, self.links_menu]
		self.other_components = self, self.status_bar, self.file_bar, self.EgonTE, self.toolbar_frame
		''' not used'''
		self.determine_highlight()
		if self.night_mode.get():
			self.night()
		else:
			self.dynamic_overall = 'SystemButtonFace'
			self.dynamic_text = 'black'
			self.dynamic_bg = 'SystemButtonFace'
			self.dynamic_button = 'SystemButtonFace'

		self.place_toolt()
		self.binds(mode='initial')
		self.stt_time = get_time()
		# Thread(target=self.record_logs, daemon=False).start()
		# self.record_logs()
		self.singular_colors_d = {'background': [self.EgonTE, 'bg'], 'text': [self.EgonTE, 'fg'],
								  'menus': [self.menus_components, 'bg-fg'],
								  'buttons': [self.toolbar_components, 'bg'], 'highlight': [self.EgonTE, 'selectbackground']}

		self.setup_auto_lists()
		if RA:
			self.right_align_language_support()
		if self.check_ver_v.get():
			self.after_idle(self.check_version)

	def load_images(self):
		'''
		loads UI's local images (for toolbar buttons) and assigning them to variables
		'''

		# buttons' icons - size=32x32 pixels
		image_names = (
			'bold', 'underline', 'italics', 'colors', 'left_align', 'center_align', 'right_align', 'tts', 'stt',
			'keyboard', 'drawToText_icon', 'calc_icon')
		self.BOLD_IMAGE, self.UNDERLINE_IMAGE, self.ITALICS_IMAGE, self.COLORS_IMAGE, self.ALIGN_LEFT_IMAGE, self.ALIGN_CENTER_IMAGE \
			, self.ALIGN_RIGHT_IMAGE, self.TTS_IMAGE, self.STT_IMAGE, self.KEY_IMAGE, self.DTT_IMAGE, self.CALC_IMAGE = \
			[PhotoImage(file=f'new_assests/{image_name}.png', master=self) for image_name in image_names]

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


	def load_function_links(self):
		self.file_functions = {'new file|(ctrl+n)': self.new_file, 'open file|(ctrl+o)': self.open_file,
							   'save|(ctrl+s)': self.save,
							   'save as': self.save_as,
							   'delete file': self.delete_file, 'change file type': self.change_file_ui,
							   'new window': new_window,
							   'screenshot content.': lambda: self.save_images(self.EgonTE, self, self.toolbar_frame,
																			   'main')
			, 'file\'s info': self.file_info, 'content stats!': self.content_stats, 'file\'s comparison': self.compare,
							   'merge files.': self.merge_files,
							   'print file|(ctrl+p).': self.print_file, 'copy file path|(ctrl+d).': self.copy_file_path,
							   'import local file!': self.special_files_import,
							   'import global file.': lambda: self.special_files_import('link'),
							   'exit|(alt+F4)': self.exit_app, 'restart': lambda: self.exit_app(event='r'),
							   }
		self.edit_functions = {'cut|(ctrl+x)': self.cut, 'copy|(ctrl+c)': self.copy, 'paste|(ctrl+v).': self.paste,
							   'correct writing': self.corrector, 'organize writing.': self.organize,
							   'undo|(ctrl+z)': self.EgonTE.edit_undo, 'redo|(ctrl+y).': self.EgonTE.edit_redo,
							   'select all|(ctrl+a)': self.select_all, 'clear all|(ctrl+del).': self.clear,
							   'find text|(ctrl+f)': self.find_replace,
							   'replace|(ctrl+h)': self.replace, 'go to|(ctrl+g).': self.goto,
							   'reverse characters|(ctrl+c)': self.reverse_characters,
							   'reverse words|(ctrl+c)': self.reverse_words, 'join words|(ctrl+c)': self.join_words,
							   'upper/lower|(ctrl+c)': self.lower_upper,
							   'sort by characters': self.sort_by_characters, 'sort by words.': self.sort_by_words,
							   'clipboard history.': self.clipboard_history, 'insert images': self.insert_image
							   }
		self.tool_functions = {'translate': self.translate, 'current datetime|(F5)': get_time(),
							   'random numbers': self.ins_random, 'random names': self.ins_random_name,
							   'url shorter': self.url,
							   'generate sequence': self.generate, 'search online': self.search_www,
							   'sort input': self.sort,
							   'dictionary': lambda: Thread(target=self.knowledge_window('dict'), daemon=True).start(),
							   'wikipedia!': lambda: Thread(target=self.knowledge_window('wiki'), daemon=True).start(),
							   'web scrapping!': self.web_scrapping, 'text decorators': self.text_decorators,
							   'inspirational quote': self.insp_quote, 'get weather': self.get_weather,
							   'send email': self.send_email,
							   'use chatgpt': self.chatGPT, 'use dalle': self.dallE, 'transcript': self.transcript,
							   'symbols translator': self.emojicons_hub, 'encryption \ decryption': self.encryption,
							   'Generate document' : self.file_template_generator
							   }

		self.nlp_functions = {
			'Get nouns': lambda: self.natural_language_process(function='nouns'),
			'Get verbs': lambda: self.natural_language_process(function='verbs'),
			'Get adjectives': lambda: self.natural_language_process(function='adjective'),
			'Get adverbs': lambda: self.natural_language_process(function='adverbs'),
			'Get pronouns': lambda: self.natural_language_process(function='pronouns'),
			'Get stop words': lambda: self.natural_language_process(function='stop words'),

			'.Entity recognition': lambda: self.natural_language_process(function='entity recognition'),
			'Dependency tree': lambda: self.natural_language_process(function='dependency'),
			'Lemmatization': lambda: self.natural_language_process(function='lemmatization'),
			'Most common words': lambda: self.natural_language_process(function='most common words'),

			'.Get names (persons)': lambda: self.natural_language_process(function='FULL_NAME'),
			'Get phone numbers': lambda: self.natural_language_process(function='PHONE_NUMBER'),
			'Extract emails': lambda: self.natural_language_process(function='EMAILS'),
			'Extract URLs': lambda: self.natural_language_process(function='URLS'),
			'Extract IP addresses': lambda: self.natural_language_process(function='IP_ADDRESSES'),

			'.Key phrases (noun chunks)': lambda: self.natural_language_process(function='KEY_PHRASES'),
			'N-grams (2–3)': lambda: self.natural_language_process(function='NGRAMS'),
			'Sentence split': lambda: self.natural_language_process(function='SENTENCE_SPLIT'),
			'POS distribution': lambda: self.natural_language_process(function='POS_DISTRIBUTION'),
			'Sentiment (VADER)': lambda: self.natural_language_process(function='SENTIMENT'),
		}

		self.color_functions = {'whole text': lambda: self.custom_ui_colors(components='text')
					, 'background': lambda: self.custom_ui_colors(components='background')
					, 'highlight.': lambda: self.custom_ui_colors(components='highlight_color')
					, 'buttons color': lambda: self.custom_ui_colors(components='buttons')
					, 'menus color': lambda: self.custom_ui_colors(components='menus')
					, 'app colors.': lambda: self.custom_ui_colors(components='app')
					, 'info page colors': lambda: self.custom_ui_colors(components='info page')
					, 'virtual keyboard colors': lambda: self.custom_ui_colors(components='v_keyboard'),
										'advance options colors': lambda: self.custom_ui_colors(components='advance_options')
										}

		self.settings_fuctions = {'Night mode': (self.night, self.night_mode),
								  'status bars': (self.hide_statusbars, self.show_statusbar),
								  'tool bar': (self.hide_toolbar, self.show_toolbar), 'custom cursor': (
				self.custom_cursor, 'tcross', 'xterm'), 'custom style': (self.custom_style, 'vista', 'clam'
																		 ), 'word wrap': (self.word_wrap, self.word_wrap_v),
								  'reader mode': (self.reader_mode,), 'auto save': (self.save_outvariables, self.auto_save_v),
								  'top most': (self.topmost,), 'automatic emoji detection': (self.automatic_emojis_v,),
								  # variable only
								  'dev mode': (lambda: self.manage_menus(mode='dev'),),
								  'special tools': (lambda: self.manage_menus(mode='tools'), self.sta),
								  'fun numbers.': (self.save_outvariables, self.fun_numbers),
								  'advance options': self.call_settings}

		self.other_functions = {'advance options': self.call_settings, 'help': lambda: self.info_page('help'),
								'patch notes': lambda: self.info_page('patch_notes')}
		self.links_functions = {'github link': lambda: self.ex_links('g'), 'discord link': lambda: self.ex_links('d')}

		self.conjoined_functions_only = {'file': self.file_functions, 'edit': self.edit_functions,
										 'tools': self.tool_functions,
										 'NLP': self.nlp_functions, 'colors': self.color_functions,
										 'options': self.call_settings,
										 'Help': lambda: self.open_windows_control(lambda: self.info_page('help')),
										 'Patch notes': lambda: self.open_windows_control(
											 lambda: self.info_page('patch_notes'))
			, 'Search': self.search_functions, 'links': self.links_functions}
		self.conjoined_functions_dict = self.conjoined_functions_only
		self.conjoined_functions_dict['options'] = self.settings_fuctions

	def menu_assests(self):
		''' a one time menu initializer, to prevent attributes and variables duplication'''
		self.file_menu, self.edit_menu, self.tool_menu, self.nlp_menu, self.color_menu, self.links_menu, self.options_menu = \
			[Menu(self.app_menu, tearoff=False) for x in range(7)]
		self.menus_list = [self.tool_menu, self.nlp_menu, self.color_menu, self.links_menu, self.options_menu]

	def create_menus(self, initial: bool):
		'''
		a function that creates the UI's menus and helps to manage them because it's option to create specific
		menus after some are deleted because of its initial parameter
		'''

		if not (initial):
			chosen_functions_dict = {key: val for key, val in self.conjoined_functions_dict.items() if
									 key not in ('file', 'edit')}
		else:
			chosen_functions_dict = self.conjoined_functions_dict
			self.menus_list = [self.file_menu, self.edit_menu] + self.menus_list

			'''+ loop of the commands - probably reverse this 
			3. fix namings

			5. fix list index - menu list

			BONUS:
			made also modes for non initials: use the specific "menu_content" with a conditional chosen name
			'''
		# newer
		index = 0
		for menu_name, menu_content in (chosen_functions_dict.items()):
			menu = self.menus_list[index]
			if isinstance(menu_content, dict) or isinstance(menu_content, list):
				index += 1
				self.app_menu.add_cascade(label=menu_name.capitalize(), menu=menu)
				for name, function in menu_content.items():
					separator = False
					font = ('Segoe UI', 9)
					name, acc = name.capitalize(), ''

					if any(x in name for x in ('.', '!', '|')):
						if '.' in name:
							separator = True
						if '!' in name:
							font = 'arial 9 bold'
						name = name.replace('.', '', 1).replace('!', '', 1)
						if '|' in name:
							name, acc = name.split('|')

					if isinstance(function, tuple):
						if len(function) > 1:
							if isinstance(function[1], BooleanVar):
								menu.add_checkbutton(label=name, command=function[0], variable=function[1])
							else:
								if [item for item in function if isinstance(item, BooleanVar)]:
									menu.add_checkbutton(label=name, command=function[0], variable=function[1],
														 onvalue=function[2],
														 offvalue=function[3])
								else:
									menu.add_checkbutton(label=name, command=function[0], onvalue=function[1],
														 offvalue=function[2])
						else:
							function = function[0]
							if isinstance(function, BooleanVar) or isinstance(function, bool):
								menu.add_checkbutton(label=name, variable=function)
							else:
								menu.add_checkbutton(label=name, command=function)

					else:
						menu.add_command(label=name, accelerator=acc, command=function, font=font)

					if separator:
						menu.add_separator()

			else:
				self.app_menu.add_cascade(label=menu_name, command=menu_content)
				index -= 1

	def place_toolt(self, *args, **kwargs):
		'''
			   placing tooltips with a function gives us the ability to be in charge of more settings
			   '''
		return self._popup.place_toolt(*args, **kwargs)


	def binds(self, mode='initial'):
		return self._popup.binds(mode)

	def unbind_group(self, mode):
		return self._popup.unbind_group(mode)

	def reset_binds(self):
		return self._popup.reset_binds()



	def open_windows_control(self, func, *args, **kwargs):
		return self._popup.open_windows_control(func, *args, **kwargs)



	def get_pos(self) -> str:
		'''
		return the index of your text pointer in the main text box
		'''
		return self.EgonTE.index(INSERT)


	def undo(self):
		try:
			return self.EgonTE.edit_undo()
		except TclError:
			pass


	def get_file(self, mode='open', message=''):
		'''+ global filedialog function that use return

		in-effective because we need a brief way to integrate every file extensions type
		'''
		if mode == 'open':
			file = filedialog.askopenfilename(title=f'{mode}{message} file', filetypes=text_extensions)
		elif mode == 'new':
			file = filedialog.asksaveasfilename(defaultextension='.*', initialdir='C:/EgonTE', title='Save File',
													 filetypes=text_extensions)
		return file


	def new_file(self, event=None):
		'''
		creates blank workspace (without file)
		'''
		if check_file_changes(self.file_name, self.EgonTE.get('1.0', 'end')):
			self.file_name = ''
			self.file_bar.config(text='New file')
			self.EgonTE.delete('1.0', END)
			self.open_status_name = ''
			self.record_list.append(f'> [{get_time()}] - New black file opened')

	def open_file(self, event=None):
		'''
		opens file, have special support also for html and python files
		'''


		content = self.EgonTE.get('1.0', 'end')
		if event == 'initial':
			self.text_name = self.data['open_last_file']

		else:
			self.text_name = self.get_file('Open')

		if check_file_changes(self.file_name, self.EgonTE.get('1.0', 'end')):
			if self.text_name:
				try:
					self.EgonTE.delete('1.0', END)
					self.open_status_name = self.text_name
					self.file_name = self.text_name
					self.file_bar.config(text=f'Opened file: {GetShortPathName(self.file_name)}')
					'''+ add a special mode to redirect the files to and egon library
					
					make it in the users document library
					'''
					if self.egon_dir.get():
						self.file_name.replace('', 'C:/EgonTE/')
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
						if self.dev_mode.get():
							self.options_menu.delete(15)
						else:
							self.options_menu.delete(14)
					# make the html files formatted when opened
					if self.file_name.endswith('.html'):
						self.soup = BeautifulSoup(stuff, 'html')
						stuff = self.soup.prettify()
					# adds functionality to compile python in EgonTE
					elif self.file_name.endswith('.py'):
						self.python_file = True
						self.output_frame, self.output_box, self.output_scroll = self.make_rich_textbox(frame, size=[100, 1]
									, selectbg='blue', wrap=None, font='arial 12', bd=2)
						self.output_box.configure(state='disabled')
					self.manage_menus(mode='python')

					self.EgonTE.insert(END, stuff)
					text_file.close()

					if self.data['open_last_file']:
						self.save_last_file()

					self.record_list.append(f'> [{get_time()}] - Opened {self.file_name}')

				except UnicodeDecodeError:
					messagebox.showerror(self.title_struct + 'error', 'File contains not supported characters')
					self.EgonTE.insert('1.0', content) # kind of revert mechanism
			else:
				messagebox.showerror(self.title_struct + 'error', 'File not found / selected')

	# save file as function
	def save_as(self, event=None):
		'''
		saves file by new location that the user will give it
		'''
		if event == None:
			text_file = filedialog.asksaveasfilename(defaultextension='.*', initialdir='C:/EgonTE', title='Save File',
													 filetypes=text_extensions)
			if text_file:
				self.file_name = text_file
				self.file_name = self.file_name.replace('C:/EgonTE', '')
				self.file_bar.config(text=f'Saved: {self.file_name} - {get_time()}')

				text_file = open(text_file, 'w')
				text_file.write(self.EgonTE.get(1.0, END))
				text_file.close()

				if self.data['open_last_file']:
					self.save_last_file()

				self.record_list.append(f'> [{get_time()}] - Saved {text_file}')

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
		if self.open_status_name:
			text_file = open(self.open_status_name, 'w')
			text_file.write(self.EgonTE.get(1.0, END))
			text_file.close()
			self.file_bar.config(text=f'Saved: {self.file_name} - {get_time()}')
			self.record_list.append(f'> [{get_time()}] - Saved {self.file_name}')
		else:
			self.save_as(event=None)

	def cut(self):
		if self.is_marked():
			try:
				selected_text = self.EgonTE.selection_get()
			except Exception:
				selected_text = ""
			if selected_text:
				# delete selection and update clipboard
				self.EgonTE.delete('sel.first', 'sel.last')
				self.clipboard_clear()
				self.clipboard_append(selected_text)
				# sync history
				self.add_to_clipboard_history(selected_text)

	def copy(self, event=None):
		if self.is_marked():
			try:
				selected_text = self.EgonTE.selection_get()
			except Exception:
				selected_text = ""
			if selected_text:
				self.clipboard_clear()
				self.clipboard_append(selected_text)
				try:
					self.update()
				except Exception:
					pass
				# sync history
				self.add_to_clipboard_history(selected_text)

	def paste(self, event=None):
		try:
			text_from_clipboard = self.clipboard_get()
		except BaseException:
			text_from_clipboard = ""
		if text_from_clipboard:
			try:
				self.EgonTE.insert(self.get_pos(), text_from_clipboard)
			except BaseException:
				pass
			# Optionally: do NOT push paste into history here, since it's already there from copy/cut/watcher.
			# If you DO want to ensure it appears at top whenever pasted, uncomment:
			# self.add_to_clipboard_history(text_from_clipboard)

	def right_click_menu(self, event):
		# it's the same pointer so it's ineffective
		right_click_menu = self.clone_menu()
		right_click_menu.delete('Correct writing'), right_click_menu.delete('Organize writing'), right_click_menu.delete(4)
		[right_click_menu.delete(LAST) for i in range(4)]
		# a condition that will prevent duplicate packing of menus

		if not self.menu_pop.get() and event.num == 3:
			x_cord, y_cord = event.x, event.y
			self.active_rc_menu = right_click_menu.tk_popup(event.x_root, event.y_root)

	def clone_menu(self, mode='right click'):
		if mode == 'right click':
			original_menu = self.edit_menu
			commands = tuple(self.edit_functions.values())

		command_index = 0
		new_menu = Menu(self, tearoff=False)
		for index in range(original_menu.index('end') + 1):
			item_type = original_menu.type(index)
			if item_type == 'separator':
				new_menu.add_separator()
			elif item_type == 'command':
				label = original_menu.entrycget(index, 'label')
				new_menu.add_command(label=label, command=commands[command_index])  # command can't be directly retrieved
				command_index += 1
		return new_menu

	def add_to_clipboard_history(self, item_text: str):
		"""Add text to the clipboard history, keeping most recent at index 0 and skipping consecutive duplicates."""
		if not item_text:
			return
		if not hasattr(self, 'copy_list') or self.copy_list is None:
			self.copy_list = []
		max_history_items = getattr(self, 'clipboard_history_capacity', 100)
		text_value = str(item_text)

		# If the same text is already at the top, do nothing
		if self.copy_list and self.copy_list[0] == text_value:
			return

		# If the same text exists elsewhere, move it to the top instead of duplicating
		try:
			existing_index = self.copy_list.index(text_value)
			self.copy_list.pop(existing_index)
			self.copy_list.insert(0, text_value)
		except ValueError:
			self.copy_list.insert(0, text_value)

		# Enforce capacity
		if len(self.copy_list) > max_history_items:
			del self.copy_list[max_history_items:]

	def clipboard_history(self):
		# Ensure storage exists
		if not hasattr(self, 'copy_list') or self.copy_list is None:
			self.copy_list = []
		# Optional: set a capacity for the history
		max_items = getattr(self, 'clipboard_history_capacity', 100)

		# Helpers to manage history
		def add_to_clipboard_history(text: str):
			if not text:
				return
			s = str(text)
			# skip immediate duplicates at the head
			if self.copy_list and self.copy_list[0] == s:
				return
			self.copy_list.insert(0, s)
			# enforce capacity
			if len(self.copy_list) > max_items:
				del self.copy_list[max_items:]
			apply_filter(refresh_list=True)

		# Expose for external use (e.g., copy/cut hooks can call this)
		self.add_to_clipboard_history = add_to_clipboard_history

		# Build the pop-up window with your standardized helper
		root = self.make_pop_ups_window(self.clipboard_history)
		root.title('Clipboard History')
		# root is a tk.Toplevel returned by the helper

		# UI state
		filter_var = StringVar() if hasattr(self, 'tk') else __import__('tkinter').StringVar()
		filtered_view = []  # snapshot of items after filter
		listbox = None
		dragging_model_index = None

		# ---- Data/UI sync helpers ----
		def apply_filter(refresh_list=False):
			nonlocal filtered_view
			q = filter_var.get().strip().lower()
			if q:
				filtered_view = [s for s in self.copy_list if q in s.lower()]
			else:
				filtered_view = list(self.copy_list)
			if refresh_list and listbox is not None:
				listbox.delete(0, 'end')
				for s in filtered_view:
					display = s if len(s) <= 120 else (s[:117] + '...')
					listbox.insert('end', display)

		def get_view_selection():
			sel = listbox.curselection()
			return sel[0] if sel else None

		def get_selected_text():
			idx = get_view_selection()
			if idx is None or not (0 <= idx < len(filtered_view)):
				return None
			return filtered_view[idx]

		def model_index_from_view():
			txt = get_selected_text()
			if txt is None:
				return None
			try:
				return self.copy_list.index(txt)
			except ValueError:
				return None

		def select_model_index(model_idx: int):
			if not (0 <= model_idx < len(self.copy_list)):
				return
			target_value = self.copy_list[model_idx]
			try:
				view_idx = filtered_view.index(target_value)
			except ValueError:
				return
			listbox.selection_clear(0, 'end')
			listbox.selection_set(view_idx)
			listbox.activate(view_idx)
			listbox.see(view_idx)

		# ---- Actions ----
		def do_copy():
			txt = get_selected_text()
			if txt is None:
				return
			try:
				root.clipboard_clear()
				root.clipboard_append(txt)
				root.update_idletasks()
			except Exception:
				pass

		def do_paste():
			# paste into main text area if available
			txt = get_selected_text()
			if txt is None:
				return
			try:
				root.clipboard_clear()
				root.clipboard_append(txt)
			except Exception:
				pass
			try:
				if hasattr(self, 'EgonTE') and self.EgonTE:
					self.EgonTE.insert(self.get_pos(), txt)
			except Exception:
				pass

		def do_delete():
			mi = model_index_from_view()
			if mi is None:
				return
			del self.copy_list[mi]
			apply_filter(refresh_list=True)

		def do_clear():
			self.copy_list.clear()
			apply_filter(refresh_list=True)

		def do_move(delta: int):
			mi = model_index_from_view()
			if mi is None:
				return
			new_idx = max(0, min(len(self.copy_list) - 1, mi + delta))
			if new_idx == mi:
				return
			self.copy_list[mi], self.copy_list[new_idx] = self.copy_list[new_idx], self.copy_list[mi]
			apply_filter(refresh_list=True)
			select_model_index(new_idx)

		def on_activate_row():
			# Default: copy; if text widget exists, also paste
			do_copy()
			if hasattr(self, 'EgonTE') and self.EgonTE:
				do_paste()

		# ---- Drag-and-drop handlers ----
		def on_drag_start(e):
			nonlocal dragging_model_index
			idx = listbox.nearest(e.y)
			if 0 <= idx < listbox.size():
				listbox.selection_clear(0, 'end')
				listbox.selection_set(idx)
				listbox.activate(idx)
				dragging_model_index = model_index_from_view()
			else:
				dragging_model_index = None

		def on_drag_motion(e):
			if dragging_model_index is None:
				return
			idx = listbox.nearest(e.y)
			if 0 <= idx < listbox.size():
				listbox.selection_clear(0, 'end')
				listbox.selection_set(idx)
				listbox.activate(idx)

		def on_drag_release(e):
			nonlocal dragging_model_index
			if dragging_model_index is None:
				return
			drop_view_idx = listbox.nearest(e.y)
			if not (0 <= drop_view_idx < listbox.size()):
				dragging_model_index = None
				return
			target_value = filtered_view[drop_view_idx]
			try:
				new_model_idx = self.copy_list.index(target_value)
			except ValueError:
				dragging_model_index = None
				return
			if new_model_idx != dragging_model_index:
				item = self.copy_list.pop(dragging_model_index)
				self.copy_list.insert(new_model_idx, item)
				apply_filter(refresh_list=True)
				select_model_index(new_model_idx)
			dragging_model_index = None

		# ---- Layout ----
		# Top: filter row
		top = Frame(root)
		top.pack(fill='x', padx=8, pady=(8, 4))
		Label(top, text='Filter:').pack(side='left')
		ent_filter = ttk.Entry(top, textvariable=filter_var, width=30)
		ent_filter.pack(side='left', fill='x', expand=True, padx=(6, 0))
		filter_var.trace_add('write', lambda *_: apply_filter(refresh_list=True))

		# Middle: listbox + scrollbar
		mid = Frame(root)
		mid.pack(fill='both', expand=True, padx=8, pady=4)
		yscroll = ttk.Scrollbar(mid, orient='vertical')
		listbox = __import__('tkinter').Listbox(mid, selectmode='browse', activestyle='dotbox',
												yscrollcommand=yscroll.set)
		yscroll.config(command=listbox.yview)
		listbox.pack(side='left', fill='both', expand=True)
		yscroll.pack(side='right', fill='y')

		# Bottom: control buttons
		btns = Frame(root)
		btns.pack(fill='x', padx=8, pady=(4, 8))
		Button(btns, text='Copy', command=do_copy).pack(side='left')
		Button(btns, text='Paste', command=do_paste).pack(side='left', padx=(6, 0))
		Button(btns, text='Delete', command=do_delete).pack(side='left', padx=(6, 0))
		Button(btns, text='Move Up', command=lambda: do_move(-1)).pack(side='left', padx=(6, 0))
		Button(btns, text='Move Down', command=lambda: do_move(1)).pack(side='left', padx=(6, 0))
		Button(btns, text='Clear All', command=do_clear).pack(side='left', padx=(6, 0))

		# Context menu
		ctx = __import__('tkinter').Menu(root, tearoff=False)
		ctx.add_command(label='Copy', command=do_copy)
		ctx.add_command(label='Paste', command=do_paste)
		ctx.add_separator()
		ctx.add_command(label='Move Up', command=lambda: do_move(-1))
		ctx.add_command(label='Move Down', command=lambda: do_move(1))
		ctx.add_separator()
		ctx.add_command(label='Delete', command=do_delete)
		ctx.add_command(label='Clear All', command=do_clear)

		def show_ctx(e):
			try:
				listbox.selection_clear(0, 'end')
				idx = listbox.nearest(e.y)
				if 0 <= idx < listbox.size():
					listbox.selection_set(idx)
					listbox.activate(idx)
				ctx.tk_popup(e.x_root, e.y_root)
			finally:
				try:
					ctx.grab_release()
				except Exception:
					pass

		# Bindings
		listbox.bind('<Button-3>', show_ctx)  # Right-click
		listbox.bind('<Double-Button-1>', lambda e: on_activate_row())
		listbox.bind('<Return>', lambda e: on_activate_row())
		listbox.bind('<Delete>', lambda e: do_delete())
		listbox.bind('<Control-BackSpace>', lambda e: do_clear())
		listbox.bind('<Control-Up>', lambda e: do_move(-1))
		listbox.bind('<Control-Down>', lambda e: do_move(1))
		root.bind('<Escape>', lambda e: root.destroy())
		root.bind('<Control-l>', lambda e: do_clear())
		root.bind('<Control-f>', lambda e: ent_filter.focus_set())

		# Drag-and-drop
		listbox.bind('<ButtonPress-1>', on_drag_start)
		listbox.bind('<B1-Motion>', on_drag_motion)
		listbox.bind('<ButtonRelease-1>', on_drag_release)

		# Populate initial data and focus
		apply_filter(refresh_list=True)
		if listbox.size() > 0:
			listbox.selection_set(0)
			listbox.activate(0)
		ent_filter.focus_set()

	def typefaces(self, tf: str):
		"""
		Toggle simple typeface styles over the selection (or whole document if no selection).

		Supported:
		  - 'weight-bold'
		  - 'slant-italic'
		  - 'underline'
		  - 'overstrike'
		  - 'normal'  -> clears all the above styles

		Notes:
		- No size or family handling here.
		- Uses the widget's base font as the starting point to keep rendering consistent.
		- Avoids trailing-newline issues by operating up to 'end-1c'.
		"""

		def base_font_copy(widget):
			spec = widget.cget('font')
			try:
				# Works only if spec is a named font
				return font.nametofont(spec).copy()
			except TclError:
				# spec is a literal like 'Arial 16' -> make a Font from it
				return font.Font(widget, font=spec)

		# Normalize selection bounds
		first, last = self.get_indexes()
		if str(last) == END:
			last = 'end-1c'

		STYLE_TAGS = ('weight-bold', 'slant-italic', 'underline', 'overstrike')

		# Clear everything for 'normal'
		if tf == 'normal':
			for tag in STYLE_TAGS:
				self.EgonTE.tag_remove(tag, first, last)
			return

		if tf not in STYLE_TAGS:
			return

		# Build base font safely (no nametofont error)
		base = base_font_copy(self.EgonTE)

		# Minimal config
		font_cfg = {}
		tag_cfg = {}

		if tf == 'weight-bold':
			font_cfg['weight'] = 'bold'
		elif tf == 'slant-italic':
			font_cfg['slant'] = 'italic'
		elif tf == 'underline':
			tag_cfg['underline'] = 1
		elif tf == 'overstrike':
			tag_cfg['overstrike'] = 1

		if font_cfg:
			base.configure(**font_cfg)

		# Configure tag idempotently
		if font_cfg and tag_cfg:
			self.EgonTE.tag_configure(tf, font=base, **tag_cfg)
		elif font_cfg:
			self.EgonTE.tag_configure(tf, font=base)
		elif tag_cfg:
			self.EgonTE.tag_configure(tf, **tag_cfg)
		else:
			self.EgonTE.tag_configure(tf, font=base)

		# Toggle based on presence in current range
		if self.EgonTE.tag_nextrange(tf, first, last):
			self.EgonTE.tag_remove(tf, first, last)
		else:
			self.EgonTE.tag_add(tf, first, last)


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


	def custom_ui_colors(self, components: str):
		'''
		custom UI colors for all of the main windows components, and for the "knowledge" (wiki/dictionary) window,
		for the help / patch notes window, and for the virtual keyboard

		NEW; WIP color picking algorithm that works for most instances
		'''
		if self.night_mode.get():
			if not (messagebox.askyesno('EgonTE', 'Night mode is on, still want to proceed?')):
				return

		if components in tuple(self.singular_colors_d.keys()):
			widget, type_ = self.singular_colors_d[components]

			if '-' in type_:
				type_lst = type_.split('-')
			else:
				type_lst = type_

			for type in type_lst:
				if type:
					if isinstance(type_lst, str) and len(type) < 2:
						type = type_lst

					color = colorchooser.askcolor(title=f'{components} {type} color')[1]
					if color:
						if isinstance(widget, list):
							for widget_ in widget:
								# not all the widgets need to be colored, some does not support it the same way
								try:
									widget_[type] = color
								except TclError:
									pass
						else:
							widget[type] = color
						self.record_list.append(f'> [{get_time()}] - {components} {type} changed to {color}')

					# checking if it the list contains one item
					if type == type_lst:
						break


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
					f'> [{get_time()}] - App\'s color changed to {selected_main_color}\n  '
					f'App\'s secondary color changed'
					f' to {selected_second_color}\n  App\'s text color changed to {selected_text_color}')


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
				if text_color and bg_color:
					for vk_btn in self.all_vk_buttons:
						vk_btn.config(bg=bg_color, fg=text_color)
			else:
				messagebox.showerror('EgonTE', 'Virtual keyboard window isn\'t opened')
		elif components == 'advance_options':
			if self.op_active:
				frames_color = colorchooser.askcolor(title='Frames color')[1]
				buttons_color = colorchooser.askcolor(title='buttons bg color')[1]
				buttons_t_color = colorchooser.askcolor(title='buttons text color')[1]
				titles_colors = colorchooser.askcolor(title='Titles text color')[1]
				title_bg_colors = colorchooser.askcolor(title='Titles bg color')[1]

				if frames_color and buttons_color and buttons_t_color and titles_colors:
					self.night_frame.configure(bg=buttons_color)
					full_buttons_list = self.opt_commands + self.dynamic_buttons
					for opt_frame in self.opt_frames:
						opt_frame.configure(bg=frames_color)
					for button in full_buttons_list:
						button.configure(bg=buttons_color, fg=buttons_t_color)
					for title in self.opt_labels:
						title.configure(fg=titles_colors, bg=title_bg_colors)

			else:
				messagebox.showerror('EgonTE', 'Advance options window isn\'t opened')


	def make_rich_textbox(self, root, place='pack_top', wrap=None, font='arial 10', size=None,
			selectbg='dark cyan', bd=0, relief='', format='txt',):
		return self._popup.make_rich_textbox(root=root, place=place, wrap=wrap, font=font,
			size=size, selectbg=selectbg, bd=bd, relief=relief, format=format,)

	def print_file(self, event=None):
		'''
		old function that aims to print your file
		'''
		file2p = filedialog.askopenfilename(initialdir='C:/EgonTE/', title='Open file', filetypes=text_extensions)
		if system().lower() == 'windows':
			printer_name = GetDefaultPrinter()
			if file2p:
				if messagebox.askquestion('EgonTE', f'are you wish to print with {printer_name}?'):
					ShellExecute(0, 'print', file2p, None, '.', 0)
		else:
			printer_name = simpledialog.askstring(self.title_struct + 'Print', 'What is your printer name?')
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
		main_color, second_color, third_color, _text_color = night_mode_colors[self.nm_palette.get()]
		if self.night_mode.get():
			USE_IMMERSIVE_DARK_MODE = 20
			self.highlight_search_c = 'yellow', 'black'
			try:
				self.record_list.append(f'> [{get_time()}] - Night mode activated')
			except AttributeError:
				pass

		else:
			self.highlight_search_c = 'blue', 'white'
			USE_IMMERSIVE_DARK_MODE = 0
			main_color, second_color, third_color = 'SystemButtonFace', 'SystemButtonFace', 'SystemButtonFace'
			_text_color = 'black'
			self.record_list.append(f'> [{get_time()}] - Night mode disabled')
			self.resizable(False, False)
			self.resizable(True, True)

		self.data['night_mode'] = self.night_mode.get()
		self.update()

		if system().lower() == 'windows':
			# support windows 11 only
			set_window_attribute = windll.dwmapi.DwmSetWindowAttribute
			get_parent = windll.user32.GetParent
			hwnd = get_parent(self.winfo_id())
			rendering_policy = USE_IMMERSIVE_DARK_MODE
			value = 2
			value = c_int(value)
			set_window_attribute(hwnd, rendering_policy, byref(value),
								 sizeof(value))

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

		# for toolt in self.tooltip_list:
		#     toolt.configure(bg=second_color, fg=_text_color)

		# help & patch notes
		if self.info_page_active:
			self.info_page_text.config(bg=second_color, fg=_text_color)
			self.info_page_title.config(bg=second_color, fg=_text_color)
		if self.vk_active:
			for vk_btn in self.all_vk_buttons:
				vk_btn.config(bg=second_color, fg=_text_color)

		if self.search_active:
			for widget in self.search_widgets:
				widget.configure(bg=second_color, fg=_text_color)
			self.search_widgets[-1].configure(bg=third_color, fg=_text_color)
			self.search_bg.configure(bg=main_color)

		if self.record_active:
			self.record_night.configure(bg=second_color, fg=_text_color)

		if self.op_active:
			for tab in self.opt_frames:
				tab.configure(bg=main_color)
			for title in self.opt_labels:
				title.configure(bg=main_color, fg=_text_color)
			for cm in self.opt_commands:
				cm.configure(bg=second_color, fg=_text_color)
			for button in tuple(self.dynamic_buttons.values()):
				button.configure(bg=third_color, fg=_text_color)
			self.night_frame.configure(bg=second_color)
			self.change_button_color(self.last_cursor[0], self.last_cursor[1])
			self.change_button_color(self.last_style[0], self.last_style[1])
			self.change_button_color(self.last_r[0], self.last_r[1])

		if self.hw_active:
			for bg in self.hw_bg:
				bg.configure(bg=main_color)
			for button in self.hw_buttons:
				button.configure(bg=third_color, fg=_text_color)
			for label in self.hw_labels:
				label.configure(bg=main_color, fg=_text_color)
			for seperator in self.hw_seperator:
				seperator.configure(bg=second_color, fg=_text_color)
			if self.night_mode.get():
				main_color = second_color
				self.draw_canvas.configure(bg=main_color)

		if self.ins_images_open:
			for widget in self.in_im_commands:
				widget.configure(bg=second_color, fg=_text_color)
			for background in self.in_im_bgs:
				background.configure(bg=main_color)

		self.style_combobox.configure('TCombobox', background=second_color, foreground=_text_color)

	def change_font(self, event):
		'''
		change the font of the main text box
		'''
		global chosen_font
		chosen_font = self.font_family.get()
		self.delete_tags()
		self.EgonTE.configure(font=(chosen_font, str(self.size_var.get())))

		self.change_font_size()
		self.record_list.append(f'> [{get_time()}] - font changed to {chosen_font}')


	def size_order(self, change_list=False):
		if self.fnt_sz_var.get() == 0:
			eq = 35 - ((self.size_var.get() - 8) // 2)
			if change_list:
				self.font_size['values'] = tuple(reversed(range(8, 80, 2)))
		else:
			eq = (self.size_var.get() - 8) // 2
			if change_list:
				self.font_size['values'] = tuple(range(8, 80, 2))
		return eq


	def change_font_size(self, event=None):
		'''
		change the fonts size of the main text box
		'''
		self.chosen_size = self.size_var.get()
		self.font_Size_c = self.size_order()
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

		self.record_list.append(f'> [{get_time()}] - font size changed to {self.chosen_size}')

	def replace(self, event=None):
		'''
		function that takes user input to change some terms with the thing that you will write
		'''

		# replacing functionality
		def rep_button():
			find_ = find_input.get()
			replace_ = replace_input.get()
			content = self.EgonTE.get(1.0, END)

			new_content = content.replace(find_, replace_)

			if not(replace_message.winfo_manager()):
				replace_message.grid(row=4, column=0)
			if new_content != content:
				replace_message.configure(text=f'{find_} text was changed to {replace_}', fg='dark green')
				pass
			else:
				replace_message.configure(text=f'{find_} wasn\'t found', fg='red')

			self.EgonTE.delete(1.0, END)
			self.EgonTE.insert(1.0, new_content)

		# window creation
		replace_root = self.make_pop_ups_window(self.replace)
		# ui components
		replace_text = Label(replace_root, text='Enter the word that you wish to replace')
		find_input = Entry(replace_root, width=20)
		replace_input = Entry(replace_root, width=20)
		by_text = Label(replace_root, text='by')
		replace_message = Label(replace_root, text='')
		replace_button = Button(replace_root, text='Replace', pady=3, command=rep_button)
		replace_text.grid(row=0, sticky=NSEW, column=0, columnspan=1)
		find_input.grid(row=1, column=0)
		by_text.grid(row=2)
		replace_input.grid(row=3, column=0)
		replace_button.grid(row=5, column=0, pady=5)

	def is_marked(self) -> bool:
		'''
		checks if text in the main text box is being marked, and returns the result in a boolean value
		'''
		if self.EgonTE.tag_ranges('sel'):
			return True
		else:
			return False

	def align_text(self, place='left'):
		'''align the main boxes text specifically if you marker, and all if you dont'''
		if self.is_marked():
			text_content = self.EgonTE.get('sel.first', 'sel.last')
		else:
			self.EgonTE.tag_add('sel', 'insert linestart', 'insert lineend')
			text_content = self.EgonTE.get('insert linestart', 'insert lineend')
		self.EgonTE.tag_config(place, justify=place)
		try:
			self.EgonTE.delete('sel.first', 'sel.last')
			self.EgonTE.insert(INSERT, text_content, place)
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
		if self.is_marked():
			content = self.EgonTE.get('sel.first', 'sel.last')
		else:
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


	def text_formatter(self, phrase: str) -> str:
		'''
		WIP function to make the analyzed text more organized


		'''
		interrogatives = ('how', 'why', 'what', 'when', 'who', 'where', 'is', 'do you', 'whom', 'whose', 'can')
		capitalized = phrase.capitalize()
		self.EgonTE.update_idletasks()
		index = self.EgonTE.index('current')


		line, col = map(int, self.get_pos().split('.'))
		before_pointer_index = (f'{line}.{int(col) - 1}') # one before pointer
		after_current = (f'{line}.{int(col)}+1c') # at pointer
		before_pointer_char = self.EgonTE.get(before_pointer_index)
		after_pointer_2char = self.EgonTE.get(after_current)
		print(before_pointer_char, after_pointer_2char)


		# part 1 - check for question words inside of the phrase
		if (after_pointer_2char in punctuation):
			if phrase.startswith(interrogatives):
				capitalized = f'{capitalized}?'
			else:
				capitalized = f'{capitalized}.'

		# part 2 - for the index before phrase
		space_before_conditions = ascii_letters + digits + punctuation
		print(space_before_conditions)
		if before_pointer_char in ['?', '!', '.']:
			capitalized = '\n' + capitalized
		elif before_pointer_char in space_before_conditions:
			capitalized = ' ' + capitalized

		# part 3 - maybe soon a better method will be added
		capitalized = capitalized + ' '

		return capitalized

	def _ensure_stt_attrs(self):
		if not hasattr(self, '_stt_queue'):
			self._stt_queue = queue.Queue()
		if not hasattr(self, '_stt_running'):
			self._stt_running = False
		if not hasattr(self, '_stt_attempts'):
			self._stt_attempts = 0
		if not hasattr(self, '_stt_max_attempts'):
			self._stt_max_attempts = 3

	def start_speech_to_text(self):
		"""
		Main-thread entry point. Bind this to the button.
		"""
		self._ensure_stt_attrs()
		if self._stt_running:
			return
		self._stt_running = True
		self._stt_attempts = 0

		# Offload TTS or any slow intro message
		Thread(target=self.read_text,
						 kwargs={'text': 'Please say the message you would like to the text editor!'},
						 daemon=True).start()

		Thread(target=self._stt_worker_once, daemon=True).start()
		self._poll_stt_queue()


	def _stt_worker_once(self):
		"""
		Background thread: does one listen+recognize cycle.
		No Tkinter calls here.
		"""
		r = Recognizer()
		try:
			with Microphone() as source:
				r.adjust_for_ambient_noise(source, duration=0.5)
				r.pause_threshold = 1.0
				audio = r.listen(source, timeout=7, phrase_time_limit=20)
			text = r.recognize_google(audio, language=getattr(self, 'stt_lang_value', 'en-US'))
			self._stt_queue.put({'status': 'ok', 'text': text})
		except WaitTimeoutError:
			self._stt_queue.put({'status': 'error', 'kind': 'timeout'})
		except Exception as e:
			self._stt_queue.put({'status': 'error', 'kind': 'recognition', 'error': str(e)})

	def _poll_stt_queue(self):
		"""
		Main-thread polling for worker results. Safe UI updates happen here.
		"""
		try:
			msg = self._stt_queue.get_nowait()
		except queue.Empty:
			# schedule next poll; use your Tk root or top-level widget here
			self.after(50, self._poll_stt_queue)
			return

		if msg['status'] == 'ok':
			raw = msg['text']
			try:
				formatted = self.text_formatter(raw)  # this touches Text widget state, keep on main thread
			except Exception:
				formatted = raw + ' '
			self.EgonTE.insert('insert', formatted)
			self._finish_stt()
			return

		# Error case
		self._stt_attempts += 1
		error_sentences = ['I don\'t know what you mean!', 'can you say that again?', 'please speak more clear']
		error_sentence = choice(error_sentences)
		error_msg = f'Excuse me, {error_sentence}'

		if self._stt_attempts < self._stt_max_attempts and messagebox.askyesno('EgonTE', 'Do you want to try again?'):
			Thread(target=self._stt_worker_once, daemon=True).start()
		self.root.after(50, self._poll_stt_queue)
		return

		self.read_text(text=f"{choice(['ok', 'goodbye', 'sorry', 'my bad'])}, I will try to do my best next time!")
		self._finish_stt()

	def _finish_stt(self):
		self._stt_running = False
		self._stt_attempts = 0

	# force the app to quit, warn user if file data is about to be lost
	def exit_app(self, event=None):
		'''
		exit function to warn the user if theres a potential for content to be lost, save the settings that are intended
		for it, and make sure that everything closes
		'''
		self.saved_settings(special_mode='save')
		self._stopwatch_running = False
		if self.usage_report_v.get():
			self.usage_report()

		if self.file_name:
			if check_file_changes(self.file_name, self.EgonTE.get('1.0', 'end')):
				self.save()

		if event == 'r':
			self.destroy()
			app = Window()
			app.mainloop()
		else:
			self.quit()
			exit_()
			quit()
			exit()
			raise Exception('Close')

	def close_pop_ups(self, root, th=False):
		self.opened_windows.remove(root)
		self.record_list.append(f'> [{get_time()}] - {root} tool window closed')
		root.destroy()

		'''+ need fixing'''
		if th:
			try:
				th.join()
			except RuntimeError:
				pass




	# Backward-compatible entry points
	def find_text(self, event=None):
		return self.find_replace(event)

	def replace(self, event=None):
		return self.find_replace(event)

	def ins_calc(self):
		'''
		a claculator using eval that gives the user option to see his equation, and an option to paste the result to
		the text editor
		NEW : claculator buttons
		'''

		self.ins_equation = ''
		self.extra_calc_ui = False
		padx_b, pady_b = 1, 1
		button_height, button_width = 3, 5
		ex_color = '#B0A695'

		def button_ui():
			if not self.extra_calc_ui:
				extra_frame.pack(side='right', fill=Y)
			else:
				extra_frame.pack_forget()
			self.extra_calc_ui = not (self.extra_calc_ui)

		def calculate_button():
			self.ins_equation = calc_entry.get()

			last_calc.configure(state='normal')
			last_calc.delete(0, END)
			last_calc.insert(0, self.ins_equation)
			last_calc.configure(state='readonly')

			try:
				self.ins_equation = numexpr.evaluate(self.ins_equation)

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
			numexpr_tutorial.pack()

		def hide_oper():
			op_frame.pack_forget()
			numexpr_tutorial.pack_forget()
			show_op.config(text='show operations', command=show_oper)

		def insert_extra(exp):
			calc_entry.insert(END, str(exp))

		calc_root = self.make_pop_ups_window(self.ins_calc)
		left_frame = Frame(calc_root)
		title = Label(left_frame, text='Calculator', font=self.titles_font, padx=2, pady=3)
		introduction_text = Label(left_frame, text='Enter a equation below:', font='arial 10 underline', padx=2, pady=3)
		enter = Button(left_frame, text='Calculate', command=calculate_button, borderwidth=1, font='arial 10 bold')
		b_frame = Frame(left_frame)
		copy_button = Button(b_frame, text='Copy', command=lambda: copy(str(self.ins_equation)), borderwidth=1,
							 font='arial 10')
		insert_button = Button(b_frame, text='Insert', command=insert_eq, borderwidth=1, font='arial 10')
		last_calc = Entry(left_frame, relief=RIDGE, justify='center', width=25, state='readonly')
		calc_entry = Entry(left_frame, relief=RIDGE, justify='center', width=25)
		show_op = Button(left_frame, text='Show operators', bd=1, command=show_oper)
		calc_ui = Button(left_frame, text='Calculator UI', command=button_ui, bd=1)
		left_frame.pack(side='left')
		title.pack(padx=10)
		introduction_text.pack(padx=10)
		last_calc.pack()
		calc_entry.pack()
		enter.pack(pady=3)
		b_frame.pack(pady=3)
		copy_button.grid(row=0, column=0, padx=2)
		insert_button.grid(row=0, column=2, padx=2)
		show_op.pack()
		calc_ui.pack()

		op_frame = Frame(left_frame)
		op_list, oper_buttons = ('+ addition', '- subtraction', '* multiply', '/ deviation', '** power', '% modulus'), []
		for index, op in enumerate(op_list):
			button = Button(op_frame, text=op, command=lambda i=op: insert_extra(f' {i[0]} '), relief=FLAT)
			oper_buttons.append(button)
		add, sub_b, mul, div, pow, modu = oper_buttons

		add.grid(row=0, column=0)
		sub_b.grid(row=0, column=2)
		mul.grid(row=1, column=0)
		div.grid(row=1, column=2)
		pow.grid(row=2, column=0)
		modu.grid(row=2, column=2)

		numexpr_link = 'https://numexpr.readthedocs.io/en/latest/user_guide.html'
		numexpr_tutorial = Button(left_frame, text='NumExpr tutorial', command=lambda: ex_links(link=numexpr_link)
								  , relief=FLAT, fg='blue', font='arial 10 underline')

		if self.is_marked():
			if str(self.EgonTE.get('sel.first', 'sel.last')).isnumeric():
				calc_entry.insert('end', self.EgonTE.get('sel.first', 'sel.last'))

		extra_frame = Frame(calc_root, bg=ex_color)
		b0, b1, b2, b3, b4, b5, b6, b7, b8, b9 = [
			Button(extra_frame, text=f'{num}', command=lambda num=num: insert_extra(num), padx=padx_b, pady=pady_b,
				   relief=FLAT, bg=ex_color, height=button_height, width=button_width) for num in range(10)]
		clear_b = Button(extra_frame, text='C', command=lambda: calc_entry.delete(0, END), pady=pady_b, relief=FLAT,
						 bg='#F3B664',
						 height=button_height
						 , width=button_width)
		del_b = Button(extra_frame, text='DEL', command=lambda: calc_entry.delete(calc_entry.index(INSERT) - 1),
					   pady=pady_b, relief=FLAT, bg='#F3B664',
					   height=button_height
					   , width=button_width)

		n_list = [b0, b1, b2, b3, b4, b5, b6, b7, b8, b9]
		pack_list, row_, column_ = [b1, b2, b3, b4, b5, b6, b7, b8, b9, clear_b, b0, del_b], 0, 0
		for widget in pack_list:
			widget.grid(row=row_, column=column_)
			column_ += 1
			if column_ == 3: row_, column_ = 1 + row_, 0

	def dt(self, event=None):
		'''
		insert the current date/time to where the pointer of your text are
		'''



		message = get_time() + ' '

		# message = self.text_formatter(message)
		line, col = map(int, self.get_pos().split('.'))
		prev_ind = f'{line}.{col - 1}'
		before_char = self.EgonTE.get(prev_ind)

		if before_char in ascii_letters or before_char in digits:
			message = ' ' + message
		self.EgonTE.insert(self.get_pos(), message)

	def ins_random(self):
		'''
		insert random numbers - random int / random decimal (between 0-1) to the text editor.
		the random int is based on your input but also has random range when you open it.
		there is also quick random int that is self-explanatory
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

		ran_num_root = self.make_pop_ups_window(self.ins_random)
		title = Label(ran_num_root, text='Random numbers:', justify='center',
					  font=self.titles_font)
		introduction_text = Label(ran_num_root, text='Enter numbers below:', justify='center',
								  font='arial 10 underline')
		sub_c = Button(ran_num_root, text='submit custom', command=enter_button_custom, relief=FLAT)
		sub_qf = Button(ran_num_root, text='submit quick float', command=enter_button_quick_float, relief=FLAT)
		sub_qi = Button(ran_num_root, text='submit quick int', command=enter_button_quick_int, relief=FLAT)
		number_entry1 = Entry(ran_num_root, relief=RIDGE, justify='center', width=20)
		number_entry2 = Entry(ran_num_root, relief=RIDGE, justify='center', width=20)
		bt_text = Label(ran_num_root, text='Between', font='arial 10 bold')
		options = None
		title.grid(row=0, column=1)
		introduction_text.grid(row=1, column=1, padx=5)
		number_entry1.grid(row=2, column=1)
		bt_text.grid(row=3, column=1)
		number_entry2.grid(row=4, column=1)
		sub_c.grid(row=5, column=1, padx=5)
		sub_qf.grid(row=5, column=0)
		sub_qi.grid(row=5, column=2, padx=5)

		if self.is_marked():
			ran_numbers = self.EgonTE.get('sel.first', 'sel.last')
			numbers_separation = ran_numbers.split(' ')
			if str(ran_numbers[0]).isnumeric():
				number_entry1.insert('end', numbers_separation[0])
			try:
				number_entry2.insert('end', numbers_separation[1])
			except IndexError:
				pass
		else:
			if self.fun_numbers.get():
				number_entry1.insert('end', str(randint(1, 10)))
				number_entry2.insert('end', str(randint(10, 1000)))

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
		if self.custom_cursor_v.get() == 'tcross':
			self.custom_cursor_v.set('xterm')
		else:
			self.custom_cursor_v.set('tcross')

		self.predefined_cursor = self.custom_cursor_v.get()
		self.data['cursor'] = self.predefined_cursor
		self.EgonTE.config(cursor=self.predefined_cursor)
		try:
			sort_input.config(cursor=self.predefined_cursor)
			self.translate_box.config(cursor=self.predefined_cursor)
		except BaseException:
			pass

		if self.op_active:
			self.change_button_color('cursors', self.predefined_cursor)

		self.record_list.append(f'> [{get_time()}] - cursor changed to {self.custom_cursor_v}')

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

		self.record_list.append(f'> [{get_time()}] - style changed to {self.cs}')

	def word_wrap(self):
		'''
		when pressed initially disabling word wrap and adding an vertical scrollbar
		'''
		if not self.word_wrap_v:
			self.EgonTE.config(wrap=WORD)
			self.geometry(f'{self.width}x{self.height - 10}')
			self.horizontal_scroll.pack_forget()
			self.word_wrap_v = True
			self.data['word_wrap'] = False
			self.record_list.append(f'> [{get_time()}] - Word wrap is activated')
		else:
			self.geometry(f'{self.width}x{self.height + 10}')
			self.horizontal_scroll.pack(side=BOTTOM, fill=X)
			self.EgonTE.config(wrap=NONE)
			self.word_wrap_v = False
			self.data['word_wrap'] = True
			self.record_list.append(f'> [{get_time()}] - Word wrap is disabled')

	def reader_mode(self):
		if not self.reader_mode_v:
			self.EgonTE.configure(state=NORMAL)
			self.record_list.append(f'> [{get_time()}] - Reader mode is disabled')
		else:
			self.EgonTE.configure(state=DISABLED)
			self.record_list.append(f'> [{get_time()}] - Reader mode is activated')
		self.data['reader_mode'] = self.reader_mode_v
		self.reader_mode_v = not (self.reader_mode_v)

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
				if type_value == 'Last Name':
					random_name = names.get_last_name()
				elif type_value == 'Full Name' or type_value == 'First Name':
					random_name = names.get_full_name(gender=gender_value.lower())
					if type_value == 'First Name':
						random_name = random_name.split(' ')[0]
				rand_name.config(text=random_name)
				re_roll.config(command=adv_random_name)

		name_root = self.make_pop_ups_window(self.ins_random_name)
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
		'''
		simply an old translate tool using google translate API,
		support auto detect, and have a UI that remind most of the translate tools UI
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
		translate_root = self.make_pop_ups_window(self.translate)
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

		auto_detect['values'] = 'Auto Detect'
		auto_detect.current(0)

		chosen_language['values'] = languages_list
		if self.fun_numbers.get():
			lng_length = len(chosen_language['values'])
			lng_index = randint(0, lng_length - 1)
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

	def url(self):
		'''
		a simple tool that takes an input of url and inserts a shorter version
		'''

		# window creation
		url_root = self.make_pop_ups_window(self.url)
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

	def get_indexes(self):
		'''
		if text is marked will return the selected indexes, and if not return the whole index of the text box
		'''
		if not (self.is_marked()):
			self.text_index = [1.0, END]
			self.first_index, self.last_index = self.text_index[0], self.text_index[1]
		else:
			self.text_index = 'sel.first', 'sel.last'
			self.first_index, self.last_index = self.EgonTE.index(self.text_index[0]), self.EgonTE.index(
				self.text_index[1])
		return self.text_index

	def reverse_characters(self, event=None):
		self.get_indexes()
		content = self.EgonTE.get(*self.text_index)
		n = ''

		if self.textwist_special_chars.get():
			content = content.replace(' ', '')

		if '\n' in content:
			content, newline = content.split('\n', maxsplit=1)
			content = content.replace('\n', '')
			if self.textwist_special_chars.get():
				n = ''
			else:
				n = '\n'
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

		if self.textwist_special_chars.get():
			content = content.replace(' ', '').replace('\n', '')

		words = content.split()
		joined_words = ''.join(words)
		self.EgonTE.delete(*self.text_index)
		self.EgonTE.insert(self.first_index, joined_words)

	def lower_upper(self, event=None):

		self.get_indexes()
		if self.text_index[1] == END:
			self.text_index[1] = 'end-1c'
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

		if self.textwist_special_chars.get():
			content = content.replace(' ', '').replace('\n', '')

		sorted_content = ''.join(sorted(content))
		# if the content is already sorted it will sort it reversed
		if content == sorted_content:
			sorted_content = ''.join(sorted(sorted_content, reverse=True))
			if self.textwist_special_chars.get():
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
		insert a random generated string in the length that you decide, contains regular english characters and numbers,
		and also can contain many common symbols if you active its option
		'''

		def generate_sequence():
			global sym_char
			try:
				length = int(length_entry.get())
				approved = True
			except ValueError:
				messagebox.showerror(self.title_struct + 'error', 'didn\'t write the length')
				approved = False
			if approved:
				if length < 20000:
					approved = True
				else:
					if messagebox.askyesno('EgonTE', '20000 characters or more can cause lag,'
													 ' are you sure you want to proceed?'):
						approved = True
					else:
						approved = False
			if approved:
				sym_char = '!', '@', '#', '$', '%', '^', '&', '*', '(', ')'
				if self.generate_sym.get():
					for character in sym_char:
						characters.append(character)
					else:
						try:
							remove_list = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')']
							for i in characters:
								if i in remove_list:
									characters.remove(i)
						except ValueError as e:
							print(e)
				shuffle(characters)
				sequence = []
				for i in range(length):
					sequence.append(choice(characters))

				desired_pos = END
				if self.insert_mc.get():
					desired_pos = self.get_pos()
				if self.preview_sequence.get():
					def insert_gs():
						self.EgonTE.insert(desired_pos, ''.join(sequence))
						preview_root.destroy()

					preview_root = Toplevel()
					self.make_tm(preview_root)
					preview_root.title(self.title_struct + 'preview of G.S')
					text_frame, text, text_scroll = self.make_rich_textbox(preview_root)
					text.insert(END, ''.join(sequence))
					text.configure(state=DISABLED)
					insert_button = Button(preview_root, text='Insert', command=insert_gs)
					insert_button.pack()
				else:
					self.EgonTE.insert(desired_pos, ''.join(sequence))

		self.generate_sym = BooleanVar()
		self.insert_mc = BooleanVar()
		self.preview_sequence = BooleanVar()
		self.insert_mc.set(True)
		generate_root = self.make_pop_ups_window(self.generate)
		characters = list(ascii_letters + digits)
		intro_text = Label(generate_root, text='Generate a random sequence', font=self.titles_font)
		length_entry = Entry(generate_root, width=15)
		option_text = Label(generate_root, text='Options', font='arial 12 underline')
		options_frame = Frame(generate_root)
		sym_checkbutton = Checkbutton(options_frame, text='Include symbols', variable=self.generate_sym)
		length_text = Label(generate_root, text='length', padx=10, font='arial 10 underline')
		# option_text = Label(generate_root, text='Options',  font='arial 10 underline')
		msc_checkbutton = Checkbutton(options_frame, text='Insert at pointer', variable=self.insert_mc)
		enter_button = Button(generate_root, text='Enter', width=8, height=1, bd=1, command=generate_sequence)
		preview_checkbutton = Checkbutton(options_frame, text='Open with preview', variable=self.preview_sequence)

		if self.fun_numbers.get():
			length_entry.insert(0, randint(10, 100))

		intro_text.pack()
		length_text.pack()
		length_entry.pack(pady=3)
		option_text.pack()
		# sym_checkbutton.pack(pady=3)
		option_text.pack()
		options_frame.pack()
		msc_checkbutton.grid(row=0, column=0)
		sym_checkbutton.grid(row=1, column=0)
		preview_checkbutton.grid(row=2, column=0)
		enter_button.pack()

		generate_root.update_idletasks()
		generate_w, generate_h = generate_root.winfo_width() + 100, generate_root.winfo_height()
		generate_root.geometry(f'{generate_w}x{generate_h}')

	# font size up / down by 1 iteration
	def sizes_shortcuts(self, value=-1):
		'''
		a shortcut to increase the font size, its increasing / decreasing it by 1 iteration of the values tuple
		'''
		message = 'maximum'
		if value == -1: message = 'minimum'
		try:
			self.font_size.current(self.font_Size_c + value)
			self.font_Size_c += value
			self.change_font_size()
		except Exception as e:
			print(e)
			messagebox.showerror(self.title_struct + 'error', f'font size at {message}')

	# tags and configurations of the same thing is clashing all the time \:
	def delete_tags(self):
		self.EgonTE.tag_delete('bold', 'underline', 'italics', 'size', 'colored_txt')

	def special_files_import(self, via: str ='file'):
		'''
		a tool that is used to import other file types to your current text file,
		supports xml, html, csv, excel and pdf
		support also the import of files via link
		'''
		# to make the functions write the whole file even if its huge
		pandas.options.display.max_rows = 9999
		content = ''

		if via == 'file':
			special_file = filedialog.askopenfilename(title='open file',
													  filetypes=special_files)
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
			self.record_list.append(f'> [{get_time()}] - Special file ({ends}) imported;\n  the files name is'
									f' {starts}\n   and the file was imported via {via}')
		except AttributeError:
			messagebox.showerror(self.title_struct + 'error', 'please enter a valid domain')

	# a window that have explanations confusing features
	def info_page(self, path: str):
		self.infp_occurs = False
		'''
		the UI for the help and patch notes pages
		'''

		def quit_page():
			self.opened_windows.remove(info_root)
			self.info_page_active = False
			info_root.destroy()

		# window creation
		self.info_page_active = True
		info_root = Toplevel()
		info_root.attributes('-alpha', self.st_value)
		self.opened_windows.append(info_root)
		self.func_window[lambda: self.info_page(path)] = info_root
		self.make_tm(info_root)
		info_root.config(bg='white')
		info_root.protocol('WM_DELETE_WINDOW', quit_page)

		# putting the lines in order
		def place_lines():
			'''+
			make scrollbars work with html-tkinter
			'''
			self.info_page_text.delete('1.0', END)
			file_path = fr'content_msgs\{path}.{self.content_mode}'
			with open(file_path) as ht:
				if self.content_mode == 'txt':
					for line in ht:
						self.info_page_text.insert('end', line)
				else:
					html_content = ht.read()
					self.info_page_text.set_html(html_content)

		def find_content(event=False):
			global entry_content, starting_index, ending_index, offset
			self.infp_occurs = False
			entry_content = entry.get().lower()
			data = self.info_page_text.get('1.0', END).lower()

			# this condition is made to hide to result of blank \ white space characters
			if entry_content and not (entry_content == ' '):
				self.infp_occurs = data.count(entry_content)
			else:
				self.infp_occurs = False
				found_label.configure(text='')

			# display the times that the term is in the text
			if self.infp_occurs:
				found_label.configure(text=f'{str(self.infp_occurs)} occurrences')
				if self.oc_color == self.dynamic_overall and self.night_mode.get():
					self.oc_color = self.dynamic_bg

			else:
				found_label.configure(text='0 occurrences')
				if self.oc_color == self.dynamic_bg and self.night_mode.get():
					self.oc_color = self.dynamic_overall

			found_label.configure(bg=self.oc_color)

			untag_all_matches()

			if self.infp_occurs:
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
		#             if ending_index == starting_index or ending_index == self.info_page_text.index('end'): # old condition ending_index == info_page_text.index('end')
		#                 more_matches = False
		#
		#             else:
		#                 self.info_page_text.tag_add('highlight_all_result', starting_index, ending_index)
		#                 starting_index = ending_index

		def tag_all_matches():
			global starting_index, ending_index
			find_upper()
			for i in range(self.infp_occurs):
				starting_index = self.info_page_text.search(entry_content, ending_index, END)
				if starting_index:
					offset = '+%dc' % len(entry_content)
					ending_index = starting_index + offset
					print(f'str:{starting_index} end:{ending_index}')
					self.info_page_text.tag_add('highlight_all_result', starting_index, ending_index)
					starting_index = ending_index

		def untag_all_matches():
			self.info_page_text.tag_remove('highlight_all_result', 1.0, END)
			self.info_page_text.tag_config('highlight_all_result', background=self.highlight_search_c[0],
										   foreground=self.highlight_search_c[1])

		def find_lower():
			global ending_index, starting_index
			if int(self.infp_occurs) > 1:
				try:
					starting_index = self.info_page_text.search(entry_content, ending_index, END)
				except Exception:
					pass
				if starting_index and starting_index != '':
					self.info_page_text.tag_remove('highlight_all_result', '1.0', starting_index)
					offset = '+%dc' % len(entry_content)
					ending_index = starting_index + offset
					print(f'str:{starting_index} end:{ending_index}')
					self.info_page_text.tag_add('highlight_all_result', starting_index, ending_index)
					starting_index = ending_index

		def find_upper():
			global ending_index, starting_index
			if int(self.infp_occurs) > 1:
				# experimental_ei = f'{starting_index}-{len()}c'
				try:
					starting_index = self.info_page_text.search(entry_content, '1.0', starting_index)
				except Exception:
					pass
				if starting_index and starting_index != '':
					offset = '+%dc' % len(entry_content)
					ending_index = starting_index + offset
					self.info_page_text.tag_remove('highlight_all_result', ending_index, END)
					print(f'str:{starting_index} end:{ending_index}')
					self.info_page_text.tag_add('highlight_all_result', starting_index, ending_index)
					ending_index = starting_index

		title_frame = Frame(info_root)
		title_frame.pack(fill=X, expand=True)

		if html_infop == 'txt' or self.content_preference_v.get() == 'txt':
			self.content_mode = 'txt'
		else:
			self.content_mode = 'html'

		# labels
		self.info_page_title = Label(title_frame, text='Help', font='arial 16 bold underline', justify='left',
									 fg=self.dynamic_text, bg=self.dynamic_bg)
		info_root_frame, self.info_page_text, help_text_scroll = self.make_rich_textbox(info_root, font='arial 10',
																						bd=3, relief=RIDGE, format=self.content_mode, wrap=WORD)

		if path == 'patch_notes':
			self.info_page_title.configure(text='Patch notes')

		self.info_page_text.focus_set()
		# add lines
		place_lines()
		self.info_page_text.config(state='disabled')
		# placing
		self.info_page_title.pack(fill=X, anchor=W, expand=True)

		self.oc_color = 'SystemButtonFace'
		if self.night_mode.get():
			self.oc_color = self.dynamic_overall

		find_frame = Frame(info_root, relief=FLAT, background=self.dynamic_overall)
		entry = Entry(find_frame, relief=FLAT, background=self.dynamic_bg, fg=self.dynamic_text)
		button_up = Button(find_frame, text='Reset', relief=FLAT, command=find_upper, background=self.dynamic_button,
						   bd=1, fg=self.dynamic_text)
		button_down = Button(find_frame, text='↓', relief=FLAT, command=find_lower, background=self.dynamic_button,
							 bd=1, fg=self.dynamic_text)
		tag_all_button = Button(find_frame, text='Highlight all', relief=FLAT, command=tag_all_matches,
								background=self.dynamic_button, fg=self.dynamic_text)
		untag_all_button = Button(find_frame, text='Lowlight all', relief=FLAT, command=untag_all_matches,
								  background=self.dynamic_button, fg=self.dynamic_text)
		found_label = Label(find_frame, text='', background=self.oc_color, fg=self.dynamic_text)
		find_frame.pack(side='left', fill=X, expand=True)
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
		# if the window will appear out of bounds, we will just change it to the middle of the screen
		# bug if using your second display
		if abs(mid_y - self.winfo_screenheight()) <= 80:
			mid_y = (self.winfo_screenheight() // 2)
		if self.open_middle_s.get():
			info_root.geometry(f'{win_w}x{win_h}+{mid_x}+{mid_y}')
		if self.limit_w_s.get():
			info_root.resizable(False, False)

		entry.bind('<KeyRelease>', find_content)

	def right_align_language_support(self):
		if self.EgonTE.get('1.0', 'end'):
			lan = poly_text(self.EgonTE.get('1.0', 'end')).language.name
			if lan in right_aligned_l:
				self.align_text('right')

	def search_www(self):
		'''
		this tool is a shortcut for web usage, you can also choose some browser beside the default one,
		and choose session type
		'''

		ser_root = self.make_pop_ups_window(self.search_www)

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

	def save_outvariables(self):
		self.data['fun_numbers'] = self.fun_numbers.get()
		self.data['auto_save'] = self.auto_save_v.get()

	def advance_options(self):
		'''
		this tool allow you to customize the UI with more option and have also a ton of option regarding many fields
		of the program itself

		UI options:
		6 different cursors: pencil, fleur, xterm, tcross, arrow, crosshair
		3 different window styles: clam, vista, classic
		3 different reliefs: groove, flat, ridge
		2 night modes: dracula, midnight blue

		In between:
		1. change if the informative labels on the bottom will be shawn (status bar and file bar)
		2. main window transparency (0-90 percent)

		functional options:
		1. speech to text languages
		2. open (when program is starting) last used file
		3. restore saved settings to default
		4. remove newlines and spaces in some text twisters functions
		5. auto save method
		6. check (if using updated) version - when the program is opening
		7. usage report - make a file upon exit - with your usage time + record window information

		activate / disable shortcuts:
		- file actions
		- typefaces actions
		- edit functions
		- window shortcuts
		- text twisters

		other windows:
		1. topmost
		2. open at the middle of the screen (for those who had it already)
		3. don't limit sizes
		4. warning when you are opening a large amount of windows
		5. transparency
		6. view text corrector changes before applying them
		'''


		def custom_binding(mode: str):
			"""
			mode is the group key (e.g., 'filea', 'typea', 'editf', 'textt', 'windf', 'autof', 'autol').
			Each checkbox drives a BooleanVar in self.binding_work[mode].
			"""
			var = self.binding_work.get(mode)
			if var and var.get():
				# enable (bind) this group only
				self.binds(mode=mode)
			else:
				# disable (unbind) this group only
				self.unbind_group(mode)

		def reset_binds():
			"""
			Restore original values: set all flags to True and re-apply all bindings.
			"""
			for var in self.binding_work.values():
				try:
					var.set(True)
				except Exception:
					pass
			self.binds('reset')  # or self.reset_binds() if you want the builder to do the unbind+rebind cycle

		def exit_op():
			self.opened_windows.remove(self.opt_root)
			self.op_active = False
			self.opt_root.destroy()

		def adv_custom_cursor(cursor: str):
			self.EgonTE.config(cursor=cursor)
			self.data['cursor'] = cursor

			if cursor == 'tcross':
				self.custom_cursor_v.set('tcross')
			elif cursor == 'xterm':
				self.custom_cursor_v.set('xterm')

			try:
				sort_input.config(cursor=cursor)
				self.translate_box.config(cursor=cursor)
				self.translate_resultbox.config(cursor=cursor)
			except BaseException:
				pass
			self.change_button_color('cursors', cursor)
			self.predefined_cursor = cursor
			self.record_list.append(f'> [{get_time()}] - Cursor changed to {cursor}')

		def hide_(bar: str):
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

		def change_style(style_: str):
			self.style.theme_use(style_)
			self.change_button_color('styles', style_)
			if style_ == 'vista':
				self.cs.set('vista')
			elif style_ == 'clam':
				self.cs.set('clam')
			self.predefined_style = style_
			self.data['style'] = style_
			self.record_list.append(f'> [{get_time()}] - Style changed to {style_}')

		def change_relief(relief_: str):
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
			self.record_list.append(f'> [{get_time()}] - Relief changed to {relief_}')

		def change_transparency(event=False):
			tranc = int(transparency_config.get()) / 100
			self.attributes('-alpha', tranc)
			self.data['transparency'] = tranc
			self.record_list.append(f'> [{get_time()}] - Transparency changed to {tranc}')

		def change_lof():
			if self.last_file_v.get():
				if self.file_name:
					self.save_last_file()
				else:
					self.data['open_last_file'] = True

			else:
				self.data['open_last_file'] = ''

		# window creation and some settings
		self.opt_root = Toplevel()
		self.make_tm(self.opt_root)
		self.opt_root.configure(bg=self.dynamic_overall)
		if self.limit_w_s.get():
			self.opt_root.resizable(False, False)
		self.op_active = True
		self.opt_root.protocol('WM_DELETE_WINDOW', exit_op)
		self.opened_windows.append(self.opt_root)
		self.usage_time = Label(self.opt_root, fg=self.dynamic_text, bg=self.dynamic_overall)

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

		def save_variables():
			self.data['usage_report'] = self.usage_report_v.get()
			self.data['text_twisters'] = self.textwist_special_chars.get()
			self.data['night_type'] = self.nm_palette.get()
			self.data['preview_cc'] = self.corrector_check_changes.get()
			self.data['check_version'] = self.check_ver_v.get()
			self.data['window_c_warning'] = self.win_count_warn.get()
			self.data['allow_duplicate'] = self.adw.get()

		def restore_defaults():

			if messagebox.askyesno(self.title_struct + 'reset settings',
								   'Are you sure you want to reset all your current\nand saved settings?'):
				self.data = self.make_default_data()
				self.match_saved_settings()

				self.bars_active.set(True)
				self.show_statusbar.set(True)
				self.show_toolbar.set(True)
				self.word_wrap_v.set(True)
				self.auto_save_v.set(True)
				self.reader_mode_v.set(False)
				self.predefined_cursor = 'xterm'
				self.predefined_style = 'clam'
				self.predefined_relief = 'ridge'
				self.save_bg.set(False)

		def stt_key(event=False):
			self.stt_lang_value = sr_supported_langs[self.stt_chosen_lang.get()]
			self.record_list.append(
				f'> [{get_time()}] - Speech to text language changed to: {self.stt_lang_value}')

		def autosave_changes():
			if self.autosave_by_p.get():
				self.EgonTE.bind('<KeyRelease>', self.auto_save_press)
				self.record_list.append(
					f'> [{get_time()}] - AutoSave method Added: save by pressing')
			else:
				self.EgonTE.unbind('<KeyRelease>', self.auto_save_press)
				self.record_list.append(
					f'> [{get_time()}] - AutoSave method Removed: save by pressing')

			if self.autosave_by_t.get():
				self.record_list.append(
					f'> [{get_time()}] - AutoSave method Added: save by waiting 30 seconds')

			else:
				self.record_list.append(
					f'> [{get_time()}] - AutoSave method Removed: save by waiting 30 seconds')

		# default values for the check buttons
		'''+ prob initialize in the init method'''
		self.def_val1 = IntVar()
		self.def_val2 = IntVar()

		# tabs for different categories
		settings_tabs = ttk.Notebook(self.opt_root)
		styles_frame = Frame(settings_tabs, bg=self.dynamic_overall)
		functional_frame = Frame(settings_tabs, bg=self.dynamic_overall)
		bindings_frame = Frame(settings_tabs, bg=self.dynamic_overall)
		pop_ups_frame = Frame(settings_tabs, bg=self.dynamic_overall)

		button_width = 8
		font_ = 'arial 10 underline'
		self.night_frame = Frame(styles_frame, bg=self.dynamic_bg)
		bar_frame = Frame(functional_frame)
		predefined_checkbuttons()
		# creating adv-options window UI
		opt_title = Label(self.opt_root, text='Advance Options', font='calibri 16 bold', bg=self.dynamic_overall,
						  fg=self.dynamic_text)
		cursor_title = Label(styles_frame, text='Advance Cursor configuration', font=font_, bg=self.dynamic_overall,
							 fg=self.dynamic_text)
		cursor_values = 'tcross', 'arrow', 'crosshair', 'pencil', 'fleur', 'xterm'
		self.tcross_button, self.arrow_button, self.crosshair_button, self.pencil_button, self.fleur_button, self.xterm_button = \
			[Button(styles_frame, text=cursor_b, command=lambda cursor_b=cursor_b: adv_custom_cursor(cursor_b),
					width=button_width, bg=self.dynamic_button, fg=self.dynamic_text)
			 for cursor_b in cursor_values]
		hide_title = Label(functional_frame, text='Advance hide status & file bar', font=font_, bg=self.dynamic_overall,
						   fg=self.dynamic_text)
		filebar_check = Checkbutton(bar_frame, text='filebar', command=lambda: hide_('filebar'), variable=self.def_val1,
									bg=self.dynamic_bg, fg=self.dynamic_text)
		statusbar_check = Checkbutton(bar_frame, text='statusbar', command=lambda: hide_('statusbar'),
									  variable=self.def_val2, bg=self.dynamic_bg, fg=self.dynamic_text)
		style_title = Label(styles_frame, text='Advance style configuration', font=font_, bg=self.dynamic_overall,
							fg=self.dynamic_text)

		'''+ shorten'''

		'''
		self.opt_buttons = {'clam' : change_style, 'classic' : change_style, 'vista' : change_style,
							'flat' : change_relief, 'ridge' : change_relief, 'groove': change_relief}

		for name, function in self.opt_buttons.values():
			b = Button(styles_frame, text=name, command=lambda: function(name), width=button_width,
				   bg=self.dynamic_button, fg=self.dynamic_text)
		'''

		self.style_clam = Button(styles_frame, text='clam', command=lambda: change_style('clam'), width=button_width,
								 bg=self.dynamic_button, fg=self.dynamic_text)
		self.style_classic = Button(styles_frame, text='classic', command=lambda: change_style('classic'),
									width=button_width, bg=self.dynamic_button, fg=self.dynamic_text)
		self.style_vista = Button(styles_frame, text='vista', command=lambda: change_style('vista'), width=button_width,
								  bg=self.dynamic_button, fg=self.dynamic_text)
		relief_title = Label(styles_frame, text='Advance relief configuration', font=font_, bg=self.dynamic_overall,
							 fg=self.dynamic_text)
		self.relief_flat = Button(styles_frame, text='flat', command=lambda: change_relief('flat'), width=button_width,
								  bg=self.dynamic_button, fg=self.dynamic_text)
		self.relief_ridge = Button(styles_frame, text='ridge', command=lambda: change_relief('ridge'),
								   width=button_width, bg=self.dynamic_button, fg=self.dynamic_text)
		self.relief_groove = Button(styles_frame, text='groove', command=lambda: change_relief('groove'),
									width=button_width, bg=self.dynamic_button, fg=self.dynamic_text)

		nm_title = Label(styles_frame, text='Choose night mode type', font=font_, bg=self.dynamic_overall,
						 fg=self.dynamic_text)
		nm_black_checkbox = Radiobutton(self.night_frame, text='Dracula', variable=self.nm_palette, value='black',
										command=save_variables, bg=self.dynamic_bg, fg=self.dynamic_text)
		nm_blue_checkbox = Radiobutton(self.night_frame, text='MidNight\nBlue', variable=self.nm_palette, value='blue',
									   command=save_variables, bg=self.dynamic_bg, fg=self.dynamic_text)

		stt_title = Label(functional_frame, text='Speech to text language', font=font_, bg=self.dynamic_overall,
						  fg=self.dynamic_text)
		stt_lang = ttk.Combobox(functional_frame, width=15, textvariable=self.stt_chosen_lang, state='readonly',
								style='TCombobox')
		stt_lang['values'] = list(sr_supported_langs.keys())

		# lf_frame = Frame(functional_frame)
		file_opt_title = Label(functional_frame, text='Files', font=font_, bg=self.dynamic_overall,
							   fg=self.dynamic_text)
		last_file_checkbox = Checkbutton(functional_frame, text='Open initially last file', variable=self.last_file_v,
										 command=change_lof, bg=self.dynamic_bg, fg=self.dynamic_text)
		usage_report_checkbox = Checkbutton(functional_frame, text='Usage report', variable=self.usage_report_v,
											command=save_variables, bg=self.dynamic_bg, fg=self.dynamic_text)

		# last_bg_checkbox = Checkbutton(lf_frame, text='last background file', variable=self.save_bg,
		#                                  bg=self.dynamic_bg, fg=self.dynamic_text, state=DISABLED)

		transparency_title = Label(styles_frame, text='Transparency configuration', font=font_, bg=self.dynamic_overall,
								   fg=self.dynamic_text)
		transparency_config = Scale(styles_frame, from_=10, to=100, orient='horizontal', command=change_transparency,
									bg=self.dynamic_bg, fg=self.dynamic_text)
		transparency_config.set(100)
		# transparency_set = Button(styles_frame, text='Change transparency', command=change_transparency)

		title_other = Label(functional_frame, text='Others', font=font_, bg=self.dynamic_overall, fg=self.dynamic_text)
		check_v_checkbox = Checkbutton(functional_frame, text='Check version', variable=self.check_ver_v,
									   bg=self.dynamic_bg, fg=self.dynamic_text, command=save_variables)
		reset_button = Button(functional_frame, text='Restore default', command=restore_defaults, bg=self.dynamic_bg,
							  fg=self.dynamic_text)
		tt_checkbox = Checkbutton(functional_frame, text='Text twisters\nremove special characters',
								  variable=self.textwist_special_chars,
								  command=save_variables, bg=self.dynamic_bg, fg=self.dynamic_text)
		# open_record_cb = Checkbutton(functional_frame, text='Text twisters\nremove special characters', variable=self.tt_sc,
		#                           command=save_variables, bg=self.dynamic_bg, fg=self.dynamic_text)

		auto_save_frame = Frame(functional_frame)
		auto_save_title = Label(functional_frame, text='Auto save method', font=font_, bg=self.dynamic_overall,
								fg=self.dynamic_text)
		by_time_rb = Checkbutton(auto_save_frame, text='By time', variable=self.autosave_by_t,
								 command=autosave_changes, bg=self.dynamic_bg, fg=self.dynamic_text)
		by_press_rb = Checkbutton(auto_save_frame, text='By pressing', variable=self.autosave_by_p,
								  command=autosave_changes, bg=self.dynamic_bg, fg=self.dynamic_text)

		indent_title = Label(functional_frame, text='indent method (virtual keyboard)', font=font_)
		indent_frame = Frame(functional_frame)
		indent_tab = Radiobutton(indent_frame, text='Tab', variable=self.indent_method, value='tab')
		indent_space = Radiobutton(indent_frame, text='Space', variable=self.indent_method, value='space')

		state_title = Label(bindings_frame, text='State of shortcuts', font=font_, bg=self.dynamic_overall,
							fg=self.dynamic_text)
		shortcuts_dict = {'file actions': self.file_actions_v, 'typefaces actions': self.typefaces_actions_v,
						  'edit functions': self.edit_functions_v,
						  'window functions': self.win_actions_v,
						  'text twisters functions': self.texttwisters_functions_v,
						  'automatic functions': self.auto_functions, 'auto list': self.aul}
		file_actions_check, typefaces_action_check, edit_functions_check, win_actions_check, textt_function_check, auto_function_check, auto_list_check = \
			[Checkbutton(bindings_frame, text=name, command=lambda name=name, value=value: custom_binding(
				f"{name.split(' ')[0][:4]}{name.split(' ')[1][0]}"), variable=value, bg=self.dynamic_bg,
						 fg=self.dynamic_text) for name, value in shortcuts_dict.items()]
		order_title = Label(bindings_frame, text='Order (of font sizes)', font=font_, bg=self.dynamic_overall,
							fg=self.dynamic_text)
		order_frame = Frame(bindings_frame)
		biggest_top = Radiobutton(order_frame, text='Biggest top', value=0, variable=self.fnt_sz_var, command=lambda: self.size_order(True), bg=self.dynamic_overall,
							fg=self.dynamic_text)
		biggest_bottom = Radiobutton(order_frame, text='Biggest Bottom', value=1, variable=self.fnt_sz_var, command=lambda: self.size_order(True), bg=self.dynamic_overall,
							fg=self.dynamic_text)
		reset_binds_button = Button(bindings_frame, text='Reset to default', command=reset_binds, bg=self.dynamic_bg,
									fg=self.dynamic_text, bd=1)

		attr_title = Label(pop_ups_frame, text='Attributes', font=font_, bg=self.dynamic_overall, fg=self.dynamic_text)
		trans_s_title = Label(pop_ups_frame, text='Transparency configuration', font=font_, bg=self.dynamic_overall,
							  fg=self.dynamic_text)
		self.transparency_s = Scale(pop_ups_frame, from_=10, to=100, orient='horizontal',
									command=self.other_transparency, bg=self.dynamic_bg, fg=self.dynamic_text)
		self.transparency_s.set(95)
		top_most_s = Checkbutton(pop_ups_frame, text='TopMost', variable=self.all_tm_v,
								 bg=self.dynamic_bg, fg=self.dynamic_text, command=lambda: self.make_tm(False))
		open_m_s = Checkbutton(pop_ups_frame, text='Open at middle (some)', variable=self.open_middle_s,
							   bg=self.dynamic_bg, fg=self.dynamic_text)
		never_limit_s = Checkbutton(pop_ups_frame, text='Don\'t limit sizes', variable=self.limit_w_s,
									bg=self.dynamic_bg, fg=self.dynamic_text, command=self.limit_sizes)
		warning_title = Label(pop_ups_frame, text='Warnings', font=font_, bg=self.dynamic_overall, fg=self.dynamic_text)
		many_windows_checkbox = Checkbutton(pop_ups_frame, text='Many windows', variable=self.win_count_warn,
											bg=self.dynamic_bg, fg=self.dynamic_text, command=save_variables)
		corrector_title = Label(pop_ups_frame, text='Text corrector', font=font_, bg=self.dynamic_overall,
								fg=self.dynamic_text)
		corrector_preview = Checkbutton(pop_ups_frame, text='Preview changes', variable=self.corrector_check_changes,
										bg=self.dynamic_bg, fg=self.dynamic_text, command=save_variables)
		content_preference_title = Label(pop_ups_frame, text='Informative content prefrence', font=font_,
										bg=self.dynamic_overall, fg=self.dynamic_text)
		preference_frame = Frame(pop_ups_frame)
		preference_text = Radiobutton(preference_frame, value='txt', variable=self.content_preference_v, text='Text file')
		preference_html = Radiobutton(preference_frame, value='html', variable=self.content_preference_v, text='HTML file')
		other_w_title = Label(pop_ups_frame, text='Others', font=font_, bg=self.dynamic_overall, fg=self.dynamic_text)
		duplicate_windows = Checkbutton(pop_ups_frame, text='Allow duplicates', variable=self.adw,
										bg=self.dynamic_bg, fg=self.dynamic_text, command=save_variables)

		# placing all the widgets
		opt_title.pack(pady=5)

		settings_tabs.pack()
		styles_frame.pack(expand=True, fill=BOTH)
		functional_frame.pack(expand=True, fill=BOTH)
		settings_tabs.add(styles_frame, text='Styles')
		settings_tabs.add(functional_frame, text='Functions')
		settings_tabs.add(bindings_frame, text='Bindings')
		settings_tabs.add(pop_ups_frame, text='Other windows')

		# styles widgets
		cursor_title.grid(row=1, column=1)

		style_grid = (
			self.tcross_button, self.arrow_button, self.crosshair_button, 1, self.pencil_button, self.fleur_button,
			self.xterm_button, 2, self.style_clam, self.style_classic, self.style_vista, 2, self.relief_flat,
			self.relief_ridge, self.relief_groove)
		row_, column_ = 2, 0
		for widget in (style_grid):
			padx, pady = 0, 0
			if column_ == 0 or column_ == 2: padx = 2
			if widget == style_grid[-1]: pady = 3
			if not (isinstance(widget, int)):
				widget.grid(row=row_, column=column_, padx=padx, pady=3)
				column_ += 1
			else:
				row_, column_ = widget + row_, 0

		style_title.grid(row=4, column=1)
		relief_title.grid(row=6, column=1)
		nm_title.grid(row=8, column=1)
		self.night_frame.grid(row=9, column=1)
		nm_black_checkbox.grid(row=1, column=0)
		nm_blue_checkbox.grid(row=1, column=2)
		transparency_title.grid(row=10, column=1)
		transparency_config.grid(row=11, column=1)
		# transparency_set.grid(row=12, column=1)

		# functional widgets
		pack_functional = (
			hide_title, bar_frame, stt_title, stt_lang, file_opt_title, last_file_checkbox, usage_report_checkbox
			, title_other, check_v_checkbox, reset_button, tt_checkbox, auto_save_title, auto_save_frame, indent_title, indent_frame)
		for widget in pack_functional:
			widget.pack()
		filebar_check.grid(row=1, column=0)
		statusbar_check.grid(row=1, column=2)
		by_time_rb.grid(row=0, column=0)
		by_press_rb.grid(row=0, column=2)
		indent_tab.grid(row=0, column=0)
		indent_space.grid(row=0, column=2)
		preference_text.grid(row=0, column=0)
		preference_html.grid(row=0, column=2)

		# binding widgets + other windows options
		pack_binding = [state_title, file_actions_check, typefaces_action_check, edit_functions_check,
						textt_function_check,
						win_actions_check, auto_function_check, auto_list_check, reset_binds_button,
						order_title, order_frame]
		pack_other = [attr_title, top_most_s, open_m_s, never_limit_s, warning_title, many_windows_checkbox,
					  trans_s_title
			, self.transparency_s, corrector_title, corrector_preview, content_preference_title, preference_frame, other_w_title, duplicate_windows]
		pack_bin_oth = pack_binding + pack_other
		for index, widget in enumerate(pack_bin_oth):
			py = 0
			if pack_bin_oth[-1] == widget or pack_bin_oth[-3] == widget:
				py = 2
			widget.pack(pady=py)

		biggest_top.grid(row=0, column=0), biggest_bottom.grid(row=0, column=2)
		self.usage_time.pack()
		# creating buttons list

		self.opt_frames = styles_frame, functional_frame, self.opt_root, bindings_frame, pop_ups_frame, order_frame
		self.opt_commands = (nm_black_checkbox, nm_blue_checkbox, transparency_config, filebar_check, statusbar_check,
							 last_file_checkbox, reset_button, tt_checkbox, by_time_rb, by_press_rb, corrector_preview,
							 file_actions_check, typefaces_action_check, edit_functions_check, auto_function_check,
							 auto_list_check, indent_tab, indent_space, preference_text, preference_html,
							 textt_function_check, win_actions_check, open_m_s, never_limit_s, self.transparency_s,
							 usage_report_checkbox, biggest_top, biggest_bottom,
							 duplicate_windows, many_windows_checkbox, top_most_s, check_v_checkbox, reset_binds_button)
		self.opt_labels = (opt_title, cursor_title, style_title, relief_title, nm_title, transparency_title, hide_title,
						   stt_title, file_opt_title, title_other, auto_save_title, self.usage_time, state_title,
						   attr_title, trans_s_title, corrector_title, warning_title, other_w_title, order_title)

		self.dynamic_buttons = {'arrow': self.arrow_button, 'tcross': self.tcross_button, 'fleur': self.fleur_button,
								'pencil': self.pencil_button
			, 'crosshair': self.crosshair_button, 'xterm': self.xterm_button, 'clam': self.style_clam,
								'vista': self.style_vista, 'classic': self.style_classic
			, 'ridge': self.relief_ridge, 'groove': self.relief_groove, 'flat': self.relief_flat}

		# print([listt[:index:] for index, lst in enumerate(listt) if isinstance(lst, int)])
		self.adv_cursor_bs, self.adv_style_bs, self.adv_reliefs_bs = style_grid[:3] + style_grid[4:7], style_grid[
																									   8:11], style_grid[
																											  12:15]
		# self.adv_cursor_bs = self.tcross_button, self.arrow_button, self.crosshair_button, self.pencil_button, self.fleur_button, self.xterm_button
		# self.adv_style_bs = self.style_clam, self.style_vista, self.style_classic
		# self.adv_reliefs_bs = self.relief_groove, self.relief_flat, self.relief_ridge
		# change button colors
		if any((self.predefined_cursor, self.predefined_style, self.predefined_relief)):
			self.change_button_color('cursors', self.predefined_cursor)
			self.change_button_color('styles', self.predefined_style)
			self.change_button_color('relief', self.predefined_relief)

		stt_lang.bind('<<ComboboxSelected>>', stt_key)

		self.opt_root.update_idletasks()
		opt_sizes = self.opt_root.winfo_width(), self.opt_root.winfo_width()
		self.limit_list.append([self.opt_root, opt_sizes])

		self.record_list.append(f'> [{get_time()}] - advanced option window opened')

	def change_button_color(self, button_family, button):
		'''
		changes the colors of the buttons that are related to the customization of the program,
		to emphasize the chosen option
		light - not active
		light grey - active

		:param button_family:
		:param button:
		'''
		if self.op_active:
			self.determine_highlight()
			if button_family == 'cursors':
				self.last_cursor = [button_family, button]
				for adv_cursor_b in self.adv_cursor_bs:
					adv_cursor_b.config(bg=self._background, fg=self.tc)
			elif button_family == 'styles':
				self.last_style = [button_family, button]
				for adv_style_b in self.adv_style_bs:
					adv_style_b.config(bg=self._background, fg=self.tc)
			elif button_family == 'relief':
				self.last_r = [button_family, button]
				for adv_reliefs_b in self.adv_reliefs_bs:
					adv_reliefs_b.config(bg=self._background, fg=self.tc)
			self.dynamic_buttons[button].configure(bg='grey')

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
		goto_root = self.make_pop_ups_window(self.goto)
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
			if mode_ == 'ascending':
				mode_ = 'descending'
				str_loop, end_loop = 0, 1
			else:
				mode_ = 'ascending'
				str_loop, end_loop = 1, 0
			mode_button.config(text=f'Mode: {mode_}')

		def enter():
			for character in list(str(sort_input.get('1.0', 'end'))):
				if str(character).isdigit():
					self.EgonTE.insert(self.get_pos(), sort_input.get('1.0', 'end'))
					break

		# window creation
		sort_root = self.make_pop_ups_window(self.sort)
		# variables
		mode_ = 'ascending'
		str_loop, end_loop = 1, 0
		# UI components
		sort_text = Label(sort_root, text='Enter the numbers/characters you wish to sort:', font='arial 10 bold')
		sort_frame, sort_input, sort_scroll = self.make_rich_textbox(sort_root, size=[30, 15])
		sort_button = Button(sort_root, text='Sort', command=sort_)
		mode_button = Button(sort_root, text='Mode: ascending', command=mode)
		sort_insert = Button(sort_root, text='Insert', command=enter)
		sort_text.pack(fill=X, anchor=W, padx=3)
		sort_button.pack(pady=2)
		mode_button.pack(pady=2)
		sort_insert.pack(pady=2)

	def knowledge_window(self, mode: str):
		'''
		the window for the dictionary and wikipedia tools
		'''

		def redirect():
			if mode == 'wiki':
				self.wiki_thread.start()
			else:
				search()

		def search():
			meaning_box.configure(state=NORMAL)
			self.paste_b_info.configure(state=DISABLED)
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
					if self.last_wiki_image and not (self.wiki_var.get() == 4):
						meaning_frame.grid(row=3, column=1)
						self.paste_b_info.grid(row=5, column=1)
					self.last_wiki_image = False

					if self.wiki_var.get() == 3 or self.wiki_var.get() == 4:
						wiki_page = page(par_entry.get())

					if self.wiki_var.get() == 1:
						self.wiki_request = summary(par_entry.get())
					elif self.wiki_var.get() == 2:
						articles = wiki_search(par_entry.get())
						articles = list(articles)
						if articles:
							meaning_box.delete('1.0', 'end')
							for line, article in enumerate(articles):
								meaning_box.insert(f'{line}.0', article + '\n')
						else:
							output_ready = False
					elif self.wiki_var.get() == 3:
						self.wiki_request = f'{wiki_page.title}\n{wiki_page.content}'


					elif self.wiki_var.get() == 4:
						self.last_wiki_image = True
						self.image_selected_index = 0
						meaning_frame.grid_forget()
						self.paste_b_info.grid_forget()
						self.wiki_img_frame.grid(row=3, column=1)
						self.wiki_nav_frame.grid(row=4, column=1)
						self.wiki_nav_backwards.grid(row=4, column=0)
						self.wiki_nav_forward.grid(row=4, column=2)

						row_index = 0
						self.wiki_request = wiki_page.images
						self.wiki_img_list = []
						label_list = []
						for index, img_link in enumerate(self.wiki_requsest):
							# label_list.append(Label(self.wiki_img_frame))
							with urllib.request.urlopen(img_link) as img_url:
								continue_ = False
								# img_url.seek(0)
								img = img_url.read()
								# img = img.read()
								bytes_image = BytesIO(img)
								try:
									img = Image.open(bytes_image)
								except UnidentifiedImageError as e:
									image_short_name = os.path.basename(urlparse(img_link).path)
									url = urllib.request.urlretrieve(img_link, image_short_name)
									try:
										img = Image.open(image_short_name)
									except:
										continue_ = True
									finally:
										os.remove(image_short_name)
								if continue_:
									continue

								multi = 1, 2
								starting_limit = 600
								img_condition = True
								while img_condition:
									img_width, img_height = img.size
									if (img_width > starting_limit * multi[0]) or (
											img_height > starting_limit * multi[0]):
										img_width, img_height = img_width // multi[1], img_height // multi[1]
										img = img.resize((img_width, img_height))
										multi = multi[0] + 1, multi[1] + 1
									else:
										img_condition = False
										img = ImageTk.PhotoImage(img)
										self.wiki_img_list.append(img)
										break

						if self.wiki_img_list:
							navigate_pics('initial')

						'''+ 
						initial image - takes time to load / or indexes bugs
						'''

					if not (self.wiki_var.get() == 2):
						meaning_box.delete('1.0', 'end')
						meaning_box.insert('1.0', self.wiki_requsest)
				except requests.exceptions.ConnectionError:
					messagebox.showerror(self.title_struct + 'error', 'check your internet connection')
					output_ready = False
				except exceptions.DisambiguationError as e:
					messagebox.showerror(self.title_struct + 'error',
										 'check your searched term\ninserting the most close match')
					print(f'Error :{e}')
					search_terms = (str(e)).split('\n')
					closest = search_terms[1]
					par_entry.delete(0, END)
					par_entry.insert(0, closest)
					output_ready = False
				except exceptions.PageError:
					messagebox.showerror(self.title_struct + 'error', 'Invalid page ID')
					output_ready = False

			if output_ready:
				self.paste_b_info.configure(state=ACTIVE)
			else:
				self.paste_b_info.configure(state=DISABLED)
			meaning_box.configure(state=DISABLED)

		def paste():
			content_to_paste = meaning_box.get('1.0', 'end')
			self.EgonTE.insert(self.get_pos(), content_to_paste)

		'''+ make when navigating that the window will more from the upward pos and not the bottom'''

		def navigate_pics(mode, event=False):
			def bind_links(event=False):
				webbrowser.open_new(self.wiki_requsest[self.image_selected_index])

			if self.wiki_var.get() == 4 and self.wiki_requsest:  # and self.wiki_img_list
				# if self.mode
				if mode == 'b' or mode == 'f':
					if mode == 'f':
						limit_value, index_change, limit_reset = -1, 1, 0
					elif mode == 'b':
						limit_value, index_change, limit_reset = 0, -1, self.wiki_img_list.index(self.wiki_img_list[-1])
					try:
						limit_condition = self.wiki_img_list[self.image_selected_index] == self.wiki_img_list[
							limit_value]
					except IndexError:
						limit_condition = True
					if not limit_condition:
						self.image_selected_index += index_change
					else:
						self.image_selected_index = limit_reset
					print(self.image_selected_index)
				elif mode == 'initial':
					self.image_selected_index = 0
					self.wiki_image_label.grid(row=3, column=1)
					# for image in
					# image_condition =  self.wiki_img_list[self.image_selected_index].verify()
					# if not image_condition:

				self.wiki_image_label.unbind_all('<ButtonRelease-1>')
				self.wiki_image_label.grid_forget()
				try:
					selected_image = self.wiki_img_list[self.image_selected_index]
				except IndexError:
					self.image_selected_index = 0
					selected_image = self.wiki_img_list[self.image_selected_index]

				self.wiki_image_label.configure(image=selected_image)
				self.wiki_image_label.grid(row=3, column=1)
				self.wiki_image_label.bind('<ButtonRelease-1>', bind_links)
			else:
				messagebox.showerror(self.title_struct + 'wiki', 'you are not in images mode \ didn\'t search')

		par_root = Toplevel()
		self.opened_windows.append(par_root)
		# self.func_window[self.knowledge_window] = par_root
		par_root.protocol('WM_DELETE_WINDOW', lambda: self.close_pop_ups(par_root, th=self.wiki_thread))
		self.make_tm(par_root)
		if self.limit_w_s.get():
			par_root.resizable(False, False)
		par_root.attributes('-alpha', self.st_value)
		par_entry = Entry(par_root, width=35)
		knowledge_search = Button(par_root, text='Search', command=redirect)
		meaning_frame = Frame(par_root)
		meaning_box = Text(meaning_frame, height=15, width=50, wrap=WORD)
		meaning_box.configure(state=DISABLED)
		self.paste_b_info = Button(par_root, text='Paste to ETE', command=paste, bd=1)
		self.paste_b_info.configure(state=DISABLED)

		par_entry.grid(row=1, column=1, pady=3)
		knowledge_search.grid(row=2, column=1, pady=3)
		if not (mode == 'wiki' and self.wiki_var.get() == 4):
			meaning_box.grid(row=3, column=1)
			self.paste_b_info.grid(row=5, column=1, pady=4)
			self.last_wiki_image = False
		else:
			self.wiki_img_frame.grid(row=3, column=1)
			self.wiki_nav_frame.grid(row=4, column=1)
			self.wiki_nav_backwards.grid(row=4, column=0)
			self.wiki_nav_forward.grid(row=4, column=2)
			self.last_wiki_image = True

		par_root.unbind('<Control-Key-.>')
		par_root.unbind('<Control-Key-,>')
		if mode == 'wiki':
			par_root.title(self.title_struct + 'Wikipedia')
			self.wiki_requsest = ''
			self.wiki_img_list = []
			self.wiki_img_frame = Frame(par_root, width=35, height=40)
			self.wiki_image_label = Label(self.wiki_img_frame)
			self.wiki_nav_frame = Frame(self.wiki_img_frame)
			self.wiki_nav_forward = Button(self.wiki_nav_frame, text='>>', command=lambda: navigate_pics(mode='f'))
			self.wiki_nav_backwards = Button(self.wiki_nav_frame, text='<<', command=lambda: navigate_pics(mode='b'))
			par_root.bind('<Control-Key-.>', lambda e: navigate_pics('f', event=e))
			par_root.bind('<Control-Key-,>', lambda e: navigate_pics('b', event=e))

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

		else:
			par_root.title(self.title_struct + 'dictionary')
			self.record_list.append(f'> [{get_time()}] - Dictionary tool window opened')

	def virtual_keyboard(self):
		'''
		virtual keyboard tool, that have most of the important functionalities:
		tab, symbols, caps, numbers, and english characters in the qwert organization
		'''

		def close_vk():
			self.opened_windows.remove(keyboard_root)
			keyboard_root.destroy()
			self.vk_active = False

		global last_abc
		# window creation and settings
		keyboard_root = Toplevel()
		self.make_tm(keyboard_root)
		keyboard_root.attributes('-alpha', self.st_value)
		if self.limit_w_s.get():
			keyboard_root.resizable(False, False)
		self.sym_var1 = False
		self.sym_var2 = False
		keyboard_root.configure(bg='black')
		keyboard_root.protocol('WM_DELETE_WINDOW', close_vk)
		self.opened_windows.append(keyboard_root)
		if not (self.vk_active) and keyboard_root in self.opened_windows:
			self.vk_active = True
		last_abc = 'upper'
		exp = ' '  # global variable

		def quick_grid(w_list, row_number):
			for index, widget in enumerate(w_list):
				widget.grid(row=row_number, column=index, ipady=10)

		def press(expr: str):
			global exp
			self.EgonTE.insert(self.get_pos(), expr)

		def tab():
			if self.indent_method.get() == 'space':
				exp = '    '
			else:
				exp = '		'
			self.EgonTE.insert(self.get_pos(), exp)

		def modes(mode: str):
			global last_abc
			modes_buttons = caps, sym_button

			if self.night_mode.get():
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
				sym_button.configure(command=lambda: modes('sym'))
				sym_button_2.configure(command=lambda: modes('sym2'))

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
				if not (self.sym_var1):
					for counter, sn in enumerate(sym_n):
						characters_by_order[counter].configure(text=sn,
															   command=lambda i=sn: press(i))
					sym_button.configure(command=lambda: modes(last_abc), bg=highlighted_color)
					if self.sym_var2:
						self.sym_var2 = False
						sym_button_2.configure(bg=self.dynamic_button, command=lambda: modes('sym2'))
				self.sym_var1 = not (self.sym_var1)

			elif mode == 'sym2':
				if not self.sym_var2:
					for counter, sn in enumerate(syn_only):
						characters_by_order[counter].configure(text=sn,
															   command=lambda i=sn: press(i))
					sym_button_2.configure(command=lambda: modes(last_abc), bg=highlighted_color)
					if self.sym_var1:
						self.sym_var1 = False
						sym_button.configure(bg=self.dynamic_button, text='1!*', command=lambda: modes('sym'))
				self.sym_var2 = not (self.sym_var2)

			if mode == 'upper' or mode == 'lower':
				self.sym_var1 = False
				self.sym_var2 = False
				sym_button.configure(command=lambda: modes('sym'), bg=self.dynamic_button)
				sym_button_2.configure(bg=self.dynamic_button, command=lambda: modes('sym2'))

		btn_frame = Frame(keyboard_root)
		extras_frame = Frame(keyboard_root)
		btn_frame.pack()
		extras_frame.pack()

		# creating buttons
		b_width = 6
		Q, W, E, R, T, Y, U, I, O, P, A, S, D, F, G, H, J, K, L, Z, X, C, V, B, N, M = \
			[Button(btn_frame, text=button, width=b_width, command=lambda: press(button)) for button in characters_str]


		sym_list = '{', '}', '\\', ';', '"', '<', '>', '/', '?', ',', '.'
		cur, cur_c, back_slash, semi_co, d_colon, less_sign, more_sign, slas, q_mark, coma, dot = \
			[Button(btn_frame, text=button, width=b_width, command=lambda: press(button)) for button in sym_list]

		space = Button(extras_frame, text='Space', width=b_width, command=lambda: press(' '))
		caps = Button(extras_frame, text='Caps', width=b_width, command=lambda: modes('lower'))
		sym_button = Button(extras_frame, text='1!*', width=b_width, command=lambda: modes('sym'))
		sym_button_2 = Button(extras_frame, text='ƒ√€', width=b_width, command=lambda: modes('sym2'))
		new_line_b = Button(extras_frame, text='Enter', width=b_width, command=lambda: press('\n'))
		open_b = Button(extras_frame, text='(', width=b_width, command=lambda: press('('))
		close_b = Button(extras_frame, text=')', width=b_width, command=lambda: press(')'))

		tab_b = Button(extras_frame, text='Tab', width=b_width, command=tab)



		# placing buttons
		grid_list_1 = (Q, W, E, R, T, Y, U, I, O, P, cur, cur_c)
		grid_list_2 = (A, S, D, F, G, H, J, K, L, semi_co, d_colon, dot)
		grid_list_3 = (Z, X, C, V, B, N, M, less_sign, more_sign, slas, q_mark, coma)

		quick_grid(grid_list_1, 1)
		back_slash.grid(row=1, column=10, ipady=10)
		quick_grid(grid_list_2, 2)
		quick_grid(grid_list_3, 3)

		space.grid(row=0, column=1, ipadx=90, ipady=10)
		new_line_b.grid(row=0, column=2, ipadx=14, ipady=10)
		open_b.grid(row=0, column=3, ipady=10)
		close_b.grid(row=0, column=4, ipady=10)
		tab_b.grid(row=0, column=5, ipady=10)
		caps.grid(row=0, column=6, ipady=10)
		sym_button.grid(row=0, column=7, ipady=10)
		sym_button_2.grid(row=0, column=8, ipady=10)

		self.record_list.append(f'> [{get_time()}] - Virtual Keyboard tool window opened')

		characters = A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z
		characters_by_order = Q, W, E, R, T, Y, U, I, O, P, A, S, D, F, G, H, J, K, L, Z, X, C, V, B, N, M
		symbols = semi_co, cur, cur_c, back_slash, d_colon, less_sign, more_sign, slas, q_mark, coma, dot, open_b, close_b
		functional_buttons = space, new_line_b, tab_b, caps, sym_button, sym_button_2
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
		if self.limit_w_s.get():
			keyboard_root.resizable(False, False)

		modes('lower')

		self.vk_sizes = win_w, win_h
		self.limit_list.append([keyboard_root, self.vk_sizes])

		keyboard_root.mainloop()  # using ending point

	def emoji_detection(self, event=None, via_settings: bool = False, reverse : bool =False):
		'detects emojis and replaces their identification mark with the emoji itself'
		# initial condition to not activate the function every interaction with the text box
		# peruse: not cause lag and prevent bugs
		cursor_pos = self.get_pos()
		active = False
		rep_t = False
		if via_settings:
			active = True
		elif not active:
			keys = list(map(str, printable[:-22]))

			for key in keys:

				if is_pressed(key):
					active = True
					break
			if not active:
				for key in keys:
					try:
						if key == self.EgonTE.get(1.0, self.EgonTE.index(CURRENT))[-1]:
							active = True
							break
					except IndexError:
						pass

		if active:
			if self.automatic_emojis_v.get() or via_settings:
				fail_msg = ''
				lang = get_k_lang()[1]
				if not lang:
					lang = 'en'

				content = self.EgonTE.get(1.0, END).split(' ')
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

	def e_list(self, mode: str):
		'''
		window that can show a formated list of emojis, morse code, and roman numbers dependent on the function's parameter
		'''
		extra = ''

		if mode == 'emojis':
			ejc_list = emoji.get_emoji_unicode_dict('en')
		elif mode == 'morse':
			ejc_list = morse_code_dict
		elif mode == 'roman':
			ejc_list = (dict(islice(roman_dict.items(), 7)))

			extra = {}
			for key, value in roman_dict.items():
				if key not in ejc_list.keys():
					extra[key] = value

		e_root = self.make_pop_ups_window(self.e_list, f'{mode} list')
		text_frame, sym_text, scroll = self.make_rich_textbox(e_root)

		for sym_, sym_code_ in ejc_list.items():
			sym_text.insert('end', f'{sym_} - {sym_code_}\n')

		if extra:
			sym_text.insert('end', '\n')

			# roman extras is combinations of letters that form unique numbers when they are together!
			if mode == 'roman':
				sym_text.insert('end', 'popular combinations')

			sym_text.insert('end', '\n')

			for sym_, sym_code_ in extra.items():
				sym_text.insert('end', f'{sym_} - {sym_code_}\n')

		sym_text.configure(state=DISABLED)

	def file_info(self):
		'''
		basic and general statistics of any file, work on the file youre running in the program - and if you dont use
		a saved file it will ask for another file location
		'''
		res_font = 'consolas 14'

		if self.file_name:
			file_info_name = self.file_name

		else:
			file_info_name = self.get_file('Open', ' file to get info about')
		try:
			if file_info_name:
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
				file_info_root = self.make_pop_ups_window(self.find_text, 'File information')
				# creating the widgets
				access_time = datetime.fromtimestamp(stat.st_atime)
				file_type = os.path.splitext(file_info_name)[-1][1:]
				lib_path = Path(file_info_name)
				try:
					owner = f'{lib_path.owner()} : {lib_path.group()}'
				except:
					owner = ''
				# attaching info to labels
				size_label = Label(file_info_root, text=f'file size - {file_size} bytes', font=res_font)
				modified_time_label = Label(file_info_root, text=f'file modified time - {modified_time}', font=res_font)
				creation_time_label = Label(file_info_root, text=f'file creation time - {creation_time}', font=res_font)
				access_time_label = Label(file_info_root, text=f'file accessed time - {access_time}', font=res_font)
				file_type_label = Label(file_info_root, text=f'file type - {file_type}', font=res_font)
				if owner:
					owner_label = Label(file_info_root, text=f'file owner - {owner}', font=res_font)

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

	def auto_save_time(self):
		if self.file_name:
			if self.autosave_by_t.get():
				t = 300
				while self.auto_save_v.get():
					while t:
						mins, secs = divmod(t, 60)
						timer = '{:02d}:{:02d}'.format(mins, secs)
						time.sleep(1)
						t -= 1
					self.save()
			else:
				self.save()



	def file_template_generator(self, event=None):
		"""
		Delegate to the standalone Document Template Generator popup implementation.
		"""
		return open_document_template_generator(self, event)


	def auto_save_press(self, event=False):
		if self.file_name and self.auto_save_v.get() and (self.autosave_by_p.get()):
			self.save()

	def setup_auto_lists(self, default_enabled: bool | None = None):
		'Initialize Auto Lists with nested functions. Snake case names, no leading underscores, letter rollover, and unit tests.'

		# Local state (closures)
		pattern_state = {'ready': False}
		compiled_patterns = {}
		binding_ids = {'return': None}
		last_applied_enabled = {'value': None}

		def build_list_patterns():
			if pattern_state['ready']:
				return

			# ASCII bullets + common Unicode bullets/dashes (– \u2013, — \u2014)
			bullet_chars = r'\-\+\*•●◦‣▪·\u2013\u2014'

			# Bulleted item at line start:
			# - Capture indent (group 1) and bullet (group 2)
			# - Allow optional space after bullet, but require some non-space later
			compiled_patterns['bullet'] = compile(rf'^(\s*)([{bullet_chars}])(?:\s+|)(?=\S)')

			# Numbered item at line start: 1., 1), 1:, 1-, 1], 1} + required space after separator
			compiled_patterns['number'] = compile(r'^(\s*)(\d+)([.\):\-\]\}])\s+')

			# Lettered item at line start: [a-z]+. or [A-Z]+. or ) variants, space required after separator
			# Accept multi-letter sequences (aa, ab, AA, AB) to support rollover
			compiled_patterns['letter'] = compile(r'^(\s*)([A-Z]+|[a-z]+)([.)])\s+')

			# Only-marker lines (no non-space content after marker)
			compiled_patterns['only_bullet'] = compile(rf'^\s*([{bullet_chars}])\s*$')
			compiled_patterns['only_number'] = compile(r'^\s*\d+[.\):\-\]\}]\s*$')
			compiled_patterns['only_letter'] = compile(r'^\s*[A-Za-z]+[.)]\s*$')

			pattern_state['ready'] = True

		def next_alpha_sequence(alpha: str) -> str:
			'Increment an alphabetical sequence with rollover, preserving case (z -> aa, Z -> AA).'
			if not alpha:
				return 'a'
			is_upper = alpha[0].isupper()
			base_a = 'A' if is_upper else 'a'

			# Convert to 0-based base-26
			values = [ord(ch) - ord(base_a) for ch in alpha]
			i = len(values) - 1
			carry = 1
			while i >= 0 and carry:
				values[i] += carry
				if values[i] >= 26:
					values[i] = 0
					carry = 1
					i -= 1
				else:
					carry = 0
			if carry:
				# Overflow at the highest digit: prepend a new 'a'/'A'
				values = [0] + values
			return ''.join(chr(v + ord(base_a)) for v in values)

		def handle_return_auto_list(key_event):
			'Enter handler: continues bullets/numbers/letters, preserves indent, smart termination.'
			try:
				if not bool(self.aul.get()):
					return None
			except Exception:
				return None

			target_widget = key_event.widget

			# Let default behavior replace selection
			if target_widget.tag_ranges('sel'):
				return None

			# Shift+Enter -> plain newline (Shift mask 0x0001)
			if getattr(key_event, 'state', 0) & 0x0001:
				return None

			# Current line
			current_line_start = target_widget.index('insert linestart')
			current_line_end = target_widget.index('insert lineend')
			current_line_text = target_widget.get(current_line_start, current_line_end)

			# Only auto-continue at EOL or when only whitespace follows
			if target_widget.compare('insert', '<', current_line_end) and target_widget.get('insert',
																							current_line_end).strip():
				return None

			build_list_patterns()

			match_bullet = compiled_patterns['bullet'].match(current_line_text)
			match_number = compiled_patterns['number'].match(current_line_text)
			match_letter = compiled_patterns['letter'].match(current_line_text)
			if not (match_bullet or match_number or match_letter):
				return None

			trimmed_line = current_line_text.rstrip()
			indent_text = (match_bullet or match_number or match_letter).group(1)

			# Smart termination: line is only the marker
			if (match_bullet and compiled_patterns['only_bullet'].fullmatch(trimmed_line)) or \
					(match_number and compiled_patterns['only_number'].fullmatch(trimmed_line)) or \
					(match_letter and compiled_patterns['only_letter'].fullmatch(trimmed_line)):
				target_widget.edit_separator()
				target_widget.delete(current_line_start, current_line_end)
				target_widget.insert(current_line_start, indent_text + '\n' + indent_text)
				target_widget.edit_separator()
				return 'break'

			# Smart termination: caret at/inside marker and nothing meaningful after
			insert_index = target_widget.index('insert')
			try:
				_, col_str = insert_index.split('.')
				caret_column = int(col_str)
			except Exception:
				caret_column = 0

			if match_number:
				marker_length = len(indent_text) + len(match_number.group(2)) + len(match_number.group(3)) + 1
			elif match_letter:
				alpha_seq = match_letter.group(2)
				marker_length = len(indent_text) + len(alpha_seq) + 1 + 1  # letters + separator + space
			else:
				bullet_col = len(indent_text) + 1
				has_space = len(current_line_text) > bullet_col and current_line_text[bullet_col] == ' '
				marker_length = len(indent_text) + 1 + (1 if has_space else 0)

			text_after_caret = target_widget.get('insert', current_line_end)
			if caret_column <= marker_length and text_after_caret.strip() == '':
				target_widget.edit_separator()
				target_widget.delete(current_line_start, current_line_end)
				target_widget.insert(current_line_start, indent_text + '\n' + indent_text)
				target_widget.edit_separator()
				return 'break'

			# Continuation: number, letter, or bullet
			if match_number:
				n = int(match_number.group(2))
				sep = match_number.group(3)
				next_marker = f'{n + 1}{sep} '
				continuation = indent_text + next_marker
			elif match_letter:
				alpha_seq = match_letter.group(2)
				sep = match_letter.group(3)
				next_seq = next_alpha_sequence(alpha_seq)
				continuation = indent_text + f'{next_seq}{sep} '
			else:
				bullet_char = match_bullet.group(2)
				continuation = indent_text + f'{bullet_char} '

			target_widget.edit_separator()
			target_widget.insert('insert', '\n' + continuation)
			target_widget.edit_separator()
			return 'break'

		def toggle_auto_lists(enable: bool) -> None:
			'Bind/unbind the <Return> handler idempotently.'
			if binding_ids['return'] is not None:
				try:
					self.EgonTE.unbind('<Return>', binding_ids['return'])
				except Exception:
					pass
			binding_ids['return'] = None

			if enable:
				binding_ids['return'] = self.EgonTE.bind('<Return>', handle_return_auto_list, add='+')

		def apply_auto_lists(key_event=None) -> None:
			'Variable manager: reads self.aul and applies the Return binding state.'
			try:
				enabled_flag = bool(self.aul.get()) if default_enabled is None else bool(default_enabled)
			except Exception:
				enabled_flag = bool(getattr(self, 'aul', False))

			if last_applied_enabled['value'] is enabled_flag:
				return
			last_applied_enabled['value'] = enabled_flag

			try:
				self.EgonTE.after(0, toggle_auto_lists, enabled_flag)
			except Exception:
				toggle_auto_lists(enabled_flag)

		def run_auto_lists_tests() -> dict:
			'Lightweight unit tests for alpha rollover, numbers, and bullets (pure logic paths).'
			results = {'passed': 0, 'failed': 0, 'cases': []}

			def check(case_name, condition):
				ok = bool(condition)
				results['cases'].append((case_name, ok))
				if ok:
					results['passed'] += 1
				else:
					results['failed'] += 1

			# Alpha rollover tests
			check('alpha a->b', next_alpha_sequence('a') == 'b')
			check('alpha z->aa', next_alpha_sequence('z') == 'aa')
			check('alpha aa->ab', next_alpha_sequence('aa') == 'ab')
			check('alpha az->ba', next_alpha_sequence('az') == 'ba')
			check('alpha zz->aaa', next_alpha_sequence('zz') == 'aaa')
			check('alpha A->B', next_alpha_sequence('A') == 'B')
			check('alpha Z->AA', next_alpha_sequence('Z') == 'AA')
			check('alpha AZ->BA', next_alpha_sequence('AZ') == 'BA')
			check('alpha ZZ->AAA', next_alpha_sequence('ZZ') == 'AAA')

			# Number formatting sanity (mirrors continuation format)
			check('number 1.', f'1. ' == '1. ')
			check('number 2)', f'2) ' == '2) ')

			# Bullet formatting sanity
			for ch in ['-', '+', '*', '•', '—']:
				check(f'bullet {ch}', f'{ch} ' == f'{ch} ')

			return results

		# Public API (snake case, no leading underscores)
		self.handle_return_auto_list = handle_return_auto_list
		self.toggle_auto_lists = toggle_auto_lists
		self.build_list_patterns = build_list_patterns
		self.apply_auto_lists = apply_auto_lists
		self.next_alpha_sequence = next_alpha_sequence
		self.run_auto_lists_tests = run_auto_lists_tests

		# Legacy compatibility (can be removed later if nothing depends on them)
		self._on_return_auto_list = handle_return_auto_list
		self.enable_auto_lists = toggle_auto_lists
		self._ensure_list_regex = build_list_patterns
		self.aul_var = apply_auto_lists

		# Ensure options UI compatibility
		if not hasattr(self, 'bindings_dict') or not isinstance(self.bindings_dict, dict):
			self.bindings_dict = {}
		self.bindings_dict['autol'] = getattr(self, 'aul', None)

		# Apply on checkbox change and once at start
		try:
			self.aul.trace_add('write', lambda *args: apply_auto_lists())
		except Exception:
			pass
		apply_auto_lists()



	def compare(self):
		'''
			   function that is comparing the file that you are using to other selected file from your computer,
			   in a plain way - basic numeric statistic and content difference
			   '''
		file_content = self.EgonTE.get('1.0', 'end').splitlines()
		another_file = filedialog.askopenfilename(initialdir=os.getcwd(), title='Open file to compare',
												  filetypes=text_extensions)
		if another_file:
			try:
				another_file = open(another_file, 'r')
				another_fc = another_file.read()
				# warning about possible lag
				proceed = True
				if len(another_fc) > 400:
					if not (
							messagebox.askyesno('EgonTE',
												'This file is pretty big\nare you sure you want to compere it?')):
						proceed = False

				if proceed:
					# window creation
					self.compare_root = self.make_pop_ups_window(self.compare)
					main_frame = Frame(self.compare_root)
					# the precise difference in content between files with the Differ function
					difference = Differ()
					c_difference_frame = Frame(main_frame)
					c_difference_title = Label(main_frame, text='Content difference', font='arial 14 underline')
					files_difference = ''.join(difference.compare(file_content, another_fc)).replace('  ', ' ')
					cd_inner_frame,  content_difference, cd_scroll = self.make_rich_textbox(c_difference_frame,
										   font='arial 12')
					content_difference.insert(END, files_difference)
					content_difference.configure(state=DISABLED)

					# the difference in the count of : words, lines, characters, spaces
					def counts_file(file):
						num_words, num_lines, num_charc, num_spaces = 0, 0, 0, 0
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

					count_frame = Frame(main_frame)
					file_1_frame = Frame(count_frame, bd=1, relief='groove')
					file_2_frame = Frame(count_frame, bd=1, relief='groove')
					file_counts_title = Label(count_frame, text='File stats', font='arial 14 underline')
					fc_title1 = Label(file_1_frame, text='Your first file', font='arial 10 underline')
					fc_title2 = Label(file_2_frame, text='Your second file', font='arial 10 underline')
					file_1_count = Label(file_1_frame, text=counts_file(file_content))
					file_2_count = Label(file_2_frame, text=counts_file(another_fc))

					main_frame.pack(expand=True, fill=BOTH)
					c_difference_title.pack()
					c_difference_frame.pack(expand=True, fill=BOTH)

					count_frame.pack()
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
				self.compare_root.destroy()

	def corrector(self):
		def insert():
			if self.advance_correction:
				self.EgonTE.delete('1.0', 'end')
				self.EgonTE.insert('1.0', corrected_content)

		def preview_ui():

			def res(mode: bool):
				self.advance_correction = mode
				insert()
				preview_root.destroy()

			preview_root = self.make_pop_ups_window(preview_ui, 'Preview corrector changes')
			title = Label(preview_root, text='Accept this text changes', font='arial 12 underline')
			title.pack()
			text_frame, changes_text_box, text_scroll = self.make_rich_textbox(preview_root)
			difference = Differ()
			differ_content = ''.join(difference.compare(content, corrected_content))
			changes_text_box.insert('1.0', differ_content)
			decision_frame = Frame(preview_root)
			accept_b = Button(decision_frame, text='Accept', command=lambda: res(True))
			deny_b = Button(decision_frame, text='Deny', command=lambda: res(False))

			text_frame.pack()
			decision_frame.pack()
			accept_b.grid(row=0, column=0)
			deny_b.grid(row=0, column=2)

		content = self.EgonTE.get('1.0', 'end')
		corrected_content = TextBlob(content).correct()
		if self.corrector_check_changes.get():
			preview_ui()
		else:
			self.advance_correction = True
			insert()

	def organize(self):
		'''+
		(note for the developer) need to remake this function
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
		This method now delegates to the new popup implementation in web_scrapping_popup.py
		'''
		open_web_scrapping_popup(self)


	def handwriting(self):
		open_handwriting(self)

	def encryption(self):
		open_encryption(self)

	def find_replace(self, event=False):
		return open_find_replace(self, event)


	def natural_language_process(self, function: str):
		open_nlp(self, preset_function=function)


	def saved_settings(self, special_mode: str =None):

		'''+ shorten'''

		'''
		the saved settings function managed a huge portion of the functionality of the saved variables,
		likes assigning them, check if the file exists, have the default dictionary of the files values,
		save the file, etc.
		'''
		file_name = 'EgonTE_settings.json'

		if special_mode == 'save':
			os.remove(file_name)
			with open(file_name, 'w') as f:
				dump(self.data, f)
				print('save 1', self.data)

			if self.data['open_last_file']:
				self.save_last_file()

		else:

			if os.path.exists(file_name):
				print('saved settings file exist')
				with open(file_name, 'r') as f:
					self.data = load(f)
					print(self.data)
				self.match_saved_settings()

				return False

			else:
				print('saved settings file doesn\'t exist')
				self.data = self.make_default_data()

				with open(file_name, 'w') as f:
					dump(self.data, f)
				# self.data = load(file_name)
				# print(self.data)

				return True

	@staticmethod
	def make_default_data():
		return {'night_mode': False, 'status_bar': True, 'file_bar': True, 'cursor': 'xterm',
				'style': 'clam',
				'word_wrap': True, 'reader_mode': False, 'auto_save': True, 'relief': 'ridge',
				'transparency': 100, 'toolbar': True, 'open_last_file': '', 'text_twisters': False,
				'night_type': 'black', 'preview_cc': False, 'fun_numbers': True, 'usage_report': False,
				'check_version': False, 'window_c_warning': True, 'allow_duplicate': False}

	def match_saved_settings(self):

		self.reader_mode_v.set(self.data['reader_mode'])
		self.bars_active.set(self.data['status_bar'] and self.data['file_bar'])
		self.show_statusbar.set(self.bars_active.get())
		self.status_ = self.data['status_bar']
		self.file_ = self.data['file_bar']
		self.show_toolbar.set(self.data['toolbar'])
		self.night_mode.set(self.data['night_mode'])
		self.textwist_special_chars.set(self.data['text_twisters'])
		self.nm_palette.set(self.data['night_type'])
		self.cs.set(self.data['style'])
		self.custom_cursor_v.set(self.data['cursor'])
		self.word_wrap_v.set(self.data['word_wrap'])
		self.auto_save_v.set(self.data['auto_save'])
		self.corrector_check_changes.set(self.data['preview_cc'])
		self.win_count_warn.set(self.data['window_c_warning'])
		self.adw.set(self.data['allow_duplicate'])
		self.fun_numbers.set(self.data['fun_numbers'])
		self.usage_report_v.set(self.data['usage_report'])
		self.check_ver_v.set(self.data['check_version'])
		self.predefined_cursor = self.custom_cursor_v.get()
		self.predefined_style = self.cs.get()
		self.predefined_relief = self.data['relief']
		if self.last_file_v.get():
			self.file_name = self.data['open_last_file']

	def text_decorators(self):
		'''
		the text decoration function is a window that let you make a bigger style of text with many symbols.
		there is 3 styles and the text can be outputted horizontally and vertically.
		also there is a UI for the process that make you manage it very easily

		(for the developer) asterisk broken
		'''
		global result_box
		inline = False
		result_box = ''

		def enter():
			self.ascii_dict, self.ascii_alph, newline_n = characters_dict[self.chosen_text_decorator]
			alphabet = 'abcdefghijklmnopqrstuvwxyz 0123456789?!,.-+'
			decorator_input = text_box.get('1.0', END).lower()

			if decorator_input:
				try:
					if self.dec_plc.get() == 'vertical':
						dec = 'horizontal'
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
						divided_list = []

						for asc_value in self.ascii_alph:
							asc_value = list(asc_value)
							asc_value[-1], asc_value[-2] = '    ', '    '
							asc_value = ''.join(asc_value)

						for word in decorator_input:
							if word in modified_ascii_dict.keys():
								word_list.append(modified_ascii_dict[word])

						print(word_list)

						for word in word_list:
							divided_list.append(word.split('\n'))

						print(divided_list)

						for index in range(newline_n):
							for line in divided_list:
								try:
									res += ''.join(line[index])
									res += '    '
								except IndexError:
									pass
							res += '\n'

						print(res)


					else:
						dec = 'vertical'
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
					result_box = Text(result_frame)
					result_scroll = ttk.Scrollbar(result_frame, orient=dec)
					if self.dec_plc.get() == 'horizontal':
						result_scroll.config(command=result_box.yview)
						result_scroll.pack(side=RIGHT, fill=Y)
						result_box.configure(wrap=WORD, yscrollcommand=result_scroll.set)
					elif self.dec_plc.get() == 'vertical':
						result_scroll.config(command=result_box.xview)
						result_scroll.pack(side=BOTTOM, fill=X)
						result_box.configure(wrap=NONE, xscrollcommand=result_scroll.set)

					result_box.insert('1.0', res)
					result_box.configure(state=DISABLED)
					result_frame.pack(expand=True, fill=BOTH)
					result_box.pack(fill=BOTH, expand=True)
				except ValueError:
					messagebox.showerror('EgonTE', 'there isn\'t a single character from the alphabet')
			else:
				messagebox.showerror('EgonTE', 'text box is empty')

		def change_style(s: str):
			self.chosen_text_decorator = s
			for style in td_styles_dict.values():
				style.configure(bg='SystemButtonFace')
			td_styles_dict[self.chosen_text_decorator].configure(bg='light grey')

		def cft():
			content = self.EgonTE.get('1.0', 'end')
			text_box.insert('end', content)

		def ptt():
			content = result_box.get('1.0', 'end')
			self.EgonTE.insert('end', '\n')
			self.EgonTE.insert('end', content)

		def show_sc():
			if self.ascii_dict:
				available_characters = ', '.join(self.ascii_dict.keys())
				sc_window = Toplevel()
				sc_frame, sc_text, sc_scroll = self.make_rich_textbox(sc_window)
				sc_text.insert(1.0, available_characters)
				sc_text.configure(state=DISABLED)

		# settings variables
		self.dec_plc = StringVar()
		self.dec_plc.set('horizontal')
		# window and it's widgets
		td_root = self.make_pop_ups_window(self.text_decorators)
		td_root.minsize(355, 311)
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
		vertical_radio = Radiobutton(settings_frame, text='Vertical', variable=self.dec_plc, value='vertical')
		horizontal_radio = Radiobutton(settings_frame, text='Horizontal', variable=self.dec_plc, value='horizontal')
		# text decorator styles
		styles_title = Label(b_frame, text='Styles', font='arial 10 underline')
		bash_style = Button(b_frame, text='bash (#)', command=lambda: change_style('bash'))
		binary_style = Button(b_frame, text='binary (10)', command=lambda: change_style('binary'))
		asterisk_style = Button(b_frame, text='asterisk (*)', command=lambda: change_style('asterisk'))
		show_characters_button = Button(b_frame, text='Show supported characters', bd=1, command=show_sc)

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
		show_characters_button.grid(row=6, column=1)

		td_styles_dict = {'bash': bash_style, 'binary': binary_style, 'asterisk': asterisk_style}
		change_style('bash')

		td_root.update_idletasks()
		print(td_root.winfo_width(), td_root.winfo_height())


	def start_stopwatch(self):
		if getattr(self, "_stopwatch_running", False):
			return
		self.start_time = time.perf_counter()
		self.start_date = datetime.now().strftime('%Y-%m-%d')
		self._stopwatch_running = True
		self._update_stopwatch()

	def _update_stopwatch(self):
		if not getattr(self, "_stopwatch_running", False):
			return
		elapsed = time.perf_counter() - self.start_time
		td = timedelta(seconds=elapsed)
		hh = int(td.total_seconds()) // 3600
		mm = (int(td.total_seconds()) % 3600) // 60
		ss = int(td.total_seconds()) % 60
		if self.op_active:
			self.usage_time.configure(text=f"Usage time: {hh:02}:{mm:02}:{ss:02}")
		self.after(500, self._update_stopwatch)


	def merge_files(self):
		'''
		this function created a shared content from the content that on the main text box and from a content of
		another file
		'''
		data = ''

		def outport_data(where):
			ask_op_root.destroy()
			if where == 'new':
				save_file_name = filedialog.asksaveasfilename(title='Save merged file', filetypes=text_extensions)
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
			self.make_tm(ask_op_root)
			ask_op_root.title(self.title_struct + 'merge files')
			q_label = Label(ask_op_root, text='where you would like to put the merged data?')
			this_file = Button(ask_op_root, text='In this file', command=lambda: outport_data('this'))
			new_file = Button(ask_op_root, text='In new file', command=lambda: outport_data('new'))

			q_label.grid(row=1, column=1)
			this_file.grid(row=2, column=0)
			new_file.grid(row=2, column=2)

	def delete_file(self, custom: str = ''):
		if self.file_name or custom:
			advance = False
			remove_fn = False
			if self.file_name and not custom:
				if messagebox.askyesno('EgonTE', 'Are tou sure you want to delete this file?'):
					self.EgonTE.delete('1.0', 'end')
					advance = True
					file_to_del = self.file_name
					remove_fn = True
			if custom:
				advance = True
				file_to_del = custom

			if advance:
				os.remove(file_to_del)
				self.file_bar.configure(text=f'deleted {file_to_del}')

			if remove_fn:
				self.file_name = ''

		else:
			messagebox.showerror(self.title_struct + 'error', 'you are not using a file')

	def insp_quote(self, op_msg: bool=False):
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
				if not op_msg:
					messagebox.showerror(self.title_struct + 'error', 'Something went wrong!')

		if quote:
			if op_msg:
				return quote
			else:
				self.EgonTE.insert('1.0', '\n')
				self.EgonTE.insert('1.0', quote)

	def save_images(self, widget_name, root_name, upper_name=False, sp_mode=False) -> str:
		'''
		this function saves an images with the info that its get from its parameters via taking screenshot of it,
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
			global loc_text, temp_text, time_text, weather_desc
			city_name = city_entry.get()
			ask_w.destroy()

			city_name = city_name.replace(' ', '+').replace('_', '+')
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
				weather_root = self.make_pop_ups_window(activate_weather, custom_title=(self.title_struct + 'Weather'))
				weather_root.tk.call('wm', 'iconphoto', weather_root._w, self.weather_image)
				w_font = 'arial 10'

				if '+' in location:
					location = location.replace('+', ' ')

				loc_text = ('Location: ' + location.capitalize())
				temp_text = ('Temperature: ' + temperature + '&deg;C')
				time_text = ('Time: ' + time)
				weather_desc = ('Weather Description: ' + info)

				loc = Label(weather_root, text=loc_text, font=w_font)
				temp = Label(weather_root, text=temp_text, font=w_font)
				tim = Label(weather_root, text=time_text, font=w_font)
				des = Label(weather_root, text=weather_desc, font=w_font)
				copy_button = Button(weather_root, text='Copy', command=copy_paste_weather, pady=2, bd=1)
				paste_button = Button(weather_root, text='Paste to ETE', command=lambda: copy_paste_weather('p')
									  , pady=2, bd=1)

				loc.pack(fill='none', expand=True)
				temp.pack(fill='none', expand=True)
				tim.pack(fill='none', expand=True)
				des.pack(fill='none', expand=True)
				copy_button.pack(fill='none', expand=True)
				paste_button.pack(fill='none', expand=True)

		def copy_paste_weather(mode: str = 'copy'):
			all_content = f'{loc_text}\n{temp_text}\n{time_text}\n{weather_desc}'
			if mode == 'copy':
				copy(all_content)
			else:
				self.EgonTE.insert('end', '\n')
				self.EgonTE.insert('end', all_content)

		def rand_city():
			chosen_city = choice(city_list)
			city_entry.delete(0, END)
			city_entry.insert(0, chosen_city)

		# a more advanced window to select the city
		ask_w = Toplevel()
		self.make_tm(ask_w)
		ask_w.title(self.title_struct + 'city selector')
		if self.limit_w_s.get():
			ask_w.resizable(False, False)

		ask_title = Label(ask_w, text='Select city', font=self.titles_font)
		weather_subtitle = Label(ask_w, text='What is the name of the city\n you want to get the weather for')
		city_entry = Entry(ask_w)
		random_city = Button(ask_w, text='Random known city', command=rand_city, bd=1)
		enter_city = Button(ask_w, text='Enter', command=lambda: self.open_windows_control(activate_weather), bd=1)

		ask_title.grid(row=0, column=1, pady=3)
		weather_subtitle.grid(row=1, column=1)
		city_entry.grid(row=2, column=1)
		random_city.grid(row=3, column=1, pady=3)
		enter_city.grid(row=4, column=1, pady=5)


	def send_email(self):
		return open_email(self)


	def chatGPT(self):
		'''
		this function attempts to create a chatGPT workspace like the website via the text editor
		'''
		open_chatgpt(self)

	def dallE(self):
		'''
		this function will try to return you the result of a simple DallE prompt with some options
		'''
		open_dalle(self)


	def full_screen(self, event=None):
		self.fs_value = not (self.fs_value)
		self.attributes('-fullscreen', self.fs_value)


	def topmost(self):
		self.tm_value = not (self.tm_value)
		self.attributes('-topmost', self.tm_value)

	def transcript(self):
		'''
		Get a transcript from YouTube (if available) or from a local audio file (wav/mp3).
		- No imports inside this method.
		- Pop-up roots are created via make_pop_ups_window.
		- Text areas are created via make_rich_textbox.
		- Everything is nested in this main method.
		- Selection window is an actual, interactive UI (no simpledialog).
		'''

		def _render_text_with_copy(result_root, text_output: str):
			text_frame, text_widget, scroll = self.make_rich_textbox(result_root)
			text_widget.insert('1.0', text_output)
			text_widget.configure(state=DISABLED)
			Button(result_root, text='Copy',
				   command=lambda: (result_root.clipboard_clear(), result_root.clipboard_append(text_output))).pack(pady=6)

		def _compose_youtube_transcript_text(transcript_items):
			lines = []
			for index, item in enumerate(transcript_items):
				start_time = item.get('start', 0)
				line_text = item.get('text', '')
				lines.append(f'time: {start_time:.2f}, iteration: {index} | content: {line_text}')
			return '\n'.join(lines)

		def _transcribe_youtube_from_entry(video_id: str, parent_root):
			if not video_id:
				messagebox.showerror(self.title_struct + 'transcript', 'Please enter a YouTube video ID.')
				return

			try:
				items = YouTubeTranscriptApi.get_transcript(video_id)
			except Exception as e:
				messagebox.showerror(self.title_struct + 'transcript', f'Failed to fetch YouTube transcript:\n{e}')
				return

			result_root = self.make_pop_ups_window(_transcribe_youtube_from_entry, custom_title='YouTube transcript')
			try:
				_render_text_with_copy(result_root, _compose_youtube_transcript_text(items))
			except Exception as e:
				messagebox.showerror(self.title_struct + 'transcript', f'Failed to display transcript:\n{e}')
				try:
					self.close_pop_ups(result_root)
				except Exception:
					pass

		def _transcribe_local_audio_file():
			audio_path = filedialog.askopenfilename(
				title='Open audio file to transcribe',
				filetypes=[('Audio files', '*.mp3 *.wav'), ('mp3 file', '*.mp3'), ('wav file', '*.wav')]
			)
			if not audio_path:
				return

			result_root = self.make_pop_ups_window(_transcribe_local_audio_file, custom_title='File transcript')

			# Prepare a non-destructive WAV path if needed
			base_name, extension = os.path.splitext(audio_path)
			extension = extension.lower()
			created_temp_wav = False
			wav_path = audio_path

			try:
				if extension == '.mp3':
					# Convert mp3 -> wav into a sibling file; do not rename the original
					wav_path = base_name + '_converted.wav'
					AudioSegment.from_mp3(audio_path).export(wav_path, format='wav')
					created_temp_wav = True
				elif extension != '.wav':
					messagebox.showerror(self.title_struct + 'transcript', 'Unsupported file type. Choose an mp3 or wav file.')
					self.close_pop_ups(result_root)
					return
			except Exception as e:
				messagebox.showerror(self.title_struct + 'transcript', f'Failed preparing audio:\n{e}')
				try:
					self.close_pop_ups(result_root)
				except Exception:
					pass
				return

			# Transcribe the prepared WAV
			try:
				recognizer = Recognizer()
				with AudioFile(wav_path) as source:
					audio_blob = recognizer.record(source)
				text_output = recognizer.recognize_google(audio_blob)
				_render_text_with_copy(result_root, text_output)
			except Exception as e:
				messagebox.showerror(self.title_struct + 'transcript', f'Failed to transcribe audio:\n{e}')
				try:
					self.close_pop_ups(result_root)
				except Exception:
					pass
			finally:
				# Clean up temporary wav if created
				try:
					if created_temp_wav and wav_path and os.path.exists(wav_path):
						os.remove(wav_path)
				except Exception:
					pass

		# Interactive selection window UI (root created via make_pop_ups_window)
		if yt_api:
			selection_root = self.make_pop_ups_window(self.transcript, custom_title='Transcript')
			# Title
			title_label = Label(selection_root, text='Transcript source', font='arial 13 bold')
			title_label.pack(pady=(6, 2))

			# Description
			desc_label = Label(selection_root, text='Choose a source and proceed. For YouTube, paste a video ID and press Enter or Fetch.',
							   font='arial 9')
			desc_label.pack(pady=(0, 8))

			# Main container
			main_frame = Frame(selection_root)
			main_frame.pack(padx=10, pady=6)

			# YouTube section
			youtube_frame = LabelFrame(main_frame, text='YouTube', padx=8, pady=8, font='arial 10 bold')
			youtube_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 8))

			youtube_id_label = Label(youtube_frame, text='Video ID:', font='arial 10')
			youtube_id_entry = Entry(youtube_frame, width=36)
			youtube_status_label = Label(youtube_frame, text='', font='arial 9')

			def _update_status(msg: str, good=False):
				try:
					youtube_status_label.configure(fg=('dark green' if good else 'red'), text=msg)
				except Exception:
					pass

			def _on_fetch_click():
				_update_status('Fetching transcript...', good=False)
				selection_root.update_idletasks()
				_transcribe_youtube_from_entry(youtube_id_entry.get().strip(), selection_root)
				_update_status('Done (or see error dialog).', good=True)

			def _on_clear_click():
				youtube_id_entry.delete(0, END)
				_update_status('', good=False)

			def _on_paste_click():
				try:
					clip = selection_root.clipboard_get()
				except Exception:
					clip = ''
				if clip:
					youtube_id_entry.delete(0, END)
					youtube_id_entry.insert(0, clip.strip())
					_update_status('Pasted from clipboard.', good=True)
				else:
					_update_status('Clipboard is empty.', good=False)

			def _on_youtube_entry_return(event=None):
				_on_fetch_click()

			youtube_id_label.grid(row=0, column=0, sticky='w', pady=(0, 4))
			youtube_id_entry.grid(row=0, column=1, sticky='ew', padx=(6, 0), pady=(0, 4))
			youtube_frame.grid_columnconfigure(1, weight=1)

			youtube_buttons_frame = Frame(youtube_frame)
			youtube_buttons_frame.grid(row=1, column=0, columnspan=2, sticky='w')
			youtube_fetch_btn = Button(youtube_buttons_frame, text='Fetch', bd=1, command=_on_fetch_click)
			youtube_clear_btn = Button(youtube_buttons_frame, text='Clear', bd=1, command=_on_clear_click)
			youtube_paste_btn = Button(youtube_buttons_frame, text='Paste', bd=1, command=_on_paste_click)
			youtube_fetch_btn.grid(row=0, column=0, padx=(0, 8))
			youtube_clear_btn.grid(row=0, column=1, padx=(0, 8))
			youtube_paste_btn.grid(row=0, column=2, padx=(0, 0))

			youtube_status_label.grid(row=2, column=0, columnspan=2, sticky='w', pady=(6, 0))

			# Bindings for better UX
			youtube_id_entry.bind('<Return>', _on_youtube_entry_return)
			youtube_id_entry.focus_set()

			# File section
			file_frame = LabelFrame(main_frame, text='Local audio file', padx=8, pady=8, font='arial 10 bold')
			file_frame.grid(row=0, column=1, sticky='nsew')

			file_hint_label = Label(file_frame, text='Choose an mp3 or wav file and transcribe it.', font='arial 10')
			file_browse_btn = Button(file_frame, text='Browse...', bd=1, command=_transcribe_local_audio_file)

			file_hint_label.grid(row=0, column=0, sticky='w', pady=(0, 6))
			file_browse_btn.grid(row=1, column=0, sticky='w')

			# Bottom controls
			bottom_frame = Frame(selection_root)
			bottom_frame.pack(fill='x', padx=10, pady=(8, 10))
			close_btn = Button(bottom_frame, text='Close', bd=1, command=lambda: self.close_pop_ups(selection_root))
			close_btn.pack(side='right')

			# Resize behavior
			main_frame.grid_columnconfigure(0, weight=1)
			main_frame.grid_columnconfigure(1, weight=1)
		else:
			_transcribe_local_audio_file()


	def content_stats(self):
		'''
		This function will output you the stats of the content of the file,
		many numeric values, presentation in a table about the usage of words and characters, and more
		'''
		res_font = 'arial 10'
		special_characters = list(printable[62:])
		print(special_characters)

		stats_root = self.make_pop_ups_window(self.content_stats)
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
		# set can contain duplicate values so by checking the length we can see the number of different characters
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

		print(f'splitted content: {words_per_line}')

		m_words_per_line = []
		for word in words_per_line:
			if ' ' in word:
				word = word.split(' ')
			m_words_per_line.extend(word)

		words_per_line = m_words_per_line
		print(f'splitted content: {words_per_line}')

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

	def record_logs(self):
		'''
		the ability to use this function is activated when you active developer mode via options menu.
		this function captures all / most the main events that happened in the program and writes them
		in order with the time of the occurrence
		'''

		def close_record():
			self.opened_windows.remove(self.log_root)
			self.record_active = False
			self.log_root.destroy()

		def save_info():
			file_name = filedialog.asksaveasfilename(title='Save record as file') + '.txt'
			info = record_tb.get(1.0, END)
			with open(file_name, 'w') as f:
				for record in self.record_list:
					f.write(record + '\n')

		def update_content():
			while self.record_active:
				time.sleep(1)
				if self.record_active:
					# condition is important if we want the tool to be a lot smoother, but it's also fine without it
					record_string = ''.join(self.record_list).replace('\n', '')
					record_textbox = record_tb.get(1.0, END).replace('\n', '')
					if record_string != record_textbox:
						record_tb.configure(state=NORMAL)
						record_tb.delete(1.0, END)
						for record in self.record_list:
							record_tb.insert('end', record + '\n')
						record_tb.configure(state=DISABLED)
				else:
					break

		self.log_root = Toplevel()
		self.make_tm(self.log_root)
		self.log_root.title(self.title_struct + 'events\' record')
		self.log_root.minsize(400, 250)
		self.record_active = True
		self.log_root.protocol('WM_DELETE_WINDOW', close_record)
		self.log_root.attributes('-alpha', self.st_value)
		self.opened_windows.append(self.log_root)
		text_frame, record_tb, rc_scrollbar = self.make_rich_textbox(self.log_root)

		# menu for functions
		record_menu = Menu(self.log_root)
		self.log_root.config(menu=record_menu)
		record_menu.add_cascade(label='Copy', command=lambda: copy(record_tb.get(1.0, END)))
		record_menu.add_cascade(label='Paste (ETE)',
								command=lambda: self.EgonTE.insert(self.get_pos(), record_tb.get(1.0, END)))
		record_menu.add_cascade(label='Save', command=save_info)

		# initial output
		for record in self.record_list:
			record_tb.insert('end', record + '\n')

		record_tb.configure(state=DISABLED)

		Thread(target=update_content).start()

		self.record_night = record_tb
		self.log_root.mainloop()

	def call_record(self):
		'''
		like the call settings function.
		calls the function with a thread in a simplified block of code,
		make that if the window is opened instead of calling the function again, it will show you the window
		'''
		if not self.record_active:
			self.record_object = self.record_logs
			self.record_object()
		else:
			self.log_root.attributes('-topmost', True)
			self.log_root.attributes('-topmost', False)

	def manage_menus(self, mode: str):
		'''
		this window manage the diffrent menu modes that the program have, is can delete menus, call the create menus
		function, change / add things to capture the mode that the user selected for the program
		'''
		if mode == 'dev':
			if self.dev_mode.get():
				self.app_menu.delete('Record')
				self.app_menu.delete('Git')
				self.options_menu.delete('prefer gpu')
				try:
					self.menus_components.remove(self.git_menu)
				except:
					self.menus_components.pop(-1)
			else:
				self.app_menu.add_cascade(label='Record', command=self.call_record)
				self.options_menu.add_checkbutton(label='prefer gpu', variable=self.prefer_gpu)

				self.git_menu = Menu(self.app_menu, tearoff=False)
				self.app_menu.add_cascade(label='Git', menu=self.git_menu)
				self.git_menu.add_command(label='Pull', command=lambda: self.gitp('pull'))
				self.git_menu.add_command(label='Push', command=lambda: self.gitp('push'))
				self.git_menu.add_command(label='Commit', command=lambda: self.gitp('commit'))
				self.git_menu.add_command(label='Add', command=lambda: self.gitp('add'))
				self.git_menu.add_separator()
				self.git_menu.add_command(label='Clone', command=lambda: self.gitp('clone'))
				self.git_menu.add_command(label='Commit data', command=lambda: self.gitp('commit data'))
				self.git_menu.add_command(label='Repository Information',
										  command=lambda: self.gitp('repo info'))
				self.git_menu.add_separator()
				self.git_menu.add_command(label='Custom command', command=lambda: self.gitp('execute'))

				self.menus_components.append(self.git_menu)

			self.dev_mode.set(not (self.dev_mode.get()))
		elif mode == 'tools':
			if not (self.sta.get()):
				self.app_menu.delete('Colors+')
				self.app_menu.delete('Tools')
			else:

				self.app_menu.delete('NLP')
				self.app_menu.delete('Options')
				self.app_menu.delete('Help')
				self.app_menu.delete('Patch notes')
				self.app_menu.delete('External links')

				if self.dev_mode.get():
					self.app_menu.delete('Record')
					self.app_menu.delete('Git')
					self.options_menu.delete('prefer gpu')

				self.create_menus(initial=False)

				if self.dev_mode.get():
					self.app_menu.add_cascade(label='Record', command=self.call_record)
		elif mode == 'python':
			# python menu
			if self.python_file:
				self.app_menu.add_cascade(label='Run', command=self.run_code)
				self.app_menu.add_cascade(label='Clear console', command=self.clear_console)

				self.options_menu.add_separator()
				self.options_menu.add_checkbutton(label='Auto clear console', variable=self.auto_clear_c)
				self.options_menu.add_checkbutton(label='Save by running', variable=self.sar)

			# self.sta.set(not(self.sta.get()))

	def emoticons(self, reverse : bool):
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
		self.spc_mode = 'emojis'

		def change_mode(b: str = 'emojis'):
			self.spc_mode = b
			for button in b_mode_dict.values():
				button.configure(background='SystemButtonFace')
			b_mode_dict[b].configure(bg='light grey')
			list_of.configure(text=f'List of {self.spc_mode}')
			transform.configure(text=f'Transform to {self.spc_mode}')
			random_e.configure(text=f'Random {self.spc_mode}')

		def transf(reverse: bool = False):
			if self.spc_mode == 'emojis':
				self.emoji_detection(via_settings=True, reverse=reverse)
			elif self.spc_mode == 'morse':
				self.morse_c_translator(reverse=reverse)
			elif self.spc_mode == 'roman':
				self.roman_numbers_translator(reverse=reverse)
			else:
				self.emoticons(reverse=reverse)

		def random_ejc():
			rdm_e = (self.ejc_values[self.spc_mode])

			if rdm_e:
				rdm_e = choice(list(rdm_e)) + ' '
				self.EgonTE.insert('end', rdm_e)

		ejc_root = self.make_pop_ups_window(self.emojicons_hub, 'Symbols translator')
		m_title = Label(ejc_root, text='Choose a mode', font=self.titles_font)
		emojis = Button(ejc_root, text='Emojis', command=lambda: change_mode('emojis'), borderwidth=1)
		emoticons = Button(ejc_root, text='Emoticons', command=lambda: change_mode('emoticons'), borderwidth=1,
						   state=emoticons_library)
		morse_c = Button(ejc_root, text='Morse Code', command=lambda: change_mode('morse'), borderwidth=1)
		roman_numbers = Button(ejc_root, text='Roman numbers', command=lambda: change_mode('roman'), borderwidth=1)
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

		b_mode_dict = {'emojis': emojis, 'emoticons': emoticons, 'morse': morse_c, 'roman': roman_numbers}
		b_func_list = transform, list_of, random_e
		ejc_list = emoji.get_emoji_unicode_dict('en')
		self.ejc_values = {'emojis': ejc_list.values(), 'morse': morse_code_dict.values(), 'roman': roman_dict.keys()}
		change_mode()

	# according to the morse code chart
	def morse_c_translator(self, reverse=False):
		'''
		translator of morse code and vice versa

		:param reverse:
		'''
		if not (reverse):
			content = reSplit('; |, |\*|\n', self.EgonTE.get('1.0', 'end'))
		else:
			content = reSplit('[^.-]|\s', self.EgonTE.get('1.0', 'end'))
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
			content = content.replace('IV', 'IIII').replace('IX', 'VIIII').replace('XL', 'XXXX').replace('XC', 'LXXXX')
			content = content.replace('CD', 'CCCC').replace('CM', 'DCCCC')
			content = reSplit('; |, |\*|\n', content)  # reSplit('; |, |\*|\n', content)
			content = (''.join(content)).split(' ')

			for roman_value in content:
				word_value = 0
				if roman_value.isalpha():
					if len(roman_value) > 1:
						for separated_roman_value in roman_value:
							print(separated_roman_value)
							if separated_roman_value.upper() in roman_dict.keys():
								word_value += roman_dict[separated_roman_value.upper()]
							else:
								new_content.append(roman_value)

						# value of an entire word full of roman numbers values
						new_content.append(str(word_value))

					else:
						if roman_value.upper() in roman_dict.keys():
							new_content.append(str(roman_dict[roman_value.upper()]))
						else:
							new_content.append(roman_value)

					new_content.append(' ')

		# converting arabic numbers to roman numbers
		else:
			# works on a really limited list of numbers !!
			print('arabic to roman')
			rev_roman_dict = {}
			for key, value in roman_dict.items():
				rev_roman_dict[value] = key

			content = reSplit('; |, |\*|\n', content)  # reSplit('; |, |\*|\n', content)
			content = ''.join(content)
			content = content.split(' ')

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

		# outputting the results
		new_content = ''.join(new_content)
		self.EgonTE.delete(1.0, 'end')
		self.EgonTE.insert('1.0', new_content)

	def run_code(self):
		'''
		function that can be used while using a python file

		used to run python file and write its output
		'''
		if self.file_name:

			if self.sar.get():
				self.save()

			if self.auto_clear_c.get():
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
				self.output_box.configure(state='readonly')
		except NameError:
			pass

	def save_last_file(self):
		if self.file_name:
			if os.path.exists(self.file_name):
				self.data['open_last_file'] = os.path.abspath(self.file_name)

	def gitp(self, action: str):
		'''
		for this function you need to activate dev mode
		collection of git actions that can be used from the program

		:param action:
		'''
		open_git_tool(self, action)


	def call_settings(self):
		'''
		by calling the advance settings by another function we get the flexibility of clean code
		and the ability to show the user their current settings window instead of opening another one if it already
		opened
		'''
		if not self.op_active:
			self.settings_object = self.advance_options
			Thread(target=self.settings_object).start()
		else:
			self.opt_root.attributes('-topmost', True)
			self.opt_root.attributes('-topmost', False)

	def update_insert_image_list(self, event=False):
		if self.in_images_list_n:
			for image in self.in_images_list_n:
				try:
					index = self.EgonTE.index(image)
				except TclError:
					self.in_images_list_n.remove(image)

			if self.ins_images_open:
				self.update_images_list()

	def update_images_list(self, general: bool  =False):
		update = False
		if not general:
			entry_content = self.image_entry.get().lower()
			if entry_content:
				update = True
		else:
			update = True
			entry_content = ' '

		print(update)

		if update:
			self.current_images_list.delete(0, END)
			for image in self.in_images_list_n:
				display_name = os.path.basename(image)
				if (entry_content in display_name.lower()) or general:
					self.current_images_list.insert(END, display_name)

	def insert_image(self):
		'''
		Insert images (beta):
		insert multiple images, and manage them,
		remove some images / all images
		add images
		rename images
		direct yourself to their index
		'''

		def add_image(sp_name: str = '', sp_image: str = ''):
			if not (sp_name):
				self.image_name = filedialog.askopenfilename(title='Open file', filetypes=img_extensions)
				self.current_inserted_image = PhotoImage(self.image_name)
			else:
				self.image_name = sp_name
				self.current_inserted_image = sp_image
			if self.image_name:
				self.EgonTE.image_create('current', image=self.current_inserted_image, name=f'{self.image_name} ')
				self.bg_count += 1
				self.in_images_list_n.append(self.image_name)
				self.in_images_dict[self.image_name] = self.current_inserted_image
				self.update_images_list(general=True)

		def get_specific_image():
			current_image = self.image_entry.get()

			in_images_list_display = []
			for image in self.in_images_list_n:
				display_name = os.path.basename(image)
				in_images_list_display.append(display_name)

			found_image = False
			if current_image:
				if current_image in in_images_list_display:
					found_image = True

			if not (found_image):
				current_image = self.current_images_list.get(ACTIVE)
				if current_image:
					if current_image in in_images_list_display:
						found_image = True

			if found_image:
				for count, path in enumerate(self.in_images_list_n):
					base_name = os.path.basename(path)
					if base_name == current_image:
						current_image = path
						break

			return current_image, found_image

		def remove_specific(sp_image: str = ''):
			if not sp_image:
				current_image, found_image = get_specific_image()
			else:
				current_image, found_image = sp_image, True

			if found_image:
				image_index = self.EgonTE.index(f'{current_image} ')
				self.EgonTE.delete(image_index)
				self.bg_count -= 1
				self.in_images_dict.pop(current_image)
				self.in_images_list_n.remove(current_image)
				self.update_images_list(general=True)
			else:
				messagebox.showerror('EgonTE', 'didn\'t found the image you wish to remove')

		def remove_all():
			for image in self.in_images_list_n:
				image_index = self.EgonTE.index(f'{image} ')
				self.EgonTE.delete(image_index)
			self.bg_count = 1
			self.image_name = ''
			self.in_images_list_n = []
			self.update_images_list(general=True)

		def rename_image():
			current_image, found_image = get_specific_image()
			if found_image:
				new_name = simpledialog.askstring('EgonTE', 'how would you like to call the image?')
				if new_name:
					if not (new_name.lower().endswith(('.png', '.jpg', '.jpeg'))):
						new_name = f'{new_name}.png'
					# for count, image in enumerate(self.in_images_list_n):
					#     if image == current_image:
					#         self.in_images_list_n[count] == new_name
					#         break
					# self.in_images_list_n.replace(current_image, new_name)
					actual_image = self.in_images_dict[current_image]
					print(actual_image)
					if actual_image:
						self.image_entry.delete(0, END)
						remove_specific(current_image)
						add_image(sp_name=new_name, sp_image=actual_image)
						self.image_entry.insert(0, new_name)
				else:
					messagebox.showerror('EgonTE', 'New name cannot be blank')
			# update_list(general=True)

		def show_image():
			pass

		def point_image_index():
			current_image, found_image = get_specific_image()
			if found_image:
				image_index = self.EgonTE.index(f'{current_image} ')
				self.EgonTE.icursor(image_index)
				self.EgonTE.insert(image_index, '')
				self.EgonTE.focus_set()

		def keyrelease_events(events=False):
			self.update_images_list()
			# enter()

		def close_insertim():
			self.opened_windows.remove(image_root)
			self.ins_images_open = False
			image_root.destroy()

		image_root = Toplevel(bg=self.dynamic_overall)
		image_root.title(self.title_struct + 'Insert images')
		image_root.protocol('WM_DELETE_WINDOW', close_insertim)
		image_root.attributes('-alpha', self.st_value)
		self.opened_windows.append(image_root)
		self.func_window[self.insert_image] = image_root
		self.ins_images_open = True
		if self.limit_w_s.get():
			image_root.resizable(False, False)
		self.selected_in_image = StringVar()

		title = Label(image_root, text='Insert images', font='arial 14 underline', bg=self.dynamic_bg,
					  fg=self.dynamic_text)

		self.image_entry = Entry(image_root)

		list_frame = Frame(image_root, bg=self.dynamic_overall)
		self.current_images_list = Listbox(list_frame, width=25, height=5, bg=self.dynamic_bg,
										   fg=self.dynamic_text)  # textvariable=self.selected_in_image)
		image_scroll = ttk.Scrollbar(list_frame, command=self.current_images_list.yview)
		self.current_images_list.configure(yscrollcommand=image_scroll.set)

		buttons_frame = Frame(image_root, bg=self.dynamic_overall)
		remove = Button(buttons_frame, text='Remove', command=remove_specific, bd=1, bg=self.dynamic_bg,
						fg=self.dynamic_text)
		add = Button(buttons_frame, text='Add', command=add_image, bd=1, bg=self.dynamic_bg, fg=self.dynamic_text)
		remove_all = Button(buttons_frame, text='Remove all', command=remove_all, bd=1, bg=self.dynamic_bg,
							fg=self.dynamic_text)
		rename_image = Button(buttons_frame, text='Rename image', command=rename_image, bd=1, bg=self.dynamic_bg,
							  fg=self.dynamic_text)
		point_image = Button(buttons_frame, text='Point to image', command=point_image_index, bd=1, bg=self.dynamic_bg,
							 fg=self.dynamic_text)
		show_image = Button(buttons_frame, text='Show image', command=show_image, bd=1, bg=self.dynamic_bg,
							fg=self.dynamic_text)

		self.current_images_list.bind('<<ListboxSelect>>', lambda e: fill_by_click(self.self.image_entry, e, self.current_images_list))
		self.image_entry.bind('<KeyRelease>', keyrelease_events)

		title.grid(row=0, column=1, pady=5)
		self.image_entry.grid(row=1, column=1, pady=2)
		list_frame.grid(row=2, column=1, pady=2)
		buttons_frame.grid(row=3, column=1, pady=5, padx=20)

		image_scroll.pack(side=RIGHT, fill=Y, expand=True)
		self.current_images_list.pack(fill=BOTH, expand=True)

		remove.grid(row=0, column=0)
		add.grid(row=0, column=1, pady=4)
		remove_all.grid(row=0, column=2)
		point_image.grid(row=1, column=0, padx=2)
		rename_image.grid(row=1, column=2, padx=2)
		# show_image.grid(row=1, column=2, padx=2)

		self.in_im_commands = remove, add, remove_all, rename_image, point_image, show_image, self.current_images_list, title
		self.in_im_bgs = image_root, buttons_frame, list_frame

	def change_file_ui(self):

		'''
		tool that allows the user to change their file extension to another textual file extension
		'''

		self.change_text_var = StringVar()

		def change_file_extension():
			if self.file_name:
				chosen_ext = self.change_text_var.get()
				if chosen_ext:
					old_name = self.file_name
					path_object = Path(old_name)
					if self.del_previous_file.get():
						self.delete_file(custom=old_name)
					self.file_name = path_object.with_suffix('.' + chosen_ext)
					self.open_status_name = self.file_name
					print(f'New file\'s name: {self.file_name}')
					self.save()
					self.file_bar.configure(text=f'File extension changed to {chosen_ext}')
				else:
					messagebox.showerror('EgonTE', 'choose desired file\'s extension!')
			else:
				messagebox.showerror('EgonTE', 'Function can\'t be used without a file!')

		cfui = self.make_pop_ups_window(self.change_file_ui, f'{self.title_struct} Change file type')
		title = Label(cfui, text='Change text to:', font='arial 12 underline')
		cfui_combo = ttk.Combobox(cfui, width=10, textvariable=self.change_text_var)
		cfui_combo['values'] = 'txt', 'html', 'log', 'asc', 'py'
		delete_last_title = Label(cfui, text='Delete file', font='arial 10 underline')
		delete_last_combo = Checkbutton(cfui, text='with previous extension', variable=self.del_previous_file)
		change = Button(cfui, text='Change type', font='arial 10 bold', command=change_file_extension)

		title.pack(padx=50)
		cfui_combo.pack(pady=5)
		delete_last_title.pack()
		delete_last_combo.pack()
		change.pack(pady=3)


	def determine_highlight(self):
		'''
		highlight color of text in text's finding / regex functions
		'''
		if self.night_mode.get():
			if not (self.nm_palette.get() == 'blue'):
				self._background = '#064663'
				self.tc = '#ECB365'
			else:
				self._background = '#110022'
				self.tc = 'green'
		else:
			self._background = 'SystemButtonFace'
			self.tc = 'black'

	def search_functions(self):

		'''
		a tool that allows to run function by writing its name and clicking enter
		have a interactive list that shows all the functions
		the list have mods based on category of the functions
		'''

		def close_search():
			self.search_active = True
			self.opened_windows.remove(fn_root)
			fn_root.destroy()

		def update_list():
			entry_content = self.find_function.get().lower()
			if entry_content:
				self.functions_list.delete(0, END)
				for term in self.functions_names:
					if entry_content in term.lower():
						self.functions_list.insert(END, term)

		def keyrelease_events(events=False):
			update_list()
			enter()

		def configure_modes(event=False):
			'''+ others and all doesnt work'''
			insert_list = []
			self.functions_list.delete(0, END)
			if self.fn_mode.get() and self.fn_mode.get() != 'all':
				chosen_functions_names = list(self.conjoined_functions_only[self.fn_mode.get()].keys())
				insert_list.extend(
					[fixed_function_name.replace('|', ' ').replace('.', '').replace('!', '') for fixed_function_name in
					 chosen_functions_names])
			else:
				insert_list.extend(
					[fixed_function_name.replace('|', ' ').replace('.', '').replace('!', '') for fixed_function_name in
					 self.functions_names])
			for ins in insert_list:
				self.functions_list.insert(END, f'{ins[0].upper()}{ins[1:]}')

		def enter():
			desired_func = self.find_function.get()
			if desired_func:
				func = self.combined_func_dict[desired_func]
				if func:
					func()

		def make_c_dict(*dicts):
			self.combined_func_dict = {}
			for dictionary in dicts:
				for key, value in dictionary.items():
					key = key.replace('!', '').replace('.', '').replace('|', ' ').capitalize()
					self.combined_func_dict[key] = value

		# all vs file vs edit vs tool , etc.
		make_c_dict(self.file_functions, self.edit_functions, self.tool_functions, self.nlp_functions,
					self.color_functions
					, self.links_functions, {'options': self.call_settings},
					{'Help': lambda: self.open_windows_control(lambda: self.info_page('help'))},
					{'Patch notes': lambda: self.open_windows_control(lambda: self.info_page('patch_notes'))}
					, {'Search': self.search_functions})


		self.conjoined_functions_only['others'] = self.other_functions
		self.functions_names = []
		for index, functions_groups in enumerate(self.conjoined_functions_only.values()):
			if isinstance(functions_groups, dict):
				self.functions_names.extend(functions_groups.keys())
			else:
				self.functions_names.append(list(self.conjoined_functions_only.keys())[index])

		self.fn_mode = StringVar()

		fn_root = self.make_pop_ups_window(self.search_functions, external_variable=True)
		self.search_active = True
		fn_root.protocol('WM_DELETE_WINDOW', close_search)
		if self.limit_w_s.get():
			fn_root.resizable(False, False)
		else:
			fn_root.maxsize(700, int(fn_root.winfo_screenheight()))

		title = Label(fn_root, text='Search functions', font='arial 14 underline', fg=self.dynamic_text,
					  bg=self.dynamic_bg)
		self.find_function = Entry(fn_root)

		list_title = Label(fn_root, text='Functions list', font='arial 12 underline', fg=self.dynamic_text,
						   bg=self.dynamic_bg)
		lists_frame = Frame(fn_root)
		self.functions_list = Listbox(lists_frame, width=25, height=8)
		list_scroll = ttk.Scrollbar(lists_frame, command=self.functions_list.yview)
		self.functions_list.configure(yscrollcommand=list_scroll.set)

		title_modes = Label(fn_root, text='Search from', font='arial 12 underline', fg=self.dynamic_text,
							bg=self.dynamic_bg)
		modes_combobox = ttk.Combobox(fn_root, width=20, textvariable=self.fn_mode, state='readonly', style='TCombobox')
		modes_combobox['values'] = 'all', 'file', 'edit', 'tools', 'NLP', 'colors', 'others', 'links'

		open_button = Button(fn_root, text='Run function', command=enter, fg=self.dynamic_text, bg=self.dynamic_button)

		# for function in self.functions_names.keys():
		#     self.functions_list.insert(END, function)

		# title.grid(row=0, column=1, padx=100)
		# self.find_function.grid(row=1, column=1)
		# title_modes.grid(row=2, column=1)
		# modes_combobox.grid(row=3, column=1)
		# list_title.grid(row=4, column=1)
		# lists_frame.grid(row=5, column=1)
		# open_button.grid(row=6, column=1)

		title.pack(padx=100)
		self.find_function.pack()
		title_modes.pack()
		modes_combobox.pack()
		list_title.pack()
		lists_frame.pack(fill=Y, expand=True)
		open_button.pack()

		list_scroll.pack(side=RIGHT, fill=Y, expand=True)
		self.functions_list.pack(fill=BOTH, expand=True)

		self.functions_list.bind('<<ListboxSelect>>', lambda e: fill_by_click(self.find_function, e, self.functions_list))
		self.find_function.bind('<KeyRelease>', keyrelease_events)
		modes_combobox.bind('<<ComboboxSelected>>', configure_modes)
		configure_modes()

		self.search_widgets = title, title_modes, list_title, open_button
		self.search_bg = fn_root

		fn_root.update_idletasks()
		# self.fn_original_size =
		self.limit_list.append([fn_root, [fn_root.winfo_width(), fn_root.winfo_height()]])

	def make_tm(self, root):
		if root:
			root.attributes('-topmost', self.all_tm_v.get())
		for win in self.opened_windows:
			try:
				win.attributes('-topmost', self.all_tm_v.get())
			except Exception:
				pass

	def limit_sizes(self):
		if self.limit_list:
			for limited_root in self.limit_list:
				# if len(self.limit_list) > 1:
				window = limited_root[0]
				sizes = limited_root[1]
				# else:
				#     window = self.limit_list[0]
				#     sizes = self.limit_list[1]
				if window in self.opened_windows:
					if self.limit_w_s.get():
						window.geometry(f'{sizes[0]}x{sizes[1]}')
						window.resizable(False, False)
					else:
						window.resizable(True, True)

	def usage_report(self):
		# gather information
		current_time = get_time()
		current_usage_time = self.ut
		# put in this file / inside this folder
		dir_name = 'EgonTE-time-report'
		if not (Path(dir_name).is_dir()):
			os.makedirs(dir_name)

		name_time = str(current_time).replace(':', '-')
		file_name = f'Report of {name_time}.txt'
		line_1 = f'used EgonTE from {self.stt_time} to {current_time}.'
		line_2 = f'it is an estimated time of {current_usage_time} (S/M/H)'
		line_3 = 'Here are some of the things you did (taken from record tool):'

		start_info = [line_1, line_2, line_3]

		final_line = ('Note: if this information concerns you, EgonTE is an open-sourced project and you can\n'
					  'see that this information does not go anywhere')
		with open(rf'{dir_name}\{file_name}', 'w') as f:
			for info in start_info:
				f.write(info + '\n')
			for record in self.record_list:
				f.write(record + '\n')
			f.write(final_line)

	def check_version(self):
		current_ver = getattr(self, "ver", None)
		if not current_ver:
			return

		def worker(ver):
			try:
				resp = requests.get("https://raw.githubusercontent.com/Ariel4545/text_editor/main/version.txt", timeout=5)
				resp.raise_for_status()
				remote = resp.text.strip()
			except Exception:
				return
			if remote and ver and remote != ver:
				# post back to main thread
				self.after(0, lambda: messagebox.showwarning("EgonTE", "You are not using the latest version"))

		th = Thread(target=worker, args=(current_ver,), daemon=True)
		th.start()
		self._ver_thread = th  # optional: keep a handle


	def other_transparency(self, event=False):
		self.st_value = int(self.transparency_s.get()) / 100
		for window in self.opened_windows:
			window.attributes('-alpha', self.st_value)
		self.record_list.append(f'> [{get_time()}] - Transparency of other windows changed to {self.st_value}')



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
