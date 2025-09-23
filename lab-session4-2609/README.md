# Serverless Workflow Lab — Plan & Prerequisites

This lab demonstrates two serverless workflows on AWS to process images and measure performance (cold-starts, throughput, cost).  

---

## Plan

Part 1. **Provision baseline infrastructure (Using Console)**  
   - Create S3 bucket for storing images.  
   - Create DynamoDB table for storing metadata.  

Part 2. **Deploy Workflows (CLI)**  
   - **Workflow 1 (Lambda ingestion):**  
     - Lambda fetches image from URL.  
     - Uploads image to S3.  
     - Inserts metadata into DynamoDB.  
   - **Workflow 2 (Step Functions classification):**  
     - Step Function reads metadata from DynamoDB.  
     - Fetches image from S3.  
     - Runs preprocessing (grayscale → flip → rotate → resize).  
     - Executes three inference Lambdas in parallel (AlexNet, ResNet, MobileNet).  
     - Aggregates results.  
     - Updates metadata with labels in DynamoDB.  
  

Part 3. **Benchmark and Visualize Workflows (CLI and console)**  
   - Use [Apache JMeter](https://jmeter.apache.org/) to invoke:  
     - Workflow 1: Lambda ingestion.  
     - Workflow 2: Step Functions classification pipeline.  
   - Load profile: **1 RPS for 180 seconds (3 minutes)**.  

   **Collect Logs & Metrics**  
      - CloudWatch Logs from each Lambda.  
      - CloudWatch Metrics: Duration, InitDuration (cold starts), Invocations, Errors, Throttles.  

   **Analysis & Visualization**  
      - Export CloudWatch logs.  
      - Parse logs with Python (Pandas).  
      - Plot timelines using Matplotlib:  
      - Cold starts vs warm starts.  
      - End-to-end latencies.  
      - Throughput over time.  
      - Estimate cost from Lambda, S3, DynamoDB usage.  

---

## Workflows

### Workflow 1 — Lambda ingestion
1. A Lambda function takes an **image URL** as input.  
2. It **downloads the image**.  
3. The image is **uploaded to S3**.  
4. The Lambda function writes **metadata** into DynamoDB.  

### Workflow 2 — Step Functions classification pipeline
1. Step Function **reads metadata** from DynamoDB.  
2. **FetchImage Lambda**: retrieves image from S3.  
3. **Preprocessing pipeline**:  
   - Grayscale  
   - Flip  
   - Rotate  
   - Resize  
4. **Parallel inference**:  
   - AlexNet  
   - ResNet  
   - MobileNet  
5. **Aggregator and Update Dynamo**: consolidates results &  writes labels and status back into DynamoDB.

---

## Step Function

``` mermaid

flowchart LR
   A[fetchImage] --> B[Grayscale]
   B --> C[Flip]
   C --> D[Rotate]
   D --> E[Resize]
   E --> F[AlexNet]
    E --> G[ResNet]
    E --> H[MobileNet]
    F --> I[PushToDynamo]
    G--> I
    H--> I

```




```markdown
# Prerequisites

## AWS Account
- Active AWS account with billing enabled
- IAM user/role with permissions for:
  - S3
  - Lambda
  - DynamoDB
  - Step Functions
  - CloudWatch
  - IAM role creation

## AWS SAM CLI Installation

### macOS
```bash
brew tap aws/tap
brew install aws-sam-cli
```

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install unzip python3-pip
pip3 install aws-sam-cli
```

## Apache JMeter
1. Download from: https://jmeter.apache.org/
2. Unzip the downloaded file
3. Add the `bin/` directory to your system PATH
4. Verify installation:
```bash
jmeter -v
```
