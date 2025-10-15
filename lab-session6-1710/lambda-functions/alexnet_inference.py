import json
import base64
import io
import numpy as np
from PIL import Image

def lambda_handler(event, context):
    """
    Lambda function to perform AlexNet-style inference (simulated)
    """
    try:
        # Parse input
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event
        image_data = body.get('processed_image_data')
        
        if not image_data:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'processed_image_data is required'})
            }
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize to AlexNet input size (224x224)
        image = image.resize((224, 224), Image.Resampling.LANCZOS)
        
        # Convert to numpy array and normalize
        img_array = np.array(image) / 255.0
        
        # Simulate AlexNet inference (in real implementation, you would use a trained model)
        # For this lab, we'll generate mock predictions
        np.random.seed(42)  # For reproducible results
        mock_predictions = np.random.random(1000)  # 1000 classes like ImageNet
        mock_predictions = mock_predictions / np.sum(mock_predictions)  # Softmax
        
        # Get top 5 predictions
        top_5_indices = np.argsort(mock_predictions)[-5:][::-1]
        top_5_scores = mock_predictions[top_5_indices]
        
        # Mock class names (in real implementation, use actual ImageNet classes)
        class_names = [f"class_{i}" for i in range(1000)]
        
        predictions = []
        for i, (idx, score) in enumerate(zip(top_5_indices, top_5_scores)):
            predictions.append({
                'rank': i + 1,
                'class_id': int(idx),
                'class_name': class_names[idx],
                'confidence': float(score)
            })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'model': 'AlexNet',
                'predictions': predictions,
                'input_size': (224, 224),
                'processing_time_ms': 150  # Mock processing time
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
