from __future__ import annotations

import re
import threading
import csv
import io
import textwrap
import tkinter as tk
from tkinter import ttk, messagebox, END, BOTH, RIGHT, Y, DISABLED
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union, Callable

# external deps (optional ones are guarded)
try:
    import spacy
    from spacy.matcher import Matcher
    from spacy.cli import download as spacy_download
except Exception as e:
    raise RuntimeError('spaCy is required for the NLP tool. Please install spacy first.') from e

try:
    import phonenumbers  # type: ignore
except Exception:
    phonenumbers = None

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as sentiment_analyzer_cls  # type: ignore
except Exception:
    sentiment_analyzer_cls = None  # type: ignore

# menu lists/maps defined centrally
try:
    from large_variables import function_items as NLP_FUNCTION_ITEMS, function_map as NLP_FUNCTION_MAP
except Exception:
    NLP_FUNCTION_ITEMS = [
        'Get nouns', 'Get verbs', 'Get adjectives', 'Get adverbs', 'Get pronouns',
        'Get stop words',
        'Entity recognition', 'Dependency tree', 'Lemmatization', 'Most common words',
        'Get names (persons)', 'Get phone numbers', 'Extract emails', 'Extract URLs', 'Extract IP addresses',
        'Key phrases (noun chunks)', 'N-grams (2–3)', 'Sentence split', 'POS distribution', 'Sentiment (VADER)',
    ]
    NLP_FUNCTION_MAP = {
        'Get nouns': 'NOUN', 'Get verbs': 'VERB', 'Get adjectives': 'ADJ', 'Get adverbs': 'ADV', 'Get pronouns': 'PRON',
        'Get stop words': 'stop words',
        'Entity recognition': 'entity recognition', 'Dependency tree': 'dependency', 'Lemmatization': 'lemmatization',
        'Most common words': 'most common words',
        'Get names (persons)': 'FULL_NAME', 'Get phone numbers': 'PHONE_NUMBER',
        'Extract emails': 'EMAILS', 'Extract URLs': 'URLS', 'Extract IP addresses': 'IP_ADDRESSES',
        'Key phrases (noun chunks)': 'KEY_PHRASES', 'N-grams (2–3)': 'NGRAMS',
        'Sentence split': 'SENTENCE_SPLIT', 'POS distribution': 'POS_DISTRIBUTION', 'Sentiment (VADER)': 'SENTIMENT',
    }


# ---------------------------------------------------------------------------
# Single entry point: call open_nlp(self[, preset_function])
# Keeps most logic/UI inside one function for easy drop-in usage
# ---------------------------------------------------------------------------
def open_nlp(app, preset_function: Optional[str] = None) -> None:
    '''
    Open the NLP popup (UI + logic), designed as a drop-in tool:
        from nlp_popup import open_nlp
        open_nlp(self, preset_function='nouns')

    Notes:
    - Caches spaCy pipeline on the app instance (app.nlp_engine_pipe).
    - Respects app.prefer_gpu (BooleanVar or similar) if present.
    - Uses app.make_pop_ups_window and app.make_rich_textbox if available.
    - Applies a time limit per analysis run (app.nlp_time_limit_s, default 5.0s).
    '''
    # ------------------- helpers: pipeline and execution -------------------
    def ensure_nlp_pipeline() -> Any:
        prefer_gpu_enabled = False
        if hasattr(app, 'prefer_gpu') and callable(getattr(app.prefer_gpu, 'get', None)):
            try:
                prefer_gpu_enabled = bool(app.prefer_gpu.get())
            except Exception:
                prefer_gpu_enabled = False

        pipeline_missing_or_changed = (
            not hasattr(app, 'nlp_engine_pipe') or getattr(app, 'nlp_engine_pipe') is None
            or getattr(app, '_nlp_gpu_pref', None) != prefer_gpu_enabled
        )

        if pipeline_missing_or_changed:
            try:
                if prefer_gpu_enabled:
                    try:
                        spacy.require_gpu()
                    except Exception:
                        try:
                            spacy.prefer_gpu()
                        except Exception:
                            pass
                pipeline = None
                try:
                    pipeline = spacy.load('en_core_web_sm')
                except OSError:
                    spacy_download('en_core_web_sm')
                    pipeline = spacy.load('en_core_web_sm')
                setattr(app, 'nlp_engine_pipe', pipeline)
                setattr(app, '_nlp_gpu_pref', prefer_gpu_enabled)
            except Exception as pipeline_error:
                raise RuntimeError(f'Failed to initialize spaCy: {pipeline_error}') from pipeline_error

        if not hasattr(app, 'nlp_time_limit_s'):
            setattr(app, 'nlp_time_limit_s', 5.0)

        return getattr(app, 'nlp_engine_pipe')

    def run_with_timeout(callable_func: Callable[..., Any], args: Tuple[Any, ...], timeout_seconds: float) -> Tuple[Optional[Any], bool]:
        result_container: List[Any] = []
        error_container: List[BaseException] = []

        def worker_thread():
            try:
                result_container.append(callable_func(*args))
            except BaseException as thread_error:
                error_container.append(thread_error)

        analysis_thread = threading.Thread(target=worker_thread, daemon=True)
        analysis_thread.start()
        analysis_thread.join(timeout_seconds)
        if analysis_thread.is_alive():
            return None, True
        if error_container:
            raise error_container[0]
        return (result_container[0] if result_container else None), False

    # ------------------------- helpers: extractors -------------------------
    def unique_preserve(values: List[str]) -> List[str]:
        return list(dict.fromkeys(values))

    def ngrams_list(tokens: List[str], size: int) -> List[str]:
        if size <= 1 or len(tokens) < size:
            return []
        return [' '.join(tokens[i: i + size]) for i in range(len(tokens) - size + 1)]

    def extract_emails(text_value: str) -> List[str]:
        matches = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text_value or '')
        return sorted(set(matches))

    def extract_urls(text_value: str) -> List[str]:
        matches = re.findall(r'https?://[^\s)>\]]+', text_value or '')
        return sorted(set(matches))

    def extract_ips(text_value: str) -> List[str]:
        raw_ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text_value or '')
        def valid_ip(ip_addr: str) -> bool:
            try:
                octets = ip_addr.split('.')
                return len(octets) == 4 and all(0 <= int(o) <= 255 for o in octets)
            except Exception:
                return False
        return sorted({ip for ip in raw_ips if valid_ip(ip)})

    def extract_phones(text_value: str) -> List[str]:
        if phonenumbers is None:
            fallback_pattern = re.compile(r'(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3}\)?[\s-]?)\d{3}[\s-]?\d{4}')
            return sorted(set(fallback_pattern.findall(text_value or '')))
        formatted: List[str] = []
        for match in phonenumbers.PhoneNumberMatcher(text_value or '', None):
            formatted.append(phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.INTERNATIONAL))
        return sorted(set(formatted))

    def to_tsv(columns: Iterable[str], rows: Iterable[Iterable[Any]]) -> str:
        header_line = '\t'.join(str(c) for c in columns)
        data_lines = ['\t'.join(str(v) for v in row) for row in rows]
        return '\n'.join([header_line] + data_lines)

    def to_csv(columns: Iterable[str], rows: Iterable[Iterable[Any]]) -> str:
        buffer = io.StringIO()
        csv_writer = csv.writer(buffer)
        csv_writer.writerow(list(columns))
        for row in rows:
            csv_writer.writerow(list(row))
        return buffer.getvalue()

    def wrap_text(content: str, max_cols: int = 80) -> str:
        return '\n'.join(textwrap.fill(line, width=max_cols, break_long_words=False) for line in str(content).splitlines())

    def normalize_key(name: str) -> str:
        if not name:
            return ''
        lowered_name = name.strip().lower()
        mapping = {
            'nouns': 'NOUN', 'verbs': 'VERB', 'adjective': 'ADJ', 'adjectives': 'ADJ',
            'adverbs': 'ADV', 'pronouns': 'PRON', 'stop words': 'STOP_WORDS',
            'names': 'FULL_NAME', 'full_name': 'FULL_NAME', 'full name': 'FULL_NAME',
            'phone numbers': 'PHONE_NUMBER', 'phone number': 'PHONE_NUMBER',
            'entity recognition': 'ENTITY_RECOGNITION',
            'dependency': 'DEPENDENCY', 'dependency tree': 'DEPENDENCY',
            'lemmatization': 'LEMMATIZATION',
            'most common words': 'MOST_COMMON_WORDS',
            'key phrases': 'KEY_PHRASES',
            'n-grams': 'NGRAMS', 'ngrams': 'NGRAMS',
            'emails': 'EMAILS', 'urls': 'URLS', 'ip addresses': 'IP_ADDRESSES',
            'sentence split': 'SENTENCE_SPLIT', 'pos distribution': 'POS_DISTRIBUTION',
            'sentiment': 'SENTIMENT',
        }
        return mapping.get(lowered_name, lowered_name.upper())

    # ------------------------- core analysis (inline) -----------------------
    def analyze(text_value: str, function_key: str, *, top_n: int, ngram_sizes: Tuple[int, ...], time_limit_seconds: float) -> Tuple[str, Optional[Tuple[Tuple[str, ...], Tuple[Tuple[Any, ...], ...]]]]:
        max_chars_allowed = 750_000
        if text_value is None:
            text_value = ''
        if len(text_value) > max_chars_allowed:
            return '(Input too large for analysis)', None

        nlp_pipeline = ensure_nlp_pipeline()

        def build_doc() -> Any:
            if function_key in {'EMAILS', 'URLS', 'IP_ADDRESSES', 'PHONE_NUMBER'}:
                return nlp_pipeline.make_doc(text_value)
            if function_key in {'ENTITY_RECOGNITION', 'FULL_NAME'}:
                try:
                    with nlp_pipeline.select_pipes(disable=['parser']):
                        return nlp_pipeline(text_value)
                except Exception:
                    return nlp_pipeline(text_value)
            if function_key in {'KEY_PHRASES', 'DEPENDENCY',
                                'VERB', 'NOUN', 'ADJ', 'ADV', 'PRON',
                                'STOP_WORDS', 'LEMMATIZATION',
                                'MOST_COMMON_WORDS', 'NGRAMS',
                                'SENTENCE_SPLIT', 'POS_DISTRIBUTION',
                                'SENTIMENT'}:
                try:
                    with nlp_pipeline.select_pipes(disable=['ner']):
                        return nlp_pipeline(text_value)
                except Exception:
                    return nlp_pipeline(text_value)
            return nlp_pipeline(text_value)

        spacy_doc, timed_out = run_with_timeout(build_doc, tuple(), time_limit_seconds)
        if timed_out:
            return '(Analysis timed out)', None
        if spacy_doc is None:
            try:
                spacy_doc = nlp_pipeline(text_value)
            except Exception as fallback_error:
                return f'(NLP error: {fallback_error})', None

        if function_key in {'VERB', 'NOUN', 'ADJ', 'ADV', 'PRON'}:
            pos_items = unique_preserve([token.text for token in spacy_doc if token.pos_ == function_key])
            return (', '.join(pos_items) if pos_items else '(No matches found!)'), None

        if function_key == 'FULL_NAME':
            person_names = unique_preserve([ent.text for ent in spacy_doc.ents if ent.label_ == 'PERSON'])
            if not person_names:
                matcher = Matcher(spacy_doc.vocab)
                matcher.add('proper_noun_bigram', [[{'POS': 'PROPN'}, {'POS': 'PROPN'}]])
                matches = matcher(spacy_doc)
                person_names = [spacy_doc[start_idx:end_idx].text for _, start_idx, end_idx in matches]
            return (', '.join(person_names) if person_names else '(No matches found!)'), None

        if function_key == 'PHONE_NUMBER':
            phone_numbers = extract_phones(text_value)
            return (', '.join(phone_numbers) if phone_numbers else '(No matches found!)'), None

        if function_key == 'ENTITY_RECOGNITION':
            entity_rows = [(ent.text, ent.label_, ent.start_char, ent.end_char) for ent in spacy_doc.ents]
            if not entity_rows:
                return '(No matches found!)', None
            return '', (('entity', 'label', 'start', 'end'), tuple(entity_rows))

        if function_key == 'DEPENDENCY':
            dependency_rows = [(token.text, token.head.text, token.dep_) for token in spacy_doc]
            if not dependency_rows:
                return '(No matches found!)', None
            return '', (('word', 'head', 'dependency'), tuple(dependency_rows))

        if function_key == 'STOP_WORDS':
            stopword_items = unique_preserve([token.text for token in spacy_doc if token.is_stop])
            return (', '.join(stopword_items) if stopword_items else '(No matches found!)'), None

        if function_key == 'LEMMATIZATION':
            lemma_rows = [(token.text, token.lemma_) for token in spacy_doc if token.lemma_ and token.lemma_ != token.text]
            if not lemma_rows:
                return '(No lemmatization changes)', None
            return '', (('original', 'lemma'), tuple(lemma_rows))

        if function_key == 'MOST_COMMON_WORDS':
            word_list = [token.text.lower() for token in spacy_doc if token.is_alpha and not token.is_stop]
            top_common = Counter(word_list).most_common(max(1, int(top_n)))
            if not top_common:
                return '(No matches found!)', None
            return '', (('word', 'occurrences'), tuple((word, count) for word, count in top_common))

        if function_key == 'KEY_PHRASES':
            phrase_list = [chunk.text.strip() for chunk in spacy_doc.noun_chunks if chunk.text.strip()]
            top_phrases = Counter(phrase_list).most_common(max(1, int(top_n)))
            if not top_phrases:
                return '(No matches found!)', None
            return '', (('phrase', 'occurrences'), tuple((phrase, count) for phrase, count in top_phrases))

        if function_key == 'NGRAMS':
            alpha_tokens = [token.text.lower() for token in spacy_doc if token.is_alpha and not token.is_stop]
            collected_ngrams: List[str] = []
            for size in ngram_sizes:
                collected_ngrams.extend(ngrams_list(alpha_tokens, size))
            top_ngrams = Counter(collected_ngrams).most_common(max(1, int(top_n)))
            if not top_ngrams:
                return '(No matches found!)', None
            return '', (('ngram', 'occurrences'), tuple((ngram, count) for ngram, count in top_ngrams))

        if function_key == 'EMAILS':
            email_list = extract_emails(text_value)
            return (', '.join(email_list) if email_list else '(No matches found!)'), None

        if function_key == 'URLS':
            url_list = [url.rstrip('.,);]') for url in extract_urls(text_value)]
            return ('\n'.join(url_list) if url_list else '(No matches found!)'), None

        if function_key == 'IP_ADDRESSES':
            ip_list = extract_ips(text_value)
            return (', '.join(ip_list) if ip_list else '(No matches found!)'), None

        if function_key == 'SENTENCE_SPLIT':
            sentence_texts = [sent.text.strip() for sent in spacy_doc.sents if sent.text.strip()]
            return ('\n'.join(sentence_texts) if sentence_texts else '(No matches found!)'), None

        if function_key == 'POS_DISTRIBUTION':
            pos_counts: Dict[str, int] = defaultdict(int)
            for token in spacy_doc:
                pos_counts[token.pos_] += 1
            pos_rows = sorted(pos_counts.items(), key=lambda item: (-item[1], item[0]))
            if not pos_rows:
                return '(No matches found!)', None
            return '', (('pos', 'count'), tuple(pos_rows))

        if function_key == 'SENTIMENT':
            if sentiment_analyzer_cls is None:
                return '(Sentiment analyzer not available)', None
            sentiment_analyzer = sentiment_analyzer_cls()
            score = sentiment_analyzer.polarity_scores(text_value or '')
            sentiment_rows = tuple((metric, score.get(metric, 0)) for metric in ('neg', 'neu', 'pos', 'compound'))
            return '', (('metric', 'value'), sentiment_rows)

        return '(No output)', None

    # --------------------------- build the popup UI -------------------------
    try:
        nlp_root = app.make_pop_ups_window(open_nlp, name='nlp_tool', title=f'{getattr(app, "title_struct", "")}Natural language processor')
    except Exception:
        nlp_root = tk.Toplevel()
        nlp_root.title('Natural language processor')

    # Controls row
    controls_frame = ttk.Frame(nlp_root)
    controls_frame.pack(fill=tk.X, padx=6, pady=6)

    function_label = ttk.Label(controls_frame, text='Function:')
    function_label.pack(side=tk.LEFT, padx=(0, 6))

    available_functions = list(NLP_FUNCTION_ITEMS) if NLP_FUNCTION_ITEMS else []
    function_combobox = ttk.Combobox(controls_frame, values=available_functions, state='readonly', width=28)
    if available_functions:
        function_combobox.set(available_functions[0])
    function_combobox.pack(side=tk.LEFT, padx=(0, 8))

    topn_label = ttk.Label(controls_frame, text='Top N:')
    topn_label.pack(side=tk.LEFT, padx=(6, 4))
    topn_variable = tk.IntVar(value=10)
    topn_spinbox = ttk.Spinbox(controls_frame, from_=1, to=100, width=4, textvariable=topn_variable)
    topn_spinbox.pack(side=tk.LEFT, padx=(0, 8))

    time_limit_label = ttk.Label(controls_frame, text='Time limit (s):')
    time_limit_label.pack(side=tk.LEFT, padx=(6, 4))
    time_limit_variable = tk.DoubleVar(value=getattr(app, 'nlp_time_limit_s', 5.0))
    time_limit_spinbox = ttk.Spinbox(controls_frame, from_=0.5, to=30.0, increment=0.5, width=6, textvariable=time_limit_variable)
    time_limit_spinbox.pack(side=tk.LEFT, padx=(0, 8))

    run_button = ttk.Button(controls_frame, text='Run')
    run_button.pack(side=tk.LEFT, padx=(4, 0))

    # Output area
    output_frame = ttk.Frame(nlp_root)
    output_frame.pack(fill=BOTH, expand=True, padx=6, pady=(0, 6))

    # State holders
    last_table_data: Dict[str, Any] = {'columns': None, 'rows': None}
    last_text_data: Dict[str, str] = {'display': ''}

    # Runner
    def run_now():
        try:
            app.nlp_time_limit_s = float(time_limit_variable.get())
        except Exception:
            app.nlp_time_limit_s = 5.0

        try:
            try:
                source_text = app.EgonTE.get('1.0', 'end')
            except Exception:
                source_text = ''

            selected_label = function_combobox.get()
            mapped_key = NLP_FUNCTION_MAP.get(selected_label, selected_label)
            mapped_key = normalize_key(mapped_key)

            display_text, table_tuple = analyze(
                text_value=source_text,
                function_key=mapped_key,
                top_n=max(1, int(topn_variable.get())),
                ngram_sizes=(2, 3),
                time_limit_seconds=getattr(app, 'nlp_time_limit_s', 5.0)
            )

            for child_widget in output_frame.winfo_children():
                try:
                    child_widget.destroy()
                except Exception:
                    pass

            last_text_data['display'] = ''
            last_table_data['columns'] = None
            last_table_data['rows'] = None

            if table_tuple is None:
                last_text_data['display'] = display_text
                if hasattr(app, 'make_rich_textbox'):
                    text_container, text_widget, y_scrollbar = app.make_rich_textbox(root=output_frame,
                                                                                     place='pack_top', wrap='word')
                    text_widget.insert(END, wrap_text(display_text, max_cols=100))
                    text_widget.configure(state=DISABLED)
                else:
                    text_widget = tk.Text(output_frame, wrap='word', height=18)
                    text_widget.insert(END, wrap_text(display_text, max_cols=100))
                    text_widget.configure(state=DISABLED)
                    text_widget.pack(fill=BOTH, expand=True)
            else:
                table_columns, table_rows = table_tuple
                last_table_data['columns'] = table_columns
                last_table_data['rows'] = table_rows

                result_tree = ttk.Treeview(output_frame, columns=table_columns, show='headings')
                for column_name in table_columns:
                    result_tree.heading(column_name, text=str(column_name).capitalize())
                    result_tree.column(column_name, stretch=True, width=120)
                for row_values in table_rows:
                    result_tree.insert('', END, values=list(row_values))
                tree_scrollbar = ttk.Scrollbar(output_frame, orient='vertical', command=result_tree.yview)
                result_tree.configure(yscrollcommand=tree_scrollbar.set)
                tree_scrollbar.pack(side=RIGHT, fill=Y)
                result_tree.pack(fill=BOTH, expand=True)

        except Exception as run_error:
            try:
                messagebox.showerror('EgonTE', f'NLP error: {run_error}')
            except Exception:
                pass

    run_button.configure(command=run_now)

    # Actions row
    actions_frame = ttk.Frame(nlp_root)
    actions_frame.pack(fill=tk.X, padx=6, pady=(0, 6))

    def copy_output_to_clipboard():
        try:
            if last_table_data['columns'] is not None:
                clipboard_content = to_tsv(last_table_data['columns'], last_table_data['rows'] or ())
            else:
                clipboard_content = last_text_data['display'] or ''
            if hasattr(app, 'copy'):
                app.copy(clipboard_content)
            else:
                nlp_root.clipboard_clear()
                nlp_root.clipboard_append(clipboard_content)
        except Exception:
            pass

    def copy_csv_to_clipboard():
        try:
            if last_table_data['columns'] is None:
                return
            clipboard_content = to_csv(last_table_data['columns'], last_table_data['rows'] or ())
            if hasattr(app, 'copy'):
                app.copy(clipboard_content)
            else:
                nlp_root.clipboard_clear()
                nlp_root.clipboard_append(clipboard_content)
            messagebox.showinfo('EgonTE', 'CSV copied to clipboard.')
        except Exception:
            pass

    copy_button = ttk.Button(actions_frame, text='Copy', command=copy_output_to_clipboard)
    copy_button.pack(side=tk.LEFT)

    copy_csv_button = ttk.Button(actions_frame, text='Copy CSV', command=copy_csv_to_clipboard)
    copy_csv_button.pack(side=tk.LEFT, padx=(6, 0))

    # Preset handling and initial run
    if preset_function:
        try:
            normalized_preset = normalize_key(preset_function)
            reverse_map = {v: k for k, v in NLP_FUNCTION_MAP.items()}
            if normalized_preset in reverse_map:
                function_combobox.set(reverse_map[normalized_preset])
            else:
                for label, key in NLP_FUNCTION_MAP.items():
                    if normalize_key(key) == normalized_preset:
                        function_combobox.set(label)
                        break
        except Exception:
            pass

    run_now()
