#!/usr/bin/env python3
"""
Generate comprehensive report for DS252 lab results
"""

import json
import argparse
from datetime import datetime
import os

def load_all_results(terraform_lambda, terraform_stepfunctions, cloudformation_lambda, cloudformation_stepfunctions, cost_analysis):
    """Load all result files"""
    results = {}
    
    with open(terraform_lambda, 'r') as f:
        results['terraform_lambda'] = json.load(f)
    
    with open(terraform_stepfunctions, 'r') as f:
        results['terraform_stepfunctions'] = json.load(f)
    
    with open(cloudformation_lambda, 'r') as f:
        results['cloudformation_lambda'] = json.load(f)
    
    with open(cloudformation_stepfunctions, 'r') as f:
        results['cloudformation_stepfunctions'] = json.load(f)
    
    with open(cost_analysis, 'r') as f:
        results['cost_analysis'] = json.load(f)
    
    return results

def generate_comprehensive_report(results, output_file):
    """Generate comprehensive lab report"""
    
    # Extract key metrics
    tf_lambda_analysis = results['terraform_lambda']['analysis']
    tf_sf_analysis = results['terraform_stepfunctions']['analysis']
    cf_lambda_analysis = results['cloudformation_lambda']['analysis']
    cf_sf_analysis = results['cloudformation_stepfunctions']['analysis']
    cost_data = results['cost_analysis']
    
    report = f"""# DS252 Lab Session 6 - Final Report
## Serverless Workflows: Terraform vs CloudFormation Comparison

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Lab Session:** DS252 - Infrastructure as Code Comparison

---

## Executive Summary

This lab compared the deployment and performance of identical serverless workflows using two different Infrastructure-as-Code (IaC) tools: **Terraform** and **AWS CloudFormation**. The workflows included Lambda-based image ingestion and Step Functions-based image classification pipelines.

### Key Findings

1. **Performance**: Both deployment methods showed similar performance characteristics
2. **Cost**: Minimal cost differences between deployment methods
3. **Operational Complexity**: Different trade-offs in deployment and management
4. **Scalability**: Both methods support similar scaling patterns

---

## Workflow Architecture

### Workflow 1: Lambda Image Ingestion
- **Purpose**: Download images from URLs and store in S3 with metadata in DynamoDB
- **Components**: Lambda function, S3 bucket, DynamoDB table
- **Process**: URL → Download → S3 Upload → DynamoDB Metadata

### Workflow 2: Step Functions Classification Pipeline
- **Purpose**: Process images through ML inference pipeline
- **Components**: Step Functions, multiple Lambda functions, S3, DynamoDB
- **Process**: Fetch Image → Preprocessing → Parallel ML Inference → Aggregation

---

## Performance Analysis

### Lambda Image Ingestion Performance

#### Terraform Deployment
- **Total Requests**: {tf_lambda_analysis['total_requests']}
- **Success Rate**: {tf_lambda_analysis['success_rate']:.2%}
- **Average Duration**: {tf_lambda_analysis.get('avg_duration_ms', 0):.2f} ms
- **P95 Duration**: {tf_lambda_analysis.get('p95_duration_ms', 0):.2f} ms
- **P99 Duration**: {tf_lambda_analysis.get('p99_duration_ms', 0):.2f} ms

#### CloudFormation Deployment
- **Total Requests**: {cf_lambda_analysis['total_requests']}
- **Success Rate**: {cf_lambda_analysis['success_rate']:.2%}
- **Average Duration**: {cf_lambda_analysis.get('avg_duration_ms', 0):.2f} ms
- **P95 Duration**: {cf_lambda_analysis.get('p95_duration_ms', 0):.2f} ms
- **P99 Duration**: {cf_lambda_analysis.get('p99_duration_ms', 0):.2f} ms

### Step Functions Performance

#### Terraform Deployment
- **Total Requests**: {tf_sf_analysis['total_requests']}
- **Success Rate**: {tf_sf_analysis['success_rate']:.2%}
- **Average Duration**: {tf_sf_analysis.get('avg_duration_ms', 0):.2f} ms
- **P95 Duration**: {tf_sf_analysis.get('p95_duration_ms', 0):.2f} ms
- **P99 Duration**: {tf_sf_analysis.get('p99_duration_ms', 0):.2f} ms

#### CloudFormation Deployment
- **Total Requests**: {cf_sf_analysis['total_requests']}
- **Success Rate**: {cf_sf_analysis['success_rate']:.2%}
- **Average Duration**: {cf_sf_analysis.get('avg_duration_ms', 0):.2f} ms
- **P95 Duration**: {cf_sf_analysis.get('p95_duration_ms', 0):.2f} ms
- **P99 Duration**: {cf_sf_analysis.get('p99_duration_ms', 0):.2f} ms

---

## Cost Analysis

### Total Costs (Estimated)

#### Terraform Deployment
- **Lambda Costs**: ${cost_data['terraform']['lambda']['total_cost_usd']:.6f}
- **Step Functions Costs**: ${cost_data['terraform']['stepfunctions']['total_cost_usd']:.6f}
- **DynamoDB Costs**: ${cost_data['terraform']['dynamodb']['total_cost_usd']:.6f}
- **S3 Costs**: ${cost_data['terraform']['s3']['total_cost_usd']:.6f}
- **Total**: ${cost_data['terraform']['total_cost_usd']:.6f}

#### CloudFormation Deployment
- **Lambda Costs**: ${cost_data['cloudformation']['lambda']['total_cost_usd']:.6f}
- **Step Functions Costs**: ${cost_data['cloudformation']['stepfunctions']['total_cost_usd']:.6f}
- **DynamoDB Costs**: ${cost_data['cloudformation']['dynamodb']['total_cost_usd']:.6f}
- **S3 Costs**: ${cost_data['cloudformation']['s3']['total_cost_usd']:.6f}
- **Total**: ${cost_data['cloudformation']['total_cost_usd']:.6f}

### Cost Comparison
- **Cost Difference**: ${cost_data['comparison']['difference_usd']:.6f}
- **Percentage Difference**: {cost_data['comparison']['difference_percent']:.2f}%
- **More Cost-Effective**: {cost_data['comparison']['cheaper_deployment'].title()}

---

## Deployment Comparison

### Terraform Advantages
- **Multi-cloud Support**: Works across different cloud providers
- **State Management**: Built-in state management and locking
- **Modularity**: Excellent support for modules and reusability
- **Community**: Large community and extensive provider ecosystem
- **Plan/Apply**: Clear preview of changes before application

### CloudFormation Advantages
- **AWS Native**: Deep integration with AWS services
- **Stack Management**: Built-in stack management and rollback
- **Change Sets**: Detailed change preview and approval workflow
- **Nested Stacks**: Support for complex nested architectures
- **AWS Support**: Direct AWS support and documentation

### Deployment Process Comparison

#### Terraform Deployment
1. **Initialize**: `terraform init`
2. **Plan**: `terraform plan`
3. **Apply**: `terraform apply`
4. **State Management**: Automatic state tracking
5. **Destroy**: `terraform destroy`

#### CloudFormation Deployment
1. **Validate**: `aws cloudformation validate-template`
2. **Create Stack**: `aws cloudformation create-stack`
3. **Monitor**: `aws cloudformation describe-stacks`
4. **Update**: `aws cloudformation update-stack`
5. **Delete**: `aws cloudformation delete-stack`

---

## Technical Insights

### Performance Characteristics
- **Cold Starts**: Both methods show similar cold start behavior
- **Latency**: Minimal differences in request processing times
- **Throughput**: Comparable throughput under load
- **Reliability**: Both deployments show high success rates

### Operational Considerations
- **Monitoring**: Both support CloudWatch integration
- **Logging**: Identical logging capabilities
- **Scaling**: Same auto-scaling behavior
- **Security**: Equivalent IAM and security configurations

### Development Experience
- **Learning Curve**: Different learning curves for each tool
- **Tooling**: Different ecosystem and tooling support
- **Debugging**: Different approaches to troubleshooting
- **Maintenance**: Different long-term maintenance considerations

---

## Recommendations

### When to Choose Terraform
- Multi-cloud or hybrid cloud strategies
- Complex infrastructure with multiple providers
- Team familiarity with Terraform
- Need for extensive customization and modules
- Preference for declarative configuration

### When to Choose CloudFormation
- AWS-only environments
- Deep AWS service integration requirements
- Team familiarity with AWS-native tools
- Need for AWS-specific features and integrations
- Preference for AWS-managed tooling

### Best Practices
1. **Consistency**: Choose one tool and stick with it for consistency
2. **Training**: Invest in team training for the chosen tool
3. **Governance**: Implement proper governance and review processes
4. **Monitoring**: Set up comprehensive monitoring and alerting
5. **Documentation**: Maintain detailed documentation for both approaches

---

## Conclusion

Both Terraform and CloudFormation are capable of deploying identical serverless workflows with similar performance and cost characteristics. The choice between them should be based on:

1. **Organizational Strategy**: Multi-cloud vs AWS-only
2. **Team Expertise**: Existing skills and preferences
3. **Operational Requirements**: Specific tooling and integration needs
4. **Long-term Vision**: Future infrastructure and scaling plans

The key takeaway is that both tools can effectively manage complex serverless architectures, and the decision should align with your organization's broader infrastructure strategy and team capabilities.

---

## Appendices

### A. Test Configuration
- **Load Test Duration**: 30 seconds
- **Request Rate**: 1 RPS
- **Test Environment**: AWS us-east-1
- **Lambda Memory**: 512 MB
- **Lambda Timeout**: 300 seconds

### B. AWS Services Used
- **Lambda**: Serverless compute
- **Step Functions**: Workflow orchestration
- **S3**: Object storage
- **DynamoDB**: NoSQL database
- **CloudWatch**: Monitoring and logging
- **IAM**: Access management

### C. Files Generated
- Performance comparison charts
- Cost analysis reports
- Load test results
- Infrastructure configurations
- This comprehensive report

---

**Report generated by DS252 Lab Session 6 Analysis Tools**
"""
    
    with open(output_file, 'w') as f:
        f.write(report)

def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive DS252 lab report')
    parser.add_argument('--terraform-results', required=True, help='Terraform results file')
    parser.add_argument('--cloudformation-results', required=True, help='CloudFormation results file')
    parser.add_argument('--cost-analysis', required=True, help='Cost analysis file')
    parser.add_argument('--output', default='final-lab-report.md', help='Output report file')
    
    args = parser.parse_args()
    
    # Load all results
    results = load_all_results(
        args.terraform_results,
        args.terraform_results.replace('lambda', 'stepfunctions'),
        args.cloudformation_results,
        args.cloudformation_results.replace('lambda', 'stepfunctions'),
        args.cost_analysis
    )
    
    # Generate report
    generate_comprehensive_report(results, args.output)
    
    print("Comprehensive Report Generated!")
    print(f"Report: {args.output}")
    print("\nReport includes:")
    print("- Executive Summary")
    print("- Performance Analysis")
    print("- Cost Comparison")
    print("- Deployment Comparison")
    print("- Technical Insights")
    print("- Recommendations")
    print("- Conclusion")

if __name__ == '__main__':
    main()
