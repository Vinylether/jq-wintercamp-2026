from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
import collections
import random

NB_SIMULATION = 3333

mp = {'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
def check(cards):
    colors = collections.Counter([i[:1] for i in cards])
    nums = collections.Counter([int(mp[i[1:]] if i[1:] in mp else i[1:]) for i in cards])
    for _, v in colors.items():
        if v >= 5:
            return 6
    twos = threes = 0
    maxSeq = seqcnt = pre = -1
    for k, v in sorted(nums.items()):
        if k == pre + 1:
            seqcnt += 1
            if seqcnt >= 5:
                return 5
        else:
            seqcnt = 0
        pre = k
        maxSeq = max(maxSeq, seqcnt)
        if v == 2:
            twos += 1
        elif v == 3:
            threes = 1
        elif v == 4:
            return 8
    if twos and threes:
        return 7
    if maxSeq >= 5:
        return 5
    if threes:
        return 4
    if twos >= 2:
        return 3
    if twos:
        return 2
    return 1

class PlayerXin(BasePokerPlayer):
    uuid = 2333
    def declare_action(self, valid_actions, hole_card, round_state):
        community_card = round_state['community_card']
        winRate = estimate_hole_card_win_rate(
                nb_simulation=NB_SIMULATION,
                nb_player=self.nb_player - self.fold_players,
                hole_card=gen_cards(hole_card),
                community_card=gen_cards(community_card)
                )
        
        call_amount = valid_actions[1]['amount']
        raiseBase = valid_actions[2]['amount']['min']
        diff = valid_actions[2]['amount']['max'] - valid_actions[2]['amount']['min']
        

        if len(community_card) >= 3:
            types = check(hole_card + community_card)
            if  types >= 5:
                return "raise", raiseBase + diff
        
        if call_amount == 0:
            return valid_actions[1]['action'], valid_actions[1]['amount']
        
        
        curStack = 0
        for it in round_state["seats"]:
            if it["name"] == "PlayerXin":
                curStack = it["stack"]
                break
        if curStack - call_amount < 40 and winRate < 0.41:
            return "fold", 0
        
        Rate = winRate * (self.prize + call_amount) / call_amount
        randNum = random.random()
        
        baseRate = 2.0
        if Rate < 0.8:
            if randNum < 0.95:
                return "fold", 0
            return "raise", raiseBase + Rate / baseRate * diff
        elif Rate < 1.0:
            if randNum < 0.8:
                return "fold", 0
            if randNum < 0.85:
                return "call", call_amount
            return "raise", raiseBase + Rate / baseRate * diff
        elif Rate < 1.3:
            if randNum < 0.6:
                return "call", call_amount
            return "raise", raiseBase + Rate / baseRate * diff
        else:
            if randNum < 0.3:
                return "call", call_amount
            return "raise", raiseBase + min(Rate / baseRate * diff, diff), 


    def receive_game_start_message(self, game_info):
        self.nb_player = game_info['player_num']

    def receive_round_start_message(self, round_count, hole_card, seats):
        print(self.__class__, hole_card)
        self.fold_players = 0
        self.prize = 0
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        self.prize += action['amount']
        if action['action'] == 'fold':
            self.fold_players += 1
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass


def setup_ai():
    return PlayerXin()