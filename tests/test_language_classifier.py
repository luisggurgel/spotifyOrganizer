"""
Tests for the improved language classifier.

These tests cover:
  - Script-based detection (CJK, Hangul, Cyrillic, Kana)
  - Genre-based detection via cached artist genres
  - lingua fallback detection
  - Edge cases (empty titles, symbols, mixed scripts)
"""

from src.language_classifier import (
    detect_language,
    set_artist_genres_cache,
    _detect_by_script,
    _detect_by_genres,
)


# ---------------------------------------------------------------------------
# Script detection
# ---------------------------------------------------------------------------

def test_detect_japanese_by_script():
    """Hiragana/katakana in title → Japanese regardless of genres."""
    track = {
        'name': '夜に駆ける',
        'artists': [{'name': 'YOASOBI', 'id': 'a1'}],
        'album': {'name': 'THE BOOK'},
    }
    assert detect_language(track) == 'Japonês'


def test_detect_korean_by_script():
    track = {
        'name': '봄날',
        'artists': [{'name': 'BTS', 'id': 'a2'}],
        'album': {'name': 'Wings'},
    }
    assert detect_language(track) == 'Coreano'


def test_detect_russian_by_script():
    track = {
        'name': 'Кукушка',
        'artists': [{'name': 'Кино', 'id': 'a3'}],
        'album': {'name': 'Черный альбом'},
    }
    assert detect_language(track) == 'Russo'


def test_detect_chinese_by_script():
    """CJK ideographs WITHOUT Kana → Chinese."""
    track = {
        'name': '月亮代表我的心',
        'artists': [{'name': '邓丽君', 'id': 'a4'}],
        'album': {'name': '邓丽君全集'},
    }
    assert detect_language(track) == 'Chinês'


# ---------------------------------------------------------------------------
# Genre-based detection
# ---------------------------------------------------------------------------

def test_detect_portuguese_by_genre():
    """Artist with sertanejo genre → Português even with Latin-script title."""
    set_artist_genres_cache({
        'art_pt': ['sertanejo', 'sertanejo universitario'],
    })
    track = {
        'name': 'Amor de Violeiro',
        'artists': [{'name': 'Artista Teste', 'id': 'art_pt'}],
        'album': {'name': 'Álbum'},
    }
    assert detect_language(track) == 'Português'


def test_detect_spanish_by_genre():
    set_artist_genres_cache({
        'art_es': ['reggaeton', 'latin pop'],
    })
    track = {
        'name': 'Dákiti',
        'artists': [{'name': 'Bad Bunny', 'id': 'art_es'}],
        'album': {'name': 'El Último Tour del Mundo'},
    }
    assert detect_language(track) == 'Espanhol'


def test_detect_kpop_by_genre():
    """k-pop genre → Coreano even if the title is in Latin script."""
    set_artist_genres_cache({
        'art_kr': ['k-pop', 'k-pop boy group'],
    })
    track = {
        'name': 'Dynamite',
        'artists': [{'name': 'BTS', 'id': 'art_kr'}],
        'album': {'name': 'BE'},
    }
    assert detect_language(track) == 'Coreano'


def test_detect_jpop_by_genre():
    set_artist_genres_cache({
        'art_jp': ['j-pop', 'anime'],
    })
    track = {
        'name': 'Pretender',
        'artists': [{'name': 'Official HIGE DANdism', 'id': 'art_jp'}],
        'album': {'name': 'Traveler'},
    }
    assert detect_language(track) == 'Japonês'


def test_detect_french_by_genre():
    set_artist_genres_cache({
        'art_fr': ['chanson', 'french pop'],
    })
    track = {
        'name': 'La Vie en Rose',
        'artists': [{'name': 'Edith Piaf', 'id': 'art_fr'}],
        'album': {'name': 'Best Of'},
    }
    assert detect_language(track) == 'Francês'


def test_detect_brazilian_funk_by_genre():
    """funk carioca → Português (not English 'funk')."""
    set_artist_genres_cache({
        'art_funk': ['funk carioca', 'baile funk'],
    })
    track = {
        'name': 'Vai Malandra',
        'artists': [{'name': 'Anitta', 'id': 'art_funk'}],
        'album': {'name': 'Kisses'},
    }
    assert detect_language(track) == 'Português'


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_track_name():
    set_artist_genres_cache({})
    track = {
        'name': '',
        'artists': [],
        'album': {},
    }
    assert detect_language(track) == 'Instrumental/Unknown'


def test_symbols_only():
    set_artist_genres_cache({})
    track = {
        'name': '!!!',
        'artists': [{'name': '???', 'id': 'unknown'}],
        'album': {'name': '...'},
    }
    assert detect_language(track) == 'Instrumental/Unknown'


def test_missing_artist_id_does_not_crash():
    """Artists without an 'id' key should not cause errors."""
    set_artist_genres_cache({})
    track = {
        'name': 'Some Track',
        'artists': [{'name': 'No ID Artist'}],
        'album': {'name': 'Album'},
    }
    # Should not raise — result depends on lingua detection
    result = detect_language(track)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def test_script_detection_hiragana():
    assert _detect_by_script('こんにちは') == 'Japonês'


def test_script_detection_hangul():
    assert _detect_by_script('안녕하세요') == 'Coreano'


def test_script_detection_cyrillic():
    assert _detect_by_script('привет') == 'Russo'


def test_script_detection_latin_returns_none():
    assert _detect_by_script('Hello World') is None


def test_genre_mapping_multiple_votes():
    """When multiple genres point to the same language, it should win."""
    result = _detect_by_genres(['sertanejo', 'mpb', 'bossa nova', 'pop'])
    assert result == 'Português'


def test_genre_mapping_empty():
    assert _detect_by_genres([]) is None
