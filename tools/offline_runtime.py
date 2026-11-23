"""Put the web runtime (Python + Pygame for the browser) INSIDE the Android app, so it starts
without internet.

pygbag pages normally download ~22 MB from https://pygame-web.github.io/cdn/ every start:
the Python interpreter (main.wasm/main.data), the terminal scripts and the pygame-ce wheel.
On a phone with no or slow internet the app then sat on "Loading" for a long time (or forever).

    python3 tools/offline_runtime.py android_app/www

1. downloads those files once (kept in build/runtime_cache/)
2. copies them to <www>/cdn/ with the same folder layout
3. points index.html at /cdn/ and adds a tiny fetch() redirect for the URLs pygbag builds
   inside Python (the package index and the pygame wheel), which we can't edit.
"""
import os
import shutil
import subprocess
import sys

CDN = "https://pygame-web.github.io/cdn/"
FILES = [
    "0.9.3/pythons.js",
    "0.9.3/empty.html",
    "0.9.3/cpythonrc.py",
    "0.9.3/cpython312/main.js",
    "0.9.3/cpython312/main.data",
    "0.9.3/cpython312/main.wasm",
    "vtx.js",
    "vt/xterm.css",
    "vt/xterm.js",
    "vt/xterm-addon-image.js",
    "index-0.9.3-cp312.json",
    "cp312/pygame_ce-2.5.7-cp312-cp312-wasm32_bi_emscripten.whl",
]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "build", "runtime_cache")

# Runs before the game's own script: any fetch() aimed at the CDN is served from the app instead.
REDIRECT = ('<script>(function(){var f=window.fetch,c="%s";window.fetch=function(u,o){'
            'if(typeof u==="string"&&u.indexOf(c)===0)u="/cdn/"+u.slice(c.length);'
            'return f.call(this,u,o)}})()</script>' % CDN)


def main(www):
    for name in FILES:
        cached = os.path.join(CACHE, name)
        if not os.path.exists(cached):
            os.makedirs(os.path.dirname(cached), exist_ok=True)
            print("downloading", name)
            # curl, not urllib: python.org Python on macOS ships without SSL certificates
            subprocess.run(["curl", "-sSfL", "-o", cached + ".part", CDN + name], check=True)
            os.replace(cached + ".part", cached)
        target = os.path.join(www, "cdn", name)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copyfile(cached, target)

    page = os.path.join(www, "index.html")
    html = open(page, encoding="utf-8").read()
    if REDIRECT not in html:
        html = html.replace(CDN, "/cdn/")
        # the browser can't register a service worker from a file we don't ship; it isn't needed offline
        html = html.replace('navigator.serviceWorker.register("/cdn/0.9.3/pygbag0.9.3.js")', "0")
        html = html.replace('<html lang="en-us">', '<html lang="en-us">' + REDIRECT, 1)
        open(page, "w", encoding="utf-8").write(html)
    if CDN in html.replace(REDIRECT, ""):
        sys.exit("index.html still points at the CDN")
    print("runtime bundled into", os.path.join(www, "cdn"))


if __name__ == "__main__":
    main(sys.argv[1])
