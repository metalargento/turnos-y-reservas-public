variable "name" {
  description = "Name prefix for the resources."
  type        = string
}

variable "image_tag" {
  description = "Tag of the Docker image in ECR to run."
  type        = string
  default     = "latest"
}

variable "environment" {
  description = "Non-secret environment variables for the backend."
  type        = map(string)
}

variable "secret_names" {
  description = "Names of the secret variables (kept separate so keys are known at plan time)."
  type        = list(string)
}

variable "secrets" {
  description = "Secret values, keyed by name."
  type        = map(string)
  sensitive   = true
}

variable "subnet_ids" {
  description = "Private subnets for the VPC connector."
  type        = list(string)
}

variable "security_group_id" {
  description = "Security group for the VPC connector."
  type        = string
}
