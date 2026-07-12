import json
import socket
import threading
import time


DISCOVERY_PORT = 5556
DISCOVERY_REQUEST = b"GRID_EXPLORER_DISCOVER_V1"


class LobbyDiscoveryResponder:
    def __init__(self, state_provider, port=DISCOVERY_PORT):
        self.state_provider = state_provider
        self.port = port
        self.running = False
        self.sock = None

    def start(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind(("", self.port))
            self.sock.settimeout(0.5)
            self.running = True
            threading.Thread(target=self._run, daemon=True).start()
        except OSError:
            self.stop()

    def _run(self):
        while self.running:
            try:
                data, address = self.sock.recvfrom(1024)
                if data != DISCOVERY_REQUEST:
                    continue
                payload = self.state_provider()
                payload["type"] = "grid_explorer_lobby"
                payload["host"] = socket.gethostname()
                self.sock.sendto(json.dumps(payload).encode("utf-8"), address)
            except socket.timeout:
                continue
            except OSError:
                break

    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None


def discover_games(timeout=1.2, port=DISCOVERY_PORT):
    games = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("", 0))
        sock.settimeout(0.15)

        targets = {"255.255.255.255"}
        try:
            for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
                parts = ip.split(".")
                if len(parts) == 4 and not ip.startswith("127."):
                    targets.add(".".join(parts[:3] + ["255"]))
        except OSError:
            pass

        for target in targets:
            try:
                sock.sendto(DISCOVERY_REQUEST, (target, port))
            except OSError:
                pass

        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                data, address = sock.recvfrom(4096)
                payload = json.loads(data.decode("utf-8"))
                if payload.get("type") == "grid_explorer_lobby":
                    payload["ip"] = address[0]
                    games[address[0]] = payload
            except socket.timeout:
                continue
            except (OSError, ValueError, UnicodeDecodeError):
                continue
    finally:
        sock.close()
    return list(games.values())
