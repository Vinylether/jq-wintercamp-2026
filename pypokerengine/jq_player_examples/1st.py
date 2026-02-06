from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
import random as rand

class ActionHistory:
    def __init__(self, action, amount):
        self.action = action
        self.amount = amount

class PlayerInfo:
    stack = 0
    actions = []
    def __init__(self, id):
        self.id = id

    def storeAction(self, action_history):
        self.actions.append(action_history)

    def storeStack(self, stack):
        self.stack = stack

    def calcRisk(self):
        if self.stack <= 0:
            return 0
        risk = 1
        for history in self.actions:
            if (history.action == "raise" or history.action == "call") and history.amount / self.stack > 0.65:
                risk = risk + 1
        return risk

class Zheyu(BasePokerPlayer):
    uuid = "Zheyu"
    players = {}
    rffplayers = []
    winplayers = []

    def __init__(self):
        self.fold_ratio = self.call_ratio = raise_ratio = 1.0 / 3

    def set_action_ratio(self, fold_ratio, call_ratio, raise_ratio):
        ratio = [fold_ratio, call_ratio, raise_ratio]
        scaled_ratio = [1.0 * num / sum(ratio) for num in ratio]
        self.fold_ratio, self.call_ratio, self.raise_ratio = scaled_ratio

    def __choice_action(self, valid_actions):
        r = rand.random()
        if r <= self.fold_ratio:
            return valid_actions[0]
        elif r <= self.call_ratio:
            return valid_actions[1]
        else:
            return valid_actions[2]

    def doBluffer(self, valid_actions, win_rate, whole_risk):
        ref_amount = valid_actions[2]["amount"]["max"] * 0.5
        if valid_actions[2]["amount"]["min"] <= ref_amount:
            action, amount = valid_actions[2]["action"], valid_actions[2]["amount"]["min"]
            return action, amount
        else:
            return self.doObjective(valid_actions, win_rate, whole_risk)
        
    def doObjective(self, valid_actions, win_rate, whole_risk):

        chance = 0.7 + win_rate - whole_risk

        if chance < 0:
            #the chance is too small, let's fold
            action, amount = valid_actions[0]["action"], valid_actions[0]["amount"]
            return action, amount
        elif chance >=0 and chance < 0.45:
            #can call if the amount is not very big, can have a try
            action, amount = valid_actions[1]["action"], valid_actions[1]["amount"]
            return action, amount
        else:
            #charge!!!
            action, amount = valid_actions[2]["action"], valid_actions[2]["amount"]["min"]
            return action, amount

    def doHonest(self, valid_actions, win_rate, whole_risk):
        if win_rate >= 0.75:
            action = valid_actions[1]
        else:
            action = valid_actions[0]
        return action["action"], action["amount"]

    def doRandom(self, valid_actions, win_rate, whole_risk):
        choice = self.__choice_action(valid_actions)
        action = choice["action"]
        amount = choice["amount"]
        if action == "raise":
            amount = rand.randrange(
                amount["min"], max(amount["min"], amount["max"]) + 1
            )
        return action, amount

    #  we define the logic to make an action through this method. (so this method would be the core of your AI)
    def declare_action(self, valid_actions, hole_card, round_state):

        
        online_player = 1
        whole_risk = 0.0
        for player in round_state["seats"]:
            if player["state"] == "folded":
                continue
            if player["uuid"] not in self.players:
                continue

            player_history = self.players[player["uuid"]]
            risk = player_history.calcRisk()

            if player["uuid"] in self.rffplayers:
                risk = risk + 1

            win_times = 0
            for winner in self.winplayers:
                if player["uuid"] == winner:
                    win_times = win_times + 1
            if risk > 0:
                whole_risk = whole_risk + win_times / risk

            online_player += 1

        print(self.__class__, online_player, whole_risk)
        community_card = round_state["community_card"]
        win_rate = estimate_hole_card_win_rate(
            nb_simulation=1000,
            nb_player=online_player,
            hole_card=gen_cards(hole_card),
            community_card=gen_cards(community_card),
        )

        if round_state["round_count"] >= 8:
            return self.doObjective(valid_actions, win_rate, whole_risk)

        if round_state["round_count"] % 4 == 1:
            return self.doBluffer(valid_actions, win_rate, whole_risk)
        elif round_state["round_count"] % 4 == 2:
            return self.doHonest(valid_actions, win_rate, whole_risk)
        elif round_state["round_count"] % 4 == 3:
            return self.doObjective(valid_actions, win_rate, whole_risk)
        else:
            return self.doRandom(valid_actions, win_rate, whole_risk)
        
        #call_action_info = valid_actions[1]
        #action, amount = call_action_info["action"], call_action_info["amount"]
        #return action, amount  # action returned here is sent to the poker engine

    # a game has multiple rounds
    def receive_game_start_message(self, game_info):
        self.players = {}
        for player in game_info["seats"]:
            if player["uuid"] == self.uuid:
                continue
            self.players[player["uuid"]] = PlayerInfo(player["uuid"])

        self.winplayers = []
        return

    # a round includes streets ["preflop", "flop", "turn", "river"]
    def receive_round_start_message(self, round_count, hole_card, seats):
        for player in seats:
            if player["uuid"] == self.uuid:
                continue
            self.players[player["uuid"]].storeStack(player["stack"])

        self.rffplayers = []
        return

    # a street is one of ["preflop", "flop", "turn", "river"]
    def receive_street_start_message(self, street, round_state):
        pass

    # a game update is received when each player takes action
    def receive_game_update_message(self, action, round_state):
        if action["player_uuid"] == self.uuid:
            return
        
        self.players[action["player_uuid"]].storeAction(ActionHistory(action["action"],action["amount"]))

        if round_state["street"] == "preflop" and action["action"] == "raise":
            self.rffplayers.append(action["player_uuid"])

    def receive_round_result_message(self, winners, hand_info, round_state):
        for winner in winners:
            if winner["uuid"] == self.uuid:
                continue
            self.winplayers.append(winner["uuid"])
        pass


def setup_ai():
    return Zheyu()
