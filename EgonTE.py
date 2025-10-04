# Standard library
import os
import queue
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from ctypes import byref, c_int, sizeof, windll  # Windows-only usage is guarded below
from datetime import datetime, timedelta
from heapq import nlargest
from io import BytesIO
from itertools import islice
from json import dump, load, loads
from pathlib import Path
from platform import system as platform_system
from random import choice, randint, shuffle
from re import findall, sub, compile, IGNORECASE, escape
from re import search as reSearch
from re import split as reSplit
from shutil import which as shutil_which
from socket import gethostname
from string import (
	ascii_letters,
	digits,
	ascii_lowercase,
	ascii_uppercase,
	printable,
	punctuation,
)
from sys import exit as exit_
from threading import Thread

# GUI (tkinter)
from tkinter import *
from tkinter import filedialog, colorchooser, font, messagebox, simpledialog
from tkinter import ttk  # same as `import tkinter.ttk as ttk`

# local modules
from UI import ui_builders
from UI.library_installer_ui import show_library_installer
from dependencies.large_variables import *
from dependencies.universal_functions import *
from dependencies.version_guard import ensure_supported_python

def library_installer(parent=None):
	'''
	Top-level installer entry point (safe with `from tkinter import *`).

	- parent: optional Tk widget to parent the dialog (e.g., a Tk or Toplevel instance).
			  If None, the installer tries to use the default Tk root; if not found,
			  it will create its own root window.
	Returns:
		result dict from show_library_installer.
	'''

	# Copy so we never mutate module-level lists
	required = list(library_list)
	optional = list(library_optional)

	# Helper: is this object a Tk widget?
	def _is_tk_widget(obj):
		try:
			from tkinter import Misc as _Misc
			return isinstance(obj, _Misc)
		except Exception:
			return False

	# If no parent provided, try to use the default Tk root (works even with star-import)
	if parent is None:
		try:
			import tkinter as _tk  # local, won’t pollute your global namespace
			parent = getattr(_tk, "_default_root", None)
		except Exception:
			parent = None

	return show_library_installer(
		parent=parent if _is_tk_widget(parent) else None,
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
		# Ensure restart launches the main app script explicitly
		restart_script='EgonTE.py',
		restart_args=[],
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
	import urllib.request, urllib.error
	from urllib.parse import urlparse
	# matplotlib (graphs library) in a way that suits tkinter
	import matplotlib
	import requests
	from smtplib import SMTP_SSL
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

# Local applications
from pop_ups.ai_popups import open_chatgpt, open_dalle
from pop_ups.calc_popup import open_calculator
from pop_ups.email_popup import open_email
from pop_ups.encryption_popup import open_encryption
from pop_ups.file_template_generator_popup import open_document_template_generator
from pop_ups.find_replace_popup import open_find_replace
from pop_ups.git_tool_popup import open_git_tool
from pop_ups.handwriting_popup import open_handwriting
from pop_ups.nlp_popup import open_nlp
from pop_ups.randomness_app import open_random
from pop_ups.web_scrapping_popup import open_web_scrapping_popup
from pop_ups.text_decorators_app import open_text_decorators
from pop_ups.translate_app import open_translate
from pop_ups.transcript_app import open_transcript

from pop_ups.weather_app import open_weather
from pop_ups.clipboard_app import open_clipboard_history
from pop_ups.knowledge_popup import open_knowledge_popup

from pop_ups.sort_popup import open_sort
from pop_ups.virtual_keyboard_popup import open_virtual_keyboard
from pop_ups.web_assistant_popup import open_web_tools

from pop_ups.info_page_popup import open_info
from pop_ups.search_functions_popup import open_search_functions
from pop_ups.record_logs_popup import open_record_logs

from pop_ups.symbols_popup import open_symbols_translator_popup

'''the optional libraries that can add a lot of extra content to the editor'''
tes = ACTIVE
try:
	from pytesseract import image_to_string  # download https://github.com/UB-Mannheim/tesseract/wiki
except:
	tes = DISABLED
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
		# virtual keyboard variables
		self.vk_feedback = False  # sound/haptic hooks (off by default)
		self.vk_smart_spacing = False  # Smart insert spacing (off by default)
		self.vk_repeat_enabled = True  # Key repeat on by default
		self.vk_repeat_initial_delay_ms = 550  # slower than before
		self.vk_repeat_interval_ms = 85  # slower than before
		self.vk_indent_size = 4  # spaces per indent when using spaces
		self.indent_method = StringVar()
		self.indent_method.set('tab')
		# Ensure ALL VK-related runtime attributes exist before loading settings,
		# so values don't "snap back" when the Options window closes.
		self.vk_feedback_modes_muted = True
		self.vk_feedback_min_interval_ms = 70
		self.vk_repeat_feedback_every = 4
		self.vk_sound_path = ''
		try:
			self.vk_sound_gain_db = float(-8.0)
		except Exception:
			self.vk_sound_gain_db = -8.0
		self.vk_advanced_mode = False

		# Virtual Keyboard Tk variables (single source of truth for UI)
		self.vk_feedback_v = BooleanVar(value=self.vk_feedback)
		self.vk_smart_spacing_v = BooleanVar(value=self.vk_smart_spacing)
		self.vk_repeat_enabled_v = BooleanVar(value=self.vk_repeat_enabled)
		self.vk_repeat_initial_delay_ms_v = IntVar(value=self.vk_repeat_initial_delay_ms)
		self.vk_repeat_interval_ms_v = IntVar(value=self.vk_repeat_interval_ms)
		self.vk_indent_size_v = IntVar(value=self.vk_indent_size)
		self.vk_feedback_modes_muted_v = BooleanVar(value=self.vk_feedback_modes_muted)
		self.vk_feedback_min_interval_ms_v = IntVar(value=self.vk_feedback_min_interval_ms)
		self.vk_repeat_feedback_every_v = IntVar(value=self.vk_repeat_feedback_every)
		self.vk_sound_path_v = StringVar(value=self.vk_sound_path)
		# DoubleVar is supported as textvariable for Spinbox; fallback to StringVar if needed
		try:
			self.vk_sound_gain_db_v = DoubleVar(value=self.vk_sound_gain_db)
		except Exception:
			self.vk_sound_gain_db_v = StringVar(value=str(self.vk_sound_gain_db))
		self.vk_advanced_mode_v = BooleanVar(value=self.vk_advanced_mode)

		self.vk_shift_enabled = True
		self.vk_shift_toggle_enabled = True
		self.vk_shift_tap_timeout_ms = 300
		self.vk_shift_hold_threshold_ms = 220
		# Tk variables for Shift settings
		self.vk_shift_enabled_v = BooleanVar(value=self.vk_shift_enabled)
		self.vk_shift_toggle_enabled_v = BooleanVar(value=self.vk_shift_toggle_enabled)
		self.vk_shift_tap_timeout_ms_v = IntVar(value=self.vk_shift_tap_timeout_ms)
		self.vk_shift_hold_threshold_ms_v = IntVar(value=self.vk_shift_hold_threshold_ms)

		# other tools
		self.del_previous_file = BooleanVar()
		self.chosen_text_decorator = 'bash'
		self.fnt_sz_var = IntVar()
		self.capital_opt, self.by_characters = BooleanVar(), BooleanVar()
		self.capital_opt.set(True), self.by_characters.set(True)
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
		self.ver = '1.13.8'
		self.title(f'Egon Text editor - {self.ver}')
		# function thats loads all the toolbar images
		self.load_images()
		# connecting the prees of the exit button the a custom exit function
		self.protocol('WM_DELETE_WINDOW', self.exit_app)
		# threads for a stopwatch function that works on advance option window and a function that loads images from the web
		self.start_stopwatch()
		Thread(target=self.load_links, daemon=True).start()
		# variables for the (UI) style of the program
		self.titles_font = ('@Microsoft YaHei Light', 16, 'underline')
		self.title_struct = 'EgonTE - '
		self.style_combobox = ttk.Style(self)

		self.init_ocr_async()

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

		self._popup = ui_builders.UIBuilders(self)
		self.make_pop_ups_window = self._popup.make_pop_ups_window

		# build main text box and its vertical scrollbar (legacy or rich path)
		self.build_main_textbox(parent_container=frame)
		# create main menu's component
		self.app_menu = Menu(frame)
		self.config(menu=self.app_menu)

		# Initialize and wire the TextStyleService so font family/size work via the service
		self._ensure_text_style_service()
		if getattr(self, 'text_style_service', None):
			self.text_style_service.initialize_from_widget()
			self.text_style_service.wire_toolbar()

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
						(self.CALC_IMAGE, self.ins_calc),
						(self.TRANSLATE_IMAGE, self.translate))
		self.bold_button, self.italics_button, self.underline_button, self.color_button, self.align_left_button, \
			self.align_center_button, self.align_right_button, self.tts_button, self.talk_button, self.v_keyboard_button, \
			self.dtt_button, self.calc_button, self.translate_button = [
			Button(self.toolbar_frame, image=b_image, command=b_command, relief=FLAT)
			for b_image, b_command in buttons_list]
		# ui tuples (and list) to make management of some UI events (like night mode) easier
		self.toolbar_components = [
			self.bold_button, self.italics_button, self.underline_button, self.color_button, self.font_ui,
			self.font_size,
			self.align_left_button, self.align_center_button, self.align_right_button, self.tts_button,
			self.talk_button,
			self.v_keyboard_button, self.dtt_button, self.calc_button, self.translate_button]
		pdx, r = 5, 0
		for index, button in enumerate(self.toolbar_components):
			padx, sticky = 2, W
			if index > 2:
				padx, sticky = 5, ''
			button.grid(row=0, column=index, sticky=sticky, padx=padx)


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

		self.stt_time = get_time()
		# Thread(target=self.record_logs, daemon=False).start()
		# self.record_logs()
		self.singular_colors_d = {'background': [self.EgonTE, 'bg'], 'text': [self.EgonTE, 'fg'],
								  'menus': [self.menus_components, 'bg-fg'],
								  'buttons': [self.toolbar_components, 'bg'], 'highlight': [self.EgonTE, 'selectbackground']}

		self.opening_msg(insert_lf)
		self.call_init_steps()

	def _ensure_file_service(self):
		'''
		Lazy-initialize the FileService to avoid import order issues.
		'''
		if not hasattr(self, 'file_service') or self.file_service is None:
			try:
				from services.file_service import FileService
				self.file_service = FileService(self)
			except Exception:
				self.file_service = None

	def _ensure_search_service(self):
		'''
		Lazy-initialize the SearchService to avoid import order issues.
		'''
		if not hasattr(self, 'search_service') or self.search_service is None:
			try:
				from services.search_service import SearchService
				self.search_service = SearchService(self)
			except Exception:
				self.search_service = None

	def _ensure_theme_service(self):
		'''
		Lazy-initialize the ThemeService to avoid import order issues.
		'''
		if not hasattr(self, 'theme_service') or self.theme_service is None:
			try:
				from services.theme_service import ThemeService
				self.theme_service = ThemeService(self)
			except Exception:
				self.theme_service = None

	def _ensure_text_style_service(self):
		'''
		Lazy-initialize the TextStyleService to avoid import order issues.
		'''
		if not hasattr(self, 'text_style_service') or self.text_style_service is None:
			try:
				from services.text_style_service import TextStyleService
				self.text_style_service = TextStyleService(self)
			except Exception:
				self.text_style_service = None

	def build_main_textbox(self, parent_container):
		'''
		Build the main editor text box using the rich textbox path only.
		The horizontal scrollbar is created in the same container as the text widget
		and the vertical scrollbar to ensure correct stacking above the status bar.
		Saves widgets into variables and wires scrollbars.
		'''
		# Build via rich textbox (container, text widget, vertical scrollbar)
		rich_container_frame, rich_text_widget, vertical_scrollbar = self.make_rich_textbox(
			root=parent_container,
			place='pack_top',
			wrap=WORD,
			font='arial 16',
			size=(100, 1),
			selectbg='blue',
			bd=0,
			relief=self.predefined_relief,
			format='txt',
		)

		# Save references
		self.editor_container_frame = rich_container_frame
		self.EgonTE = rich_text_widget
		self.text_scroll = vertical_scrollbar

		# Configure vertical scrollbar to control the text widget
		try:
			self.text_scroll.config(command=self.EgonTE.yview)
		except Exception:
			pass

			# Create horizontal scrollbar in the same container, but DON'T pack initially
		self.horizontal_scroll = ttk.Scrollbar(self.editor_container_frame, orient='horizontal')

		# Configure text <-> horizontal scrollbar linkage
		try:
			self.horizontal_scroll.config(command=self.EgonTE.xview)
			self.EgonTE.configure(xscrollcommand=self.horizontal_scroll.set)
		except Exception:
			pass


		# Focus and cursor (mirror original behavior)
		try:
			self.EgonTE.configure(cursor=self.predefined_cursor)
		except Exception:
			pass
		self.EgonTE.focus_set()

	def init_ocr_async(self):
		'''
		Non-blocking OCR (Tesseract) setup.
		Resolves tesseract path cross-platform and configures pytesseract if found.
		Keeps original ACTIVE/DISABLED semantics via the global 'tes'.
		'''
		self.tes = tes

		def ocr_worker():
			try:
				if self.tes != ACTIVE:
					return

				tesseract_path = None

				try:
					tesseract_path = shutil_which('tesseract')
				except Exception:
					tesseract_path = None

				if not tesseract_path:
					try:
						if os.path.exists(r'Tesseract-OCR\tesseract.exe'):
							tesseract_path = r'Tesseract-OCR\tesseract.exe'
					except Exception:
						pass

				# Normalize platform string once
				try:
					_sys = (platform_system() or '').lower()
				except Exception:
					_sys = ''
					for candidate_path in (
						r'C:\Program Files\Tesseract-OCR\tesseract.exe',
						r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
					):
						if os.path.exists(candidate_path):
							tesseract_path = candidate_path
							break

				if not tesseract_path and (_sys == 'darwin'):
					for candidate_path in ('/opt/homebrew/bin/tesseract', '/usr/local/bin/tesseract'):
						if os.path.exists(candidate_path):
							tesseract_path = candidate_path
							break

				if tesseract_path:
					try:
						pytesseract.pytesseract.tesseract_cmd = tesseract_path
						print('pytesseract - initial steps completed')
					except Exception:
						self.tes = DISABLED
				else:
					self.tes = DISABLED
			except Exception:
				try:
					self.tes = DISABLED
				except Exception:
					pass

		try:
			Thread(target=ocr_worker, daemon=True).start()
		except Exception:
			try:
				if self.tes == ACTIVE:
					try:
						if not (os.path.exists(r'Tesseract-OCR\tesseract.exe')):
							pytesseract.pytesseract.tesseract_cmd = (r'C:\Program Files\Tesseract-OCR\tesseract.exe')
						print('pytesseract - initial steps completed')
					except Exception:
						self.tes = DISABLED
			except Exception:
				pass


	def opening_msg(self, insert_lf: bool):
		'''
		Insert a friendly opening message without blocking startup.
		Matches original behavior: sometimes fetch from API, otherwise pick local.
		'''
		# If a last file was opened, don't insert any opening message
		if insert_lf:
			return

		# If text already has content, do nothing (idempotent guard)
		try:
			if self.EgonTE.get('1.0', 'end-1c').strip():
				return
		except Exception:
			# If widget not ready for any reason, try a bit later
			self.after(50, lambda: self.opening_msg(insert_lf))
			return


		def insert_message(msg: str):
			try:
				# Check again to avoid double insert if user typed quickly
				if not self.EgonTE.get('1.0', 'end-1c').strip():
					self.EgonTE.insert('1.0', msg)
			except Exception:
				pass

		# Decide whether to attempt a web message (same coin-flip behavior)
		try:
			use_web = choice([True, False])
		except Exception:
			use_web = False

		if not use_web:
			# Purely local, schedule ASAP but idle-safe
			self.after_idle(lambda: insert_message(choice(op_msgs)))
			return

		# Web path: run API in background and update UI via after
		def _fetch_and_insert():
			final_msg = None
			try:
				op_insp_msg = self.insp_quote(op_msg=True)
				if op_insp_msg:
					final_msg = op_insp_msg
			except Exception:
				final_msg = None
			if not final_msg:
				try:
					final_msg = choice(op_msgs)
				except Exception:
					final_msg = 'Welcome!'
			self.after(0, lambda: insert_message(final_msg))

		try:
			Thread(target=_fetch_and_insert, daemon=True).start()
		except Exception:
			# If threading fails for any reason, fall back to local immediately
			self.after_idle(lambda: insert_message(choice(op_msgs)))


	def call_init_steps(self):
		'''
		Minimal dispatcher: call existing methods in order.
		Keep only methods that are safe to run at this point.
		'''
		self.place_toolt()
		self.binds(mode='initial')
		self.setup_auto_lists()


		if 'RA' in globals() and RA and hasattr(self, 'right_align_language_support'):
			self.right_align_language_support()

		if hasattr(self, 'check_ver_v') and self.check_ver_v.get():
			# preserve idle scheduling
			self.after_idle(self.check_version)


	def load_images(self):
		'''
		loads UI's local images (for toolbar buttons) and assigning them to variables
		'''

		# buttons' icons - size=32x32 pixels
		image_names = (
			'bold', 'underline', 'italics', 'colors', 'left_align', 'center_align', 'right_align', 'tts', 'stt',
			'keyboard', 'drawToText_icon', 'calc_icon', 'translate_icon')
		self.BOLD_IMAGE, self.UNDERLINE_IMAGE, self.ITALICS_IMAGE, self.COLORS_IMAGE, self.ALIGN_LEFT_IMAGE, self.ALIGN_CENTER_IMAGE \
			, self.ALIGN_RIGHT_IMAGE, self.TTS_IMAGE, self.STT_IMAGE, self.KEY_IMAGE, self.DTT_IMAGE, self.CALC_IMAGE, self.TRANSLATE_IMAGE = \
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
							   'replace|(ctrl+h)': self.replace_dialog, 'go to|(ctrl+g).': self.goto,
							   'reverse characters|(ctrl+shift+c)': self.reverse_characters,
							   'reverse words|(ctrl+shift+r)': self.reverse_words, 'join words|(ctrl+shift+r)': self.join_words,
							   'upper/lower|(ctrl+shift+u)': self.lower_upper,
							   'sort by characters': self.sort_by_characters, 'sort by words.': self.sort_by_words,
							   'clipboard history.': self.clipboard_history, 'insert images': self.insert_image
							   }
		self.tool_functions = {'current datetime|(F5)': get_time(), 'Advanced calculator' : lambda: self.ins_calc('advanced'),
							   'randomness tools!': self.ins_random, 'Web assistant': self.url,
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

		self.settings_functions = {
			'Night mode': (self.night, self.night_mode),  # (command, BooleanVar)
			'status bars': (self.hide_statusbars, self.show_statusbar),
			'tool bar': (self.hide_toolbar, self.show_toolbar),
			# For these, use plain commands; remove onvalue/offvalue pattern without var
			'custom cursor': self.custom_cursor,
			'custom style': self.custom_style,
			'word wrap': (self.word_wrap, self.word_wrap_v),
			'reader mode': (self.reader_mode,),  # treated as checkbutton with command
			'auto save': (self.save_outvariables, self.auto_save_v),
			'top most': (self.topmost,),
			'automatic emoji detection': (self.automatic_emojis_v,),  # BooleanVar only
			'dev mode': (lambda: self.manage_menus(mode='dev'),),
			'special tools': (lambda: self.manage_menus(mode='tools'), self.sta),
			'fun numbers.': (self.save_outvariables, self.fun_numbers),
			'advance options': self.call_settings,
		}

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
		self.conjoined_functions_dict = dict(self.conjoined_functions_only)
		self.conjoined_functions_dict['options'] = self.settings_functions


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
			# Fetch the Menu object ONLY for dict-like submenus
			if isinstance(menu_content, dict) or isinstance(menu_content, list):
				# Guard against running out of Menu objects
				if index >= len(self.menus_list):
					break
				menu = self.menus_list[index]
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
			# IMPORTANT: do NOT modify index here; non-dict entries don't consume a Menu


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
		'''
		Centralized file dialog helper (delegates to FileService).
		'''
		self._ensure_file_service()
		if getattr(self, 'file_service', None):
			return self.file_service.get_file(mode=mode, message=message)
		return ''


	def new_file(self, event=None):
		'''
		Creates a blank workspace (delegates to FileService).
		'''
		self._ensure_file_service()
		if getattr(self, 'file_service', None):
			return self.file_service.new_file(event=event)

	def open_file(self, event=None):
			'''
			Opens a file with HTML/Python handling (delegates to FileService).
			'''
			self._ensure_file_service()
			if getattr(self, 'file_service', None):
				return self.file_service.open_file(event=event)

	# save file as function
	def save_as(self, event=None):
		'''
		Saves buffer to a new location (delegates to FileService).
		'''
		self._ensure_file_service()
		if getattr(self, 'file_service', None):
			return self.file_service.save_as(event=event)

	# save function
	def save(self, event=None):
			'''
			Saves buffer to existing path or falls back to Save As (delegates to FileService).
			'''
			self._ensure_file_service()
			if getattr(self, 'file_service', None):
				return self.file_service.save(event=event)

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
		try:
			right_click_menu.delete('Correct writing')
			right_click_menu.delete('Organize writing')
			right_click_menu.delete(4)
			for _ in range(4):
				right_click_menu.delete(LAST)
		except Exception:
			pass
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
		'''Add text to the clipboard history, keeping most recent at index 0 and skipping consecutive duplicates.'''
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
		'''
			Forwarder: open the standalone Clipboard History popup.
			'''
		return open_clipboard_history(self)

	def typefaces(self, tf: str):
		'''
		Toggle simple typeface styles over the selection (or whole document if no selection).
		Supported:
		  - 'weight-bold'
		  - 'slant-italic'
		  - 'underline'
		  - 'overstrike'
		  - 'normal'  -> clears all the above styles
		'''
		self._ensure_text_style_service()
		if getattr(self, 'text_style_service', None):
			self.text_style_service.apply_typeface(tf)
			return


	def text_color(self):
		'''
		texts color, if the content isnt marked it will choose to apply it for all the text
		'''
		self._ensure_text_style_service()
		if getattr(self, 'text_style_service', None):
			self.text_style_service.apply_text_color(None)
			return


	def custom_ui_colors(self, components: str):
		'''
		Delegate UI color customization to ThemeService.
		'''
		self._ensure_theme_service()
		if getattr(self, 'theme_service', None):
			return self.theme_service.custom_ui_colors(components=components)


	def make_rich_textbox(self, root=None, place='pack_top', wrap=None, font='arial 10',
			size=None, selectbg='dark cyan', bd=0, relief='', format='txt', *,
			# new kwargs mapped to ui_builders.UIBuilders.make_rich_textbox
			parent_container=None,
			show_xscroll=True,
			auto_hide_scrollbars=True,
			enable_mousewheel=True,
			initial_refresh_delays=(80, 180),
			external_y=None,
			external_x=None,
		):
		'''
		Forwarder updated to match ui_builders.UIBuilders.make_rich_textbox signature.

		Notes:
		  - `root` kept for backward compatibility and mapped to `parent_container` if not provided.
		  - Returns (container_frame, text_widget, y_scrollbar) just like the builder.
		'''
		# Prefer explicit parent_container; fall back to legacy root
		parent_container = parent_container or root

		# Default wrap to WORD if None while keeping backward-compat behavior (tk.WORD already imported via *)
		try:
			eff_wrap = wrap if wrap is not None else WORD
		except Exception:
			eff_wrap = wrap

		return self._popup.make_rich_textbox(
			parent_container=parent_container,
			place=place,
			wrap=eff_wrap,
			font=font,
			size=size,
			selectbg=selectbg,
			bd=bd,
			relief=relief,
			format=format,
			root=root,  # legacy alias supported by builder
			show_xscroll=show_xscroll,
			auto_hide_scrollbars=auto_hide_scrollbars,
			enable_mousewheel=enable_mousewheel,
			initial_refresh_delays=initial_refresh_delays,
			external_y=external_y,
			external_x=external_x,
		)

	def print_file(self):
		'''
		Best-effort print for the current file (delegates to FileService).
		'''
		self._ensure_file_service()
		if getattr(self, 'file_service', None):
			return self.file_service.print_file()

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
		if not self.show_statusbar.get():
			self.status_bar.pack_forget()
			self.file_bar.pack_forget()
			self.geometry(f'{self.width}x{self.height - 30}')
			self.show_statusbar.set(False)
			self.bars_active.set(False)
		else:
			self.status_bar.pack(side=LEFT)
			self.file_bar.pack(side=RIGHT)
			self.geometry(f'{self.width}x{self.height - 20}')
			self.show_statusbar.set(True)
			self.bars_active.set(True)

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
			self.editor_container_frame.pack_forget()
			self.toolbar_frame.pack(fill=X, anchor=W)
			self.text_scroll.pack(side=RIGHT, fill=Y)
			self.editor_container_frame.pack(fill=BOTH, expand=True)
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

		if platform_system().lower() == 'windows':
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
		# Use TextStyleService for robust font setting
		self._ensure_text_style_service()
		if getattr(self, 'text_style_service', None):
			self.text_style_service.set_font(family=chosen_font, size=self.size_var.get())
			return
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

		# Delegate to TextStyleService
		self._ensure_text_style_service()
		if getattr(self, 'text_style_service', None):
			self.text_style_service.set_font_size(self.chosen_size)
			return
		self.record_list.append(f'> [{get_time()}] - font size changed to {self.chosen_size}')

	def replace_dialog(self, event=None):
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
		replace_root = self.make_pop_ups_window(self.replace_dialog)
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
		self._ensure_text_style_service()
		if getattr(self, 'text_style_service', None):
			self.text_style_service.align_text(place)
			return

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
		'''
		Main-thread entry point. Bind this to the button.
		'''
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
		'''
		Background thread: does one listen+recognize cycle.
		No Tkinter calls here.
		'''
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
		'''
		Main-thread polling for worker results. Safe UI updates happen here.
		'''
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
		self.after(50, self._poll_stt_queue)
		return

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
		# Cancel any scheduled stopwatch update to avoid "invalid command name" after destroy
		try:
			if getattr(self, "_sw_after", None):
				self.after_cancel(self._sw_after)
				self._sw_after = None
		except Exception:
			pass
		if self.usage_report_v.get():
			self.usage_report()

		if self.file_name:
			if check_file_changes(self.file_name, self.EgonTE.get('1.0', 'end')):
				self.save()

		if event == 'r':
			# Slightly delay restart to let Tk settle and avoid pending callbacks firing on a destroyed widget
			self.after(200, lambda: (self.destroy(), Window().mainloop()))
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

	def ins_calc(self, mode='basic'):
		'''
		a claculator using eval that gives the user option to see his equation, and an option to paste the result to
		the text editor
		NEW : claculator buttons
		'''
		open_calculator(self, mode)

	def dt(self, event=None):
		'''
		insert the current date/time to where the pointer of your text are
		'''
		message = get_time() + ' '

		line, col = map(int, self.get_pos().split('.'))
		prev_ind = f'{line}.{max(0, col - 1)}'
		try:
			before_char = self.EgonTE.get(prev_ind)
		except Exception:
			before_char = ''

		if before_char in ascii_letters or before_char in digits:
			message = ' ' + message
		self.EgonTE.insert(self.get_pos(), message)

	def ins_random(self):
		open_random(self)

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


	def translate(self):
		'''
		simply an old translate tool using google translate API,
		support auto detect, and have a UI that remind most of the translate tools UI
		with input and output so the translation doesnt paste automatically to the main text box
		'''
		open_translate(self)

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
		self.EgonTE.insert(self.first_index, ' '.join(reversed_words))

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
		self.EgonTE.insert(self.first_index, ' '.join(sorted_words))


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
		open_info(self, path)

	def right_align_language_support(self):
		if self.EgonTE.get('1.0', 'end'):
			lan = poly_text(self.EgonTE.get('1.0', 'end')).language.name
			if lan in right_aligned_l:
				self.align_text('right')

	def url(self):
		'''
		a simple tool that takes an input of url and inserts a shorter version
		'''

		open_web_tools(self)

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
			'''
			mode is the group key (e.g., 'filea', 'typea', 'editf', 'textt', 'windf', 'autof', 'autol').
			Each checkbox drives a BooleanVar in self.binding_work[mode].
			'''
			var = self.binding_work.get(mode)
			if var and var.get():
				# enable (bind) this group only
				self.binds(mode=mode)
			else:
				# disable (unbind) this group only
				self.unbind_group(mode)

		def reset_binds():
			'''
			Restore original values: set all flags to True and re-apply all bindings.
			'''
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
				# Do NOT recreate self.show_statusbar; just set the existing one
				try:
					self.show_statusbar.set(True)
				except Exception:
					pass
				self.def_val1.set(1)
				self.def_val2.set(1)
			else:
				self.status_ = False
				self.file_ = False
				# Do NOT recreate self.show_statusbar; just set the existing one
				try:
					self.show_statusbar.set(False)
				except Exception:
					pass
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
		# Place the title at the very top of the window, above the tabs
		opt_title.pack(pady=(6, 4))  # centered by default
		# Now place the tabs beneath the title (single pack call)
		settings_tabs.pack()

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

		# REMOVED from Functions tab: indent controls now live under "Virtual keyboard" tab


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

		# NEW: Virtual keyboard tab and controls
		vk_frame = Frame(settings_tabs, bg=self.dynamic_overall)

		# Use ONLY class-level VK variables initialized in __init__
		# No local duplicates; keep single source of truth

		# Configure the VK tab grid (center content, single widget per row)
		try:
			vk_frame.grid_columnconfigure(0, weight=1)
		except Exception:
			pass

		# Internal tabs to keep the VK UI compact
		try:
			vk_tabs = ttk.Notebook(vk_frame)
			tab_basic = Frame(vk_tabs, bg=self.dynamic_overall)
			tab_repeat_indent = Frame(vk_tabs, bg=self.dynamic_overall)
			tab_feedback = Frame(vk_tabs, bg=self.dynamic_overall)
			tab_sound_layout = Frame(vk_tabs, bg=self.dynamic_overall)
			# NEW: Shift tab
			tab_shift = Frame(vk_tabs, bg=self.dynamic_overall)
			for _f in (tab_basic, tab_repeat_indent, tab_feedback, tab_sound_layout, tab_shift):
				try:
					_f.grid_columnconfigure(0, weight=1)
				except Exception:
					pass
			vk_tabs.pack(fill='both', expand=True, padx=4, pady=4)
			vk_tabs.add(tab_basic, text='Basics')
			vk_tabs.add(tab_repeat_indent, text='Repeat & Indent')
			vk_tabs.add(tab_feedback, text='Feedback')
			vk_tabs.add(tab_sound_layout, text='Sound & Layout')
			vk_tabs.add(tab_shift, text='Shift')
		except Exception:
			# Fallback: no inner tabs (place directly on vk_frame)
			tab_basic = tab_repeat_indent = tab_feedback = tab_sound_layout = tab_shift = vk_frame

		row_i = 0
		# Basics: direct binding to class variables
		vk_feedback_chk = Checkbutton(
			tab_basic, text='Sound / Haptic hooks', variable=self.vk_feedback_v,
			bg=self.dynamic_bg, fg=self.dynamic_text
		)
		vk_feedback_chk.grid(row=row_i, column=0, pady=2, sticky='w')
		row_i += 1

		vk_smart_spacing_chk = Checkbutton(
			tab_basic, text='Smart insert spacing', variable=self.vk_smart_spacing_v,
			bg=self.dynamic_bg, fg=self.dynamic_text
		)
		vk_smart_spacing_chk.grid(row=row_i, column=0, pady=2, sticky='w')
		row_i += 1

		vk_repeat_enabled_chk = Checkbutton(
			tab_basic, text='Key repeat (press-and-hold)', variable=self.vk_repeat_enabled_v,
			bg=self.dynamic_bg, fg=self.dynamic_text
		)
		vk_repeat_enabled_chk.grid(row=row_i, column=0, pady=2, sticky='w')

		# Repeat & Indent tab (bind spinboxes to variables)
		repeat_group = Frame(tab_repeat_indent, bg=self.dynamic_overall)
		repeat_group.grid(row=0, column=0, pady=(8, 4), sticky='w')
		repeat_title = Label(repeat_group, text='Repeat timings (ms)', font='arial 10',
							 bg=self.dynamic_overall, fg=self.dynamic_text)
		repeat_title.grid(row=0, column=0, sticky='w')
		repeat_row = Frame(repeat_group, bg=self.dynamic_overall)
		repeat_row.grid(row=1, column=0, pady=2, sticky='w')

		repeat_delay_lbl = Label(repeat_row, text='Initial delay:', bg=self.dynamic_overall, fg=self.dynamic_text)
		repeat_delay_spin = Spinbox(
			repeat_row, from_=0, to=5000, increment=25, width=8,
			textvariable=self.vk_repeat_initial_delay_ms_v,
			bg=self.dynamic_bg, fg=self.dynamic_text
		)
		repeat_interval_lbl = Label(repeat_row, text='Interval:', bg=self.dynamic_overall, fg=self.dynamic_text)
		repeat_interval_spin = Spinbox(
			repeat_row, from_=10, to=1000, increment=5, width=8,
			textvariable=self.vk_repeat_interval_ms_v,
			bg=self.dynamic_bg, fg=self.dynamic_text
		)

		repeat_delay_lbl.grid(row=0, column=0, padx=(0, 6), sticky='w')
		repeat_delay_spin.grid(row=0, column=1, padx=(0, 6), sticky='w')
		repeat_interval_lbl.grid(row=1, column=0, padx=(0, 6), sticky='w')
		repeat_interval_spin.grid(row=1, column=1, padx=(0, 6), sticky='w')

		indent_group = Frame(tab_repeat_indent, bg=self.dynamic_overall)
		indent_group.grid(row=2, column=0, pady=(10, 4), sticky='w')
		indent_title_vk = Label(indent_group, text='Indent method', font='arial 10',
								bg=self.dynamic_overall, fg=self.dynamic_text)
		indent_title_vk.grid(row=0, column=0, sticky='w')

		indent_row_vk = Frame(indent_group, bg=self.dynamic_overall)
		indent_row_vk.grid(row=1, column=0, pady=2, sticky='w')

		indent_tab_vk = Radiobutton(indent_row_vk, text='Tab', variable=self.indent_method, value='tab',
									bg=self.dynamic_overall, fg=self.dynamic_text, selectcolor=self.dynamic_bg)
		indent_space_vk = Radiobutton(indent_row_vk, text='Space', variable=self.indent_method, value='space',
									  bg=self.dynamic_overall, fg=self.dynamic_text, selectcolor=self.dynamic_bg)
		indent_tab_vk.grid(row=0, column=0, padx=(0, 12), sticky='w')
		indent_space_vk.grid(row=0, column=1, sticky='w')

		indent_size_group = Frame(tab_repeat_indent, bg=self.dynamic_overall)
		indent_size_group.grid(row=3, column=0, pady=(8, 6), sticky='w')
		indent_size_lbl = Label(indent_size_group, text='Spaces per indent:', bg=self.dynamic_overall, fg=self.dynamic_text)
		indent_size_spin = Spinbox(
			indent_size_group, from_=1, to=12, increment=1, width=6,
			textvariable=self.vk_indent_size_v,
			bg=self.dynamic_bg, fg=self.dynamic_text
		)
		indent_size_lbl.grid(row=0, column=0, padx=(0, 6), sticky='w')
		indent_size_spin.grid(row=0, column=1, sticky='w')

		# Feedback tab (bind to variables)
		feedback_group = Frame(tab_feedback, bg=self.dynamic_overall)
		feedback_group.grid(row=0, column=0, pady=(8, 6), sticky='w')
		feedback_title = Label(feedback_group, text='Feedback behavior', font='arial 10',
							   bg=self.dynamic_overall, fg=self.dynamic_text)
		feedback_title.grid(row=0, column=0, sticky='w')

		feedback_row = Frame(feedback_group, bg=self.dynamic_overall)
		feedback_row.grid(row=1, column=0, pady=2, sticky='w')

		vk_modes_muted_chk = Checkbutton(
			feedback_row, text='Mute mode keys (Caps/Shift/Symbols)', variable=self.vk_feedback_modes_muted_v,
			bg=self.dynamic_bg, fg=self.dynamic_text
		)
		vk_modes_muted_chk.grid(row=0, column=0, pady=2, sticky='w')

		lbl_deb = Label(feedback_group, text='Debounce (ms):', bg=self.dynamic_overall, fg=self.dynamic_text)
		lbl_deb.grid(row=2, column=0, sticky='w')
		vk_debounce_spin = Spinbox(
			feedback_group, from_=0, to=300, increment=5, width=6,
			textvariable=self.vk_feedback_min_interval_ms_v,
			bg=self.dynamic_bg, fg=self.dynamic_text
		)
		vk_debounce_spin.grid(row=3, column=0, sticky='w', pady=(0, 2))

		lbl_rep = Label(feedback_group, text='Repeat feedback every:', bg=self.dynamic_overall, fg=self.dynamic_text)
		lbl_rep.grid(row=4, column=0, sticky='w')
		vk_repeat_every_spin = Spinbox(
			feedback_group, from_=1, to=10, increment=1, width=6,
			textvariable=self.vk_repeat_feedback_every_v,
			bg=self.dynamic_bg, fg=self.dynamic_text
		)
		vk_repeat_every_spin.grid(row=5, column=0, sticky='w')

		# Sound & Layout tab
		sound_group = Frame(tab_sound_layout, bg=self.dynamic_overall)
		sound_group.grid(row=0, column=0, pady=(8, 6), sticky='w')
		sound_title = Label(sound_group, text='Feedback sound', font='arial 10',
							bg=self.dynamic_overall, fg=self.dynamic_text)
		sound_title.grid(row=0, column=0, sticky='w')

		sound_row1 = Frame(sound_group, bg=self.dynamic_overall)
		sound_row1.grid(row=1, column=0, pady=2, sticky='w')

		Label(sound_row1, text='Custom click sound:', bg=self.dynamic_overall, fg=self.dynamic_text).grid(row=0, column=0,
																										  sticky='w')
		vk_sound_path_entry = Entry(sound_row1, width=30, textvariable=self.vk_sound_path_v, bg=self.dynamic_bg,
									fg=self.dynamic_text)
		vk_sound_path_entry.grid(row=1, column=0, pady=(2, 0), sticky='w')

		def _browse_sound_file():
			try:
				from tkinter import filedialog as _fd
				p = _fd.askopenfilename(title='Choose click sound',
										filetypes=[('Audio files', '*.wav *.mp3 *.ogg *.flac'), ('All files', '*.*')])
				if p:
					self.vk_sound_path_v.set(p)
					apply_vk_settings()
			except Exception:
				pass

		vk_sound_browse_btn = Button(sound_row1, text='Browse...', command=_browse_sound_file, bg=self.dynamic_button,
									 fg=self.dynamic_text)
		vk_sound_browse_btn.grid(row=2, column=0, pady=(4, 0), sticky='w')

		sound_row2 = Frame(sound_group, bg=self.dynamic_overall)
		sound_row2.grid(row=2, column=0, pady=(6, 2), sticky='w')

		Label(sound_row2, text='Volume gain (dB):', bg=self.dynamic_overall, fg=self.dynamic_text).grid(row=0, column=0,
																										sticky='w')
		vk_sound_gain_spin = Spinbox(
			sound_row2, from_=-30.0, to=12.0, increment=0.5, width=8,
			textvariable=self.vk_sound_gain_db_v,
			bg=self.dynamic_bg, fg=self.dynamic_text
		)
		vk_sound_gain_spin.grid(row=1, column=0, sticky='w')

		layout_group = Frame(tab_sound_layout, bg=self.dynamic_overall)
		layout_group.grid(row=3, column=0, pady=(10, 6), sticky='w')
		layout_title = Label(layout_group, text='Layout', font='arial 10',
							 bg=self.dynamic_overall, fg=self.dynamic_text)
		layout_title.grid(row=0, column=0, sticky='w')
		vk_advanced_mode_chk = Checkbutton(
			layout_group, text='Use advanced layout (numbers/nav rows)',
			variable=self.vk_advanced_mode_v, bg=self.dynamic_bg, fg=self.dynamic_text
		)
		vk_advanced_mode_chk.grid(row=1, column=0, sticky='w')

		# Auto-apply VK settings on any change (no separate Apply button)
		def apply_vk_settings():
			# Read from class Tk variables
			self.vk_feedback = bool(self.vk_feedback_v.get())
			self.vk_smart_spacing = bool(self.vk_smart_spacing_v.get())
			self.vk_repeat_enabled = bool(self.vk_repeat_enabled_v.get())
			self.vk_repeat_initial_delay_ms = max(0, min(5000, int(self.vk_repeat_initial_delay_ms_v.get())))
			self.vk_repeat_interval_ms = max(10, min(1000, int(self.vk_repeat_interval_ms_v.get())))
			self.vk_indent_size = max(1, min(12, int(self.vk_indent_size_v.get())))

			self.vk_feedback_modes_muted = bool(self.vk_feedback_modes_muted_v.get())
			self.vk_feedback_min_interval_ms = max(0, min(300, int(self.vk_feedback_min_interval_ms_v.get())))
			self.vk_repeat_feedback_every = max(1, min(10, int(self.vk_repeat_feedback_every_v.get())))
			self.vk_sound_path = self.vk_sound_path_v.get().strip()
			try:
				self.vk_sound_gain_db = float(self.vk_sound_gain_db_v.get())
			except Exception:
				try:
					self.vk_sound_gain_db = float(str(self.vk_sound_gain_db_v.get()))
				except Exception:
					self.vk_sound_gain_db = -8.0
			self.vk_sound_gain_db = max(-30.0, min(12.0, self.vk_sound_gain_db))
			self.vk_advanced_mode = bool(self.vk_advanced_mode_v.get())

			self.vk_shift_enabled = bool(self.vk_shift_enabled_v.get())
			self.vk_shift_toggle_enabled = bool(self.vk_shift_toggle_enabled_v.get())
			try:
				self.vk_shift_tap_timeout_ms = max(100, min(1000, int(self.vk_shift_tap_timeout_ms_v.get())))
			except Exception:
				self.vk_shift_tap_timeout_ms = 300
			try:
				self.vk_shift_hold_threshold_ms = max(100, min(1000, int(self.vk_shift_hold_threshold_ms_v.get())))
			except Exception:
				self.vk_shift_hold_threshold_ms = 220

			#  Persist (only through the saved_settings mechanism)
			try:
				if not hasattr(self, 'data') or not isinstance(self.data, dict):
					# Keep a dict so saved_settings can dump
					self.data = {}
				self.data['vk_feedback'] = self.vk_feedback
				self.data['vk_smart_spacing'] = self.vk_smart_spacing
				self.data['vk_repeat_enabled'] = self.vk_repeat_enabled
				self.data['vk_repeat_initial_delay_ms'] = self.vk_repeat_initial_delay_ms
				self.data['vk_repeat_interval_ms'] = self.vk_repeat_interval_ms
				self.data['vk_indent_size'] = self.vk_indent_size

				self.data['vk_feedback_modes_muted'] = self.vk_feedback_modes_muted
				self.data['vk_feedback_min_interval_ms'] = self.vk_feedback_min_interval_ms
				self.data['vk_repeat_feedback_every'] = self.vk_repeat_feedback_every
				self.data['vk_sound_path'] = self.vk_sound_path
				self.data['vk_sound_gain_db'] = self.vk_sound_gain_db
				self.data['vk_advanced_mode'] = self.vk_advanced_mode

				self.data['vk_shift_enabled'] = self.vk_shift_enabled
				self.data['vk_shift_toggle_enabled'] = self.vk_shift_toggle_enabled
				self.data['vk_shift_tap_timeout_ms'] = self.vk_shift_tap_timeout_ms
				self.data['vk_shift_hold_threshold_ms'] = self.vk_shift_hold_threshold_ms

				self.saved_settings(special_mode='save')
			except Exception:
				pass

			# Live refresh hook
			try:
				if self.vk_active and callable(getattr(self, 'on_vk_settings_changed', None)):
					self.on_vk_settings_changed()
			except Exception:
				pass

		# Bind auto-apply on variable changes and relevant entries
		try:
			for v in (
					self.vk_feedback_v, self.vk_smart_spacing_v, self.vk_repeat_enabled_v,
					self.vk_repeat_initial_delay_ms_v, self.vk_repeat_interval_ms_v, self.vk_indent_size_v,
					self.vk_feedback_modes_muted_v, self.vk_feedback_min_interval_ms_v, self.vk_repeat_feedback_every_v,
					self.vk_sound_path_v, self.vk_sound_gain_db_v, self.vk_advanced_mode_v,
					# NEW: Shift variables
					self.vk_shift_enabled_v, self.vk_shift_toggle_enabled_v,
					self.vk_shift_tap_timeout_ms_v, self.vk_shift_hold_threshold_ms_v
			):
				if hasattr(v, 'trace_add'):
					v.trace_add('write', lambda *args: apply_vk_settings())
		except Exception:
			pass
		try:
			vk_sound_path_entry.bind('<FocusOut>', lambda _e: apply_vk_settings())
			vk_sound_path_entry.bind('<KeyRelease>', lambda _e: apply_vk_settings())
		except Exception:
			pass

		# --- Shift tab UI (Virtual keyboard → Shift) ---
		try:
			shift_group = Frame(tab_shift, bg=self.dynamic_overall)
			shift_group.grid(row=0, column=0, pady=(8, 6), sticky='w')

			shift_title = Label(
				shift_group, text='Shift behavior', font='arial 10',
				bg=self.dynamic_overall, fg=self.dynamic_text
			)
			shift_title.grid(row=0, column=0, columnspan=2, sticky='w')

			shift_enabled_cb = Checkbutton(
				shift_group, text='Enable Shift keys', variable=self.vk_shift_enabled_v,
				bg=self.dynamic_bg, fg=self.dynamic_text
			)
			shift_enabled_cb.grid(row=1, column=0, pady=(4, 2), sticky='w')

			shift_toggle_cb = Checkbutton(
				shift_group,
				text='Tap to toggle (double-tap → Caps); off = one‑shot',
				variable=self.vk_shift_toggle_enabled_v,
				bg=self.dynamic_bg, fg=self.dynamic_text
			)
			shift_toggle_cb.grid(row=2, column=0, pady=(2, 2), sticky='w')

			# Timings
			timing_group = Frame(tab_shift, bg=self.dynamic_overall)
			timing_group.grid(row=1, column=0, pady=(8, 6), sticky='w')

			timing_title = Label(
				timing_group, text='Timings (ms)', font='arial 10',
				bg=self.dynamic_overall, fg=self.dynamic_text
			)
			timing_title.grid(row=0, column=0, columnspan=2, sticky='w')

			lbl_tap = Label(timing_group, text='Double‑tap window:', bg=self.dynamic_overall, fg=self.dynamic_text)
			spin_tap = Spinbox(
				timing_group, from_=100, to=1000, increment=20, width=8,
				textvariable=self.vk_shift_tap_timeout_ms_v,
				bg=self.dynamic_bg, fg=self.dynamic_text
			)
			lbl_hold = Label(timing_group, text='Hold threshold:', bg=self.dynamic_overall, fg=self.dynamic_text)
			spin_hold = Spinbox(
				timing_group, from_=100, to=1000, increment=20, width=8,
				textvariable=self.vk_shift_hold_threshold_ms_v,
				bg=self.dynamic_bg, fg=self.dynamic_text
			)

			lbl_tap.grid(row=1, column=0, padx=(0, 6), pady=(2, 2), sticky='w')
			spin_tap.grid(row=1, column=1, padx=(0, 6), pady=(2, 2), sticky='w')
			lbl_hold.grid(row=2, column=0, padx=(0, 6), pady=(2, 2), sticky='w')
			spin_hold.grid(row=2, column=1, padx=(0, 6), pady=(2, 2), sticky='w')
		except Exception:
			pass

		# Fit height on tab change
		def _fit_options_height(_event=None):
			try:
				self.opt_root.update_idletasks()
				cur_w = self.opt_root.winfo_width()
				new_h = self.opt_root.winfo_height()
				self.opt_root.geometry(f'{cur_w}x{new_h}')
			except Exception:
				pass

		try:
			if 'vk_tabs' in locals() and hasattr(vk_tabs, 'bind'):
				vk_tabs.bind('<<NotebookTabChanged>>', _fit_options_height)
		except Exception:
			pass

		# Initial sync (apply current values)
		apply_vk_settings()

		# tabs assembly (only once)
		settings_tabs.add(styles_frame, text='Styles')
		settings_tabs.add(functional_frame, text='Functions')
		settings_tabs.add(bindings_frame, text='Bindings')
		settings_tabs.add(pop_ups_frame, text='Alt Windows')
		settings_tabs.add(vk_frame, text='V-keyboard')
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
			, title_other, check_v_checkbox, reset_button, tt_checkbox, auto_save_title, auto_save_frame)
		for widget in pack_functional:
			widget.pack()
		filebar_check.grid(row=1, column=0)
		statusbar_check.grid(row=1, column=2)
		by_time_rb.grid(row=0, column=0)
		by_press_rb.grid(row=0, column=2)
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

		self.opt_frames = styles_frame, functional_frame, self.opt_root, bindings_frame, pop_ups_frame, order_frame, preference_frame

		self.opt_commands = (nm_black_checkbox, nm_blue_checkbox, transparency_config, filebar_check, statusbar_check,
							 last_file_checkbox, reset_button, tt_checkbox, by_time_rb, by_press_rb, corrector_preview,
							 file_actions_check, typefaces_action_check, edit_functions_check, auto_function_check,
							 auto_list_check, preference_text, preference_html,
							 textt_function_check, win_actions_check, open_m_s, never_limit_s, self.transparency_s,
							 usage_report_checkbox, biggest_top, biggest_bottom,
							 duplicate_windows, many_windows_checkbox, top_most_s, check_v_checkbox, reset_binds_button,
							 shift_enabled_cb, shift_toggle_cb, spin_tap, spin_hold)
		self.opt_labels = (opt_title, cursor_title, style_title, relief_title, nm_title, transparency_title, hide_title,
						   stt_title, file_opt_title, title_other, auto_save_title, self.usage_time, state_title,
						   attr_title, trans_s_title, corrector_title, warning_title, other_w_title, order_title,
						   shift_title, timing_title, lbl_tap, lbl_hold)


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
		open_sort(self)

	def knowledge_window(self, mode: str):
		'''
		the window for the dictionary and wikipedia tools
		'''
		open_knowledge_popup(self, mode)

	def virtual_keyboard(self):
		'''
		virtual keyboard tool, that have most of the important functionalities:
		tab, symbols, caps, numbers, and english characters in the qwert organization
		'''
		open_virtual_keyboard(self)


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
				any_replaced = False
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
						any_replaced = True
						fail_msg = False
						# a message for the manual use of the function about the result - positive
						if via_settings:
							messagebox.showinfo('EgonTE', 'emoji(s) found!')

					else:
						fail_msg = True

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
				if any_replaced:
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

	def file_info(self, path: str | None = None):
		'''
		Return file stats and optionally reflect to status (delegates to FileService).
		'''
		self._ensure_file_service()
		if getattr(self, 'file_service', None):
			return self.file_service.file_info(path=path)
		return {}

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
		'''
		Delegate to the standalone Document Template Generator popup implementation.
		'''
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
			# Write safely without removing the file first; use UTF-8
			try:
				with open(file_name, 'w', encoding='utf-8') as f:
					dump(self.data, f)
					print('save 1', self.data)
			except Exception:
				# Fallback to atomic replace if direct write fails
				try:
					tmp = file_name + '.tmp'
					with open(tmp, 'w', encoding='utf-8') as f:
						dump(self.data, f)
					os.replace(tmp, file_name)
				except Exception:
					pass

			if self.data['open_last_file']:
				self.save_last_file()

		else:

			if os.path.exists(file_name):
				print('saved settings file exist')
				with open(file_name, 'r', encoding='utf-8') as f:
					self.data = load(f)
					print(self.data)
				self.match_saved_settings()

				return False

			else:
				print('saved settings file doesn\'t exist')
				self.data = self.make_default_data()

				with open(file_name, 'w', encoding='utf-8') as f:
					dump(self.data, f)

				return True

	@staticmethod
	def make_default_data():
		return {'night_mode': False, 'status_bar': True, 'file_bar': True, 'cursor': 'xterm',
				'style': 'clam',
				'word_wrap': True, 'reader_mode': False, 'auto_save': True, 'relief': 'ridge',
				'transparency': 100, 'toolbar': True, 'open_last_file': '', 'text_twisters': False,
				'night_type': 'black', 'preview_cc': False, 'fun_numbers': True, 'usage_report': False,
				'check_version': False, 'window_c_warning': True, 'allow_duplicate': False,
				'vk_feedback': False,
				'vk_smart_spacing': False,
				'vk_repeat_enabled': True,
				'vk_repeat_initial_delay_ms': 550,
				'vk_repeat_interval_ms': 85,
				'vk_indent_size': 4,
				# Newly added VK defaults
				'vk_feedback_modes_muted': True,
				'vk_advanced_mode': False,
				'vk_sound_path': '',
				'vk_sound_gain_db': -8.0,
				'vk_feedback_min_interval_ms': 70,
				'vk_repeat_feedback_every': 4,
				'vk_shift_enabled': True,
				'vk_shift_toggle_enabled': True,
				'vk_shift_tap_timeout_ms': 300,
				'vk_shift_hold_threshold_ms': 220,
		}

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
		self.vk_feedback = bool(self.data.get('vk_feedback', False))
		self.vk_smart_spacing = bool(self.data.get('vk_smart_spacing', False))
		self.vk_repeat_enabled = bool(self.data.get('vk_repeat_enabled', True))
		self.vk_repeat_initial_delay_ms = int(self.data.get('vk_repeat_initial_delay_ms', 550))
		self.vk_repeat_interval_ms = int(self.data.get('vk_repeat_interval_ms', 85))
		self.vk_indent_size = int(self.data.get('vk_indent_size', 4))

		# Newly added VK settings (load from saved data)
		self.vk_feedback_modes_muted = bool(self.data.get('vk_feedback_modes_muted', True))
		self.vk_advanced_mode = bool(self.data.get('vk_advanced_mode', False))
		self.vk_sound_path = self.data.get('vk_sound_path', '') or ''
		try:
			self.vk_sound_gain_db = float(self.data.get('vk_sound_gain_db', -8.0))
		except Exception:
			self.vk_sound_gain_db = -8.0

		try:
			self.vk_feedback_min_interval_ms = int(self.data.get('vk_feedback_min_interval_ms', 70))
		except Exception:
			self.vk_feedback_min_interval_ms = 70
		try:
			self.vk_repeat_feedback_every = int(self.data.get('vk_repeat_feedback_every', 4))
		except Exception:
			self.vk_repeat_feedback_every = 4

		# NEW: load Shift settings from saved data
		try:
			self.vk_shift_enabled = bool(self.data.get('vk_shift_enabled', True))
			self.vk_shift_toggle_enabled = bool(self.data.get('vk_shift_toggle_enabled', True))
			self.vk_shift_tap_timeout_ms = int(self.data.get('vk_shift_tap_timeout_ms', 300))
			self.vk_shift_hold_threshold_ms = int(self.data.get('vk_shift_hold_threshold_ms', 220))
		except Exception:
			self.vk_shift_enabled = True
			self.vk_shift_toggle_enabled = True
			self.vk_shift_tap_timeout_ms = 300
			self.vk_shift_hold_threshold_ms = 220

		# Sync VK Tk variables with loaded values (no duplicates elsewhere)
		try:
			self.vk_feedback_v.set(self.vk_feedback)
			self.vk_smart_spacing_v.set(self.vk_smart_spacing)
			self.vk_repeat_enabled_v.set(self.vk_repeat_enabled)
			self.vk_repeat_initial_delay_ms_v.set(self.vk_repeat_initial_delay_ms)
			self.vk_repeat_interval_ms_v.set(self.vk_repeat_interval_ms)
			self.vk_indent_size_v.set(self.vk_indent_size)
			self.vk_feedback_modes_muted_v.set(self.vk_feedback_modes_muted)
			self.vk_feedback_min_interval_ms_v.set(self.vk_feedback_min_interval_ms)
			self.vk_repeat_feedback_every_v.set(self.vk_repeat_feedback_every)
			self.vk_sound_path_v.set(self.vk_sound_path or '')
			if hasattr(self.vk_sound_gain_db_v, 'set'):
				self.vk_sound_gain_db_v.set(self.vk_sound_gain_db)
			else:
				self.vk_sound_gain_db_v = StringVar(value=str(self.vk_sound_gain_db))
			self.vk_advanced_mode_v.set(self.vk_advanced_mode)
			self.vk_shift_enabled_v.set(self.vk_shift_enabled)
			self.vk_shift_toggle_enabled_v.set(self.vk_shift_toggle_enabled)
			self.vk_shift_tap_timeout_ms_v.set(self.vk_shift_tap_timeout_ms)
			self.vk_shift_hold_threshold_ms_v.set(self.vk_shift_hold_threshold_ms)
		except Exception:
			pass

		if self.last_file_v.get():
			self.file_name = self.data['open_last_file']


	def text_decorators(self):
		'''
		the text decoration function is a window that let you make a bigger style of text with many symbols.
		there is 3 styles and the text can be outputted horizontally and vertically.
		also there is a UI for the process that make you manage it very easily

		(for the developer) asterisk broken
		'''
		open_text_decorators(self)

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
		# Store the after() id so we can cancel it on exit/restart
		self._sw_after = self.after(500, self._update_stopwatch)

	def merge_files(self, paths=None, separator='\n'):
		'''
		Merge multiple files into the editor (delegates to FileService).
		'''
		self._ensure_file_service()
		if getattr(self, 'file_service', None):
			return self.file_service.merge_files(paths=paths, separator=separator)


	def delete_file(self, path: str | None = None):
		'''
		Delete a file (delegates to FileService).
		'''
		self._ensure_file_service()
		if getattr(self, 'file_service', None):
			return self.file_service.delete_file(path=path)

	def insp_quote(self, op_msg: bool=False):
		'''
		This function is outputting a formated text of a quote with the name of its owner with API
		'''
		# consider making the function a thread
		quote = None
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
			sp_x = (self.editor_container_frame.winfo_width() - self.EgonTE.winfo_width())
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
		open_weather(self)


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
		open_transcript(self)


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
		open_record_logs(self)


	def manage_menus(self, mode: str):
		'''
			this window manage the diffrent menu modes that the program have, is can delete menus, call the create menus
			function, change / add things to capture the mode that the user selected for the program
			'''

		# Helpers: reliable label-based add/remove in any Menu
		def _find_entry_index_by_label(menu_obj, label_text: str):
			try:
				end = menu_obj.index('end')
			except Exception:
				end = None
			if end is None:
				return None
			target = (label_text or '').casefold()
			for i in range(end + 1):
				try:
					t = menu_obj.type(i)
					if t in ('cascade', 'command', 'checkbutton', 'radiobutton'):
						if (menu_obj.entrycget(i, 'label') or '').casefold() == target:
							return i
				except Exception:
					pass
			return None

		def _delete_if_exists(menu_obj, label_text: str):
			idx = _find_entry_index_by_label(menu_obj, label_text)
			if idx is not None:
				try:
					menu_obj.delete(idx)
				except Exception:
					pass

		def _add_check_once(menu_obj, label_text: str, **kwargs):
			if _find_entry_index_by_label(menu_obj, label_text) is None:
				try:
					menu_obj.add_checkbutton(label=label_text, **kwargs)
				except Exception:
					pass

		def _add_cascade_once(root_menu, label_text: str, *, menu=None, command=None):
			if _find_entry_index_by_label(root_menu, label_text) is not None:
				return
			try:
				if menu is not None:
					root_menu.add_cascade(label=label_text, menu=menu)
				elif command is not None:
					root_menu.add_cascade(label=label_text, command=command)
			except Exception:
				pass

		# Ensure the "Options" cascade exists before we touch self.options_menu
		def _ensure_options_cascade():
			try:
				if _find_entry_index_by_label(self.app_menu, 'Options') is None:
					# Attach the existing submenu instance
					self.app_menu.add_cascade(label='Options', menu=self.options_menu)
			except Exception:
				pass

		if mode == 'dev':
			# Toggle internally (restores previous automatic behavior)
			new_state = not self.dev_mode.get()
			self.dev_mode.set(new_state)

			# Always ensure Options cascade is visible before editing its items
			_ensure_options_cascade()

			if new_state:
				_add_cascade_once(self.app_menu, 'Record', command=self.record_logs)
				_add_check_once(self.options_menu, 'prefer gpu', variable=self.prefer_gpu)

				if _find_entry_index_by_label(self.app_menu, 'Git') is None:
					self.git_menu = Menu(self.app_menu, tearoff=False)
					self.app_menu.add_cascade(label='Git', menu=self.git_menu)
					self.git_menu.add_command(label='Pull', command=lambda: self.gitp('pull'))
					self.git_menu.add_command(label='Push', command=lambda: self.gitp('push'), state=DISABLED)
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
			else:
				_delete_if_exists(self.app_menu, 'Record')
				_delete_if_exists(self.app_menu, 'Git')
				_delete_if_exists(self.options_menu, 'prefer gpu')
				try:
					self.menus_components.remove(self.git_menu)
				except Exception:
					try:
						self.menus_components.pop(-1)
					except Exception:
						pass

		elif mode == 'tools':
			if not (self.sta.get()):
				_delete_if_exists(self.app_menu, 'Colors+')
				_delete_if_exists(self.app_menu, 'Tools')
			else:

				for lbl in ('NLP', 'Options', 'Help', 'Patch notes', 'External links'):
					_delete_if_exists(self.app_menu, lbl)

				if self.dev_mode.get():
					_delete_if_exists(self.app_menu, 'Record')
					_delete_if_exists(self.app_menu, 'Git')
					_delete_if_exists(self.options_menu, 'prefer gpu')

				self.create_menus(initial=False)

				if self.dev_mode.get():
					_add_cascade_once(self.app_menu, 'Record', command=self.record_logs)

		elif mode == 'python':
			# python menu
			if self.python_file:
				_add_cascade_once(self.app_menu, 'Run', command=self.run_code)
				_add_cascade_once(self.app_menu, 'Clear console', command=self.clear_console)

				# Ensure Options cascade is present before adding items to it
				_ensure_options_cascade()

				# Avoid stacking separators and duplicates
				try:
					last = self.options_menu.index('end')
					last_type = self.options_menu.type(last) if last is not None else None
					if last_type != 'separator':
						self.options_menu.add_separator()
				except Exception:
					pass
				_add_check_once(self.options_menu, 'Auto clear console', variable=self.auto_clear_c)
				_add_check_once(self.options_menu, 'Save by running', variable=self.sar)

		# Hint Tk to refresh menu UI (best-effort, harmless if not needed)
		try:
			self.update_idletasks()
		except Exception:
			pass

	def emojicons_hub(self):
		'''
		this function is used the connect all the operation with emojis, emoticons and roman numbers
		its a UI for the detection and the via verse process, for the lists and for a random output of item
		from the selected set of characters (emojis, emoticons, roman numbers)
		'''

		open_symbols_translator_popup(self)

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
			for image in list(self.in_images_list_n):
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
				self.current_inserted_image = PhotoImage(file=self.image_name, master=self)
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

		self.current_images_list.bind('<<ListboxSelect>>', lambda e: fill_by_click(self.image_entry, e, self.current_images_list))
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

		open_search_functions(self)


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

		# duration: use only the stopwatch variables (no local timers, no alternate trackers)
		duration_seconds_value = None
		try:
			if hasattr(self, 'start_time') and isinstance(getattr(self, 'start_time'), (int, float)):
				duration_seconds_value = max(0.0, time.perf_counter() - float(self.start_time))
		except Exception:
			duration_seconds_value = None

		# helper: format timestamp as a string
		def format_timestamp(timestamp_value):
			try:
				if hasattr(timestamp_value, 'strftime'):
					return timestamp_value.strftime('%Y-%m-%d %H:%M:%S%z')
				return str(timestamp_value)
			except Exception:
				return str(timestamp_value)

		# helper: pretty-print a duration in seconds
		def format_duration_seconds(duration_value):
			try:
				total_seconds = float(duration_value)
			except Exception:
				return 'unknown'
			if total_seconds < 60:
				return f'{total_seconds:.2f} s'
			minutes_part, seconds_part = divmod(total_seconds, 60)
			if minutes_part < 60:
				return f'{int(minutes_part)} m {int(seconds_part)} s'
			hours_part, minutes_rem = divmod(int(minutes_part), 60)
			return f'{hours_part} h {minutes_rem} m {int(seconds_part)} s'

		# destination directory (portable, created if missing)
		reports_dir_path = 'EgonTE-time-report'
		try:
			if not os.path.isdir(reports_dir_path):
				os.makedirs(reports_dir_path, exist_ok=True)
		except Exception:
			pass

		# build a safe, informative file name
		try:
			if hasattr(current_time, 'strftime'):
				timestamp_for_name = current_time.strftime('%Y-%m-%d_%H-%M-%S')
			else:
				timestamp_for_name = str(current_time)
		except Exception:
			timestamp_for_name = str(current_time)
		timestamp_for_name = (
			timestamp_for_name
			.replace(':', '-')
			.replace(' ', '_')
			.replace('/', '-')
			.replace('\\', '-')
		)
		report_file_name = f'Report_{timestamp_for_name}.txt'
		report_file_path = os.path.join(reports_dir_path, report_file_name)

		# header (prefer stopwatch start_date if available)
		start_label_value = getattr(self, 'start_date', None)
		start_time_str = str(start_label_value) if start_label_value else format_timestamp(
			getattr(self, 'stt_time', 'unknown'))
		end_time_str = format_timestamp(current_time)
		duration_str = format_duration_seconds(duration_seconds_value) if duration_seconds_value is not None else 'unknown'

		header_lines = [
			'EgonTE Session Usage Report',
			'---------------------------',
			f'Session start: {start_time_str}',
			f'Session end  : {end_time_str}',
			f'Duration     : {duration_str}',
			'',
		]

		# session statistics if available (dict-like)
		statistics_lines = []
		session_statistics_dict = None
		try:
			if hasattr(self, 'session_stats') and callable(getattr(self, 'session_stats')):
				session_statistics_dict = self.session_stats()
			elif hasattr(self, 'statistics'):
				session_statistics_dict = self.statistics
		except Exception:
			session_statistics_dict = None

		if isinstance(session_statistics_dict, dict) and session_statistics_dict:
			statistics_lines.append('Session statistics:')
			for statistics_key in sorted(session_statistics_dict.keys(), key=str):
				statistics_value = session_statistics_dict.get(statistics_key)
				try:
					statistics_lines.append(f'  - {statistics_key}: {statistics_value}')
				except Exception:
					statistics_lines.append(f'  - {statistics_key}: <unavailable>')
			statistics_lines.append('')
		else:
			statistics_lines.append('Session statistics: (none available)')
			statistics_lines.append('')

		# recorded actions and summary
		recorded_actions = list(getattr(self, 'record_list', []) or [])
		total_actions_count = len(recorded_actions)
		unique_actions_count = len(set(map(str, recorded_actions))) if recorded_actions else 0

		action_category_counts = {}
		for record_entry in recorded_actions:
			try:
				record_text = str(record_entry).strip()
			except Exception:
				record_text = '<unprintable record>'
			category_key = 'misc'
			try:
				if ' - ' in record_text:
					after_dash = record_text.split(' - ', 1)[1].strip()
					first_word = after_dash.split(' ', 1)[0].strip('>:').lower()
					if first_word:
						category_key = first_word
			except Exception:
				pass
			action_category_counts[category_key] = action_category_counts.get(category_key, 0) + 1

		sorted_categories = sorted(action_category_counts.items(),
								   key=lambda kv: (-kv[1], kv[0])) if action_category_counts else []
		top_categories_lines = []
		if sorted_categories:
			top_categories_lines.append('Top action categories:')
			for category_name, category_count in sorted_categories[:5]:
				top_categories_lines.append(f'  - {category_name}: {category_count}')
			top_categories_lines.append('')
		else:
			top_categories_lines.append('Top action categories: (none)')
			top_categories_lines.append('')

		records_header_lines = [
			'Recorded actions (from record tool):',
			f'  Total actions : {total_actions_count}',
			f'  Unique actions: {unique_actions_count}',
			'',
			*top_categories_lines,
		]

		# detailed actions (truncate very long logs for safety)
		max_detailed_actions = 1000
		detailed_record_lines = []
		if recorded_actions:
			detailed_record_lines.append('Detailed action log:')
			truncated = False
			for index_position, record_entry in enumerate(recorded_actions):
				if index_position >= max_detailed_actions:
					truncated = True
					break
				try:
					flattened_record = str(record_entry).replace('\n', ' ').strip()
				except Exception:
					flattened_record = '<unprintable record>'
				detailed_record_lines.append(f'  - {flattened_record}')
			if truncated:
				remaining_count = max(0, total_actions_count - max_detailed_actions)
				detailed_record_lines.append(f'  ... ({remaining_count} more not shown)')
			detailed_record_lines.append('')
		else:
			detailed_record_lines.append('No actions recorded.')
			detailed_record_lines.append('')

		# privacy note
		privacy_note_lines = [
			'Note: EgonTE is an open-source project; this report is generated locally.',
			'No data is transmitted anywhere by this reporting functionality.',
			'',
		]

		# compose full text
		full_text_lines = []
		full_text_lines.extend(header_lines)
		full_text_lines.extend(statistics_lines)
		full_text_lines.extend(records_header_lines)
		full_text_lines.extend(detailed_record_lines)
		full_text_lines.extend(privacy_note_lines)

		# write the report
		try:
			with open(report_file_path, 'w', encoding='utf-8', newline='\n') as report_file:
				report_file.write('\n'.join(full_text_lines))
				if not full_text_lines or full_text_lines[-1] != '':
					report_file.write('\n')
		except Exception as write_exception:
			fallback_path = os.path.join(reports_dir_path, 'Report_fallback.txt')
			fallback_lines = [
				'EgonTE Session Usage Report (partial)',
				'-------------------------------------',
				f'Failed to write full report to disk: {write_exception}',
				'',
				*header_lines,
			]
			try:
				with open(fallback_path, 'w', encoding='utf-8', newline='\n') as fallback_file:
					fallback_file.write('\n'.join(fallback_lines))
					fallback_file.write('\n')
			except Exception:
				pass

		# return the path to the generated report for convenience
		return str(report_file_path)


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
	# python version guard
	if not ensure_supported_python():
		sys.exit(1)
	else:
		# libraries installation guard
		if req_lib:
			app = Window()
			app.mainloop()
		else:
			if messagebox.askyesno('EgonTE', 'some of the required libraries aren\'t installed\ndo you want to open the '
											 'libraries installer again?'):
				library_installer()
