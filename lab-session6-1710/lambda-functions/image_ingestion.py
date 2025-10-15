import json
import boto3
import urllib.request
import os
from datetime import datetime
import uuid

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Lambda function to ingest images from URLs and store them in S3 with metadata in DynamoDB
    """
    try:
        # Parse input
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event
        image_url = body.get('image_url')
        metadata = body.get('metadata', {})
        
        if not image_url:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'image_url is required'})
            }
        
        # Generate unique image ID
        image_id = str(uuid.uuid4())
        
        # Download image
        with urllib.request.urlopen(image_url) as response:
            image_data = response.read()
        
        # Get file extension from URL
        file_extension = image_url.split('.')[-1].split('?')[0]
        if file_extension not in ['jpg', 'jpeg', 'png', 'gif']:
            file_extension = 'jpg'
        
        # Upload to S3
        s3_bucket = os.environ['S3_BUCKET']
        s3_key = f"images/{image_id}.{file_extension}"
        
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=image_data,
            ContentType=f'image/{file_extension}'
        )
        
        # Prepare metadata for DynamoDB
        table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
        
        item = {
            'image_id': image_id,
            's3_bucket': s3_bucket,
            's3_key': s3_key,
            'original_url': image_url,
            'file_extension': file_extension,
            'file_size': len(image_data),
            'status': 'ingested',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Add custom metadata
        item.update(metadata)
        
        # Store in DynamoDB
        table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Image ingested successfully',
                'image_id': image_id,
                's3_location': f's3://{s3_bucket}/{s3_key}'
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
