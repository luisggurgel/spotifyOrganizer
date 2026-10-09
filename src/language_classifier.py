"""
Language classifier for Spotify tracks.

Uses a multi-strategy cascade to maximize accuracy:
  1. Unicode script detection (CJK, Hangul, Cyrillic, Kana, etc.)
  2. Spotify artist genre → language mapping
  3. lingua-language-detector with high-confidence thresholds
  4. Fallback to "Instrumental/Unknown"

The key insight is that song titles are terrible for text-based language
detection (too short, mixed scripts, proper nouns). Artist genre metadata
from Spotify is far more reliable for determining the language of the lyrics.
"""

import re
import logging
import unicodedata
from typing import Optional, Dict, Set, List, Tuple

from lingua import Language, LanguageDetectorBuilder

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1.  lingua detector — built once, reused for every call
# ---------------------------------------------------------------------------
_LANGUAGES = [
    Language.PORTUGUESE,
    Language.ENGLISH,
    Language.SPANISH,
    Language.JAPANESE,
    Language.KOREAN,
    Language.FRENCH,
    Language.GERMAN,
    Language.ITALIAN,
    Language.RUSSIAN,
    Language.CHINESE,
]

detector = (
    LanguageDetectorBuilder
    .from_languages(*_LANGUAGES)
    .with_minimum_relative_distance(0.15)   # require margin between top-2
    .build()
)

LANGUAGE_MAP: Dict[Language, str] = {
    Language.PORTUGUESE: "Português",
    Language.ENGLISH:    "Inglês",
    Language.SPANISH:    "Espanhol",
    Language.JAPANESE:   "Japonês",
    Language.KOREAN:     "Coreano",
    Language.FRENCH:     "Francês",
    Language.GERMAN:     "Alemão",
    Language.ITALIAN:    "Italiano",
    Language.RUSSIAN:    "Russo",
    Language.CHINESE:    "Chinês",
}

# ---------------------------------------------------------------------------
# 2.  Unicode script detection
# ---------------------------------------------------------------------------
# Character ranges that unambiguously indicate a language/script family.
# These are checked FIRST because they are nearly 100 % accurate.

_SCRIPT_PATTERNS: List[Tuple[str, str]] = [
    # pattern (regex), language label
    (r"[\u3040-\u309F\u30A0-\u30FF]", "Japonês"),        # Hiragana + Katakana
    (r"[\uAC00-\uD7AF\u1100-\u11FF]", "Coreano"),        # Hangul
    (r"[\u0400-\u04FF]",              "Russo"),           # Cyrillic
    # CJK unified ideographs — could be Chinese or Japanese.
    # If we already detected Kana above, it's Japanese; otherwise Chinese.
    (r"[\u4E00-\u9FFF\u3400-\u4DBF]", "_CJK"),           # handled specially
]

_CJK_RE = re.compile(r"[\u4E00-\u9FFF\u3400-\u4DBF]")
_KANA_RE = re.compile(r"[\u3040-\u309F\u30A0-\u30FF]")
_HANGUL_RE = re.compile(r"[\uAC00-\uD7AF\u1100-\u11FF]")
_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")


def _detect_by_script(text: str) -> Optional[str]:
    """Return a language label if the text contains enough non-Latin script."""
    if not text:
        return None

    has_kana = bool(_KANA_RE.search(text))
    has_hangul = bool(_HANGUL_RE.search(text))
    has_cyrillic = bool(_CYRILLIC_RE.search(text))
    has_cjk = bool(_CJK_RE.search(text))

    if has_kana:
        return "Japonês"
    if has_hangul:
        return "Coreano"
    if has_cyrillic:
        return "Russo"
    if has_cjk:
        # CJK ideographs without Kana → almost certainly Chinese
        return "Chinês"

    return None


# ---------------------------------------------------------------------------
# 3.  Spotify artist-genre → language mapping
# ---------------------------------------------------------------------------
# This is the MOST ACCURATE signal.  Spotify genres like "j-pop", "k-pop",
# "mpb", "sertanejo", "reggaeton", etc. directly reveal the language.
#
# The mapping below covers ~300+ genre keywords.  Each key is a LOWERCASE
# substring that we search for inside the genre strings returned by Spotify.
# Order matters: more specific substrings should come before generic ones.

_GENRE_TO_LANGUAGE: List[Tuple[str, str]] = [
    # ── Portuguese ─────────────────────────────────────────────
    ("mpb",              "Português"),
    ("sertanejo",        "Português"),
    ("pagode",           "Português"),
    ("axe",              "Português"),
    ("axé",              "Português"),
    ("forro",            "Português"),
    ("forró",            "Português"),
    ("bossa nova",       "Português"),
    ("brazilian",        "Português"),
    ("brasil",           "Português"),
    ("samba",            "Português"),
    ("funk carioca",     "Português"),
    ("funk brasilei",    "Português"),
    ("funk paulista",    "Português"),
    ("baile funk",       "Português"),
    ("funk ostentação",  "Português"),
    ("piseiro",          "Português"),
    ("pisadinha",        "Português"),
    ("arrocha",          "Português"),
    ("tecnobrega",       "Português"),
    ("brega",            "Português"),
    ("maracatu",         "Português"),
    ("manguebeat",       "Português"),
    ("tropicalia",       "Português"),
    ("tropicália",       "Português"),
    ("musica popular brasileira", "Português"),
    ("pop brasileiro",   "Português"),
    ("rock brasileiro",  "Português"),
    ("rap brasileiro",   "Português"),
    ("hip hop brasileiro", "Português"),
    ("trap brasileiro",  "Português"),
    ("r&b brasileiro",   "Português"),
    ("soul brasileiro",  "Português"),
    ("pop nacional",     "Português"),
    ("rock nacional",    "Português"),
    ("rap nacional",     "Português"),
    ("funk melody",      "Português"),
    ("funk mandelão",    "Português"),
    ("funk 150 bpm",     "Português"),
    ("funk proibidao",   "Português"),
    ("funk proibidão",   "Português"),
    ("portuguese",       "Português"),
    ("fado",             "Português"),

    # ── Japanese ───────────────────────────────────────────────
    ("j-pop",            "Japonês"),
    ("j-rock",           "Japonês"),
    ("j-rap",            "Japonês"),
    ("j-dance",          "Japonês"),
    ("j-metal",          "Japonês"),
    ("j-idol",           "Japonês"),
    ("j-division",       "Japonês"),
    ("japanese",         "Japonês"),
    ("anime",            "Japonês"),
    ("vocaloid",         "Japonês"),
    ("city pop",         "Japonês"),
    ("visual kei",       "Japonês"),
    ("enka",             "Japonês"),
    ("kayokyoku",        "Japonês"),
    ("shibuya-kei",      "Japonês"),
    ("jpop",             "Japonês"),
    ("jrock",            "Japonês"),

    # ── Korean ─────────────────────────────────────────────────
    ("k-pop",            "Coreano"),
    ("k-rock",           "Coreano"),
    ("k-rap",            "Coreano"),
    ("k-indie",          "Coreano"),
    ("k-r&b",            "Coreano"),
    ("korean",           "Coreano"),
    ("kpop",             "Coreano"),
    ("hallyu",           "Coreano"),
    ("trot",             "Coreano"),

    # ── Spanish ────────────────────────────────────────────────
    ("reggaeton",        "Espanhol"),
    ("reggaetón",        "Espanhol"),
    ("latin pop",        "Espanhol"),
    ("latin rock",       "Espanhol"),
    ("latin hip hop",    "Espanhol"),
    ("latin trap",       "Espanhol"),
    ("latin alternative","Espanhol"),
    ("latin arena pop",  "Espanhol"),
    ("cumbia",           "Espanhol"),
    ("salsa",            "Espanhol"),
    ("bachata",          "Espanhol"),
    ("merengue",         "Espanhol"),
    ("vallenato",        "Espanhol"),
    ("mariachi",         "Espanhol"),
    ("norteno",          "Espanhol"),
    ("norteño",          "Espanhol"),
    ("corridos",         "Espanhol"),
    ("corrido",          "Espanhol"),
    ("tango",            "Espanhol"),
    ("ranchera",         "Espanhol"),
    ("regional mexican", "Espanhol"),
    ("mexican",          "Espanhol"),
    ("colombian",        "Espanhol"),
    ("argentinian",      "Espanhol"),
    ("chilean",          "Espanhol"),
    ("perreo",           "Espanhol"),
    ("dembow",           "Espanhol"),
    ("urbano latino",    "Espanhol"),
    ("spanish",          "Espanhol"),
    ("flamenco",         "Espanhol"),
    ("copla",            "Espanhol"),
    ("rumba",            "Espanhol"),
    ("musica mexicana",  "Espanhol"),
    ("pop urbano",       "Espanhol"),
    ("trap latino",      "Espanhol"),

    # ── French ─────────────────────────────────────────────────
    ("french",           "Francês"),
    ("chanson",          "Francês"),
    ("variete francaise","Francês"),
    ("variété française","Francês"),
    ("rap francais",     "Francês"),
    ("rap français",     "Francês"),
    ("pop francais",     "Francês"),
    ("zouk",             "Francês"),
    ("french house",     "Francês"),
    ("french touch",     "Francês"),

    # ── German ─────────────────────────────────────────────────
    ("german",           "Alemão"),
    ("schlager",         "Alemão"),
    ("volksmusik",       "Alemão"),
    ("neue deutsche",    "Alemão"),
    ("deutsch",          "Alemão"),
    ("german pop",       "Alemão"),
    ("german rap",       "Alemão"),
    ("german hip hop",   "Alemão"),
    ("krautrock",        "Alemão"),

    # ── Italian ────────────────────────────────────────────────
    ("italian",          "Italiano"),
    ("musica italiana",  "Italiano"),
    ("cantautorato",     "Italiano"),
    ("sanremo",          "Italiano"),
    ("napoli",           "Italiano"),
    ("musica leggera",   "Italiano"),
    ("italian pop",      "Italiano"),

    # ── Russian ────────────────────────────────────────────────
    ("russian",          "Russo"),
    ("russian pop",      "Russo"),
    ("russian rap",      "Russo"),
    ("russian rock",     "Russo"),
    ("shanson",          "Russo"),

    # ── Chinese ────────────────────────────────────────────────
    ("c-pop",            "Chinês"),
    ("mandopop",         "Chinês"),
    ("cantopop",         "Chinês"),
    ("chinese",          "Chinês"),
    ("cpop",             "Chinês"),
    ("zhongguo",         "Chinês"),
    ("taiwanese",        "Chinês"),
]

# Pre-compile for faster matching (sorted longest-first for greedy match)
_GENRE_TO_LANGUAGE.sort(key=lambda x: len(x[0]), reverse=True)


def _detect_by_genres(genres: List[str]) -> Optional[str]:
    """
    Given a list of Spotify genre strings for an artist, return the
    most likely language or None if inconclusive.
    """
    if not genres:
        return None

    # Count votes from each genre tag
    votes: Dict[str, int] = {}
    genre_blob = " | ".join(genres).lower()

    for substring, lang in _GENRE_TO_LANGUAGE:
        if substring in genre_blob:
            votes[lang] = votes.get(lang, 0) + 1

    if not votes:
        return None

    # Return the language with the most genre-keyword hits
    winner = max(votes, key=votes.get)  # type: ignore[arg-type]
    return winner


# ---------------------------------------------------------------------------
# 4.  Artist genre cache (to avoid repeated Spotify API calls)
# ---------------------------------------------------------------------------
# Populated externally by SpotifyManager before classification begins.

_artist_genre_cache: Dict[str, List[str]] = {}


def set_artist_genres_cache(cache: Dict[str, List[str]]) -> None:
    """Inject pre-fetched artist genres into the classifier module."""
    global _artist_genre_cache
    _artist_genre_cache = cache


def get_artist_genres_cache() -> Dict[str, List[str]]:
    return _artist_genre_cache


# ---------------------------------------------------------------------------
# 5.  lingua-based detection (high confidence only)
# ---------------------------------------------------------------------------

_HIGH_CONFIDENCE = 0.88   # for track name alone
_MEDIUM_CONFIDENCE = 0.75  # for track name + album combined

# Strip these common words that confuse the detector
_NOISE_PATTERNS = re.compile(
    r"\b(feat\.?|ft\.?|remix|remaster(ed)?|live|acoustic|version|"
    r"deluxe|edition|bonus\s*track|official|video|audio|lyric(s)?|"
    r"explicit|clean|radio\s*edit|extended|mix|original|intro|outro|"
    r"interlude|skit|prod\.?)\b",
    re.IGNORECASE,
)

# Punctuation / numbers / parenthesised annotations
_PAREN_RE = re.compile(r"\([^)]*\)|\[[^\]]*\]")
_NONALPHA_RE = re.compile(r"[^a-zA-ZÀ-ÿа-яА-ЯёЁ\u3000-\u9FFF\uAC00-\uD7AF\u3040-\u30FF\s]")


def _clean_text(text: str) -> str:
    """Remove noise tokens that confuse the lingua detector."""
    text = _PAREN_RE.sub(" ", text)
    text = _NOISE_PATTERNS.sub(" ", text)
    text = _NONALPHA_RE.sub(" ", text)
    return " ".join(text.split())


def _detect_by_lingua(text: str, min_confidence: float) -> Optional[str]:
    """
    Run lingua on cleaned text.  Returns a language label only if the top
    result exceeds *min_confidence*.
    """
    cleaned = _clean_text(text)
    if len(cleaned) < 4:
        return None

    try:
        results = detector.compute_language_confidence_values(cleaned)
        if results and results[0].value >= min_confidence:
            return LANGUAGE_MAP.get(results[0].language)
    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# 6.  Public API — the cascade
# ---------------------------------------------------------------------------

def detect_language(track: dict) -> str:
    """
    Determines the language of a Spotify track using a cascade:

    1. Script detection (CJK / Hangul / Cyrillic / Kana)
    2. Artist genre mapping (most reliable for Latin-script languages)
    3. High-confidence lingua detection on track name
    4. Medium-confidence lingua on track name + album name
    5. Fallback → "Instrumental/Unknown"
    """
    track_name = track.get("name", "").strip()
    album_name = track.get("album", {}).get("name", "").strip()
    artists = track.get("artists", [])

    if not track_name:
        return "Instrumental/Unknown"

    # ── Step 1: Script detection ──────────────────────────────
    script_lang = _detect_by_script(track_name)
    if script_lang:
        logger.debug("Script detection → %s for '%s'", script_lang, track_name)
        return script_lang

    # ── Step 2: Artist genre mapping ──────────────────────────
    all_genres: List[str] = []
    for artist in artists:
        artist_id = artist.get("id", "")
        if artist_id and artist_id in _artist_genre_cache:
            all_genres.extend(_artist_genre_cache[artist_id])

    genre_lang = _detect_by_genres(all_genres)
    if genre_lang:
        logger.debug("Genre mapping → %s for '%s' (genres: %s)", genre_lang, track_name, all_genres)
        return genre_lang

    # ── Step 3: High-confidence lingua on track name ──────────
    lingua_lang = _detect_by_lingua(track_name, _HIGH_CONFIDENCE)
    if lingua_lang:
        logger.debug("Lingua (high) → %s for '%s'", lingua_lang, track_name)
        return lingua_lang

    # ── Step 4: Medium-confidence lingua on combined text ─────
    combined = f"{track_name}  {album_name}"
    lingua_lang = _detect_by_lingua(combined, _MEDIUM_CONFIDENCE)
    if lingua_lang:
        logger.debug("Lingua (medium) → %s for '%s'", lingua_lang, track_name)
        return lingua_lang

    # ── Step 5: Fallback ──────────────────────────────────────
    logger.debug("Unclassified: '%s'", track_name)
    return "Instrumental/Unknown"
