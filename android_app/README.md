# Android app

The Android app is the **web version** (`build_web.sh`) inside an Android WebView,
made with [Capacitor](https://capacitorjs.com). GitHub Actions builds it for you
(`.github/workflows/release.yml`) - no Android Studio needed.

`server.hostname` is set to `drifttank.app` because the web runtime (pygbag)
treats a page on `localhost` as a local test server and would look for files there.
