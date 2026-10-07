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
app.secret_key = os.getenv("FLASK_SECRET_KEY", "spotify-sorter-secret-session-key-2026")
app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_auth_manager():
    client_id, client_secret, redirect_uri = get_credentials()
    if not client_id or not client_secret or "client_id" in client_id.lower() or "seu_client_id" in client_id.lower():
        return None
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
    if not auth_manager:
        return render_template_string("""
            <html><head><title>Spotify Language Sorter - Configuração</title></head>
            <body style="font-family: sans-serif; text-align: center; margin-top: 60px; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                    <h2 style="color: #e74c3c;">⚠️ Credenciais não configuradas</h2>
                    <p>O arquivo <code>.env</code> no servidor ainda não contém suas credenciais reais do Spotify.</p>
                    <p style="text-align: left; background: #f8f9fa; padding: 15px; border-radius: 5px; font-size: 14px;">
                        Abra o terminal na AWS e edite o arquivo <code>.env</code>:<br><br>
                        <code>nano .env</code><br><br>
                        Preencha com seu Client ID e Client Secret:<br>
                        <b>SPOTIFY_CLIENT_ID=</b>seu_client_id_real<br>
                        <b>SPOTIFY_CLIENT_SECRET=</b>seu_client_secret_real<br>
                        <b>SPOTIFY_REDIRECT_URI=</b>http://{{ host }}/callback
                    </p>
                    <p><a href="/" style="padding: 10px 20px; background-color: #1DB954; color: white; text-decoration: none; border-radius: 5px;">Recarregar Página</a></p>
                </div>
            </body></html>
        """, host=request.host)

    try:
        cached_token = auth_manager.cache_handler.get_cached_token()
        token_valid = auth_manager.validate_token(cached_token) if cached_token else False
    except Exception as e:
        logging.error(f"Erro ao verificar token: {e}")
        token_valid = False

    if not token_valid:
        try:
            auth_url = auth_manager.get_authorize_url()
        except Exception as e:
            return f"Erro ao gerar URL de autorização do Spotify: {e}", 500

        return render_template_string("""
            <html><head><title>Spotify Language Sorter</title></head>
            <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
                <div style="max-width: 500px; margin: 0 auto;">
                    <h1>Organizador de Playlists por Idioma</h1>
                    <p>Separe suas músicas curtidas por idioma automaticamente.</p>
                    <br>
                    <a href="{{ auth_url }}" style="padding: 14px 28px; background-color: #1DB954; color: white; text-decoration: none; font-size: 16px; font-weight: bold; border-radius: 25px; display: inline-block;">Conectar com Spotify</a>
                </div>
            </body></html>
        """, auth_url=auth_url)
    else:
        return render_template_string("""
            <html><head><title>Spotify Language Sorter</title></head>
            <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
                <h1>Você está conectado! 🎉</h1>
                <p>Clique abaixo para iniciar a organização das suas músicas.</p>
                <form action="/sync" method="post">
                    <button type="submit" style="padding: 12px 24px; background-color: #1DB954; color: white; border: none; border-radius: 25px; cursor: pointer; font-size: 16px; font-weight: bold;">Iniciar Organização em Segundo Plano</button>
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
