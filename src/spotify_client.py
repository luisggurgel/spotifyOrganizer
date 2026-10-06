import spotipy
from typing import List, Dict, Set, Optional
from src.config import PLAYLIST_PREFIX

class SpotifyManager:
    def __init__(self, sp: spotipy.Spotify):
        self.sp = sp
        self.user_id = self.sp.me()['id']
        
        # Cache for playlists: name -> playlist_id
        self.playlists_cache: Dict[str, str] = {}
        
        # Cache for tracks inside playlists: playlist_id -> set of track_ids
        self.playlist_tracks_cache: Dict[str, Set[str]] = {}
        
    def fetch_all_liked_songs(self, progress_callback=None) -> List[dict]:
        """
        Fetches all liked songs using pagination.
        Handles duplicates by tracking seen IDs.
        """
        results = self.sp.current_user_saved_tracks(limit=50)
        tracks = []
        seen_ids = set()
        
        total = results['total']
        fetched = 0
        
        while results:
            for item in results['items']:
                track = item['track']
                track_id = track.get('id')
                if track_id and track_id not in seen_ids:
                    seen_ids.add(track_id)
                    tracks.append(track)
                    
            fetched += len(results['items'])
            if progress_callback:
                progress_callback(fetched, total)
                
            if results['next']:
                results = self.sp.next(results)
            else:
                break
                
        return tracks
        
    def load_existing_playlists(self):
        """
        Loads all existing playlists to avoid creating duplicates.
        Only caches playlists created by this script (starting with PLAYLIST_PREFIX).
        """
        results = self.sp.current_user_playlists(limit=50)
        
        while results:
            for pl in results['items']:
                name = pl['name']
                if name.startswith(PLAYLIST_PREFIX):
                    self.playlists_cache[name] = pl['id']
                    
            if results['next']:
                results = self.sp.next(results)
            else:
                break

    def get_playlist_id(self, language: str) -> str:
        """
        Gets the ID of the playlist for a specific language.
        Creates it if it doesn't exist.
        """
        name = f"{PLAYLIST_PREFIX}{language}"
        
        if name in self.playlists_cache:
            return self.playlists_cache[name]
            
        # Create playlist using the current non-deprecated endpoint
        playlist = self.sp.current_user_playlist_create(
            name=name,
            public=False,
            description=f"Canções em {language} organizadas automaticamente."
        )
        
        playlist_id = playlist['id']
        self.playlists_cache[name] = playlist_id
        return playlist_id

    def load_playlist_tracks(self, playlist_id: str) -> Set[str]:
        """
        Loads all track IDs currently in a playlist to ensure idempotency.
        Caches the result.
        """
        if playlist_id in self.playlist_tracks_cache:
            return self.playlist_tracks_cache[playlist_id]
            
        track_ids = set()
        results = self.sp.playlist_items(playlist_id, limit=100, additional_types=['track'])
        
        while results:
            for item in results['items']:
                track = item.get('track')
                if track and track.get('id'):
                    track_ids.add(track['id'])
                    
            if results['next']:
                results = self.sp.next(results)
            else:
                break
                
        self.playlist_tracks_cache[playlist_id] = track_ids
        return track_ids

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]):
        """
        Adds tracks to a playlist, filtering out those that are already there.
        Handles chunking to respect API limits (100 tracks max per request).
        """
        existing_track_ids = self.load_playlist_tracks(playlist_id)
        
        # Filter duplicates
        new_track_ids = [tid for tid in track_ids if tid not in existing_track_ids]
        
        if not new_track_ids:
            return 0
            
        # Chunk into groups of 100
        chunk_size = 100
        for i in range(0, len(new_track_ids), chunk_size):
            chunk = new_track_ids[i:i+chunk_size]
            self.sp.playlist_add_items(playlist_id, chunk)
            
            # Update cache
            for tid in chunk:
                self.playlist_tracks_cache[playlist_id].add(tid)
                
        return len(new_track_ids)
