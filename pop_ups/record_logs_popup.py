# pop_ups/record_logs_popup.py

import tkinter as tk
from tkinter import font as tkfont, filedialog, Menu, messagebox, simpledialog, ttk
import re
import threading
import queue
import json
import os
import time
from collections import deque, OrderedDict
from datetime import datetime, timedelta
import difflib

# --- Helper Class ---

class Tooltip:
    """Creates a tooltip for a given widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.tooltip_window = None

    def enter(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def leave(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

# --- Constants ---
TAG_ERROR = "error"
TAG_WARNING = "warning"
TAG_DEBUG = "debug"
TAG_ODD_ROW = "odd_row"
TAG_EVEN_ROW = "even_row"
TAG_CURRENT_SEARCH = "current_search"
TAG_SEARCH_MATCH = "search"
TAG_FILTER_MATCH = "filter_match"
TAG_GOTO = "goto"
TAG_BOOKMARK = "bookmark"
TAG_DELTA_WARN = "delta_warn"
TAG_DELTA_CRIT = "delta_crit"
FILE_PATH_REGEX = re.compile(r'([a-zA-Z]:\\[^:]+?\.pyw?|/[^:]+?\.pyw?)(?::(\d+))?')
JSON_SNIPPET_REGEX = re.compile(r'({.*?}|\[.*?\])')
BOOKMARKS_FILE = 'log_viewer_bookmarks.json'
HIGHLIGHTS_FILE = 'log_viewer_highlights.json'
ALERTS_FILE = 'log_viewer_alerts.json'
SESSION_FILE = 'log_viewer_session.json'
CORRELATION_ID_REGEXES = {
    'UUID': re.compile(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'),
    'RequestID': re.compile(r'request_id[=:\s]+([\w-]+)'),
    'TraceID': re.compile(r'trace_id[=:\s]+([\w-]+)'),
    'SessionID': re.compile(r'session_id[=:\s]+([\w-]+)'),
}
TIMESTAMP_REGEX = re.compile(r'^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[,\.]\d{3,6})?Z?\b')

# --- Helper Functions ---

def _load_json_file(filename, default_value):
    if not os.path.exists(filename):
        return default_value
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        messagebox.showwarning("Config Error", f"Could not load {filename}: {e}.\nUsing default settings.")
        return default_value

def _save_json_file(filename, data):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"Error saving {filename}: {e}")

def get_tags_for_record(record, state):
    tags = []
    # System tags
    if "[ERROR]" in record or "[CRITICAL]" in record: tags.append(TAG_ERROR)
    if "[WARNING]" in record: tags.append(TAG_WARNING)
    if "[DEBUG]" in record: tags.append(TAG_DEBUG)
    if record in state['bookmarks']: tags.append(TAG_BOOKMARK)
    
    # Custom highlight tags
    for i, rule in enumerate(state.get('highlights', [])):
        try:
            if re.search(rule['pattern'], record, re.IGNORECASE if rule.get('case_insensitive', True) else 0):
                tags.append(f"custom_highlight_{i}")
        except re.error:
            continue # Ignore invalid regex in rules
    return tuple(tags)

def _save_setting(state, key, value):
    state['settings'][key] = value

def _stop_tailing_thread(state):
    if state.get('tail_thread') and state['tail_thread'].is_alive():
        state['stop_tailing'].set()
        state['tail_thread'].join(timeout=1)
    state['tailed_file_path'] = None

def close_record(state):
    state['app'].record_active = False
    _stop_tailing_thread(state)
    
    # Save session
    session = {key: var.get() for key, var in state.items() if isinstance(var, tk.Variable)}
    session['font_size'] = state['log_font'].cget('size')
    session['filter_term'] = state['filter_entry_var'].get()
    session['search_term'] = state['search_entry_var'].get()
    session['tailed_file_path'] = state.get('tailed_file_path')
    session['timestamp_format'] = state['timestamp_format_var'].get()
    session['controls_collapsed'] = not state['bottom_frame'].winfo_ismapped()
    _save_json_file(SESSION_FILE, session)

    _save_json_file(BOOKMARKS_FILE, state['bookmarks'])
    _save_json_file(HIGHLIGHTS_FILE, state['highlights'])
    _save_json_file(ALERTS_FILE, state['alerts'])
    if state.get('queue_job'):
        state['log_root'].after_cancel(state['queue_job'])
    if hasattr(state['app'], 'opened_windows') and state['log_root'] in state['app'].opened_windows:
        state['app'].opened_windows.remove(state['log_root'])
    state['log_root'].destroy()
    state['app'].log_root = None

def _alerting_engine(state, line):
    now = time.time()
    for i, rule in enumerate(state['alerts']):
        try:
            if re.search(rule['pattern'], line, re.IGNORECASE if rule.get('case_insensitive', True) else 0):
                history = state['alert_history'][i]
                history.append(now)
                while history and now - history[0] > rule['window']:
                    history.popleft()
                if len(history) >= rule['threshold']:
                    state['queue'].put({'type': 'alert_triggered', 'rule_name': rule['name']})
                    history.clear() # Reset after triggering
        except (re.error, KeyError, TypeError):
            continue # Ignore broken rules

def _tail_log_file(state, file_path):
    state['tailed_file_path'] = file_path
    state['stop_tailing'].clear()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.seek(0, 2) # Go to the end of the file
            while not state['stop_tailing'].is_set():
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                stripped_line = line.strip()
                state['queue'].put({'type': 'new_log_lines', 'lines': [stripped_line]})
                _alerting_engine(state, stripped_line)
    except Exception as e:
        state['queue'].put({'type': 'tail_error', 'error': str(e)})

def open_and_tail_log(state):
    file_path = filedialog.askopenfilename(title="Select Log File to Tail", filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")] )
    if not file_path:
        return

    _stop_tailing_thread(state)
    state['app'].record_list.clear()
    state['bookmarks'].clear()
    update_content(state, force_update=True, clear_only=True)

    state['tail_thread'] = threading.Thread(target=_tail_log_file, args=(state, file_path), daemon=True)
    state['tail_thread'].start()

def import_logs(state):
    if not messagebox.askyesno("Confirm Import", "This will replace all current logs. Are you sure?", parent=state['log_root']):
        return
    file_path = filedialog.askopenfilename(title="Import Log File", filetypes=[("Text files", "*.txt"), ("Log files", "*.log"), ("All files", "*.*")])
    if not file_path:
        return
    _stop_tailing_thread(state)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            imported_logs = [line.strip() for line in f.readlines()]
        state['app'].record_list.clear()
        state['app'].record_list.extend(imported_logs)
        if state['is_paused_var'].get():
            toggle_pause(state)
        else:
            update_content(state, force_update=True)
        messagebox.showinfo("Success", f"Imported {len(imported_logs)} lines.", parent=state['log_root'])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to import file: {e}", parent=state['log_root'])

def save_logs(state, content_provider, title):
    file_path = filedialog.asksaveasfilename(title=title, defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if not file_path:
        return
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content_provider())
        messagebox.showinfo("Success", f"Logs saved to {file_path}", parent=state['log_root'])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save logs: {e}", parent=state['log_root'])

def clear_all_logs(state):
    if messagebox.askyesno("Confirm Clear", "This will permanently delete all recorded logs. Are you sure?", parent=state['log_root']):
        _stop_tailing_thread(state)
        state['app'].record_list.clear()
        state['bookmarks'].clear()
        update_content(state, force_update=True)

def update_status_bar(state, text):
    if state.get('tailed_file_path'):
        text += f" | Tailing: {os.path.basename(state['tailed_file_path'])}"
    state['status_bar'].config(text=text)

def _background_filter(q, all_logs, filter_options, original_log_count):
    display_list = all_logs
    active_qf_levels = filter_options['active_qf_levels']
    if active_qf_levels:
        display_list = [r for r in display_list if any(level in r for level in active_qf_levels)]

    filter_term = filter_options['filter_term']
    filter_re = None
    is_valid_regex = True
    if filter_term:
        if filter_options['is_regex']:
            try:
                flags = re.IGNORECASE if not filter_options['is_case'] else 0
                filter_re = re.compile(filter_term, flags)
                display_list = [r for r in display_list if filter_re.search(r)]
            except re.error:
                display_list = []
                is_valid_regex = False
        else:
            is_case = filter_options['is_case']
            term = filter_term if is_case else filter_term.lower()
            include_terms = [t for t in term.split() if not t.startswith('-')]
            exclude_terms = [t[1:] for t in term.split() if t.startswith('-') and len(t) > 1]
            
            if not include_terms and not exclude_terms:
                display_list = []
            else:
                temp_list = []
                for r in display_list:
                    record_to_search = r if is_case else r.lower()
                    match_includes = all(it in record_to_search for it in include_terms)
                    if not match_includes: continue
                    match_excludes = any(et in record_to_search for et in exclude_terms)
                    if match_excludes: continue
                    temp_list.append(r)
                display_list = temp_list

    q.put({
        'type': 'filter_result', 
        'display_list': display_list, 
        'filter_term': filter_term, 
        'filter_re': filter_re,
        'original_log_count': original_log_count,
        'is_valid_regex': is_valid_regex
    })

def _parse_timestamp(line, state):
    custom_format = state['timestamp_format_var'].get()
    if custom_format:
        try:
            return datetime.strptime(line, custom_format)
        except ValueError:
            pass # Fallback to regex

    match = TIMESTAMP_REGEX.match(line)
    if not match: return None
    ts_str = match.group(1).replace('T', ' ').replace(',', '.')
    try:
        # Handle varying fractional second lengths
        if '.' in ts_str:
            parts = ts_str.split('.')
            ts_str = parts[0] + '.' + parts[1][:6] # Truncate to microseconds
            return datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S.%f')
        else:
            return datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
    except (ValueError, IndexError):
        return None

def _preprocess_logs(logs, state):
    processed_logs = []
    last_ts = None

    # Stack trace folding
    folding_mode = state['stack_trace_folding_mode_var'].get()
    if state['fold_stack_traces_var'].get() and folding_mode != 'Full':
        in_trace = False
        trace_buffer = []
        temp_logs = []
        for line in logs:
            is_trace_start = line.strip().startswith("Traceback (most recent call last):")
            is_trace_body = in_trace and (line.startswith('  ') or not line.strip())
            if is_trace_start:
                if trace_buffer: # Should not happen, but for safety
                    temp_logs.append((trace_buffer[0], trace_buffer[1:]))
                trace_buffer = [line]
                in_trace = True
            elif is_trace_body:
                trace_buffer.append(line)
            else:
                if in_trace:
                    if folding_mode == 'Compact' and len(trace_buffer) > 2:
                        summary = trace_buffer[0]
                        details = ["  ...", trace_buffer[-1]]
                    else: # Minimal or short trace
                        summary = trace_buffer[0]
                        details = ["  ..."]
                    temp_logs.append((summary, details))
                    trace_buffer = []
                in_trace = False
                temp_logs.append((line, []))
        if trace_buffer:
            if folding_mode == 'Compact' and len(trace_buffer) > 2:
                summary = trace_buffer[0]
                details = ["  ...", trace_buffer[-1]]
            else: # Minimal or short trace
                summary = trace_buffer[0]
                details = ["  ..."]
            temp_logs.append((summary, details))
        logs = temp_logs
    else:
        logs = [(line, []) for line in logs]

    # Time-delta calculation
    units = state['time_delta_units_var'].get()
    multiplier = {'s': 1, 'ms': 1000, 'µs': 1000000}[units]
    warn_threshold = float(state['time_delta_warn_var'].get())
    crit_threshold = float(state['time_delta_crit_var'].get())

    for summary, details in logs:
        delta_str, delta_tag = "", ""
        if state['show_time_deltas_var'].get():
            ts = _parse_timestamp(summary, state)
            if ts:
                if last_ts:
                    delta = (ts - last_ts).total_seconds() * multiplier
                    delta_str = f"+{delta:.3f}{units}"
                    if delta >= crit_threshold: delta_tag = TAG_DELTA_CRIT
                    elif delta >= warn_threshold: delta_tag = TAG_DELTA_WARN
                last_ts = ts
            elif last_ts: # If a timestamp is missing, we can't calculate delta
                delta_str = "<PARSE ERROR>"

        processed_logs.append((delta_str, delta_tag, summary, details))
    
    return processed_logs

def _render_logs_treeview(state, processed_logs):
    log_tree = state['log_tree']
    log_tree.delete(*log_tree.get_children())
    for i, (delta, delta_tag, summary, details) in enumerate(processed_logs):
        tags = get_tags_for_record(summary, state)
        row_tag = (TAG_ODD_ROW,) if i % 2 else (TAG_EVEN_ROW,)
        all_tags = tags + row_tag + ((delta_tag,) if delta_tag else ())
        parent_iid = log_tree.insert("", tk.END, iid=f"item_{i}", values=(delta, summary), tags=all_tags, open=False)
        if details:
            for detail_line in details:
                log_tree.insert(parent_iid, tk.END, values=("", detail_line), tags=row_tag)

def _render_logs_textview(state, display_list, filter_term, filter_re):
    record_tb = state['record_tb']
    record_tb.configure(state=tk.NORMAL)
    record_tb.delete('1.0', tk.END)
    
    case_sensitive_filter = state['filter_case_var'].get()
    is_regex_filter = state['filter_regex_var'].get()

    for i, record in enumerate(display_list):
        line_start_index = record_tb.index("end-1c")
        tags = get_tags_for_record(record, state)
        row_tag = (TAG_ODD_ROW,) if i % 2 else (TAG_EVEN_ROW,)
        record_tb.insert(tk.END, record + '\n', tags + row_tag)

        if not filter_term: continue

        if is_regex_filter and filter_re:
            for match in filter_re.finditer(record):
                start = f"{line_start_index}+{match.start()}c"; end = f"{line_start_index}+{match.end()}c"
                record_tb.tag_add(TAG_FILTER_MATCH, start, end)
        elif not is_regex_filter:
            term_to_find = filter_term if case_sensitive_filter else filter_term.lower()
            record_to_search = record if case_sensitive_filter else record.lower()
            start_char = 0
            while True:
                start_char = record_to_search.find(term_to_find, start_char)
                if start_char == -1: break
                end_char = start_char + len(term_to_find)
                start = f"{line_start_index}+{start_char}c"; end = f"{line_start_index}+{end_char}c"
                record_tb.tag_add(TAG_FILTER_MATCH, start, end)
                start_char = end_char
                
    record_tb.configure(state=tk.DISABLED)

def _render_view(state, display_list, filter_term, filter_re):
    try:
        processed_logs = _preprocess_logs(display_list, state)
        if state['use_virtual_view_var'].get():
            _render_logs_treeview(state, processed_logs)
        else:
            # Flatten for text view
            flat_logs = []
            for delta, delta_tag, summary, details in processed_logs:
                flat_logs.append(summary)
                flat_logs.extend(details)
            _render_logs_textview(state, flat_logs, filter_term, filter_re)

        if state['auto_scroll_var'].get():
            if state['use_virtual_view_var'].get():
                children = state['log_tree'].get_children()
                if children: state['log_tree'].see(children[-1])
            else:
                state['record_tb'].see(tk.END)
    except Exception as e:
        try: state['app'].record_list.append(f"> [LOGS_TOOL_ERROR] - Rendering failed: {e}")
        except Exception: pass

def update_content(state, force_update=False, clear_only=False):
    app = state['app']
    if (state['is_paused_var'].get() and not force_update) or not getattr(app, 'record_active', False):
        return

    if state.get('update_running', False):
        return

    current_log_count = len(app.record_list)
    if not force_update and not clear_only and current_log_count == state['last_log_count'] and not state['tailed_file_path']:
        if getattr(app, 'record_active', False) and not state['is_paused_var'].get():
            state['log_root'].after(1000, lambda: update_content(state))
        return

    state['update_running'] = True
    
    if clear_only:
        _render_view(state, [], "", None)
        state['last_log_count'] = 0
        update_status_bar(state, f" Showing 0 of 0 logs")
        state['update_running'] = False
        if getattr(app, 'record_active', False) and not state['is_paused_var'].get():
            state['log_root'].after(1000, lambda: update_content(state))
        return

    update_status_bar(state, "Filtering...")
    filter_options = {
        'active_qf_levels': [],
        'filter_term': state['filter_entry'].get().strip(),
        'is_regex': state['filter_regex_var'].get(),
        'is_case': state['filter_case_var'].get(),
    }
    if state['qf_error_var'].get(): filter_options['active_qf_levels'].extend(["[ERROR]", "[CRITICAL]"])
    if state['qf_warning_var'].get(): filter_options['active_qf_levels'].append("[WARNING]")
    if state['qf_debug_var'].get(): filter_options['active_qf_levels'].append("[DEBUG]")

    all_logs_copy = app.record_list[:]
    threading.Thread(
        target=_background_filter,
        args=(state['queue'], all_logs_copy, filter_options, current_log_count),
        daemon=True
    ).start()

def clear_search_state(state):
    if state['use_virtual_view_var'].get():
        for iid in state['search_matches']:
            try:
                tags = list(state['log_tree'].item(iid, 'tags'))
                if TAG_CURRENT_SEARCH in tags: tags.remove(TAG_CURRENT_SEARCH); state['log_tree'].item(iid, tags=tags)
            except tk.TclError: pass
    else:
        state['record_tb'].tag_remove(TAG_SEARCH_MATCH, '1.0', tk.END)
        state['record_tb'].tag_remove(TAG_CURRENT_SEARCH, '1.0', tk.END)
    
    state['search_matches'] = []
    state['current_match_index'] = -1
    state['search_status_label'].config(text="")
    state['find_next_btn'].config(state=tk.DISABLED)
    state['find_prev_btn'].config(state=tk.DISABLED)

def _background_search(q, use_virtual, view_items, search_term, is_regex, is_case, highlight_all):
    search_matches = []
    is_valid_regex = True
    try:
        if use_virtual:
            if is_regex:
                flags = re.IGNORECASE if not is_case else 0
                search_re = re.compile(search_term, flags)
                for iid, log_text in view_items:
                    if search_re.search(log_text): search_matches.append(iid)
            else:
                term_to_find = search_term if is_case else search_term.lower()
                or_clauses = term_to_find.split(' OR ')
                for iid, log_text in view_items:
                    log_to_search = log_text if is_case else log_text.lower()
                    is_match = False
                    for clause in or_clauses:
                        and_terms = [t for t in clause.split() if not t.startswith('-')]
                        not_terms = [t[1:] for t in clause.split() if t.startswith('-') and len(t) > 1]
                        clause_match = (all(t in log_to_search for t in and_terms) and
                                        not any(t in log_to_search for t in not_terms))
                        if clause_match:
                            is_match = True
                            break
                    if is_match:
                        search_matches.append(iid)
        else: # Text View
            pass 
    except re.error:
        is_valid_regex = False

    q.put({
        'type': 'search_result',
        'search_matches': search_matches,
        'is_valid_regex': is_valid_regex
    })

def search_logs(state, event=None):
    if state.get('search_running', False): return
    clear_search_state(state)
    search_term = state['search_entry_var'].get()
    if not search_term: return

    state['search_running'] = True
    state['search_status_label'].config(text="Searching...")
    use_virtual = state['use_virtual_view_var'].get()

    if use_virtual:
        view_items = [(iid, state['log_tree'].item(iid, 'values')[1]) for iid in state['log_tree'].get_children()]
        threading.Thread(
            target=_background_search,
            args=(state['queue'], use_virtual, view_items, search_term, state['search_regex_var'].get(), state['search_case_var'].get(), state['search_highlight_all_var'].get()),
            daemon=True
        ).start()
    else:
        state['queue'].put({'type': 'search_in_text'})

def highlight_current_match(state):
    if state['current_match_index'] == -1: return
    current_match = state['search_matches'][state['current_match_index']]
    if state['use_virtual_view_var'].get():
        for iid in state['log_tree'].get_children():
             tags = list(state['log_tree'].item(iid, 'tags'))
             if TAG_CURRENT_SEARCH in tags: tags.remove(TAG_CURRENT_SEARCH); state['log_tree'].item(iid, tags=tags)
        tags = list(state['log_tree'].item(current_match, 'tags'))
        if TAG_CURRENT_SEARCH not in tags: tags.append(TAG_CURRENT_SEARCH)
        state['log_tree'].item(current_match, tags=tags)
        state['log_tree'].selection_set(current_match); state['log_tree'].see(current_match)
    else:
        record_tb = state['record_tb']
        record_tb.tag_remove(TAG_CURRENT_SEARCH, '1.0', tk.END)
        start, end = current_match
        record_tb.tag_add(TAG_CURRENT_SEARCH, start, end)
        record_tb.see(start)
    state['search_status_label'].config(text=f"{state['current_match_index'] + 1} of {len(state['search_matches'])}")

def navigate_search(state, direction):
    if not state['search_matches']: return
    new_index = (state['current_match_index'] + direction) % len(state['search_matches'])
    state['current_match_index'] = new_index
    highlight_current_match(state)

def toggle_highlight_all(state):
    _save_setting(state, 'search_highlight_all', state['search_highlight_all_var'].get())
    if state['use_virtual_view_var'].get(): return
    record_tb = state['record_tb']
    record_tb.configure(state=tk.NORMAL)
    if state['search_highlight_all_var'].get():
        for start, end in state['search_matches']:
            record_tb.tag_add(TAG_SEARCH_MATCH, start, end)
    else:
        record_tb.tag_remove(TAG_SEARCH_MATCH, '1.0', tk.END)
    highlight_current_match(state)
    record_tb.configure(state=tk.DISABLED)

def go_to_line(state):
    line_num_str = simpledialog.askstring("Go to Line", "Enter line number:", parent=state['log_root'])
    if not line_num_str or not line_num_str.isdigit(): return
    line_num = int(line_num_str)
    if state['use_virtual_view_var'].get():
        all_visible_items = state['log_tree'].get_children()
        if 0 < line_num <= len(all_visible_items):
            target_iid = all_visible_items[line_num - 1]
            state['log_tree'].selection_set(target_iid); state['log_tree'].see(target_iid)
        else: messagebox.showwarning("Go to Line", f"Line {line_num} does not exist in the current view.", parent=state['log_root'])
    else:
        record_tb = state['record_tb']
        record_tb.tag_remove(TAG_GOTO, '1.0', tk.END)
        line_start = f"{line_num}.0"; line_end = f"{line_num}.end"
        if record_tb.compare(line_start, "<", "end"):
            record_tb.see(line_start); record_tb.tag_add(TAG_GOTO, line_start, line_end)
            state['log_root'].after(2000, lambda: record_tb.tag_remove(TAG_GOTO, line_start, line_end))
        else: messagebox.showwarning("Go to Line", f"Line {line_num} does not exist.", parent=state['log_root'])

def toggle_pause(state):
    is_paused = not state['is_paused_var'].get()
    state['is_paused_var'].set(is_paused)
    state['pause_button'].config(text="Resume" if is_paused else "Pause")
    if not is_paused:
        update_content(state, force_update=True)
    visible_count = len(state['log_tree'].get_children()) if state['use_virtual_view_var'].get() else len(state['record_tb'].get("1.0", tk.END).strip().split('\n'))
    status = f" Showing {visible_count} of {len(state['app'].record_list)} logs"
    if is_paused: status += " | PAUSED"
    update_status_bar(state, status)

def schedule_filter(state, *args):
    if state['filter_job']:
        state['log_root'].after_cancel(state['filter_job'])
    state['filter_job'] = state['log_root'].after(300, lambda: update_content(state, force_update=True))

def schedule_search(state, *args):
    if state['search_job']:
        state['log_root'].after_cancel(state['search_job'])
    state['search_job'] = state['log_root'].after(300, lambda: search_logs(state))

def change_font_size(state, delta):
    new_size = state['log_font'].cget("size") + delta
    if 6 <= new_size <= 30:
        state['log_font'].configure(size=new_size)
        state['style'].configure("Treeview", rowheight=state['log_font'].metrics()['linespace'] + 2, font=state['log_font'])
        _save_setting(state, 'font_size', new_size)

def clear_all_filters(state):
    state['filter_entry'].delete(0, tk.END)
    state['qf_error_var'].set(False); state['qf_warning_var'].set(False); state['qf_debug_var'].set(False)
    update_content(state, force_update=True)

def toggle_view(state):
    _save_setting(state, 'use_virtual_view', state['use_virtual_view_var'].get())
    if state['use_virtual_view_var'].get():
        state['text_frame'].grid_remove(); state['tree_frame'].grid(row=0, column=0, sticky='nsew')
        state['app'].record_night = state['log_tree']
    else:
        state['tree_frame'].grid_remove(); state['text_frame'].grid(row=0, column=0, sticky='nsew')
        state['app'].record_night = state['record_tb']
    update_content(state, force_update=True)

def toggle_time_deltas(state):
    _save_setting(state, 'show_time_deltas', state['show_time_deltas_var'].get())
    if state['show_time_deltas_var'].get():
        state['log_tree'].configure(displaycolumns=('delta', 'log'))
    else:
        state['log_tree'].configure(displaycolumns=('log',))
    update_content(state, force_update=True)

def _set_custom_timestamp_format(state):
    new_format = simpledialog.askstring("Timestamp Format", "Enter strptime format string (e.g., %Y-%m-%d %H:%M:%S):", parent=state['log_root'])
    if new_format is not None:
        state['timestamp_format_var'].set(new_format)
        update_content(state, force_update=True)

def _configure_delta_thresholds(state):
    win = tk.Toplevel(state['log_root'])
    win.title("Configure Delta Thresholds")
    win.transient(state['log_root'])
    win.grab_set()
    
    ttk.Label(win, text="Warning Threshold (s):").grid(row=0, column=0, padx=5, pady=5)
    warn_entry = ttk.Entry(win, textvariable=state['time_delta_warn_var'])
    warn_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(win, text="Critical Threshold (s):").grid(row=1, column=0, padx=5, pady=5)
    crit_entry = ttk.Entry(win, textvariable=state['time_delta_crit_var'])
    crit_entry.grid(row=1, column=1, padx=5, pady=5)

    def _save():
        try:
            float(warn_entry.get())
            float(crit_entry.get())
            win.destroy()
            update_content(state, force_update=True)
        except ValueError:
            messagebox.showerror("Invalid Input", "Thresholds must be numbers.", parent=win)

    ttk.Button(win, text="Save", command=_save).grid(row=2, column=0, columnspan=2, pady=10)

def _toggle_bookmarks_tab(state):
    show = state['show_bookmarks_panel_var'].get()
    _save_setting(state, 'show_bookmarks_panel', show)
    if show:
        try:
            state['notebook'].insert(2, state['bookmarks_tab'], text='Bookmarks')
        except tk.TclError: # Already exists
            pass
    else:
        try:
            state['notebook'].forget(state['bookmarks_tab'])
        except tk.TclError: # Already gone
            pass

def _toggle_controls_panel(state):
    panel = state['bottom_frame']
    btn = state['toggle_controls_btn']
    if panel.winfo_ismapped():
        panel.grid_remove()
        btn.config(text='▲')
    else:
        panel.grid()
        btn.config(text='▼')

def _toggle_status_bar(state):
    frame = state['status_bar_frame']
    _save_setting(state, 'show_status_bar', state['show_status_bar_var'].get())
    if state['show_status_bar_var'].get():
        frame.grid()
    else:
        frame.grid_remove()

def _toggle_bookmark_notes(state):
    pane = state['b_pane']
    note_frame = state['b_note_frame']
    _save_setting(state, 'show_bookmark_notes', state['show_bookmark_notes_var'].get())
    if state['show_bookmark_notes_var'].get():
        try:
            pane.add(note_frame)
        except tk.TclError:
            pass
    else:
        try:
            pane.forget(note_frame)
        except tk.TclError:
            pass

def _toggle_context_menu(state):
    log_tree = state['log_tree']
    record_tb = state['record_tb']
    _save_setting(state, 'enable_context_menu', state['enable_context_menu_var'].get())
    if state['enable_context_menu_var'].get():
        log_tree.bind("<Button-3>", lambda e: show_log_context_menu(state, e))
        record_tb.bind("<Button-3>", lambda e: show_log_context_menu(state, e))
    else:
        log_tree.unbind("<Button-3>")
        record_tb.unbind("<Button-3>")

def create_entry_context_menu(event):
    menu = Menu(event.widget, tearoff=False)
    menu.add_command(label="Cut", command=lambda: event.widget.event_generate('<<Cut>>'))
    menu.add_command(label="Copy", command=lambda: event.widget.event_generate('<<Copy>>'))
    menu.add_command(label="Paste", command=lambda: event.widget.event_generate('<<Paste>>'))
    menu.add_command(label="Clear", command=lambda: event.widget.delete(0, 'end'))
    menu.add_separator()
    menu.add_command(label="Select All", command=lambda: event.widget.selection_range(0, 'end'))
    menu.tk_popup(event.x_root, event.y_root)

def _get_selected_text(state, first_line_only=False):
    if state['use_virtual_view_var'].get():
        selection = state['log_tree'].selection()
        if not selection: return ""
        if first_line_only:
            return state['log_tree'].item(selection[0], 'values')[1]
        return '\n'.join([state['log_tree'].item(iid, 'values')[1] for iid in selection])
    else:
        if state['record_tb'].tag_ranges("sel"): 
            try: 
                text = state['record_tb'].get("sel.first", "sel.last").strip()
                return text.split('\n')[0] if first_line_only else text
            except tk.TclError: return ""
    return ""

def _show_pretty_json_from_selection(state):
    selected_text = _get_selected_text(state)
    if not selected_text: 
        messagebox.showinfo("Info", "Please select text containing a JSON object.", parent=state['log_root'])
        return
    json_match = JSON_SNIPPET_REGEX.search(selected_text)
    if json_match:
        _show_pretty_json(state['log_root'], json_match.group(0))
    else:
        messagebox.showinfo("Info", "No valid JSON object found in selection.", parent=state['log_root'])

def _show_table_view_from_selection(state):
    selected_text = _get_selected_text(state)
    if not selected_text: 
        messagebox.showinfo("Info", "Please select multiple lines of columnar data.", parent=state['log_root'])
        return
    selected_lines = selected_text.strip().split('\n')
    if len(selected_lines) < 2: 
        messagebox.showinfo("Info", "Please select at least two lines to detect table structure.", parent=state['log_root'])
        return
    delimiter = _detect_columnar(selected_lines)
    if delimiter:
        _show_table_view(state, selected_lines, delimiter)
    else:
        messagebox.showinfo("Info", "Could not detect a consistent column structure (e.g., |, ,, \t, or multiple spaces) in the selection.", parent=state['log_root'])

def _update_correlation_ids(state, event=None):
    selected_text = _get_selected_text(state, first_line_only=True)
    if not selected_text: 
        state['correlation_id_combo']['values'] = []
        state['correlation_id_var'].set("")
        return
    
    found_ids = []
    for name, regex in CORRELATION_ID_REGEXES.items():
        match = regex.search(selected_text)
        if match:
            id_value = match.group(1) if match.groups() else match.group(0)
            found_ids.append(f"{name}: {id_value}")
    
    if found_ids:
        state['correlation_id_combo']['values'] = found_ids
        state['correlation_id_var'].set(found_ids[0])
        if state['auto_filter_correlation_var'].get():
            # Extract just the value for filtering
            id_val_only = found_ids[0].split(': ', 1)[1]
            state['filter_entry_var'].set(f'"' + id_val_only + '"')
    else:
        state['correlation_id_combo']['values'] = []
        state['correlation_id_var'].set("")

def toggle_bookmark_from_selection(state):
    first_line = _get_selected_text(state, first_line_only=True)
    if not first_line: 
        messagebox.showinfo("Info", "Please select a line to bookmark.", parent=state['log_root'])
        return
    toggle_bookmark(state, first_line)

def _show_pretty_json(parent, json_string):
    try:
        parsed_json = json.loads(json_string)
        pretty_json = json.dumps(parsed_json, indent=4)
    except json.JSONDecodeError:
        pretty_json = "Invalid JSON snippet"

    win = tk.Toplevel(parent)
    win.title("Formatted JSON")
    text = tk.Text(win, wrap=tk.WORD, font=("Courier New", 10))
    text.pack(expand=True, fill=tk.BOTH)
    text.insert(tk.END, pretty_json)
    text.config(state=tk.DISABLED)
    win.transient(parent)
    win.grab_set()
    win.geometry("600x500")

def toggle_bookmark(state, record):
    if not record: return
    if record in state['bookmarks']:
        del state['bookmarks'][record]
    else:
        state['bookmarks'][record] = "" # Add with empty note
    update_content(state, force_update=True)
    _update_bookmark_list(state)

def _update_bookmark_list(state):
    b_tree = state['bookmark_tree']
    b_tree.delete(*b_tree.get_children())
    for bm, note in sorted(state['bookmarks'].items()):
        ts = _parse_timestamp(bm, state)
        ts_str = ts.strftime('%H:%M:%S') if ts else "N/A"
        b_tree.insert("", tk.END, values=(ts_str, bm))

def _jump_to_bookmark(state, event):
    b_tree = state['bookmark_tree']
    selection = b_tree.selection()
    if not selection: return
    
    bookmark_text = b_tree.item(selection[0], 'values')[1]
    
    # Find the item in the main log view
    for iid in state['log_tree'].get_children():
        if state['log_tree'].item(iid, 'values')[1] == bookmark_text:
            state['log_tree'].selection_set(iid)
            state['log_tree'].see(iid)
            return

def _show_bookmark_note(state, event):
    b_tree = state['bookmark_tree']
    selection = b_tree.selection()
    if not selection: 
        state['bookmark_note_text'].config(state=tk.DISABLED)
        state['bookmark_note_text'].delete('1.0', tk.END)
        return

    bookmark_text = b_tree.item(selection[0], 'values')[1]
    note = state['bookmarks'].get(bookmark_text, "")
    state['bookmark_note_text'].config(state=tk.NORMAL)
    state['bookmark_note_text'].delete('1.0', tk.END)
    state['bookmark_note_text'].insert('1.0', note)

def _save_bookmark_note(state):
    b_tree = state['bookmark_tree']
    selection = b_tree.selection()
    if not selection: 
        messagebox.showinfo("Info", "Please select a bookmark to save a note for.", parent=state['log_root'])
        return
    
    bookmark_text = b_tree.item(selection[0], 'values')[1]
    note_text = state['bookmark_note_text'].get('1.0', tk.END).strip()
    state['bookmarks'][bookmark_text] = note_text
    messagebox.showinfo("Success", "Bookmark note saved.", parent=state['log_root'])

def toggle_bookmark_at_event(state, event):
    record = ""
    if state['use_virtual_view_var'].get():
        iid = state['log_tree'].identify_row(event.y)
        if iid: record = state['log_tree'].item(iid, 'values')[1]
    else:
        index = state['record_tb'].index(f"@{event.x},{event.y}")
        record = state['record_tb'].get(f"{index} linestart", f"{index} lineend").strip()
    toggle_bookmark(state, record)

def navigate_bookmarks(state, direction):
    view = state['log_tree'] if state['use_virtual_view_var'].get() else state['record_tb']
    
    visible_bookmarks = []
    if state['use_virtual_view_var'].get():
        for iid in view.get_children():
            if view.item(iid, 'values')[1] in state['bookmarks']:
                visible_bookmarks.append(iid)
    else:
        ranges = view.tag_ranges(TAG_BOOKMARK)
        for i in range(0, len(ranges), 2):
            visible_bookmarks.append(view.index(ranges[i]).split('.')[0])

    if not visible_bookmarks: return

    current_item = ""
    if state['use_virtual_view_var'].get():
        selection = view.selection()
        if selection: current_item = selection[0]
    else:
        current_item = view.index(tk.INSERT).split('.')[0]

    try:
        current_index = visible_bookmarks.index(current_item)
        next_index = (current_index + direction) % len(visible_bookmarks)
    except ValueError:
        next_index = 0 if direction == 1 else -1

    target_item = visible_bookmarks[next_index]
    
    if state['use_virtual_view_var'].get():
        view.selection_set(target_item)
        view.see(target_item)
    else:
        view.see(f"{target_item}.0")
        view.mark_set(tk.INSERT, f"{target_item}.0")

def _detect_columnar(logs):
    if not logs or len(logs) < 2:
        return None
    
    delimiters = ['|', ',', '\t', '  '] # Pipe, comma, tab, or multiple spaces
    for delim in delimiters:
        try:
            num_cols = len(logs[0].split(delim))
            if num_cols > 1 and all(len(line.split(delim)) == num_cols for line in logs[1:10]): # check first 10 lines
                return delim
        except Exception:
            continue
    return None

def _sort_treeview_column(tv, col, reverse):
    l = [(tv.set(k, col), k) for k in tv.get_children('')]
    try:
        l.sort(key=lambda t: float(t[0]), reverse=reverse)
    except ValueError:
        l.sort(key=lambda t: t[0], reverse=reverse)

    for index, (val, k) in enumerate(l):
        tv.move(k, '', index)

    tv.heading(col, command=lambda: _sort_treeview_column(tv, col, not reverse))

def _show_table_view(state, logs, delimiter, headers=None):
    win = tk.Toplevel(state['log_root'])
    win.title("Table View")
    win.geometry("800x600")

    if headers is None:
        headers = [h.strip() for h in logs[0].split(delimiter)]
        logs = logs[1:]
    
    tree = ttk.Treeview(win, columns=headers, show='headings')
    
    for col in headers:
        tree.heading(col, text=col, command=lambda _col=col: _sort_treeview_column(tree, _col, False))
    
    for log_line in logs:
        values = [v.strip() for v in log_line.split(delimiter)] if isinstance(log_line, str) else log_line
        if len(values) == len(headers):
            tree.insert('', tk.END, values=values)

    vsb = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(win, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    
    tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    hsb.pack(side=tk.BOTTOM, fill=tk.X)

def _parse_and_show_table(state):
    regex = simpledialog.askstring("Parse Logs", "Enter regex with named capture groups (?P<name>...):", parent=state['log_root'])
    if not regex: return

    try:
        pattern = re.compile(regex)
        headers = pattern.groupindex.keys()
        if not headers:
            messagebox.showerror("Error", "Regex must contain at least one named capture group (?P<name>...).", parent=state['log_root'])
            return

        parsed_data = []
        visible_logs = [state['log_tree'].item(iid, 'values')[1] for iid in state['log_tree'].get_children()] if state['use_virtual_view_var'].get() else state['record_tb'].get('1.0', tk.END).splitlines()
        
        for line in visible_logs:
            match = pattern.search(line)
            if match:
                parsed_data.append([match.group(h) for h in headers])
        
        if not parsed_data:
            messagebox.showinfo("Info", "No lines matched the provided regex.", parent=state['log_root'])
            return

        _show_table_view(state, parsed_data, delimiter=None, headers=list(headers))

    except re.error as e:
        messagebox.showerror("Regex Error", f"Invalid regular expression: {e}", parent=state['log_root'])

def _manage_json_rules(state, file, title):
    win = tk.Toplevel(state['log_root'])
    win.title(title)
    win.transient(state['log_root'])
    win.grab_set()
    win.geometry("600x400")

    text = tk.Text(win, wrap=tk.WORD, font=("Courier New", 10))
    text.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
    
    key = file.split('_')[-1].split('.')[0] # highlights or alerts
    
    try:
        text.insert('1.0', json.dumps(state[key], indent=4))
    except Exception as e:
        text.insert('1.0', f"Error loading {key}: {e}")

    def _save_rules_from_text():
        try:
            new_rules = json.loads(text.get('1.0', tk.END))
            if isinstance(new_rules, list):
                state[key] = new_rules
                if key == 'highlights':
                    for i, rule in enumerate(state['highlights']):
                        color = rule.get('color', '#FFDDC1')
                        tag_name = f"custom_highlight_{i}"
                        state['log_tree'].tag_configure(tag_name, background=color)
                        state['record_tb'].tag_configure(tag_name, background=color)
                elif key == 'alerts':
                    state['alert_history'] = [deque() for _ in state['alerts']]
                update_content(state, force_update=True)
                win.destroy()
            else:
                messagebox.showerror("Error", f"{key.capitalize()} must be a JSON list of objects.", parent=win)
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON.", parent=win)

    save_button = ttk.Button(win, text="Save and Close", command=_save_rules_from_text)
    save_button.pack(pady=5)

def _update_statistics(state, display_list):
    stats = {'Total': len(display_list), 'Errors': 0, 'Warnings': 0, 'Debug': 0}
    for record in display_list:
        if "[ERROR]" in record or "[CRITICAL]" in record: stats['Errors'] += 1
        if "[WARNING]" in record: stats['Warnings'] += 1
        if "[DEBUG]" in record: stats['Debug'] += 1
    
    state['stats_labels']['total'].config(text=f"Visible Logs: {stats['Total']}")
    state['stats_labels']['errors'].config(text=f"Errors: {stats['Errors']}")
    state['stats_labels']['warnings'].config(text=f"Warnings: {stats['Warnings']}")
    state['stats_labels']['debug'].config(text=f"Debug: {stats['Debug']}")

def show_log_context_menu(state, event):
    menu = Menu(state['log_root'], tearoff=False)
    selected_text = _get_selected_text(state)
    
    if selected_text:
        menu.add_command(label="Filter by Selection", command=lambda: state['filter_entry_var'].set(selected_text))
        menu.add_command(label="Search for Selection", command=lambda: state['search_entry_var'].set(selected_text))
        menu.add_separator()

    menu.add_command(label="Copy", command=lambda: state['log_root'].event_generate("<<Copy>>"))
    menu.add_command(label="Copy All Visible", command=lambda: state['app'].clipboard_append('\n'.join([state['log_tree'].item(iid, 'values')[1] for iid in state['log_tree'].get_children()]))) # Simplified for brevity
    
    try: menu.tk_popup(event.x_root, event.y_root)
    finally: menu.grab_release()

def _process_queue(state):
    try:
        while not state['queue'].empty():
            msg = state['queue'].get_nowait()
            if msg['type'] == 'filter_result':
                _render_view(state, msg['display_list'], msg['filter_term'], msg['filter_re'])
                _update_statistics(state, msg['display_list'])
                _update_bookmark_list(state)
                state['last_log_count'] = msg['original_log_count']
                status = f" Showing {len(msg['display_list'])} of {len(state['app'].record_list)} logs"
                if state['is_paused_var'].get(): status += " | PAUSED"
                update_status_bar(state, status)
                state['filter_entry'].config(background='white' if msg['is_valid_regex'] else 'pink')
                state['update_running'] = False
                if getattr(state['app'], 'record_active', False) and not state['is_paused_var'].get() and not state['tailed_file_path']:
                    state['log_root'].after(1000, lambda: update_content(state))
            elif msg['type'] == 'search_result':
                state['search_entry'].config(background='white' if msg['is_valid_regex'] else 'pink')
                state['search_matches'] = msg['search_matches']
                if state['search_matches']:
                    state['current_match_index'] = 0
                    highlight_current_match(state)
                    state['find_next_btn'].config(state=tk.NORMAL); state['find_prev_btn'].config(state=tk.NORMAL)
                state['search_status_label'].config(text=f"{len(state['search_matches'])} matches")
                state['search_running'] = False
            elif msg['type'] == 'search_in_text':
                search_matches = []
                record_tb = state['record_tb']
                search_term = state['search_entry_var'].get()
                is_case = state['search_case_var'].get()
                is_regex = state['search_regex_var'].get()
                try:
                    record_tb.configure(state=tk.NORMAL)
                    start_pos = '1.0'
                    while True:
                        res = record_tb.search(search_term, start_pos, stopindex=tk.END, nocase=not is_case, regexp=is_regex, count=tk.Variable())
                        if not res: break
                        end_pos = f"{res}+{res.getvar(str(res))}c"
                        search_matches.append((res, end_pos))
                        if state['search_highlight_all_var'].get(): record_tb.tag_add(TAG_SEARCH_MATCH, res, end_pos)
                        start_pos = end_pos
                    state['search_entry'].config(background='white')
                    state['queue'].put({'type': 'search_result', 'search_matches': search_matches, 'is_valid_regex': True})
                except tk.TclError:
                    state['queue'].put({'type': 'search_result', 'search_matches': [], 'is_valid_regex': False})
                finally:
                    record_tb.configure(state=tk.DISABLED)
            elif msg['type'] == 'new_log_lines':
                state['app'].record_list.extend(msg['lines'])
                if not state['is_paused_var'].get():
                    update_content(state, force_update=True)
            elif msg['type'] == 'tail_error':
                messagebox.showerror("Tailing Error", f"Error while tailing file: {msg['error']}", parent=state['log_root'])
                _stop_tailing_thread(state)
            elif msg['type'] == 'alert_triggered':
                original_color = state['status_bar'].cget('background')
                state['status_bar'].config(background='red', foreground='white')
                messagebox.showwarning("Alert Triggered", f"Alert: {msg['rule_name']}", parent=state['log_root'])
                state['status_bar'].config(background=original_color, foreground='black')
    except queue.Empty:
        pass
    finally:
        if getattr(state['app'], 'record_active', False):
            state['queue_job'] = state['log_root'].after(100, lambda: _process_queue(state))

# --- Main Function ---
def open_record_logs(app):
    """Opens a standalone, improved window to display program event logs."""
    if getattr(app, 'record_active', False) and getattr(app, 'log_root', None):
        try: app.log_root.attributes('-topmost', True); app.log_root.attributes('-topmost', False); app.log_root.focus_set(); return
        except tk.TclError: pass

    session = _load_json_file(SESSION_FILE, {})
    settings = session # For backward compatibility with old settings

    try: log_root = app.make_pop_ups_window(open_record_logs, custom_title="Events' Record")
    except (AttributeError, TypeError): log_root = tk.Toplevel(app); log_root.title("Events' Record")
    
    app.log_root = log_root; app.record_active = True; log_root.minsize(800, 600)
    if hasattr(app, 'st_value'): log_root.attributes('-alpha', app.st_value)
    if hasattr(app, 'make_tm'): app.make_tm(log_root)

    bookmarks = _load_json_file(BOOKMARKS_FILE, {})
    if isinstance(bookmarks, list): # Backward compatibility for old list-based bookmarks
        bookmarks = {b: "" for b in bookmarks}
    highlights = _load_json_file(HIGHLIGHTS_FILE, [])
    alerts = _load_json_file(ALERTS_FILE, [])

    state = {
        'app': app, 'log_root': log_root, 'settings': settings, 'last_log_count': -1,
        'filter_job': None, 'search_job': None, 'search_matches': [], 'current_match_index': -1,
        'queue': queue.Queue(), 'update_running': False, 'search_running': False, 'queue_job': None,
        'bookmarks': bookmarks,
        'highlights': highlights,
        'alerts': alerts,
        'alert_history': [deque() for _ in alerts],
        'stats_labels': {},
        'tail_thread': None,
        'stop_tailing': threading.Event(),
        'tailed_file_path': None
    }

    state['log_font'] = tkfont.Font(family="arial", size=settings.get('font_size', 10))
    
    # Setup variables, loading from session or using defaults
    for key, default in [('use_virtual_view', True), ('auto_scroll', True), ('word_wrap', True),
                         ('search_case', False), ('filter_case', False), ('search_regex', False),
                         ('filter_regex', False), ('search_highlight_all', False), ('qf_error', False),
                         ('qf_warning', False), ('qf_debug', False), ('fold_stack_traces', False), ('show_time_deltas', False),
                         ('show_bookmarks_panel', True), ('auto_filter_correlation', False), ('show_bookmark_notes', True),
                         ('enable_context_menu', True), ('show_status_bar', True)]:
        state[f'{key}_var'] = tk.BooleanVar(value=settings.get(key, default))
    
    state['is_paused_var'] = tk.BooleanVar(value=False)
    state['filter_entry_var'] = tk.StringVar(value=settings.get('filter_term', ''))
    state['search_entry_var'] = tk.StringVar(value=settings.get('search_term', ''))
    state['correlation_id_var'] = tk.StringVar()
    state['timestamp_format_var'] = tk.StringVar(value=settings.get('timestamp_format', ''))
    state['time_delta_units_var'] = tk.StringVar(value=settings.get('time_delta_units', 's'))
    state['time_delta_warn_var'] = tk.StringVar(value=settings.get('time_delta_warn', '1.0'))
    state['time_delta_crit_var'] = tk.StringVar(value=settings.get('time_delta_crit', '5.0'))
    state['stack_trace_folding_mode_var'] = tk.StringVar(value=settings.get('stack_trace_folding_mode', 'Compact'))

    log_root.grid_rowconfigure(0, weight=1); log_root.grid_columnconfigure(0, weight=1)
    view_container = tk.Frame(log_root); view_container.grid(row=0, column=0, sticky="nsew")
    view_container.grid_rowconfigure(0, weight=1); view_container.grid_columnconfigure(0, weight=1)

    text_frame, record_tb, _ = app.make_rich_textbox(view_container, place='grid', wrap=tk.WORD if state['word_wrap_var'].get() else tk.NONE, font=state['log_font'])
    text_frame.grid(row=0, column=0, sticky="nsew"); state.update({'text_frame': text_frame, 'record_tb': record_tb})

    style = ttk.Style(); style.configure("Treeview", rowheight=state['log_font'].metrics()['linespace'] + 2, font=state['log_font'])
    style.map("Treeview", background=[('selected', '#cce8ff')], foreground=[('selected', 'black')])
    tree_frame = ttk.Frame(view_container)
    log_tree = ttk.Treeview(tree_frame, columns=('delta', 'log'), show='headings')
    log_tree.heading('delta', text='Delta'); log_tree.column('delta', width=80, stretch=tk.NO)
    log_tree.heading('log', text='Log Entry')
    tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=log_tree.yview)
    log_tree.configure(yscrollcommand=tree_scrollbar.set); log_tree.grid(row=0, column=0, sticky='nsew'); tree_scrollbar.grid(row=0, column=1, sticky='ns')
    tree_frame.grid_rowconfigure(0, weight=1); tree_frame.grid_columnconfigure(0, weight=1); tree_frame.grid(row=0, column=0, sticky="nsew")
    state.update({'style': style, 'tree_frame': tree_frame, 'log_tree': log_tree})

    for view in (record_tb, log_tree):
        view.tag_configure(TAG_ERROR, foreground="red"); view.tag_configure(TAG_WARNING, foreground="orange")
        view.tag_configure(TAG_DEBUG, foreground="gray"); view.tag_configure(TAG_ODD_ROW, background="#f0f0f0")
        view.tag_configure(TAG_EVEN_ROW, background="white"); view.tag_configure(TAG_CURRENT_SEARCH, background="#ff9933", foreground="black")
        view.tag_configure(TAG_BOOKMARK, background="#d7ffd7")
        view.tag_configure(TAG_DELTA_WARN, foreground="#b8860b")
        view.tag_configure(TAG_DELTA_CRIT, foreground="#dc143c")
    record_tb.tag_configure(TAG_SEARCH_MATCH, background="#ffff00"); record_tb.tag_configure(TAG_FILTER_MATCH, background="#d4f0d4"); record_tb.tag_configure(TAG_GOTO, background="lightblue")

    for i, rule in enumerate(state['highlights']):
        color = rule.get('color', '#FFDDC1')
        tag_name = f"custom_highlight_{i}"
        log_tree.tag_configure(tag_name, background=color)
        record_tb.tag_configure(tag_name, background=color)

    bottom_frame = ttk.Frame(log_root, padding=5); state['bottom_frame'] = bottom_frame
    bottom_frame.grid(row=1, column=0, sticky='ew', pady=(5,0))
    bottom_frame.grid_columnconfigure(0, weight=1)

    notebook = ttk.Notebook(bottom_frame)
    notebook.pack(expand=True, fill=tk.BOTH)
    state['notebook'] = notebook
    filter_tab = ttk.Frame(notebook, padding=5)
    search_tab = ttk.Frame(notebook, padding=5)
    bookmarks_tab = ttk.Frame(notebook, padding=5); state['bookmarks_tab'] = bookmarks_tab
    analysis_tab = ttk.Frame(notebook, padding=5)
    view_tab = ttk.Frame(notebook, padding=5)
    notebook.add(filter_tab, text='Find & Filter')
    notebook.add(search_tab, text='Navigate')
    notebook.add(analysis_tab, text='Analysis')
    notebook.add(view_tab, text='View & Stats')

    status_bar_frame = ttk.Frame(log_root); status_bar_frame.grid(row=2, column=0, sticky='ew', pady=(5,0)); state['status_bar_frame'] = status_bar_frame
    state['status_bar'] = tk.Label(status_bar_frame, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W); state['status_bar'].pack(side=tk.LEFT, expand=True, fill=tk.X)
    toggle_btn = ttk.Button(status_bar_frame, text="▼", width=3, command=lambda: _toggle_controls_panel(state)); toggle_btn.pack(side=tk.RIGHT); state['toggle_controls_btn'] = toggle_btn

    log_root.protocol('WM_DELETE_WINDOW', lambda: close_record(state))

    # --- Find & Filter Tab ---
    filter_tab.grid_columnconfigure(1, weight=1)
    qf_group = ttk.LabelFrame(filter_tab, text="Quick Filters", padding=5); qf_group.grid(row=0, column=0, sticky='nswe', rowspan=2, padx=(0, 5))
    for i, (text, var_key) in enumerate([("Error/Critical", 'qf_error'), ("Warning", 'qf_warning'), ("Debug", 'qf_debug')]):
        cb = ttk.Checkbutton(qf_group, text=text, variable=state[f'{var_key}_var'], command=lambda k=var_key: (update_content(state, force_update=True), _save_setting(state, k, state[f'{k}_var'].get())))
        cb.grid(row=i, column=0, sticky='w'); Tooltip(cb, f"Show only logs containing [{text.split('/')[0].upper()}].")
    clear_all_filters_btn = ttk.Button(qf_group, text="Clear All Filters", command=lambda: clear_all_filters(state)); clear_all_filters_btn.grid(row=3, column=0, sticky='ew', pady=(5,0))
    Tooltip(clear_all_filters_btn, "Clear all active quick and text filters.")

    filter_entry_frame = ttk.LabelFrame(filter_tab, text="Text Filter", padding=5); filter_entry_frame.grid(row=0, column=1, sticky='nsew')
    filter_entry_frame.grid_columnconfigure(0, weight=1)
    filter_entry = ttk.Entry(filter_entry_frame, textvariable=state['filter_entry_var']); filter_entry.grid(row=0, column=0, sticky='ew')
    filter_entry.bind("<Button-3>", create_entry_context_menu); state.update({'filter_entry': filter_entry})
    state['filter_entry_var'].trace_add("write", lambda *a: schedule_filter(state, *a))
    Tooltip(filter_entry, "Filter terms. Use space for AND, '-' to exclude.")
    filter_buttons = ttk.Frame(filter_entry_frame); filter_buttons.grid(row=0, column=1, sticky='e', padx=(5,0))
    filter_case_check = ttk.Checkbutton(filter_buttons, text="Case", variable=state['filter_case_var'], command=lambda: (update_content(state, force_update=True), _save_setting(state, 'filter_case', state['filter_case_var'].get()))); filter_case_check.grid(row=0, column=0); Tooltip(filter_case_check, "Make the filter case-sensitive.")
    filter_regex_check = ttk.Checkbutton(filter_buttons, text="Regex", variable=state['filter_regex_var'], command=lambda: (update_content(state, force_update=True), _save_setting(state, 'filter_regex', state['filter_regex_var'].get()))); filter_regex_check.grid(row=0, column=1, padx=5); Tooltip(filter_regex_check, "Interpret the filter term as a regular expression.")

    search_frame = ttk.LabelFrame(filter_tab, text="Search", padding=5); search_frame.grid(row=1, column=1, sticky='nsew', pady=(5,0))
    search_frame.grid_columnconfigure(0, weight=1)
    search_entry = ttk.Entry(search_frame, textvariable=state['search_entry_var']); search_entry.grid(row=0, column=0, sticky='ew')
    search_entry.bind("<Button-3>", create_entry_context_menu); state.update({'search_entry': search_entry})
    state['search_entry_var'].trace_add("write", lambda *a: schedule_search(state, *a))
    Tooltip(search_entry, "Search terms. Use space for AND, 'OR' for OR, '-' to exclude.")
    search_status_label = ttk.Label(search_frame, width=20); search_status_label.grid(row=0, column=1, sticky='w', padx=5); state.update({'search_status_label': search_status_label})
    search_buttons = ttk.Frame(search_frame); search_buttons.grid(row=1, column=0, columnspan=2, pady=(5,0))
    search_case_check = ttk.Checkbutton(search_buttons, text="Case", variable=state['search_case_var'], command=lambda: _save_setting(state, 'search_case', state['search_case_var'].get())); search_case_check.pack(side=tk.LEFT, padx=(0,10)); Tooltip(search_case_check, "Make the search case-sensitive.")
    search_regex_check = ttk.Checkbutton(search_buttons, text="Regex", variable=state['search_regex_var'], command=lambda: _save_setting(state, 'search_regex', state['search_regex_var'].get())); search_regex_check.pack(side=tk.LEFT); Tooltip(search_regex_check, "Interpret the search term as a regular expression.")

    # --- Navigate Tab ---
    search_tab.grid_columnconfigure(0, weight=1)
    nav_search_frame = ttk.LabelFrame(search_tab, text="Search Results", padding=5); nav_search_frame.grid(row=0, column=0, sticky='ew', pady=(0,5))
    find_prev_btn = ttk.Button(nav_search_frame, text="Previous Match (Shift+F3)", command=lambda: navigate_search(state, -1), state=tk.DISABLED); find_prev_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5)); state.update({'find_prev_btn': find_prev_btn})
    find_next_btn = ttk.Button(nav_search_frame, text="Next Match (F3)", command=lambda: navigate_search(state, 1), state=tk.DISABLED); find_next_btn.pack(side=tk.LEFT, expand=True, fill=tk.X); state.update({'find_next_btn': find_next_btn})
    
    nav_bookmark_frame = ttk.LabelFrame(search_tab, text="Bookmarks", padding=5); nav_bookmark_frame.grid(row=1, column=0, sticky='ew', pady=(0,5))
    toggle_bookmark_btn = ttk.Button(nav_bookmark_frame, text="Toggle Bookmark on Selection", command=lambda: toggle_bookmark_from_selection(state)); toggle_bookmark_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5)); Tooltip(toggle_bookmark_btn, "Toggle bookmark on selected line.")
    prev_bookmark_btn = ttk.Button(nav_bookmark_frame, text="Previous Bookmark", command=lambda: navigate_bookmarks(state, -1)); prev_bookmark_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5)); Tooltip(prev_bookmark_btn, "Go to previous bookmark.")
    next_bookmark_btn = ttk.Button(nav_bookmark_frame, text="Next Bookmark", command=lambda: navigate_bookmarks(state, 1)); next_bookmark_btn.pack(side=tk.LEFT, expand=True, fill=tk.X); Tooltip(next_bookmark_btn, "Go to next bookmark.")

    nav_line_frame = ttk.LabelFrame(search_tab, text="Go to Line", padding=5); nav_line_frame.grid(row=2, column=0, sticky='ew')
    go_to_line_btn = ttk.Button(nav_line_frame, text="Go to Line...", command=lambda: go_to_line(state)); go_to_line_btn.pack(expand=True, fill=tk.X)

    # --- Bookmarks Tab ---
    bookmarks_tab.grid_rowconfigure(0, weight=1); bookmarks_tab.grid_columnconfigure(0, weight=1)
    b_pane = ttk.PanedWindow(bookmarks_tab, orient=tk.VERTICAL); state['b_pane'] = b_pane
    b_pane.pack(expand=True, fill=tk.BOTH)
    b_tree_frame = ttk.Frame(b_pane); b_pane.add(b_tree_frame, weight=3)
    b_note_frame = ttk.LabelFrame(b_pane, text="Notes", padding=5); state['b_note_frame'] = b_note_frame
    b_pane.add(b_note_frame, weight=1)

    b_tree = ttk.Treeview(b_tree_frame, columns=('time', 'log'), show='headings')
    b_tree.heading('time', text='Time'); b_tree.column('time', width=80, stretch=tk.NO)
    b_tree.heading('log', text='Log Entry')
    b_tree_scroll = ttk.Scrollbar(b_tree_frame, orient="vertical", command=b_tree.yview)
    b_tree.configure(yscrollcommand=b_tree_scroll.set)
    b_tree.grid(row=0, column=0, sticky='nsew'); b_tree_scroll.grid(row=0, column=1, sticky='ns')
    b_tree_frame.grid_rowconfigure(0, weight=1); b_tree_frame.grid_columnconfigure(0, weight=1)
    b_tree.bind("<<TreeviewSelect>>", lambda e: _show_bookmark_note(state, e))
    b_tree.bind("<Double-1>", lambda e: _jump_to_bookmark(state, e))
    state['bookmark_tree'] = b_tree

    b_note_frame.grid_rowconfigure(0, weight=1); b_note_frame.grid_columnconfigure(0, weight=1)
    b_note_text = tk.Text(b_note_frame, wrap=tk.WORD, height=4, state=tk.DISABLED); b_note_text.grid(row=0, column=0, sticky='nsew')
    b_note_save_btn = ttk.Button(b_note_frame, text="Save Note", command=lambda: _save_bookmark_note(state)); b_note_save_btn.grid(row=1, column=0, sticky='e', pady=(5,0))
    state['bookmark_note_text'] = b_note_text

    # --- Analysis Tab ---
    analysis_tab.grid_columnconfigure(0, weight=1)
    corr_frame = ttk.LabelFrame(analysis_tab, text="Correlation", padding=5); corr_frame.grid(row=0, column=0, sticky='ew', pady=(0,5))
    corr_frame.grid_columnconfigure(1, weight=1)
    ttk.Label(corr_frame, text="ID:").grid(row=0, column=0)
    corr_combo = ttk.Combobox(corr_frame, textvariable=state['correlation_id_var']); corr_combo.grid(row=0, column=1, sticky='ew', padx=5); state['correlation_id_combo'] = corr_combo
    filter_by_id_btn = ttk.Button(corr_frame, text="Filter by ID", command=lambda: state['filter_entry_var'].set(f'"' + state['correlation_id_var'].get().split(': ', 1)[-1] + '"')); filter_by_id_btn.grid(row=0, column=2)
    auto_filter_corr_check = ttk.Checkbutton(corr_frame, text="Auto-filter on Find", variable=state['auto_filter_correlation_var']); auto_filter_corr_check.grid(row=1, column=1, columnspan=2, pady=(5,0), sticky='w')

    tools_frame = ttk.LabelFrame(analysis_tab, text="Tools", padding=5); tools_frame.grid(row=1, column=0, sticky='ew')
    tools_frame.grid_columnconfigure(0, weight=1); tools_frame.grid_columnconfigure(1, weight=1); tools_frame.grid_columnconfigure(2, weight=1)
    json_btn = ttk.Button(tools_frame, text="Format Selection as JSON", command=lambda: _show_pretty_json_from_selection(state)); json_btn.grid(row=0, column=0, sticky='ew')
    table_btn = ttk.Button(tools_frame, text="View Selection as Table", command=lambda: _show_table_view_from_selection(state)); table_btn.grid(row=0, column=1, sticky='ew', padx=5)
    parse_btn = ttk.Button(tools_frame, text="Parse View with Regex...", command=lambda: _parse_and_show_table(state)); parse_btn.grid(row=0, column=2, sticky='ew')

    # --- View & Stats Tab ---
    view_tab.grid_columnconfigure(0, weight=1)
    view_notebook = ttk.Notebook(view_tab)
    view_notebook.pack(expand=True, fill=tk.BOTH)
    display_sub_tab = ttk.Frame(view_notebook, padding=5)
    options_sub_tab = ttk.Frame(view_notebook, padding=5)
    advanced_sub_tab = ttk.Frame(view_notebook, padding=5)
    stats_sub_tab = ttk.Frame(view_notebook, padding=5)
    view_notebook.add(display_sub_tab, text='Display')
    view_notebook.add(options_sub_tab, text='Options')
    view_notebook.add(advanced_sub_tab, text='Advanced')
    view_notebook.add(stats_sub_tab, text='Statistics')

    display_sub_tab.grid_columnconfigure(0, weight=1)
    view_controls_frame = ttk.LabelFrame(display_sub_tab, text="Display Controls", padding=5); view_controls_frame.grid(row=0, column=0, sticky='ew')
    pause_button = ttk.Button(view_controls_frame, text="Pause", command=lambda: toggle_pause(state)); pause_button.pack(side=tk.LEFT, padx=(0,5)); state.update({'pause_button': pause_button}); Tooltip(pause_button, "Pause or resume the live log updates.")
    refresh_button = ttk.Button(view_controls_frame, text="Refresh", command=lambda: update_content(state, force_update=True)); refresh_button.pack(side=tk.LEFT); Tooltip(refresh_button, "Manually force a refresh of the log view.")
    font_size_frame = ttk.Frame(view_controls_frame); font_size_frame.pack(side=tk.RIGHT, padx=(10,0))
    ttk.Button(font_size_frame, text="A-", command=lambda: change_font_size(state, -1), width=3).pack(side=tk.LEFT)
    ttk.Button(font_size_frame, text="A+", command=lambda: change_font_size(state, 1), width=3).pack(side=tk.LEFT)
    Tooltip(font_size_frame, "Change font size.")

    options_sub_tab.grid_columnconfigure(0, weight=1)
    view_options_frame = ttk.LabelFrame(options_sub_tab, text="General Options", padding=5); view_options_frame.grid(row=0, column=0, sticky='ew', pady=(0,5))
    auto_scroll_check = ttk.Checkbutton(view_options_frame, text="Auto-scroll", variable=state['auto_scroll_var']); auto_scroll_check.pack(side=tk.LEFT, anchor='w'); Tooltip(auto_scroll_check, "Automatically scroll to the bottom as new logs arrive.")
    word_wrap_check = ttk.Checkbutton(view_options_frame, text="Word Wrap (Text View)", variable=state['word_wrap_var'], command=lambda: (record_tb.configure(wrap=tk.WORD if state['word_wrap_var'].get() else tk.NONE), _save_setting(state, 'word_wrap', state['word_wrap_var'].get()))); word_wrap_check.pack(side=tk.LEFT, anchor='w', padx=10)
    
    panel_options_frame = ttk.LabelFrame(options_sub_tab, text="Panel Visibility", padding=5); panel_options_frame.grid(row=1, column=0, sticky='ew')
    show_bookmarks_check = ttk.Checkbutton(panel_options_frame, text="Show Bookmarks Panel", variable=state['show_bookmarks_panel_var'], command=lambda: _toggle_bookmarks_tab(state)); show_bookmarks_check.pack(side=tk.LEFT, anchor='w', padx=(0,10))
    show_notes_check = ttk.Checkbutton(panel_options_frame, text="Show Bookmark Notes", variable=state['show_bookmark_notes_var'], command=lambda: _toggle_bookmark_notes(state)); show_notes_check.pack(side=tk.LEFT, anchor='w', padx=(0,10))
    show_status_check = ttk.Checkbutton(panel_options_frame, text="Show Status Bar", variable=state['show_status_bar_var'], command=lambda: _toggle_status_bar(state)); show_status_check.pack(side=tk.LEFT, anchor='w', padx=(0,10))
    enable_ctx_menu_check = ttk.Checkbutton(panel_options_frame, text="Enable Context Menu", variable=state['enable_context_menu_var'], command=lambda: _toggle_context_menu(state)); enable_ctx_menu_check.pack(side=tk.LEFT, anchor='w')

    advanced_sub_tab.grid_columnconfigure(0, weight=1)
    trace_folding_frame = ttk.LabelFrame(advanced_sub_tab, text="Stack Trace Folding", padding=5); trace_folding_frame.grid(row=0, column=0, sticky='ew', pady=(0,5))
    fold_traces_check = ttk.Checkbutton(trace_folding_frame, text="Enable Folding", variable=state['fold_stack_traces_var'], command=lambda: (update_content(state, force_update=True), _save_setting(state, 'fold_stack_traces', state['fold_stack_traces_var'].get()))); fold_traces_check.pack(side=tk.LEFT, anchor='w')
    fold_mode_combo = ttk.Combobox(trace_folding_frame, textvariable=state['stack_trace_folding_mode_var'], values=['Compact', 'Minimal', 'Full'], width=10); fold_mode_combo.pack(side=tk.LEFT, padx=10); fold_mode_combo.bind("<<ComboboxSelected>>", lambda e: update_content(state, force_update=True))

    time_delta_frame = ttk.LabelFrame(advanced_sub_tab, text="Time Delta Analysis", padding=5); time_delta_frame.grid(row=1, column=0, sticky='ew', pady=(0,5))
    time_delta_check = ttk.Checkbutton(time_delta_frame, text="Show Deltas", variable=state['show_time_deltas_var'], command=lambda: toggle_time_deltas(state)); time_delta_check.pack(side=tk.LEFT, anchor='w')
    time_delta_units_combo = ttk.Combobox(time_delta_frame, textvariable=state['time_delta_units_var'], values=['s', 'ms', 'µs'], width=5); time_delta_units_combo.pack(side=tk.LEFT, padx=10); time_delta_units_combo.bind("<<ComboboxSelected>>", lambda e: update_content(state, force_update=True))
    ts_format_btn = ttk.Button(time_delta_frame, text="Set Timestamp Format...", command=lambda: _set_custom_timestamp_format(state)); ts_format_btn.pack(side=tk.LEFT, padx=5)
    ts_threshold_btn = ttk.Button(time_delta_frame, text="Configure Thresholds...", command=lambda: _configure_delta_thresholds(state)); ts_threshold_btn.pack(side=tk.LEFT)

    stats_sub_tab.grid_columnconfigure(0, weight=1)
    stats_frame = ttk.LabelFrame(stats_sub_tab, text="Statistics", padding=5); stats_frame.grid(row=0, column=0, sticky='ew')
    state['stats_labels']['total'] = ttk.Label(stats_frame, text="Visible Logs: 0"); state['stats_labels']['total'].pack(anchor='w')
    state['stats_labels']['errors'] = ttk.Label(stats_frame, text="Errors: 0"); state['stats_labels']['errors'].pack(anchor='w')
    state['stats_labels']['warnings'] = ttk.Label(stats_frame, text="Warnings: 0"); state['stats_labels']['warnings'].pack(anchor='w')
    state['stats_labels']['debug'] = ttk.Label(stats_frame, text="Debug: 0"); state['stats_labels']['debug'].pack(anchor='w')

    # --- Menubar & Bindings ---
    menubar = Menu(log_root); log_root.config(menu=menubar)
    file_menu = Menu(menubar, tearoff=False); menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Import Logs...", command=lambda: import_logs(state))
    file_menu.add_command(label="Open and Tail Log File...", command=lambda: open_and_tail_log(state))
    file_menu.add_separator()
    file_menu.add_command(label='Save All Logs...', command=lambda: save_logs(state, lambda: '\n'.join(app.record_list), 'Save All Logs As'))
    get_visible = lambda: '\n'.join([state['log_tree'].item(iid, 'values')[1] for iid in state['log_tree'].get_children()]) if state['use_virtual_view_var'].get() else record_tb.get('1.0', tk.END)
    file_menu.add_command(label='Save Visible Logs...', command=lambda: save_logs(state, get_visible, 'Save Visible Logs As'))
    file_menu.add_separator(); file_menu.add_command(label="Clear All Logs...", command=lambda: clear_all_logs(state)); file_menu.add_separator()
    file_menu.add_command(label='Close', command=lambda: close_record(state))
    edit_menu = Menu(menubar, tearoff=False); menubar.add_cascade(label="Edit", menu=edit_menu)
    edit_menu.add_command(label='Copy All Visible', command=lambda: app.clipboard_append(get_visible()))
    edit_menu.add_separator(); edit_menu.add_command(label="Go to Line...", command=lambda: go_to_line(state))
    view_menu = Menu(menubar, tearoff=False); menubar.add_cascade(label="View", menu=view_menu)
    view_menu.add_checkbutton(label="Use Virtualized View (Faster)", variable=state['use_virtual_view_var'], onvalue=True, offvalue=False, command=lambda: toggle_view(state))
    rules_menu = Menu(menubar, tearoff=False); menubar.add_cascade(label="Rules", menu=rules_menu)
    rules_menu.add_command(label="Manage Custom Highlights...", command=lambda: _manage_json_rules(state, HIGHLIGHTS_FILE, "Manage Highlights"))
    rules_menu.add_command(label="Manage Alerts...", command=lambda: _manage_json_rules(state, ALERTS_FILE, "Manage Alerts"))

    log_root.bind("<F3>", lambda e: navigate_search(state, 1)); log_root.bind("<Shift-F3>", lambda e: navigate_search(state, -1))
    log_tree.bind("<<TreeviewSelect>>", lambda e: _update_correlation_ids(state, e))
    log_tree.bind("<Button-3>", lambda e: show_log_context_menu(state, e)); record_tb.bind("<Button-3>", lambda e: show_log_context_menu(state, e))
    log_tree.bind("<Double-1>", lambda e: toggle_bookmark_at_event(state, e)); record_tb.bind("<Double-1>", lambda e: toggle_bookmark_at_event(state, e))

    # --- Final Initialization ---
    toggle_view(state)
    toggle_time_deltas(state) # Set initial column visibility
    _toggle_bookmarks_tab(state) # Set initial bookmark tab visibility
    _toggle_bookmark_notes(state)
    _toggle_status_bar(state)
    _toggle_context_menu(state)
    if session.get('controls_collapsed'): _toggle_controls_panel(state)
    if session.get('tailed_file_path') and os.path.exists(session['tailed_file_path']):
        open_and_tail_log(state)
    else:
        update_content(state, force_update=True)
    _process_queue(state)
