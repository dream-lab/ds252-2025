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

## PART 3: Benchmark Performance

### Step 3.1: Install Benchmarking Dependencies
```bash
# Install required packages
pip install boto3 matplotlib numpy
```

### Step 3.2: Run Benchmark Script
```bash
# Run the benchmark (takes exactly 5 minutes)
python3 benchmark.py

# Expected output shows real-time progress:
# [  10/300] E2E Latency: 1245.3ms | Avg E2E: 1245.3ms | Status: 200 | ✓
# [  20/300] E2E Latency: 1189.2ms | Avg E2E: 1210.4ms | Status: 200 | ✓
# ... continues for 300 requests at 1 RPS
```

### Step 3.3: Analyze Benchmark Results

After benchmark completes, you'll see statistics:

```
======================================================================
BENCHMARK STATISTICS
======================================================================

End-to-End (E2E) Lambda Response Latency:
  Min:     1050.23 ms
  Max:     2340.56 ms
  Mean:    1250.40 ms
  Median:  1190.10 ms
  Std Dev:   280.45 ms
  P95:     1890.30 ms
  P99:     2150.80 ms
  Count:   300

Lambda to EC2 and Back Call Latency:
  Min:      850.12 ms
  Max:     2100.45 ms
  Mean:    1050.30 ms
  Median:   980.20 ms
  Std Dev:   210.15 ms
  P95:     1650.40 ms
  P99:     1920.50 ms
  Count:   300

Status Code Distribution:
  200: 298 ( 99.3%)
  504:   2 (  0.7%)
```

### Step 3.4: View Visualization Plots

The benchmark generates `benchmark_results.png` with 2 plots:

**Plot 1: E2E Latency Timeline**
- Shows how latency changes across all 300 requests
- Red line: Median latency
- Green line: Mean latency

**Plot 2: Median Latency Comparison**
- Blue bar: E2E Lambda Response latency
- Red bar: Lambda-to-EC2 round-trip latency
- Shows which component is the bottleneck

```bash
# View the plots
open benchmark_results.png  # macOS
# or
display benchmark_results.png  # Linux
```

### Step 3.5: Analyze Performance Data

```bash
# View raw benchmark data in JSON
cat benchmark_results.json | jq '.statistics'

# Expected output:
# {
#   "e2e_median": 1190.10,
#   "e2e_mean": 1250.40,
#   "lambda_ec2_median": 980.20,
#   "lambda_ec2_mean": 1050.30
# }
```

### Step 3.6: Key Metrics to Understand

```
E2E Latency = Total time for Lambda to:
  1. Start execution
  2. Call EC2 Flask server
  3. Wait for EC2 response
  4. Parse response
  5. Return to caller

Lambda-to-EC2 Latency = Time spent on HTTP call only:
  1. Network latency to EC2
  2. EC2 processing (image download + S3 upload)
  3. Network latency back to Lambda

Difference = Lambda overhead (startup, JSON parsing, etc.)
```

### Step 3.7: Performance Analysis Questions

```bash
# Question 1: What's the dominant bottleneck?
# If E2E ≈ Lambda-EC2: EC2 processing is the bottleneck
# If E2E >> Lambda-EC2: Lambda startup/overhead is the bottleneck

# Question 2: What's the 99th percentile latency?
# This indicates worst-case performance

# Question 3: Success rate?
# High 504 errors indicate EC2 connectivity issues

# Question 4: How much variation in latency?
# Large Std Dev = inconsistent performance
# Small Std Dev = predictable performance
```

### Step 3.8: Expected Performance Ranges

| Metric | Good | Acceptable | Poor |
|--------|------|-----------|------|
| E2E Median | <1000ms | 1000-1500ms | >1500ms |
| Lambda-EC2 Median | <800ms | 800-1200ms | >1200ms |
| Success Rate | >99% | 95-99% | <95% |
| P99 Latency | <1500ms | 1500-2000ms | >2000ms |

### Step 3.9: Common Performance Patterns

**Pattern 1: High E2E, Lower Lambda-EC2**
```
Likely cause: Lambda cold start on first request
Solution: Pre-warm Lambda or use Provisioned Concurrency
```

**Pattern 2: High Lambda-EC2, High E2E**
```
Likely cause: EC2 slow or image download slow
Solution: Upgrade EC2 instance type or use smaller image
```

**Pattern 3: Consistent High Latency**
```
Likely cause: Network latency between regions
Solution: Ensure EC2 and Lambda in same region/AZ
```

**Pattern 4: Inconsistent Latency (high Std Dev)**
```
Likely cause: EC2 CPU throttling or network jitter
Solution: Monitor EC2 CPU/network metrics
```

### Step 3.10: Export Results

```bash
# Copy results to analyze later
mkdir -p benchmark_results
cp benchmark_results.png benchmark_results/
cp benchmark_results.json benchmark_results/

# Create summary report
cat > benchmark_results/SUMMARY.txt << 'EOF'
DS252 Lab Session 6 - Benchmark Results
Timestamp: $(date)

E2E Median Latency: [INSERT VALUE] ms
Lambda-EC2 Median Latency: [INSERT VALUE] ms
Success Rate: [INSERT VALUE] %

Key Observations:
[Your analysis here]

EOF
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
rm -rf benchmark_results/

echo "✅ Cleanup complete"
```

---

## Notes

- All commands assume you're in `ds252-2025/lab-session6-1710`
- Flask server runs on port 5000
- Lambda calls EC2 Flask server synchronously
- Images are stored in public S3 bucket
- Delete resources when done to avoid AWS charges
