# =====================================================================
#  part1_engine/network.py  —  LAN MULTIPLAYER (host + laptops + phones)
# =====================================================================
#
#  Host    : the laptop that runs the real game. Player 1 plays on it.
#  Client  : another laptop: sends its inputs, draws the host's state.
#  Phones  : open http://<host ip>:8080 in the browser -> joystick
#            controller page (see phone.py). They play on the host's screen.
#  Phone app / web version: connects to ws://<host ip>:8080/game and is a
#            full player like a laptop (same messages inside WebSocket frames).
#
#  Messages are JSON dicts, one per line ("\n" at the end) — Lesson 3.
#    host -> client : {"type": "welcome", "player_id": 2, "map_id": "dust_bowl"}
#                     {"type": "state", ...whole game..., "ev": [events]}
#    client -> host : {"move_x": .., "move_y": .., "aim_angle": .., "shoot": ..}
# =====================================================================
import json
import socket
import threading

from shared.settings import Settings

PORT = Settings.GAME_PORT
MAX_PLAYERS = 4             # the scoreboard and colors support players 1-4


def get_lan_ip():
    """The host's address on the Wi-Fi, e.g. 192.168.1.5 (what others type to join)."""
    finder = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        finder.connect(("8.8.8.8", 80))     # UDP: nothing is actually sent
        return finder.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        finder.close()


def send_message(conn, message):
    """Send one dict as one line of JSON."""
    conn.sendall((json.dumps(message, separators=(",", ":")) + "\n").encode())


class Host:
    def __init__(self, map_id, rules="br", reserved=None, seed=None, start_phones=True):
        self.map_id = map_id
        self.rules = rules
        self.seed = seed
        self.reserved = set(reserved or ())     # player numbers already used by bots
        self.inputs = {}        # player_id -> latest inputs from that laptop/phone
        self.conns = {}         # player_id -> laptop socket
        self.phones = {}        # player_id -> PhoneConnection (phone used as a controller)
        self.web_clients = {}   # player_id -> PhoneConnection (phone/web version of the game)
        self.names = {}         # player_id -> name shown in the HUD
        self.lock = threading.Lock()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("0.0.0.0", PORT))
        self.server.listen()
        threading.Thread(target=self.accept_players, daemon=True).start()
        self.host_name = "HOST"
        from part1_engine.lan import LanBeacon        # tell the Wi-Fi "a game is here" every second
        self.beacon = LanBeacon(lambda: {"name": self.host_name, "players": 1 + len(self.connected_ids()),
                                         "rules": self.rules, "map": self.map_id})
        self.phone_server = None
        if start_phones:
            from part1_engine.phone import PhoneServer
            try:
                self.phone_server = PhoneServer(self)
            except OSError as error:
                print("Phone controllers unavailable:", error)

    # ---------- player slots (shared by laptops and phones) ----------
    def connected_ids(self):
        with self.lock:
            return set(self.conns) | set(self.phones) | set(self.web_clients)

    def claim_id(self):
        """The host is player 1. Newcomers get the lowest free number 2-4."""
        with self.lock:
            for candidate in range(2, MAX_PLAYERS + 1):
                if candidate not in self.reserved and candidate not in self.conns \
                        and candidate not in self.phones and candidate not in self.web_clients:
                    return candidate
        return None

    def release_id(self, player_id):
        with self.lock:
            self.inputs.pop(player_id, None)
            self.conns.pop(player_id, None)
            self.phones.pop(player_id, None)
            self.web_clients.pop(player_id, None)
            self.names.pop(player_id, None)

    # ---------- laptops ----------
    def accept_players(self):
        while True:
            try:
                conn, address = self.server.accept()
            except OSError:
                break
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)   # send small messages right away
            player_id = self.claim_id()
            if player_id is None:
                try:
                    send_message(conn, {"type": "full"})
                except OSError:
                    pass
                conn.close()
                continue
            # Welcome FIRST, then add to conns: otherwise the game loop could send
            # a "state" before the "welcome" and confuse the client.
            try:
                send_message(conn, {"type": "welcome", "player_id": player_id, "map_id": self.map_id,
                                    "seed": self.seed, "rules": self.rules})
            except OSError:
                conn.close()
                continue
            with self.lock:
                self.conns[player_id] = conn
                self.names[player_id] = "P%d" % player_id
            threading.Thread(target=self.handle_client, args=(conn, player_id), daemon=True).start()

    def handle_client(self, conn, player_id):
        buffer = ""
        while True:
            try:
                chunk = conn.recv(4096).decode()
            except (OSError, UnicodeDecodeError):
                break
            if chunk == "":
                break
            buffer += chunk
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                try:
                    message = json.loads(line)
                except ValueError:
                    continue
                if "name" in message:
                    self.names[player_id] = str(message["name"])[:12]
                self.inputs[player_id] = message
        self.release_id(player_id)
        conn.close()

    def send_state(self, state):
        data = (json.dumps(state, separators=(",", ":")) + "\n").encode()
        for player_id, conn in list(self.conns.items()):
            try:
                conn.sendall(data)
            except OSError:
                self.release_id(player_id)
        for player_id, client in list(self.web_clients.items()):
            client.send(state)

    def send_phone_status(self, statuses):
        for player_id, phone in list(self.phones.items()):
            if player_id in statuses:
                phone.send(statuses[player_id])

    def phone_url(self):
        if self.phone_server is None:
            return None
        return "http://%s:%d" % (get_lan_ip(), Settings.PHONE_PORT)

    def close(self):
        self.beacon.close()
        try:
            self.server.close()
        except OSError:
            pass
        for conn in list(self.conns.values()):
            try:
                conn.close()
            except OSError:
                pass
        if self.phone_server is not None:
            self.phone_server.close()


class Client:
    def __init__(self, host_ip, name=""):
        self.latest_state = None     # newest game state from the host
        self.events = []             # effects (explosions...) not drawn yet
        self.lock = threading.Lock()
        self.connected = True
        self.buffer = ""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)      # don't hang forever if the IP is wrong
        self.sock.connect((host_ip, PORT))
        self.sock.settimeout(None)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        welcome = self.read_message()
        if welcome is None or welcome.get("type") != "welcome":
            raise ConnectionError("The game is full (max %d players)." % MAX_PLAYERS)
        self.player_id = welcome["player_id"]
        self.map_id = welcome.get("map_id")
        self.seed = welcome.get("seed")
        self.rules = welcome.get("rules")
        self.name = name
        threading.Thread(target=self.receive_states, daemon=True).start()

    def read_message(self):
        while "\n" not in self.buffer:
            chunk = self.sock.recv(65536).decode()
            if chunk == "":
                return None
            self.buffer += chunk
        line, self.buffer = self.buffer.split("\n", 1)
        return json.loads(line)

    def receive_states(self):
        while True:
            try:
                message = self.read_message()
            except (OSError, ValueError, UnicodeDecodeError):
                break
            if message is None:
                break
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
        try:
            send_message(self.sock, inputs)
        except OSError:
            self.connected = False

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass
