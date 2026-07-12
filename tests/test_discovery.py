import json
import socket
import time
import unittest

from gui.app import blend_color
from network.discovery import DISCOVERY_REQUEST, LobbyDiscoveryResponder


class DiscoveryTest(unittest.TestCase):
    def test_responder_advertises_lobby(self):
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
        probe.close()

        responder = LobbyDiscoveryResponder(
            lambda: {
                "port": 5555,
                "players": 1,
                "max_players": 4,
                "game_started": False,
            },
            port=port,
        )
        responder.start()
        self.addCleanup(responder.stop)

        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addCleanup(client.close)
        client.settimeout(1.0)
        time.sleep(0.02)
        client.sendto(DISCOVERY_REQUEST, ("127.0.0.1", port))
        data, _ = client.recvfrom(4096)
        payload = json.loads(data.decode("utf-8"))

        self.assertEqual(payload["type"], "grid_explorer_lobby")
        self.assertEqual(payload["players"], 1)
        self.assertFalse(payload["game_started"])

    def test_blended_canvas_color_uses_six_digit_hex(self):
        color = blend_color("#00d2ff")
        self.assertRegex(color, r"^#[0-9a-f]{6}$")
        self.assertNotEqual(color, "#00d2ff")


if __name__ == "__main__":
    unittest.main()
