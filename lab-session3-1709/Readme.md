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

### Local Tools
- Git ≥ 2.30  
- Python ≥ 3.9 (3.11+ recommended), pip  
- Docker Desktop/Engine  
- Java 11+ (JRE)  
- Apache **JMeter 5.6+** (install script provided below)

### Pre-Lab Reading
- [S3 Versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html?utm_source=chatgpt.com)
- [S3 Lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html?utm_source=chatgpt.com)
- [ECS Service Autoscaling](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-autoscaling-targettracking.html?utm_source=chatgpt.com)
- [ALB Target Groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html?utm_source=chatgpt.com)
- [AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-create.html?utm_source=chatgpt.com)
- [JMeter](https://jmeter.apache.org/?utm_source=chatgpt.com)

### JMeter Setup

JMeter is Java-based. Install a supported OpenJDK first, then JMeter.

**[Linux (Ubuntu/Debian)](https://downloads.apache.org/jmeter/binaries/)**

```bash
# Java
sudo apt-get update
sudo apt-get install -y openjdk-17-jre

# JMeter (download + unpack to ~/jmeter)
cd ~
curl -L -o apache-jmeter.tgz https://downloads.apache.org/jmeter/binaries/apache-jmeter-5.6.3.tgz
mkdir -p ~/jmeter && tar -xzf apache-jmeter.tgz -C ~/jmeter --strip-components=1

# Add to PATH (temporary for this shell)
export PATH="$HOME/jmeter/bin:$PATH"

# Verify
java -version
jmeter -v
```

**[Windows WSL](https://mati-qa.medium.com/jmeter-in-wsl-how-to-start-simple-use-case-b67b9063902b)**

```bash
sudo apt-get update && sudo apt-get install -y openjdk-17-jre
curl -L -o apache-jmeter.tgz https://downloads.apache.org/jmeter/binaries/apache-jmeter-5.6.3.tgz
mkdir -p ~/jmeter && tar -xzf apache-jmeter.tgz -C ~/jmeter --strip-components=1
export PATH="$HOME/jmeter/bin:$PATH"
jmeter -n -v
```

**macOS**
```bash
# Java (Homebrew)
brew install openjdk

# JMeter
cd ~
curl -L -o apache-jmeter.tgz https://downloads.apache.org/jmeter/binaries/apache-jmeter-5.6.3.tgz
mkdir -p ~/jmeter && tar -xzf apache-jmeter.tgz -C ~/jmeter --strip-components=1

# PATH (temporary)
export PATH="$HOME/jmeter/bin:$PATH"

# Verify
java -version
jmeter -v
```


### AWS ECR/ECS/ALB prerequisites to confirm

- IAM permissions: You must be able to use S3, ECR, ECS, EC2/Auto Scaling, ALB, CloudWatch, Budgets/Cost Explorer
- Region: set your default region to ap-south-1

```bash
aws configure set default.region ap-south-1
aws sts get-caller-identity
```
- Docker -> ECR login

```bash
aws ecr get-login-password --region ap-south-1 \
  | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com
```

### “Verify everything” checklist

- [AWS CLI: aws sts get-caller-identity prints your Account + ARN](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html?utm_source=chatgpt.com)
- [Docker: docker run --rm hello-world prints the hello message](https://docs.docker.com/desktop/?utm_source=chatgpt.com)
- [Java & JMeter: java -version and jmeter -v both work](https://jmeter.apache.org/changes.html?utm_source=chatgpt.com)
- [Browser access: You can reach AWS Console and navigate to S3/ECS/EC2/ALB/Billing pages.](https://aws.amazon.com/console/)

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
  --copy-source "$BUCKET/site/prod/note.txt?versionId=<OLD_VERSION_ID>" \
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
# Build image locally
docker build -t ${REPO}:latest .
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

Once the docker image is pushed to ECR, we will start setting up the cluster. For the cluster to work there are 4 primary steps that we generally need to follow:
- Create a Target Group (for your tasks)
    - A registry of where to send traffic—ECS tasks register their IP:port here, and the load balancer health-checks these targets to route only to healthy ones.
- Create an Application Load Balancer (ALB)
    - A public entry point that distributes HTTP traffic across tasks, does health checks, and provides a stable DNS name instead of hitting task IPs directly
- Create the ECS cluster with capacity
    - A logical pool of compute where ECS runs your tasks (either on your EC2 instances or on Fargate); services schedule and scale tasks inside this cluster.
- Create the Task Definition
    - The blueprint for a containerized app—image, CPU/memory, ports, env vars, roles, and logging—that ECS uses to launch each task.
---

Console:

**Create a Target Group**

Why: The ALB needs a target; with awsvpc tasks, the target type must be IP so task ENIs can register.

Console -> EC2 -> Target groups -> Create target group

- Target type: IP addresses
- Name: ds252-tg
- Protocol/Port: HTTP / 5000
- VPC: your VPC
- Health checks: Protocol HTTP, Path /healthz, Healthy 2, Unhealthy 2, Interval 10s, Timeout 5s, Success codes 200
- Create target group


**Create an Application Load Balancer (ALB)**

Why: Public endpoint, health checks, spreads load across tasks.

Console -> EC2 -> Load balancers -> Create load balancer -> Application Load Balancer

- Name: ds252-alb
- Scheme: Internet-facing | IP type: IPv4
- VPC: your VPC | Mappings: select two public subnets (different AZs)
- Security groups: ALB SG (HTTP 80 from Internet)
- Listeners: HTTP :80 → Forward to ds252-tg
- Create load balancer

After creation, open the ALB and note its DNS name (you’ll test with this and use it in JMeter).

**Security Groups**

Why: The ALB must accept HTTP on :80 from the Internet, and your ECS tasks must accept app traffic on :5000 only from the ALB. A self-reference lets tasks talk to each other (east-west) if needed.

Console -> EC2 -> Security Groups -> Select security group

- Inbound rules:
    - HTTP | Port 80 | Source: 0.0.0.0/0 (IPv4)
    - HTTP | Port 80 | Source: ::/0 (IPv6) (prevents IPv6 clients from hanging)
    - Custom TCP | Port 5000 | Source: Security group = security_group_name


**Create (or verify) the ECS (EC2) cluster with capacity**

Why: The cluster is the pool of EC2 hosts where tasks run. The EC2 Linux + Networking wizard sets up an Auto Scaling Group for you.

Console -> ECS -> Clusters -> Create -> EC2 Linux + Networking

- Cluster name: ds252-cluster-<team>
- Instance type: t3.small | Desired capacity: 2 (min 1, max 3–4)
- AMI: Amazon ECS-optimized default | Key pair: optional
- Instance role: select or create ecsInstanceRole
- Networking:
  - VPC: your VPC
  - Subnets: the two public subnets
- Auto-assign public IP: Enable (lab path so hosts/tasks can reach ECR/CloudWatch/S3)
- Create

**Create the Task Definition**

Why: Defines how to run your container: image, ports, env vars, logging, and roles.

Console -> ECS -> Task definitions -> Create new task definition

- Launch type: EC2
- Task family: ds252-flask
- Task role: ecsTaskRoleDs252 (S3 access for your app)
- Task execution role: ecsTaskExecutionRole (pull from ECR, logs)
- Network mode: awsvpc (required for ALB + IP target type)
- Task size: 0.25 vCPU and 0.5 GB (or 256 CPU / 512 MiB)
- Add container:
  - Name: flask
  - Image: paste your ECR Image URI
  - Port mappings: 5000/TCP
  - Environment variables:
    - S3_BUCKET = <your-bucket-name>
    - AWS_REGION = <your-region>
- Log configuration:
  - Log driver: awslogs
  - Log group: /ecs/ds252-flask (type a new name; will be created)
  - Region: your region
  - Stream prefix: ecs
- Create task definition

**Create the Service and attach it to the ALB**

Why: Keeps the desired number of task copies running, registers them in the target group, and applies autoscaling.

Console -> ECS -> Clusters -> your cluster -> Services -> Create

- Compute options: EC2
- Task definition: ds252-flask (latest revision)
- Service name: ds252-flask-svc
- Desired tasks: 1 (for a cold-start demo, you can start at 0 and increase to 1 while JMeter is running)
- Networking:
    - VPC: same VPC
    - Subnets: the two public subnets
    - Security group: Tasks SG (allows TCP 5000 from ALB SG)
    - Auto-assign public IP: Enabled (lab path)
- Load balancing:
- Type: Application Load Balancer
- Load balancer: ds252-alb
- Listener: HTTP:80
- Target group: ds252-tg
- Container to load balance: flask:5000
- Service Auto Scaling (Target tracking):
  - Metric: ECSServiceAverageCPUUtilization
  - Target value: 50%
- Min tasks: 1, Max tasks: 4
- Cooldowns: Scale-out 60–120s, Scale-in 180–300s
- Create service

---

**JMeter Tests**

We will use JMeter to send requests to the backend service that is running on the cluster now. We will call the /hash endpoint - this endpoint takes a random string and returns a hash for it. Use the ```hash-load.jmx``` file to run jmeter tests with the following configs & commands:

```bash
jmeter -n -t hash-load.jmx \
  -JSERVER=<ALB DNS NAME>.ap-south-1.elb.amazonaws.com \
  -JPORT=80 -JPROTOCOL=http \
  -JTHREADS=50 -JRAMP=10 -JDURATION=<DURATION OF THE RUN> \
  -l results.jtl -e -o out-report
```


**Test 1 — Cold Start**

- Set Service Desired=0
- Thread Group: 10 users, 10s ramp, 2–3 min duration
- Start JMeter, then set Desired Tasks=1
- Watch: ECS Tasks show PROVISIONING -> PENDING -> RUNNING; ALB HealthyHostCount 0 → 1; CPU rises after healthy

```bash
jmeter -n -t hash-load.jmx \
  -JSERVER=<ALB DNS NAME>.ap-south-1.elb.amazonaws.com \
  -JPORT=80 -JPROTOCOL=http \
  -JTHREADS=50 -JRAMP=10 -JDURATION=180 \
  -l results_cs.jtl -e -o out-report-cs
```


**Test 2 — Reactive Scale-Out**

- Ensure Desired=1 initially
- Thread Group: 60 users, 60s ramp, 3–4 min duration
- Watch: ECS Service CPU > target -> Running tasks goes 1 -> 2 (-> 3)
- If no scale out: increase users to 80–120 or extend duration

```bash
jmeter -n -t hash-load.jmx \
  -JSERVER=<ALB DNS NAME>.ap-south-1.elb.amazonaws.com \
  -JPORT=80 -JPROTOCOL=http \
  -JTHREADS=50 -JRAMP=10 -JDURATION=300 \
  -l results_so.jtl -e -o out-report-so
```


**Test 3 — Stable State**

- Thread Group: 15–20 users, 30s ramp, 4–5 min duration
- Watch: CPU stays below target; Running tasks remain 1

```bash
jmeter -n -t hash-load.jmx \
  -JSERVER=<ALB DNS NAME>.ap-south-1.elb.amazonaws.com \
  -JPORT=80 -JPROTOCOL=http \
  -JTHREADS=50 -JRAMP=10 -JDURATION=300 \
  -l results_ss.jtl -e -o out-report-ss
```



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
