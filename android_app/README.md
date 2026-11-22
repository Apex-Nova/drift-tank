# Android app

The Android app is the **web version** (`build_web.sh`) inside an Android WebView,
made with [Capacitor](https://capacitorjs.com). GitHub Actions builds it for you
(`.github/workflows/release.yml`) - no Android Studio needed.

`server.hostname` is set to `drifttank.app` because the web runtime (pygbag)
treats a page on `localhost` as a local test server and would look for files there.

`prepare_www.sh` copies the web build into `www/`. It renames `drift-tank.tar.gz`
to `drift-tank.tgzdata` because Android's packaging tool unpacks every `.gz` file
and drops the extension, which left the game stuck on "Loading".

**Hosting from the phone:** `native/DriftNetPlugin.java` is a tiny Capacitor plugin that opens
port 5757 (laptops, JSON lines) and 8080 (phones: WebSocket, plus the controller page).
`patch_android.sh` copies it (and `MainActivity.java`, which registers it) into the generated
Android project, turns on landscape and allows plain `ws://` traffic on the local Wi-Fi.
