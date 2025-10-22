# Lab: IAM + OpenTelemetry + Prometheus on Kubernetes


## Goal:
Students will explore how IAM governs access to cloud resources from inside Kubernetes, and how OpenTelemetry and Prometheus can instrument, collect, and visualize application metrics and traces.
We’ll use the same EKS cluster from previous labs.

## Architecture:
```
+---------------------------------------------------------+
|                     AWS EKS Cluster                     |
|                                                         |
|  +--------------------+     +------------------------+  |
|  | Flask App (OTel)   | --> | OTel Collector         |  |
|  | Emits traces/metrics|    | (aggregates + exports) |  |
|  +--------------------+     +-----------+------------+  |
|                                     |                 |
|                       +-------------+------------+     |
|                       | Prometheus (scrapes)     |     |
|                       +-------------+------------+     |
|                                     |                 |
|                               +-----+-----+           |
|                               | Grafana    |           |
+-------------------------------+-------------+----------+
             |
        IAM Role (IRSA)
        grants limited access to CloudWatch/AMP
```

## Prerequisites:

EKS Cluster ready (from [lab 5]([url](https://github.com/dream-lab/ds252-2025/tree/main/lab-session5-0310))):
```
kubectl get nodes
```

Helm installed:
```
helm version
```

AWS CLI configured:
```
aws sts get-caller-identity
```

IRSA enabled cluster:
```
eksctl utils associate-iam-oidc-provider --cluster <cluster-name> --approve
```


## Task 1: IAM: Connect Kubernetes to AWS Securely (IRSA)

- Create IAM policy for metrics and traces
This policy allows pushing metrics/traces to CloudWatch and AMP if needed.

```
cat > prometheus-iam-policy.json <<'JSON'
```

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow",
      "Action": [
        "aps:RemoteWrite",
        "aps:QueryMetrics",
        "aps:GetSeries",
        "aps:GetLabels",
        "aps:GetMetricMetadata"
      ],
      "Resource": "*"
    },
    { "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

```bash
POLICY_ARN=$(aws iam create-policy \
  --policy-name ds252-prometheus-otel-policy \
  --policy-document file://prometheus-iam-policy.json \
  --query 'Policy.Arn' --output text)
```

- Create IAM role for Prometheus via IRSA
```bash
eksctl create iamserviceaccount \
  --name prometheus-sa \
  --namespace monitoring \
  --cluster <cluster-name> \
  --attach-policy-arn $POLICY_ARN \
  --approve
```

## Task 2: Install Prometheus & Grafana Stack
- Add repo & install chart

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

kubectl create namespace monitoring || true

helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --set serviceAccounts.server.name=prometheus-sa \
  --set serviceAccounts.server.create=false
```

- Access dashboards locally
```bash
kubectl -n monitoring port-forward svc/prometheus-grafana 3000:80
# Grafana at: http://localhost:3000  (admin / prom-operator)
```

- Explore
Go to Dashboards -> Kubernetes / Compute Resources / Namespace and observe live metrics for CPU, memory, pods

## Task 3: Deploy the Instrumented App with OpenTelemetry

- Apply Deployment
```bash
kubectl create ns app || true

cat <<'YAML' | kubectl apply -n app -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-flask
spec:
  replicas: 2
  selector:
    matchLabels:
      app: otel-flask
  template:
    metadata:
      labels:
        app: otel-flask
    spec:
      containers:
      - name: flask
        image: 961341544454.dkr.ecr.ap-south-1.amazonaws.com/ds252-flask:latest
        env:
        - name: OTEL_SERVICE_NAME
          value: ds252-hash
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: http://otel-collector.monitoring.svc.cluster.local:4317
        - name: OTEL_TRACES_EXPORTER
          value: otlp
        - name: OTEL_METRICS_EXPORTER
          value: otlp
        ports:
        - containerPort: 5000
---
apiVersion: v1
kind: Service
metadata:
  name: otel-flask
spec:
  type: ClusterIP
  selector:
    app: otel-flask
  ports:
  - port: 80
    targetPort: 5000
YAML
```

- Deploy OpenTelemetry Collector
```bash
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update

helm upgrade --install otel-collector open-telemetry/opentelemetry-collector \
  -n monitoring \
  --set mode=deployment \
  --set config.exporters.prometheus.endpoint="0.0.0.0:8889" \
  --set config.receivers.otlp.protocols.grpc.endpoint="0.0.0.0:4317"
```

- Verify Metrics in Prometheus
Open Prometheus -> Targets -> confirm:

```otel-collector``` exporter appears as UP
Queries like:
```SCSS
rate(flask_http_request_duration_seconds_count[1m])
```
show your app’s HTTP metrics.

# Task 4: Explore IAM + Observability Connections
Go to AWS IAM Console -> Roles -> find ```eksctl-*-prometheus-sa-role```
Observe:

- Trust policy (OIDC provider)
- Permissions policy (aps:*, cloudwatch:*)

Go to Prometheus Console -> “Configuration” -> check external write permissions.


Questions to thunk about:
- Why do we need IRSA instead of embedding AWS credentials in pods?
- What happens if this IAM role loses the aps:RemoteWrite permission?

# Task 5: Explore OpenTelemetry

- Create JMeter Test Plan:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Hash Load Test" enabled="true">
      <stringProp name="TestPlan.comments">Simple load generator for /hash endpoint</stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.tearDown_on_shutdown">true</boolProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments">
        <collectionProp name="Arguments.arguments">
          <elementProp name="SERVER" elementType="Argument"><stringProp name="Argument.value">${__P(SERVER,localhost)}</stringProp></elementProp>
          <elementProp name="PORT" elementType="Argument"><stringProp name="Argument.value">${__P(PORT,80)}</stringProp></elementProp>
          <elementProp name="PROTOCOL" elementType="Argument"><stringProp name="Argument.value">${__P(PROTOCOL,http)}</stringProp></elementProp>
        </collectionProp>
      </elementProp>
      <stringProp name="TestPlan.user_define_classpath"></stringProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Users" enabled="true">
        <stringProp name="ThreadGroup.num_threads">${__P(THREADS,60)}</stringProp>
        <stringProp name="ThreadGroup.ramp_time">${__P(RAMP,10)}</stringProp>
        <stringProp name="ThreadGroup.duration">${__P(DURATION,120)}</stringProp>
        <boolProp name="ThreadGroup.scheduler">true</boolProp>
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="POST /hash" enabled="true">
          <stringProp name="HTTPSampler.domain">${SERVER}</stringProp>
          <stringProp name="HTTPSampler.port">${PORT}</stringProp>
          <stringProp name="HTTPSampler.protocol">${PROTOCOL}</stringProp>
          <stringProp name="HTTPSampler.path">/hash</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
            <collectionProp name="Arguments.arguments">
              <elementProp name="data" elementType="HTTPArgument">
                <boolProp name="HTTPArgument.always_encode">false</boolProp>
                <stringProp name="Argument.name">data</stringProp>
                <stringProp name="Argument.value">${__RandomString(10,abcdefghijklmnopqrstuvwxyz)}</stringProp>
              </elementProp>
            </collectionProp>
          </elementProp>
        </HTTPSamplerProxy>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
```

- Run the Load Test
Forward your app’s service (if not already public):
```bash
kubectl -n app port-forward svc/otel-flask 8080:80
```

Run JMeter:
```bash
jmeter -n -t hash-load.jmx \
  -JSERVER=localhost -JPORT=8080 -JPROTOCOL=http \
  -JTHREADS=60 -JRAMP=15 -JDURATION=120 \
  -l results.jtl
```

- Observe load on Grafana
