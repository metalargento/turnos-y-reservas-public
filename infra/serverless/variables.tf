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
