#!/bin/sh
# Builds "Drift Tank.app" (macOS) or "Drift Tank.exe" (Windows, run in Git Bash) into dist/
# Needs:  pip install -r requirements.txt pyinstaller
set -e
cd "$(dirname "$0")"
SEP=":"; ICON="build_assets/icon.icns"
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) SEP=";"; ICON="part4_ui/assets/images/ui/icon.png";; esac
python -m PyInstaller --noconfirm --clean --windowed --name "Drift Tank" \
  --icon "$ICON" \
  --osx-bundle-identifier com.drifttank.game \
  --add-data "part4_ui/assets${SEP}part4_ui/assets" \
  --add-data "part1_engine/phone_page.html${SEP}part1_engine" \
  main.py
echo "Done -> dist/"
