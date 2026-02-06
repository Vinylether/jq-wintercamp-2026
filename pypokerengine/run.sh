#!/bin/bash


if [ $# -ne 3 ]; then
    echo "Usage: $0 <number_of_rounds> <app_path> <mount_path>"
    exit 1
fi


TOTAL_ROUNDS=$1
APP_PATH=$2
MOUNT_PATH=$3



TIMESTAMP=$(date +%H%M%S)

BASE_OUTPUT_DIR="./output"
OUTPUT_DIR="$BASE_OUTPUT_DIR/$TIMESTAMP"
mkdir -p $OUTPUT_DIR

echo "Creating output directory: $OUTPUT_DIR"

 
MAX_PARALLEL=20
 
run_poker() {
    local round_num=$1
    local log_file="$OUTPUT_DIR/round_$round_num.log"
    
    echo "Starting round $round_num, logging to $log_file"
    docker run --rm --name="pokerengine_test_$round_num" \
        -v $APP_PATH:/app \
        -v $MOUNT_PATH:/app/players \
        pokerengine > "$log_file" 2>&1
}

 
for ((i=1; i<=$TOTAL_ROUNDS; i++)); do
 
    while [ $(jobs -p | wc -l) -ge $MAX_PARALLEL ]; do
        sleep 1
    done
     
    run_poker $i &
    
    echo "Started round $i"
done
 
wait

echo "All rounds completed. Results are saved in $OUTPUT_DIR/"
