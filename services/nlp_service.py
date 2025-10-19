from __future__ import annotations

import re
import threading
import csv
import io
import json
import textwrap
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

# New optional dependencies for expanded features
try:
    from wordcloud import WordCloud
except Exception:
    WordCloud = None

try:
    import textstat
except Exception:
    textstat = None

try:
    from PIL import Image, ImageTk
except Exception:
    Image = ImageTk = None

try:
    from langdetect import detect_langs
except Exception:
    detect_langs = None

try:
    from textblob import TextBlob
except Exception:
    TextBlob = None

try:
    from nrclex import NRCLex
except Exception:
    NRCLex = None

try:
    from thefuzz import process as fuzzy_process
except Exception:
    fuzzy_process = None

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

try:
    from gensim.corpora import Dictionary
    from gensim.models import LdaModel
except Exception:
    Dictionary = LdaModel = None

try:
    import nltk
    from nltk.corpus import wordnet
    # Ensure wordnet is downloaded
    try:
        wordnet.synsets('test')
    except nltk.downloader.DownloadError:
        nltk.download('wordnet')
except Exception:
    nltk = wordnet = None

# --- Embedded Resources ---
# Sample concreteness ratings (Brysbaert et al., 2014). A larger list could be loaded from a file.
CONCRETENESS_RATINGS = {
    'table': 5.0, 'dog': 4.97, 'book': 4.93, 'water': 4.88, 'chair': 4.87, 'car': 4.85, 'hand': 4.83, 'tree': 4.8, 'sun': 4.77, 'moon': 4.7, 'house': 4.68, 'apple': 4.65, 'road': 4.5, 'computer': 4.4, 'love': 1.53, 'peace': 1.6, 'justice': 1.67, 'freedom': 1.7, 'hope': 1.73, 'idea': 1.8, 'dream': 1.83, 'soul': 1.9, 'mind': 1.97, 'thought': 2.0, 'knowledge': 2.1, 'power': 2.2, 'time': 2.3, 'reality': 2.4, 'truth': 2.5
}

# A small sample of contractions for the expander function
CONTRACTION_MAP = {
    "ain't": "is not", "aren't": "are not","can't": "cannot", "'cause": "because", "could've": "could have",
    "couldn't": "could not", "didn't": "did not",  "doesn't": "does not", "don't": "do not", "hadn't": "had not",
    "hasn't": "has not", "haven't": "have not", "he'd": "he would", "he'll": "he will", "he's": "he is",
    "I'd": "I would", "I'll": "I will", "I'm": "I am", "I've": "I have", "isn't": "is not", "it's": "it is",
    "let's": "let us", "might've": "might have", "must've": "must have", "shan't": "shall not", "she'd": "she would",
    "she'll": "she will", "she's": "she is", "should've": "should have", "shouldn't": "should not", "that's": "that is",
    "there's": "there is", "they're": "they are", "they've": "they have", "wasn't": "was not", "we'd": "we would",
    "we're": "we are", "we've": "we have", "weren't": "were not", "what's": "what is", "where's": "where is",
    "who's": "who is", "won't": "will not", "wouldn't": "would not", "you're": "you are", "you've": "you have"
}


# menu lists/maps defined centrally
try:
    from large_variables import function_items as NLP_FUNCTION_ITEMS, function_map as NLP_FUNCTION_MAP
except Exception:
    # Added new functions to the list
    NLP_FUNCTION_ITEMS = [
        'Get nouns', 'Get verbs', 'Get adjectives', 'Get adverbs', 'Get pronouns',
        'Get stop words',
        'Entity recognition', 'Named Entity Frequency', 'Dependency tree', 'Lemmatization', 'Most common words',
        'Get names (persons)', 'Get phone numbers', 'Extract emails', 'Extract URLs', 'Extract IP addresses',
        'Key phrases (noun chunks)', 'N-grams', 'Sentence split', 'POS distribution', 'Sentiment (VADER)',
        'Summarization', 'Topic Modeling', 'Readability Analysis', 'Word Cloud',
        'Language Detection', 'Keyword Extraction', 'Common POS Sequences', 'Text Statistics', 'Spelling Correction',
        'Emotion Analysis', 'Root Verbs', 'Quote Extraction', 'Acronym Detection',
        'Coreference Resolution', 'Passive Voice Detection', 'Subordinate Clauses', 'JSON Extraction',
        'SVO Extraction', 'Dependency Distance', 'Fuzzy Search',
        'Polarity/Subjectivity', 'Noun Phrase Extraction', 'Verb Phrase Extraction', 'Word Shapes', 'Hashtag Extraction',
        'Gender Pronoun Analysis', 'Question Detection', 'Concreteness Score', 'Sentence Complexity',
        'Punctuation Analysis', 'Stopword Percentage', 'Type-Token Ratio', 'Extract Numbers',
        'Formality Score', 'Emphasis Analysis', 'Difficult Words', 'Sentence Start Analysis',
        'Readability Grade Levels', 'Lexical Density', 'Expletive Detection', 'Sentence Type Analysis',
        'Regex Search', 'Hedge Word Detection', 'Collocation Extraction', 'Find Similar Sentences',
        'POS Tagged Text', 'Read Time Estimation', 'Temporal Expressions', 'Money/Currency Extraction',
        'Adjective-Noun Pairs', 'Proper Noun Extraction', 'Word Count per Sentence', 'Unique Word List', 'Unique Lemma List',
        'Nominalization Detection', 'Gerund/Participle Analysis', 'Prepositional Phrases', 'Sentence-Final POS',
        'Extract Quantities', 'Extract Ordinals', 'Extract Products', 'Extract Works of Art',
        'Adverb-Adjective Pairs', 'Clause Count per Sentence', 'Interjection Analysis', 'Language/Code Name Extraction',
        'Simile Detection', 'Paragraph Statistics', 'Get Organizations', 'Get Locations',
        'Concordance (KWIC)', 'Hapax Legomena', 'Verb Tense Analysis', 'Comprehensive Text Profile',
        'Extract Events', 'Extract Nationalities/Groups', 'Extract Laws', 'Sentence-level Sentiment',
        'Dependency Path', 'Text Similarity', 'Key Sentence Extraction', 'Readability Visualization',
        'Named Entity Density', 'Syntactic Complexity (Tree Depth)', 'Pronoun-to-Noun Ratio', 'Coordinating Conjunction Analysis',
        'LDA Topic Modeling', 'Discourse Connectives', 'Word Ambiguity (Polysemy)', 'Extract Facilities',
        'Expand Contractions', 'Remove HTML Tags', 'Extract Percentages', 'Extract Cardinal Numbers'
    ]
    # Added mappings for new functions
    NLP_FUNCTION_MAP = {
        'Get nouns': 'NOUN', 'Get verbs': 'VERB', 'Get adjectives': 'ADJ', 'Get adverbs': 'ADV', 'Get pronouns': 'PRON',
        'Get stop words': 'stop words', 'Entity recognition': 'entity recognition', 'Dependency tree': 'dependency',
        'Lemmatization': 'lemmatization', 'Most common words': 'most common words',
        'Get names (persons)': 'FULL_NAME', 'Get phone numbers': 'PHONE_NUMBER',
        'Extract emails': 'EMAILS', 'Extract URLs': 'URLS', 'Extract IP addresses': 'IP_ADDRESSES',
        'Key phrases (noun chunks)': 'KEY_PHRASES', 'Noun Phrase Extraction': 'NP_EXTRACTION',
        'Verb Phrase Extraction': 'VP_EXTRACTION',
        'N-grams': 'NGRAMS', 'ngrams': 'NGRAMS',
        'Sentence split': 'SENTENCE_SPLIT', 'POS distribution': 'POS_DISTRIBUTION',
        'Sentiment (VADER)': 'SENTIMENT', 'Polarity/Subjectivity': 'POLARITY_SUBJECTIVITY',
        'Summarization': 'SUMMARIZATION', 'Topic Modeling': 'TOPIC_MODELING',
        'Readability Analysis': 'READABILITY', 'Word Cloud': 'WORD_CLOUD',
        'Language Detection': 'LANGUAGE_DETECTION', 'Keyword Extraction': 'KEYWORDS',
        'Common POS Sequences': 'POS_SEQUENCES', 'pos sequences': 'POS_SEQUENCES',
        'Text Statistics': 'TEXT_STATISTICS', 'Spelling Correction': 'SPELLING_CORRECTION',
        'Emotion Analysis': 'EMOTION_ANALYSIS', 'Root Verbs': 'ROOT_VERBS',
        'Quote Extraction': 'QUOTE_EXTRACTION', 'Acronym Detection': 'ACRONYM_DETECTION',
        'Coreference Resolution': 'COREFERENCE', 'Passive Voice Detection': 'PASSIVE_VOICE',
        'Subordinate Clauses': 'SUBORD_CLAUSES', 'JSON Extraction': 'JSON_EXTRACTION',
        'SVO Extraction': 'SVO_EXTRACTION', 'Dependency Distance': 'DEPENDENCY_DISTANCE', 'Fuzzy Search': 'FUZZY_SEARCH',
        'Word Shapes': 'WORD_SHAPES', 'Hashtag Extraction': 'HASHTAG_EXTRACTION',
        'Gender Pronoun Analysis': 'GENDER_ANALYSIS', 'Question Detection': 'QUESTION_DETECTION',
        'Concreteness Score': 'CONCRETENESS', 'Sentence Complexity': 'SENTENCE_COMPLEXITY',
        'Punctuation Analysis': 'PUNCT_ANALYSIS', 'Stopword Percentage': 'STOPWORD_PERCENTAGE',
        'Type-Token Ratio': 'TTR', 'Extract Numbers': 'EXTRACT_NUMBERS',
        'Formality Score': 'FORMALITY_SCORE', 'Emphasis Analysis': 'EMPHASIS_ANALYSIS',
        'Difficult Words': 'DIFFICULT_WORDS', 'Sentence Start Analysis': 'SENTENCE_START_ANALYSIS',
        'Readability Grade Levels': 'GRADE_LEVELS', 'Lexical Density': 'LEXICAL_DENSITY',
        'Expletive Detection': 'EXPLETIVE_DETECTION', 'Sentence Type Analysis': 'SENTENCE_TYPES',
        'Regex Search': 'REGEX_SEARCH', 'Hedge Word Detection': 'HEDGE_DETECTION',
        'Collocation Extraction': 'COLLOCATIONS', 'Find Similar Sentences': 'SIMILAR_SENTENCES',
        'POS Tagged Text': 'POS_TAGGED_TEXT', 'Read Time Estimation': 'READ_TIME',
        'Temporal Expressions': 'TEMPORAL_EXPRESSIONS', 'Money/Currency Extraction': 'MONEY_EXTRACTION',
        'Adjective-Noun Pairs': 'ADJ_NOUN_PAIRS', 'Proper Noun Extraction': 'PROPER_NOUNS',
        'Word Count per Sentence': 'SENTENCE_WORD_COUNT', 'Unique Word List': 'UNIQUE_WORDS', 'Unique Lemma List': 'UNIQUE_LEMMAS',
        'Nominalization Detection': 'NOMINALIZATIONS', 'Gerund/Participle Analysis': 'GERUNDS_PARTICIPLES',
        'Prepositional Phrases': 'PREP_PHRASES', 'Sentence-Final POS': 'SENTENCE_FINAL_POS',
        'Extract Quantities': 'QUANTITIES', 'Extract Ordinals': 'ORDINALS',
        'Extract Products': 'PRODUCTS', 'Extract Works of Art': 'WORKS_OF_ART',
        'Adverb-Adjective Pairs': 'ADV_ADJ_PAIRS', 'Clause Count per Sentence': 'CLAUSE_COUNT',
        'Interjection Analysis': 'INTERJECTION_ANALYSIS', 'Language/Code Name Extraction': 'LANGUAGE_EXTRACTION',
        'Simile Detection': 'SIMILE_DETECTION', 'Paragraph Statistics': 'PARAGRAPH_STATS',
        'Get Organizations': 'GET_ORGS', 'Get Locations': 'GET_LOCATIONS',
        'Concordance (KWIC)': 'CONCORDANCE', 'Hapax Legomena': 'HAPAX_LEGOMENA',
        'Verb Tense Analysis': 'VERB_TENSE_ANALYSIS', 'Comprehensive Text Profile': 'TEXT_PROFILE',
        'Extract Events': 'EVENTS', 'Extract Nationalities/Groups': 'NORPS',
        'Extract Laws': 'LAWS', 'Sentence-level Sentiment': 'SENTENCE_SENTIMENT',
        'Dependency Path': 'DEP_PATH', 'Text Similarity': 'TEXT_SIMILARITY',
        'Key Sentence Extraction': 'KEY_SENTENCES', 'Readability Visualization': 'READABILITY_VIZ',
        'Named Entity Density': 'ENTITY_DENSITY', 'Syntactic Complexity (Tree Depth)': 'SYNTACTIC_COMPLEXITY',
        'Pronoun-to-Noun Ratio': 'PRONOUN_NOUN_RATIO', 'Coordinating Conjunction Analysis': 'CONJUNCTION_ANALYSIS',
        'LDA Topic Modeling': 'TOPIC_MODELING_LDA', 'Discourse Connectives': 'DISCOURSE_CONNECTIVES',
        'Word Ambiguity (Polysemy)': 'WORD_AMBIGUITY', 'Extract Facilities': 'FACILITIES',
        'Expand Contractions': 'EXPAND_CONTRACTIONS', 'Remove HTML Tags': 'REMOVE_HTML',
        'Extract Percentages': 'PERCENTAGES', 'Extract Cardinal Numbers': 'CARDINALS'
    }

# ------------------- helpers: pipeline and execution -------------------
def ensure_nlp_pipeline(app) -> Any:
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
                # Try a larger model that might have coref, fallback to small
                try:
                    pipeline = spacy.load('en_core_web_trf')
                except OSError:
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
    matches = re.findall(r'https?://[^\s)>\\]]+', text_value or '')
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
    # Updated mapping with new functions
    mapping = {
        'nouns': 'NOUN', 'verbs': 'VERB', 'adjective': 'ADJ', 'adjectives': 'ADJ',
        'adverbs': 'ADV', 'pronouns': 'PRON', 'stop words': 'STOP_WORDS',
        'names': 'FULL_NAME', 'full_name': 'FULL_NAME', 'full name': 'FULL_NAME',
        'phone numbers': 'PHONE_NUMBER', 'phone number': 'PHONE_NUMBER',
        'entity recognition': 'ENTITY_RECOGNITION', 'named entity frequency': 'ENTITY_FREQUENCY',
        'dependency': 'DEPENDENCY', 'dependency tree': 'DEPENDENCY',
        'lemmatization': 'LEMMATIZATION',
        'most common words': 'MOST_COMMON_WORDS',
        'key phrases': 'KEY_PHRASES', 'noun phrase extraction': 'NP_EXTRACTION',
        'verb phrase extraction': 'VP_EXTRACTION',
        'n-grams': 'NGRAMS', 'ngrams': 'NGRAMS',
        'emails': 'EMAILS', 'urls': 'URLS', 'ip addresses': 'IP_ADDRESSES',
        'sentence split': 'SENTENCE_SPLIT', 'pos distribution': 'POS_DISTRIBUTION',
        'sentiment': 'SENTIMENT', 'polarity/subjectivity': 'POLARITY_SUBJECTIVITY',
        'summarization': 'SUMMARIZATION', 'topic modeling': 'TOPIC_MODELING',
        'readability analysis': 'READABILITY', 'word cloud': 'WORD_CLOUD',
        'language detection': 'LANGUAGE_DETECTION', 'keyword extraction': 'KEYWORDS',
        'common pos sequences': 'POS_SEQUENCES', 'pos sequences': 'POS_SEQUENCES',
        'text statistics': 'TEXT_STATISTICS', 'spelling correction': 'SPELLING_CORRECTION',
        'emotion analysis': 'EMOTION_ANALYSIS', 'root verbs': 'ROOT_VERBS',
        'quote extraction': 'QUOTE_EXTRACTION', 'acronym detection': 'ACRONYM_DETECTION',
        'coreference resolution': 'COREFERENCE', 'passive voice detection': 'PASSIVE_VOICE',
        'subordinate clauses': 'SUBORD_CLAUSES', 'json extraction': 'JSON_EXTRACTION',
        'svo extraction': 'SVO_EXTRACTION', 'dependency distance': 'DEPENDENCY_DISTANCE', 'fuzzy search': 'FUZZY_SEARCH',
        'word shapes': 'WORD_SHAPES', 'hashtag extraction': 'HASHTAG_EXTRACTION',
        'gender pronoun analysis': 'GENDER_ANALYSIS', 'question detection': 'QUESTION_DETECTION',
        'concreteness score': 'CONCRETENESS', 'sentence complexity': 'SENTENCE_COMPLEXITY',
        'punctuation analysis': 'PUNCT_ANALYSIS', 'stopword percentage': 'STOPWORD_PERCENTAGE',
        'type-token ratio': 'TTR', 'extract numbers': 'EXTRACT_NUMBERS',
        'formality score': 'FORMALITY_SCORE', 'emphasis analysis': 'EMPHASIS_ANALYSIS',
        'difficult words': 'DIFFICULT_WORDS', 'sentence start analysis': 'SENTENCE_START_ANALYSIS',
        'readability grade levels': 'GRADE_LEVELS', 'lexical density': 'LEXICAL_DENSITY',
        'expletive detection': 'EXPLETIVE_DETECTION', 'sentence type analysis': 'SENTENCE_TYPES',
        'regex search': 'REGEX_SEARCH', 'hedge word detection': 'HEDGE_DETECTION',
        'collocation extraction': 'COLLOCATIONS', 'find similar sentences': 'SIMILAR_SENTENCES',
        'pos tagged text': 'POS_TAGGED_TEXT', 'read time estimation': 'READ_TIME',
        'temporal expressions': 'TEMPORAL_EXPRESSIONS', 'money/currency extraction': 'MONEY_EXTRACTION',
        'adjective-noun pairs': 'ADJ_NOUN_PAIRS', 'proper noun extraction': 'PROPER_NOUNS',
        'word count per sentence': 'SENTENCE_WORD_COUNT', 'unique word list': 'UNIQUE_WORDS', 'unique lemma list': 'UNIQUE_LEMMAS',
        'nominalization detection': 'NOMINALIZATIONS', 'gerund/participle analysis': 'GERUNDS_PARTICIPLES',
        'prepositional phrases': 'PREP_PHRASES', 'sentence-final pos': 'SENTENCE_FINAL_POS',
        'extract quantities': 'QUANTITIES', 'extract ordinals': 'ORDINALS',
        'extract products': 'PRODUCTS', 'extract works of art': 'WORKS_OF_ART',
        'adverb-adjective pairs': 'ADV_ADJ_PAIRS', 'clause count per sentence': 'CLAUSE_COUNT',
        'interjection analysis': 'INTERJECTION_ANALYSIS', 'language/code name extraction': 'LANGUAGE_EXTRACTION',
        'simile detection': 'SIMILE_DETECTION', 'paragraph statistics': 'PARAGRAPH_STATS',
        'get organizations': 'GET_ORGS', 'get locations': 'GET_LOCATIONS',
        'concordance (kwic)': 'CONCORDANCE', 'hapax legomena': 'HAPAX_LEGOMENA',
        'verb tense analysis': 'VERB_TENSE_ANALYSIS', 'comprehensive text profile': 'TEXT_PROFILE',
        'extract events': 'EVENTS', 'extract nationalities/groups': 'NORPS',
        'extract laws': 'LAWS', 'sentence-level sentiment': 'SENTENCE_SENTIMENT',
        'dependency path': 'DEP_PATH', 'text similarity': 'TEXT_SIMILARITY',
        'key sentence extraction': 'KEY_SENTENCES', 'readability visualization': 'READABILITY_VIZ',
        'named entity density': 'ENTITY_DENSITY', 'syntactic complexity (tree depth)': 'SYNTACTIC_COMPLEXITY',
        'pronoun-to-noun ratio': 'PRONOUN_NOUN_RATIO', 'coordinating conjunction analysis': 'CONJUNCTION_ANALYSIS',
        'lda topic modeling': 'TOPIC_MODELING_LDA', 'discourse connectives': 'DISCOURSE_CONNECTIVES',
        'word ambiguity (polysemy)': 'WORD_AMBIGUITY', 'extract facilities': 'FACILITIES',
        'expand contractions': 'EXPAND_CONTRACTIONS', 'remove html tags': 'REMOVE_HTML',
        'extract percentages': 'PERCENTAGES', 'extract cardinal numbers': 'CARDINALS'
    }
    return mapping.get(lowered_name, lowered_name.upper())

# ------------------------- core analysis (refactored and expanded) -----------------------
def analyze(app, text_value: str, function_key: str, *, top_n: int, ngram_sizes: Tuple[int, ...], time_limit_seconds: float, summary_ratio: float, query_param: str, value_param: int, text_param: str, cancel_event: Optional[threading.Event] = None) -> Tuple[str, Optional[Tuple[Tuple[str, ...], Tuple[Tuple[Any, ...], ...]]], Optional[Any]]:
    max_chars_allowed = 1_000_000  # Increased limit for larger models
    if text_value is None:
        text_value = ''
    if len(text_value) > max_chars_allowed:
        return '(Input too large for analysis)', None, None

    # Functions that don't need the spacy pipeline
    if function_key == 'LANGUAGE_DETECTION':
        if detect_langs is None:
            return '(langdetect library not available)', None, None
        try:
            languages = detect_langs(text_value)
            lang_rows = [(lang.lang, f'{lang.prob:.2f}') for lang in languages]
            return '', (('language', 'probability'), tuple(lang_rows)), None
        except Exception as e:
            return f'(Language detection error: {e})', None, None

    if function_key == 'SPELLING_CORRECTION':
        if TextBlob is None:
            return '(textblob library not available)', None, None
        blob = TextBlob(text_value)
        corrections = []
        for word in blob.words:
            corrected_word = word.correct()
            if word.lower() != corrected_word.lower():
                corrections.append((str(word), str(corrected_word)))
        if not corrections:
            return '(No spelling corrections found)', None, None
        correction_counts = Counter(corrections).most_common()
        return '', (('original', 'correction', 'count'), tuple((orig, corr, count) for (orig, corr), count in correction_counts)), None

    if function_key == 'EMOTION_ANALYSIS':
        if NRCLex is None:
            return '(nrclex library not available)', None, None
        try:
            emotion_obj = NRCLex(text_value)
            emotion_rows = sorted(emotion_obj.affect_frequencies.items(), key=lambda item: (-item[1], item[0]))
            emotion_rows = [(e, f'{s:.2f}') for e, s in emotion_rows if s > 0]
            if not emotion_rows:
                return '(No emotions detected)', None, None
            return '', (('emotion', 'score'), tuple(emotion_rows)), None
        except Exception as e:
            return f'(Emotion analysis error: {e})', None, None

    if function_key == 'QUOTE_EXTRACTION':
        matches = re.findall(
            r'"(.*?)"|\'(.*?)\'|“(.*?)”|‘(.*?)’',
            text_value or ''
        )
        quotes = [group for t in matches for group in t if group]
        if not quotes:
            return '(No quotes found)', None, None
        return '\n'.join(f'- {q.strip()}' for q in quotes), None, None

    if function_key == 'ACRONYM_DETECTION':
        acronyms = re.findall(r'\b[A-Z][A-Z0-9]{1,}\b', text_value or '')
        if not acronyms:
            return '(No acronyms found)', None, None
        acronym_counts = Counter(acronyms).most_common(max(1, int(top_n)))
        return '', (('acronym', 'count'), tuple(acronym_counts)), None

    if function_key == 'JSON_EXTRACTION':
        json_finds = re.findall(r'(\{.*?\})|(\[.*?\])', text_value or '', re.DOTALL)
        extracted_json = []
        for group in json_finds:
            for match in group:
                if match:
                    try:
                        parsed = json.loads(match)
                        extracted_json.append(json.dumps(parsed, indent=2))
                    except json.JSONDecodeError:
                        pass
        if not extracted_json:
            return '(No valid JSON found)', None, None
        return '\n\n---\n\n'.join(extracted_json), None, None

    if function_key == 'POLARITY_SUBJECTIVITY':
        if TextBlob is None:
            return '(textblob library not available)', None, None
        blob = TextBlob(text_value)
        polarity, subjectivity = blob.sentiment
        rows = [
            ('Polarity', f'{polarity:.2f} (Negative < 0 < Positive)'),
            ('Subjectivity', f'{subjectivity:.2f} (Objective < 0.5 < Subjective)')
        ]
        return '', (('metric', 'value'), tuple(rows)), None

    if function_key == 'NP_EXTRACTION':
        if TextBlob is None:
            return '(textblob library not available)', None, None
        blob = TextBlob(text_value)
        nps = unique_preserve(str(p) for p in blob.noun_phrases)
        if not nps:
            return '(No noun phrases found)', None, None
        return ', '.join(nps), None, None

    if function_key == 'HASHTAG_EXTRACTION':
        hashtags = re.findall(r'#\w+', text_value or '')
        if not hashtags:
            return '(No hashtags found)', None, None
        return ', '.join(sorted(set(hashtags))), None, None

    if function_key == 'DIFFICULT_WORDS':
        if textstat is None:
            return '(textstat library not available)', None, None
        difficult_words = list(set(textstat.difficult_words_list(text_value)))
        if not difficult_words:
            return '(No difficult words found)', None, None
        display_words = difficult_words[:max(1, int(top_n * 2))]
        return ', '.join(sorted(display_words)), None, None

    if function_key == 'GRADE_LEVELS':
        if textstat is None:
            return '(textstat library not available)', None, None
        try:
            fk_grade = textstat.flesch_kincaid_grade(text_value)
            gf_grade = textstat.gunning_fog(text_value)
            ari_grade = textstat.automated_readability_index(text_value)
            cli_grade = textstat.coleman_liau_index(text_value)
            
            grades = [fk_grade, gf_grade, ari_grade, cli_grade]
            avg_grade = sum(grades) / len(grades)

            rows = [
                ('Flesch-Kincaid Grade', f'{fk_grade:.2f}'),
                ('Gunning Fog Index', f'{gf_grade:.2f}'),
                ('Automated Readability Index (ARI)', f'{ari_grade:.2f}'),
                ('Coleman-Liau Index', f'{cli_grade:.2f}'),
                ('---', '---'),
                ('Average Grade Level', f'{avg_grade:.2f}')
            ]
            return '', (('metric', 'grade_level'), tuple(rows)), None
        except Exception as e:
            return f'(Readability error: {e})', None, None

    if function_key == 'EXPLETIVE_DETECTION':
        expletives = {'damn', 'hell', 'bitch', 'asshole', 'fuck', 'shit', 'crap', 'piss', 'dick', 'cunt'}
        found_expletives = [word for word in re.split(r'\W+', text_value.lower()) if word in expletives]
        if not found_expletives:
            return '(No expletives found)', None, None
        expletive_counts = Counter(found_expletives).most_common()
        return '', (('expletive', 'count'), tuple(expletive_counts)), None

    if function_key == 'REGEX_SEARCH':
        try:
            matches = re.findall(query_param, text_value or '')
            if not matches:
                return '(No matches found for the regex pattern)', None, None
            if matches and isinstance(matches[0], tuple):
                num_groups = len(matches[0])
                header = tuple(f'group_{i+1}' for i in range(num_groups))
                return '', (header, tuple(matches)), None
            else:
                return '\n'.join(matches), None, None
        except re.error as e:
            return f'(Invalid Regex: {e})', None, None

    if function_key == 'READABILITY_VIZ':
        if textstat is None or plt is None:
            return '(textstat and matplotlib libraries are required for this feature)', None, None
        
        scores = {
            'Flesch-Kincaid': textstat.flesch_kincaid_grade(text_value),
            'Gunning Fog': textstat.gunning_fog(text_value),
            'ARI': textstat.automated_readability_index(text_value),
            'Coleman-Liau': textstat.coleman_liau_index(text_value),
            'SMOG': textstat.smog_index(text_value)
        }
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(scores.keys(), scores.values(), color=['#ff9999','#66b3ff','#99ff99','#ffcc99','#c2c2f0'])
        ax.set_ylabel('Grade Level')
        ax.set_title('Readability Grade Levels')
        ax.set_xticklabels(scores.keys(), rotation=45, ha="right")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img = Image.open(buf)
        return '', None, img

    if function_key == 'EXPAND_CONTRACTIONS':
        contraction_re = re.compile('(%s)' % '|'.join(CONTRACTION_MAP.keys()))
        def expand(match):
            return CONTRACTION_MAP[match.group(0)]
        expanded_text = contraction_re.sub(expand, text_value)
        return expanded_text, None, None

    if function_key == 'REMOVE_HTML':
        clean_text = re.sub(r'<.*?>', '', text_value)
        return clean_text, None, None

    nlp_pipeline = ensure_nlp_pipeline(app)

    def build_doc() -> Any:
        if function_key in {'COREFERENCE', 'SIMILAR_SENTENCES', 'TEXT_SIMILARITY'}:
            return nlp_pipeline(text_value)
        if function_key in {'EMAILS', 'URLS', 'IP_ADDRESSES', 'PHONE_NUMBER', 'READABILITY', 'WORD_CLOUD', 'FUZZY_SEARCH', 'CONCRETENESS', 'SENTENCE_COMPLEXITY', 'PUNCT_ANALYSIS', 'STOPWORD_PERCENTAGE', 'TTR', 'EXTRACT_NUMBERS', 'FORMALITY_SCORE', 'EMPHASIS_ANALYSIS', 'SENTENCE_START_ANALYSIS', 'LEXICAL_DENSITY', 'SENTENCE_TYPES', 'HEDGE_DETECTION', 'COLLOCATIONS', 'POS_TAGGED_TEXT', 'READ_TIME', 'ADJ_NOUN_PAIRS', 'PROPER_NOUNS', 'SENTENCE_WORD_COUNT', 'UNIQUE_WORDS', 'UNIQUE_LEMMAS', 'NOMINALIZATIONS', 'GERUNDS_PARTICIPLES', 'PREP_PHRASES', 'SENTENCE_FINAL_POS', 'ADV_ADJ_PAIRS', 'CLAUSE_COUNT', 'INTERJECTION_ANALYSIS', 'PARAGRAPH_STATS', 'SIMILE_DETECTION', 'CONCORDANCE', 'HAPAX_LEGOMENA', 'VERB_TENSE_ANALYSIS', 'TEXT_PROFILE', 'SENTENCE_SENTIMENT', 'DEP_PATH', 'KEY_SENTENCES', 'ENTITY_DENSITY', 'SYNTACTIC_COMPLEXITY', 'PRONOUN_NOUN_RATIO', 'CONJUNCTION_ANALYSIS', 'TOPIC_MODELING_LDA', 'DISCOURSE_CONNECTIVES', 'WORD_AMBIGUITY'}:
            return nlp_pipeline.make_doc(text_value)
        if function_key in {'ENTITY_RECOGNITION', 'FULL_NAME', 'ENTITY_FREQUENCY', 'TEMPORAL_EXPRESSIONS', 'MONEY_EXTRACTION', 'QUANTITIES', 'ORDINALS', 'PRODUCTS', 'WORKS_OF_ART', 'LANGUAGE_EXTRACTION', 'GET_ORGS', 'GET_LOCATIONS', 'EVENTS', 'NORPS', 'LAWS', 'FACILITIES', 'PERCENTAGES', 'CARDINALS'}:
            try:
                with nlp_pipeline.select_pipes(enable=['ner']):
                    return nlp_pipeline(text_value)
            except Exception:
                return nlp_pipeline(text_value)
        try:
            with nlp_pipeline.select_pipes(disable=['ner']):
                return nlp_pipeline(text_value)
        except Exception:
            return nlp_pipeline(text_value)

    spacy_doc, timed_out = run_with_timeout(build_doc, tuple(), time_limit_seconds)
    if timed_out:
        return '(Analysis timed out)', None, None
    if spacy_doc is None:
        try:
            spacy_doc = nlp_pipeline(text_value)
        except Exception as fallback_error:
            return f'(NLP error: {fallback_error})', None, None

    # --- Analysis function handlers ---
    if function_key == 'FUZZY_SEARCH':
        if fuzzy_process is None:
            return '(thefuzz library not available)', None, None
        
        choices = list(set(token.text for token in spacy_doc if token.is_alpha))
        if not choices:
            return '(No words to search in)', None, None

        matches = fuzzy_process.extract(query_param, choices, limit=max(1, int(top_n)))
        filtered_matches = [m for m in matches if m[1] >= value_param]

        if not filtered_matches:
            return f'(No matches found for "{query_param}" with cutoff {value_param})', None, None
        
        return '', (('match', 'score'), tuple(filtered_matches)), None

    if function_key in {'VERB', 'NOUN', 'ADJ', 'ADV', 'PRON'}:
        pos_items = unique_preserve([token.text for token in spacy_doc if token.pos_ == function_key])
        return (', '.join(pos_items) if pos_items else '(No matches found!)'), None, None

    if function_key == 'FULL_NAME':
        person_names = unique_preserve([ent.text for ent in spacy_doc.ents if ent.label_ == 'PERSON'])
        if not person_names:
            matcher = Matcher(spacy_doc.vocab)
            matcher.add('proper_noun_bigram', [[{'POS': 'PROPN'}, {'POS': 'PROPN'}]])
            matches = matcher(spacy_doc)
            person_names = [spacy_doc[start_idx:end_idx].text for _, start_idx, end_idx in matches]
        return (', '.join(person_names) if person_names else '(No matches found!)'), None, None

    if function_key == 'PHONE_NUMBER':
        phone_numbers = extract_phones(text_value)
        return (', '.join(phone_numbers) if phone_numbers else '(No matches found!)'), None, None

    if function_key == 'ENTITY_RECOGNITION':
        entity_rows = [(ent.text, ent.label_, ent.start_char, ent.end_char) for ent in spacy_doc.ents]
        if not entity_rows:
            return '(No matches found!)', None, None
        return '', (('entity', 'label', 'start', 'end'), tuple(entity_rows)), None

    if function_key == 'DEPENDENCY':
        dependency_rows = [(token.text, token.head.text, token.dep_) for token in spacy_doc]
        if not dependency_rows:
            return '(No matches found!)', None, None
        return '', (('word', 'head', 'dependency'), tuple(dependency_rows)), None

    if function_key == 'STOP_WORDS':
        stopword_items = unique_preserve([token.text for token in spacy_doc if token.is_stop])
        return (', '.join(stopword_items) if stopword_items else '(No matches found!)'), None, None

    if function_key == 'LEMMATIZATION':
        lemma_rows = [(token.text, token.lemma_) for token in spacy_doc if token.lemma_ and token.lemma_ != token.text]
        if not lemma_rows:
            return '(No lemmatization changes)', None, None
        return '', (('original', 'lemma'), tuple(lemma_rows)), None

    if function_key == 'MOST_COMMON_WORDS':
        word_list = [token.text.lower() for token in spacy_doc if token.is_alpha and not token.is_stop]
        top_common = Counter(word_list).most_common(max(1, int(top_n)))
        if not top_common:
            return '(No matches found!)', None, None
        return '', (('word', 'occurrences'), tuple(top_common)), None

    if function_key == 'KEY_PHRASES':
        phrase_list = [chunk.text.strip() for chunk in spacy_doc.noun_chunks if chunk.text.strip()]
        top_phrases = Counter(phrase_list).most_common(max(1, int(top_n)))
        if not top_phrases:
            return '(No matches found!)', None, None
        return '', (('phrase', 'occurrences'), tuple(top_phrases)), None

    if function_key == 'NGRAMS':
        alpha_tokens = [token.text.lower() for token in spacy_doc if token.is_alpha and not token.is_stop]
        collected_ngrams: List[str] = []
        for size in range(ngram_sizes[0], ngram_sizes[1] + 1):
            collected_ngrams.extend(ngrams_list(alpha_tokens, size))
        top_ngrams = Counter(collected_ngrams).most_common(max(1, int(top_n)))
        if not top_ngrams:
            return '(No matches found!)', None, None
        return '', (('ngram', 'occurrences'), tuple(top_ngrams)), None

    if function_key == 'EMAILS':
        email_list = extract_emails(text_value)
        return (', '.join(email_list) if email_list else '(No matches found!)'), None, None

    if function_key == 'URLS':
        url_list = [url.rstrip('.,);]') for url in extract_urls(text_value)]
        return ('\n'.join(url_list) if url_list else '(No matches found!)'), None, None

    if function_key == 'IP_ADDRESSES':
        ip_list = extract_ips(text_value)
        return (', '.join(ip_list) if ip_list else '(No matches found!)'), None, None

    if function_key == 'SENTENCE_SPLIT':
        sentence_texts = [sent.text.strip() for sent in spacy_doc.sents if sent.text.strip()]
        return ('\n'.join(sentence_texts) if sentence_texts else '(No matches found!)'), None, None

    if function_key == 'POS_DISTRIBUTION':
        pos_counts: Dict[str, int] = defaultdict(int)
        for token in spacy_doc:
            pos_counts[token.pos_] += 1
        pos_rows = sorted(pos_counts.items(), key=lambda item: (-item[1], item[0]))
        if not pos_rows:
            return '(No matches found!)', None, None
        return '', (('pos', 'count'), tuple(pos_rows)), None

    if function_key == 'SENTIMENT':
        if sentiment_analyzer_cls is None:
            return '(Sentiment analyzer not available)', None, None
        sentiment_analyzer = sentiment_analyzer_cls()
        score = sentiment_analyzer.polarity_scores(text_value or '')
        sentiment_rows = tuple((metric, score.get(metric, 0)) for metric in ('neg', 'neu', 'pos', 'compound'))
        return '', (('metric', 'value'), sentiment_rows), None

    if function_key == 'SUMMARIZATION':
        sents = list(spacy_doc.sents)
        if len(sents) < 3:
            return '(Not enough sentences to summarize)', None, None
        
        word_frequencies = Counter(token.text.lower() for token in spacy_doc if token.is_alpha and not token.is_stop)
        max_freq = max(word_frequencies.values() or [1])
        for word in word_frequencies:
            word_frequencies[word] = word_frequencies[word] / max_freq

        sent_scores = Counter()
        for i, sent in enumerate(sents):
            for token in sent:
                if token.text.lower() in word_frequencies:
                    sent_scores[i] += word_frequencies[token.text.lower()]
        
        num_sents = max(1, int(len(sents) * summary_ratio))
        summary_indices = sorted([item[0] for item in sent_scores.most_common(num_sents)])
        summary = ' '.join(sents[i].text.strip() for i in summary_indices)
        return summary, None, None

    if function_key == 'TOPIC_MODELING':
        # Simple topic modeling based on noun chunks
        noun_chunks = [chunk.text.lower() for chunk in spacy_doc.noun_chunks if len(chunk.text.split()) > 1]
        top_topics = Counter(noun_chunks).most_common(max(1, int(top_n)))
        if not top_topics:
            return '(No topics found)', None, None
        return '', (('topic', 'occurrences'), tuple(top_topics)), None

    if function_key == 'READABILITY':
        if textstat is None:
            return '(textstat library not available)', None, None
        scores = [
            ('Flesch reading ease', textstat.flesch_reading_ease(text_value)),
            ('Flesch-Kincaid grade', textstat.flesch_kincaid_grade(text_value)),
            ('Gunning fog', textstat.gunning_fog(text_value)),
            ('SMOG index', textstat.smog_index(text_value)),
            ('Automated readability index', textstat.automated_readability_index(text_value)),
            ('Coleman-Liau index', textstat.coleman_liau_index(text_value)),
            ('Linsear write formula', textstat.linsear_write_formula(text_value)),
            ('Dale-Chall readability score', textstat.dale_chall_readability_score(text_value)),
        ]
        return '', (('metric', 'score'), tuple(scores)), None

    if function_key == 'WORD_CLOUD':
        if WordCloud is None or Image is None:
            return '(wordcloud or Pillow library not available)', None, None
        
        word_list = [token.text for token in spacy_doc if token.is_alpha and not token.is_stop]
        if not word_list:
            return '(No words to build a cloud)', None, None

        wc = WordCloud(width=800, height=400, background_color='white', collocations=False).generate(' '.join(word_list))
        return '', None, wc.to_image()

    if function_key == 'KEYWORDS':
        keywords = [token.lemma_.lower() for token in spacy_doc if token.pos_ in {'NOUN', 'PROPN', 'VERB'} and not token.is_stop and token.is_alpha]
        top_keywords = Counter(keywords).most_common(max(1, int(top_n)))
        if not top_keywords:
            return '(No keywords found)', None, None
        return '', (('keyword', 'score'), tuple(top_keywords)), None

    if function_key == 'POS_SEQUENCES':
        pos_tags = [token.pos_ for token in spacy_doc]
        collected_sequences: List[str] = []
        for size in range(ngram_sizes[0], ngram_sizes[1] + 1):
            if len(pos_tags) >= size:
                sequences = ['-'.join(pos_tags[i:i+size]) for i in range(len(pos_tags) - size + 1)]
                collected_sequences.extend(sequences)
        top_sequences = Counter(collected_sequences).most_common(max(1, int(top_n)))
        if not top_sequences:
            return '(No POS sequences found)', None, None
        return '', (('pos_sequence', 'occurrences'), tuple(top_sequences)), None

    if function_key == 'TEXT_STATISTICS':
        words = [token.text for token in spacy_doc if token.is_alpha]
        sentences = list(spacy_doc.sents)
        word_count = len(words)
        sentence_count = len(sentences)
        unique_words = len(set(w.lower() for w in words))
        
        stats = [
            ('Character count', len(text_value)),
            ('Word count (alpha only)', word_count),
            ('Sentence count', sentence_count),
            ('Unique words', unique_words),
            ('Lexical diversity (unique/total)', f'{unique_words / word_count:.2f}' if word_count > 0 else 'N/A'),
            ('Avg word length', f'{sum(len(w) for w in words) / word_count:.2f}' if word_count > 0 else 'N/A'),
            ('Avg sentence length (words)', f'{word_count / sentence_count:.2f}' if sentence_count > 0 else 'N/A'),
        ]
        return '', (('statistic', 'value'), tuple(stats)), None

    if function_key == 'ENTITY_FREQUENCY':
        entity_counts = Counter((ent.text, ent.label_) for ent in spacy_doc.ents)
        top_entities = entity_counts.most_common(max(1, int(top_n)))
        if not top_entities:
            return '(No named entities found)', None, None
        entity_rows = [(text, label, count) for (text, label), count in top_entities]
        return '', (('entity', 'label', 'count'), tuple(entity_rows)), None

    if function_key == 'ROOT_VERBS':
        root_verbs = []
        processed_sents = set()
        for sent in spacy_doc.sents:
            if sent.text in processed_sents:
                continue
            processed_sents.add(sent.text)
            if sent.root.pos_ == 'VERB':
                root_verbs.append((sent.root.lemma_, sent.text.strip()))
        if not root_verbs:
            return '(No root verbs found)', None, None
        return '', (('root_verb', 'sentence'), tuple(root_verbs)), None

    if function_key == 'COREFERENCE':
        if not hasattr(spacy_doc._, 'coref_clusters') or not spacy_doc._.coref_clusters:
            return '(Coreference model not available or no clusters found. Please use a model like en_core_web_trf)', None, None
        coref_rows = []
        for cluster in spacy_doc._.coref_clusters:
            main_mention = cluster.main.text
            mentions = ', '.join(m.text for m in cluster.mentions if m.text != main_mention)
            if mentions:
                coref_rows.append((main_mention, mentions))
        if not coref_rows:
            return '(No coreference clusters found)', None, None
        return '', (('entity', 'mentions'), tuple(coref_rows)), None

    if function_key == 'PASSIVE_VOICE':
        passive_sents = []
        for sent in spacy_doc.sents:
            if any(tok.dep_ == 'nsubjpass' for tok in sent):
                passive_sents.append((sent.text.strip(),))
        if not passive_sents:
            return '(No passive voice sentences found)', None, None
        return '', (('passive sentence',), tuple(passive_sents)), None

    if function_key == 'SUBORD_CLAUSES':
        clauses = []
        for token in spacy_doc:
            if token.dep_ == 'mark' and token.head.pos_ == 'VERB':
                clause_root = token.head
                clause_text = ' '.join(t.text for t in clause_root.subtree)
                clauses.append((token.text, clause_text))
        if not clauses:
            return '(No subordinate clauses found)', None, None
        return '', (('marker', 'clause'), tuple(clauses)), None

    if function_key == 'SVO_EXTRACTION':
        svo_triplets = []
        for sent in spacy_doc.sents:
            subjects = [tok for tok in sent if 'subj' in tok.dep_]
            for subj in subjects:
                verb = subj.head
                if verb.pos_ == 'VERB':
                    objects = [tok for tok in verb.children if 'obj' in tok.dep_]
                    for obj in objects:
                        svo_triplets.append((subj.text, verb.lemma_, obj.text))
        if not svo_triplets:
            return '(No SVO triplets found)', None, None
        return '', (('subject', 'verb', 'object'), tuple(unique_preserve(svo_triplets))), None

    if function_key == 'DEPENDENCY_DISTANCE':
        distances = [abs(token.i - token.head.i) for token in spacy_doc if token.dep_ != 'ROOT']
        if not distances:
            return '(Could not calculate dependency distances)', None, None
        avg_dist = sum(distances) / len(distances)
        max_dist = max(distances)
        
        dist_rows = [
            ('Average Distance', f'{avg_dist:.2f}'),
            ('Maximum Distance', max_dist),
            ('Token Count', len(spacy_doc))
        ]
        return '', (('metric', 'value'), tuple(dist_rows)), None

    if function_key == 'VP_EXTRACTION':
        matcher = Matcher(nlp_pipeline.vocab)
        pattern = [[{'POS': 'VERB', 'op': '+'}, {'POS': 'ADV', 'op': '*'}]]
        matcher.add('VP', pattern)
        matches = matcher(spacy_doc)
        vps = [spacy_doc[start:end].text for _, start, end in matches]
        if not vps:
            return '(No verb phrases found)', None, None
        top_vps = Counter(vps).most_common(max(1, int(top_n)))
        return '', (('verb_phrase', 'count'), tuple(top_vps)), None

    if function_key == 'WORD_SHAPES':
        shapes = [token.shape_ for token in spacy_doc]
        top_shapes = Counter(shapes).most_common(max(1, int(top_n)))
        if not top_shapes:
            return '(Could not determine word shapes)', None, None
        return '', (('shape', 'count'), tuple(top_shapes)), None

    if function_key == 'GENDER_ANALYSIS':
        male_pronouns = {'he', 'him', 'his'}
        female_pronouns = {'she', 'her', 'hers'}
        neutral_pronouns = {'they', 'them', 'their', 'theirs', 'it', 'its'}
        counts = Counter()
        for token in spacy_doc:
            lower = token.text.lower()
            if lower in male_pronouns:
                counts['male'] += 1
            elif lower in female_pronouns:
                counts['female'] += 1
            elif lower in neutral_pronouns:
                counts['neutral'] += 1
        if not counts:
            return '(No gendered pronouns found)', None, None
        return '', (('gender', 'count'), tuple(counts.most_common())), None

    if function_key == 'QUESTION_DETECTION':
        questions = [sent.text.strip() for sent in spacy_doc.sents if sent.text.strip().endswith('?')]
        if not questions:
            return '(No questions found)', None, None
        return '\n'.join(questions), None, None

    if function_key == 'CONCRETENESS':
        scores = [CONCRETENESS_RATINGS[token.lemma_] for token in spacy_doc if token.lemma_ in CONCRETENESS_RATINGS]
        if not scores:
            return '(No words with concreteness ratings found in text)', None, None
        avg_score = sum(scores) / len(scores)
        rows = [
            ('Average Concreteness', f'{avg_score:.2f} (1=Abstract, 5=Concrete)'),
            ('Words Found', len(scores))
        ]
        return '', (('metric', 'value'), tuple(rows)), None

    if function_key == 'SENTENCE_COMPLEXITY':
        if textstat is None:
            return '(textstat library not available)', None, None
        rows = []
        for sent in spacy_doc.sents:
            text = sent.text.strip()
            if len(text) > 5:
                rows.append((text, textstat.syllable_count(text)))
        if not rows:
            return '(No sentences to analyze)', None, None
        # Sort by most complex (most syllables)
        rows.sort(key=lambda x: x[1], reverse=True)
        return '', (('sentence', 'syllable_count'), tuple(rows[:max(1, int(top_n))])), None

    if function_key == 'PUNCT_ANALYSIS':
        puncts = [token.text for token in spacy_doc if token.is_punct]
        if not puncts:
            return '(No punctuation found)', None, None
        punct_counts = Counter(puncts).most_common()
        return '', (('punctuation', 'count'), tuple(punct_counts)), None

    if function_key == 'STOPWORD_PERCENTAGE':
        total_tokens = len(spacy_doc)
        if total_tokens == 0:
            return '(Empty text)', None, None
        stopword_count = len([token for token in spacy_doc if token.is_stop])
        percentage = (stopword_count / total_tokens) * 100
        rows = [
            ('Total Tokens', total_tokens),
            ('Stopword Count', stopword_count),
            ('Stopword Percentage', f'{percentage:.2f}%')
        ]
        return '', (('metric', 'value'), tuple(rows)), None

    if function_key == 'TTR':
        tokens = [token.text.lower() for token in spacy_doc if token.is_alpha]
        if not tokens:
            return '(No words to analyze)', None, None
        total_tokens = len(tokens)
        unique_types = len(set(tokens))
        ttr = unique_types / total_tokens
        rows = [
            ('Total Tokens (words)', total_tokens),
            ('Unique Types (words)', unique_types),
            ('Type-Token Ratio (TTR)', f'{ttr:.3f}')
        ]
        return '', (('metric', 'value'), tuple(rows)), None

    if function_key == 'EXTRACT_NUMBERS':
        numbers = [token.text for token in spacy_doc if token.like_num]
        if not numbers:
            return '(No numbers found)', None, None
        return ', '.join(sorted(set(numbers))), None, None

    if function_key == 'FORMALITY_SCORE':
        contractions = len(re.findall(r"\b(n't|'re|'s|'ve|'d|'ll|'m)\b", text_value.lower()))
        you_count = len([tok for tok in spacy_doc if tok.text.lower() == 'you'])
        total_words = len([tok for tok in spacy_doc if tok.is_alpha])
        if total_words == 0:
            return '(No words to analyze for formality)', None, None
        informal_indicators = contractions + you_count
        formality_score = (informal_indicators / total_words) * 100
        rows = [
            ('Contractions Count', contractions),
            ('Second-person Pronoun ("you") Count', you_count),
            ('Informality Score', f'{formality_score:.2f} (higher is more informal)')
        ]
        return '', (('metric', 'value'), tuple(rows)), None

    if function_key == 'EMPHASIS_ANALYSIS':
        exclamations = text_value.count('!')
        all_caps_words = len([tok for tok in spacy_doc if tok.is_upper and tok.is_alpha and len(tok.text) > 1])
        rows = [
            ('Exclamation Marks', exclamations),
            ('All-Caps Words', all_caps_words)
        ]
        return '', (('metric', 'count'), tuple(rows)), None

    if function_key == 'SENTENCE_START_ANALYSIS':
        sents = list(spacy_doc.sents)
        if not sents:
            return '(No sentences to analyze)', None, None
        first_word_pos = [sent[0].pos_ for sent in sents if len(sent) > 0]
        if not first_word_pos:
            return '(Could not analyze sentence starts)', None, None
        pos_counts = Counter(first_word_pos).most_common(max(1, int(top_n)))
        return '', (('starting_pos', 'count'), tuple(pos_counts)), None

    if function_key == 'LEXICAL_DENSITY':
        content_words = [token for token in spacy_doc if token.pos_ in {'NOUN', 'VERB', 'ADJ', 'ADV'}]
        total_words = [token for token in spacy_doc if token.is_alpha]
        if not total_words:
            return '(No words to analyze)', None, None
        
        density = len(content_words) / len(total_words)
        rows = [
            ('Content Words', len(content_words)),
            ('Total Words', len(total_words)),
            ('Lexical Density', f'{density:.3f}')
        ]
        return '', (('metric', 'value'), tuple(rows)), None

    if function_key == 'SENTENCE_TYPES':
        counts = Counter()
        for sent in spacy_doc.sents:
            text = sent.text.strip()
            if not text:
                continue
            
            if text.endswith('?'):
                counts['interrogative'] += 1
            elif text.endswith('!'):
                counts['exclamatory'] += 1
            elif sent[0].pos_ == 'VERB':
                counts['imperative'] += 1
            else:
                counts['declarative'] += 1
        
        if not counts:
            return '(No sentences found)', None, None
        
        return '', (('sentence_type', 'count'), tuple(counts.most_common())), None

    if function_key == 'HEDGE_DETECTION':
        hedge_words = {
            'may', 'might', 'could', 'can', 'would', 'should', 'perhaps', 'possibly', 'probably',
            'suggests', 'appears', 'seems', 'indicates', 'likely', 'unlikely', 'conceivably',
            'reportedly', 'allegedly', 'supposedly', 'arguably', 'essentially', 'generally',
            'sometimes', 'often', 'usually', 'typically', 'almost', 'nearly', 'about',
            'around', 'somewhat', 'partially', 'relatively', 'to some extent'
        }
        found_hedges = [token.text for token in spacy_doc if token.lemma_.lower() in hedge_words]
        if not found_hedges:
            return '(No hedge words found)', None, None
        hedge_counts = Counter(found_hedges).most_common()
        return '', (('hedge_word', 'count'), tuple(hedge_counts)), None

    if function_key == 'COLLOCATIONS':
        bigrams = ngrams_list([token.text.lower() for token in spacy_doc if token.is_alpha], 2)
        if not bigrams:
            return '(Not enough words to find collocations)', None, None
        top_collocations = Counter(bigrams).most_common(max(1, int(top_n)))
        return '', (('collocation', 'count'), tuple(top_collocations)), None

    if function_key == 'SIMILAR_SENTENCES':
        sents = [s for s in spacy_doc.sents if len(s.text.strip()) > 10]
        if len(sents) < 2:
            return '(Not enough sentences to compare)', None, None
        if not sents[0].has_vector:
            return '(The loaded spaCy model does not have sentence vectors. Try a medium, large, or transformer model.)', None, None
        
        similarities = []
        for i in range(len(sents)):
            for j in range(i + 1, len(sents)):
                similarity = sents[i].similarity(sents[j])
                if similarity > 0.8:
                    similarities.append((f'{similarity:.3f}', sents[i].text.strip(), sents[j].text.strip()))
        
        if not similarities:
            return '(No sentences found with similarity > 0.8)', None, None
        
        similarities.sort(key=lambda x: x[0], reverse=True)
        top_similarities = similarities[:max(1, int(top_n))]
        return '', (('similarity', 'sentence_1', 'sentence_2'), tuple(top_similarities)), None

    if function_key == 'POS_TAGGED_TEXT':
        tagged_text = ' '.join([f'{token.text}/{token.pos_}' for token in spacy_doc])
        if not tagged_text:
            return '(No text to tag)', None, None
        return tagged_text, None, None

    if function_key == 'READ_TIME':
        words = [token.text for token in spacy_doc if token.is_alpha]
        word_count = len(words)
        if word_count == 0:
            return '(No words to calculate reading time)', None, None
        
        wpm = 225
        reading_time_minutes = word_count / wpm
        seconds = int(reading_time_minutes * 60)
        
        minutes, sec = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        
        time_str = ''
        if hours > 0:
            time_str += f'{hours} hour(s) '
        if minutes > 0:
            time_str += f'{minutes} minute(s) '
        if sec > 0 or not time_str:
            time_str += f'{sec} second(s)'
            
        rows = [
            ('Word Count', word_count),
            ('Assumed WPM', wpm),
            ('Estimated Read Time', time_str.strip())
        ]
        return '', (('metric', 'value'), tuple(rows)), None

    if function_key == 'TEMPORAL_EXPRESSIONS':
        temporal_entities = [ent.text for ent in spacy_doc.ents if ent.label_ in {'DATE', 'TIME'}]
        if not temporal_entities:
            return '(No temporal expressions found)', None, None
        temporal_counts = Counter(temporal_entities).most_common(max(1, int(top_n)))
        return '', (('expression', 'count'), tuple(temporal_counts)), None

    if function_key == 'MONEY_EXTRACTION':
        money_entities = [ent.text for ent in spacy_doc.ents if ent.label_ == 'MONEY']
        if not money_entities:
            return '(No money/currency expressions found)', None, None
        money_counts = Counter(money_entities).most_common(max(1, int(top_n)))
        return '', (('expression', 'count'), tuple(money_counts)), None

    if function_key == 'ADJ_NOUN_PAIRS':
        pairs = []
        for i, token in enumerate(spacy_doc[:-1]):
            if token.pos_ == 'ADJ' and spacy_doc[i+1].pos_ == 'NOUN':
                pairs.append(f'{token.text} {spacy_doc[i+1].text}')
        if not pairs:
            return '(No adjective-noun pairs found)', None, None
        pair_counts = Counter(pairs).most_common(max(1, int(top_n)))
        return '', (('adj-noun_pair', 'count'), tuple(pair_counts)), None

    if function_key == 'PROPER_NOUNS':
        proper_nouns = [token.text for token in spacy_doc if token.pos_ == 'PROPN']
        if not proper_nouns:
            return '(No proper nouns found)', None, None
        pn_counts = Counter(proper_nouns).most_common(max(1, int(top_n)))
        return '', (('proper_noun', 'count'), tuple(pn_counts)), None

    if function_key == 'SENTENCE_WORD_COUNT':
        rows = [(sent.text.strip(), len([tok for tok in sent if tok.is_alpha])) for sent in spacy_doc.sents]
        if not rows:
            return '(No sentences to count)', None, None
        return '', (('sentence', 'word_count'), tuple(rows)), None

    if function_key == 'UNIQUE_WORDS':
        words = sorted(list(set(token.text.lower() for token in spacy_doc if token.is_alpha)))
        if not words:
            return '(No unique words found)', None, None
        return ', '.join(words), None, None

    if function_key == 'UNIQUE_LEMMAS':
        lemmas = sorted(list(set(token.lemma_.lower() for token in spacy_doc if token.is_alpha and token.lemma_ != '-')))
        if not lemmas:
            return '(No unique lemmas found)', None, None
        return ', '.join(lemmas), None, None

    if function_key == 'NOMINALIZATIONS':
        suffixes = ('tion', 'ment', 'sion', 'ance', 'ence', 'ity')
        nominalizations = [token.text for token in spacy_doc if token.pos_ == 'NOUN' and token.text.lower().endswith(suffixes)]
        if not nominalizations:
            return '(No nominalizations found)', None, None
        nom_counts = Counter(nominalizations).most_common(max(1, int(top_n)))
        return '', (('nominalization', 'count'), tuple(nom_counts)), None

    if function_key == 'GERUNDS_PARTICIPLES':
        gerunds = [token.text for token in spacy_doc if token.tag_ == 'VBG']
        if not gerunds:
            return '(No gerunds or participles found)', None, None
        gerund_counts = Counter(gerunds).most_common(max(1, int(top_n)))
        return '', (('gerund/participle', 'count'), tuple(gerund_counts)), None

    if function_key == 'PREP_PHRASES':
        phrases = []
        for token in spacy_doc:
            if token.dep_ == 'pobj':
                obj_phrase = ' '.join(t.text for t in token.subtree)
                full_phrase = f'{token.head.text} {obj_phrase}'
                phrases.append(full_phrase)
        if not phrases:
            return '(No prepositional phrases found)', None, None
        phrase_counts = Counter(phrases).most_common(max(1, int(top_n)))
        return '', (('prepositional_phrase', 'count'), tuple(phrase_counts)), None

    if function_key == 'SENTENCE_FINAL_POS':
        final_pos_tags = [sent.tokens[-1].pos_ for sent in spacy_doc.sents if len(sent.tokens) > 0]
        if not final_pos_tags:
            return '(No sentences to analyze)', None, None
        pos_counts = Counter(final_pos_tags).most_common()
        return '', (('final_pos_tag', 'count'), tuple(pos_counts)), None

    if function_key == 'QUANTITIES':
        quantity_entities = [ent.text for ent in spacy_doc.ents if ent.label_ == 'QUANTITY']
        if not quantity_entities:
            return '(No quantities found)', None, None
        quantity_counts = Counter(quantity_entities).most_common(max(1, int(top_n)))
        return '', (('quantity', 'count'), tuple(quantity_counts)), None

    if function_key == 'ORDINALS':
        ordinal_entities = [ent.text for ent in spacy_doc.ents if ent.label_ == 'ORDINAL']
        if not ordinal_entities:
            return '(No ordinals found)', None, None
        ordinal_counts = Counter(ordinal_entities).most_common(max(1, int(top_n)))
        return '', (('ordinal', 'count'), tuple(ordinal_counts)), None

    if function_key == 'PRODUCTS':
        product_entities = [ent.text for ent in spacy_doc.ents if ent.label_ == 'PRODUCT']
        if not product_entities:
            return '(No products found)', None, None
        product_counts = Counter(product_entities).most_common(max(1, int(top_n)))
        return '', (('product', 'count'), tuple(product_counts)), None

    if function_key == 'WORKS_OF_ART':
        art_entities = [ent.text for ent in spacy_doc.ents if ent.label_ == 'WORK_OF_ART']
        if not art_entities:
            return '(No works of art found)', None, None
        art_counts = Counter(art_entities).most_common(max(1, int(top_n)))
        return '', (('work_of_art', 'count'), tuple(art_counts)), None

    if function_key == 'ADV_ADJ_PAIRS':
        pairs = []
        for token in spacy_doc:
            if token.pos_ == 'ADV' and token.head.pos_ == 'ADJ':
                pairs.append(f'{token.text} {token.head.text}')
        if not pairs:
            return '(No adverb-adjective pairs found)', None, None
        pair_counts = Counter(pairs).most_common(max(1, int(top_n)))
        return '', (('adv-adj_pair', 'count'), tuple(pair_counts)), None

    if function_key == 'CLAUSE_COUNT':
        rows = []
        for sent in spacy_doc.sents:
            clause_count = len([token for token in sent if 'subj' in token.dep_])
            if clause_count == 0 and any(t.pos_ == 'VERB' for t in sent):
                clause_count = 1
            rows.append((sent.text.strip(), clause_count))
        if not rows:
            return '(No sentences to analyze)', None, None
        return '', (('sentence', 'clause_count'), tuple(rows)), None

    if function_key == 'INTERJECTION_ANALYSIS':
        interjections = [token.text for token in spacy_doc if token.pos_ == 'INTJ']
        if not interjections:
            return '(No interjections found)', None, None
        interjection_counts = Counter(interjections).most_common(max(1, int(top_n)))
        return '', (('interjection', 'count'), tuple(interjection_counts)), None

    if function_key == 'LANGUAGE_EXTRACTION':
        lang_entities = [ent.text for ent in spacy_doc.ents if ent.label_ == 'LANGUAGE']
        if not lang_entities:
            return '(No language/code names found)', None, None
        lang_counts = Counter(lang_entities).most_common(max(1, int(top_n)))
        return '', (('language/code', 'count'), tuple(lang_counts)), None

    if function_key == 'SIMILE_DETECTION':
        matcher = Matcher(nlp_pipeline.vocab)
        pattern1 = [{'LOWER': 'as'}, {'POS': 'ADJ'}, {'LOWER': 'as'}, {'POS': 'NOUN'}]
        pattern2 = [{'LOWER': 'like'}, {'LOWER': 'a'}, {'POS': 'NOUN'}]
        matcher.add('SIMILE', [pattern1, pattern2])
        matches = matcher(spacy_doc)
        similes = [spacy_doc[start:end].sent.text.strip() for _, start, end in matches]
        if not similes:
            return '(No similes found)', None, None
        unique_similes = unique_preserve(similes)
        return '\n'.join(f'- {s}' for s in unique_similes), None, None

    if function_key == 'PARAGRAPH_STATS':
        paragraphs = [p.strip() for p in text_value.split('\n\n') if p.strip()]
        if not paragraphs:
            return '(No paragraphs found)', None, None
        rows = []
        for i, para_text in enumerate(paragraphs):
            para_doc = nlp_pipeline(para_text)
            word_count = len([t for t in para_doc if t.is_alpha])
            sent_count = len(list(para_doc.sents))
            rows.append((i + 1, sent_count, word_count, para_text[:100] + '...'))
        if not rows:
            return '(Could not analyze paragraphs)', None, None
        return '', (('paragraph', 'sentences', 'words', 'preview'), tuple(rows)), None

    if function_key == 'GET_ORGS':
        orgs = [ent.text for ent in spacy_doc.ents if ent.label_ == 'ORG']
        if not orgs:
            return '(No organizations found)', None, None
        org_counts = Counter(orgs).most_common(max(1, int(top_n)))
        return '', (('organization', 'count'), tuple(org_counts)), None

    if function_key == 'GET_LOCATIONS':
        locations = [ent.text for ent in spacy_doc.ents if ent.label_ in {'GPE', 'LOC'}]
        if not locations:
            return '(No locations found)', None, None
        loc_counts = Counter(locations).most_common(max(1, int(top_n)))
        return '', (('location', 'count'), tuple(loc_counts)), None

    if function_key == 'CONCORDANCE':
        keyword = query_param.lower()
        if not keyword:
            return '(Please enter a keyword for concordance search)', None, None
        
        results = []
        window_size = 5 # words before and after
        for token in spacy_doc:
            if token.text.lower() == keyword:
                left_context = ' '.join([t.text for t in spacy_doc[max(0, token.i - window_size):token.i]])
                right_context = ' '.join([t.text for t in spacy_doc[token.i + 1:token.i + 1 + window_size]])
                results.append((left_context, token.text, right_context))
        
        if not results:
            return f'(Keyword "{query_param}" not found)', None, None
        
        return '', (('Left Context', 'Keyword', 'Right Context'), tuple(results[:max(1, int(top_n*2))])), None

    if function_key == 'HAPAX_LEGOMENA':
        words = [token.text.lower() for token in spacy_doc if token.is_alpha]
        counts = Counter(words)
        hapaxes = sorted([word for word, count in counts.items() if count == 1])
        if not hapaxes:
            return '(No once-occurring words found)', None, None
        return ', '.join(hapaxes), None, None

    if function_key == 'VERB_TENSE_ANALYSIS':
        tense_map = {
            'VBD': 'Past',
            'VBG': 'Present Participle/Gerund',
            'VBN': 'Past Participle',
            'VBP': 'Present (Non-3rd Person Singular)',
            'VBZ': 'Present (3rd Person Singular)',
            'VB': 'Base Form'
        }
        tense_counts = Counter()
        for token in spacy_doc:
            if token.pos_ == 'VERB':
                tense = tense_map.get(token.tag_, 'Other')
                tense_counts[tense] += 1
        
        if not tense_counts:
            return '(No verbs found)', None, None
        
        return '', (('Tense', 'Count'), tuple(tense_counts.most_common())), None

    if function_key == 'TEXT_PROFILE':
        if textstat is None or TextBlob is None:
            return '(textstat and textblob libraries are required for a full profile)', None, None
        
        words = [token.text for token in spacy_doc if token.is_alpha]
        word_count = len(words)
        sentence_count = len(list(spacy_doc.sents))
        unique_words = len(set(w.lower() for w in words))
        stopword_count = len([token for token in spacy_doc if token.is_stop])
        content_words = len([token for token in spacy_doc if token.pos_ in {'NOUN', 'VERB', 'ADJ', 'ADV'}])
        
        blob = TextBlob(text_value)
        polarity, subjectivity = blob.sentiment

        profile_rows = [
            ('Word Count', word_count),
            ('Sentence Count', sentence_count),
            ('Avg. Words per Sentence', f'{word_count / sentence_count:.2f}' if sentence_count > 0 else 'N/A'),
            ('Stopword Percentage', f'{(stopword_count / len(spacy_doc)) * 100:.2f}%' if len(spacy_doc) > 0 else 'N/A'),
            ('Lexical Density', f'{content_words / word_count:.3f}' if word_count > 0 else 'N/A'),
            ('Flesch Reading Ease', f'{textstat.flesch_reading_ease(text_value):.2f}'),
            ('Flesch-Kincaid Grade Level', f'{textstat.flesch_kincaid_grade(text_value):.2f}'),
            ('Sentiment Polarity', f'{polarity:.2f}'),
            ('Sentiment Subjectivity', f'{subjectivity:.2f}'),
        ]
        return '', (('Metric', 'Value'), tuple(profile_rows)), None

    if function_key == 'EVENTS':
        events = [ent.text for ent in spacy_doc.ents if ent.label_ == 'EVENT']
        if not events:
            return '(No events found)', None, None
        event_counts = Counter(events).most_common(max(1, int(top_n)))
        return '', (('Event', 'Count'), tuple(event_counts)), None

    if function_key == 'NORPS':
        norps = [ent.text for ent in spacy_doc.ents if ent.label_ == 'NORP']
        if not norps:
            return '(No nationalities, religious, or political groups found)', None, None
        norp_counts = Counter(norps).most_common(max(1, int(top_n)))
        return '', (('Group', 'Count'), tuple(norp_counts)), None

    if function_key == 'LAWS':
        laws = [ent.text for ent in spacy_doc.ents if ent.label_ == 'LAW']
        if not laws:
            return '(No laws found)', None, None
        law_counts = Counter(laws).most_common(max(1, int(top_n)))
        return '', (('Law', 'Count'), tuple(law_counts)), None

    if function_key == 'SENTENCE_SENTIMENT':
        if sentiment_analyzer_cls is None:
            return '(Sentiment analyzer not available)', None, None
        sentiment_analyzer = sentiment_analyzer_cls()
        rows = []
        for sent in spacy_doc.sents:
            text = sent.text.strip()
            if not text:
                continue
            score = sentiment_analyzer.polarity_scores(text)
            compound = score['compound']
            if compound > 0.05:
                label = 'Positive'
            elif compound < -0.05:
                label = 'Negative'
            else:
                label = 'Neutral'
            rows.append((text, f'{compound:.2f}', label))
        if not rows:
            return '(No sentences to analyze)', None, None
        return '', (('Sentence', 'Compound Score', 'Label'), tuple(rows)), None

    if function_key == 'DEP_PATH':
        words = query_param.split()
        if len(words) != 2:
            return '(Please provide two words separated by a space for Dependency Path)', None, None
        
        tokens = [tok for tok in spacy_doc if tok.text.lower() in [w.lower() for w in words]]
        if len(tokens) < 2:
            return '(Could not find both words in the text)', None, None
        
        # Find the path between the first occurrences
        token1, token2 = tokens[0], tokens[1]
        path = token1.ancestors
        path2 = token2.ancestors
        
        # Find common ancestor
        common_ancestor = None
        for p1 in path:
            if p1 in path2:
                common_ancestor = p1
                break
        
        if not common_ancestor:
            return '(No dependency path found between the words)', None, None

        path_to_ancestor1 = [t.text for t in token1.ancestors if t.i >= common_ancestor.i]
        path_to_ancestor2 = [t.text for t in token2.ancestors if t.i >= common_ancestor.i]
        
        full_path = path_to_ancestor1 + [common_ancestor.text] + list(reversed(path_to_ancestor2))
        return ' -> '.join(full_path), None, None

    if function_key == 'TEXT_SIMILARITY':
        if not text_param:
            return '(Please provide a second text to compare with)', None, None
        
        doc2 = nlp_pipeline(text_param)
        if not spacy_doc.has_vector or not doc2.has_vector:
            return '(One or both texts do not have vectors for comparison. Try a larger model.)', None, None
        
        similarity = spacy_doc.similarity(doc2)
        return f'The similarity between the two texts is: {similarity:.3f}', None, None

    if function_key == 'KEY_SENTENCES':
        sents = list(spacy_doc.sents)
        if len(sents) < 3:
            return '(Not enough sentences to analyze)', None, None
        
        word_frequencies = Counter(token.text.lower() for token in spacy_doc if token.is_alpha and not token.is_stop)
        max_freq = max(word_frequencies.values() or [1])
        for word in word_frequencies:
            word_frequencies[word] = word_frequencies[word] / max_freq

        sent_scores = Counter()
        for i, sent in enumerate(sents):
            for token in sent:
                if token.text.lower() in word_frequencies:
                    sent_scores[i] += word_frequencies[token.text.lower()]
        
        top_sents = sent_scores.most_common(max(1, int(top_n)))
        key_sentences = [sents[i].text.strip() for i, score in top_sents]
        return '\n'.join(f'- {s}' for s in key_sentences), None, None

    if function_key == 'ENTITY_DENSITY':
        num_ents = len(spacy_doc.ents)
        num_tokens = len(spacy_doc)
        density = num_ents / num_tokens if num_tokens > 0 else 0
        rows = [
            ('Named Entity Count', num_ents),
            ('Token Count', num_tokens),
            ('Entity Density', f'{density:.3f}')
        ]
        return '', (('Metric', 'Value'), tuple(rows)), None

    if function_key == 'SYNTACTIC_COMPLEXITY':
        depths = []
        for sent in spacy_doc.sents:
            root = sent.root
            max_depth = 0
            for token in sent:
                ancestors = list(token.ancestors)
                depth = len(ancestors)
                if depth > max_depth:
                    max_depth = depth
            depths.append(max_depth)
        avg_depth = sum(depths) / len(depths) if depths else 0
        rows = [
            ('Average Max Sentence Depth', f'{avg_depth:.2f}'),
            ('Sentence Count', len(depths))
        ]
        return '', (('Metric', 'Value'), tuple(rows)), None

    if function_key == 'PRONOUN_NOUN_RATIO':
        pronouns = len([t for t in spacy_doc if t.pos_ == 'PRON'])
        nouns = len([t for t in spacy_doc if t.pos_ in {'NOUN', 'PROPN'}])
        ratio = pronouns / nouns if nouns > 0 else float('inf')
        rows = [
            ('Pronoun Count', pronouns),
            ('Noun Count', nouns),
            ('Pronoun-to-Noun Ratio', f'{ratio:.3f}')
        ]
        return '', (('Metric', 'Value'), tuple(rows)), None

    if function_key == 'CONJUNCTION_ANALYSIS':
        conjunctions = [t.text.lower() for t in spacy_doc if t.pos_ == 'CCONJ']
        if not conjunctions:
            return '(No coordinating conjunctions found)', None, None
        counts = Counter(conjunctions).most_common()
        return '', (('Conjunction', 'Count'), tuple(counts)), None

    if function_key == 'TOPIC_MODELING_LDA':
        if Dictionary is None or LdaModel is None:
            return '(gensim library not available for LDA)', None, None
        
        texts = [[token.lemma_ for token in sent if token.is_alpha and not token.is_stop] for sent in spacy_doc.sents]
        dictionary = Dictionary(texts)
        corpus = [dictionary.doc2bow(text) for text in texts]
        
        if not corpus:
            return '(Not enough text to perform LDA)', None, None

        lda_model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=max(2, int(top_n/2)), passes=10)
        topics = lda_model.print_topics(num_words=5)
        topic_rows = [(f'Topic {i+1}', words) for i, words in topics]
        return '', (('Topic', 'Top Words'), tuple(topic_rows)), None

    if function_key == 'DISCOURSE_CONNECTIVES':
        connectives = {
            'however', 'therefore', 'furthermore', 'in addition', 'consequently', 'nevertheless',
            'in contrast', 'on the other hand', 'for example', 'for instance', 'in conclusion',
            'in summary', 'similarly', 'likewise', 'accordingly', 'hence', 'thus', 'meantime'
        }
        found_connectives = [token.text.lower() for token in spacy_doc if token.text.lower() in connectives]
        if not found_connectives:
            return '(No discourse connectives found)', None, None
        connective_counts = Counter(found_connectives).most_common()
        return '', (('Connective', 'Count'), tuple(connective_counts)), None

    if function_key == 'WORD_AMBIGUITY':
        if wordnet is None:
            return '(nltk library with wordnet is not available)', None, None
        
        words = list(set(token.lemma_.lower() for token in spacy_doc if token.is_alpha and not token.is_stop))
        ambiguity = {word: len(wordnet.synsets(word)) for word in words}
        top_ambiguous = sorted(ambiguity.items(), key=lambda item: -item[1])[:max(1, int(top_n))]
        if not top_ambiguous:
            return '(Could not calculate word ambiguity)', None, None
        return '', (('Word', 'Number of Meanings'), tuple(top_ambiguous)), None

    if function_key == 'FACILITIES':
        facilities = [ent.text for ent in spacy_doc.ents if ent.label_ == 'FAC']
        if not facilities:
            return '(No facilities found)', None, None
        facility_counts = Counter(facilities).most_common(max(1, int(top_n)))
        return '', (('Facility', 'Count'), tuple(facility_counts)), None

    return '(No output)', None, None
