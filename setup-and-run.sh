#!/bin/bash

set -e  # Exit on error
set -o pipefail

# echo "🔧 Installing PyTorch, torchvision, and xformers..."
# pip3 install torch==2.1.0 torchvision==0.16.0 xformers --index-url https://download.pytorch.org/whl/cu118

# echo "📦 Installing StreamDiffusion from GitHub..."
# pip install
# git+https://github.com/cumulo-autumn/StreamDiffusion.git@main#egg=streamdiffusion

pip install -e .
pip install "numpy<2"

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

echo "📜 Installing Python dependencies..."
cd ..
pip install -r requirements.txt


echo "🚀 Launching StreamDiffusion realtime img2img..."
python main.py
