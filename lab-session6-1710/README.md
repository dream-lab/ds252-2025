# DS252 Lab — Hybrid Architecture with Terraform and CloudFormation

## 🎯 Objective
In this lab, you will deploy the same **hybrid cloud architecture** using two different Infrastructure-as-Code (IaC) tools:
1. **Terraform** — a cross-cloud, open-source IaC tool.
2. **AWS CloudFormation** — an AWS-native IaC service.

You will deploy a hybrid workflow that combines serverless and traditional compute to process images:

**Hybrid Image Processing Workflow:**
- Lambda function receives an image URL as input
- Lambda makes a synchronous HTTP call to a Flask server running on EC2
- EC2 instance downloads the image from the provided URL
- EC2 uploads the image to S3 and writes metadata to DynamoDB
- EC2 returns success/failure status back to Lambda
- Lambda returns the final response to the client

By the end of the lab, you will understand the key differences between Terraform and CloudFormation in defining, deploying, and managing hybrid AWS architectures that combine serverless and traditional compute resources.

---

## 🧠 Learning Outcomes
You will learn to:
- Write and apply Terraform configurations for hybrid AWS architectures
- Define equivalent infrastructure using CloudFormation YAML templates
- Deploy Lambda functions, EC2 instances, S3 buckets, and DynamoDB tables
- Configure security groups and IAM roles for cross-service communication
- Understand declarative infrastructure workflows (`apply`, `plan`, and `stack creation`)
- Benchmark and measure performance of hybrid architectures
- Deploy, test, and destroy AWS hybrid resources safely

---

## ⚙️ Environment Setup

### Prerequisites
- Active AWS account with billing enabled
- AWS CLI configured with appropriate permissions
- Python 3.8+ for Lambda functions and Flask server
- Basic understanding of hybrid cloud architectures
- Knowledge of HTTP requests and Flask web framework

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

### Part 1: Deploy Hybrid Architecture with Terraform
- **Infrastructure Setup:**
  - Create S3 bucket for storing images
  - Create DynamoDB table for storing metadata
  - Launch EC2 instance with Flask server
  - Set up IAM roles and policies for all services
  - Configure security groups for Lambda-EC2 communication
- **Lambda Function:**
  - Receives image URL as input
  - Makes synchronous HTTP POST request to EC2 Flask server
  - Returns response from EC2 back to client
- **EC2 Flask Server:**
  - Receives image URL from Lambda
  - Downloads image from the provided URL
  - Uploads image to S3 bucket
  - Writes metadata to DynamoDB table
  - Returns success/failure status to Lambda

### Part 2: Deploy Same Architecture with CloudFormation
- Create equivalent CloudFormation templates
- Deploy the same hybrid infrastructure using AWS CloudFormation
- Compare deployment processes and resource management
- Test Lambda-EC2 communication

### Part 3: Benchmark and Compare Architectures
- Use Python client to invoke both deployments
- Load profile: **1 RPS for 30 seconds**
- Measure response times, throughput, and cost
- Compare performance between Terraform and CloudFormation deployments
- Analyze hybrid architecture benefits and trade-offs

---

## 🏗️ Architecture Overview

### System Components

1. **AWS Lambda Function**
   - Entry point for the workflow
   - Receives image URL via API Gateway or direct invocation
   - Makes HTTP POST request to EC2 Flask server
   - Returns processed response to client

2. **EC2 Instance**
   - Runs Flask web server
   - Receives image URL from Lambda
   - Downloads image from external URL
   - Uploads image to S3
   - Returns processing status to Lambda

3. **S3 Bucket**
   - Stores downloaded images
   - Organized by image ID
   - Versioning enabled for data protection

### Data Flow

```
Client → Lambda → EC2 Flask Server → External URL (Image Download)
                ↓
                S3 Bucket (Image Storage)
                ↓
                Lambda ← EC2 (Response)
                ↓
                Client (Final Response)
```

### Key Benefits of Hybrid Architecture

- **Flexibility**: Combines serverless benefits with traditional compute control
- **Cost Optimization**: Pay-per-use Lambda with always-on EC2 for processing
- **Scalability**: Lambda handles variable load, EC2 provides consistent processing
- **Technology Choice**: Use best tool for each component (serverless vs traditional)