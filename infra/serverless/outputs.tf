output "frontend_url" {
  description = "Public HTTPS URL of the frontend."
  value       = module.frontend.url
}

output "frontend_bucket" {
  description = "Bucket where the built frontend (frontend/dist) is uploaded."
  value       = module.frontend.bucket_name
}

output "backend_url" {
  description = "Public HTTPS URL of the backend."
  value       = module.api.url
}

output "ecr_repository_url" {
  description = "Where to push the backend Docker image."
  value       = module.api.ecr_repository_url
}
