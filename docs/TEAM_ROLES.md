# Team Roles — who codes where

Each person codes **only inside their own folder**. That's how 4 people work at the
same time without merge conflicts.

| Part | Folder | Person | Owns | One-line job |
|---|---|---|---|---|
| 1 — Engine | `part1_engine/` + `main.py` | _name_ | game loop, Tank | The hub that runs everything + the tanks |
| 2 — Combat | `part2_combat/` | _name_ | Bullet, collisions, effects | Shooting, hitting, damage |
| 3 — World | `part3_world/` | _name_ | Wall, arena, power-ups, maps | The battlefield |
| 4 — UI | `part4_ui/` + `shared/settings.py` | _name_ | menus, HUD, scoreboard, assets, CI | Makes it a finished game |

(Fill in names in your first PR.)

## Territory rules
1. **Your folder = your code.** Don't edit another part's files, even "just a small fix".
   Open an issue / message the owner instead.
2. **Need something from someone else's part?** Use the name from
   `docs/CLASS_CONTRACTS.md`, and test with a fake object until theirs is merged.
3. **Shared files:** `shared/settings.py` is owned by Person 4. `docs/` changes go
   in a PR everyone glances at.
4. **Learning from others' parts is encouraged** — read their merged code. If you
   want to re-write their part for practice, do it in `practice/<your-name>/`, never
   in their folder.

## Timeline
| Phase | Weeks | Goal | Who |
|---|---|---|---|
| 0 | 0 | Everyone learns basics; skeleton + settings pushed | All (P1 + P4 push) |
| 1 | 1–2 | One tank drives around a walled map | P1, P3 |
| 2 | 3–4 | Shooting; walls break | P2, P3 |
| 3 | 5–6 | 2 players, scoring, winner | P1, P4 |
| 4 | 7–8 | Power-ups, menus, sound, art, 3–4 players | everyone |
| 5 | later | Online play (sockets), AI tank | stretch |
