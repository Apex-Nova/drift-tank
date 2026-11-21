#!/bin/sh
# Run after "npx cap add android": makes the app landscape-only (like a console game).
set -e
cd "$(dirname "$0")"
M=android/app/src/main/AndroidManifest.xml
if ! grep -q 'screenOrientation=' "$M"; then
  perl -0pi -e 's/<activity(?=\s)/<activity android:screenOrientation="sensorLandscape"/' "$M"
fi
grep -q 'screenOrientation="sensorLandscape"' "$M"
echo "landscape set"
