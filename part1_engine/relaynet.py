# =====================================================================
#  part1_engine/relaynet.py  —  ONLINE ROOMS FOR THE MAC / WINDOWS APP
# =====================================================================
# Same idea as webnet.py (phone/web), but for the desktop app, which has
# real threads and sockets:
#
#   RelayHost   : connects to  wss://<relay>/host  and gets a 5-digit room code.
#                 Same interface as network.Host, so game.py doesn't care.
#   RelayClient : connects to  wss://<relay>/join/<code>.
#                 Same interface as network.Client.
#
# The relay (server/src/index.js) only forwards messages; the host's
# computer still runs the whole match. Because desktop, phone and web
# players all talk to the same relay, they can share one room.
#
# A WebSocket is "HTTP that turns into a two-way pipe". We speak the tiny
# part of the protocol we need by hand (like phone.py does for the server
# side): one handshake, then small frames. Over the internet it runs inside
# TLS (wss://), exactly like an https web page.
# =====================================================================
import base64
import json
import os
import socket
import ssl
import struct
import threading
import time
from urllib.parse import urlparse

from shared.settings import Settings

MAX_PLAYERS = 4


def _ssl_context():
    try:
        import certifi                       # up-to-date certificate list (python.org Python has none)
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


class WebSocketConnection:
    """A minimal WebSocket client (text messages only)."""

    def __init__(self, url, timeout=8):
        u = urlparse(url)
        secure = u.scheme == "wss"
        port = u.port or (443 if secure else 80)
        path = (u.path or "/") + ("?" + u.query if u.query else "")
        raw = socket.create_connection((u.hostname, port), timeout=timeout)
        raw.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock = _ssl_context().wrap_socket(raw, server_hostname=u.hostname) if secure else raw
        key = base64.b64encode(os.urandom(16)).decode()
        host = u.hostname + ("" if u.port is None else ":%d" % u.port)
        self.sock.sendall(("GET %s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                           "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n" % (path, host, key)).encode())
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("The online server closed the connection.")
            head += chunk
        head, self.buffer = head.split(b"\r\n\r\n", 1)
        status = head.split(b"\r\n")[0].decode(errors="ignore")
        if " 101 " not in status + " ":
            code = status.split(" ")[1] if " " in status else "?"
            raise ConnectionError({"404": "No room with that code.", "403": "That room is full."}.get(
                code, "The online server said no (%s)." % code))
        self.sock.settimeout(None)
        self.send_lock = threading.Lock()

    def _read(self, n):
        while len(self.buffer) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("closed")
            self.buffer += chunk
        data, self.buffer = self.buffer[:n], self.buffer[n:]
        return data

    def _send_frame(self, opcode, payload):
        mask = os.urandom(4)                          # clients must mask what they send
        n = len(payload)
        header = bytearray([0x80 | opcode])
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header.append(0x80 | 126)
            header += struct.pack(">H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", n)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        with self.send_lock:
            self.sock.sendall(bytes(header) + mask + masked)

    def send_text(self, text):
        self._send_frame(0x1, text.encode())

    def recv_text(self):
        """Next text message, or None when the connection closes."""
        while True:
            b0, b1 = self._read(2)
            opcode, length = b0 & 0x0F, b1 & 0x7F
            if length == 126:
                length = struct.unpack(">H", self._read(2))[0]
            elif length == 127:
                length = struct.unpack(">Q", self._read(8))[0]
            data = self._read(length)
            if opcode == 0x8:
                return None
            if opcode == 0x9:
                self._send_frame(0xA, data)           # ping -> pong
                continue
            if opcode in (0x1, 0x0):
                return data.decode(errors="ignore")

    def close(self):
        try:
            self._send_frame(0x8, b"")
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass


class RelayHost:
    """Host an internet room. Same interface as network.Host."""
    online = True

    def __init__(self, map_id, rules="br", reserved=None, seed=None):
        self.map_id, self.rules, self.seed = map_id, rules, seed
        self.reserved = set(reserved or ())
        self.inputs, self.names = {}, {}
        self.phones = {}                    # (no controller pages through the relay)
        self.players = {}                   # player_id -> relay connection id
        self.conn_player = {}
        self.lock = threading.Lock()
        self.error = None
        self.frame = 0
        self.ws = WebSocketConnection(Settings.RELAY_URL + "/host")
        hello = json.loads(self.ws.recv_text() or "{}")
        self.ip = hello.get("code", "")      # shown as the ROOM CODE
        threading.Thread(target=self.receive, daemon=True).start()

    def connected_ids(self):
        with self.lock:
            return set(self.players)

    def claim_id(self):
        for candidate in range(2, MAX_PLAYERS + 1):
            if candidate not in self.reserved and candidate not in self.players:
                return candidate
        return None

    def release_id(self, player_id):
        with self.lock:
            self.players.pop(player_id, None)
            self.inputs.pop(player_id, None)
            self.names.pop(player_id, None)

    def _to(self, conn_ids, text):
        try:
            self.ws.send_text(json.dumps({"to": conn_ids, "d": text}))
        except OSError:
            self.error = "Lost the online server."

    def receive(self):
        while True:
            try:
                text = self.ws.recv_text()
            except (OSError, ConnectionError, ValueError):
                text = None
            if text is None:
                self.error = "Lost the online server."
                return
            try:
                m = json.loads(text)
            except ValueError:
                continue
            kind = m.get("k")
            if kind == "join":
                conn_id = m["id"]
                with self.lock:
                    player_id = self.claim_id()
                    if player_id is not None:
                        self.players[player_id] = conn_id
                        self.conn_player[conn_id] = player_id
                        self.names[player_id] = "P%d" % player_id
                if player_id is None:
                    self._to([conn_id], json.dumps({"type": "full"}))
                    continue
                self._to([conn_id], json.dumps({"type": "welcome", "player_id": player_id, "map_id": self.map_id,
                                                "seed": self.seed, "rules": self.rules}))
            elif kind == "msg":
                player_id = self.conn_player.get(m.get("id"))
                if player_id is None:
                    continue
                try:
                    message = json.loads(m.get("d", ""))
                except ValueError:
                    continue
                if message.get("name"):
                    self.names[player_id] = str(message["name"])[:12]
                self.inputs[player_id] = message
            elif kind == "leave":
                player_id = self.conn_player.pop(m.get("id"), None)
                if player_id is not None:
                    self.release_id(player_id)

    def send_state(self, state):
        self.frame += 1
        if self.frame % 2:                  # 30 updates a second is plenty online
            return
        with self.lock:
            conn_ids = list(self.players.values())
        if conn_ids:
            self._to(conn_ids, json.dumps(state, separators=(",", ":")))

    def send_phone_status(self, statuses):
        pass

    def phone_url(self):
        return None

    def close(self):
        self.ws.close()


class RelayClient:
    """Join an internet room by its code. Same interface as network.Client."""

    def __init__(self, code, name=""):
        self.name = name
        self.latest_state = None
        self.events = []
        self.lock = threading.Lock()
        self.connected = True
        self.last_sent, self.last_sent_ms = None, 0
        self.ws = WebSocketConnection("%s/join/%s?kind=game" % (Settings.RELAY_URL, code))
        self.ws.sock.settimeout(8)
        welcome = json.loads(self.ws.recv_text() or "{}")
        self.ws.sock.settimeout(None)
        if welcome.get("type") != "welcome":
            raise ConnectionError("The game is full (max %d players)." % MAX_PLAYERS)
        self.player_id = welcome["player_id"]
        self.map_id, self.seed, self.rules = welcome.get("map_id"), welcome.get("seed"), welcome.get("rules")
        threading.Thread(target=self.receive, daemon=True).start()

    def receive(self):
        while True:
            try:
                text = self.ws.recv_text()
            except (OSError, ConnectionError, ValueError):
                text = None
            if text is None:
                break
            try:
                message = json.loads(text)
            except ValueError:
                continue
            if message.get("type") == "state":
                with self.lock:
                    self.events.extend(message.get("ev", []))
                    self.latest_state = message
        self.connected = False

    def take_events(self):
        with self.lock:
            events, self.events = self.events, []
        return events

    def send_inputs(self, inputs):
        if self.name:
            inputs = dict(inputs, name=self.name)
        text = json.dumps(inputs, separators=(",", ":"))
        now = time.monotonic()
        if text == self.last_sent and now - self.last_sent_ms < 0.2:   # only send changes (+5x a second)
            return
        self.last_sent, self.last_sent_ms = text, now
        try:
            self.ws.send_text(text)
        except OSError:
            self.connected = False

    def close(self):
        self.ws.close()
