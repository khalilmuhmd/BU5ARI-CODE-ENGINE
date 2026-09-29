#!/data/data/com.termux/files/usr/bin/bash
set -e
pkg update -y
pkg install -y python
mkdir -p "$HOME/.bu5ari/projects"
echo "Installed BU5ARI CODE ENGINE."
echo "Run: python $HOME/bu5ari_code_engine/main.py"
