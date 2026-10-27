variable "name" {
  description = "Name prefix for the API resources."
  type        = string
}

variable "image_tag" {
  description = "Tag of the backend image in ECR."
  type        = string
}

variable "environment" {
  description = "Non-secret environment variables for the backend."
  type        = map(string)
}

variable "secrets" {
  description = "Secret environment variables for the backend (SECRET_KEY, JWT_SECRET, DATABASE_URL)."
  type        = map(string)
  sensitive   = true
}

variable "memory_mb" {
  description = "Memory of the function. CPU scales with it."
  type        = number
  default     = 1024
}

variable "timeout_seconds" {
  description = "Maximum duration of one request."
  type        = number
  default     = 15
}

variable "throttle_rate" {
  description = "Steady requests per second allowed by the API."
  type        = number
  default     = 20
}

variable "throttle_burst" {
  description = "Short burst of requests allowed above the steady rate."
  type        = number
  default     = 40
}
