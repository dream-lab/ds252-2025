# DS252 Lab Session 6 - Hybrid Architecture Workflow

## Complete End-to-End Flow

```
User/Client Request
         ↓
Lambda Function (ds252-hybrid-processor)
    - Receives: { "image_url": "https://..." }
    - Calls EC2 Flask Server at http://10.0.1.xxx:5000/process-image (VPC private IP)
    - Waits for response (synchronous)
         ↓
EC2 Instance - Flask Server (port 5000)
    - Endpoint: /process-image (POST)
    - Step 1: Download image from public URL (using requests library)
    - Step 2: Generate unique image_id (UUID)
    - Step 3: Upload to PUBLIC S3 bucket using REST API (PUT request, no credentials needed)
         ↓
    S3 Bucket (PUBLIC)
    - bucket-policy allows: s3:GetObject and s3:PutObject for Principal "*"
    - Image stored at: https://bucket-name.s3.region.amazonaws.com/images/{image_id}.{ext}
         ↓
    - Step 4: Return JSON response to Lambda
         {
           "success": true,
           "image_id": "uuid",
           "s3_location": "https://...",
           "file_size": 1234,
           "timestamp": "2025-10-16T..."
         }
         ↓
Lambda Function
    - Receives Flask response
    - Wraps it in Lambda response format
    - Returns to user
         ↓
User Receives Final Response
    {
      "statusCode": 200,
      "body": {
        "message": "Image processed successfully",
        "result": { ... Flask response ... }
      }
    }
```

## Key Design Points

1. **No Credentials Required**: 
   - Flask uses PUBLIC S3 bucket (GET/PUT allowed for all)
   - No boto3, no instance profiles, no credentials
   - Lambda has basic VPC permissions for EC2 communication

2. **Synchronous Communication**:
   - Lambda waits for Flask response
   - Flask returns immediately after S3 upload
   - End-to-end synchronous chain

3. **VPC Connectivity**:
   - Lambda in VPC with EC2 subnet
   - EC2 in private subnet
   - Communication via private IP (10.0.1.x:5000)

4. **Technology Stack**:
   - Lambda: Python 3.9 with urllib3
   - EC2: Flask + requests library
   - S3: Public bucket with REST PUT

## Deployment Components

- **main.tf**: Terraform infrastructure (VPC, Lambda, EC2, S3, Security Groups)
- **variables.tf**: Configuration variables (region: ap-south-1)
- **outputs.tf**: Output resource IDs and IPs
- **lambda_function.py**: Lambda code (calls Flask)
- **flask_server_startup.sh**: EC2 user data script (embedded Flask app)
- **cloudformation-template.yaml**: CloudFormation alternative
