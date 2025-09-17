# DS252 Lab (Week X): S3 → ECS (EC2) + ALB → FinOps

This lab extends your previous Flask-on-EC2 work into a production-style path with 3 activites:

1) **S3** — enable **versioning**, verify versions, and apply **lifecycle** rules  
2) **ECS (EC2) + ALB** — deploy the Flask app as a service with **CPU target-tracking autoscaling** and exercise it with **JMeter**  
3) **FinOps** — tag everything, set a **budget**, and attribute/estimate **the cost of this specific lab session**

---

## Table of Contents

- [0) Prerequisites](#0-prerequisites)
- [1) App Summary (Verbose)](#1-app-summary-verbose)
- [2) Local Setup](#2-local-setup)
- [Activity 1 — S3 Versioning + Lifecycle](#activity-1--s3-versioning--lifecycle)
- [Activity 2 — ECS(EC2) + ALB + Autoscaling + JMeter](#activity-2--ecsec2--alb--autoscaling--jmeter)
- [Activity 3 — FinOps: Tagging, Budget](#activity-3--finops-tagging-budget)
- [Cleanup](#cleanup)
- [Appendix A — Files & JSON Snippets](#appendix-a--files--json-snippets)
- [Appendix B — Troubleshooting Quick Reference](#appendix-b--troubleshooting-quick-reference)

---

## 0) Prerequisites

### Accounts & Permissions
- AWS account with CLI configured: `aws configure` (verify with `aws sts get-caller-identity`).
- Permissions (or a TA-managed role) for: **S3, ECR, ECS, EC2/Auto Scaling, ELB/ALB, CloudWatch, Budgets/Cost Explorer (read)**.

### Local Tools
- Git ≥ 2.30  
- Python ≥ 3.9 (3.11+ recommended), pip  
- Docker Desktop/Engine  
- Java 11+ (JRE)  
- Apache **JMeter 5.6+** (install script provided below)

### Pre-Lab Reading (skim)
- S3 **Versioning**: “current vs noncurrent version”, delete markers  
- S3 **Lifecycle**: transitions (Standard, Intelligent-Tiering, IA, Glacier* tiers) and expirations  
- ECS **Service Auto Scaling**: target tracking on CPU, scheduled actions  
- ALB basics: listeners, target groups, health checks

---

## 1) App Summary (Verbose)

We reuse the Flask app from the previous lab, extended to talk to S3. It expects:

- Env vars: **`S3_BUCKET`**, **`AWS_REGION`**
- AWS credentials from **ECS task role** (in ECS) or **instance profile** (in EC2)

**Endpoints**

- `GET /healthz`  
  Fast 200 for ALB health checks (verifies env + basic readiness).

- **S3 Object I/O (for versioning demos)**
  - `POST /text`  
    Body: `{"key":"path/file.txt","text":"Hello","metadata":{"author":"alice"}}`  
    Writes to `s3://$S3_BUCKET/<key>`. If versioning is ON, creates a **new version**.
  - `GET /text/<key>?versionId=`  
    Reads the latest version or a specific `versionId`.
  - `GET /list?prefix=`  
    Lists objects under a prefix.
  - `GET /list-versions?prefix=`  
    Lists **versions** and **delete markers** beneath a prefix.
  - `DELETE /object/<key>?versionId=`  
    Deletes a **specific** version (if provided), otherwise sets a **delete marker**.

- **Load endpoint (for JMeter)**
  - `GET /work?mode=read|write|mixed&size_kb=128&key=lab/test.bin`  
    Performs small S3 reads/writes per request (predictable CPU + I/O) to drive **ECS CPU target-tracking autoscaling**.

---

## 2) Local Setup

```bash
git clone https://github.com/dream-lab/ds252-2025.git
cd ds252-2025/lab-session2-2908

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

---
## Activity 1 — S3 Versioning & Lifecycle

**Set Variables**
```bash
export AWS_REGION=ap-south-1
export TEAM_ID=<your_netid_or_team>
export BUCKET=ds252-${TEAM_ID}-site
```
**Create Bucket**
```bash
aws s3api create-bucket \
  --bucket "$BUCKET" \
  --region "$AWS_REGION" \
  --create-bucket-configuration LocationConstraint="$AWS_REGION"
```
**Enable Versioning (then verify)**
```bash
aws s3api put-bucket-versioning \
  --bucket "$BUCKET" \
  --versioning-configuration Status=Enabled

aws s3api get-bucket-versioning --bucket $BUCKET
# Expected: {"Status":"Enabled"}
```
**Upload, Overwrite, List Versions, Restore (use .txt)**
```bash
echo "v1 content" > note.txt
aws s3 cp note.txt s3://$BUCKET/site/prod/note.txt

echo "v2 content" > note.txt
aws s3 cp note.txt s3://$BUCKET/site/prod/note.txt

aws s3api list-object-versions --bucket $BUCKET --prefix site/prod/note.txt
```
**Restore an older version (copy the chosen VersionId):**
```bash
aws s3api copy-object \
  --bucket $BUCKET \
  --copy-source $BUCKET/site/prod/note.txt?versionId=<OLD_VERSION_ID> \
  --key site/prod/note.txt
```
**Lifecycle Rules**
Common storage classes:
- Standard: default for frequent access
- Intelligent-Tiering: automatic tiering based on access patterns
- Standard-IA: infrequent access, lower storage $ / higher retrieval $
- One Zone-IA: single-AZ; cheaper, lower availability target
- Glacier Instant / Flexible / Deep Archive: archival tiers with varying retrieval latencies and lower $/GB

Industry rule patterns
- Prod site history: noncurrent -> IA @ 30 days, expire noncurrent @ 90 days
- Announcements: current expire @ 60 days; noncurrent @ 7 days
- Media: current -> Intelligent-Tiering @ 30d, Glacier @ 180d
- Compliance: Compliance=true tagged objects keep noncurrent 365d; don’t expire current


**Apply a minimal prod-style rule**
Create Lifecycle.json
```json
{
  "Rules": [
    {
      "ID": "prod-noncurrent-to-IA-then-expire",
      "Status": "Enabled",
      "Filter": { "Prefix": "site/prod/" },
      "NoncurrentVersionTransitions": [
        { "NoncurrentDays": 30, "StorageClass": "STANDARD_IA" }
      ],
      "NoncurrentVersionExpiration": { "NoncurrentDays": 90 },
      "AbortIncompleteMultipartUpload": { "DaysAfterInitiation": 7 }
    }
  ]
}
```

**Apply & verify:**

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket $BUCKET \
  --lifecycle-configuration file://lifecycle.json

aws s3api get-bucket-lifecycle-configuration --bucket $BUCKET
```

_Note: lifecycle actions apply over days. Today we’re setting the policy (governance); savings show up with time + data._

---
## Activity 2 — ECS(EC2) + ALB + Autoscaling + JMeter

You will push a prebuilt Docker image to ECR, create an ECS(EC2) cluster, configure ALB + Target Group, register a Task Definition, create a Service with CPU target tracking, then run 3 JMeter tests.

**Install JMeter**
```bash
#!/usr/bin/env bash
set -euo pipefail
JM_VERSION="${JM_VERSION:-5.6.3}"
INSTALL_DIR="$HOME/jmeter"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$INSTALL_DIR" "$BIN_DIR"

if ! command -v java >/dev/null 2>&1; then
  if [[ "$(uname)" == "Darwin" ]]; then
    brew install openjdk || true
  else
    sudo apt-get update -y && sudo apt-get install -y openjdk-11-jre || sudo apt-get install -y default-jre
  fi
fi

cd "$INSTALL_DIR"
curl -L -o apache-jmeter.tgz "https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-${JM_VERSION}.tgz"
tar xf apache-jmeter.tgz
ln -sf "$INSTALL_DIR/apache-jmeter-${JM_VERSION}/bin/jmeter" "$BIN_DIR/jmeter"

echo 'Add to your shell rc if needed: export PATH="$HOME/.local/bin:$PATH"'
echo "Then run: jmeter -v"
```

**Run and verify:**
```bash
bash install_jmeter.sh
jmeter -v
```

**Push Prebuilt Image to ECR**

```bash
# Load image locally
docker load -i ds252-flask-prebuilt.tar
docker images | grep ds252-flask

# Create ECR repo (once)
aws ecr create-repository --repository-name ds252-flask --region $AWS_REGION

# Login & push
aws ecr get-login-password --region $AWS_REGION \
 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.$AWS_REGION.amazonaws.com

docker tag ds252-flask:latest <ACCOUNT_ID>.dkr.ecr.$AWS_REGION.amazonaws.com/ds252-flask:latest
docker push <ACCOUNT_ID>.dkr.ecr.$AWS_REGION.amazonaws.com/ds252-flask:latest
```

**Create ECS(EC2) Cluster**

CLI Method:
```bash
aws ecs create-cluster --cluster-name ds252-cluster
```

Console:
- ECS -> Clusters -> Create -> EC2 Linux + Networking
- Capacity/ASG: 2× t3.small across 2 AZs
- Security Groups (SG):
    - ALB SG: inbound 80 (from your IP or 0.0.0.0/0 for demo)
    - Tasks SG: inbound 5000 from ALB SG only

**Create ALB + Target Group**
ALB (Application Load Balancer)
- Scheme: Internet-facing
- Subnets: two public subnets
- SG: ALB SG allowing 80
- Listener: HTTP :80 -> forward to target group

Target Group
- Target type: IP (for ECS awsvpc tasks)
- Port: 5000
- Health check: path /healthz, healthy=2, unhealthy=2, timeout=5s, interval=10s

**IAM Roles (Execution + Task Role)**
Execution Role (ecsTaskExecutionRole): lets ECS pull from ECR + write logs to CloudWatch
Task Role (e.g., ecsTaskRoleDs252): grants S3 access to your bucket


**Minimal S3 policy (attach to the task role; replace YOUR_BUCKET_NAME):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": ["s3:ListBucket"], "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME" },
    { "Effect": "Allow", "Action": ["s3:GetObject","s3:PutObject","s3:DeleteObject","s3:GetObjectVersion","s3:DeleteObjectVersion"], "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/*" }
  ]
}
```

**Register Task Definition**
```json
{
  "family": "ds252-flask",
  "networkMode": "awsvpc",
  "executionRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/ecsTaskRoleDs252",
  "cpu": "256",
  "memory": "512",
  "requiresCompatibilities": ["EC2"],
  "containerDefinitions": [
    {
      "name": "flask",
      "image": "<ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/ds252-flask:latest",
      "portMappings": [{ "containerPort": 5000, "protocol": "tcp" }],
      "environment": [
        { "name": "S3_BUCKET", "value": "<YOUR_S3_BUCKET>" },
        { "name": "AWS_REGION", "value": "<REGION>" }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ds252-flask",
          "awslogs-region": "<REGION>",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "essential": true
    }
  ]
}
```

**Create Service + Autoscaling**

CLI:
```bash
# Create service (attach to ALB target group)
aws ecs create-service \
  --cluster ds252-cluster \
  --service-name ds252-flask-svc \
  --task-definition ds252-flask \
  --desired-count 1 \
  --launch-type EC2 \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-AAAA,subnet-BBBB],securityGroups=[sg-tasks],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:<REGION>:<ACCOUNT_ID>:targetgroup/ds252-tg/XYZ,containerName=flask,containerPort=5000"

# Register scalable target + target tracking (CPU 50%)
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/ds252-cluster/ds252-flask-svc \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 --max-capacity 4

cat > cpu50.json <<'JSON'
{
  "TargetValue": 50.0,
  "PredefinedMetricSpecification": { "PredefinedMetricType": "ECSServiceAverageCPUUtilization" },
  "ScaleOutCooldown": 60,
  "ScaleInCooldown": 300
}
JSON

aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/ds252-cluster/ds252-flask-svc \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu50-target \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://cpu50.json
```

Console:

- Service type: EC2
- Cluster: ds252-cluster
- Task definition: ds252-flask
- Desired tasks: 1 (we’ll temporarily set to 0 for cold-start test)
- Networking: pick 2 subnets + Tasks SG
- Load balancing: choose your ALB + Target Group (port 5000)
- Service Auto Scaling:
    - Target tracking metric: ECSServiceAverageCPUUtilization
    - Target: 50%
    - Min=1, Max=4
    - Scale-out cooldown: 60–120s
    - Scale-in cooldown: 180–300s
    - (Optional) Scheduled action (predictive): set Desired=2 at a specific time


**JMeter Tests**

**JMeter GUI setup**

- Test Plan -> Thread Group
    - HTTP Request Defaults: Protocol http (or https), Server <ALB-DNS>, Port 80 (or 443)
    - HTTP Request: GET /work
    - Scheduler: Enabled -> set Duration per test

**Test 1 — Cold Start**

- Set Service Desired=0
- Thread Group: 10 users, 10s ramp, 2–3 min duration
- Start JMeter, then set Desired Tasks=1
- Watch: ECS Tasks show PROVISIONING -> PENDING -> RUNNING; ALB HealthyHostCount 0 → 1; CPU rises after healthy

**Test 2 — Reactive Scale-Out**

- Ensure Desired=1 initially
- Thread Group: 60 users, 60s ramp, 3–4 min duration
- Watch: ECS Service CPU > target -> Running tasks goes 1 -> 2 (-> 3)
- If no scale out: increase users to 80–120 or extend duration

**Test 3 — Stable State**

- Thread Group: 15–20 users, 30s ramp, 4–5 min duration
- Watch: CPU stays below target; Running tasks remain 1


## Activity 3 — FinOps: Tagging, Budget

We’ll tag resources for this specific session, create a budget filtered by those tags, and query Cost Explorer. Cost data is delayed; we’ll also estimate in real time using CloudWatch metrics.

**Tag Resources**

```bash
export COURSE_TAG_KEY=Course
export COURSE_TAG_VAL=DS252
export LAB_TAG_KEY=LabSession
export LAB_TAG_VAL=2025-09-17-Session3-<TEAM_ID>
```

**Apply tags (update ARNs accordingly):**

```bash
# S3 bucket
aws s3api put-bucket-tagging --bucket $BUCKET \
  --tagging "TagSet=[{Key=$COURSE_TAG_KEY,Value=$COURSE_TAG_VAL},{Key=$LAB_TAG_KEY,Value=$LAB_TAG_VAL}]"

# Bulk-tag example (ALB, TG, ECS service, ECR). Add your actual ARNs:
aws resourcegroupstaggingapi tag-resources \
  --resource-arn-list arn:aws:elasticloadbalancing:<REGION>:<ACCT>:loadbalancer/app/ds252-alb/..., \
arn:aws:elasticloadbalancing:<REGION>:<ACCT>:targetgroup/ds252-tg/..., \
arn:aws:ecs:<REGION>:<ACCT>:service/ds252-cluster/ds252-flask-svc, \
arn:aws:ecr:<REGION>:<ACCT>:repository/ds252-flask \
  --tags $COURSE_TAG_KEY=$COURSE_TAG_VAL $LAB_TAG_KEY=$LAB_TAG_VAL
```

_Note:Activate these keys as cost allocation tags: Billing → Cost allocation tags → Activate._


**Create a Budget for this Lab**
budget.json
```json
{
  "Budget": {
    "BudgetName": "DS252-Lab-2025-09-17",
    "BudgetLimit": { "Amount": "5.00", "Unit": "USD" },
    "CostFilters": {
      "TagKeyValue": [
        "Course$DS252",
        "LabSession$2025-09-17-Session3-<TEAM_ID>"
      ]
    },
    "CostTypes": { "IncludeDiscount": true, "IncludeRefund": false, "IncludeCredit": false, "UseAmortized": true },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  },
  "NotificationsWithSubscribers": [
    {
      "Notification": { "NotificationType": "ACTUAL", "ComparisonOperator": "GREATER_THAN", "Threshold": 80, "ThresholdType": "PERCENTAGE" },
      "Subscribers": [ { "Address": "<YOUR_EMAIL>", "SubscriptionType": "EMAIL" } ]
    }
  ]
}
```

Create:
```bash
aws budgets create-budget --account-id <ACCOUNT_ID> --cli-input-json file://budget.json
```

## Cleanup

- ECS Service: scale Desired=0 or delete service
- ALB + Target Group: delete
- ASG/EC2 capacity: scale to 0 or delete
- S3 Bucket: remove all objects & versions before deleting
- ECR repo: keep (small cost) or delete
- CloudWatch log groups: optional cleanup

## Troubleshoot

TODO
