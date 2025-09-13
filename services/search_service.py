from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Tuple, Optional
import re


@dataclass
class SearchService:
    '''
    Find/replace/highlight service for a Tkinter Text widget.

    This service performs:
      - Plain and regex finds with optional case sensitivity and whole-word matching.
      - Highlighting all matches and marking the current match.
      - Next/previous navigation across found matches.
      - Replace (single/all) with optional regex backreferences.
      - Basic navigation helpers (go to offset or line/column).
    It expects the hosting app to expose:
      - app.EgonTE: a tk.Text-compatible widget
      - app.highlight_search_c: a (background, foreground) tuple for highlight colors
    '''
    app: Any  # expects access to .EgonTE (tk.Text) and colors like app.highlight_search_c

    # runtime state for navigation
    last_needle: str = ''
    last_flags: Tuple[bool, bool, bool] = (False, False, False)  # (case_sensitive, whole_word, regex)
    last_index_spans: Optional[List[Tuple[str, str]]] = None  # tk index spans
    current_match_index: int = 0
    haystack_snapshot: Optional[str] = None
    search_in_selection: bool = False
    selection_bounds: Optional[Tuple[str, str]] = None

    # ---------- pure find logic ----------
    @staticmethod
    def is_word_char(character: str) -> bool:
        '''
        Return True if character is considered part of a word (alnum or underscore), else False.
        '''
        return character.isalnum() or character == '_'

    @classmethod
    def is_word_boundary(cls, text_value: str, span_start: int, span_end: int) -> bool:
        '''
        Return True if the [span_start, span_end) boundaries fall on non-word characters.
        '''
        char_before = text_value[span_start - 1] if span_start > 0 else ''
        char_after = text_value[span_end] if span_end < len(text_value) else ''
        return (not char_before or not cls.is_word_char(char_before)) and (not char_after or not cls.is_word_char(char_after))

    @classmethod
    def find_all_offsets(
        cls,
        haystack_text: str,
        needle_text: str,
        *,
        case_sensitive: bool,
        whole_word: bool,
        regex: bool = False,
    ) -> List[Tuple[int, int]]:
        '''
        Find all occurrences of needle_text in haystack_text and return a list of (start, end) offsets.

        Parameters:
            haystack_text: the source string to search in
            needle_text: the pattern or literal substring to search
            case_sensitive: when False, perform a case-insensitive match
            whole_word: when True, only accept matches with word boundaries
            regex: when True, treat needle_text as a regular expression
        '''
        if not haystack_text or not needle_text:
            return []

        if regex:
            regex_flags = 0 if case_sensitive else re.IGNORECASE
            try:
                compiled_pattern = re.compile(needle_text, regex_flags)
            except re.error:
                return []
            result_spans: List[Tuple[int, int]] = []
            for match_obj in compiled_pattern.finditer(haystack_text):
                span_start, span_end = match_obj.start(), match_obj.end()
                if not whole_word or cls.is_word_boundary(haystack_text, span_start, span_end):
                    result_spans.append((span_start, span_end))
            return result_spans

        prepared_haystack = haystack_text if case_sensitive else haystack_text.lower()
        prepared_needle = needle_text if case_sensitive else needle_text.lower()
        result_spans: List[Tuple[int, int]] = []
        search_from = 0
        needle_length = len(prepared_needle)
        while True:
            found_at = prepared_haystack.find(prepared_needle, search_from)
            if found_at == -1:
                break
            found_end = found_at + needle_length
            if not whole_word or cls.is_word_boundary(haystack_text, found_at, found_end):
                result_spans.append((found_at, found_end))
            search_from = found_end
        return result_spans

    # ---------- tk index helpers ----------
    @staticmethod
    def offset_to_index(offset_value: int) -> str:
        '''
        Convert a 0-based character offset to a Tk Text index string relative to '1.0'.
        '''
        return f'1.0+{max(0, offset_value)}c'

    @classmethod
    def offsets_to_indices(cls, spans: List[Tuple[int, int]]) -> List[Tuple[str, str]]:
        '''
        Convert a list of (start_offset, end_offset) into Tk Text index spans.
        '''
        return [(cls.offset_to_index(start_off), cls.offset_to_index(end_off)) for (start_off, end_off) in spans]

    # ---------- tag management ----------
    def configure_tags(self) -> None:
        '''
        Ensure the highlight tags exist with current theme colors.
        '''
        try:
            bg_color, fg_color = getattr(self.app, 'highlight_search_c', ('yellow', 'black'))
            self.app.EgonTE.tag_config('highlight_all_result', background=bg_color, foreground=fg_color)
            self.app.EgonTE.tag_config('current_match', background=fg_color, foreground=bg_color, underline=1)
        except Exception:
            pass

    def clear_all_tags(self) -> None:
        '''
        Remove all highlight tags from the entire buffer.
        '''
        try:
            self.app.EgonTE.tag_remove('highlight_all_result', '1.0', 'end')
            self.app.EgonTE.tag_remove('current_match', '1.0', 'end')
        except Exception:
            pass

    def apply_all_highlights(self, index_spans: List[Tuple[str, str]]) -> None:
        '''
        Apply the 'highlight_all_result' tag to all provided index spans.
        '''
        self.configure_tags()
        self.clear_all_tags()
        for start_index, end_index in index_spans:
            try:
                self.app.EgonTE.tag_add('highlight_all_result', start_index, end_index)
            except Exception:
                continue

    def mark_current(self, match_index: int) -> None:
        '''
        Remove any existing 'current_match' tag and apply it to the match at match_index.
        Also moves the cursor and ensures visibility.
        '''
        try:
            self.app.EgonTE.tag_remove('current_match', '1.0', 'end')
            if not self.last_index_spans:
                return
            match_index = max(0, min(match_index, len(self.last_index_spans) - 1))
            start_index, end_index = self.last_index_spans[match_index]
            self.app.EgonTE.tag_add('current_match', start_index, end_index)
            self.app.EgonTE.see(start_index)
            self.app.EgonTE.mark_set('insert', end_index)
        except Exception:
            pass

    # ---------- internal helpers ----------
    def get_haystack_text(self) -> str:
        '''
        Return the current search scope text: selection (if active scope) or full buffer.
        '''
        try:
            if self.search_in_selection and self.selection_bounds:
                selection_start, selection_end = self.selection_bounds
                return self.app.EgonTE.get(selection_start, selection_end)
            return self.app.EgonTE.get('1.0', 'end-1c')
        except Exception:
            return ''

    def get_selection_bounds_or_none(self) -> Optional[Tuple[str, str]]:
        '''
        Return ('sel.first', 'sel.last') as absolute indices if a selection exists; otherwise None.
        '''
        try:
            if self.app.EgonTE.tag_ranges('sel'):
                return (self.app.EgonTE.index('sel.first'), self.app.EgonTE.index('sel.last'))
        except Exception:
            pass
        return None

    def rebuild_if_needed(self, needle_text: str, flags_tuple: Tuple[bool, bool, bool], in_selection_flag: bool) -> None:
        '''
        Rebuild internal match cache if haystack, scope, needle or flags have changed.
        '''
        haystack_text = self.get_haystack_text()
        same_source = (haystack_text == self.haystack_snapshot) and (self.search_in_selection == in_selection_flag)
        if same_source and needle_text == self.last_needle and flags_tuple == self.last_flags and self.last_index_spans:
            return

        case_sensitive, whole_word, regex = flags_tuple
        span_offsets = self.find_all_offsets(
            haystack_text,
            needle_text,
            case_sensitive=case_sensitive,
            whole_word=whole_word,
            regex=regex,
        )

        if in_selection_flag and self.selection_bounds:
            selection_start_abs = self.selection_bounds[0]
            base_line, base_col = map(int, selection_start_abs.split('.'))
            absolute_spans: List[Tuple[str, str]] = []
            for start_off, end_off in span_offsets:
                absolute_spans.append((f'{base_line}.{base_col}+{start_off}c', f'{base_line}.{base_col}+{end_off}c'))
            index_spans = absolute_spans
        else:
            index_spans = self.offsets_to_indices(span_offsets)

        self.last_needle = needle_text
        self.last_flags = flags_tuple
        self.last_index_spans = index_spans
        self.current_match_index = 0
        self.haystack_snapshot = haystack_text
        self.search_in_selection = in_selection_flag

    # ---------- public API ----------
    def find_text(
        self,
        needle_text: str,
        *,
        case_sensitive: bool = False,
        whole_word: bool = False,
        regex: bool = False,
        highlight: bool = True,
        in_selection: bool = False,
    ) -> List[Tuple[str, str]]:
        '''
        Find all matches and optionally highlight them.

        Returns:
            A copy of the list of Tk index spans for each match.
        '''
        self.selection_bounds = self.get_selection_bounds_or_none() if in_selection else None

        self.rebuild_if_needed(needle_text, (case_sensitive, whole_word, regex), in_selection)
        if highlight:
            self.apply_all_highlights(self.last_index_spans or [])
            if self.last_index_spans:
                self.mark_current(0)
        return list(self.last_index_spans or [])

    def find_next(self, wrap: bool = True) -> Optional[Tuple[str, str]]:
        '''
        Move to the next match and return its index span. If wrap is False, stop at the last match.
        '''
        if not self.last_index_spans:
            return None
        self.current_match_index += 1
        if self.current_match_index >= len(self.last_index_spans):
            if wrap:
                self.current_match_index = 0
            else:
                self.current_match_index = len(self.last_index_spans) - 1
                return None
        self.mark_current(self.current_match_index)
        return self.last_index_spans[self.current_match_index]

    def find_prev(self, wrap: bool = True) -> Optional[Tuple[str, str]]:
        '''
        Move to the previous match and return its index span. If wrap is False, stop at the first match.
        '''
        if not self.last_index_spans:
            return None
        self.current_match_index -= 1
        if self.current_match_index < 0:
            if wrap:
                self.current_match_index = len(self.last_index_spans) - 1
            else:
                self.current_match_index = 0
                return None
        self.mark_current(self.current_match_index)
        return self.last_index_spans[self.current_match_index]

    def replace(
        self,
        needle_text: str,
        replacement_text: str,
        *,
        case_sensitive: bool = False,
        whole_word: bool = False,
        regex: bool = False,
        replace_all: bool = True,
        in_selection: bool = False,
    ) -> int:
        '''
        Replace occurrences of needle_text with replacement_text.

        Parameters:
            replace_all: when True, replace all; otherwise, only the first occurrence
            in_selection: when True, replace inside current selection bounds only
        Returns:
            Number of replacements performed.
        '''
        self.selection_bounds = self.get_selection_bounds_or_none() if in_selection else None
        haystack_text = self.get_haystack_text()
        span_offsets = self.find_all_offsets(
            haystack_text,
            needle_text,
            case_sensitive=case_sensitive,
            whole_word=whole_word,
            regex=regex,
        )
        if not span_offsets:
            return 0

        result_pieces: List[str] = []
        last_copied_upto = 0
        replaced_count = 0
        for start_off, end_off in span_offsets:
            if not replace_all and replaced_count >= 1:
                break
            result_pieces.append(haystack_text[last_copied_upto:start_off])
            if regex:
                try:
                    regex_flags = 0 if case_sensitive else re.IGNORECASE
                    compiled_pattern = re.compile(needle_text, regex_flags)
                    result_pieces.append(compiled_pattern.sub(replacement_text, haystack_text[start_off:end_off], count=1))
                except re.error:
                    result_pieces.append(replacement_text)
            else:
                result_pieces.append(replacement_text)
            last_copied_upto = end_off
            replaced_count += 1
        final_text = ''.join(result_pieces) if replace_all else (''.join(result_pieces) + haystack_text[span_offsets[0][1]:])

        try:
            if in_selection and self.selection_bounds:
                selection_start_abs, selection_end_abs = self.selection_bounds
                self.app.EgonTE.delete(selection_start_abs, selection_end_abs)
                self.app.EgonTE.insert(selection_start_abs, final_text)
            else:
                self.app.EgonTE.delete('1.0', 'end')
                self.app.EgonTE.insert('1.0', final_text)
        except Exception:
            return 0

        if not replace_all:
            self.haystack_snapshot = None
            self.find_text(
                needle_text,
                case_sensitive=case_sensitive,
                whole_word=whole_word,
                regex=regex,
                highlight=True,
                in_selection=in_selection,
            )
        else:
            self.clear_all_tags()
            self.last_index_spans = []
            self.current_match_index = 0
            self.haystack_snapshot = self.get_haystack_text()

        return replaced_count

    def replace_current(self, replacement_text: str) -> bool:
        '''
        Replace only the currently highlighted 'current_match' span, if present.
        '''
        try:
            current_ranges = self.app.EgonTE.tag_ranges('current_match')
            if not current_ranges:
                return False
            start_index, end_index = current_ranges[0], current_ranges[1]
            self.app.EgonTE.delete(start_index, end_index)
            self.app.EgonTE.insert(start_index, replacement_text)
            if self.last_index_spans:
                self.find_next(wrap=False)
            return True
        except Exception:
            return False

    def count(self, needle_text: str, *, case_sensitive: bool = False, whole_word: bool = False, regex: bool = False) -> int:
        '''
        Return the number of matches of needle_text in the current scope.
        '''
        self.selection_bounds = None
        haystack_text = self.get_haystack_text()
        return len(self.find_all_offsets(haystack_text, needle_text, case_sensitive=case_sensitive, whole_word=whole_word, regex=regex))

    def goto_absolute_offset(self, offset_value: int) -> None:
        '''
        Move the cursor and viewport to an absolute character offset from the start of the buffer.
        '''
        try:
            index_value = self.offset_to_index(max(0, offset_value))
            self.app.EgonTE.see(index_value)
            self.app.EgonTE.mark_set('insert', index_value)
            self.app.EgonTE.focus_set()
        except Exception:
            pass

    def goto_line_col(self, line_number: int, column_number: int) -> None:
        '''
        Move the cursor and viewport to a specific line and column (1-based line, 0-based column).
        '''
        try:
            index_value = f'{max(1, int(line_number))}.{max(0, int(column_number))}'
            self.app.EgonTE.see(index_value)
            self.app.EgonTE.mark_set('insert', index_value)
            self.app.EgonTE.focus_set()
        except Exception:
            pass
