# DS252 Lab Session 6 - Deployment Guide

## Hybrid Architecture: Lambda + EC2 + S3

Simple step-by-step guide to deploy and test the hybrid architecture.

---

## ⚠️ Prerequisites

```bash
# Check installations
aws --version
terraform -version
jq --version

# Configure AWS
aws configure
# Region: ap-south-1
# Format: json

# Verify
aws sts get-caller-identity
```

---

## PART 1: Deploy with Terraform

### Step 1.1: Initialize Terraform
```bash
cd ds252-2025/lab-session6-1710
terraform init
```

### Step 1.2: Validate Configuration
```bash
terraform validate
# Expected: Success! The configuration is valid.
```

### Step 1.3: Create Plan
```bash
terraform plan -out=tfplan
```

### Step 1.4: Deploy Infrastructure
```bash
terraform apply tfplan
# Takes 3-5 minutes
# Expected: Apply complete! Resources: XX added
```

### Step 1.5: Get Outputs
```bash
terraform output

# Save to variables
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

### Step 1.6: Wait for EC2 to be Ready
```bash
# Check instance status
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

### Step 1.7: Verify Flask Server is Running
```bash
# SSH into EC2 (key is in current directory)
ssh -o StrictHostKeyChecking=no -i ds252-hybrid-key.pem ec2-user@$EC2_PUBLIC_IP

# Inside EC2, check Flask
sudo systemctl status flask-app.service

# Test locally on EC2
curl http://localhost:5000/

# Exit
exit
```

---

## PART 2: Invoke Lambda and Test EC2

### Step 2.1: Test Flask Server via HTTP
```bash
# Test directly from your machine
curl http://$EC2_PUBLIC_IP:5000/
# Expected: JSON response with service info
```

### Step 2.2: Test Lambda Invocation
```bash
# Create test payload
cat > test-payload.json << 'EOF'
{
  "image_url": "https://www.w3schools.com/css/img_5terre.jpg"
}
EOF

# Invoke Lambda
aws lambda invoke \
  --function-name $LAMBDA_NAME \
  --payload file://test-payload.json \
  response.json

# Check response
jq . response.json

# Expected: statusCode 200 with image processed
```

### Step 2.3: Verify Image in S3
```bash
# List images
aws s3 ls s3://$S3_BUCKET/images/

# Get image count
aws s3 ls s3://$S3_BUCKET/images/ --recursive --summarize | grep "Total Objects:"
```

### Step 2.4: Multiple Test Invocations
```bash
# Run 5 tests
for i in {1..5}; do
  echo "Test $i/5..."
  
  cat > test-$i.json << EOF
{
  "image_url": "https://www.w3schools.com/css/img_5terre.jpg?test=$i"
}
EOF

  aws lambda invoke \
    --function-name $LAMBDA_NAME \
    --payload file://test-$i.json \
    response-$i.json
  
  echo "Response $i:"
  jq '.statusCode' response-$i.json
  sleep 1
done

# Final count
echo "Total images in S3:"
aws s3 ls s3://$S3_BUCKET/images/ --recursive --summarize | grep "Total Objects:"
```

---

## Cleanup

### Destroy Terraform Resources
```bash
terraform destroy -auto-approve
```

### Clean Up Local Files
```bash
rm -rf .terraform/
rm -f .terraform.lock.hcl
rm -f terraform.tfstate*
rm -f *.pem
rm -f lambda_function.zip
rm -f tfplan
rm -f test-*.json
rm -f response*.json

echo "✅ Cleanup complete"
```

---

## Notes

- All commands assume you're in `ds252-2025/lab-session6-1710`
- Flask server runs on port 5000
- Lambda calls EC2 Flask server synchronously
- Images are stored in public S3 bucket
- Delete resources when done to avoid AWS charges
