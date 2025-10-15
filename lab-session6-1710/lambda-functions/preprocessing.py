import json
import base64
import io
from PIL import Image
import numpy as np

def lambda_handler(event, context):
    """
    Lambda function to preprocess images (grayscale, flip, rotate, resize)
    """
    try:
        # Parse input
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event
        image_data = body.get('image_data')
        preprocessing_config = body.get('preprocessing_config', {})
        
        if not image_data:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'image_data is required'})
            }
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Apply preprocessing steps
        processed_image = image.copy()
        
        # Grayscale
        if preprocessing_config.get('grayscale', False):
            processed_image = processed_image.convert('L').convert('RGB')
        
        # Flip
        flip_type = preprocessing_config.get('flip')
        if flip_type == 'horizontal':
            processed_image = processed_image.transpose(Image.FLIP_LEFT_RIGHT)
        elif flip_type == 'vertical':
            processed_image = processed_image.transpose(Image.FLIP_TOP_BOTTOM)
        
        # Rotate
        rotate_angle = preprocessing_config.get('rotate', 0)
        if rotate_angle != 0:
            processed_image = processed_image.rotate(rotate_angle, expand=True)
        
        # Resize
        resize_dimensions = preprocessing_config.get('resize')
        if resize_dimensions and len(resize_dimensions) == 2:
            processed_image = processed_image.resize(resize_dimensions, Image.Resampling.LANCZOS)
        
        # Convert back to base64
        buffer = io.BytesIO()
        processed_image.save(buffer, format='JPEG')
        processed_image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Image preprocessed successfully',
                'processed_image_data': processed_image_data,
                'original_size': image.size,
                'processed_size': processed_image.size,
                'preprocessing_applied': preprocessing_config
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
