#!/bin/bash

set -e  # Exit on error
set -o pipefail

echo "🔧 Installing PyTorch, torchvision, and xformers..."
pip3 install torch==2.1.0 torchvision==0.16.0 xformers --index-url https://download.pytorch.org/whl/cu118

echo "📦 Installing StreamDiffusion from GitHub..."
pip install git+https://github.com/cumulo-autumn/StreamDiffusion.git@main#egg=streamdiffusion

echo "🌐 Installing Node.js and npm..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

echo "📁 Installing frontend dependencies and building UI..."
cd ./demo/realtime-img2img/frontend
npm install
npm run build

echo "📜 Installing Python dependencies..."
cd ..
pip install -r requirements.txt

echo "🚀 Launching StreamDiffusion realtime img2img..."
python main.py
