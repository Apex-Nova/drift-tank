# =====================================================================
#  part1_engine/webnet.py  —  ONLINE PLAY FOR THE PHONE / WEB VERSION
# =====================================================================
# network.py uses threads and normal sockets. A browser (and the Android
# app, which is a browser inside an app) has neither, so here:
#
#   WebClient : joins a host with a WebSocket  ws://<host ip>:8080/game  (same Wi-Fi)
#               or an ONLINE room through the relay  wss://<relay>/join/<5-digit code>
#   WebHost   : online=True  -> hosts an internet room through the relay server
#               (server/src/index.js); players anywhere join with the room code.
#               online=False -> the Android app hosts on the Wi-Fi. A small native Android plugin
#               (android_app/native/DriftNetPlugin.java) opens the ports:
#                 5757  laptops   (same JSON lines as network.Host)
#                 8080  phones    (WebSocket: game app at /game, or the
#                                  controller page at /)
#
# The browser puts every network message in a queue (shared/web.py,
# dtNet). Python empties it once per frame with poll(). Same message
# format as network.py, so a laptop host and a phone host are the same
# to everyone.
# =====================================================================
import json

import pygame

from shared import web
from shared.resources import resource_path
from shared.settings import Settings
from part1_engine.phone import phone_to_inputs

MAX_PLAYERS = 4


def _queue():
    try:
        return json.loads(str(web.window().dtNet.poll()))
    except (ValueError, TypeError):
        return []


class WebClient:
    """Same interface as network.Client, but it fills in over a few frames (call poll())."""

    def __init__(self, host_ip, name=""):
        self.name = name
        self.player_id = None
        self.map_id = self.seed = self.rules = None
        self.latest_state = None
        self.events = []
        self.connected = True
        self.error = None
        self.online = web.is_room_code(host_ip)
        self.code = host_ip
        self.last_sent = None
        self.last_sent_ms = 0
        if self.online:
            url = "%s/join/%s?kind=game" % (web.relay_url(), host_ip)
        else:
            url = "ws://%s:%d/game" % (host_ip, Settings.PHONE_PORT)
        web.js("dtNet.connect(%s)" % web.js_str(url))

    @property
    def ready(self):
        return self.player_id is not None

    def poll(self):
        for item in _queue():
            kind = item.get("k")
            if kind == "msg":
                try:
                    message = json.loads(item.get("d", ""))
                except ValueError:
                    continue
                kind = message.get("type")
                if kind == "welcome":
                    self.player_id = message["player_id"]
                    self.map_id, self.seed, self.rules = message.get("map_id"), message.get("seed"), message.get("rules")
                elif kind == "state":
                    self.events.extend(message.get("ev", []))
                    self.latest_state = message
                elif kind == "full":
                    self.error = "The game is full (max %d players)." % MAX_PLAYERS
                    self.connected = False
            elif kind in ("error", "close"):
                self.connected = False
                if not self.ready and not self.error:
                    if self.online:
                        self.error = "No room %s. Check the code (or your internet)." % self.code
                    else:
                        self.error = "Could not connect. Same Wi-Fi? Right IP? Is the host running?"

    def take_events(self):
        events, self.events = self.events, []
        return events

    def send_inputs(self, inputs):
        if not self.name:
            self.name = web.cg_name()          # CrazyGames username (arrives a moment after start)
        if self.name:
            inputs = dict(inputs, name=self.name)
        text = json.dumps(inputs, separators=(",", ":"))
        if self.online:
            # online rooms: only send when something changed (or 5 times a second to stay in sync).
            # Every message costs a little on the free server plan.
            now = pygame.time.get_ticks()
            if text == self.last_sent and now - self.last_sent_ms < 200:
                return
            self.last_sent, self.last_sent_ms = text, now
        web.window().dtNet.send(text)

    def close(self):
        web.js("dtNet.close()")


class WebFinder:
    """Android app: games announced on the Wi-Fi (same interface as lan.LanFinder)."""

    def __init__(self):
        web.js("dtNet.find()")

    def games(self):
        try:
            rows = json.loads(str(web.js("dtNet.foundList()")))
        except ValueError:
            return []
        games = []
        for ip, info in rows:
            try:
                games.append((ip, json.loads(info)))
            except ValueError:
                pass
        return games

    def close(self):
        web.js("dtNet.stopFind()")


class _WebPhone:
    """A phone controller connected to the phone host (same send() as phone.PhoneConnection)."""

    def __init__(self, conn_id):
        self.conn_id = conn_id

    def send(self, message):
        web.window().dtNet.hostSend(self.conn_id, json.dumps(message, separators=(",", ":")))


class WebHost:
    """Same interface as network.Host, for the Android app. Call poll() every frame."""

    def __init__(self, map_id, rules="br", reserved=None, seed=None, online=False):
        self.map_id, self.rules, self.seed = map_id, rules, seed
        self.reserved = set(reserved or ())
        self.inputs = {}
        self.phones = {}            # player_id -> _WebPhone (controller page)
        self.players = {}           # player_id -> connection id (game app or laptop)
        self.conn_player = {}       # connection id -> player_id
        self.names = {}
        self.ip = ""
        self.error = None
        self.frame = 0
        self.online = online
        if online:
            web.js("dtNet.hostRelay(%s)" % web.js_str(web.relay_url()))
            return
        try:
            with open(resource_path("part1_engine", "phone_page.html"), encoding="utf-8") as f:
                page = f.read()
        except OSError:
            page = "<h1>Drift Tank</h1>"
        web.window().dtNet.host(page, Settings.GAME_PORT, Settings.PHONE_PORT)

    # ---------- slots ----------
    def connected_ids(self):
        return set(self.players) | set(self.phones)

    def claim_id(self):
        for candidate in range(2, MAX_PLAYERS + 1):
            if candidate not in self.reserved and candidate not in self.connected_ids():
                return candidate
        return None

    def release_id(self, player_id):
        self.inputs.pop(player_id, None)
        self.phones.pop(player_id, None)
        self.players.pop(player_id, None)
        self.names.pop(player_id, None)

    # ---------- messages from the native server ----------
    def poll(self):
        dt = web.window().dtNet
        self.frame_polls = getattr(self, "frame_polls", 0) + 1
        if not self.online and self.frame_polls % 60 == 1:     # announce the game on the Wi-Fi once a second
            dt.announce(json.dumps({"name": getattr(self, "host_name", "HOST"), "players": 1 + len(self.connected_ids()),
                                    "rules": self.rules, "map": self.map_id}))
        for item in _queue():
            kind = item.get("k")
            if kind == "hosting":
                self.ip = item.get("ip", "")
            elif kind == "hosterror":
                self.error = "Could not host: %s" % item.get("d", "")
            elif kind == "join":
                conn_id = item["id"]
                player_id = self.claim_id()
                if player_id is None:
                    dt.hostSend(conn_id, json.dumps({"type": "full", "t": "full"}))
                    dt.hostKick(conn_id)
                    continue
                self.conn_player[conn_id] = player_id
                self.names[player_id] = "P%d" % player_id
                if item.get("kind") == "phone":
                    self.phones[player_id] = _WebPhone(conn_id)
                    dt.hostSend(conn_id, json.dumps({"t": "welcome", "id": player_id}))
                else:
                    self.players[player_id] = conn_id
                    dt.hostSend(conn_id, json.dumps({"type": "welcome", "player_id": player_id, "map_id": self.map_id,
                                                     "seed": self.seed, "rules": self.rules}))
            elif kind == "msg":
                player_id = self.conn_player.get(item.get("id"))
                if player_id is None:
                    continue
                try:
                    message = json.loads(item.get("d", ""))
                except ValueError:
                    continue
                if message.get("name"):
                    self.names[player_id] = str(message["name"])[:12]
                self.inputs[player_id] = phone_to_inputs(message) if player_id in self.phones else message
            elif kind == "leave":
                player_id = self.conn_player.pop(item.get("id"), None)
                if player_id is not None:
                    self.release_id(player_id)

    # ---------- to everyone ----------
    def send_state(self, state):
        self.frame += 1
        if not self.players or self.frame % 2:      # 30 updates a second is plenty and saves the phone's CPU
            return
        ids = json.dumps(list(self.players.values()))
        web.window().dtNet.hostBroadcast(ids, json.dumps(state, separators=(",", ":")))

    def send_phone_status(self, statuses):
        for player_id, phone in list(self.phones.items()):
            if player_id in statuses:
                phone.send(statuses[player_id])

    def phone_url(self):
        if self.online:
            return None
        return "http://%s:%d" % (self.ip, Settings.PHONE_PORT) if self.ip else None

    def close(self):
        web.js("dtNet.hostStop()")
