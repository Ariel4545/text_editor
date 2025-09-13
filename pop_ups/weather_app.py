# Standalone weather tool with autocomplete, details, hourly/daily charts,
# keyboard shortcuts, and a 'last city' tab.
# Conventions: snake_case, no leading underscores, single quotes, widgets saved to variables.

import os
import threading
from datetime import datetime, timedelta

try:
    import requests
except Exception:
    requests = None

try:
    from PIL import Image, ImageTk
except Exception:
    Image, ImageTk = None, None

from dependencies.universal_functions import get_time, fill_by_click
from large_variables import city_list as provided_city_list

try:
    from pyperclip import copy as copy_to_clipboard
except ImportError:
    pass

try:
    from io import BytesIO
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except Exception:
    Figure, FigureCanvasTkAgg = None, None

import tkinter as tk
from tkinter import Frame, Label, Entry, Button, Listbox, END, messagebox
from tkinter import ttk
import unicodedata


REQUEST_TIMEOUT = 10  # seconds
RECENTS_CAPACITY = 30

# ---- Unit conversion helpers (to avoid refetch on unit toggle) ----
def c_to_f(val_c):
    try:
        return (float(val_c) * 9.0 / 5.0) + 32.0
    except Exception:
        return None


def f_to_c(val_f):
    try:
        return (float(val_f) - 32.0) * 5.0 / 9.0
    except Exception:
        return None


def ms_to_mph(val_ms):
    try:
        return float(val_ms) * 2.2369362921
    except Exception:
        return None


def km_to_miles(val_km):
    try:
        return float(val_km) * 0.621371
    except Exception:
        return None


def safe_after(app, delay_ms, func):
    try:
        root = getattr(app, 'weather_root', None)
        if root is None:
            return
        if hasattr(root, 'winfo_exists') and not root.winfo_exists():
            return
        app.after(delay_ms, func)
    except Exception:
        try:
            func()
        except Exception:
            pass


def make_popup(app, title):
    try:
        return app.make_pop_ups_window(lambda: None, custom_title=title)
    except Exception:
        parent_widget = getattr(app, 'tk', None) or getattr(app, 'root', None)
        if not isinstance(parent_widget, tk.Misc):
            parent_widget = tk._get_default_root() or tk.Tk()
        popup_window = tk.Toplevel(parent_widget)
        popup_window.title(getattr(app, 'title_struct', '') + title)
        return popup_window


def format_time(fallback_datetime):
    try:
        return get_time()
    except Exception:
        return fallback_datetime.strftime('%Y-%m-%d %H:%M:%S')


def normalize_city_name(name):
    try:
        s = str(name).replace('_', ' ').replace('-', ' ').strip()
        s = ' '.join(s.split())
        parts = s.title().split(' ')
        lowered = {'Of', 'And', 'The', 'De', 'Da', 'Di', 'Du', 'La', 'Le', 'El', 'Van', 'Von'}
        fixed = [p.lower() if i > 0 and p in lowered else p for i, p in enumerate(parts)]
        result = ' '.join(fixed)
        if len(result) < 2:
            return ''
        return result
    except Exception:
        return ''


def _city_key(value: str) -> str:
    # Accent-insensitive + case-insensitive key for dedupe
    try:
        nfkd = unicodedata.normalize('NFKD', value)
        ascii_only = ''.join(c for c in nfkd if not unicodedata.combining(c))
        return ascii_only.casefold()
    except Exception:
        return str(value).strip().casefold()


def build_city_pool(app):
    # Prefer provided list; dedupe accent/case-insensitive; sanitize and title-case
    raw = []
    try:
        raw = list(provided_city_list)
    except Exception:
        raw = [
            'New York', 'London', 'Paris', 'Tokyo', 'Berlin', 'Sydney', 'Toronto', 'Madrid',
            'São Paulo', 'Mexico City', 'Cairo', 'Istanbul'
        ]

    sanitized = []
    seen = set()
    for item in raw:
        norm = normalize_city_name(item)
        if not norm:
            continue
        key = _city_key(norm)
        if key in seen:
            continue
        seen.add(key)
        sanitized.append(norm)
    for fallback in ('New York', 'London', 'Paris', 'Tokyo'):
        if _city_key(fallback) not in seen:
            sanitized.append(fallback)
            seen.add(_city_key(fallback))
    return sanitized


def open_weather(app):
    # Persistent state on app
    if not hasattr(app, 'weather_api_key'):
        app.weather_api_key = os.getenv('OPENWEATHER_API_KEY', '')
    if not hasattr(app, 'weather_cache'):
        app.weather_cache = {}
    if not hasattr(app, 'weather_recent_cities'):
        app.weather_recent_cities = []
    if not hasattr(app, 'weather_units'):
        app.weather_units = 'metric'
    if not hasattr(app, 'weather_last_snapshot'):
        app.weather_last_snapshot = None
    # Track distinct current city and previous snapshot for reliability
    if not hasattr(app, 'weather_current_city'):
        app.weather_current_city = None
    if not hasattr(app, 'weather_previous_snapshot'):
        app.weather_previous_snapshot = None
    # Raw cache for current and forecast in base metric units, for fast local C/F toggle
    if not hasattr(app, 'weather_numeric_state'):
        app.weather_numeric_state = None
    if not hasattr(app, 'weather_forecast_metric'):
        app.weather_forecast_metric = None
    if not hasattr(app, 'weather_current_location'):
        app.weather_current_location = None

    # Build sanitized cities pool once
    if not hasattr(app, 'weather_cities') or not isinstance(app.weather_cities, list) or not app.weather_cities:
        app.weather_cities = build_city_pool(app)

    # Reuse existing window
    if getattr(app, 'weather_root', None) and app.weather_root.winfo_exists():
        try:
            app.weather_root.deiconify()
            app.weather_root.lift()
            app.weather_entry.focus_set()
        except Exception:
            pass
        return

    # Build popup
    app.weather_root = make_popup(app, title='Weather')
    try:
        if hasattr(app, 'make_tm'):
            app.make_tm(app.weather_root)
        if hasattr(app, 'st_value'):
            app.weather_root.attributes('-alpha', getattr(app, 'st_value', 0.95))
        if hasattr(app, 'limit_w_s') and callable(getattr(app.limit_w_s, 'get', None)) and app.limit_w_s.get():
            app.weather_root.resizable(False, False)
        app.weather_root.tk.call('wm', 'iconphoto', app.weather_root._w, app.weather_image)
    except Exception:
        pass

    # Register in opened_windows list if present
    try:
        if hasattr(app, 'opened_windows'):
            app.opened_windows.append(app.weather_root)
    except Exception:
        pass

    def on_close():
        try:
            if hasattr(app, 'opened_windows') and app.weather_root in app.opened_windows:
                app.opened_windows.remove(app.weather_root)
        except Exception:
            pass
        try:
            app.weather_hourly_canvas = None
            app.weather_daily_canvas = None
            app.weather_last_canvas = None
        except Exception:
            pass
        try:
            app.weather_root.destroy()
        except Exception:
            pass

    try:
        app.weather_root.protocol('WM_DELETE_WINDOW', on_close)
    except Exception:
        pass

    # Top bar
    top_bar_frame = Frame(app.weather_root)
    top_bar_frame.pack(fill='x', padx=10, pady=8)

    city_label = Label(top_bar_frame, text='City')
    city_label.grid(row=0, column=0, sticky='w')

    app.weather_entry = Entry(top_bar_frame, width=32)
    app.weather_entry.grid(row=0, column=1, padx=6)

    app.weather_units_map = {'Celsius (°C)': 'metric', 'Fahrenheit (°F)': 'imperial'}
    app.weather_units_combo = ttk.Combobox(top_bar_frame, width=16, state='readonly', values=list(app.weather_units_map.keys()))
    app.weather_units_combo.set('Celsius (°C)' if app.weather_units == 'metric' else 'Fahrenheit (°F)')
    app.weather_units_combo.grid(row=0, column=2, padx=6)

    search_button = Button(top_bar_frame, text='Search', bd=1, command=lambda: weather_fetch_async(app))
    search_button.grid(row=0, column=3, padx=3)

    # Apply units change instantly (without re-search) by converting from cached numeric state
    def _on_units_combo_change(_e=None):
        try:
            label = app.weather_units_combo.get().strip()
            app.weather_units = app.weather_units_map.get(label, 'metric')
        except Exception:
            app.weather_units = 'metric'
        weather_render_from_cache(app)

    try:
        app.weather_units_combo.bind('<<ComboboxSelected>>', _on_units_combo_change)
    except Exception:
        pass

    # Autocomplete (hidden initially)
    app.weather_suggest_frame = Frame(app.weather_root)
    app.weather_suggest_list = Listbox(app.weather_suggest_frame, height=8)
    app.weather_suggest_list.pack(fill='x')
    app.weather_suggest_frame.pack_forget()

    # Main container
    main_container_frame = Frame(app.weather_root)
    main_container_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

    # Recent section
    recent_frame = Frame(main_container_frame)
    recent_frame.pack(side='left', fill='y')

    recent_title_label = Label(recent_frame, text='Recommended cities')
    recent_title_label.pack(anchor='w')

    app.weather_recent_list = Listbox(recent_frame, height=14)
    app.weather_recent_list.pack(fill='y')

    try:
        recent_seen = set()
        recent_source = []
        for name in reversed(app.weather_recent_cities):
            norm = normalize_city_name(name)
            if not norm:
                continue
            low = norm.lower()
            if low not in recent_seen:
                recent_source.append(norm)
                recent_seen.add(low)
        if not recent_source:
            recent_source = app.weather_cities[:8]
    except Exception:
        recent_source = app.weather_cities[:8]

    # Helper to render recent cities without duplicates (accent/case-insensitive)
    def weather_refresh_recent_list():
        try:
            app.weather_recent_list.delete(0, END)
        except Exception:
            pass
        try:
            seen_local = set()
            ordered = []
            # Prefer user's own history (most recent first); ensure uniqueness
            for name in reversed(getattr(app, 'weather_recent_cities', []) or []):
                norm = normalize_city_name(name)
                if not norm:
                    continue
                key = _city_key(norm)
                if key in seen_local:
                    continue
                seen_local.add(key)
                ordered.append(norm)
            # If no history, show a short recommended list
            if not ordered:
                for v in app.weather_cities[:8]:
                    k = _city_key(v)
                    if k not in seen_local:
                        seen_local.add(k)
                        ordered.append(v)
            for nm in ordered:
                app.weather_recent_list.insert(END, nm)
        except Exception:
            # Hard fallback to the default pool (dedup)
            try:
                app.weather_recent_list.delete(0, END)
                seen_fallback = set()
                for v in app.weather_cities[:8]:
                    k = _city_key(v)
                    if k in seen_fallback:
                        continue
                    seen_fallback.add(k)
                    app.weather_recent_list.insert(END, v)
            except Exception:
                pass

    # Expose refresh helper on app so other functions can call it (prevents duplication bugs)
    try:
        app.weather_refresh_recent_list = weather_refresh_recent_list
    except Exception:
        pass

    # Populate initial recents/recommended list (deduped)
    weather_refresh_recent_list()

    def fill_from_recent_list(event=None):
        try:
            fill_by_click(app.weather_entry, None, app.weather_recent_list)
        except Exception:
            try:
                selected_city_name = app.weather_recent_list.get('anchor')
                if selected_city_name:
                    app.weather_entry.delete(0, END)
                    app.weather_entry.insert(0, selected_city_name)
            except Exception:
                pass
        weather_fetch_async(app)

    app.weather_recent_list.bind('<Double-Button-1>', fill_from_recent_list)

    # Info panel
    info_frame = Frame(main_container_frame)
    info_frame.pack(side='left', fill='both', expand=True, padx=(12, 0))

    header_info_frame = Frame(info_frame)
    header_info_frame.pack(fill='x')

    app.weather_location_label = Label(header_info_frame, text='Location: -')
    app.weather_location_label.grid(row=0, column=0, sticky='w', padx=3)

    app.weather_time_label = Label(header_info_frame, text='Time: -')
    app.weather_time_label.grid(row=0, column=1, sticky='w', padx=12)

    main_info_frame = Frame(info_frame)
    main_info_frame.pack(fill='x', pady=(8, 2))

    app.weather_icon_label = Label(main_info_frame)
    app.weather_icon_label.grid(row=0, column=0, rowspan=3, padx=3)

    app.weather_temp_label = Label(main_info_frame, text='Temperature: -')
    app.weather_temp_label.grid(row=0, column=1, sticky='w', padx=6)

    app.weather_desc_label = Label(main_info_frame, text='Condition: -')
    app.weather_desc_label.grid(row=1, column=1, sticky='w', padx=6)

    app.weather_extra_label = Label(main_info_frame, text='Wind: - | Humidity: -')
    app.weather_extra_label.grid(row=2, column=1, sticky='w', padx=6)

    more_info_frame = Frame(info_frame)
    more_info_frame.pack(fill='x', pady=(4, 0))

    app.weather_more_main_label = Label(more_info_frame, text='Feels like: - | Pressure: - | Visibility: -')
    app.weather_more_main_label.pack(anchor='w')

    app.weather_more_sun_label = Label(more_info_frame, text='Sunrise: - | Sunset: -')
    app.weather_more_sun_label.pack(anchor='w')

    # Tabs
    app.weather_tabs = ttk.Notebook(info_frame)
    app.weather_tabs.pack(fill='both', expand=True, pady=(10, 0))

    app.weather_hourly_tab = Frame(app.weather_tabs)
    app.weather_daily_tab = Frame(app.weather_tabs)
    app.weather_last_tab = Frame(app.weather_tabs)

    app.weather_tabs.add(app.weather_hourly_tab, text='Hourly')
    app.weather_tabs.add(app.weather_daily_tab, text='Daily')
    app.weather_tabs.add(app.weather_last_tab, text='Last city')

    # Make tabs responsive when children use grid
    for _tab in (app.weather_hourly_tab, app.weather_daily_tab, app.weather_last_tab):
        try:
            _tab.grid_rowconfigure(0, weight=1)
            _tab.grid_columnconfigure(0, weight=1)
        except Exception:
            pass

    app.weather_hourly_canvas = None
    app.weather_daily_canvas = None
    app.weather_last_canvas = None

    app.weather_last_summary_label = Label(app.weather_last_tab, text='No previous city yet', justify='left')
    # Use grid for responsive layout
    try:
        app.weather_last_summary_label.grid(row=0, column=0, sticky='nw', padx=6, pady=6)
    except Exception:
        app.weather_last_summary_label.pack(anchor='w', padx=6, pady=6)

    # Enforce readable minimum size for tabs
    try:
        _enforce_min_tab_size(app, min_w=820, min_h=560, center=True)
    except Exception:
        pass

    # Actions
    actions_frame = Frame(info_frame)
    actions_frame.pack(fill='x', pady=8)

    copy_button = Button(actions_frame, text='Copy', bd=1, command=lambda: weather_copy(app))
    copy_button.pack(side='left')

    paste_button = Button(actions_frame, text='Paste to Editor', bd=1, command=lambda: weather_copy(app, paste=True))
    paste_button.pack(side='left', padx=6)

    refresh_button = Button(actions_frame, text='Refresh', bd=1, command=lambda: weather_fetch_async(app, force_refresh=True))
    refresh_button.pack(side='left', padx=6)

    # Helper: focus suggestions only if they exist
    def focus_suggestions_list(event=None):
        try:
            if app.weather_suggest_list.size() > 0:
                app.weather_suggest_list.focus_set()
                app.weather_suggest_list.selection_clear(0, END)
                app.weather_suggest_list.selection_set(0)
        except Exception:
            pass

    # Bindings (builder preferred; fallback to direct binds)
    try:
        app._popup.binds({
            'weather': [
                (app.weather_entry, '<Return>', lambda e: weather_fetch_async(app)),
                (app.weather_entry, '<KeyRelease>', lambda e: weather_update_suggestions(app)),
                (app.weather_suggest_list, '<Double-Button-1>', lambda e: weather_apply_suggestion(app)),
                (app.weather_suggest_list, '<Return>', lambda e: weather_apply_suggestion(app)),
                (app.weather_entry, '<Down>', lambda e: focus_suggestions_list()),
                (app.weather_root, '<Control-l>', lambda e: app.weather_entry.focus_set()),
                (app.weather_root, '<Control-c>', lambda e: weather_copy(app)),
                (app.weather_root, '<Control-Shift-V>', lambda e: weather_copy(app, paste=True)),
                (app.weather_root, '<F5>', lambda e: weather_fetch_async(app, force_refresh=True)),
                (app.weather_root, '<Control-u>', lambda e: weather_toggle_units(app)),
                (app.weather_root, '<Control-h>', lambda e: app.weather_tabs.select(app.weather_hourly_tab)),
                (app.weather_root, '<Control-d>', lambda e: app.weather_tabs.select(app.weather_daily_tab)),
                (app.weather_root, '<Control-j>', lambda e: app.weather_tabs.select(app.weather_last_tab)),
            ]
        })
        if hasattr(app, 'place_toolt'):
            app.place_toolt([
                (app.weather_entry, 'Type city, autocomplete will suggest'),
                (app.weather_units_combo, 'Units'),
                (search_button, 'Search (Enter)'),
                (copy_button, 'Copy summary'),
                (paste_button, 'Paste summary to editor'),
                (refresh_button, 'Refresh data (F5)'),
            ])
    except Exception:
        try:
            app.weather_root.bind('<Return>', lambda e: weather_fetch_async(app))
            app.weather_root.bind('<Control-l>', lambda e: app.weather_entry.focus_set())
            app.weather_root.bind('<Control-c>', lambda e: weather_copy(app))
            app.weather_root.bind('<Control-Shift-V>', lambda e: weather_copy(app, paste=True))
            app.weather_root.bind('<F5>', lambda e: weather_fetch_async(app, force_refresh=True))
            app.weather_root.bind('<Control-u>', lambda e: weather_toggle_units(app))
            app.weather_root.bind('<Control-h>', lambda e: app.weather_tabs.select(app.weather_hourly_tab))
            app.weather_root.bind('<Control-d>', lambda e: app.weather_tabs.select(app.weather_daily_tab))
            app.weather_root.bind('<Control-j>', lambda e: app.weather_tabs.select(app.weather_last_tab))
            app.weather_entry.bind('<KeyRelease>', lambda e: weather_update_suggestions(app))
            app.weather_entry.bind('<Down>', focus_suggestions_list)
            app.weather_suggest_list.bind('<Double-Button-1>', lambda e: weather_apply_suggestion(app))
            app.weather_suggest_list.bind('<Return>', lambda e: weather_apply_suggestion(app))
        except Exception:
            pass

    # Best-effort centering near the app window
    try:
        app.weather_root.update_idletasks()
        win_w, win_h = app.weather_root.winfo_width(), app.weather_root.winfo_height()
        app_x, app_y = app.winfo_x(), app.winfo_y()
        app_w, app_h = app.winfo_width(), app.winfo_height()
        pos_x = int(app_x + (app_w / 2) - (win_w / 2))
        pos_y = int(app_y + (app_h / 2) - (win_h / 2))
        app.weather_root.geometry(f'{win_w}x{win_h}+{pos_x}+{pos_y}')
    except Exception:
        pass

    try:
        app.weather_entry.focus_set()
    except Exception:
        pass


def weather_toggle_units(app):
    try:
        current_label = app.weather_units_combo.get()
        new_label = 'Fahrenheit (°F)' if 'Celsius' in current_label else 'Celsius (°C)'
        app.weather_units_combo.set(new_label)
        # Re-render from cached raw (no network)
        weather_render_from_cache(app)
    except Exception:
        pass


def weather_copy(app, paste=False):
    try:
        location_line = app.weather_location_label.cget('text')
        temperature_line = app.weather_temp_label.cget('text')
        time_line = app.weather_time_label.cget('text')
        description_line = app.weather_desc_label.cget('text')
    except Exception:
        return
    payload_text = f'{location_line}\n{temperature_line}\n{time_line}\n{description_line}'
    try:
        copy_to_clipboard(payload_text)
    except Exception:
        pass
    if paste:
        try:
            if getattr(app, 'EgonTE', None):
                insert_index = app.get_pos() if hasattr(app, 'get_pos') else 'end'
                app.EgonTE.insert(insert_index, '\n' + payload_text + '\n')
        except Exception:
            pass


def weather_update_suggestions(app):
    try:
        search_text_lower = app.weather_entry.get().strip().lower()
    except Exception:
        search_text_lower = ''
    if not search_text_lower:
        app.weather_suggest_frame.pack_forget()
        return
    try:
        pool = list(dict.fromkeys(app.weather_cities))  # unique, preserve order
        starts = [c for c in pool if c.lower().startswith(search_text_lower)]
        contains = [c for c in pool if search_text_lower in c.lower() and c not in starts]
        filtered_cities = starts + contains
    except Exception:
        filtered_cities = []
    if not filtered_cities:
        app.weather_suggest_frame.pack_forget()
        return
    try:
        app.weather_suggest_list.delete(0, END)
        for suggestion in filtered_cities[:25]:
            app.weather_suggest_list.insert(END, suggestion)
        app.weather_suggest_frame.pack(fill='x', padx=10, pady=(0, 6))
    except Exception:
        app.weather_suggest_frame.pack_forget()


def weather_apply_suggestion(app):
    try:
        selected_indices = app.weather_suggest_list.curselection()
        if not selected_indices:
            return
        selected_value = app.weather_suggest_list.get(selected_indices[0])
        app.weather_entry.delete(0, END)
        app.weather_entry.insert(0, selected_value)
        app.weather_suggest_frame.pack_forget()
        weather_fetch_async(app)
    except Exception:
        pass


def weather_fetch_async(app, force_refresh=False):
    '''
    Fetches current weather and forecast for the city in the entry box.
    Network work runs in a background thread.
    - Always fetches base data in metric units for consistent local conversions.
    - Updates 'recent cities' without duplicates (case/accent-insensitive).
    - Respects the currently selected UI units when rendering (no extra fetch).
    '''
    # Resolve target UI units (metric/imperial) from the combobox if present
    try:
        units_label = app.weather_units_combo.get().strip()
        app.weather_units = app.weather_units_map.get(units_label, 'metric')
    except Exception:
        app.weather_units = getattr(app, 'weather_units', 'metric') or 'metric'

    # Resolve and normalize city name
    try:
        city_input = app.weather_entry.get().strip()
        city_name = normalize_city_name(city_input)
    except Exception:
        city_name = ''
    if not city_name:
        try:
            messagebox.showinfo(getattr(app, 'title_struct', '') + 'Weather', 'Please enter a city name')
        except Exception:
            pass
        return

    # Echo normalized value to the entry
    try:
        app.weather_entry.delete(0, END)
        app.weather_entry.insert(0, city_name)
    except Exception:
        pass

    # Maintain recent cities without duplicates (accent/case-insensitive) and capacity cap
    try:
        if not hasattr(app, 'weather_recent_cities') or app.weather_recent_cities is None:
            app.weather_recent_cities = []
        key_list = [_city_key(c) for c in app.weather_recent_cities]
        if _city_key(city_name) not in key_list:
            app.weather_recent_cities.append(city_name)
            if len(app.weather_recent_cities) > RECENTS_CAPACITY:
                app.weather_recent_cities = app.weather_recent_cities[-RECENTS_CAPACITY:]

        # Try to refresh listbox using helper if available
        refresh_helper = getattr(app, 'weather_refresh_recent_list', None)
        if callable(refresh_helper):
            refresh_helper()
        else:
            # Minimal re-render: latest-first, unique by key
            try:
                if hasattr(app, 'weather_recent_list'):
                    app.weather_recent_list.delete(0, END)
                    seen_local = set()
                    for nm in reversed(app.weather_recent_cities):
                        k = _city_key(nm)
                        if k in seen_local:
                            continue
                        seen_local.add(k)
                        app.weather_recent_list.insert(END, normalize_city_name(nm))
            except Exception:
                pass
    except Exception:
        pass

    # Hide suggestions popup
    try:
        app.weather_suggest_frame.pack_forget()
    except Exception:
        pass

    # Worker for background fetch
    def worker_fetch():
        try:
            base_units = 'metric'  # canonical fetch units for consistent local conversion
            raw_current_display, forecast_metric = weather_cached_fetch(
                app, city_name, base_units, force_refresh=force_refresh
            )

            # Extract numeric state in metric for future instant conversions
            app.weather_numeric_state = extract_numeric_state(raw_current_display, base_units)

            # Ensure we have some forecast points (fallback to wttr or synthesize)
            if forecast_metric is None:
                forecast_metric = wttr_get_forecast(city_name)
            app.weather_forecast_metric = ensure_forecast_data(
                forecast_metric, city_name, app.weather_numeric_state
            )

            # Build display in the currently selected UI units without re-fetch
            current_filled = build_display_from_numeric(app.weather_numeric_state, app.weather_units)
            converted_forecast = convert_forecast_units(app.weather_forecast_metric, app.weather_units)

            safe_after(app, 0, lambda: weather_update_ui(app, city_name, current_filled, converted_forecast))
        except Exception:
            safe_after(
                app,
                0,
                lambda: messagebox.showerror(
                    getattr(app, 'title_struct', '') + 'Weather',
                    'Could not fetch weather data. Please try another city.'
                )
            )

    # Run in thread; fallback to sync if thread creation fails
    try:
        threading.Thread(target=worker_fetch, daemon=True).start()
    except Exception:
        try:
            base_units = 'metric'
            raw_current_display, forecast_metric = weather_cached_fetch(
                app, city_name, base_units, force_refresh=force_refresh
            )
            app.weather_numeric_state = extract_numeric_state(raw_current_display, base_units)
            if forecast_metric is None:
                forecast_metric = wttr_get_forecast(city_name)
            app.weather_forecast_metric = ensure_forecast_data(
                forecast_metric, city_name, app.weather_numeric_state
            )
            current_filled = build_display_from_numeric(app.weather_numeric_state, app.weather_units)
            converted_forecast = convert_forecast_units(app.weather_forecast_metric, app.weather_units)
            weather_update_ui(app, city_name, current_filled, converted_forecast)
        except Exception:
            try:
                messagebox.showerror(
                    getattr(app, 'title_struct', '') + 'Weather',
                    'Could not fetch weather data. Please try another city.'
                )
            except Exception:
                pass

def weather_cached_fetch(app, city_name, units, force_refresh=False):
    cache_key = (city_name.lower(), units)
    cache_entry = app.weather_cache.get(cache_key)
    now_time = datetime.now()
    if (not force_refresh) and cache_entry and cache_entry.get('expiry', now_time) > now_time:
        return cache_entry.get('current'), cache_entry.get('forecast')

    current_data = None
    forecast_data = None

    # Primary: OpenWeather API if available
    if app.weather_api_key and requests is not None:
        try:
            current_data = ow_get_current(app, city_name, units)
            forecast_data = ow_get_forecast(app, city_name, units)
        except Exception:
            current_data, forecast_data = None, None

    # Secondary: wttr.in free JSON (no key needed) for rich stats and forecast
    if requests is not None and (current_data is None or forecast_data is None):
        try:
            if current_data is None:
                current_data = wttr_get_current(city_name, units)
            if forecast_data is None:
                forecast_data = wttr_get_forecast(city_name)
        except Exception:
            pass

    # Fallback: minimal
    if current_data is None:
        current_data = legacy_scrape_current_fallback(app, city_name, units)

    expiry_time = now_time + timedelta(minutes=10 if forecast_data is None else 30)
    app.weather_cache[cache_key] = {'expiry': expiry_time, 'current': current_data, 'forecast': forecast_data}
    return current_data, forecast_data


def extract_numeric_state(current_display, source_units='metric'):
    # Parse numeric values from a display dict into a normalized metric-based structure
    d = current_display or {}

    temp_txt = str(d.get('temperature', '')).strip()
    feels_txt = str(d.get('feels_like', '')).strip()

    def parse_temp_to_c(txt):
        if not txt or txt == '-':
            return None
        if txt.endswith('°C'):
            try:
                return float(txt[:-2])
            except Exception:
                return None
        if txt.endswith('°F'):
            val = f_to_c(txt[:-2])
            return float(val) if val is not None else None
        try:
            val = float(txt)
            return val if source_units == 'metric' else (f_to_c(val) or None)
        except Exception:
            return None

    temp_c = parse_temp_to_c(temp_txt)
    feels_c = parse_temp_to_c(feels_txt)
    # If feels is missing but temp exists, echo temp
    if feels_c is None:
        feels_c = temp_c

    # Humidity
    hum_txt = str(d.get('humidity', '')).strip()
    try:
        humidity_pct = int(str(hum_txt).rstrip('%'))
    except Exception:
        humidity_pct = None

    # Wind (normalize to m/s)
    wind_txt = str(d.get('wind', '')).strip()
    wind_ms = None
    try:
        num = ''.join(ch for ch in wind_txt if (ch.isdigit() or ch == '.'))
        numf = float(num)
        wlower = wind_txt.lower()
        if 'mph' in wlower:
            wind_ms = numf / 2.2369362921
        elif 'km/h' in wlower or 'kmph' in wlower:
            wind_ms = (numf * 1000.0) / 3600.0
        else:
            wind_ms = numf  # assume m/s
    except Exception:
        wind_ms = None

    # Visibility (normalize to km)
    vis_txt = str(d.get('visibility', '')).strip()
    visibility_km = None
    try:
        num = ''.join(ch for ch in vis_txt if (ch.isdigit() or ch == '.'))
        numf = float(num)
        if 'mi' in vis_txt.lower():
            visibility_km = numf / 0.621371
        else:
            visibility_km = numf
    except Exception:
        visibility_km = None

    # Pressure (hPa)
    pressure_txt = str(d.get('pressure', '')).strip()
    try:
        pressure_hpa = int(''.join(ch for ch in pressure_txt if ch.isdigit()))
    except Exception:
        pressure_hpa = None

    return {
        'location': d.get('location', ''),
        'time': d.get('time', format_time(datetime.now())),
        'description': d.get('description', ''),
        'temp_c': temp_c,
        'feels_c': feels_c,
        'humidity_pct': humidity_pct,
        'wind_ms': wind_ms,
        'visibility_km': visibility_km,
        'pressure_hpa': pressure_hpa,
        'sunrise': d.get('sunrise', '-'),
        'sunset': d.get('sunset', '-'),
        'icon': d.get('icon', None),
    }


def build_display_from_numeric(numeric, target_units='metric'):
    unit_temp = '°C' if target_units == 'metric' else '°F'

    def fmt_temp_c(val_c):
        if val_c is None:
            return f'-{unit_temp}'
        if target_units == 'metric':
            return f'{round(val_c)}°C'
        f = c_to_f(val_c)
        return f'{round(f) if f is not None else "-"}°F'

    temp_txt = fmt_temp_c(numeric.get('temp_c'))
    feels_txt = fmt_temp_c(numeric.get('feels_c'))

    wind_ms = numeric.get('wind_ms')
    if wind_ms is None:
        wind_txt = '-'
    else:
        if target_units == 'metric':
            wind_txt = f'{round(wind_ms, 1)} m/s'
        else:
            mph = ms_to_mph(wind_ms)
            wind_txt = f'{round(mph, 1) if mph is not None else "-"} mph'

    vis_km = numeric.get('visibility_km')
    if vis_km is None:
        vis_txt = '-'
    else:
        if target_units == 'metric':
            vis_txt = f'{round(vis_km, 1)} km'
        else:
            mi = km_to_miles(vis_km)
            vis_txt = f'{round(mi, 1) if mi is not None else "-"} mi'

    hum_pct = numeric.get('humidity_pct')
    hum_txt = f'{int(hum_pct)}%' if hum_pct is not None else '-'
    pres = numeric.get('pressure_hpa')
    pres_txt = f'{int(pres)} hPa' if pres is not None else '-'

    return {
        'location': numeric.get('location', '-'),
        'time': numeric.get('time', format_time(datetime.now())),
        'description': (numeric.get('description') or '-') if numeric.get('description') else '-',
        'temperature': temp_txt,
        'feels_like': feels_txt,
        'pressure': pres_txt,
        'visibility': vis_txt,
        'humidity': hum_txt,
        'wind': wind_txt,
        'sunrise': numeric.get('sunrise', '-'),
        'sunset': numeric.get('sunset', '-'),
        'icon': numeric.get('icon', None),
    }


def convert_forecast_units(forecast_metric, target_units='metric'):
    # Accepts OW-like {'list': [{'dt_txt', 'main': {'temp': <C>}, 'pop': 0..1}, ...]}
    # Returns the same but with temp converted to desired units (C/F)
    if not forecast_metric or not isinstance(forecast_metric, dict):
        return None
    try:
        out = {'list': []}
        for p in forecast_metric.get('list', []):
            t_c = p.get('main', {}).get('temp', None)
            if t_c is None:
                continue
            t_val = t_c if target_units == 'metric' else c_to_f(t_c)
            out['list'].append({
                'dt_txt': p.get('dt_txt', ''),
                'main': {'temp': t_val},
                'pop': p.get('pop', 0.0),
            })
        return out if out['list'] else None
    except Exception:
        return None


def ensure_forecast_data(forecast_data, city_name, numeric_state):
    # Ensure we have some meaningful forecast structure; if missing, synthesize a simple series.
    if forecast_data and isinstance(forecast_data, dict) and forecast_data.get('list'):
        return forecast_data
    # Synthesize 12 points for next hours using current temp (metric base)
    base_temp_c = numeric_state.get('temp_c') if numeric_state else 20.0
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    points = []
    for i in range(12):
        t = base_temp_c + (i - 3) * 0.2  # gentle variation
        dt_txt = (now + timedelta(hours=i)).strftime('%Y-%m-%d %H:00:00')
        points.append({'dt_txt': dt_txt, 'main': {'temp': t}, 'pop': 0.0})
    return {'list': points}


def weather_render_from_cache(app):
    # Re-render UI and charts using cached raw numeric + forecast in base metric, converting to selected units
    try:
        if not app.weather_numeric_state:
            weather_fetch_async(app, force_refresh=False)
            return
        display_current = build_display_from_numeric(app.weather_numeric_state, app.weather_units)
        forecast_converted = convert_forecast_units(app.weather_forecast_metric, app.weather_units)
        city_name = normalize_city_name(display_current.get('location', ''))
        weather_update_ui(app, city_name or '-', display_current, forecast_converted)
    except Exception:
        pass


def weather_update_ui(app, city_name, current_data, forecast_data):
    # Snapshot previous visible state only when switching to a different city
    try:
        incoming_city_key = _city_key(city_name or current_data.get('location', ''))
        if app.weather_current_city is not None and _city_key(app.weather_current_city) != incoming_city_key:
            # Save previous content as "previous city"
            if app.weather_location_label.cget('text') and app.weather_location_label.cget('text') != 'Location: -':
                app.weather_previous_snapshot = {
                    'city': app.weather_current_city,
                    'loc': app.weather_location_label.cget('text'),
                    'time': app.weather_time_label.cget('text'),
                    'temp': app.weather_temp_label.cget('text'),
                    'desc': app.weather_desc_label.cget('text'),
                    'extra': app.weather_extra_label.cget('text'),
                    'more1': app.weather_more_main_label.cget('text'),
                    'more2': app.weather_more_sun_label.cget('text'),
                    'units': app.weather_units,
                    'forecast': getattr(app, 'weather_last_forecast_for_snapshot', None)
                }
                weather_render_last_tab(app, app.weather_previous_snapshot)
        # Set current city (normalized)
        app.weather_current_city = normalize_city_name(city_name or current_data.get('location', '')) or city_name
    except Exception:
        pass

    # Update labels
    app.weather_location_label.config(text=f'Location: {current_data.get("location", city_name)}')
    app.weather_time_label.config(text=f'Time: {current_data.get("time", "-")}')
    app.weather_temp_label.config(text=f'Temperature: {current_data.get("temperature", "-")}')
    app.weather_desc_label.config(text=f'Condition: {current_data.get("description", "-")}')
    app.weather_extra_label.config(text=f'Wind: {current_data.get("wind", "-")} | Humidity: {current_data.get("humidity", "-")}')
    app.weather_more_main_label.config(
        text=f'Feels like: {current_data.get("feels_like", "-")} | Pressure: {current_data.get("pressure", "-")} | Visibility: {current_data.get("visibility", "-")}'
    )
    app.weather_more_sun_label.config(
        text=f'Sunrise: {current_data.get("sunrise", "-")} | Sunset: {current_data.get("sunset", "-")}'
    )

    # Icon
    icon_code_value = current_data.get('icon')
    if icon_code_value and Image and ImageTk and requests is not None:
        weather_set_icon(app, icon_code_value)
    else:
        app.weather_icon_label.config(image='', text='')

    # Charts (use converted forecast data; if matplotlib missing, show textual summaries)
    if Figure and FigureCanvasTkAgg:
        weather_plot_hourly(app, forecast_data)
        weather_plot_daily(app, forecast_data)
    else:
        render_textual_forecast(app, forecast_data)

    # Ensure minimum readable size after content updated
    _enforce_min_tab_size(app)

    # Remember for snapshot (for next switch)
    app.weather_last_forecast_for_snapshot = forecast_data

def ow_get_current(app, city_name, units):
    if requests is None:
        unit_temp = '°C' if units == 'metric' else '°F'
        return {
            'location': city_name,
            'time': format_time(datetime.now()),
            'description': '-',
            'temperature': f'-{unit_temp}',
            'feels_like': f'-{unit_temp}',
            'pressure': '-',
            'visibility': '-',
            'humidity': '-',
            'wind': '-',
            'sunrise': '-',
            'sunset': '-',
            'icon': None
        }

    params = {'q': city_name, 'appid': app.weather_api_key, 'units': units}
    response = requests.get('https://api.openweathermap.org/data/2.5/weather', params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    response_data = response.json()

    unit_temp = '°C' if units == 'metric' else '°F'
    unit_wind = 'm/s' if units == 'metric' else 'mph'

    wind_speed_value = response_data.get('wind', {}).get('speed', 0)
    try:
        wind_speed_value = round(float(wind_speed_value), 1)
    except Exception:
        pass

    try:
        timezone_offset_seconds = int(response_data.get('timezone', 0))
    except Exception:
        timezone_offset_seconds = 0

    def fmt_timestamp(epoch_value):
        try:
            return datetime.utcfromtimestamp(int(epoch_value) + timezone_offset_seconds).strftime('%H:%M')
        except Exception:
            return '-'

    main_section = response_data.get('main', {})
    visibility_meters = response_data.get('visibility', None)
    visibility_display = f'{round(visibility_meters / 1000, 1)} km' if visibility_meters is not None else '-'

    return {
        'location': f'{response_data.get("name", city_name)}, {response_data.get("sys", {}).get("country", "")}'.strip().strip(','),
        'time': format_time(datetime.now()),
        'description': response_data.get('weather', [{}])[0].get('description', '').title(),
        'temperature': f'{round(main_section.get("temp", 0))}{unit_temp}',
        'feels_like': f'{round(main_section.get("feels_like", 0))}{unit_temp}' if main_section.get('feels_like') is not None else f'-{unit_temp}',
        'pressure': f'{main_section.get("pressure", "-")} hPa',
        'visibility': visibility_display,
        'humidity': f'{main_section.get("humidity", "-")}%',
        'wind': f'{wind_speed_value} {unit_wind}',
        'sunrise': fmt_timestamp(response_data.get('sys', {}).get('sunrise')),
        'sunset': fmt_timestamp(response_data.get('sys', {}).get('sunset')),
        'icon': response_data.get('weather', [{}])[0].get('icon')
    }


def ow_get_forecast(app, city_name, units):
    if not Figure or not FigureCanvasTkAgg or requests is None:
        # We still return None to trigger fallback textual/chart synthesis
        return None
    params = {'q': city_name, 'appid': app.weather_api_key, 'units': units, 'cnt': 24}
    response = requests.get('https://api.openweathermap.org/data/2.5/forecast', params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    # Normalize: ensure 'list' exists
    if not isinstance(data, dict) or 'list' not in data:
        return None
    return data


def wttr_get_current(city_name, units):
    # Free source, no key required
    if requests is None:
        raise RuntimeError('requests not available')
    q = city_name.replace(' ', '+')
    url = f'https://wttr.in/{q}?format=j1'
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    current = (data.get('current_condition') or [{}])[0]
    weather = (data.get('weather') or [{}])[0]
    astronomy = (weather.get('astronomy') or [{}])[0]

    desc = (current.get('weatherDesc') or [{'value': '-'}])[0].get('value', '-')
    temp_c = current.get('temp_C')
    temp_f = current.get('temp_F')
    feels_c = current.get('FeelsLikeC')
    feels_f = current.get('FeelsLikeF')
    pressure_mb = current.get('pressure')  # mb ~ hPa
    visibility_km = current.get('visibility')
    humidity = current.get('humidity')
    wind_kmph = current.get('windspeedKmph')
    sunrise = astronomy.get('sunrise') or current.get('sunrise') or '-'
    sunset = astronomy.get('sunset') or current.get('sunset') or '-'

    if units == 'metric':
        temp_txt = f'{round(float(temp_c)) if temp_c not in (None, "") else 0}°C'
        feels_txt = f'{round(float(feels_c)) if feels_c not in (None, "") else 0}°C'
        wind_ms = None
        try:
            wind_ms = round((float(wind_kmph) * 1000 / 3600), 1)
        except Exception:
            wind_ms = None
        wind_txt = f'{wind_ms} m/s' if wind_ms is not None else '-'
        visibility_txt = f'{round(float(visibility_km), 1)} km' if visibility_km not in (None, '') else '-'
    else:
        temp_txt = f'{round(float(temp_f)) if temp_f not in (None, "") else 0}°F'
        feels_txt = f'{round(float(feels_f)) if feels_f not in (None, "") else 0}°F'
        mph = None
        try:
            mph = round(float(wind_kmph) * 0.621371, 1)
        except Exception:
            mph = None
        wind_txt = f'{mph} mph' if mph is not None else '-'
        try:
            miles = round(float(visibility_km) * 0.621371, 1)
            visibility_txt = f'{miles} mi'
        except Exception:
            visibility_txt = '-'

    pressure_txt = f'{pressure_mb} hPa' if pressure_mb not in (None, '') else '-'
    humidity_txt = f'{humidity}%' if humidity not in (None, '') else '-'

    return {
        'location': city_name,
        'time': format_time(datetime.now()),
        'description': desc.title() if isinstance(desc, str) else '-',
        'temperature': temp_txt,
        'feels_like': feels_txt,
        'pressure': pressure_txt,
        'visibility': visibility_txt,
        'humidity': humidity_txt,
        'wind': wind_txt,
        'sunrise': sunrise,
        'sunset': sunset,
        'icon': None  # wttr provides icon urls in other endpoints; keep None here
    }


def wttr_get_forecast(city_name):
    # Returns OW-like dict with 'list' entries at hourly steps in metric (Celsius, km-based), for fallback charts
    if requests is None:
        return None
    try:
        q = city_name.replace(' ', '+')
        url = f'https://wttr.in/{q}?format=j1'
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        days = data.get('weather') or []
        list_points = []
        for day in days[:2]:
            date_str = day.get('date', '')
            for h in day.get('hourly', []):
                time_val = h.get('time', '0')
                try:
                    minutes = int(time_val)
                except Exception:
                    minutes = 0
                hh = (minutes // 100) % 24
                dt_txt = f'{date_str} {hh:02d}:00:00'
                # tempC is string in wttr
                try:
                    temp_c = float(h.get('tempC')) if h.get('tempC') is not None else float(h.get('temp_C') or 0)
                except Exception:
                    temp_c = 0.0
                try:
                    pop = float(h.get('chanceofrain') or h.get('chanceofprecip') or 0) / 100.0
                except Exception:
                    pop = 0.0
                list_points.append({'dt_txt': dt_txt, 'main': {'temp': temp_c}, 'pop': pop})
        # Keep at most 24 points
        return {'list': list_points[:24]} if list_points else None
    except Exception:
        return None


def weather_set_icon(app, icon_code):
    try:
        if requests is None or not Image or not ImageTk:
            raise RuntimeError('icon prerequisites missing')
        icon_url = f'https://openweathermap.org/img/wn/{icon_code}@2x.png'
        icon_response = requests.get(icon_url, timeout=REQUEST_TIMEOUT)
        icon_response.raise_for_status()
        # Load image fully, then close buffers to avoid resource warnings
        with BytesIO(icon_response.content) as bio:
            image_object = Image.open(bio)
            image_object.load()
        with BytesIO(icon_response.content) as bio2:
            image_object2 = Image.open(bio2)
            photo_image = ImageTk.PhotoImage(image_object2, master=app.weather_root)
        app.weather_icon_label.config(image=photo_image)
        app.weather_icon_label.image = photo_image
    except Exception:
        app.weather_icon_label.config(image='', text='')


def clear_canvas(existing_canvas, parent_frame):
    if existing_canvas:
        try:
            existing_canvas.get_tk_widget().destroy()
        except Exception:
            pass


# --- Responsive helpers for matplotlib canvases & tab sizing ---
def _initial_fig_size_for(parent_widget, dpi=100, min_w=420, min_h=220, pad=16):
    try:
        parent_widget.update_idletasks()
        w = max(parent_widget.winfo_width() - pad, min_w)
        h = max(parent_widget.winfo_height() - pad, min_h)
    except Exception:
        w, h = min_w, min_h
    return (w / dpi, h / dpi), dpi


def _attach_responsive_resize(tab_widget, canvas):
    # Resize the figure when tab is resized; debounce to avoid redraw storms
    try:
        if not hasattr(tab_widget, '_resize_job'):
            tab_widget._resize_job = None
    except Exception:
        pass

    def _on_configure(event=None):
        try:
            if tab_widget._resize_job:
                tab_widget.after_cancel(tab_widget._resize_job)
        except Exception:
            pass

        def _do():
            try:
                fig = canvas.figure
                widget = canvas.get_tk_widget()
                # Compute new size
                new_w = max(tab_widget.winfo_width() - 16, 240)
                new_h = max(tab_widget.winfo_height() - 16, 160)
                dpi = fig.get_dpi() or 100
                fig.set_size_inches(new_w / dpi, new_h / dpi, forward=True)
                try:
                    fig.tight_layout()
                except Exception:
                    pass
                canvas.draw_idle()
                # Ensure the canvas widget fills the tab
                try:
                    widget.grid(row=0, column=0, sticky='nsew')
                except Exception:
                    pass
            except Exception:
                pass
            finally:
                try:
                    tab_widget._resize_job = None
                except Exception:
                    pass

        try:
            tab_widget._resize_job = tab_widget.after(120, _do)
        except Exception:
            _do()

    try:
        tab_widget.bind('<Configure>', _on_configure)
    except Exception:
        pass


def _enforce_min_tab_size(app, *, min_w=820, min_h=560, center=False):
    '''Guarantee the weather popup is large enough so tab content is readable.'''
    try:
        root = getattr(app, 'weather_root', None)
        if not root or not root.winfo_exists():
            return
        # Apply minimum size constraints
        try:
            root.minsize(min_w, min_h)
        except Exception:
            pass

        # If current size is smaller, grow it (optionally keep centered relative to app)
        try:
            root.update_idletasks()
            cur_w, cur_h = root.winfo_width(), root.winfo_height()
            if cur_w < min_w or cur_h < min_h:
                new_w = max(cur_w, min_w)
                new_h = max(cur_h, min_h)
                if center:
                    try:
                        app_x, app_y = app.winfo_x(), app.winfo_y()
                        app_w, app_h = app.winfo_width(), app.winfo_height()
                        pos_x = int(app_x + (app_w / 2) - (new_w / 2))
                        pos_y = int(app_y + (app_h / 2) - (new_h / 2))
                        root.geometry(f'{new_w}x{new_h}+{pos_x}+{pos_y}')
                    except Exception:
                        root.geometry(f'{new_w}x{new_h}')
                else:
                    root.geometry(f'{new_w}x{new_h}')
        except Exception:
            pass
    except Exception:
        pass
# ... existing code ...


def render_textual_forecast(app, forecast_data):
    # When matplotlib is not available, show a simple textual preview
    try:
        # Clear tabs
        for child in app.weather_hourly_tab.winfo_children():
            child.destroy()
        for child in app.weather_daily_tab.winfo_children():
            child.destroy()
        if not forecast_data or not forecast_data.get('list'):
            Label(app.weather_hourly_tab, text='No forecast data available.').grid(row=0, column=0, sticky='nw', padx=6, pady=6)
            Label(app.weather_daily_tab, text='No forecast data available.').grid(row=0, column=0, sticky='nw', padx=6, pady=6)
            _enforce_min_tab_size(app)
            return
        # Hourly: next 6 entries
        Label(app.weather_hourly_tab, text='Hourly (textual preview):').grid(row=0, column=0, sticky='nw', padx=6, pady=(6, 2))
        row_i = 1
        for p in forecast_data.get('list', [])[:6]:
            ts = p.get('dt_txt', '').split(' ')[1][:5]
            t = p.get('main', {}).get('temp', '-')
            Label(app.weather_hourly_tab, text=f'{ts}  {round(t,1) if isinstance(t,(int,float)) else t}').grid(row=row_i, column=0, sticky='nw', padx=12)
            row_i += 1
        # Daily: group by date
        grouped = {}
        for p in forecast_data.get('list', []):
            day = p.get('dt_txt', '').split(' ')[0]
            grouped.setdefault(day, []).append(p.get('main', {}).get('temp', None))
        Label(app.weather_daily_tab, text='Daily (textual preview):').grid(row=0, column=0, sticky='nw', padx=6, pady=(6, 2))
        row_j = 1
        for day, vals in list(grouped.items())[:5]:
            vals = [v for v in vals if isinstance(v, (int, float))]
            if not vals:
                continue
            Label(
                app.weather_daily_tab,
                text=f'{day}: min {round(min(vals),1)}, avg {round(sum(vals)/len(vals),1)}, max {round(max(vals),1)}'
            ).grid(row=row_j, column=0, sticky='nw', padx=12)
            row_j += 1
        _enforce_min_tab_size(app)
    except Exception:
        pass


def weather_plot_hourly(app, forecast_data):
    if not forecast_data or not Figure or not FigureCanvasTkAgg:
        return
    clear_canvas(app.weather_hourly_canvas, app.weather_hourly_tab)
    try:
        forecast_points = forecast_data.get('list', [])[:12]
        if not forecast_points:
            # Fallback label (grid)
            Label(app.weather_hourly_tab, text='No hourly data.').grid(row=0, column=0, sticky='nw', padx=6, pady=6)
            _enforce_min_tab_size(app)
            return

        # Size figure to current tab; it will keep responsive via resize binding
        figsize, dpi = _initial_fig_size_for(app.weather_hourly_tab, dpi=100)

        figure_object = Figure(figsize=figsize, dpi=dpi)
        axis_left = figure_object.add_subplot(111)

        axis_labels = [point.get('dt_txt', '').split(' ')[1][:5] for point in forecast_points]
        temperature_values = [point.get('main', {}).get('temp', 0) for point in forecast_points]
        precipitation_percentages = [round(float(point.get('pop', 0) or 0) * 100) for point in forecast_points]

        axis_left.plot(axis_labels, temperature_values, color='#d9480f', marker='o', label='Temp')
        axis_left.set_ylabel('Temp ' + ('°C' if app.weather_units == 'metric' else '°F'))
        axis_left.grid(True, alpha=0.3)

        axis_right = axis_left.twinx()
        axis_right.bar(axis_labels, precipitation_percentages, alpha=0.25, color='#1e88e5', label='PoP %')
        axis_right.set_ylabel('Precip %')
        axis_right.set_ylim(0, 100)

        left_lines, left_labels = axis_left.get_legend_handles_labels()
        right_lines, right_labels = axis_right.get_legend_handles_labels()
        axis_left.legend(left_lines + right_lines, left_labels + right_labels, loc='upper left')
        axis_left.set_title('Next hours')
        try:
            figure_object.tight_layout()
        except Exception:
            pass

        canvas_object = FigureCanvasTkAgg(figure_object, master=app.weather_hourly_tab)
        widget = canvas_object.get_tk_widget()
        # Grid for responsiveness
        app.weather_hourly_tab.grid_rowconfigure(0, weight=1)
        app.weather_hourly_tab.grid_columnconfigure(0, weight=1)
        widget.grid(row=0, column=0, sticky='nsew')
        canvas_object.draw()

        # Attach resize behavior
        _attach_responsive_resize(app.weather_hourly_tab, canvas_object)

        app.weather_hourly_canvas = canvas_object

        # Guarantee readability
        _enforce_min_tab_size(app)
    except Exception:
        pass


def weather_plot_daily(app, forecast_data):
    if not forecast_data or not Figure or not FigureCanvasTkAgg:
        return
    clear_canvas(app.weather_daily_canvas, app.weather_daily_tab)
    try:
        forecast_points = forecast_data.get('list', [])
        if not forecast_points:
            Label(app.weather_daily_tab, text='No daily data.').grid(row=0, column=0, sticky='nw', padx=6, pady=6)
            _enforce_min_tab_size(app)
            return

        grouped_by_day = {}
        for point in forecast_points:
            date_text = point.get('dt_txt', '')
            day_key = date_text.split(' ')[0] if ' ' in date_text else date_text
            grouped_by_day.setdefault(day_key, []).append(point.get('main', {}).get('temp', 0))

        sorted_days = sorted(grouped_by_day.keys())[:5]
        if not sorted_days:
            Label(app.weather_daily_tab, text='No daily data.').grid(row=0, column=0, sticky='nw', padx=6, pady=6)
            _enforce_min_tab_size(app)
            return

        axis_labels = [day_value[5:] for day_value in sorted_days]  # MM-DD
        daily_avg = [round(sum(grouped_by_day[day_key]) / max(len(grouped_by_day[day_key]), 1), 1) for day_key in sorted_days]
        daily_min = [round(min(grouped_by_day[day_key]), 1) for day_key in sorted_days]
        daily_max = [round(max(grouped_by_day[day_key]), 1) for day_key in sorted_days]

        figsize, dpi = _initial_fig_size_for(app.weather_daily_tab, dpi=100)
        figure_object = Figure(figsize=figsize, dpi=dpi)
        axis_object = figure_object.add_subplot(111)
        axis_object.fill_between(axis_labels, daily_min, daily_max, color='#90caf9', alpha=0.35, label='Min–Max')
        axis_object.plot(axis_labels, daily_avg, color='#0d47a1', marker='o', label='Avg')
        axis_object.set_title('Next days')
        axis_object.set_ylabel('Temp ' + ('°C' if app.weather_units == 'metric' else '°F'))
        axis_object.grid(True, alpha=0.3)
        axis_object.legend(loc='upper left')
        try:
            figure_object.tight_layout()
        except Exception:
            pass

        canvas_object = FigureCanvasTkAgg(figure_object, master=app.weather_daily_tab)
        widget = canvas_object.get_tk_widget()
        app.weather_daily_tab.grid_rowconfigure(0, weight=1)
        app.weather_daily_tab.grid_columnconfigure(0, weight=1)
        widget.grid(row=0, column=0, sticky='nsew')
        canvas_object.draw()

        _attach_responsive_resize(app.weather_daily_tab, canvas_object)

        app.weather_daily_canvas = canvas_object

        # Guarantee readability
        _enforce_min_tab_size(app)
    except Exception:
        pass


def weather_render_last_tab(app, snapshot_data):
    # Use latest previous snapshot if none provided
    if not snapshot_data:
        snapshot_data = getattr(app, 'weather_previous_snapshot', None)

    # If no snapshot or snapshot city equals current city -> friendly message
    try:
        cur_city_key = _city_key(getattr(app, 'weather_current_city', '') or '')
        snap_city_key = _city_key(snapshot_data.get('city', '')) if snapshot_data else ''
        if (not snapshot_data) or (cur_city_key and cur_city_key == snap_city_key):
            for child_widget in app.weather_last_tab.winfo_children():
                child_widget.destroy()
            Label(
                app.weather_last_tab,
                text='No previous city yet.\nSearch a different city to see it here.',
                justify='left'
            ).grid(row=0, column=0, sticky='nw', padx=6, pady=6)
            return
    except Exception:
        pass

    # Clear existing content
    if app.weather_last_canvas:
        try:
            app.weather_last_canvas.get_tk_widget().destroy()
        except Exception:
            pass
        app.weather_last_canvas = None
    try:
        for child_widget in app.weather_last_tab.winfo_children():
            child_widget.destroy()
    except Exception:
        pass

    # Summary
    summary_text = '\n'.join([
        snapshot_data.get('loc', 'Location: -'),
        snapshot_data.get('time', 'Time: -'),
        snapshot_data.get('temp', 'Temperature: -'),
        snapshot_data.get('desc', 'Condition: -'),
        snapshot_data.get('extra', 'Wind: - | Humidity: -'),
        snapshot_data.get('more1', 'Feels like: - | Pressure: - | Visibility: -'),
        snapshot_data.get('more2', 'Sunrise: - | Sunset: -'),
    ])
    Label(app.weather_last_tab, text=summary_text, justify='left').grid(row=0, column=0, sticky='nw', padx=6, pady=6)

    # Actions row: restore button
    def restore_previous_city():
        try:
            prev_city = snapshot_data.get('city') or ''
            if prev_city:
                app.weather_entry.delete(0, END)
                app.weather_entry.insert(0, prev_city)
                weather_fetch_async(app, force_refresh=False)
        except Exception:
            pass

    btn_frame = Frame(app.weather_last_tab)
    btn_frame.grid(row=1, column=0, sticky='w', padx=6, pady=(4, 2))
    Button(btn_frame, text='Use previous city', bd=1, command=restore_previous_city).pack(side='left')

    # Forecast preview (if any)
    forecast_data = snapshot_data.get('forecast')
    if forecast_data and Figure and FigureCanvasTkAgg:
        try:
            points = forecast_data.get('list', [])[:12]
            if points:
                axis_labels = [point.get('dt_txt', '').split(' ')[1][:5] for point in points]
                values = [point.get('main', {}).get('temp', 0) for point in points]
                figure_object = Figure(figsize=(5.6, 2.2), dpi=100)
                axis_object = figure_object.add_subplot(111)
                axis_object.plot(axis_labels, values, marker='o', color='#6a1b9a')
                axis_object.set_title('Previous city: next hours')
                axis_object.set_ylabel('Temp ' + ('°C' if snapshot_data.get('units') == 'metric' else '°F'))
                axis_object.grid(True, alpha=0.3)
                try:
                    figure_object.tight_layout()
                except Exception:
                    pass
                canvas_object = FigureCanvasTkAgg(figure_object, master=app.weather_last_tab)
                widget = canvas_object.get_tk_widget()
                app.weather_last_tab.grid_rowconfigure(2, weight=1)
                app.weather_last_tab.grid_columnconfigure(0, weight=1)
                widget.grid(row=2, column=0, sticky='nsew', padx=4, pady=4)
                canvas_object.draw()
                app.weather_last_canvas = canvas_object
        except Exception:
            pass


def legacy_scrape_current_fallback(app, city_name, units):
    # Minimal, resilient fallback when all other sources are not available
    unit_temp = '°C' if units == 'metric' else '°F'
    return {
        'location': city_name,
        'time': format_time(datetime.now()),
        'description': '-',
        'temperature': f'-{unit_temp}',
        'feels_like': f'-{unit_temp}',
        'pressure': '-',
        'visibility': '-',
        'humidity': '-',
        'wind': '-',
        'sunrise': '-',
        'sunset': '-',
        'icon': None
    }
