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

### Step 2.1 – Create Docker Image

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

## Task 3: Run Kubeflow Pipeline

### Step 3.1 – Compile and Submit Pipeline

```bash
pip install kfp
python scripts/compile_and_submit.py \
  --kfp_host "$KFP_HOST" \
  --bucket "$BUCKET" \
  --train_image "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_TRAIN:latest"
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
