output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.image_processor.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.image_processor.arn
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.flask_server.id
}

output "ec2_instance_public_ip" {
  description = "EC2 instance public IP"
  value       = aws_instance.flask_server.public_ip
}

output "ec2_instance_private_ip" {
  description = "EC2 instance private IP"
  value       = aws_instance.flask_server.private_ip
}

output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.image_bucket.bucket
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.metadata_table.name
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "subnet_id" {
  description = "Subnet ID"
  value       = aws_subnet.main.id
}
