#!/bin/bash

# Detect container runtime (docker or podman)
if command -v docker >/dev/null 2>&1; then
    CONTAINER_CMD="docker"
    echo "✅ Detected Docker"
elif command -v podman >/dev/null 2>&1; then
    CONTAINER_CMD="podman"
    echo "✅ Detected Podman"
else
    echo "❌ Error: Neither Docker nor Podman is installed or not in PATH"
    echo "Please install Docker or Podman first. See install_docker.md or install_podman.md for instructions."
    exit 1
fi

# Default to 5 rounds for testing
TOTAL_ROUNDS=5

# Get script directory and set paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_PATH="$SCRIPT_DIR/app"
MOUNT_PATH="$SCRIPT_DIR/app/players"

TIMESTAMP=$(date +%H%M%S)

BASE_OUTPUT_DIR="./output"
OUTPUT_DIR="$BASE_OUTPUT_DIR/$TIMESTAMP"
mkdir -p $OUTPUT_DIR

MAX_PARALLEL=20

run_poker() {
    local round_num=$1
    local log_file="$OUTPUT_DIR/round_$round_num.log"

    $CONTAINER_CMD run --rm --name="pokerengine_test_$round_num" \
        -v $APP_PATH:/app \
        -v $MOUNT_PATH:/app/players \
        pokerengine > "$log_file" 2>&1
    return $?
}

SUCCESS_COUNT=0
FAIL_COUNT=0

for ((i=1; i<=$TOTAL_ROUNDS; i++)); do

    while [ $(jobs -p | wc -l) -ge $MAX_PARALLEL ]; do
        sleep 1
    done

    run_poker $i &
done

wait

# Check results
for ((i=1; i<=$TOTAL_ROUNDS; i++)); do
    log_file="$OUTPUT_DIR/round_$i.log"
    if [ -f "$log_file" ]; then
        # Check if log file contains error indicators or is empty
        if [ -s "$log_file" ] && ! grep -qi "error\|failed\|exception" "$log_file"; then
            # Check if it contains game results (winner information)
            if grep -qi "winner\|game\|stack" "$log_file"; then
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            else
                FAIL_COUNT=$((FAIL_COUNT + 1))
            fi
        else
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
done

if [ $FAIL_COUNT -eq 0 ]; then
    echo "✅ SUCCESS:"
    exit 0
else
    echo "❌ FAILED:"
    echo "Check log files in $OUTPUT_DIR/ for error details."
    exit 1
fi
