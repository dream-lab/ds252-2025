# Lab: Kubeflow MLOps with Feast, KServe, and Drift Monitoring

**Goal:**

Students will build an end-to-end MLOps workflow using  **Kubeflow on AWS** . The lab demonstrates how data ingestion, feature storage, model training, deployment, and drift-based auto-retraining integrate in a real ML pipeline. The use case is built around the **E-Commerce Sales Dataset** from Kaggle.

---

## Architecture

```
+-------------------------------------------------------------+
|                       AWS EKS Cluster                       |
|                                                             |
|  +--------------------+     +---------------------------+   |
|  | Kubeflow Pipelines | --> | KServe (Model Serving)    |   |
|  | (train/retrain)    |     | + S3 / DynamoDB backend   |   |
|  +--------------------+     +---------------------------+   |
|             |                           |                   |
|             |                    +------+--------+          |
|             |                    | Drift Detector |         |
|             |                    | (CronJob + KS) |         |
|             |                    +------+--------+          |
|             |                           |                   |
|        +----+------+           +--------+---------+         |
|        |  S3 Bucket |<-------->| Feast Feature Store |      |
|        +-------------+         +--------------------+       |
+-------------------------------------------------------------+
```

---

## Prerequisites

**Start the EKS cluster from Lab 5.**

- Setup EKS Cluster from [Lab 5](https://github.com/dream-lab/ds252-2025/tree/main/lab-session5-0310) (Till Step 3 of Lab 5)
- Download and store [this](https://www.kaggle.com/datasets/thedevastator/unlock-profits-with-e-commerce-sales-data) dataset locally.

Ensure the following are configured:

* AWS CLI (`aws sts get-caller-identity`)
* IAM permissions for S3, ECR, DynamoDB, and EKS

---
## Task 1: Feature Store Integration with Feast

**Goal:** Use Feast to register features and store them in DynamoDB for online access.

### Step 1.1 – Install and Configure Feast

```bash
pip install "feast[aws]" pandas pyarrow boto3 s3fs
feast init ecommerce_features
```

Cleanup example file:
```bash
cd ecommerce_features/feature_repo
rm example.py example_repo.py || true
```

Edit `feature_store/feature_store.yaml`:

```yaml
project: ecommerce_features
registry: data/registry.db
provider: local

offline_store:
  type: file

online_store:
  type: dynamodb
  region: ap-south-1
```

### Step 1.2 – Prepare Dataset

Place your raw CSV file at:

```bash
ecommerce_features/feature_repo/data/raw/Amazon Sale Report.csv
```

Run ETL:

```bash
python scripts/prepare_dataset.py
```

### Step 1.3 – Apply and materialize

```bash
feast apply
feast materialize 2018-01-01T00:00:00 2026-01-01T00:00:00
```

Validate lookup:

```bash
python - <<'PY'
from feast import FeatureStore
store = FeatureStore(repo_path="ecommerce_features/feature_repo")

resp = store.get_online_features(
    features=[
        "sales_features:amount",
        "sales_features:qty",
        "sales_features:category",
    ],
    entity_rows=[{"order_id": "405-8078784-5731545"}],
).to_dict()

print(resp)
PY
```

**Outcome:** Features are now registered, versioned, and queryable in DynamoDB.

---

## Task 2: Build & Push Training Image
export variables:
```bash
export REGION=ap-south-1                                                                                                      11:08:52 AM
export ACCOUNT_ID=961341544454
export BUCKET=ml-bucket-nikhil                # <-- change to your bucket
export MODEL_PREFIX=models/sales-model        # path where model will land
export DATA_PREFIX=data                       # path where parquet
### Step 2.1 – Create Docker Image
```

```bash
cd pipelines/components/train
docker build -t $ECR_REPO_TRAIN:latest .
docker tag $ECR_REPO_TRAIN:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_TRAIN:latest
```

### Step 2.2 – Push to ECR

```bash
aws ecr create-repository --repository-name $ECR_REPO_TRAIN --region $AWS_REGION || true
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_TRAIN:latest
```

**Outcome:** Your model training container image is now available to Kubeflow.

---

## Task 3: Build & Run Kubeflow Pipeline

### Step 3.1 – Setup Kubeflow Pipelines:
Install cert-manager
```bash
kubectl create ns cert-manager --dry-run=client -o yaml | kubectl apply -f -
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm upgrade --install cert-manager jetstack/cert-manager \
  -n cert-manager --version v1.15.1 --set installCRDs=true

kubectl -n cert-manager rollout status deploy/cert-manager --timeout=120s
kubectl -n cert-manager get pods
```

Install Kubeflow Pipelines:
```bash
# Cluster-scoped CRDs
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=$PIPELINE_VERSION"
kubectl wait --for=condition=Established --timeout=90s crd/applications.app.k8s.io || true

# Namespaced resources (env/dev)
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/dev?ref=$PIPELINE_VERSION"

# Watch until mysql, minio, cache-server, metadata-*, ml-pipeline-*, ui are Running
watch -n2 'kubectl -n kubeflow get pods'
```

Install KServe:
```bash
helm repo add kserve https://ghcr.io/kserve/charts
helm repo update

# CRDs first
helm upgrade --install kserve-crd oci://ghcr.io/kserve/charts/kserve-crd \
  -n kserve --create-namespace --version v0.15.0

# Controller (RawDeployment works out-of-the-box; you can use it without Knative)
helm upgrade --install kserve oci://ghcr.io/kserve/charts/kserve \
  -n kserve --version v0.15.0

kubectl -n kserve get pods
```

Portforward and Access KFP UI:
```bash
# From your laptop:
kubectl -n kubeflow port-forward svc/ml-pipeline-ui 8080:80
# Open: http://localhost:8080
```

Set Appropriate Permissions:
```bash
# Enable IRSA (OIDC) on the cluster
eksctl utils associate-iam-oidc-provider --cluster "$CLUSTER" --region "$REGION" --approve

# Create a policy (edit your bucket/permissions)
cat > policy.json <<'JSON'
{
  "Version":"2012-10-17",
  "Statement":[
    {"Effect":"Allow","Action":["dynamodb:GetItem","dynamodb:BatchGetItem","dynamodb:Query","dynamodb:Scan"],"Resource":"*"},
    {"Effect":"Allow","Action":["s3:GetObject","s3:PutObject","s3:ListBucket"],"Resource":["arn:aws:s3:::ds252-ml-models-nikhil","arn:aws:s3:::ds252-ml-models-nikhil/*"]}
  ]
}
JSON
aws iam create-policy --policy-name kfp-feast-s3-policy --policy-document file://policy.json

# Bind policy to a ServiceAccount (used when creating the Run in KFP UI)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
eksctl create iamserviceaccount \
  --cluster "$CLUSTER" --region "$REGION" \
  --namespace kubeflow --name kfp-runner \
  --attach-policy-arn arn:aws:iam::$ACCOUNT_ID:policy/kfp-feast-s3-policy \
  --approve --override-existing-serviceaccounts
```


If Pods are in CrashLoop (Install standalone KFP):
```bash
# 1) Install (or re-apply) KFP cluster-scoped CRDs
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=$PIPELINE_VERSION"
kubectl wait --for=condition=established --timeout=60s crd/applications.app.k8s.io

# 2) Install the platform-agnostic env (works off-cloud, incl. EKS)
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/platform-agnostic?ref=$PIPELINE_VERSION"
```

**Outcome:** Kubeflow orchestrates training and saves the model artifact in S3.

---

## Task 4: Deploy Model with KServe

### Step 4.1 – Create the InferenceService

Edit `serving/kserve_inference.yaml` with your bucket name:

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: ecommerce-sales-model
spec:
  predictor:
    sklearn:
      storageUri: "s3://$BUCKET/models/ecommerce/"
```

Deploy:

```bash
kubectl apply -f serving/kserve_inference.yaml
kubectl get inferenceservices
```

### Step 4.2 – Test the Endpoint

```bash
MODEL_URL=$(kubectl get inferenceservice ecommerce-sales-model -o jsonpath='{.status.url}')
curl -v -X POST "${MODEL_URL}/v1/models/ecommerce-sales-model:predict" \
  -d '{"instances": [[3, 0.10, 40.0]]}'
```

**Outcome:** Model serving endpoint live with autoscaling via KServe.

---

## Task 5: Drift Monitoring & Auto-Retraining

### Step 5.1 – Create Baseline & Live Data

```bash
aws s3 cp s3://$BUCKET/data/ecommerce_sales.csv s3://$BUCKET/baseline/train.csv
aws s3 cp s3://$BUCKET/data/ecommerce_sales.csv s3://$BUCKET/live/window.csv
```

### Step 5.2 – Build Monitoring Image

```bash
cd monitoring
docker build -t ecommerce-monitor:latest .
docker tag ecommerce-monitor:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/ecommerce-monitor:latest
aws ecr create-repository --repository-name ecommerce-monitor --region $AWS_REGION || true
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/ecommerce-monitor:latest
```

### Step 5.3 – Deploy CronJob

Edit `monitoring/cronjob.yaml` with your bucket + ECR details and apply:

```bash
kubectl apply -f monitoring/cronjob.yaml
```

**Outcome:** Every 15 minutes, a CronJob runs KS-tests between baseline and live windows, retriggering training if drift is detected.

---

## Cleanup

```bash
kubectl delete -f serving/kserve_inference.yaml
kubectl delete -f monitoring/cronjob.yaml
aws s3 rm s3://$BUCKET --recursive
aws ecr delete-repository --repository-name $ECR_REPO_TRAIN --force --region $AWS_REGION
aws ecr delete-repository --repository-name ecommerce-monitor --force --region $AWS_REGION
```

---
