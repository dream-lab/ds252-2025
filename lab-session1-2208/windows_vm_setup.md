# Guide: Running Lab Environments on Windows (WSL, Docker, and VM with VNC)

## Prerequisites

- Windows 10/11 PC with **WSL2** enabled  
- **Ubuntu 22.04** installed in WSL2  
- Stable internet connection  
- At least **20GB** free disk space  

---

## Step 1: Set Up WSL2 on Windows

```powershell
wsl --install -d Ubuntu-22.04
```
Restart your computer if prompted.

Verify installation:
```powershell
wsl --version
```

---

## Step 2: Install Docker inside WSL

```bash
sudo apt-get update
sudo apt-get install docker.io -y
sudo systemctl enable docker --now
sudo usermod -aG docker $USER
```
Log out and back in for group changes to apply.

---

## Step 3: Install KVM and Virt-Manager inside WSL

```bash
sudo apt-get install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager
sudo systemctl enable --now libvirtd
```
> ⚠️ WSL2 has no hardware KVM, so QEMU runs in software emulation (slower, but functional).

---

## Step 4: Download Ubuntu ISO for VM

```bash
sudo mkdir -p /var/lib/libvirt/boot /var/lib/libvirt/images
sudo curl -L -o /var/lib/libvirt/boot/ubuntu-22.04.5-live-server-amd64.iso \
https://releases.ubuntu.com/22.04.5/ubuntu-22.04.5-live-server-amd64.iso
```

---

## Step 5: Launch Docker Environment

**Dockerfile**
```dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y --no-install-recommends \
    stress-ng procps sysstat ifstat iperf3 iproute2 net-tools \
    && rm -rf /var/lib/apt/lists/*
CMD ["/bin/bash"]
```

**Build and Run**
```bash
docker build -t lab-env .
docker run -it --name lab-env-1 -v ~/lab-logs:/logs lab-env /bin/bash
```

---

## Step 6: Launch VM Environment with VNC

```bash
sudo virt-install \
  --name ubuntu22-cli \
  --memory 4096 --vcpus 2 \
  --disk path=/var/lib/libvirt/images/ubuntu22-cli.qcow2,size=30,format=qcow2,bus=virtio \
  --os-variant ubuntu22.04 \
  --network network=default,model=virtio \
  --graphics vnc,listen=0.0.0.0 \
  --video qxl \
  --cdrom /var/lib/libvirt/boot/ubuntu-22.04.5-live-server-amd64.iso \
  --boot cdrom,hd,menu=on \
  --wait -1 \
  --virt-type qemu
```

---

## Step 7: Connect to VM via VNC

Check VM state:
```bash
sudo virsh domstate ubuntu22-cli
```

Find VNC display:
```bash
sudo virsh vncdisplay ubuntu22-cli
```

Check listener:
```bash
ss -lntp | grep 59
```

Get WSL IP:
```bash
hostname -I | awk '{print $1}'
```

On Windows, install a VNC client (RealVNC, TightVNC, TigerVNC).  
Connect to:
```
<WSL-IP>:5900
```

---

## Step 8: Run Workloads in All Environments

Each workload runs for 300 seconds.

**Compute-Intensive**
```bash
stress-ng --cpu 8 --timeout 300s --metrics-brief
```

**Memory-Intensive**
```bash
stress-ng --vm 4 --vm-bytes 1G --timeout 300s --metrics-brief
```

**I/O-Intensive**
```bash
stress-ng --hdd 2 --hdd-bytes 2G --timeout 300s --metrics-brief
```

**Network-Intensive**
```bash
iperf3 -c <server-ip> -t 300
```

---

## Step 9: Collect Metrics

**Startup Latency**
```bash
/usr/bin/time -f "Startup latency: %E" docker run --rm lab-env echo "ready" 2>> startup_latency.log
/usr/bin/time -f "Startup latency: %E" virsh start ubuntu22-cli --console 2>> startup_latency.log
```

**CPU & Memory**
```bash
top -b -d 1 -n 300 > cpu_mem.log
```

**Disk I/O**
```bash
iotop -b -d 1 -n 300 > io_activity.log
```

**Network Throughput**
```bash
ifstat -t 1 300
