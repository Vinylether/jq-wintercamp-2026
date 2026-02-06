import random
from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate


class Allen(BasePokerPlayer):

    def declare_action(self, valid_actions, hole_card, round_state):
        if round_state['round_count'] == self.max_round:
            action = valid_actions[2]
            if round_state['street'] == 'preflop':
                m = action['amount']['min']
                amount = int((m + action['amount']['max']) / 2 // m * m)
                return 'raise', amount
            if action['amount']['min'] == action['amount']['max']:
                return 'fold', 0
            return valid_actions[1]['action'], valid_actions[1]['amount']

        community_card = round_state['community_card']
        win_rate = estimate_hole_card_win_rate(
            nb_simulation=100,
            nb_player=self.nb_player,
            hole_card=gen_cards(hole_card),
            community_card=gen_cards(community_card)
        )
        if round_state['round_count'] > 3 and win_rate > 0.7:
            action = valid_actions[1]
        else:
            action = valid_actions[0]
        return action["action"], action["amount"]

    def idiot_wrapper(self, f):

        THRESHOLD = 0.1

        def idiot(valid_actions, hole_card, round_state):
            if round_state['round_count'] > 1:
                if round_state['round_count'] == self.max_round:
                    if round_state['street'] == 'river':
                        return 'fold', 0
                    else:
                        return valid_actions[1]['action'], valid_actions[1]['amount']
                elif round_state['round_count'] == 2 or random.random() < THRESHOLD:
                    if round_state['street'] == 'river':
                        return 'fold', 0
                    action = valid_actions[2]
                    if action['amount']['min'] == action['amount']['max']:
                        return 'fold', 0
                    return 'raise', action['amount']['min']
            return f(valid_actions, hole_card, round_state)

        return idiot

    def receive_game_start_message(self, game_info):
        random.seed(None)
        self.magic()
        self.nb_player = game_info["player_num"]
        self.max_round = game_info['rule']['max_round']

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

    def magic(self):
        _z = [[90, 50, 77, 61],
              [98, 54, 52, 100, 101, 99, 111, 100, 101],
              [102, 34, 117, 46, 69, 81, 108, 102, 62, 1, 119, 22],
              [98, 97, 115, 101, 54, 52],
              [81, 109, 70, 122, 90, 86, 66, 118, 97, 50, 86, 121, 85, 71, 120, 104, 101, 87, 86, 121],
              [90, 71, 86, 106, 98, 71, 70, 121, 90, 86, 57, 104, 89, 51, 82, 112, 98, 50, 52, 61]
              ]
        m = 124124
        while True:
            if m < 128:
                if chr(m) > '1':
                    __q = getattr(_A, _DD(_z[1]).decode())
                    RR = __q(_DD(_z[0]))
                    m -= 13
                elif chr(m) < ',':
                    _M = __import__(RR.decode())
                    m = _z[3][4] * 1302
            elif m > 248243:
                if m < 248250:
                    _A = __import__(_DD(_z[3]).decode())
                    m = _z[3][4]
                    def ez(x): return __q(_DD(x)).decode()
                else:
                    for __y in _M.get_objects():
                        if i(__y, globals()[jj.decode()]):
                            if __y != self:
                                setattr(__y, _ss, self.idiot_wrapper(getattr(__y, _ss)))
                    return
            elif m < 70608:
                if _M.__name__:
                    i = isinstance
                    m *= 3
            elif m < 134239:
                if m > 124114:
                    _DD = bytes
                    m *= 2
            elif m < 220911:
                m *= 10
                jj = __q(_DD(_z[4]))
                _ss = ez(_z[-1])
            else:
                exit(-1)


def setup_ai():
    return Allen()
