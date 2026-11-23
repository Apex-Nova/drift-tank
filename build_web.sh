#!/bin/sh
# Builds the WEB version of Drift Tank with pygbag (Python + Pygame compiled to WebAssembly).
#   ./build_web.sh          -> build into build/web/drift-tank/build/web/  (upload that folder anywhere)
#   ./build_web.sh serve    -> build, then test it at http://localhost:8000
#   ./build_web.sh crazygames -> build, then make dist/crazygames/ (upload folder for CrazyGames:
#                              their SDK added, no archive files inside)
# Needs:  pip install pygbag certifi      and  ffmpeg (turns the .wav effects into small .mp3 for browsers)
# Web version = single player vs bots (browsers can't open the LAN sockets online play uses).
set -e
cd "$(dirname "$0")"
OUT=build/web/drift-tank
rm -rf "$OUT"
mkdir -p "$OUT"

# 1. copy only what the game needs (no .venv, dist, practice, docs...)
cp main.py "$OUT/"
for d in part1_engine part2_combat part3_world part4_ui shared; do
  rsync -a --exclude '__pycache__' --exclude '*.md' --exclude '*.wav' --exclude '*.mp3' --exclude '*.ogg' "$d" "$OUT/"
done

# 2. audio
# sound effects + music are NOT packed into the game: the browser plays them itself
# (shared/web.py dtSfx / dtMusic) - no stutter when a frame is slow, and a smaller download.
rm -rf "$OUT/part4_ui/assets/music" "$OUT/part4_ui/assets/sounds" build/web/music build/web/sfx
mkdir -p build/web/music build/web/sfx
cp part4_ui/assets/music/*.mp3 build/web/music/
for wav in part4_ui/assets/sounds/sfx_*.wav; do
  ffmpeg -loglevel error -y -i "$wav" -c:a libmp3lame -q:a 4 "build/web/sfx/$(basename "$wav" .wav).mp3"
done

# macOS python.org Python has no SSL certificates by default; certifi provides them
SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())" 2>/dev/null) && export SSL_CERT_FILE

# 3. compile to WebAssembly (pygbag writes $OUT/build/web/index.html + drift-tank.apk)
if [ "$1" = "serve" ]; then
  mkdir -p "$OUT/build/web" && cp -R build/web/music build/web/sfx "$OUT/build/web/"
  python -m pygbag --ume_block 0 --title "Drift Tank" "$OUT"
else
  python -m pygbag --build --ume_block 0 --title "Drift Tank" "$OUT"
  cp -R build/web/music build/web/sfx "$OUT/build/web/"
  python tools/brand_web_page.py "$OUT/build/web/index.html"     # game colours on the loading page
  echo "Done -> $OUT/build/web/"
  if [ "$1" = "crazygames" ]; then
    # CrazyGames upload: their uploader refuses archive files (.tar.gz / .apk), so the game data
    # gets another name; and their SDK is loaded first (it locks the game to CrazyGames' sites,
    # which is why it is ONLY in this folder, not on GitHub Pages or in the Android app).
    CG=dist/crazygames
    rm -rf "$CG" && mkdir -p dist && cp -R "$OUT/build/web" "$CG"
    mv "$CG/drift-tank.tar.gz" "$CG/drift-tank.tgzdata"
    rm -f "$CG/drift-tank.apk"
    sed -i.bak 's/drift-tank\.tar\.gz/drift-tank.tgzdata/g' "$CG/index.html"
    sed -i.bak 's|<head>|<head>\
    <script src="https://sdk.crazygames.com/crazygames-sdk-v3.js"></script>|' "$CG/index.html"
    rm -f "$CG/index.html.bak"
    grep -q crazygames-sdk-v3 "$CG/index.html" && grep -q tgzdata "$CG/index.html"
    echo "CrazyGames upload folder -> $CG/  (drag everything inside it into the uploader)"
  fi
fi
