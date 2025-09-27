from tkinter import StringVar, END, BOTH, LEFT, RIGHT, Y, X, Menu
from tkinter import Label, Entry, Listbox, Frame, Button
from tkinter import ttk
import tkinter as tk
from tkinter import messagebox
from dependencies.universal_functions import fill_by_click
import time
import math

# --- Constants for UI and Logic ---
PIN_CHAR = "★"
SEPARATOR_PREFIX = "---"
RECENCY_DECAY_RATE = 0.1  # Higher value = faster decay
FRECENCY_RECENCY_WEIGHT = 0.6
CONTEXT_BOOST = 50

def open_search_functions(app):
    '''
    Standalone popup to search and run functions by their display names.
    '''

    # -------- helpers --------
    def normalize_label(label_text: str) -> str:
        return (
            label_text.replace('!', '')
                      .replace('.', '')
                      .replace('|', ' ')
                      .strip()
                      .casefold()
        )

    def format_pretty_label(label_text: str) -> str:
        cleaned_label = label_text.split('|')[0].strip()
        return f'{cleaned_label[:1].upper()}{cleaned_label[1:]}' if cleaned_label else cleaned_label

    def call_target_function(target_callable_or_tuple):
        if callable(target_callable_or_tuple):
            target_callable_or_tuple()
            return
        if isinstance(target_callable_or_tuple, (tuple, list)) and target_callable_or_tuple:
            function_ref, *function_args = target_callable_or_tuple
            if callable(function_ref):
                function_ref(*function_args)
            return

    def categories_as_dicts(conjoined_categories):
        return {
            category_name: category_map
            for category_name, category_map in conjoined_categories.items()
            if isinstance(category_map, dict)
        }

    def ensure_command_sources(app_ref):
        '''
        Build a comprehensive conjoined_functions_dict from all known mappings
        established by load_function_links, if necessary. Also capture singleton actions.
        '''
        existing = getattr(app_ref, 'conjoined_functions_dict', None)
        base_conjoined = getattr(app_ref, 'conjoined_functions_only', {})

        # Always refresh singleton actions (non-dict entries) for 'All'
        singletons = {}
        if isinstance(base_conjoined, dict):
            for k, v in base_conjoined.items():
                if not isinstance(v, dict):
                    singletons[k] = v
        app_ref.search_singleton_actions = singletons

        if isinstance(existing, dict) and existing:
            return

        # Collect known groups (may not all exist)
        file_map = getattr(app_ref, 'file_functions', {}) or {}
        edit_map = getattr(app_ref, 'edit_functions', {}) or {}
        tools_map = getattr(app_ref, 'tool_functions', {}) or {}
        nlp_map = getattr(app_ref, 'nlp_functions', {}) or {}
        colors_map = getattr(app_ref, 'color_functions', {}) or {}
        links_map = getattr(app_ref, 'links_functions', {}) or {}
        others_map = getattr(app_ref, 'other_functions', {}) or {}
        settings_map = getattr(app_ref, 'settings_fuctions', {}) or {}

        composed = {
            'file': file_map,
            'edit': edit_map,
            'tools': tools_map,
            'NLP': nlp_map,
            'colors': colors_map,
            'links': links_map,
            'options': settings_map if isinstance(settings_map, dict) else {},
            'others': others_map,
        }

        if isinstance(base_conjoined, dict):
            # Merge dict-backed categories from base_conjoined not already present
            for k, v in base_conjoined.items():
                if isinstance(v, dict) and k not in composed:
                    composed[k] = v

        app_ref.conjoined_functions_dict = composed

    def get_all_functions_map():
        """Helper to get a map of all available functions with pretty labels."""
        if hasattr(app, '_search_all_functions_map') and app._search_all_functions_map:
            return app._search_all_functions_map

        ensure_command_sources(app)
        conjoined_map = getattr(app, 'conjoined_functions_dict', {})
        categories_map = categories_as_dicts(conjoined_map)

        merged_map = {}
        for category_dict in categories_map.values():
            merged_map.update(category_dict)

        singletons = getattr(app, 'search_singleton_actions', {}) or {}
        merged_map.update(singletons)

        all_label_to_target = {}
        shortcut_map = {}
        for raw_label, target in merged_map.items():
            pretty_label = format_pretty_label(raw_label)
            all_label_to_target[pretty_label] = target
            
            # Extract and map shortcut
            if '|' in raw_label:
                try:
                    shortcut = raw_label.split('|')[1].strip('()')
                    shortcut_map[shortcut.lower()] = pretty_label
                except IndexError:
                    pass

        app._search_all_functions_map = all_label_to_target
        app._search_shortcut_map = shortcut_map
        return app._search_all_functions_map

    def get_contextual_suggestions():
        suggestions = []
        try:
            # Text selection context
            if app.EgonTE.tag_ranges('sel'):
                suggestions.extend(['Copy', 'Cut', 'Translate', 'Correct writing', 'Bold', 'Italics', 'Underline'])
            
            # Unsaved changes context
            if getattr(app, 'text_changed', False):
                suggestions.extend(['Save', 'Save as'])

            # File type context
            file_name = getattr(app, 'file_name', '')
            if file_name and file_name.endswith('.py'):
                suggestions.append('Run code')

        except Exception:
            pass # Fail silently if app state is not available
        return suggestions

    def get_mode_source_dict(mode_key: str):
        ensure_command_sources(app)
        conjoined_map = getattr(app, 'conjoined_functions_dict', {})
        categories_map = categories_as_dicts(conjoined_map)

        requested_key = (mode_key or '').strip().casefold()

        if requested_key == 'pinned':
            pinned_labels = get_pinned_functions()
            all_functions = get_all_functions_map()
            pinned_map = {}
            for label in pinned_labels:
                if label in all_functions:
                    pinned_map[label] = all_functions[label]
            return pinned_map

        if requested_key == 'smart':
            mru_data = {}
            try:
                if hasattr(app, 'data') and isinstance(app.data, dict):
                    mru_data = app.data.get('search_functions_mru', {})
                    if not isinstance(mru_data, dict):
                        mru_data = {}
            except Exception:
                mru_data = {}

            if not mru_data:
                return {}

            all_functions = get_all_functions_map()
            scored_labels = []
            now = time.time()
            
            # Exponential decay for recency, normalized frequency
            counts = [d.get('count', 1) for d in mru_data.values()]
            max_count = max(counts) if counts else 1

            for label, data in mru_data.items():
                if label not in all_functions: continue

                count_score = data.get('count', 1) / max_count
                
                time_delta_days = (now - data.get('last_used', now)) / (60 * 60 * 24)
                recency_score = math.exp(-RECENCY_DECAY_RATE * time_delta_days)
                
                score = (FRECENCY_RECENCY_WEIGHT * recency_score) + ((1 - FRECENCY_RECENCY_WEIGHT) * count_score)
                scored_labels.append((label, score))

            scored_labels.sort(key=lambda x: x[1], reverse=True)
            
            smart_map = {}
            for label, score in scored_labels:
                smart_map[label] = all_functions[label]
            return smart_map

        if requested_key == 'all':
            # For 'All' mode, we now return a structured list with separators
            structured_list = []
            for category_name, category_dict in sorted(categories_map.items()):
                if category_dict:
                    separator = f'{SEPARATOR_PREFIX} {category_name.upper()} {SEPARATOR_PREFIX}'
                    structured_list.append(separator)
                    structured_list.extend(sorted(category_dict.keys(), key=lambda k: normalize_label(k)))

            singletons = getattr(app, 'search_singleton_actions', {}) or {}
            if singletons:
                structured_list.append(f'{SEPARATOR_PREFIX} OTHERS {SEPARATOR_PREFIX}')
                structured_list.extend(sorted(singletons.keys(), key=lambda k: normalize_label(k)))

            # The 'source' is now the structured list itself
            return structured_list

        for category_name, category_dict in categories_map.items():
            if category_name.strip().casefold() == requested_key:
                return category_dict
        return {}

    def build_label_maps(source, sort=True):
        label_list = []
        label_to_target_map = {}
        normalized_to_label_map = {}

        if isinstance(source, list):
            # This is our structured list for 'All' mode
            all_funcs_map = get_all_functions_map() # Safe to call now
            for item in source:
                if item.startswith(SEPARATOR_PREFIX):
                    label_list.append(item)
                else:
                    pretty_label = format_pretty_label(item)
                    label_list.append(pretty_label)
                    if pretty_label in all_funcs_map:
                        label_to_target_map[pretty_label] = all_funcs_map[pretty_label]
                        normalized_to_label_map[normalize_label(pretty_label)] = pretty_label
            return label_list, label_to_target_map, normalized_to_label_map

        source_dict = source if isinstance(source, dict) else {}
        for raw_label_text, target in source_dict.items():
            pretty_label = format_pretty_label(raw_label_text)
            label_to_target_map[pretty_label] = target
            normalized_to_label_map[normalize_label(pretty_label)] = pretty_label
            label_list.append(pretty_label)

        if sort:
            label_list = sorted(set(label_list), key=lambda s: s.casefold())
        else: # For Smart/Pinned mode, respect the pre-sorted order
            label_list = list(source_dict.keys())

        return label_list, label_to_target_map, normalized_to_label_map

    def fuzzy_score(query, text):
        query, text = query.lower(), text.lower()
        score = 0
        m = 0
        n = 0
        consecutive_bonus = 0

        while m < len(query) and n < len(text):
            if query[m] == text[n]:
                score += 1 + consecutive_bonus
                if n == 0 or text[n-1] in ' -_(': # Word start bonus
                    score += 10
                consecutive_bonus += 1
                m += 1
            else:
                consecutive_bonus = 0
            n += 1

        if m != len(query):
            return 0

        # Normalize score
        score = score / len(text)
        if text.startswith(query):
            score += 20 # Prefix bonus
        return score

    def ranked_filter_labels(all_labels, query_text: str, *, strategy: str = 'ranked'):
        # For empty query, show a prioritized list
        if not query_text:
            pinned = get_pinned_functions()
            contextual = get_contextual_suggestions()
            
            # Combine and de-duplicate
            ordered_suggestions = []
            seen = set()
            for label in pinned + contextual:
                if label not in seen:
                    ordered_suggestions.append(label)
                    seen.add(label)

            # For All and Smart modes, show suggestions on top of the full list
            if app.search_mode_variable.get() in ('All', 'Smart'):
                others = [lbl for lbl in all_labels if lbl not in seen]
                return ordered_suggestions + others
            return list(all_labels)

        # Shortcut search
        shortcut_map = getattr(app, '_search_shortcut_map', {})
        if query_text.lower() in shortcut_map:
            return [shortcut_map[query_text.lower()]]

        qn = normalize_label(query_text)
        
        if strategy == 'prefix':
            results = [label for label in all_labels if not label.startswith(SEPARATOR_PREFIX) and normalize_label(label).startswith(qn)]
        elif strategy == 'contains':
            results = [label for label in all_labels if not label.startswith(SEPARATOR_PREFIX) and qn in normalize_label(label)]
        else:
            # Fuzzy ranking
            scored_labels = []
            contextual_suggestions = get_contextual_suggestions()
            for label in all_labels:
                if label.startswith(SEPARATOR_PREFIX): continue
                score = fuzzy_score(qn, normalize_label(label))
                if label in contextual_suggestions:
                    score += CONTEXT_BOOST
                if score > 0:
                    scored_labels.append((label, score))
            scored_labels.sort(key=lambda x: x[1], reverse=True)
            results = [label for label, score in scored_labels]

        # Elevate pinned items within the search results
        pinned_labels = get_pinned_functions()
        pinned_results = [label for label in results if label in pinned_labels]
        other_results = [label for label in results if label not in pinned_labels]
        return pinned_results + other_results

    # -------- persistence helpers --------
    def get_pinned_functions():
        """Safely retrieves the list of pinned function labels."""
        try:
            if hasattr(app, 'data') and isinstance(app.data, dict):
                pinned = app.data.get('search_functions_pinned', [])
                return pinned if isinstance(pinned, list) else []
        except Exception:
            return []

    def toggle_pin_status(label_to_toggle: str):
        """Adds or removes a function label from the pinned list."""
        try:
            if not hasattr(app, 'data') or not isinstance(app.data, dict):
                app.data = {}
            if 'search_functions_pinned' not in app.data or not isinstance(app.data['search_functions_pinned'], list):
                app.data['search_functions_pinned'] = []
            
            pinned_list = app.data['search_functions_pinned']
            
            if label_to_toggle in pinned_list:
                pinned_list.remove(label_to_toggle)
            else:
                pinned_list.append(label_to_toggle)
            
            do_apply_filter()
        except Exception:
            pass

    def add_to_mru(label_text: str):
        """Adds a function label to the MRU list in app.data."""
        try:
            if not hasattr(app, 'data') or not isinstance(app.data, dict):
                app.data = {}

            if 'search_functions_mru' not in app.data or not isinstance(app.data['search_functions_mru'], dict):
                app.data['search_functions_mru'] = {}

            mru_data = app.data['search_functions_mru']
            now = time.time()

            if label_text in mru_data:
                mru_data[label_text]['count'] = mru_data[label_text].get('count', 0) + 1
                mru_data[label_text]['last_used'] = now
            else:
                mru_data[label_text] = {'count': 1, 'last_used': now}

            # Prune old entries if list grows too large
            max_mru_size = 50
            if len(mru_data) > max_mru_size:
                sorted_by_lru = sorted(mru_data.items(), key=lambda item: item[1].get('last_used', 0))
                for i in range(len(mru_data) - max_mru_size):
                    del mru_data[sorted_by_lru[i][0]]

        except Exception:
            pass

    def restore_state():
        try:
            state = getattr(app, 'data', None)
            if not isinstance(state, dict):
                return '', 'All'
            sf = state.get('search_functions_state', {})
            if not isinstance(sf, dict):
                return '', 'All'
            q = str(sf.get('query') or '')
            m = str(sf.get('mode') or 'All')
            return q, m
        except Exception:
            return '', 'All'

    def save_state():
        try:
            if not hasattr(app, 'data') or not isinstance(app.data, dict):
                app.data = {}
            if 'search_functions_state' not in app.data or not isinstance(app.data['search_functions_state'], dict):
                app.data['search_functions_state'] = {}
            app.data['search_functions_state']['query'] = app.search_entry.get()
            app.data['search_functions_state']['mode'] = app.search_mode_variable.get()
        except Exception:
            pass

    def clear_pinned_functions():
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all pinned functions?"):
            try:
                if hasattr(app, 'data') and isinstance(app.data, dict):
                    app.data['search_functions_pinned'] = []
                    do_apply_filter()
            except Exception:
                pass

    def clear_smart_history():
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all Smart History data?"):
            try:
                if hasattr(app, 'data') and isinstance(app.data, dict):
                    app.data['search_functions_mru'] = {}
                    do_apply_filter()
            except Exception:
                pass

    # -------- UI callbacks --------
    def get_selected_label(strip_star=True):
        """Gets the currently selected label, optionally stripping the pin marker."""
        selection_indices = app.functions_listbox.curselection()
        if not selection_indices:
            if app.functions_listbox.size() > 0:
                selected_text = app.functions_listbox.get(0)
            else:
                return None
        else:
            selected_text = app.functions_listbox.get(selection_indices[0])

        if strip_star:
            return selected_text.lstrip(f'{PIN_CHAR} ')
        return selected_text

    def toggle_pin_selected(event=None):
        selected_label = get_selected_label(strip_star=True)
        if not selected_label or selected_label.startswith(SEPARATOR_PREFIX):
            return
        
        # Preserve selection
        current_selection_index = app.functions_listbox.curselection()
        
        toggle_pin_status(selected_label)
        
        # Restore selection
        if current_selection_index:
            try:
                app.functions_listbox.selection_set(current_selection_index[0])
                app.functions_listbox.focus_set()
            except tk.TclError:
                pass # Item may no longer be at that index

    def set_run_button_state():
        try:
            has_items = app.functions_listbox.size() > 0
            app.run_button.configure(state=('normal' if has_items else 'disabled'))
        except Exception:
            pass

    def populate_listbox(visible_labels):
        app.functions_listbox.delete(0, END)
        pinned_list = get_pinned_functions()
        for i, label_text in enumerate(visible_labels):
            display_text = f"{PIN_CHAR} {label_text}" if label_text in pinned_list else label_text
            app.functions_listbox.insert(END, display_text)
            
            try:
                if label_text.startswith(SEPARATOR_PREFIX):
                    app.functions_listbox.itemconfig(i, {
                        'bg': '#eee', 
                        'fg': '#333', 
                        'selectbackground': '#eee', 
                        'selectforeground': '#333'
                    })
                elif label_text in pinned_list:
                    app.functions_listbox.itemconfig(i, {'fg': 'goldenrod'})
            except tk.TclError:
                pass # Widget might be destroyed

        if visible_labels:
            # Select the first non-separator item
            first_selectable = -1
            for i, item in enumerate(visible_labels):
                if not item.startswith(SEPARATOR_PREFIX):
                    first_selectable = i
                    break
            
            if first_selectable != -1:
                app.functions_listbox.selection_clear(0, END)
                app.functions_listbox.selection_set(first_selectable)
                app.functions_listbox.activate(first_selectable)
                app.functions_listbox.see(first_selectable)

        results_count = sum(1 for item in visible_labels if not item.startswith(SEPARATOR_PREFIX))
        results_count_variable.set(f'{results_count} result{"s" if results_count != 1 else ""}')
        set_run_button_state()
        on_list_select() # Update docstring for initial selection

    def refresh_sources_for_mode():
        display_mode_text = app.search_mode_variable.get() or 'All'
        source = get_mode_source_dict(display_mode_text)
        is_smart_mode = (display_mode_text or '').strip().casefold() == 'smart'
        is_all_mode = (display_mode_text or '').strip().casefold() == 'all'
        is_pinned_mode = (display_mode_text or '').strip().casefold() == 'pinned'
        
        sort_needed = not (is_smart_mode or is_all_mode or is_pinned_mode)

        app.search_labels, app.search_label_to_target, app.search_normalized_to_label = build_label_maps(
            source, sort=sort_needed
        )

    # Parse search syntax: ^=prefix, *=contains, mode:<name> (e.g., mode:tools)
    def parse_search_syntax(raw_query: str):
        # strip leading spaces
        query = (raw_query or '').lstrip()
        strategy = 'ranked'
        new_mode = None

        # detect ^= and *= prefixes
        if query.startswith('^='):
            strategy = 'prefix'
            query = query[2:].lstrip()
        elif query.startswith('*='):
            strategy = 'contains'
            query = query[2:].lstrip()

        # detect mode:token anywhere (token is up to whitespace)
        tokens = [t for t in query.split() if t]
        filtered_tokens = []
        for t in tokens:
            low = t.lower()
            if low.startswith('mode:') and len(t) > 5:
                candidate = t[5:]
                # Allow common names regardless of case; canonicalize 'nlp' -> 'NLP'
                candidate_norm = candidate.strip()
                # We'll pick from available display values later in do_apply_filter
                new_mode = candidate_norm
                # do not include this token in visible filter terms
            else:
                filtered_tokens.append(t)
        # Rebuild query without the mode token
        effective_query = ' '.join(filtered_tokens).strip()
        return effective_query, strategy, new_mode

    # Debounced apply for smooth typing
    debounce_state = {'id': None}
    def do_apply_filter():
        # Apply search syntax before filtering
        raw = app.search_entry.get()
        effective_query, strategy, new_mode_candidate = parse_search_syntax(raw)

        # Possibly adjust mode from syntax without opening the combobox
        try:
            values = list(mode_combobox['values'])
        except Exception:
            values = []
        current_mode = app.search_mode_variable.get()
        desired_mode = current_mode

        if new_mode_candidate:
            # Find a display value match ignoring case; also map 'nlp' properly
            for v in values:
                if str(v).strip().casefold() == new_mode_candidate.strip().casefold():
                    desired_mode = v
                    break

        if desired_mode != current_mode:
            app.search_mode_variable.set(desired_mode)
            refresh_sources_for_mode()

        # Now filter according to strategy with the effective query
        is_all_mode_with_no_query = (app.search_mode_variable.get().lower() == 'all' and not effective_query)
        if is_all_mode_with_no_query:
            visible_labels = app.search_labels
        else:
            visible_labels = ranked_filter_labels(app.search_labels, effective_query, strategy=strategy)
        populate_listbox(visible_labels)

    def apply_filter(event=None):
        # Persist query on every change (user typing only)
        save_state()
        if debounce_state['id']:
            try:
                app.search_entry.after_cancel(debounce_state['id'])
            except Exception:
                pass
        debounce_state['id'] = app.search_entry.after(120, do_apply_filter)

    def run_selected_command():
        chosen_label = get_selected_label(strip_star=True)
        if not chosen_label or chosen_label.startswith(SEPARATOR_PREFIX): return

        target_callable = app.search_label_to_target.get(chosen_label)
        if target_callable is None:
            return

        add_to_mru(chosen_label)
        close_search_window()
        call_target_function(target_callable)

    def on_return_key(event=None):
        run_selected_command()

    def on_double_click(event=None):
        run_selected_command()

    def on_escape_key(event=None):
        close_search_window()

    def on_list_select(event=None):
        selected_text = get_selected_label(strip_star=False)
        if not selected_text:
            update_docstring_display()
            set_run_button_state()
            return

        if selected_text.startswith(SEPARATOR_PREFIX):
            selection_indices = app.functions_listbox.curselection()
            if not selection_indices: return
            selected_index = selection_indices[0]

            next_selectable = -1
            for i in range(selected_index + 1, app.functions_listbox.size()):
                if not app.functions_listbox.get(i).startswith(SEPARATOR_PREFIX):
                    next_selectable = i
                    break
            
            if next_selectable == -1:
                for i in range(selected_index - 1, -1, -1):
                    if not app.functions_listbox.get(i).startswith(SEPARATOR_PREFIX):
                        next_selectable = i
                        break

            app.functions_listbox.selection_clear(0, END)
            if next_selectable != -1:
                app.functions_listbox.selection_set(next_selectable)
                app.functions_listbox.activate(next_selectable)
            return
        
        update_docstring_display()
        set_run_button_state()

    def update_docstring_display(*args):
        if not docstring_viewer: return
        docstring_viewer.config(state='normal')
        docstring_viewer.delete('1.0', END)

        chosen_label = get_selected_label(strip_star=True)

        if not chosen_label or chosen_label.startswith(SEPARATOR_PREFIX):
            docstring_viewer.insert('1.0', 'Select a function to see its description.')
            docstring_viewer.config(state='disabled')
            return

        target = app.search_label_to_target.get(chosen_label)
        docstring = None

        if target:
            func_to_check = target[0] if isinstance(target, (tuple, list)) else target
            if hasattr(func_to_check, '__doc__') and func_to_check.__doc__:
                docstring = func_to_check.__doc__

        display_text = "No description available."
        if docstring:
            lines = docstring.strip().split('\n')
            if len(lines) > 1:
                min_indent = float('inf')
                for line in lines[1:]:
                    stripped = line.lstrip()
                    if stripped:
                        indent = len(line) - len(stripped)
                        min_indent = min(min_indent, indent)
                
                if min_indent != float('inf'):
                    dedented_lines = [lines[0].strip()] + [l[min_indent:] for l in lines[1:]]
                    display_text = '\n'.join(dedented_lines)
                else:
                    display_text = '\n'.join(l.strip() for l in lines)
            else:
                display_text = lines[0].strip()

        docstring_viewer.insert('1.0', display_text)
        docstring_viewer.config(state='disabled')

    # Entry Up/Down navigates list selection without touching Entry (prevents cycles)
    def on_entry_up_down(delta: int):
        try:
            size = app.functions_listbox.size()
            if size <= 0: return 'break'

            cur = 0
            sel = app.functions_listbox.curselection()
            if sel: cur = sel[0]

            # Find next valid item, skipping separators
            next_idx = cur + delta
            while 0 <= next_idx < size and app.functions_listbox.get(next_idx).startswith(SEPARATOR_PREFIX):
                next_idx += delta

            if 0 <= next_idx < size:
                app.functions_listbox.selection_clear(0, END)
                app.functions_listbox.selection_set(next_idx)
                app.functions_listbox.activate(next_idx)
                app.functions_listbox.see(next_idx)
            
            set_run_button_state()
            return 'break'
        except Exception:
            return 'break'

    # Small detail: clear-search button next to the entry
    def clear_search():
        try:
            app.search_entry.delete(0, END)
        except Exception:
            pass
        save_state()
        do_apply_filter()

    # Visual polish: move mode quickly (Alt+Up/Down) without opening combobox
    def nudge_mode(delta: int):
        try:
            values = list(mode_combobox['values'])
            cur = app.search_mode_variable.get()
            try:
                idx = values.index(cur)
            except ValueError:
                idx = 0
            nxt = min(len(values) - 1, max(0, idx + delta))
            if nxt != idx:
                app.search_mode_variable.set(values[nxt])
                refresh_sources_for_mode()
                save_state()
                do_apply_filter()
            return 'break'
        except Exception:
            return 'break'

    def show_context_menu(event):
        try:
            # Select the item under the cursor
            listbox = event.widget
            index = listbox.nearest(event.y)
            listbox.selection_clear(0, END)
            listbox.selection_set(index)
            listbox.activate(index)

            selected_label = get_selected_label(strip_star=True)
            if not selected_label or selected_label.startswith(SEPARATOR_PREFIX):
                return

            context_menu = Menu(search_root, tearoff=0)
            is_pinned = selected_label in get_pinned_functions()
            pin_label_text = f"Unpin {PIN_CHAR}" if is_pinned else f"Pin {PIN_CHAR}"
            context_menu.add_command(label=pin_label_text, command=toggle_pin_selected)
            
            context_menu.add_separator()

            clear_menu = Menu(context_menu, tearoff=0)
            clear_menu.add_command(label="Clear Pinned Functions", command=clear_pinned_functions)
            clear_menu.add_command(label="Clear Smart History", command=clear_smart_history)
            context_menu.add_cascade(label="Clear History...", menu=clear_menu)

            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            try:
                context_menu.grab_release()
            except Exception:
                pass

    def close_search_window():
        # Save final state
        try:
            save_state()
        except Exception:
            pass
        # Cancel pending debounce to avoid callbacks after destroy
        try:
            if debounce_state.get('id'):
                app.search_entry.after_cancel(debounce_state['id'])
                debounce_state['id'] = None
        except Exception:
            pass
        app.search_active = False
        try:
            app.opened_windows.remove(search_root)
        except Exception:
            pass
        try:
            search_root.destroy()
        except Exception:
            pass

    # -------- ensure sources present --------
    ensure_command_sources(app)
    app._search_all_functions_map = None  # Initialize cache
    app._search_shortcut_map = None

    # -------- popup root creation (prefer enhanced UI builders with singleton name) --------
    search_root = None
    make_window = getattr(app, 'make_pop_ups_window', None)
    if callable(make_window):
        try:
            search_root = make_window(
                function=lambda: None,
                custom_title='Search functions',
                name='search_functions_popup',
            )
        except Exception:
            search_root = None

    if search_root is None:
        parent_widget = getattr(app, 'tk', None) or getattr(app, 'root', None)
        if not isinstance(parent_widget, tk.Misc):
            parent_widget = tk._get_default_root() or tk.Tk()
        search_root = tk.Toplevel(parent_widget)
        search_root.title((getattr(app, 'title_struct', '') + 'Search functions'))
        if hasattr(app, 'st_value'):
            try: search_root.attributes('-alpha', app.st_value)
            except Exception: pass
        try: app.opened_windows.append(search_root)
        except Exception: pass

    # -------- window setup --------
    app.search_active = True
    search_root.protocol('WM_DELETE_WINDOW', close_search_window)

    try:
        if getattr(app, 'limit_w_s', None) and app.limit_w_s.get():
            search_root.resizable(False, False)
        else:
            search_root.maxsize(700, int(search_root.winfo_screenheight()))
    except Exception:
        pass

    # -------- widgets --------
    bg_color = getattr(app, 'dynamic_bg', search_root.cget('bg'))
    fg_color = getattr(app, 'dynamic_text', 'black')
    btn_color = getattr(app, 'dynamic_button', search_root.cget('bg'))

    # Main container frame
    main_frame = Frame(search_root, bg=bg_color)
    main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

    title_label = Label(
        main_frame,
        text='Search Functions',
        font='arial 14 underline',
        fg=fg_color,
        bg=bg_color,
    )
    title_label.pack(pady=(0, 10))

    # --- Search input and mode selector ---
    search_controls_frame = Frame(main_frame, bg=bg_color)
    search_controls_frame.pack(fill=X)

    search_from_label = Label(
        search_controls_frame,
        text='From:',
        font='arial 10',
        fg=fg_color,
        bg=bg_color,
    )
    search_from_label.pack(side=LEFT, padx=(0, 5))

    categories_list = list(categories_as_dicts(app.conjoined_functions_dict).keys())
    categories_list = sorted(categories_list, key=lambda s: s.casefold())
    display_modes_list = ['All', 'Smart', 'Pinned'] + categories_list

    restored_query, restored_mode = restore_state()
    app.search_mode_variable = StringVar(value=(restored_mode if restored_mode in display_modes_list else 'All'))
    mode_combobox = ttk.Combobox(
        search_controls_frame,
        width=12,
        textvariable=app.search_mode_variable,
        state='readonly',
        style='TCombobox'
    )
    mode_combobox['values'] = tuple(display_modes_list)
    mode_combobox.pack(side=LEFT, padx=(0, 5))

    app.search_entry = Entry(search_controls_frame)
    app.search_entry.pack(side=LEFT, fill=X, expand=True)

    clear_button = Button(
        search_controls_frame,
        text='×',
        bd=1, relief='flat',
        padx=4, pady=0,
        fg=fg_color,
        bg=btn_color,
        command=clear_search
    )
    clear_button.pack(side=LEFT, padx=(5, 0))

    try:
        if restored_query:
            app.search_entry.insert(0, restored_query)
        app.search_entry.focus_set()
    except Exception:
        pass

    # --- Hint label (compact and wrapping) ---
    hint_label = Label(
        main_frame,
        text='Syntax: ^=prefix, *=contains, mode:<category>\nShortcuts: Ctrl+P (pin), Alt+Up/Down (mode), Ctrl+F (focus)',
        font='arial 8',
        fg='#666',
        bg=bg_color,
        justify=LEFT,
        wraplength=300  # Adjust as needed
    )
    hint_label.pack(pady=(4, 8), fill=X)

    # --- Results listbox ---
    lists_container_frame = Frame(main_frame)
    lists_container_frame.pack(fill=BOTH, expand=True)

    app.functions_listbox = Listbox(lists_container_frame, width=30, height=10)
    app.functions_listbox.pack(side=LEFT, fill=BOTH, expand=True)

    list_scrollbar = ttk.Scrollbar(lists_container_frame, command=app.functions_listbox.yview)
    list_scrollbar.pack(side=RIGHT, fill=Y)
    app.functions_listbox.configure(yscrollcommand=list_scrollbar.set)

    # --- Docstring Viewer ---
    docstring_viewer = None
    try:
        make_textbox = getattr(app, 'make_rich_textbox', None)
        if callable(make_textbox):
            docstring_frame, docstring_viewer, _ = make_textbox(
                parent_container=main_frame,
                format='txt',
                size=(30, 4),
                wrap=tk.WORD,
                bd=1,
                relief='sunken'
            )
            docstring_frame.pack(fill=X, pady=(5, 0))
            docstring_viewer.config(state='disabled', font='arial 9', bg=bg_color, fg=fg_color)
    except Exception:
        docstring_viewer = None # Ensure it exists for callbacks

    # --- Empty state label (centered, wrapping) ---
    empty_state_label = Label(
        app.functions_listbox,  # Place inside listbox to overlay
        text='No results found.\nTry a different query or category.',
        font='arial 9 italic',
        fg='#888',
        bg=app.functions_listbox.cget('bg'),
        justify=tk.CENTER
    )

    # --- Footer ---
    footer_frame = Frame(main_frame, bg=bg_color)
    footer_frame.pack(fill=X, pady=(5, 0))

    app.run_button = Button(
        footer_frame,
        text='Run Function',
        command=run_selected_command,
        fg=fg_color,
        bg=btn_color,
    )
    app.run_button.pack(side=LEFT, padx=(0, 4))

    results_count_variable = StringVar(value='')
    results_count_label = Label(
        footer_frame,
        textvariable=results_count_variable,
        fg=fg_color,
        bg=bg_color,
    )
    results_count_label.pack(side=RIGHT, padx=4)

    # -------- bindings --------
    mode_combobox.bind('<<ComboboxSelected>>', lambda event: (refresh_sources_for_mode(), save_state(), do_apply_filter()))
    app.search_entry.bind('<KeyRelease>', apply_filter)
    app.search_entry.bind('<Return>', on_return_key)
    app.functions_listbox.bind('<Double-Button-1>', on_double_click)
    app.functions_listbox.bind('<Return>', on_return_key)
    app.functions_listbox.bind('<<ListboxSelect>>', on_list_select)
    app.functions_listbox.bind('<Button-3>', show_context_menu)
    search_root.bind('<Escape>', on_escape_key)
    search_root.bind('<Control-f>', lambda e: (app.search_entry.focus_set(), app.search_entry.selection_range(0, END)))
    search_root.bind('<Control-l>', lambda e: (app.functions_listbox.focus_set(), 'break'))
    search_root.bind('<Control-p>', toggle_pin_selected)
    app.search_entry.bind('<Control-Return>', lambda e: (run_selected_command(), 'break'))
    app.search_entry.bind('<Up>', lambda e: on_entry_up_down(-1))
    app.search_entry.bind('<Down>', lambda e: on_entry_up_down(+1))
    search_root.bind('<Alt-Up>', lambda e: nudge_mode(-1))
    search_root.bind('<Alt-Down>', lambda e: nudge_mode(+1))

    # -------- initial data --------
    refresh_sources_for_mode()

    def _update_results_header_and_empty_state():
        try:
            mode_name = app.search_mode_variable.get()
        except Exception:
            mode_name = 'All'
        try:
            count_text = results_count_variable.get()
            if count_text:
                results_count_variable.set(f'{count_text} in {mode_name}')
        except Exception:
            pass
        try:
            size = app.functions_listbox.size()
            has_real_items = any(not item.startswith(SEPARATOR_PREFIX) for item in app.functions_listbox.get(0, END))
            if not has_real_items:
                empty_state_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            else:
                empty_state_label.place_forget()
        except Exception:
            pass

    # Wrap populate_listbox to also adjust header/empty-state
    orig_populate = populate_listbox
    def populate_listbox(visible_labels):
        orig_populate(visible_labels)
        _update_results_header_and_empty_state()
    do_apply_filter()

    app.search_widgets = (title_label, search_from_label, app.run_button)
    app.search_bg = search_root

    try:
        search_root.update_idletasks()
        app.limit_list.append([search_root, [search_root.winfo_width(), search_root.winfo_height()]])
    except Exception:
        pass
