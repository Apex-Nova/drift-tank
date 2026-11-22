"""Helpers for the WEB / PHONE version (the game compiled to WebAssembly with pygbag).

In a browser, Python can't use threads or normal sockets, and decoding music in
Python while the game runs makes it crackle when a frame is slow. So for those jobs
we hand the work to the browser itself with a little JavaScript (installed once):

    dtMusic  - plays the music with the browser's own <audio> player (smooth, no crackle)
    dtNet    - WebSocket client (join a host) and, inside the Android app, the native
               DriftNet server plugin (host a game). Messages wait in a queue until
               Python picks them up once per frame with poll().
"""
import json
import sys

IS_WEB = sys.platform == "emscripten"

_JS = r"""
window.dtSfx = window.dtSfx || {
  // Sound effects played by the browser's Web Audio (no stutter when a frame is slow).
  ctx: null, buffers: {}, loading: {},
  context() {
    if (!this.ctx) {
      const C = window.AudioContext || window.webkitAudioContext;
      if (!C) return null;
      this.ctx = new C();
      const wake = () => { if (this.ctx.state !== "running") this.ctx.resume(); };
      ["pointerdown", "touchstart", "keydown"].forEach(e => document.addEventListener(e, wake, true));
    }
    return this.ctx;
  },
  load(name) {
    const ctx = this.context();
    if (!ctx || this.loading[name]) return;
    this.loading[name] = true;
    fetch("sfx/" + name + ".mp3").then(r => r.arrayBuffer())
      .then(b => ctx.decodeAudioData(b)).then(buf => { this.buffers[name] = buf; })
      .catch(() => {});
  },
  play(name, gain) {
    const ctx = this.context();
    if (!ctx) return;
    const buf = this.buffers[name];
    if (!buf) { this.load(name); return; }          // first time: start loading, play next time
    const src = ctx.createBufferSource();
    const g = ctx.createGain();
    g.gain.value = gain;
    src.buffer = buf; src.connect(g); g.connect(ctx.destination); src.start();
  },
  preload(names) { names.split(",").forEach(n => this.load(n)); }
};

window.dtMusic = window.dtMusic || {
  a: null, vol: 0.3, list: [], last: "",
  // play a shuffled playlist: when a track ends, a different random one starts
  playlist(names, loop) {
    this.list = names.split(",");
    this.loopList = loop;
    this.next();
  },
  next() {
    const pool = this.list.filter(n => n !== this.last);
    const name = (pool.length ? pool : this.list)[Math.floor(Math.random() * (pool.length || this.list.length))];
    this.last = name;
    this.play(name, false);
  },
  play(name, loop) {
    if (this.a) { this.a.onended = null; this.a.pause(); }
    const a = new Audio("music/" + name + ".mp3");
    a.loop = loop; a.volume = this.vol; this.a = a;
    a.onended = () => { if (this.a === a && this.loopList && this.list.length) this.next(); };
    a.play().catch(() => {             // browsers only allow sound after the first tap/key
      const go = () => {
        ["pointerdown", "touchstart", "keydown"].forEach(e => document.removeEventListener(e, go, true));
        if (this.a === a) a.play().catch(() => {});
      };
      ["pointerdown", "touchstart", "keydown"].forEach(e => document.addEventListener(e, go, true));
    });
  },
  stop() { if (this.a) { this.a.pause(); this.a = null; } },
  volume(v) { this.vol = v; if (this.a) this.a.volume = v; }
};

window.dtNet = window.dtNet || {
  q: [], ws: null, state: "idle", ip: "", hosting: false,
  push(m) { this.q.push(m); },
  poll() { const out = this.q; this.q = []; return JSON.stringify(out); },

  // ---- client: join a host with a WebSocket ----
  connect(url) {
    this.close();
    this.state = "connecting";
    let ws;
    try { ws = new WebSocket(url); } catch (e) { this.state = "error"; this.push({k: "error"}); return; }
    this.ws = ws;
    ws.onopen = () => { this.state = "open"; this.push({k: "open"}); };
    ws.onmessage = (e) => this.push({k: "msg", d: e.data});
    ws.onerror = () => this.push({k: "error"});
    ws.onclose = () => { this.state = "closed"; this.push({k: "close"}); };
  },
  send(text) { if (this.ws && this.ws.readyState === 1) this.ws.send(text); },
  close() { if (this.ws) { try { this.ws.close(); } catch (e) {} this.ws = null; } },

  // ---- host an INTERNET room through the relay server (server/src/index.js) ----
  relay: null,
  hostRelay(url) {
    this.hostStop();
    const ws = new WebSocket(url + "/host");
    this.relay = ws;
    ws.onmessage = (e) => {
      let m; try { m = JSON.parse(e.data); } catch (x) { return; }
      if (m.k === "hosting") { this.hosting = true; this.ip = m.code; this.push({k: "hosting", ip: m.code}); }
      else this.push(m);                   // join / msg / leave: same events as the Android plugin
    };
    ws.onclose = () => {
      if (this.relay === ws) { this.relay = null; this.hosting = false; this.push({k: "hosterror", d: "lost the online server"}); }
    };
  },
  relaySend(obj) { if (this.relay && this.relay.readyState === 1) this.relay.send(JSON.stringify(obj)); },

  // ---- host on the local Wi-Fi: only inside the Android app (native DriftNet plugin) ----
  plugin() {
    const C = window.Capacitor;
    return C && C.Plugins && C.Plugins.DriftNet ? C.Plugins.DriftNet : null;
  },
  canHost() { return !!this.plugin(); },
  async host(page, tcpPort, wsPort) {
    const p = this.plugin();
    if (!p) { this.push({k: "hosterror", d: "no plugin"}); return; }
    if (!this.listening) {
      this.listening = true;
      p.addListener("join", (e) => this.push({k: "join", id: e.id, kind: e.kind}));
      p.addListener("message", (e) => this.push({k: "msg", id: e.id, d: e.data}));
      p.addListener("leave", (e) => this.push({k: "leave", id: e.id}));
    }
    try {
      const r = await p.start({tcpPort: tcpPort, wsPort: wsPort, page: page});
      this.ip = r.ip || ""; this.hosting = true; this.push({k: "hosting", ip: this.ip});
    } catch (e) { this.push({k: "hosterror", d: String(e)}); }
  },
  hostSend(id, text) {
    if (this.relay) { this.relaySend({to: [id], d: text}); return; }
    const p = this.plugin(); if (p) p.send({id: id, data: text});
  },
  hostBroadcast(ids, text) {
    if (typeof ids === "string") ids = JSON.parse(ids);
    if (this.relay) { this.relaySend({to: ids, d: text}); return; }
    const p = this.plugin(); if (p) p.broadcast({ids: ids, data: text});
  },
  hostKick(id) {
    if (this.relay) { this.relaySend({kick: id}); return; }
    const p = this.plugin(); if (p) p.kick({id: id});
  },
  hostStop() {
    this.hosting = false;
    if (this.relay) { const r = this.relay; this.relay = null; try { r.close(); } catch (e) {} return; }
    const p = this.plugin(); if (p && this.listening) p.stop();
  },
  async lanIp() { const p = this.plugin(); if (!p) return ""; try { const r = await p.ip(); this.ip = r.ip || ""; } catch (e) {} return this.ip; }
};
"""

_installed = False


def window():
    """The browser's `window` object (with our helpers installed)."""
    global _installed
    import platform as browser          # in pygbag, platform.window is the JavaScript window
    if not _installed:
        browser.window.eval(_JS)
        _installed = True
    return browser.window


def js(code):
    """Run a line of JavaScript (only with text we build ourselves, never user input)."""
    return window().eval(code)


def js_str(text):
    """Turn a Python string into a safe JavaScript string literal."""
    return json.dumps(str(text))


_can_host = None


def can_host():
    """True inside the Android app (it has the native DriftNet server plugin)."""
    global _can_host
    if _can_host is None:
        _can_host = IS_WEB and bool(js("dtNet.canHost()"))
    return _can_host


def relay_url():
    """The online-rooms server. A test page can override it: index.html?relay=ws://127.0.0.1:8787"""
    from shared.settings import Settings
    override = str(js("new URLSearchParams(location.search).get('relay') || ''"))
    return override or Settings.RELAY_URL


def is_room_code(text):
    return len(text) == 5 and text.isdigit()


def can_join():
    """A web page on https can't open ws:// to a LAN address; the Android app can."""
    return IS_WEB and (can_host() or str(js("location.protocol")) == "http:")
