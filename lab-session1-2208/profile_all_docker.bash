#!/bin/bash

# --- Config ---
CONTAINER="077f781263c5"      # Docker container ID or name
LOG_DIR="./docker_logs"
mkdir -p "$LOG_DIR"

# Network benchmark server and port
NET_SERVER="10.24.24.2"
NET_PORT=5201

# Define workloads (command + label)
declare -A WORKLOADS
WORKLOADS["cpu"]="stress-ng --cpu 8 --timeout 60s --metrics-brief"
WORKLOADS["vm"]="stress-ng --vm 4 --vm-bytes 1G --timeout 60s --metrics-brief"
WORKLOADS["hdd"]="stress-ng --hdd 2 --hdd-bytes 2G --timeout 60s --metrics-brief"
WORKLOADS["net"]="iperf3 -c $NET_SERVER -t 60 -P 4"

log_docker_stats() {
    local log_file="$1"
    echo "Timestamp,CPU(%),Memory(RAM),Net I/O(RX/Tx),Block I/O(Read/Write)" > "$log_file"

    # Get number of CPU cores for normalization
    CORES=$(nproc)

    while true; do
        TIMESTAMP=$(date +"%F %T")

        # Raw stats
        RAW=$(sudo docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}" "$CONTAINER")

        # Example RAW line:
        # 99.49%,170MiB / 3911MiB,233.46MB / 696.31MB,0.53MB / 173.85MB

        # Clean CPU (strip % and divide by cores)
        CPU=$(echo "$RAW" | awk -F',' -v cores="$CORES" '{gsub(/%/,"",$1); cpu=$1/cores; printf "%.3f", cpu}')

        # Rebuild line with cleaned CPU and keep other fields untouched
        LINE=$(echo "$RAW" | awk -F',' -v cpu="$CPU" '{gsub(/^ /,"",$2); gsub(/^ /,"",$3); gsub(/^ /,"",$4); print cpu "," $2 "," $3 "," $4}')

        echo "$TIMESTAMP,$LINE" >> "$log_file"
        sleep 1
    done
}



# --- Main loop ---
for label in "${!WORKLOADS[@]}"; do
    echo "Starting workload: $label"

    LOG_FILE="$LOG_DIR/stats_${label}_$(date +%F_%H-%M-%S).csv"

    # Start logging Docker stats in background
    log_docker_stats "$LOG_FILE" &
    LOG_PID=$!

    # Run workload inside container (including network benchmark)
    sudo docker exec "$CONTAINER" bash -c "${WORKLOADS[$label]}"

    # Stop logging
    kill $LOG_PID
    wait $LOG_PID 2>/dev/null

    echo "Finished workload: $label"
done

echo "All Docker workloads completed. Logs saved in $LOG_DIR"

