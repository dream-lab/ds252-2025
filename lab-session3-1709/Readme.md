# DS252 Lab (Week X): S3 → ECS (EC2) + ALB → FinOps

This lab extends your previous Flask-on-EC2 work into a production-style path:

1) **S3** — enable **versioning**, verify versions, and apply **lifecycle** rules  
2) **ECS (EC2) + ALB** — deploy the Flask app as a service with **CPU target-tracking autoscaling** and exercise it with **JMeter**  
3) **FinOps** — tag everything, set a **budget**, and attribute/estimate **the cost of this specific lab session**

> **Only AWS** is used (no third-party services).  
> Time budget: ~90 minutes in-class (you can finish tagging/budget follow-ups after the session).

---

## Table of Contents

- [0) Prerequisites](#0-prerequisites)
- [1) App Summary (Verbose)](#1-app-summary-verbose)
- [2) Local Setup](#2-local-setup)
- [Activity 1 — S3 Versioning + Lifecycle](#activity-1--s3-versioning--lifecycle)
- [Activity 2 — ECS(EC2) + ALB + Autoscaling + JMeter](#activity-2--ecsec2--alb--autoscaling--jmeter)
  - [2A) Install JMeter](#2a-install-jmeter)
  - [2B) Push Prebuilt Image to ECR](#2b-push-prebuilt-image-to-ecr)
  - [2C) Create ECS(EC2) Cluster](#2c-create-ecsec2-cluster)
  - [2D) Create ALB + Target Group](#2d-create-alb--target-group)
  - [2E) IAM Roles (Execution + Task Role)](#2e-iam-roles-execution--task-role)
  - [2F) Register Task Definition](#2f-register-task-definition)
  - [2G) Create Service + Autoscaling](#2g-create-service--autoscaling)
  - [2H) JMeter Tests (Cold Start, Scale-Out→In, Stable)](#2h-jmeter-tests-cold-start-scale-outin-stable)
- [Activity 3 — FinOps: Tagging, Budget, “What Did This Lab Cost?”](#activity-3--finops-tagging-budget-what-did-this-lab-cost)
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
