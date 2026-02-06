#!/usr/bin/env python3

from pypokerengine.api.game import setup_config, start_poker
from pypokerengine.players import BasePokerPlayer

import argparse
import multiprocessing as mp


def load_sub_classes(directory, base_class):
    import importlib.util
    import os

    abs_dir = os.path.abspath(directory)
    classes = []
    files = filter(lambda f: f.endswith(".py"), os.listdir(abs_dir))

    for f in files:
        spec = importlib.util.spec_from_file_location("", os.path.join(abs_dir, f))
        a_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(a_module)
        for name in dir(a_module):
            obj = getattr(a_module, name)
            if (
                isinstance(obj, type)
                and issubclass(obj, base_class)
                and obj != base_class
            ):
                classes.append(obj)

    return classes


def start_one_game(rounds):
    config = setup_config(max_round=rounds, initial_stack=1000, small_blind_amount=5)
    player_constructors = load_sub_classes("/app/players", BasePokerPlayer)

    names = set([ctor.__name__ for ctor in player_constructors])
    assert len(names) == len(player_constructors), "found duplicated player name!"

    for ctor in player_constructors:
        config.register_player(name=ctor.__name__, algorithm=ctor())

    return start_poker(config, verbose=1)


def get_result(game_index, rounds):
    game_result = start_one_game(rounds)
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
        "all_stacks": {p["name"]: p["stack"] for p in game_result["players"]}
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run multiple poker games")
    parser.add_argument("-g", "--games", type=int, default=1, help="game count")
    parser.add_argument(
        "-r", "--rounds", type=int, default=50, help="round count in each game"
    )
    parser.add_argument("-c", "--cores", type=int, default=1, help="use how many cores")

    args = parser.parse_args()
    n = args.games
    rounds = args.rounds
    core_num = args.cores

    with mp.Pool(core_num) as pool: 
        game_params = [(i, rounds) for i in range(n)] 
        results = pool.starmap(get_result, game_params)
         
        results.sort(key=lambda x: x["game"])
        
        print("\nGame Results:")
        print("-" * 60)
        for result in results:
            print(f"Game {result['game'] + 1}:")
            print(f"Winner: {result['winner']} (stack: {result['stack']})")
            print("All players' stacks:")
            for name, stack in result['all_stacks'].items():
                print(f"  {name}: {stack}")
            print("-" * 60)
