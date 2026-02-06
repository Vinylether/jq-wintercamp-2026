# jq_poker_competition
JQ wintership 2025 poker bot competition

Please only add/remove/modify files in `./app/players`!, the `./app/main.py` shall not be changed.

## Dependency

- Podman/Docker

## How to use

1. Build (for once) with

  ```
podman build --network=host -t pokerengine .
```

2. Run with

  (Replace `/path/to/app` with the absolute path to `app` folder.)

  ```
podman run -it --rm --name=pokerengine_test -v /path/to/app:/app pokerengine
```


  It has 3 optional parameters, run above command with an extra `-h` for details

  When debugging, `-g 1 -r 10 -c 1` is recommended.

3. Add custom poker bot

  You have full control over the `./app/players` folder, feel free to add your own bot or remove the existing dummy bots. You don't need to rebuild image after change `./app/players` folder, as you can see it is mounted to the container. The framework will automatically import all the bots in `./app/players` folder.
