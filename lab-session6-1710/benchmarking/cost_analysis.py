#!/usr/bin/env python3
"""
Cost analysis script for DS252 serverless workflows
"""

import json
import argparse
import boto3
from datetime import datetime, timedelta
import pandas as pd

def get_lambda_costs(region='us-east-1', days_back=1):
    """Get Lambda costs from AWS Cost Explorer"""
    ce_client = boto3.client('ce', region_name=region)
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back)
    
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}
            ]
        )
        
        return response
    except Exception as e:
        print(f"Error getting cost data: {e}")
        return None

def estimate_lambda_costs(results_data):
    """Estimate Lambda costs based on load test results"""
    # AWS Lambda pricing (as of 2024)
    # $0.0000166667 per GB-second
    # $0.20 per 1M requests
    
    memory_gb = 0.5  # Assuming 512MB memory allocation
    avg_duration_seconds = results_data['analysis'].get('avg_duration_ms', 1000) / 1000
    
    total_requests = results_data['analysis']['total_requests']
    successful_requests = results_data['analysis']['successful_requests']
    
    # Calculate compute cost
    compute_cost = successful_requests * memory_gb * avg_duration_seconds * 0.0000166667
    
    # Calculate request cost
    request_cost = (successful_requests / 1000000) * 0.20
    
    total_cost = compute_cost + request_cost
    
    return {
        'compute_cost_usd': compute_cost,
        'request_cost_usd': request_cost,
        'total_cost_usd': total_cost,
        'total_requests': total_requests,
        'successful_requests': successful_requests,
        'avg_duration_seconds': avg_duration_seconds
    }

def estimate_stepfunctions_costs(results_data):
    """Estimate Step Functions costs based on load test results"""
    # AWS Step Functions pricing (as of 2024)
    # $0.025 per 1,000 state transitions
    
    # Assuming each workflow has ~10 state transitions
    state_transitions_per_execution = 10
    
    successful_requests = results_data['analysis']['successful_requests']
    total_state_transitions = successful_requests * state_transitions_per_execution
    
    # Calculate cost
    cost = (total_state_transitions / 1000) * 0.025
    
    return {
        'total_cost_usd': cost,
        'total_executions': successful_requests,
        'state_transitions_per_execution': state_transitions_per_execution,
        'total_state_transitions': total_state_transitions
    }

def estimate_dynamodb_costs(results_data):
    """Estimate DynamoDB costs based on load test results"""
    # AWS DynamoDB pricing (as of 2024)
    # On-demand: $0.25 per million write request units
    # On-demand: $0.25 per million read request units
    
    successful_requests = results_data['analysis']['successful_requests']
    
    # Assuming each request does 2 writes and 1 read
    write_requests = successful_requests * 2
    read_requests = successful_requests * 1
    
    write_cost = (write_requests / 1000000) * 0.25
    read_cost = (read_requests / 1000000) * 0.25
    
    total_cost = write_cost + read_cost
    
    return {
        'write_cost_usd': write_cost,
        'read_cost_usd': read_cost,
        'total_cost_usd': total_cost,
        'write_requests': write_requests,
        'read_requests': read_requests
    }

def estimate_s3_costs(results_data):
    """Estimate S3 costs based on load test results"""
    # AWS S3 pricing (as of 2024)
    # Standard storage: $0.023 per GB per month
    # PUT requests: $0.0005 per 1,000 requests
    # GET requests: $0.0004 per 1,000 requests
    
    successful_requests = results_data['analysis']['successful_requests']
    
    # Assuming each image is 1MB on average
    avg_image_size_mb = 1
    total_storage_gb = (successful_requests * avg_image_size_mb) / 1024
    
    # Storage cost (for the test duration, prorated)
    storage_cost_per_month = total_storage_gb * 0.023
    storage_cost = storage_cost_per_month * (1/30)  # Assuming 1 day test
    
    # Request costs
    put_cost = (successful_requests / 1000) * 0.0005
    get_cost = (successful_requests / 1000) * 0.0004  # Assuming same number of GETs
    
    total_cost = storage_cost + put_cost + get_cost
    
    return {
        'storage_cost_usd': storage_cost,
        'put_cost_usd': put_cost,
        'get_cost_usd': get_cost,
        'total_cost_usd': total_cost,
        'total_storage_gb': total_storage_gb,
        'put_requests': successful_requests,
        'get_requests': successful_requests
    }

def analyze_costs(terraform_results, cloudformation_results):
    """Analyze and compare costs between Terraform and CloudFormation deployments"""
    
    cost_analysis = {
        'terraform': {},
        'cloudformation': {},
        'comparison': {}
    }
    
    # Analyze Terraform costs
    terraform_lambda_cost = estimate_lambda_costs(terraform_results)
    terraform_stepfunctions_cost = estimate_stepfunctions_costs(terraform_results)
    terraform_dynamodb_cost = estimate_dynamodb_costs(terraform_results)
    terraform_s3_cost = estimate_s3_costs(terraform_results)
    
    cost_analysis['terraform'] = {
        'lambda': terraform_lambda_cost,
        'stepfunctions': terraform_stepfunctions_cost,
        'dynamodb': terraform_dynamodb_cost,
        's3': terraform_s3_cost,
        'total_cost_usd': (
            terraform_lambda_cost['total_cost_usd'] +
            terraform_stepfunctions_cost['total_cost_usd'] +
            terraform_dynamodb_cost['total_cost_usd'] +
            terraform_s3_cost['total_cost_usd']
        )
    }
    
    # Analyze CloudFormation costs
    cloudformation_lambda_cost = estimate_lambda_costs(cloudformation_results)
    cloudformation_stepfunctions_cost = estimate_stepfunctions_costs(cloudformation_results)
    cloudformation_dynamodb_cost = estimate_dynamodb_costs(cloudformation_results)
    cloudformation_s3_cost = estimate_s3_costs(cloudformation_results)
    
    cost_analysis['cloudformation'] = {
        'lambda': cloudformation_lambda_cost,
        'stepfunctions': cloudformation_stepfunctions_cost,
        'dynamodb': cloudformation_dynamodb_cost,
        's3': cloudformation_s3_cost,
        'total_cost_usd': (
            cloudformation_lambda_cost['total_cost_usd'] +
            cloudformation_stepfunctions_cost['total_cost_usd'] +
            cloudformation_dynamodb_cost['total_cost_usd'] +
            cloudformation_s3_cost['total_cost_usd']
        )
    }
    
    # Compare costs
    terraform_total = cost_analysis['terraform']['total_cost_usd']
    cloudformation_total = cost_analysis['cloudformation']['total_cost_usd']
    
    cost_analysis['comparison'] = {
        'terraform_total_usd': terraform_total,
        'cloudformation_total_usd': cloudformation_total,
        'difference_usd': cloudformation_total - terraform_total,
        'difference_percent': ((cloudformation_total - terraform_total) / terraform_total * 100) if terraform_total > 0 else 0,
        'cheaper_deployment': 'terraform' if terraform_total < cloudformation_total else 'cloudformation'
    }
    
    return cost_analysis

def generate_cost_report(cost_analysis, output_file):
    """Generate cost analysis report"""
    
    report = f"""
# DS252 Serverless Workflows - Cost Analysis Report

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

This report analyzes the cost differences between Terraform and CloudFormation deployments of the DS252 serverless workflows.

## Cost Breakdown

### Terraform Deployment
- **Lambda Costs**: ${cost_analysis['terraform']['lambda']['total_cost_usd']:.6f}
- **Step Functions Costs**: ${cost_analysis['terraform']['stepfunctions']['total_cost_usd']:.6f}
- **DynamoDB Costs**: ${cost_analysis['terraform']['dynamodb']['total_cost_usd']:.6f}
- **S3 Costs**: ${cost_analysis['terraform']['s3']['total_cost_usd']:.6f}
- **Total Cost**: ${cost_analysis['terraform']['total_cost_usd']:.6f}

### CloudFormation Deployment
- **Lambda Costs**: ${cost_analysis['cloudformation']['lambda']['total_cost_usd']:.6f}
- **Step Functions Costs**: ${cost_analysis['cloudformation']['stepfunctions']['total_cost_usd']:.6f}
- **DynamoDB Costs**: ${cost_analysis['cloudformation']['dynamodb']['total_cost_usd']:.6f}
- **S3 Costs**: ${cost_analysis['cloudformation']['s3']['total_cost_usd']:.6f}
- **Total Cost**: ${cost_analysis['cloudformation']['total_cost_usd']:.6f}

## Cost Comparison

- **Cost Difference**: ${cost_analysis['comparison']['difference_usd']:.6f}
- **Percentage Difference**: {cost_analysis['comparison']['difference_percent']:.2f}%
- **More Cost-Effective**: {cost_analysis['comparison']['cheaper_deployment'].title()}

## Detailed Analysis

### Lambda Costs
- Terraform: ${cost_analysis['terraform']['lambda']['total_cost_usd']:.6f}
- CloudFormation: ${cost_analysis['cloudformation']['lambda']['total_cost_usd']:.6f}

### Step Functions Costs
- Terraform: ${cost_analysis['terraform']['stepfunctions']['total_cost_usd']:.6f}
- CloudFormation: ${cost_analysis['cloudformation']['stepfunctions']['total_cost_usd']:.6f}

### DynamoDB Costs
- Terraform: ${cost_analysis['terraform']['dynamodb']['total_cost_usd']:.6f}
- CloudFormation: ${cost_analysis['cloudformation']['dynamodb']['total_cost_usd']:.6f}

### S3 Costs
- Terraform: ${cost_analysis['terraform']['s3']['total_cost_usd']:.6f}
- CloudFormation: ${cost_analysis['cloudformation']['s3']['total_cost_usd']:.6f}

## Recommendations

1. **Cost Optimization**: Consider the cost differences when choosing deployment methods
2. **Scale Considerations**: Cost differences may become more significant at scale
3. **Operational Costs**: Factor in operational overhead and maintenance costs
4. **Monitoring**: Implement cost monitoring and alerting for both deployments

## Notes

- Costs are estimated based on AWS pricing as of 2024
- Actual costs may vary based on usage patterns and AWS pricing changes
- This analysis is based on load test results and may not reflect production usage
"""
    
    with open(output_file, 'w') as f:
        f.write(report)

def main():
    parser = argparse.ArgumentParser(description='Analyze costs for DS252 serverless workflows')
    parser.add_argument('--terraform-results', required=True, help='Terraform results file')
    parser.add_argument('--cloudformation-results', required=True, help='CloudFormation results file')
    parser.add_argument('--output', default='cost-comparison.json', help='Output JSON file')
    parser.add_argument('--report', default='cost-analysis-report.md', help='Output report file')
    
    args = parser.parse_args()
    
    # Load results
    with open(args.terraform_results, 'r') as f:
        terraform_results = json.load(f)
    
    with open(args.cloudformation_results, 'r') as f:
        cloudformation_results = json.load(f)
    
    # Analyze costs
    cost_analysis = analyze_costs(terraform_results, cloudformation_results)
    
    # Save JSON results
    with open(args.output, 'w') as f:
        json.dump(cost_analysis, f, indent=2)
    
    # Generate report
    generate_cost_report(cost_analysis, args.report)
    
    # Print summary
    print("Cost Analysis Complete!")
    print(f"JSON Results: {args.output}")
    print(f"Report: {args.report}")
    print(f"\nCost Summary:")
    print(f"Terraform Total: ${cost_analysis['terraform']['total_cost_usd']:.6f}")
    print(f"CloudFormation Total: ${cost_analysis['cloudformation']['total_cost_usd']:.6f}")
    print(f"Difference: ${cost_analysis['comparison']['difference_usd']:.6f}")
    print(f"More Cost-Effective: {cost_analysis['comparison']['cheaper_deployment'].title()}")

if __name__ == '__main__':
    main()
