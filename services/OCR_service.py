import os
import tempfile
import tkinter as tk
import requests
import zipfile
import io
import json
from shutil import which as shutil_which, move as shutil_move, rmtree
from platform import system as platform_system
from threading import Thread

try:
    from PIL import Image, ImageOps, ImageFilter, ImageGrab
except ImportError:
    Image = None
    ImageOps = None
    ImageFilter = None
    ImageGrab = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

# --- Service States ---
ACTIVE = 'ACTIVE'
DISABLED = 'DISABLED'
INITIALIZING = 'INITIALIZING'
DOWNLOADING = 'DOWNLOADING'
EXTRACTING = 'EXTRACTING'
ERROR = 'ERROR'

# --- Constants ---
TESSERACT_PORTABLE_URL = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-w32-v5.3.3.20231005.zip"
LANGUAGE_PACKS_URL = "https://api.github.com/repos/tesseract-ocr/tessdata_fast/contents/"
INSTALL_DIR = "."
EXTRACT_DIR = "Tesseract-OCR-portable"

# --- Language Code to Name Mapping ---
LANG_CODE_TO_NAME = {
    'afr': 'Afrikaans', 'amh': 'Amharic', 'ara': 'Arabic', 'asm': 'Assamese', 'aze': 'Azerbaijani',
    'aze_cyrl': 'Azerbaijani (Cyrillic)', 'bel': 'Belarusian', 'ben': 'Bengali', 'bod': 'Tibetan',
    'bos': 'Bosnian', 'bre': 'Breton', 'bul': 'Bulgarian', 'cat': 'Catalan', 'ceb': 'Cebuano',
    'ces': 'Czech', 'chi_sim': 'Chinese (Simplified)', 'chi_tra': 'Chinese (Traditional)',
    'chr': 'Cherokee', 'cos': 'Corsican', 'cym': 'Welsh', 'dan': 'Danish', 'deu': 'German',
    'dzo': 'Dzongkha', 'ell': 'Greek', 'eng': 'English', 'enm': 'English (Middle)', 'epo': 'Esperanto',
    'est': 'Estonian', 'eus': 'Basque', 'fao': 'Faroese', 'fas': 'Persian', 'fil': 'Filipino',
    'fin': 'Finnish', 'fra': 'French', 'frk': 'German (Fraktur)', 'frm': 'French (Middle)',
    'fry': 'Western Frisian', 'gla': 'Scottish Gaelic', 'gle': 'Irish', 'glg': 'Galician',
    'grc': 'Greek (Ancient)', 'guj': 'Gujarati', 'hat': 'Haitian Creole', 'heb': 'Hebrew',
    'hin': 'Hindi', 'hrv': 'Croatian', 'hun': 'Hungarian', 'hye': 'Armenian', 'iku': 'Inuktitut',
    'ind': 'Indonesian', 'isl': 'Icelandic', 'ita': 'Italian', 'ita_old': 'Italian (Old)',
    'jav': 'Javanese', 'jpn': 'Japanese', 'kan': 'Kannada', 'kat': 'Georgian',
    'kat_old': 'Georgian (Old)', 'kaz': 'Kazakh', 'khm': 'Khmer', 'kir': 'Kyrgyz', 'kmr': 'Kurmanji',
    'kor': 'Korean', 'kor_vert': 'Korean (Vertical)', 'lao': 'Lao', 'lat': 'Latin', 'lav': 'Latvian',
    'lit': 'Lithuanian', 'ltz': 'Luxembourgish', 'mal': 'Malayalam', 'mar': 'Marathi', 'mkd': 'Macedonian',
    'mlt': 'Maltese', 'mon': 'Mongolian', 'mri': 'Maori', 'msa': 'Malay', 'mya': 'Burmese',
    'nep': 'Nepali', 'nld': 'Dutch', 'nor': 'Norwegian', 'oci': 'Occitan', 'ori': 'Oriya',
    'osd': 'Orientation and Script Detection', 'pan': 'Punjabi', 'pol': 'Polish', 'por': 'Portuguese',
    'pus': 'Pashto', 'que': 'Quechua', 'ron': 'Romanian', 'rus': 'Russian', 'san': 'Sanskrit',
    'sin': 'Sinhala', 'slk': 'Slovak', 'slv': 'Slovenian', 'snd': 'Sindhi', 'spa': 'Spanish',
    'spa_old': 'Spanish (Old)', 'sqi': 'Albanian', 'srp': 'Serbian', 'srp_latn': 'Serbian (Latin)',
    'sun': 'Sundanese', 'swa': 'Swahili', 'swe': 'Swedish', 'syr': 'Syriac', 'tam': 'Tamil',
    'tat': 'Tatar', 'tel': 'Telugu', 'tgk': 'Tajik', 'tha': 'Thai', 'tir': 'Tigrinya', 'ton': 'Tonga',
    'tur': 'Turkish', 'uig': 'Uyghur', 'ukr': 'Ukrainian', 'urd': 'Urdu', 'uzb': 'Uzbek',
    'uzb_cyrl': 'Uzbek (Cyrillic)', 'vie': 'Vietnamese', 'yid': 'Yiddish', 'yor': 'Yoruba'
}

# --- Module-level cache ---
_tesseract_installed = None
_available_languages = None
_remote_languages_cache = None
_tesseract_path = None
_tessdata_prefix = None


def get_language_name(lang_code):
    """Returns the full language name for a given Tesseract language code."""
    return LANG_CODE_TO_NAME.get(lang_code, lang_code)


def get_tesseract_install_dir():
    """Returns the absolute path for the portable Tesseract installation."""
    return os.path.abspath(os.path.join(INSTALL_DIR, EXTRACT_DIR))


def get_tesseract_zip_path():
    """Returns the absolute path where the Tesseract zip should be placed for manual install."""
    return os.path.abspath(INSTALL_DIR)


def get_tessdata_prefix():
    """Returns the path to the tessdata directory, if found."""
    return _tessdata_prefix


def get_tesseract_path():
    """Returns the discovered path to the Tesseract executable."""
    global _tesseract_path
    return _tesseract_path


def is_tesseract_installed():
    """Checks if the Tesseract executable is installed and caches the result."""
    global _tesseract_installed
    if _tesseract_installed is None:
        if pytesseract is None:
            _tesseract_installed = False
            return False
        try:
            # Attempt to get version using the configured path or system PATH
            pytesseract.get_tesseract_version()
            _tesseract_installed = True
        except (getattr(pytesseract, 'TesseractNotFoundError', FileNotFoundError), FileNotFoundError):
            _tesseract_installed = False
    return _tesseract_installed


def get_available_languages(force_refresh=False, print_fn=print):
    """
    Returns a sorted list of available Tesseract OCR languages, with 'eng' prioritized.
    Caches the result to avoid repeated, slow calls to the Tesseract executable.
    'osd' is excluded as it's for script detection, not a user-selectable language.
    """
    global _available_languages
    if _available_languages is not None and not force_refresh:
        print_fn(f"Using cached available languages: {_available_languages}")
        return _available_languages

    if not is_tesseract_installed():
        print_fn("Tesseract not installed, cannot get available languages.")
        _available_languages = ['eng'] # Fallback
        return _available_languages

    langs = []
    try:
        # Ensure pytesseract is configured with the correct tessdata path
        config_str = f'--tessdata-dir "{_tessdata_prefix}"' if _tessdata_prefix else ''
        print_fn(f"Attempting to get languages with config: {config_str}")
        langs = pytesseract.get_languages(config=config_str)
        print_fn(f"Languages from pytesseract.get_languages: {langs}")
    except (pytesseract.TesseractError, Exception) as e:
        print_fn(f'Could not fetch Tesseract languages via executable: {e}. Falling back to directory scan.')
        if _tessdata_prefix and os.path.exists(_tessdata_prefix):
            try:
                # If that fails, scan the tessdata directory directly
                langs = [f.split('.')[0] for f in os.path.listdir(_tessdata_prefix) if f.endswith('.traineddata')]
                print_fn(f"Languages from tessdata directory scan: {langs}")
            except Exception as dir_e:
                print_fn(f'Could not scan tessdata directory: {dir_e}')
        else:
            print_fn("tessdata directory not found or accessible for scanning.")

    # Filter out 'osd' as it's not a language for recognition
    if 'osd' in langs:
        langs.remove('osd')

    # Ensure 'eng' is present and move it to the top of the list
    if 'eng' in langs:
        langs.remove('eng')
    langs.insert(0, 'eng')

    # Sort the languages alphabetically, keeping 'eng' at the top
    sorted_langs = [langs[0]] + sorted(langs[1:])
    _available_languages = sorted_langs
    print_fn(f"Final available languages: {_available_languages}")
    return _available_languages


def get_remote_language_packs(force_refresh=False, print_fn=print):
    """Fetches the list of available language packs from the remote repository, with caching."""
    global _remote_languages_cache
    if _remote_languages_cache and not force_refresh:
        print_fn(f"Using cached remote languages: {_remote_languages_cache}")
        return _remote_languages_cache
    try:
        print_fn(f"Fetching remote language list from: {LANGUAGE_PACKS_URL}")
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(LANGUAGE_PACKS_URL, headers=headers, timeout=15)
        response.raise_for_status()
        files = response.json()
        langs = [f['name'].replace('.traineddata', '') for f in files if f['name'].endswith('.traineddata')]
        _remote_languages_cache = sorted(langs)
        print_fn(f"Successfully fetched remote languages: {_remote_languages_cache}")
        return _remote_languages_cache
    except requests.exceptions.RequestException as e:
        print_fn(f"Could not fetch remote language list: {e}")
        return None
    except Exception as e:
        print_fn(f"An error occurred while fetching language list: {e}")
        return None


def install_language_pack(lang_code, progress_callback=None, print_fn=print):
    """Downloads and installs a single language pack."""
    if not _tessdata_prefix or not os.path.exists(_tessdata_prefix):
        print_fn("Error: tessdata directory not found. Cannot install language pack.")
        return False

    if not os.access(_tessdata_prefix, os.W_OK):
        print_fn(f"Error: No write permission for tessdata directory: {_tessdata_prefix}")
        return False

    file_url = f"https://github.com/tesseract-ocr/tessdata_fast/raw/main/{lang_code}.traineddata"
    dest_path = os.path.join(_tessdata_prefix, f"{lang_code}.traineddata")

    try:
        print_fn(f"Downloading {lang_code} from {file_url}...")
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(file_url, stream=True, timeout=30, headers=headers)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        with open(dest_path, 'wb') as f:
            for data in response.iter_content(chunk_size=8192):
                downloaded_size += len(data)
                f.write(data)
                if callable(progress_callback) and total_size > 0:
                    progress = (downloaded_size / total_size) * 100
                    progress_callback(lang_code, progress)

        print_fn(f"Successfully installed language: {lang_code} to {_tessdata_prefix}")
        get_available_languages(force_refresh=True, print_fn=print_fn)
        return True

    except requests.exceptions.RequestException as e:
        print_fn(f"Failed to download {lang_code}: {e}")
        return False
    except Exception as e:
        print_fn(f"An error occurred during {lang_code} installation: {e}")
        return False


def uninstall_language_pack(lang_code, print_fn=print):
    """Uninstalls a single language pack."""
    if lang_code in ('eng', 'osd'):
        print_fn(f"Cannot uninstall mandatory language pack: '{lang_code}'.")
        return False

    if not _tessdata_prefix or not os.path.exists(_tessdata_prefix):
        print_fn("Error: tessdata directory not found.")
        return False

    file_path = os.path.join(_tessdata_prefix, f"{lang_code}.traineddata")
    if not os.path.exists(file_path):
        print_fn(f"Language pack '{lang_code}' is not installed.")
        return True

    try:
        os.remove(file_path)
        print_fn(f"Successfully uninstalled language: {lang_code}")
        get_available_languages(force_refresh=True, print_fn=print_fn)
        return True
    except OSError as e:
        print_fn(f"Error removing language file {file_path}: {e}")
        return False


def get_pytesseract():
    """Returns the imported pytesseract module, or None if not available."""
    return pytesseract


def _install_tesseract_windows(print_fn, set_state_callback, progress_callback):
    """Downloads and extracts a portable Tesseract version for Windows."""
    final_install_dir = get_tesseract_install_dir()

    if not os.access(INSTALL_DIR, os.W_OK):
        msg = f"No write permission in directory: {os.path.abspath(INSTALL_DIR)}"
        print_fn(f"Error: {msg}")
        if callable(set_state_callback):
            set_state_callback((ERROR, msg))
        return None

    zip_path = None
    try:
        if callable(set_state_callback):
            set_state_callback(DOWNLOADING)
        print_fn(f"Downloading Tesseract from {TESSERACT_PORTABLE_URL}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}

        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
            zip_path = tmp_zip.name
            response = requests.get(TESSERACT_PORTABLE_URL, stream=True, timeout=60, headers=headers)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            for data in response.iter_content(chunk_size=8192):
                downloaded_size += len(data)
                tmp_zip.write(data)
                if callable(progress_callback) and total_size > 0:
                    progress = (downloaded_size / total_size) * 100
                    progress_callback(progress)

        if callable(set_state_callback):
            set_state_callback(EXTRACTING)
        print_fn("Download complete. Extracting...")

        with tempfile.TemporaryDirectory() as tmp_extract_dir:
            with zipfile.ZipFile(zip_path) as z:
                z.extractall(tmp_extract_dir)

            tesseract_exe_path_in_tmp = None
            for root, _, files in os.walk(tmp_extract_dir):
                if 'tesseract.exe' in files:
                    tesseract_exe_path_in_tmp = os.path.join(root, 'tesseract.exe')
                    break

            if tesseract_exe_path_in_tmp:
                # The extracted structure is usually Tesseract-OCR-portable/Tesseract-OCR/tesseract.exe
                # We want to move the Tesseract-OCR folder to final_install_dir
                tesseract_root_in_zip = os.path.dirname(tesseract_exe_path_in_tmp)
                while os.path.basename(tesseract_root_in_zip).lower() != 'tesseract-ocr' and tesseract_root_in_zip != tmp_extract_dir:
                    tesseract_root_in_zip = os.path.dirname(tesseract_root_in_zip)
                
                if os.path.exists(final_install_dir):
                    rmtree(final_install_dir)
                
                # Move the actual Tesseract-OCR directory to the desired install location
                shutil_move(tesseract_root_in_zip, final_install_dir)

                tesseract_exe_path = os.path.join(final_install_dir, 'tesseract.exe')
                # Adjust path if the exe is in a subdirectory like Tesseract-OCR/bin/tesseract.exe
                if not os.path.exists(tesseract_exe_path):
                    for root, _, files in os.walk(final_install_dir):
                        if 'tesseract.exe' in files:
                            tesseract_exe_path = os.path.join(root, 'tesseract.exe')
                            break

                print_fn(f"Tesseract executable found at: {tesseract_exe_path}")
                return tesseract_exe_path
            else:
                raise FileNotFoundError("tesseract.exe not found in extracted folder.")

    except requests.exceptions.RequestException as e:
        error_msg = f"Download failed. A firewall may be blocking the connection, or the server may be down. Try downloading the file manually.\nDetails: {e}"
        print_fn(error_msg)
        if callable(set_state_callback):
            set_state_callback((ERROR, error_msg))
        return None
    except zipfile.BadZipFile:
        error_msg = "Failed to extract Tesseract. The downloaded file may be corrupt."
        print_fn(error_msg)
        if callable(set_state_callback):
            set_state_callback((ERROR, error_msg))
        return None
    except Exception as e:
        error_msg = f"An unexpected error occurred during Tesseract installation: {e}"
        print_fn(error_msg)
        if callable(set_state_callback):
            set_state_callback((ERROR, error_msg))
        return None
    finally:
        if zip_path and os.path.exists(zip_path):
            os.unlink(zip_path)


def manual_install_tesseract(set_state_callback=None, progress_callback=None, print_fn=print):
    """Manually triggers the Tesseract download and installation process in a background thread."""

    def install_worker():
        if 'windows' not in (platform_system() or '').lower():
            msg = "Automatic installation is only supported on Windows."
            print_fn(msg)
            if callable(set_state_callback):
                set_state_callback((ERROR, msg))
            return

        path = _install_tesseract_windows(print_fn, set_state_callback, progress_callback)

        if path:
            _configure_tesseract(path, set_state_callback, print_fn)
        else:
            if callable(set_state_callback):
                set_state_callback((ERROR, "Tesseract installation failed. See logs for details."))

    Thread(target=install_worker, daemon=True).start()


def _find_tessdata_dir(tesseract_exe_path, print_fn):
    """
    Attempts to find the tessdata directory relative to the Tesseract executable.
    """
    tess_dir = os.path.dirname(tesseract_exe_path)
    possible_tessdata_paths = [
        os.path.join(tess_dir, 'tessdata'), # Common for direct installs
        os.path.join(os.path.dirname(tess_dir), 'tessdata'), # For portable installs like Tesseract-OCR/bin/tessdata
        os.path.join(os.path.dirname(tess_dir), 'share', 'tessdata'), # Linux/macOS common
        os.path.join(tess_dir, '..\share\tessdata'), # Windows portable structure
        os.path.join(get_tesseract_install_dir(), 'tessdata') # Our portable install location
    ]

    for path in possible_tessdata_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path) and os.path.isdir(abs_path):
            print_fn(f"Found tessdata directory at: {abs_path}")
            return abs_path
    print_fn(f"Could not find tessdata directory for Tesseract at {tesseract_exe_path}")
    return None


def _configure_tesseract(tesseract_exe_path, set_state_callback, print_fn):
    """Sets up pytesseract and finds the tessdata directory."""
    global _tesseract_path, _tesseract_installed, _tessdata_prefix
    print_fn(f"Configuring Tesseract with executable: {tesseract_exe_path}")
    try:
        pytesseract.pytesseract.tesseract_cmd = tesseract_exe_path
        _tesseract_path = tesseract_exe_path
        _tesseract_installed = None # Reset cache

        # Verify Tesseract is runnable
        if not is_tesseract_installed():
            msg = "Found Tesseract executable, but it failed to run. It may be corrupt or missing dependencies."
            print_fn(f"Warning: {msg}")
            if callable(set_state_callback):
                set_state_callback((ERROR, msg))
            return

        # Find tessdata directory
        tessdata_dir = _find_tessdata_dir(tesseract_exe_path, print_fn)

        if tessdata_dir:
            _tessdata_prefix = tessdata_dir
            os.environ['TESSDATA_PREFIX'] = tessdata_dir
            print_fn(f'Tessdata directory set to: {tessdata_dir}')
            print_fn(f'Pytesseract configured with: {tesseract_exe_path}')
            if callable(set_state_callback):
                set_state_callback(ACTIVE)
        else:
            msg = "Tesseract found, but its 'tessdata' directory is missing or could not be located."
            print_fn(msg)
            if callable(set_state_callback):
                set_state_callback((ERROR, msg))

    except Exception as e:
        msg = f"Error configuring pytesseract: {e}"
        print_fn(msg)
        if callable(set_state_callback):
            set_state_callback((ERROR, msg))


def init_ocr_async_service(set_state_callback=None, print_fn=print):
    """
    Non-blocking OCR (Tesseract) setup. Finds, configures, or prompts for installation.
    """

    def ocr_worker():
        global _tesseract_path, _tessdata_prefix
        if callable(set_state_callback):
            set_state_callback(INITIALIZING)
        print_fn("Initializing OCR service...")

        # 1. Check if pytesseract module is even available
        if pytesseract is None:
            msg = "Pytesseract Python module not found. Please install it (e.g., pip install pytesseract)."
            print_fn(f"Error: {msg}")
            if callable(set_state_callback):
                set_state_callback((ERROR, msg))
            return

        # 2. Try to find Tesseract executable
        found_path = None

        # Check if already configured from a previous run/session
        if _tesseract_path and os.path.exists(_tesseract_path):
            found_path = _tesseract_path
            print_fn(f"Using previously configured Tesseract path: {found_path}")
        
        # Check system PATH
        if not found_path:
            path_from_which = shutil_which('tesseract')
            if path_from_which:
                found_path = path_from_which
                print_fn(f"Found Tesseract in system PATH: {found_path}")

        # Check our portable install location
        if not found_path:
            portable_path = os.path.join(get_tesseract_install_dir(), 'tesseract.exe')
            if os.path.exists(portable_path):
                found_path = portable_path
                print_fn(f"Found Tesseract in portable install directory: {found_path}")
            else:
                # Check for common subdirectories within the portable install
                portable_bin_path = os.path.join(get_tesseract_install_dir(), 'bin', 'tesseract.exe')
                if os.path.exists(portable_bin_path):
                    found_path = portable_bin_path
                    print_fn(f"Found Tesseract in portable install subdirectory: {found_path}")

        # Check common default install locations (Windows specific)
        if not found_path and 'windows' in (platform_system() or '').lower():
            search_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            ]
            for candidate_path in search_paths:
                if os.path.exists(candidate_path):
                    found_path = candidate_path
                    print_fn(f"Found Tesseract in common Windows path: {found_path}")
                    break
        
        # Check common default install locations (macOS specific)
        if not found_path and 'darwin' in (platform_system() or '').lower():
            search_paths = [
                '/opt/homebrew/bin/tesseract', # Homebrew on Apple Silicon
                '/usr/local/bin/tesseract' # Homebrew on Intel Macs
            ]
            for candidate_path in search_paths:
                if os.path.exists(candidate_path):
                    found_path = candidate_path
                    print_fn(f"Found Tesseract in common macOS path: {found_path}")
                    break

        if found_path:
            _configure_tesseract(found_path, set_state_callback, print_fn)
        else:
            msg = "Tesseract OCR executable not found. Please install it manually or use the automatic installer."
            print_fn(msg)
            if callable(set_state_callback):
                set_state_callback((DISABLED, msg))

    Thread(target=ocr_worker, daemon=True).start()


def _preprocess_for_ocr(pil_img, invert=False, binarize_threshold=160):
    """
    Pre-processes a PIL image for OCR by converting it to grayscale,
    inverting colors if specified, and applying filters to improve text recognition.
    """
    if ImageOps is None or ImageFilter is None:
        return pil_img

    img = pil_img.convert('L')
    if invert:
        img = ImageOps.invert(img)

    img = ImageOps.autocontrast(img)
    try:
        # Use the more modern and higher-quality LANCZOS filter if available
        resample_filter = getattr(Image, 'LANCZOS', getattr(Image, 'ANTIALIAS', Image.BICUBIC))
        img = img.resize((img.width * 2, img.height * 2), resample_filter)
    except (ValueError, IOError) as e:
        print(f"Could not resize image for OCR: {e}")
    
    img = img.filter(ImageFilter.MedianFilter(size=3))
    return img.point(lambda x: 0 if x < binarize_threshold else 255, mode='1')


def _ocr_image(pil_img, lang='eng', psm='6', invert=False, binarize_threshold=160, custom_config=''):
    """
    Performs OCR on a PIL image using Tesseract, returning a dictionary of recognized text data.
    """
    pytesseract = get_pytesseract()
    if not is_tesseract_installed() or not pytesseract:
        return {'error': 'Tesseract library not available or not installed.'}
    try:
        processed_img = _preprocess_for_ocr(pil_img, invert=invert, binarize_threshold=binarize_threshold)
        
        # Tesseract expects languages to be joined by '+'
        lang_str = '+'.join(lang) if isinstance(lang, list) else lang

        # Combine base config with custom user parameters
        config_str = f'--oem 3 --psm {psm}'
        if _tessdata_prefix:
            config_str += f' --tessdata-dir "{_tessdata_prefix}"'
        if custom_config:
            config_str += f' {custom_config}'
        
        print(f"Running Tesseract with lang='{lang_str}', config='{config_str}'")

        return pytesseract.image_to_data(
            processed_img,
            lang=lang_str,
            config=config_str,
            output_type=pytesseract.Output.DICT
        )
    except pytesseract.TesseractError as e:
        # Provide a more informative error message
        error_message = str(e)
        if "Failed loading language" in error_message:
            return {'error': f"OCR Error: Language pack for '{lang_str}' not found. Please install it via the Language Manager."}
        return {'error': f'Tesseract OCR failed: {e}'}
    except Exception as e:
        return {'error': f'An unexpected error occurred in OCR processing: {e}'}


def recognize_text_from_canvas(canvas, bbox, lang, psm, invert, binarize_threshold, custom_config=''):
    """
    Performs OCR on a region of the canvas content by capturing it directly.
    This avoids the need for temporary files and the Ghostscript dependency.
    Returns a dictionary of OCR data or an error message.
    """
    if not is_tesseract_installed():
        return {'error': "Tesseract OCR not found. Please install it and ensure it is in your system's PATH."}
    if not Image or not ImageGrab:
        return {'error': "Pillow library not found or incomplete. OCR is disabled."}
    if not bbox or not all(isinstance(v, (int, float)) for v in bbox):
        return {'text': []} # Return empty text if no valid bounding box is provided

    x1, y1, x2, y2 = bbox

    # Calculate the absolute coordinates for ImageGrab
    try:
        canvas_x = canvas.winfo_rootx()
        canvas_y = canvas.winfo_rooty()
        grab_x1 = canvas_x + x1
        grab_y1 = canvas_y + y1
        grab_x2 = canvas_x + x2
        grab_y2 = canvas_y + y2

        # Ensure the grab box has a positive area
        if grab_x1 >= grab_x2 or grab_y1 >= grab_y2:
            return {'text': []}

        # Use ImageGrab to capture the screen area corresponding to the canvas bbox
        img = ImageGrab.grab(bbox=(grab_x1, grab_y1, grab_x2, grab_y2), all_screens=True)
        
        return _ocr_image(img, lang=lang, psm=psm, invert=invert, binarize_threshold=binarize_threshold, custom_config=custom_config)

    except (tk.TclError, ValueError) as e:
        return {'error': f"Error capturing canvas for OCR: {e}"}
    except Exception as e:
        # This will catch potential errors from ImageGrab on different OSes or setups
        return {'error': f"An unexpected error occurred during canvas capture: {e}"}
