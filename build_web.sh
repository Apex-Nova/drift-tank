#!/bin/sh
# Builds the WEB version of Drift Tank with pygbag (Python + Pygame compiled to WebAssembly).
#   ./build_web.sh          -> build into build/web/drift-tank/build/web/  (upload that folder anywhere)
#   ./build_web.sh serve    -> build, then test it at http://localhost:8000
# Needs:  pip install pygbag certifi      and  ffmpeg (to turn .wav into small .ogg for browsers)
# Web version = single player vs bots (browsers can't open the LAN sockets online play uses).
set -e
cd "$(dirname "$0")"
OUT=build/web/drift-tank
rm -rf "$OUT"
mkdir -p "$OUT"

# 1. copy only what the game needs (no .venv, dist, practice, docs...)
cp main.py "$OUT/"
for d in part1_engine part2_combat part3_world part4_ui shared; do
  rsync -a --exclude '__pycache__' --exclude '*.md' --exclude '*.wav' "$d" "$OUT/"
done

# 2. browsers play .ogg best, and it is ~10x smaller than .wav
CODEC="-c:a libvorbis -q:a 3"
ffmpeg -hide_banner -encoders 2>/dev/null | grep -q libvorbis || CODEC="-c:a vorbis -strict -2 -ac 2 -q:a 3"
for wav in part4_ui/assets/sounds/*.wav part4_ui/assets/music/*.wav; do
  ffmpeg -loglevel error -y -i "$wav" $CODEC "$OUT/${wav%.wav}.ogg"
done

# macOS python.org Python has no SSL certificates by default; certifi provides them
SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())" 2>/dev/null) && export SSL_CERT_FILE

# 3. compile to WebAssembly (pygbag writes $OUT/build/web/index.html + drift-tank.apk)
if [ "$1" = "serve" ]; then
  python -m pygbag --ume_block 0 --title "Drift Tank" "$OUT"
else
  python -m pygbag --build --ume_block 0 --title "Drift Tank" "$OUT"
  echo "Done -> $OUT/build/web/"
fi
