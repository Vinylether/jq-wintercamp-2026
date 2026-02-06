import random
from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate

NB_SIMULATION = 1000

def calculate_odds(cost, pot):
    return pot/cost

class Nickge(BasePokerPlayer):
    uuid = "nickge"

    def __init__(self):
        super().__init__()
        self.bluffing = True
        self.turnCount = 0
        self.prevRound = 0

    def declare_action(self, valid_actions, hole_card, round_state):
        community_card = round_state['community_card']
        win_rate = estimate_hole_card_win_rate(
                nb_simulation=NB_SIMULATION,
                nb_player=self.nb_player,
                hole_card=gen_cards(hole_card),
                community_card=gen_cards(community_card)
                )
        try:
            opponent_action_dict = round_state['action_histories'][round_state['street']][-1]
        except:
            if round_state["street"] == 'turn':
                opponent_action_dict = round_state['action_histories']['flop'][-1]
            else:
                opponent_action_dict = round_state['action_histories']['preflop'][-1]

        #print(hole_card)

        if 'round_count' not in round_state.keys() and self.turn == 0:
            self.bluffing = False

        if 'round_count' in round_state.keys():
            if round_state['round_count'] != self.prevRound:
                self.prevRound = round_state['round_count']
                self.bluffing = False
                self.turnCount = 0

        stack = [player['stack'] for player in round_state['seats'] if player['uuid'] == self.uuid][0]
        raise_amount_options = [item for item in valid_actions if item['action'] == 'raise'][0]['amount']
        opponent_action = opponent_action_dict['action']
        max = raise_amount_options['max']
        min = raise_amount_options['min']

        can_call = len([item for item in valid_actions if item['action'] == 'call']) > 0
        if can_call:
            # If so, compute the amount that needs to be called
            call_amount = [item for item in valid_actions if item['action'] == 'call'][0]['amount']
        else:
            call_amount = 0

        amount = None

        if opponent_action == "raise":
            if win_rate > .75:
                action = 'raise'
                amount = max
            elif win_rate > .65:
                action = 'raise'
                amount = int(((500-stack)/500)*(max-min)+min)
            elif win_rate > .55:
                action = 'call'
            else:
                if self.bluffing:
                    action = 'call'
                else:
                    num = random.uniform(0, 1)
                    if num > win_rate / 2:
                        action = 'fold'
                    elif can_call:
                        action = 'call'
        else:
            if win_rate > .75:
                action = 'raise'
                amount = int(((500-stack)/500)*(max-min)+min)
            elif win_rate > .65:
                action = 'raise'
                amount = int(.85*((500-stack)/(500))*(max- min) + min)
            elif win_rate > .55:
                action = 'call'
            else:
                num = random.uniform(0, 1)
                if self.bluffing:
                    if num > .5:
                        action = 'raise'
                        amount = int((stack/100)/8*(max-min))
                        amount += min
                    else:
                        action = "call"
                else:
                    if can_call and call_amount == 0:
                        action = "call"
                        print("Match Call 0")
                    elif num > win_rate:
                        action = 'fold'
                    elif num > win_rate/2 and can_call:
                        action = 'call'
                    else:
                        action = 'raise'
                        amount = int((stack/100)/8*(max-min))
                        amount += min
                        self.bluffing = True
            
            if amount is None:
                items = [item for item in valid_actions if item['action'] == action]
                amount = items[0]['amount']

            if amount < 0 or self.turnCount == 0:
                action = 'call'
                items = [item for item in valid_actions if item['action'] == action]
                amount = items[0]['amount']

                if win_rate < .25:
                    action = 'fold'

                if opponent_action == 'raise' and win_rate < .4:
                    action = 'fold'

        if action == 'raise' and amount > max:
            amount = max

        if action == 'raise' and amount < min:
            amount = min

        self.turnCount += 1
        return action, amount

    def receive_game_start_message(self, game_info):
        self.nb_player = game_info['player_num']

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

def setup_ai():
    return Nickge()