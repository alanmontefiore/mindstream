#!/bin/bash

set -e  # Exit on error
set -o pipefail

apt update && apt install -y nano && apt install -y lsof

git fetch --all
git reset --hard origin/$(git rev-parse --abbrev-ref HEAD)

PORT=7860
PID=$(lsof -ti :$PORT)

if [ -n "$PID" ]; then
  echo "🔪 Killing process on port $PORT (PID: $PID)..."
  kill -9 $PID
  echo "✅ Done."
else
  echo "✅ No process running on port $PORT."
fi

cd ./demo/realtime-img2img

echo "🚀 Launching StreamDiffusion realtime img2img..."
python main.py
