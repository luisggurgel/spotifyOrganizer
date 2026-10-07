import os
from dotenv import load_dotenv

load_dotenv()

def get_credentials() -> tuple[str, str, str]:
    """
    Returns (client_id, client_secret, redirect_uri).
    If missing or containing placeholder values, runs an interactive setup wizard.
    """
    import sys
    load_dotenv(override=True)
    client_id = (os.getenv("SPOTIFY_CLIENT_ID") or os.getenv("SPOTIPY_CLIENT_ID") or "").strip()
    client_secret = (os.getenv("SPOTIFY_CLIENT_SECRET") or os.getenv("SPOTIPY_CLIENT_SECRET") or "").strip()
    redirect_uri = (os.getenv("SPOTIFY_REDIRECT_URI") or os.getenv("SPOTIPY_REDIRECT_URI") or "").strip()

    is_placeholder = (
        not client_id
        or not client_secret
        or "your_client_id" in client_id.lower()
        or "your_client_secret" in client_secret.lower()
        or "seu_client_id" in client_id.lower()
        or "seu_client_secret" in client_secret.lower()
    )

    if is_placeholder and sys.stdin and sys.stdin.isatty():
        from src.setup_wizard import run_setup_wizard
        client_id, client_secret, redirect_uri = run_setup_wizard()

    if not redirect_uri:
        redirect_uri = "http://127.0.0.1:8080/callback"

    return client_id, client_secret, redirect_uri

# For backwards compatibility with direct imports
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8080/callback")

# Valid scopes for reading library and modifying playlists
SPOTIFY_SCOPES = "user-library-read playlist-read-private playlist-modify-private playlist-modify-public"

# Prefix for our playlists to keep them organized
PLAYLIST_PREFIX = "Spotify — "
