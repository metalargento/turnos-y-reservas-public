output "backend_url" {
  description = "Public HTTPS URL of the backend."
  value       = module.app.service_url
}

output "ecr_repository_url" {
  description = "Where to push the backend Docker image."
  value       = module.app.ecr_repository_url
}

output "database_address" {
  description = "Private hostname of the PostgreSQL database."
  value       = module.database.address
}
