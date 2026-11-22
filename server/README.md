# Drift Tank relay (online rooms)

Browsers can't open network ports, so web / phone players meet through this tiny
server. The **host's device still runs the game** (same as LAN play); the relay only
passes messages between the host and the players in a room with a 5-digit code.

- `src/index.js` — the whole server (a Cloudflare Worker + one Durable Object per room)
- Messages are the same events the Android plugin produces (`join`, `msg`, `leave`), so the
  Python side is shared: `part1_engine/webnet.py` (`WebHost(online=True)`, `WebClient`).

```bash
cd server
npm install
npx wrangler dev        # test locally: open the game with  ?relay=ws://127.0.0.1:8787
npx wrangler login      # once
npx wrangler deploy     # prints the address -> put it in shared/settings.py RELAY_URL (wss://...)
```

Free plan: plenty for a small game. Inputs are only sent when they change and the host sends
30 updates a second, to keep the number of messages low.
