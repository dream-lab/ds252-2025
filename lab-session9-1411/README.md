# **K3s Edge Computing Lab**

```bash
                     ┌───────────────────────────┐
                     │        K3s Server         │
                     │  (Control Plane + API)    │
                     │                           │
                     │  - kube-apiserver         │
   kubectl ────────▶   - etcd-lite / sqlite      │
                     │  - scheduler              │
                     │  - controller-manager     │
                     │                           │
                     └───────────┬───────────────┘
                                 │
                                 │ K3S_URL=https://<SERVER_PRIVATE_IP>:6443
                                 │ K3S_TOKEN=<TOKEN>
                                 │
                     ┌───────────▼───────────────┐
                     │        K3s Agent          │
                     │       (Edge Node)         │
                     │                           │
                     │  - kubelet                │
                     │  - containerd             │
                     │  - flannel (CNI)          │
                     │                           │
                     └───────────┬───────────────┘
                                 │
                                 │ CNI Overlay Network (Flannel)
                                 │   Pod-to-Pod: 10.42.x.x
                                 │
       ┌─────────────────────────▼─────────────────────────┐
       │                   Workloads                       │
       │                                                   │
       │  compute-python Job -> runs ONLY on edge node      │
       │  via: nodeSelector: { node-type: edge }           │
       │                                                   │
       │  pods spread across edge nodes as cluster scales  │
       └───────────────────────────────────────────────────┘

```



This tutorial walks you through:

* Setting up a **K3s lightweight Kubernetes cluster** using **two EC2 instances**
* Labeling an **edge node** so only it runs compute workloads
* Running a **Python CPU compute task**
* Scaling the cluster
* Observing **job timing** using `kubectl describe job`

## 1. Launch Fresh EC2 Instances (AWS Console)

Create **two EC2 instances** in the same VPC + subnet:

* AMI: **Ubuntu Server 22.04**
* Type: **t2.micro or t3.micro**
* Names:
  * `k3s-server`
  * `k3s-agent`
* Security Group (same SG):
  * Allow inbound:
    * SSH (22) from your IP
    * NodePort 30080 (optional, for demo)
  * Allow all traffic **within the same SG**

## 2. Install K3s Server (EC2 #1)

SSH:

```bash
ssh -i ~/.ssh/YOUR_KEY.pem ubuntu@<SERVER_PUBLIC_IP>
sudo -s
apt update && apt -y upgrade
apt install -y curl
```

Install server:

```bash
curl -sfL https://get.k3s.io | sh -
```

Check:

```bash
systemctl status k3s --no-pager
kubectl get nodes -o wide
```

Extract join token:

```bash
cat /var/lib/rancher/k3s/server/node-token
```

Get private IP:

```bash
hostname -I
```

## 3. Install K3s Agent (EC2 #2)

SSH:

```bash
ssh -i ~/.ssh/YOUR_KEY.pem ubuntu@<AGENT_PUBLIC_IP>
sudo -s
apt update && apt -y upgrade
apt install -y curl
```

Install agent:

```bash
curl -sfL https://get.k3s.io | \
  K3S_URL="https://<SERVER_PRIVATE_IP>:6443" \
  K3S_TOKEN="<TOKEN>" \
  sh -
```

Check:

```bash
systemctl status k3s-agent --no-pager
```

Verify on server:

```bash
kubectl get nodes -o wide
```


## 4. Label the Edge Node (Only Edge Runs Compute)

Find nodes:

```bash
kubectl get nodes
```

Label it:

```bash
kubectl label node ip-172-31-5-182 node-type=edge
```

Verify:

```bash
kubectl get nodes --show-labels
```



## 5. Create the Compute Job (Python CPU Task)

Create file:

```bash
cat << 'EOF' > compute-python.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: compute-python
spec:
  completions: 20          # total tasks
  parallelism: 2           # tasks run in parallel
  template:
    spec:
      nodeSelector:
        node-type: edge    # only run on edge node
      containers:
      - name: py-worker
        image: python:3.11-slim
        command:
        - python
        - -u
        - -c
        - |
          import time, os
          MOD = 1_000_000_007
          result = 1
          print("Starting compute task on node:", os.uname().nodename, flush=True)
          for i in range(2_000_000):
              result = (result * 13) % MOD
          print("Finished. Result:", result, flush=True)
      restartPolicy: Never
EOF

```

Apply:

```bash
kubectl apply -f compute-python.yaml
```

Watch tasks:

```bash
kubectl get pods -o wide -w
kubectl logs -f -l job-name=compute-python
```


## 6. Observe Timing

After the job finishes, run:

```bash
kubectl describe job compute-python
```

Look for:

```bash
Start Time:      2025-11-14T12:01:22Z
Completion Time: 2025-11-14T12:01:37Z
```

## 7. Scaling Test — Add Another Edge Node

Create a new EC2 instance and add it to the cluster.
Time the job:

```bash
kubectl describe job compute-python
```
