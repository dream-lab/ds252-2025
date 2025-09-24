import json
import boto3
from datetime import datetime
import os

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']

def lambda_handler(event, context):
    """
    Aggregator Lambda - Final step of Workflow 2
    
    Consolidates results from all ML models and updates DynamoDB with labels
    
    Input: {
        "image_id": "uuid",
        "alexnet_result": {...},
        "resnet_result": {...},
        "mobilenet_result": {...}
    }
    Output: {"image_id": "uuid", "aggregated_results": {...}, "status": "completed"}
    """
    
    try:
        image_id = event['image_id']
        print(f"Aggregating results for image_id: {image_id}")
        
        # Extract results from each model
        alexnet_result = event.get('alexnet_result', {})
        resnet_result = event.get('resnet_result', {})
        mobilenet_result = event.get('mobilenet_result', {})
        
        # Check if any model failed
        failed_models = []
        successful_models = []
        
        for model_name, result in [('alexnet', alexnet_result), ('resnet', resnet_result), ('mobilenet', mobilenet_result)]:
            if result.get('statusCode') != 200 or result.get('inference_failed'):
                failed_models.append(model_name)
                print(f"WARNING: {model_name} inference failed")
            else:
                successful_models.append(model_name)
        
        if not successful_models:
            raise Exception("All ML model inferences failed")
        
        # Aggregate predictions from successful models
        aggregated_predictions = aggregate_model_predictions(
            alexnet_result, resnet_result, mobilenet_result, successful_models
        )
        
        # Calculate consensus and confidence
        consensus_result = calculate_consensus(aggregated_predictions)
        
        # Prepare comprehensive results
        final_results = {
            'image_id': image_id,
            'processing_timestamp': datetime.utcnow().isoformat(),
            'successful_models': successful_models,
            'failed_models': failed_models,
            'individual_predictions': {
                'alexnet': extract_model_predictions(alexnet_result),
                'resnet': extract_model_predictions(resnet_result),
                'mobilenet': extract_model_predictions(mobilenet_result)
            },
            'aggregated_predictions': aggregated_predictions,
            'consensus': consensus_result,
            'processing_summary': {
                'total_models': 3,
                'successful_models': len(successful_models),
                'failed_models': len(failed_models),
                'overall_confidence': consensus_result.get('confidence', 0.0)
            }
        }
        
        # Update DynamoDB with results
        update_dynamodb_with_results(image_id, final_results)
        
        print(f"Aggregation completed successfully for image_id: {image_id}")
        print(f"Consensus prediction: {consensus_result.get('label')} ({consensus_result.get('confidence', 0):.3f})")
        
        return {
            'statusCode': 200,
            'image_id': image_id,
            'aggregated_results': final_results,
            'status': 'classification_completed',
            'consensus_prediction': consensus_result
        }
        
    except Exception as e:
        error_msg = f"Error in result aggregation: {str(e)}"
        print(f"ERROR: {error_msg}")
        
        # Update DynamoDB with error status
        try:
            update_dynamodb_error(event.get('image_id', 'unknown'), error_msg)
        except:
            pass
        
        return {
            'statusCode': 500,
            'error': error_msg,
            'image_id': event.get('image_id', 'unknown'),
            'status': 'aggregation_failed'
        }

def extract_model_predictions(model_result):
    """Extract clean predictions from model result"""
    if model_result.get('statusCode') != 200 or model_result.get('inference_failed'):
        return {
            'status': 'failed',
            'error': model_result.get('error', 'Unknown error')
        }
    
    return {
        'status': 'success',
        'model_name': model_result.get('model_name', 'unknown'),
        'predictions': model_result.get('predictions', []),
        'confidence_scores': model_result.get('confidence_scores', []),
        'top_prediction': model_result.get('top_prediction', {}),
        'processing_time': model_result.get('processing_time', 0),
        'model_version': model_result.get('model_version', 'unknown')
    }

def aggregate_model_predictions(alexnet_result, resnet_result, mobilenet_result, successful_models):
    """Combine predictions from all successful models"""
    
    all_predictions = {}
    
    # Collect all unique labels and their scores
    for model_name, result in [('alexnet', alexnet_result), ('resnet', resnet_result), ('mobilenet', mobilenet_result)]:
        if model_name not in successful_models:
            continue
            
        predictions = result.get('predictions', [])
        scores = result.get('confidence_scores', [])
        
        for label, score in zip(predictions, scores):
            if label not in all_predictions:
                all_predictions[label] = []
            all_predictions[label].append({
                'model': model_name,
                'score': score
            })
    
    # Calculate aggregated scores for each label
    aggregated = {}
    for label, model_scores in all_predictions.items():
        # Average score across models that predicted this label
        avg_score = sum(item['score'] for item in model_scores) / len(model_scores)
        # Boost score based on number of models that agree
        consensus_boost = len(model_scores) / len(successful_models)
        final_score = avg_score * (0.7 + 0.3 * consensus_boost)  # Weight consensus
        
        aggregated[label] = {
            'average_confidence': round(avg_score, 3),
            'consensus_score': round(final_score, 3),
            'model_count': len(model_scores),
            'models': [item['model'] for item in model_scores]
        }
    
    # Sort by consensus score
    sorted_predictions = sorted(aggregated.items(), key=lambda x: x[1]['consensus_score'], reverse=True)
    
    return dict(sorted_predictions)

def calculate_consensus(aggregated_predictions):
    """Calculate final consensus prediction"""
    
    if not aggregated_predictions:
        return {
            'label': 'unknown',
            'confidence': 0.0,
            'method': 'no_predictions'
        }
    
    # Get top prediction
    top_label, top_data = next(iter(aggregated_predictions.items()))
    
    return {
        'label': top_label,
        'confidence': top_data['consensus_score'],
        'model_agreement': top_data['model_count'],
        'method': 'weighted_consensus',
        'alternative_predictions': list(aggregated_predictions.keys())[1:3]  # Top 2 alternatives
    }

def update_dynamodb_with_results(image_id, results):
    """Update DynamoDB table with classification results"""
    
    table = dynamodb.Table(TABLE_NAME)
    
    # Prepare update expression
    update_expression = """
        SET workflow_stage = :stage,
            classification_results = :results,
            consensus_label = :label,
            consensus_confidence = :confidence,
            successful_models = :success_models,
            failed_models = :failed_models,
            processing_completed_at = :timestamp,
            updated_at = :timestamp
    """
    
    expression_values = {
        ':stage': 'classification_completed',
        ':results': results,
        ':label': results['consensus']['label'],
        ':confidence': results['consensus']['confidence'],
        ':success_models': results['successful_models'],
        ':failed_models': results['failed_models'],
        ':timestamp': results['processing_timestamp']
    }
    
    table.update_item(
        Key={'image_id': image_id},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_values
    )
    
    print(f"DynamoDB updated successfully for image_id: {image_id}")

def update_dynamodb_error(image_id, error_message):
    """Update DynamoDB with error status"""
    
    table = dynamodb.Table(TABLE_NAME)
    
    table.update_item(
        Key={'image_id': image_id},
        UpdateExpression='SET workflow_stage = :stage, error_message = :error, updated_at = :timestamp',
        ExpressionAttributeValues={
            ':stage': 'classification_failed',
            ':error': error_message,
            ':timestamp': datetime.utcnow().isoformat()
        }
    )
    
    print(f"DynamoDB updated with error status for image_id: {image_id}")
