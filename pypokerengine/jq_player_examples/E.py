from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate

NB_SIMULATION = 3000


class LinjiePlayer(BasePokerPlayer):

    FOLD, CALL, MIN_RAISE, AVG_RAISE, MAX_RAISE, ALL_IN = 0, 1, 2, 3, 4, 5

    def declare_action(self, valid_actions, hole_card, round_state):

        community_card = round_state['community_card']
        win_rate = estimate_hole_card_win_rate(
                nb_simulation=NB_SIMULATION,
                nb_player=self.nb_player - self.fold_players,
                hole_card=gen_cards(hole_card),
                community_card=gen_cards(community_card)
                )

        call_amount = valid_actions[1]['amount']
        raise_amount = 0
        if win_rate >= 0.95:
            self.action = self.ALL_IN
            raise_amount = valid_actions[2]['amount']['max']
            if call_amount > raise_amount:
                self.action = self.CALL
        elif win_rate >= 0.8:
            self.action = self.MAX_RAISE
            raise_amount = (valid_actions[2]['amount']['min'] + valid_actions[2]['amount']['max']) // 2
            if call_amount > raise_amount:
                self.action = self.CALL
        elif win_rate >= 0.65:
            self.action = self.AVG_RAISE
            raise_amount = (valid_actions[2]['amount']['min'] + valid_actions[2]['amount']['max']) // 4
            if call_amount > raise_amount:
                self.action = self.CALL
        elif win_rate >= 0.5:
            raise_amount = valid_actions[2]['amount']['min']
            if call_amount <= raise_amount and self.raise_times < 10:
                self.action = self.MIN_RAISE
                self.raise_times += 1
            elif call_amount >= raise_amount * 3:
                self.action = self.FOLD
            else:
                self.action = self.CALL
        elif win_rate >= 0.3:
            if call_amount <= 10:
                self.action = self.CALL
            else:
                self.action = self.FOLD
        elif valid_actions[1]['amount'] == 0:
            self.action = self.CALL
        else:
            self.action = self.FOLD

        if self.FOLD == self.action:
            return valid_actions[0]['action'], valid_actions[0]['amount']
        elif self.CALL == self.action:
            return valid_actions[1]['action'], valid_actions[1]['amount']
        elif self.MIN_RAISE <= self.action:
            return valid_actions[2]['action'], raise_amount

    def receive_game_start_message(self, game_info):
        self.nb_player = game_info['player_num']

    def receive_round_start_message(self, round_count, hole_card, seats):
        print(self.__class__, hole_card)
        self.nb_player = len([seat for seat in seats if seat['state'] =="participating"])
        self.fold_players = 0
        self.raise_times = 0
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        if action['action'] == 'fold':
            self.fold_players += 1
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

def setup_ai():
    return LinjiePlayer()
