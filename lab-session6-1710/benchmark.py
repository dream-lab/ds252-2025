#!/usr/bin/env python3
"""
DS252 Lab Session 6 - Hybrid Architecture Benchmarking Script

Measures:
1. End-to-end (E2E) Lambda response time
2. Lambda to EC2 and back call latency
3. Generates visualizations and statistics

Runs at 1 RPS (1 request per second) for 5 minutes = 300 requests
"""

import json
import time
import sys
import os
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Configuration
RPS = 1  # Requests per second
DURATION = 300  # 5 minutes in seconds
TOTAL_REQUESTS = RPS * DURATION  # 300 requests
IMAGE_URL = "https://www.w3schools.com/css/img_5terre.jpg"

# Data tracking
results = {
    "e2e_latencies": [],  # End-to-end Lambda response times
    "lambda_ec2_latencies": [],  # Lambda to EC2 call latency
    "timestamps": [],
    "status_codes": [],
    "errors": []
}


def get_lambda_name():
    """Get Lambda function name from Terraform outputs"""
    try:
        with open("terraform.tfstate", "r") as f:
            state = json.load(f)
            for output_key, output_value in state.get("outputs", {}).items():
                if "lambda_function_name" in output_key:
                    return output_value["value"]
    except Exception as e:
        print(f"Error reading terraform.tfstate: {e}")
    
    print("Error: Could not find Lambda function name")
    print("Make sure you've run 'terraform apply' first")
    sys.exit(1)


def invoke_lambda(lambda_client, function_name, image_url):
    """
    Invoke Lambda function and extract timing information
    
    Returns:
    - e2e_latency: Total time Lambda took to respond (ms)
    - lambda_ec2_latency: Time Lambda spent calling EC2 (ms)
    - status_code: HTTP status code from response
    """
    payload = {
        "image_url": image_url
    }
    
    start_time = time.time() * 1000  # Convert to milliseconds
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        end_time = time.time() * 1000
        e2e_latency = end_time - start_time
        
        # Parse Lambda response
        response_payload = json.loads(response['Payload'].read())
        
        # Extract Lambda-to-EC2 latency from response body
        lambda_ec2_latency = None
        status_code = response_payload.get('statusCode', 500)
        
        # Try to extract lambda_ec2_call_time from the response body
        if 'body' in response_payload and isinstance(response_payload['body'], str):
            try:
                body = json.loads(response_payload['body'])
                lambda_ec2_latency = body.get('lambda_ec2_call_time_ms')
            except:
                pass
        
        return e2e_latency, lambda_ec2_latency, status_code, None
        
    except ClientError as e:
        error_msg = str(e)
        return None, None, 500, error_msg
    except Exception as e:
        error_msg = str(e)
        return None, None, 500, error_msg


def run_benchmark(lambda_name):
    """Run benchmark test at 1 RPS for 5 minutes"""
    print(f"\n{'='*70}")
    print("DS252 Lab Session 6 - Hybrid Architecture Benchmarking")
    print(f"{'='*70}")
    print(f"Lambda Function: {lambda_name}")
    print(f"Image URL: {IMAGE_URL}")
    print(f"Target RPS: {RPS} requests/second")
    print(f"Duration: {DURATION} seconds (5 minutes)")
    print(f"Total Requests: {TOTAL_REQUESTS}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    # Initialize Lambda client
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Benchmark loop
    request_count = 0
    start_time = time.time()
    
    for i in range(TOTAL_REQUESTS):
        loop_start = time.time()
        
        # Invoke Lambda
        e2e_latency, lambda_ec2_latency, status_code, error = invoke_lambda(
            lambda_client, lambda_name, IMAGE_URL
        )
        
        request_count += 1
        
        # Record results
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        results["timestamps"].append(timestamp)
        results["status_codes"].append(status_code)
        
        if e2e_latency:
            results["e2e_latencies"].append(e2e_latency)
        
        if lambda_ec2_latency:
            results["lambda_ec2_latencies"].append(lambda_ec2_latency)
        
        if error:
            results["errors"].append(error)
        
        # Print progress
        if (request_count) % 10 == 0:
            avg_e2e = np.mean(results["e2e_latencies"]) if results["e2e_latencies"] else 0
            print(f"[{request_count:3d}/{TOTAL_REQUESTS}] "
                  f"E2E Latency: {e2e_latency:6.1f}ms | "
                  f"Avg E2E: {avg_e2e:6.1f}ms | "
                  f"Status: {status_code} | "
                  f"{'✓' if status_code == 200 else '✗'}")
        
        # Rate limiting: maintain 1 RPS
        loop_elapsed = time.time() - loop_start
        sleep_time = (1.0 / RPS) - loop_elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    total_time = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"Benchmark Complete!")
    print(f"Total Time: {total_time:.1f} seconds")
    print(f"Requests Completed: {request_count}")
    print(f"Errors: {len(results['errors'])}")
    print(f"{'='*70}\n")
    
    return results


def calculate_statistics(results):
    """Calculate and print statistics"""
    e2e_latencies = results["e2e_latencies"]
    lambda_ec2_latencies = results["lambda_ec2_latencies"]
    
    print(f"\n{'='*70}")
    print("BENCHMARK STATISTICS")
    print(f"{'='*70}\n")
    
    # E2E Latency Statistics
    if e2e_latencies:
        print("End-to-End (E2E) Lambda Response Latency:")
        print(f"  Min:     {np.min(e2e_latencies):7.2f} ms")
        print(f"  Max:     {np.max(e2e_latencies):7.2f} ms")
        print(f"  Mean:    {np.mean(e2e_latencies):7.2f} ms")
        print(f"  Median:  {np.median(e2e_latencies):7.2f} ms")
        print(f"  Std Dev: {np.std(e2e_latencies):7.2f} ms")
        print(f"  P95:     {np.percentile(e2e_latencies, 95):7.2f} ms")
        print(f"  P99:     {np.percentile(e2e_latencies, 99):7.2f} ms")
        print(f"  Count:   {len(e2e_latencies)}")
    
    print()
    
    # Lambda-EC2 Latency Statistics
    if lambda_ec2_latencies:
        print("Lambda to EC2 and Back Call Latency:")
        print(f"  Min:     {np.min(lambda_ec2_latencies):7.2f} ms")
        print(f"  Max:     {np.max(lambda_ec2_latencies):7.2f} ms")
        print(f"  Mean:    {np.mean(lambda_ec2_latencies):7.2f} ms")
        print(f"  Median:  {np.median(lambda_ec2_latencies):7.2f} ms")
        print(f"  Std Dev: {np.std(lambda_ec2_latencies):7.2f} ms")
        print(f"  P95:     {np.percentile(lambda_ec2_latencies, 95):7.2f} ms")
        print(f"  P99:     {np.percentile(lambda_ec2_latencies, 99):7.2f} ms")
        print(f"  Count:   {len(lambda_ec2_latencies)}")
    
    print()
    
    # Status Code Distribution
    status_counts = {}
    for status in results["status_codes"]:
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("Status Code Distribution:")
    for status, count in sorted(status_counts.items()):
        percentage = (count / len(results["status_codes"])) * 100
        print(f"  {status}: {count:3d} ({percentage:5.1f}%)")
    
    if results["errors"]:
        print(f"\nErrors: {len(results['errors'])}")
        for error in results["errors"][:5]:  # Show first 5 errors
            print(f"  - {error}")
    
    print(f"{'='*70}\n")
    
    return {
        "e2e_median": np.median(e2e_latencies) if e2e_latencies else 0,
        "e2e_mean": np.mean(e2e_latencies) if e2e_latencies else 0,
        "lambda_ec2_median": np.median(lambda_ec2_latencies) if lambda_ec2_latencies else 0,
        "lambda_ec2_mean": np.mean(lambda_ec2_latencies) if lambda_ec2_latencies else 0,
    }


def plot_results(results, stats):
    """Generate visualization plots"""
    print("Generating plots...")
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle('DS252 Lab Session 6 - Hybrid Architecture Benchmarking Results', 
                 fontsize=16, fontweight='bold')
    
    # Plot 1: Timeline of E2E Latencies
    ax1 = axes[0]
    if results["e2e_latencies"]:
        x = range(len(results["e2e_latencies"]))
        ax1.plot(x, results["e2e_latencies"], 'b-', linewidth=1, alpha=0.7, label='E2E Latency')
        ax1.axhline(y=stats["e2e_median"], color='r', linestyle='--', 
                    linewidth=2, label=f'Median: {stats["e2e_median"]:.1f}ms')
        ax1.axhline(y=stats["e2e_mean"], color='g', linestyle='--', 
                    linewidth=2, label=f'Mean: {stats["e2e_mean"]:.1f}ms')
        ax1.set_xlabel('Request Number', fontsize=11)
        ax1.set_ylabel('Latency (ms)', fontsize=11)
        ax1.set_title('Timeline of End-to-End Lambda Response Latency', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper right')
    
    # Plot 2: Bar plot comparing medians
    ax2 = axes[1]
    latency_types = ['E2E Lambda\nResponse', 'Lambda to EC2\nRound Trip']
    median_values = [
        stats["e2e_median"],
        stats["lambda_ec2_median"]
    ]
    colors = ['#3498db', '#e74c3c']
    bars = ax2.bar(latency_types, median_values, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
    
    # Add value labels on bars
    for bar, value in zip(bars, median_values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.1f}ms',
                ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    ax2.set_ylabel('Median Latency (ms)', fontsize=11)
    ax2.set_title('Median Latency Comparison', fontsize=12, fontweight='bold')
    ax2.set_ylim(0, max(median_values) * 1.2)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add statistics text
    stats_text = (
        f"Total Requests: {len(results['e2e_latencies'])}\n"
        f"Success Rate: {(sum(1 for s in results['status_codes'] if s == 200) / len(results['status_codes']) * 100):.1f}%\n"
        f"Errors: {len(results['errors'])}"
    )
    ax2.text(0.98, 0.97, stats_text, transform=ax2.transAxes, 
            fontsize=10, verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    # Save plot
    output_file = 'benchmark_results.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Plot saved: {output_file}")
    
    # Save raw data
    data_file = 'benchmark_results.json'
    with open(data_file, 'w') as f:
        json.dump({
            "e2e_latencies": results["e2e_latencies"],
            "lambda_ec2_latencies": results["lambda_ec2_latencies"],
            "status_codes": results["status_codes"],
            "statistics": stats
        }, f, indent=2)
    print(f"✓ Data saved: {data_file}")
    
    plt.show()
    print(f"✓ Plots generated successfully!\n")


def main():
    """Main entry point"""
    # Check if in correct directory
    if not os.path.exists('terraform.tfstate'):
        print("Error: terraform.tfstate not found!")
        print("Make sure you're in the lab-session6-1710 directory")
        print("and have run 'terraform apply' first")
        sys.exit(1)
    
    # Get Lambda function name
    lambda_name = get_lambda_name()
    print(f"Found Lambda Function: {lambda_name}")
    
    # Run benchmark
    results = run_benchmark(lambda_name)
    
    # Calculate and print statistics
    stats = calculate_statistics(results)
    
    # Generate plots
    plot_results(results, stats)
    
    print("✓ Benchmarking complete!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
