#!/bin/sh
# Run after "npx cap add android":
#   - landscape only (like a console game)
#   - allow plain ws:// / http:// on the local Wi-Fi (LAN games don't use https)
#   - add our native DriftNet plugin (lets the phone HOST a game) + register it
set -e
cd "$(dirname "$0")"
M=android/app/src/main/AndroidManifest.xml
if ! grep -q 'screenOrientation=' "$M"; then
  perl -0pi -e 's/<activity(?=\s)/<activity android:screenOrientation="sensorLandscape"/' "$M"
fi
if ! grep -q 'usesCleartextTraffic' "$M"; then
  perl -0pi -e 's/<application(?=\s)/<application android:usesCleartextTraffic="true"/' "$M"
fi
# Wi-Fi game finder: receive the hosts' broadcast announcements
if ! grep -q 'CHANGE_WIFI_MULTICAST_STATE' "$M"; then
  perl -0pi -e 's|(<uses-permission android:name="android.permission.INTERNET" />)|$1\n    <uses-permission android:name="android.permission.CHANGE_WIFI_MULTICAST_STATE" />\n    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />|' "$M"
fi
grep -q 'screenOrientation="sensorLandscape"' "$M"
grep -q 'usesCleartextTraffic="true"' "$M"
grep -q 'CHANGE_WIFI_MULTICAST_STATE' "$M"

JAVA=android/app/src/main/java/com/drifttank/game
mkdir -p "$JAVA"
cp native/DriftNetPlugin.java native/MainActivity.java "$JAVA/"
echo "android project patched"
