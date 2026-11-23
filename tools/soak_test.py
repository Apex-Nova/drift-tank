"""Soak test: plays many full matches headless (no window, fast clock) and reports every crash
and every impossible state it sees. Run it after any change:

    .venv/bin/python tools/soak_test.py            # local + LAN scenarios
    .venv/bin/python tools/soak_test.py --online   # also an online room through the real relay

Exit code 0 = everything passed. Each scenario prints one line: PASS / FAIL + what went wrong.
"""
import base64
import json
import math
import os
import socket
import struct
import sys
import threading
import time
import traceback

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import pygame  # noqa: E402

# ---- one simulated clock for everything (matches run much faster than real time) ----
CLOCK = [100000]
pygame.time.get_ticks = lambda: CLOCK[0]

from part1_engine.app import App  # noqa: E402
from part1_engine.bot import Bot  # noqa: E402
from part1_engine.game import Game  # noqa: E402
from part1_engine import network  # noqa: E402
from part3_world.maps import MAPS  # noqa: E402

FRAME_MS = 1000 // 60
results = []


def tick(*games, draw_every=6, surface=None, frames=1):
    for _ in range(frames):
        CLOCK[0] += FRAME_MS
        for g in games:
            g.update_screen()
        if surface is not None and CLOCK[0] // FRAME_MS % draw_every == 0:
            for g in games:
                g.draw(surface)


def check_world(g, problems):
    """Invariants every frame should keep."""
    b = g.map.bounds.inflate(80, 80)
    for t in g.tanks:
        if not (math.isfinite(t.pos.x) and math.isfinite(t.pos.y)):
            problems.add("tank %d position is not a number" % t.player_id)
        elif t.alive and not b.collidepoint(t.pos):
            problems.add("tank %d left the map at %s" % (t.player_id, (round(t.pos.x), round(t.pos.y))))
        if t.health > t.max_health or (t.alive and t.health <= 0):
            problems.add("tank %d health %s while alive=%s" % (t.player_id, t.health, t.alive))
        if t.weapon is not None and t.ammo <= 0:
            problems.add("tank %d holds %s with 0 ammo" % (t.player_id, t.weapon))


def scenario(name):
    def wrap(fn):
        def run():
            problems = set()
            start = time.time()
            try:
                fn(problems)
            except Exception:
                problems.add("CRASH: " + traceback.format_exc().strip().splitlines()[-1] + "\n" +
                             "".join(traceback.format_exc().splitlines(True)[-6:-1]))
            results.append((name, sorted(problems), time.time() - start))
            print("%-46s %s  (%.1fs)" % (name, "PASS" if not problems else "FAIL", time.time() - start), flush=True)
            for p in sorted(problems):
                print("      - " + p.replace("\n", "\n        "), flush=True)
        return run
    return wrap


# ------------------------------------------------------------------ scenarios
def full_local_match(map_id, rules):
    @scenario("local %s on %s: full match" % (rules.upper(), map_id))
    def run(problems):
        app = App()
        app.start_game("local", map_id, bots=3, rules=rules)
        g = app.screen
        g.bots[1] = Bot(1, skill=0.9)                 # a bot drives the player too
        surf = pygame.Surface(app.window.get_size())
        for i in range(60 * 60 * 6):                  # up to 6 simulated minutes
            tick(g, surface=surf)
            check_world(g, problems)
            if g.phase == "over":
                break
        if g.phase != "over":
            problems.add("match did not end in 6 minutes (phase=%s)" % g.phase)
        elif rules == "br" and g.winner is None and any(t.alive for t in g.tanks):
            problems.add("BR ended with no winner while tanks are alive")
        # play again on a fresh map, then leave
        g.start_match()
        tick(g, surface=surf, frames=240)
        check_world(g, problems)
        g.leave()
        app.step()
    return run


@scenario("pause, resume, spectate after death")
def pause_and_spectate(problems):
    app = App()
    app.start_game("local", "frost", bots=3, rules="br")
    g = app.screen
    tick(g, frames=300)
    g.paused = True
    before = [tuple(t.pos) for t in g.tanks]
    tick(g, frames=120)
    if g.mode == "local" and [tuple(t.pos) for t in g.tanks] != before:
        problems.add("tanks moved while paused")
    g.paused = False
    me = g.find_tank(1)
    me.take_damage(999, CLOCK[0])
    tick(g, frames=120)
    if me.alive:
        problems.add("player still alive after 999 damage")
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB, mod=0, unicode="", scancode=0))
    tick(g, frames=30)
    g.leave()


def ws_connect(port, path):
    s = socket.create_connection(("127.0.0.1", port), timeout=5)
    key = base64.b64encode(os.urandom(16)).decode()
    s.sendall(("GET %s HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
               "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n" % (path, key)).encode())
    buf = b""
    while b"\r\n\r\n" not in buf:
        buf += s.recv(4096)
    rest = [buf.split(b"\r\n\r\n", 1)[1]]

    def rx(n):
        while len(rest[0]) < n:
            d = s.recv(65536)
            if not d:
                raise EOFError
            rest[0] += d
        d, rest[0] = rest[0][:n], rest[0][n:]
        return d

    def recv():
        b0, b1 = rx(2)
        n = b1 & 0x7F
        if n == 126:
            n = struct.unpack(">H", rx(2))[0]
        elif n == 127:
            n = struct.unpack(">Q", rx(8))[0]
        return rx(n).decode()

    def send(text):
        p = text.encode()
        m = os.urandom(4)
        h = bytearray([0x81])
        if len(p) < 126:
            h.append(0x80 | len(p))
        else:
            h.append(0x80 | 126)
            h += struct.pack(">H", len(p))
        s.sendall(bytes(h) + m + bytes(b ^ m[i % 4] for i, b in enumerate(p)))
    return s, recv, send


@scenario("LAN host + laptop + phone app + controller")
def lan_everyone(problems):
    app = App()
    err = app.start_game("host", "scrap", bots=0, rules="tdm")
    if err:
        problems.add("could not host: " + err)
        return
    host = app.screen
    surf = pygame.Surface(app.window.get_size())
    laptop = Game(mode="join", host_ip="127.0.0.1", name="LAPTOP")
    s_game, recv_game, send_game = ws_connect(8080, "/game")
    welcome = json.loads(recv_game())
    s_pad, recv_pad, send_pad = ws_connect(8080, "/")
    pad_welcome = json.loads(recv_pad())
    states = [0]

    def reader():
        while True:
            try:
                if json.loads(recv_game()).get("type") == "state":
                    states[0] += 1
            except Exception:
                return
    threading.Thread(target=reader, daemon=True).start()
    tick(host, laptop, frames=30)
    ids = host.network.connected_ids()
    if len(ids) != 3:
        problems.add("host sees %d players, expected 3 (laptop, phone app, controller)" % len(ids))
    if welcome.get("type") != "welcome" or pad_welcome.get("t") != "welcome":
        problems.add("missing welcome message")
    # lobby: start must wait for READY
    host.begin_match()
    if host.phase != "lobby":
        problems.add("match started before everyone pressed READY")
    laptop.ready = True
    for i in range(30):
        send_game(json.dumps({"move_x": 0, "move_y": 0, "aim_angle": None, "shoot": False, "ready": True}))
        tick(host, laptop)
        time.sleep(0.002)
    host.begin_match()
    if host.phase != "countdown":
        problems.add("START did not work once everyone was READY (phase=%s)" % host.phase)
    for i in range(60 * 30):
        if i % 4 == 0:
            send_game(json.dumps({"move_x": 1, "move_y": 0.3, "aim_angle": 45, "shoot": True}))
            send_pad(json.dumps({"mx": -1, "my": 0, "ax": 1, "ay": 0, "fire": True}))
        tick(host, laptop, surface=surf)
        check_world(host, problems)
        if i % 200 == 0:
            time.sleep(0.01)
    if laptop.phase != host.phase:
        problems.add("laptop phase %s != host phase %s" % (laptop.phase, host.phase))
    if states[0] < 50:
        problems.add("phone app received only %d state updates" % states[0])
    # phone app leaves, laptop leaves, then rejoins
    s_game.close()
    s_pad.close()
    laptop.leave()
    for i in range(60):
        tick(host)
        time.sleep(0.003)
    if host.network.connected_ids():
        problems.add("players still listed after leaving: %s" % host.network.connected_ids())
    laptop2 = Game(mode="join", host_ip="127.0.0.1", name="AGAIN")
    tick(host, laptop2, frames=60)
    if not host.network.connected_ids():
        problems.add("rejoin failed")
    laptop2.leave()
    host.leave()
    app.step()


@scenario("online room through the relay (desktop)")
def online_room(problems):
    app = App()
    err = app.start_game("host", "valley", bots=1, online=True)
    if err:
        problems.add("could not host online: " + err)
        return
    host = app.screen
    for i in range(30):
        tick(host)
        time.sleep(0.01)
    code = host.network.ip
    friend = Game(mode="join", host_ip=code, name="FRIEND")
    friend.ready = True
    for i in range(200):
        tick(host, friend)
        time.sleep(0.005)
    host.begin_match()
    for i in range(600):
        tick(host, friend)
        if i % 50 == 0:
            time.sleep(0.02)
    if host.phase not in ("countdown", "playing"):
        problems.add("online match did not start (host phase=%s)" % host.phase)
    for i in range(40):                       # let the last state arrive over the real network
        host.update_screen()
        friend.update_screen()
        time.sleep(0.03)
    if friend.phase != host.phase:
        problems.add("friend phase %s != host phase %s" % (friend.phase, host.phase))
    friend.leave()
    host.leave()
    app.step()


if __name__ == "__main__":
    for m in MAPS:
        for rules in ("br", "tdm"):
            full_local_match(m["id"], rules)()
    pause_and_spectate()
    lan_everyone()
    if "--online" in sys.argv:
        online_room()
    failed = [r for r in results if r[1]]
    print("\n%d / %d scenarios passed" % (len(results) - len(failed), len(results)))
    sys.exit(1 if failed else 0)
