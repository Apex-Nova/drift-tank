# 🎮 Drift Tank

A 3/4 top-down **pixel-art tank battle** built with Python and Pygame: loot crates with random
limited-ammo weapons, drifting tanks, randomly generated (but fair) maps, **Battleground** (shrinking
zone, last tank standing) and **Team Deathmatch** modes, bots, and **LAN multiplayer** — other laptops
join over Wi-Fi and **phones work as controllers** in the browser. Built by a team of 4 as a first
collaborative project.

> 📖 **New here? Read [docs/CODEBASE_GUIDE.md](docs/CODEBASE_GUIDE.md)** — the whole codebase,
> who built what, and how the multiplayer works, explained step by step.

## 🕹️ How to Play
- **Drive:** WASD or ARROW keys
- **Aim:** MOUSE, or Q/E or J/K to turn the barrel
- **Fire:** SPACE or LEFT CLICK · **Pause:** ESC · **Fullscreen:** F11
- **Phone / tablet:** left thumb stick drives, right thumb stick aims — push it to the edge to fire, **II** pauses
- Drive over loot crates to get a weapon. Ammo runs out — find the next crate!

**Versions:** Mac app · Windows app · Android app · Web (play in the browser, also on phones).
**Online play:**
- **Room codes (internet, anywhere):** in every version (Mac, Windows, Android, website), *HOST ONLINE* gives a
  5-digit code; friends tap *JOIN GAME* and type it. Messages go through a tiny relay server
  ([server/](server/)), the host's device runs the match.
- **Same Wi-Fi:** the Mac, Windows and Android apps can host on the local network; laptops join with
  the host's IP, phones can also open `http://<host IP>:8080` as a controller.
  (The website can't do Wi-Fi play: browsers block web pages from reaching devices on your network.)
- **Waiting room:** hosting opens a lobby. Players join and press *READY*; the host presses *START*.

```bash
.venv/bin/python main.py                    # menu
.venv/bin/python main.py join 192.168.1.5   # join a host on the same Wi-Fi
./build_app.sh                              # build "Drift Tank.app"
./build_web.sh serve                        # web version -> http://localhost:8000
```
Windows, Android and web builds are made by GitHub Actions: push a tag like `v1.1`
(see [.github/workflows/release.yml](.github/workflows/release.yml)).

## 📁 File Tree — 4 parts, one per person

```
drift-tank/
├── main.py                 ← PART 1  runs the game (tiny)
├── part1_engine/           ← PART 1  ENGINE   — game loop + tanks
│   ├── game.py
│   └── tank.py
├── part2_combat/           ← PART 2  COMBAT   — bullets, collisions, effects
│   ├── bullet.py
│   ├── collisions.py
│   └── effects.py
├── part3_world/            ← PART 3  WORLD    — walls, arena, power-ups
│   ├── wall.py
│   ├── arena.py
│   ├── powerup.py
│   └── maps/
├── part4_ui/               ← PART 4  UI       — menus, HUD, score, sound/art, CI
│   ├── menu.py
│   ├── hud.py
│   ├── scoreboard.py
│   ├── assets.py
│   ├── CI_SETUP.md
│   └── assets/ (images/, sounds/)
├── shared/settings.py      ← PART 4 owns, everyone imports
├── docs/
│   ├── CLASS_CONTRACTS.md  ← the agreed class shapes (read this!)
│   └── TEAM_ROLES.md       ← who owns what + territory rules
├── practice/               ← everyone's learning scripts (never imported by the game)
├── AI_TUTOR.md             ← rules for the AI that teaches you
├── CLAUDE.md / AGENTS.md   ← make AI tools load AI_TUTOR.md automatically
├── requirements.txt
└── .gitignore
```

Every `.py` file currently contains **only a description**: what it is, what to
study, and a checklist of what to build. You write the code.
Each part folder has a `README.md` with your study path and milestones — start there.

## 🚀 Getting Started (every team member)
1. Install [Python 3](https://python.org), [Git](https://git-scm.com), [VS Code](https://code.visualstudio.com)
2. Clone the repo and install:
   ```bash
   git clone https://github.com/OWNER/drift-tank.git
   cd drift-tank
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Open the folder in your editor, open your AI assistant, and say **"hi"**.
   It will ask which part you are and start teaching you (see `AI_TUTOR.md`).

## 🔄 Daily Git Workflow
```bash
git checkout main
git pull
git checkout -b part2/bullet-movement     # partN/what-you-are-doing
# ... code ONLY in your part's folder ...
git add part2_combat/
git commit -m "feat: bullets move in facing direction"
git push origin part2/bullet-movement
# → open a Pull Request → someone reviews → merge
```
**Golden rules:** never push straight to `main`; never edit another part's folder.

## 📝 Commit prefixes
`feat:` new feature · `fix:` bug fix · `docs:` documentation · `refactor:` cleanup · `assets:` art/sound
