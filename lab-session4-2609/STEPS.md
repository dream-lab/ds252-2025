# Serverless Workflow Lab - Actionable Steps

## Part 1: Provision Baseline Infrastructure (Using AWS Console)

### Step 1: Create S3 Bucket for Image Storage

#### 1.1 Navigate to S3 Service
1. Open AWS Management Console
2. Search for "S3" in the services search bar
3. Click on "S3" to open the S3 dashboard

#### 1.2 Create the Bucket
1. Click **"Create bucket"** button
2. **Bucket name**: Enter a globally unique name (e.g., `serverless-lab-images-[timestamp]`)
   - Example: `serverless-lab-images-240925`
   - Note: Bucket names must be globally unique across all AWS accounts
3. **AWS Region**: Select your preferred region (e.g., `ap-south-1`)
4. **Object Ownership**: Keep default "ACLs disabled (recommended)"

#### 1.3 Configure Public Access Settings
1. **Block Public Access settings for this bucket**:
   - ✅ **UNCHECK** "Block all public access" (we need public read access for this lab)
   - ✅ **UNCHECK** all four individual settings:
     - Block public access to buckets and objects granted through new access control lists (ACLs)
     - Block public access to buckets and objects granted through any access control lists (ACLs)
     - Block public access to buckets and objects granted through new public bucket or access point policies
     - Block public access to buckets and objects granted through any public bucket or access point policies
2. ✅ **CHECK** the acknowledgment: "I acknowledge that the current settings might result in this bucket and the objects within becoming public"

#### 1.5 Create the Bucket
1. Click **"Create bucket"** button
2. Wait for the bucket to be created successfully

#### 1.6 Configure Bucket Policy for Public Read Access
1. Click on your newly created bucket name to open it
2. Go to the **"Permissions"** tab
3. Scroll down to **"Bucket policy"** section
4. Click **"Edit"**
5. Paste the following policy (replace `YOUR-BUCKET-NAME` with your actual bucket name):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
        }
    ]
}
```

6. Click **"Save changes"**

### Step 2: Create DynamoDB Table for Metadata Storage

#### 2.1 Navigate to DynamoDB Service
1. In AWS Management Console, search for "DynamoDB"
2. Click on "DynamoDB" to open the DynamoDB dashboard

#### 2.2 Create the Table
1. Click **"Create table"** button
2. **Table name**: `image-metadata`
3. **Partition key**: 
   - Key name: `image_id`
   - Type: `String`
4. **Sort key**: Leave empty (not needed for this use case)

#### 2.3 Configure Table Settings
1. **Table settings**: Select **"Customize settings"**
2. **Table class**: Keep default "DynamoDB Standard"
3. **Capacity mode**: Select **"On-demand"** (better for variable workloads)
   - This automatically scales based on traffic
   - No need to provision read/write capacity

#### 2.4 Configure Additional Settings
1. **Secondary indexes**: Skip (not needed for this lab)
2. **Encryption at rest**: Keep default "Owned by Amazon DynamoDB"
3. **Tags**: (Optional) Add tags:
   - Key: `Project`, Value: `ServerlessLab`
   - Key: `Environment`, Value: `Development`

#### 2.5 Create the Table
1. Click **"Create table"** button
2. Wait for the table status to change to "Active" (usually takes 1-2 minutes)

### Step 2.6: Understanding Lambda Permissions (For Reference)

**Q: How will Lambda functions get permissions to access DynamoDB and S3?**

Lambda functions will get permissions through **IAM Execution Roles**. Here's how it works:

#### Method 1: AWS SAM Template (Recommended - Part 2)
When we deploy using SAM in Part 2, the template will automatically create IAM roles with these permissions:

```yaml
# This will be in our SAM template (Part 2)
Policies:
  - DynamoDBCrudPolicy:
      TableName: image-metadata
  - S3CrudPolicy:
      BucketName: !Ref ImageBucket
```

#### Method 2: Manual IAM Role Creation (If needed)
If creating roles manually, each Lambda needs an execution role with:

**For DynamoDB access:**
- `dynamodb:GetItem` - Read metadata
- `dynamodb:PutItem` - Write metadata  
- `dynamodb:UpdateItem` - Update metadata
- `dynamodb:Query` - Query metadata
- `dynamodb:Scan` - Scan table (if needed)

**For S3 access:**
- `s3:GetObject` - Download images
- `s3:PutObject` - Upload images
- `s3:DeleteObject` - Delete images (if needed)

#### Security Flow:
```
1. Lambda function starts
2. AWS automatically assumes the execution role
3. Role provides temporary credentials
4. Lambda uses credentials to access DynamoDB/S3
5. All actions are logged in CloudTrail
```

**Note:** We'll handle all IAM permissions automatically in Part 2 using AWS SAM templates - no manual role creation needed!

---

## Part 2: Deploy Workflow 1 (Lambda Ingestion) - CLI

### Prerequisites for Part 2
- ✅ Part 1 completed (S3 bucket and DynamoDB table created)
- ✅ AWS SAM CLI installed (from prerequisites)
- ✅ AWS CLI configured with your credentials

### Step 1: Navigate to Workflow 1 Directory

```bash
cd /path/to/your/lab-session4-2609/workflow1-lambda
```

### Step 2: Update SAM Template Parameters

1. Open `template.yaml` in the workflow1-lambda directory
2. Update the default parameters to match your resources from Part 1:

```yaml
Parameters:
  S3BucketName:
    Type: String
    Description: Name of the S3 bucket for storing images
    Default: YOUR-ACTUAL-BUCKET-NAME  # Replace with your bucket name from Part 1
  
  DynamoDBTableName:
    Type: String
    Description: Name of the DynamoDB table for storing metadata
    Default: image-metadata  # Should match what you created in Part 1
```

### Step 3: Build the SAM Application

```bash
sam build
```

**Expected output:**
```
Building codeuri: src/ runtime: python3.9 architecture: x86_64 function: ImageIngestionFunction
Running PythonPipBuilder:ResolveDependencies
Running PythonPipBuilder:CopySource

Build Succeeded
```

### Step 4: Deploy the Lambda Function

#### Option A: Guided Deployment (First time)
```bash
sam deploy --guided
```

**Follow the prompts:**
- Stack Name: `serverless-lab-workflow1`
- AWS Region: `ap-south-1` (or your preferred region)
- Parameter S3BucketName: `[your-bucket-name-from-part1]`
- Parameter DynamoDBTableName: `image-metadata`
- Confirm changes before deploy: `Y`
- Allow SAM CLI IAM role creation: `Y`
- Save parameters to configuration file: `Y`
- SAM configuration file: `samconfig.toml`

#### Option B: Direct Deployment (Subsequent deployments)
```bash
sam deploy \
  --stack-name serverless-lab-workflow1 \
  --parameter-overrides S3BucketName=YOUR-BUCKET-NAME DynamoDBTableName=image-metadata \
  --capabilities CAPABILITY_IAM \
  --region ap-south-1 \
  --resolve-s3
```

**Note:** The `--resolve-s3` flag automatically creates a managed S3 bucket for Lambda deployment packages.

### Step 5: Verify Deployment

#### 5.1 Check CloudFormation Stack
```bash
aws cloudformation describe-stacks --stack-name serverless-lab-workflow1 --region ap-south-1
```

#### 5.2 Get Stack Outputs
```bash
aws cloudformation describe-stacks \
  --stack-name serverless-lab-workflow1 \
  --region ap-south-1 \
  --query 'Stacks[0].Outputs'
```

**Expected outputs:**
- `ImageIngestionFunction`: Lambda function ARN
- `ApiGatewayEndpoint`: HTTP endpoint for testing
- `S3BucketName`: Your S3 bucket name
- `DynamoDBTableName`: Your DynamoDB table name

### Step 6: Test the Lambda Function

#### Method 1: Test via AWS CLI (Direct Lambda invocation)

1. Create a test payload file:
```bash
cat > test-payload.json << EOF
{
  "image_url": "https://picsum.photos/800/600"
}
EOF
```

2. Invoke the Lambda function:
```bash
aws lambda invoke \
  --function-name serverless-lab-workflow1-image-ingestion \
  --payload file://test-payload.json \
  --region ap-south-1 \
  response.json
```

3. Check the response:
```bash
cat response.json
```

#### Method 2: Test via API Gateway (HTTP endpoint)

1. Get the API endpoint from stack outputs:
```bash
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name serverless-lab-workflow1 \
  --region ap-south-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayEndpoint`].OutputValue' \
  --output text)

echo "API Endpoint: $API_ENDPOINT"
```

2. Test with curl:
```bash
curl -X POST $API_ENDPOINT \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://picsum.photos/800/600"}' 
```

### Step 7: Verify Results

#### 7.1 Check S3 Bucket
1. Go to AWS S3 Console
2. Open your bucket
3. Look for a new object in the `raw-images/` folder
4. Verify the image was uploaded successfully

#### 7.2 Check DynamoDB Table
1. Go to AWS DynamoDB Console
2. Open your `image-metadata` table
3. Click "Explore table items"
4. Verify metadata record was created with:
   - `image_id`
   - `s3_url`
   - `status: uploaded`
   - `workflow_stage: ingestion_complete`

#### 7.3 Check CloudWatch Logs
```bash
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/serverless-lab-workflow1" --region ap-south-1
```


### Step 8: Clean Up (AT THE END)

To delete the Lambda function and API Gateway:
```bash
sam delete --stack-name serverless-lab-workflow1 --region ap-south-1
```

**Note:** This will NOT delete your S3 bucket and DynamoDB table from Part 1.

### ✅ Workflow 1 Complete!

You have successfully deployed and tested:
- ✅ Lambda function that downloads images from URLs
- ✅ Automatic S3 upload with proper metadata
- ✅ DynamoDB metadata storage
- ✅ API Gateway endpoint for HTTP access
- ✅ Proper IAM permissions (automatically created by SAM)

**Next**: Proceed to create Workflow 2 (Step Functions classification pipeline).

---

## Part 2B: Deploy Workflow 2 (Step Functions Classification Pipeline) - CLI

### Prerequisites for Workflow 2
- ✅ Part 1 completed (S3 bucket and DynamoDB table created)
- ✅ Workflow 1 deployed and tested (recommended)
- ✅ AWS SAM CLI installed
- ✅ AWS CLI configured

### Step 1: Navigate to Workflow 2 Directory

```bash
cd /path/to/your/lab-session4-2609/workflow2-stepfunctions
```

### Step 2: Update SAM Template Parameters

1. Open `template.yaml` in the workflow2-stepfunctions directory
2. Update the default parameters to match your resources from Part 1:

```yaml
Parameters:
  S3BucketName:
    Type: String
    Description: Name of the S3 bucket for storing images
    Default: YOUR-ACTUAL-BUCKET-NAME  # Replace with your bucket name from Part 1
  
  DynamoDBTableName:
    Type: String
    Description: Name of the DynamoDB table for storing metadata
    Default: image-metadata  # Should match what you created in Part 1
```

### Step 3: Build the SAM Application

```bash
sam build
```

**Expected output:**
```
Building codeuri: fetch-image/src/ runtime: python3.9 architecture: x86_64 function: FetchImageFunction
Building codeuri: preprocessing/src/ runtime: python3.9 architecture: x86_64 function: PreprocessingFunction
Building codeuri: ml-inference/src/ runtime: python3.9 architecture: x86_64 function: MLInferenceFunction
Building codeuri: aggregator/src/ runtime: python3.9 architecture: x86_64 function: AggregatorFunction

Build Succeeded
```

### Step 4: Deploy the Step Functions Pipeline

#### Option A: Guided Deployment (First time)
```bash
sam deploy --guided
```

**Follow the prompts:**
- Stack Name: `serverless-lab-workflow2`
- AWS Region: `ap-south-1` (same as Workflow 1)
- Parameter S3BucketName: `[your-bucket-name-from-part1]`
- Parameter DynamoDBTableName: `image-metadata`
- Confirm changes before deploy: `Y`
- Allow SAM CLI IAM role creation: `Y`
- Save parameters to configuration file: `Y`
- SAM configuration file: `samconfig.toml`

#### Option B: Direct Deployment (Subsequent deployments)
```bash
sam deploy \
  --stack-name serverless-lab-workflow2 \
  --parameter-overrides S3BucketName=YOUR-BUCKET-NAME DynamoDBTableName=image-metadata \
  --capabilities CAPABILITY_IAM \
  --region ap-south-1 \
  --resolve-s3
```

**Note:** The `--resolve-s3` flag automatically creates a managed S3 bucket for Lambda deployment packages. SAM will show:
```
Managed S3 bucket: aws-sam-cli-managed-default-samclisourcebucket-[random-id]
A different default S3 bucket can be set in samconfig.toml
```

### Step 5: Verify Deployment

#### 5.1 Check CloudFormation Stack
```bash
aws cloudformation describe-stacks --stack-name serverless-lab-workflow2 --region ap-south-1
```

#### 5.2 Get Stack Outputs
```bash
aws cloudformation describe-stacks \
  --stack-name serverless-lab-workflow2 \
  --region ap-south-1 \
  --query 'Stacks[0].Outputs'
```

**Expected outputs:**
- `FetchImageFunctionArn`: Fetch image Lambda ARN
- `PreprocessingFunctionArn`: Preprocessing Lambda ARN
- `MLInferenceFunctionArn`: ML inference Lambda ARN
- `AggregatorFunctionArn`: Aggregator Lambda ARN
- `StateMachineArn`: Step Functions state machine ARN
- `ApiGatewayEndpoint`: HTTP endpoint for triggering pipeline

### Step 6: Test the Step Functions Pipeline

#### Method 1: Test via AWS CLI (Direct Step Functions invocation)

1. First, make sure you have an image uploaded via Workflow 1:
```bash
# Get an image_id from DynamoDB (from previous Workflow 1 test)
aws dynamodb scan \
  --table-name image-metadata \
  --region ap-south-1 \
  --query 'Items[0].image_id.S'
```

2. Create test payload with the image_id:
```bash
IMAGE_ID="your-image-id-from-step-above"
cat > test-stepfunctions-payload.json << EOF
{
  "image_id": "$IMAGE_ID"
}
EOF
```

3. Get the State Machine ARN:
```bash
STATE_MACHINE_ARN=$(aws cloudformation describe-stacks \
  --stack-name serverless-lab-workflow2 \
  --region ap-south-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`StateMachineArn`].OutputValue' \
  --output text)

echo "State Machine ARN: $STATE_MACHINE_ARN"
```

4. Start execution:
```bash
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --input file://test-stepfunctions-payload.json \
  --region ap-south-1
```

5. Monitor execution:
```bash
# Get execution ARN from previous command output, then:
EXECUTION_ARN="your-execution-arn-here"

aws stepfunctions describe-execution \
  --execution-arn $EXECUTION_ARN \
  --region ap-south-1
```

#### Method 2: Test via API Gateway (HTTP endpoint)

1. Get the API endpoint:
```bash
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name serverless-lab-workflow2 \
  --region ap-south-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayEndpoint`].OutputValue' \
  --output text)

echo "API Endpoint: $API_ENDPOINT"
```

2. Test with curl:
```bash
curl -X POST $API_ENDPOINT \
  -H "Content-Type: application/json" \
  -d '{"image_id": "your-image-id-here"}' 
```

### Step 7: Monitor Pipeline Execution

#### 7.1 Step Functions Console
1. Go to AWS Step Functions Console
2. Find your state machine: `serverless-lab-workflow2-classification-pipeline`
3. Click on recent executions to see visual workflow progress
4. View execution details, input/output, and any errors

#### 7.2 CloudWatch Logs for Individual Lambdas
```bash
# Fetch Image Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/serverless-lab-workflow2-fetch" --region ap-south-1

# Preprocessing Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/serverless-lab-workflow2-preprocessing" --region ap-south-1

# ML Inference Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/serverless-lab-workflow2-ml-inference" --region ap-south-1

# Aggregator Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/serverless-lab-workflow2-aggregator" --region ap-south-1
```

#### 7.3 Step Functions Execution History
```bash
aws stepfunctions get-execution-history \
  --execution-arn $EXECUTION_ARN \
  --region ap-south-1
```

### Step 8: Verify Results

#### 8.1 Check DynamoDB for Classification Results
```bash
# Query the specific image record
aws dynamodb get-item \
  --table-name image-metadata \
  --key '{"image_id":{"S":"your-image-id-here"}}' \
  --region ap-south-1
```

**Expected fields in the result:**
- `workflow_stage`: `classification_completed`
- `classification_results`: Complete results from all models
- `consensus_label`: Final predicted label
- `consensus_confidence`: Confidence score
- `successful_models`: List of models that completed successfully
- `processing_completed_at`: Timestamp

#### 8.2 Verify Pipeline Flow
The complete pipeline should show:
1. ✅ **FetchImage**: Image retrieved from S3
2. ✅ **Preprocessing**: Grayscale → Flip → Rotate → Resize
3. ✅ **Parallel Inference**: AlexNet, ResNet, MobileNet (in parallel)
4. ✅ **Aggregation**: Results combined and consensus calculated
5. ✅ **DynamoDB Update**: Final results stored

### Step 9: Test End-to-End Workflow (Both Workflows)

#### 9.1 Complete Pipeline Test
```bash
# Step 1: Ingest new image (Workflow 1)
curl -X POST https://your-workflow1-api-endpoint/ingest \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://picsum.photos/800/600"}' \
  | jq '.image_id'

# Step 2: Get the image_id from response, then classify (Workflow 2)
curl -X POST $API_ENDPOINT \
  -H "Content-Type: application/json" \
  -d '{"image_id": "image-id-from-step1"}' \
  | jq '.'
```

#### 9.2 Monitor Complete Flow
1. **Workflow 1**: Check S3 for uploaded image and DynamoDB for initial metadata
2. **Workflow 2**: Check Step Functions execution and final DynamoDB results

### Step 10: Performance Analysis Preparation

The deployed pipeline is now ready for Part 3 (JMeter benchmarking):

```bash
# Get both API endpoints for JMeter testing
echo "Workflow 1 (Ingestion) API:"
aws cloudformation describe-stacks \
  --stack-name serverless-lab-workflow1 \
  --region ap-south-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayEndpoint`].OutputValue' \
  --output text

echo "Workflow 2 (Classification) State Machine ARN:"
aws cloudformation describe-stacks \
  --stack-name serverless-lab-workflow2 \
  --region ap-south-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`StateMachineArn`].OutputValue' \
  --output text
```

### Step 11: Clean Up (Optional)

To delete Workflow 2 resources:
```bash
sam delete --stack-name serverless-lab-workflow2 --region ap-south-1
```

**Note:** This preserves your S3 bucket and DynamoDB table for other workflows.

### ✅ Workflow 2 Complete!

You have successfully deployed and tested:
- ✅ **4 Lambda Functions**: FetchImage, Preprocessing, MLInference, Aggregator
- ✅ **Step Functions Pipeline**: Orchestrates the complete classification workflow
- ✅ **Parallel Processing**: AlexNet, ResNet, MobileNet run simultaneously
- ✅ **Result Aggregation**: Consensus calculation from multiple models
- ✅ **Error Handling**: Retry logic and graceful failure handling
- ✅ **API Gateway Integration**: HTTP endpoint for easy testing

**Architecture Flow:**
```
Input: image_id → FetchImage → Preprocessing → [AlexNet || ResNet || MobileNet] → Aggregator → DynamoDB Results
```

**Next**: Proceed to Part 3 for JMeter benchmarking and performance analysis!

---

### Step 3: Verification Steps (Part 1)

#### 3.1 Verify S3 Bucket
1. Go back to S3 console
2. Find your bucket in the list
3. Click on the bucket name
4. Verify:
   - ✅ Bucket is accessible
   - ✅ "Permissions" tab shows public access is allowed
   - ✅ Bucket policy is correctly applied

#### 3.2 Verify DynamoDB Table
1. Go back to DynamoDB console
2. Click on "Tables" in the left sidebar
3. Find your `image-metadata` table
4. Click on the table name
5. Verify:
   - ✅ Table status is "Active"
   - ✅ Partition key is `image_id` (String)
   - ✅ Billing mode is "On-demand"

#### 3.3 Record Important Information
Create a note with the following information (you'll need this for later parts):

```
S3 Bucket Details:
- Bucket Name: [your-bucket-name]
- Region: [your-selected-region]
- ARN: arn:aws:s3:::[your-bucket-name]

DynamoDB Table Details:
- Table Name: image-metadata
- Partition Key: image_id (String)
- Region: [your-selected-region]
- ARN: [copy from table details page]
```

### ✅ Part 1 Complete!

You have successfully provisioned:
- ✅ S3 bucket for image storage with public read access
- ✅ DynamoDB table for metadata storage with on-demand billing

**Next**: Proceed to Part 2 for deploying the serverless workflows using AWS CLI and SAM.

---

## Troubleshooting

### Common Issues:

**S3 Bucket Name Already Exists**
- Solution: Try a different, more unique bucket name with your initials and timestamp

**Access Denied Errors**
- Solution: Ensure your AWS user has appropriate S3 and DynamoDB permissions

**Public Access Warnings**
- This is expected for this lab - we need public read access to S3 objects

**DynamoDB Table Creation Timeout**
- Wait a few more minutes - table creation can take 2-5 minutes depending on AWS region load

**SAM Deployment Issues:**

**"S3 Bucket not specified" Error**
- Solution: Add `--resolve-s3` flag to create managed bucket automatically
- Or use `--s3-bucket your-existing-bucket-name` if you have a specific bucket

**"Unable to upload artifact" Error**
- Solution: Ensure you have internet connectivity and AWS credentials are valid
- Try: `aws sts get-caller-identity` to verify your AWS access

**Large Upload Timeouts**
- The ML inference Lambda has large dependencies (NumPy, Pillow)
- If upload is slow, be patient or use a faster internet connection
- Consider using `sam build` with `--use-container` for consistent builds

---

## Part 3: Load Testing with Python Client

### Prerequisites
- ✅ Both Workflow 1 and Workflow 2 deployed and tested
- ✅ Python 3.x installed
- ✅ `requests` library (`pip install requests`)

### Step 1: Get API Endpoints

```bash
# Get Workflow 1 endpoint
WORKFLOW1_API=$(aws cloudformation describe-stacks \
  --stack-name serverless-lab-workflow1 \
  --region ap-south-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayEndpoint`].OutputValue' \
  --output text)

echo "Workflow 1 API: $WORKFLOW1_API"

# Get Workflow 2 API endpoint
WORKFLOW2_API=$(aws cloudformation describe-stacks \
  --stack-name serverless-lab-workflow2 \
  --region ap-south-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayEndpoint`].OutputValue' \
  --output text)

echo "Workflow 2 API: $WORKFLOW2_API"

# Get Workflow 2 State Machine ARN (for reference)
WORKFLOW2_ARN=$(aws cloudformation describe-stacks \
  --stack-name serverless-lab-workflow2 \
  --region ap-south-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`StateMachineArn`].OutputValue' \
  --output text)

echo "Workflow 2 ARN: $WORKFLOW2_ARN"

# Get an actual image_id for Workflow 2 testing
IMAGE_ID=$(aws dynamodb scan \
  --table-name image-metadata \
  --region ap-south-1 \
  --query 'Items[0].image_id.S' \
  --output text)

echo "Test Image ID: $IMAGE_ID"
```

### Step 2: Install Dependencies

```bash
# Install required Python package
pip install requests
```

### Step 3: Run Load Test (Using Environment Variables)

The script automatically uses the environment variables set in Step 1:

```bash
# Export the variables (from Step 1 commands)
export WORKFLOW1_API="$WORKFLOW1_API"
export WORKFLOW2_API="$WORKFLOW2_API" 
export IMAGE_ID="$IMAGE_ID"

# Run the load test
python3 load_test.py
```

**Note**: The CloudFormation outputs include the full paths (`/ingest` and `/classify`), and the Python script handles this automatically.

**Alternative: Direct Run**
If you prefer to run without setting environment variables:
```bash
# Run with inline environment variables
WORKFLOW1_API="$WORKFLOW1_API" WORKFLOW2_API="$WORKFLOW2_API" IMAGE_ID="$IMAGE_ID" python3 load_test.py
```

**Note**: The script has fallback default values, so it will work even without environment variables (using the current configured endpoints).

### Expected Output:

```
🧪 Serverless Workflow Load Tester
==================================================
Workflow 1 API: https://your-api.execute-api.ap-south-1.amazonaws.com/prod
Workflow 2 API: https://your-api.execute-api.ap-south-1.amazonaws.com/prod
Test Image ID:  84aedee2-e274-4d6a-ada8-dcd6c7bbf5ff

🚀 Starting Workflow 1 Load Test
   Duration: 30s, Rate: 1 RPS
   ✅ Request 1: 1234.5ms
   ✅ Request 2: 987.2ms
   ...
✅ Workflow 1 test completed: 30 requests

🚀 Starting Workflow 2 Load Test
   Duration: 30s, Rate: 1 RPS
   ✅ Request 1: 15678.3ms
   ✅ Request 2: 12456.7ms
   ...
✅ Workflow 2 test completed: 30 requests

📊 LOAD TEST RESULTS SUMMARY
============================================================
🔹 Workflow 1 (Ingestion)
Total Requests:     30
Successful:         30
Success Rate:       100.0%
Avg Response Time:  1234.5ms

🔹 Workflow 2 (Classification)
Total Requests:     30
Successful:         29
Success Rate:       96.7%
Avg Response Time:  14567.8ms
============================================================
📄 Detailed results saved to: load_test_results.json
```
