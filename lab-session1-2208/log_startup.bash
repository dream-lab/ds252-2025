#!/bin/bash

LOG_FILE="startup_latency.csv"

# Add headers if file doesn't exist
if [ ! -s "$LOG_FILE" ]; then
    echo "Environment,Startup Latency" >> "$LOG_FILE"
fi

# --- Baremetal startup measurement ---
BAREMETAL_LAT=$( { /usr/bin/time -f "%E" echo ready >/dev/null; } 2>&1 )
echo "Baremetal,$BAREMETAL_LAT" >> "$LOG_FILE"

# --- VM startup measurement (wait until fully running) ---
VM_NAME="myvm"

# Use /usr/bin/time to measure the whole process
VM_LAT=$(/usr/bin/time -f "%E" bash -c '
    virsh start '"$VM_NAME"' >/dev/null
    while [ "$(virsh domstate '"$VM_NAME"')" != "running" ]; do
        sleep 1
    done
' 2>&1)

echo "VM,$VM_LAT" >> "$LOG_FILE"

# --- Docker container startup measurement ---
DOCKER_LAT=$( { /usr/bin/time -f "%E" docker run --rm lab-env echo ready >/dev/null; } 2>&1 )
echo "Docker,$DOCKER_LAT" >> "$LOG_FILE"
