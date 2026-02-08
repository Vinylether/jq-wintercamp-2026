#!/usr/bin/env python3

import argparse
import multiprocessing as mp
import os
import importlib.util
import random

from pypokerengine.api.game import setup_config, start_poker
from pypokerengine.players import BasePokerPlayer


def load_sub_classes(directory, base_class, exclude_files=None):
    if exclude_files is None:
        exclude_files = set()
    abs_dir = os.path.abspath(directory)
    classes = []
    for fname in os.listdir(abs_dir):
        if not fname.endswith(".py"):
            continue
        if fname in exclude_files:
            continue
        spec = importlib.util.spec_from_file_location("", os.path.join(abs_dir, fname))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, base_class) and obj != base_class:
                classes.append(obj)
    return classes


def _unique_name(base, used):
    if base not in used:
        used.add(base)
        return base
    idx = 2
    while True:
        name = f"{base}_{idx}"
        if name not in used:
            used.add(name)
            return name
        idx += 1


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


def start_one_game(
    rounds,
    player_dir,
    opponent_dir,
    opponent_max,
    table_size,
    seed,
    enable_callbot,
):
    config = setup_config(max_round=rounds, initial_stack=1000, small_blind_amount=5)
    player_constructors = load_sub_classes(
        player_dir,
        BasePokerPlayer,
        exclude_files={"backtest.py"},
    )
    opponent_constructors = []
    if opponent_dir and os.path.isdir(opponent_dir):
        opponent_constructors = load_sub_classes(opponent_dir, BasePokerPlayer)

    random.seed(seed)
    random.shuffle(opponent_constructors)
    opponent_constructors = opponent_constructors[: max(0, opponent_max)]

    used_names = set()
    for ctor in player_constructors:
        name = _unique_name(ctor.__name__, used_names)
        config.register_player(name=name, algorithm=ctor())

    for ctor in opponent_constructors:
        if len(used_names) >= table_size:
            break
        name = _unique_name(ctor.__name__, used_names)
        config.register_player(name=name, algorithm=ctor())

    if enable_callbot:
        missing = max(0, table_size - len(used_names))
        for idx in range(missing):
            config.register_player(name=f"CallBot{idx}", algorithm=CallBot())

    return start_poker(config, verbose=0)


def get_result(
    game_index,
    rounds,
    player_dir,
    opponent_dir,
    opponent_max,
    table_size,
    seed,
    enable_callbot,
):
    game_result = start_one_game(
        rounds,
        player_dir,
        opponent_dir,
        opponent_max,
        table_size,
        seed + game_index,
        enable_callbot,
    )
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


def _summarize_results(results):
    win_counts = {}
    stack_totals = {}
    stack_counts = {}
    strategy_wins = {"AdaptiveBot": 0, "Other": 0}
    for result in results:
        winner = result["winner"]
        win_counts[winner] = win_counts.get(winner, 0) + 1
        if winner in strategy_wins:
            strategy_wins[winner] += 1
        else:
            strategy_wins["Other"] += 1
        for name, stack in result["all_stacks"].items():
            stack_totals[name] = stack_totals.get(name, 0) + stack
            stack_counts[name] = stack_counts.get(name, 0) + 1

    avg_stacks = {}
    for name, total in stack_totals.items():
        avg_stacks[name] = total / float(stack_counts[name])

    win_counts = dict(sorted(win_counts.items(), key=lambda x: (-x[1], x[0])))
    avg_stacks = dict(sorted(avg_stacks.items(), key=lambda x: (-x[1], x[0])))

    return {
        "games": len(results),
        "win_counts": win_counts,
        "avg_stacks": avg_stacks,
        "strategy_wins": strategy_wins,
    }


def main():
    parser = argparse.ArgumentParser(description="Local backtest runner")
    parser.add_argument("-g", "--games", type=int, default=10, help="game count")
    parser.add_argument("-r", "--rounds", type=int, default=50, help="round count in each game")
    parser.add_argument("-c", "--cores", type=int, default=1, help="use how many cores")
    parser.add_argument("-d", "--dir", default=".", help="bot directory to load")
    parser.add_argument("-t", "--table-size", type=int, default=8, help="players per table")
    parser.add_argument(
        "-o",
        "--opponents-dir",
        default="pypokerengine/jq_player_examples",
        help="opponent directory to load",
    )
    parser.add_argument("-m", "--opponents-max", type=int, default=7, help="max opponents to load")
    parser.add_argument("-s", "--seed", type=int, default=17, help="random seed")
    parser.add_argument(
        "--enable-callbot",
        action="store_true",
        help="fill remaining seats with CallBot",
    )
    args = parser.parse_args()

    with mp.Pool(args.cores) as pool:
        game_params = [
            (
                i,
                args.rounds,
                args.dir,
                args.opponents_dir,
                args.opponents_max,
                args.table_size,
                args.seed,
                args.enable_callbot,
            )
            for i in range(args.games)
        ]
        results = pool.starmap(get_result, game_params)

    results.sort(key=lambda x: x["game"])
    summary = _summarize_results(results)

    print("\nGame Results:")
    print("-" * 60)
    for result in results:
        print(f"Game {result['game'] + 1}:")
        print(f"Winner: {result['winner']} (stack: {result['stack']})")
        print("All players' stacks:")
        for name, stack in result["all_stacks"].items():
            print(f"  {name}: {stack}")
        print("-" * 60)

    print("\nOverall Summary:")
    print("-" * 60)
    print(f"Games: {summary['games']}")
    print("Win counts:")
    for name, wins in summary["win_counts"].items():
        print(f"  {name}: {wins}")
    print("Average stacks:")
    for name, avg_stack in summary["avg_stacks"].items():
        print(f"  {name}: {avg_stack:.1f}")
    print("Strategy wins:")
    for name, wins in summary["strategy_wins"].items():
        print(f"  {name}: {wins}")
    print("-" * 60)


if __name__ == "__main__":
    main()
