#!/usr/bin/env python3

import argparse
import multiprocessing as mp
import os
import importlib.util

from pypokerengine.api.game import setup_config, start_poker
from pypokerengine.players import BasePokerPlayer


def load_sub_classes(directory, base_class):
    abs_dir = os.path.abspath(directory)
    classes = []
    for fname in os.listdir(abs_dir):
        if not fname.endswith(".py"):
            continue
        spec = importlib.util.spec_from_file_location("", os.path.join(abs_dir, fname))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, base_class) and obj != base_class:
                classes.append(obj)
    return classes


class CallBot(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
        call_action = next(a for a in valid_actions if a["action"] == "call")
        return call_action["action"], call_action["amount"]

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass


def start_one_game(rounds, player_dir, table_size):
    config = setup_config(max_round=rounds, initial_stack=1000, small_blind_amount=5)
    player_constructors = load_sub_classes(player_dir, BasePokerPlayer)

    names = set([ctor.__name__ for ctor in player_constructors])
    if len(names) != len(player_constructors):
        raise ValueError("Found duplicated player name in bot directory")

    for ctor in player_constructors:
        config.register_player(name=ctor.__name__, algorithm=ctor())

    missing = max(0, table_size - len(player_constructors))
    for idx in range(missing):
        config.register_player(name=f"CallBot{idx}", algorithm=CallBot())

    return start_poker(config, verbose=0)


def get_result(game_index, rounds, player_dir, table_size):
    game_result = start_one_game(rounds, player_dir, table_size)
    winner_name = ""
    winner_stack = 0

    for player in game_result["players"]:
        if player["stack"] > winner_stack:
            winner_name = player["name"]
            winner_stack = player["stack"]

    return {
        "game": game_index,
        "winner": winner_name,
        "stack": winner_stack,
        "all_stacks": {p["name"]: p["stack"] for p in game_result["players"]},
    }


def main():
    parser = argparse.ArgumentParser(description="Local backtest runner")
    parser.add_argument("-g", "--games", type=int, default=10, help="game count")
    parser.add_argument("-r", "--rounds", type=int, default=50, help="round count in each game")
    parser.add_argument("-c", "--cores", type=int, default=1, help="use how many cores")
    parser.add_argument("-d", "--dir", default=".", help="bot directory to load")
    parser.add_argument("-t", "--table-size", type=int, default=8, help="players per table")
    args = parser.parse_args()

    with mp.Pool(args.cores) as pool:
        game_params = [(i, args.rounds, args.dir, args.table_size) for i in range(args.games)]
        results = pool.starmap(get_result, game_params)

    results.sort(key=lambda x: x["game"])

    print("\nGame Results:")
    print("-" * 60)
    for result in results:
        print(f"Game {result['game'] + 1}:")
        print(f"Winner: {result['winner']} (stack: {result['stack']})")
        print("All players' stacks:")
        for name, stack in result["all_stacks"].items():
            print(f"  {name}: {stack}")
        print("-" * 60)


if __name__ == "__main__":
    main()
