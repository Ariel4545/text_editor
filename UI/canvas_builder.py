
import tkinter as tk
import tkinter.ttk as ttk
from typing import Any, Optional, Tuple, Union, List, Dict, Callable
import json
import os
import tempfile
from tkinter import font, colorchooser, simpledialog
import base64

try:
    from PIL import Image, ImageGrab, ImageTk
except ImportError:
    Image = None
    ImageGrab = None
    ImageTk = None


class RichCanvas(ttk.Frame):
    def __init__(self, master, app: Any,
                 place: Union[str, Tuple[int, int], list] = 'pack_top',
                 size: Optional[Tuple[int, int]] = (800, 600),
                 bg: Optional[str] = '#ffffff',
                 cursor: str = 'pencil',
                 enable_drawing: bool = True,
                 enable_text: bool = True,
                 enable_selection: bool = True,
                 enable_pan: bool = True,
                 enable_zoom: bool = True,
                 enable_grid: bool = True,
                 enable_undo: bool = True,
                 initial_tool: str = 'pencil',
                 pencil_color: str = 'black',
                 pencil_width: int = 3,
                 eraser_width: int = 20,
                 line_width: int = 3,
                 initial_font: Tuple[str, int, str] = ('Arial', 12, 'normal'),
                 show_scrollbars: bool = True,
                 auto_hide_scrollbars: bool = True,
                 show_coords_bar: bool = True,
                 mousewheel_zoom_modifier: int = 0x4,
                 zoom_factor: float = 1.1,
                 enable_mouse_wheel_width: bool = False,
                 on_width_adjust: Optional[Callable] = None,
                 **kwargs):
        super().__init__(master, **kwargs)

        self.app = app
        self.bg = bg
        self.mousewheel_zoom_modifier = mousewheel_zoom_modifier
        self.zoom_factor = zoom_factor
        self.enable_text = enable_text
        self.enable_selection = enable_selection
        self.auto_hide_scrollbars = auto_hide_scrollbars
        self.show_scrollbars = show_scrollbars
        self.enable_mouse_wheel_width = enable_mouse_wheel_width
        self.on_width_adjust = on_width_adjust

        # --- Constants ---
        self.UI_COLORS = {
            'GRID_COLOR': '#e0e0e0',
            'SELECTION_RECT_OUTLINE_COLOR': '#0078d7',
        }
        self.TAG_ALL = 'all'
        self.TAG_GRID = 'grid'
        self.TAG_NO_SAVE = 'no_save'
        self.TAG_SELECTED = 'selected'
        self.TAG_SELECTION_RECT = 'selection_rect'
        self.TAG_TEXT = 'text'
        self.TAG_IMAGE = 'image'
        self.GRID_CONFIG = {'Off': 0, 'Small': 10, 'Medium': 20, 'Large': 50}

        # --- State ---
        self.tool = initial_tool
        self.color = pencil_color
        self.font = initial_font
        self.widths = {'pencil': pencil_width, 'eraser': eraser_width, 'line': line_width}
        self.zoom = 1.0
        self.grid_visible = True
        self.grid_spacing = self.GRID_CONFIG.get(initial_tool, 20)
        self.pan_start = [0, 0]
        self.shape_start = [0, 0]
        self.current_shape_item = None
        self.current_stroke_id = None
        self.current_stroke_points = []
        self.clipboard = []
        self.image_refs = {}
        self.image_paths = {}
        self.editing_text_item = None
        self.items_deleted_by_eraser = False

        # --- Widget Creation ---
        self.y_scrollbar = ttk.Scrollbar(self, orient='vertical') if show_scrollbars else None
        self.x_scrollbar = ttk.Scrollbar(self, orient='horizontal') if show_scrollbars else None

        self.canvas = tk.Canvas(
            self,
            width=size[0] if size else None,
            height=size[1] if size else None,
            bg=self.bg,
            cursor=cursor,
            yscrollcommand=self.y_scrollbar.set if self.y_scrollbar else None,
            xscrollcommand=self.x_scrollbar.set if self.x_scrollbar else None,
            highlightthickness=0
        )

        if self.y_scrollbar: self.y_scrollbar.config(command=self.canvas.yview)
        if self.x_scrollbar: self.x_scrollbar.config(command=self.canvas.xview)

        self.coords_label = tk.Label(self, text='X: 0, Y: 0', anchor='w') if show_coords_bar else None

        # --- Layout ---
        if self.x_scrollbar: self.x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        if self.y_scrollbar: self.y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        if self.coords_label: self.coords_label.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # --- Internal API for UndoManager ---
        _api = {'serialize': self.serialize, 'load': self.load}
        self.undo_manager = _UndoManager(_api) if enable_undo else None

        # --- Bindings ---
        if enable_drawing:
            self.canvas.bind('<ButtonPress-1>', self._start_drawing, add='+')
            self.canvas.bind('<B1-Motion>', self._do_drawing, add='+')
            self.canvas.bind('<ButtonRelease-1>', self._stop_drawing, add='+')

        if show_coords_bar:
            self.canvas.bind('<Motion>', self._update_coords, add='+')
            self.canvas.bind('<Leave>', lambda e: self.coords_label.config(text=''), add='+')

        if enable_pan:
            self.canvas.bind('<ButtonPress-2>', self._pan_start, add='+')
            self.canvas.bind('<B2-Motion>', self._pan_move, add='+')
            self.canvas.bind('<ButtonPress-3>', self._pan_start, add='+')
            self.canvas.bind('<B3-Motion>', self._pan_move, add='+')
            for key in ['<Left>', '<Right>', '<Up>', '<Down>']:
                self.bind(key, self._arrow_pan)

        if enable_zoom:
            self.canvas.bind('<MouseWheel>', self._mousewheel_zoom, add='+')
            self.canvas.bind('<Button-4>', lambda e: self._mousewheel_zoom(type('event', (), {'delta': 120, 'state': e.state, 'x':e.x, 'y':e.y})()), add='+')
            self.canvas.bind('<Button-5>', lambda e: self._mousewheel_zoom(type('event', (), {'delta': -120, 'state': e.state, 'x':e.x, 'y':e.y})()), add='+')

        self.canvas.bind('<Double-1>', self._start_text_edit, add='+')
        self.canvas.bind('<Button-3>', self._show_context_menu, add='+')

        # --- Initial Setup ---
        self.set_tool(initial_tool)
        self._draw_grid()
        if self.undo_manager: self.undo_manager.save_state()
        self.after(50, self._update_scrollregion)

    def get_canvas(self):
        return self.canvas

    def set_tool(self, tool: str):
        if tool not in ['pencil', 'eraser', 'line', 'text', 'select']:
            return
        self.tool = tool
        cursors = {'pencil': 'pencil', 'eraser': 'dotbox', 'line': 'crosshair', 'text': 'xterm', 'select': 'arrow'}
        self.canvas.config(cursor=cursors.get(tool, 'pencil'))

    def get_tool(self) -> str:
        return self.tool

    def set_color(self, color: str):
        self.color = color

    def get_color(self) -> str:
        return self.color

    def set_width(self, width: int, tool: Optional[str] = None):
        self.widths[tool or self.tool] = max(1, width)

    def get_width(self, tool: Optional[str] = None) -> int:
        return self.widths.get(tool or self.tool)

    def set_font(self, font_tuple: Tuple[str, int, str]):
        self.font = font_tuple

    def get_font(self) -> Tuple[str, int, str]:
        return self.font

    def undo(self):
        if self.undo_manager: self.undo_manager.undo()

    def redo(self):
        if self.undo_manager: self.undo_manager.redo()

    def on_undo_redo_update(self, callback: Callable):
        if self.undo_manager: self.undo_manager.on_update(callback)

    def clear(self):
        self.canvas.delete(self.TAG_ALL)
        self.image_refs.clear()
        self.image_paths.clear()
        self._update_scrollregion()
        if self.undo_manager: self.undo_manager.save_state()

    def save_canvas(self, path: str):
        if not (Image and ImageGrab): return
        try:
            bbox = self.canvas.bbox(self.TAG_ALL)
            if not bbox: return

            fd, temp_ps_path = tempfile.mkstemp(suffix=".eps")
            os.close(fd)
            try:
                self.canvas.postscript(file=temp_ps_path, colormode='color', x=bbox[0], y=bbox[1], width=bbox[2]-bbox[0], height=bbox[3]-bbox[1])
                with Image.open(temp_ps_path) as img:
                    img.save(path, 'png')
            finally:
                if os.path.exists(temp_ps_path): os.remove(temp_ps_path)
        except Exception:
            x1, y1, x2, y2 = bbox
            grab_x1, grab_y1 = self.canvas.winfo_rootx() + x1, self.canvas.winfo_rooty() + y1
            grab_x2, grab_y2 = self.canvas.winfo_rootx() + x2, self.canvas.winfo_rooty() + y2
            if grab_x1 < grab_x2 and grab_y1 < grab_y2:
                ImageGrab.grab(bbox=(grab_x1, grab_y1, grab_x2, grab_y2)).save(path)

    def save_as_svg(self, path: str):
        bbox = self.canvas.bbox(self.TAG_ALL)
        if not bbox:
            return

        svg_lines = [f'<svg width="{bbox[2]-bbox[0]}" height="{bbox[3]-bbox[1]}" viewBox="{bbox[0]} {bbox[1]} {bbox[2]-bbox[0]} {bbox[3]-bbox[1]}" xmlns="http://www.w3.org/2000/svg">']

        for item_id in self.canvas.find_withtag(self.TAG_ALL):
            item_type = self.canvas.type(item_id)
            coords = self.canvas.coords(item_id)
            opts = self._get_item_options(item_id)

            if item_type == 'line' or 'stroke' in opts.get('tags', ''):
                points = " ".join(f"{coords[i]},{coords[i+1]}" for i in range(0, len(coords), 2))
                stroke_color = opts.get('fill', 'black')
                stroke_width = opts.get('width', '1')
                svg_lines.append(f'<polyline points="{points}" stroke="{stroke_color}" stroke-width="{stroke_width}" fill="none" />')
            elif item_type == 'text':
                x, y = coords[0], coords[1]
                text = opts.get('text', '')
                fill = opts.get('fill', 'black')
                font_str = opts.get('font', 'Arial 12')
                try:
                    font_obj = font.Font(font=font_str)
                    font_parts = font_obj.actual()
                    family = font_parts['family']
                    size = font_parts['size']
                    weight = font_parts['weight']
                    slant = font_parts['slant']
                    anchor = {'nw': 'start', 'n': 'middle', 'ne': 'end'}.get(opts.get('anchor', 'nw'), 'start')
                    svg_lines.append(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" font-style="{slant}" text-anchor="{anchor}" fill="{fill}">{text}</text>')
                except tk.TclError:
                    pass # Ignore font parsing errors
            elif item_type == self.TAG_IMAGE:
                img_path = self.image_paths.get(item_id)
                if img_path and os.path.exists(img_path):
                    x, y = coords[0], coords[1]
                    photo_image = self.image_refs.get(item_id)
                    if photo_image:
                        width, height = photo_image.width(), photo_image.height()
                        svg_lines.append(f'<image href="{os.path.abspath(img_path)}" x="{x}" y="{y}" width="{width}" height="{height}"/>')

        svg_lines.append('</svg>')
        with open(path, 'w', encoding='utf-8') as f:
            f.write("\n".join(svg_lines))

    def load_image(self, path: str, x: int = 0, y: int = 0):
        if not (Image and ImageTk): return
        try:
            img = Image.open(path)
            photo_img = ImageTk.PhotoImage(img)
            item_id = self.canvas.create_image(x, y, image=photo_img, anchor=tk.NW, tags=(self.TAG_ALL, self.TAG_IMAGE))
            self.image_refs[item_id] = photo_img
            self.image_paths[item_id] = path
            self._update_scrollregion()
            if self.undo_manager: self.undo_manager.save_state()
        except Exception as e:
            print(f"Failed to load image: {e}")

    def copy_selection(self):
        self.clipboard.clear()
        selected_items = self.canvas.find_withtag(self.TAG_SELECTED)
        if not selected_items: return

        bbox = self.canvas.bbox(self.TAG_SELECTED)
        if not bbox: return
        
        for item_id in selected_items:
            item_type = self.canvas.type(item_id)
            if 'stroke' in self.canvas.gettags(item_id): item_type = 'stroke'
            
            coords = self.canvas.coords(item_id)
            for i in range(0, len(coords), 2):
                coords[i] -= bbox[0]
                coords[i+1] -= bbox[1]

            self.clipboard.append({
                'type': item_type,
                'coords': coords,
                'options': self._get_item_options(item_id)
            })

    def paste_selection(self):
        if not self.clipboard: return
        self._clear_selection_visuals()
        
        paste_x, paste_y = self.canvas.canvasx(self.canvas.winfo_width()//2), self.canvas.canvasy(self.canvas.winfo_height()//2)

        create_dispatch = {
            'line': self.canvas.create_line, 'stroke': self.canvas.create_line, 'text': self.canvas.create_text,
            'oval': self.canvas.create_oval, 'rectangle': self.canvas.create_rectangle,
        }
        new_items = []
        for item_info in self.clipboard:
            item_type = item_info['type']
            opts = item_info.get('options', {})
            coords = item_info.get('coords', [])

            if item_type == self.TAG_IMAGE and opts.get('image_path'):
                self.load_image(opts['image_path'], coords[0] + paste_x, coords[1] + paste_y)
                continue

            creator = create_dispatch.get(item_type)
            if not creator: continue

            new_coords = coords[:]
            for i in range(0, len(new_coords), 2):
                new_coords[i] += paste_x
                new_coords[i+1] += paste_y
            
            if 'tags' in opts and isinstance(opts['tags'], str):
                opts['tags'] = opts['tags'].split()
            if 'tags' not in opts: opts['tags'] = []
            if self.TAG_ALL not in opts['tags']: opts['tags'].append(self.TAG_ALL)
            if self.TAG_SELECTED not in opts['tags']: opts['tags'].append(self.TAG_SELECTED)

            new_item = creator(*new_coords, **opts)
            self.canvas.itemconfigure(new_item, stipple='gray50')
            new_items.append(new_item)
        
        if new_items:
            if self.undo_manager: self.undo_manager.save_state()
            self._update_scrollregion()

    def delete_selection(self):
        selected_items = self.canvas.find_withtag(self.TAG_SELECTED)
        if selected_items:
            for item_id in selected_items:
                self.canvas.delete(item_id)
                self.image_paths.pop(item_id, None)
                self.image_refs.pop(item_id, None)
            if self.undo_manager: self.undo_manager.save_state()
            self._update_scrollregion()

    def move_selection(self, dx, dy):
        selected_items = self.canvas.find_withtag(self.TAG_SELECTED)
        if not selected_items:
            return

        for item_id in selected_items:
            self.canvas.move(item_id, dx, dy)

        if self.undo_manager:
            self.undo_manager.save_state()
        self._update_scrollregion()

    def adjust_width(self, delta: int):
        """Adjusts the width of the current tool and calls the callback."""
        tool = self.tool
        if tool in self.widths:
            current_width = self.widths[tool]
            new_width = max(1, current_width + delta)
            self.widths[tool] = new_width
            if self.on_width_adjust:
                self.on_width_adjust(tool, new_width)

    def zoom_in(self):
        self._zoom(self.zoom_factor)

    def zoom_out(self):
        self._zoom(1 / self.zoom_factor)

    def reset_zoom(self):
        self._zoom(1 / self.zoom)

    def get_zoom(self) -> float:
        return self.zoom

    def get_selected_items(self) -> list:
        return list(self.canvas.find_withtag(self.TAG_SELECTED))

    def toggle_grid(self, visible: bool):
        self.grid_visible = visible
        self._draw_grid()

    def set_grid_size(self, size_name: str):
        self.grid_spacing = self.GRID_CONFIG.get(size_name, 20)
        self._draw_grid()

    def serialize(self) -> dict:
        items = []
        for item_id in self.canvas.find_withtag(self.TAG_ALL):
            if self.TAG_NO_SAVE in self.canvas.gettags(item_id):
                continue
            item_type = self.canvas.type(item_id)
            if 'stroke' in self.canvas.gettags(item_id):
                item_type = 'stroke'
            
            item_data = {
                'type': item_type,
                'coords': self.canvas.coords(item_id),
                'options': self._get_item_options(item_id)
            }
            items.append(item_data)
        
        return {
            'items': items,
            'camera': {'zoom': self.zoom, 'xview': self.canvas.xview(), 'yview': self.canvas.yview()}
        }

    def load(self, data: dict, internal_call=False):
        self.canvas.delete(self.TAG_ALL)
        self.image_refs.clear()
        self.image_paths.clear()

        items = data.get('items', [])
        create_dispatch = {
            'line': self.canvas.create_line,
            'stroke': self.canvas.create_line,
            'text': self.canvas.create_text,
            'oval': self.canvas.create_oval,
            'rectangle': self.canvas.create_rectangle,
        }
        for item in items:
            item_type = item.get('type')
            opts = item.get('options', {})
            coords = item.get('coords', [])

            if item_type == self.TAG_IMAGE and opts.get('image_path'):
                self.load_image(opts['image_path'], coords[0], coords[1])
                continue

            creator = create_dispatch.get(item_type)
            if creator:
                if 'tags' in opts and isinstance(opts['tags'], str):
                    opts['tags'] = opts['tags'].split()
                
                if 'tags' not in opts: opts['tags'] = []
                if self.TAG_ALL not in opts['tags']: opts['tags'].append(self.TAG_ALL)

                creator(*coords, **opts)

        camera = data.get('camera')
        if camera:
            self.canvas.scale(self.TAG_ALL, 0, 0, 1/self.zoom, 1/self.zoom)
            self.zoom = 1.0
            
            loaded_zoom = camera.get('zoom', 1.0)
            if loaded_zoom != 1.0:
                self.canvas.scale(self.TAG_ALL, 0, 0, loaded_zoom, loaded_zoom)
            self.zoom = loaded_zoom

            self.canvas.xview_moveto(camera.get('xview', [0.0])[0])
            self.canvas.yview_moveto(camera.get('yview', [0.0])[0])

        self._update_scrollregion()
        self._draw_grid()
        if self.undo_manager and not internal_call:
            self.undo_manager.save_state()

    def _update_scrollregion(self, event=None):
        bbox = self.canvas.bbox(self.TAG_ALL)
        self.canvas.config(scrollregion=bbox or (0, 0, 1, 1))
        self._update_scrollbar_visibility()

    def _update_scrollbar_visibility(self):
        if not self.auto_hide_scrollbars or not self.show_scrollbars:
            return
        x0, x1 = self.canvas.xview()
        y0, y1 = self.canvas.yview()

        def _manage_bar(bar, condition, pack_opts):
            if not bar: return
            is_mapped = bar.winfo_ismapped()
            if condition and not is_mapped:
                bar.pack(**pack_opts)
            elif not condition and is_mapped:
                bar.pack_forget()

        _manage_bar(self.y_scrollbar, (y0, y1) != (0.0, 1.0), {'side': tk.RIGHT, 'fill': tk.Y})
        _manage_bar(self.x_scrollbar, (x0, x1) != (0.0, 1.0), {'side': tk.BOTTOM, 'fill': tk.X})

    def _draw_grid(self):
        self.canvas.delete(self.TAG_GRID)
        if not self.grid_visible or self.grid_spacing <= 0:
            return
        
        width = int(self.canvas.cget('width')) * 4
        height = int(self.canvas.cget('height')) * 4
        
        for i in range(0, width, self.grid_spacing):
            self.canvas.create_line(i, 0, i, height, fill=self.UI_COLORS['GRID_COLOR'], tags=(self.TAG_GRID, self.TAG_NO_SAVE))
        for i in range(0, height, self.grid_spacing):
            self.canvas.create_line(0, i, width, i, fill=self.UI_COLORS['GRID_COLOR'], tags=(self.TAG_GRID, self.TAG_NO_SAVE))
        self.canvas.tag_lower(self.TAG_GRID)

    def _get_canvas_coords(self, event):
        return self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

    def _start_drawing(self, event):
        tool = self.tool
        x, y = self._get_canvas_coords(event)
        self.shape_start = [x, y]

        if tool == 'pencil':
            color = self.color
            width = self.widths[tool]
            self.current_stroke_points = [x, y]
            self.current_stroke_id = self.canvas.create_line(
                x, y, x, y, fill=color, width=width, capstyle="round", joinstyle="round", smooth=True, tags=('stroke',)
            )
        elif tool == 'eraser':
            self.items_deleted_by_eraser = False
            self._do_drawing(event)
        elif tool == 'line':
            self.current_shape_item = self.canvas.create_line(
                x, y, x, y, fill=self.color, width=self.widths['line'], capstyle="round", tags=(self.TAG_NO_SAVE,)
            )
        elif tool == 'text' and self.enable_text:
            self._place_text_tool(x, y)
        elif tool == 'select' and self.enable_selection:
            if event.state & 0x0001: # Shift key
                self._toggle_selection_at(x, y)
            else:
                self._clear_selection_visuals()
                self.current_shape_item = self.canvas.create_rectangle(
                    x, y, x, y, outline=self.UI_COLORS['SELECTION_RECT_OUTLINE_COLOR'], dash=(4, 2), tags=(self.TAG_SELECTION_RECT, self.TAG_NO_SAVE)
                )

    def _do_drawing(self, event):
        tool = self.tool
        x, y = self._get_canvas_coords(event)

        if tool == 'eraser':
            width = self.widths['eraser'] / 2
            items = self.canvas.find_overlapping(x - width, y - width, x + width, y + width)
            for item in items:
                tags = self.canvas.gettags(item)
                if self.TAG_GRID not in tags and self.TAG_NO_SAVE not in tags:
                    self.canvas.delete(item)
                    self.items_deleted_by_eraser = True
            return

        if tool == 'pencil' and self.current_stroke_id:
            self.current_stroke_points.extend([x, y])
            if len(self.current_stroke_points) < 2000: # Performance limit
                self.canvas.coords(self.current_stroke_id, *self.current_stroke_points)
        elif tool in ['line', 'select'] and self.current_shape_item:
            start_x, start_y = self.shape_start
            self.canvas.coords(self.current_shape_item, start_x, start_y, x, y)

    def _stop_drawing(self, event):
        tool = self.tool
        
        if tool == 'pencil' and self.current_stroke_id:
            self.canvas.addtag_withtag(self.TAG_ALL, self.current_stroke_id)
            if len(self.current_stroke_points) <= 2: # Draw a dot
                x, y = self.current_stroke_points
                r = self.widths['pencil'] / 2
                color = self.color
                self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline=color, tags=(self.TAG_ALL, 'stroke'))
                self.canvas.delete(self.current_stroke_id)
            if self.undo_manager: self.undo_manager.save_state()
        elif tool == 'eraser':
            if self.items_deleted_by_eraser:
                if self.undo_manager: self.undo_manager.save_state()
            self.items_deleted_by_eraser = False
        elif tool == 'line' and self.current_shape_item:
            self.canvas.delete(self.current_shape_item)
            start_x, start_y = self.shape_start
            end_x, end_y = self._get_canvas_coords(event)
            self.canvas.create_line(
                start_x, start_y, end_x, end_y, fill=self.color, width=self.widths['line'], capstyle="round", tags=(self.TAG_ALL, 'line')
            )
            if self.undo_manager: self.undo_manager.save_state()
        elif tool == 'select' and self.current_shape_item:
            x1, y1, x2, y2 = self.canvas.coords(self.current_shape_item)
            self.canvas.delete(self.current_shape_item)
            for item in self.canvas.find_enclosed(x1, y1, x2, y2):
                if self.TAG_NO_SAVE not in self.canvas.gettags(item):
                    self.canvas.addtag_withtag(self.TAG_SELECTED, item)
                    self.canvas.itemconfigure(item, stipple='gray50')

        self.current_stroke_id = None
        self.current_shape_item = None
        self.current_stroke_points = []
        self._update_scrollregion()

    def _place_text_tool(self, x, y):
        text = simpledialog.askstring('Enter Text', 'Enter text:', parent=self)
        if text:
            font_tuple = (self.font[0], int(self.font[1] / self.zoom), self.font[2])
            self.canvas.create_text(
                x, y, text=text, fill=self.color, font=font_tuple, tags=(self.TAG_TEXT, self.TAG_ALL), anchor='nw'
            )
            if self.undo_manager: self.undo_manager.save_state()

    def _update_coords(self, event):
        if self.coords_label:
            x, y = self._get_canvas_coords(event)
            self.coords_label.config(text=f'X: {x:.0f}, Y: {y:.0f}')

    def _pan_start(self, event):
        self.pan_start = [event.x, event.y]
    def _pan_move(self, event):
        dx = event.x - self.pan_start[0]
        dy = event.y - self.pan_start[1]
        self.canvas.xview_scroll(-dx, "units")
        self.canvas.yview_scroll(-dy, "units")
        self.pan_start = [event.x, event.y]

    def _arrow_pan(self, event):
        move_map = {'Left': (-10, 0), 'Right': (10, 0), 'Up': (0, -10), 'Down': (0, 10)}
        dx, dy = move_map.get(event.keysym, (0, 0))
        if dx or dy:
            self.canvas.xview_scroll(dx, "units")
            self.canvas.yview_scroll(dy, "units")

    def _mousewheel_zoom(self, event):
        if event.state & self.mousewheel_zoom_modifier:
            factor = self.zoom_factor if event.delta > 0 else 1 / self.zoom_factor
            self._zoom(factor, event.x, event.y)
            return "break"
        elif self.enable_mouse_wheel_width:
            delta = 1 if event.delta > 0 else -1
            self.adjust_width(delta)
            return "break"
        else: # Scroll
            if event.state & 0x1:  # Shift for horizontal
                self.canvas.xview_scroll(-1 * (event.delta // 120), "units")
            else:
                self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
            self._update_scrollbar_visibility()
            return "break"

    def _zoom(self, factor, x=None, y=None):
        if x is None or y is None:
            x, y = self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2
        
        canvas_x, canvas_y = self.canvas.canvasx(x), self.canvas.canvasy(y)
        
        self.zoom *= factor
        self.canvas.scale(self.TAG_ALL, canvas_x, canvas_y, factor, factor)
        self._draw_grid()
        self._update_scrollregion()

    def _clear_selection_visuals(self):
        self.canvas.delete(self.TAG_SELECTION_RECT)
        for item in self.canvas.find_withtag(self.TAG_SELECTED):
            self.canvas.dtag(item, self.TAG_SELECTED)
            self.canvas.itemconfigure(item, stipple='')

    def _toggle_selection_at(self, x, y):
        item = self.canvas.find_closest(x, y)
        if not item: return
        item = item[0]

        if self.TAG_NO_SAVE in self.canvas.gettags(item):
            return

        if self.TAG_SELECTED in self.canvas.gettags(item):
            self.canvas.dtag(item, self.TAG_SELECTED)
            self.canvas.itemconfigure(item, stipple='')
        else:
            self.canvas.addtag_withtag(self.TAG_SELECTED, item)
            self.canvas.itemconfigure(item, stipple='gray50')

    def _start_text_edit(self, event):
        if self.tool != 'text': return
        item = self.canvas.find_closest(event.x, event.y)
        if not item or self.TAG_TEXT not in self.canvas.gettags(item[0]):
            return
        item = item[0]

        if self.editing_text_item:
            self._end_text_edit(None)

        x1, y1, x2, y2 = self.canvas.bbox(item)
        text = self.canvas.itemcget(item, 'text')
        font_ = self.canvas.itemcget(item, 'font')

        entry = tk.Text(self.canvas, wrap=tk.WORD, bd=1, relief=tk.SOLID, font=font_)
        entry.insert('1.0', text)
        entry.place(x=x1, y=y1, width=x2-x1, height=y2-y1)
        entry.focus_set()

        self.editing_text_item = {'widget': entry, 'item_id': item}
        self.canvas.itemconfigure(item, state=tk.HIDDEN)

        entry.bind('<Return>', lambda e: self._end_text_edit(e, commit=True))
        entry.bind('<FocusOut>', lambda e: self._end_text_edit(e, commit=True))
        entry.bind('<Escape>', lambda e: self._end_text_edit(e, commit=False))

    def _end_text_edit(self, event, commit=True):
        edit_info = self.editing_text_item
        if not edit_info: return

        entry = edit_info['widget']
        item_id = edit_info['item_id']

        if commit:
            new_text = entry.get('1.0', 'end-1c')
            self.canvas.itemconfigure(item_id, text=new_text)
            if self.undo_manager: self.undo_manager.save_state()

        self.canvas.itemconfigure(item_id, state=tk.NORMAL)
        entry.destroy()
        self.editing_text_item = None
        self._update_scrollregion()

    def _show_context_menu(self, event):
        context_menu = tk.Menu(self.canvas, tearoff=0)
        item = self.canvas.find_closest(event.x, event.y)
        has_selection = self.canvas.find_withtag(self.TAG_SELECTED)

        if item and self.TAG_NO_SAVE not in self.canvas.gettags(item[0]):
            item = item[0]
            if not has_selection or item not in has_selection:
                self._clear_selection_visuals()
                self.canvas.addtag_withtag(self.TAG_SELECTED, item)
                self.canvas.itemconfigure(item, stipple='gray50')
            
            context_menu.add_command(label="Copy", command=self.copy_selection)
            context_menu.add_command(label="Delete", command=self.delete_selection)
            context_menu.add_separator()
            context_menu.add_command(label="Bring to Front", command=lambda: self.canvas.lift(item))
            context_menu.add_command(label="Send to Back", command=lambda: self.canvas.lower(item))
        else:
            self._clear_selection_visuals()

        context_menu.add_command(label="Paste", command=self.paste_selection, state=tk.NORMAL if self.clipboard else tk.DISABLED)
        if self.undo_manager:
            context_menu.add_separator()
            context_menu.add_command(label="Undo", command=self.undo_manager.undo, state=tk.NORMAL if self.undo_manager.can_undo() else tk.DISABLED)
            context_menu.add_command(label="Redo", command=self.undo_manager.redo, state=tk.NORMAL if self.undo_manager.can_redo() else tk.DISABLED)

        context_menu.tk_popup(event.x_root, event.y_root)

    def _get_item_options(self, item_id):
        options = {}
        item_type = self.canvas.type(item_id)
        valid_opts = {
            'line': ['fill', 'width', 'capstyle', 'tags', 'smooth'],
            'stroke': ['fill', 'width', 'capstyle', 'tags', 'smooth'],
            'text': ['fill', 'font', 'tags', 'text', 'anchor'],
            'oval': ['fill', 'outline', 'width', 'tags'],
            'rectangle': ['fill', 'outline', 'width', 'tags'],
            'image': ['tags', 'anchor']
        }
        for opt in valid_opts.get(item_type, []):
            try:
                options[opt] = self.canvas.itemcget(item_id, opt)
            except tk.TclError:
                pass
        if item_type == self.TAG_IMAGE:
            options['image_path'] = self.image_paths.get(item_id)
        return options


class _UndoManager:
    def __init__(self, canvas_api):
        self.stack = []
        self.pointer = -1
        self.api = canvas_api
        self.update_callbacks = []

    def save_state(self):
        state_str = json.dumps(self.api['serialize'](), sort_keys=True)
        if self.pointer >= 0 and state_str == self.stack[self.pointer]:
            return

        self.pointer += 1
        self.stack = self.stack[:self.pointer]
        self.stack.append(state_str)
        self.notify()

    def undo(self):
        if self.pointer > 0:
            self.pointer -= 1
            state = json.loads(self.stack[self.pointer])
            self.api['load'](state, internal_call=True)
            self.notify()

    def redo(self):
        if self.pointer < len(self.stack) - 1:
            self.pointer += 1
            state = json.loads(self.stack[self.pointer])
            self.api['load'](state, internal_call=True)
            self.notify()

    def can_undo(self) -> bool:
        return self.pointer > 0

    def can_redo(self) -> bool:
        return self.pointer < len(self.stack) - 1

    def clear(self):
        self.stack = []
        self.pointer = -1
        self.save_state()
        self.notify()

    def on_update(self, callback: Callable):
        self.update_callbacks.append(callback)

    def notify(self):
        for cb in self.update_callbacks:
            cb(self.can_undo(), self.can_redo())
