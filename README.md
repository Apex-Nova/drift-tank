# 🎮 Drift Tank

A local-multiplayer tank game built with Python and Pygame. 2–4 players share one
keyboard, drive tanks around a walled arena, shoot each other, blow up walls, grab
power-ups. Last tank standing wins. Built by a team of 4 as a first collaborative
project — **and built to learn**: we write the code ourselves and use AI only as a tutor.

## 🕹️ How to Play
- **Player 1:** WASD to move, SPACE to shoot
- **Player 2:** Arrow keys to move, ENTER to shoot
- Last tank alive (or most kills when the timer ends) wins.

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
