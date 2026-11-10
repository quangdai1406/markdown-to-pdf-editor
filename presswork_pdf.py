"""Presswork PDF - standalone Markdown -> PDF exporter (A3 / A4, portrait / landscape).

Based on Presswork.html (same typography). Renders with marked.js and prints to PDF
through Microsoft Edge (headless), which ships with Windows 10/11. No internet needed.
"""
import datetime
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import webview

APP = "Presswork PDF"
PAGE_MM = {"A4": (210, 297), "A3": (297, 420)}
ACCENTS = {  # name: (accent, code bg, line)
    "Ink blue": ("#23425e", "#f1efe6", "#ddd6c4"),
    "Umber": ("#5c4a2e", "#f2ede2", "#ddd3bd"),
    "Forest": ("#3f5b42", "#eef2ea", "#d5ddce"),
    "Plum": ("#5b3a52", "#f2eaf0", "#ddd0da"),
    "Ink black": ("#201c16", "#f1efe6", "#ddd6c4"),
}
EDGE_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def resource(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def find_browser():
    for p in EDGE_PATHS:
        if os.path.exists(p):
            return p
    return None


def build_html(md_text, title, base_dir, size, orient, accent, margin_mm):
    w, h = PAGE_MM[size]
    if orient == "Landscape":
        w, h = h, w
    a, code_bg, line = ACCENTS[accent]
    with open(resource("marked.umd.js"), encoding="utf-8") as f:
        marked_js = f.read().replace("</script", "<\\/script")
    base = "file:///" + base_dir.replace("\\", "/").rstrip("/") + "/"
    md_json = json.dumps(md_text).replace("</", "<\\/")
    css = f"""
@page {{ size: {w}mm {h}mm; margin: {margin_mm}mm; }}
:root {{ --accent:{a}; --code-bg:{code_bg}; --line:{line}; }}
* {{ box-sizing: border-box; }}
html, body {{ margin:0; padding:0; background:#fff; }}
main {{ font-family:"Source Serif 4", Georgia, "Times New Roman", serif; font-size:11pt;
  line-height:1.65; color:#232016; }}
h1,h2,h3,h4,h5,h6 {{ font-family:"Fraunces","Iowan Old Style","Palatino Linotype",Palatino,serif;
  font-weight:600; color:var(--accent); line-height:1.25; text-wrap:balance;
  break-after:avoid; break-inside:avoid; }}
h1 {{ font-size:22pt; margin:0 0 .15em; padding-bottom:.3em; border-bottom:2px solid var(--accent); }}
h2 {{ font-size:15pt; margin:1.7em 0 .55em; }}
h3 {{ font-size:12.5pt; margin:1.5em 0 .45em; }}
h4,h5,h6 {{ font-size:11pt; margin:1.3em 0 .4em; }}
p {{ margin:.9em 0; }}
a {{ color:var(--accent); text-underline-offset:2px; }}
ul,ol {{ margin:.9em 0; padding-left:1.4em; }}
li {{ margin:.35em 0; }}
li::marker {{ color:var(--accent); }}
blockquote {{ margin:1.2em 0; padding:.2em 0 .2em 1.1em; border-left:3px solid var(--accent);
  color:#58513f; font-style:italic; }}
code {{ font-family:"JetBrains Mono",Consolas,monospace; font-size:.85em; background:var(--code-bg);
  padding:.15em .4em; border-radius:3px; }}
pre {{ background:var(--code-bg); border:1px solid var(--line); border-radius:4px; padding:14px 16px;
  margin:1.1em 0; white-space:pre-wrap; word-wrap:break-word; }}
pre code {{ background:none; padding:0; font-size:.82em; line-height:1.55; }}
hr {{ border:none; border-top:1px solid var(--line); margin:2.2em 0; }}
img {{ max-width:100%; border-radius:3px; break-inside:avoid; }}
table {{ width:100%; max-width:100%; border-collapse:collapse; margin:1.2em 0; font-size:.92em; }}
th,td {{ border:1px solid var(--line); padding:7px 10px; text-align:left; vertical-align:top;
  overflow-wrap:anywhere; word-break:break-word; }}
th {{ background:var(--code-bg); font-family:"Public Sans","Segoe UI",Arial,sans-serif; font-weight:600;
  font-size:.85em; text-transform:uppercase; letter-spacing:.03em; }}
thead {{ display:table-header-group; }}
tr {{ break-inside:avoid; }}
* {{ -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
"""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<base href="{html.escape(base)}">
<title>{html.escape(title)}</title>
<style>{css}</style>
<script>{marked_js}</script>
</head><body><main id="out"></main>
<script>
document.getElementById('out').innerHTML = marked.parse({md_json});
</script></body></html>"""


def render_pdf(browser, html_path, pdf_path, timeout=120):
    html_path, pdf_path = os.path.abspath(html_path), os.path.abspath(pdf_path)
    profile = tempfile.mkdtemp(prefix="presswork_edge_")
    cmd = [
        browser, "--headless=new", "--disable-gpu", "--no-first-run",
        f"--user-data-dir={profile}", "--no-pdf-header-footer",
        "--virtual-time-budget=8000",
        f"--print-to-pdf={pdf_path}",
        "file:///" + html_path.replace("\\", "/"),
    ]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.run(cmd, capture_output=True, timeout=timeout, creationflags=flags)
    ok = os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0
    try:
        import shutil
        shutil.rmtree(profile, ignore_errors=True)
    except Exception:
        pass
    return ok


PROGID = "PressworkPDF.Markdown"


def _exe_command():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" "%1"'
    return f'"{sys.executable}" "{os.path.abspath(__file__)}" "%1"'


def register_md():
    """Per-user (HKCU) file association for .md / .markdown. No admin needed."""
    import ctypes
    import winreg
    cls = "Software\\Classes\\"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cls + PROGID) as k:
        winreg.SetValue(k, "", winreg.REG_SZ, "Markdown document (Presswork PDF)")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cls + PROGID + "\\shell\\open\\command") as k:
        winreg.SetValue(k, "", winreg.REG_SZ, _exe_command())
    for ext in (".md", ".markdown"):
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cls + ext + "\\OpenWithProgids") as k:
            winreg.SetValueEx(k, PROGID, 0, winreg.REG_NONE, b"")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cls + ext) as k:
            winreg.SetValue(k, "", winreg.REG_SZ, PROGID)
    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)


def user_choice_blocks():
    """True if Windows already has another app chosen for .md (it overrides ours)."""
    import winreg
    key = r"Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.md\UserChoice"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as k:
            return winreg.QueryValueEx(k, "ProgId")[0] != PROGID
    except OSError:
        return False


class Api:
    def __init__(self, initial):
        self._initial = initial
        self._window = None
        self._browser = find_browser()

    def _read(self, path):
        path = os.path.abspath(path)
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            text = f.read()
        d = "file:///" + os.path.dirname(path).replace("\\", "/").rstrip("/") + "/"
        return {"ok": True, "path": path, "text": text, "dir": d}

    def initial_file(self):
        for p in self._initial:
            if os.path.isfile(p):
                return self._read(p)
        return None

    def read_file(self, path):
        try:
            return self._read(path)
        except Exception as e:
            return {"ok": False, "error": f"Could not read file: {e}"}

    def pick_file(self):
        kind = getattr(getattr(webview, "FileDialog", None), "OPEN", None) or webview.OPEN_DIALOG
        r = self._window.create_file_dialog(
            kind, allow_multiple=False,
            file_types=("Markdown (*.md;*.markdown;*.txt)", "All files (*.*)"))
        if not r:
            return {"ok": False}
        return self.read_file(r[0])

    def export_pdf(self, path, o, all_four):
        if not self._browser:
            return {"ok": False, "error": "Microsoft Edge (or Chrome) was not found."}
        try:
            with open(path, encoding="utf-8-sig", errors="replace") as f:
                text = f.read()
            name = os.path.splitext(os.path.basename(path))[0]
            safe = re.sub(r'[<>:"/\|?*]', "_", name)
            stamp = datetime.date.today().strftime("%y_%m%d")
            m = re.search(r"^#\s+(.+)$", text, re.M)
            title = m.group(1).strip() if m else name
            folder = os.path.dirname(path)
            if all_four:
                jobs = [(s, r, os.path.join(folder, f"{stamp}_{safe}_{s}_{r.lower()}.pdf"))
                        for s in PAGE_MM for r in ("Portrait", "Landscape")]
            else:
                default = f"{stamp}_{safe}_{o['size']}_{o['orient'].lower()}.pdf"
                kind = getattr(getattr(webview, "FileDialog", None), "SAVE", None) or webview.SAVE_DIALOG
                r = self._window.create_file_dialog(kind, directory=folder, save_filename=default,
                                                   file_types=("PDF (*.pdf)",))
                if not r:
                    return {"ok": False, "error": "Export cancelled."}
                out = r if isinstance(r, str) else r[0]
                if not out.lower().endswith(".pdf"):
                    out += ".pdf"
                jobs = [(o["size"], o["orient"], out)]
            files = []
            for s, ori, out in jobs:
                page = build_html(text, title, folder, s, ori, o["accent"], int(o["margin"]))
                fd, tmp = tempfile.mkstemp(suffix=".html", prefix="presswork_")
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(page)
                try:
                    if os.path.exists(out):
                        os.remove(out)
                    if render_pdf(self._browser, tmp, out):
                        files.append(out)
                finally:
                    os.remove(tmp)
            if not files:
                return {"ok": False, "error": "The PDF could not be created."}
            return {"ok": True, "files": files}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def show_in_folder(self, path):
        subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])

    def associate(self):
        try:
            register_md()
        except Exception as e:
            return {"ok": False, "msg": f"Could not register: {e}"}
        if user_choice_blocks():
            return {"ok": False, "msg": "Registered, but Windows still has another app chosen for .md. "
                    "Right-click a .md file > Open with > Choose another app > Presswork PDF > tick Always."}
        return {"ok": True, "msg": "Done. Double-clicking a .md file now opens it here."}


def main():
    initial = [os.path.abspath(a) for a in sys.argv[1:] if not a.startswith("--")]
    api = Api(initial)
    api._window = webview.create_window(APP, resource("ui.html"), js_api=api, width=1280, height=860,
                                       min_size=(900, 600))
    webview.start()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        b = find_browser()
        src, out = sys.argv[2], sys.argv[3]
        os.makedirs(out, exist_ok=True)
        t = open(src, encoding="utf-8").read()
        for s in PAGE_MM:
            for o in ("Portrait", "Landscape"):
                hp = os.path.join(out, "t.html")
                open(hp, "w", encoding="utf-8").write(
                    build_html(t, "t", os.path.dirname(os.path.abspath(src)), s, o, "Ink blue", 18))
                print(s, o, render_pdf(b, hp, os.path.join(out, f"{s}_{o}.pdf")))
        sys.exit(0)
    main()
