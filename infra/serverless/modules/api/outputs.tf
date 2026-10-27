output "url" {
  description = "Public HTTPS URL of the backend."
  value       = aws_apigatewayv2_api.this.api_endpoint
}

output "ecr_repository_url" {
  description = "Where to push the Docker image."
  value       = aws_ecr_repository.this.repository_url
}
