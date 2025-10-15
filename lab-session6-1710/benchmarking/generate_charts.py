#!/usr/bin/env python3
"""
Generate charts for DS252 lab results
"""

import json
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
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
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('DS252 Serverless Workflows - Performance Comparison', fontsize=16, fontweight='bold')
    
    # 1. Success Rate Comparison
    ax1 = axes[0, 0]
    success_rate_pivot = df.pivot(index='workflow', columns='target', values='success_rate')
    success_rate_pivot.plot(kind='bar', ax=ax1, color=['#2E8B57', '#4682B4'])
    ax1.set_title('Success Rate Comparison', fontweight='bold')
    ax1.set_ylabel('Success Rate')
    ax1.set_xlabel('Workflow')
    ax1.legend(title='Deployment Method', title_fontsize=10)
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)
    
    # 2. Average Duration Comparison
    ax2 = axes[0, 1]
    avg_duration_pivot = df.pivot(index='workflow', columns='target', values='avg_duration_ms')
    avg_duration_pivot.plot(kind='bar', ax=ax2, color=['#2E8B57', '#4682B4'])
    ax2.set_title('Average Duration Comparison', fontweight='bold')
    ax2.set_ylabel('Average Duration (ms)')
    ax2.set_xlabel('Workflow')
    ax2.legend(title='Deployment Method', title_fontsize=10)
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3)
    
    # 3. P95 Duration Comparison
    ax3 = axes[1, 0]
    p95_duration_pivot = df.pivot(index='workflow', columns='target', values='p95_duration_ms')
    p95_duration_pivot.plot(kind='bar', ax=ax3, color=['#2E8B57', '#4682B4'])
    ax3.set_title('P95 Duration Comparison', fontweight='bold')
    ax3.set_ylabel('P95 Duration (ms)')
    ax3.set_xlabel('Workflow')
    ax3.legend(title='Deployment Method', title_fontsize=10)
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(True, alpha=0.3)
    
    # 4. Throughput Comparison
    ax4 = axes[1, 1]
    throughput_pivot = df.pivot(index='workflow', columns='target', values='successful_requests')
    throughput_pivot.plot(kind='bar', ax=ax4, color=['#2E8B57', '#4682B4'])
    ax4.set_title('Throughput Comparison', fontweight='bold')
    ax4.set_ylabel('Successful Requests')
    ax4.set_xlabel('Workflow')
    ax4.legend(title='Deployment Method', title_fontsize=10)
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/performance_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Generate individual charts
    generate_individual_charts(df, output_dir)

def generate_individual_charts(df, output_dir):
    """Generate individual charts for each metric"""
    
    # Success Rate Chart
    plt.figure(figsize=(10, 6))
    success_rate_pivot = df.pivot(index='workflow', columns='target', values='success_rate')
    success_rate_pivot.plot(kind='bar', color=['#2E8B57', '#4682B4'])
    plt.title('Success Rate Comparison: Terraform vs CloudFormation', fontweight='bold', fontsize=14)
    plt.ylabel('Success Rate', fontsize=12)
    plt.xlabel('Workflow', fontsize=12)
    plt.legend(title='Deployment Method', title_fontsize=11)
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/success_rate_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Average Duration Chart
    plt.figure(figsize=(10, 6))
    avg_duration_pivot = df.pivot(index='workflow', columns='target', values='avg_duration_ms')
    avg_duration_pivot.plot(kind='bar', color=['#2E8B57', '#4682B4'])
    plt.title('Average Duration Comparison: Terraform vs CloudFormation', fontweight='bold', fontsize=14)
    plt.ylabel('Average Duration (ms)', fontsize=12)
    plt.xlabel('Workflow', fontsize=12)
    plt.legend(title='Deployment Method', title_fontsize=11)
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/avg_duration_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # P95 Duration Chart
    plt.figure(figsize=(10, 6))
    p95_duration_pivot = df.pivot(index='workflow', columns='target', values='p95_duration_ms')
    p95_duration_pivot.plot(kind='bar', color=['#2E8B57', '#4682B4'])
    plt.title('P95 Duration Comparison: Terraform vs CloudFormation', fontweight='bold', fontsize=14)
    plt.ylabel('P95 Duration (ms)', fontsize=12)
    plt.xlabel('Workflow', fontsize=12)
    plt.legend(title='Deployment Method', title_fontsize=11)
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/p95_duration_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Throughput Chart
    plt.figure(figsize=(10, 6))
    throughput_pivot = df.pivot(index='workflow', columns='target', values='successful_requests')
    throughput_pivot.plot(kind='bar', color=['#2E8B57', '#4682B4'])
    plt.title('Throughput Comparison: Terraform vs CloudFormation', fontweight='bold', fontsize=14)
    plt.ylabel('Successful Requests', fontsize=12)
    plt.xlabel('Workflow', fontsize=12)
    plt.legend(title='Deployment Method', title_fontsize=11)
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/throughput_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Duration Distribution Chart
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
                # Create a bar chart with key metrics
                metrics = ['avg_duration_ms', 'median_duration_ms', 'p95_duration_ms']
                values = [subset[metric].iloc[0] for metric in metrics]
                colors = ['#2E8B57', '#4682B4', '#DC143C']
                
                bars = plt.bar(metrics, values, color=colors, alpha=0.7)
                plt.title(f'{workflow} - {target}', fontweight='bold')
                plt.ylabel('Duration (ms)')
                plt.xticks(rotation=45)
                
                # Add value labels on bars
                for bar, value in zip(bars, values):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                            f'{value:.1f}', ha='center', va='bottom', fontsize=9)
    
    plt.suptitle('Duration Distribution by Workflow and Deployment Method', fontweight='bold', fontsize=16)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/duration_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

def generate_cost_charts(cost_data, output_dir):
    """Generate cost comparison charts"""
    
    # Cost breakdown chart
    plt.figure(figsize=(12, 8))
    
    # Prepare data
    services = ['Lambda', 'Step Functions', 'DynamoDB', 'S3']
    terraform_costs = [
        cost_data['terraform']['lambda']['total_cost_usd'],
        cost_data['terraform']['stepfunctions']['total_cost_usd'],
        cost_data['terraform']['dynamodb']['total_cost_usd'],
        cost_data['terraform']['s3']['total_cost_usd']
    ]
    cloudformation_costs = [
        cost_data['cloudformation']['lambda']['total_cost_usd'],
        cost_data['cloudformation']['stepfunctions']['total_cost_usd'],
        cost_data['cloudformation']['dynamodb']['total_cost_usd'],
        cost_data['cloudformation']['s3']['total_cost_usd']
    ]
    
    x = np.arange(len(services))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(12, 8))
    bars1 = ax.bar(x - width/2, terraform_costs, width, label='Terraform', color='#2E8B57', alpha=0.8)
    bars2 = ax.bar(x + width/2, cloudformation_costs, width, label='CloudFormation', color='#4682B4', alpha=0.8)
    
    ax.set_xlabel('AWS Services', fontsize=12)
    ax.set_ylabel('Cost (USD)', fontsize=12)
    ax.set_title('Cost Breakdown Comparison: Terraform vs CloudFormation', fontweight='bold', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(services)
    ax.legend(title='Deployment Method', title_fontsize=11)
    ax.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.000001,
                   f'${height:.6f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/cost_breakdown_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Total cost comparison
    plt.figure(figsize=(8, 6))
    
    total_costs = [cost_data['terraform']['total_cost_usd'], cost_data['cloudformation']['total_cost_usd']]
    deployment_methods = ['Terraform', 'CloudFormation']
    colors = ['#2E8B57', '#4682B4']
    
    bars = plt.bar(deployment_methods, total_costs, color=colors, alpha=0.8)
    plt.title('Total Cost Comparison: Terraform vs CloudFormation', fontweight='bold', fontsize=14)
    plt.ylabel('Total Cost (USD)', fontsize=12)
    plt.xlabel('Deployment Method', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, cost in zip(bars, total_costs):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.000001,
                f'${cost:.6f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/total_cost_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Generate charts for DS252 lab results')
    parser.add_argument('--input-dir', default='.', help='Input directory containing result files')
    parser.add_argument('--output-dir', default='charts', help='Output directory for charts')
    parser.add_argument('--cost-analysis', help='Cost analysis JSON file')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Find result files
    result_files = []
    for file in os.listdir(args.input_dir):
        if file.endswith('results.json'):
            result_files.append(os.path.join(args.input_dir, file))
    
    if not result_files:
        print("No result files found!")
        return
    
    # Load results
    results = load_results(*result_files)
    
    # Create comparison DataFrame
    df = create_comparison_dataframe(results)
    
    # Generate performance charts
    generate_performance_charts(df, args.output_dir)
    
    # Generate cost charts if cost analysis file is provided
    if args.cost_analysis and os.path.exists(args.cost_analysis):
        with open(args.cost_analysis, 'r') as f:
            cost_data = json.load(f)
        generate_cost_charts(cost_data, args.output_dir)
    
    print("Charts generated successfully!")
    print(f"Output directory: {args.output_dir}")
    print("\nGenerated charts:")
    print("- performance_comparison.png")
    print("- success_rate_comparison.png")
    print("- avg_duration_comparison.png")
    print("- p95_duration_comparison.png")
    print("- throughput_comparison.png")
    print("- duration_distribution.png")
    
    if args.cost_analysis:
        print("- cost_breakdown_comparison.png")
        print("- total_cost_comparison.png")

if __name__ == '__main__':
    main()
