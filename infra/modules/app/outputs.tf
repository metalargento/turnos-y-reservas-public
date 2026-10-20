output "service_url" {
  description = "Public HTTPS URL of the backend."
  value       = "https://${aws_apprunner_service.this.service_url}"
}

output "ecr_repository_url" {
  description = "Where to push the Docker image."
  value       = aws_ecr_repository.this.repository_url
}
