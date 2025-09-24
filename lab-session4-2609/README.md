# Serverless Workflow Lab — Plan & Prerequisites

This lab demonstrates two serverless workflows on AWS to process images and measure performance (cold-starts, throughput, cost).  

---

# Prerequisites

## AWS Account
- Active AWS account with billing enabled

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

# Plan for the Lab Session

Part 1. **Provision baseline infrastructure (Using Console)**  
   - Create S3 bucket for storing images.  
   - Create DynamoDB table for storing metadata.  

Part 2. **Deploy Workflows (CLI)**  
   - **Lambda Function 1 (Lambda ingestion):**  
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
   - Use a python client to invoke:  
     - Workflow 1: Lambda ingestion.  
     - Workflow 2: Step Functions classification pipeline.  
   - Load profile: **1 RPS for 30 seconds**.  

     

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




