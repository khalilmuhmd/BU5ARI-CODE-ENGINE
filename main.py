#!/usr/bin/env python3
import os, sys, json, subprocess, shlex, shutil, re
from pathlib import Path
from datetime import datetime

APP = "BU5ARI CODE ENGINE"
BASE = Path.home() / ".bu5ari"
PROJECTS = BASE / "projects"
CONFIG = BASE / "config.json"
BASE.mkdir(parents=True, exist_ok=True)
PROJECTS.mkdir(parents=True, exist_ok=True)

def load_config():
    if CONFIG.exists():
        try: return json.loads(CONFIG.read_text())
        except Exception: pass
    return {}

def save_config(c):
    CONFIG.write_text(json.dumps(c, indent=2))

def banner():
    print("\033[91m" + r"""
 ██████╗ ██╗   ██╗███████╗ █████╗ ██████╗ ██╗
 ██╔══██╗██║   ██║╚══███╔╝██╔══██╗██╔══██╗██║
 ██████╔╝██║   ██║  ███╔╝ ███████║██████╔╝██║
 ██╔══██╗██║   ██║ ███╔╝  ██╔══██║██╔══██╗██║
 ██████╔╝╚██████╔╝███████╗██║  ██║██║  ██║██║
 ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝
""" + "\033[0m")
    print("\033[90m[ AI CODE ENGINE V1 ]   Gemini-compatible backend\033[0m\n")

def current_file(project):
    f = project / ".current"
    return Path(f.read_text().strip()) if f.exists() else None

def set_current(project, p):
    (project / ".current").write_text(str(p))

def choose_project():
    items = [p for p in PROJECTS.iterdir() if p.is_dir()]
    if not items:
        print("No projects. Use /newproj <name>"); return None
    for i,p in enumerate(items,1): print(f"{i}. {p.name}")
    try: return items[int(input("Select: "))-1]
    except Exception: return None

def ai_request(prompt, cfg):
    # Uses Gemini REST API without extra Python packages.
    import urllib.request
    key = cfg.get("api_key")
    model = cfg.get("model", "gemini-2.5-flash")
    if not key:
        return None, "No API key. Use /key YOUR_GEMINI_API_KEY"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {"contents":[{"parts":[{"text":prompt}]}]}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data=json.loads(r.read())
        return data["candidates"][0]["content"]["parts"][0]["text"], None
    except Exception as e:
        return None, f"Gemini request failed: {e}"

def extract_code(text):
    blocks = re.findall(r"```(?:python|py|javascript|js|typescript|ts|bash|sh|json|html|css)?\s*\n?(.*?)```", text, re.S|re.I)
    return blocks[0].strip() if blocks else text.strip()

def cmd_newproj(args, state):
    if not args: print("Usage: /newproj <name>"); return
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", args[0])
    p = PROJECTS / name
    p.mkdir(exist_ok=True)
    state["project"] = p
    print(f"Project created: {p}")

def cmd_files(state):
    p=state.get("project")
    if not p: print("Select/create a project first."); return
    for x in sorted(p.rglob("*")):
        if x.is_file() and x.name not in {".current"}:
            print("  " + str(x.relative_to(p)))

def cmd_new(args,state):
    p=state.get("project")
    if not p: print("Use /newproj first."); return
    if not args: print("Usage: /new <filename>"); return
    f=p / args[0]
    f.parent.mkdir(parents=True, exist_ok=True)
    f.touch(exist_ok=True); set_current(p,f)
    print(f"Current file: {f.relative_to(p)}")

def cmd_show(state):
    p=state.get("project"); f=current_file(p) if p else None
    if not f: print("No current file."); return
    path=f if f.is_absolute() else p/f
    if path.exists(): print(path.read_text(errors="replace"))
    else: print("File not found.")

def cmd_run(state):
    p=state.get("project"); f=current_file(p) if p else None
    if not f: print("No current file."); return
    path=f if f.is_absolute() else p/f
    if not path.exists(): print("File not found."); return
    ext=path.suffix.lower()
    if ext==".py": cmd=[sys.executable,str(path)]
    elif ext in {".js",".mjs"} and shutil.which("node"): cmd=["node",str(path)]
    elif ext==".sh": cmd=["bash",str(path)]
    else:
        print("Supported runners: Python, Node.js, Bash."); return
    print("$ " + " ".join(map(shlex.quote,cmd)))
    try:
        r=subprocess.run(cmd,cwd=p,text=True,capture_output=True,timeout=60)
        print(r.stdout, end="")
        if r.stderr: print(r.stderr, end="", file=sys.stderr)
        print(f"\n[exit {r.returncode}]")
    except Exception as e: print("Run failed:",e)

def cmd_edit(state,cfg):
    p=state.get("project")
    if not p: print("Use /newproj first."); return
    request=input("Describe the change: ").strip()
    if not request: return
    f=current_file(p)
    context=""
    if f:
        path=f if f.is_absolute() else p/f
        if path.exists(): context=path.read_text(errors="replace")
    prompt=f"""You are a coding assistant. Project: {p.name}.
Current file: {f}
User request: {request}
Current code:
```text
{context}
```
Return ONLY the complete replacement code for the current file, inside one code block.
Do not explain."""
    out,err=ai_request(prompt,cfg)
    if err: print(err); return
    code=extract_code(out)
    if not f:
        f=p/"main.py"; set_current(p,f)
    path=f if f.is_absolute() else p/f
    backup=path.with_suffix(path.suffix+".bak")
    if path.exists(): shutil.copy2(path,backup)
    path.write_text(code)
    print(f"Updated {path.relative_to(p)}")

def cmd_fix(state,cfg):
    p=state.get("project")
    f=current_file(p) if p else None
    if not f: print("No current file."); return
    path=f if f.is_absolute() else p/f
    try:
        if path.suffix==".py":
            r=subprocess.run([sys.executable,"-m","py_compile",str(path)],cwd=p,text=True,capture_output=True)
        else:
            print("Automatic check currently supports Python."); return
        if r.returncode==0:
            print("No Python syntax errors found."); return
        print(r.stderr)
        prompt=f"""Fix this Python file. Return ONLY complete corrected code.
Error:
{r.stderr}
Code:
```python
{path.read_text(errors="replace")}
```"""
        out,err=ai_request(prompt,cfg)
        if err: print(err); return
        shutil.copy2(path,path.with_suffix(path.suffix+".bak"))
        path.write_text(extract_code(out))
        print("AI fix applied. Run /fix again to verify.")
    except Exception as e: print("Fix failed:",e)

def help_text():
    print("""\033[91mWRITE\033[0m
/new <file>       create/select a file
/paste             paste code interactively
PROJECT
/newproj <name>    create project
/files             list project files
/switch            switch project
EDIT
/edit              ask AI to modify current file
/fix               check Python and ask AI to repair errors
/undo              restore current file from .bak
RUN
/run               run current file
/show              display current file
/open <file>       open/select saved file
SYSTEM
/key <API_KEY>    save Gemini API key
/model <name>      change Gemini model
/stats              show local stats
/help               show help
/quit               exit""")

def main():
    cfg=load_config(); state={"project":None}; banner(); help_text()
    while True:
        try: raw=input("\n\033[92mbu5ari\033[0m ❯ ").strip()
        except (EOFError,KeyboardInterrupt): print(); break
        if not raw: continue
        if not raw.startswith("/"):
            print("Use a command such as /newproj, /edit or /help."); continue
        parts=shlex.split(raw); c=parts[0].lower(); args=parts[1:]
        if c=="/help": help_text()
        elif c=="/newproj": cmd_newproj(args,state)
        elif c=="/files": cmd_files(state)
        elif c=="/switch": state["project"]=choose_project()
        elif c=="/new": cmd_new(args,state)
        elif c=="/show": cmd_show(state)
        elif c=="/run": cmd_run(state)
        elif c=="/edit": cmd_edit(state,cfg)
        elif c=="/fix": cmd_fix(state,cfg)
        elif c=="/open":
            p=state.get("project")
            if p and args:
                f=p/args[0]
                if f.exists(): set_current(p,f); print("Current:",args[0])
                else: print("File not found.")
        elif c=="/paste":
            p=state.get("project")
            if not p: print("Use /newproj first."); continue
            name=input("Filename [main.py]: ").strip() or "main.py"
            print("Paste code; finish with a line containing only END")
            lines=[]
            while True:
                line=input()
                if line=="END": break
                lines.append(line)
            f=p/name; f.parent.mkdir(parents=True,exist_ok=True); f.write_text("\n".join(lines)+"\n"); set_current(p,f)
            print("Saved.")
        elif c=="/undo":
            p=state.get("project"); f=current_file(p) if p else None
            if f:
                path=f if f.is_absolute() else p/f; b=path.with_suffix(path.suffix+".bak")
                if b.exists(): shutil.copy2(b,path); print("Restored backup.")
                else: print("No backup.")
        elif c=="/key":
            if args: cfg["api_key"]=args[0]; save_config(cfg); print("API key saved.")
            else: print("Usage: /key YOUR_GEMINI_API_KEY")
        elif c=="/model":
            if args: cfg["model"]=args[0]; save_config(cfg); print("Model:",cfg["model"])
            else: print("Model:",cfg.get("model","gemini-2.5-flash"))
        elif c=="/stats":
            print("Projects:",len([x for x in PROJECTS.iterdir() if x.is_dir()]))
            print("Model:",cfg.get("model","gemini-2.5-flash"))
        elif c=="/quit": break
        else: print("Unknown command. Use /help.")

if __name__=="__main__": main()
