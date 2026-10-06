import os
from dotenv import load_dotenv

load_dotenv()

def get_credentials() -> tuple[str, str, str]:
    """
    Returns (client_id, client_secret, redirect_uri).
    If missing or containing placeholder values, runs an interactive setup wizard.
    """
    load_dotenv(override=True)
    client_id = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "").strip()

    is_placeholder = (
        not client_id
        or not client_secret
        or "your_client_id" in client_id.lower()
        or "your_client_secret" in client_secret.lower()
    )

    if is_placeholder:
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
