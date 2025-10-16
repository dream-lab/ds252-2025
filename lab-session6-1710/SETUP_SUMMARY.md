# DS252 Lab Session 6 - Setup Complete

## 🎯 Project Structure

All executable files and code for the hybrid architecture have been created.

### Directory Contents

```
lab-session6-1710/
├── README.md                           # Lab overview and architecture
├── STEPS.md                            # Step-by-step deployment guide
├── SETUP_SUMMARY.md                    # This file
├── main.tf                             # Terraform main configuration
├── variables.tf                        # Terraform variables
├── outputs.tf                          # Terraform outputs
├── lambda_function.py                  # Lambda function code
├── flask_server_startup.sh             # EC2 startup script (includes Flask app)
└── WORKFLOW.md                         # Workflow documentation
```

## 📋 Architecture Components

### 1. **Lambda Function** (`lambda_function.py`)
- Entry point for the workflow
- Receives image URLs
- Makes synchronous HTTP POST call to EC2 Flask server
- Returns response to client

### 2. **EC2 Flask Server** (`flask_server_startup.sh`)
- Runs on EC2 instance (`t2.micro`)
- Downloads and processes images from URLs
- Uploads images to S3 via REST API calls
- Responds back to Lambda with processing results
- Port: 5000
- Flask app code is embedded in the startup script

### 3. **S3 Bucket**
- Stores downloaded images
- Versioning enabled
- Public access allowed for PUT/GET operations

### 4. **Infrastructure as Code**
- **Terraform**: main.tf, variables.tf, outputs.tf

## 🚀 Deployment Options

### Terraform Deployment
```bash
terraform init
terraform plan
terraform apply
```

## 📝 Key Features

✅ **Hybrid Architecture**: Combines serverless (Lambda) with traditional compute (EC2)
✅ **Synchronous Communication**: Lambda-EC2 direct HTTP calls
✅ **Scalable Storage**: S3 for images
✅ **Infrastructure as Code**: Terraform support
✅ **Ready to Deploy**: All code and configurations included

## 🔧 File Descriptions

### Terraform Files
- **main.tf**: Defines all AWS resources (VPC, EC2, Lambda, S3, IAM, Security Groups)
- **variables.tf**: Input variables with defaults (AWS region, instance type, etc.)
- **outputs.tf**: Exports important resource IDs and IPs

### Application Code
- **lambda_function.py**: Lambda code that calls Flask server on EC2
- **flask_server_startup.sh**: EC2 user data script that installs and starts Flask app (embedded code)

## ⚙️ Next Steps

1. Review the STEPS.md file for detailed deployment steps
2. Configure AWS CLI credentials
3. Deploy infrastructure using Terraform
4. Test the hybrid workflow
5. Run tests and verify results

## 📚 Notes

- All code is production-ready with proper error handling
- EC2 instance uses Amazon Linux 2 AMI (t2.micro eligible)
- Lambda function uses urllib3 for making HTTP requests
- All services have appropriate IAM permissions
