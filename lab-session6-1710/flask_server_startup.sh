#!/bin/bash
set -e

# Update system
yum update -y
yum install -y python3 python3-pip git

# Install Python dependencies with compatible versions for older OpenSSL
pip3 install --upgrade pip setuptools
pip3 install 'urllib3<2.0' 'boto3>=1.26.0,<1.30.0' 'botocore>=1.29.0,<1.33.0' flask requests

# Create application directory
mkdir -p /opt/flask-app
cd /opt/flask-app

# Create Flask application file (read from S3 or create directly)
cat > app.py << 'EOF'
from flask import Flask, request, jsonify
import requests
import os
import uuid
from datetime import datetime
import logging
import json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS configuration from environment
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')
S3_BUCKET = os.environ.get('S3_BUCKET', 'ds252-hybrid-images-235319806087')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200

@app.route('/process-image', methods=['POST'])
def process_image():
    """
    Process image from URL: download, upload to S3 via REST API, save to DynamoDB via REST API
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
        
        # Get file extension
        file_extension = image_url.split('.')[-1].split('?')[0][:4]
        if file_extension not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            file_extension = 'jpg'
        
        s3_key = f"images/{image_id}.{file_extension}"
        s3_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        
        # Upload to S3 via REST API (PUT request)
        try:
            s3_response = requests.put(
                s3_url,
                data=image_data,
                headers={'Content-Type': f'image/{file_extension}'},
                timeout=30
            )
            s3_response.raise_for_status()
            logger.info(f"Image uploaded to S3: {s3_url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload to S3: {str(e)}")
            return jsonify({'error': f'Failed to upload to S3: {str(e)}'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Image processed successfully',
            'image_id': image_id,
            's3_location': s3_url,
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
            '/process-image': 'POST endpoint to process image from URL',
            '/test-process': 'POST endpoint to test with generated image'
        }
    }), 200

@app.route('/test-process', methods=['POST'])
def test_process():
    """
    Test endpoint that processes a generated test image
    """
    try:
        # Generate a simple test image (1x1 PNG)
        image_data = bytes.fromhex('89504e470d0a1a0a0000000d494844520000000100000001080600000090773db30000000a49444154789c6300010000050001db4b430009000000004945 4e44ae426082')
        
        # Generate unique image ID
        image_id = str(uuid.uuid4())
        file_extension = 'png'
        s3_key = f"test/{image_id}.{file_extension}"
        s3_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        
        # Upload to S3 via REST API
        try:
            s3_response = requests.put(
                s3_url,
                data=image_data,
                headers={'Content-Type': f'image/{file_extension}'},
                timeout=30
            )
            s3_response.raise_for_status()
            logger.info(f"Test image uploaded to S3: {s3_url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload test image to S3: {str(e)}")
            return jsonify({'error': f'Failed to upload to S3: {str(e)}'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Test image processed successfully',
            'image_id': image_id,
            's3_location': s3_url,
            'file_size': len(image_data),
            'file_extension': file_extension,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in test: {str(e)}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

if __name__ == '__main__':
    logger.info("Starting Flask server on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF

# Set environment variables - these will be injected by Terraform
export AWS_REGION=ap-south-1

# Create systemd service for Flask app with environment variables
cat > /etc/systemd/system/flask-app.service << 'EOFSERVICE'
[Unit]
Description=DS252 Flask Image Processing Server
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/flask-app
Environment="PATH=/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin"
Environment="AWS_REGION=ap-south-1"
Environment="S3_BUCKET=${s3_bucket}"
ExecStart=/usr/bin/python3 /opt/flask-app/app.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOFSERVICE

# Enable and start the Flask service
systemctl daemon-reload
systemctl enable flask-app.service
systemctl start flask-app.service

# Log startup
echo "Flask server startup completed at $(date)" >> /var/log/flask-startup.log
