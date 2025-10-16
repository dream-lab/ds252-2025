import json
import boto3
import urllib3
import os
from datetime import datetime

http = urllib3.PoolManager()

def lambda_handler(event, context):
    """
    Lambda function to process image URLs by calling Flask server on EC2
    """
    try:
        # Parse input
        body = event.get('body')
        if isinstance(body, str):
            params = json.loads(body)
        else:
            params = event
        
        image_url = params.get('image_url')
        
        if not image_url:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'image_url is required'})
            }
        
        # Get EC2 Flask server URL from environment
        ec2_flask_url = os.environ.get('EC2_FLASK_URL')
        
        if not ec2_flask_url:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'EC2_FLASK_URL not configured'})
            }
        
        # Prepare payload for Flask server
        payload = {
            'image_url': image_url,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Make synchronous HTTP POST request to Flask server
        try:
            response = http.request(
                'POST',
                f'{ec2_flask_url}/process-image',
                body=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                timeout=urllib3.Timeout(connect=5, read=55)
            )
            
            flask_response = json.loads(response.data.decode('utf-8'))
            
            return {
                'statusCode': response.status,
                'body': json.dumps({
                    'message': 'Image processed successfully',
                    'result': flask_response
                })
            }
            
        except urllib3.exceptions.HTTPError as e:
            return {
                'statusCode': 504,
                'body': json.dumps({
                    'error': 'Failed to connect to EC2 Flask server',
                    'details': str(e)
                })
            }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
