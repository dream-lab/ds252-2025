# Serverless Workflow Lab — Plan & Prerequisites

This lab demonstrates two serverless workflows on AWS to process images and measure performance (cold-starts, throughput, cost).  

---

## Plan

1. **Provision baseline infrastructure**  
   - Create S3 bucket for storing images.  
   - Create DynamoDB table for storing metadata.  

2. **Implement Workflows**  
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

3. **Deploy Step Function**  
   - Define workflow with retries, timeouts, and error handling.  
   - Ensure all Lambdas and IAM roles are wired correctly.  

4. **Benchmark Workflows**  
   - Use [Apache JMeter](https://jmeter.apache.org/) to invoke:  
     - Workflow 1: Lambda ingestion.  
     - Workflow 2: Step Functions classification pipeline.  
   - Load profile: **1 RPS for 180 seconds (3 minutes)**.  

5. **Collect Logs & Metrics**  
   - CloudWatch Logs from each Lambda.  
   - CloudWatch Metrics: Duration, InitDuration (cold starts), Invocations, Errors, Throttles.  

6. **Analysis & Visualization**  
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
5. **Aggregator Lambda**: consolidates results.  
6. **Update Lambda**: writes labels and status back into DynamoDB.  

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
    F --> I[Aggregator]
    G--> I
    H--> I

```




