import json
import base64
from PIL import Image, ImageOps
import io
import os

def lambda_handler(event, context):
    """
    Preprocessing Pipeline Lambda - Steps 2-5 of Workflow 2
    
    Performs all preprocessing steps in sequence:
    1. Grayscale conversion
    2. Flip (horizontal)
    3. Rotate (90 degrees)
    4. Resize (224x224 for ML models)
    
    Input: {"image_data": "base64", "image_id": "uuid", ...}
    Output: {"processed_image_data": "base64", "image_id": "uuid", ...}
    """
    
    try:
        image_id = event['image_id']
        image_base64 = event['image_data']
        
        print(f"Starting preprocessing pipeline for image_id: {image_id}")
        
        # Decode base64 image
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data))
        
        original_size = image.size
        print(f"Original image size: {original_size}")
        
        # Step 1: Convert to Grayscale
        print("Step 1: Converting to grayscale")
        if image.mode != 'L':  # If not already grayscale
            image = image.convert('L')
        
        # Step 2: Flip horizontally
        print("Step 2: Flipping horizontally")
        image = ImageOps.mirror(image)
        
        # Step 3: Rotate 90 degrees clockwise
        print("Step 3: Rotating 90 degrees")
        image = image.rotate(-90, expand=True)  # -90 for clockwise rotation
        
        # Step 4: Resize to 224x224 (standard input size for many ML models)
        print("Step 4: Resizing to 224x224")
        target_size = (224, 224)
        image = image.resize(target_size, Image.Resampling.LANCZOS)
        
        # Convert back to RGB for ML models (even though grayscale, some models expect RGB)
        image = image.convert('RGB')
        
        final_size = image.size
        print(f"Final processed image size: {final_size}")
        
        # Convert processed image back to base64
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=95)
        processed_image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        print(f"Preprocessing completed successfully for image_id: {image_id}")
        
        # Return processed data for ML inference
        result = {
            'statusCode': 200,
            'image_id': image_id,
            'processed_image_data': processed_image_base64,
            'original_dimensions': event.get('original_dimensions', {}),
            'processed_dimensions': {'width': final_size[0], 'height': final_size[1]},
            'preprocessing_steps': [
                'grayscale_conversion',
                'horizontal_flip', 
                'rotate_90_degrees',
                'resize_224x224',
                'convert_to_rgb'
            ],
            'metadata': event.get('metadata', {})
        }
        
        return result
        
    except Exception as e:
        error_msg = f"Error in preprocessing pipeline: {str(e)}"
        print(f"ERROR: {error_msg}")
        
        return {
            'statusCode': 500,
            'error': error_msg,
            'image_id': event.get('image_id', 'unknown'),
            'preprocessing_failed': True
        }

def resize_image_only(event, context):
    """
    Alternative function for just resizing (if you want to test individual steps)
    """
    try:
        image_base64 = event['image_data']
        target_width = event.get('width', 224)
        target_height = event.get('height', 224)
        
        # Decode and resize
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data))
        image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Encode back to base64
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        resized_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return {
            'statusCode': 200,
            'resized_image_data': resized_base64,
            'dimensions': {'width': target_width, 'height': target_height}
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'error': f"Resize error: {str(e)}"
        }
