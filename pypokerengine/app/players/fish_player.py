from pypokerengine.players import BasePokerPlayer


class FishPlayer(
    BasePokerPlayer
):  # Do not forget to make parent class as "BasePokerPlayer"

    #  we define the logic to make an action through this method. (so this method would be the core of your AI)
    def declare_action(self, valid_actions, hole_card, round_state):
        # valid_actions format => [fold_action_info, call_action_info, raise_action_info]
        call_action_info = valid_actions[1]
        action, amount = call_action_info["action"], call_action_info["amount"]
        return action, amount  # action returned here is sent to the poker engine

    # a game has multiple rounds
    def receive_game_start_message(self, game_info):
        pass

    # a round includes streets ["preflop", "flop", "turn", "river"]
    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    # a street is one of ["preflop", "flop", "turn", "river"]
    def receive_street_start_message(self, street, round_state):
        pass

    # a game update is received when each player takes action
    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass


def setup_ai():
    return FishPlayer()
