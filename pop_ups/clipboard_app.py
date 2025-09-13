# Standalone Clipboard History popup
# - Two sections: Pinned (📌) and Unpinned (history with capacity)
# - Index-based mapping (safe with duplicates)
# - Multi-select Copy/Paste/Delete; Move Up/Down; Pin/Unpin
# - Drag-and-drop reorder within section (disabled while filtered)
# - Optional live-refresh hook for external updates: app._clipboard_apply_filter
# - Pause/Resume clipboard watcher, Clear Pins, selection/count indicators
# - Notebook tabs: History (main tools) and Settings (mouse behavior)
# - Section filter dropdown: All / Pinned / Unpinned

import tkinter as tk
from tkinter import ttk


def make_popup(app, title_text, *, name='clipboard_history_popup'):
	# Prefer enhanced builders if available
	builders = getattr(app, 'ui_builders', None)
	if builders and hasattr(builders, 'make_pop_ups_window'):
		try:
			return builders.make_pop_ups_window(
				function=lambda: None,
				custom_title=title_text,
				parent=getattr(app, 'root', None),
				name=name,
				topmost=False,
				modal=False,
			)
		except Exception:
			pass
	# Fallback to app's helper if present (ensure correct signature)
	if hasattr(app, 'make_pop_ups_window') and callable(app.make_pop_ups_window):
		try:
			return app.make_pop_ups_window(lambda: None, custom_title=title_text)
		except Exception:
			pass
	# Final fallback to a plain Toplevel
	parent_widget = getattr(app, 'tk', None) or getattr(app, 'root', None)
	if not isinstance(parent_widget, tk.Misc):
		parent_widget = tk._get_default_root() or tk.Tk()
	popup_window = tk.Toplevel(parent_widget)
	popup_window.title(title_text)
	# Apply optional transparency if app exposes it
	if hasattr(app, 'st_value'):
		try:
			popup_window.attributes('-alpha', app.st_value)
		except Exception:
			pass
	# Respect "topmost" and "limit sizes" app preferences when available
	try:
		if getattr(app, 'all_tm_v', None):
			popup_window.attributes('-topmost', bool(app.all_tm_v.get()))
	except Exception:
		pass
	try:
		if getattr(app, 'limit_w_s', None) and app.limit_w_s.get():
			popup_window.resizable(False, False)
	except Exception:
		pass
	# Track window in app for theming/management if supported
	try:
		if hasattr(app, 'opened_windows') and isinstance(app.opened_windows, list):
			app.opened_windows.append(popup_window)
	except Exception:
		pass
	return popup_window


def open_clipboard_history(app):
	# Ensure history storage exists on the app
	if not hasattr(app, 'copy_list') or app.copy_list is None:
		app.copy_list = []
	# Pinned items container (strings, unique, most-recent first)
	if not hasattr(app, 'clipboard_pins') or app.clipboard_pins is None:
		app.clipboard_pins = []
	history_capacity_limit = getattr(app, 'clipboard_history_capacity', 100)

	popup_window = make_popup(app, 'Clipboard History')

	# Resolve tk/ttk modules (prefer real modules, not instances)
	# NOTE:
	# - app.tk is typically a Tk instance (tkapp), not the tkinter module.
	# - Always bind tk_mod to the tkinter module and ttk_mod to tkinter.ttk to access classes like StringVar.
	try:
		import tkinter as _tk
		import tkinter.ttk as _ttk
	except Exception:
		_tk, _ttk = tk, ttk
	# Bind unconditionally so these names always exist
	tk_mod = _tk
	ttk_mod = _ttk

	# ---- Local state (self-sustained) ----
	search_filter_variable = tk_mod.StringVar(master=popup_window)
	filtered_pinned_items: list[str] = []
	filtered_unpinned_items: list[str] = []
	last_seen_clipboard_text = {'value': None}
	clipboard_watcher_enabled = {'on': True}
	watcher_paused_var = tk_mod.BooleanVar(master=popup_window, value=False)
	auto_close_on_paste_var = tk_mod.BooleanVar(master=popup_window, value=False)  # optional nicety

	# Widgets (saved to variables)
	history_listbox: tk.Listbox | None = None
	context_menu: tk.Menu | None = None
	selection_status_label: ttk.Label | None = None
	counts_label: ttk.Label | None = None

	# NOTE: removed unused 'dragging_model_index' to avoid confusion

	# ---- Helpers: history and view sync ----
	def _ensure_unique_in_list(container_list, text_value: str):
		try:
			existing_index = container_list.index(text_value)
			container_list.pop(existing_index)
		except ValueError:
			pass

	def _trim_capacity():
		# Capacity applies to non-pinned list only
		if len(app.copy_list) > history_capacity_limit:
			del app.copy_list[history_capacity_limit:]

	def push_history_item_to_top(item_text: str, force_pin: bool = False):
		if not item_text:
			return
		normalized_text = str(item_text)

		# If pinned toggle requested, ensure goes to pins
		if force_pin:
			_ensure_unique_in_list(app.clipboard_pins, normalized_text)
			app.clipboard_pins.insert(0, normalized_text)
			# Remove from unpinned if present
			try:
				app.copy_list.remove(normalized_text)
			except ValueError:
				pass
		else:
			# If already pinned, move to top of pins; else move in unpinned
			if normalized_text in app.clipboard_pins:
				_ensure_unique_in_list(app.clipboard_pins, normalized_text)
				app.clipboard_pins.insert(0, normalized_text)
			else:
				_ensure_unique_in_list(app.copy_list, normalized_text)
				app.copy_list.insert(0, normalized_text)
				_trim_capacity()

		refresh_filtered_items(update_listbox_items=True)

	def _filtered_concat():
		return filtered_pinned_items + filtered_unpinned_items

	def _view_index_to_model(view_index: int):
		# Return tuple (in_pins: bool, model_index: int|None) for a given view index
		total_pins = len(filtered_pinned_items)
		if 0 <= view_index < total_pins:
			value = filtered_pinned_items[view_index]
			try:
				return True, app.clipboard_pins.index(value)
			except ValueError:
				return True, None
		else:
			up_index = view_index - total_pins
			if 0 <= up_index < len(filtered_unpinned_items):
				value = filtered_unpinned_items[up_index]
				try:
					return False, app.copy_list.index(value)
				except ValueError:
					return False, None
		return False, None

	def _view_selection_indices_sorted():
		if history_listbox is None:
			return []
		selection_indices = list(history_listbox.curselection())
		return sorted(selection_indices)

	def _update_status_labels():
		# Selection count
		try:
			if selection_status_label is not None and history_listbox is not None:
				n = len(history_listbox.curselection())
				selection_status_label.configure(text=f'{n} selected' if n else '')
		except Exception:
			pass
		# Totals (visible counts)
		try:
			if counts_label is not None:
				counts_label.configure(
					text=f'Pins: {len(filtered_pinned_items)} • Items: {len(filtered_unpinned_items)}'
				)
		except Exception:
			pass

	def _get_show_mode_value() -> str:
		# Safe access to show mode var if it's not initialized yet
		try:
			val = (show_mode_var.get() or 'All').strip().lower()
			if val in ('all', 'pinned', 'unpinned'):
				return val
		except Exception:
			pass
		return 'all'

	def refresh_filtered_items(update_listbox_items: bool = False):
		nonlocal filtered_pinned_items, filtered_unpinned_items
		query_text = (search_filter_variable.get() or '').strip().lower()

		# Section filter (All / Pinned / Unpinned)
		show_mode = _get_show_mode_value()
		src_pins = list(app.clipboard_pins)
		src_unpins = list(app.copy_list)
		if show_mode == 'pinned':
			src_unpins = []
		elif show_mode == 'unpinned':
			src_pins = []

		if query_text:
			filtered_pinned_items = [s for s in src_pins if query_text in s.lower()]
			filtered_unpinned_items = [s for s in src_unpins if query_text in s.lower()]
		else:
			filtered_pinned_items = src_pins
			filtered_unpinned_items = src_unpins

		if update_listbox_items and history_listbox is not None:
			history_listbox.delete(0, 'end')
			# Render pins first, prefixed with a pin marker for clarity
			for history_text in filtered_pinned_items:
				display_text = history_text if len(history_text) <= 120 else (history_text[:117] + '...')
				history_listbox.insert('end', f'📌 {display_text}')
			# Then unpinned
			for history_text in filtered_unpinned_items:
				display_text = history_text if len(history_text) <= 120 else (history_text[:117] + '...')
				history_listbox.insert('end', display_text)
		_update_status_labels()

	def get_selected_texts_in_view_order():
		all_items = _filtered_concat()
		return [all_items[i] for i in _view_selection_indices_sorted() if 0 <= i < len(all_items)]

	def select_model_indices_in_view(in_pins: bool, model_indices: list[int]):
		# Select a set of model indices (all in same section) in view
		if history_listbox is None:
			return
		history_listbox.selection_clear(0, 'end')
		for m_idx in model_indices:
			try:
				value = (app.clipboard_pins if in_pins else app.copy_list)[m_idx]
				# Find in filtered lists
				if in_pins:
					view_index = filtered_pinned_items.index(value)
				else:
					view_index = len(filtered_pinned_items) + filtered_unpinned_items.index(value)
				history_listbox.selection_set(view_index)
				history_listbox.activate(view_index)
				history_listbox.see(view_index)
			except Exception:
				continue
		_update_status_labels()

	# ---- Expose live-refresh hook for external callers (e.g., app.add_to_clipboard_history)
	def _external_refresh(refresh_list=True):
		try:
			refresh_filtered_items(update_listbox_items=bool(refresh_list))
		except Exception:
			pass

	try:
		app._clipboard_apply_filter = _external_refresh
	except Exception:
		pass

	# ---- Popup preferences (persist softly on app)
	# mouse_action: 'paste' (double-click pastes) or 'reorder' (Alt+Drag to reorder, no dbl-click paste)
	_clipboard_opts = getattr(app, '_clipboard_opts', None)
	if not isinstance(_clipboard_opts, dict):
		_clipboard_opts = {}
		try:
			app._clipboard_opts = _clipboard_opts
		except Exception:
			pass
	mouse_action_var = tk_mod.StringVar(master=popup_window, value=_clipboard_opts.get('mouse_action', 'paste'))
	# Also hydrate moved options from saved prefs (if any)
	try:
		watcher_paused_var.set(bool(_clipboard_opts.get('pause_watcher', False)))
	except Exception:
		pass
	try:
		auto_close_on_paste_var.set(bool(_clipboard_opts.get('auto_close', False)))
	except Exception:
		pass

	# NOTE: do not reassign mouse_action_var again to avoid duplicates
	# (removed duplicate assignment here)

	# ---- Actions ----
	def action_copy_to_clipboard():
		selected_texts = get_selected_texts_in_view_order()
		if not selected_texts:
			return
		payload_text = '\n'.join(selected_texts)
		try:
			popup_window.clipboard_clear()
			popup_window.clipboard_append(payload_text)
			popup_window.update_idletasks()
			last_seen_clipboard_text['value'] = payload_text
		except Exception:
			pass
		# Move each selected item to top while preserving relative order (last becomes topmost)
		for text_value in selected_texts[::-1]:
			push_history_item_to_top(text_value)

	def action_paste_into_editor():
		selected_texts = get_selected_texts_in_view_order()
		if not selected_texts:
			return
		payload_text = '\n'.join(selected_texts)
		try:
			popup_window.clipboard_clear()
			popup_window.clipboard_append(payload_text)
			popup_window.update_idletasks()
			last_seen_clipboard_text['value'] = payload_text
		except Exception:
			pass
		for text_value in selected_texts[::-1]:
			push_history_item_to_top(text_value)
		try:
			if getattr(app, 'EgonTE', None):
				app.EgonTE.insert(app.get_pos(), payload_text)
				if auto_close_on_paste_var.get():
					on_close_popup()
		except Exception:
			pass

	def action_delete_selected():
		selection = _view_selection_indices_sorted()
		if not selection:
			return
		# Collect values per section to avoid index shift issues
		pins_to_remove = []
		unpins_to_remove = []
		all_items = _filtered_concat()
		for view_index in selection:
			if 0 <= view_index < len(filtered_pinned_items):
				pins_to_remove.append(all_items[view_index])
			else:
				unpins_to_remove.append(all_items[view_index])
		# Remove unique items
		for text_value in set(pins_to_remove):
			try:
				app.clipboard_pins.remove(text_value)
			except ValueError:
				pass
		for text_value in set(unpins_to_remove):
			try:
				app.copy_list.remove(text_value)
			except ValueError:
				pass
		refresh_filtered_items(update_listbox_items=True)

	def action_clear_all():
		# Clear only unpinned by default; pinned are preserved
		app.copy_list.clear()
		refresh_filtered_items(update_listbox_items=True)

	def action_clear_pins():
		app.clipboard_pins.clear()
		refresh_filtered_items(update_listbox_items=True)

	def action_move_selected(delta: int):
		# Moving with an active filter can be confusing; disable when filtered
		if search_filter_variable.get().strip():
			try:
				popup_window.bell()
			except Exception:
				pass
			return
		selection = _view_selection_indices_sorted()
		if not selection:
			return
		# Separate into pin and unpin groups
		pin_indices = []
		unpin_indices = []
		for view_index in selection:
			in_pins, model_idx = _view_index_to_model(view_index)
			if model_idx is None:
				continue
			(pin_indices if in_pins else unpin_indices).append(model_idx)

		# Move blocks within their own section while preserving order
		def move_block(container: list[str], indices: list[int], delta_val: int):
			if not indices:
				return indices
			indices = sorted(set(indices))
			first = indices[0]
			last = indices[-1]
			new_first = max(0, min(len(container) - (last - first + 1), first + delta_val))
			if new_first == first:
				return indices
			block = container[first:last + 1]
			# Remove original
			del container[first:last + 1]
			# Adjust if deletion was before insertion point
			if new_first > first:
				new_first -= (last - first + 1)
				new_first = max(new_first, 0)
			# Insert at new position
			container[new_first:new_first] = block
			# Return new indices
			return list(range(new_first, new_first + len(block)))

		new_pin_indices = move_block(app.clipboard_pins, pin_indices, delta)
		new_unpin_indices = move_block(app.copy_list, unpin_indices, delta)

		refresh_filtered_items(update_listbox_items=True)
		# Reselect moved items
		if new_pin_indices:
			select_model_indices_in_view(True, new_pin_indices)
		if new_unpin_indices:
			select_model_indices_in_view(False, new_unpin_indices)

	def action_toggle_pin_selected():
		selection = _view_selection_indices_sorted()
		if not selection:
			return
		all_items = _filtered_concat()
		selected_values = [all_items[i] for i in selection if 0 <= i < len(all_items)]
		# Toggle each item
		for text_value in selected_values:
			if text_value in app.clipboard_pins:
				# Unpin: remove from pins, push to top of unpinned
				try:
					app.clipboard_pins.remove(text_value)
				except ValueError:
					pass
				push_history_item_to_top(text_value, force_pin=False)
			else:
				# Pin: remove from unpinned (if present), push to top of pins
				try:
					app.copy_list.remove(text_value)
				except ValueError:
					pass
				push_history_item_to_top(text_value, force_pin=True)
		refresh_filtered_items(update_listbox_items=True)

	def action_activate_row():
		# Paste path supports multiple selection and copies to clipboard
		action_paste_into_editor()

	# ---- Drag-and-drop (clarified): only when Alt is held and mode is 'reorder'
	#      - Drag a single row or a selected block; drop target indicated by active row.
	#      - No reordering sounds/beeps; filter-active moves are silently ignored.
	#      - This avoids colliding with normal click/selection/paste actions.
	#
	# Helpers
	def _state_has_alt(event_state: int) -> bool:
		# Tk 'Alt/Mod1' bit is commonly 0x0008; keep tolerant by checking this bit.
		try:
			return bool(event_state & 0x0008)
		except Exception:
			return False

	def _move_block(container: list[str], indices: list[int], insert_at: int) -> list[int]:
		if not indices:
			return []
		indices = sorted(set(indices))
		first, last = indices[0], indices[-1]
		block = container[first:last + 1]
		del container[first:last + 1]
		if insert_at > first:
			insert_at -= (last - first + 1)
		insert_at = max(0, min(insert_at, len(container)))
		container[insert_at:insert_at] = block
		return list(range(insert_at, insert_at + len(block)))

	_drag = {'start_view_indices': [], 'in_pins': None, 'active': False}

	def _selection_section_and_model_indices():
		sel = _view_selection_indices_sorted()
		if not sel:
			return None, []
		sect_set, models = set(), []
		for v in sel:
			in_pins, mi = _view_index_to_model(v)
			if mi is None:
				continue
			sect_set.add(bool(in_pins))
			models.append(mi)
		if len(sect_set) != 1:
			return None, []
		return next(iter(sect_set)), sorted(set(models))

	def on_drag_start_event(e):
		# Only start drag when:
		# - user chose 'reorder' mode
		# - Alt key is held during Button-1 press
		if mouse_action_var.get() != 'reorder':
			return
		if not _state_has_alt(getattr(e, 'state', 0)):
			return
		if history_listbox is None:
			return
		try:
			click_idx = history_listbox.nearest(e.y)
		except Exception:
			return
		# ensure clicked row is selected (or make it the selection)
		if click_idx not in history_listbox.curselection():
			history_listbox.selection_clear(0, 'end')
			if 0 <= click_idx < history_listbox.size():
				history_listbox.selection_set(click_idx)
				history_listbox.activate(click_idx)
		in_pins, model_indices = _selection_section_and_model_indices()
		_drag['start_view_indices'] = _view_selection_indices_sorted()
		_drag['in_pins'] = in_pins
		_drag['active'] = bool(model_indices)

	def on_drag_motion_event(e):
		if not _drag['active'] or history_listbox is None:
			return
		# show current drop target
		try:
			tvi = history_listbox.nearest(e.y)
			if 0 <= tvi < history_listbox.size():
				history_listbox.activate(tvi)
				# gentle auto-scroll
				h = history_listbox.winfo_height()
				margin = max(10, int(h * 0.12))
				if e.y < margin:
					history_listbox.yview_scroll(-1, 'units')
				elif e.y > h - margin:
					history_listbox.yview_scroll(1, 'units')
		except Exception:
			pass

	def on_drag_release_event(e):
		if not _drag['active'] or history_listbox is None:
			_drag['active'] = False
			return
		_drag['active'] = False

		# Ignore when filtered (for simplicity and clarity)
		if (search_filter_variable.get() or '').strip():
			return

		try:
			drop_view_idx = history_listbox.nearest(e.y)
		except Exception:
			return
		if not (0 <= drop_view_idx < (history_listbox.size() or 0)):
			return

		# Resolve selection to model indices (use snapshot from start)
		in_pins, model_indices = _selection_section_and_model_indices()
		if not model_indices:
			tmp_sect, tmp_models = set(), []
			for v in _drag['start_view_indices']:
				ip, mi = _view_index_to_model(v)
				if mi is not None:
					tmp_sect.add(bool(ip))
					tmp_models.append(mi)
			if len(tmp_sect) == 1 and tmp_models:
				in_pins = next(iter(tmp_sect))
				model_indices = sorted(set(tmp_models))
			else:
				return

		drop_in_pins, drop_model_idx = _view_index_to_model(drop_view_idx)
		# Only in-section reorder; cross-section moves should use explicit Pin/Unpin action
		if drop_in_pins is None or bool(drop_in_pins) != bool(in_pins):
			return

		container = app.clipboard_pins if in_pins else app.copy_list
		if drop_model_idx is None:
			drop_model_idx = len(container)
		new_idxs = _move_block(container, model_indices, drop_model_idx)
		refresh_filtered_items(update_listbox_items=True)
		select_model_indices_in_view(bool(in_pins), new_idxs)

	# ---- Context menu ----
	def show_context_menu(mouse_event):
		if history_listbox is None:
			return
		try:
			clicked_index = history_listbox.nearest(mouse_event.y)
			if clicked_index not in history_listbox.curselection():
				history_listbox.selection_clear(0, 'end')
				if 0 <= clicked_index < history_listbox.size():
					history_listbox.selection_set(clicked_index)
					history_listbox.activate(clicked_index)
			context_menu.tk_popup(mouse_event.x_root, mouse_event.y_root)
		finally:
			try:
				context_menu.grab_release()
			except Exception:
				pass
		_update_status_labels()

	# ---- Clipboard watcher (active while popup is open) ----
	# Seed watcher with the current clipboard so the first poll won't import it accidentally.
	try:
		current_at_start = popup_window.clipboard_get()
	except Exception:
		current_at_start = None
	last_seen_clipboard_text['value'] = current_at_start

	def poll_system_clipboard():
		if not clipboard_watcher_enabled['on']:
			return
		if watcher_paused_var.get():
			try:
				popup_window.after(800, poll_system_clipboard)
			except Exception:
				clipboard_watcher_enabled['on'] = False
			return
		try:
			current_text = popup_window.clipboard_get()
		except Exception:
			current_text = None
		if current_text and current_text != last_seen_clipboard_text['value']:
			last_seen_clipboard_text['value'] = current_text
			push_history_item_to_top(current_text)
		try:
			popup_window.after(800, poll_system_clipboard)
		except Exception:
			clipboard_watcher_enabled['on'] = False

	def on_close_popup(_event=None):
		clipboard_watcher_enabled['on'] = False
		# Clear live refresh hook if it points to ours
		try:
			if getattr(app, '_clipboard_apply_filter', None) is _external_refresh:
				app._clipboard_apply_filter = None
		except Exception:
			pass
		# Untrack window from app if present
		try:
			if hasattr(app, 'opened_windows') and isinstance(app.opened_windows, list):
				if popup_window in app.opened_windows:
					app.opened_windows.remove(popup_window)
		except Exception:
			pass
		try:
			popup_window.destroy()
		except Exception:
			pass

	popup_window.protocol('WM_DELETE_WINDOW', on_close_popup)
	popup_window.bind('<Destroy>', lambda e: on_close_popup() if e.widget is popup_window else None)

	# ---- Layout ----
	# Notebook with "History" and "Settings"
	settings_nb = ttk_mod.Notebook(popup_window)
	history_tab = ttk_mod.Frame(settings_nb)
	settings_tab = ttk_mod.Frame(settings_nb)
	settings_nb.add(history_tab, text='History')
	settings_nb.add(settings_tab, text='Settings')
	settings_nb.pack(fill='both', expand=True, padx=8, pady=(8, 6))

	# Top controls: filter, section dropdown, watcher toggle, counts (History tab)
	top_controls_frame = ttk_mod.Frame(history_tab)
	top_controls_frame.pack(fill='x', pady=(0, 6))

	filter_label = ttk_mod.Label(top_controls_frame, text='Filter:')
	filter_label.pack(side='left')

	# Make filter shorter and avoid expanding to balance row
	filter_entry = ttk_mod.Entry(top_controls_frame, textvariable=search_filter_variable, width=18)
	filter_entry.pack(side='left', padx=(6, 8))

	# Tiny spacer to visually separate filter from section selector
	spacer = ttk_mod.Label(top_controls_frame, text=' ')
	spacer.pack(side='left')

	# Section dropdown
	show_mode_var = tk_mod.StringVar(master=popup_window, value='All')
	show_label = ttk_mod.Label(top_controls_frame, text='Show:')
	show_label.pack(side='left')
	show_combo = ttk_mod.Combobox(
		top_controls_frame,
		textvariable=show_mode_var,
		state='readonly',
		width=10,
		values=('All', 'Pinned', 'Unpinned')
	)
	show_combo.pack(side='left', padx=(4, 8))

	# Watcher and counts on the right side
	right_controls = ttk_mod.Frame(top_controls_frame)
	right_controls.pack(side='right')
	counts_label = ttk_mod.Label(right_controls, text='')
	counts_label.pack(side='left')

	search_filter_variable.trace_add('write', lambda *_: refresh_filtered_items(update_listbox_items=True))
	show_combo.bind('<<ComboboxSelected>>', lambda e: refresh_filtered_items(update_listbox_items=True))

	# Middle: listbox with scrollbar (multi-select)
	list_container_frame = ttk_mod.Frame(history_tab)
	list_container_frame.pack(fill='both', expand=True)

	vertical_scrollbar = ttk_mod.Scrollbar(list_container_frame, orient='vertical')
	history_listbox = tk_mod.Listbox(
		list_container_frame,
		selectmode='extended',
		activestyle='dotbox',
		exportselection=False,
		yscrollcommand=vertical_scrollbar.set
	)
	vertical_scrollbar.config(command=history_listbox.yview)

	history_listbox.pack(side='left', fill='both', expand=True)
	vertical_scrollbar.pack(side='right', fill='y')

	# Bottom: split action buttons into two rows (History tab)
	# Row 1: Primary actions + ordering
	primary_row = ttk_mod.Frame(history_tab)
	primary_row.pack(fill='x', pady=(6, 2))

	left_primary = ttk_mod.Frame(primary_row)
	center_primary = ttk_mod.Frame(primary_row)
	right_primary = ttk_mod.Frame(primary_row)

	left_primary.pack(side='left')
	center_primary.pack(side='left', padx=(10, 0))
	right_primary.pack(side='right')

	# Primary actions
	copy_button = ttk_mod.Button(left_primary, text='Copy', command=action_copy_to_clipboard)
	copy_button.pack(side='left')
	paste_button = ttk_mod.Button(left_primary, text='Paste', command=action_paste_into_editor)
	paste_button.pack(side='left', padx=(6, 0))
	pin_toggle_button = ttk_mod.Button(left_primary, text='Pin/Unpin', command=action_toggle_pin_selected)
	pin_toggle_button.pack(side='left', padx=(6, 0))

	# Ordering
	move_up_button = ttk_mod.Button(center_primary, text='Move Up', command=lambda: action_move_selected(-1))
	move_up_button.pack(side='left')
	move_down_button = ttk_mod.Button(center_primary, text='Move Down', command=lambda: action_move_selected(1))
	move_down_button.pack(side='left', padx=(6, 0))

	# Row 2: Cleanup / destructive
	secondary_row = ttk_mod.Frame(history_tab)
	secondary_row.pack(fill='x', pady=(2, 4))

	left_secondary = ttk_mod.Frame(secondary_row)
	right_secondary = ttk_mod.Frame(secondary_row)

	left_secondary.pack(side='left')
	right_secondary.pack(side='right')

	delete_button = ttk_mod.Button(left_secondary, text='Delete', command=action_delete_selected)
	delete_button.pack(side='left')
	clear_all_button = ttk_mod.Button(left_secondary, text='Clear Unpinned', command=action_clear_all)
	clear_all_button.pack(side='left', padx=(6, 0))
	clear_pins_button = ttk_mod.Button(left_secondary, text='Clear Pins', command=action_clear_pins)
	clear_pins_button.pack(side='left', padx=(6, 0))

	# Options and selection status on the right (History tab footer)
	options_frame = ttk_mod.Frame(history_tab)
	options_frame.pack(fill='x')
	# Selection indicator lives in History. Behavior checkboxes live in Settings (no duplicates).
	selection_status_label = ttk_mod.Label(options_frame, text='')
	selection_status_label.pack(side='right')
	# (removed History-tab auto-close checkbox and duplicate selection_status_label here)

	# Settings tab (mouse behavior)
	mouse_mode_label = ttk_mod.Label(settings_tab, text='Mouse action in list:')
	mouse_mode_label.grid(row=0, column=0, sticky='w', padx=(6, 6), pady=(6, 2))
	mouse_mode_paste = ttk_mod.Radiobutton(settings_tab, text='Paste on double-click', value='paste',
										   variable=mouse_action_var)
	mouse_mode_reorder = ttk_mod.Radiobutton(settings_tab, text='Reorder items (hold Alt + drag)', value='reorder',
											 variable=mouse_action_var)
	mouse_mode_paste.grid(row=1, column=0, sticky='w', padx=(6, 6))
	mouse_mode_reorder.grid(row=2, column=0, sticky='w', padx=(6, 6))
	mouse_hint = ttk_mod.Label(settings_tab,
							   text='Tip: In Reorder mode, hold Alt while dragging to move selected items.\nPin/Unpin moves are available via the Pin/Unpin button.',
							   foreground='gray')
	mouse_hint.grid(row=3, column=0, sticky='w', padx=(6, 6), pady=(4, 8))
	# Additional settings (moved from History)
	behavior_label = ttk_mod.Label(settings_tab, text='Behavior:')
	behavior_label.grid(row=4, column=0, sticky='w', padx=(6, 6), pady=(8, 2))
	settings_row = ttk_mod.Frame(settings_tab)
	settings_row.grid(row=5, column=0, sticky='w', padx=(6, 6))
	watcher_check = ttk_mod.Checkbutton(settings_row, text='Pause watcher', variable=watcher_paused_var)
	watcher_check.pack(side='left', padx=(0, 10))
	auto_close_check = ttk_mod.Checkbutton(settings_row, text='Auto-close on paste', variable=auto_close_on_paste_var)
	auto_close_check.pack(side='left')
	# Persist moved settings
	def _persist_settings(*_):
		try:
			app._clipboard_opts['pause_watcher'] = bool(watcher_paused_var.get())
			app._clipboard_opts['auto_close'] = bool(auto_close_on_paste_var.get())
		except Exception:
			pass
	try:
		watcher_paused_var.trace_add('write', _persist_settings)
		auto_close_on_paste_var.trace_add('write', _persist_settings)
	except Exception:
		pass


	def _apply_mouse_action_bindings():
		# Save preference
		try:
			app._clipboard_opts['mouse_action'] = mouse_action_var.get()
		except Exception:
			pass

		# Clear bindings we control
		try:
			history_listbox.unbind('<Double-Button-1>')
			history_listbox.unbind('<ButtonPress-1>')
			history_listbox.unbind('<B1-Motion>')
			history_listbox.unbind('<ButtonRelease-1>')
		except Exception:
			pass

		# Paste mode: enable double-click paste, no drag handlers
		if mouse_action_var.get() == 'paste':
			history_listbox.bind('<Double-Button-1>', lambda e: action_activate_row())
		else:
			# Reorder mode: require Alt + left-drag to move; disable dbl-click paste to avoid collisions
			history_listbox.bind('<ButtonPress-1>', on_drag_start_event)
			history_listbox.bind('<B1-Motion>', on_drag_motion_event)
			history_listbox.bind('<ButtonRelease-1>', on_drag_release_event)

	mouse_action_var.trace_add('write', lambda *_: _apply_mouse_action_bindings())

	# Context menu build
	context_menu = tk_mod.Menu(popup_window, tearoff=False)
	context_menu.add_command(label='Copy', command=action_copy_to_clipboard)
	context_menu.add_command(label='Paste', command=action_paste_into_editor)
	context_menu.add_separator()
	context_menu.add_command(label='Move Up', command=lambda: action_move_selected(-1))
	context_menu.add_command(label='Move Down', command=lambda: action_move_selected(1))
	context_menu.add_separator()
	context_menu.add_command(label='Pin/Unpin', command=action_toggle_pin_selected)
	context_menu.add_separator()
	context_menu.add_command(label='Delete', command=action_delete_selected)
	context_menu.add_command(label='Clear All (Unpinned)', command=action_clear_all)
	context_menu.add_command(label='Clear Pins', command=action_clear_pins)

	# ---- Bindings ----
	history_listbox.bind('<Button-3>', show_context_menu)  # Right-click (Win/Linux)
	history_listbox.bind('<Button-2>', show_context_menu)  # Middle-click (often mac)
	history_listbox.bind('<Control-Button-1>', show_context_menu)  # Ctrl+Click (macOS context)
	history_listbox.bind('<Return>', lambda e: action_activate_row())
	history_listbox.bind('<Delete>', lambda e: action_delete_selected())
	history_listbox.bind('<Control-BackSpace>', lambda e: action_clear_all())
	history_listbox.bind('<Control-Shift-BackSpace>', lambda e: action_clear_pins())
	history_listbox.bind('<Control-Up>', lambda e: action_move_selected(-1))
	history_listbox.bind('<Control-Down>', lambda e: action_move_selected(1))
	history_listbox.bind('<Control-c>', lambda e: action_copy_to_clipboard())
	history_listbox.bind('<Control-v>', lambda e: action_paste_into_editor())
	history_listbox.bind('<Control-p>', lambda e: action_toggle_pin_selected())
	# QoL: select all items
	history_listbox.bind('<Control-a>', lambda e: (history_listbox.select_set(0, 'end'), _update_status_labels()))
	history_listbox.bind('<<ListboxSelect>>', lambda e: _update_status_labels())

	popup_window.bind('<Escape>', lambda e: on_close_popup())
	popup_window.bind('<Control-l>', lambda e: action_clear_all())
	popup_window.bind('<Control-f>', lambda e: filter_entry.focus_set())

	# Apply initial mouse mode bindings based on saved preference
	_apply_mouse_action_bindings()

	# Populate initial data and focus
	refresh_filtered_items(update_listbox_items=True)
	if history_listbox.size() > 0:
		history_listbox.selection_set(0)
		history_listbox.activate(0)
	filter_entry.focus_set()

	# Start clipboard watcher while popup is open (seeded to avoid importing the current clipboard)
	poll_system_clipboard()

	return popup_window
