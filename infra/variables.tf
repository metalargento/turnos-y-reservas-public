variable "project_name" {
  description = "Name prefix for all resources."
  type        = string
  default     = "turnos-y-reservas"
}

variable "aws_region" {
  description = "AWS region to deploy to."
  type        = string
  default     = "us-east-1"
}

variable "use_fake_credentials" {
  description = "Run offline with fake credentials (plan only, for CI)."
  type        = bool
  default     = false
}

# Secrets: no defaults on purpose. Pass them with TF_VAR_* or a local
# terraform.tfvars (git-ignored). Never commit real values.
variable "secret_key" {
  description = "Backend SECRET_KEY."
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "Backend JWT_SECRET."
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Master password for the RDS PostgreSQL instance."
  type        = string
  sensitive   = true
}

variable "image_tag" {
  description = "Tag of the backend image in ECR."
  type        = string
  default     = "latest"
}

variable "allowed_origins" {
  description = "Frontend origin allowed by CORS (exact URL)."
  type        = string
  default     = "https://example.vercel.app"
}

variable "frontend_url" {
  description = "Frontend URL used for redirects."
  type        = string
  default     = "https://example.vercel.app"
}
