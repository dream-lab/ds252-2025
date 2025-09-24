import json
import boto3
import base64
from PIL import Image
import io
import os

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Environment variables
TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']

def lambda_handler(event, context):
    """
    Fetch Image Lambda - Step 1 of Workflow 2
    
    Reads metadata from DynamoDB and fetches image from S3
    
    Input: {"image_id": "uuid-string"}
    Output: {"image_id": "uuid", "image_data": "base64", "metadata": {...}}
    """
    
    try:
        # Get image_id from input
        image_id = event['image_id']
        print(f"Fetching image for image_id: {image_id}")
        
        # Step 1: Get metadata from DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        response = table.get_item(Key={'image_id': image_id})
        
        if 'Item' not in response:
            raise ValueError(f"Image metadata not found for image_id: {image_id}")
        
        metadata = response['Item']
        s3_bucket = metadata['s3_bucket']
        s3_key = metadata['s3_key']
        
        print(f"Fetching image from S3: s3://{s3_bucket}/{s3_key}")
        
        # Step 2: Fetch image from S3
        s3_response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        image_data = s3_response['Body'].read()
        
        # Convert to base64 for passing through Step Functions
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Verify image can be opened
        image = Image.open(io.BytesIO(image_data))
        width, height = image.size
        mode = image.mode
        
        print(f"Image loaded successfully: {width}x{height}, mode: {mode}")
        
        # Update metadata with processing status
        table.update_item(
            Key={'image_id': image_id},
            UpdateExpression='SET workflow_stage = :stage, updated_at = :timestamp',
            ExpressionAttributeValues={
                ':stage': 'image_fetched',
                ':timestamp': metadata.get('updated_at', metadata['created_at'])
            }
        )
        
        # Return data for next step
        return {
            'statusCode': 200,
            'image_id': image_id,
            'image_data': image_base64,
            'original_dimensions': {'width': width, 'height': height},
            'image_mode': mode,
            'metadata': dict(metadata)  # Convert DynamoDB item to regular dict
        }
        
    except Exception as e:
        error_msg = f"Error fetching image: {str(e)}"
        print(f"ERROR: {error_msg}")
        
        # Update metadata with error status
        try:
            table = dynamodb.Table(TABLE_NAME)
            table.update_item(
                Key={'image_id': image_id},
                UpdateExpression='SET workflow_stage = :stage, error_message = :error',
                ExpressionAttributeValues={
                    ':stage': 'fetch_failed',
                    ':error': error_msg
                }
            )
        except:
            pass  # Don't fail if we can't update the error status
        
        return {
            'statusCode': 500,
            'error': error_msg,
            'image_id': image_id
        }
