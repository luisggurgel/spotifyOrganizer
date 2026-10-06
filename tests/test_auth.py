import pytest
from unittest.mock import patch, MagicMock
from src.auth import get_spotify_client

def test_get_spotify_client(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "test_id")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "test_secret")
    monkeypatch.setenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8080/callback")

    with patch("spotipy.Spotify") as mock_spotify:
        client = get_spotify_client()
        assert client is not None
        mock_spotify.assert_called_once()
