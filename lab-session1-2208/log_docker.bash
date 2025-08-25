CONTAINER=077f781263c5
while true; do
  echo "$(date +%F\ %T),$(sudo docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}" $CONTAINER)" >> stats_$CONTAINER.csv
  sleep 1
done

