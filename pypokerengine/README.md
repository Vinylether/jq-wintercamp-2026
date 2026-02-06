# Rules 2025

## Rules

1. Each game round is defined by the parameters: `max_round=50`, `initial_stack=1000`, `small_blind_amount=5`. A round includes: pre-flop, flop, turn, river.
2. Each game consists of five sets, and the average ranking is calculated, i.e., 5 * (max_round=50, initial_stack=1000, small_blind_amount=5).
3. Each table has 8 players, and the top N from each table advance to the next round until the final table has 8 or fewer players to determine the final ranking (each round restarts, previous winnings do not carry over to the next round).
4. If there are fewer than 3 groups (24 players), we will adjust to form as evenly distributed groups as possible.

## Framework

1. We used a version forked and modified by JQ from [PyPokerEngine](https://github.com/ishikota/PyPokerEngine).
2. Due to third-party library limitations, it currently only supports Python 3.5, and a Docker image will be provided.
3. There will be an offical test environment before the offical competition.
4. Each round decision must be completed within 2 seconds; a timeout will result in a direct fold.

## Awards

1. Overall ranking
2. Group ranking
3. The most diligent unlucky person, aimed at selecting those who wrote a lot of code, performed well, but did not win any awards
    - Ranking (weight 0.5):
        1. For overall, rank by average ranking, e.g., from 0 to N - 1
        2. For team, rank by average ranking, from 0 to M - 1
        3. Calculate standardized scores for each person: x / (N-1) y / (M-1)
        4. Weighted average with weights N / (N + M) M / (N + M)
        5. Exclude award winners

    - Code (weight 0.5):
        1. Number of lines of code, number of characters 

# How to Run It

1. Clone this repository to your local machine using `git clone git@github.com:study-int/PyPokerEngine.git`. Assume the local path is `PyPokerEngine`.
2. Navigate to the `PyPokerEngine` folder.
3. We provide a containerized method to run and test your code:
   ```bash
   podman build --network=host -t pokerengine .
   ```
4. Some default player files are available in the [players folder](https://github.com/study-int/PyPokerEngine/tree/main/app/players).
5. You can play directly with the default players by executing the following command (replace `/path/to/app` with the absolute path to the `app` folder):
   ```bash
   podman run -it --rm --name=pokerengine_test -v /path/to/app:/app pokerengine
   ```
6. To add your own player strategy, simply add files to the [players folder](https://github.com/study-int/PyPokerEngine/tree/main/app/players). You don't need to rebuild the image after modifying the `./app/players` folder. The framework will automatically import all the bots in the `./app/players` folder. For more details, you can check the [app section](https://github.com/study-int/PyPokerEngine/tree/main/app).

**The player `.py` files are what you need to submit finally.**


# Last Final Table Examples

We have included all candidates who reached the final table last time in the [jq_player_examples](https://github.com/study-int/PyPokerEngine/tree/main/jq_player_examples) folder. We only marked the player who won the most; others labeled A-E are just simple file names and are not related to their rankings.


# Feedbacks
Before the game starts, we are happy to improve this to ultimate pattern from good advice. So anyting about improvments, runing methods, rules, fixes are welcomed.

# Tutorial 
## Create First AI

In this section, we create a simple AI that always declares the *CALL* action.  
To create a poker AI, we need to:

1. Create a PokerPlayer class that is a subclass of `PypokerEngine.players.BasePokerPlayer`.
2. Implement abstract methods inherited from the `BasePokerPlayer` class.

Here is the code for our first AI. (Assume you saved this file at `~/dev/fish_player.py`)

```python
from pypokerengine.players import BasePokerPlayer

class FishPlayer(BasePokerPlayer):  # Do not forget to make the parent class "BasePokerPlayer"

    # We define the logic to make an action through this method. (So this method would be the core of your AI)
    def declare_action(self, valid_actions, hole_card, round_state):
        # valid_actions format => [raise_action_info, call_action_info, fold_action_info]
        call_action_info = valid_actions[1]
        action, amount = call_action_info["action"], call_action_info["amount"]
        return action, amount   # Action returned here is sent to the poker engine

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
```

If you are interested in what each callback method receives, see *AI_CALLBACK_FORMAT.md*.

## Play AI vs AI Poker Game

Let's play a poker game using our created `FishPlayer`.  
To start the game, we need to:

1. Define game rules through a `Config` object (e.g., start stack, blind amount, ante, blind structures).
2. Register your AI with the `Config` object.
3. Start the game and get the game result.

Here is the code to play poker for 10 rounds with our created `FishPlayer`.

```python
from pypokerengine.api.game import setup_config, start_poker

config = setup_config(max_round=10, initial_stack=100, small_blind_amount=5)
config.register_player(name="p1", algorithm=FishPlayer())
config.register_player(name="p2", algorithm=FishPlayer())
config.register_player(name="p3", algorithm=FishPlayer())
game_result = start_poker(config, verbose=1)
```

We set `verbose=1`, so simple game logs are output after the `start_poker` call.

```
Started the round 1
Street "preflop" started. (community card = [])
"p1" declared "call:10"
"p2" declared "call:10"
"p3" declared "call:10"
Street "flop" started. (community card = ['C4', 'C6', 'CA'])
"p2" declared "call:0"
"p3" declared "call:0"
"p1" declared "call:0"
Street "turn" started. (community card = ['C4', 'C6', 'CA', 'D4'])
"p2" declared "call:0"
"p3" declared "call:0"
"p1" declared "call:0"
Street "river" started. (community card = ['C4', 'C6', 'CA', 'D4', 'H2'])
"p2" declared "call:0"
"p3" declared "call:0"
"p1" declared "call:0"
"['p3']" won the round 1 (stack = {'p2': 90, 'p3': 120, 'p1': 90})
Started the round 2
...
"['p1']" won the round 10 (stack = {'p2': 30, 'p3': 120, 'p1': 150})
```

Finally, let's check the game result!

```python
>>> print game_result
{
  'rule': {'ante': 0, 'blind_structure': {}, 'max_round': 10, 'initial_stack': 100, 'small_blind_amount': 5},
  'players': [
    {'stack': 150, 'state': 'participating', 'name': 'p1', 'uuid': 'ijaukuognlkplasfspehcp'},
    {'stack': 30, 'state': 'participating', 'name': 'p2', 'uuid': 'uadjzyetdwsaxzflrdsysj'},
    {'stack': 120, 'state': 'participating', 'name': 'p3', 'uuid': 'tmnkoazoqitkzcreihrhao'}
  ]
} 
```

# Documentation

For more details, please check out the [documentation site](https://ishikota.github.io/PyPokerEngine/).
