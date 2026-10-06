#!/usr/bin/env bash

set -e

echo "============================================================"
echo "     Organizador de Playlists do Spotify por Idioma"
echo "============================================================"
echo ""

# 1. Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "[ERRO] Python 3 não foi encontrado no sistema!"
    echo "Instale o Python 3.8+ antes de continuar."
    exit 1
fi

# 2. Criar ambiente virtual se não existir
if [ ! -d ".venv" ]; then
    echo "[*] Criando ambiente virtual isolado (.venv)..."
    python3 -m venv .venv
fi

# 3. Instalar/Verificar dependências
echo "[*] Verificando dependências..."
source .venv/bin/activate
pip install -r requirements.txt --quiet --disable-pip-version-check

echo ""
echo "[*] Iniciando aplicação..."
echo ""

# 4. Executar aplicação
python main.py
