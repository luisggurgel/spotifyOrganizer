import os
from flask import Flask, request, redirect, session, render_template_string
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from src.config import get_credentials, SPOTIFY_SCOPES
from src.spotify_client import SpotifyManager
from src.language_classifier import detect_language
from collections import defaultdict
import threading
import logging

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))
app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_auth_manager():
    client_id, client_secret, redirect_uri = get_credentials()
    # No cloud, o open_browser é False. O Flask lidará com a rota
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SPOTIFY_SCOPES,
        open_browser=False,
        cache_handler=spotipy.cache_handler.FlaskSessionCacheHandler(session)
    )

@app.route('/')
def index():
    auth_manager = get_auth_manager()
    if not auth_manager.validate_token(auth_manager.cache_handler.get_cached_token()):
        auth_url = auth_manager.get_authorize_url()
        return render_template_string("""
            <html><head><title>Spotify Language Sorter</title></head>
            <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
                <h1>Organizador de Playlists por Idioma</h1>
                <p>Para começar, faça login com o seu Spotify.</p>
                <a href="{{ auth_url }}" style="padding: 10px 20px; background-color: #1DB954; color: white; text-decoration: none; border-radius: 5px;">Login com Spotify</a>
            </body></html>
        """, auth_url=auth_url)
    else:
        return render_template_string("""
            <html><head><title>Spotify Language Sorter</title></head>
            <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
                <h1>Você está logado!</h1>
                <form action="/sync" method="post">
                    <button type="submit" style="padding: 10px 20px; background-color: #1DB954; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">Iniciar Sincronização em Background</button>
                </form>
            </body></html>
        """)

@app.route('/callback')
def callback():
    auth_manager = get_auth_manager()
    if request.args.get("code"):
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')
    return "Erro ao realizar login."

@app.route('/sync', methods=['POST'])
def sync():
    auth_manager = get_auth_manager()
    token_info = auth_manager.validate_token(auth_manager.cache_handler.get_cached_token())
    if not token_info:
        return redirect('/')
        
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    # Rodar em background para não travar a requisição (pode demorar minutos)
    thread = threading.Thread(target=run_sync, args=(sp,))
    thread.start()
    
    return render_template_string("""
        <html><head><title>Sincronizando</title></head>
        <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
            <h1>Sincronização iniciada!</h1>
            <p>A organização está acontecendo no servidor em background.</p>
            <p>Você pode fechar esta página e conferir seu Spotify em alguns minutos.</p>
            <a href="/">Voltar</a>
        </body></html>
    """)

def run_sync(sp):
    manager = SpotifyManager(sp)
    logging.info("Carregando playlists existentes...")
    manager.load_existing_playlists()
    
    logging.info("Buscando músicas curtidas...")
    liked_songs = manager.fetch_all_liked_songs()
    
    lang_to_tracks = defaultdict(list)
    for track in liked_songs:
        lang = detect_language(track)
        lang_to_tracks[lang].append(track['id'])
        
    for lang, track_ids in lang_to_tracks.items():
        try:
            playlist_id = manager.get_playlist_id(lang)
            manager.add_tracks_to_playlist(playlist_id, track_ids)
            logging.info(f"Adicionadas músicas em {lang}")
        except Exception as e:
            logging.error(f"Erro na playlist {lang}: {e}")

    logging.info("Sincronização concluída!")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
