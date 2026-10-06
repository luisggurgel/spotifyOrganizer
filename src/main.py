import sys
from pathlib import Path
from collections import defaultdict
import logging

# Ensure project root is in sys.path when executed directly as `python src/main.py`
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.auth import get_spotify_client
from src.spotify_client import SpotifyManager
from src.language_classifier import detect_language
from src.ui import print_progress, print_summary

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='spotify_sorter.log')

def main():
    try:
        print("Iniciando autenticação no Spotify...")
        sp = get_spotify_client()
        manager = SpotifyManager(sp)
        print("Autenticação bem sucedida!")
    except Exception as e:
        print(f"\nErro de autenticação: {e}")
        print("Verifique seu arquivo .env e certifique-se de que as credenciais estão corretas.")
        sys.exit(1)

    print("\nCarregando playlists existentes...")
    try:
        manager.load_existing_playlists()
        print(f"Playlists carregadas. {len(manager.playlists_cache)} playlists do script encontradas.")
    except Exception as e:
        print(f"\nErro ao carregar playlists: {e}")
        sys.exit(1)

    print("\nBuscando músicas curtidas...")
    try:
        liked_songs = manager.fetch_all_liked_songs(
            progress_callback=lambda fetched, total: print(f"\rBuscando músicas... {fetched}/{total}", end="")
        )
        print(f"\nTotal de {len(liked_songs)} músicas únicas encontradas.")
    except Exception as e:
        print(f"\nErro ao buscar músicas: {e}")
        sys.exit(1)

    # Statistics
    total_analyzed = len(liked_songs)
    language_counts = defaultdict(int)
    added_counts = defaultdict(int)
    unclassified_count = 0
    errors = []

    # Mapping language to track ids
    lang_to_tracks = defaultdict(list)

    print("\nAnalisando idiomas...")
    for idx, track in enumerate(liked_songs, 1):
        try:
            track_name = track.get('name', 'Unknown')
            artists = ", ".join([a.get('name', '') for a in track.get('artists', [])])
            
            # Show progress
            sys.stdout.write("\033[K") # Clear to the end of line
            print(f"\r[{idx}/{total_analyzed}] Analisando: {artists} — {track_name}"[:100], end="")
            
            lang = detect_language(track)
            
            if lang == "Instrumental/Unknown":
                unclassified_count += 1
            
            language_counts[lang] += 1
            lang_to_tracks[lang].append(track['id'])
            
        except Exception as e:
            errors.append(f"Erro ao analisar '{track_name}': {e}")
            logging.error(f"Error analyzing track {track.get('id')}: {e}")

    print("\n\nAdicionando músicas às playlists...")
    
    total_langs = len(lang_to_tracks)
    for idx, (lang, track_ids) in enumerate(lang_to_tracks.items(), 1):
        try:
            print_progress(idx, total_langs, prefix='Atualizando Playlists:', suffix=f'({lang})', length=30)
            
            playlist_id = manager.get_playlist_id(lang)
            added = manager.add_tracks_to_playlist(playlist_id, track_ids)
            added_counts[lang] = added
            
        except Exception as e:
            errors.append(f"Erro ao atualizar playlist '{lang}': {e}")
            logging.error(f"Error updating playlist for {lang}: {e}")

    print_summary(total_analyzed, dict(language_counts), dict(added_counts), unclassified_count, errors)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Operação interrompida pelo usuário.")
        sys.exit(0)
