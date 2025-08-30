# Python
import tkinter as tk
from tkinter import ttk, messagebox
import colorsys
from datetime import datetime, time, timedelta
import importlib.util, importlib

try:
    import names as names_lib  # optional dependency
except Exception:
    names_lib = None


def is_valid_int_string(candidate_text: str) -> bool:
    candidate_text = candidate_text.strip()
    if candidate_text == '':
        return True
    if candidate_text.startswith('-'):
        candidate_text = candidate_text[1:]
    return candidate_text.isdigit()


def get_popup_window(app, title: str):
    make_window = getattr(app, 'make_pop_ups_window', None)
    if callable(make_window):
        try:
            return make_window(lambda: None, custom_title=(title))
        except Exception:
            pass
    parent_widget = getattr(app, 'tk', None) or getattr(app, 'root', None)
    if not isinstance(parent_widget, tk.Misc):
        parent_widget = tk._get_default_root() or tk.Tk()
    popup_window = tk.Toplevel(parent_widget)
    popup_window.title(getattr(app, 'title_struct', '') + title)
    return popup_window


def insert_into_editor(app, value_string: str):
    try:
        app.EgonTE.insert(app.get_pos(), value_string)
    except Exception:
        app.EgonTE.insert('end', value_string)


def rng_randint_inclusive(app, low_value: int, high_value: int) -> int:
    rng_object = getattr(app, 'rng', None)
    try:
        if hasattr(rng_object, 'integers'):
            return int(rng_object.integers(low_value, high_value + 1))
    except Exception:
        pass
    try:
        return rng_object.randint(low_value, high_value)  # type: ignore[attr-defined]
    except Exception:
        import random as std_random
        return std_random.randint(low_value, high_value)


def rng_random_unit_interval(app) -> float:
    rng_object = getattr(app, 'rng', None)
    try:
        if hasattr(rng_object, 'random'):
            return float(rng_object.random())
    except Exception:
        pass
    try:
        return float(rng_object.random())  # type: ignore[attr-defined]
    except Exception:
        import random as std_random
        return std_random.random()


def rng_choice_one(app, sequence):
    if not sequence:
        raise ValueError('empty sequence')
    rng_object = getattr(app, 'rng', None)
    try:
        if hasattr(rng_object, 'choice'):
            return rng_object.choice(sequence)
    except Exception:
        pass
    try:
        return rng_object.choice(sequence)  # type: ignore[attr-defined]
    except Exception:
        import random as std_random
        return std_random.choice(sequence)


def rng_sample_k(app, sequence, sample_size: int):
    if sample_size < 0:
        raise ValueError('sample size must be non-negative')
    if sample_size > len(sequence):
        raise ValueError('sample size larger than population')
    rng_object = getattr(app, 'rng', None)
    try:
        if hasattr(rng_object, 'choice'):
            return list(rng_object.choice(sequence, size=sample_size, replace=False))
    except Exception:
        pass
    try:
        return rng_object.sample(sequence, sample_size)  # type: ignore[attr-defined]
    except Exception:
        import random as std_random
        return std_random.sample(sequence, sample_size)


def rng_shuffled(app, sequence):
    rng_object = getattr(app, 'rng', None)
    try:
        if hasattr(rng_object, 'permutation'):
            return list(rng_object.permutation(sequence))
    except Exception:
        pass
    try:
        sequence_copy = list(sequence)
        rng_object.shuffle(sequence_copy)  # type: ignore[attr-defined]
        return sequence_copy
    except Exception:
        import random as std_random
        sequence_copy = list(sequence)
        std_random.shuffle(sequence_copy)
        return sequence_copy


def open_random(app):
    '''
    Unified random tool:
    - Numbers: random int (range) with previews and spinners, quick float with decimals, quick int.
    - Names: full/first/last, optional gender.
    - Colors: random HEX/RGB/HSL, preview, palette generation (scheme + size), copy as CSS var(s).
    - Lists: choice, sample (k, no replacement), shuffle.
    - Sequence: random string generator (length, flexible charset, inline preview, insert/copy/clear).
    - Dates and times: random date/time in a range with format presets, quick 'today + N days' range.
    '''
    tool_root = get_popup_window(app, 'Randomness generators')
    try:
        tool_root.grid_columnconfigure(0, weight=1)
        tool_root.grid_rowconfigure(1, weight=1)
    except Exception:
        pass

    header_label = ttk.Label(tool_root, text='Randomness generators', anchor='center')
    header_label.grid(row=0, column=0, padx=10, pady=(10, 6), sticky='ew')

    tabs_notebook = ttk.Notebook(tool_root)
    tabs_notebook.grid(row=1, column=0, padx=10, pady=(0, 10), sticky='nsew')

    # Numbers tab
    numbers_tab = ttk.Frame(tabs_notebook)
    tabs_notebook.add(numbers_tab, text='Numbers')
    for numbers_column_index in range(3):
        numbers_tab.grid_columnconfigure(numbers_column_index, weight=1)

    numbers_title_label = ttk.Label(numbers_tab, text='Random numbers', anchor='center')
    numbers_title_label.grid(row=0, column=0, columnspan=3, pady=(10, 6), sticky='ew')

    validate_integer_command = (numbers_tab.register(is_valid_int_string), '%P')
    numbers_lower_bound_var = tk.StringVar()
    numbers_upper_bound_var = tk.StringVar()

    spinbox_factory = getattr(ttk, 'Spinbox', None)

    def make_spinbox(parent_widget, variable, from_value, to_value, step=1, width=12, validate_cmd=None):
        if spinbox_factory is not None:
            return ttk.Spinbox(
                parent_widget,
                textvariable=variable,
                from_=from_value,
                to=to_value,
                increment=step,
                width=width,
                wrap=False,
                validate='key',
                validatecommand=validate_cmd or (parent_widget.register(is_valid_int_string), '%P'),
            )
        return tk.Spinbox(
            parent_widget,
            textvariable=variable,
            from_=from_value,
            to=to_value,
            increment=step,
            width=width,
            wrap=False,
            validate='key',
            validatecommand=validate_cmd or (parent_widget.register(is_valid_int_string), '%P'),
            justify='left',
        )

    numbers_lower_bound_spinner = make_spinbox(
        numbers_tab, numbers_lower_bound_var, -1000000, 1000000, 1, 12, validate_integer_command
    )
    numbers_upper_bound_spinner = make_spinbox(
        numbers_tab, numbers_upper_bound_var, -1000000, 1000000, 1, 12, validate_integer_command
    )
    numbers_between_label = ttk.Label(numbers_tab, text='Between')

    numbers_lower_bound_spinner.grid(row=1, column=0, padx=(10, 4), pady=(0, 8), sticky='ew')
    numbers_between_label.grid(row=1, column=1, padx=4, pady=(0, 8))
    numbers_upper_bound_spinner.grid(row=1, column=2, padx=(4, 10), pady=(0, 8), sticky='ew')

    # Float decimals spinner
    float_decimals_var = tk.StringVar(value='8')
    float_decimals_label = ttk.Label(numbers_tab, text='Float decimals:')
    float_decimals_spinner = make_spinbox(
        numbers_tab, float_decimals_var, 0, 12, 1, 6, (numbers_tab.register(is_valid_int_string), '%P')
    )

    float_decimals_label.grid(row=2, column=0, padx=(10, 4), pady=(0, 6), sticky='w')
    float_decimals_spinner.grid(row=2, column=1, padx=(4, 4), pady=(0, 6), sticky='w')

    # Previews and actions
    generated_integer_var = tk.StringVar(value='')
    current_integer_label = ttk.Label(numbers_tab, text='Current int:')
    current_integer_value_label = ttk.Label(numbers_tab, textvariable=generated_integer_var, font=('Arial', 10, 'bold'))
    reroll_integer_button = ttk.Button(numbers_tab, text='Re-roll int')
    insert_integer_button = ttk.Button(numbers_tab, text='Insert int')

    current_integer_label.grid(row=3, column=0, padx=(10, 4), pady=(0, 6), sticky='w')
    current_integer_value_label.grid(row=3, column=1, padx=(4, 4), pady=(0, 6), sticky='w')
    reroll_integer_button.grid(row=3, column=2, padx=(4, 10), pady=(0, 6), sticky='ew')
    insert_integer_button.grid(row=4, column=2, padx=(4, 10), pady=(0, 8), sticky='ew')

    generated_float_var = tk.StringVar(value='')
    current_float_label = ttk.Label(numbers_tab, text='Current float:')
    current_float_value_label = ttk.Label(numbers_tab, textvariable=generated_float_var, font=('Arial', 10, 'bold'))
    reroll_float_button = ttk.Button(numbers_tab, text='Re-roll float')
    insert_float_button = ttk.Button(numbers_tab, text='Insert float')

    current_float_label.grid(row=5, column=0, padx=(10, 4), pady=(4, 6), sticky='w')
    current_float_value_label.grid(row=5, column=1, padx=(4, 4), pady=(4, 6), sticky='w')
    reroll_float_button.grid(row=5, column=2, padx=(4, 10), pady=(4, 6), sticky='ew')
    insert_float_button.grid(row=6, column=2, padx=(4, 10), pady=(0, 8), sticky='ew')

    generated_quick_int_var = tk.StringVar(value='')
    current_quick_int_label = ttk.Label(numbers_tab, text='Current quick int:')
    current_quick_int_value_label = ttk.Label(numbers_tab, textvariable=generated_quick_int_var, font=('Arial', 10, 'bold'))
    reroll_quick_int_button = ttk.Button(numbers_tab, text='Re-roll quick int')
    insert_quick_int_button = ttk.Button(numbers_tab, text='Insert quick int')

    current_quick_int_label.grid(row=7, column=0, padx=(10, 4), pady=(4, 6), sticky='w')
    current_quick_int_value_label.grid(row=7, column=1, padx=(4, 4), pady=(4, 6), sticky='w')
    reroll_quick_int_button.grid(row=7, column=2, padx=(4, 10), pady=(4, 6), sticky='ew')
    insert_quick_int_button.grid(row=8, column=2, padx=(4, 10), pady=(0, 10), sticky='ew')

    def validate_range_fields():
        try:
            lower_value = int(numbers_lower_bound_var.get().strip())
            upper_value = int(numbers_upper_bound_var.get().strip())
        except ValueError:
            messagebox.showerror(getattr(app, 'title_struct', '') + ' error', 'Please enter valid integers for range.')
            return None
        if lower_value > upper_value:
            lower_value, upper_value = upper_value, lower_value
        return lower_value, upper_value

    def get_float_decimals() -> int:
        try:
            decimals_count = int(float_decimals_var.get().strip() or '8')
        except ValueError:
            decimals_count = 8
        return max(0, min(12, decimals_count))

    def handle_reroll_integer(_event=None):
        bounds = validate_range_fields()
        if bounds is None:
            return 'break'
        lower_value, upper_value = bounds
        try:
            integer_value = rng_randint_inclusive(app, lower_value, upper_value)
        except Exception as exception:
            messagebox.showerror(getattr(app, 'title_struct', '') + ' error', f'Invalid range: {exception}')
            return 'break'
        generated_integer_var.set(str(integer_value))
        return 'break'

    def handle_insert_integer(_event=None):
        integer_text = generated_integer_var.get().strip()
        if integer_text == '':
            if handle_reroll_integer() == 'break':
                return 'break'
            integer_text = generated_integer_var.get().strip()
        insert_into_editor(app, integer_text + ' ')
        return 'break'

    def handle_reroll_float(_event=None):
        decimals_count = get_float_decimals()
        float_text = f'{rng_random_unit_interval(app):.{decimals_count}f}'
        generated_float_var.set(float_text)
        return 'break'

    def handle_insert_float(_event=None):
        float_text = generated_float_var.get().strip()
        if float_text == '':
            handle_reroll_float()
            float_text = generated_float_var.get().strip()
        insert_into_editor(app, float_text + ' ')
        return 'break'

    def handle_reroll_quick_int(_event=None):
        quick_integer_text = str(rng_randint_inclusive(app, 0, 9999))
        generated_quick_int_var.set(quick_integer_text)
        return 'break'

    def handle_insert_quick_int(_event=None):
        quick_integer_text = generated_quick_int_var.get().strip()
        if quick_integer_text == '':
            handle_reroll_quick_int()
            quick_integer_text = generated_quick_int_var.get().strip()
        insert_into_editor(app, quick_integer_text + ' ')
        return 'break'

    reroll_integer_button.configure(command=handle_reroll_integer)
    insert_integer_button.configure(command=handle_insert_integer)
    reroll_float_button.configure(command=handle_reroll_float)
    insert_float_button.configure(command=handle_insert_float)
    reroll_quick_int_button.configure(command=handle_reroll_quick_int)
    insert_quick_int_button.configure(command=handle_insert_quick_int)

    # Prefill and initial previews
    try:
        if hasattr(app, 'is_marked') and app.is_marked():
            selected_text_parts = app.EgonTE.get('sel.first', 'sel.last').split()
            if len(selected_text_parts) >= 1:
                try:
                    numbers_lower_bound_var.set(str(int(selected_text_parts[0])))
                except Exception:
                    pass
            if len(selected_text_parts) >= 2:
                try:
                    numbers_upper_bound_var.set(str(int(selected_text_parts[1])))
                except Exception:
                    pass
        elif getattr(app, 'fun_numbers', None) and app.fun_numbers.get():
            default_lower_bound = rng_randint_inclusive(app, 1, 10)
            default_upper_bound = rng_randint_inclusive(app, 10, 1000)
            if default_lower_bound > default_upper_bound:
                default_lower_bound, default_upper_bound = default_upper_bound, default_lower_bound
            numbers_lower_bound_var.set(str(default_lower_bound))
            numbers_upper_bound_var.set(str(default_upper_bound))
    except Exception:
        pass

    handle_reroll_integer()
    handle_reroll_float()
    handle_reroll_quick_int()

    # Names tab
    names_tab = ttk.Frame(tabs_notebook)
    tabs_notebook.add(names_tab, text='Names')
    for names_column_index in range(2):
        names_tab.grid_columnconfigure(names_column_index, weight=1)

    names_title_label = ttk.Label(names_tab, text='Random names', anchor='center')
    names_title_label.grid(row=0, column=0, columnspan=2, pady=(10, 6), sticky='ew')

    generated_name_var = tk.StringVar()
    try:
        if names_lib is not None:
            generated_name_var.set(names_lib.get_full_name())
        else:
            generated_name_var.set('')
    except Exception:
        generated_name_var.set('')

    generated_name_label = ttk.Label(names_tab, text='Generated name:')
    generated_name_value_label = ttk.Label(names_tab, textvariable=generated_name_var, font=('Arial', 10, 'bold'))
    generated_name_label.grid(row=1, column=0, columnspan=2, padx=10, sticky='w')
    generated_name_value_label.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 8), sticky='w')

    name_gender_var = tk.StringVar(value='Any')
    name_type_var = tk.StringVar(value='Full Name')
    gender_select = ttk.Combobox(names_tab, width=14, textvariable=name_gender_var, state='readonly',
                                 values=('Any', 'Male', 'Female'))
    name_type_select = ttk.Combobox(names_tab, width=14, textvariable=name_type_var, state='readonly',
                                    values=('Full Name', 'First Name', 'Last Name'))
    gender_select.grid(row=3, column=0, padx=(10, 5), pady=(0, 8), sticky='w')
    name_type_select.grid(row=3, column=1, padx=(5, 10), pady=(0, 8), sticky='e')

    def handle_roll_name(_event=None):
        if names_lib is None:
            generated_name_var.set('')
            return 'break'
        selected_gender = name_gender_var.get()
        normalized_gender = None if selected_gender == 'Any' else selected_gender.lower()
        selected_name_type = name_type_var.get()
        if selected_name_type == 'Last Name':
            value_to_set = names_lib.get_last_name()
        elif selected_name_type == 'First Name':
            try:
                full_name = names_lib.get_full_name(gender=normalized_gender) if normalized_gender else names_lib.get_full_name()
                value_to_set = full_name.split(' ', 1)[0] if full_name else ''
            except Exception:
                value_to_set = ''
        else:
            try:
                value_to_set = names_lib.get_full_name(gender=normalized_gender) if normalized_gender else names_lib.get_full_name()
            except Exception:
                value_to_set = ''
        generated_name_var.set(value_to_set)
        return 'break'

    def handle_insert_name(_event=None):
        insert_into_editor(app, generated_name_var.get() + ' ')
        return 'break'

    def handle_copy_name(_event=None):
        try:
            tool_root.clipboard_clear()
            tool_root.clipboard_append(generated_name_var.get())
        except Exception:
            pass
        return 'break'

    reroll_name_button = ttk.Button(names_tab, text='Re-roll', command=handle_roll_name)
    insert_name_button = ttk.Button(names_tab, text='Insert', command=handle_insert_name)
    copy_name_button = ttk.Button(names_tab, text='Copy', command=handle_copy_name)
    reroll_name_button.grid(row=4, column=0, padx=(10, 5), pady=(0, 10), sticky='ew')
    insert_name_button.grid(row=4, column=1, padx=(5, 10), pady=(0, 10), sticky='ew')
    copy_name_button.grid(row=5, column=0, columnspan=2, padx=10, pady=(0, 10), sticky='ew')

    # Colors tab
    colors_tab = ttk.Frame(tabs_notebook)
    tabs_notebook.add(colors_tab, text='Colors')
    for colors_column_index in range(4):
        colors_tab.grid_columnconfigure(colors_column_index, weight=1)

    colors_title_label = ttk.Label(colors_tab, text='Random color and palettes', anchor='center')
    colors_title_label.grid(row=0, column=0, columnspan=4, pady=(10, 6), sticky='ew')

    color_string_var = tk.StringVar()
    uppercase_hex_var = tk.BooleanVar(value=False)
    include_hash_var = tk.BooleanVar(value=True)
    color_format_var = tk.StringVar(value='HEX')

    color_preview_canvas = tk.Canvas(colors_tab, width=64, height=24, highlightthickness=1, relief='solid')
    color_value_label = ttk.Label(colors_tab, textvariable=color_string_var, font=('Arial', 10, 'bold'))

    current_red_value = {'value': 0}
    current_green_value = {'value': 0}
    current_blue_value = {'value': 0}

    color_format_select = ttk.Combobox(colors_tab, width=10, textvariable=color_format_var, state='readonly',
                                       values=('HEX', 'RGB', 'HSL'))

    def format_color_string(red_value: int, green_value: int, blue_value: int) -> str:
        format_choice = color_format_var.get()
        if format_choice == 'RGB':
            return f'rgb({red_value}, {green_value}, {blue_value})'
        if format_choice == 'HSL':
            red_float = red_value / 255.0
            green_float = green_value / 255.0
            blue_float = blue_value / 255.0
            hue_float, light_float, saturation_float = colorsys.rgb_to_hls(red_float, green_float, blue_float)
            hue_degrees = int(round(hue_float * 360))
            saturation_percent = int(round(saturation_float * 100))
            light_percent = int(round(light_float * 100))
            return f'hsl({hue_degrees}, {saturation_percent}%, {light_percent}%)'
        base_string = f'#{red_value:02x}{green_value:02x}{blue_value:02x}'
        if uppercase_hex_var.get():
            base_string = base_string.upper()
        if not include_hash_var.get():
            base_string = base_string[1:]
        return base_string

    def update_color_display_from_current(_event=None):
        formatted_color_text = format_color_string(
            current_red_value['value'],
            current_green_value['value'],
            current_blue_value['value']
        )
        color_string_var.set(formatted_color_text)
        try:
            hex_for_canvas = f'#{current_red_value["value"]:02x}{current_green_value["value"]:02x}{current_blue_value["value"]:02x}'
            color_preview_canvas.delete('all')
            color_preview_canvas.create_rectangle(0, 0, 64, 24, fill=hex_for_canvas, outline='')
        except Exception:
            pass
        return 'break'

    def handle_roll_color(_event=None):
        current_red_value['value'] = rng_randint_inclusive(app, 0, 255)
        current_green_value['value'] = rng_randint_inclusive(app, 0, 255)
        current_blue_value['value'] = rng_randint_inclusive(app, 0, 255)
        update_color_display_from_current()
        return 'break'

    def handle_insert_color(_event=None):
        insert_into_editor(app, color_string_var.get() + ' ')
        return 'break'

    def handle_copy_color(_event=None):
        try:
            tool_root.clipboard_clear()
            tool_root.clipboard_append(color_string_var.get())
        except Exception:
            pass
        return 'break'

    color_format_select.bind('<<ComboboxSelected>>', lambda e: (update_color_display_from_current(), refresh_palette_text_if_any()))
    handle_roll_color()

    color_preview_canvas.grid(row=1, column=0, padx=(10, 5), pady=(0, 6), sticky='w')
    color_value_label.grid(row=1, column=1, padx=(0, 10), pady=(0, 6), sticky='w')
    color_format_select.grid(row=1, column=2, padx=(0, 10), pady=(0, 6), sticky='e')

    uppercase_hex_check = ttk.Checkbutton(colors_tab, text='Uppercase', variable=uppercase_hex_var,
                                          command=lambda: (update_color_display_from_current(), refresh_palette_text_if_any()))
    include_hash_check = ttk.Checkbutton(colors_tab, text='Include #', variable=include_hash_var,
                                         command=lambda: (update_color_display_from_current(), refresh_palette_text_if_any()))
    uppercase_hex_check.grid(row=2, column=0, padx=(10, 5), pady=(0, 8), sticky='w')
    include_hash_check.grid(row=2, column=1, padx=(5, 10), pady=(0, 8), sticky='w')

    css_variable_name_var = tk.StringVar(value='--color')
    css_variable_name_entry = ttk.Entry(colors_tab, textvariable=css_variable_name_var, width=18)
    copy_color_css_button = ttk.Button(colors_tab, text='Copy as CSS var')

    def handle_copy_color_css(_event=None):
        css_name = css_variable_name_var.get().strip() or '--color'
        css_value = color_string_var.get().strip()
        css_line = f'{css_name}: {css_value};'
        try:
            tool_root.clipboard_clear()
            tool_root.clipboard_append(css_line)
        except Exception:
            pass
        return 'break'

    copy_color_css_button.configure(command=handle_copy_color_css)
    css_variable_name_entry.grid(row=1, column=3, padx=(5, 10), pady=(0, 6), sticky='ew')
    copy_color_css_button.grid(row=2, column=2, padx=(5, 5), pady=(0, 8), sticky='ew')

    reroll_color_button = ttk.Button(colors_tab, text='Re-roll', command=handle_roll_color)
    insert_color_button = ttk.Button(colors_tab, text='Insert', command=handle_insert_color)
    copy_color_button = ttk.Button(colors_tab, text='Copy', command=handle_copy_color)
    reroll_color_button.grid(row=2, column=3, padx=(5, 10), pady=(0, 8), sticky='ew')
    insert_color_button.grid(row=3, column=2, padx=(5, 5), pady=(0, 8), sticky='ew')
    copy_color_button.grid(row=3, column=3, padx=(5, 10), pady=(0, 8), sticky='ew')

    # Palette
    palette_title_label = ttk.Label(colors_tab, text='Palette', anchor='center')
    palette_title_label.grid(row=4, column=0, columnspan=4, pady=(8, 4), sticky='ew')

    palette_scheme_var = tk.StringVar(value='Complementary')
    palette_size_var = tk.StringVar(value='5')
    palette_result_var = tk.StringVar(value='')

    palette_scheme_select = ttk.Combobox(colors_tab, width=16, textvariable=palette_scheme_var, state='readonly',
                                         values=('Complementary', 'Triadic', 'Analogous', 'Monochrome'))
    palette_size_entry = ttk.Entry(colors_tab, width=6, textvariable=palette_size_var,
                                   validate='key',
                                   validatecommand=(colors_tab.register(is_valid_int_string), '%P'))
    palette_swatch_canvas = tk.Canvas(colors_tab, width=260, height=24, highlightthickness=1, relief='solid')
    palette_value_label = ttk.Label(colors_tab, textvariable=palette_result_var)

    palette_scheme_select.grid(row=5, column=0, padx=(10, 5), pady=(0, 6), sticky='w')
    palette_size_entry.grid(row=5, column=1, padx=(5, 10), pady=(0, 6), sticky='w')
    palette_swatch_canvas.grid(row=5, column=2, columnspan=2, padx=(5, 10), pady=(0, 6), sticky='ew')
    palette_value_label.grid(row=6, column=0, columnspan=4, padx=10, pady=(0, 6), sticky='w')

    last_palette_rgb_list = {'value': []}

    def clamp_byte(value_float: float) -> int:
        return max(0, min(255, int(round(value_float))))

    def make_rgb_from_hsv(hue_degrees: float, saturation_float: float, value_float: float):
        hue_normalized = (hue_degrees % 360) / 360.0
        red_float, green_float, blue_float = colorsys.hsv_to_rgb(hue_normalized, saturation_float, value_float)
        return clamp_byte(red_float * 255), clamp_byte(green_float * 255), clamp_byte(blue_float * 255)

    def generate_palette_colors(base_red: int, base_green: int, base_blue: int, scheme_name: str, palette_size: int):
        red_float = base_red / 255.0
        green_float = base_green / 255.0
        blue_float = base_blue / 255.0
        hue_float, light_float, saturation_hls = colorsys.rgb_to_hls(red_float, green_float, blue_float)
        base_hue_degrees = hue_float * 360.0
        saturation_hsv = max(0.35, min(0.9, saturation_hls if saturation_hls > 0 else 0.6))
        value_hsv = max(0.35, min(0.95, light_float + 0.2))

        palette_hues = [base_hue_degrees]
        if scheme_name == 'Complementary':
            hue_step = 180
            while len(palette_hues) < palette_size:
                palette_hues.append((base_hue_degrees + hue_step) % 360)
                hue_step = -hue_step
        elif scheme_name == 'Triadic':
            base_set_hues = [base_hue_degrees, base_hue_degrees + 120, base_hue_degrees + 240]
            index_counter = 0
            while len(palette_hues) < palette_size:
                palette_hues.append(base_set_hues[index_counter % 3])
                index_counter += 1
        elif scheme_name == 'Analogous':
            offsets_list = [-30, -15, 0, 15, 30]
            index_counter = 0
            while len(palette_hues) < palette_size:
                palette_hues.append(base_hue_degrees + offsets_list[index_counter % len(offsets_list)])
                index_counter += 1
        else:
            rgb_results = []
            for index_i in range(palette_size):
                value_clamped = max(0.2, min(0.95, (index_i + 1) / (palette_size + 1) + (value_hsv - 0.5)))
                rgb_results.append(make_rgb_from_hsv(base_hue_degrees, saturation_hsv, value_clamped))
            return rgb_results

        rgb_results = []
        for index_i in range(palette_size):
            hue_value = palette_hues[index_i] if index_i < len(palette_hues) else base_hue_degrees
            rgb_results.append(make_rgb_from_hsv(hue_value, saturation_hsv, value_hsv))
        return rgb_results

    def format_color_value(red_value: int, green_value: int, blue_value: int):
        format_choice = color_format_var.get()
        if format_choice == 'RGB':
            return f'rgb({red_value}, {green_value}, {blue_value})'
        if format_choice == 'HSL':
            red_float = red_value / 255.0
            green_float = green_value / 255.0
            blue_float = blue_value / 255.0
            hue_float, light_float, saturation_float = colorsys.rgb_to_hls(red_float, green_float, blue_float)
            return f'hsl({int(round(hue_float * 360))}, {int(round(saturation_float * 100))}%, {int(round(light_float * 100))}%)'
        hex_string = f'#{red_value:02x}{green_value:02x}{blue_value:02x}'
        if uppercase_hex_var.get():
            hex_string = hex_string.upper()
        if not include_hash_var.get():
            hex_string = hex_string[1:]
        return hex_string

    def draw_palette_swatch(rgb_list):
        palette_swatch_canvas.delete('all')
        canvas_width = int(palette_swatch_canvas.winfo_width() or 260)
        canvas_height = int(palette_swatch_canvas.winfo_height() or 24)
        color_count = max(1, len(rgb_list))
        cell_width = max(1, canvas_width // color_count)
        cell_left = 0
        for (red_value, green_value, blue_value) in rgb_list:
            hex_box = f'#{red_value:02x}{green_value:02x}{blue_value:02x}'
            palette_swatch_canvas.create_rectangle(cell_left, 0, cell_left + cell_width, canvas_height, fill=hex_box, outline='')
            cell_left += cell_width

    def handle_generate_palette(_event=None):
        try:
            requested_size = int(palette_size_var.get().strip() or '1')
        except ValueError:
            messagebox.showerror(getattr(app, 'title_struct', '') + ' error', 'Palette size must be a positive integer.')
            return 'break'
        requested_size = max(1, min(12, requested_size))
        selected_scheme = palette_scheme_var.get()
        rgb_list = generate_palette_colors(current_red_value['value'],
                                           current_green_value['value'],
                                           current_blue_value['value'],
                                           selected_scheme, requested_size)
        last_palette_rgb_list['value'] = rgb_list
        draw_palette_swatch(rgb_list)
        formatted_list = [format_color_value(red_value, green_value, blue_value) for (red_value, green_value, blue_value) in rgb_list]
        palette_result_var.set(', '.join(formatted_list))
        return 'break'

    def handle_insert_palette(_event=None):
        palette_text = palette_result_var.get().strip()
        if palette_text:
            insert_into_editor(app, palette_text + ' ')
        return 'break'

    def handle_copy_palette(_event=None):
        try:
            tool_root.clipboard_clear()
            tool_root.clipboard_append(palette_result_var.get())
        except Exception:
            pass
        return 'break'

    generate_palette_button = ttk.Button(colors_tab, text='Generate palette', command=handle_generate_palette)
    insert_palette_button = ttk.Button(colors_tab, text='Insert palette', command=handle_insert_palette)
    copy_palette_button = ttk.Button(colors_tab, text='Copy palette', command=handle_copy_palette)

    generate_palette_button.grid(row=7, column=0, padx=(10, 5), pady=(0, 10), sticky='ew')
    insert_palette_button.grid(row=7, column=1, padx=(5, 5), pady=(0, 10), sticky='ew')
    copy_palette_button.grid(row=7, column=2, padx=(5, 10), pady=(0, 10), sticky='ew')

    def handle_palette_resize(_event=None):
        if last_palette_rgb_list['value']:
            draw_palette_swatch(last_palette_rgb_list['value'])
        return 'break'

    def refresh_palette_text_if_any():
        if last_palette_rgb_list['value']:
            formatted_list = [format_color_value(red_value, green_value, blue_value) for (red_value, green_value, blue_value) in last_palette_rgb_list['value']]
            palette_result_var.set(', '.join(formatted_list))

    palette_swatch_canvas.bind('<Configure>', handle_palette_resize)

    css_palette_prefix_var = tk.StringVar(value='--color')
    css_palette_prefix_entry = ttk.Entry(colors_tab, textvariable=css_palette_prefix_var, width=18)
    copy_palette_css_button = ttk.Button(colors_tab, text='Copy palette as CSS vars')

    def handle_copy_palette_css(_event=None):
        if not last_palette_rgb_list['value']:
            handle_generate_palette()
        css_prefix = css_palette_prefix_var.get().strip() or '--color'
        values_text = palette_result_var.get().strip()
        if not values_text:
            return 'break'
        parts = [value.strip() for value in values_text.split(',') if value.strip()]
        lines = [f'{css_prefix}-{index + 1}: {parts[index]};' for index in range(len(parts))]
        css_block_text = '\n'.join(lines)
        try:
            tool_root.clipboard_clear()
            tool_root.clipboard_append(css_block_text)
        except Exception:
            pass
        return 'break'

    copy_palette_css_button.configure(command=handle_copy_palette_css)
    css_palette_prefix_entry.grid(row=7, column=3, padx=(5, 10), pady=(0, 10), sticky='ew')
    copy_palette_css_button.grid(row=8, column=0, columnspan=4, padx=10, pady=(0, 10), sticky='ew')

    # Lists tab
    lists_tab = ttk.Frame(tabs_notebook)
    tabs_notebook.add(lists_tab, text='Lists')
    for lists_column_index in range(2):
        lists_tab.grid_columnconfigure(lists_column_index, weight=1)
    lists_tab.grid_rowconfigure(2, weight=1)

    lists_title_label = ttk.Label(lists_tab, text='Random from list', anchor='center')
    lists_title_label.grid(row=0, column=0, columnspan=2, pady=(10, 6), sticky='ew')

    items_prompt_label = ttk.Label(lists_tab, text='Items (one per line or comma-/semicolon-separated):')
    items_prompt_label.grid(row=1, column=0, columnspan=2, padx=10, sticky='w')

    items_text_widget = tk.Text(lists_tab, height=8, width=40)
    items_text_widget.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 6), sticky='nsew')

    list_result_label = ttk.Label(lists_tab, text='Result:')
    list_result_var = tk.StringVar(value='')
    list_result_value_label = ttk.Label(lists_tab, textvariable=list_result_var, font=('Arial', 10, 'bold'))
    list_result_label.grid(row=3, column=0, padx=10, sticky='w')
    list_result_value_label.grid(row=3, column=1, padx=10, sticky='ew')

    sample_size_label = ttk.Label(lists_tab, text='Sample size:')
    sample_size_var = tk.StringVar(value='2')
    sample_size_entry = ttk.Entry(lists_tab, textvariable=sample_size_var, width=8,
                                  validate='key',
                                  validatecommand=(lists_tab.register(is_valid_int_string), '%P'))
    sample_size_label.grid(row=4, column=0, padx=10, pady=(6, 0), sticky='w')
    sample_size_entry.grid(row=4, column=1, padx=10, pady=(6, 0), sticky='w')

    def parse_items_text():
        raw_text = items_text_widget.get('1.0', 'end').strip()
        if not raw_text:
            return []
        parts = []
        for raw_line in raw_text.splitlines():
            for item_piece in raw_line.replace(';', ',').split(','):
                item_piece = item_piece.strip()
                if item_piece:
                    parts.append(item_piece)
        return parts

    def set_result_and_insert(result_value):
        if isinstance(result_value, (list, tuple)):
            result_text = ', '.join(map(str, result_value))
        else:
            result_text = str(result_value)
        list_result_var.set(result_text)
        insert_into_editor(app, result_text + ' ')

    def handle_list_choice(_event=None):
        items = parse_items_text()
        if not items:
            messagebox.showerror(getattr(app, 'title_struct', '') + ' error', 'Please enter at least one item.')
            return 'break'
        try:
            chosen_item = rng_choice_one(app, items)
        except Exception as exception:
            messagebox.showerror(getattr(app, 'title_struct', '') + ' error', str(exception))
            return 'break'
        set_result_and_insert(chosen_item)
        return 'break'

    def handle_list_sample(_event=None):
        items = parse_items_text()
        if not items:
            messagebox.showerror(getattr(app, 'title_struct', '') + ' error', 'Please enter items to sample from.')
            return 'break'
        try:
            sample_size_value = int(sample_size_var.get().strip() or '0')
        except ValueError:
            messagebox.showerror(getattr(app, 'title_struct', '') + ' error', 'Sample size must be a non-negative integer.')
            return 'break'
        try:
            sampled_items = rng_sample_k(app, items, sample_size_value)
        except Exception as exception:
            messagebox.showerror(getattr(app, 'title_struct', '') + ' error', str(exception))
            return 'break'
        set_result_and_insert(sampled_items)
        return 'break'

    def handle_list_shuffle(_event=None):
        items = parse_items_text()
        if not items:
            messagebox.showerror(getattr(app, 'title_struct', '') + ' error', 'Please enter items to shuffle.')
            return 'break'
        shuffled_items = rng_shuffled(app, items)
        set_result_and_insert(shuffled_items)
        return 'break'

    list_choice_button = ttk.Button(lists_tab, text='Choice', command=handle_list_choice)
    list_sample_button = ttk.Button(lists_tab, text='Sample (k)', command=handle_list_sample)
    list_shuffle_button = ttk.Button(lists_tab, text='Shuffle', command=handle_list_shuffle)
    list_choice_button.grid(row=5, column=0, padx=(10, 5), pady=(8, 10), sticky='ew')
    list_sample_button.grid(row=5, column=1, padx=(5, 10), pady=(8, 10), sticky='ew')
    list_shuffle_button.grid(row=6, column=0, columnspan=2, padx=10, pady=(0, 10), sticky='ew')

    # Sequence tab (improved: inline preview, clearer options, no extra preview window)
    sequence_tab = ttk.Frame(tabs_notebook)
    tabs_notebook.add(sequence_tab, text='Sequence')
    for sequence_column_index in range(3):
        sequence_tab.grid_columnconfigure(sequence_column_index, weight=1)
    sequence_tab.grid_rowconfigure(5, weight=1)

    sequence_title_label = ttk.Label(sequence_tab, text='Random sequence generator', anchor='center')
    sequence_title_label.grid(row=0, column=0, columnspan=3, pady=(10, 6), sticky='ew')

    # Length
    sequence_length_var = tk.StringVar(value='32')
    sequence_length_label = ttk.Label(sequence_tab, text='Length:')
    def make_sequence_spin(parent_widget, variable, from_value, to_value, step=1, width=10):
        if getattr(ttk, 'Spinbox', None) is not None:
            return ttk.Spinbox(
                parent_widget,
                textvariable=variable,
                from_=from_value,
                to=to_value,
                increment=step,
                width=width,
                wrap=False,
                validate='key',
                validatecommand=(sequence_tab.register(is_valid_int_string), '%P'),
            )
        return tk.Spinbox(
            parent_widget,
            textvariable=variable,
            from_=from_value,
            to=to_value,
            increment=step,
            width=width,
            wrap=False,
            validate='key',
            validatecommand=(sequence_tab.register(is_valid_int_string), '%P'),
            justify='left',
        )

    sequence_length_spinner = make_sequence_spin(sequence_tab, sequence_length_var, 0, 1000000, 1, 10)
    sequence_length_label.grid(row=1, column=0, padx=(10, 5), pady=(0, 6), sticky='e')
    sequence_length_spinner.grid(row=1, column=1, padx=(5, 10), pady=(0, 6), sticky='w')

    # Charset and options
    insert_at_caret_var = tk.BooleanVar(value=True)
    include_lowercase_var = tk.BooleanVar(value=True)
    include_uppercase_var = tk.BooleanVar(value=True)
    include_digits_var = tk.BooleanVar(value=True)
    include_symbols_var = tk.BooleanVar(value=False)
    use_custom_charset_var = tk.BooleanVar(value=False)
    custom_charset_var = tk.StringVar(value='')

    sequence_options_frame = ttk.LabelFrame(sequence_tab, text='Options')
    sequence_options_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=(0, 8), sticky='ew')
    for seq_opt_col in range(3):
        sequence_options_frame.grid_columnconfigure(seq_opt_col, weight=1)

    include_lowercase_check = ttk.Checkbutton(sequence_options_frame, text='a-z', variable=include_lowercase_var)
    include_uppercase_check = ttk.Checkbutton(sequence_options_frame, text='A-Z', variable=include_uppercase_var)
    include_digits_check = ttk.Checkbutton(sequence_options_frame, text='0-9', variable=include_digits_var)
    include_symbols_check = ttk.Checkbutton(sequence_options_frame, text='!@#$%^&*()', variable=include_symbols_var)
    insert_at_caret_check = ttk.Checkbutton(sequence_options_frame, text='Insert at caret', variable=insert_at_caret_var)
    use_custom_charset_check = ttk.Checkbutton(sequence_options_frame, text='Use custom set:', variable=use_custom_charset_var)

    include_lowercase_check.grid(row=0, column=0, padx=10, pady=(6, 2), sticky='w')
    include_uppercase_check.grid(row=0, column=1, padx=10, pady=(6, 2), sticky='w')
    include_digits_check.grid(row=0, column=2, padx=10, pady=(6, 2), sticky='w')
    include_symbols_check.grid(row=1, column=0, padx=10, pady=2, sticky='w')
    insert_at_caret_check.grid(row=1, column=1, padx=10, pady=2, sticky='w')
    use_custom_charset_check.grid(row=2, column=0, padx=10, pady=(2, 6), sticky='w')

    custom_charset_entry = ttk.Entry(sequence_options_frame, textvariable=custom_charset_var)
    custom_charset_entry.grid(row=2, column=1, columnspan=2, padx=(4, 10), pady=(2, 6), sticky='ew')

    # Actions
    sequence_buttons_frame = ttk.Frame(sequence_tab)
    sequence_buttons_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=(0, 6), sticky='ew')
    for seq_btn_col in range(4):
        sequence_buttons_frame.grid_columnconfigure(seq_btn_col, weight=1)

    generate_sequence_button = ttk.Button(sequence_buttons_frame, text='Generate')
    insert_sequence_button = ttk.Button(sequence_buttons_frame, text='Insert')
    copy_sequence_button = ttk.Button(sequence_buttons_frame, text='Copy')
    clear_sequence_button = ttk.Button(sequence_buttons_frame, text='Clear')

    generate_sequence_button.grid(row=0, column=0, padx=(0, 6), sticky='ew')
    insert_sequence_button.grid(row=0, column=1, padx=6, sticky='ew')
    copy_sequence_button.grid(row=0, column=2, padx=6, sticky='ew')
    clear_sequence_button.grid(row=0, column=3, padx=(6, 0), sticky='ew')

    # Inline preview area
    sequence_preview_container = ttk.Frame(sequence_tab)
    sequence_preview_container.grid(row=4, column=0, columnspan=3, padx=10, pady=(0, 6), sticky='nsew')
    sequence_tab.grid_rowconfigure(4, weight=1)

    sequence_preview_text = None
    try:
        sequence_preview_frame, sequence_preview_text, sequence_preview_scrollbar = app.make_rich_textbox(
            sequence_preview_container, place=(0, 0), size=(60, 8)
        )
    except Exception:
        sequence_preview_text = tk.Text(sequence_preview_container, height=8, width=60, wrap='word')
        sequence_preview_text.grid(row=0, column=0, sticky='nsew')
        preview_vertical_scrollbar = ttk.Scrollbar(sequence_preview_container, orient='vertical', command=sequence_preview_text.yview)
        sequence_preview_text.configure(yscrollcommand=preview_vertical_scrollbar.set)
        preview_vertical_scrollbar.grid(row=0, column=1, sticky='ns')
    sequence_preview_container.grid_rowconfigure(0, weight=1)
    sequence_preview_container.grid_columnconfigure(0, weight=1)

    def confirm_large(length_value: int) -> bool:
        if length_value >= 20000:
            return messagebox.askyesno(getattr(app, 'title_struct', '') + ' warning',
                                       '20,000 characters or more can cause lag.\nProceed?')
        return True

    def build_charset():
        if use_custom_charset_var.get():
            return list(custom_charset_var.get())
        from string import ascii_lowercase, ascii_uppercase, digits
        charset = []
        if include_lowercase_var.get():
            charset.extend(ascii_lowercase)
        if include_uppercase_var.get():
            charset.extend(ascii_uppercase)
        if include_digits_var.get():
            charset.extend(digits)
        if include_symbols_var.get():
            charset.extend(list('!@#$%^&*()'))
        return charset

    def generate_sequence_string(length_value: int) -> str:
        charset = build_charset()
        if not charset:
            return ''
        try:
            charset = rng_shuffled(app, charset)
        except Exception:
            pass
        result_chars = []
        for _ in range(length_value):
            try:
                result_chars.append(rng_choice_one(app, charset))
            except Exception:
                import random as std_random
                result_chars.append(std_random.choice(charset))
        return ''.join(result_chars)

    def insert_text(content_text: str, at_caret: bool):
        try:
            if at_caret and hasattr(app, 'get_pos'):
                app.EgonTE.insert(app.get_pos(), content_text)
            else:
                app.EgonTE.insert('end', content_text)
        except Exception:
            app.EgonTE.insert('end', content_text)

    def handle_generate_sequence(_event=None):
        try:
            requested_length = int(sequence_length_var.get().strip() or '0')
        except ValueError:
            messagebox.showerror(getattr(app, 'title_struct', '') + ' error', 'Please enter a valid length.')
            return 'break'
        if requested_length < 0:
            messagebox.showerror(getattr(app, 'title_struct', '') + ' error', 'Length must be non-negative.')
            return 'break'
        if not confirm_large(requested_length):
            return 'break'
        sequence_text = generate_sequence_string(requested_length)
        try:
            sequence_preview_text.configure(state='normal')
        except Exception:
            pass
        try:
            sequence_preview_text.delete('1.0', 'end')
            sequence_preview_text.insert('end', sequence_text)
        except Exception:
            pass
        try:
            sequence_preview_text.configure(state='disabled')
        except Exception:
            pass
        return 'break'

    def handle_insert_sequence(_event=None):
        try:
            sequence_text = sequence_preview_text.get('1.0', 'end-1c')
        except Exception:
            sequence_text = ''
        if not sequence_text:
            if handle_generate_sequence() == 'break':
                return 'break'
            try:
                sequence_text = sequence_preview_text.get('1.0', 'end-1c')
            except Exception:
                sequence_text = ''
        if not sequence_text:
            return 'break'
        insert_text(sequence_text, insert_at_caret_var.get())
        return 'break'

    def handle_copy_sequence(_event=None):
        try:
            sequence_text = sequence_preview_text.get('1.0', 'end-1c')
        except Exception:
            sequence_text = ''
        if not sequence_text:
            return 'break'
        try:
            tool_root.clipboard_clear()
            tool_root.clipboard_append(sequence_text)
        except Exception:
            pass
        return 'break'

    def handle_clear_sequence(_event=None):
        try:
            sequence_preview_text.configure(state='normal')
            sequence_preview_text.delete('1.0', 'end')
            sequence_preview_text.configure(state='disabled')
        except Exception:
            try:
                sequence_preview_text.delete('1.0', 'end')
            except Exception:
                pass
        return 'break'

    generate_sequence_button.configure(command=handle_generate_sequence)
    insert_sequence_button.configure(command=handle_insert_sequence)
    copy_sequence_button.configure(command=handle_copy_sequence)
    clear_sequence_button.configure(command=handle_clear_sequence)

    try:
        if getattr(app, 'fun_numbers', None) and app.fun_numbers.get():
            try:
                sequence_length_var.set(str(rng_randint_inclusive(app, 10, 100)))
            except Exception:
                sequence_length_var.set('32')
    except Exception:
        pass

    # Dates and times tab
    datetimes_tab = ttk.Frame(tabs_notebook)
    tabs_notebook.add(datetimes_tab, text='Dates and times')
    for dates_column_index in range(4):
        datetimes_tab.grid_columnconfigure(dates_column_index, weight=1)

    datetimes_title_label = ttk.Label(datetimes_tab, text='Random date/time', anchor='center')
    datetimes_title_label.grid(row=0, column=0, columnspan=4, pady=(10, 6), sticky='ew')

    date_format_help_label = ttk.Label(datetimes_tab, text='Input dates: YYYY-MM-DD. Output uses format below.')
    date_format_help_label.grid(row=1, column=0, columnspan=4, padx=10, sticky='w')

    start_date_label = ttk.Label(datetimes_tab, text='Start date:')
    end_date_label = ttk.Label(datetimes_tab, text='End date:')
    today_string = datetime.now().date().isoformat()
    start_date_var = tk.StringVar(value=today_string)
    end_date_var = tk.StringVar(value=(datetime.now().date() + timedelta(days=30)).isoformat())
    start_date_entry = ttk.Entry(datetimes_tab, textvariable=start_date_var, width=14)
    end_date_entry = ttk.Entry(datetimes_tab, textvariable=end_date_var, width=14)

    start_date_label.grid(row=2, column=0, padx=(10, 5), pady=(4, 4), sticky='e')
    start_date_entry.grid(row=2, column=1, padx=(5, 10), pady=(4, 4), sticky='w')
    end_date_label.grid(row=2, column=2, padx=(10, 5), pady=(4, 4), sticky='e')
    end_date_entry.grid(row=2, column=3, padx=(5, 10), pady=(4, 4), sticky='w')

    include_time_var = tk.BooleanVar(value=False)
    include_time_check = ttk.Checkbutton(datetimes_tab, text='Include time (00:00:00 .. 23:59:59)',
                                         variable=include_time_var)
    include_time_check.grid(row=3, column=0, columnspan=4, padx=10, pady=(4, 6), sticky='w')

    output_format_var = tk.StringVar(value='%Y-%m-%d')
    output_format_select = ttk.Combobox(datetimes_tab, width=22, textvariable=output_format_var)
    output_format_select['values'] = (
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M:%S',
        '%d/%m/%Y',
        '%d/%m/%Y %H:%M',
        '%b %d, %Y',
        '%a, %d %b %Y %H:%M:%S'
    )

    output_format_label = ttk.Label(datetimes_tab, text='Output format:')
    output_format_label.grid(row=4, column=0, padx=(10, 5), pady=(0, 6), sticky='e')
    output_format_select.grid(row=4, column=1, columnspan=3, padx=(5, 10), pady=(0, 6), sticky='w')

    generated_datetime_var = tk.StringVar(value='')
    generated_datetime_label = ttk.Label(datetimes_tab, text='Generated:')
    generated_datetime_value_label = ttk.Label(datetimes_tab, textvariable=generated_datetime_var,
                                               font=('Arial', 10, 'bold'))
    generated_datetime_label.grid(row=5, column=0, padx=(10, 5), sticky='e')
    generated_datetime_value_label.grid(row=5, column=1, columnspan=3, padx=(5, 10), sticky='w')

    today_plus_label = ttk.Label(datetimes_tab, text='Today + days:')
    today_plus_var = tk.StringVar(value='30')
    today_plus_entry = ttk.Entry(datetimes_tab, textvariable=today_plus_var, width=8,
                                 validate='key',
                                 validatecommand=(datetimes_tab.register(is_valid_int_string), '%P'))
    set_today_plus_button = ttk.Button(datetimes_tab, text='Set today + N')

    def handle_set_today_plus(_event=None):
        try:
            days_count = int(today_plus_var.get().strip() or '0')
        except ValueError:
            messagebox.showerror(getattr(app, 'title_struct', '') + ' error', 'Days must be a non-negative integer.')
            return 'break'
        if days_count < 0:
            messagebox.showerror(getattr(app, 'title_struct', '') + ' error', 'Days must be a non-negative integer.')
            return 'break'
        start_date_value = datetime.now().date()
        end_date_value = start_date_value + timedelta(days=days_count)
        start_date_var.set(start_date_value.isoformat())
        end_date_var.set(end_date_value.isoformat())
        return 'break'

    set_today_plus_button.configure(command=handle_set_today_plus)
    today_plus_label.grid(row=6, column=0, padx=(10, 5), pady=(0, 6), sticky='e')
    today_plus_entry.grid(row=6, column=1, padx=(5, 10), pady=(0, 6), sticky='w')
    set_today_plus_button.grid(row=6, column=2, padx=(5, 10), pady=(0, 6), sticky='ew')

    def try_parse_date_only(text_value: str):
        try:
            parsed_date_value = datetime.strptime(text_value.strip(), '%Y-%m-%d').date()
            return datetime.combine(parsed_date_value, time(0, 0, 0))
        except Exception:
            return None

    def handle_roll_datetime(_event=None):
        start_datetime = try_parse_date_only(start_date_var.get())
        end_datetime = try_parse_date_only(end_date_var.get())
        if not start_datetime or not end_datetime:
            messagebox.showerror(getattr(app, 'title_struct', '') + ' error', 'Dates must be in YYYY-MM-DD format.')
            return 'break'
        if start_datetime > end_datetime:
            start_datetime, end_datetime = end_datetime, start_datetime

        if include_time_var.get():
            start_datetime = start_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
            end_datetime = end_datetime.replace(hour=23, minute=59, second=59, microsecond=0)
            seconds_range = int((end_datetime - start_datetime).total_seconds())
            chosen_datetime = start_datetime + timedelta(seconds=rng_randint_inclusive(app, 0, max(0, seconds_range)))
        else:
            day_range = (end_datetime.date() - start_datetime.date()).days
            chosen_datetime = start_datetime + timedelta(days=rng_randint_inclusive(app, 0, max(0, day_range)))
            chosen_datetime = chosen_datetime.replace(hour=0, minute=0, second=0, microsecond=0)

        try:
            formatted_date_text = chosen_datetime.strftime(output_format_var.get())
        except Exception as exception:
            messagebox.showerror(getattr(app, 'title_struct', '') + ' error', f'Invalid output format: {exception}')
            return 'break'
        generated_datetime_var.set(formatted_date_text)
        return 'break'

    def handle_insert_datetime(_event=None):
        if generated_datetime_var.get():
            insert_into_editor(app, generated_datetime_var.get() + ' ')
        return 'break'

    def handle_copy_datetime(_event=None):
        try:
            tool_root.clipboard_clear()
            tool_root.clipboard_append(generated_datetime_var.get())
        except Exception:
            pass
        return 'break'

    roll_datetime_button = ttk.Button(datetimes_tab, text='Re-roll', command=handle_roll_datetime)
    insert_datetime_button = ttk.Button(datetimes_tab, text='Insert', command=handle_insert_datetime)
    copy_datetime_button = ttk.Button(datetimes_tab, text='Copy', command=handle_copy_datetime)
    roll_datetime_button.grid(row=7, column=0, padx=(10, 5), pady=(6, 10), sticky='ew')
    insert_datetime_button.grid(row=7, column=1, padx=(5, 5), pady=(6, 10), sticky='ew')
    copy_datetime_button.grid(row=7, column=2, padx=(5, 10), pady=(6, 10), sticky='ew')

    # Bindings and tooltips
    def handle_escape_key(_event=None):
        try:
            tool_root.destroy()
        finally:
            return 'break'

    def get_active_tab_name():
        try:
            current_tab_id = tabs_notebook.select()
            return tabs_notebook.tab(current_tab_id, 'text')
        except Exception:
            return ''

    try:
        def handle_enter_key():
            tab_text = get_active_tab_name()
            if tab_text == 'Numbers':
                return insert_integer_button.invoke() or 'break'
            if tab_text == 'Names':
                return handle_insert_name()
            if tab_text == 'Colors':
                return handle_insert_color()
            if tab_text == 'Lists':
                return handle_list_choice()
            if tab_text == 'Sequence':
                return handle_insert_sequence()
            if tab_text == 'Dates and times':
                return handle_roll_datetime()
            return 'break'

        # Prefer using the app's binding system, otherwise bind locally
        if hasattr(app, 'binds') and callable(app.binds):
            app.binds(tool_root, {
                '<Return>': lambda event: handle_enter_key(),
                '<KP_Enter>': lambda event: handle_enter_key(),
                '<Escape>': handle_escape_key,
            }, group='random_tool')
        else:
            tool_root.bind('<Return>', lambda event: handle_enter_key())
            tool_root.bind('<KP_Enter>', lambda event: handle_enter_key())
            tool_root.bind('<Escape>', handle_escape_key)
    except Exception:
        tool_root.bind('<Return>', lambda event: handle_enter_key())
        tool_root.bind('<KP_Enter>', lambda event: handle_enter_key())
        tool_root.bind('<Escape>', handle_escape_key)

        # Tooltips (if available) - pass as a batch for compatibility with iterable API
        try:
            place_tooltip = getattr(app, 'place_toolt', None)
            if callable(place_tooltip):
                tooltip_items = [
                    # Numbers
                    (numbers_lower_bound_spinner, 'Lower bound (use arrows or type).'),
                    (numbers_upper_bound_spinner, 'Upper bound (use arrows or type).'),
                    (float_decimals_spinner, 'Decimal places for float preview/insert.'),
                    (reroll_integer_button, 'Re-roll an integer within the current bounds.'),
                    (insert_integer_button, 'Insert the current integer.'),
                    (reroll_float_button, 'Re-roll a float in [0, 1).'),
                    (insert_float_button, 'Insert the current float.'),
                    (reroll_quick_int_button, 'Re-roll a quick integer in [0, 9999].'),
                    (insert_quick_int_button, 'Insert the current quick integer.'),
                    # Names
                    (gender_select, 'Gender for first/full name. ''Any'' ignores gender.'),
                    (name_type_select, 'Choose Full, First, or Last name.'),
                    (reroll_name_button, 'Generate another name.'),
                    (insert_name_button, 'Insert the shown name.'),
                    (copy_name_button, 'Copy the shown name to clipboard.'),
                    # Colors
                    (color_format_select, 'Output format for color values.'),
                    (uppercase_hex_check, 'Uppercase hex letters A-F (HEX only).'),
                    (include_hash_check, 'Include the leading ''#'' (HEX only).'),
                    (css_variable_name_entry, 'CSS variable name for single color (e.g., --color).'),
                    (copy_color_css_button, 'Copy the single color as a CSS variable declaration.'),
                    (reroll_color_button, 'Generate another color.'),
                    (insert_color_button, 'Insert this color value.'),
                    (copy_color_button, 'Copy this color value.'),
                    (palette_scheme_select, 'Pick a palette scheme.'),
                    (palette_size_entry, 'Number of colors in the palette (1-12).'),
                    (generate_palette_button, 'Generate palette from the current base color.'),
                    (insert_palette_button, 'Insert the palette values.'),
                    (copy_palette_button, 'Copy the palette values.'),
                    (css_palette_prefix_entry, 'CSS variable prefix for palette (e.g., --color).'),
                    (copy_palette_css_button, 'Copy the palette as multiple CSS variable declarations.'),
                    # Lists
                    (items_text_widget, 'Enter items separated by lines or commas/semicolons.'),
                    (sample_size_entry, 'Sample size (k) for ''Sample''.'),
                    (list_choice_button, 'Pick one random item.'),
                    (list_sample_button, 'Pick k items without replacement.'),
                    (list_shuffle_button, 'Shuffle all items.'),
                    # Sequence
                    (sequence_length_spinner, 'Length of the sequence (up to 1,000,000).'),
                    (include_lowercase_check, 'Include lowercase letters (a-z).'),
                    (include_uppercase_check, 'Include uppercase letters (A-Z).'),
                    (include_digits_check, 'Include digits (0-9).'),
                    (include_symbols_check, 'Include common symbols (!@#$%^&*()).'),
                    (use_custom_charset_check, 'Use only the characters from the custom set.'),
                    (custom_charset_entry, 'Custom characters to draw from (used when enabled).'),
                    (insert_at_caret_check, 'Insert at caret; otherwise append at end.'),
                    (generate_sequence_button, 'Generate a sequence into the preview box.'),
                    (insert_sequence_button, 'Insert the previewed sequence.'),
                    (copy_sequence_button, 'Copy the previewed sequence to clipboard.'),
                    (clear_sequence_button, 'Clear the preview box.'),
                    # Dates and times
                    (start_date_entry, 'Start date in YYYY-MM-DD.'),
                    (end_date_entry, 'End date in YYYY-MM-DD.'),
                    (include_time_check, 'Include random time in the full-day range.'),
                    (output_format_select, 'strftime format for output (editable).'),
                    (today_plus_entry, 'Days ahead for quick range (non-negative).'),
                    (set_today_plus_button, 'Set start/end to today and today + N days.'),
                    (roll_datetime_button, 'Generate another date/time.'),
                    (insert_datetime_button, 'Insert the shown date/time.'),
                    (copy_datetime_button, 'Copy the shown date/time.'),
                ]
                place_tooltip(tooltip_items)
        except Exception:
            pass

        # DPI scaling integration (optional and safe)
        try:
            def on_dpi_scaling_change():
                try:
                    window_width = max(420, tool_root.winfo_width())
                    header_label.configure(wraplength=max(320, window_width - 40))
                    generated_name_value_label.configure(wraplength=max(320, window_width - 40))
                    palette_swatch_canvas.configure(width=max(240, window_width - 180))
                except Exception:
                    pass

            # Initial call to size things reasonably on open
            on_dpi_scaling_change()

            # Try to attach to a scaling tracker only if available
            scaling_spec = importlib.util.find_spec('scaling_tracker')
            if scaling_spec is not None:
                scaling_module = importlib.import_module('scaling_tracker')
                scaling_class = getattr(scaling_module, 'ScalingTracker', None)
                if scaling_class is not None:
                    try:
                        scaling_class.add_widget(on_dpi_scaling_change, tool_root)
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            numbers_lower_bound_spinner.focus_set()
        except Exception:
            pass

        return tool_root
