# =====================================================================
#  part1_engine/phone.py  —  PHONES AS GAME CONTROLLERS
# =====================================================================
#
# The host runs a tiny web server on port 8080. A phone on the same Wi-Fi
# opens  http://<host ip>:8080  and gets phone_page.html: a left joystick
# (drive), a right joystick (aim + fire) and a FIRE button.
#
# The page talks to the host through a WebSocket (a socket that browsers
# are allowed to use). Python's standard library has no WebSocket server,
# so the few lines of the protocol we need are written here by hand:
#   1. handshake: the browser sends a key, we answer with SHA1(key + magic)
#   2. frames: 2-byte header + (mask) + payload
# No extra packages needed, so it also works inside the packaged app.
# =====================================================================
import base64
import hashlib
import json
import socket
import struct
import threading

from pygame.math import Vector2

from shared.resources import resource_path
from shared.settings import Settings

MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def _recv_exact(conn, n):
    data = b""
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            raise ConnectionError("closed")
        data += chunk
    return data


class PhoneConnection:
    def __init__(self, conn):
        self.conn = conn
        self.send_lock = threading.Lock()

    def send(self, message):
        payload = json.dumps(message, separators=(",", ":")).encode()
        header = bytearray([0x81])
        n = len(payload)
        if n < 126:
            header.append(n)
        elif n < 65536:
            header.append(126)
            header += struct.pack(">H", n)
        else:
            header.append(127)
            header += struct.pack(">Q", n)
        try:
            with self.send_lock:
                self.conn.sendall(bytes(header) + payload)
        except OSError:
            pass

    def recv(self):
        """Returns the text of the next message, or None when the phone disconnects."""
        while True:
            b0, b1 = _recv_exact(self.conn, 2)
            opcode = b0 & 0x0F
            length = b1 & 0x7F
            if length == 126:
                length = struct.unpack(">H", _recv_exact(self.conn, 2))[0]
            elif length == 127:
                length = struct.unpack(">Q", _recv_exact(self.conn, 8))[0]
            mask = _recv_exact(self.conn, 4) if b1 & 0x80 else b"\0\0\0\0"
            data = bytearray(_recv_exact(self.conn, length))
            for i in range(length):
                data[i] ^= mask[i % 4]
            if opcode == 0x8:            # close
                return None
            if opcode == 0x9:            # ping -> pong
                with self.send_lock:
                    self.conn.sendall(bytes([0x8A, len(data)]) + bytes(data))
                continue
            if opcode in (0x1, 0x0):
                return data.decode(errors="ignore")


class PhoneServer:
    def __init__(self, host):
        self.host = host
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("0.0.0.0", Settings.PHONE_PORT))
        self.server.listen()
        with open(resource_path("part1_engine", "phone_page.html"), "rb") as f:
            self.page = f.read()
        threading.Thread(target=self.accept_loop, daemon=True).start()

    def close(self):
        try:
            self.server.close()
        except OSError:
            pass

    def accept_loop(self):
        while True:
            try:
                conn, _ = self.server.accept()
            except OSError:
                break
            threading.Thread(target=self.handle, args=(conn,), daemon=True).start()

    def handle(self, conn):
        try:
            request = b""
            while b"\r\n\r\n" not in request:
                chunk = conn.recv(2048)
                if not chunk:
                    conn.close()
                    return
                request += chunk
                if len(request) > 16000:
                    conn.close()
                    return
            head = request.split(b"\r\n\r\n", 1)[0].decode(errors="ignore")
            lines = head.split("\r\n")
            headers = {}
            for line in lines[1:]:
                if ":" in line:
                    k, v = line.split(":", 1)
                    headers[k.strip().lower()] = v.strip()
            path = lines[0].split(" ")[1] if lines[0].count(" ") >= 2 else "/"
            if headers.get("upgrade", "").lower() == "websocket":
                if path.startswith("/game"):
                    self.game_client(conn, headers)      # a phone running the game app itself
                else:
                    self.websocket(conn, headers)        # a phone used as a controller
            else:
                if path in ("/", "/index.html"):
                    body, ctype, status = self.page, "text/html; charset=utf-8", "200 OK"
                else:
                    body, ctype, status = b"not found", "text/plain", "404 Not Found"
                conn.sendall(("HTTP/1.1 %s\r\nContent-Type: %s\r\nContent-Length: %d\r\n"
                              "Cache-Control: no-store\r\nConnection: close\r\n\r\n" % (status, ctype, len(body))).encode() + body)
                conn.close()
        except (OSError, ConnectionError, IndexError):
            try:
                conn.close()
            except OSError:
                pass

    @staticmethod
    def handshake(conn, headers):
        key = headers.get("sec-websocket-key", "")
        accept = base64.b64encode(hashlib.sha1((key + MAGIC).encode()).digest()).decode()
        conn.sendall(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                      "Sec-WebSocket-Accept: %s\r\n\r\n" % accept).encode())
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        return PhoneConnection(conn)

    def game_client(self, conn, headers):
        """The phone/web version of the game joining as a full player (it draws the game itself).
        Same messages as a laptop (welcome, state, inputs), just inside WebSocket frames."""
        client = self.handshake(conn, headers)
        player_id = self.host.claim_id()
        if player_id is None:
            client.send({"type": "full"})
            conn.close()
            return
        client.send({"type": "welcome", "player_id": player_id, "map_id": self.host.map_id,
                     "seed": self.host.seed, "rules": self.host.rules})
        with self.host.lock:
            self.host.web_clients[player_id] = client
            self.host.names[player_id] = "P%d" % player_id
        try:
            while True:
                text = client.recv()
                if text is None:
                    break
                try:
                    message = json.loads(text)
                except ValueError:
                    continue
                if message.get("name"):
                    self.host.names[player_id] = str(message["name"])[:12]
                self.host.inputs[player_id] = message
        except (OSError, ConnectionError):
            pass
        self.host.release_id(player_id)
        try:
            conn.close()
        except OSError:
            pass

    def websocket(self, conn, headers):
        phone = self.handshake(conn, headers)
        player_id = self.host.claim_id()
        if player_id is None:
            phone.send({"t": "full"})
            conn.close()
            return
        with self.host.lock:
            self.host.phones[player_id] = phone
            self.host.names[player_id] = "P%d" % player_id
        phone.send({"t": "welcome", "id": player_id})
        try:
            while True:
                text = phone.recv()
                if text is None:
                    break
                try:
                    msg = json.loads(text)
                except ValueError:
                    continue
                if msg.get("name"):
                    self.host.names[player_id] = str(msg["name"])[:12]
                self.host.inputs[player_id] = phone_to_inputs(msg)
        except (OSError, ConnectionError):
            pass
        self.host.release_id(player_id)
        try:
            conn.close()
        except OSError:
            pass


def phone_to_inputs(msg):
    """Phone sticks -> the same inputs dict the keyboard makes (up on the stick = up on screen)."""
    mx, my = float(msg.get("mx", 0)), float(msg.get("my", 0))
    ax, ay = float(msg.get("ax", 0)), float(msg.get("ay", 0))
    move = Vector2(mx, my)
    if move.length() > 1:
        move = move.normalize()
    inputs = {"move_x": move.x, "move_y": move.y, "aim_angle": None, "shoot": bool(msg.get("fire"))}
    aim_strength = (ax * ax + ay * ay) ** 0.5
    if aim_strength > 0.25:
        inputs["aim_angle"] = Vector2(1, 0).angle_to(Vector2(ax, ay))
        if aim_strength > 0.8:
            inputs["shoot"] = True
    return inputs
