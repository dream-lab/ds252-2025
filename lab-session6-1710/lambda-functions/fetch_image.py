import json
import boto3
import os
import base64

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda function to fetch image from S3 and return base64 encoded data
    """
    try:
        # Parse input
        image_id = event.get('image_id')
        
        if not image_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'image_id is required'})
            }
        
        # Get S3 bucket from environment
        s3_bucket = os.environ['S3_BUCKET']
        
        # Try different file extensions
        extensions = ['jpg', 'jpeg', 'png', 'gif']
        image_data = None
        s3_key = None
        
        for ext in extensions:
            try:
                s3_key = f"images/{image_id}.{ext}"
                response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
                image_data = response['Body'].read()
                break
            except s3_client.exceptions.NoSuchKey:
                continue
        
        if image_data is None:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'Image {image_id} not found in S3'})
            }
        
        # Encode image to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'image_id': image_id,
                's3_key': s3_key,
                'image_data': image_base64,
                'file_size': len(image_data)
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
