#!/bin/bash

set -e  # Exit on error
set -o pipefail

apt update && apt install -y nano

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "🌐 Installing Node.js and npm..."
  curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
  apt install -y nodejs
else
  echo "✅ Node.js and npm already installed."
fi


echo "📁 Installing frontend dependencies and building UI..."
cd ./demo/realtime-img2img/frontend

if [ ! -d "public" ]; then
  echo "⚙️  Building frontend..."
  npm install
  npm run build
else
  echo "✅ Skipping build — 'public/' already exists."
fi

echo "🚀 Launching StreamDiffusion realtime img2img..."
python main.py
