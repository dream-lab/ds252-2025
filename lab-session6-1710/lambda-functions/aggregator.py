import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Lambda function to aggregate results from parallel inference and update DynamoDB
    """
    try:
        # Parse input from Step Functions
        # event contains results from parallel branches
        alexnet_result = event[0]  # First branch result
        resnet_result = event[1]   # Second branch result
        mobilenet_result = event[2]  # Third branch result
        
        # Parse each result
        alexnet_data = json.loads(alexnet_result.get('body', '{}'))
        resnet_data = json.loads(resnet_result.get('body', '{}'))
        mobilenet_data = json.loads(mobilenet_result.get('body', '{}'))
        
        # Aggregate predictions
        aggregated_results = {
            'alexnet': {
                'model': alexnet_data.get('model'),
                'top_prediction': alexnet_data.get('predictions', [{}])[0] if alexnet_data.get('predictions') else {},
                'processing_time_ms': alexnet_data.get('processing_time_ms', 0)
            },
            'resnet': {
                'model': resnet_data.get('model'),
                'top_prediction': resnet_data.get('predictions', [{}])[0] if resnet_data.get('predictions') else {},
                'processing_time_ms': resnet_data.get('processing_time_ms', 0)
            },
            'mobilenet': {
                'model': mobilenet_data.get('model'),
                'top_prediction': mobilenet_data.get('predictions', [{}])[0] if mobilenet_data.get('predictions') else {},
                'processing_time_ms': mobilenet_data.get('processing_time_ms', 0)
            }
        }
        
        # Find consensus prediction (most common top prediction)
        predictions = [
            alexnet_data.get('predictions', [{}])[0].get('class_name', 'unknown') if alexnet_data.get('predictions') else 'unknown',
            resnet_data.get('predictions', [{}])[0].get('class_name', 'unknown') if resnet_data.get('predictions') else 'unknown',
            mobilenet_data.get('predictions', [{}])[0].get('class_name', 'unknown') if mobilenet_data.get('predictions') else 'unknown'
        ]
        
        # Simple consensus: most frequent prediction
        consensus_prediction = max(set(predictions), key=predictions.count)
        
        # Calculate average confidence
        confidences = [
            alexnet_data.get('predictions', [{}])[0].get('confidence', 0) if alexnet_data.get('predictions') else 0,
            resnet_data.get('predictions', [{}])[0].get('confidence', 0) if resnet_data.get('predictions') else 0,
            mobilenet_data.get('predictions', [{}])[0].get('confidence', 0) if mobilenet_data.get('predictions') else 0
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Update DynamoDB (assuming image_id is passed in context)
        # In real implementation, you would get image_id from the Step Functions input
        image_id = context.get('image_id', 'unknown')
        
        table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
        
        # Update the item with classification results
        table.update_item(
            Key={'image_id': image_id},
            UpdateExpression='SET #status = :status, #results = :results, #updated_at = :updated_at',
            ExpressionAttributeNames={
                '#status': 'status',
                '#results': 'classification_results',
                '#updated_at': 'updated_at'
            },
            ExpressionAttributeValues={
                ':status': 'classified',
                ':results': {
                    'consensus_prediction': consensus_prediction,
                    'average_confidence': avg_confidence,
                    'model_results': aggregated_results,
                    'classification_timestamp': datetime.utcnow().isoformat()
                },
                ':updated_at': datetime.utcnow().isoformat()
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Classification results aggregated successfully',
                'consensus_prediction': consensus_prediction,
                'average_confidence': avg_confidence,
                'model_results': aggregated_results,
                'image_id': image_id
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
