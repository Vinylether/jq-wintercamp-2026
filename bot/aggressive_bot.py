from __future__ import annotations

import random
from typing import Dict, Tuple

from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate


class AggressiveBot(BasePokerPlayer):
    """Looser, higher-variance bot intended for stage-2 pushes."""

    def __init__(self) -> None:
        self.uuid = ""
        self.nb_player = 0
        self.folded_players = 0
        self.bluff_chance = 0.18
        self.opponents: Dict[str, OpponentStats] = {}

    def declare_action(self, valid_actions, hole_card, round_state):
        street = round_state["street"]
        call_action = next(a for a in valid_actions if a["action"] == "call")
        fold_action = next(a for a in valid_actions if a["action"] == "fold")
        raise_action = next((a for a in valid_actions if a["action"] == "raise"), None)

        call_amount = call_action["amount"]

        table_aggr, table_loose = self._table_profile()
        bluff_bias = self._bluff_bias(table_aggr, table_loose)

        if street == "preflop":
            return self._preflop_action(
                hole_card,
                call_amount,
                raise_action,
                call_action,
                fold_action,
                bluff_bias,
            )

        win_rate = self._estimate_win_rate(hole_card, round_state, self._nb_simulation(street))
        if call_amount == 0:
            if raise_action and (win_rate >= 0.52 or random.random() < bluff_bias):
                return self._raise_scaled(raise_action, 0.45 + 0.1 * (1.0 - table_aggr))
            return call_action["action"], call_action["amount"]

        pot_amount = round_state["pot"]["main"]["amount"]
        pot_odds = call_amount / float(pot_amount + call_amount)
        if win_rate >= pot_odds:
            if raise_action and win_rate >= 0.6:
                return self._raise_scaled(raise_action, 0.4 + 0.1 * (1.0 - table_aggr))
            return call_action["action"], call_action["amount"]

        if raise_action and random.random() < bluff_bias / 2:
            return self._raise_scaled(raise_action, 0.25)
        return fold_action["action"], fold_action["amount"]

    def receive_game_start_message(self, game_info):
        random.seed(23)
        self.nb_player = game_info.get("player_num", 0)
        self.uuid = self._find_my_uuid(game_info.get("seats", []))
        self.opponents = {}

    def receive_round_start_message(self, round_count, hole_card, seats):
        self.folded_players = 0
        self.nb_player = len([seat for seat in seats if seat.get("state") == "participating"])
        for seat in seats:
            uuid = seat.get("uuid")
            if not uuid or uuid == self.uuid:
                continue
            if uuid not in self.opponents:
                self.opponents[uuid] = OpponentStats()
            self.opponents[uuid].start_hand()

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        if action.get("action") == "fold":
            self.folded_players += 1
        player_uuid = action.get("player_uuid")
        if not player_uuid or player_uuid == self.uuid:
            return
        if player_uuid not in self.opponents:
            self.opponents[player_uuid] = OpponentStats()
        self.opponents[player_uuid].record_action(round_state.get("street", ""), action.get("action"))

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

    def _preflop_action(self, hole_card, call_amount, raise_action, call_action, fold_action, bluff_bias):
        strength = self._preflop_strength(hole_card)
        if strength >= 0.72 and raise_action:
            return self._raise_scaled(raise_action, 0.5)
        if strength >= 0.5:
            return call_action["action"], call_action["amount"]
        if call_amount == 0:
            return call_action["action"], call_action["amount"]
        if raise_action and random.random() < bluff_bias:
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

    def _find_my_uuid(self, seats) -> str:
        for seat in seats:
            if seat.get("name") == self.__class__.__name__:
                return seat.get("uuid", "")
        return ""

    def _table_profile(self) -> Tuple[float, float]:
        if not self.opponents:
            return 0.45, 0.35
        aggr_sum = 0.0
        loose_sum = 0.0
        for stats in self.opponents.values():
            aggr_sum += stats.aggression()
            loose_sum += stats.looseness()
        count = float(len(self.opponents))
        return aggr_sum / count, loose_sum / count

    def _bluff_bias(self, table_aggr: float, table_loose: float) -> float:
        bias = self.bluff_chance
        if table_aggr > 0.55:
            bias *= 0.7
        if table_loose < 0.3:
            bias *= 1.2
        return max(0.05, min(0.35, bias))


class OpponentStats:
    def __init__(self) -> None:
        self.hands = 0
        self.vpip = 0
        self.pfr = 0
        self.raises = 0
        self.calls = 0
        self.folds = 0
        self._vpip_mark = False
        self._pfr_mark = False

    def start_hand(self) -> None:
        self.hands += 1
        self._vpip_mark = False
        self._pfr_mark = False

    def record_action(self, street: str, action: str) -> None:
        if action == "raise":
            self.raises += 1
        elif action == "call":
            self.calls += 1
        elif action == "fold":
            self.folds += 1

        if street == "preflop" and action in ("call", "raise"):
            if not self._vpip_mark:
                self.vpip += 1
                self._vpip_mark = True
            if action == "raise" and not self._pfr_mark:
                self.pfr += 1
                self._pfr_mark = True

    def aggression(self) -> float:
        total = self.raises + self.calls
        if total == 0:
            return 0.4
        return self.raises / float(total)

    def looseness(self) -> float:
        if self.hands == 0:
            return 0.3
        return self.vpip / float(self.hands)


def setup_ai():
    return AggressiveBot()
