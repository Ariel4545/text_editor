from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Dict, Optional, Tuple
from tkinter import colorchooser, messagebox, TclError, ttk

try:
	from dependencies.universal_functions import get_time
except Exception:
	from datetime import datetime as datetime_fallback
	def get_time() -> str:
		return datetime_fallback.now().strftime('%Y-%m-%d %H:%M:%S')


@dataclass
class ThemeService:
	'''
	Theme management service for applying and customizing colors across the UI.

	Responsibilities:
	  - Manage an application-wide color palette (overall/frame, background, text, button).
	  - Apply palette to known widget groups (main window, editor, menus, popups).
	  - Support preview (snapshot/rollback) during customization interactions.
	  - Save/load named presets via the app's settings storage.
	'''
	app: Any  # expects EgonTE Window-like object
	preview_backup: Dict[str, Any] = field(default_factory=dict)
	last_applied: Dict[str, str] = field(default_factory=dict)  # keys: main, second, text, button

	# ------------- Utilities -------------

	def append_record(self, message_text: str) -> None:
		'''
		Append a formatted message to the app's record list (if available).
		'''
		try:
			self.app.record_list.append(message_text)
		except Exception:
			pass

	def ask_color(self, dialog_title: str, default_color: Optional[str] = None) -> str | None:
		'''
		Show a color chooser and return the selected color (hex string) or the default on cancel.
		'''
		try:
			chosen_color = colorchooser.askcolor(color=default_color, title=dialog_title)[1]
			return chosen_color or default_color
		except Exception:
			return default_color

	def show_error_message(self, message_text: str) -> None:
		'''
		Show an error dialog with the app's title prefix (if available).
		'''
		try:
			messagebox.showerror(getattr(self.app, 'title_struct', '') + 'error', message_text)
		except Exception:
			pass

	def night_mode_guard(self) -> bool:
		'''
		If night mode is on, confirm that the user still wants to proceed with color changes.
		'''
		try:
			if self.app.night_mode.get():
				return bool(messagebox.askyesno('EgonTE', 'Night mode is on, still want to proceed?'))
		except Exception:
			pass
		return True

	def set_widget_color(self, target_widget, option_key: str, option_value: str) -> None:
		'''
		Safely set a color option on a Tk widget (e.g., 'bg', 'fg').
		'''
		try:
			target_widget[option_key] = option_value
		except TclError:
			pass
		except Exception:
			pass

	# ------------- Color math -------------

	@staticmethod
	def parse_hex_color(hex_color: str) -> Tuple[int, int, int]:
		'''
		Parse a hex color string into an RGB tuple.
		'''
		if not hex_color:
			return (0, 0, 0)
		hex_digits = hex_color.lstrip('#')
		if len(hex_digits) == 3:
			hex_digits = ''.join([hex_digit * 2 for hex_digit in hex_digits])
		try:
			red_value = int(hex_digits[0:2], 16)
			green_value = int(hex_digits[2:4], 16)
			blue_value = int(hex_digits[4:6], 16)
			return (red_value, green_value, blue_value)
		except Exception:
			return (0, 0, 0)

	@classmethod
	def compute_relative_luminance(cls, hex_color: str) -> float:
		'''
		Compute the relative luminance of a color using the WCAG formula.
		'''
		red_value, green_value, blue_value = cls.parse_hex_color(hex_color)

		def channel_transform(channel_0_255: int) -> float:
			normalized = channel_0_255 / 255.0
			return normalized / 12.92 if normalized <= 0.03928 else ((normalized + 0.055) / 1.055) ** 2.4

		red_l = channel_transform(red_value)
		green_l = channel_transform(green_value)
		blue_l = channel_transform(blue_value)
		return 0.2126 * red_l + 0.7152 * green_l + 0.0722 * blue_l

	@classmethod
	def compute_contrast_ratio(cls, foreground_hex: str, background_hex: str) -> float:
		'''
		Compute the contrast ratio between two colors (foreground vs background).
		'''
		luminance_foreground = cls.compute_relative_luminance(foreground_hex)
		luminance_background = cls.compute_relative_luminance(background_hex)
		lighter_value, darker_value = (luminance_foreground, luminance_background) if luminance_foreground >= luminance_background else (luminance_background, luminance_foreground)
		return (lighter_value + 0.05) / (darker_value + 0.05)

	@classmethod
	def ideal_text_on(cls, background_hex: str) -> str:
		'''
		Choose black or white text for best contrast on the provided background color.
		'''
		black_contrast = cls.compute_contrast_ratio('#000000', background_hex)
		white_contrast = cls.compute_contrast_ratio('#FFFFFF', background_hex)
		return '#000000' if black_contrast >= white_contrast else '#FFFFFF'

	# ------------- Snapshots (Preview) -------------

	def start_preview(self) -> None:
		'''
		Snapshot current theme-related attributes to allow canceling changes.
		'''
		try:
			self.preview_backup = {
				'dynamic_overall': getattr(self.app, 'dynamic_overall', None),
				'dynamic_text': getattr(self.app, 'dynamic_text', None),
				'dynamic_bg': getattr(self.app, 'dynamic_bg', None),
				'dynamic_button': getattr(self.app, 'dynamic_button', None),
			}
		except Exception:
			self.preview_backup = {}

	def cancel_preview(self) -> None:
		'''
		Roll back to snapshot (if taken) and re-apply visuals.
		'''
		if not self.preview_backup:
			return
		try:
			for key_name, value in self.preview_backup.items():
				if value is not None:
					setattr(self.app, key_name, value)
			self.apply_current_theme()
		except Exception:
			pass
		finally:
			self.preview_backup.clear()

	def commit_preview(self) -> None:
		'''
		Accept current visuals and clear snapshot.
		'''
		self.preview_backup.clear()

	# ------------- Central apply -------------

	def set_palette(self, main_color: str, secondary_color: str, text_color: Optional[str] = None, button_color: Optional[str] = None) -> None:
		'''
		Set the dynamic colors on the app (no dialogs) and apply everywhere.
		If text_color is None, auto-pick text color for readability. If button_color is None, derive from main/second.
		'''
		if not main_color or not secondary_color:
			return
		if text_color is None:
			text_color = self.ideal_text_on(secondary_color)
		if button_color is None:
			button_color = main_color
			try:
				if self.compute_contrast_ratio(text_color, main_color) < 3.5:
					button_color = secondary_color
			except Exception:
				pass

		try:
			self.app.dynamic_overall = main_color
			self.app.dynamic_text = text_color
			self.app.dynamic_bg = secondary_color
			self.app.dynamic_button = button_color
		except Exception:
			pass

		self.last_applied = {'main': main_color, 'second': secondary_color, 'text': text_color, 'button': button_color}
		self.apply_current_theme()

	def apply_current_theme(self) -> None:
		'''
		Push current dynamic_* colors to all relevant widgets (mirrors what night() covers).
		'''
		main_color = getattr(self.app, 'dynamic_overall', 'SystemButtonFace')
		text_color = getattr(self.app, 'dynamic_text', 'black')
		secondary_color = getattr(self.app, 'dynamic_bg', 'SystemButtonFace')
		button_color = getattr(self.app, 'dynamic_button', 'SystemButtonFace')

		# Root + status areas
		try:
			self.app.config(bg=main_color)
			self.app.status_frame.configure(bg=main_color)
			self.app.status_bar.config(bg=main_color, fg=text_color)
			self.app.file_bar.config(bg=main_color, fg=text_color)
		except Exception:
			pass

		# Main editor and toolbar
		try:
			self.app.EgonTE.config(bg=secondary_color, fg=text_color, insertbackground=text_color)
			self.app.toolbar_frame.config(bg=main_color)
			for toolbar_button_widget in getattr(self.app, 'toolbar_components', []):
				try:
					toolbar_button_widget.config(background=button_color, foreground=text_color)
				except Exception:
					pass
		except Exception:
			pass

		# Menus (bg/fg when supported)
		try:
			for menu_widget in getattr(self.app, 'menus_components', []):
				try:
					menu_widget.config(background=secondary_color, foreground=text_color)
				except Exception:
					pass
		except Exception:
			pass

		# Info/patch windows
		try:
			if getattr(self.app, 'info_page_active', False):
				self.app.info_page_text.config(bg=secondary_color, fg=text_color)
				self.app.info_page_title.config(bg=secondary_color, fg=text_color)
		except Exception:
			pass

		# Virtual keyboard
		try:
			if getattr(self.app, 'vk_active', False):
				for vk_button_widget in getattr(self.app, 'all_vk_buttons', []):
					try:
						vk_button_widget.config(bg=secondary_color, fg=text_color)
					except Exception:
						pass
		except Exception:
			pass

		# Search popup
		try:
			if getattr(self.app, 'search_active', False):
				for search_widget in getattr(self.app, 'search_widgets', []):
					try:
						search_widget.configure(bg=secondary_color, fg=text_color)
					except Exception:
						pass
				try:
					self.app.search_widgets[-1].configure(bg=button_color, fg=text_color)
				except Exception:
					pass
				try:
					self.app.search_bg.configure(bg=main_color)
				except Exception:
					pass
		except Exception:
			pass

		# Record logs popup
		try:
			if getattr(self.app, 'record_active', False):
				self.app.record_night.configure(bg=secondary_color, fg=text_color)
		except Exception:
			pass

		# Options popup
		try:
			if getattr(self.app, 'op_active', False):
				for options_tab in getattr(self.app, 'opt_frames', []):
					try:
						options_tab.configure(bg=main_color)
					except Exception:
						pass
				for title_label in getattr(self.app, 'opt_labels', []):
					try:
						title_label.configure(bg=main_color, fg=text_color)
					except Exception:
						pass
				for option_widget in getattr(self.app, 'opt_commands', []):
					try:
						option_widget.configure(bg=secondary_color, fg=text_color)
					except Exception:
						pass
				for dynamic_button_widget in tuple(getattr(self.app, 'dynamic_buttons', {}).values()):
					try:
						dynamic_button_widget.configure(bg=button_color, fg=text_color)
					except Exception:
						pass
				try:
					self.app.night_frame.configure(bg=secondary_color)
				except Exception:
					pass
				try:
					self.app.change_button_color(self.app.last_cursor[0], self.app.last_cursor[1])
					self.app.change_button_color(self.app.last_style[0], self.app.last_style[1])
					self.app.change_button_color(self.app.last_r[0], self.app.last_r[1])
				except Exception:
					pass
		except Exception:
			pass

		# Handwriting / images popups
		try:
			if getattr(self.app, 'hw_active', False):
				for background_widget in getattr(self.app, 'hw_bg', []):
					try:
						background_widget.configure(bg=main_color)
					except Exception:
						pass
				for tool_button_widget in getattr(self.app, 'hw_buttons', []):
					try:
						tool_button_widget.configure(bg=button_color, fg=text_color)
					except Exception:
						pass
				for label_widget in getattr(self.app, 'hw_labels', []):
					try:
						label_widget.configure(bg=main_color, fg=text_color)
					except Exception:
						pass
				for separator_widget in getattr(self.app, 'hw_seperator', []):
					try:
						separator_widget.configure(bg=secondary_color, fg=text_color)
					except Exception:
						pass
				if getattr(self.app, 'night_mode', None) and self.app.night_mode.get():
					try:
						self.app.draw_canvas.configure(bg=secondary_color)
					except Exception:
						pass
		except Exception:
			pass

		try:
			if getattr(self.app, 'ins_images_open', False):
				for command_widget in getattr(self.app, 'in_im_commands', []):
					try:
						command_widget.configure(bg=secondary_color, fg=text_color)
					except Exception:
						pass
				for background_widget in getattr(self.app, 'in_im_bgs', []):
					try:
						background_widget.configure(bg=main_color)
					except Exception:
						pass
		except Exception:
			pass

		# ttk combobox for font family/sizes
		try:
			self.app.style_combobox.configure('TCombobox', background=secondary_color, foreground=text_color)
		except Exception:
			pass

	# ------------- Single-target helpers (existing behavior parity) -------------

	def configure_single_target(self, target_widget, option_key: str, dialog_title: Optional[str] = None) -> None:
		'''
		Open a color chooser and apply the result to a single widget option (e.g., 'bg' or 'fg').
		'''
		chosen_color = self.ask_color(dialog_title or f'{option_key} color', default_color=None)
		if not chosen_color:
			return
		self.set_widget_color(target_widget, option_key, chosen_color)
		self.append_record(f'> [{get_time()}] - {option_key} changed to {chosen_color}')

	def configure_group_target(self, target_widgets: Iterable, option_key: str, dialog_title: Optional[str] = None) -> None:
		'''
		Open a color chooser and apply the result to a collection of widgets for the given option.
		'''
		chosen_color = self.ask_color(dialog_title or f'{option_key} color', default_color=None)
		if not chosen_color:
			return
		for widget_item in (target_widgets or []):
			self.set_widget_color(widget_item, option_key, chosen_color)
		self.append_record(f'> [{get_time()}] - {option_key} changed to {chosen_color}')

	def configure_singular_component(self, component_key: str) -> None:
		'''
		Configure a 'singular' UI component (as defined by app.singular_colors_d mapping).
		'''
		try:
			singular_map = getattr(self.app, 'singular_colors_d', {}) or {}
			target_object, option_spec = singular_map.get(component_key, [None, None])
		except Exception:
			target_object, option_spec = None, None

		if not target_object or not option_spec:
			return

		option_keys = option_spec.split('-') if isinstance(option_spec, str) and '-' in option_spec else [option_spec]

		for option_key in option_keys:
			if not option_key:
				continue
			if isinstance(target_object, list):
				self.configure_group_target(target_object, option_key, dialog_title=f'{component_key} {option_key} color')
			else:
				self.configure_single_target(target_object, option_key, dialog_title=f'{component_key} {option_key} color')

	# ------------- App-level palettes & components -------------

	def configure_app_palette(self, preset_colors: Optional[Dict[str, str]] = None) -> None:
		'''
		Configure the entire app palette either from a preset dict or via color dialogs.
		'''
		if preset_colors:
			self.set_palette(
				main_color=preset_colors.get('main'),
				secondary_color=preset_colors.get('second'),
				text_color=preset_colors.get('text'),
				button_color=preset_colors.get('button'),
			)
			return

		main_frames_color = self.ask_color('Frames color', default_color=self.last_applied.get('main'))
		editor_background_color = self.ask_color('Text box color', default_color=self.last_applied.get('second'))
		body_text_color = self.ask_color('Text color', default_color=self.last_applied.get('text') or self.ideal_text_on(editor_background_color or '#ffffff'))
		if not (main_frames_color and editor_background_color and body_text_color):
			return

		derived_button_color = self.last_applied.get('button')
		if not derived_button_color:
			derived_button_color = main_frames_color
			if self.compute_contrast_ratio(body_text_color, derived_button_color) < 3.5:
				derived_button_color = editor_background_color

		self.set_palette(main_frames_color, editor_background_color, body_text_color, derived_button_color)
		self.append_record(
			f"> [{get_time()}] - App's color changed to {main_frames_color}\n  "
			f"App's secondary color changed to {editor_background_color}\n  "
			f"App's text color changed to {body_text_color}"
		)

	def configure_info_page(self) -> None:
		'''
		Configure the info/patch window colors (must be open).
		'''
		try:
			if not getattr(self.app, 'info_page_active', False):
				self.show_error_message('Information window is not opened')
				return
			background_color = self.ask_color('Backgrounds color', default_color=self.last_applied.get('second'))
			text_color = self.ask_color('Text color', default_color=self.last_applied.get('text'))
			if not (background_color and text_color):
				return
			self.app.info_page_text.config(bg=background_color, fg=text_color)
			self.app.info_page_title.config(bg=background_color, fg=text_color)
		except Exception:
			pass

	def configure_virtual_keyboard(self) -> None:
		'''
		Configure colors for the virtual keyboard window (must be open).
		'''
		try:
			if not getattr(self.app, 'vk_active', False):
				self.show_error_message('Virtual keyboard window is not opened')
				return
			background_color = self.ask_color('Backgrounds color', default_color=self.last_applied.get('second'))
			text_color = self.ask_color('Text color', default_color=self.last_applied.get('text'))
			if not (background_color and text_color):
				return
			for vk_button_widget in getattr(self.app, 'all_vk_buttons', []):
				try:
					vk_button_widget.config(bg=background_color, fg=text_color)
				except Exception:
					pass
		except Exception:
			pass

	def configure_advance_options(self) -> None:
		'''
		Configure colors for the 'Advance Options' window sections (must be open).
		'''
		try:
			if not getattr(self.app, 'op_active', False):
				self.show_error_message('Advance options window is not opened')
				return
			frames_color = self.ask_color('Frames color', default_color=self.last_applied.get('main'))
			buttons_background_color = self.ask_color('Buttons background color', default_color=self.last_applied.get('button'))
			buttons_text_color = self.ask_color('Buttons text color', default_color=self.last_applied.get('text'))
			titles_text_color = self.ask_color('Titles text color', default_color=self.last_applied.get('text'))
			titles_background_color = self.ask_color('Titles background color', default_color=self.last_applied.get('main'))
			if not (frames_color and buttons_background_color and buttons_text_color and titles_text_color and titles_background_color):
				return

			try:
				self.app.night_frame.configure(bg=buttons_background_color)
			except Exception:
				pass

			full_button_widgets = []
			try:
				full_button_widgets = list(getattr(self.app, 'opt_commands', ())) + list(getattr(self.app, 'dynamic_buttons', {}).values())
			except Exception:
				pass

			for frame_widget in getattr(self.app, 'opt_frames', []):
				try:
					frame_widget.configure(bg=frames_color)
				except Exception:
					pass
			for button_widget in full_button_widgets:
				try:
					button_widget.configure(bg=buttons_background_color, fg=buttons_text_color)
				except Exception:
					pass
			for title_widget in getattr(self.app, 'opt_labels', []):
				try:
					title_widget.configure(fg=titles_text_color, bg=titles_background_color)
				except Exception:
					pass
		except Exception:
			pass

	def apply_handwriting_style(self, root_window: Any) -> Dict[str, Any]:
		"""Configures the ttk styles for the handwriting popup window."""
		COLOR_BG = '#f0f0f0'
		COLOR_FG = '#333333'
		COLOR_ACCENT = '#0078d4'
		COLOR_SECONDARY_BG = '#e0e0e0'
		COLOR_BORDER = '#cccccc'
		COLOR_SELECTED_BG = COLOR_ACCENT
		CANVAS_BG = '#ffffff'
		GRID_COLOR = '#e0e0e0'
		SELECTION_RECT_OUTLINE_COLOR = '#005a9e'

		style = ttk.Style(root_window)
		style.theme_use('clam')
		root_window.configure(bg=COLOR_BG)

		style.configure('.', background=COLOR_BG, foreground=COLOR_FG, bordercolor=COLOR_BORDER,
						focuscolor=COLOR_ACCENT, font=('Segoe UI', 8))
		style.configure('TFrame', background=COLOR_BG)
		style.configure('TLabel', background=COLOR_BG, foreground=COLOR_FG, padding=3)
		style.configure('TNotebook', background=COLOR_BG, borderwidth=0)
		style.configure('Tool.TNotebook', padding=0)
		style.configure('Tool.TNotebook.Tab', padding=[5, 2], font=('Segoe UI', 8, 'bold'))
		style.map('Tool.TNotebook.Tab', padding=[('selected', [8, 4])])

		style.configure('TButton', background=COLOR_SECONDARY_BG, foreground=COLOR_FG, padding=(8, 4), relief='flat',
						borderwidth=0, focusthickness=0, font=('Segoe UI', 8))
		style.map('TButton', background=[('active', COLOR_ACCENT), ('pressed', COLOR_ACCENT)])
		style.configure('Selected.TButton', background=COLOR_SELECTED_BG, foreground='white')
		style.configure('Toggle.TButton', padding=(8, 4), relief='flat', borderwidth=0, focusthickness=0)
		style.map('Toggle.TButton', background=[('selected', COLOR_SELECTED_BG), ('active', COLOR_ACCENT)])

		style.configure('TLabelframe', background=COLOR_BG, bordercolor=COLOR_BORDER, padding=5)
		style.configure('TLabelframe.Label', background=COLOR_BG, foreground=COLOR_FG, font=('Segoe UI', 9, 'bold'))
		style.configure('TCombobox', fieldbackground=CANVAS_BG, background=COLOR_SECONDARY_BG,
						arrowcolor=COLOR_FG, bordercolor=COLOR_BORDER, padding=4)
		style.map('TCombobox', fieldbackground=[('readonly', CANVAS_BG)])
		style.configure('Vertical.TScrollbar', background=COLOR_BG, troughcolor=COLOR_SECONDARY_BG,
						bordercolor=COLOR_BG, arrowcolor=COLOR_FG)
		style.configure('Horizontal.TScrollbar', background=COLOR_BG, troughcolor=COLOR_SECONDARY_BG,
						bordercolor=COLOR_BG, arrowcolor=COLOR_FG)
		style.configure('TCheckbutton', background=COLOR_BG, foreground=COLOR_FG, font=('Segoe UI', 8))
		style.map('TCheckbutton', indicatorbackground=[('selected', COLOR_ACCENT)], background=[('active', COLOR_BG)])

		return {
			'CANVAS_BG': CANVAS_BG, 'GRID_COLOR': GRID_COLOR,
			'SELECTION_RECT_OUTLINE_COLOR': SELECTION_RECT_OUTLINE_COLOR,
			'COLOR_BG': COLOR_BG, 'COLOR_FG': COLOR_FG,
			'OCR_STATUS_COLORS': {
				'ACTIVE': 'green',
				'DISABLED': '#a0a0a0',
				'INITIALIZING': 'orange',
				'DOWNLOADING': 'blue',
				'EXTRACTING': 'purple',
				'ERROR': 'red'
			}
		}

	# ------------- Presets & persistence -------------

	def export_current_theme(self) -> Dict[str, str]:
		'''
		Export the current dynamic colors as a small preset dictionary.
		'''
		return {
			'main': getattr(self.app, 'dynamic_overall', 'SystemButtonFace'),
			'second': getattr(self.app, 'dynamic_bg', 'SystemButtonFace'),
			'text': getattr(self.app, 'dynamic_text', 'black'),
			'button': getattr(self.app, 'dynamic_button', 'SystemButtonFace'),
		}

	def save_preset(self, preset_name: str) -> None:
		'''
		Save the current theme as a named preset in app.data['theme_presets'] and persist settings.
		'''
		if not preset_name:
			return
		preset_data = self.export_current_theme()
		try:
			if not hasattr(self.app, 'data') or not isinstance(self.app.data, dict):
				self.app.data = {}
			theme_presets = self.app.data.get('theme_presets', {})
			if not isinstance(theme_presets, dict):
				theme_presets = {}
			theme_presets[preset_name] = preset_data
			self.app.data['theme_presets'] = theme_presets
			if hasattr(self.app, 'saved_settings'):
				self.app.saved_settings(special_mode='save')
			self.append_record(f"> [{get_time()}] - Theme preset '{preset_name}' saved")
		except Exception:
			pass

	def load_preset(self, preset_name: str) -> bool:
		'''
		Load a named preset from app.data['theme_presets'] and apply it.
		'''
		try:
			theme_presets = (getattr(self.app, 'data', {}) or {}).get('theme_presets', {}) or {}
			chosen_preset = theme_presets.get(preset_name)
			if not chosen_preset:
				self.show_error_message(f"Preset '{preset_name}' not found")
				return False
			self.configure_app_palette(preset_colors=chosen_preset)
			self.append_record(f"> [{get_time()}] - Theme preset '{preset_name}' applied")
			return True
		except Exception:
			return False

	def delete_preset(self, preset_name: str) -> bool:
		'''
		Delete a named theme preset from the app settings and persist the change.
		'''
		try:
			theme_presets = (getattr(self.app, 'data', {}) or {}).get('theme_presets', {}) or {}
			if preset_name in theme_presets:
				del theme_presets[preset_name]
				self.app.data['theme_presets'] = theme_presets
				if hasattr(self.app, 'saved_settings'):
					self.app.saved_settings(special_mode='save')
				self.append_record(f"> [{get_time()}] - Theme preset '{preset_name}' deleted")
				return True
		except Exception:
			pass
		return False

	def list_presets(self) -> Tuple[str, ...]:
		'''
		Return all preset names sorted alphabetically.
		'''
		try:
			theme_presets = (getattr(self.app, 'data', {}) or {}).get('theme_presets', {}) or {}
			return tuple(sorted(theme_presets.keys()))
		except Exception:
			return tuple()

	# ------------- Public entry point (Window.custom_ui_colors) -------------
	def custom_ui_colors(self, components: str, *, preview: bool = False,
						 colors: Optional[Dict[str, str]] = None) -> None:
		'''
		Central entry for theme customization (formerly on Window).

		Parameters:
			components: identifiers like 'text', 'background', 'app', 'info_page', 'v_keyboard', 'advance_options'
			preview: when True, take a snapshot first (call cancel_preview()/commit_preview() externally)
			colors: programmatic palette for 'app' components (keys: main, second, text, button)
		'''
		if not self.night_mode_guard():
			return

		# Normalize known aliases coming from menu items
		# - 'info page' -> 'info_page'
		# - 'highlight_color' -> 'highlight' (singular map key)
		normalized_name = (components or '').strip().lower()
		if normalized_name == 'info page':
			components = 'info_page'
		elif normalized_name == 'highlight_color':
			components = 'highlight'

		try:
			if preview:
				self.start_preview()
		except Exception:
			pass

		try:
			if components in (getattr(self.app, 'singular_colors_d', {}) or {}):
				self.configure_singular_component(components)
				return

			if components == 'app':
				if colors:
					self.set_palette(
						colors.get('main'),
						colors.get('second'),
						colors.get('text'),
						colors.get('button'),
					)
				else:
					self.configure_app_palette()
				return

			if components == 'info_page':
				self.configure_info_page()
				return

			if components == 'v_keyboard':
				self.configure_virtual_keyboard()
				return

			if components == 'advance_options':
				self.configure_advance_options()
				return
		finally:
			# Caller decides whether to commit or cancel preview.
			pass

		# Unknown component: no action
		return
