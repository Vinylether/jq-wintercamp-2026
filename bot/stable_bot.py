from __future__ import annotations

import random
from typing import List, Tuple

from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate


class StableBot(BasePokerPlayer):
    """Tight, low-variance bot intended for stage-1 stability."""

    def __init__(self) -> None:
        self.nb_player = 0
        self.small_blind = 5
        self.folded_players = 0

    def declare_action(self, valid_actions, hole_card, round_state):
        street = round_state["street"]
        call_action = next(a for a in valid_actions if a["action"] == "call")
        fold_action = next(a for a in valid_actions if a["action"] == "fold")
        raise_action = next((a for a in valid_actions if a["action"] == "raise"), None)

        call_amount = call_action["amount"]
        pot_amount = self._pot_for_me(round_state)

        if street == "preflop":
            return self._preflop_action(hole_card, call_amount, raise_action, call_action, fold_action)

        win_rate = self._estimate_win_rate(hole_card, round_state, self._nb_simulation(street))
        if call_amount == 0:
            if win_rate >= 0.55 and raise_action:
                return self._raise_min(raise_action)
            return call_action["action"], call_action["amount"]

        pot_odds = call_amount / float(pot_amount + call_amount)
        if win_rate >= max(0.5, pot_odds + 0.05):
            if raise_action and win_rate >= 0.72:
                return self._raise_min(raise_action)
            return call_action["action"], call_action["amount"]

        return fold_action["action"], fold_action["amount"]

    def receive_game_start_message(self, game_info):
        random.seed(17)
        self.nb_player = game_info.get("player_num", 0)
        self.small_blind = game_info["rule"]["small_blind_amount"]

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
        if strength >= 0.78 and raise_action:
            return self._raise_min(raise_action)
        if strength >= 0.58:
            return call_action["action"], call_action["amount"]
        if call_amount == 0:
            return call_action["action"], call_action["amount"]
        return fold_action["action"], fold_action["amount"]

    def _preflop_strength(self, hole_card: List[str]) -> float:
        ranks = [card[1] for card in hole_card]
        suits = [card[0] for card in hole_card]
        pair = ranks[0] == ranks[1]
        suited = suits[0] == suits[1]
        high = max(self._rank_value(ranks[0]), self._rank_value(ranks[1]))
        low = min(self._rank_value(ranks[0]), self._rank_value(ranks[1]))

        if pair:
            if high >= 11:
                return 0.9
            if high >= 8:
                return 0.78
            return 0.62
        if high >= 13 and low >= 10:
            return 0.74
        if suited and high >= 12 and low >= 9:
            return 0.68
        if high >= 12 and low >= 8:
            return 0.6
        return 0.4

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
            return 350
        if street == "turn":
            return 450
        if street == "river":
            return 550
        return 200

    def _raise_min(self, raise_action: dict) -> Tuple[str, int]:
        min_amount = raise_action["amount"]["min"]
        return raise_action["action"], min_amount

    def _pot_for_me(self, round_state) -> int:
        pot = round_state["pot"]["main"]["amount"]
        for side_pot in round_state["pot"]["side"]:
            if self._is_eligible(round_state, side_pot):
                pot += side_pot["amount"]
        return pot

    def _is_eligible(self, round_state, side_pot) -> bool:
        for seat in round_state["seats"]:
            if seat.get("uuid") in side_pot["eligibles"] and seat.get("name") == self.__class__.__name__:
                return True
        return False


def setup_ai():
    return StableBot()
