import unittest
from unittest.mock import patch

from gui.app import GridGameApp
from network.server import GridServer


class MultiplayerRulesTest(unittest.TestCase):
    def make_server(self):
        server = GridServer(max_players=2)
        server.game_started = True
        server.players = {
            1: {"r": 0, "c": 0, "color": "#00d2ff", "ip": "one", "moves": 0},
            2: {"r": 0, "c": 1, "color": "#ff4d4d", "ip": "two", "moves": 0},
        }
        server.player_visited = {1: {(0, 0)}, 2: {(0, 1)}}
        server.player_items = {1: set(), 2: set()}
        server.player_collected = {1: {}, 2: {}}
        server.player_item_keys = {1: {}, 2: {}}
        server.player_powerups = {1: [None, None, None], 2: [None, None, None]}
        server.broadcast_state = lambda: None
        return server

    @patch("network.server.play_sound", lambda *_: None)
    def test_players_can_cross_other_trails_and_positions(self):
        server = self.make_server()
        server.process_client_move(1, 0, 1)
        self.assertEqual((server.players[1]["r"], server.players[1]["c"]), (0, 1))
        self.assertIn((0, 1), server.player_visited[1])

    def test_state_shares_items_but_only_own_vault_keys(self):
        server = self.make_server()
        server.player_items = {1: {(2, 2)}, 2: {(3, 3)}}
        server.player_item_keys = {1: {(2, 2): "ONE|PGF|1"}, 2: {(3, 3): "TWO|UXP|1"}}

        state = server._build_state(1)["per_player"]

        self.assertEqual(state["1"]["item_keys"], {"2,2": "ONE|PGF|1"})
        self.assertEqual(state["2"]["item_keys"], {})
        self.assertEqual(state["2"]["visited"], [])
        self.assertEqual(state["2"]["collected"], {})
        self.assertEqual(state["2"]["items"], [(3, 3)])

    @patch("network.server.play_sound", lambda *_: None)
    def test_powerups_are_collected_into_fixed_slots(self):
        server = self.make_server()
        cases = (("reveal", 0), ("shield", 1), ("speed", 2))
        for powerup, slot in cases:
            server.players[1]["r"], server.players[1]["c"] = 0, 0
            server.powerups = {(1, 0): powerup}
            server.process_client_move(1, 1, 0)
            self.assertEqual(server.player_powerups[1][slot], powerup)
            server.player_powerups[1] = [None, None, None]

    @patch("network.server.play_sound", lambda *_: None)
    @patch("network.server.random.randint", side_effect=[9, 19])
    def test_powerup_two_moves_opponent_item_under_player(self, _randint):
        server = self.make_server()
        source = (0, 0)
        destination = (9, 19)
        server.player_items[2] = {source}
        server.player_item_keys[2] = {source: "VAULT|XBVMU|2"}
        server.player_visited[2] = {
            (r, c) for r in range(10) for c in range(20)
            if (r, c) != destination
        }
        server.player_powerups[1][1] = "shield"

        server.process_client_powerup(1, 1)

        self.assertEqual(server.player_items[2], {destination})
        self.assertEqual(server.player_item_keys[2][destination], "VAULT|XBVMU|2")
        self.assertIsNone(server.player_powerups[1][1])

    @patch("network.server.play_sound", lambda *_: None)
    def test_powerup_two_is_not_consumed_without_opponent_item(self):
        server = self.make_server()
        server.player_powerups[1][1] = "shield"
        server.process_client_powerup(1, 1)
        self.assertEqual(server.player_powerups[1][1], "shield")


class EnterVaultTest(unittest.TestCase):
    def test_enter_opens_multiplayer_vault_on_owned_item(self):
        app = GridGameApp.__new__(GridGameApp)
        app.in_active_game = True
        app.qte_active = False
        app.my_player_id = 1
        app.is_client = True
        app.players = {1: {"r": 4, "c": 5}}
        app.per_player_data = {1: {"items": {(4, 5)}}}
        opened = []
        app.open_lock_dialog = lambda: opened.append(True)

        app.open_vault_at_current_item()

        self.assertEqual(opened, [True])


if __name__ == "__main__":
    unittest.main()
