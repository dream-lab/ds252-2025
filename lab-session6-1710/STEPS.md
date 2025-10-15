# DS252 Lab Session 6 - Detailed Steps

## Overview
This lab demonstrates deploying serverless workflows using both Terraform and CloudFormation. We'll deploy two workflows: Lambda image ingestion and Step Functions classification pipeline.

---

## Part 1: Deploy Workflows with Terraform

### Step 1.1: Initialize Terraform Project
```bash
# Navigate to the lab directory
cd lab-session6-1710

# Initialize Terraform
terraform init

# Verify initialization
ls -la .terraform/
```

### Step 1.2: Review Terraform Configuration
```bash
# Review main configuration
cat main.tf

# Review variables
cat variables.tf

# Review outputs
cat outputs.tf

# Review Lambda function code
ls -la lambda-functions/
```

### Step 1.3: Plan Infrastructure Deployment
```bash
# Create a plan to see what will be created
terraform plan

# Save plan to file for review
terraform plan -out=tfplan

# Review the plan
terraform show tfplan
```

### Step 1.4: Deploy Infrastructure
```bash
# Apply the configuration
terraform apply

# Or apply using the saved plan
terraform apply tfplan

# Monitor the deployment progress
# Expected resources:
# - S3 bucket for images
# - DynamoDB table for metadata
# - IAM roles and policies
# - Lambda functions
# - Step Functions state machine
```

### Step 1.5: Verify Terraform Deployment
```bash
# Check Terraform outputs
terraform output

# Verify S3 bucket
aws s3 ls | grep ds252

# Verify DynamoDB table
aws dynamodb list-tables

# Verify Lambda functions
aws lambda list-functions --query 'Functions[?contains(FunctionName, `ds252`)]'

# Verify Step Functions
aws stepfunctions list-state-machines --query 'stateMachines[?contains(name, `ds252`)]'
```

### Step 1.6: Test Lambda Function 1 (Image Ingestion)
```bash
# Create test payload
cat > test-image-ingestion.json << EOF
{
  "image_url": "https://example.com/sample-image.jpg",
  "metadata": {
    "source": "test",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  }
}
EOF

# Invoke the Lambda function
aws lambda invoke \
  --function-name ds252-image-ingestion \
  --payload file://test-image-ingestion.json \
  --output json \
  response.json

# Check the response
cat response.json

# Verify image was uploaded to S3
aws s3 ls s3://ds252-image-bucket-$(aws sts get-caller-identity --query Account --output text)/

# Check DynamoDB for metadata
aws dynamodb scan --table-name ds252-metadata-table
```

### Step 1.7: Test Step Functions Workflow
```bash
# Create test payload for Step Functions
cat > test-stepfunctions-payload.json << EOF
{
  "image_id": "test-image-001",
  "preprocessing_config": {
    "grayscale": true,
    "flip": "horizontal",
    "rotate": 90,
    "resize": [224, 224]
  }
}
EOF

# Start Step Functions execution
aws stepfunctions start-execution \
  --state-machine-arn $(terraform output -raw stepfunctions_arn) \
  --input file://test-stepfunctions-payload.json \
  --name "test-execution-$(date +%s)"

# Monitor execution
aws stepfunctions list-executions \
  --state-machine-arn $(terraform output -raw stepfunctions_arn) \
  --max-items 5
```

---

## Part 2: Deploy Same Workflows with CloudFormation

### Step 2.1: Review CloudFormation Templates
```bash
# Navigate to CloudFormation directory
cd cloudformation/

# Review main template
cat template.yaml

# Review nested templates
ls -la nested-stacks/

# Review Lambda function code (same as Terraform)
ls -la lambda-functions/
```

### Step 2.2: Validate CloudFormation Template
```bash
# Validate the main template
aws cloudformation validate-template \
  --template-body file://template.yaml

# Validate nested templates
for template in nested-stacks/*.yaml; do
  echo "Validating $template"
  aws cloudformation validate-template \
    --template-body file://$template
done
```

### Step 2.3: Deploy CloudFormation Stack
```bash
# Create the CloudFormation stack
aws cloudformation create-stack \
  --stack-name ds252-serverless-workflows \
  --template-body file://template.yaml \
  --parameters ParameterKey=ProjectName,ParameterValue=ds252 \
               ParameterKey=Environment,ParameterValue=lab \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

# Monitor stack creation
aws cloudformation describe-stacks \
  --stack-name ds252-serverless-workflows \
  --query 'Stacks[0].StackStatus'

# Wait for stack creation to complete
aws cloudformation wait stack-create-complete \
  --stack-name ds252-serverless-workflows
```

### Step 2.4: Verify CloudFormation Deployment
```bash
# Check stack outputs
aws cloudformation describe-stacks \
  --stack-name ds252-serverless-workflows \
  --query 'Stacks[0].Outputs'

# Verify resources (same as Terraform verification)
aws s3 ls | grep ds252
aws dynamodb list-tables
aws lambda list-functions --query 'Functions[?contains(FunctionName, `ds252`)]'
aws stepfunctions list-state-machines --query 'stateMachines[?contains(name, `ds252`)]'
```

### Step 2.5: Test CloudFormation Deployed Workflows
```bash
# Test Lambda Function 1 (same test as Terraform)
aws lambda invoke \
  --function-name ds252-image-ingestion-cf \
  --payload file://../test-image-ingestion.json \
  --output json \
  response-cf.json

# Test Step Functions (same test as Terraform)
aws stepfunctions start-execution \
  --state-machine-arn $(aws cloudformation describe-stacks \
    --stack-name ds252-serverless-workflows \
    --query 'Stacks[0].Outputs[?OutputKey==`StepFunctionsArn`].OutputValue' \
    --output text) \
  --input file://../test-stepfunctions-payload.json \
  --name "test-execution-cf-$(date +%s)"
```

---

## Part 3: Benchmark and Visualize Workflows

### Step 3.1: Set Up Load Testing Environment
```bash
# Navigate to benchmarking directory
cd ../benchmarking/

# Install required Python packages
pip install -r requirements.txt

# Verify load testing script
cat load_test.py
```

### Step 3.2: Prepare Test Data
```bash
# Create test image URLs
cat > test_images.json << EOF
[
  "https://example.com/image1.jpg",
  "https://example.com/image2.jpg",
  "https://example.com/image3.jpg",
  "https://example.com/image4.jpg",
  "https://example.com/image5.jpg"
]
EOF

# Create test metadata
cat > test_metadata.json << EOF
[
  {"image_id": "test-001", "source": "benchmark"},
  {"image_id": "test-002", "source": "benchmark"},
  {"image_id": "test-003", "source": "benchmark"},
  {"image_id": "test-004", "source": "benchmark"},
  {"image_id": "test-005", "source": "benchmark"}
]
EOF
```

### Step 3.3: Benchmark Terraform-Deployed Workflows
```bash
# Benchmark Lambda Function 1 (1 RPS for 30 seconds)
python load_test.py \
  --workflow lambda-ingestion \
  --target terraform \
  --rps 1 \
  --duration 30 \
  --output terraform-lambda-results.json

# Benchmark Step Functions (1 RPS for 30 seconds)
python load_test.py \
  --workflow stepfunctions \
  --target terraform \
  --rps 1 \
  --duration 30 \
  --output terraform-stepfunctions-results.json

# Monitor CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=ds252-image-ingestion \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Average,Maximum
```

### Step 3.4: Benchmark CloudFormation-Deployed Workflows
```bash
# Benchmark Lambda Function 1 (1 RPS for 30 seconds)
python load_test.py \
  --workflow lambda-ingestion \
  --target cloudformation \
  --rps 1 \
  --duration 30 \
  --output cloudformation-lambda-results.json

# Benchmark Step Functions (1 RPS for 30 seconds)
python load_test.py \
  --workflow stepfunctions \
  --target cloudformation \
  --rps 1 \
  --duration 30 \
  --output cloudformation-stepfunctions-results.json
```

### Step 3.5: Analyze Performance Results
```bash
# Run analysis script
python analyze_results.py \
  --terraform-lambda terraform-lambda-results.json \
  --terraform-stepfunctions terraform-stepfunctions-results.json \
  --cloudformation-lambda cloudformation-lambda-results.json \
  --cloudformation-stepfunctions cloudformation-stepfunctions-results.json \
  --output analysis-report.html

# Generate comparison charts
python generate_charts.py \
  --input-dir . \
  --output-dir charts/

# View results
open analysis-report.html
```

### Step 3.6: Cost Analysis
```bash
# Get cost data for the last hour
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d '1 hour ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity HOURLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# Analyze Lambda costs
python cost_analysis.py \
  --terraform-results terraform-lambda-results.json \
  --cloudformation-results cloudformation-lambda-results.json \
  --output cost-comparison.json
```

### Step 3.7: Generate Final Report
```bash
# Create comprehensive report
python generate_report.py \
  --terraform-results terraform-*-results.json \
  --cloudformation-results cloudformation-*-results.json \
  --cost-analysis cost-comparison.json \
  --output final-lab-report.md

# Convert to PDF (optional)
pandoc final-lab-report.md -o final-lab-report.pdf

# View the report
cat final-lab-report.md
```

---

## Cleanup Steps

### Cleanup Terraform Resources
```bash
# Navigate back to main directory
cd ..

# Destroy Terraform resources
terraform destroy

# Confirm destruction
terraform show
```

### Cleanup CloudFormation Resources
```bash
# Delete CloudFormation stack
aws cloudformation delete-stack \
  --stack-name ds252-serverless-workflows

# Wait for deletion
aws cloudformation wait stack-delete-complete \
  --stack-name ds252-serverless-workflows

# Verify deletion
aws cloudformation describe-stacks \
  --stack-name ds252-serverless-workflows
```

### Cleanup Test Files
```bash
# Remove test files
rm -f test-*.json
rm -f response*.json
rm -f *.html
rm -f *.pdf

# Remove Terraform plan files
rm -f tfplan
```

---

## Troubleshooting

### Common Issues and Solutions

1. **Terraform State Lock Issues**
   ```bash
   terraform force-unlock <LOCK_ID>
   ```

2. **CloudFormation Stack Rollback**
   ```bash
   aws cloudformation describe-stack-events \
     --stack-name ds252-serverless-workflows \
     --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'
   ```

3. **Lambda Function Timeout**
   ```bash
   aws lambda update-function-configuration \
     --function-name ds252-image-ingestion \
     --timeout 300
   ```

4. **Step Functions Execution Issues**
   ```bash
   aws stepfunctions describe-execution \
     --execution-arn <EXECUTION_ARN>
   ```

5. **Permission Issues**
   ```bash
   aws sts get-caller-identity
   aws iam list-attached-user-policies --user-name <USERNAME>
   ```

---

## Expected Results

After completing all parts, you should have:

1. **Terraform Deployment**: Fully functional serverless workflows deployed via Terraform
2. **CloudFormation Deployment**: Identical workflows deployed via CloudFormation
3. **Performance Metrics**: Comparative analysis of both deployments
4. **Cost Analysis**: Cost comparison between deployment methods
5. **Final Report**: Comprehensive analysis document

The lab demonstrates the practical differences between Terraform and CloudFormation in managing complex AWS serverless architectures.
