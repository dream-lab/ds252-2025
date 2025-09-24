#!/usr/bin/env python3
"""
Simple Python Load Test Client for Serverless Workflows
1 RPS for 30 seconds for both Workflow 1 and Workflow 2
"""

import requests
import json
import time
import threading
import sys
import os
from datetime import datetime
import statistics

class LoadTester:
    def __init__(self):
        self.results = []
        self.lock = threading.Lock()
    
    def test_workflow1(self, api_endpoint, duration=30, rps=1):
        """Test Workflow 1 - Image Ingestion"""
        print(f"\n🚀 Starting Workflow 1 Load Test")
        print(f"   Duration: {duration}s, Rate: {rps} RPS")
        print(f"   Endpoint: {api_endpoint}")
        
        interval = 1.0 / rps
        start_time = time.time()
        request_count = 0
        
        while time.time() - start_time < duration:
            request_start = time.time()
            
            # Prepare request - check if endpoint already has /ingest
            if api_endpoint.endswith('/ingest'):
                url = api_endpoint
            else:
                url = f"{api_endpoint}/ingest"
            payload = {
                "image_url": f"https://picsum.photos/800/600?random={int(time.time() * 1000)}"
            }
            headers = {"Content-Type": "application/json"}
            
            try:
                # Make request
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                request_end = time.time()
                
                # Record result
                result = {
                    "workflow": "1",
                    "request_id": request_count + 1,
                    "timestamp": datetime.now().isoformat(),
                    "status_code": response.status_code,
                    "response_time": round((request_end - request_start) * 1000, 2),  # ms
                    "success": response.status_code == 200,
                    "error": None if response.status_code == 200 else response.text[:100]
                }
                
                with self.lock:
                    self.results.append(result)
                
                # Print progress
                status = "✅" if result["success"] else "❌"
                print(f"   {status} Request {request_count + 1}: {result['response_time']}ms")
                
            except Exception as e:
                request_end = time.time()
                result = {
                    "workflow": "1",
                    "request_id": request_count + 1,
                    "timestamp": datetime.now().isoformat(),
                    "status_code": 0,
                    "response_time": round((request_end - request_start) * 1000, 2),
                    "success": False,
                    "error": str(e)[:100]
                }
                
                with self.lock:
                    self.results.append(result)
                
                print(f"   ❌ Request {request_count + 1}: Error - {str(e)[:50]}")
            
            request_count += 1
            
            # Wait for next request (maintain 1 RPS)
            elapsed = time.time() - request_start
            sleep_time = max(0, interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        print(f"✅ Workflow 1 test completed: {request_count} requests")
    
    def test_workflow2(self, api_endpoint, image_id, duration=30, rps=1):
        """Test Workflow 2 - Classification Pipeline"""
        print(f"\n🚀 Starting Workflow 2 Load Test")
        print(f"   Duration: {duration}s, Rate: {rps} RPS")
        print(f"   Endpoint: {api_endpoint}")
        print(f"   Image ID: {image_id}")
        
        interval = 1.0 / rps
        start_time = time.time()
        request_count = 0
        
        while time.time() - start_time < duration:
            request_start = time.time()
            
            # Prepare request - check if endpoint already has /classify
            if api_endpoint.endswith('/classify'):
                url = api_endpoint
            else:
                url = f"{api_endpoint}/classify"
            payload = {"image_id": image_id}
            headers = {"Content-Type": "application/json"}
            
            try:
                # Make request (longer timeout for Step Functions)
                response = requests.post(url, json=payload, headers=headers, timeout=300)
                request_end = time.time()
                
                # Record result
                result = {
                    "workflow": "2",
                    "request_id": request_count + 1,
                    "timestamp": datetime.now().isoformat(),
                    "status_code": response.status_code,
                    "response_time": round((request_end - request_start) * 1000, 2),  # ms
                    "success": response.status_code == 200,
                    "error": None if response.status_code == 200 else response.text[:100]
                }
                
                with self.lock:
                    self.results.append(result)
                
                # Print progress
                status = "✅" if result["success"] else "❌"
                print(f"   {status} Request {request_count + 1}: {result['response_time']}ms")
                
            except Exception as e:
                request_end = time.time()
                result = {
                    "workflow": "2",
                    "request_id": request_count + 1,
                    "timestamp": datetime.now().isoformat(),
                    "status_code": 0,
                    "response_time": round((request_end - request_start) * 1000, 2),
                    "success": False,
                    "error": str(e)[:100]
                }
                
                with self.lock:
                    self.results.append(result)
                
                print(f"   ❌ Request {request_count + 1}: Error - {str(e)[:50]}")
            
            request_count += 1
            
            # Wait for next request (maintain 1 RPS)
            elapsed = time.time() - request_start
            sleep_time = max(0, interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        print(f"✅ Workflow 2 test completed: {request_count} requests")
    
    def print_summary(self):
        """Print test results summary"""
        if not self.results:
            print("\n❌ No results to summarize")
            return
        
        # Separate results by workflow
        wf1_results = [r for r in self.results if r["workflow"] == "1"]
        wf2_results = [r for r in self.results if r["workflow"] == "2"]
        
        print("\n" + "="*60)
        print("📊 LOAD TEST RESULTS SUMMARY")
        print("="*60)
        
        for workflow, results in [("Workflow 1 (Ingestion)", wf1_results), 
                                 ("Workflow 2 (Classification)", wf2_results)]:
            if not results:
                continue
                
            print(f"\n🔹 {workflow}")
            print("-" * 40)
            
            # Calculate metrics
            total_requests = len(results)
            successful_requests = len([r for r in results if r["success"]])
            failed_requests = total_requests - successful_requests
            success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
            
            response_times = [r["response_time"] for r in results if r["success"]]
            
            print(f"Total Requests:     {total_requests}")
            print(f"Successful:         {successful_requests}")
            print(f"Failed:             {failed_requests}")
            print(f"Success Rate:       {success_rate:.1f}%")
            
            if response_times:
                print(f"Avg Response Time:  {statistics.mean(response_times):.1f}ms")
                print(f"Min Response Time:  {min(response_times):.1f}ms")
                print(f"Max Response Time:  {max(response_times):.1f}ms")
                print(f"Med Response Time:  {statistics.median(response_times):.1f}ms")
            
            # Show errors if any
            errors = [r["error"] for r in results if r["error"]]
            if errors:
                print(f"\nErrors encountered:")
                for error in set(errors):
                    count = errors.count(error)
                    print(f"  - {error} ({count}x)")
        
        print("\n" + "="*60)
    
    def save_results(self, filename="load_test_results.json"):
        """Save detailed results to JSON file"""
        with open(filename, 'w') as f:
            json.dump({
                "test_summary": {
                    "timestamp": datetime.now().isoformat(),
                    "total_requests": len(self.results),
                    "duration": "30s per workflow",
                    "rate": "1 RPS"
                },
                "detailed_results": self.results
            }, f, indent=2)
        print(f"📄 Detailed results saved to: {filename}")

def main():
    """Main function"""
    print("🧪 Serverless Workflow Load Tester")
    print("=" * 50)
    
    # Configuration - Get from environment variables or use defaults
    WORKFLOW1_API = os.getenv('WORKFLOW1_API', 'https://heotjvdzx8.execute-api.ap-south-1.amazonaws.com/prod')
    WORKFLOW2_API = os.getenv('WORKFLOW2_API', 'https://fjkynodbkf.execute-api.ap-south-1.amazonaws.com/prod')
    TEST_IMAGE_ID = os.getenv('IMAGE_ID', '84aedee2-e274-4d6a-ada8-dcd6c7bbf5ff')
    
    print(f"Workflow 1 API: {WORKFLOW1_API}")
    print(f"Workflow 2 API: {WORKFLOW2_API}")
    print(f"Test Image ID:  {TEST_IMAGE_ID}")
    
    # Initialize tester
    tester = LoadTester()
    
    try:
        # Run tests sequentially
        tester.test_workflow1(WORKFLOW1_API)
        time.sleep(2)  # Brief pause between tests
        tester.test_workflow2(WORKFLOW2_API, TEST_IMAGE_ID)
        
        # Print summary
        tester.print_summary()
        
        # Save detailed results
        tester.save_results()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        tester.print_summary()
        tester.save_results()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
