#!/usr/bin/env python3
"""
Load testing script for DS252 serverless workflows
"""

import json
import time
import boto3
import argparse
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

class LoadTester:
    def __init__(self, target='terraform'):
        self.target = target
        self.lambda_client = boto3.client('lambda')
        self.stepfunctions_client = boto3.client('stepfunctions')
        self.results = []
        
        # Set function names based on target
        if target == 'terraform':
            self.image_ingestion_function = 'ds252-image-ingestion'
            self.stepfunctions_arn = None  # Will be set from terraform output
        else:  # cloudformation
            self.image_ingestion_function = 'ds252-image-ingestion-cf'
            self.stepfunctions_arn = None  # Will be set from cloudformation output
    
    def set_stepfunctions_arn(self, arn):
        """Set the Step Functions ARN"""
        self.stepfunctions_arn = arn
    
    def invoke_lambda_ingestion(self, image_url, metadata=None):
        """Invoke the image ingestion Lambda function"""
        start_time = time.time()
        
        payload = {
            'image_url': image_url,
            'metadata': metadata or {}
        }
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.image_ingestion_function,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # Convert to milliseconds
            
            result = json.loads(response['Payload'].read())
            
            return {
                'success': True,
                'duration_ms': duration,
                'response': result,
                'timestamp': datetime.utcnow().isoformat(),
                'function_name': self.image_ingestion_function
            }
            
        except Exception as e:
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            
            return {
                'success': False,
                'duration_ms': duration,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'function_name': self.image_ingestion_function
            }
    
    def invoke_stepfunctions(self, image_id, preprocessing_config=None):
        """Invoke the Step Functions workflow"""
        start_time = time.time()
        
        payload = {
            'image_id': image_id,
            'preprocessing_config': preprocessing_config or {
                'grayscale': True,
                'flip': 'horizontal',
                'rotate': 90,
                'resize': [224, 224]
            }
        }
        
        try:
            response = self.stepfunctions_client.start_execution(
                stateMachineArn=self.stepfunctions_arn,
                input=json.dumps(payload),
                name=f"load-test-{int(time.time())}-{image_id}"
            )
            
            execution_arn = response['executionArn']
            
            # Wait for execution to complete
            while True:
                execution_status = self.stepfunctions_client.describe_execution(
                    executionArn=execution_arn
                )
                
                status = execution_status['status']
                if status in ['SUCCEEDED', 'FAILED', 'TIMED_OUT', 'ABORTED']:
                    break
                
                time.sleep(1)
            
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # Convert to milliseconds
            
            return {
                'success': status == 'SUCCEEDED',
                'duration_ms': duration,
                'status': status,
                'execution_arn': execution_arn,
                'timestamp': datetime.utcnow().isoformat(),
                'state_machine_arn': self.stepfunctions_arn
            }
            
        except Exception as e:
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            
            return {
                'success': False,
                'duration_ms': duration,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'state_machine_arn': self.stepfunctions_arn
            }
    
    def run_load_test(self, workflow, rps, duration, test_data):
        """Run load test for specified workflow"""
        print(f"Starting load test for {workflow} at {rps} RPS for {duration} seconds")
        print(f"Target: {self.target}")
        
        total_requests = rps * duration
        interval = 1.0 / rps
        
        start_time = time.time()
        end_time = start_time + duration
        
        with ThreadPoolExecutor(max_workers=rps * 2) as executor:
            futures = []
            request_count = 0
            
            while time.time() < end_time and request_count < total_requests:
                if workflow == 'lambda-ingestion':
                    image_url = test_data['image_urls'][request_count % len(test_data['image_urls'])]
                    metadata = test_data['metadata'][request_count % len(test_data['metadata'])]
                    future = executor.submit(self.invoke_lambda_ingestion, image_url, metadata)
                elif workflow == 'stepfunctions':
                    image_id = test_data['image_ids'][request_count % len(test_data['image_ids'])]
                    preprocessing_config = test_data['preprocessing_configs'][request_count % len(test_data['preprocessing_configs'])]
                    future = executor.submit(self.invoke_stepfunctions, image_id, preprocessing_config)
                else:
                    raise ValueError(f"Unknown workflow: {workflow}")
                
                futures.append(future)
                request_count += 1
                
                # Wait for next request
                time.sleep(interval)
            
            # Collect results
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    })
            
            self.results = results
            return results
    
    def analyze_results(self):
        """Analyze load test results"""
        if not self.results:
            return {}
        
        successful_requests = [r for r in self.results if r.get('success', False)]
        failed_requests = [r for r in self.results if not r.get('success', False)]
        
        durations = [r['duration_ms'] for r in successful_requests if 'duration_ms' in r]
        
        analysis = {
            'total_requests': len(self.results),
            'successful_requests': len(successful_requests),
            'failed_requests': len(failed_requests),
            'success_rate': len(successful_requests) / len(self.results) if self.results else 0,
            'target': self.target
        }
        
        if durations:
            analysis.update({
                'avg_duration_ms': statistics.mean(durations),
                'min_duration_ms': min(durations),
                'max_duration_ms': max(durations),
                'median_duration_ms': statistics.median(durations),
                'p95_duration_ms': statistics.quantiles(durations, n=20)[18] if len(durations) > 20 else max(durations),
                'p99_duration_ms': statistics.quantiles(durations, n=100)[98] if len(durations) > 100 else max(durations)
            })
        
        if failed_requests:
            error_types = {}
            for req in failed_requests:
                error = req.get('error', 'Unknown error')
                error_types[error] = error_types.get(error, 0) + 1
            analysis['error_breakdown'] = error_types
        
        return analysis

def main():
    parser = argparse.ArgumentParser(description='Load test DS252 serverless workflows')
    parser.add_argument('--workflow', choices=['lambda-ingestion', 'stepfunctions'], required=True,
                       help='Workflow to test')
    parser.add_argument('--target', choices=['terraform', 'cloudformation'], default='terraform',
                       help='Deployment target to test')
    parser.add_argument('--rps', type=int, default=1, help='Requests per second')
    parser.add_argument('--duration', type=int, default=30, help='Test duration in seconds')
    parser.add_argument('--output', default='load_test_results.json', help='Output file for results')
    
    args = parser.parse_args()
    
    # Create test data
    test_data = {
        'image_urls': [
            'https://example.com/image1.jpg',
            'https://example.com/image2.jpg',
            'https://example.com/image3.jpg',
            'https://example.com/image4.jpg',
            'https://example.com/image5.jpg'
        ],
        'metadata': [
            {'source': 'load_test', 'batch': 1},
            {'source': 'load_test', 'batch': 2},
            {'source': 'load_test', 'batch': 3},
            {'source': 'load_test', 'batch': 4},
            {'source': 'load_test', 'batch': 5}
        ],
        'image_ids': [
            'test-image-001',
            'test-image-002',
            'test-image-003',
            'test-image-004',
            'test-image-005'
        ],
        'preprocessing_configs': [
            {'grayscale': True, 'flip': 'horizontal', 'rotate': 90, 'resize': [224, 224]},
            {'grayscale': False, 'flip': 'vertical', 'rotate': 180, 'resize': [224, 224]},
            {'grayscale': True, 'flip': None, 'rotate': 0, 'resize': [224, 224]},
            {'grayscale': False, 'flip': 'horizontal', 'rotate': 270, 'resize': [224, 224]},
            {'grayscale': True, 'flip': 'vertical', 'rotate': 45, 'resize': [224, 224]}
        ]
    }
    
    # Initialize load tester
    load_tester = LoadTester(target=args.target)
    
    # Set Step Functions ARN if needed
    if args.workflow == 'stepfunctions':
        # In real implementation, get this from terraform/cloudformation outputs
        print("Warning: Step Functions ARN not set. Please set it manually.")
        # load_tester.set_stepfunctions_arn("arn:aws:states:us-east-1:123456789012:stateMachine:ds252-classification-pipeline")
    
    # Run load test
    results = load_tester.run_load_test(args.workflow, args.rps, args.duration, test_data)
    
    # Analyze results
    analysis = load_tester.analyze_results()
    
    # Save results
    output_data = {
        'test_config': {
            'workflow': args.workflow,
            'target': args.target,
            'rps': args.rps,
            'duration': args.duration,
            'timestamp': datetime.utcnow().isoformat()
        },
        'results': results,
        'analysis': analysis
    }
    
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    # Print summary
    print(f"\nLoad Test Summary:")
    print(f"Workflow: {args.workflow}")
    print(f"Target: {args.target}")
    print(f"Total Requests: {analysis['total_requests']}")
    print(f"Successful Requests: {analysis['successful_requests']}")
    print(f"Failed Requests: {analysis['failed_requests']}")
    print(f"Success Rate: {analysis['success_rate']:.2%}")
    
    if 'avg_duration_ms' in analysis:
        print(f"Average Duration: {analysis['avg_duration_ms']:.2f} ms")
        print(f"Median Duration: {analysis['median_duration_ms']:.2f} ms")
        print(f"P95 Duration: {analysis['p95_duration_ms']:.2f} ms")
        print(f"P99 Duration: {analysis['p99_duration_ms']:.2f} ms")
    
    print(f"\nResults saved to: {args.output}")

if __name__ == '__main__':
    main()
