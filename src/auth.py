import spotipy
from spotipy.oauth2 import SpotifyOAuth
from src.config import get_credentials, SPOTIFY_SCOPES

def get_spotify_client() -> spotipy.Spotify:
    """
    Initializes and returns a Spotify client authenticated via OAuth 2.0.
    Will trigger a browser window to authenticate the first time, then caches the token.
    """
    client_id, client_secret, redirect_uri = get_credentials()

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SPOTIFY_SCOPES,
        open_browser=True
    )

    return spotipy.Spotify(auth_manager=auth_manager)
