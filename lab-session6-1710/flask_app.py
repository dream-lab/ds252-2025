from flask import Flask, request, jsonify
import boto3
import requests
import os
import uuid
from datetime import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS clients
s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

S3_BUCKET = os.environ.get('S3_BUCKET')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200


@app.route('/process-image', methods=['POST'])
def process_image():
    """
    Process image from URL: download, store in S3, and save metadata to DynamoDB
    """
    try:
        # Parse request
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        image_url = data.get('image_url')
        
        if not image_url:
            return jsonify({'error': 'image_url is required'}), 400
        
        # Generate unique image ID
        image_id = str(uuid.uuid4())
        
        logger.info(f"Processing image: {image_id} from URL: {image_url}")
        
        # Download image from URL
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_data = response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download image: {str(e)}")
            return jsonify({'error': f'Failed to download image: {str(e)}'}), 400
        
        # Get file extension from URL
        file_extension = image_url.split('.')[-1].split('?')[0][:4]
        if file_extension not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            file_extension = 'jpg'
        
        s3_key = f"images/{image_id}.{file_extension}"
        
        # Upload to S3
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=image_data,
                ContentType=f'image/{file_extension}'
            )
            logger.info(f"Image uploaded to S3: s3://{S3_BUCKET}/{s3_key}")
        except Exception as e:
            logger.error(f"Failed to upload to S3: {str(e)}")
            return jsonify({'error': f'Failed to upload to S3: {str(e)}'}), 500
        
        # Write metadata to DynamoDB
        try:
            table = dynamodb.Table(DYNAMODB_TABLE)
            
            metadata_item = {
                'image_id': image_id,
                's3_bucket': S3_BUCKET,
                's3_key': s3_key,
                'original_url': image_url,
                'file_extension': file_extension,
                'file_size': len(image_data),
                'status': 'processed',
                'created_at': datetime.utcnow().isoformat(),
                'processed_by': 'flask_ec2_server'
            }
            
            table.put_item(Item=metadata_item)
            logger.info(f"Metadata saved to DynamoDB for image: {image_id}")
        except Exception as e:
            logger.error(f"Failed to save metadata to DynamoDB: {str(e)}")
            return jsonify({'error': f'Failed to save metadata: {str(e)}'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Image processed successfully',
            'image_id': image_id,
            's3_location': f's3://{S3_BUCKET}/{s3_key}',
            'file_size': len(image_data),
            'file_extension': file_extension,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'service': 'DS252 Image Processing Flask Server',
        'version': '1.0',
        'endpoints': {
            '/health': 'Health check endpoint',
            '/process-image': 'POST endpoint to process image from URL'
        }
    }), 200


if __name__ == '__main__':
    logger.info("Starting Flask server on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
