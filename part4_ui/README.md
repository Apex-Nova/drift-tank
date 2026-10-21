# Part 4 — UI (Menus, HUD, Scoreboard, Sound/Art, Settings, CI)

**You own:** `part4_ui/` (everything inside), `shared/settings.py`, `requirements.txt`,
`.gitignore`, `.github/workflows/ci.yml` (you create it — see `CI_SETUP.md`)
**You never edit:** `main.py`, `part1_*`, `part2_*`, `part3_*`

You make the game feel like a *finished game*: menus, scores, a winner,
sound, art — and you keep the shared settings and the team's CI.

## Study path (do them in order)
1. Python modules, constants, dictionaries → write `shared/settings.py` on Day 1
2. Pygame basics (do the "move a square" exercise)
3. `pygame.font` — drawing text, centering it
4. Game states (menu / playing / game over)
5. Classes with pure logic (scoreboard) + `get_ticks()` timers
6. Health bars with `draw.rect`
7. `pygame.mixer` sounds + music
8. Loading images, `convert_alpha`, `transform.scale`, `pathlib` paths
9. GitHub Actions basics

## Milestones
- [ ] Day 1: `shared/settings.py` pushed
- [ ] Scoreboard logic works in a practice script (no window needed)
- [ ] HUD shows health bars + kills
- [ ] Start screen + game-over "Player X wins"
- [ ] Sounds + sprite art
- [ ] CI checks every Pull Request
