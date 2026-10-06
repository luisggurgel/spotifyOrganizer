import pytest
from unittest.mock import MagicMock
from src.spotify_client import SpotifyManager
from src.config import PLAYLIST_PREFIX

@pytest.fixture
def mock_spotipy():
    mock_sp = MagicMock()
    mock_sp.me.return_value = {'id': 'test_user'}
    return mock_sp

@pytest.fixture
def manager(mock_spotipy):
    return SpotifyManager(mock_spotipy)

def test_fetch_liked_songs_pagination(manager, mock_spotipy):
    # Mock pagination: 2 pages
    mock_spotipy.current_user_saved_tracks.return_value = {
        'items': [{'track': {'id': '1', 'name': 'T1'}}],
        'total': 2,
        'next': 'url'
    }
    mock_spotipy.next.return_value = {
        'items': [{'track': {'id': '2', 'name': 'T2'}}],
        'next': None
    }
    
    tracks = manager.fetch_all_liked_songs()
    assert len(tracks) == 2
    assert tracks[0]['id'] == '1'
    assert tracks[1]['id'] == '2'

def test_fetch_liked_songs_duplicates(manager, mock_spotipy):
    # Mock duplicate track
    mock_spotipy.current_user_saved_tracks.return_value = {
        'items': [
            {'track': {'id': '1', 'name': 'T1'}},
            {'track': {'id': '1', 'name': 'T1_dup'}}
        ],
        'total': 2,
        'next': None
    }
    
    tracks = manager.fetch_all_liked_songs()
    assert len(tracks) == 1
    assert tracks[0]['id'] == '1'

def test_load_existing_playlists(manager, mock_spotipy):
    mock_spotipy.current_user_playlists.return_value = {
        'items': [
            {'name': f'{PLAYLIST_PREFIX}Português', 'id': 'pl_1'},
            {'name': 'Minha Playlist Aleatoria', 'id': 'pl_2'}
        ],
        'next': None
    }
    
    manager.load_existing_playlists()
    assert len(manager.playlists_cache) == 1
    assert f'{PLAYLIST_PREFIX}Português' in manager.playlists_cache
    assert manager.playlists_cache[f'{PLAYLIST_PREFIX}Português'] == 'pl_1'

def test_get_playlist_id_existing(manager, mock_spotipy):
    manager.playlists_cache[f'{PLAYLIST_PREFIX}Inglês'] = 'pl_en'
    pl_id = manager.get_playlist_id('Inglês')
    assert pl_id == 'pl_en'
    mock_spotipy.current_user_playlist_create.assert_not_called()

def test_get_playlist_id_new(manager, mock_spotipy):
    mock_spotipy.current_user_playlist_create.return_value = {'id': 'new_pl_id'}
    pl_id = manager.get_playlist_id('Coreano')
    assert pl_id == 'new_pl_id'
    mock_spotipy.current_user_playlist_create.assert_called_once_with(
        name=f'{PLAYLIST_PREFIX}Coreano',
        public=False,
        description='Canções em Coreano organizadas automaticamente.'
    )

def test_add_tracks_idempotency(manager, mock_spotipy):
    # Existing tracks in playlist: '1', '2'
    manager.playlist_tracks_cache['pl_1'] = {'1', '2'}
    
    # We want to add '2', '3'
    # Only '3' should be added
    added = manager.add_tracks_to_playlist('pl_1', ['2', '3'])
    
    assert added == 1
    mock_spotipy.playlist_add_items.assert_called_once_with('pl_1', ['3'])
    assert '3' in manager.playlist_tracks_cache['pl_1']

def test_add_tracks_chunking(manager, mock_spotipy):
    manager.playlist_tracks_cache['pl_1'] = set()
    # 150 tracks
    tracks = [str(i) for i in range(150)]
    
    added = manager.add_tracks_to_playlist('pl_1', tracks)
    assert added == 150
    assert mock_spotipy.playlist_add_items.call_count == 2
