from distutils.dir_util import copy_tree
from lib2to3.pgen2.token import OP
from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate, Card
from typing import Dict, Sequence
import random
from collections import Counter
import os.path

ACTION_FOLD = 0
ACTION_CALL = 1
ACTION_RAISE = 2

STREET_PREFLOP = 'preflop'
STREET_FLOP = 'flop'

STATE_IN = 'participating'
STATE_FOLD = 'folded'

PLAYER_UNKNOWN = "unknown"
PLAYER_BLUFFER = "bluffer"
PLAYER_FISH = "fish"
PLAYER_NIT = "nit"
PLAYER_NORMAL = "normal"

WIN_RATE_FACTOR = 0.75


class Opponent:
    def __init__(self, name, uuid) -> None:
        self.name = name
        self.uuid = uuid
        self.total_games = 0
        self.current_seat = 0
        self.total_actions = 0
        self.preflop_raise = 0
        self.preflop_call = 0
        self.fold_cnt = 0
        self.allin_cnt = 0
        self.allin_win_cnt = 0
        pass

    @staticmethod
    def dump(opponents:Dict, filename='yue_s_cheating.csv'):
        try:
            with open(filename,'w') as f:
                for uuid,op in opponents.items():
                    f.write("{},{},{},{},{},{},{},{},{}\n".format(op.name, op.total_games,
                        op.current_seat, op.total_actions,op.preflop_raise,
                        op.preflop_call,op.fold_cnt,op.allin_cnt, op.allin_win_cnt))
                    f.flush()
        except:
            pass

    @staticmethod
    def load(filename='yue_s_cheating.csv'):
        opponents = {}
        if not os.path.isfile(filename):
            return opponents
        try:
            with open(filename, 'r+') as f:
                for line in f:
                    op = Opponent("","")
                    stem = line.split(',')
                    if len(stem) != 9:
                        # print("bad line", line)
                        continue
                    op.name = stem[0]
                    op.total_games = int(stem[1])
                    op.current_seat = int(stem[2])
                    op.total_actions = int(stem[3])
                    op.preflop_raise = int(stem[4])
                    op.preflop_call = int(stem[5])
                    op.fold_cnt = int(stem[6])
                    op.allin_cnt = int(stem[7])
                    op.allin_win_cnt = int(stem[8])
                    opponents[op.name] = op
        except:
            pass
        # print("Load ops:", opponents)
        return opponents

    def seat_at(self, idx):
        self.current_seat = idx
        self.total_games += 1

    def action(self, street, action, amount):
        self.total_actions += 1
        if street == STREET_PREFLOP:
            if action == 'raise':
                self.preflop_raise += 1
            elif action == 'call':
                self.preflop_call += 1
        if action == 'fold':
            self.fold_cnt += 1
    
    def try_allin(self, street, action, amount):
        self.allin_cnt += 1

    def allin_win_rate(self):
        if self.allin_cnt == 0:
            return 0
        return self.allin_win_cnt / self.allin_cnt

    def get_vpip(self):
        if self.total_games == 0:
            return float('Nan')
        return (self.preflop_raise + self.preflop_call) / self.total_games

    def get_pfr(self):
        if self.total_games == 0:
            return float('Nan')
        return (self.preflop_raise) / self.total_games
    
    def getPlayerType(self):
        if self.total_games < 2:
            return PLAYER_UNKNOWN
        elif self.get_pfr() > 0.4:
            return PLAYER_BLUFFER
        elif self.get_vpip() > 0.4:
            return PLAYER_FISH
        elif self.get_vpip() < 0.2:
            return PLAYER_NIT
        else:
            return PLAYER_NORMAL

def hand_better_than_inner(target:str,hole_card:Sequence[Card], same_suit:bool) -> bool:
    if same_suit:
        if hole_card[0].suit != hole_card[1].suit:
            return False
    # compare rank
    high_rank = max(hole_card[0].rank, hole_card[1].rank)
    low_rank = min(hole_card[0].rank, hole_card[1].rank)
    inverse = lambda hsh: {v:k for k,v in hsh.items()}
    target_high = inverse(Card.RANK_MAP)[target[0]]
    target_low = inverse(Card.RANK_MAP)[target[1]]
    if high_rank >= target_high and low_rank >= target_low:
        return True
    return False

def hand_equal_inner(target:str, hole_card:Sequence[Card], same_suit:bool) -> bool:
    if same_suit:
        if hole_card[0].suit != hole_card[1].suit:
            return False
    # compare rank
    high_rank = max(hole_card[0].rank, hole_card[1].rank)
    low_rank = min(hole_card[0].rank, hole_card[1].rank)
    inverse = lambda hsh: {v:k for k,v in hsh.items()}
    target_high = inverse(Card.RANK_MAP)[target[0]]
    target_low = inverse(Card.RANK_MAP)[target[1]]
    if high_rank == target_high and low_rank == target_low:
        return True
    return False

def hand_better_than(target:str,hole_card:Sequence[Card]) -> bool:
    if target[-1] == '+':
        if len(target) == 3 or target[2] == 'o':  # 'JJ+', 'A2o+'
            return hand_better_than_inner(target, hole_card, False)
        else: # 'A2o'
            return hand_better_than_inner(target, hole_card, True)
    else:
        if len(target) == 2 or target[2] == 'o':  # 'TT', 'J3o'
            return hand_equal_inner(target,hole_card, False)
        else:
            return hand_equal_inner(target,hole_card, True)



def calculate_ev(win_rate, cost, pot):
    return win_rate * pot - cost * (1 - win_rate)

class HandEvaluate:
    def __init__(self) -> None:
        self.rate_pair = 0
        self.rate_two_pair = 0
        self.rate_three_kind = 0
        self.rate_four_kind = 0
        self.rate_full_house = 0
        self.rate_flush = 0
        self.rate_straight = 0

    def clear(self):
        self.rate_pair = 0
        self.rate_two_pair = 0
        self.rate_three_kind = 0
        self.rate_four_kind = 0
        self.rate_full_house = 0
        self.rate_flush = 0
        self.rate_straight = 0


    def update(self, street, hole_card:Sequence[Card], community_card:Sequence[Card]):
        all_rank = []
        all_suit = []
        for card in hole_card:
            all_rank.append(card.rank)
            all_suit.append(card.suit)
        for card in community_card:
            all_rank.append(card.rank)
            all_suit.append(card.suit)
        all_rank = sorted(all_rank)
        all_suit = sorted(all_suit)
        rank_cnt = Counter(all_rank)
        suit_cnt = Counter(all_suit)
        succ_rate = 0
        if street == 'turn':
            succ_rate = 2
        elif street == 'flop':
            succ_rate = 4

        for rank, cnt in rank_cnt.most_common():
            if cnt == 4:
                self.rate_four_kind = 1
            elif cnt == 3:
                self.rate_three_kind = 1
                self.rate_four_kind = 0.01 * succ_rate
                self.rate_full_house = max(self.rate_pair, self.rate_full_house)
            elif cnt == 2:
                self.rate_pair = 1  # todo two pair
                self.rate_three_kind = max(0.02 * succ_rate, self.rate_three_kind)
                self.rate_full_house = max(self.rate_three_kind,self.rate_full_house)
        for suit, cnt in suit_cnt.most_common():
            if cnt >= 5:
                self.rate_flush = 1
            elif cnt == 4:
                self.rate_flush = 0.09 * succ_rate
        self.check_straight(all_rank, succ_rate)
        if 14 in all_rank:
            for i in range(len(all_rank)):
                if all_rank[i] == 14:
                    all_rank[i] = 1
            all_rank = sorted(all_rank)
        self.check_straight(all_rank, succ_rate)

    # todo fixme
    def check_straight(self, all_rank, succ_rate):
        for i in range(4, len(all_rank)):
            diff5 = all_rank[i] - all_rank[i-4]
            if diff5 == 4:
                self.rate_straight = 1
                break
            elif (diff5 == 3 or diff5 == 5) and len(all_rank) <= 6:
                self.rate_straight = max(self.rate_straight, 0.04 * succ_rate)
        for i in range(3, len(all_rank)):
            diff4 = all_rank[i] - all_rank[i-3]
            if diff4 == 3 and len(all_rank) <= 6:  # 4 continuos card
                self.rate_straight = max(self.rate_straight, 0.08 * succ_rate)


    def nuts_rate(self):
        return self.rate_flush+self.rate_four_kind+self.rate_full_house+self.rate_straight

class Yue_SPlayer(BasePokerPlayer):
    def __init__(self) -> None:
        self.name = "Yue_SPlayer"
        self.uuid = ''
        self.max_round = 0
        self.opponents = {}
        self.his_opponents = {}
        self.current_seat = 0
        self.init_stack = 500
        self.small_blind_amount = 10
        self.nb_player = 0
        self.evaluator = HandEvaluate()
        # round info
        self.allin_players = []
        pass

    def declare_action(self, valid_actions, hole_card, round_state):
        street = round_state['street']
        if street == 'preflop':
            pass
            # print(hole_card)
        btn = round_state['dealer_btn']
        seats = round_state['seats']
        activate_player = [p['uuid'] for p in seats if p['state'] == STATE_IN]
        activate_player = [self.opponents[uuid] for uuid in activate_player if uuid != self.uuid]
        hole = gen_cards(hole_card)
        # print(valid_actions)

        if (street == STREET_PREFLOP):
            return self.handle_preflop(valid_actions, hole_card, round_state)

        community_card = gen_cards(round_state["community_card"])
        win_rate = estimate_hole_card_win_rate(
            nb_simulation=1000,
            nb_player=self.nb_player,
            hole_card=hole,
            community_card=community_card
        )
        win_rate = win_rate * WIN_RATE_FACTOR
        pot = round_state["pot"]["main"]["amount"]
        for side_pot in round_state["pot"]["side"]:
            if self.uuid in side_pot["eligibles"]:
                pot += side_pot["amount"]
        call_ev = calculate_ev(win_rate, valid_actions[ACTION_CALL]['amount'], pot)
        # print("Call ev:", call_ev)
        self.evaluator.update(street, hole, community_card)

        nuts_rate = self.evaluator.nuts_rate()
        if nuts_rate > 0.2:
            luck = random.random()
            if luck<nuts_rate:
                bet_amount = max(valid_actions[ACTION_RAISE]['amount']['min'],
                                 valid_actions[ACTION_RAISE]['amount']['max']*min(nuts_rate,1))
                return valid_actions[ACTION_RAISE]['action'], bet_amount

        # handle oppoents
        has_bluffer = False
        for player in activate_player:
            if player.getPlayerType() == PLAYER_BLUFFER:
                has_bluffer = True
        
        # someone is aggressive
        if len(self.allin_players) > 0:
            allin_uuid = self.allin_players[0]
            # bet on value
            if self.opponents[allin_uuid].allin_win_rate() > 0.8:
                return valid_actions[ACTION_FOLD]['action'], 0

        if (call_ev > 0):
            if not has_bluffer:
                # try to bluff when not likely to win
                blucky = random.random()
                if blucky > 0.9 and win_rate * len(activate_player) < 1.2:
                    bluff_amount = max(valid_actions[ACTION_RAISE]['amount']['max']*0.8,
                            valid_actions[ACTION_RAISE]['amount']['min'])
                    return valid_actions[ACTION_RAISE]['action'], bluff_amount

            return valid_actions[ACTION_CALL]['action'], valid_actions[ACTION_CALL]['amount']
        else:
            call_cost = valid_actions[ACTION_CALL]['amount']
            if call_cost == 0:
                return valid_actions[ACTION_CALL]['action'], valid_actions[ACTION_CALL]['amount']
            return valid_actions[0]['action'], valid_actions[0]['amount']


    def handle_preflop(self, valid_actions, hole_card, round_state):
        sb_pos = round_state['small_blind_pos']
        bb_pos = round_state['big_blind_pos']
        fold_ratio = 0.8
        if self.current_seat == bb_pos or self.current_seat == sb_pos:
            if valid_actions[ACTION_CALL]['amount'] == 2* self.small_blind_amount:
                fold_ratio = 0
        hole = gen_cards(hole_card)
        nuts = ['AA','KK','QQ']
        for card in nuts:
            if (hand_better_than(card, hole)):
                return valid_actions[ACTION_RAISE]['action'], valid_actions[ACTION_RAISE]['amount']['max']*0.5
        better_choose = ['JJ','TT','ATo+','JTo+','A2o+']
        for card in better_choose:
            if (hand_better_than(card, hole)):
                return valid_actions[ACTION_RAISE]['action'], valid_actions[ACTION_RAISE]['amount']['min']
        valid_choose = ['99','88','77','66','55','44','33','22','98o','87o',
                        '76o','65s','76s','87s','T9o','QJo','T7o+']
        for card in valid_choose:
            if (hand_better_than(card, hole)):
                return valid_actions[ACTION_CALL]['action'], valid_actions[ACTION_CALL]['amount']
        
        luck = random.random()
        if luck < fold_ratio:
            return valid_actions[ACTION_FOLD]['action'], 0
        else:
            return valid_actions[ACTION_CALL]['action'], valid_actions[ACTION_CALL]['amount']

    def receive_game_start_message(self, game_info):
        self.init_stack = game_info['rule']['initial_stack']
        self.small_blind_amount = game_info['rule']['small_blind_amount']
        self.nb_player = game_info["player_num"]
        self.his_opponents = Opponent.load()
        self.max_round = game_info['rule']['max_round']
        # print("Rememberd players:",len(self.his_opponents))
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        self.allin_players = []
        for idx, player in enumerate(seats):
            uuid = player['uuid']
            name = player["name"]
            # print(name, uuid)
            if name == self.name:
                self.current_seat = idx
                self.uuid = uuid
                continue

            if name in self.his_opponents:
                self.opponents[uuid] = self.his_opponents[name]

            if uuid not in self.opponents:
                self.opponents[uuid] = Opponent(name, uuid)
            self.opponents[uuid].seat_at(idx)
        self.evaluator.clear()
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, new_action, round_state):
        # print(new_action)
        # Track player actions
        street = round_state['street']
        uuid =new_action['player_uuid']
        if uuid == self.uuid:
            return
        if uuid in self.opponents:
            action = new_action['action']
            amount = new_action['amount']
            self.opponents[uuid].action(street,action, amount)
            if action == 'raise' and amount > 0.6 * self.init_stack:
                # all in like actions
                self.opponents[uuid].try_allin(street, action, amount)
        else:
            self.opponents[uuid] = Opponent("Unknow", uuid)
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        for uuid in self.allin_players:
            for winner in winners:
                if uuid == winner['uuid']:
                    self.opponents[uuid].allin_win_cnt += 1
        if round_state['round_count'] == self.max_round:
            # print("DO DUMP------------------------>")
            Opponent.dump(self.opponents)
        pass



def setup_ai():
    return Yue_SPlayer()