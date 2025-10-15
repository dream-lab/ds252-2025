# DS252 Lab — Serverless Workflows with Terraform and CloudFormation

## 🎯 Objective
In this lab, you will deploy the same **serverless workflows** using two different Infrastructure-as-Code (IaC) tools:
1. **Terraform** — a cross-cloud, open-source IaC tool.
2. **AWS CloudFormation** — an AWS-native IaC service.

You will deploy two serverless workflows to process images and measure performance (cold-starts, throughput, cost):

**Workflow 1 — Lambda ingestion:**
- Lambda function takes an image URL as input
- Downloads the image from the given URL
- Uploads the image to S3
- Writes metadata into DynamoDB

**Workflow 2 — Step Functions classification pipeline:**
- Step Function reads metadata from DynamoDB
- FetchImage Lambda retrieves image from S3
- Preprocessing pipeline (grayscale → flip → rotate → resize)
- Parallel inference using three ML models (AlexNet, ResNet, MobileNet)
- Aggregates results and updates metadata in DynamoDB

By the end of the lab, you will understand the key differences between Terraform and CloudFormation in defining, deploying, and managing complex AWS serverless architectures.

---

## 🧠 Learning Outcomes
You will learn to:
- Write and apply Terraform configurations for complex AWS serverless architectures
- Define equivalent infrastructure using CloudFormation YAML templates
- Deploy Lambda functions, Step Functions, S3 buckets, and DynamoDB tables
- Understand declarative infrastructure workflows (`apply`, `plan`, and `stack creation`)
- Benchmark and measure performance of serverless workflows
- Deploy, test, and destroy AWS serverless resources safely

---

## ⚙️ Environment Setup

### Prerequisites
- Active AWS account with billing enabled
- AWS CLI configured with appropriate permissions
- Python 3.8+ for Lambda functions
- Basic understanding of serverless architectures

---

### 1. Install Terraform

#### macOS (Homebrew)
```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

#### Linux (Debian/Ubuntu)
```bash
sudo apt-get update && sudo apt-get install -y wget unzip
wget https://releases.hashicorp.com/terraform/1.8.5/terraform_1.8.5_linux_amd64.zip
unzip terraform_1.8.5_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

#### Verify installation
```bash
terraform -version

Expected output:
Terraform v1.8.x
on darwin_amd64 or linux_amd64
```

---

## 📋 Lab Plan

### Part 1: Deploy Workflows with Terraform
- **Infrastructure Setup:**
  - Create S3 bucket for storing images
  - Create DynamoDB table for storing metadata
  - Set up IAM roles and policies
- **Lambda Function 1 (Image ingestion):**
  - Lambda fetches image from URL
  - Uploads image to S3
  - Inserts metadata into DynamoDB
- **Workflow 2 (Step Functions classification):**
  - Step Function reads metadata from DynamoDB
  - Fetches image from S3
  - Runs preprocessing (grayscale → flip → rotate → resize)
  - Executes three inference Lambdas in parallel (AlexNet, ResNet, MobileNet)
  - Aggregates results and updates metadata in DynamoDB

### Part 2: Deploy Same Workflows with CloudFormation
- Create equivalent CloudFormation templates
- Deploy the same infrastructure using AWS CloudFormation
- Compare deployment processes and resource management

### Part 3: Benchmark and Visualize Workflows
- Use Python client to invoke both workflows
- Load profile: **1 RPS for 30 seconds**
- Measure cold-starts, throughput, and cost
- Compare performance between Terraform and CloudFormation deployments