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

data "aws_caller_identity" "current" {}

# ==================== S3 BUCKET ====================
resource "aws_s3_bucket" "image_bucket" {
  bucket = "${var.project_name}-images-${local.suffix}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${var.project_name}-images-${local.suffix}"
  }
}

resource "aws_s3_bucket_versioning" "image_bucket_versioning" {
  bucket = aws_s3_bucket.image_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "image_bucket_pab" {
  bucket = aws_s3_bucket.image_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "image_bucket_policy" {
  bucket = aws_s3_bucket.image_bucket.id
  
  depends_on = [aws_s3_bucket_public_access_block.image_bucket_pab]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "PublicReadGetObject"
        Effect = "Allow"
        Principal = "*"
        Action = "s3:GetObject"
        Resource = "${aws_s3_bucket.image_bucket.arn}/*"
      },
      {
        Sid    = "PublicPutObject"
        Effect = "Allow"
        Principal = "*"
        Action = "s3:PutObject"
        Resource = "${aws_s3_bucket.image_bucket.arn}/*"
      }
    ]
  })
}

# ==================== SECURITY GROUP ====================
resource "aws_security_group" "public_sg" {
  name        = "${var.project_name}-sg"
  description = "Public security group for Flask and Lambda"

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-sg"
  }
}

# ==================== IAM ROLE FOR LAMBDA ====================
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role-${local.suffix}"

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
      }
    ]
  })
}

# ==================== DATA SOURCE FOR AMI ====================
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

# ==================== EC2 KEY PAIR ====================
resource "tls_private_key" "flask_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "flask_key" {
  key_name   = "${var.project_name}-key-${local.suffix}"
  public_key = tls_private_key.flask_key.public_key_openssh
}

resource "local_file" "flask_key_pem" {
  content         = tls_private_key.flask_key.private_key_pem
  filename        = "${path.module}/${var.project_name}-key.pem"
  file_permission = "0600"
}

# ==================== EC2 INSTANCE (PUBLIC) ====================
resource "aws_instance" "flask_server" {
  ami                    = data.aws_ami.amazon_linux_2.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.flask_key.key_name
  vpc_security_group_ids = [aws_security_group.public_sg.id]
  associate_public_ip_address = true

  user_data = base64encode(templatefile("${path.module}/flask_server_startup.sh", {
    s3_bucket = aws_s3_bucket.image_bucket.bucket
  }))

  tags = {
    Name = "${var.project_name}-flask-server"
  }
}

# ==================== LAMBDA FUNCTION ====================
resource "aws_lambda_function" "image_processor" {
  function_name = "${var.project_name}-processor-${local.suffix}"
  role         = aws_iam_role.lambda_role.arn
  handler      = "index.lambda_handler"
  runtime      = "python3.9"
  timeout      = var.lambda_timeout
  memory_size  = var.lambda_memory

  filename = "lambda_function.zip"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      EC2_FLASK_URL  = "http://${aws_instance.flask_server.public_ip}:5000"
      S3_BUCKET      = aws_s3_bucket.image_bucket.bucket
    }
  }

  depends_on = [aws_iam_role_policy.lambda_policy]
}

# ==================== LAMBDA ARCHIVE ====================
data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda_function.zip"

  source {
    content  = file("${path.module}/lambda_function.py")
    filename = "index.py"
  }
}
