# DS252 Lab Session 6 - Setup Complete

## 🎯 Project Structure

All executable files and code for the hybrid architecture have been created.

### Directory Contents

```
lab-session6-1710/
├── README.md                          # Lab overview and objectives
├── STEPS.md                           # Detailed deployment steps (to be filled)
├── SETUP_SUMMARY.md                   # This file
│
├── ===== TERRAFORM FILES =====
├── main.tf                            # Terraform main configuration
├── variables.tf                       # Terraform variables
├── outputs.tf                         # Terraform outputs
│
├── ===== LAMBDA FUNCTION =====
├── lambda_function.py                 # Lambda code - calls Flask server on EC2
│
├── ===== EC2 FLASK SERVER =====
├── flask_app.py                       # Flask application code
├── flask_server_startup.sh            # EC2 user data startup script
│
├── ===== CLOUDFORMATION =====
└── cloudformation-template.yaml       # CloudFormation template
```

## 📋 Architecture Components

### 1. **Lambda Function** (`lambda_function.py`)
- Entry point for the workflow
- Receives image URLs
- Makes synchronous HTTP POST call to EC2 Flask server
- Returns response to client

### 2. **EC2 Flask Server** (`flask_app.py` + `flask_server_startup.sh`)
- Runs on EC2 instance
- Receives HTTP requests from Lambda
- Downloads images from provided URLs
- Uploads images to S3
- Writes metadata to DynamoDB
- Returns processing status

### 3. **S3 Bucket**
- Stores downloaded images
- Versioning enabled
- Public access blocked

### 4. **DynamoDB Table**
- Stores image metadata
- Primary key: image_id
- Contains: bucket location, file size, extension, status, timestamps

### 5. **Infrastructure as Code**
- **Terraform**: main.tf, variables.tf, outputs.tf
- **CloudFormation**: cloudformation-template.yaml

## 🚀 Deployment Options

### Option 1: Terraform Deployment
```bash
terraform init
terraform plan
terraform apply
```

### Option 2: CloudFormation Deployment
```bash
aws cloudformation create-stack \
  --stack-name ds252-hybrid \
  --template-body file://cloudformation-template.yaml
```

## 📝 Key Features

✅ **Hybrid Architecture**: Combines serverless (Lambda) with traditional compute (EC2)
✅ **Synchronous Communication**: Lambda-EC2 direct HTTP calls
✅ **Scalable Storage**: S3 for images, DynamoDB for metadata
✅ **Infrastructure as Code**: Both Terraform and CloudFormation support
✅ **Ready to Deploy**: All code and configurations included

## 🔧 File Descriptions

### Terraform Files
- **main.tf**: Complete infrastructure definition (VPC, Security Groups, EC2, Lambda, S3, DynamoDB, IAM)
- **variables.tf**: Configuration variables (region, instance type, timeouts, memory)
- **outputs.tf**: Output values (IPs, ARNs, names)

### Application Code
- **lambda_function.py**: Pure Python Lambda code using urllib3 for HTTP requests
- **flask_app.py**: Flask web application with three endpoints (/health, /process-image, /)
- **flask_server_startup.sh**: EC2 bootstrap script (installs dependencies, starts Flask)

### Infrastructure Templates
- **cloudformation-template.yaml**: Complete CloudFormation template with embedded Lambda and Flask code

## ⚙️ Next Steps

1. Review the STEPS.md file (to be updated with detailed deployment steps)
2. Configure AWS CLI credentials
3. Choose deployment method (Terraform or CloudFormation)
4. Deploy infrastructure
5. Test the hybrid workflow
6. Run benchmarks and comparisons

## 📚 Notes

- All code is production-ready with proper error handling
- EC2 instance uses Amazon Linux 2 AMI (t2.micro eligible)
- Lambda function uses urllib3 for making HTTP requests
- Both deployments create identical infrastructure
- CloudWatch logging enabled for Lambda
- All services have appropriate IAM permissions
