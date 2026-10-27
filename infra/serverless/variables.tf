variable "project_name" {
  description = "Name prefix for all resources."
  type        = string
  default     = "turnos-y-reservas-sls"
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

variable "database_url" {
  description = "PostgreSQL connection string (Supabase pooler, port 6543)."
  type        = string
  sensitive   = true
}

variable "image_tag" {
  description = "Tag of the backend image in ECR."
  type        = string
  default     = "latest"
}
