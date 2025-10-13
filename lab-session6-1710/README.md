# DS252 Lab — Deploying AWS Lambda with Terraform and AWS CloudFormation

## 🎯 Objective
In this lab, you will learn how to deploy the same **AWS Lambda** function using two different Infrastructure-as-Code (IaC) tools:
1. **Terraform** — a cross-cloud, open-source IaC tool.
2. **AWS CloudFormation** — an AWS-native IaC service.

The Lambda function will:
- Take an input JSON containing an image URL.
- Download the image from the given URL.
- Upload the image to **your own S3 bucket**.

By the end of the lab, you will understand the key differences between Terraform and CloudFormation in defining, deploying, and managing AWS resources.

---

## 🧠 Learning Outcomes
You will learn to:
- Write and apply Terraform configurations for AWS.
- Define equivalent infrastructure using a CloudFormation YAML template.
- Understand declarative infrastructure workflows (`apply`, `plan`, and `stack creation`).
- Deploy, test, and destroy AWS Lambda resources safely.

---

## ⚙️ Environment Setup

1. AWS Account Setup and CLI configured

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