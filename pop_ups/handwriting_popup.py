# python
import os
import tkinter as tk
from tkinter import ttk, filedialog as fd

# Optional OCR deps; safe if missing
try:
    from PIL import Image, ImageOps, ImageFilter, ImageTk
except Exception:
    Image = None
    ImageOps = None
    ImageFilter = None
    ImageTk = None

try:
    from pytesseract import image_to_string as _pyt_image_to_string
except Exception:
    _pyt_image_to_string = None


class _StrokeRecorder:
    def __init__(self):
        self.strokes = []
        self.current = []

    def start(self):
        self.current = []

    def add(self, item_id):
        if item_id:
            self.current.append(item_id)

    def commit(self):
        if self.current:
            self.strokes.append(self.current)
            self.current = []

    def clear(self):
        self.strokes.clear()

    def undo(self, canvas: tk.Canvas):
        if not self.strokes:
            return
        last = self.strokes.pop()
        for it in last:
            try:
                canvas.delete(it)
            except Exception:
                pass


def _preprocess_for_ocr(pil_img):
    if ImageOps is None or ImageFilter is None:
        return pil_img
    img = pil_img.convert("L")
    img = ImageOps.autocontrast(img)
    try:
        img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    except Exception:
        pass
    img = img.filter(ImageFilter.MedianFilter(size=3))
    img = img.point(lambda x: 0 if x < 160 else 255, mode="1")
    return img


def _ocr_image(pil_img):
    if _pyt_image_to_string is None or Image is None:
        return "[OCR not available]"
    img = _preprocess_for_ocr(pil_img)
    try:
        return _pyt_image_to_string(img, config="--oem 3 --psm 6")
    except Exception as e:
        return f"[OCR failed: {e}]"


def open_handwriting(app):
    """
    Entry point to open the handwriting popup.
    Receives the main app instance (app) and uses its state (colors, settings, helpers).
    """

    # Globals kept for compatibility with older code paths
    global previous_point, current_point
    previous_point = [0, 0]
    current_point = [0, 0]

    # Ensure per-instance references
    if not hasattr(app, "_image_refs"):
        app._image_refs = []
    if not hasattr(app, "hw_bonus_root"):
        app.hw_bonus_root = None
    if not hasattr(app, "last_items"):
        app.last_items = []
    if not hasattr(app, "move_dict"):
        app.move_dict = {'right': [10, 0], 'left': [-10, 0], 'up': [0, -10], 'down': [0, 10]}

    # Local state
    app.convert_output = ''
    app.convert_image = ''
    color = tk.StringVar(value='black')
    width = tk.IntVar(value=1)
    lines_list, images_list = [], []
    canvas_x, canvas_y = 500, 400
    app.pnc_width, app.ers_width = tk.IntVar(value=2), tk.IntVar(value=5)
    app.current_tool = 'pencil'
    app.ers_current, app.pnc_current = 1, 1
    _DRAW_TAG = "drawn"

    rec = _StrokeRecorder()

    def _current_canvas_bg():
        try:
            return app.draw_canvas.cget('bg')
        except Exception:
            return getattr(app, "dynamic_bg", "#ffffff")

    # Create popup via your factory (handles title, owner, singleton, logging, etc.)
    hw_root = app.make_pop_ups_window(
        app.handwriting,
        custom_title=getattr(app, "title_struct", "") + 'Draw and convert',
        name="handwriting_popup",
        external_variable=False,
        modal=False,
        topmost=False,
    )

    draw_frame = tk.Frame(hw_root, bg=getattr(app, "dynamic_overall", None))
    buttons_frame = tk.Frame(hw_root, bg=getattr(app, "dynamic_overall", None))
    app.draw_canvas = tk.Canvas(
        draw_frame, width=canvas_x, height=canvas_y,
        bg=getattr(app, "dynamic_bg", "#ffffff"), cursor='pencil'
    )

    def move(key, event=None):
        # Arrow-key move via app.move_dict
        if key in ('left', 'right', 'up', 'down'):
            dx, dy = app.move_dict[key]
            app.draw_canvas.move(_DRAW_TAG, dx, dy)
            # Keep original lists in sync (extra safety)
            for l in lines_list:
                try:
                    app.draw_canvas.move(l, dx, dy)
                except Exception:
                    pass
            for img in images_list:
                try:
                    app.draw_canvas.move(img, dx, dy)
                except Exception:
                    pass
            return
        # Right-click drag phases
        if key == 'press' and event is not None:
            app.mp_x, app.mp_y = event.x, event.y
            return
        if key in ('drag', 'release') and event is not None:
            dx = event.x - getattr(app, 'mp_x', event.x)
            dy = event.y - getattr(app, 'mp_y', event.y)
            if dx or dy:
                app.draw_canvas.move(_DRAW_TAG, dx, dy)
                for l in lines_list:
                    try:
                        app.draw_canvas.move(l, dx, dy)
                    except Exception:
                        pass
                for img in images_list:
                    try:
                        app.draw_canvas.move(img, dx, dy)
                    except Exception:
                        pass
                app.mp_x, app.mp_y = event.x, event.y

    def cords(event):
        app.draw_x, app.draw_y = event.x, event.y
        cords_label.configure(text=f'X coordinates:{app.draw_x} | Y coordinates:{app.draw_y}')

    def _start_stroke(_event=None):
        rec.start()
        try:
            app.last_items.clear()
        except Exception:
            pass
        global previous_point
        previous_point = [0, 0]

    def paint(event):
        global previous_point, current_point
        app.draw_x, app.draw_y = event.x, event.y
        current_point = [app.draw_x, app.draw_y]
        if previous_point != [0, 0]:
            app.line = app.draw_canvas.create_line(
                previous_point[0], previous_point[1], app.draw_x, app.draw_y,
                fill=color.get(), width=width.get(),
                capstyle="round", joinstyle="round", tags=(_DRAW_TAG,)
            )
            lines_list.append(app.line)
            rec.add(app.line)
            if app.current_tool == 'pencil':
                if not hasattr(app, "line_group"):
                    app.line_group = []
                if not hasattr(app, "lg_dict"):
                    app.lg_dict = {}
                if not hasattr(app, "line_groups"):
                    app.line_groups = []
                if not hasattr(app, "lgs_dict"):
                    app.lgs_dict = {}
                app.line_group.append(app.line)
                app.lg_dict[app.line] = (app.draw_canvas.coords(app.line), app.draw_canvas.itemcget(app.line, 'width'))
        previous_point = [app.draw_x, app.draw_y]
        app.line = ''

    def _end_stroke(_event=None):
        rec.commit()
        if app.current_tool == 'pencil':
            if getattr(app, "line_group", None):
                app.line_groups.append(app.line_group)
                app.lgs_dict[app.line_groups.index(app.line_group)] = app.lg_dict
        app.line_group, app.lg_dict = [], {}
        global previous_point
        previous_point = [0, 0]

    def undo_line(_event=None):
        rec.undo(app.draw_canvas)
        try:
            if getattr(app, "line_groups", None):
                app.line_groups.pop()
        except Exception:
            pass
        try:
            if getattr(app, "lgs_dict", None):
                bad = [k for k in list(app.lgs_dict.keys()) if k >= len(getattr(app, "line_groups", []))]
                for k in bad:
                    del app.lgs_dict[k]
        except Exception:
            pass

    def _center_image_size(path: str):
        # Return width/height using PIL (preferred) or PhotoImage
        if Image is not None:
            try:
                pil = Image.open(path)
                return pil.width, pil.height, ImageTk.PhotoImage(pil) if ImageTk else None
            except Exception:
                pass
        # Fallback to tk.PhotoImage (supports PNG/GIF only)
        try:
            img = tk.PhotoImage(file=path)
            return img.width(), img.height(), img
        except Exception:
            return 0, 0, None

    def upload():
        filetypes = getattr(app, "img_extensions", [("Images", "*.png *.jpg *.jpeg *.bmp *.gif")])
        app.convert_image = fd.askopenfilename(filetypes=filetypes)
        if app.convert_image:
            img_w, img_h, img_ref = _center_image_size(app.convert_image)
            if img_ref is None:
                # As a last resort, try PIL -> ImageTk after load
                if Image is not None and ImageTk is not None:
                    try:
                        pil = Image.open(app.convert_image)
                        img_ref = ImageTk.PhotoImage(pil)
                        img_w, img_h = pil.width, pil.height
                    except Exception:
                        pass
            if img_ref is None:
                return  # Unsupported format; do nothing

            app._image_refs.append(img_ref)
            image_x = (app.draw_canvas.winfo_width() // 2) - (img_w // 2)
            image_y = (app.draw_canvas.winfo_height() // 2) - (img_h // 2)
            canvas_image = app.draw_canvas.create_image(image_x, image_y, image=img_ref, anchor=tk.NW, tags=(_DRAW_TAG,))
            images_list.append(canvas_image)
            rec.start()
            rec.add(canvas_image)
            rec.commit()
            app.cimage_from = 'upload'

    def save_canvas():
        path = app.save_images(app.draw_canvas, hw_root, buttons_frame)
        if path and os.path.exists(path):
            app.convert_image = path
            app.cimage_from = 'save'

    def draw_erase(mode='pencil'):
        # Keep your highlight logic if available
        try:
            app.determine_highlight()
        except Exception:
            pass

        if mode == 'pencil':
            try:
                app.draw_canvas.configure(cursor='pencil')
            except Exception:
                app.draw_canvas.configure(cursor='arrow')
            color.set('black')
            try:
                pencil.configure(bg=app._background)
                eraser.configure(bg=getattr(app, "dynamic_button", None))
            except Exception:
                pass
        else:
            try:
                app.draw_canvas.configure(cursor='dotbox')
            except Exception:
                app.draw_canvas.configure(cursor='crosshair')
            color.set(_current_canvas_bg())
            try:
                pencil.configure(bg=getattr(app, "dynamic_button", None))
                eraser.configure(bg=app._background)
            except Exception:
                pass
        app.current_tool = mode
        update_sizes()

    def update_sizes(_scrollwheel_event=False):
        if app.current_tool == 'pencil':
            size = app.pnc_width.get()
            pencil_list = list(map(int, list(app.pencil_size['values'])))
            if size in pencil_list:
                app.pnc_current = pencil_list.index(size)
            app.pencil_size.current(app.pnc_current)
        else:
            size = app.ers_width.get()
            eraser_list = list(map(int, list(app.eraser_size['values'])))
            if size in eraser_list:
                app.ers_current = eraser_list.index(size)
            app.eraser_size.current(app.ers_current)
        width.set(app.pnc_width.get() if app.current_tool == 'pencil' else app.ers_width.get())

    def sizes_shortcuts_hw(event):
        if isinstance(event, int):
            step = event
        else:
            step = -1 if getattr(event, "delta", 0) < 0 else 1
        try:
            if app.current_tool == 'pencil':
                values = list(map(int, app.pencil_size['values']))
                idx = max(0, min(len(values) - 1, app.pnc_current + step))
                app.pnc_current = idx
                app.pencil_size.current(idx)
                app.pnc_width.set(values[idx])
            else:
                values = list(map(int, app.eraser_size['values']))
                idx = max(0, min(len(values) - 1, app.ers_current + step))
                app.ers_current = idx
                app.eraser_size.current(idx)
                app.ers_width.set(values[idx])
            width.set(app.pnc_width.get() if app.current_tool == 'pencil' else app.ers_width.get())
        except Exception as e:
            print(e)

    def custom_size(_event=False):
        if app.current_tool == 'pencil':
            if isinstance(app.pnc_width.get(), int):
                app.pnc_width.set(app.pencil_size.get())
        else:
            if isinstance(app.ers_width.get(), int):
                app.ers_width.set(app.eraser_size.get())
                try:
                    fixed_values_list = list(map(int, list(app.eraser_size['values'])))
                    app.eraser_size.current(fixed_values_list.index(app.ers_width.get()))
                except ValueError:
                    pass

    def convert_():
        if not getattr(app, "convert_image", ""):
            save_canvas()
        if not getattr(app, "convert_image", ""):
            if app.convert_output:
                app.convert_output.destroy()
            app.convert_output = tk.Text(hw_root, bg=getattr(app, "dynamic_overall", None), fg=getattr(app, "dynamic_text", None))
            app.convert_output.insert('1.0', '[No image available for OCR. Please draw or upload, then Save as png.]')
            app.convert_output.configure(relief='flat', state=tk.DISABLED, height=5)
            app.convert_output.pack()
            return
        text = ''
        try:
            if Image is not None:
                pil_img = Image.open(app.convert_image)
                text = _ocr_image(pil_img)
            else:
                text = '[OCR not available]'
        except Exception as e:
            text = f'[Failed to open saved image: {e}]'
        if app.convert_output:
            app.convert_output.destroy()
        app.convert_output = tk.Text(hw_root, bg=getattr(app, "dynamic_overall", None), fg=getattr(app, "dynamic_text", None))
        app.convert_output.insert('1.0', text or '')
        app.convert_output.configure(relief='flat', state=tk.DISABLED, height=5)
        app.convert_output.pack()

    def cord_opt():
        def lt_cords(_event):
            if app.draw_tool_cords.get():
                pos_x, pos_y = app.draw_x, app.draw_y
                tool_lc.configure(text=f'{app.current_tool} coordinates:{pos_x} | {app.current_tool} coordinates:{pos_y}')

        if app.draw_tool_cords.get():
            cords_label.pack_forget()
            cords_label.grid(row=1, column=0)
            tool_lc.grid(row=1, column=2)
            hw_root.bind('<B1-Motion>', lt_cords)
        else:
            tool_lc.grid_forget()
            cords_label.grid_forget()
            cords_label.pack(fill=tk.BOTH)
            hw_root.unbind('<B1-Motion>')
            app.draw_canvas.bind('<B1-Motion>', paint)

    def information():
        app.hw_bonus_root = tk.Toplevel()
        try:
            app.make_tm(app.hw_bonus_root)
        except Exception:
            pass
        app.hw_bonus_root.title(f'{getattr(app, "title_struct", "")} Handwriting bonuses')

        arrows_desc = 'with the arrows keys, you can move the entire content \nof the canvas to the direction thatyou want'
        keybind_dict = {'': 'up', '': 'down', '': 'right', '': 'left'}
        btn_up, btn_down, btn_right, btn_left = tk.Label(app.hw_bonus_root), tk.Label(app.hw_bonus_root), tk.Label(app.hw_bonus_root), tk.Label(app.hw_bonus_root)
        keybind_exp = btn_up, btn_down, btn_right, btn_left

        keybind_title = tk.Label(app.hw_bonus_root, text='Keybindings', font=getattr(app, "titles_font", None))
        arrows_description = tk.Label(app.hw_bonus_root, text=arrows_desc, font='arial 8')
        for index, arr in enumerate(keybind_dict.keys()):
            keybind_exp[index].configure(text=f'{keybind_dict[arr]} : {arr}')

        keybind_title.grid(row=0, column=1)
        arrows_description.grid(row=1, column=1)
        btn_up.grid(row=2, column=0)
        btn_down.grid(row=2, column=2)
        btn_right.grid(row=3, column=0)
        btn_left.grid(row=3, column=2)

        scroll_wheel_up, scroll_wheel_down = '', ''
        scroll_wheel_desc = 'With your mouse scrollwheel you can change the\nthickness of the tool your using'

        scroll_up  = tk.Label(app.hw_bonus_root, text=f'more thickness : {scroll_wheel_up}')
        scroll_down = tk.Label(app.hw_bonus_root, text=f'less thickness : {scroll_wheel_down}')
        scroll_wheel_description = tk.Label(app.hw_bonus_root, text=scroll_wheel_desc, font='arial 8')

        scroll_wheel_description.grid(row=4, column=1)
        scroll_up.grid(row=5, column=0)
        scroll_down.grid(row=5, column=2)

        settings_label = tk.Label(app.hw_bonus_root, text='Settings', font=getattr(app, "titles_font", None))
        check_frame = tk.Frame(app.hw_bonus_root)
        last_tool_cords = tk.Checkbutton(check_frame, text='Tool cords', variable=app.draw_tool_cords, command=cord_opt)
        spin_shortcut = tk.Checkbutton(check_frame, text='Mouse wheel\nshortcut', variable=app.mw_shortcut, command=switch_sc)

        settings_label.grid(row=6, column=1)
        check_frame.grid(row=7, column=1)
        last_tool_cords.grid(row=1, column=0)
        spin_shortcut.grid(row=1, column=2)

    def switch_sc():
        if app.mw_shortcut.get():
            app.draw_canvas.bind('<MouseWheel>', sizes_shortcuts_hw)
            app.draw_canvas.bind('<Button-4>', lambda _e: sizes_shortcuts_hw(1))
            app.draw_canvas.bind('<Button-5>', lambda _e: sizes_shortcuts_hw(-1))
            app.draw_canvas.unbind('<Control-Key-.>')
            app.draw_canvas.unbind('<Control-Key-,>')
        else:
            app.draw_canvas.unbind('<MouseWheel>')
            app.draw_canvas.unbind('<Button-4>')
            app.draw_canvas.unbind('<Button-5>')
            app.draw_canvas.bind('<Control-Key-.>', lambda _e: sizes_shortcuts_hw(1))
            app.draw_canvas.bind('<Control-Key-,>', lambda _e: sizes_shortcuts_hw(-1))

    # Controls
    undo_button = tk.Button(buttons_frame, text='↩', command=undo_line, borderwidth=1,
                            bg=getattr(app, "dynamic_button", None), fg=getattr(app, "dynamic_text", None))
    pencil = tk.Button(buttons_frame, text='Pencil', command=lambda: draw_erase('pencil'), borderwidth=1,
                       bg=getattr(app, "dynamic_button", None), fg=getattr(app, "dynamic_text", None))
    eraser = tk.Button(buttons_frame, text='Eraser', command=lambda: draw_erase('erase'), borderwidth=1,
                       bg=getattr(app, "dynamic_button", None), fg=getattr(app, "dynamic_text", None))
    save_png = tk.Button(buttons_frame, text='Save as png', command=save_canvas, borderwidth=1,
                         bg=getattr(app, "dynamic_button", None), fg=getattr(app, "dynamic_text", None))

    # Upload button state fallback if 'tes' is absent
    upload_state = getattr(app, "tes", tk.NORMAL)
    upload_writing = tk.Button(buttons_frame, text='Upload', command=upload, state=upload_state, borderwidth=1,
                               bg=getattr(app, "dynamic_button", None), fg=getattr(app, "dynamic_text", None))

    convert_to_writing = tk.Button(buttons_frame, text='Convert to writing', command=convert_, borderwidth=1,
                                   bg=getattr(app, "dynamic_button", None), fg=getattr(app, "dynamic_text", None))
    erase_all = tk.Button(
        buttons_frame, text='Erase all',
        command=lambda: (app.draw_canvas.delete('all'), lines_list.clear(), images_list.clear(), rec.clear()),
        borderwidth=1, bg=getattr(app, "dynamic_button", None), fg=getattr(app, "dynamic_text", None)
    )
    seperator, seperator_2, seperator_3 = [
        tk.Label(buttons_frame, text='|', bg=getattr(app, "dynamic_bg", None), fg=getattr(app, "dynamic_text", None))
        for _ in range(3)
    ]
    info_button = tk.Button(buttons_frame, text='i', command=information,
                            bg=getattr(app, "dynamic_button", None), fg=getattr(app, "dynamic_text", None))

    app.pencil_size = ttk.Combobox(buttons_frame, width=10, textvariable=app.pnc_width, state='normal', values=(1, 2, 3, 4, 6, 8))
    app.pencil_size.current(app.pnc_current)
    app.eraser_size = ttk.Combobox(buttons_frame, width=10, textvariable=app.ers_width, state='normal', values=(3, 5, 8, 10, 12, 15))
    app.eraser_size.current(app.ers_current)

    cords_frame = tk.Frame(hw_root, bg=getattr(app, "dynamic_bg", None))
    tool_lc = tk.Label(cords_frame, text='', bg=getattr(app, "dynamic_overall", None), fg=getattr(app, "dynamic_text", None))
    cords_label = tk.Label(cords_frame, text='', bg=getattr(app, "dynamic_overall", None), fg=getattr(app, "dynamic_text", None))

    # Layout
    buttons_frame.pack()
    draw_frame.pack(fill=tk.BOTH, expand=True)
    app.draw_canvas.pack(fill=tk.BOTH, expand=True)

    grid_loop = (
        undo_button, seperator_3, pencil, app.pencil_size, eraser, app.eraser_size, seperator_2,
        erase_all, save_png, upload_writing, convert_to_writing, seperator, info_button
    )
    for cul, widget in enumerate(grid_loop):
        widget.grid(row=0, column=cul, padx=2)

    app.hw_bg = draw_frame, buttons_frame
    app.hw_buttons = pencil, eraser, save_png, upload_writing, convert_to_writing, erase_all, info_button
    app.hw_labels = tool_lc, cords_label
    app.hw_seperator = seperator, seperator_2, seperator_3

    cords_frame.pack(fill=tk.BOTH)
    cords_label.pack(fill=tk.BOTH)

    # Initial tool
    draw_erase('pencil')

    # Bindings
    app.draw_canvas.bind('<ButtonPress-1>', _start_stroke)
    app.draw_canvas.bind('<B1-Motion>', paint)
    app.draw_canvas.bind('<ButtonRelease-1>', _end_stroke)

    hw_root.bind('<Left>', lambda _e: move('left'))
    hw_root.bind('<Right>', lambda _e: move('right'))
    hw_root.bind('<Up>', lambda _e: move('up'))
    hw_root.bind('<Down>', lambda _e: move('down'))

    # Tool hotkeys
    hw_root.bind('p', lambda _e: draw_erase('pencil'))
    hw_root.bind('e', lambda _e: draw_erase('erase'))

    hw_root.bind('<Motion>', cords)

    if hasattr(app, "undo") and callable(app.undo):
        hw_root.bind('<Control-Key-z>', lambda _e: app.undo(), add="+")
    else:
        hw_root.bind('<Control-Key-z>', lambda _e: undo_line(), add="+")

    app.pencil_size.bind('<<ComboboxSelected>>', lambda _e: update_sizes())
    app.eraser_size.bind('<<ComboboxSelected>>', lambda _e: update_sizes())

    app.draw_canvas.bind('<MouseWheel>', sizes_shortcuts_hw)
    app.draw_canvas.bind('<Button-4>', lambda _e: sizes_shortcuts_hw(1))
    app.draw_canvas.bind('<Button-5>', lambda _e: sizes_shortcuts_hw(-1))

    app.draw_canvas.bind('<ButtonPress-3>', lambda e: move('press', e))
    app.draw_canvas.bind('<B3-Motion>',   lambda e: move('drag', e))
    app.draw_canvas.bind('<ButtonRelease-3>', lambda e: move('release', e))

    # Night-mode syncing for eraser/button highlights
    _nm_trace_token = None

    def _refresh_eraser_if_needed(*_args):
        if getattr(app, "current_tool", "") == "erase":
            color.set(_current_canvas_bg())
        draw_erase(app.current_tool)

    if hasattr(app, "night_mode"):
        try:
            _nm_trace_token = app.night_mode.trace_add("write", _refresh_eraser_if_needed)
        except Exception:
            _nm_trace_token = None

    def _cleanup_theme_trace(_=None):
        try:
            if _nm_trace_token and hasattr(app.night_mode, "trace_remove"):
                app.night_mode.trace_remove("write", _nm_trace_token)
        except Exception:
            pass

    hw_root.bind("<Destroy>", _cleanup_theme_trace, add="+")
