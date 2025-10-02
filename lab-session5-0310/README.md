# DS252 • Lab — EKS + Prometheus/Grafana + HPA + Load Test

**Goal:** Stand up a small **Amazon EKS** cluster, deploy the DS252 **Flask `/hash` app** via Helm, install **Prometheus + Grafana** for monitoring, attach an **HPA** (CPU target), and **load test** to watch scale-out and CPU in real time.

---

## Learning Outcomes

* Create a managed K8s cluster on **AWS EKS** using `eksctl`. ([AWS Documentation][1])
* Install **metrics-server** and **kube-prometheus-stack** to collect & visualize metrics. ([Artifact Hub][2])
* Deploy an app with **Helm**, then autoscale with **HPA** (CPU). ([helm.sh][3])
* Use **JMeter** to generate load; interpret latency percentiles and CPU/replica graphs. ([GitHub][4])

---

## Prerequisites (install + read)

**Tools (install on your workstation or Cloud9):**

* **kubectl:** install for Linux/macOS/Windows. ([Kubernetes][6])
* **eksctl:** quick start & cluster management guide. ([AWS Documentation][1])
* **Helm 3:** install and quickstart. ([helm.sh][3])

**Reading (skim before lab):**

* EKS with `eksctl` – "Getting started". ([AWS Documentation][1])
* Helm install/usage basics. ([helm.sh][3])
* kube-prometheus-stack (what's inside: Prometheus, Grafana, exporters). ([Artifact Hub][7])
* metrics-server (why HPA needs it). ([GitHub][8])

> **Accounts & image:** You already have AWS accounts. Ensure your **Flask `/hash` image** we used in lab 3 is in **ECR** (e.g., `…dkr.ecr.ap-south-1.amazonaws.com/ds252-flask:hash-v2`).

---

## Architecture We'll Build

```
client (JMeter)
        |
   kubectl port-forward
        |
   Service (ClusterIP :80) → Deployment (Flask /hash on :5000)
        |                               |
        |                         metrics-server
        |                               |
  Prometheus <- kube-prometheus-stack -> Grafana dashboards
              (scrapes cluster + app)    (CPU, replicas, latency)
                          |
                          └── HPA (target CPU %) scales replicas
```

---

## Environment Variables (copy/paste)

```bash
export REGION=ap-south-1
export CLUSTER=ds252-observe
export NS_APP=app
export NS_MON=monitoring
# Your ECR image (already pushed in prior lab)
export APP_IMAGE="123456789012.dkr.ecr.${REGION}.amazonaws.com/ds252-flask:hash-v2"
```

---

## 1) Create the EKS Cluster (managed node group)

```bash
eksctl create cluster \
  --name $CLUSTER --region $REGION --version 1.29 \
  --managed --nodes 2 --node-type t3.medium \
  --with-oidc

kubectl cluster-info
kubectl get nodes
```

> Expect: 2 Ready worker nodes after ~10–12 minutes. ([AWS Documentation][1])

---

## 2) Install **metrics-server** (required for HPA)

```bash
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm repo update
helm upgrade --install metrics-server metrics-server/metrics-server -n kube-system \
  --set args="{--kubelet-preferred-address-types=InternalIP,Hostname,ExternalIP,--kubelet-insecure-tls}"

kubectl -n kube-system rollout status deploy/metrics-server
kubectl top nodes     # should show CPU/mem shortly
```

> metrics-server feeds CPU/Memory resource metrics to the HPA controller. ([Artifact Hub][2])

---

## 3) Install **Prometheus + Grafana** (kube-prometheus-stack)

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install kps prometheus-community/kube-prometheus-stack -n $NS_MON --create-namespace \
  --set grafana.adminPassword='admin' \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false

kubectl -n $NS_MON get pods
```

**Open UIs (port-forward):**

```bash
# Prometheus
kubectl -n $NS_MON port-forward svc/kps-kube-prometheus-stack-prometheus 9090:9090 >/dev/null &
# Grafana
kubectl -n $NS_MON port-forward svc/kps-grafana 3000:80 >/dev/null &
```

* Prometheus → [http://localhost:9090](http://localhost:9090)
* Grafana → [http://localhost:3000](http://localhost:3000) (admin / admin)

Dashboards to use:

* *Kubernetes / Compute Resources / Workload*
* *Kubernetes / Compute Resources / Namespace (Pods)*
* *Kubernetes / Compute Resources / Pod*
  ([Artifact Hub][7])

---

## 4) Deploy the DS252 Flask **`/hash`** App (Helm)

> Use the minimal Helm chart from the repo (Service on port **80** → container **5000**, readiness/liveness on `/healthz`, CPU requests/limits 250m).

```bash
kubectl create ns $NS_APP

helm upgrade --install labapp ./charts/ds252-hash -n $NS_APP \
  --set image.repository="${APP_IMAGE%:*}" \
  --set image.tag="${APP_IMAGE##*:}" \
  --set env.AWS_REGION="$REGION" \
  --set env.S3_BUCKET="" \
  --set resources.requests.cpu="250m" \
  --set resources.limits.cpu="250m"

kubectl -n $NS_APP get deploy,svc,pods
```

**Smoke test (port-forward):**

```bash
kubectl -n $NS_APP port-forward svc/labapp 8080:80 >/dev/null &
curl -s http://localhost:8080/healthz | jq .
curl -s -X POST http://localhost:8080/hash -d "data=hello-ds252" | jq .
```

> Helm install basics: `helm repo`, `helm upgrade --install`, chart values. ([helm.sh][3])

---

## 5) Add **HPA** (target 50% CPU, min=1, max=6)

```bash
kubectl -n $NS_APP autoscale deploy labapp --cpu-percent=50 --min=1 --max=6
kubectl -n $NS_APP get hpa
```

> HPA compares actual CPU to requested CPU (here 250m); target 50% ≈ 125m per replica.

---

## 6) **Load Test** the `/hash` endpoint

Record **Requests/sec, Avg, P50/P95/P99** from the summary. ([GitHub][4])

**JMeter:**
Use your prior JMX. Set a HTTP Request Sampler to **POST** `data=${__RandomString(32,abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789,)}` against `/hash`. CLI example:

```bash
jmeter -n -t hash-load.jmx \
  -JSERVER=localhost -JPORT=8080 -JPROTOCOL=http \
  -JTHREADS=80 -JRAMP=15 -JDURATION=120 \
  -l results.jtl -e -o out-report
```

---

## 7) Observe **Scale-Out** and **CPU** in Grafana

Run these in separate shells while the test is active:

```bash
kubectl -n $NS_APP get hpa -w
kubectl -n $NS_APP get deploy labapp -w
kubectl -n $NS_APP get pods -w
```

Open **Grafana**:

* Workload dashboard → select namespace **app**, workload **labapp** (watch CPU line and replica count).
* Pod dashboard → per-pod CPU (new pods appear as HPA scales).

If scaling is too slow, increase `-c` (hey) or threads (JMeter). You can also increase work globally by bumping the app env `MICRO_HASH_ROUNDS` and rolling the deployment.

---


## Troubleshooting

* **No metrics (`kubectl top` empty):** metrics-server not Ready—recheck Step 2. ([GitHub][8])
* **Grafana not opening:** confirm service name `kps-grafana` in namespace `monitoring`; ensure port-forward still running. ([Artifact Hub][7])
* **No scale-out:** increase concurrency/threads; verify HPA exists and `kubectl top pods -n app` shows CPU; ensure requests/limits set on the Deployment.
* **App 404/health fails:** confirm Service is `labapp` on port 80 and app listens on `0.0.0.0:5000`; probes on `/healthz`.
* **EKS creation errors:** ensure correct region & instance availability; retry `eksctl` with a different instance type if needed. ([AWS Documentation][9])

---

## Cleanup (avoid costs)

```bash
helm -n $NS_APP uninstall labapp
helm -n $NS_MON uninstall kps
eksctl delete cluster --name $CLUSTER --region $REGION
```

---

## Appendix: Quick Links

* **EKS getting started with eksctl** (official). ([AWS Documentation][1])
* **eksctl create/manage clusters** (reference). ([AWS Documentation][9])
* **helm install / quickstart**. ([helm.sh][10])
* **kube-prometheus-stack** (chart page). ([Artifact Hub][7])
* **metrics-server** (install/why). ([GitHub][8])
* **hey** (GitHub) and **man page**. ([GitHub][4])

---


[1]: https://docs.aws.amazon.com/eks/latest/userguide/getting-started-eksctl.html?utm_source=chatgpt.com "Get started with Amazon EKS – eksctl"
[2]: https://artifacthub.io/packages/helm/metrics-server/metrics-server?utm_source=chatgpt.com "metrics-server 3.13.0 · kubernetes-sigs ..."
[3]: https://helm.sh/docs/intro/install/?utm_source=chatgpt.com "Installing Helm"
[4]: https://github.com/rakyll/hey?utm_source=chatgpt.com "rakyll/hey: HTTP load generator, ApacheBench (ab) ..."
[5]: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html?utm_source=chatgpt.com "Install or update the latest version of the AWS CLI"
[6]: https://kubernetes.io/docs/tasks/tools/?utm_source=chatgpt.com "Install Tools"
[7]: https://artifacthub.io/packages/helm/prometheus-community/kube-prometheus-stack?utm_source=chatgpt.com "kube-prometheus-stack 77.12.0"
[8]: https://github.com/kubernetes-sigs/metrics-server?utm_source=chatgpt.com "kubernetes-sigs/metrics-server: Scalable and efficient ..."
[9]: https://docs.aws.amazon.com/eks/latest/eksctl/creating-and-managing-clusters.html?utm_source=chatgpt.com "Creating and managing clusters - Eksctl User Guide"
[10]: https://helm.sh/docs/helm/helm_install/?utm_source=chatgpt.com "Helm Install"

