import os
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8080/callback"

def run_setup_wizard() -> tuple[str, str, str]:
    """
    Guides the user through an interactive setup to configure their Spotify credentials.
    Saves the values directly to the .env file.
    """
    print("\n" + "=" * 65)
    print(" CONFIGURAÇÃO INICIAL - ORGANIZADOR DO SPOTIFY ".center(65))
    print("=" * 65)
    print("\nOlá! Para que o aplicativo possa ler suas músicas curtidas e criar")
    print("as playlists no seu Spotify, precisamos conectar à API do Spotify.\n")
    print("Siga estes passos rápidos (leva menos de 2 minutos):")
    print("  1. Acesse: https://developer.spotify.com/dashboard")
    print("  2. Faça login e clique no botão 'Create app'.")
    print("  3. Preencha um nome qualquer (ex: 'Organizador de Idiomas').")
    print("  4. No campo 'Redirect URIs', adicione OBRIGATORIAMENTE:")
    print(f"     {DEFAULT_REDIRECT_URI}")
    print("  5. Salve, clique em 'Settings' e copie seu Client ID e Client Secret.\n")
    print("-" * 65)

    client_id = ""
    while not client_id:
        client_id = input("-> Cole o seu Client ID aqui: ").strip()
        if not client_id:
            print("   O Client ID não pode ser vazio. Tente novamente.")

    client_secret = ""
    while not client_secret:
        client_secret = input("-> Cole o seu Client Secret aqui: ").strip()
        if not client_secret:
            print("   O Client Secret não pode ser vazio. Tente novamente.")

    redirect_uri = DEFAULT_REDIRECT_URI

    # Salva no arquivo .env
    content = (
        "# Credenciais do aplicativo no Spotify Developer Dashboard\n"
        f"SPOTIFY_CLIENT_ID={client_id}\n"
        f"SPOTIFY_CLIENT_SECRET={client_secret}\n"
        f"SPOTIFY_REDIRECT_URI={redirect_uri}\n"
    )

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("-" * 65)
    print("Configuração salva com sucesso no arquivo .env!")
    print("=" * 65 + "\n")

    return client_id, client_secret, redirect_uri
