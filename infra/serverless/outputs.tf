output "frontend_url" {
  description = "Public HTTPS URL of the frontend."
  value       = module.frontend.url
}

output "frontend_bucket" {
  description = "Bucket where the built frontend (frontend/dist) is uploaded."
  value       = module.frontend.bucket_name
}
