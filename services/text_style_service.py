from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Tuple, Optional, Dict, Callable
from tkinter import font as tkfont
from tkinter import messagebox, colorchooser, TclError
from dependencies.universal_functions import get_time


@dataclass
class TextStyleService:
	'''
	Text styling utilities for a Tk Text-based editor.

	Host `app` should provide:
	  - app.EgonTE: tk.Text-compatible widget
	  - app.size_var: IntVar (optional)
	  - app.font_family: StringVar (optional)
	  - app.font_ui, app.font_size: Combobox widgets (optional)
	  - app.indent_method: StringVar or 'tab'/'space' (optional)
	  - app.data + app.saved_settings(...) for presets (optional)
	  - app.record_list (optional)
	'''
	app: Any

	# ---------------- internals: base font binding ----------------

	def ensure_base_font(self) -> tkfont.Font:
		'''
		Ensure there's a persistent tkfont.Font object bound to the text widget.
		Using a single Font instance guarantees .configure(...) changes reflect immediately.
		'''
		# If we already created a base font earlier, ensure the widget uses it
		base_font = getattr(self.app, 'ete_base_font', None)
		if isinstance(base_font, tkfont.Font):
			try:
				# Rebind widget to the same font instance if needed
				current_spec = self.app.EgonTE.cget('font')
				# If widget isn't using our Font (e.g., tuple or different name), set it now
				if current_spec != str(base_font):
					self.app.EgonTE.configure(font=base_font)
				return base_font
			except Exception:
				pass

		# Otherwise, derive from current widget font and create a persistent tkfont.Font
		try:
			current_font_spec = self.app.EgonTE.cget('font')
			try:
				# Named font -> copy
				derived_font = tkfont.nametofont(current_font_spec).copy()
			except TclError:
				# Literal spec -> build a Font from it
				derived_font = tkfont.Font(self.app.EgonTE, font=current_font_spec)
		except Exception:
			derived_font = tkfont.Font(self.app.EgonTE, family='Arial', size=16)

		# Store and bind
		setattr(self.app, 'ete_base_font', derived_font)
		try:
			self.app.EgonTE.configure(font=derived_font)
		except Exception:
			pass
		return derived_font

	def font_actual(self) -> Tuple[str, int]:
		'''
		Return (family, size) for the current bound font (safe).
		'''
		try:
			base_font = self.ensure_base_font()
			family_name = base_font.actual('family')
			size_value = int(base_font.actual('size'))
			return str(family_name), int(size_value)
		except Exception:
			return 'Arial', 16

	def initialize_from_widget(self) -> None:
		'''
		Call once after the Text widget is created: binds a persistent font and syncs toolbar vars.
		'''
		base_font = self.ensure_base_font()
		try:
			family_name = base_font.actual('family')
			size_value = int(base_font.actual('size'))
		except Exception:
			family_name, size_value = 'Arial', 16

		# Sync toolbar variables if present
		try:
			if hasattr(self.app, 'font_family') and callable(getattr(self.app.font_family, 'set', None)):
				self.app.font_family.set(family_name)
		except Exception:
			pass
		try:
			if hasattr(self.app, 'size_var') and callable(getattr(self.app.size_var, 'set', None)):
				self.app.size_var.set(size_value)
		except Exception:
			pass

	# ---------------- logging helper ----------------

	def append_record(self, log_message: str) -> None:
		try:
			self.app.record_list.append(log_message)
		except Exception:
			pass

	# ---------------- selection helpers ----------------

	def get_selection_bounds(self) -> Tuple[str, str]:
		'''
		Return (first, last) Tk indices for current selection; otherwise ('1.0', 'end-1c').
		'''
		try:
			if self.app.EgonTE.tag_ranges('sel'):
				return self.app.EgonTE.index('sel.first'), self.app.EgonTE.index('sel.last')
		except Exception:
			pass
		return '1.0', 'end-1c'

	def apply_to_lines_in_selection(self, line_function: Callable[[str, str], None]) -> None:
		'''
		Run line_function(line_start, line_end) for each line touched by selection.
		'''
		first_index, last_index = self.get_selection_bounds()
		try:
			start_line_index = self.app.EgonTE.index(f'{first_index} linestart')
			end_line_end_index = self.app.EgonTE.index(f'{last_index} lineend')
			current_line_index = start_line_index
			while self.app.EgonTE.compare(current_line_index, '<=', end_line_end_index):
				current_line_end = self.app.EgonTE.index(f'{current_line_index} lineend')
				line_function(current_line_index, current_line_end)
				if self.app.EgonTE.compare(current_line_end, '==', 'end-1c'):
					break
				current_line_index = self.app.EgonTE.index(f'{current_line_end} +1c')
		except Exception:
			pass

	# ---------------- widget-wide font controls ----------------

	def set_font_family(self, family_name: str) -> None:
		if not family_name:
			return
		base_font = self.ensure_base_font()
		try:
			base_font.configure(family=family_name)
			# Ensure widget is bound to the persistent font
			self.app.EgonTE.configure(font=base_font)
			try:
				if hasattr(self.app, 'font_family'):
					self.app.font_family.set(family_name)
			except Exception:
				pass
		except Exception:
			pass
		applied_family, applied_size = self.font_actual()
		self.append_record(f'> [{get_time()}] - font changed to {applied_family} {applied_size}')

	def set_font_size(self, size_value: int) -> None:
		base_font = self.ensure_base_font()
		try:
			size_value = int(size_value)
		except Exception:
			size_value = 16
		try:
			if hasattr(self.app, 'size_var'):
				self.app.size_var.set(size_value)
		except Exception:
			pass
		try:
			base_font.configure(size=size_value)
			self.app.EgonTE.configure(font=base_font)
		except Exception:
			pass
		_, applied_size = self.font_actual()
		self.append_record(f'> [{get_time()}] - font size changed to {applied_size}')

	def set_font(self, *, family: Optional[str] = None, size: Optional[int] = None) -> None:
		'''
		Convenience: set both family and/or size using the persistent font instance.
		'''
		base_font = self.ensure_base_font()
		try:
			if family:
				base_font.configure(family=family)
				try:
					if hasattr(self.app, 'font_family'):
						self.app.font_family.set(family)
				except Exception:
					pass
			if size is not None:
				base_font.configure(size=int(size))
				try:
					if hasattr(self.app, 'size_var'):
						self.app.size_var.set(int(size))
				except Exception:
					pass
			self.app.EgonTE.configure(font=base_font)
		except Exception:
			pass
		applied_family, applied_size = self.font_actual()
		self.append_record(f'> [{get_time()}] - font set to {applied_family} {applied_size}')

	def nudge_font_size(self, delta: int) -> None:
		try:
			current_size = int(self.app.size_var.get())
		except Exception:
			current_size = self.font_actual()[1]
		self.set_font_size(max(1, current_size + int(delta)))

	# ---------------- inline typeface via tags ----------------

	def base_font_copy(self) -> tkfont.Font:
		'''
		Return a copy of the current base font for tag use (do not bind to widget).
		'''
		try:
			base_font = self.ensure_base_font()
			return base_font.copy()
		except Exception:
			return tkfont.Font(self.app.EgonTE, family='Arial', size=16)

	def apply_typeface(self, typeface_tag: str) -> None:
		'''
		Toggle a typeface/style over selection (or whole buffer).
		Supported:
		  - 'weight-bold'
		  - 'slant-italic'
		  - 'underline'
		  - 'overstrike'
		  - 'normal' (clears all above)
		'''
		first_index, last_index = self.get_selection_bounds()
		style_tags = ('weight-bold', 'slant-italic', 'underline', 'overstrike')

		if typeface_tag == 'normal':
			try:
				for tag_name in style_tags:
					self.app.EgonTE.tag_remove(tag_name, first_index, last_index)
			except Exception:
				pass
			return

		if typeface_tag not in style_tags:
			return

		derived_font = self.base_font_copy()
		font_cfg: Dict[str, Any] = {}
		tag_cfg: Dict[str, Any] = {}

		if typeface_tag == 'weight-bold':
			font_cfg['weight'] = 'bold'
		elif typeface_tag == 'slant-italic':
			font_cfg['slant'] = 'italic'
		elif typeface_tag == 'underline':
			tag_cfg['underline'] = 1
		elif typeface_tag == 'overstrike':
			tag_cfg['overstrike'] = 1

		try:
			if font_cfg:
				derived_font.configure(**font_cfg)
			if font_cfg and tag_cfg:
				self.app.EgonTE.tag_configure(typeface_tag, font=derived_font, **tag_cfg)
			elif font_cfg:
				self.app.EgonTE.tag_configure(typeface_tag, font=derived_font)
			elif tag_cfg:
				self.app.EgonTE.tag_configure(typeface_tag, **tag_cfg)
			else:
				self.app.EgonTE.tag_configure(typeface_tag, font=derived_font)

			if self.app.EgonTE.tag_nextrange(typeface_tag, first_index, last_index):
				self.app.EgonTE.tag_remove(typeface_tag, first_index, last_index)
			else:
				self.app.EgonTE.tag_add(typeface_tag, first_index, last_index)
		except Exception:
			pass

	def toggle_bold(self) -> None:
		self.apply_typeface('weight-bold')

	def toggle_italic(self) -> None:
		self.apply_typeface('slant-italic')

	def toggle_underline(self) -> None:
		self.apply_typeface('underline')

	def toggle_overstrike(self) -> None:
		self.apply_typeface('overstrike')

	def clear_style_tags(self, *, scope: Optional[Tuple[str, str]] = None) -> None:
		'''
		Remove known typeface/color/paragraph tags from scope (default: whole buffer).
		'''
		first_index, last_index = scope or ('1.0', 'end-1c')
		tags_to_remove = (
			'weight-bold', 'slant-italic', 'underline', 'overstrike',
			'size', 'colored_txt', 'colored_bg', 'paragraph',
		)
		for tag_name in tags_to_remove:
			try:
				self.app.EgonTE.tag_remove(tag_name, first_index, last_index)
			except Exception:
				pass

	def clear_all_formatting(self) -> None:
		'''
		Reset to the widget base font and remove known style tags/colors over entire buffer.
		'''
		try:
			self.clear_style_tags()
			base_font = self.ensure_base_font()
			# Rebind to base font and reset fg/bg best-effort
			self.app.EgonTE.configure(
				font=base_font,
				foreground=self.app.EgonTE.cget('fg'),
				background=self.app.EgonTE.cget('bg'),
			)
		except Exception:
			pass

	# ---------------- alignment (non-destructive; tag-only) ----------------

	def align_text(self, alignment: str = 'left') -> None:
		'''
		Apply justification tag across selected lines (or current line if no selection).
		alignment in {'left', 'center', 'right'}.
		'''
		if alignment not in ('left', 'center', 'right'):
			alignment = 'left'
		try:
			self.app.EgonTE.tag_config(alignment, justify=alignment)

			def tag_line(line_start: str, line_end: str) -> None:
				self.app.EgonTE.tag_add(alignment, line_start, line_end)

			self.apply_to_lines_in_selection(tag_line)
		except Exception:
			try:
				messagebox.showerror(getattr(self.app, 'title_struct', 'App - ') + 'error', 'choose a content')
			except Exception:
				pass

	# ---------------- color via tags ----------------

	def apply_text_color(self, color_hex: Optional[str] = None) -> None:
		'''
		Apply foreground color to selection or whole buffer using a 'colored_txt' tag.
		'''
		if color_hex is None:
			try:
				color_hex = colorchooser.askcolor(title='Text color')[1]
			except Exception:
				color_hex = None
		if not color_hex:
			return

		try:
			derived_font = self.base_font_copy()
			self.app.EgonTE.tag_configure('colored_txt', font=derived_font, foreground=color_hex)
			first_index, last_index = self.get_selection_bounds()
			self.app.EgonTE.tag_add('colored_txt', first_index, last_index)
		except Exception:
			pass

	def apply_background_color(self, color_hex: Optional[str] = None) -> None:
		'''
		Apply background color to selection or whole buffer using a 'colored_bg' tag.
		'''
		if color_hex is None:
			try:
				color_hex = colorchooser.askcolor(title='Background color')[1]
			except Exception:
				color_hex = None
		if not color_hex:
			return

		try:
			self.app.EgonTE.tag_configure('colored_bg', background=color_hex)
			first_index, last_index = self.get_selection_bounds()
			self.app.EgonTE.tag_add('colored_bg', first_index, last_index)
		except Exception:
			pass

	# ---------------- indentation ----------------

	def get_indent_unit(self) -> str:
		'''
		Return '\t' or spaces based on app.indent_method (default 4 spaces).
		'''
		try:
			indent_method_var = getattr(self.app, 'indent_method', None)
			if indent_method_var and callable(getattr(indent_method_var, 'get', None)):
				return '\t' if indent_method_var.get() == 'tab' else '    '
			if isinstance(indent_method_var, str) and indent_method_var.lower() == 'tab':
				return '\t'
		except Exception:
			pass
		return '    '

	def indent_selection(self, delta: int) -> None:
		'''
		Indent (delta > 0) or outdent (delta < 0) each selected line by one indent unit.
		'''
		indent_unit = self.get_indent_unit()

		def indent_line(line_start: str, line_end: str) -> None:
			try:
				current_line_text = self.app.EgonTE.get(line_start, line_end)
			except Exception:
				return
			if delta > 0:
				try:
					self.app.EgonTE.insert(line_start, indent_unit)
				except Exception:
					pass
			elif delta < 0:
				try:
					if current_line_text.startswith('\t'):
						self.app.EgonTE.delete(line_start, f'{line_start} +1c')
					elif current_line_text.startswith(' ' * len(indent_unit)):
						self.app.EgonTE.delete(line_start, f'{line_start} +{len(indent_unit)}c')
				except Exception:
					pass

		self.apply_to_lines_in_selection(indent_line)

	# ---------------- paragraph/line spacing ----------------

	def set_line_spacing(
		self,
		spacing_line_top: Optional[int] = None,
		spacing_wrap_extra: Optional[int] = None,
		spacing_line_bottom: Optional[int] = None,
	) -> None:
		'''
		Configure paragraph spacing using tag 'paragraph' (spacing1/2/3).
		'''
		cfg: Dict[str, int] = {}
		if isinstance(spacing_line_top, int):
			cfg['spacing1'] = spacing_line_top
		if isinstance(spacing_wrap_extra, int):
			cfg['spacing2'] = spacing_wrap_extra
		if isinstance(spacing_line_bottom, int):
			cfg['spacing3'] = spacing_line_bottom
		if not cfg:
			return

		try:
			self.app.EgonTE.tag_configure('paragraph', **cfg)

			def tag_paragraph(line_start: str, line_end: str) -> None:
				self.app.EgonTE.tag_add('paragraph', line_start, line_end)

			self.apply_to_lines_in_selection(tag_paragraph)
			try:
				self.app.paragraph_spacing_meta = dict(cfg)
				self.app._paragraph_spacing_meta = dict(cfg)
			except Exception:
				pass
		except Exception:
			pass

	# ---------------- presets ----------------

	def export_current_text_style(self) -> Dict[str, Any]:
		'''
		Export family, size, widget fg/bg and paragraph spacing tag if present.
		'''
		out: Dict[str, Any] = {}
		try:
			base_font = self.ensure_base_font()
			out['family'] = base_font.actual('family')
			out['size'] = int(base_font.actual('size'))
		except Exception:
			out.setdefault('family', 'Arial')
			out.setdefault('size', 16)
		try:
			out['fg'] = self.app.EgonTE.cget('fg')
			out['bg'] = self.app.EgonTE.cget('bg')
		except Exception:
			pass
		try:
			meta = getattr(self.app, 'paragraph_spacing_meta', None)
			if not isinstance(meta, dict):
				meta = getattr(self.app, '_paragraph_spacing_meta', None)
			if isinstance(meta, dict):
				out['paragraph'] = dict(meta)
		except Exception:
			pass
		return out

	def save_style_preset(self, preset_name: str) -> None:
		if not preset_name:
			return
		data = self.export_current_text_style()
		try:
			if not hasattr(self.app, 'data') or not isinstance(self.app.data, dict):
				self.app.data = {}
			presets = self.app.data.get('text_style_presets', {}) or {}
			if not isinstance(presets, dict):
				presets = {}
			presets[preset_name] = data
			self.app.data['text_style_presets'] = presets
			if hasattr(self.app, 'saved_settings'):
				self.app.saved_settings(special_mode='save')
			self.append_record(f"> [{get_time()}] - Text style preset '{preset_name}' saved")
		except Exception:
			pass

	def load_style_preset(self, preset_name: str) -> bool:
		try:
			presets = (getattr(self.app, 'data', {}) or {}).get('text_style_presets', {}) or {}
			payload = presets.get(preset_name)
			if not payload:
				try:
					messagebox.showerror(
						getattr(self.app, 'title_struct', '') + 'error',
						f"Preset '{preset_name}' not found",
					)
				except Exception:
					pass
				return False

			self.set_font(family=payload.get('family'), size=payload.get('size'))

			try:
				fg = payload.get('fg')
				bg = payload.get('bg')
				if fg:
					self.app.EgonTE.configure(fg=fg, insertbackground=fg)
				if bg:
					self.app.EgonTE.configure(bg=bg)
			except Exception:
				pass

			paragraph = payload.get('paragraph')
			if isinstance(paragraph, dict):
				try:
					self.app.paragraph_spacing_meta = dict(paragraph)
					self.app._paragraph_spacing_meta = dict(paragraph)
				except Exception:
					pass
				self.set_line_spacing(
					spacing_line_top=paragraph.get('spacing1'),
					spacing_wrap_extra=paragraph.get('spacing2'),
					spacing_line_bottom=paragraph.get('spacing3'),
				)

			self.append_record(f"> [{get_time()}] - Text style preset '{preset_name}' applied")
			return True
		except Exception:
			return False

	def delete_style_preset(self, preset_name: str) -> bool:
		try:
			presets = (getattr(self.app, 'data', {}) or {}).get('text_style_presets', {}) or {}
			if preset_name in presets:
				del presets[preset_name]
				self.app.data['text_style_presets'] = presets
				if hasattr(self.app, 'saved_settings'):
					self.app.saved_settings(special_mode='save')
				self.append_record(f"> [{get_time()}] - Text style preset '{preset_name}' deleted")
				return True
		except Exception:
			pass
		return False

	def list_style_presets(self) -> Tuple[str, ...]:
		try:
			presets = (getattr(self.app, 'data', {}) or {}).get('text_style_presets', {}) or {}
			return tuple(sorted(presets.keys()))
		except Exception:
			return tuple()

	# ---------------- toolbar wiring ----------------

	def wire_toolbar(self) -> None:
		'''
		Bind toolbar comboboxes to this service (safe to call even if missing).
		Saves widgets to attributes to comply with project conventions.
		'''
		try:
			self.font_family_widget = getattr(self.app, 'font_ui', None)
			if self.font_family_widget is not None:
				def on_family_selected(_event=None) -> None:
					try:
						selected_family = self.app.font_family.get()
						selected_size = int(self.app.size_var.get()) if hasattr(self.app, 'size_var') else None
						self.set_font(family=selected_family, size=selected_size)
					except Exception:
						pass
				self.font_family_widget.bind('<<ComboboxSelected>>', on_family_selected)
		except Exception:
			pass

		try:
			self.size_combobox_widget = getattr(self.app, 'font_size', None)
			if self.size_combobox_widget is not None:
				def on_size_selected(_event=None) -> None:
					try:
						self.set_font(size=int(self.app.size_var.get()))
					except Exception:
						pass
				self.size_combobox_widget.bind('<<ComboboxSelected>>', on_size_selected)
		except Exception:
			pass

	# ---------------- UI convenience ----------------

	def increase_font_size(self) -> None:
		self.nudge_font_size(+1)

	def decrease_font_size(self) -> None:
		self.nudge_font_size(-1)
