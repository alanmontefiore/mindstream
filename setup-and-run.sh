#!/bin/bash

set -e  # Exit on error
set -o pipefail

cd ./StreamDiffusion
source .venv/bin/activate

cd ../mindstream/

apt update && apt install -y nano && apt install -y lsof

git fetch --all
git reset --hard origin/$(git rev-parse --abbrev-ref HEAD)

chmod +x setup-and-run.sh

cd ./demo/realtime-img2img

echo "🚀 Launching StreamDiffusion realtime img2img..."
python single.py
