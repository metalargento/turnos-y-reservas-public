output "url" {
  description = "Public HTTPS URL of the frontend."
  value       = "https://${aws_cloudfront_distribution.this.domain_name}"
}

output "bucket_name" {
  description = "Bucket where the built frontend is uploaded."
  value       = aws_s3_bucket.this.bucket
}
