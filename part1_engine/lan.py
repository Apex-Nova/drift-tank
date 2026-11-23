# =====================================================================
#  part1_engine/lan.py  —  FIND GAMES ON THE SAME WI-FI (no IP typing)
# =====================================================================
# A host on Wi-Fi shouts "I'm hosting Drift Tank!" once a second as a UDP
# broadcast (a message sent to every device on the local network).
# The JOIN screen listens for those shouts and lists the games it hears;
# the joiner just taps one. The sender's address comes with the message,
# so nobody ever types or even sees an IP.
#
#   LanBeacon(info_fn)  host side: broadcasts info_fn() every second
#   LanFinder()         joiner side: .games() -> games heard in the last 3 s
#
# Some Wi-Fi (colleges, cafes) blocks devices from talking to each other.
# Then nothing shows up - that's what HOST ONLINE + room codes are for.
# =====================================================================
import json
import socket
import threading
import time

from shared.settings import Settings

MAGIC = b"DRIFTTANK1 "


def _broadcast_targets():
    """255.255.255.255, plus this network's own broadcast address (some routers only pass that)."""
    targets = ["255.255.255.255"]
    try:
        from part1_engine.network import get_lan_ip
        ip = get_lan_ip()
        if ip and not ip.startswith("127."):
            targets.append(ip.rsplit(".", 1)[0] + ".255")
    except OSError:
        pass
    return targets


class LanBeacon:
    """Host side: announce the game on the Wi-Fi once a second."""

    def __init__(self, info_fn):
        self.info_fn = info_fn          # returns a dict: name, players, rules, map ...
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        while self.running:
            try:
                info = dict(self.info_fn(), port=Settings.GAME_PORT, ws=Settings.PHONE_PORT)
                data = MAGIC + json.dumps(info, separators=(",", ":")).encode()
                for target in _broadcast_targets():
                    try:
                        self.sock.sendto(data, (target, Settings.LAN_FIND_PORT))
                    except OSError:
                        pass
            except Exception:
                pass
            time.sleep(1.0)

    def close(self):
        self.running = False
        try:
            self.sock.close()
        except OSError:
            pass


class LanFinder:
    """Joiner side: listen for hosts on the Wi-Fi."""

    def __init__(self):
        self.found = {}                 # ip -> (info dict, time last heard)
        self.lock = threading.Lock()
        self.running = True
        self.error = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):            # several games on one computer can all listen
            try:
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                pass
        try:
            self.sock.bind(("", Settings.LAN_FIND_PORT))
        except OSError as error:
            self.error = str(error)
            return
        self.sock.settimeout(0.5)
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        while self.running:
            try:
                data, (ip, _port) = self.sock.recvfrom(2048)
            except socket.timeout:
                continue
            except OSError:
                break
            if not data.startswith(MAGIC):
                continue
            try:
                info = json.loads(data[len(MAGIC):].decode())
            except ValueError:
                continue
            with self.lock:
                self.found[ip] = (info, time.monotonic())

    def games(self):
        """[(ip, info), ...] heard in the last 3 seconds, newest first."""
        now = time.monotonic()
        with self.lock:
            alive = [(ip, info, seen) for ip, (info, seen) in self.found.items() if now - seen < 3.0]
        alive.sort(key=lambda g: -g[2])
        return [(ip, info) for ip, info, _ in alive]

    def close(self):
        self.running = False
        try:
            self.sock.close()
        except OSError:
            pass
