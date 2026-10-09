# Spotify Language Sorter (Organizador de Playlists por Idioma)

Organize todas as músicas curtidas da sua conta do Spotify automaticamente em playlists separadas por idioma (ex: *Spotify — Português*, *Spotify — Inglês*, *Spotify — Japonês*, etc.) com 1 clique!

---

## Recursos Principais

- **Classificação de Idioma em Cascata (Nova Arquitetura!):** Identifica idiomas com precisão extrema usando uma cascata de 5 etapas:
  1. **Detecção de Scripts Unicode:** CJK (Katakana, Hangul, Cirílico) → ~100% preciso para JP, KR, RU, CN.
  2. **Gêneros de Artistas (Spotify API):** Pré-busca de gêneros do artista (`sertanejo`, `k-pop`, `reggaeton`) → Mapeia mais de 300 palavras-chave para o idioma correto, eliminando erros com títulos latinos mistos.
  3. **High-Confidence Lingua:** Usa o `lingua-language-detector` no título com limite de 88% de confiança.
  4. **Fallback:** Usa o `lingua-language-detector` combinando título + álbum com 75% de confiança.
  5. **Categoria Desconhecidos/Instrumentais:** Músicas sem letras claras vão para *Spotify — Instrumental/Unknown*.
- **100% Idempotente e Seguro:** Não cria playlists repetidas nem adiciona faixas duplicadas. Pode rodar quantas vezes quiser.
- **Assistente Interativo para Iniciantes:** Se o arquivo `.env` não existir, o aplicativo guia a configuração no próprio terminal.
- **Executável com 1 Clique:** Arquivos `run.bat` (Windows) e `run.sh` (Linux/Mac) configuram o ambiente virtual e instalam tudo automaticamente.

---

## Início Rápido (Método Mais Fácil)

### 1. Criar credenciais no Spotify Developer (Leva 2 minutos)
1. Acesse o [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) e faça login.
2. Clique no botão **"Create app"**.
3. Preencha um nome qualquer (ex: `Organizador de Musicas`).
4. No campo **Redirect URIs**, adicione exatamente:
   ```text
   http://127.0.0.1:8080/callback
   ```
   *(Atenção: o Spotify não aceita `localhost`, use exatamente o IP `127.0.0.1`)*.
5. Marque os termos de uso e clique em **Save**.
6. Vá em **Settings** e copie o **Client ID** e o **Client Secret** (clique em *View client secret*).

---

### 2. Executar

#### No Windows:
Basta dar **duplo clique no arquivo `run.bat`** (ou abrir o terminal e rodar `.\run.bat`).

- O script detecta o Python, cria o ambiente virtual isolado, instala as dependências e inicia o programa.
- Se for a sua primeira vez, ele exibirá um assistente amigável pedindo para você colar o seu Client ID e Client Secret.
- O navegador abrirá automaticamente pedindo autorização para ler sua biblioteca e criar playlists na sua conta.

#### No Linux / macOS:
Abra o terminal na pasta e execute:
```bash
chmod +x run.sh
./run.sh
```

---

## Método Manual / Linha de Comando (Avançado)

Se preferir rodar manualmente pelo terminal:

1. **Configurar o `.env`:**
   Copie `.env.example` para `.env` e preencha:
   ```env
   SPOTIFY_CLIENT_ID=seu_client_id_aqui
   SPOTIFY_CLIENT_SECRET=seu_client_secret_aqui
   SPOTIFY_REDIRECT_URI=http://127.0.0.1:8080/callback
   ```

2. **Criar e ativar o ambiente virtual:**
   ```bash
   python -m venv .venv

   # No Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1

   # No Linux/Mac:
   source .venv/bin/activate
   ```

3. **Instalar dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Executar:**
   ```bash
   python main.py
   ```

---

## Executar Novamente no Futuro (Sincronização)

Sempre que você curtir novas músicas no Spotify e quiser adicioná-las às respectivas playlists:

1. Basta abrir o projeto e dar duplo clique em `run.bat` (ou rodar `python main.py`).
2. O aplicativo:
   - Utilizará o token salvo em cache (sem precisar logar no navegador novamente).
   - Identificará as playlists já criadas (*Spotify — Idioma*).
   - Analisará as músicas novas.
   - Adicionará **apenas** as músicas que ainda não estiverem nas playlists, evitando qualquer duplicação.

---

## Executando os Testes Automatizados

Para validar o funcionamento sem realizar chamadas reais à API:
```bash
pytest
```
Todos os testes usam mocks e cobrem paginação, detecção de idiomas, prevenção de duplicatas e criação de playlists.

---

## Segurança

- Suas credenciais e tokens são mantidos localmente nos arquivos `.env` e `.cache`.
- Esses arquivos já estão incluídos no `.gitignore` para nunca serem compartilhados acidentalmente.
- O aplicativo só realiza ações de **leitura da sua biblioteca** e **criação/adição às playlists próprias** (nunca apaga nem altera suas playlists existentes).

---

## ☁️ Hospedagem na Nuvem (AWS) e GitHub

Esta aplicação foi preparada nativamente para ser hospedada na **AWS** (ECS Fargate, AWS App Runner ou Elastic Beanstalk) e para ser enviada ao GitHub com segurança:

1. **Git / GitHub:** O projeto já está inicializado com `git init` e com o `.gitignore` devidamente configurado, impedindo vazamentos do `.env` ou tokens de cache. Para subir pro GitHub:
   ```bash
   git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
   git push -u origin master
   ```

2. **Web Server Nativo:** Como ambientes de nuvem não possuem "tela" para abrir o navegador e autorizar o login do Spotify, o projeto inclui o arquivo **`src/web.py`**, que é um Web App construído em **Flask**.

3. **Deploy via Docker na AWS:**
   O projeto já contém um **`Dockerfile`** configurado com `gunicorn`.
   - **No AWS App Runner ou ECS:** Basta conectar o repositório do GitHub ou enviar a imagem via AWS ECR (Elastic Container Registry).
   - O contêiner expõe automaticamente a porta `8080`.
   - Lembre-se de configurar as **Variáveis de Ambiente** (`SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `FLASK_SECRET_KEY` e `SPOTIFY_REDIRECT_URI`) no painel da AWS.
   - Configure no Dashboard do Spotify a nova *Redirect URI* gerada pela AWS (ex: `https://seu-app.awsapprunner.com/callback`).

**Para testar o modo Web (Nuvem) localmente:**
```bash
python -m src.web
```
Em seguida, acesse `http://localhost:8080` no seu navegador!
