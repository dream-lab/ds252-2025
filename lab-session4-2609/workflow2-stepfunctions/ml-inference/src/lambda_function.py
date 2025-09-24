import json
import base64
import numpy as np
from PIL import Image
import io
import os
import random

def lambda_handler(event, context):
    """
    ML Inference Lambda - Parallel execution for AlexNet, ResNet, MobileNet
    
    This is a mock implementation that simulates ML model inference.
    In a real scenario, you would load actual models (TensorFlow, PyTorch, etc.)
    
    Input: {"processed_image_data": "base64", "model_name": "alexnet|resnet|mobilenet", ...}
    Output: {"predictions": [...], "model_name": "...", "confidence": 0.95}
    """
    
    try:
        image_id = event['image_id']
        model_name = event.get('model_name', 'unknown')
        processed_image_base64 = event['processed_image_data']
        
        print(f"Running {model_name} inference for image_id: {image_id}")
        
        # Decode the processed image
        image_data = base64.b64decode(processed_image_base64)
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to numpy array (simulating model preprocessing)
        image_array = np.array(image)
        print(f"Image array shape: {image_array.shape}")
        
        # Mock inference based on model type
        predictions = perform_mock_inference(model_name, image_array)
        
        # Simulate processing time (different models have different speeds)
        processing_times = {
            'alexnet': 0.1,    # Faster, older model
            'resnet': 0.3,     # Slower, more accurate
            'mobilenet': 0.05  # Fastest, optimized for mobile
        }
        
        import time
        time.sleep(processing_times.get(model_name.lower(), 0.2))
        
        print(f"{model_name} inference completed for image_id: {image_id}")
        
        return {
            'statusCode': 200,
            'image_id': image_id,
            'model_name': model_name,
            'predictions': predictions['labels'],
            'confidence_scores': predictions['scores'],
            'top_prediction': predictions['top_prediction'],
            'processing_time': processing_times.get(model_name.lower(), 0.2),
            'model_version': get_model_version(model_name)
        }
        
    except Exception as e:
        error_msg = f"Error in {model_name} inference: {str(e)}"
        print(f"ERROR: {error_msg}")
        
        return {
            'statusCode': 500,
            'error': error_msg,
            'image_id': event.get('image_id', 'unknown'),
            'model_name': event.get('model_name', 'unknown'),
            'inference_failed': True
        }

def perform_mock_inference(model_name, image_array):
    """
    Mock ML inference that returns realistic-looking predictions
    In a real implementation, this would call actual ML models
    """
    
    # Common ImageNet-like class labels
    class_labels = [
        'cat', 'dog', 'bird', 'car', 'bicycle', 'airplane', 'boat', 'train',
        'truck', 'traffic_light', 'fire_hydrant', 'stop_sign', 'parking_meter',
        'bench', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella',
        'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports_ball',
        'kite', 'baseball_bat', 'baseball_glove', 'skateboard', 'surfboard',
        'tennis_racket', 'bottle', 'wine_glass', 'cup', 'fork', 'knife', 'spoon',
        'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot',
        'hot_dog', 'pizza', 'donut', 'cake'
    ]
    
    # Model-specific behavior simulation
    if model_name.lower() == 'alexnet':
        # AlexNet: Older model, slightly less accurate
        confidence_base = 0.75
        num_predictions = 5
    elif model_name.lower() == 'resnet':
        # ResNet: More accurate, higher confidence
        confidence_base = 0.85
        num_predictions = 5
    elif model_name.lower() == 'mobilenet':
        # MobileNet: Fast but slightly less confident
        confidence_base = 0.78
        num_predictions = 3
    else:
        confidence_base = 0.70
        num_predictions = 3
    
    # Generate mock predictions
    selected_labels = random.sample(class_labels, num_predictions)
    
    # Generate confidence scores (decreasing order)
    scores = []
    base_score = confidence_base + random.uniform(-0.1, 0.1)
    for i in range(num_predictions):
        score = max(0.1, base_score - (i * random.uniform(0.05, 0.15)))
        scores.append(round(score, 3))
    
    # Ensure scores sum to reasonable total (normalize if needed)
    total_score = sum(scores)
    if total_score > 1.0:
        scores = [round(score / total_score, 3) for score in scores]
    
    predictions = {
        'labels': selected_labels,
        'scores': scores,
        'top_prediction': {
            'label': selected_labels[0],
            'confidence': scores[0]
        }
    }
    
    return predictions

def get_model_version(model_name):
    """Return mock model version information"""
    versions = {
        'alexnet': 'v2.1',
        'resnet': 'ResNet-50 v1.5',
        'mobilenet': 'MobileNetV2 v2.0'
    }
    return versions.get(model_name.lower(), 'v1.0')

# Individual model handlers (for testing individual models)
def alexnet_handler(event, context):
    """Specific handler for AlexNet"""
    event['model_name'] = 'alexnet'
    return lambda_handler(event, context)

def resnet_handler(event, context):
    """Specific handler for ResNet"""
    event['model_name'] = 'resnet'
    return lambda_handler(event, context)

def mobilenet_handler(event, context):
    """Specific handler for MobileNet"""
    event['model_name'] = 'mobilenet'
    return lambda_handler(event, context)
