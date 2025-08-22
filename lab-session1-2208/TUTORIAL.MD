# Setup & Dependencies

## Install Docker

```bash
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl enable docker --now
sudo usermod -aG docker $USER
```

## Install KVM and Virt-Manager

```bash
sudo apt-get install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager
sudo usermod -aG libvirt $USER
```

## Download Ubuntu 22.04 ISO for VM

```bash
wget https://releases.ubuntu.com/22.04/ubuntu-22.04.5-live-server-amd64.iso
```

## Additional Dependencies

```bash
sudo apt update
sudo apt install -y procps iotop sysstat iperf3 stress-ng net-tools ifstat
```

---

# Benchmarking

## Startup Latency

```bash
/usr/bin/time -f "Startup latency: %E" docker run --rm lab-env echo "ready"
/usr/bin/time -f "Startup latency: %E" docker run --rm lab-env echo "ready" 2>> startup_latency.log
```

## CPU and Memory Usage

```bash
top
top -b -d 1 -n 300 > cpu_mem.log
```

```bash
mpstat           # average CPU stats
mpstat -P ALL    # per-CPU/core stats
mpstat 2 5       # every 2s, 5 times

free -m          # memory usage
```

## Disk I/O Monitoring

```bash
iotop
iotop -b -d 1 -n 300 > io_activity.log
iostat
```

## Network Throughput Monitoring

```bash
ifstat
ifconfig
ip -s link show eno1
```

---

# Workloads

## Compute-Intensive

```bash
stress-ng --cpu 8 --timeout 300s --metrics-brief
```

## Memory-Intensive

```bash
stress-ng --vm 4 --vm-bytes 1G --timeout 300s --metrics-brief
```

## I/O-Intensive

```bash
stress-ng --hdd 2 --hdd-bytes 2G --timeout 300s --metrics-brief
```

## Network-Intensive

```bash
iperf3 -c <server-ip> -t 300
```

---

# Docker

## Dockerfile

```dockerfile
# Use a base image
FROM ubuntu:22.04

# Install packages
RUN apt-get update && apt-get install -y curl iperf3 stress-ng

# Default command
CMD ["bash"]
```

## Build & Run

```bash
# Build image
docker build -t myimage .

# Run container
docker run -it --name mycontainer myimage bash

# Exec into running container
docker exec -it mycontainer bash
```

## Manage Containers & Images

```bash
# Stop / Start
docker stop mycontainer
docker start -ai mycontainer

# List containers
docker ps        # running
docker ps -a     # all

# List images
docker images

# Remove container & image
docker rm mycontainer
docker rmi myimage
```

---

# Virtual Machines

## Create VM with ISO

```bash
virt-install \
  --name ubuntu22-vm \
  --ram 4096 \
  --vcpus 2 \
  --disk path=/var/lib/libvirt/images/ubuntu22-vm.qcow2,size=20 \
  --os-variant ubuntu22.04 \
  --cdrom /path/to/ubuntu-22.04.5-live-server-amd64.iso \
  --network network=default \
  --graphics spice
```

### Options explained

* `--name` → VM name
* `--ram` → memory in MB
* `--vcpus` → number of CPUs
* `--disk` → VM storage (qcow2 recommended)
* `--os-variant` → optimize settings (`osinfo-query os` to list)
* `--cdrom` → ISO path (downloaded earlier)
* `--network network=default` → NAT networking
* `--graphics spice` → graphical console

---

## VM Management with virsh

```bash
# Get VM IP
virsh domifaddr myvm
ssh user@<vm-ip>
# Copy files between host and VM
scp /path/to/local/file user@<vm-ip>:/path/to/remote/destination
scp user@<vm-ip>:/path/to/remote/file /path/to/local/destination
```

```bash
# Stop / Force stop
virsh shutdown myvm
virsh destroy myvm

# Start VM
virsh start myvm
```

```bash
# List VMs
virsh list           # running
virsh list --all     # all
virsh domstate myvm
```

```bash
# Delete VM
virsh undefine myvm

# Remove disk image
rm ubuntu.qcow2
```
