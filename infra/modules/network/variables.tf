variable "name" {
  description = "Name prefix for the resources."
  type        = string
}

variable "vpc_cidr" {
  description = "IP range of the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Two availability zones (RDS needs subnets in at least two)."
  type        = list(string)
}
