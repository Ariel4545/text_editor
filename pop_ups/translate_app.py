# python
from __future__ import annotations

import sys
import re
import csv
import json
import threading
import warnings
import importlib
from datetime import datetime
from typing import Any, Callable, Iterable, List, Optional, Tuple

import tkinter as tk
from tkinter import ttk
from tkinter import (
	StringVar,
	BooleanVar,
	IntVar,
	END,
	NORMAL,
	DISABLED,
	TclError,
	messagebox,
)

# optional language lists (soft dependency)
try:
	from dependencies.large_variables import (
		LANGUAGES_LIST_CLEAN as canonical_language_list_clean,
		languages_name_to_code as canonical_language_map,
	)
	fallback_language_list = None
except Exception:
	try:
		from large_variables import (
			languages_list as fallback_language_list,
			languages_name_to_code as canonical_language_map,
		)
		canonical_language_list_clean = None
	except Exception:
		canonical_language_list_clean = None
		fallback_language_list = None
		canonical_language_map = None

warnings.filterwarnings(
	'ignore',
	message='.*Enable tracemalloc to get the object allocation traceback.*',
	category=RuntimeWarning,
)

# translation backends
try:
	import googletrans as googletrans_module  # type: ignore
	from googletrans import Translator  # type: ignore
	googletrans_available = True
	googletrans_langs = getattr(googletrans_module, 'LANGUAGES', {}) or {}
except Exception:
	googletrans_module = None
	Translator = None  # type: ignore
	googletrans_available = False
	googletrans_langs = {}
# Compute googletrans supported codes (lowercase) for validation and aliasing
try:
	googletrans_supported_codes = {str(k).strip().lower() for k in (googletrans_langs or {}).keys()}
except Exception:
	googletrans_supported_codes = set()

try:
	from deep_translator import GoogleTranslator as deep_google_translator  # type: ignore
	deep_translator_available = True
except Exception:
	deep_google_translator = None  # type: ignore
	deep_translator_available = False
# Compute deep-translator supported codes (normalized lowercase) for validation and aliasing
try:
	_dt_map = deep_google_translator.get_supported_languages(as_dict=True)  # type: ignore[attr-defined]
	deep_supported_codes = {str(v).strip().lower() for v in (_dt_map or {}).values()} if isinstance(_dt_map, dict) else set()
except Exception:
	deep_supported_codes = set()

# language list for UI
ui_languages_list = list(
	canonical_language_list_clean
	or fallback_language_list
	or [
		'English',
		'Arabic',
		'Hebrew',
		'Russian',
		'Hindi',
		'Chinese (Simplified)',
		'Chinese (Traditional)',
		'Japanese',
		'Korean',
		'French',
		'German',
		'Spanish',
		'Portuguese',
		'Italian',
	]
)

canonical_language_map_seed = dict(canonical_language_map) if isinstance(canonical_language_map, dict) else {}


# --------------- utilities ---------------
def chunk_text(source_text: str, max_chunk_size: int) -> List[str]:
	text_value = source_text or ''
	if len(text_value) <= max_chunk_size:
		return [text_value]
	output_chunks: List[str] = []
	cursor_index = 0
	while cursor_index < len(text_value):
		output_chunks.append(text_value[cursor_index:cursor_index + max_chunk_size])
		cursor_index += max_chunk_size
	return output_chunks


def join_chunks(chunks: Iterable[str]) -> str:
	return ''.join(chunks or [])


def normalize_display_language(display_name: str) -> str:
	normalized_name = ' '.join((display_name or '').split())
	if not normalized_name:
		return normalized_name
	special_map = {
		'zh-cn': 'Chinese (Simplified)',
		'zh-tw': 'Chinese (Traditional)',
		'chinese (simplified)': 'Chinese (Simplified)',
		'chinese (traditional)': 'Chinese (Traditional)',
		'norwegianodia': 'Norwegian',
		'xhosayiddish': 'Xhosa',
		'odia': 'Odia',
		' czech': 'Czech',
		' catalan': 'Catalan',
		' azerbaijani': 'Azerbaijani',
		' chinese': 'Chinese (Simplified)',
	}
	key = normalized_name.strip().lower()
	return special_map.get(key, normalized_name.title())


def canonical_language_code(code: str) -> str:
	lower_code = (code or '').strip().lower()
	alias_map = {
		'iw': 'he',
		'jw': 'jv',
		'zh_cn': 'zh-cn',
		'zh_tw': 'zh-tw',
		'pt-br': 'pt',
		'pt-pt': 'pt',
		'ua': 'uk',
		'fil': 'tl',
		'zh': 'zh-cn',
	}
	return alias_map.get(lower_code, lower_code)


def build_language_mapping(languages_source: Iterable[str]) -> Tuple[List[str], dict]:
	'''
	Returns (display_names ordered, name_to_code_map)
	'''
	merged_map: dict[str, str] = {}

	# seed with local canonical map
	if canonical_language_map_seed:
		for display, code in canonical_language_map_seed.items():
			sane_display = normalize_display_language(display)
			merged_map[sane_display] = canonical_language_code(str(code))

	# deep_translator languages
	if deep_translator_available and deep_google_translator is not None:
		try:
			deep_map = deep_google_translator.get_supported_languages(as_dict=True)  # type: ignore[attr-defined]
			if isinstance(deep_map, dict):
				for deep_name, deep_code in deep_map.items():
					disp = normalize_display_language(deep_name)
					merged_map.setdefault(disp, canonical_language_code(str(deep_code)))
		except Exception:
			pass

	# googletrans languages
	if googletrans_available and isinstance(googletrans_langs, dict) and googletrans_langs:
		for backend_code, backend_name in googletrans_langs.items():
			disp = normalize_display_language(str(backend_name))
			merged_map.setdefault(disp, canonical_language_code(str(backend_code)))

	if not merged_map:
		merged_map = {
			'English': 'en',
			'Arabic': 'ar',
			'Hebrew': 'he',
			'Russian': 'ru',
			'Hindi': 'hi',
			'Chinese (Simplified)': 'zh-cn',
			'Chinese (Traditional)': 'zh-tw',
			'Japanese': 'ja',
			'Korean': 'ko',
			'French': 'fr',
			'German': 'de',
			'Spanish': 'es',
			'Portuguese': 'pt',
			'Italian': 'it',
			'Norwegian': 'no',
			'Odia': 'or',
			'Farsi': 'fa',
			'Xhosa': 'xh',
			'Yiddish': 'yi',
			'Hawaiian': 'haw',
			'Burmese': 'my',
			'Indonesian': 'id',
			'Ukrainian': 'uk',
		}

	alias_to_code = {
		'Chinese': 'zh-cn',
		'Farsi': 'fa',
		'Persian': 'fa',
		'Norwegianodia': 'no',
		'Xhosayiddish': 'xh',
		'Czech': merged_map.get('Czech', 'cs'),
		'Catalan': merged_map.get('Catalan', 'ca'),
		'Azerbaijani': merged_map.get('Azerbaijani', 'az'),
	}

	ordered_display_names: list[str] = []
	name_to_code_map: dict[str, str] = {}
	seen_display_names: set[str] = set()

	for user_name in (languages_source or []):
		disp = normalize_display_language(str(user_name))
		if not disp or disp in seen_display_names:
			continue
		code_value = merged_map.get(disp) or merged_map.get(disp.title())
		if not code_value:
			alias_key = disp.replace(' ', '').lower()
			for alias_key_candidate, alias_code in alias_to_code.items():
				if alias_key == alias_key_candidate.lower():
					code_value = alias_code
					break
		if code_value:
			ordered_display_names.append(disp)
			name_to_code_map[disp] = canonical_language_code(code_value)
			seen_display_names.add(disp)

	for disp, code_value in merged_map.items():
		if disp not in seen_display_names:
			ordered_display_names.append(disp)
			name_to_code_map[disp] = canonical_language_code(code_value)
			seen_display_names.add(disp)

	return ordered_display_names, name_to_code_map


def build_code_to_display_map(name_to_code_map: dict) -> dict:
	code_to_display_map: dict[str, str] = {}
	for display, code in name_to_code_map.items():
		code_to_display_map.setdefault((code or '').lower(), display)
	legacy_map = {
		'iw': 'he',
		'jw': 'jv',
		'zh_cn': 'zh-cn',
		'zh_tw': 'zh-tw',
		'fil': 'tl',
		'ua': 'uk',
		'nb': 'no',
		'nn': 'no',
	}
	for old_code, new_code in legacy_map.items():
		if new_code in code_to_display_map and old_code not in code_to_display_map:
			code_to_display_map[old_code] = code_to_display_map[new_code]
	return code_to_display_map


def display_to_code(name_to_code_map: dict, display_name: str) -> str:
	return (
		name_to_code_map.get(display_name)
		or name_to_code_map.get((display_name or '').title())
		or 'en'
	)


def is_rtl_language(display_name: str) -> bool:
	normalized = (display_name or '').strip().lower()
	return any(key in normalized for key in ('arabic', 'hebrew', 'urdu', 'persian', 'farsi', 'ar', 'he', 'fa', 'ur'))


def maybe_format_text(text_value: str) -> str:
	formatted = (text_value or '').replace('\r\n', '\n').replace('\r', '\n')
	formatted = re.sub(r'\n{3,}', '\n\n', formatted)
	return formatted.strip()


def normalize_code_for_backend(code: str, backend_key: str) -> str:
	lower_code = (code or '').strip().lower()

	# fast-path 'auto'
	if lower_code in ('auto', ''):
		return 'auto'

	# if backend key is unknown, return best-effort canonical code
	if not backend_key:
		return canonical_language_code(lower_code)

	deep_name_or_code_aliases = {
		# Hebrew: deep-translator may only accept 'iw' (legacy), so normalize to 'iw'
		'he': 'iw', 'iw': 'iw', 'hebrew': 'iw',
		'arabic': 'ar', 'persian': 'fa', 'farsi': 'fa', 'urdu': 'ur',
		'zh': 'zh-CN', 'zh_cn': 'zh-CN', 'zh-cn': 'zh-CN', 'chinese (simplified)': 'zh-CN', 'simplified chinese': 'zh-CN',
		'zh_tw': 'zh-TW', 'zh-tw': 'zh-TW', 'chinese (traditional)': 'zh-TW', 'traditional chinese': 'zh-TW',
		'jw': 'jv', 'javanese': 'jv',
		'en-us': 'en', 'en-gb': 'en', 'pt-br': 'pt', 'pt-pt': 'pt',
		'burmese': 'my', 'myanmar': 'my', 'ukrainian': 'uk', 'ua': 'uk',
		'indonesian': 'id', 'kurdish': 'ku', 'norwegian': 'no', 'nb': 'no', 'nn': 'no',
		'hawaiian': 'haw', 'haw': 'haw',
		'tagalog': 'tl', 'filipino': 'tl', 'fil': 'tl',
		'moldavian': 'ro', 'moldovan': 'ro',
		'japanese': 'ja', 'korean': 'ko', 'french': 'fr', 'german': 'de', 'spanish': 'es', 'italian': 'it',
		'russian': 'ru', 'hindi': 'hi', 'polish': 'pl', 'romanian': 'ro', 'czech': 'cs', 'slovak': 'sk',
		'slovenian': 'sl', 'hungarian': 'hu', 'greek': 'el', 'turkish': 'tr', 'thai': 'th', 'vietnamese': 'vi',
		'welsh': 'cy', 'yiddish': 'yi', 'xhosa': 'xh',
	}

	# googletrans: uses legacy 'iw'/'jw', and 'fil' for Filipino; prefers 'zh-cn'/'zh-tw'
	google_name_or_code_aliases = {
		'he': 'iw', 'iw': 'iw', 'hebrew': 'iw',
		'jv': 'jw', 'jw': 'jw', 'javanese': 'jw',
		'zh': 'zh-cn', 'zh_cn': 'zh-cn', 'zh-cn': 'zh-cn', 'chinese (simplified)': 'zh-cn', 'simplified chinese': 'zh-cn',
		'zh_tw': 'zh-tw', 'zh-tw': 'zh-tw', 'chinese (traditional)': 'zh-tw', 'traditional chinese': 'zh-tw',
		'en-us': 'en', 'en-gb': 'en', 'pt-br': 'pt', 'pt-pt': 'pt',
		'burmese': 'my', 'myanmar': 'my', 'ukrainian': 'uk', 'ua': 'uk',
		'indonesian': 'id', 'kurdish': 'ku', 'norwegian': 'no', 'nb': 'no', 'nn': 'no',
		'hawaiian': 'haw', 'haw': 'haw',
		'tagalog': 'fil', 'filipino': 'fil', 'tl': 'fil',
		'moldavian': 'ro', 'moldovan': 'ro',
		'japanese': 'ja', 'korean': 'ko', 'french': 'fr', 'german': 'de', 'spanish': 'es', 'italian': 'it',
		'russian': 'ru', 'hindi': 'hi', 'polish': 'pl', 'romanian': 'ro', 'czech': 'cs', 'slovak': 'sk',
		'slovenian': 'sl', 'hungarian': 'hu', 'greek': 'el', 'turkish': 'tr', 'thai': 'th', 'vietnamese': 'vi',
		'welsh': 'cy', 'yiddish': 'yi', 'xhosa': 'xh',
	}

	if backend_key in ('deep_translator.google', 'deep', 'deep_translator'):
		mapped = deep_name_or_code_aliases.get(lower_code, lower_code)
		# Normalize deep-translator code case for Chinese if user passed lowercase variants
		if mapped in ('zh-cn', 'zh_cn'):
			mapped = 'zh-CN'
		elif mapped in ('zh-tw', 'zh_tw'):
			mapped = 'zh-TW'

		# Validate against known supported codes if available and repair common mismatches
		try:
			if deep_supported_codes:
				# direct check (compare lower because deep_supported_codes are lowercased)
				if mapped.lower() not in deep_supported_codes:
					candidates = {
						mapped.lower(),
						mapped.replace('-', '_').lower(),
						mapped.replace('_', '-').lower(),
					}
					fixed = next((c for c in candidates if c in deep_supported_codes), None)
					if fixed:
						mapped = 'zh-CN' if fixed == 'zh-cn' else ('zh-TW' if fixed == 'zh-tw' else fixed)
					else:
						# Hebrew special-case: many installs report 'iw' not 'he'
						if mapped.lower() == 'he' and 'iw' in deep_supported_codes:
							mapped = 'iw'
		except Exception:
			pass

		# Final hardening: enforce legacy Hebrew 'iw' for deep if still 'he'
		if mapped.lower() == 'he':
			mapped = 'iw'
		return mapped

	if backend_key == 'googletrans':
		mapped = google_name_or_code_aliases.get(lower_code, lower_code)
		# Validate against known supported codes if available
		try:
			if googletrans_supported_codes and mapped not in googletrans_supported_codes:
				# last-chance fixups
				if mapped == 'he' and 'iw' in googletrans_supported_codes:
					mapped = 'iw'
				elif mapped == 'jv' and 'jw' in googletrans_supported_codes:
					mapped = 'jw'
				elif mapped == 'tl' and 'fil' in googletrans_supported_codes:
					mapped = 'fil'
		except Exception:
			pass
		return mapped

	return lower_code


def normalize_code_from_backend(code: Optional[str], backend_key: Optional[str]) -> Optional[str]:
	if not code:
		return code
	lower_code = str(code).strip().lower()
	legacy_to_canonical_map = {
		'iw': 'he',
		'jw': 'jv',
		'zh_cn': 'zh-cn',
		'zh_tw': 'zh-tw',
		'en-us': 'en',
		'en-gb': 'en',
		'pt-br': 'pt',
		'pt-pt': 'pt',
		'zh-cn': 'zh-cn',
		'zh-tw': 'zh-tw',
		'fil': 'tl',
		'ua': 'uk',
		'zh': 'zh-cn',
	}
	return legacy_to_canonical_map.get(lower_code, lower_code)


def translator_available(selected_backend_var: Optional[StringVar] = None) -> bool:
	selection = (selected_backend_var.get() if selected_backend_var else 'auto') or 'auto'
	selection = selection.strip().lower()
	if selection == 'googletrans':
		return bool(googletrans_available and Translator is not None)
	if selection in ('deep_translator.google', 'deep', 'deep_translator'):
		return bool(deep_translator_available and deep_google_translator is not None)
	return bool(
		(deep_translator_available and deep_google_translator is not None)
		or (googletrans_available and Translator is not None)
	)


def run_translation(
	source_text_value: str,
	source_lang_code: str,
	target_lang_code: str,
	selected_backend_var: Optional[StringVar],
	on_done_callback: Callable[[str, Optional[str], Optional[str]], None],
	on_error_callback: Callable[[Exception], None],
) -> None:
	"""
	Run translation using the preferred backend with chunking and robust fallbacks.
	Ensures compatibility with googletrans==3.1.0a0 (no 'timeout' kw) and deep-translator.
	"""
	try:
		# Guard against non-string inputs and normalize newlines
		source_text_value = '' if source_text_value is None else str(source_text_value)
		# Fast path: nothing to translate
		if not (source_text_value or '').strip():
			on_done_callback('', None, None)
			return

		# Resolve preferred backend from UI selection (or 'auto')
		preference_name = ((selected_backend_var.get() if selected_backend_var else 'auto') or 'auto').strip().lower()

		def can_use_google() -> bool:
			return bool(googletrans_available and Translator is not None)

		def can_use_deep() -> bool:
			return bool(deep_translator_available and deep_google_translator is not None)

		# Decide backend
		if preference_name == 'googletrans' and can_use_google():
			chosen_backend_name: Optional[str] = 'googletrans'
		elif preference_name in ('deep_translator.google', 'deep', 'deep_translator') and can_use_deep():
			chosen_backend_name = 'deep_translator.google'
		elif preference_name == 'auto':
			chosen_backend_name = 'deep_translator.google' if can_use_deep() else ('googletrans' if can_use_google() else None)
		else:
			# Invalid preference or missing package
			chosen_backend_name = None

		if chosen_backend_name is None:
			raise RuntimeError('No translation backend is available')

		# Normalize language codes for the selected backend
		src_for_backend = normalize_code_for_backend(source_lang_code or 'auto', chosen_backend_name)
		dst_for_backend = normalize_code_for_backend(target_lang_code or 'en', chosen_backend_name)
		# Avoid passing 'auto' as a target by mistake
		if (dst_for_backend or '').strip().lower() in ('', 'auto'):
			dst_for_backend = 'en'

		# ---------------- googletrans flow ----------------
		if chosen_backend_name == 'googletrans':
			# googletrans 3.1.0a0 sometimes requires trying several service urls
			service_urls_candidates = [
				['translate.googleapis.com'],
				['translate.google.com'],
				['translate.google.co.kr', 'translate.google.com'],
			]
			last_exc: Optional[Exception] = None
			text_parts = chunk_text(source_text_value, 4500)
			result_chunks: List[str] = []
			detected_source_code: Optional[str] = None

			for urls in service_urls_candidates:
				translator_instance = None
				try:
					# Init translator with candidate urls
					translator_instance = Translator(service_urls=urls)  # type: ignore[arg-type]
				except Exception as e_init:
					last_exc = e_init
					continue

				try:
					result_chunks.clear()
					detected_source_code = None
					for text_part in text_parts:
						# googletrans 3.1.0a0: no 'timeout' kw support here
						translate_kwargs = {'dest': dst_for_backend}
						if src_for_backend and src_for_backend.lower() != 'auto':
							translate_kwargs['src'] = src_for_backend
						translate_result = translator_instance.translate(text_part, **translate_kwargs)  # type: ignore[arg-type]
						if detected_source_code is None:
							detected_source_code = normalize_code_from_backend(getattr(translate_result, 'src', None), chosen_backend_name)
						result_chunks.append(getattr(translate_result, 'text', '') or '')

					# Success with this URL set
					on_done_callback(join_chunks(result_chunks), detected_source_code, 'googletrans')
					return
				except Exception as e_try:
					# Try the next url set
					last_exc = e_try
					continue

			# All service urls failed: attempt deep-translator fallback if available
			if can_use_deep():
				try:
					text_parts_dt = chunk_text(source_text_value, 2800)
					# Reuse a single instance per request for efficiency
					dt_src = 'auto' if (src_for_backend or 'auto').lower() == 'auto' else src_for_backend
					dt = deep_google_translator(source=dt_src, target=dst_for_backend)  # type: ignore[misc]
					result_chunks_dt: List[str] = []
					for text_part in text_parts_dt:
						result_chunks_dt.append(dt.translate(text_part) or '')
					on_done_callback(join_chunks(result_chunks_dt), None, 'deep_translator.google')
					return
				except Exception as e_fallback:
					# Prefer the original googletrans error if present
					on_error_callback(last_exc or e_fallback)
					return

			# No fallback available: surface the last googletrans error
			on_error_callback(last_exc or RuntimeError('googletrans failed'))
			return

		# ---------------- deep-translator flow ----------------
		if not can_use_deep():
			raise RuntimeError('deep-translator backend is not available')

		text_parts_dt = chunk_text(source_text_value, 2800)
		# Reuse single instance for the whole request
		dt_src = 'auto' if (src_for_backend or 'auto').lower() == 'auto' else src_for_backend
		translator_dt = deep_google_translator(source=dt_src, target=dst_for_backend)  # type: ignore[misc]
		result_chunks_dt: List[str] = []
		for text_part in text_parts_dt:
			result_chunks_dt.append(translator_dt.translate(text_part) or '')
		on_done_callback(join_chunks(result_chunks_dt), None, 'deep_translator.google')
		return

	except Exception as exc:
		# One last guard to surface unexpected exceptions
		on_error_callback(exc)

# --------------- main popup ---------------
def open_translate(app):
	selected_backend_var = StringVar(value='deep_translator.google')

	window_root = app.make_pop_ups_window(open_translate, name='translate_app_popup', title='Translate')
	container_frame = ttk.Frame(window_root, padding=(6, 6, 6, 6))
	container_frame.pack(fill='both', expand=True)

	status_text_var = StringVar(value='')
	status_label = ttk.Label(container_frame, textvariable=status_text_var, foreground='gray')

	notebook_widget = ttk.Notebook(container_frame)
	tab_translate = ttk.Frame(notebook_widget)
	tab_history = ttk.Frame(notebook_widget)
	tab_options = ttk.Frame(notebook_widget)
	tab_modules = ttk.Frame(notebook_widget)

	notebook_widget.add(tab_translate, text='Translate')
	notebook_widget.add(tab_history, text='History')
	notebook_widget.add(tab_options, text='Options')
	notebook_widget.add(tab_modules, text='Modules')
	notebook_widget.pack(fill='both', expand=True)
	status_label.pack(fill='x', pady=(4, 0))

	style_manager = ttk.Style()
	try:
		style_manager.configure('GroupTitle.TLabel', foreground='#666666')
		style_manager.configure('TransBtn.TButton', padding=(6, 2))
		style_manager.configure('TransBtnLarge.TButton', padding=(12, 8))
	except Exception:
		pass

	# --------------- translate tab ---------------
	group_quick_actions_label = ttk.Label(tab_translate, text='Quick actions', style='GroupTitle.TLabel')
	group_quick_actions_label.pack(anchor='w', padx=6, pady=(8, 0))

	translate_toolbar_frame = ttk.Frame(tab_translate)
	translate_toolbar_frame.pack(fill='x', pady=(0, 4))

	auto_detect_var = BooleanVar(value=True)
	auto_detect_checkbutton_quick = ttk.Checkbutton(translate_toolbar_frame, text='Auto-detect', variable=auto_detect_var)
	auto_detect_checkbutton_quick.pack(side='left')

	swap_languages_button = ttk.Button(translate_toolbar_frame, text='⇄ Swap')
	swap_languages_button.pack(side='left', padx=(6, 0))

	detect_language_button = ttk.Button(translate_toolbar_frame, text='Detect now')
	detect_language_button.pack(side='left', padx=(6, 0))

	group_languages_label = ttk.Label(tab_translate, text='Language selection', style='GroupTitle.TLabel')
	group_languages_label.pack(anchor='w', padx=6, pady=(8, 0))

	language_selectors_frame = ttk.Frame(tab_translate)
	language_selectors_frame.pack(fill='x', pady=(0, 4))

	from_label = ttk.Label(language_selectors_frame, text='From')
	from_label.grid(row=0, column=0, sticky='w', padx=(0, 4))
	source_language_var = StringVar()
	source_language_combobox = ttk.Combobox(language_selectors_frame, width=22, textvariable=source_language_var, state='readonly')

	to_label = ttk.Label(language_selectors_frame, text='To')
	to_label.grid(row=0, column=2, sticky='w', padx=(8, 4))
	target_language_var = StringVar()
	target_language_combobox = ttk.Combobox(language_selectors_frame, width=22, textvariable=target_language_var, state='readonly')

	display_names, name_to_code_map = build_language_mapping(ui_languages_list)
	code_to_display_map = build_code_to_display_map(name_to_code_map)
	source_values = ['Auto Detect'] + display_names
	target_values = list(display_names)

	source_language_combobox['values'] = source_values
	target_language_combobox['values'] = target_values
	source_language_combobox.grid(row=0, column=1, sticky='ew')
	target_language_combobox.grid(row=0, column=3, sticky='ew')
	language_selectors_frame.columnconfigure(1, weight=1)
	language_selectors_frame.columnconfigure(3, weight=1)

	# ---- Minimal language search inputs under the dropdowns ----
	source_search_var = StringVar(value='')
	target_search_var = StringVar(value='')

	def _filter_values_by_query(full_values: List[str], query: str) -> List[str]:
		"""
		Filter by substring against display names and their codes (case-insensitive).
		We also allow code queries like 'en', 'he', 'iw', etc.
		"""
		q = (query or '').strip().lower()
		if not q:
			return full_values
		def match(disp: str) -> bool:
			code = (name_to_code_map.get(disp) or '').lower()
			return (q in disp.lower()) or (q in code)
		return [v for v in full_values if match(v)]

	def _apply_language_filters(*_):
		# Remember current selections
		cur_src = source_language_combobox.get()
		cur_tgt = target_language_combobox.get()
		# Compute filtered lists (source keeps 'Auto Detect' at top)
		src_filtered_rest = _filter_values_by_query(display_names, source_search_var.get())
		src_filtered = ['Auto Detect'] + src_filtered_rest
		tgt_filtered = _filter_values_by_query(display_names, target_search_var.get())
		# Update comboboxes
		source_language_combobox.configure(values=src_filtered)
		target_language_combobox.configure(values=tgt_filtered)
		# Restore selections if still present; otherwise choose first sensible option
		try:
			if cur_src in src_filtered:
				source_language_combobox.set(cur_src)
			else:
				source_language_combobox.set(src_filtered[0] if src_filtered else 'Auto Detect')
		except Exception:
			pass
		try:
			if cur_tgt in tgt_filtered:
				target_language_combobox.set(cur_tgt)
			elif tgt_filtered:
				target_language_combobox.set(tgt_filtered[0])
		except Exception:
			pass

	# Search row (labels+entries)
	ttk.Label(language_selectors_frame, text='Search').grid(row=1, column=0, sticky='w', padx=(0, 4), pady=(3, 0))
	source_search_entry = ttk.Entry(language_selectors_frame, textvariable=source_search_var, width=22)
	source_search_entry.grid(row=1, column=1, sticky='ew', pady=(3, 0))
	ttk.Label(language_selectors_frame, text='Search').grid(row=1, column=2, sticky='w', padx=(8, 4), pady=(3, 0))
	target_search_entry = ttk.Entry(language_selectors_frame, textvariable=target_search_var, width=22)
	target_search_entry.grid(row=1, column=3, sticky='ew', pady=(3, 0))

	# Clear-on-Escape in search boxes
	def _clear_src_search(_e=None):
		if source_search_var.get():
			source_search_var.set('')
			_apply_language_filters()
	def _clear_tgt_search(_e=None):
		if target_search_var.get():
			target_search_var.set('')
			_apply_language_filters()

	source_search_entry.bind('<Escape>', _clear_src_search)
	target_search_entry.bind('<Escape>', _clear_tgt_search)
	# Live filtering as user types
	source_search_var.trace_add('write', _apply_language_filters)
	target_search_var.trace_add('write', _apply_language_filters)

	# Defaults for combos
	source_language_combobox.current(0)
	try:
		preferred_code = None
		get_language_method = getattr(app, 'get_k_lang', None)
		if callable(get_language_method):
			preferred_code = (get_language_method()[1] or '').lower() or None
		preferred_display_name = code_to_display_map.get(preferred_code, None) if preferred_code else None
		if preferred_display_name and preferred_display_name in target_values:
			target_language_combobox.set(preferred_display_name)
		else:
			english_index = 0
			for display_index, display_value in enumerate(display_names):
				if display_value.lower().startswith('english'):
					english_index = display_index
					break
			target_language_combobox.current(english_index)
	except Exception:
		if target_values:
			target_language_combobox.current(0)

	def filter_combobox_values(combobox_widget: ttk.Combobox, _full_values_unused: List[str]):
		# Keep the user-filtered list persistent: refine the CURRENT list, don't reset to full.
		typed_value = (combobox_widget.get() or '').strip().lower()
		current_values = list(combobox_widget.cget('values')) or []
		if not typed_value:
			# Do nothing here; persistence is controlled exclusively by the search entries
			return
		filtered_values = [value for value in current_values if typed_value in value.lower()]
		if filtered_values:
			combobox_widget.configure(values=filtered_values)

	# Typing inside the combobox itself still narrows the currently shown list
	source_language_combobox.bind('<KeyRelease>', lambda event: filter_combobox_values(source_language_combobox, []))
	target_language_combobox.bind('<KeyRelease>', lambda event: filter_combobox_values(target_language_combobox, []))

	editors_group_label = ttk.Label(tab_translate, text='Editors', style='GroupTitle.TLabel')
	editors_group_label.pack(anchor='w', padx=6, pady=(8, 0))

	editors_frame = ttk.Frame(tab_translate)
	editors_frame.pack(fill='both', expand=True)

	left_editor_frame = ttk.Frame(editors_frame)
	right_editor_frame = ttk.Frame(editors_frame)
	left_editor_frame.pack(side='left', fill='both', expand=True, padx=(0, 3))
	right_editor_frame.pack(side='right', fill='both', expand=True, padx=(3, 0))

	input_label = ttk.Label(left_editor_frame, text='Input')
	input_label.pack(anchor='w', pady=(0, 2))
	input_container_frame, input_text_widget, input_scrollbar = app.make_rich_textbox(left_editor_frame, size=[48, 14])
	input_container_frame.pack(fill='both', expand=True)

	output_label = ttk.Label(right_editor_frame, text='Output')
	output_label.pack(anchor='w', pady=(0, 2))
	output_container_frame, output_text_widget, output_scrollbar = app.make_rich_textbox(right_editor_frame, size=[48, 14])
	output_container_frame.pack(fill='both', expand=True)
	output_text_widget.configure(state=DISABLED)

	clipboard_group_label = ttk.Label(tab_translate, text='Clipboard actions', style='GroupTitle.TLabel')
	clipboard_group_label.pack(anchor='w', padx=6, pady=(8, 0))

	manage_frame = ttk.Frame(tab_translate)
	manage_frame.pack(fill='x', padx=6, pady=(0, 2))

	def copy_from_text(text_widget: tk.Text):
		try:
			selection_text = text_widget.get('sel.first', 'sel.last')
		except TclError:
			selection_text = text_widget.get('1.0', 'end-1c')
		window_root.clipboard_clear()
		window_root.clipboard_append(selection_text)

	def paste_to_text(text_widget: tk.Text):
		try:
			clipboard_text = window_root.clipboard_get()
		except Exception:
			clipboard_text = ''
		if not clipboard_text:
			return
		try:
			text_widget.insert('insert', clipboard_text)
		except Exception:
			pass
		update_counters()

	def select_all_text(text_widget: tk.Text):
		try:
			text_widget.tag_add('sel', '1.0', 'end-1c')
			text_widget.mark_set('insert', '1.0')
			text_widget.see('insert')
		except Exception:
			pass

	def clear_text(text_widget: tk.Text):
		try:
			current_state = str(text_widget.cget('state'))
			if current_state != 'normal':
				text_widget.configure(state='normal')
				text_widget.delete('1.0', 'end')
				text_widget.configure(state=current_state)
			else:
				text_widget.delete('1.0', 'end')
		except Exception:
			pass
		update_counters()

	input_tools_frame = ttk.Frame(manage_frame)
	output_tools_frame = ttk.Frame(manage_frame)
	input_tools_frame.pack(side='left')
	output_tools_frame.pack(side='right')

	input_tools_label = ttk.Label(input_tools_frame, text='Input')
	input_tools_label.pack(side='left')
	input_copy_button = ttk.Button(input_tools_frame, text='Copy', command=lambda: copy_from_text(input_text_widget))
	input_copy_button.pack(side='left', padx=2)
	input_paste_button = ttk.Button(input_tools_frame, text='Paste', command=lambda: paste_to_text(input_text_widget))
	input_paste_button.pack(side='left', padx=2)
	input_select_all_button = ttk.Button(input_tools_frame, text='Select All',
										 command=lambda: select_all_text(input_text_widget))
	input_select_all_button.pack(side='left', padx=2)
	input_clear_button = ttk.Button(input_tools_frame, text='Clear', command=lambda: clear_text(input_text_widget))
	input_clear_button.pack(side='left', padx=2)

	output_tools_label = ttk.Label(output_tools_frame, text='Output')
	output_tools_label.pack(side='left')
	output_copy_button = ttk.Button(output_tools_frame, text='Copy', command=lambda: copy_from_text(output_text_widget))
	output_copy_button.pack(side='left', padx=2)
	output_select_all_button = ttk.Button(output_tools_frame, text='Select All',
										  command=lambda: select_all_text(output_text_widget))
	output_select_all_button.pack(side='left', padx=2)
	output_clear_button = ttk.Button(output_tools_frame, text='Clear', command=lambda: clear_text(output_text_widget))
	output_clear_button.pack(side='left', padx=2)

	stats_group_label = ttk.Label(tab_translate, text='Statistics', style='GroupTitle.TLabel')
	stats_group_label.pack(anchor='w', padx=6, pady=(8, 0))

	counters_frame = ttk.Frame(tab_translate)
	counters_frame.pack(fill='x', padx=6, pady=(0, 6))
	input_counter_var = StringVar(value='Input: 0 chars • 0 words')
	output_counter_var = StringVar(value='Output: 0 chars • 0 words')
	input_counter_label = ttk.Label(counters_frame, textvariable=input_counter_var)
	output_counter_label = ttk.Label(counters_frame, textvariable=output_counter_var)
	input_counter_label.pack(side='left')
	output_counter_label.pack(side='right')

	def count_stats(text_value: str) -> tuple[int, int]:
		content_text = text_value or ''
		return len(content_text), len(content_text.split())

	def update_counters(*_ignored):
		try:
			input_text_value = input_text_widget.get('1.0', 'end-1c')
			output_text_value = get_output_text()
			input_chars, input_words = count_stats(input_text_value)
			output_chars, output_words = count_stats(output_text_value)
			input_counter_var.set(f'Input: {input_chars} chars • {input_words} words')
			output_counter_var.set(f'Output: {output_chars} chars • {output_words} words')
		except Exception:
			pass

	translate_actions_group_label = ttk.Label(tab_translate, text='Translate actions', style='GroupTitle.TLabel')
	translate_actions_group_label.pack(anchor='w', padx=6, pady=(4, 0))

	actions_frame = ttk.Frame(tab_translate)
	actions_frame.pack(fill='x', pady=(0, 4))
	translate_button = ttk.Button(actions_frame, text='Translate')
	copy_from_editor_button = ttk.Button(actions_frame, text='Copy from editor')
	paste_output_to_editor_button = ttk.Button(actions_frame, text='Paste Output to editor')
	swap_text_button = ttk.Button(actions_frame, text='Swap Text')
	reverse_translate_button = ttk.Button(actions_frame, text='Reverse Translate')

	translate_button.grid(row=0, column=0, padx=2, pady=2, sticky='w')
	copy_from_editor_button.grid(row=0, column=1, padx=2, pady=2)
	paste_output_to_editor_button.grid(row=0, column=2, padx=2, pady=2)
	swap_text_button.grid(row=0, column=3, padx=2, pady=2)
	reverse_translate_button.grid(row=0, column=4, padx=2, pady=2)
	for grid_column_index in range(5):
		actions_frame.grid_columnconfigure(grid_column_index, weight=1)

	# --------------- options tab ---------------
	options_automation_label = ttk.Label(tab_options, text='Automation', style='GroupTitle.TLabel')
	options_automation_label.pack(anchor='w', padx=6, pady=(8, 0))

	options_frame = ttk.Frame(tab_options)
	options_frame.pack(fill='x', pady=(0, 0))

	auto_translate_var = BooleanVar(value=True)
	auto_format_var = BooleanVar(value=True)
	lock_source_after_detect_var = BooleanVar(value=False)
	auto_align_rtl_var = BooleanVar(value=True)
	auto_hint_lang_var = BooleanVar(value=True)
	auto_copy_to_editor_var = BooleanVar(value=False)
	auto_clear_input_var = BooleanVar(value=False)
	show_status_line_var = BooleanVar(value=True)
	compact_spacing_var = BooleanVar(value=True)
	large_buttons_var = BooleanVar(value=False)
	high_contrast_var = BooleanVar(value=False)
	editor_font_size_var = IntVar(value=10)
	rtl_hint_var = StringVar(value='')
	history_enabled_var = BooleanVar(value=True)
	debounce_delay_var = IntVar(value=380)
	auto_focus_editor_after_var = BooleanVar(value=False)
	history_limit_var = IntVar(value=500)

	auto_detect_check_options = ttk.Checkbutton(options_frame, text='Auto-detect source', variable=auto_detect_var)
	auto_translate_check = ttk.Checkbutton(options_frame, text='Auto-translate on changes', variable=auto_translate_var)
	auto_format_check = ttk.Checkbutton(options_frame, text='Auto-format inserts', variable=auto_format_var)
	auto_detect_check_options.grid(row=0, column=0, sticky='w')
	auto_translate_check.grid(row=0, column=1, sticky='w', padx=(8, 0))
	auto_format_check.grid(row=0, column=2, sticky='w', padx=(8, 0))

	lock_after_detect_check = ttk.Checkbutton(options_frame, text='Lock source after detect',
											  variable=lock_source_after_detect_var)
	auto_align_rtl_check = ttk.Checkbutton(options_frame, text='Auto-align RTL', variable=auto_align_rtl_var)
	auto_hint_lang_check = ttk.Checkbutton(options_frame, text='Auto-hint language while typing',
										   variable=auto_hint_lang_var)
	lock_after_detect_check.grid(row=1, column=0, sticky='w', pady=(4, 0))
	auto_align_rtl_check.grid(row=1, column=1, sticky='w', padx=(8, 0), pady=(4, 0))
	auto_hint_lang_check.grid(row=1, column=2, sticky='w', padx=(8, 0), pady=(4, 0))

	auto_copy_to_editor_check = ttk.Checkbutton(options_frame, text='Auto-copy output to editor',
												variable=auto_copy_to_editor_var)
	auto_clear_input_check = ttk.Checkbutton(options_frame, text='Auto-clear input after translate',
											 variable=auto_clear_input_var)
	rtl_hint_label = ttk.Label(options_frame, textvariable=rtl_hint_var, foreground='gray')
	auto_copy_to_editor_check.grid(row=2, column=0, sticky='w', pady=(4, 0))
	auto_clear_input_check.grid(row=2, column=1, sticky='w', padx=(8, 0), pady=(4, 0))
	rtl_hint_label.grid(row=2, column=3, sticky='e')
	options_frame.columnconfigure(3, weight=1)

	history_toggle_check = ttk.Checkbutton(options_frame, text='Save translations in History tab',
										   variable=history_enabled_var)
	history_toggle_check.grid(row=3, column=0, sticky='w', pady=(6, 2))

	options_title_label = ttk.Label(tab_options, text='Options • Automation and appearance')
	options_title_label.pack(anchor='w', padx=6, pady=(6, 2))

	behavior_frame = ttk.LabelFrame(tab_options, text='Behavior')
	behavior_frame.pack(fill='x', padx=0, pady=(0, 6))
	debounce_label = ttk.Label(behavior_frame, text='Debounce (ms)')
	debounce_label.grid(row=0, column=0, sticky='w', padx=6, pady=(6, 4))
	debounce_spinbox = ttk.Spinbox(behavior_frame, from_=80, to=3000, increment=20, width=6,
								   textvariable=debounce_delay_var)
	debounce_spinbox.grid(row=0, column=1, sticky='w', pady=(6, 4))
	history_limit_label = ttk.Label(behavior_frame, text='History limit')
	history_limit_label.grid(row=0, column=2, sticky='w', padx=(12, 4), pady=(6, 4))
	history_limit_spinbox = ttk.Spinbox(behavior_frame, from_=50, to=10000, increment=50, width=8,
										textvariable=history_limit_var)
	history_limit_spinbox.grid(row=0, column=3, sticky='w', pady=(6, 4))
	auto_focus_after_check = ttk.Checkbutton(behavior_frame, text='Auto-focus editor after translate',
											 variable=auto_focus_editor_after_var)
	auto_focus_after_check.grid(row=1, column=0, columnspan=4, sticky='w', padx=6, pady=(0, 8))
	behavior_frame.grid_columnconfigure(4, weight=1)

	appearance_frame = ttk.LabelFrame(tab_options, text='Window appearance (local)')
	appearance_frame.pack(fill='x', padx=0, pady=(0, 6))
	compact_spacing_check = ttk.Checkbutton(appearance_frame, text='Compact spacing', variable=compact_spacing_var)
	large_buttons_check = ttk.Checkbutton(appearance_frame, text='Large buttons', variable=large_buttons_var)
	show_status_line_check = ttk.Checkbutton(appearance_frame, text='Show status line', variable=show_status_line_var)
	high_contrast_check = ttk.Checkbutton(appearance_frame, text='High contrast', variable=high_contrast_var)
	editor_font_label = ttk.Label(appearance_frame, text='Editor font size')
	editor_font_spinbox = ttk.Spinbox(appearance_frame, from_=8, to=20, width=5, textvariable=editor_font_size_var)
	compact_spacing_check.grid(row=0, column=0, sticky='w', padx=6, pady=4)
	large_buttons_check.grid(row=0, column=1, sticky='w', padx=6, pady=4)
	show_status_line_check.grid(row=0, column=2, sticky='w', padx=6, pady=4)
	high_contrast_check.grid(row=0, column=3, sticky='w', padx=6, pady=4)
	editor_font_label.grid(row=1, column=0, sticky='w', padx=(6, 4))
	editor_font_spinbox.grid(row=1, column=1, sticky='w', padx=(0, 6))

	primary_buttons: list[ttk.Button] = []

	def collect_primary_buttons():
		primary_buttons.clear()
		try:
			primary_buttons.extend([
				translate_button,
				copy_from_editor_button,
				paste_output_to_editor_button,
				swap_text_button,
				reverse_translate_button,
				swap_languages_button,
				detect_language_button,
			])
		except Exception:
			pass

	def set_buttons_style(is_large: bool):
		style_name = 'TransBtnLarge.TButton' if is_large else 'TransBtn.TButton'
		for button_widget in primary_buttons:
			try:
				button_widget.configure(style=style_name)
			except Exception:
				pass

	def apply_compact_spacing(is_compact: bool):
		try:
			for child_widget in translate_toolbar_frame.winfo_children():
				child_widget.pack_configure(padx=(4 if is_compact else 6), pady=(0 if is_compact else 2))
		except Exception:
			pass
		try:
			for tab_widget in (tab_translate, tab_history, tab_modules):
				tab_widget.configure(padding=(2, 2) if is_compact else (8, 6))
		except Exception:
			pass

	def apply_editor_font(font_size: int):
		try:
			input_text_widget.configure(font=f'arial {font_size}')
		except Exception:
			pass
		try:
			output_text_widget.configure(state=NORMAL)
			output_text_widget.configure(font=f'arial {font_size}')
			output_text_widget.configure(state=DISABLED)
		except Exception:
			pass

	def apply_status_visibility(show_line: bool):
		try:
			if show_line and not status_label.winfo_ismapped():
				status_label.pack(fill='x', pady=(4, 0))
			elif not show_line and status_label.winfo_ismapped():
				status_label.pack_forget()
		except Exception:
			pass

	def apply_high_contrast(enabled: bool):
		try:
			if enabled:
				input_text_widget.configure(bg='black', fg='white', insertbackground='white')
				output_text_widget.configure(state=NORMAL)
				output_text_widget.configure(bg='black', fg='white', insertbackground='white')
				output_text_widget.configure(state=DISABLED)
			else:
				input_text_widget.configure(bg='', fg='', insertbackground='')
				output_text_widget.configure(state=NORMAL)
				output_text_widget.configure(bg='', fg='', insertbackground='')
				output_text_widget.configure(state=DISABLED)
		except Exception:
			pass

	def apply_ui_preferences(*_ignored):
		collect_primary_buttons()
		set_buttons_style(large_buttons_var.get())
		apply_compact_spacing(compact_spacing_var.get())
		apply_editor_font(int(editor_font_size_var.get() or 10))
		apply_status_visibility(show_status_line_var.get())
		apply_high_contrast(high_contrast_var.get())

	for option_var in (compact_spacing_var, large_buttons_var, show_status_line_var, high_contrast_var):
		option_var.trace_add('write', apply_ui_preferences)
	editor_font_size_var.trace_add('write', apply_ui_preferences)

	def apply_alignment(text_widget: Any, justify_right: bool):
		try:
			text_widget.tag_delete('align')
		except Exception:
			pass
		try:
			text_widget.tag_configure('align', justify='right' if justify_right else 'left')
			text_widget.tag_add('align', '1.0', 'end')
		except Exception:
			pass

	def set_output_text(output_text_value: str):
		output_text_widget.configure(state=NORMAL)
		output_text_widget.delete('1.0', END)
		output_text_widget.insert('1.0', output_text_value or '')
		if auto_align_rtl_var.get():
			apply_alignment(output_text_widget, is_rtl_language(target_language_combobox.get()))
		output_text_widget.configure(state=DISABLED)

	def get_output_text() -> str:
		output_text_widget.configure(state=NORMAL)
		content_text = output_text_widget.get('1.0', 'end-1c')
		output_text_widget.configure(state=DISABLED)
		return content_text

	def apply_rtl_alignment_if_needed():
		rtl_mode = is_rtl_language(target_language_combobox.get()) if auto_align_rtl_var.get() else False
		rtl_hint_var.set('RTL' if rtl_mode else '')
		if auto_align_rtl_var.get():
			apply_alignment(input_text_widget, rtl_mode)
			output_text_widget.configure(state=NORMAL)
			apply_alignment(output_text_widget, rtl_mode)
			output_text_widget.configure(state=DISABLED)

	def guess_language_code_for_text(sample_text: str) -> Tuple[str, Optional[float]]:
		text_value = (sample_text or '').strip()
		if not text_value:
			return 'auto', None
		if any('\u0600' <= char <= '\u06FF' for char in text_value):
			return 'ar', None
		if any('\u0590' <= char <= '\u05FF' for char in text_value):
			return 'he', None
		if any('\u0400' <= char <= '\u04FF' for char in text_value):
			return 'ru', None
		if any('\u0900' <= char <= '\u097F' for char in text_value):
			return 'hi', None
		if any('\u4E00' <= char <= '\u9FFF' for char in text_value):
			return 'zh-cn', None
		if any('\u3040' <= char <= '\u30FF' for char in text_value):
			return 'ja', None
		if any('\uAC00' <= char <= '\uD7AF' for char in text_value):
			return 'ko', None
		return 'auto', None

	def detect_language_of_input():
		input_text_value = input_text_widget.get('1.0', 'end-1c').strip()
		if not input_text_value:
			messagebox.showinfo('Detect', 'Input is empty.')
			return
		detected_code, confidence = guess_language_code_for_text(input_text_value)
		detected_code = normalize_code_from_backend(detected_code, None)
		detected_display = code_to_display_map.get(detected_code,
												   detected_code) if detected_code and detected_code != 'auto' else 'unknown'
		if detected_code and detected_code != 'auto':
			status_text_var.set(
				f'Detected source: {detected_display} (confidence: {confidence if confidence is not None else "?"})')
			if lock_source_after_detect_var.get():
				try:
					if detected_display in source_values:
						source_language_combobox.set(detected_display)
						auto_detect_var.set(False)
				except Exception:
					pass
		else:
			status_text_var.set('Detection: unknown')

	detect_language_button.configure(command=detect_language_of_input)

	def copy_from_editor_to_input():
		if hasattr(app, 'is_marked') and app.is_marked():
			content_value = app.EgonTE.get('sel.first', 'sel.last')
		else:
			content_value = app.EgonTE.get('1.0', 'end-1c')
		if auto_format_var.get():
			content_value = maybe_format_text(content_value)
		input_text_widget.delete('1.0', END)
		input_text_widget.insert('1.0', content_value)
		input_text_widget.focus_set()
		apply_rtl_alignment_if_needed()
		if auto_translate_var.get():
			schedule_translation()
		update_counters()

	def paste_output_to_editor():
		content_value = get_output_text()
		if not content_value:
			return
		if hasattr(app, 'is_marked') and app.is_marked():
			app.EgonTE.delete('sel.first', 'sel.last')
			app.EgonTE.insert('insert', content_value)
		else:
			app.EgonTE.insert(app.get_pos(), content_value)

	def swap_languages_selection():
		current_source_display = source_language_combobox.get()
		current_target_display = target_language_combobox.get()
		if not current_source_display or not current_target_display:
			return
		if current_source_display == 'Auto Detect':
			source_language_combobox.set(current_target_display)
			target_language_combobox.set('English' if 'English' in target_values else current_target_display)
		else:
			source_language_combobox.set(current_target_display)
			target_language_combobox.set(current_source_display)
		apply_rtl_alignment_if_needed()
		if input_text_widget.get('1.0', 'end-1c').strip() and auto_translate_var.get():
			schedule_translation()

	def swap_input_output_texts():
		input_value = input_text_widget.get('1.0', 'end-1c')
		output_value = get_output_text()
		input_text_widget.delete('1.0', END)
		input_text_widget.insert('1.0', output_value)
		set_output_text(input_value)
		apply_rtl_alignment_if_needed()
		update_counters()

	def reverse_translate_sequence():
		output_value = get_output_text()
		if not output_value.strip():
			return
		input_text_widget.delete('1.0', END)
		input_text_widget.insert('1.0', output_value)
		swap_languages_selection()
		schedule_translation()

	copy_from_editor_button.configure(command=copy_from_editor_to_input)
	paste_output_to_editor_button.configure(command=paste_output_to_editor)
	swap_languages_button.configure(command=swap_languages_selection)
	swap_text_button.configure(command=swap_input_output_texts)
	reverse_translate_button.configure(command=reverse_translate_sequence)

	# debounced translation trigger
	pending_timer = {'id': None}

	def get_debounce_delay_ms() -> int:
		try:
			value = int(debounce_delay_var.get())
			return max(50, min(3000, value))
		except Exception:
			return 380

	def schedule_translation(_event=None):
		if not auto_translate_var.get():
			return
		if pending_timer['id']:
			try:
				window_root.after_cancel(pending_timer['id'])
			except Exception:
				pass
		pending_timer['id'] = window_root.after(get_debounce_delay_ms(), lambda: translate_now(True))

	def translate_now(_triggered: bool = False):
		if not translator_available(selected_backend_var):
			pref_name = (selected_backend_var.get() or 'auto')
			if pref_name != 'auto':
				messagebox.showinfo('Translator', f'Selected backend "{pref_name}" is not available.')
			else:
				messagebox.showinfo('Translator', 'No translation backend is available.')
			return

		input_text_value = input_text_widget.get('1.0', 'end-1c')
		if not input_text_value.strip():
			set_output_text('')
			status_text_var.set('Enter/import text to translate')
			update_counters()
			return

		if auto_detect_var.get() and auto_hint_lang_var.get() and source_language_combobox.get() in ('',
																									 'Auto Detect') and len(
				input_text_value.strip()) >= 14:
			code_hint, conf_hint = guess_language_code_for_text(input_text_value[:2000])
			if code_hint and code_hint != 'auto':
				disp_hint = code_to_display_map.get(code_hint, code_hint)
				status_text_var.set(f'Hint: {disp_hint} (confidence: {conf_hint if conf_hint is not None else "?"})')

		effective_source_code = 'auto' if (
					auto_detect_var.get() or source_language_combobox.get() == 'Auto Detect') else (
					name_to_code_map.get(source_language_combobox.get()) or 'auto')
		effective_target_code = name_to_code_map.get(target_language_combobox.get()) or 'en'

		translate_button.config(state=DISABLED)
		status_text_var.set('Translating...')
		set_output_text('')

		def on_translation_done(final_text: str, detected_lang_code: Optional[str], backend_name: Optional[str]):
			def ui_update():
				normalized_detected_code = normalize_code_from_backend(detected_lang_code,
																	   backend_name) if detected_lang_code else None
				set_output_text(final_text)
				translate_button.config(state=NORMAL)
				backend_suffix = f' • {backend_name}' if backend_name else ''
				if normalized_detected_code and effective_source_code == 'auto':
					disp = code_to_display_map.get(normalized_detected_code, normalized_detected_code)
					status_text_var.set(f'Detected: {disp}  →  {effective_target_code}{backend_suffix}')
					if lock_source_after_detect_var.get() and disp in source_values:
						source_language_combobox.set(disp)
						auto_detect_var.set(False)
				else:
					status_text_var.set(f'Done  →  {effective_target_code}{backend_suffix}')

				if auto_copy_to_editor_var.get():
					try:
						paste_output_to_editor()
					except Exception:
						pass
				if auto_clear_input_var.get():
					try:
						input_text_widget.delete('1.0', END)
					except Exception:
						pass

				if history_enabled_var.get():
					push_history(
						input_full=input_text_value,
						output_full=final_text,
						src_code=(normalized_detected_code or effective_source_code),
						dst_code=effective_target_code,
						backend=(backend_name or '-'),
					)
				if auto_focus_editor_after_var.get():
					try:
						app.EgonTE.focus_set()
					except Exception:
						pass
				apply_rtl_alignment_if_needed()
				update_counters()

			window_root.after(0, ui_update)

		def on_translation_error(exc: Exception):
			def ui_error():
				translate_button.config(state=NORMAL)
				status_text_var.set('')
				messagebox.showerror('Translation error', f'{exc}')

			window_root.after(0, ui_error)

		threading.Thread(
			target=run_translation,
			args=(input_text_value, effective_source_code, effective_target_code, selected_backend_var,
				  on_translation_done, on_translation_error),
			daemon=True,
		).start()

	translate_button.configure(command=lambda: translate_now(True))

	def on_input_key(_event=None):
		apply_rtl_alignment_if_needed()
		schedule_translation(_event)
		update_counters()

	input_text_widget.bind('<KeyRelease>', on_input_key, add='+')
	window_root.bind('<Control-Return>', lambda event: (translate_now(True), 'break')[1])
	window_root.bind('<Escape>', lambda event: (window_root.destroy(), 'break')[1])
	# Preserve filtered lists on selection; do not clear search fields automatically
	source_language_combobox.bind('<<ComboboxSelected>>', lambda e: (schedule_translation(e)))
	target_language_combobox.bind('<<ComboboxSelected>>', lambda e: (apply_rtl_alignment_if_needed(), schedule_translation(e)))

	# --------------- history tab ---------------
	history_filter_export_label = ttk.Label(tab_history, text='Filter & export', style='GroupTitle.TLabel')
	history_filter_export_label.pack(anchor='w', padx=6, pady=(8, 0))

	history_top_frame = ttk.Frame(tab_history)
	history_top_frame.pack(fill='x', padx=6, pady=6)

	history_filter_label = ttk.Label(history_top_frame, text='Filter:')
	history_filter_label.pack(side='left')
	history_filter_var = StringVar(value='')
	history_filter_entry = ttk.Entry(history_top_frame, textvariable=history_filter_var, width=24)
	history_filter_entry.pack(side='left', padx=(6, 0))
	history_apply_button = ttk.Button(history_top_frame, text='Apply')
	history_clear_button = ttk.Button(history_top_frame, text='Clear Log')
	history_export_json_button = ttk.Button(history_top_frame, text='Export JSON')
	history_export_csv_button = ttk.Button(history_top_frame, text='Export CSV')
	history_export_json_button.pack(side='right')
	history_export_csv_button.pack(side='right', padx=(0, 6))
	history_clear_button.pack(side='right', padx=(6, 0))
	history_apply_button.pack(side='left', padx=6)

	history_log_label = ttk.Label(tab_history, text='History log', style='GroupTitle.TLabel')
	history_log_label.pack(anchor='w', padx=6, pady=(0, 0))

	history_columns = ('time', 'src', 'dst', 'backend', 'src_preview', 'out_preview')
	history_tree = ttk.Treeview(tab_history, columns=history_columns, show='headings', height=10)
	for column_id, column_title in zip(history_columns,
									   ('Time', 'Source', 'Target', 'Backend', 'Input (preview)', 'Output (preview)')):
		history_tree.heading(column_id, text=column_title)
		history_tree.column(column_id, stretch=True, width=120 if column_id in ('src_preview', 'out_preview') else 90,
							anchor='w')
	history_tree.pack(fill='both', expand=True, padx=6, pady=(0, 6))

	history_actions_label = ttk.Label(tab_history, text='Actions', style='GroupTitle.TLabel')
	history_actions_label.pack(anchor='w', padx=6, pady=(0, 0))

	history_buttons_frame = ttk.Frame(tab_history)
	history_buttons_frame.pack(fill='x', padx=6, pady=(0, 6))
	history_reapply_button = ttk.Button(history_buttons_frame, text='Reapply')
	history_copy_input_button = ttk.Button(history_buttons_frame, text='Copy Input')
	history_copy_output_button = ttk.Button(history_buttons_frame, text='Copy Output')
	history_delete_button = ttk.Button(history_buttons_frame, text='Delete Selected')
	history_reapply_button.pack(side='left')
	history_copy_input_button.pack(side='left', padx=6)
	history_copy_output_button.pack(side='left')
	history_delete_button.pack(side='left', padx=6)

	history_rows: list[tuple] = []

	def match_history_filter(history_item: tuple) -> bool:
		query_text = (history_filter_var.get() or '').strip().lower()
		if not query_text:
			return True
		return any(query_text in str(part).lower() for part in history_item)

	def populate_history():
		history_tree.delete(*history_tree.get_children())
		for row_index, history_item in enumerate(history_rows):
			if not match_history_filter(history_item):
				continue
			timestamp_text, source_disp, target_disp, backend_name, source_preview, output_preview, _full_source, _full_output = history_item
			history_tree.insert('', END, iid=str(row_index),
								values=(timestamp_text, source_disp, target_disp, backend_name, source_preview,
										output_preview))

	def preview_text(text_value: str, char_limit: int = 64) -> str:
		single_line = (text_value or '').replace('\n', ' ')
		return single_line if len(single_line) <= char_limit else single_line[:char_limit - 1] + '…'

	def push_history(input_full: str, output_full: str, src_code: str, dst_code: str, backend: str):
		source_display = code_to_display_map.get(src_code, src_code) if src_code else 'auto'
		target_display = code_to_display_map.get(dst_code, dst_code)
		timestamp_text = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		history_row = (
			timestamp_text, source_display, target_display, backend or '-',
			preview_text(input_full), preview_text(output_full), input_full, output_full
		)
		history_rows.append(history_row)
		try:
			limit_value = int(history_limit_var.get())
			if limit_value > 0 and len(history_rows) > limit_value:
				del history_rows[:len(history_rows) - limit_value]
		except Exception:
			pass
		populate_history()
		try:
			history_tree.see(history_tree.get_children()[-1])
		except Exception:
			pass

	def selected_history_indices() -> list[int]:
		index_list: list[int] = []
		for selection_id in history_tree.selection():
			try:
				index_list.append(int(selection_id))
			except Exception:
				continue
		return index_list

	def history_reapply():
		indices = selected_history_indices()
		if not indices:
			return
		selected_index = indices[-1]
		try:
			selected_item = history_rows[selected_index]
		except Exception:
			return
		full_src_text = selected_item[6]
		input_text_widget.delete('1.0', END)
		input_text_widget.insert('1.0', full_src_text)
		apply_rtl_alignment_if_needed()
		if auto_translate_var.get():
			schedule_translation()

	def history_copy(kind: str = 'src'):
		indices = selected_history_indices()
		if not indices:
			return
		selected_index = indices[-1]
		try:
			selected_item = history_rows[selected_index]
		except Exception:
			return
		full_src_text = selected_item[6]
		full_out_text = selected_item[7]
		content_to_copy = full_src_text if kind == 'src' else full_out_text
		try:
			window_root.clipboard_clear()
			window_root.clipboard_append(content_to_copy)
		except Exception:
			pass

	def history_delete():
		indices = sorted(selected_history_indices(), reverse=True)
		if not indices:
			return
		try:
			for index_value in indices:
				if 0 <= index_value < len(history_rows):
					del history_rows[index_value]
		except Exception:
			pass
		populate_history()

	def export_history(fmt: str = 'json'):
		if not history_rows:
			messagebox.showinfo('Export', 'History is empty.')
			return
		try:
			from tkinter import filedialog
			output_path = filedialog.asksaveasfilename(
				title='Export Translation History',
				defaultextension=f'.{fmt}',
				filetypes=[(fmt.upper(), f'*.{fmt}'), ('All files', '*.*')],
				parent=window_root,
			)
		except Exception:
			output_path = ''
		if not output_path:
			return
		try:
			if fmt.lower() == 'json':
				payload = [
					{
						'time': item[0], 'source': item[1], 'target': item[2], 'backend': item[3],
						'input_preview': item[4], 'output_preview': item[5],
						'input_full': item[6], 'output_full': item[7],
					} for item in history_rows
				]
				with open(output_path, 'w', encoding='utf-8') as out_file:
					out_file.write(json.dumps(payload, ensure_ascii=False, indent=2))
			else:
				with open(output_path, 'w', encoding='utf-8', newline='') as out_file:
					csv_writer = csv.writer(out_file)
					csv_writer.writerow(
						['time', 'source', 'target', 'backend', 'input_preview', 'output_preview', 'input_full',
						 'output_full'])
					for row in history_rows:
						csv_writer.writerow(list(row))
			status_text_var.set(f'History exported to {output_path}')
		except Exception as exc:
			messagebox.showerror('Export', f'Failed to export: {exc}')

	history_apply_button.configure(command=populate_history)
	history_clear_button.configure(command=lambda: (history_rows.clear(), populate_history()))
	history_export_json_button.configure(command=lambda: export_history('json'))
	history_export_csv_button.configure(command=lambda: export_history('csv'))
	history_reapply_button.configure(command=history_reapply)
	history_copy_input_button.configure(command=lambda: history_copy('src'))
	history_copy_output_button.configure(command=lambda: history_copy('out'))
	history_delete_button.configure(command=history_delete)

	def apply_history_toggle(*_ignored):
		enabled = bool(history_enabled_var.get())
		try:
			desired_state = NORMAL if enabled else DISABLED
			for button_widget in (
					history_apply_button, history_clear_button, history_export_json_button,
					history_export_csv_button, history_reapply_button, history_copy_input_button,
					history_copy_output_button, history_delete_button
			):
				button_widget.configure(state=desired_state)
			history_filter_entry.configure(state=desired_state)
			style_name = 'Hist.Treeview.Disabled' if not enabled else 'Treeview'
			try:
				style_manager.configure('Hist.Treeview.Disabled', foreground='#888888')
				history_tree.configure(style=style_name)
			except Exception:
				pass
		except Exception:
			pass

	history_enabled_var.trace_add('write', apply_history_toggle)
	apply_history_toggle()

	# --------------- modules tab ---------------
	backend_pref_label = ttk.Label(tab_modules, text='Backend preference', style='GroupTitle.TLabel')
	backend_pref_label.pack(anchor='w', padx=6, pady=(8, 0))

	modules_top_frame = ttk.Frame(tab_modules)
	modules_top_frame.pack(fill='x', padx=6, pady=6)

	preferred_backend_label = ttk.Label(modules_top_frame, text='Preferred backend:')
	preferred_backend_label.pack(side='left')
	backend_choice_combobox = ttk.Combobox(
		modules_top_frame, state='readonly', width=28,
		values=('deep_translator.google', 'googletrans', 'auto'),
		textvariable=selected_backend_var
	)
	backend_choice_combobox.pack(side='left', padx=(6, 0))
	refresh_modules_button = ttk.Button(modules_top_frame, text='Refresh')
	install_module_button = ttk.Button(modules_top_frame, text='Install Selected')
	refresh_modules_button.pack(side='right')
	install_module_button.pack(side='right', padx=(6, 8))

	installed_modules_label = ttk.Label(tab_modules, text='Installed modules', style='GroupTitle.TLabel')
	installed_modules_label.pack(anchor='w', padx=6, pady=(0, 0))

	modules_tree = ttk.Treeview(tab_modules, columns=('package', 'status', 'version'), show='headings', height=6)
	modules_tree.pack(fill='both', expand=True, padx=6, pady=(0, 6))
	modules_tree.heading('package', text='Package')
	modules_tree.heading('status', text='Status')
	modules_tree.heading('version', text='Version')
	modules_tree.column('package', width=180, anchor='w')
	modules_tree.column('status', width=120, anchor='center')
	modules_tree.column('version', width=120, anchor='center')

	modules_hint_label = ttk.Label(
		tab_modules,
		text='Select a row and click "Install Selected" to install missing packages.',
		foreground='gray',
	)
	modules_hint_label.pack(anchor='w', padx=6, pady=(0, 6))

	backends_meta = [
		{'key': 'googletrans', 'pip': 'googletrans==3.1.0a0', 'dists': ['googletrans']},
		{'key': 'deep_translator.google', 'pip': 'deep-translator', 'dists': ['deep-translator', 'deep_translator']},
	]

	# importlib metadata
	try:
		from importlib import metadata as importlib_metadata
	except Exception:  # pragma: no cover
		import importlib_metadata  # type: ignore

		importlib_metadata = importlib_metadata


	def get_package_version(distribution_names: List[str]) -> Optional[str]:
		for dist_name in distribution_names:
			try:
				return importlib_metadata.version(dist_name)
			except Exception:
				continue
		return None

	def is_backend_installed(backend_key: str) -> bool:
		"""Return True if any of the dists for backend_key is present."""
		meta = next((m for m in backends_meta if m['key'] == backend_key), None)
		if not meta:
			return False
		return get_package_version(meta['dists']) is not None


	def refresh_backend_flags():
		nonlocal_google_available = False
		nonlocal_deep_available = False

		global googletrans_available, deep_translator_available, Translator, deep_google_translator, googletrans_module
		# Also refresh language maps for googletrans when available
		global googletrans_langs, googletrans_supported_codes
		try:
			googletrans_module = importlib.import_module('googletrans')
			from googletrans import Translator as google_translator_class  # type: ignore
			Translator = google_translator_class  # type: ignore
			nonlocal_google_available = True
			try:
				# Refresh langs and supported codes to keep alias validation accurate
				googletrans_langs = getattr(googletrans_module, 'LANGUAGES', {}) or {}
				googletrans_supported_codes = {str(k).strip().lower() for k in (googletrans_langs or {}).keys()}
			except Exception:
				# Keep previous values if refresh fails
				pass
		except Exception:
			Translator = None  # type: ignore
			nonlocal_google_available = False

		try:
			importlib.import_module('deep_translator')
			from deep_translator import GoogleTranslator as deep_gt_class  # type: ignore
			deep_google_translator = deep_gt_class  # type: ignore
			nonlocal_deep_available = True
		except Exception:
			deep_google_translator = None  # type: ignore
			nonlocal_deep_available = False

		googletrans_available = nonlocal_google_available
		deep_translator_available = nonlocal_deep_available

	def status_label_for_backend(backend_key: str, is_available: bool) -> str:
		current_selection = (selected_backend_var.get() or 'deep_translator.google').strip().lower()
		if is_available:
			preferred_auto = 'deep_translator.google' if deep_translator_available else 'googletrans'
			effective_backend = current_selection if current_selection != 'auto' else preferred_auto
			return 'active' if effective_backend == backend_key else 'installed'
		return 'not installed'

	def populate_modules_tree():
		modules_tree.delete(*modules_tree.get_children())
		google_status = status_label_for_backend('googletrans', googletrans_available)
		google_version = get_package_version(backends_meta[0]['dists']) or '-'
		modules_tree.insert('', END, iid='googletrans', values=('googletrans', google_status, google_version))
		deep_status = status_label_for_backend('deep_translator.google', deep_translator_available)
		deep_version = get_package_version(backends_meta[1]['dists']) or '-'
		modules_tree.insert('', END, iid='deep_translator.google',
							values=('deep-translator', deep_status, deep_version))

		# Adjust action button label based on selection/installation
		_update_install_button_text()
		# And adjust translate button enablement state
		_apply_backend_enablement()

	def _update_install_button_text():
		sel = modules_tree.selection()
		if not sel:
			try:
				install_module_button.configure(text='Install Selected', state=DISABLED)
			except Exception:
				pass
			return
		backend_key = sel[0]
		try:
			if is_backend_installed(backend_key):
				install_module_button.configure(text='Reinstall Selected', state=NORMAL)
			else:
				install_module_button.configure(text='Install Selected', state=NORMAL)
		except Exception:
			try:
				install_module_button.configure(text='Install Selected', state=NORMAL)
			except Exception:
				pass

	def install_selected_backend():
		selected_items = modules_tree.selection()
		if not selected_items:
			messagebox.showinfo('Modules', 'Select a module first.')
			return
		selected_backend_key = selected_items[0]
		selected_backend_meta = next((meta for meta in backends_meta if meta['key'] == selected_backend_key), None)
		if not selected_backend_meta:
			messagebox.showerror('Modules', f'Unknown module: {selected_backend_key}')
			return
		package_spec = selected_backend_meta['pip']

		# Determine install or reinstall flow
		reinstalling = is_backend_installed(selected_backend_key)
		if reinstalling:
			ask_text = f'Reinstall package "{package_spec}"?\nThis will uninstall then install again.'
		else:
			ask_text = f'Install package "{package_spec}" now?'

		if not messagebox.askyesno('Modules', ask_text):
			return

		try:
			status_text_var.set(('Reinstalling ' if reinstalling else 'Installing ') + package_spec + '...')
			window_root.update_idletasks()
			import subprocess

			# If reinstalling: uninstall all known distributions for this backend first
			if reinstalling:
				for dist in selected_backend_meta.get('dists', []):
					try:
						subprocess.run(
							[sys.executable, '-m', 'pip', 'uninstall', '-y', dist],
							stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
						)
					except Exception:
						# Continue even if uninstall of one dist fails
						pass

			# Install (or re-install) the requested spec
			process = subprocess.run(
				[sys.executable, '-m', 'pip', 'install', package_spec],
				stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
			)
			if process.returncode != 0:
				raise RuntimeError(process.stderr.strip() or 'pip failed')
		except Exception as exc:
			messagebox.showerror('Modules', f'Operation failed:\n{exc}')
			status_text_var.set('')
			return

		refresh_backend_flags()
		populate_modules_tree()
		_apply_backend_enablement()
		status_text_var.set(('Reinstallation' if reinstalling else 'Installation') + ' completed.')


	def on_refresh_modules():
		refresh_backend_flags()
		populate_modules_tree()
		status_text_var.set('Refreshed.')


	refresh_modules_button.configure(command=on_refresh_modules)
	install_module_button.configure(command=install_selected_backend)
	# Live enable/disable Translate button when backend selection changes
	def _apply_backend_enablement(*_a):
		is_avail = translator_available(selected_backend_var)
		try:
			if is_avail:
				translate_button.state(['!disabled'])
			else:
				translate_button.state(['disabled'])
		except Exception:
			pass


	backend_choice_combobox.bind(
		'<<ComboboxSelected>>',
		lambda event: (
			populate_modules_tree(),
			status_text_var.set(f'Backend set to: {selected_backend_var.get()}'),
			_apply_backend_enablement()
		)
	)
	modules_tree.bind('<<TreeviewSelect>>', lambda e: _update_install_button_text())
	on_refresh_modules()
	_apply_backend_enablement()

# tooltips (optional)
	try:
		app.place_toolt((
			(swap_languages_button, 'Swap languages'),
			(translate_button, 'Translate now (Ctrl+Enter)'),
			(copy_from_editor_button, 'Copy selection/file to Input'),
			(paste_output_to_editor_button, 'Paste Output into editor'),
			(swap_text_button, 'Swap text between Input and Output'),
			(reverse_translate_button, 'Move Output to Input, swap languages, translate'),
			(detect_language_button, 'Detect source language now'),
		))
	except Exception:
		pass

	collect_primary_buttons()
	apply_ui_preferences()
	apply_rtl_alignment_if_needed()
	update_counters()

	if not translator_available(selected_backend_var):
		translate_button.state(['disabled'])
		status_text_var.set('No translation backend available. Install deep_translator or googletrans.')
	else:
		translate_button.state(['!disabled'])

	window_root.translate_widgets = {
		'window_root': window_root,
		'container_frame': container_frame,
		'notebook_widget': notebook_widget,
		'tab_translate': tab_translate,
		'tab_history': tab_history,
		'tab_options': tab_options,
		'tab_modules': tab_modules,
		'source_lang_combo': source_language_combobox,
		'target_lang_combo': target_language_combobox,
		'input_text_widget': input_text_widget,
		'output_text_widget': output_text_widget,
		'status_label': status_label,
		'status_text_var': status_text_var,
		'translate_button': translate_button,
		'selected_backend_var': selected_backend_var,
	}

	return window_root
