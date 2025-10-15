output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.image_bucket.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.image_bucket.arn
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.metadata_table.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  value       = aws_dynamodb_table.metadata_table.arn
}

output "lambda_image_ingestion_arn" {
  description = "ARN of the image ingestion Lambda function"
  value       = aws_lambda_function.image_ingestion.arn
}

output "stepfunctions_arn" {
  description = "ARN of the Step Functions state machine"
  value       = aws_sfn_state_machine.classification_pipeline.arn
}

output "aws_account_id" {
  description = "Current AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "aws_region" {
  description = "Current AWS Region"
  value       = data.aws_region.current.name
}
