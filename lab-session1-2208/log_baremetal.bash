#!/bin/bash
LOG_FILE="stats_baremetal.csv"
IFACE="eno1"   # Change this if your interface name differs

# Ensure log file exists with headers
if [ ! -s "$LOG_FILE" ]; then
    echo "Timestamp,CPU(%),Memory(RAM),Net I/O(RX/Tx),Block I/O(Read/Write)" >> "$LOG_FILE"
fi

while true; do
    TIMESTAMP=$(date +"%F %T")

    # --- CPU Usage (%) ---
    CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print 100 - $8}')  # idle -> usage

    # --- Memory Usage (used/total) ---
    MEM=$(free -m | awk 'NR==2{printf "%dMiB / %dMiB", $3,$2}')

    # --- Network I/O (cumulative MB) ---
    NET_IO=$(ip -s link show "$IFACE" | \
        awk '/RX:/ {getline; rx=$1} /TX:/ {getline; tx=$1} \
             END{printf "%.2fMB/%.2fMB", rx/1024/1024, tx/1024/1024}')

    # --- Block I/O (MB) ---
    BLK_READ=$(iostat -d -k 1 2 | awk 'NR>6 {read+=$3} END{printf "%.2fMB", read/1024}')
    BLK_WRITE=$(iostat -d -k 1 2 | awk 'NR>6 {write+=$4} END{printf "%.2fMB", write/1024}')
    BLOCK_IO="$BLK_READ/$BLK_WRITE"

    # --- Append to CSV ---
    echo "$TIMESTAMP,$CPU,$MEM,$NET_IO,$BLOCK_IO" >> "$LOG_FILE"

    sleep 1
done
