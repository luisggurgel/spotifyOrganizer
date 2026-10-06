from src.language_classifier import detect_language

def test_detect_portuguese():
    track = {
        'name': 'Águas de Março',
        'artists': [{'name': 'Elis Regina'}, {'name': 'Tom Jobim'}],
        'album': {'name': 'Elis & Tom'}
    }
    assert detect_language(track) == 'Português'

def test_detect_english():
    track = {
        'name': 'Weird Fishes/ Arpeggi',
        'artists': [{'name': 'Radiohead'}],
        'album': {'name': 'In Rainbows'}
    }
    assert detect_language(track) == 'Inglês'

def test_detect_japanese():
    track = {
        'name': '夜に駆ける',
        'artists': [{'name': 'YOASOBI'}],
        'album': {'name': 'THE BOOK'}
    }
    assert detect_language(track) == 'Japonês'

def test_detect_instrumental_or_unknown():
    # Emojis or symbols usually fail language detection or have very low confidence
    track = {
        'name': 'Instrumental Part 1',
        'artists': [{'name': 'Unknown Artist'}],
        'album': {'name': 'Beats'}
    }
    # Wait, 'Instrumental Part 1' is English text, it might detect as English
    # Let's test with just symbols
    track2 = {
        'name': '!!!',
        'artists': [{'name': '???'}],
        'album': {'name': '...'}
    }
    assert detect_language(track2) == 'Instrumental/Unknown'
    
    track3 = {
        'name': '',
        'artists': [],
        'album': {}
    }
    assert detect_language(track3) == 'Instrumental/Unknown'
