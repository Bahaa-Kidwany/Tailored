"""Tailored Brand Book — master build script.
Usage: python build.py module1,module2,... output.pdf
"""
import sys, os, importlib, subprocess, time, tempfile, pathlib

BUILD_DIR = pathlib.Path(__file__).parent
BRAND_DIR = BUILD_DIR.parent
FONTS_DIR = BRAND_DIR / "fonts"

HTML_HEAD = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
{css}
</style>
</head><body>
"""
HTML_TAIL = "</body></html>"


def assemble(module_names):
    import ds
    ds._counter["n"] = 0
    mods = []
    for name in module_names:
        name = name.strip()
        if not name:
            continue
        spec = importlib.util.spec_from_file_location(name, BUILD_DIR / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mods.append(mod)

    pages = []
    for mod in mods:
        pages.extend(mod.pages())

    return ds.CSS, pages


def build(module_names, out_path):
    t0 = time.time()
    css, pages = assemble(module_names)
    html = HTML_HEAD.format(css=css) + "\n".join(pages) + HTML_TAIL

    html_file = BUILD_DIR / "book.html"
    html_file.write_text(html, encoding="utf-8")

    out = pathlib.Path(out_path)
    if not out.is_absolute():
        out = BRAND_DIR / out

    # Edge headless PDF
    edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge):
        edge = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

    result = subprocess.run([
        edge,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        f"--print-to-pdf={out}",
        "--print-to-pdf-no-header",
        f"file:///{html_file.as_posix()}",
    ], capture_output=True, text=True)

    size_kb = out.stat().st_size // 1024 if out.exists() else 0
    elapsed = time.time() - t0
    print(f"pages {len(pages)}  pdf {size_kb} KB  {elapsed:.1f} s")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python build.py module1,module2 output.pdf")
        sys.exit(1)
    mods = sys.argv[1].split(",")
    out = sys.argv[2]
    sys.path.insert(0, str(BUILD_DIR))
    build(mods, out)
