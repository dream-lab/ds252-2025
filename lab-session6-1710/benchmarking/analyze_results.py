#!/usr/bin/env python3
"""
Analysis script for DS252 load test results
"""

import json
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

def load_results(*result_files):
    """Load results from multiple JSON files"""
    all_results = []
    
    for file_path in result_files:
        with open(file_path, 'r') as f:
            data = json.load(f)
            all_results.append(data)
    
    return all_results

def create_comparison_dataframe(results_list):
    """Create a pandas DataFrame for comparison analysis"""
    comparison_data = []
    
    for result in results_list:
        test_config = result['test_config']
        analysis = result['analysis']
        
        comparison_data.append({
            'workflow': test_config['workflow'],
            'target': test_config['target'],
            'rps': test_config['rps'],
            'duration': test_config['duration'],
            'total_requests': analysis['total_requests'],
            'successful_requests': analysis['successful_requests'],
            'failed_requests': analysis['failed_requests'],
            'success_rate': analysis['success_rate'],
            'avg_duration_ms': analysis.get('avg_duration_ms', 0),
            'median_duration_ms': analysis.get('median_duration_ms', 0),
            'p95_duration_ms': analysis.get('p95_duration_ms', 0),
            'p99_duration_ms': analysis.get('p99_duration_ms', 0),
            'min_duration_ms': analysis.get('min_duration_ms', 0),
            'max_duration_ms': analysis.get('max_duration_ms', 0)
        })
    
    return pd.DataFrame(comparison_data)

def generate_performance_charts(df, output_dir):
    """Generate performance comparison charts"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Set style
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    
    # 1. Success Rate Comparison
    plt.figure(figsize=(12, 6))
    success_rate_pivot = df.pivot(index='workflow', columns='target', values='success_rate')
    success_rate_pivot.plot(kind='bar', ax=plt.gca())
    plt.title('Success Rate Comparison: Terraform vs CloudFormation')
    plt.ylabel('Success Rate')
    plt.xlabel('Workflow')
    plt.legend(title='Deployment Method')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/success_rate_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Average Duration Comparison
    plt.figure(figsize=(12, 6))
    avg_duration_pivot = df.pivot(index='workflow', columns='target', values='avg_duration_ms')
    avg_duration_pivot.plot(kind='bar', ax=plt.gca())
    plt.title('Average Duration Comparison: Terraform vs CloudFormation')
    plt.ylabel('Average Duration (ms)')
    plt.xlabel('Workflow')
    plt.legend(title='Deployment Method')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/avg_duration_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. P95 Duration Comparison
    plt.figure(figsize=(12, 6))
    p95_duration_pivot = df.pivot(index='workflow', columns='target', values='p95_duration_ms')
    p95_duration_pivot.plot(kind='bar', ax=plt.gca())
    plt.title('P95 Duration Comparison: Terraform vs CloudFormation')
    plt.ylabel('P95 Duration (ms)')
    plt.xlabel('Workflow')
    plt.legend(title='Deployment Method')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/p95_duration_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. Throughput Comparison
    plt.figure(figsize=(12, 6))
    throughput_pivot = df.pivot(index='workflow', columns='target', values='successful_requests')
    throughput_pivot.plot(kind='bar', ax=plt.gca())
    plt.title('Throughput Comparison: Terraform vs CloudFormation')
    plt.ylabel('Successful Requests')
    plt.xlabel('Workflow')
    plt.legend(title='Deployment Method')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/throughput_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 5. Duration Distribution (if we have individual request data)
    plt.figure(figsize=(15, 10))
    
    # Create subplots for each workflow and target combination
    workflows = df['workflow'].unique()
    targets = df['target'].unique()
    
    for i, workflow in enumerate(workflows):
        for j, target in enumerate(targets):
            plt.subplot(len(workflows), len(targets), i * len(targets) + j + 1)
            
            # Filter data for this combination
            subset = df[(df['workflow'] == workflow) & (df['target'] == target)]
            
            if not subset.empty:
                # Create a simple bar chart with key metrics
                metrics = ['avg_duration_ms', 'median_duration_ms', 'p95_duration_ms']
                values = [subset[metric].iloc[0] for metric in metrics]
                
                plt.bar(metrics, values)
                plt.title(f'{workflow} - {target}')
                plt.ylabel('Duration (ms)')
                plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/duration_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

def generate_html_report(df, output_file):
    """Generate HTML report"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>DS252 Load Test Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .metric {{ font-weight: bold; }}
            .terraform {{ background-color: #e8f5e8; }}
            .cloudformation {{ background-color: #e8f0ff; }}
        </style>
    </head>
    <body>
        <h1>DS252 Serverless Workflows - Load Test Analysis Report</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>Executive Summary</h2>
        <p>This report compares the performance of serverless workflows deployed using Terraform and CloudFormation.</p>
        
        <h2>Performance Metrics</h2>
        <table>
            <tr>
                <th>Workflow</th>
                <th>Deployment Method</th>
                <th>Total Requests</th>
                <th>Success Rate</th>
                <th>Avg Duration (ms)</th>
                <th>Median Duration (ms)</th>
                <th>P95 Duration (ms)</th>
                <th>P99 Duration (ms)</th>
            </tr>
    """
    
    for _, row in df.iterrows():
        css_class = 'terraform' if row['target'] == 'terraform' else 'cloudformation'
        html_content += f"""
            <tr class="{css_class}">
                <td>{row['workflow']}</td>
                <td>{row['target']}</td>
                <td>{row['total_requests']}</td>
                <td>{row['success_rate']:.2%}</td>
                <td>{row['avg_duration_ms']:.2f}</td>
                <td>{row['median_duration_ms']:.2f}</td>
                <td>{row['p95_duration_ms']:.2f}</td>
                <td>{row['p99_duration_ms']:.2f}</td>
            </tr>
        """
    
    html_content += """
        </table>
        
        <h2>Key Findings</h2>
        <ul>
            <li><strong>Success Rate:</strong> Both deployment methods show similar success rates</li>
            <li><strong>Performance:</strong> Duration metrics help identify performance differences</li>
            <li><strong>Reliability:</strong> P95 and P99 metrics show tail latency characteristics</li>
        </ul>
        
        <h2>Charts</h2>
        <p>Performance comparison charts are saved in the charts/ directory:</p>
        <ul>
            <li>success_rate_comparison.png</li>
            <li>avg_duration_comparison.png</li>
            <li>p95_duration_comparison.png</li>
            <li>throughput_comparison.png</li>
            <li>duration_distribution.png</li>
        </ul>
        
        <h2>Recommendations</h2>
        <ul>
            <li>Monitor cold start performance differences</li>
            <li>Consider cost implications of different deployment methods</li>
            <li>Evaluate operational complexity and maintenance overhead</li>
        </ul>
    </body>
    </html>
    """
    
    with open(output_file, 'w') as f:
        f.write(html_content)

def main():
    parser = argparse.ArgumentParser(description='Analyze DS252 load test results')
    parser.add_argument('--terraform-lambda', required=True, help='Terraform Lambda results file')
    parser.add_argument('--terraform-stepfunctions', required=True, help='Terraform Step Functions results file')
    parser.add_argument('--cloudformation-lambda', required=True, help='CloudFormation Lambda results file')
    parser.add_argument('--cloudformation-stepfunctions', required=True, help='CloudFormation Step Functions results file')
    parser.add_argument('--output', default='analysis-report.html', help='Output HTML report file')
    parser.add_argument('--charts-dir', default='charts', help='Directory for charts')
    
    args = parser.parse_args()
    
    # Load all results
    results = load_results(
        args.terraform_lambda,
        args.terraform_stepfunctions,
        args.cloudformation_lambda,
        args.cloudformation_stepfunctions
    )
    
    # Create comparison DataFrame
    df = create_comparison_dataframe(results)
    
    # Generate charts
    generate_performance_charts(df, args.charts_dir)
    
    # Generate HTML report
    generate_html_report(df, args.output)
    
    # Print summary
    print("Analysis Complete!")
    print(f"HTML Report: {args.output}")
    print(f"Charts Directory: {args.charts_dir}")
    print("\nSummary Statistics:")
    print(df.to_string(index=False))

if __name__ == '__main__':
    main()
