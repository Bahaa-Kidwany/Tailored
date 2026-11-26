import sys, subprocess, os, importlib, time
sys.path.insert(0, os.path.dirname(__file__))
import ds

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def assemble(modules):
    ds._counter["n"] = 0
    pages = []
    for m in modules:
        mod = importlib.import_module(m)
        importlib.reload(mod)
        pages += mod.pages()
    html = f'<!doctype html><html><head><meta charset="utf-8"><title>Tailored - Brand Book</title><style>{ds.CSS}</style></head><body>{"".join(pages)}</body></html>'
    p = os.path.join(OUT, "build", "book.html")
    open(p, "w", encoding="utf8").write(html)
    return p, len(pages)


def to_pdf(html, pdf):
    subprocess.run([EDGE, "--headless", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=20000",
                    f"--print-to-pdf={pdf}", "file:///" + html.replace("\\", "/")], capture_output=True)


if __name__ == "__main__":
    mods = sys.argv[1].split(",") if len(sys.argv) > 1 else ["p_strategy", "p_identity", "p_type", "p_system", "p_ui", "p_apps"]
    pdfname = sys.argv[2] if len(sys.argv) > 2 else "Tailored_Brand_Book.pdf"
    t = time.time()
    html, n = assemble(mods)
    pdf = os.path.join(OUT, pdfname)
    to_pdf(html, pdf)
    print("pages", n, "pdf", os.path.getsize(pdf) // 1024, "KB", round(time.time() - t, 1), "s")

