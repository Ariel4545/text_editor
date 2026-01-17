import os
import json
from typing import Dict, Any

class ConfigService:
    SETTINGS_FILE = 'EgonTE_settings.json'

    def __init__(self):
        self.data: Dict[str, Any] = self.make_default_data()

    def make_default_data(self) -> Dict[str, Any]:
        return {
            'night_mode': False, 'status_bar': True, 'file_bar': True, 'cursor': 'xterm',
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

    def load_settings(self) -> bool:
        """
        Loads settings from file. Returns True if a new default file was created or fallback occurred, 
        False if loaded successfully.
        """
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # Merge loaded data with defaults to ensure all keys exist
                    self.data.update(loaded_data)
                return False
            except Exception as e:
                print(f"Error loading settings: {e}")
                # Fallback to default
                self.data = self.make_default_data()
                self.save_settings()
                return True
        else:
            self.data = self.make_default_data()
            self.save_settings()
            return True

    def save_settings(self):
        try:
            with open(self.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f)
        except Exception:
            try:
                tmp = self.SETTINGS_FILE + '.tmp'
                with open(tmp, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f)
                os.replace(tmp, self.SETTINGS_FILE)
            except Exception as e:
                print(f"Error saving settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        self.data[key] = value

    def update(self, new_data: Dict[str, Any]):
        self.data.update(new_data)
