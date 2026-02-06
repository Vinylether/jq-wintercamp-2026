from __future__ import annotations

import random
from typing import Tuple

from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate


class AggressiveBot(BasePokerPlayer):
    """Looser, higher-variance bot intended for stage-2 pushes."""

    def __init__(self) -> None:
        self.nb_player = 0
        self.folded_players = 0
        self.bluff_chance = 0.18

    def declare_action(self, valid_actions, hole_card, round_state):
        street = round_state["street"]
        call_action = next(a for a in valid_actions if a["action"] == "call")
        fold_action = next(a for a in valid_actions if a["action"] == "fold")
        raise_action = next((a for a in valid_actions if a["action"] == "raise"), None)

        call_amount = call_action["amount"]

        if street == "preflop":
            return self._preflop_action(hole_card, call_amount, raise_action, call_action, fold_action)

        win_rate = self._estimate_win_rate(hole_card, round_state, self._nb_simulation(street))
        if call_amount == 0:
            if raise_action and (win_rate >= 0.52 or random.random() < self.bluff_chance):
                return self._raise_scaled(raise_action, 0.45)
            return call_action["action"], call_action["amount"]

        pot_amount = round_state["pot"]["main"]["amount"]
        pot_odds = call_amount / float(pot_amount + call_amount)
        if win_rate >= pot_odds:
            if raise_action and win_rate >= 0.6:
                return self._raise_scaled(raise_action, 0.4)
            return call_action["action"], call_action["amount"]

        if raise_action and random.random() < self.bluff_chance / 2:
            return self._raise_scaled(raise_action, 0.25)
        return fold_action["action"], fold_action["amount"]

    def receive_game_start_message(self, game_info):
        random.seed(23)
        self.nb_player = game_info.get("player_num", 0)

    def receive_round_start_message(self, round_count, hole_card, seats):
        self.folded_players = 0

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        if action.get("action") == "fold":
            self.folded_players += 1

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

    def _preflop_action(self, hole_card, call_amount, raise_action, call_action, fold_action):
        strength = self._preflop_strength(hole_card)
        if strength >= 0.72 and raise_action:
            return self._raise_scaled(raise_action, 0.5)
        if strength >= 0.5:
            return call_action["action"], call_action["amount"]
        if call_amount == 0:
            return call_action["action"], call_action["amount"]
        if raise_action and random.random() < self.bluff_chance:
            return self._raise_scaled(raise_action, 0.2)
        return fold_action["action"], fold_action["amount"]

    def _preflop_strength(self, hole_card):
        ranks = [card[1] for card in hole_card]
        suits = [card[0] for card in hole_card]
        pair = ranks[0] == ranks[1]
        suited = suits[0] == suits[1]
        high = max(self._rank_value(ranks[0]), self._rank_value(ranks[1]))
        low = min(self._rank_value(ranks[0]), self._rank_value(ranks[1]))

        if pair:
            if high >= 10:
                return 0.85
            if high >= 7:
                return 0.7
            return 0.6
        if high >= 12 and low >= 9:
            return 0.68
        if suited and high >= 11 and low >= 7:
            return 0.62
        if high >= 11 and low >= 6:
            return 0.55
        return 0.42

    def _rank_value(self, rank: str) -> int:
        if rank == "A":
            return 14
        if rank == "K":
            return 13
        if rank == "Q":
            return 12
        if rank == "J":
            return 11
        if rank == "T":
            return 10
        return int(rank)

    def _estimate_win_rate(self, hole_card, round_state, nb_simulation: int) -> float:
        community_card = round_state["community_card"]
        active_players = self.nb_player - self.folded_players
        active_players = max(2, active_players)
        return estimate_hole_card_win_rate(
            nb_simulation=nb_simulation,
            nb_player=active_players,
            hole_card=gen_cards(hole_card),
            community_card=gen_cards(community_card),
        )

    def _nb_simulation(self, street: str) -> int:
        if street == "flop":
            return 450
        if street == "turn":
            return 650
        if street == "river":
            return 850
        return 250

    def _raise_scaled(self, raise_action: dict, factor: float) -> Tuple[str, int]:
        min_amount = raise_action["amount"]["min"]
        max_amount = raise_action["amount"]["max"]
        amount = int(min_amount + (max_amount - min_amount) * factor)
        amount = max(min_amount, min(amount, max_amount))
        return raise_action["action"], amount


def setup_ai():
    return AggressiveBot()
