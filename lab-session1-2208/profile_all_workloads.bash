#!/bin/bash

# --- Config ---
IFACE="eno1"   # Network interface
LOG_DIR="./logs"
mkdir -p "$LOG_DIR"

# Server IP for network test
NET_SERVER="10.24.24.2"
NET_PORT=5201

# Define workloads (command + label)
declare -A WORKLOADS
WORKLOADS["cpu"]="stress-ng --cpu 8 --timeout 60s --metrics-brief"
WORKLOADS["vm"]="stress-ng --vm 4 --vm-bytes 1G --timeout 60s --metrics-brief"
WORKLOADS["hdd"]="stress-ng --hdd 2 --hdd-bytes 2G --timeout 60s --metrics-brief"
WORKLOADS["net"]="iperf3 -c $NET_SERVER -t 60 -P 4"

# Function to log stats
log_stats() {
    local log_file="$1"
    echo "Timestamp,CPU(%),Memory(RAM),Net I/O(RX/Tx),Block I/O(Read/Write)" > "$log_file"
    while true; do
        TIMESTAMP=$(date +"%F %T")
        CPU=$(mpstat -P ALL 1 1 | awk '/Average/ && $2 ~ /[0-9]+/ {usr+=$3; sys+=$5; count++} END{print (usr+sys)/count}')
        MEM=$(free -m | awk 'NR==2{printf "%dMiB / %dMiB", $3,$2}')
        NET_IO=$(ip -s link show "$IFACE" | awk '/RX:/ {getline; rx=$1} /TX:/ {getline; tx=$1} END{printf "%.2fMB/%.2fMB", rx/1024/1024, tx/1024/1024}')
        BLK_READ=$(iostat -d -k 1 2 | awk 'NR>6 {read+=$3} END{printf "%.2fMB", read/1024}')
        BLK_WRITE=$(iostat -d -k 1 2 | awk 'NR>6 {write+=$4} END{printf "%.2fMB", write/1024}')
        BLOCK_IO="$BLK_READ/$BLK_WRITE"
        echo "$TIMESTAMP,$CPU,$MEM,$NET_IO,$BLOCK_IO" >> "$log_file"
        sleep 1
    done
}

# --- Main loop ---
for label in "${!WORKLOADS[@]}"; do
    echo "Starting workload: $label"
    LOG_FILE="$LOG_DIR/stats_${label}_$(date +%F_%H-%M-%S).csv"

    # Start logging in background
    log_stats "$LOG_FILE" &
    LOG_PID=$!

    # Run workload
    ${WORKLOADS[$label]}

    # Stop logging
    kill $LOG_PID
    wait $LOG_PID 2>/dev/null

    echo "Finished workload: $label"
done

echo "All workloads completed. Logs saved in $LOG_DIR"

