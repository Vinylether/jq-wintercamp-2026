import os
import random
import sys
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import pandas as pd
from tqdm import tqdm

from pypokerengine.engine.card import Card
from pypokerengine.engine.hand_evaluator import HandEvaluator
from pypokerengine.utils.card_utils import gen_cards


def card_str_to_card_list(card_str: str) -> list:
    card_str = card_str.strip("[]' ")
    community_cards = card_str.split("', '") if "', '" in card_str else card_str.split(", ")
    return list(filter(bool, community_cards))

def convert_cards_to_emoji(cards: list):
    suit_conversion = {
        'H': '♥️',
        'S': '♠️',
        'C': '♣️',
        'D': '♦️'
    }
     
    converted_cards = []

    for card in cards:
        suit = card[0]
        rank = card[1:]
        converted_card = f"[{suit_conversion.get(suit, suit)} {rank}]"
        converted_cards.append(converted_card)
    
    return ' '.join(converted_cards)

def calc_global_win_rate(players: dict, community_cards: list, folded_player_names: set):
    all_cards = set(range(1, 53))
    all_cards -= set([Card.from_str(c).to_id() for c in community_cards])

    simulation_round = 1000
    for name, p in players.items():
        if name in folded_player_names:
            continue
        p['win_rate'] = 0
        all_cards -= set([Card.from_str(c).to_id() for c in p['hole_cards']])


    for _ in range(simulation_round):
        generated_remaining_community_cards = [
            str(Card.from_id(c_id))
            for c_id in random.sample(list(all_cards), k=5 - len(community_cards))
        ]
        player_hand_score = dict()
        for name, player in players.items():
            if name in folded_player_names:
                continue

            score = HandEvaluator.eval_hand(
                gen_cards(player['hole_cards']),
                gen_cards(community_cards + generated_remaining_community_cards))
            player_hand_score[name] = score
        max_score = max(player_hand_score.values())
        for name, score in player_hand_score.items():
            if score == max_score:
                players[name]['win_rate'] += 1 / simulation_round


def format_game_log(log_content, set_num):
    print(f"🎲 Texas Hold'em Poker Game Log {set_num} 🎲")
    print("=" * 50)

    players = {}
    round_actions = {}   
    current_round = 0
    current_street = None
    lines = log_content.split('\n')

    # 初始化新一轮的记录
    def init_round_record(round_num):
        round_actions[round_num] = {
            "players": {},
            "streets": {     
                "preflop": {"actions": [], "community_cards": []},
                "flop": {"actions": [], "community_cards": []},
                "turn": {"actions": [], "community_cards": []},
                "river": {"actions": [], "community_cards": []}
            },
            "winner": None,
            "final_stacks": {}
        }

    temp_players = {}

    for line in lines:

        if "Started the round" in line:
            current_round = int(line.split("round")[1].strip())
            init_round_record(current_round)
            round_actions[current_round]["players"] = temp_players.copy()
            temp_players = {}

        elif "gets hole card" in line:
            player = line.split('[')[1].split(']')[0]
            cards = card_str_to_card_list(line.split('[')[2].split(']')[0])
            stack = int(line.split()[-1])

            temp_players[player] = {
                "hole_cards": cards,
                "initial_stack": stack
            }
             
            if player not in players:
                players[player] = {
                    "current_stack": stack,
                    "max_stack": stack,
                    "status": "active",
                    "elimination_round": None
                }
            else:
                players[player]["current_stack"] = stack
                players[player]["max_stack"] = max(players[player]["max_stack"], stack)

        
        elif "Street" in line and "started" in line:
            current_street = line.split('"')[1]
            if "community card = [" in line:
                try:
                    community_cards = card_str_to_card_list(line.split("community card = [")[1].split("]")[0])
                    round_actions[current_round]["streets"][current_street]["community_cards"] = community_cards
                except IndexError:
                    pass

       
        elif "declared" in line:
            if current_round and current_street:
                player = line.split('"')[1]
                action = line.split('"')[3]
                round_actions[current_round]["streets"][current_street]["actions"].append(
                    (player, action)
                )

        
        elif "won the round" in line:
            winner = line.split("['")[1].split("']")[0]
            round_actions[current_round]["winner"] = winner
            
            stack_str = line.split("stack = ")[1].strip(")")
            try:
                stack_info = eval(stack_str)
                round_actions[current_round]["final_stacks"] = stack_info
                
                
                for p, s in stack_info.items():
                    if p in players:
                        players[p]["current_stack"] = s
                        if s == 0 and players[p]["status"] == "active":
                            players[p]["status"] = "eliminated"
                            players[p]["elimination_round"] = current_round
                            players[p]["max_stack"] = players[p]["max_stack"]
            except:
                print(f"Warning: Unable to parse stack info: {stack_str}")

 
    print("\n📊 Detailed Game Log:")
    print("=" * 50)
    
    for round_num in sorted(round_actions.keys()):
        round_data = round_actions[round_num]
        print(f"\n🔄 Round {round_num}")
        print("-" * 40)
        
        # 打印玩家初始状态
        print("Initial State:")
        for player, data in round_data["players"].items():
            converted_cards = convert_cards_to_emoji(data['hole_cards'])
            print(f"👤 {player:<15} | {converted_cards:<20} | 💰 {data['initial_stack']:>5}")

        current_community_cards = []

        folded_player_names = set()
        
        for street in ["preflop", "flop", "turn", "river"]:
            street_data = round_data["streets"][street]
            if street_data["actions"] or street_data["community_cards"]:
                print(f"\n🎴 {street.upper()}")
                
         
                if street_data["community_cards"]:
                    current_community_cards = street_data["community_cards"]
                
               
                if street == "preflop":
                    print("Board: [  ]")
                else:
                    converted_community = convert_cards_to_emoji(current_community_cards)
                    print(f"Board: [ {converted_community} ]")

                calc_global_win_rate(round_data['players'], current_community_cards, folded_player_names)
                
                
                for player, action in street_data["actions"]:
                    action_type = action.split(':')[0]
                    amount = action.split(':')[1]
                    
                     
                    action_emoji = {
                        'fold': '❌',
                        'call': '✅',
                        'raise': '⬆️',
                        'smallblind': '💰',
                        'bigblind': '💰'
                    }.get(action_type, '➡️')
                    
                     
                    formatted_action = f"{action_type}:${amount}" if amount != "0" else action_type
                    player_info = round_data['players'][player]
                    converted_cards = convert_cards_to_emoji(player_info['hole_cards'])
                    win_rate_str = f"{player_info['win_rate'] * 100:.2f}%"
                    print(f"  {player:<15} | {converted_cards:<8} | {win_rate_str:>8} | {action_emoji} {formatted_action}")
                    if action_type == "fold":
                        folded_player_names.add(player)
                        calc_global_win_rate(round_data['players'], current_community_cards, folded_player_names)
        
    
        print(f"\n🏆 Winner: {round_data['winner']}")
        print("Final Stacks:")
        for player, stack in round_data["final_stacks"].items():
            initial_stack = round_data["players"].get(player, {"initial_stack": stack})["initial_stack"]
            stack_change = stack - initial_stack
            change_symbol = "📈" if stack_change > 0 else "📉" if stack_change < 0 else "➡️"
            print(f"  {player:<15}: ${stack:>6} {change_symbol} ({stack_change:+})")
        print("-" * 40)



    def sort_key(item):
        player_data = item[1]
        is_active = player_data["status"] == "active"
        
        if is_active:
            # 活跃玩家排在最前面，按当前筹码排序
            return (-1, -player_data["current_stack"], 0)
        else:
            # 淘汰玩家按出局轮数（越晚越好）和出局前最高筹码排序
            elimination_round = player_data["elimination_round"] or 0
            return (1, -elimination_round, -player_data["max_stack"])

    rankings = sorted(players.items(), key=sort_key)
    
 
    print("\n🏁 Final Rankings:")
    print("-" * 50)
    
    current_status = None
    for rank, (player, info) in enumerate(rankings, 1): 
        if info["status"] == "active" and current_status != "active":
            print("\n🎮 Active Players:")
            current_status = "active"
        elif info["status"] == "eliminated" and current_status != "eliminated":
            print("\n💀 Eliminated Players:")
            current_status = "eliminated"
             
        status_emoji = "🏆" if rank == 1 else "👥" if info["status"] == "active" else "💀"
        
        # 出局信息
        elimination_info = ""
        if info["status"] == "eliminated":
            elimination_info = f" (Round {info['elimination_round']})"
        
        # 筹码信息
        stack_info = str(info['current_stack'])
        if info["status"] == "eliminated":
            stack_info = f"0 (Max: {info['max_stack']})"
        
        print(f"{rank}. {status_emoji} {player:<15} | "
              f"Stack: {stack_info:>10} | "
              f"Status: {info['status']}{elimination_info}")
     
    rankings_output = []
    for rank, (player, info) in enumerate(rankings, 1):
        elimination_info = f" (Round {info['elimination_round']})" if info["status"] == "eliminated" else ""
        stack_info = str(info['current_stack'])
        if info["status"] == "eliminated":
            stack_info = f"0 (Max: {info['max_stack']})"
         
        rankings_output.append(
            f"{set_num},{rank},{player},{stack_info},{info['status']}|{elimination_info}\n"
        )
    
    return rankings_output

def process_single_file(input_file_path): 
    input_dir_name = os.path.basename(os.path.dirname(input_file_path))
     
    output_base_dir = "log_viewer"
    output_dir = os.path.join(output_base_dir, input_dir_name)
    os.makedirs(output_dir, exist_ok=True)
     
    input_filename = os.path.basename(input_file_path)
    output_filename = os.path.splitext(input_filename)[0] + ".log"
    output_path = os.path.join(output_dir, output_filename)
     
    set_num = int(input_filename.split('_')[1].split('.')[0])
     
    original_stdout = sys.stdout
    rankings = []
    
    with open(input_file_path, 'r') as infile, open(output_path, 'w') as outfile:
        sys.stdout = outfile
        log_content = infile.read() 
        if "Game Results:" not in log_content:
            print("⚠️ CRASH SET ⚠️")
            return [f"{set_num},CRASH,CRASH,CRASH,CRASH\n"]
        rankings = format_game_log(log_content, set_num)
    
    sys.stdout = original_stdout
    return rankings

def process_all_files(input_dir): 
    if os.path.exists("rankings_all.csv"):
        os.remove("rankings_all.csv")
     
    with open("rankings_all.csv", "w") as f:
        f.write("set_num,rank,player,stack,elimination_info\n")
    
    # 收集所有需要处理的文件
    files_to_process = []
    for root, _, files in os.walk(input_dir):
        for name in files:
            if name.endswith('.log'):  
                files_to_process.append(os.path.join(root, name))
    
    print(f"\n🔄 processing {len(files_to_process)} files...")
    
 
    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
   
        all_rankings = list(tqdm(
            executor.map(process_single_file, files_to_process),
            total=len(files_to_process),
            desc="📊 Game results All",
            ncols=100,   
            bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [剩余时间: {remaining}]'
        ))
    
    print("\n✅ Game results All done!")
    
    with open("rankings_all.csv", "a") as f:
        for rankings in all_rankings:
            for ranking in rankings:
                f.write(ranking)

def display_all_rankings(df):
    all_sets = sorted(df['set_num'].unique())
    num_sets = len(all_sets)
    rows = 5
    cols = 4
    
    print("\n📊 All Sets Rankings Display")
    print("=" * 140)  

    for row in range(rows):
        set_displays = []
        
        for col in range(cols):
            set_idx = row + col * rows
            if set_idx >= num_sets:
                continue
                
            set_num = all_sets[set_idx]
            set_data = df[df['set_num'] == set_num]
            
             
            if set_data['player'].iloc[0] == 'CRASH':
                set_displays.append([
                    f"Set {int(set_num):02d}:",
                    "-" * 35,   
                    "⚠️ CRASH SET ⚠️"
                ])
                continue
             
            display_lines = [
                f"Set {int(set_num):02d}:",   
                "-" * 35   
            ]
             
            for _, row_data in set_data.iterrows():
                player = str(row_data['player'])   
                rank = int(row_data['rank'])
                stack = str(row_data['stack'])
                elimination_info = str(row_data['elimination_info'])
                 
                round_info = ""
                if "Round" in elimination_info:
                    round_num = elimination_info.split("Round")[1].strip("() ")
                    round_info = f"R{round_num}"
                
                status = "🏆" if rank == 1 else "👥" if "active" in elimination_info else "💀"
                 
                display_line = f"{rank:2d}. {status} {player:<12}"
                if round_info:
                    display_line += f" ({round_info})"
                display_line += f" ${stack:<15}"  
                display_lines.append(display_line)
            
            set_displays.append(display_lines)
        
        if set_displays: 
            max_lines = max(len(display) for display in set_displays)
             
            for line_idx in range(max_lines):
                for display in set_displays: 
                    if line_idx < len(display):
                        print(f"{str(display[line_idx]):<40}", end="")  
                    else:
                        print(" " * 40, end="")   
                print()
            
            print()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python log_viewer.py <input_directory>")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    process_all_files(input_dir)
 
    df = pd.read_csv("rankings_all.csv")
    
    display_all_rankings(df)
     
    if not df['player'].eq('CRASH').any():
        print("\n🏆 Average Rankings:")
        print("=" * 40)
        print(f"{'Player':<15} {'Average Rank':<15} {'Games Played':<15}")
        print("-" * 40)
        
        avg_ranks = df.groupby('player')['rank'].agg(['mean', 'count']).round(2)
        avg_ranks = avg_ranks.sort_values('mean')
        for player, stats in avg_ranks.iterrows():
            print(f"{player:<15} {stats['mean']:<10.2f} {stats['count']:<10.0f}")
