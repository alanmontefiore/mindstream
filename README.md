# MindStream

`cd workspace/mindstream/`

`source .venv/bin/activate`

`apt update && apt install -y nano && apt install -y lsof`

`git fetch --all`

`git reset --hard origin/$(git rev-parse --abbrev-ref HEAD)`

`python server/server.py`

## Installation

`pip install torch==2.1.0 torchvision==0.16.0 xformers --index-url https://download.pytorch.org/whl/cu121`

`pip install -r requirements.txt`

`python setup.py develop easy_install streamdiffusion[tensorrt]`

`python -m streamdiffusion.tools.install-tensorrt`
