#!/bin/bash

set -e  # Exit on error
set -o pipefail

apt update && apt install -y nano && apt install -y lsof

cd ./demo/realtime-img2img

echo "🚀 Launching StreamDiffusion realtime img2img..."
python main.py
