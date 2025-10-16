# DS252 Lab Session 6 - Complete Deployment Guide

## Hybrid Architecture: Lambda + EC2 + S3

This guide will walk you through deploying a hybrid AWS architecture using both **Terraform** and **CloudFormation**. Follow this step-by-step to reproduce the entire setup.

---

## ⚠️ Prerequisites (Must Complete First)

### 1. AWS Account Setup
```bash
# Check if AWS CLI is installed
aws --version

# If not installed, install AWS CLI v2
# macOS:
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Linux:
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### 2. Configure AWS Credentials
```bash
# Configure AWS CLI with your credentials
aws configure

# You will be prompted for:
# AWS Access Key ID: [paste your access key]
# AWS Secret Access Key: [paste your secret key]
# Default region name: ap-south-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
# Expected output: Shows your AWS Account ID, User ARN, and UserId
```

### 3. Install Terraform
```bash
# macOS (using Homebrew)
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Linux (Ubuntu/Debian)
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common
curl https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null
sudo apt-add-repository "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install terraform

# Verify installation
terraform -version
# Expected: Terraform v1.8.x or higher
```

### 4. Install jq (for JSON parsing)
```bash
# macOS
brew install jq

# Linux
sudo apt-get install -y jq

# Verify
jq --version
```

### 5. Verify All Prerequisites
```bash
# Run this verification script
echo "✅ Checking prerequisites..."
aws --version && echo "AWS CLI: ✓"
terraform -version && echo "Terraform: ✓"
jq --version && echo "jq: ✓"
aws sts get-caller-identity > /dev/null && echo "AWS Credentials: ✓"
echo "All prerequisites completed!"
```

---

## PART 1: Deploy with Terraform

### Step 1.1: Verify All Files Exist
```bash
# Navigate to lab directory
cd ds252-2025/lab-session6-1710

# List all required files
ls -1 *.tf *.py *.sh *.yaml

# Expected output:
# cloudformation-template.yaml
# flask_server_startup.sh
# lambda_function.py
# main.tf
# outputs.tf
# variables.tf
```

### Step 1.2: Initialize Terraform
```bash
# Initialize Terraform (downloads AWS provider plugin)
terraform init

# Expected output:
# Initializing the backend...
# Initializing provider plugins...
# Terraform has been successfully initialized!

# Verify .terraform directory was created
ls -la .terraform/
```

### Step 1.3: Review Configuration Files
```bash
# Review main infrastructure code
echo "=== main.tf ===" && head -30 main.tf

# Review variables
echo "=== variables.tf ===" && cat variables.tf

# Review outputs
echo "=== outputs.tf ===" && cat outputs.tf

# Review Lambda code
echo "=== lambda_function.py ===" && cat lambda_function.py

# Review EC2 bootstrap script
echo "=== flask_server_startup.sh ===" && head -50 flask_server_startup.sh
```

### Step 1.4: Validate Terraform Configuration
```bash
# Validate syntax and configuration
terraform validate

# Expected output:
# Success! The configuration is valid.
```

### Step 1.5: Create and Review Terraform Plan
```bash
# Create a plan to see what will be created
terraform plan -out=tfplan

# This will show:
# - VPC creation
# - Subnet creation
# - Security groups
# - IAM roles and policies
# - EC2 instance
# - S3 bucket
# - Lambda function

# Save plan details to file for review
terraform plan -out=tfplan > plan-details.txt
cat plan-details.txt
```

### Step 1.6: Deploy Infrastructure with Terraform
```bash
# Apply the Terraform configuration
terraform apply tfplan

# This will take 3-5 minutes to complete
# You will see resource creation progress

# Expected: "Apply complete! Resources: XX added, 0 changed, 0 destroyed."
```

### Step 1.7: Verify Terraform Deployment - Get Outputs
```bash
# Display all outputs
terraform output

# Expected output shows:
# - ec2_instance_id
# - ec2_instance_public_ip
# - ec2_instance_private_ip
# - lambda_function_name
# - lambda_function_arn
# - s3_bucket_name
# - vpc_id

# Save outputs to variable for later use
EC2_ID=$(terraform output -raw ec2_instance_id)
EC2_PUBLIC_IP=$(terraform output -raw ec2_instance_public_ip)
EC2_PRIVATE_IP=$(terraform output -raw ec2_instance_private_ip)
LAMBDA_NAME=$(terraform output -raw lambda_function_name)
S3_BUCKET=$(terraform output -raw s3_bucket_name)

echo "EC2 ID: $EC2_ID"
echo "EC2 Public IP: $EC2_PUBLIC_IP"
echo "EC2 Private IP: $EC2_PRIVATE_IP"
echo "Lambda Name: $LAMBDA_NAME"
echo "S3 Bucket: $S3_BUCKET"
```

### Step 1.8: Verify AWS Resources Created
```bash
# Check S3 bucket
echo "=== Checking S3 ===" 
aws s3 ls | grep hybrid
aws s3api head-bucket --bucket $S3_BUCKET && echo "S3 bucket exists ✓"

# Check EC2 instance
echo "=== Checking EC2 ==="
aws ec2 describe-instances --instance-ids $EC2_ID \
  --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PrivateIpAddress,PublicIpAddress]' \
  --output table

# Check Lambda function
echo "=== Checking Lambda ==="
aws lambda get-function --function-name $LAMBDA_NAME \
  --query 'Configuration.[FunctionName,Runtime,Timeout]' \
  --output table
```

### Step 1.9: Wait for EC2 Instance to be Ready
```bash
# Wait for EC2 to pass status checks (3-5 minutes)
echo "Waiting for EC2 instance to be ready..."

# Check instance status
aws ec2 describe-instance-status --instance-ids $EC2_ID \
  --query 'InstanceStatuses[0].[InstanceStatus.Status,SystemStatus.Status]'

# Keep checking until you see "ok" for both
# Or run this loop:
for i in {1..30}; do
  STATUS=$(aws ec2 describe-instance-status --instance-ids $EC2_ID \
    --query 'InstanceStatuses[0].InstanceStatus.Status' --output text 2>/dev/null)
  
  if [ "$STATUS" == "ok" ]; then
    echo "✓ EC2 instance is ready!"
    break
  else
    echo "Waiting... (attempt $i/30)"
    sleep 10
  fi
done
```

### Step 1.10: Verify Flask Server is Running on EC2
```bash
# SSH into EC2 instance
ssh -i ~/.ssh/your-key-pair.pem ec2-user@$EC2_PUBLIC_IP

# Inside EC2, check Flask service status:
sudo systemctl status flask-app.service

# Check Flask server logs:
sudo journalctl -u flask-app.service -n 50

# Test Flask server locally on EC2:
curl http://localhost:5000/

# Expected response: JSON with service info

# Exit SSH
exit
```

### Step 1.11: Test Lambda Function - Synchronous Call
```bash
# Create test payload with image URL
cat > test-payload.json << 'EOF'
{
  "image_url": "https://httpbin.org/image/jpeg",
  "timestamp": "2025-01-01T00:00:00Z"
}
EOF

# Invoke Lambda function synchronously
echo "Invoking Lambda function..."
aws lambda invoke \
  --function-name $LAMBDA_NAME \
  --payload file://test-payload.json \
  --output json \
  lambda-response.json

# Check the response
echo "Lambda Response:"
cat lambda-response.json
jq . lambda-response.json

# Extract the actual response body if needed
aws lambda invoke \
  --function-name $LAMBDA_NAME \
  --payload file://test-payload.json \
  response.txt && cat response.txt
```

### Step 1.12: Verify Image Processing in S3
```bash
# List images in S3 bucket
echo "=== Images in S3 ==="
aws s3 ls s3://$S3_BUCKET/images/

# Get image count
aws s3 ls s3://$S3_BUCKET/images/ --recursive --summarize | grep "Total Objects:"
```

### Step 1.13: Multiple Test Calls
```bash
# Run 5 test invocations
for i in {1..5}; do
  echo "Test call $i/5..."
  
  cat > test-payload-$i.json << EOF
{
  "image_url": "https://httpbin.org/image/jpeg?size=$((i*100))",
  "test_number": $i
}
EOF

  aws lambda invoke \
    --function-name $LAMBDA_NAME \
    --payload file://test-payload-$i.json \
    response-$i.json
  
  echo "Response $i:"
  jq '.StatusCode' response-$i.json
  sleep 2
done

# Verify all images in S3
echo "Total images processed:"
aws s3 ls s3://$S3_BUCKET/images/ --recursive --summarize | grep "Total Objects:"
```

---

## PART 2: Deploy with CloudFormation

### Step 2.1: Review CloudFormation Template
```bash
# Check template file
ls -la cloudformation-template.yaml

# Validate template syntax
aws cloudformation validate-template \
  --template-body file://cloudformation-template.yaml

# Expected: No errors

# View template structure
echo "=== CloudFormation Template Structure ==="
head -50 cloudformation-template.yaml
```

### Step 2.2: Create CloudFormation Stack
```bash
# Create stack with default parameters
aws cloudformation create-stack \
  --stack-name ds252-hybrid-cf \
  --template-body file://cloudformation-template.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=ds252-hybrid-cf \
    ParameterKey=InstanceType,ParameterValue=t2.micro \
    ParameterKey=Environment,ParameterValue=lab

# Expected: Returns StackId

# Save stack name
CF_STACK_NAME="ds252-hybrid-cf"
echo "Created CloudFormation stack: $CF_STACK_NAME"
```

### Step 2.3: Monitor CloudFormation Stack Creation
```bash
# Check stack status
aws cloudformation describe-stacks \
  --stack-name $CF_STACK_NAME \
  --query 'Stacks[0].StackStatus'

# Watch stack creation in real-time (continuous monitoring)
watch -n 10 "aws cloudformation describe-stacks --stack-name $CF_STACK_NAME --query 'Stacks[0].StackStatus' --output text"

# Or check periodically with a loop
echo "Waiting for CloudFormation stack creation..."
for i in {1..60}; do
  STATUS=$(aws cloudformation describe-stacks \
    --stack-name $CF_STACK_NAME \
    --query 'Stacks[0].StackStatus' \
    --output text)
  
  echo "[$i/60] Stack Status: $STATUS"
  
  if [[ $STATUS == *"COMPLETE"* ]]; then
    echo "✓ Stack creation complete!"
    break
  elif [[ $STATUS == *"FAILED"* ]]; then
    echo "✗ Stack creation failed!"
    break
  fi
  
  sleep 5
done
```

### Step 2.4: Get CloudFormation Outputs
```bash
# Get all stack outputs
aws cloudformation describe-stacks \
  --stack-name $CF_STACK_NAME \
  --query 'Stacks[0].Outputs' \
  --output table

# Extract specific outputs
CF_EC2_IP=$(aws cloudformation describe-stacks \
  --stack-name $CF_STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`EC2InstancePublicIP`].OutputValue' \
  --output text)

CF_LAMBDA=$(aws cloudformation describe-stacks \
  --stack-name $CF_STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionName`].OutputValue' \
  --output text)

CF_S3=$(aws cloudformation describe-stacks \
  --stack-name $CF_STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
  --output text)

echo "CF Lambda: $CF_LAMBDA"
echo "CF S3: $CF_S3"
echo "CF EC2 IP: $CF_EC2_IP"
```

### Step 2.5: Wait for CloudFormation EC2 Instance
```bash
# Check EC2 status from CloudFormation
CF_EC2_ID=$(aws cloudformation describe-stacks \
  --stack-name $CF_STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`EC2InstanceId`].OutputValue' \
  --output text)

echo "CloudFormation EC2 Instance ID: $CF_EC2_ID"

# Wait for EC2 to be ready
for i in {1..30}; do
  STATUS=$(aws ec2 describe-instance-status --instance-ids $CF_EC2_ID \
    --query 'InstanceStatuses[0].InstanceStatus.Status' --output text 2>/dev/null)
  
  if [ "$STATUS" == "ok" ]; then
    echo "✓ EC2 instance is ready!"
    break
  else
    echo "Waiting... (attempt $i/30)"
    sleep 10
  fi
done
```

### Step 2.6: Verify CloudFormation Resources
```bash
# List all resources in stack
aws cloudformation describe-stack-resources \
  --stack-name $CF_STACK_NAME \
  --query 'StackResources[*].[LogicalResourceId,ResourceType,ResourceStatus]' \
  --output table

# Verify S3 bucket exists
aws s3 ls | grep cf

# Verify Lambda function
aws lambda get-function --function-name $CF_LAMBDA \
  --query 'Configuration.FunctionName'
```

### Step 2.7: Test CloudFormation Lambda Function
```bash
# Create test payload
cat > test-payload-cf.json << 'EOF'
{
  "image_url": "https://httpbin.org/image/jpeg",
  "timestamp": "2025-01-01T00:00:00Z",
  "source": "cloudformation"
}
EOF

# Invoke CloudFormation Lambda
echo "Invoking CloudFormation Lambda..."
aws lambda invoke \
  --function-name $CF_LAMBDA \
  --payload file://test-payload-cf.json \
  --output json \
  cf-lambda-response.json

# Check response
echo "CloudFormation Lambda Response:"
cat cf-lambda-response.json
jq . cf-lambda-response.json
```

### Step 2.8: Verify CloudFormation Image Processing
```bash
# List images in S3 from CloudFormation
echo "=== Images in CloudFormation S3 ==="
aws s3 ls s3://$CF_S3/images/

# Get count
aws s3 ls s3://$CF_S3/images/ --recursive --summarize | grep "Total Objects:"
```

---

## PART 3: Comparison Testing

### Step 3.1: Prepare Comparison Test Data
```bash
# Create multiple test payloads
mkdir -p test-data

for i in {1..10}; do
  cat > test-data/payload-$i.json << EOF
{
  "image_url": "https://httpbin.org/image/jpeg?size=$((i*50))",
  "test_number": $i,
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
done

echo "Created 10 test payloads"
```

### Step 3.2: Test Terraform Deployment Multiple Times
```bash
# Run 5 invocations on Terraform deployment
echo "=== Testing Terraform Deployment ==="
TERRAFORM_RESULTS=()

for i in {1..5}; do
  echo "Terraform test $i/5..."
  
  START=$(date +%s%N)
  
  aws lambda invoke \
    --function-name $LAMBDA_NAME \
    --payload file://test-data/payload-$i.json \
    tf-response-$i.json
  
  END=$(date +%s%N)
  DURATION=$(( (END - START) / 1000000 ))  # Convert to ms
  
  STATUS=$(jq '.StatusCode' tf-response-$i.json)
  TERRAFORM_RESULTS+=("Response $i: Status=$STATUS, Duration=${DURATION}ms")
  
  echo "Response $i: Status Code = $STATUS, Duration = ${DURATION}ms"
  sleep 2
done

# Summary
echo "=== Terraform Results ==="
for result in "${TERRAFORM_RESULTS[@]}"; do
  echo "$result"
done
```

### Step 3.3: Test CloudFormation Deployment Multiple Times
```bash
# Run 5 invocations on CloudFormation deployment
echo "=== Testing CloudFormation Deployment ==="
CF_RESULTS=()

for i in {1..5}; do
  echo "CloudFormation test $i/5..."
  
  START=$(date +%s%N)
  
  aws lambda invoke \
    --function-name $CF_LAMBDA \
    --payload file://test-data/payload-$((i+5)).json \
    cf-response-$i.json
  
  END=$(date +%s%N)
  DURATION=$(( (END - START) / 1000000 ))  # Convert to ms
  
  STATUS=$(jq '.StatusCode' cf-response-$i.json)
  CF_RESULTS+=("Response $i: Status=$STATUS, Duration=${DURATION}ms")
  
  echo "Response $i: Status Code = $STATUS, Duration = ${DURATION}ms"
  sleep 2
done

# Summary
echo "=== CloudFormation Results ==="
for result in "${CF_RESULTS[@]}"; do
  echo "$result"
done
```

### Step 3.4: Compare Data in Both S3 Buckets
```bash
# Count images in Terraform S3
echo "=== S3 Comparison ==="
TF_COUNT=$(aws s3 ls s3://$S3_BUCKET/images/ --recursive --summarize | grep "Total Objects:" | awk '{print $NF}')
CF_COUNT=$(aws s3 ls s3://$CF_S3/images/ --recursive --summarize | grep "Total Objects:" | awk '{print $NF}')

echo "Terraform S3 Images: $TF_COUNT"
echo "CloudFormation S3 Images: $CF_COUNT"

# List both
echo "Terraform images:"
aws s3 ls s3://$S3_BUCKET/images/ --recursive

echo "CloudFormation images:"
aws s3 ls s3://$CF_S3/images/ --recursive
```

---

## PART 4: Cleanup and Destruction

### Step 4.1: Destroy Terraform Resources
```bash
# Destroy all Terraform-managed resources
echo "Destroying Terraform resources..."
terraform destroy -auto-approve

# Verify destruction
echo "Verifying Terraform destruction..."
terraform show

# Check that EC2 instance is terminated
aws ec2 describe-instances --instance-ids $EC2_ID \
  --query 'Reservations[0].Instances[0].State.Name'

# Expected: terminated or in terminating state
```

### Step 4.2: Delete CloudFormation Stack
```bash
# Delete CloudFormation stack
echo "Deleting CloudFormation stack..."
aws cloudformation delete-stack --stack-name $CF_STACK_NAME

# Monitor deletion
echo "Waiting for stack deletion..."
for i in {1..30}; do
  STATUS=$(aws cloudformation describe-stacks \
    --stack-name $CF_STACK_NAME \
    --query 'Stacks[0].StackStatus' \
    --output text 2>&1)
  
  if [[ $STATUS == *"DELETE_COMPLETE"* ]]; then
    echo "✓ Stack deleted!"
    break
  elif [[ $STATUS == *"does not exist"* ]]; then
    echo "✓ Stack deleted!"
    break
  else
    echo "[$i/30] Stack Status: $STATUS"
    sleep 5
  fi
done

# Verify deletion
aws cloudformation describe-stacks --stack-name $CF_STACK_NAME 2>&1 | grep -q "does not exist" && echo "Stack successfully deleted"
```

### Step 4.3: Clean Up Test Files
```bash
# Remove local test files
rm -f test-*.json
rm -f response*.json
rm -f cf-*.json
rm -f tf-*.json
rm -f tfplan
rm -rf test-data/

echo "Test files cleaned up"

# Verify cleanup
ls -la *.json 2>/dev/null || echo "No JSON test files remaining"
```

### Step 4.4: Remove Terraform State Files (Optional)
```bash
# WARNING: Only do this if you don't need to manage resources later
rm -rf .terraform/
rm -f .terraform.lock.hcl
rm -f terraform.tfstate*
rm -f *.pem
rm -f lambda_function.zip
rm -f tfplan

echo "✅ Terraform artifacts cleaned up"
```

---

## 📊 Summary Comparison Script

Create this script to get a full comparison:

```bash
# Save as: compare.sh

#!/bin/bash

echo "╔════════════════════════════════════════════╗"
echo "║  TERRAFORM vs CLOUDFORMATION COMPARISON    ║"
echo "╚════════════════════════════════════════════╝"

# Terraform data
TF_S3=$(terraform output -raw s3_bucket_name 2>/dev/null)
TF_LAMBDA=$(terraform output -raw lambda_function_name 2>/dev/null)

# CloudFormation data
CF_STACK="ds252-hybrid-cf"
CF_S3=$(aws cloudformation describe-stacks --stack-name $CF_STACK --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' --output text 2>/dev/null)
CF_LAMBDA=$(aws cloudformation describe-stacks --stack-name $CF_STACK --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionName`].OutputValue' --output text 2>/dev/null)

echo ""
echo "S3 Buckets:"
echo "  Terraform: $TF_S3"
echo "  CloudFormation: $CF_S3"

echo ""
echo "Lambda Functions:"
echo "  Terraform: $TF_LAMBDA"
echo "  CloudFormation: $CF_LAMBDA"

echo ""
echo "Image Counts:"
TF_IMG=$(aws s3 ls s3://$TF_S3/images/ --recursive --summarize 2>/dev/null | grep "Total Objects:" | awk '{print $NF}')
CF_IMG=$(aws s3 ls s3://$CF_S3/images/ --recursive --summarize 2>/dev/null | grep "Total Objects:" | awk '{print $NF}')
echo "  Terraform: $TF_IMG"
echo "  CloudFormation: $CF_IMG"
```

---

## ✅ Verification Checklist

Use this checklist to verify your deployment:

- [ ] AWS CLI configured and authenticated
- [ ] Terraform initialized successfully
- [ ] Terraform plan shows all resources
- [ ] Terraform apply completed without errors
- [ ] Terraform outputs display correctly
- [ ] EC2 instance running and status checks passing
- [ ] Flask server running on EC2 (port 5000)
- [ ] Lambda function invocation successful
- [ ] Images uploaded to S3
- [ ] CloudFormation template validates
- [ ] CloudFormation stack created successfully
- [ ] CloudFormation resources match Terraform
- [ ] Both S3 buckets have images
- [ ] Lambda logs show successful executions
- [ ] Comparison tests completed
- [ ] Cleanup completed (if destroying)

---

## 🆘 Quick Troubleshooting

### Problem: Terraform init fails
```bash
# Solution: Check internet connection and AWS credentials
aws sts get-caller-identity
rm -rf .terraform/
terraform init
```

### Problem: EC2 takes too long to initialize
```bash
# Solution: Check EC2 user data logs
aws ssm start-session --target $EC2_ID
tail -f /var/log/cloud-init-output.log
```

### Problem: Lambda can't connect to Flask server
```bash
# Solution: Verify security group and networking
aws ec2 describe-security-groups --query 'SecurityGroups[?GroupName==`*flask*`]'
```

### Problem: S3 bucket doesn't exist
```bash
# Solution: Check if deployment completed successfully
terraform output s3_bucket_name
aws s3api head-bucket --bucket $S3_BUCKET
```

### Problem: Lambda function is empty
```bash
# Solution: Check Lambda execution and logs
aws logs tail /aws/lambda/$LAMBDA_NAME --follow
```

---

## 📝 Notes

- All commands assume you're in the `ds252-2025/lab-session6-1710` directory
- Replace `$VARIABLE` with actual values if needed
- Keep outputs saved for reference
- Don't skip the prerequisite verification
- Delete resources when done to avoid AWS charges
