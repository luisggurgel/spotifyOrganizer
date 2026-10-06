from lingua import Language, LanguageDetectorBuilder

# Build the detector with the requested languages to reduce false positives
languages = [
    Language.PORTUGUESE,
    Language.ENGLISH,
    Language.SPANISH,
    Language.JAPANESE,
    Language.KOREAN,
    Language.FRENCH,
    Language.GERMAN,
    Language.ITALIAN,
    Language.RUSSIAN,
    Language.CHINESE
]
detector = LanguageDetectorBuilder.from_languages(*languages).build()

LANGUAGE_MAP = {
    Language.PORTUGUESE: 'Português',
    Language.ENGLISH: 'Inglês',
    Language.SPANISH: 'Espanhol',
    Language.JAPANESE: 'Japonês',
    Language.KOREAN: 'Coreano',
    Language.FRENCH: 'Francês',
    Language.GERMAN: 'Alemão',
    Language.ITALIAN: 'Italiano',
    Language.RUSSIAN: 'Russo',
    Language.CHINESE: 'Chinês'
}

def detect_language(track: dict) -> str:
    """
    Determines the language of a track based on its name, artists, and album.
    Returns the formatted language name (e.g., 'Português') or 'Instrumental/Unknown'.
    """
    track_name = track.get('name', '')
    album_name = track.get('album', {}).get('name', '')
    artists = [artist.get('name', '') for artist in track.get('artists', [])]
    
    # Clean up empty text
    if not track_name.strip():
        return "Instrumental/Unknown"

    try:
        # Try to detect with high confidence just from the track name
        confidence_values = detector.compute_language_confidence_values(track_name)
        
        if confidence_values and confidence_values[0].value > 0.6:
            return LANGUAGE_MAP.get(confidence_values[0].language, "Instrumental/Unknown")
            
        # If low confidence, provide more context (e.g. title + album + artist)
        combined_text = f"{track_name}. {album_name}. {' '.join(artists)}"
        confidence_values = detector.compute_language_confidence_values(combined_text)
        
        if confidence_values and confidence_values[0].value > 0.4:
            return LANGUAGE_MAP.get(confidence_values[0].language, "Instrumental/Unknown")
            
        return "Instrumental/Unknown"
        
    except Exception:
        return "Instrumental/Unknown"
