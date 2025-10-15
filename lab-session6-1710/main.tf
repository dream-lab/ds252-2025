# Configure the AWS Provider
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Data source to get the current AWS account ID
data "aws_caller_identity" "current" {}

# Data source to get the current AWS region
data "aws_region" "current" {}

# S3 bucket for storing images
resource "aws_s3_bucket" "image_bucket" {
  bucket = "${var.project_name}-image-bucket-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "image_bucket_versioning" {
  bucket = aws_s3_bucket.image_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "image_bucket_pab" {
  bucket = aws_s3_bucket.image_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DynamoDB table for metadata
resource "aws_dynamodb_table" "metadata_table" {
  name           = "${var.project_name}-metadata-table"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "image_id"

  attribute {
    name = "image_id"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-metadata-table"
    Environment = var.environment
  }
}

# IAM role for Lambda functions
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for Lambda functions
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.image_bucket.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.image_bucket.arn
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.metadata_table.arn
      }
    ]
  })
}

# IAM role for Step Functions
resource "aws_iam_role" "stepfunctions_role" {
  name = "${var.project_name}-stepfunctions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for Step Functions
resource "aws_iam_role_policy" "stepfunctions_policy" {
  name = "${var.project_name}-stepfunctions-policy"
  role = aws_iam_role.stepfunctions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.fetch_image.arn,
          aws_lambda_function.preprocessing.arn,
          aws_lambda_function.alexnet_inference.arn,
          aws_lambda_function.resnet_inference.arn,
          aws_lambda_function.mobilenet_inference.arn,
          aws_lambda_function.aggregator.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = aws_dynamodb_table.metadata_table.arn
      }
    ]
  })
}

# Lambda function for image ingestion
resource "aws_lambda_function" "image_ingestion" {
  filename         = "lambda_functions.zip"
  function_name    = "${var.project_name}-image-ingestion"
  role            = aws_iam_role.lambda_role.arn
  handler         = "image_ingestion.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      S3_BUCKET = aws_s3_bucket.image_bucket.bucket
      DYNAMODB_TABLE = aws_dynamodb_table.metadata_table.name
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_policy,
    aws_cloudwatch_log_group.lambda_logs,
  ]
}

# Lambda function for fetching images
resource "aws_lambda_function" "fetch_image" {
  filename         = "lambda_functions.zip"
  function_name    = "${var.project_name}-fetch-image"
  role            = aws_iam_role.lambda_role.arn
  handler         = "fetch_image.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      S3_BUCKET = aws_s3_bucket.image_bucket.bucket
    }
  }
}

# Lambda function for preprocessing
resource "aws_lambda_function" "preprocessing" {
  filename         = "lambda_functions.zip"
  function_name    = "${var.project_name}-preprocessing"
  role            = aws_iam_role.lambda_role.arn
  handler         = "preprocessing.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = 300
}

# Lambda function for AlexNet inference
resource "aws_lambda_function" "alexnet_inference" {
  filename         = "lambda_functions.zip"
  function_name    = "${var.project_name}-alexnet-inference"
  role            = aws_iam_role.lambda_role.arn
  handler         = "alexnet_inference.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = 300
}

# Lambda function for ResNet inference
resource "aws_lambda_function" "resnet_inference" {
  filename         = "lambda_functions.zip"
  function_name    = "${var.project_name}-resnet-inference"
  role            = aws_iam_role.lambda_role.arn
  handler         = "resnet_inference.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = 300
}

# Lambda function for MobileNet inference
resource "aws_lambda_function" "mobilenet_inference" {
  filename         = "lambda_functions.zip"
  function_name    = "${var.project_name}-mobilenet-inference"
  role            = aws_iam_role.lambda_role.arn
  handler         = "mobilenet_inference.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = 300
}

# Lambda function for aggregating results
resource "aws_lambda_function" "aggregator" {
  filename         = "lambda_functions.zip"
  function_name    = "${var.project_name}-aggregator"
  role            = aws_iam_role.lambda_role.arn
  handler         = "aggregator.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.metadata_table.name
    }
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.project_name}"
  retention_in_days = 14
}

# Step Functions state machine definition
locals {
  stepfunctions_definition = jsonencode({
    Comment = "Image Classification Pipeline"
    StartAt = "FetchImage"
    States = {
      FetchImage = {
        Type = "Task"
        Resource = aws_lambda_function.fetch_image.arn
        Next = "Preprocessing"
      }
      Preprocessing = {
        Type = "Task"
        Resource = aws_lambda_function.preprocessing.arn
        Next = "ParallelInference"
      }
      ParallelInference = {
        Type = "Parallel"
        Branches = [
          {
            StartAt = "AlexNet"
            States = {
              AlexNet = {
                Type = "Task"
                Resource = aws_lambda_function.alexnet_inference.arn
                End = true
              }
            }
          },
          {
            StartAt = "ResNet"
            States = {
              ResNet = {
                Type = "Task"
                Resource = aws_lambda_function.resnet_inference.arn
                End = true
              }
            }
          },
          {
            StartAt = "MobileNet"
            States = {
              MobileNet = {
                Type = "Task"
                Resource = aws_lambda_function.mobilenet_inference.arn
                End = true
              }
            }
          }
        ]
        Next = "AggregateResults"
      }
      AggregateResults = {
        Type = "Task"
        Resource = aws_lambda_function.aggregator.arn
        End = true
      }
    }
  })
}

# Step Functions state machine
resource "aws_sfn_state_machine" "classification_pipeline" {
  name     = "${var.project_name}-classification-pipeline"
  role_arn = aws_iam_role.stepfunctions_role.arn

  definition = local.stepfunctions_definition
}

# Archive the Lambda function code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "lambda-functions"
  output_path = "lambda_functions.zip"
}
