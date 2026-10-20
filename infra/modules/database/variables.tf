variable "name" {
  description = "Name prefix for the resources."
  type        = string
}

variable "subnet_ids" {
  description = "Private subnets where the database lives."
  type        = list(string)
}

variable "security_group_id" {
  description = "Security group that guards the database."
  type        = string
}

variable "instance_class" {
  description = "RDS instance size (smallest is enough for a demo)."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_name" {
  type    = string
  default = "turnos"
}

variable "db_username" {
  type    = string
  default = "turnos_admin"
}

variable "db_password" {
  type      = string
  sensitive = true
}
