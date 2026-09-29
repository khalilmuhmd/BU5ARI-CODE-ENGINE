# BU5ARI CODE ENGINE

A lightweight Termux AI coding assistant inspired by the interface shown in the reference video.

## Install
```bash
pkg update -y
pkg install -y python
git clone <your-repository-url> ~/bu5ari_code_engine
cd ~/bu5ari_code_engine
python main.py
```

## Gemini API
Inside the program:
```text
/key YOUR_GEMINI_API_KEY
/model gemini-2.5-flash
```

The API key is stored locally in `~/.bu5ari/config.json`.

## Main commands
`/newproj`, `/files`, `/switch`, `/new`, `/paste`, `/edit`, `/fix`, `/undo`, `/run`, `/show`, `/open`, `/key`, `/model`, `/stats`, `/help`, `/quit`.

This is an original implementation inspired by the visible workflow, not a copy of the original video's source code.
