# If this bucket already exists in your account, import it before applying:
#   terraform import aws_s3_bucket.assets daily-office-app-assets
resource "aws_s3_bucket" "assets" {
  bucket = "daily-office-app-assets"

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = "daily-office-app-assets"
  }
}

resource "aws_s3_bucket_versioning" "assets" {
  bucket = aws_s3_bucket.assets.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "assets" {
  bucket = aws_s3_bucket.assets.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "assets_bucket_name" {
  description = "Name of the S3 assets bucket."
  value       = aws_s3_bucket.assets.id
}

output "assets_bucket_arn" {
  description = "ARN of the S3 assets bucket."
  value       = aws_s3_bucket.assets.arn
}
