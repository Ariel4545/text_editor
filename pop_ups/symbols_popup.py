import tkinter as tk
from tkinter import Listbox, END, StringVar, Text, BooleanVar, messagebox
from tkinter import ttk
from typing import Dict, List, Tuple, Optional
import base64
import codecs
from urllib.parse import quote, unquote
import threading
import collections
import json
import os
from pydub import AudioSegment
from pydub.playback import play
import hashlib
import re
import random
from tkinter import filedialog
import uuid

try:
    import lorem

    lorem_installed = True
except ModuleNotFoundError:
    lorem = None
    lorem_installed = False

from dependencies.large_variables import MORSE_CODE_MAP, ROMAN_MAP, ROMAN_PAIRS, characters_dict, LEET_MAP, \
    LEET_MAP_REV, NATO_PHONETIC_MAP


def _get_popup_window(app, title: str) -> tk.Toplevel:
    """Creates and configures a Toplevel window with appropriate fallbacks."""
    builders = getattr(app, 'ui_builders', None)
    if builders and hasattr(builders, 'make_pop_ups_window'):
        try:
            return builders.make_pop_ups_window(
                function=open_symbols_translator_popup,  # used for naming/logging/singleton control
                custom_title=title,
                parent=getattr(app, 'root', None),
                name='symbols_translator_popup',
                topmost=False,
                modal=False,
            )
        except Exception:
            pass

    make_window = getattr(app, 'make_pop_ups_window', None)
    if callable(make_window):
        try:
            return make_window(lambda: None, title)
        except Exception:
            pass

    parent_widget = getattr(app, 'tk', None) or getattr(app, 'root', None)
    if not isinstance(parent_widget, tk.Misc):
        parent_widget = tk._get_default_root() or tk.Tk()
    popup_window = tk.Toplevel(parent_widget)
    popup_window.title(getattr(app, 'title_struct', '') + title)
    if hasattr(app, 'st_value'):
        try:
            popup_window.attributes('-alpha', app.st_value)
        except Exception:
            pass
    return popup_window


def _generate_morse_audio(morse_code: str, dot_duration=50, dash_duration=150, space_duration=50) -> AudioSegment:
    """Generates an audio segment from a Morse code string."""
    dot = AudioSegment.silent(duration=dot_duration)
    dash = AudioSegment.silent(duration=dash_duration)
    space = AudioSegment.silent(duration=space_duration)

    audio = AudioSegment.empty()
    for char in morse_code:
        if char == '.':
            audio += dot
        elif char == '-':
            audio += dash
        elif char == ' ':
            audio += space
        elif char == '/':
            audio += space * 3
    return audio


def _get_language_code(app) -> str:
    """Retrieves the language code from the main application."""
    try:
        get_lang = getattr(app, 'get_k_lang', None)
        if callable(get_lang):
            lang = get_lang()[1] or 'en'
            return lang
    except Exception:
        pass
    return 'en'


def _collect_emoji_values(emoji_lib) -> List[str]:
    """Collects emoji values from the emoji library."""
    emoji_values = []
    if not emoji_lib:
        return emoji_values
    try:
        name_to_emoji = getattr(emoji_lib, 'EMOJI_UNICODE_ENGLISH', None)
        if name_to_emoji:
            return list(name_to_emoji.values())
        emoji_data = getattr(emoji_lib, 'EMOJI_DATA', {}) or {}
        return list(emoji_data.keys())
    except Exception:
        return []


def _transform_case(text_value: str, case_type: str, **kwargs) -> Tuple[bool, str]:
    """Converts the case of the text based on the specified type."""
    if case_type == 'Capitalize':
        return True, text_value.capitalize()
    words = re.findall(r'\w+', text_value.lower())
    if not words:
        return True, text_value

    if case_type == 'camelCase':
        return True, words[0] + ''.join(word.capitalize() for word in words[1:])
    elif case_type == 'PascalCase':
        return True, ''.join(word.capitalize() for word in words)
    elif case_type == 'snake_case':
        return True, '_'.join(words)
    elif case_type == 'kebab-case':
        return True, '-'.join(words)
    return True, text_value


def _transform_hash(text_value: str, hash_type: str, **kwargs) -> Tuple[bool, str]:
    """Hashes the text using the specified algorithm."""
    hasher = hashlib.new(hash_type)
    hasher.update(text_value.encode('utf-8'))
    return True, hasher.hexdigest()


def _transform_sort_lines(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """Sorts the lines of the text alphabetically."""
    lines = text_value.splitlines()
    lines.sort(reverse=is_reverse)
    return True, '\n'.join(lines)


def _transform_natural_sort_lines(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """Sorts the lines of the text using natural sort order."""

    def convert(text): return int(text) if text.isdigit() else text.lower()

    def alphanum_key(key): return [convert(c) for c in re.split('([0-9]+)', key)]

    lines = text_value.splitlines()
    lines.sort(key=alphanum_key, reverse=is_reverse)
    return True, '\n'.join(lines)


def _transform_unique_lines(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """Removes duplicate lines from the text."""
    lines = text_value.splitlines()
    unique_lines = list(dict.fromkeys(lines))
    if is_reverse:
        unique_lines.reverse()
    return True, '\n'.join(unique_lines)


def _transform_shuffle_lines(text_value: str, **kwargs) -> Tuple[bool, str]:
    """Shuffles the lines of the text randomly."""
    lines = text_value.splitlines()
    random.shuffle(lines)
    return True, '\n'.join(lines)


def _transform_uppercase(text_value: str, **kwargs) -> Tuple[bool, str]:
    """Converts the text to uppercase."""
    return True, text_value.upper()


def _transform_lowercase(text_value: str, **kwargs) -> Tuple[bool, str]:
    """Converts the text to lowercase."""
    return True, text_value.lower()


def _generate_lorem_ipsum(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """Generates Lorem Ipsum text."""
    if not lorem_installed:
        return False, "The 'lorem' module is not installed. Please install it to use this feature."
    try:
        count = kwargs.get('lorem_count', 1)
        unit = kwargs.get('lorem_unit', 'paragraphs')
        if unit == 'paragraphs':
            return True, lorem.paragraph(count)
        elif unit == 'sentences':
            return True, lorem.sentence(count)
        else:
            return True, lorem.text(count)
    except Exception as e:
        return False, f'Error: {e}'


def _generate_uuid(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """Generates a UUID."""
    return True, str(uuid.uuid4())


def _transform_html_entities(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """Encodes or decodes HTML entities."""
    if not text_value:
        return True, text_value
    if is_reverse:
        return True, codecs.decode(text_value, 'html_entities')
    return True, codecs.encode(text_value, 'html_entities').decode('utf-8')


def _slugify(text_value: str, **kwargs) -> Tuple[bool, str]:
    """Converts text to a URL-friendly slug."""
    text_value = re.sub(r'[^\w\s-]', '', text_value).strip().lower()
    return True, re.sub(r'[-\s]+', '-', text_value)


def _convert_base(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """Converts a number from one base to another."""
    try:
        from_base = kwargs.get('from_base', 10)
        to_base = kwargs.get('to_base', 16)
        return True, str(int(text_value, from_base)).__format__(f'0{to_base}b')
    except ValueError:
        return False, 'Invalid number for the selected base.'


def _transform_emojis(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """Transforms text to emojis and vice versa."""
    if not text_value:
        return True, text_value
    try:
        emoji_lib = kwargs.get('emoji_lib')
        shortcode_replace = kwargs.get('shortcode_replace')
        language_code = kwargs.get('language_code')
        if is_reverse:
            if emoji_lib:
                return True, emoji_lib.demojize(text_value, language=language_code)
            return True, text_value
        if shortcode_replace:
            return True, shortcode_replace(text_value, default_variant=None)
        if emoji_lib:
            return True, emoji_lib.emojize(text_value, language=language_code)
        return True, text_value
    except Exception as e:
        return False, f'Error: {e}'


def _transform_emoticons(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """Transforms text to emoticons and vice versa."""
    if not text_value:
        return True, text_value
    try:
        from ascii_emoticons import emoticon as ascii_expand, demoticon as ascii_collapse
        return True, ascii_collapse(text_value) if is_reverse else ascii_expand(text_value)
    except Exception:
        pass
    try:
        if is_reverse:
            return True, text_value.replace(':)', ':smile:').replace(':(', ':sad:')
        return True, text_value.replace(':smile:', ':)').replace(':sad:', ':(')
    except Exception as e:
        return False, f'Error: {e}'


def _transform_morse(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """Transforms text to Morse code and vice versa."""
    if not text_value:
        return True, text_value
    try:
        morse_map = kwargs.get('morse_map')
        morse_rev = kwargs.get('morse_rev')
        if not is_reverse:
            morse_words = [' '.join(morse_map.get(ch.upper(), ch) for ch in word) for word in text_value.split(' ')]
            return True, ' / '.join(morse_words).strip()
        reconstructed_words = [''.join(morse_rev.get(token, token) for token in morse_word.strip().split(' ') if token)
                               for morse_word in text_value.split('/')]
        text_out = ' '.join(w for w in reconstructed_words if w)
        return True, text_out.lower().capitalize() if text_out else text_out
    except Exception as e:
        return False, f'Morse Transformation Error: {e}'


def _arabic_to_roman(value: int, pairs: List[Tuple[int, str]]) -> str:
    """Converts an Arabic numeral to a Roman numeral."""
    roman_result = []
    for arabic_value, roman_literal in pairs:
        while value >= arabic_value:
            roman_result.append(roman_literal)
            value -= arabic_value
    return ''.join(roman_result)


def _roman_to_arabic(text_value: str, roman_map: Dict[str, int]) -> int:
    """Converts a Roman numeral to an Arabic numeral."""
    total_value = 0
    i = 0
    while i < len(text_value):
        current_val = roman_map.get(text_value[i], 0)
        next_val = roman_map.get(text_value[i + 1], 0) if i + 1 < len(text_value) else 0
        if current_val < next_val:
            total_value += (next_val - current_val)
            i += 2
        else:
            total_value += current_val
            i += 1
    return total_value


def _transform_roman(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """Transforms text to Roman numerals and vice versa."""
    if not text_value:
        return True, text_value
    try:
        roman_map = kwargs['roman_map']
        roman_pairs = kwargs['roman_pairs']
        if is_reverse:
            return True, ' '.join([str(_roman_to_arabic(token.upper(), roman_map)) if token.isalpha() and all(
                ch in roman_map for ch in token.upper()) else token for token in text_value.split()])
        return True, ' '.join(
            [_arabic_to_roman(int(token), roman_pairs) if token.isdigit() and int(token) > 0 else token for token in
             text_value.split()])
    except Exception as e:
        return False, f'Error: {e}'


def _transform_ascii_art(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """Transforms text to ASCII art."""
    if not text_value:
        return True, text_value
    art_style = kwargs.get('art_style', 'bash')
    justification = kwargs.get('justification', 'left')
    art_dict, _, line_height = characters_dict.get(art_style, ({}, [], 0))
    if not art_dict:
        return False, 'Invalid ASCII art style'

    output_lines = [''] * line_height
    for char in text_value:
        char_art = art_dict.get(char.lower(), art_dict.get(' ', ''))
        char_lines = char_art.split('\n')
        for i in range(len(output_lines)):
            if i < len(char_lines):
                output_lines[i] += char_lines[i]

    if justification != 'left':
        max_len = max(len(line) for line in output_lines)
        for i, line in enumerate(output_lines):
            if justification == 'center':
                output_lines[i] = line.center(max_len)
            elif justification == 'right':
                output_lines[i] = line.rjust(max_len)

    return True, '\n'.join(output_lines)


def _transform_leet(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """Transforms text to Leet speak and vice versa."""
    if not text_value:
        return True, text_value
    if is_reverse:
        return True, ''.join([LEET_MAP_REV.get(char, char) for char in text_value])
    return True, ''.join([LEET_MAP.get(char.upper(), char) for char in text_value])


def _transform_nato(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """Transforms text to the NATO phonetic alphabet."""
    if not text_value:
        return True, text_value
    if is_reverse:
        return False, 'NATO phonetic alphabet is a one-way transformation.'
    return True, ' '.join(NATO_PHONETIC_MAP.get(char.upper(), char) for char in text_value)


def _transform_binary(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """Transforms text to binary and vice versa."""
    if not text_value:
        return True, text_value
    try:
        group_size = kwargs.get('group_size', 0)
        if is_reverse:
            return True, ''.join([chr(int(binary, 2)) for binary in text_value.split()])
        binary_text = ' '.join(format(ord(char), '08b') for char in text_value)
        if group_size > 0:
            binary_text = ' '.join(binary_text[i:i + group_size] for i in range(0, len(binary_text), group_size))
        return True, binary_text
    except (ValueError, TypeError):
        return False, 'Invalid binary input for decoding.'


def _transform_base64(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """Transforms text to Base64 and vice versa."""
    if not text_value:
        return True, text_value
    try:
        if is_reverse:
            return True, base64.b64decode(text_value.encode('utf-8')).decode('utf-8')
        return True, base64.b64encode(text_value.encode('utf-8')).decode('utf-8')
    except Exception as e:
        return False, f'Base64 Error: {e}'


def _transform_hex(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """Transforms text to hexadecimal and vice versa."""
    if not text_value:
        return True, text_value
    try:
        group_size = kwargs.get('group_size', 0)
        if is_reverse:
            return True, bytes.fromhex(text_value).decode('utf-8')
        hex_text = text_value.encode('utf-8').hex()
        if group_size > 0:
            hex_text = ' '.join(hex_text[i:i + group_size] for i in range(0, len(hex_text), group_size))
        return True, hex_text
    except Exception as e:
        return False, f'Hex Error: {e}'


def _transform_url(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """URL-encodes or decodes the text."""
    if not text_value:
        return True, text_value
    if is_reverse:
        return True, unquote(text_value)
    return True, quote(text_value)


def _transform_rot13(text_value: str, is_reverse: bool, **kwargs) -> Tuple[bool, str]:
    """Applies the ROT13 cipher to the text."""
    if not text_value:
        return True, text_value
    return True, codecs.encode(text_value, 'rot_13')


def open_symbols_translator_popup(app) -> None:
    """Opens the main symbols translator popup window."""
    # 1. --- Data & Setup ---
    try:
        import emoji as emoji_lib
    except ImportError:
        emoji_lib = None
    try:
        from ._emoji_replace import _emoji_replace as emoji_shortcode_replace
    except ImportError:
        emoji_shortcode_replace = None

    language_code = _get_language_code(app)
    morse_rev = {v: k for k, v in MORSE_CODE_MAP.items()}
    emoji_values = _collect_emoji_values(emoji_lib)
    try:
        from ascii_emoticons import list_emoticon_aliases
        emoticon_values = list(list_emoticon_aliases())
    except ImportError:
        emoticon_values = [':smile:', ':sad:', ':shrug:', ':tableflip:']

    values_by_mode: Dict[str, List[str]] = {
        'emojis': emoji_values,
        'emoticons': emoticon_values,
        'morse': list(MORSE_CODE_MAP.values()),
        'roman': list(ROMAN_MAP.keys()),
        'ascii_art': list(characters_dict.get('bash', ({}, [], 0))[0].keys()),
        'leet': list(LEET_MAP.keys()),
        'nato': list(NATO_PHONETIC_MAP.keys()),
    }
    transformation_history = collections.deque(maxlen=50)

    favorites_file = 'favorites.json'
    history_file = 'history.json'

    try:
        if os.path.exists(favorites_file):
            with open(favorites_file, 'r') as f:
                favorite_modes = json.load(f)
        else:
            favorite_modes = []
    except (IOError, json.JSONDecodeError):
        favorite_modes = []

    # 2. --- Window Creation ---
    root = _get_popup_window(app, 'Symbols translator')
    root.minsize(600, 500)

    # 3. --- State & UI Variables ---
    state = {'mode': 'emojis', '_is_updating': False}
    art_style_var = StringVar(root, value='bash')
    justification_var = StringVar(root, value='left')
    grouping_var = tk.IntVar(root, value=0)
    dot_duration_var = tk.IntVar(value=50)
    dash_duration_var = tk.IntVar(value=150)
    space_duration_var = tk.IntVar(value=50)
    lorem_count_var = tk.IntVar(value=1)
    lorem_unit_var = tk.StringVar(value='paragraphs')
    from_base_var = tk.IntVar(value=10)
    to_base_var = tk.IntVar(value=16)
    live_transform_var = BooleanVar(value=False)
    output_reverse_var = BooleanVar(value=False)
    list_in_window_var = BooleanVar(value=False)
    embedded_list_visible = BooleanVar(value=False)
    natural_sort_var = BooleanVar(value=False)
    clear_on_transform_var = BooleanVar(value=False)
    copy_on_transform_var = BooleanVar(value=False)
    keep_on_top_var = BooleanVar(value=False)
    autoload_history_var = BooleanVar(value=False)
    confirm_clear_history_var = BooleanVar(value=True)
    save_history_var = BooleanVar(value=True)
    confirm_remove_favorite_var = BooleanVar(value=True)
    sort_favorites_var = BooleanVar(value=False)
    show_history_tab_var = BooleanVar(value=True)
    show_favorites_tab_var = BooleanVar(value=True)
    shrink_to_fit_var = BooleanVar(value=False)
    action_buttons_cols_var = StringVar(value='5')
    embedded_search_var = StringVar()
    compact_mode_var = BooleanVar(value=False)

    core_action_buttons = ['Run', 'Reverse', 'Swap', 'Copy']
    optional_action_buttons = ['List', 'Random', 'Clear', 'Favorite', 'Load', 'Save']
    action_button_vars = {name: BooleanVar(value=True) for name in optional_action_buttons}

    # --- Settings Management ---
    def load_settings():
        try:
            settings = app.data.get('symbols_popup_settings', {})
            if not settings:
                return

            live_transform_var.set(settings.get('live_transform', False))
            output_reverse_var.set(settings.get('output_reverse', False))
            list_in_window_var.set(settings.get('list_in_window', False))
            natural_sort_var.set(settings.get('natural_sort', False))
            clear_on_transform_var.set(settings.get('clear_on_transform', False))
            copy_on_transform_var.set(settings.get('copy_on_transform', False))
            keep_on_top_var.set(settings.get('keep_on_top', False))
            autoload_history_var.set(settings.get('autoload_history', False))
            confirm_clear_history_var.set(settings.get('confirm_clear_history', True))
            save_history_var.set(settings.get('save_history', True))
            confirm_remove_favorite_var.set(settings.get('confirm_remove_favorite', True))
            sort_favorites_var.set(settings.get('sort_favorites', False))
            show_history_tab_var.set(settings.get('show_history_tab', True))
            show_favorites_tab_var.set(settings.get('show_favorites_tab', True))
            shrink_to_fit_var.set(settings.get('shrink_to_fit', False))
            action_buttons_cols_var.set(settings.get('action_buttons_cols', '5'))
            compact_mode_var.set(settings.get('compact_mode', False))

            ab_vis_settings = settings.get('action_button_visibility', {})
            for name, var in action_button_vars.items():
                var.set(ab_vis_settings.get(name, True))

        except Exception:
            pass

    def save_settings(*args):
        try:
            if not hasattr(app, 'data'):
                app.data = {}

            settings = {
                'live_transform': live_transform_var.get(),
                'output_reverse': output_reverse_var.get(),
                'list_in_window': list_in_window_var.get(),
                'natural_sort': natural_sort_var.get(),
                'clear_on_transform': clear_on_transform_var.get(),
                'copy_on_transform': copy_on_transform_var.get(),
                'keep_on_top': keep_on_top_var.get(),
                'autoload_history': autoload_history_var.get(),
                'confirm_clear_history': confirm_clear_history_var.get(),
                'save_history': save_history_var.get(),
                'confirm_remove_favorite': confirm_remove_favorite_var.get(),
                'sort_favorites': sort_favorites_var.get(),
                'show_history_tab': show_history_tab_var.get(),
                'show_favorites_tab': show_favorites_tab_var.get(),
                'shrink_to_fit': shrink_to_fit_var.get(),
                'action_buttons_cols': action_buttons_cols_var.get(),
                'compact_mode': compact_mode_var.get(),
                'action_button_visibility': {name: var.get() for name, var in action_button_vars.items()}
            }
            app.data['symbols_popup_settings'] = settings

            if hasattr(app, 'saved_settings'):
                app.saved_settings(special_mode='save')
        except Exception:
            pass

    # 4. --- Core Function Definitions ---
    def create_case_transformer(case_type):
        return lambda text, is_reverse, **kwargs: _transform_case(text, case_type=case_type, **kwargs)

    def create_hash_transformer(hash_type):
        return lambda text, is_reverse, **kwargs: _transform_hash(text, hash_type=hash_type, **kwargs)

    TRANSFORM_MAP = {
        'emojis': _transform_emojis,
        'emoticons': _transform_emoticons,
        'morse': _transform_morse,
        'roman': _transform_roman,
        'ascii_art': _transform_ascii_art,
        'leet': _transform_leet,
        'nato': _transform_nato,
        'binary': _transform_binary,
        'base64': _transform_base64,
        'hex': _transform_hex,
        'url': _transform_url,
        'rot13': _transform_rot13,
        'UPPERCASE': _transform_uppercase,
        'lowercase': _transform_lowercase,
        'Sort Lines': _transform_sort_lines,
        'Natural Sort': _transform_natural_sort_lines,
        'Unique Lines': _transform_unique_lines,
        'Shuffle Lines': _transform_shuffle_lines,
        'Lorem Ipsum': _generate_lorem_ipsum,
        'UUID': _generate_uuid,
        'HTML Entities': _transform_html_entities,
        'Slugify': _slugify,
        'Number Base': _convert_base,
    }

    for case_type in ['camelCase', 'PascalCase', 'snake_case', 'kebab-case', 'Capitalize']:
        TRANSFORM_MAP[case_type] = create_case_transformer(case_type)

    for hash_type in ['md5', 'sha1', 'sha256', 'sha512', 'sha3_256', 'sha3_512']:
        TRANSFORM_MAP[hash_type] = create_hash_transformer(hash_type)

    def get_input_text() -> str:
        try:
            return input_text.get('1.0', 'end-1c')
        except Exception:
            return ''

    def set_input_text(new_text: str):
        try:
            input_text.delete('1.0', 'end')
            input_text.insert('1.0', new_text)
        except Exception:
            pass

    def get_output_text() -> str:
        try:
            return output_text.get('1.0', 'end-1c')
        except Exception:
            return ''

    def set_output_text(new_text: str, is_error: bool = False):
        try:
            output_text.config(state='normal', fg='red' if is_error else 'black')
            output_text.delete('1.0', 'end')
            output_text.insert('1.0', new_text)
        except Exception:
            pass

    def get_transformed_text(text_value: str, is_reverse: bool) -> Tuple[bool, str]:
        mode = state['mode']
        transform_func = TRANSFORM_MAP.get(mode)
        if transform_func:
            try:
                kwargs = {
                    'art_style': art_style_var.get(),
                    'justification': justification_var.get(),
                    'group_size': grouping_var.get(),
                    'lorem_count': lorem_count_var.get(),
                    'lorem_unit': lorem_unit_var.get(),
                    'from_base': from_base_var.get(),
                    'to_base': to_base_var.get(),
                    'emoji_lib': emoji_lib,
                    'shortcode_replace': emoji_shortcode_replace,
                    'language_code': language_code,
                    'morse_map': MORSE_CODE_MAP,
                    'morse_rev': morse_rev,
                    'roman_map': ROMAN_MAP,
                    'roman_pairs': ROMAN_PAIRS,
                }
                return transform_func(text_value, is_reverse=is_reverse, **kwargs)
            except Exception as e:
                return False, f'Transformation Error: {e}'
        return True, text_value

    def update_output(event=None):
        if state['_is_updating']:
            return
        if not live_transform_var.get():
            set_output_text('Live transform is off. To enable it, check the box above.')
            output_text.config(state='disabled', fg='grey')
            return

        state['_is_updating'] = True
        text_value = get_input_text()
        is_reverse = output_reverse_var.get()
        success, transformed_text = get_transformed_text(text_value, is_reverse)

        set_output_text(transformed_text, not success)
        state['_is_updating'] = False

    def update_input(event=None):
        if state['_is_updating']:
            return
        if not live_transform_var.get():
            return

        state['_is_updating'] = True
        text_value = get_output_text()
        is_reverse = not output_reverse_var.get()
        success, transformed_text = get_transformed_text(text_value, is_reverse)

        if success:
            set_input_text(transformed_text)
        state['_is_updating'] = False

    def update_mode(new_mode: str):
        state['mode'] = new_mode
        for button in mode_buttons.values():
            button.configure(style='TButton')
        if new_mode in mode_buttons:
            mode_buttons[new_mode].configure(style='Active.TButton')

        # Update tab titles to show the active one
        for tab_id in modes_notebook.tabs():
            current_text = modes_notebook.tab(tab_id, 'text')
            modes_notebook.tab(tab_id, text=current_text.replace(' *', ''))

        for tab_frame, button_keys in button_layout_config.items():
            if new_mode in button_keys:
                current_text = modes_notebook.tab(tab_frame, 'text')
                if not current_text.endswith(' *'):
                    modes_notebook.tab(tab_frame, text=current_text + ' *')
                break

        list_button.config(state=tk.NORMAL if values_by_mode.get(new_mode) else tk.DISABLED)
        random_button.config(state=tk.NORMAL if values_by_mode.get(new_mode) else tk.DISABLED)
        hide_embedded_list()

        for widget in contextual_controls_frame.winfo_children():
            widget.grid_forget()
        contextual_controls_frame.pack_forget()

        contextual_widgets = {
            'ascii_art': [art_style_menu, justification_menu],
            'morse': [morse_controls_frame],
            'binary': [grouping_menu],
            'hex': [grouping_menu],
            'Lorem Ipsum': [lorem_ipsum_frame] if lorem_installed else [],
            'Number Base': [number_base_frame],
            'Sort Lines': [natural_sort_check],
        }

        if new_mode in contextual_widgets:
            contextual_controls_frame.pack(pady=5, fill='x')
            widgets_to_show = contextual_widgets[new_mode]
            for i, widget in enumerate(widgets_to_show):
                contextual_controls_frame.grid_columnconfigure(i, weight=1)
                widget.grid(row=0, column=i, padx=2, pady=2, sticky='ew')
        update_output()

    def run_transform(is_reverse: bool = False):
        mode = state['mode']
        is_generator = mode in ['Lorem Ipsum', 'UUID']

        source_text = get_output_text() if is_reverse else get_input_text()

        if not source_text and not is_generator:
            return

        try:
            success, new_text = get_transformed_text(source_text, is_reverse)
            if success:
                if copy_on_transform_var.get():
                    root.clipboard_clear()
                    root.clipboard_append(new_text)

                if is_generator:
                    set_input_text(new_text)
                    set_output_text('')
                elif is_reverse:
                    set_input_text(new_text)
                else:
                    set_output_text(new_text)
                    if clear_on_transform_var.get():
                        set_input_text('')

                add_to_history(mode, source_text, new_text, is_reverse)
            else:
                set_output_text(new_text, is_error=True)
        except Exception as e:
            set_output_text(f'An unexpected error occurred: {e}', is_error=True)

    def add_to_history(mode, input_text, output_text, is_reverse):
        direction = 'Reverse' if is_reverse else 'Forward'
        entry = (mode, direction, input_text, output_text)
        if entry not in transformation_history:
            transformation_history.appendleft(entry)
        update_history_display()

    def update_history_display():
        for i in history_tree.get_children():
            history_tree.delete(i)
        for i, (mode, direction, input_text, output_text) in enumerate(transformation_history):
            history_tree.insert("", 'end', iid=i, values=(mode, direction, input_text[:30], output_text[:30]))

    def on_history_select(event):
        if not history_tree.selection():
            return
        selected_id = history_tree.selection()[0]
        mode, direction, input_text, output_text = transformation_history[int(selected_id)]
        update_mode(mode)
        set_input_text(input_text)
        set_output_text(output_text)

    def clear_history():
        if confirm_clear_history_var.get():
            if not messagebox.askyesno('Confirm', 'Are you sure you want to clear the history?'):
                return
        transformation_history.clear()
        update_history_display()

    def save_favorites():
        try:
            with open(favorites_file, 'w') as f:
                json.dump(favorite_modes, f)
        except IOError:
            pass

    def add_to_favorites():
        mode = state['mode']
        if mode not in favorite_modes:
            favorite_modes.append(mode)
            update_favorites_display()
            save_favorites()

    def remove_favorite():
        selected_indices = favorites_listbox.curselection()
        if selected_indices:
            if confirm_remove_favorite_var.get():
                if not messagebox.askyesno('Confirm', 'Are you sure you want to remove this favorite?'):
                    return
            selected_mode = favorites_listbox.get(selected_indices[0])
            if selected_mode in favorite_modes:
                favorite_modes.remove(selected_mode)
                update_favorites_display()
                save_favorites()

    def update_favorites_display():
        favorites_listbox.delete(0, END)
        modes_to_display = sorted(favorite_modes) if sort_favorites_var.get() else favorite_modes
        for mode in modes_to_display:
            favorites_listbox.insert(END, mode)

    def on_favorite_select(event):
        selected_indices = favorites_listbox.curselection()
        if selected_indices:
            selected_mode = favorites_listbox.get(selected_indices[0])
            update_mode(selected_mode)

    def show_list():
        if list_in_window_var.get():
            if embedded_list_visible.get():
                hide_embedded_list()
            else:
                show_embedded_list()
        else:
            hide_embedded_list()  # Ensure embedded is hidden if we open the popup
            show_list_popup()

    def show_list_popup():
        items = values_by_mode.get(state['mode'], [])
        if not items:
            return

        list_root = _get_popup_window(app, f"List of {state['mode']}")
        list_root.transient(root)
        list_root.grab_set()

        top_frame = ttk.Frame(list_root)
        top_frame.pack(fill='x', padx=10, pady=10)
        search_var = StringVar()
        search_entry = ttk.Entry(top_frame, textvariable=search_var)
        search_entry.pack(fill='x')

        tree_frame = ttk.Frame(list_root)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        tree = ttk.Treeview(tree_frame, columns=('Item',), show='headings', selectmode='extended')
        tree.heading('Item', text='Item')
        tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        def update_list(event=None):
            search_term = search_var.get().lower()
            tree.delete(*tree.get_children())
            for item in items:
                if search_term in str(item).lower():
                    try:
                        tree.insert("", 'end', values=(str(item),))
                    except tk.TclError:
                        pass

        def get_selected_items():
            return [tree.item(i, 'values')[0] for i in tree.selection()]

        def insert_items():
            selected = get_selected_items()
            if selected:
                set_input_text(get_input_text() + ' '.join(selected) + ' ')

        def copy_items():
            selected = get_selected_items()
            if selected:
                root.clipboard_clear()
                root.clipboard_append(' '.join(selected))

        def copy_and_close():
            copy_items()
            list_root.destroy()

        button_frame = ttk.Frame(list_root)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))

        insert_button = ttk.Button(button_frame, text='Insert', command=insert_items)
        copy_button_popup = ttk.Button(button_frame, text='Copy', command=copy_items)
        copy_close_button = ttk.Button(button_frame, text='Copy & Close', command=copy_and_close)

        insert_button.pack(side='left', expand=True, fill='x', padx=2)
        copy_button_popup.pack(side='left', expand=True, fill='x', padx=2)
        copy_close_button.pack(side='left', expand=True, fill='x', padx=2)

        search_var.trace_add('write', update_list)
        tree.bind('<Double-1>', lambda e: (insert_items(), list_root.destroy()))
        update_list()
        search_entry.focus_set()

    def show_embedded_list():
        embedded_list_visible.set(True)
        list_button.configure(style='Active.TButton')
        output_section_frame.pack_forget()
        embedded_list_frame.pack(fill='both', expand=True)
        update_embedded_list()

    def hide_embedded_list():
        embedded_list_visible.set(False)
        list_button.configure(style='TButton')
        embedded_list_frame.pack_forget()
        output_section_frame.pack(fill='both', expand=True)

    def update_embedded_list(*args):
        search_term = embedded_search_var.get().lower()
        embedded_list_tree.delete(*embedded_list_tree.get_children())
        items = values_by_mode.get(state['mode'], [])
        for item in items:
            if search_term in str(item).lower():
                try:
                    embedded_list_tree.insert("", 'end', values=(str(item),))
                except tk.TclError:
                    pass

    def on_embedded_list_select(event=None):
        selected_items = [embedded_list_tree.item(i, 'values')[0] for i in embedded_list_tree.selection()]
        if selected_items:
            set_input_text(get_input_text() + ' '.join(selected_items) + ' ')

    def copy_output_to_clipboard():
        root.clipboard_clear()
        root.clipboard_append(get_output_text())

    def insert_random_item():
        """Inserts a random item from the current mode's collection."""
        mode = state['mode']
        collection = values_by_mode.get(mode, [])
        if not collection:
            return
        try:
            item = random.choice(list(collection))
            set_input_text(get_input_text() + f'{item} ')
        except Exception as e:
            messagebox.showerror('Error', f'Could not insert random item: {e}')

    def swap_texts():
        """Swaps the text between the input and output boxes."""
        input_content = get_input_text()
        output_content = get_output_text()
        set_input_text(output_content)
        set_output_text(input_content)

    def load_from_file():
        filepath = filedialog.askopenfilename()
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    set_input_text(f.read())
            except Exception as e:
                messagebox.showerror('File Error', f'Could not read file: {e}')

    def save_to_file():
        filepath = filedialog.asksaveasfilename(defaultextension='.txt',
                                                filetypes=[('Text files', '*.txt'), ('All files', '*.*')])
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(get_output_text())
            except Exception as e:
                messagebox.showerror('File Error', f'Could not write to file: {e}')

    def on_close():
        save_settings()
        if save_history_var.get():
            try:
                with open(history_file, 'w') as f:
                    json.dump(list(transformation_history), f)
            except IOError:
                pass
        if 'input_keyrelease_id' in locals() and input_keyrelease_id:
            input_text.unbind('<KeyRelease>', input_keyrelease_id)
        if 'output_keyrelease_id' in locals() and output_keyrelease_id:
            output_text.unbind('<KeyRelease>', output_keyrelease_id)
        root.destroy()

    def play_morse_audio():
        text_to_play = get_output_text()
        audio = _generate_morse_audio(text_to_play, dot_duration_var.get(), dash_duration_var.get(),
                                      space_duration_var.get())
        threading.Thread(target=play, args=(audio,)).start()

    def save_morse_audio():
        text_to_play = get_output_text()
        audio = _generate_morse_audio(text_to_play, dot_duration_var.get(), dash_duration_var.get(),
                                      space_duration_var.get())
        filepath = filedialog.asksaveasfilename(defaultextension='.wav', filetypes=[('WAV files', '*.wav')])
        if filepath:
            audio.export(filepath, format='wav')

    def toggle_tabs():
        # Correctly hide or show the History tab
        try:
            if show_history_tab_var.get():
                nb.add(tabs['History'])
            else:
                nb.hide(tabs['History'])
        except tk.TclError:
            pass  # Tab might not exist or already in the desired state

        # Correctly hide or show the Favorites tab
        try:
            if show_favorites_tab_var.get():
                nb.add(tabs['Favorites'])
            else:
                nb.hide(tabs['Favorites'])
        except tk.TclError:
            pass  # Tab might not exist or already in the desired state

    def update_action_buttons_layout(*args):
        for widget in action_buttons_frame.winfo_children():
            widget.grid_forget()

        visible_buttons = core_action_buttons + [name for name, var in action_button_vars.items() if var.get()]
        num_visible = len(visible_buttons)

        # Update symmetric column options
        divisors = [str(i) for i in range(2, num_visible + 1) if num_visible % i == 0]
        if not divisors and num_visible > 0:
            divisors.append(str(num_visible))
        if not divisors:
            divisors = ['1']
            
        action_buttons_cols_combo['values'] = divisors
        if action_buttons_cols_var.get() not in divisors:
            action_buttons_cols_var.set(divisors[-1])

        max_cols = int(action_buttons_cols_var.get())

        for i, button_name in enumerate(visible_buttons):
            button = action_buttons[button_name]
            row = i // max_cols
            col = i % max_cols
            action_buttons_frame.grid_columnconfigure(col, weight=1)
            button.grid(row=row, column=col, padx=2, pady=2, sticky='ew')

    def on_main_tab_changed(event=None):
        if shrink_to_fit_var.get():
            selected_tab_name = nb.tab(nb.select(), 'text')
            light_content_tabs = ['History', 'Favorites', 'Options']
            if selected_tab_name in light_content_tabs:
                if io_paned_window in main_paned_window.panes():
                    main_paned_window.remove(io_paned_window)
            else:
                if io_paned_window not in main_paned_window.panes():
                    main_paned_window.add(io_paned_window, weight=1)

    def toggle_compact_mode():
        is_compact = compact_mode_var.get()
        button_map = {
            'Run': ('Run', '▶'),
            'Reverse': ('Reverse', '◀'),
            'Swap': ('Swap', '⇄'),
            'List': ('List', '☰'),
            'Random': ('Random', '🎲'),
            'Clear': ('Clear', '🗑️'),
            'Favorite': ('Favorite', '⭐'),
            'Copy': ('Copy', '📋'),
            'Load': ('Load', '📂'),
            'Save': ('Save', '💾'),
        }
        for name, (text, icon) in button_map.items():
            if name in action_buttons:
                action_buttons[name].config(text=icon if is_compact else text)

    # 5. --- UI Widget Creation ---
    style = ttk.Style()
    style.configure('Active.TButton', background='#d0d0d0', relief='sunken')

    main_paned_window = ttk.PanedWindow(root, orient=tk.VERTICAL)
    nb = ttk.Notebook(main_paned_window)
    io_paned_window = ttk.PanedWindow(main_paned_window, orient=tk.VERTICAL)

    tabs = {name: ttk.Frame(nb) for name in ['Modes', 'History', 'Favorites', 'Options']}

    modes_notebook = ttk.Notebook(tabs['Modes'])
    modes_tabs = {name: ttk.Frame(modes_notebook) for name in
                  ['Fun & Ciphers', 'Encodings & Web', 'Case', 'Hashing', 'Text Manipulation', 'Data']}

    input_frame = ttk.Labelframe(io_paned_window, text='Input')
    input_text = Text(input_frame, height=10, relief='flat', borderwidth=0)
    
    output_container = ttk.Frame(io_paned_window)
    output_section_frame = ttk.Labelframe(output_container, text='Output')
    embedded_list_frame = ttk.Labelframe(output_container, text='List')

    options_frame = tabs['Options']
    options_notebook = ttk.Notebook(options_frame)
    transformation_options_tab = ttk.Frame(options_notebook)
    appearance_options_tab = ttk.Frame(options_notebook)
    history_options_tab = ttk.Frame(options_notebook)
    favorites_options_tab = ttk.Frame(options_notebook)
    action_buttons_options_tab = ttk.Frame(options_notebook)

    top_controls_frame = ttk.Frame(root)
    action_buttons_frame = ttk.Frame(top_controls_frame)

    action_buttons = {
        'Run': ttk.Button(action_buttons_frame, text='Run'),
        'Reverse': ttk.Button(action_buttons_frame, text='Reverse'),
        'Swap': ttk.Button(action_buttons_frame, text='Swap'),
        'List': ttk.Button(action_buttons_frame, text='List'),
        'Random': ttk.Button(action_buttons_frame, text='Random'),
        'Clear': ttk.Button(action_buttons_frame, text='Clear'),
        'Favorite': ttk.Button(action_buttons_frame, text='Favorite'),
        'Copy': ttk.Button(action_buttons_frame, text='Copy'),
        'Load': ttk.Button(action_buttons_frame, text='Load'),
        'Save': ttk.Button(action_buttons_frame, text='Save')
    }
    run_button, reverse_button, swap_button, list_button, random_button, clear_button, favorite_button, copy_button, load_button, save_button = action_buttons.values()

    contextual_controls_frame = ttk.Frame(root)
    art_style_menu = ttk.Combobox(contextual_controls_frame, textvariable=art_style_var,
                                  values=list(characters_dict.keys()), state='readonly')
    justification_menu = ttk.Combobox(contextual_controls_frame, textvariable=justification_var,
                                      values=['left', 'center', 'right'], state='readonly')
    grouping_menu = ttk.Combobox(contextual_controls_frame, textvariable=grouping_var, values=[0, 2, 4, 8],
                                 state='readonly')
    morse_controls_frame = ttk.Frame(contextual_controls_frame)
    lorem_ipsum_frame = ttk.Frame(contextual_controls_frame)
    number_base_frame = ttk.Frame(contextual_controls_frame)
    natural_sort_check = ttk.Checkbutton(contextual_controls_frame, text='Natural Sort', variable=natural_sort_var)
    lorem_count_spinbox = ttk.Spinbox(lorem_ipsum_frame, from_=1, to=100, textvariable=lorem_count_var)
    lorem_unit_menu = ttk.Combobox(lorem_ipsum_frame, textvariable=lorem_unit_var,
                                   values=['paragraphs', 'sentences', 'words'], state='readonly')
    from_base_menu = ttk.Combobox(number_base_frame, textvariable=from_base_var, values=[2, 8, 10, 16],
                                  state='readonly')
    to_base_menu = ttk.Combobox(number_base_frame, textvariable=to_base_var, values=[2, 8, 10, 16], state='readonly')
    play_morse_button = ttk.Button(morse_controls_frame, text='Play Morse')
    save_morse_button = ttk.Button(morse_controls_frame, text='Save Audio')
    dot_slider = ttk.Scale(morse_controls_frame, from_=10, to=200, orient=tk.HORIZONTAL, variable=dot_duration_var)
    dash_slider = ttk.Scale(morse_controls_frame, from_=50, to=400, orient=tk.HORIZONTAL, variable=dash_duration_var)
    space_slider = ttk.Scale(morse_controls_frame, from_=10, to=200, orient=tk.HORIZONTAL, variable=space_duration_var)

    button_layout_config = {
        modes_tabs['Fun & Ciphers']: ['emojis', 'emoticons', 'ascii_art', 'roman', 'leet', 'rot13'],
        modes_tabs['Encodings & Web']: ['morse', 'binary', 'nato', 'base64', 'hex', 'url', 'HTML Entities', 'Slugify'],
        modes_tabs['Case']: ['camelCase', 'PascalCase', 'snake_case', 'kebab-case', 'Capitalize', 'UPPERCASE', 'lowercase'],
        modes_tabs['Hashing']: ['md5', 'sha1', 'sha256', 'sha512', 'sha3_256', 'sha3_512'],
        modes_tabs['Text Manipulation']: ['Sort Lines', 'Natural Sort', 'Unique Lines', 'Shuffle Lines'],
        modes_tabs['Data']: ['Lorem Ipsum', 'UUID', 'Number Base']
    }

    mode_buttons = {}
    MAX_COLS = 4
    for frame, buttons in button_layout_config.items():
        for i, button_key in enumerate(buttons):
            row, col = i // MAX_COLS, i % MAX_COLS
            button = ttk.Button(frame, text=button_key)
            mode_buttons[button_key] = button
            button.grid(row=row, column=col, padx=2, pady=2, sticky='nsew')
        for i in range(MAX_COLS):
            frame.grid_columnconfigure(i, weight=1)

    live_transform_check = ttk.Checkbutton(transformation_options_tab, text='Live Transform', variable=live_transform_var)
    output_reverse_check = ttk.Checkbutton(transformation_options_tab, text='Reverse', variable=output_reverse_var)
    output_text_frame = ttk.Frame(output_section_frame, relief='sunken', borderwidth=1)
    output_text = Text(output_text_frame, height=10, relief='flat', borderwidth=0)
    
    # Embedded List View Widgets
    embedded_list_search_entry = ttk.Entry(embedded_list_frame, textvariable=embedded_search_var)
    embedded_list_tree_frame = ttk.Frame(embedded_list_frame)
    embedded_list_tree = ttk.Treeview(embedded_list_tree_frame, columns=('Item',), show='headings', selectmode='extended')
    embedded_list_scrollbar = ttk.Scrollbar(embedded_list_tree_frame, orient='vertical', command=embedded_list_tree.yview)
    embedded_list_tree.configure(yscrollcommand=embedded_list_scrollbar.set)
    embedded_list_button_frame = ttk.Frame(embedded_list_frame)
    embedded_list_insert_button = ttk.Button(embedded_list_button_frame, text='Insert')
    embedded_list_copy_button = ttk.Button(embedded_list_button_frame, text='Copy')
    embedded_list_close_button = ttk.Button(embedded_list_button_frame, text='Close List', command=hide_embedded_list)

    history_tree = ttk.Treeview(tabs['History'], columns=('Mode', 'Direction', 'Input', 'Output'), show='headings')
    favorites_listbox = Listbox(tabs['Favorites'])
    clear_history_button = ttk.Button(tabs['History'], text='Clear History')
    remove_favorite_button = ttk.Button(tabs['Favorites'], text='Remove Favorite')

    # 6. --- UI Layout ---
    main_paned_window.pack(fill='both', expand=True, padx=10, pady=5)
    main_paned_window.add(nb)
    main_paned_window.add(io_paned_window, weight=1)

    contextual_controls_frame.pack(pady=5, fill='x', padx=10)
    top_controls_frame.pack(side='bottom', fill='x', padx=10, pady=(0, 5))

    io_paned_window.add(input_frame, weight=1)
    io_paned_window.add(output_container, weight=1)
    output_section_frame.pack(fill='both', expand=True)

    for name, frame in tabs.items():
        nb.add(frame, text=name)

    modes_notebook.pack(fill='both', expand=True)
    for name, frame in modes_tabs.items():
        modes_notebook.add(frame, text=name)

    input_text.pack(fill='both', expand=True)

    action_buttons_frame.pack(fill='x', expand=True)

    options_notebook.pack(fill='both', expand=True, padx=5, pady=5)
    options_notebook.add(transformation_options_tab, text='Transformation')
    options_notebook.add(appearance_options_tab, text='Appearance')
    options_notebook.add(history_options_tab, text='History')
    options_notebook.add(favorites_options_tab, text='Favorites')
    options_notebook.add(action_buttons_options_tab, text='Action Buttons')

    live_transform_check.pack(anchor='w', padx=10, pady=2)
    output_reverse_check.pack(anchor='w', padx=10, pady=2)
    ttk.Checkbutton(transformation_options_tab, text='Clear Input on Transform', variable=clear_on_transform_var).pack(
        anchor='w', padx=10, pady=2)
    ttk.Checkbutton(transformation_options_tab, text='Copy to Clipboard on Transform', variable=copy_on_transform_var).pack(
        anchor='w', padx=10, pady=2)

    ttk.Checkbutton(appearance_options_tab, text='Show List in Window', variable=list_in_window_var).pack(anchor='w', padx=10, pady=2)
    ttk.Checkbutton(appearance_options_tab, text='Keep Window on Top', variable=keep_on_top_var,
                    command=lambda: root.attributes('-topmost', keep_on_top_var.get())).pack(anchor='w', padx=10, pady=2)
    ttk.Checkbutton(appearance_options_tab, text='Show History Tab', variable=show_history_tab_var, command=toggle_tabs).pack(anchor='w', padx=10, pady=2)
    ttk.Checkbutton(appearance_options_tab, text='Show Favorites Tab', variable=show_favorites_tab_var, command=toggle_tabs).pack(anchor='w', padx=10, pady=2)
    ttk.Checkbutton(appearance_options_tab, text='Shrink to Fit Content', variable=shrink_to_fit_var, command=on_main_tab_changed).pack(anchor='w', padx=10, pady=2)
    ttk.Checkbutton(appearance_options_tab, text='Compact Mode', variable=compact_mode_var, command=toggle_compact_mode).pack(anchor='w', padx=10, pady=2)

    ttk.Checkbutton(history_options_tab, text='Auto-load last history entry on startup',
                    variable=autoload_history_var).pack(anchor='w', padx=10, pady=2)
    ttk.Checkbutton(history_options_tab, text='Confirm before clearing history',
                    variable=confirm_clear_history_var).pack(anchor='w', padx=10, pady=2)
    ttk.Checkbutton(history_options_tab, text='Save history on exit', variable=save_history_var).pack(anchor='w', padx=10, pady=2)

    ttk.Checkbutton(favorites_options_tab, text='Confirm before removing a favorite',
                    variable=confirm_remove_favorite_var).pack(anchor='w', padx=10, pady=2)
    ttk.Checkbutton(favorites_options_tab, text='Sort Favorites Alphabetically', variable=sort_favorites_var, command=update_favorites_display).pack(anchor='w', padx=10, pady=2)

    ttk.Label(action_buttons_options_tab, text='Number of Columns:').pack(anchor='w', padx=10, pady=(10, 2))
    action_buttons_cols_combo = ttk.Combobox(action_buttons_options_tab, textvariable=action_buttons_cols_var, state='readonly')
    action_buttons_cols_combo.pack(anchor='w', padx=10, pady=2, fill='x')

    action_buttons_visibility_frame = ttk.Labelframe(action_buttons_options_tab, text='Visible Buttons')
    action_buttons_visibility_frame.pack(fill='x', expand=True, padx=10, pady=10)
    MAX_COLS_ACTION_OPTIONS = 2
    for i, name in enumerate(optional_action_buttons):
        var = action_button_vars[name]
        row, col = i // MAX_COLS_ACTION_OPTIONS, i % MAX_COLS_ACTION_OPTIONS
        ttk.Checkbutton(action_buttons_visibility_frame, text=name, variable=var, command=update_action_buttons_layout).grid(row=row, column=col, sticky='w', padx=5, pady=2)
        action_buttons_visibility_frame.columnconfigure(col, weight=1)

    ttk.Label(morse_controls_frame, text='Dot (ms)').grid(row=0, column=0, sticky='ew')
    ttk.Label(morse_controls_frame, text='Dash (ms)').grid(row=0, column=1, sticky='ew')
    ttk.Label(morse_controls_frame, text='Space (ms)').grid(row=0, column=2, sticky='ew')
    dot_slider.grid(row=1, column=0, padx=2, pady=2, sticky='ew')
    dash_slider.grid(row=1, column=1, padx=2, pady=2, sticky='ew')
    space_slider.grid(row=1, column=2, padx=2, pady=2, sticky='ew')
    play_morse_button.grid(row=2, column=0, columnspan=2, padx=2, pady=2, sticky='ew')
    save_morse_button.grid(row=2, column=2, padx=2, pady=2, sticky='ew')
    lorem_ipsum_frame.grid_columnconfigure(0, weight=1)
    lorem_ipsum_frame.grid_columnconfigure(1, weight=1)
    lorem_count_spinbox.grid(row=0, column=0, padx=2, pady=2, sticky='ew')
    lorem_unit_menu.grid(row=0, column=1, padx=2, pady=2, sticky='ew')
    number_base_frame.grid_columnconfigure(0, weight=1)
    number_base_frame.grid_columnconfigure(1, weight=1)
    from_base_menu.grid(row=0, column=0, padx=2, pady=2, sticky='ew')
    to_base_menu.grid(row=0, column=1, padx=2, pady=2, sticky='ew')

    output_text_frame.pack(fill='both', expand=True, padx=5, pady=5)
    output_text.pack(fill='both', expand=True)
    
    embedded_list_search_entry.pack(fill='x', padx=5, pady=5)
    embedded_list_tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
    embedded_list_tree.pack(side='left', fill='both', expand=True)
    embedded_list_scrollbar.pack(side='right', fill='y')
    embedded_list_button_frame.pack(fill='x', padx=5, pady=5)
    embedded_list_insert_button.pack(side='left', expand=True, fill='x', padx=2)
    embedded_list_copy_button.pack(side='left', expand=True, fill='x', padx=2)
    embedded_list_close_button.pack(side='left', expand=True, fill='x', padx=2)

    history_frame = tabs['History']
    history_frame.rowconfigure(0, weight=1)
    history_frame.columnconfigure(0, weight=1)
    history_tree.grid(row=0, column=0, sticky='nsew')
    clear_history_button.grid(row=1, column=0, sticky='ew')

    history_tree.heading('Mode', text='Mode', anchor='w')
    history_tree.heading('Direction', text='Direction', anchor='w')
    history_tree.heading('Input', text='Input', anchor='w')
    history_tree.heading('Output', text='Output', anchor='w')
    history_tree.column('Mode', width=100)
    history_tree.column('Direction', width=80)
    history_tree.column('Input', width=200)
    history_tree.column('Output', width=200)

    favorites_frame = tabs['Favorites']
    favorites_frame.rowconfigure(0, weight=1)
    favorites_frame.columnconfigure(0, weight=1)
    favorites_listbox.grid(row=0, column=0, sticky='nsew')
    remove_favorite_button.grid(row=1, column=0, sticky='ew')

    def set_initial_sash():
        root.update_idletasks()
        options_frame.update_idletasks()
        req_height = options_frame.winfo_reqheight()
        sash_position = max(150, req_height + 40)  # Ensure a minimum height
        main_paned_window.sashpos(0, sash_position)

    root.after(100, set_initial_sash)

    # 7. --- UI Configuration & Binding ---
    run_button.configure(command=lambda: run_transform(False))
    reverse_button.configure(command=lambda: run_transform(True))
    swap_button.configure(command=swap_texts)
    list_button.configure(command=show_list)
    random_button.configure(command=insert_random_item)
    clear_button.configure(command=lambda: (set_input_text(''), set_output_text('')))
    load_button.configure(command=load_from_file)
    save_button.configure(command=save_to_file)
    favorite_button.configure(command=add_to_favorites)
    clear_history_button.configure(command=clear_history)
    remove_favorite_button.configure(command=remove_favorite)
    copy_button.configure(command=copy_output_to_clipboard)
    live_transform_check.configure(command=update_output)
    output_reverse_check.configure(command=update_output)
    lorem_count_spinbox.configure(command=update_output)
    play_morse_button.configure(command=play_morse_audio)
    save_morse_button.configure(command=save_morse_audio)
    dot_slider.configure(command=lambda e: update_output())
    dash_slider.configure(command=lambda e: update_output())
    space_slider.configure(command=lambda e: update_output())
    art_style_menu.bind('<<ComboboxSelected>>', update_output)
    justification_menu.bind('<<ComboboxSelected>>', update_output)
    grouping_menu.bind('<<ComboboxSelected>>', update_output)
    lorem_unit_menu.bind('<<ComboboxSelected>>', update_output)
    from_base_menu.bind('<<ComboboxSelected>>', update_output)
    to_base_menu.bind('<<ComboboxSelected>>', update_output)
    natural_sort_check.configure(command=update_output)
    action_buttons_cols_var.trace_add('write', update_action_buttons_layout)
    action_buttons_cols_combo.bind('<<ComboboxSelected>>', update_action_buttons_layout)
    embedded_search_var.trace_add('write', update_embedded_list)
    embedded_list_tree.bind('<<TreeviewSelect>>', on_embedded_list_select)
    history_tree.bind('<<TreeviewSelect>>', on_history_select)
    favorites_listbox.bind('<<ListboxSelect>>', on_favorite_select)
    nb.bind('<<NotebookTabChanged>>', on_main_tab_changed)
    for key, button in mode_buttons.items():
        button.configure(command=lambda k=key: update_mode(k))
    if not lorem_installed:
        mode_buttons['Lorem Ipsum'].config(state=tk.DISABLED)
    input_keyrelease_id = input_text.bind('<KeyRelease>', update_output, add='+')
    output_keyrelease_id = output_text.bind('<KeyRelease>', update_input, add='+')

    # Bind settings variables to save function
    settings_vars = [
        live_transform_var, output_reverse_var, list_in_window_var, natural_sort_var,
        clear_on_transform_var, copy_on_transform_var, keep_on_top_var, autoload_history_var,
        confirm_clear_history_var, save_history_var, confirm_remove_favorite_var,
        sort_favorites_var, show_history_tab_var, show_favorites_tab_var, shrink_to_fit_var,
        action_buttons_cols_var, compact_mode_var
    ]
    for var in settings_vars:
        var.trace_add('write', save_settings)
    for var in action_button_vars.values():
        var.trace_add('write', save_settings)

    # 8. --- Finalization ---
    root.protocol('WM_DELETE_WINDOW', on_close)
    builders = getattr(app, 'ui_builders', None)
    if builders:
        try:
            # Tooltips setup
            builders.place_toolt(mode_buttons['emojis'], 'Work with emojis (:shortcodes: <-> emoji)')
            builders.place_toolt(mode_buttons['emoticons'], 'Work with ASCII/kaomoji emoticons (:alias: <-> ASCII)')
            builders.place_toolt(mode_buttons['morse'], 'Morse code translator (Text <-> Morse)')
            builders.place_toolt(mode_buttons['roman'], 'Roman numerals translator (Arabic <-> Roman)')
            builders.place_toolt(mode_buttons['ascii_art'], 'Convert text to ASCII art')
            builders.place_toolt(mode_buttons['leet'], 'Convert text to Leet speak')
            builders.place_toolt(mode_buttons['nato'], 'Convert text to NATO phonetic alphabet')
            builders.place_toolt(mode_buttons['binary'], 'Convert text to binary')
            builders.place_toolt(mode_buttons['base64'], 'Encode/decode Base64')
            builders.place_toolt(mode_buttons['hex'], 'Encode/decode Hex')
            builders.place_toolt(mode_buttons['url'], 'Encode/decode URL')
            builders.place_toolt(mode_buttons['rot13'], 'Apply ROT13 cipher')
            builders.place_toolt(mode_buttons['camelCase'], 'Convert text to camelCase')
            builders.place_toolt(mode_buttons['PascalCase'], 'Convert text to PascalCase')
            builders.place_toolt(mode_buttons['snake_case'], 'Convert text to snake_case')
            builders.place_toolt(mode_buttons['kebab-case'], 'Convert text to kebab-case')
            builders.place_toolt(mode_buttons['Capitalize'], 'Capitalize the first character of the text')
            builders.place_toolt(mode_buttons['UPPERCASE'], 'Convert text to UPPERCASE')
            builders.place_toolt(mode_buttons['lowercase'], 'Convert text to lowercase')
            builders.place_toolt(mode_buttons['md5'], 'Calculate MD5 hash')
            builders.place_toolt(mode_buttons['sha1'], 'Calculate SHA-1 hash')
            builders.place_toolt(mode_buttons['sha256'], 'Calculate SHA-256 hash')
            builders.place_toolt(mode_buttons['sha512'], 'Calculate SHA-512 hash')
            builders.place_toolt(mode_buttons['sha3_256'], 'Calculate SHA3-256 hash')
            builders.place_toolt(mode_buttons['sha3_512'], 'Calculate SHA3-512 hash')
            builders.place_toolt(mode_buttons['Sort Lines'], 'Sort lines alphabetically')
            builders.place_toolt(mode_buttons['Natural Sort'], 'Sort lines using natural number order')
            builders.place_toolt(mode_buttons['Unique Lines'], 'Remove duplicate lines')
            builders.place_toolt(mode_buttons['Shuffle Lines'], 'Shuffle lines randomly')
            builders.place_toolt(mode_buttons['Lorem Ipsum'], 'Generate Lorem Ipsum text')
            builders.place_toolt(mode_buttons['UUID'], 'Generate a UUID')
            builders.place_toolt(mode_buttons['HTML Entities'], 'Encode/decode HTML entities')
            builders.place_toolt(mode_buttons['Slugify'], 'Convert text to a URL-friendly slug')
            builders.place_toolt(mode_buttons['Number Base'], 'Convert numbers between bases')
            builders.place_toolt(run_button, 'Run the selected transformation on the input text')
            builders.place_toolt(reverse_button, 'Run the reverse of the selected transformation')
            builders.place_toolt(swap_button, 'Swap the contents of the input and output boxes')
            builders.place_toolt(list_button, 'Show a list of items for the current mode')
            builders.place_toolt(random_button, 'Insert a random item for the current mode')
            builders.place_toolt(clear_button, 'Clear the input text')
            builders.place_toolt(copy_button, 'Copy output to clipboard')
            builders.place_toolt(load_button, 'Load text from a file into the input box')
            builders.place_toolt(save_button, 'Save the output text to a file')
            builders.place_toolt(favorite_button, 'Add the current mode to your favorites')
            builders.place_toolt(play_morse_button, 'Play Morse code audio from output')
            builders.place_toolt(save_morse_button, 'Save Morse code audio from output to a file')
        except Exception:
            pass
        try:
            root.bind('<Return>', lambda e: run_transform(False))
        except Exception:
            pass
    else:
        try:
            root.bind('<Escape>', lambda e: on_close())
            root.bind('<Control-w>', lambda e: on_close())
            root.bind('<Return>', lambda e: run_transform(False))
        except Exception:
            pass

    if save_history_var.get():
        try:
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history_list = json.load(f)
                    transformation_history.extend(history_list)
                    update_history_display()
                    if autoload_history_var.get() and transformation_history:
                        history_tree.selection_set(history_tree.get_children()[0])
                        on_history_select(None)
        except (IOError, json.JSONDecodeError):
            pass

    load_settings()
    toggle_tabs()
    update_action_buttons_layout()
    on_main_tab_changed(None)
    update_mode('emojis')
    update_output()
    update_favorites_display()
    toggle_compact_mode()
