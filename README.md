# MindStream

`cd workspace`

`source .venv/bin/activate`

`git clone https://github.com/alanmontefiore/mindstream.git`

`cd mindstream`

`apt update && apt install -y nano && apt install -y lsof`

`git fetch --all`

`git reset --hard origin/$(git rev-parse --abbrev-ref HEAD)`

`chmod +x setup-and-run.sh`

`./setup-and-run.sh`

### Port running

`lsof -i :7860`

`kill -9 <PID>`
