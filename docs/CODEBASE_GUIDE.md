# Drift Tank — The Complete Codebase Guide

This guide explains **everything** in this repository: what the game is, how the code is organised,
what every file does, who built what, and — step by step — **how the online multiplayer works**.
Read it top to bottom once, and you can explain the whole project to anyone.

---

## Contents
1. [The game in one minute](#1-the-game-in-one-minute)
2. [How to run it](#2-how-to-run-it)
3. [The big picture: how the code fits together](#3-the-big-picture)
4. [Folder map + who built what](#4-folder-map--who-built-what)
5. [One frame of the game, step by step](#5-one-frame-of-the-game-step-by-step)
6. [Every file explained](#6-every-file-explained)
7. [The multiplayer lesson (from the first socket to the finished game)](#7-the-multiplayer-lesson)
8. [Art, sound, fonts and colours](#8-art-sound-fonts-and-colours)
9. [How to explain this project to someone (cheat sheet)](#9-cheat-sheet-explaining-the-project)
10. [Glossary](#10-glossary)

---

## 1. The game in one minute

**Drift Tank** is a top-down (3/4 view) pixel-art tank battle for up to **4 players**.

| Thing | How it works |
|---|---|
| **Loot** | Tanks start with **no weapon**. Crates drop from the sky. Drive over one to get a random weapon with **limited ammo**. Ammo runs out → find the next crate. |
| **6 weapons** | Machine Gun, Big Cannon, Scatter Gun, Rockets, Railgun (pierces tanks), Bouncer (bounces off walls). |
| **Drifting** | The hull turns slowly and the tank slides before it grips (extra slippery on ice). |
| **2 modes** | **Battleground**: one life, a safe zone shrinks every ~minute, last tank standing wins. **Team Deathmatch**: red (P1, P3) vs blue (P2, P4), respawns, first team to 15 kills. |
| **Maps** | 4 themes (Canyon, Valley, Frost, Scrapyard). A **new random map is generated every match** — mirrored into 4 equal quarters so it's fair. |
| **Players** | You vs bots, or **online**: other laptops on the same Wi-Fi, and **phones as controllers** (no app — just the browser). |

**Controls:** WASD or ARROWS drive · MOUSE or Q/E or J/K aim · SPACE or LEFT CLICK fire · ESC pause · F11 fullscreen

---

## 2. How to run it

```bash
.venv/bin/python main.py                 # main menu
.venv/bin/python main.py host            # straight to "host online"
.venv/bin/python main.py join 192.168.1.5  # join a host (use the IP the host shows)
```
Phones: while someone hosts, open `http://<host IP>:8080` in the phone's browser.

Build the Mac app (Windows: run the same script on a Windows PC):
```bash
./build_app.sh        # -> dist/Drift Tank.app
```
Web version (pygbag compiles Python + Pygame to WebAssembly so it runs in a browser):
```bash
./build_web.sh serve  # test at http://localhost:8000   (./build_web.sh alone = build only)
```
How the web/phone versions work:
- `App.run()` is **async**: each frame ends with `await asyncio.sleep(0)`, which hands control
  back to the browser (a browser tab can't run a never-ending `while` loop).
- `part1_engine/touch.py` draws two thumb sticks and turns fingers into the same inputs dict
  the keyboard makes. In a browser a finger tap doesn't create a mouse click, so `App.touch_as_mouse`
  makes one, which lets the menus work with taps.
- **Speed on phones:** the game logic always runs 60 times a second (`App.updates_this_frame`);
  a slow phone just draws fewer frames. Text, panels, name tags and the zone tint are cached
  instead of redrawn every frame, and the screen-edge vignette is skipped (`renderer.LITE`).
- **Music on the web** is played by the browser's own `<audio>` player (`shared/web.py`, `dtMusic`),
  as `.mp3` files next to the page. Decoding it in Python crackled whenever a frame was slow.
- The **Android app** (`android_app/`) is the web version inside an Android WebView (Capacitor).
- **Online play on phones** (`part1_engine/webnet.py`):
  - *Join*: a browser can open a WebSocket, so the phone connects to `ws://<host>:8080/game`
    and gets the same messages a laptop gets (welcome, state, inputs).
    `phone.py` on a Mac/Windows host answers `/game` as a full player, `/` as a controller.
  - *Host*: a WebView can't open ports, so a small native plugin
    (`android_app/native/DriftNetPlugin.java`) opens port 5757 (laptops) and 8080 (phones) and
    passes every message to Python; all game rules stay in Python (`WebHost`).
  - *Online rooms (internet)*: the website can't reach `ws://` addresses on your Wi-Fi, so it uses
    the relay server in `server/` (Cloudflare). HOST ONLINE connects to `wss://<relay>/host` and gets a
    5-digit room code; JOIN connects to `wss://<relay>/join/<code>`. The relay just forwards the same
    `join` / `msg` / `leave` events as the Android plugin, so `WebHost` doesn't care which one it uses.
    The host's tab must stay open and visible: a hidden browser tab is paused, and so is the match.
  - *Mac / Windows online rooms*: `part1_engine/relaynet.py` (`RelayHost`, `RelayClient`) talks to the
    same relay over `wss://` with a small hand-written WebSocket client, so desktop, phone and web
    players can share one room.
- **Waiting room**: a hosted game starts in phase `"lobby"`. Nothing moves; `Game.lobby_list()` sends
  who is there and who pressed READY (joiners send `"ready": true` with their inputs). The host's
  START calls `Game.begin_match()`, which only works once everyone is ready.
- **CrazyGames** (`./build_web.sh crazygames` -> `dist/crazygames/`): the upload folder loads the
  CrazyGames SDK (only there - it locks a game to CrazyGames' sites). `shared/web.py` `dtCG` reports
  loading and gameplay start/stop, shares the online room (Invite button + `updateRoom`), joins a
  friend's room from an invite link, hosts right away for "instant multiplayer", obeys
  `muteAudio`, and uses the CrazyGames username. Outside CrazyGames all of it does nothing.
- **Phone screen fit**: `main.py` makes the game as wide as the phone's screen shape
  (e.g. 1600x720 on a 20:9 phone) before anything else loads, so there are no black bars.
- **Windows / Android / web** are built on GitHub's computers by `.github/workflows/release.yml`
  when you push a tag like `v1.1`.

Regenerate all sounds + music:
```bash
.venv/bin/python tools/make_audio.py
```

---

## 3. The big picture

The project is split into **4 parts** (one per team member) plus a shared settings file.

```
                         main.py  ── starts ──►  App (part1_engine/app.py)
                                                     │  owns the window + main loop
                                                     │  shows ONE "screen" at a time
               ┌─────────────────────────────────────┼─────────────────────────────┐
               ▼                                     ▼                             ▼
   Menus (part4_ui/screens.py)            Game (part1_engine/game.py)        Settings/Help...
   intro, main menu, map select,          one match: rules, players,
   join, settings, help                   network, camera
                                                     │ uses
        ┌──────────────────┬───────────────────┬─────┴────────────┬──────────────────────┐
        ▼                  ▼                   ▼                  ▼                      ▼
   Tank + Bot          Weapons + FX        Map + Loot         Renderer + View        HUD + UI + Art
   (part1_engine)      (part2_combat)      (part3_world)      (part1_engine)         (part4_ui)
```

### The 3 most important ideas

**1. The world is flat; only the drawing is tilted.**
All game logic (movement, collisions, bullets, network) uses simple `(x, y)` pixel coordinates,
like a map seen straight from above. Only `view.py` + `renderer.py` turn that into the tilted 3/4 picture.
That's why the rules are simple and the network messages stay small.

**2. Inputs are data.** (your Lesson 6 — B1)
A tank never reads the keyboard. Every frame it receives a dictionary:
```python
{"move_x": 0.0, "move_y": -1.0, "aim_angle": 90, "barrel_left": False, "barrel_right": False, "shoot": True}
```
That dictionary can come from **your keyboard, a bot, another laptop, or a phone** — the tank doesn't care.
This one idea is what made online play, bots and phones possible.

**3. The host is the boss.** (host-authoritative)
Only one computer (the host) runs the real rules. Everyone else just sends inputs and draws what the
host tells them. So two players can never disagree about who got hit.

---

## 4. Folder map + who built what

Honest credits — who wrote what (from the git history and our sessions):

| Folder / file | Purpose | Built by |
|---|---|---|
| `main.py` | Starts the app, reads `host` / `join IP` from the command line | **Person 1 (you)** — first version; extended later |
| `part1_engine/tank.py` | The Tank: drift movement, barrel, shooting, health | **You** (movement, drift, barrel, shoot, take_damage, inputs-as-data) → extended by Claude (loot weapons, respawn, shield) |
| `part1_engine/game.py` | One match: rules, players, modes, zone, network glue | **You** (game loop, `read_keys`, `update()`/`draw()` split, `get_state()`, host/join modes) → rebuilt by Claude for modes, zone, camera |
| `part1_engine/network.py` | Host + Client over TCP | **You** (`Host` and `Client` classes, Lessons 1–7) → extended by Claude (phones, seeds, bot slots, safety) |
| `part1_engine/app.py`, `bot.py`, `view.py`, `renderer.py`, `phone.py`, `phone_page.html` | Window/screens, bots, camera + 3/4 drawing, phone controller | Claude (at your request, after the project deadline) |
| `part2_combat/bullet.py`, `collisions.py`, `effects.py` | Original bullet, collision helpers, explosion rings | **Person 2 — Sanskar** (Raushan did the Part 2 skeleton). `rect_touches_wall` is still used by every tank |
| `part2_combat/weapons.py`, `fx.py` | Loot weapons + projectiles, particle effects | Claude |
| `part3_world/wall.py` | `Wall` class: rect, destructible, health, `hit()` | **Person 3** — still the base class of every map object |
| `part3_world/arena.py`, `powerup.py` | Original grid-map experiment, power-up plan | **Person 3** (kept for history, not used by the game now) |
| `part3_world/maps.py`, `loot.py` | Random map generator + drawing, loot crates | Claude |
| `part4_ui/scoreboard.py` | Kill counting, timer, winner | **Person 4 — Shivansh** — still used by every match |
| `part4_ui/hud.py`, `menu.py` | Original HUD + menu | **Person 4** (replaced by `game_hud.py` / `screens.py`, kept for history) |
| `part4_ui/assets.py`, `art.py`, `ui.py`, `screens.py`, `game_hud.py` | Asset loader, pixel art, UI kit, menus, HUD | Claude (assets.py follows Person 4's original spec) |
| `shared/settings.py` | Every number in one place | Person 1 started it, **Person 4** owned it; new values added later |
| `shared/resources.py` | Finds files inside the packaged app + saves your options | Claude |
| `tools/make_audio.py` | Synthesizer that makes all sounds + music | Claude |
| `build_app.sh` | Builds `Drift Tank.app` with PyInstaller | Claude |

> Your teammates' original files (`bullet.py`, `effects.py`, `hud.py`, `menu.py`, `arena.py`) are
> **kept on purpose** — they show the project's history and were the base the new versions grew from.

---

## 5. One frame of the game, step by step

The game runs **60 frames per second**. Here is everything that happens in one frame:

```
App.run()  (part1_engine/app.py)
 │
 ├─ 1. EVENTS        pygame.event.get() → screen.handle_event()   (mouse, keys, ESC, F11)
 │
 ├─ 2. UPDATE        Game.step()
 │     ├─ collect_inputs()   keyboard+mouse → read_keys() ; bots → Bot.think() ; network → host.inputs
 │     ├─ update(all_inputs)       ◄── ONLY on the host / local game (the rules)
 │     │     ├─ zone shrinks, crates drop
 │     │     ├─ every tank: tank.move(inputs, walls) ; if shoot → tank.shoot() → new Projectiles
 │     │     ├─ projectiles fly, hit walls / tanks, explode (splash damage, barrels chain-react)
 │     │     └─ check winner
 │     ├─ host: network.send_state(get_state())      → every laptop
 │     ├─ join: apply_state(latest_state)            ← from the host
 │     ├─ present_events()   explosions, sounds, kill feed (from "events" list)
 │     └─ update_camera()    follow your tank (zoom out if several players share the screen)
 │
 └─ 3. DRAW          Game.draw()
       ├─ renderer.draw_world()   floor → zone → shadows → objects/tanks/crates/bullets sorted by depth
       │                          → particles → health bars → colour grade → scale up 2x (pixel art)
       └─ game_hud.draw()         player list, minimap, timer/score, kill feed, pause/game-over
```

---

## 6. Every file explained

### `main.py`
Tiny on purpose. Reads the command line (`local`, `host`, `join <IP>`) and starts `App`.

### `part1_engine/app.py` — the window and the screens
- Creates the 1280×720 window with `pygame.SCALED | RESIZABLE` (it scales to any window/fullscreen).
- Shows one **screen** at a time. Every screen (menu, map select, a Game…) has the same 3 methods:
  `handle_event(event)`, `update_screen()`, `draw(surface)`. That's why switching screens is just `app.go(new_screen)`.
- `start_game(...)` builds a `Game`; if hosting/joining fails it returns a friendly error message.
- `update_music()` plays menu music in menus, battle music in a match, a jingle at the end.

### `part1_engine/game.py` — one match
The heart of the game. Important parts:

| Method | What it does |
|---|---|
| `__init__` | Sets up the mode (`local` / `host` / `join` / `demo`), rules (`br` / `tdm`), map, tanks, bots |
| `read_keys(keys, controls)` | **Your B1 function.** Turns pressed keys into the inputs dictionary |
| `mouse_aim()` | Converts the mouse position into a world point → `aim_angle` |
| `collect_inputs()` | Gathers inputs for every tank: you, bots, laptops, phones |
| `update(all_inputs)` | **Your B2 split.** The rules: movement, shooting, zone damage, loot, winner |
| `update_projectiles()` / `explode()` / `damage_tank()` | Bullets hitting things, splash damage, kills |
| `plan_zone()` / `update_zone()` | Battleground: pre-plans 6 zone stages, then shrinks the circle over time |
| `get_state()` | **Your B3 function.** The whole match as a dictionary (sent to clients) |
| `apply_state(state)` | Client side: makes the local copy look exactly like the host's |
| `sync_players()` | Host: adds a tank when a laptop/phone joins, removes it when they leave |
| `step()` | One frame (see section 5) |

### `part1_engine/tank.py` — the Tank
- Stores position (`pos`, a float `Vector2`), collision `rect`, `hull_angle`, `barrel_angle`, `health`, `weapon`, `ammo`.
- `move(inputs, walls, bounds, on_ice)`:
  1. reads `move_x/move_y` → which way to steer
  2. turns the **barrel** (aim angle or Q/E keys)
  3. turns the **hull** toward the steering direction using the *shortest turn* formula `(target - current + 180) % 360 - 180`
  4. **drift**: `velocity += (drive - velocity) * grip` — velocity only slowly follows the hull (low grip on ice = big slides)
  5. moves **X then Y separately**, undoing an axis if it hits a wall (so you slide along walls)
- `shoot(now)` → returns a list of Projectiles (or `[]` if no weapon / cooling down). Uses ammo; at 0 the weapon is gone.
- `take_damage()` → returns `True` if the tank died.

### `part1_engine/bot.py` — computer players
A bot returns the **same inputs dictionary** a player would. Its brain:
get back into the zone → no weapon? drive to a crate → otherwise pick the nearest enemy, keep a good distance,
lead the target, and shoot only if no wall blocks the line (`rect.clipline`). Stuck? reverse in a random direction.

### `part1_engine/view.py` — camera + 3/4 drawing maths
- `YS = 0.75` — the floor is squashed to 75% height. That's the "tilted camera".
- `Camera.to_view(x, y, z)` → `(x - left, y * 0.75 - z - top)`. `z` = height, so things with height are drawn higher.
- `Camera.follow(points)` keeps all followed tanks on screen and zooms out (down to ~1×) when they're far apart.
- **Sprite stacking**: a 3D tank is cut into 1-pixel slices (`build_slices`); `StackModel.render(angle)` rotates each
  slice, squashes it, and stacks them 1 px apart → a chunky 3D tank at any angle (cached in 5° steps).
- `outlined()` adds the dark 1-px pixel-art outline.

### `part1_engine/renderer.py` — draws the battle
Draws onto a **small** surface (1 world pixel = 1 pixel), then scales it up 2× with no smoothing → crisp pixel art.
Order: floor → zone tint → shadows → everything **sorted by depth (y)** so a tank behind a wall is hidden by it →
particles → health bars, names, crown on the leader → colour grade + vignette.

### `part1_engine/network.py` — Host + Client (see section 7)
### `part1_engine/phone.py` + `phone_page.html` — phones as controllers (see section 7)

### `part2_combat/weapons.py`
- `WEAPONS` — a dictionary of stats per weapon (ammo, cooldown, damage, speed, spread, pellets, range, splash, bounces, pierce).
- `Projectile.update(walls, bounds)` moves in small steps (so fast shots can't skip through walls), bounces or stops.
- `fire()` creates one projectile per pellet with random spread. `splash_targets()` = who an explosion hurts (less at the edge, never teammates).

### `part2_combat/fx.py` — effects
The game makes **events** (small dicts like `{"t": "boom", "x": 300, "y": 220, "s": 1.5}`).
`FX.event()` turns each into particles + a sound. Particles have a height `z` and gravity, so debris flies up and bounces.
Explosions are cartoon puffs that change colour white → yellow → orange → grey smoke.

### `part2_combat/collisions.py` (Sanskar)
`rect_touches_wall(rect, walls)` — used by every tank to block movement. (`bullets_vs_walls/tanks` were the original bullet rules.)

### `part3_world/maps.py` — random maps
- `generate(theme, seed)` builds **one quarter** (24×18 tiles): organic cliff edge, spawn, lakes/chasms,
  winding roads (Catmull-Rom curves) with bridges, then theme clusters (rock formations, forests, ruined walls,
  barricades, crates, barrels), loot spots, and a check that the spawn can reach the middle.
  The quarter is **mirrored** into the 48×36 map → every spawn is identical = fair.
- Same **seed** = same map. The host sends the seed, so every laptop builds the identical map.
- `MapObject` **extends Person 3's `Wall`** (rect, destructible, health, `hit()`), adding kind, explosive, height.
- `bake()` draws the whole floor once (ground texture, grass, roads, ice, water, cliffs, decorations) — fast to reuse every frame.

### `part3_world/loot.py`
`LootManager.update()` drops crates (inside the zone in Battleground), lets tanks pick them up, and returns events.
Crates fall for 0.75 s before they can be collected.

### `part4_ui/` — everything you see and hear
| File | What it does |
|---|---|
| `assets.py` | Loads images, fonts, sounds once; `play_sound(name)`, `play_music(name)` |
| `art.py` | **All pixel art drawn in code**: tanks, walls, barricades, crates, barrels, rocks, trees, bushes, loot boxes, weapon icons |
| `ui.py` | Panels, text, buttons, text input, the colour palette |
| `screens.py` | Intro, main menu (with a live bot battle behind it), map select, join, settings, help |
| `game_hud.py` | Player list, minimap, timer/score, zone warning, kill feed, pause + game-over screens |
| `scoreboard.py` | **Shivansh's** kill counter + timer + winner — used by every match |

### `shared/settings.py` / `shared/resources.py`
All tuning numbers live in `Settings` (speeds, zone stages, kill limit, ports...).
`resource_path()` finds files both from source and inside the packaged app; `load_prefs/save_prefs` remember your options.

---

## 7. The multiplayer lesson

This is the path we followed, lesson by lesson. Each step builds on the last.

### Lesson 1 — Sockets (`practice: net1`)
A **socket** is a phone line between two programs. TCP (`SOCK_STREAM`) guarantees bytes arrive in order.
```python
server.bind(("0.0.0.0", 5757)); server.listen(); conn, address = server.accept()   # host waits
client.connect((host_ip, 5757))                                                     # client calls
conn.sendall("hi".encode());  data = conn.recv(1024).decode()                       # bytes both ways
```
`0.0.0.0` = "accept calls from any network card". Sockets carry **bytes**, so text needs `.encode()` / `.decode()`.

### Lesson 2 — Two computers (`net2`)
The host's address on the Wi-Fi is found with a trick: "connect" a UDP socket to 8.8.8.8 (nothing is sent)
and ask which local IP it would use → `get_lan_ip()`. College Wi-Fi often blocks device-to-device traffic → use a phone hotspot.

### Lesson 3 — Messages as JSON lines (`net3`)
TCP is a **stream**, not separate messages: 3 sends can arrive glued together or cut in half.
Fix: every message is one JSON dict + `"\n"`. The receiver keeps a **buffer** and only processes complete lines:
```python
buffer += chunk
while "\n" in buffer:
    line, buffer = buffer.split("\n", 1)
    message = json.loads(line)
```
An empty `recv()` means the other side disconnected.

### Lesson 4 — Threads (`net4`)
`recv()` **waits** until data arrives — that would freeze the game. So receiving runs on a background **thread**
(the "waiter"), while the main thread keeps running the game (the "chef"). They share a dictionary (`latest_inputs`).

### Lesson 5 — Many players (`net5`)
`accept()` also runs on its own thread, in a loop. Each newcomer gets a **player id** (in a `welcome` message)
and their own receiving thread, which stores `inputs[player_id]`. When they leave, their id is freed.

### Lesson 6 — Getting the game ready (B1, B2, B3 — you wrote these)
- **B1** `tank.move(inputs)` — tanks read a dictionary, not the keyboard.
- **B2** `update()` (rules) split from `draw()` (pictures) — a client can draw without running the rules.
- **B3** `get_state()` — the whole match as a dictionary of plain numbers (no images!) that JSON can send.

### Lesson 7 — Host + Client classes (you wrote these)
`Host` = Lesson 5 turned into a class (`accept_players`, `handle_client`, `send_state`).
`Client` = connect, read the welcome, a thread that keeps `latest_state` up to date, `send_inputs()`.

### Lesson 8 — The finished system (how it works now)

```
   LAPTOP 2 (Client)                         LAPTOP 1 (Host)                            PHONE
   ─────────────────                         ───────────────                            ─────
   connect ───────── TCP :5757 ───────────►  accept_players()  ◄── WebSocket :8080 ──  opens http://IP:8080
   ◄── {"type":"welcome","player_id":3,                                                 ◄── {"t":"welcome","id":4}
        "map_id":"canyon","seed":5749,
        "rules":"br"}
   builds the SAME map from the seed
                                                                                          every 33 ms:
   every frame:                              every frame:                                {"mx","my","ax","ay","fire"}
   send_inputs({move_x, move_y,    ───────►  host.inputs[3] = ...   ◄────────────────── phone_to_inputs() → host.inputs[4]
               aim_angle, shoot})            update(all_inputs)   (THE RULES)
                                             send_state(get_state())
   apply_state(state)  ◄───────────────────  {"type":"state", tanks, projectiles,
   draw it                                     crates, zone, kills, "ev":[events]...}
   play the events (explosions, sounds)      every 6 frames: send_phone_status() ─────►  health, weapon, ammo,
                                                                                          vibrate when hit
```

Key details that make it solid:
| Problem | Solution |
|---|---|
| A state could arrive before the welcome | Host sends `welcome` **first**, then adds the player to the send list |
| A client might miss a frame and lose an explosion | Events are collected in `client.events` by the receiving thread, never overwritten |
| Everyone must see the same random map | The host sends the **seed**; `GameMap(id, seed)` always builds the same map |
| Bots and humans share 4 slots | `Host.reserved` = bot ids; humans get the lowest free id 2–4; full → `{"type":"full"}` |
| A laptop or phone vanishes | `recv()` returns `""` or errors → `release_id()` → `sync_players()` removes its tank |
| Small messages felt laggy | `TCP_NODELAY` sends each message immediately |
| Browsers can't open raw TCP sockets | Phones use a **WebSocket**: we wrote the handshake (SHA-1 of key + magic string) and frame decoding by hand in `phone.py`, so no extra packages are needed |

**Why the host is the boss:** if each computer ran its own rules, tiny timing differences would make them
disagree ("I hit you!" / "No you didn't!"). With one authority there is only one truth.
**The cost:** clients see the game a few milliseconds late — fine on Wi-Fi.

---

## 8. Art, sound, fonts and colours

| What | Where it comes from |
|---|---|
| Pixel art (tanks, walls, rocks, trees, crates, UI icons) | **Drawn in code** in `part4_ui/art.py` — light from the top-left, dark outlines, texture detail |
| Some extra sound variations + the tiny pixel label font | **Kenney.nl**, CC0 (public domain) — see `part4_ui/assets/CREDITS.md` |
| Fonts | **Bungee** (titles) + **Pixelify Sans** (UI/HUD) — Google Fonts, SIL Open Font License |
| Sound effects + music | **Synthesized** by `tools/make_audio.py` (oscillators, noise, envelopes, filters — no samples) |
| Hero image + app icon | AI-generated for this project |

**Colour theory used:**
- **UI:** a *complementary* pair — cool deep **navy** for backgrounds vs warm **amber** for important things (buttons, titles) = maximum contrast where your eye should go. A *split-complementary* pair for meaning: **coral** = danger/enemies, **teal** = good/you.
- **Teams:** red vs blue — opposite sides of the colour wheel, impossible to confuse.
- **Colour grading per map** (like a film colourist): warm golden-hour canyon, fresh green valley, cold blue frost, gritty desaturated scrapyard with teal shadows. Plus a soft **vignette** that pulls the eye to the centre.

---

## 9. Cheat sheet: explaining the project

If someone looks at the repo, walk them through it in this order:

1. **"It's a 4-player pixel-art tank battle with loot weapons, drifting, random maps and LAN multiplayer — phones can be controllers."**
2. **"The world is flat; only the drawing is tilted."** Show `view.py` → `to_view()`.
3. **"Tanks are controlled by data, not the keyboard."** Show `game.read_keys()` and `tank.move(inputs)`. That's why bots, laptops and phones all work.
4. **"The host runs the rules, clients just draw."** Show `game.step()`: host → `update()` + `send_state(get_state())`; client → `apply_state()`.
5. **"Messages are JSON lines over TCP, received on threads."** Show `Client.read_message()` and the buffer.
6. **"Maps are generated from a seed and mirrored, so they're random but fair, and identical on every laptop."** Show `maps.generate()`.
7. **"Everything visible is drawn in code and scaled up 2×."** Show `art.py` and the end of `renderer.draw_world()`.
8. **Team credit:** Part 1 engine + networking basics (me), Part 2 combat foundations (Sanskar/Raushan), Part 3 walls/world foundation, Part 4 scoreboard/settings/UI foundation (Shivansh) — later expanded into the full game.

---

## 10. Glossary

| Word | Meaning |
|---|---|
| **Frame** | One update + one picture. 60 per second. |
| **Vector2** | An (x, y) pair with maths built in: length, normalize, rotate, angle_to. |
| **Rect** | A rectangle (x, y, width, height). `colliderect` = do two rects overlap? |
| **Host-authoritative** | Only the host decides what happens; others follow its state. |
| **Socket / TCP** | A two-way connection between programs; TCP delivers bytes in order. |
| **JSON** | Text format for dictionaries/lists, so they can be sent as bytes. |
| **Thread** | A second worker in the same program (used to wait for network data without freezing). |
| **WebSocket** | A socket browsers are allowed to use (how phones talk to the host). |
| **Seed** | A number that makes "random" repeatable: same seed → same map. |
| **Sprite stacking** | Drawing a 3D object as a stack of rotated 2D slices. |
| **Depth sorting** | Drawing things further back first, so closer things cover them. |
| **Event** | A small dict describing something that happened (shot, explosion, pickup) — used for effects and sounds. |
| **Colour grading** | Tinting the final picture to set a mood (warm, cold, gritty). |
