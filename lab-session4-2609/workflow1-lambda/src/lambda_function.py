import json
import boto3
import requests
import uuid
from datetime import datetime
from urllib.parse import urlparse
import os

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Environment variables
BUCKET_NAME = os.environ['S3_BUCKET_NAME']
TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']

def lambda_handler(event, context):
    """
    Lambda function for Workflow 1: Image Ingestion
    
    Takes an image URL as input, downloads the image, uploads to S3,
    and stores metadata in DynamoDB.
    
    Expected input:
    {
        "image_url": "https://example.com/image.jpg"
    }
    """
    
    try:
        # Parse input
        if 'body' in event:
            # If called via API Gateway
            body = json.loads(event['body'])
            image_url = body['image_url']
        else:
            # If called directly
            image_url = event['image_url']
        
        print(f"Processing image URL: {image_url}")
        
        # Generate unique image ID
        image_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Extract filename from URL
        parsed_url = urlparse(image_url)
        original_filename = os.path.basename(parsed_url.path)
        if not original_filename or '.' not in original_filename:
            original_filename = f"image_{image_id}.jpg"
        
        # Generate S3 key
        s3_key = f"raw-images/{image_id}_{original_filename}"
        
        # Step 1: Download image from URL
        print(f"Downloading image from: {image_url}")
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        image_data = response.content
        content_type = response.headers.get('content-type', 'image/jpeg')
        image_size = len(image_data)
        
        print(f"Downloaded image: {image_size} bytes, content-type: {content_type}")
        
        # Step 2: Upload image to S3
        print(f"Uploading to S3: s3://{BUCKET_NAME}/{s3_key}")
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=image_data,
            ContentType=content_type,
            Metadata={
                'original-url': image_url,
                'image-id': image_id,
                'upload-timestamp': timestamp
            }
        )
        
        # Generate public URL for the uploaded image
        s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
        
        # Step 3: Store metadata in DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        
        metadata = {
            'image_id': image_id,
            'original_url': image_url,
            's3_bucket': BUCKET_NAME,
            's3_key': s3_key,
            's3_url': s3_url,
            'original_filename': original_filename,
            'content_type': content_type,
            'file_size': image_size,
            'upload_timestamp': timestamp,
            'status': 'uploaded',
            'workflow_stage': 'ingestion_complete',
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        print(f"Storing metadata in DynamoDB table: {TABLE_NAME}")
        table.put_item(Item=metadata)
        
        # Success response
        result = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Image ingestion completed successfully',
                'image_id': image_id,
                's3_url': s3_url,
                'metadata': metadata
            })
        }
        
        print(f"Ingestion completed successfully for image_id: {image_id}")
        return result
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to download image from URL: {str(e)}"
        print(f"ERROR: {error_msg}")
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Download failed',
                'message': error_msg
            })
        }
        
    except Exception as e:
        error_msg = f"Unexpected error during image ingestion: {str(e)}"
        print(f"ERROR: {error_msg}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': error_msg
            })
        }

def get_image_metadata(image_id):
    """
    Helper function to retrieve image metadata from DynamoDB
    """
    try:
        table = dynamodb.Table(TABLE_NAME)
        response = table.get_item(Key={'image_id': image_id})
        
        if 'Item' in response:
            return response['Item']
        else:
            return None
            
    except Exception as e:
        print(f"Error retrieving metadata for image_id {image_id}: {str(e)}")
        return None
