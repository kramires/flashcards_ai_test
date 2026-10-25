#!/bin/bash

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# uv fica em /opt/homebrew/bin, que nem sempre está no PATH ao abrir pelo Finder
export PATH="/opt/homebrew/bin:$HOME/.local/bin:$PATH"

if [ ! -f "$DIR/.env" ]; then
  echo "Crie o arquivo .env com a senha (veja .env.example)."; read -r; exit 1
fi

# Abre o painel do professor no navegador após 2s (dá tempo do servidor subir)
IP=$(python3 -c "import socket; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(('8.8.8.8',80)); print(s.getsockname()[0]); s.close()" 2>/dev/null || echo "localhost")
(sleep 2 && open "http://$IP:9527/admin") &

# caffeinate impede o Mac de dormir (e derrubar o servidor) durante a aula
caffeinate -i uv run app.py
