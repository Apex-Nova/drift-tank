"""Gives the web page (made by pygbag) the game's look while it loads:
dark navy background instead of grey/pale-blue, an amber "DRIFT TANK - loading" box instead
of the green one, and no text selection / long-press menus on phones and tablets.

    python tools/brand_web_page.py build/web/drift-tank/build/web/index.html
"""
import sys

STYLE = """<style>
  /* Drift Tank look (tools/brand_web_page.py) */
  html, body { background-color: #14182c !important; }
  body { -webkit-user-select: none; user-select: none; -webkit-touch-callout: none; }
  #infobox {
    background: #14182c !important; color: #ffb234 !important;
    font: 700 22px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif !important;
    letter-spacing: .12em; text-align: center; padding: 18px 30px !important;
    border: 2px solid #ffb234; border-radius: 14px; box-shadow: 0 0 40px rgba(255, 178, 52, .25);
    left: 50% !important; top: 50% !important; transform: translate(-50%, -50%);   /* always centred */
  }
</style>
"""

path = sys.argv[1]
html = open(path, encoding="utf-8").read()
if "brand_web_page.py" not in html:
    html = html.replace("</head>", STYLE + "</head>", 1)
    html = html.replace('<div id="infobox">Loading, please wait ...</div>', '<div id="infobox">DRIFT TANK &middot; loading...</div>')
    html = html.replace('platform.document.body.style.background = "#7f7f7f"',
                        'platform.document.body.style.background = "#14182c"')
    open(path, "w", encoding="utf-8").write(html)
assert "brand_web_page.py" in html and "#14182c" in html
print("page branded:", path)
