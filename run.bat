@echo off
chcp 65001 >nul
title Organizador de Playlists do Spotify por Idioma

echo ============================================================
echo      Organizador de Playlists do Spotify por Idioma
echo ============================================================
echo.

:: 1. Verificar se Python esta instalado
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Python nao foi encontrado no seu computador!
    echo Por favor, instale o Python (versao 3.8 ou superior) em https://www.python.org/downloads/
    echo Lembre-se de marcar a opcao "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b 1
)

:: 2. Criar ambiente virtual se nao existir
if not exist ".venv" (
    echo [*] Criando ambiente virtual isolado (.venv)...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [ERRO] Falha ao criar o ambiente virtual.
        pause
        exit /b 1
    )
)

:: 3. Instalar/Verificar dependencias
echo [*] Verificando dependencias...
call .\.venv\Scripts\activate.bat
pip install -r requirements.txt --quiet --disable-pip-version-check
if %ERRORLEVEL% neq 0 (
    echo [AVISO] Houve um problema ao verificar pacotes, tentando iniciar mesmo assim...
)

echo.
echo [*] Iniciando aplicacao...
echo.

:: 4. Executar aplicacao
python main.py

echo.
echo Pressione qualquer tecla para fechar esta janela...
pause >nul
