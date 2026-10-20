locals {
  # Fixed zones so `plan` works offline (looking them up would need AWS access).
  availability_zones = ["${var.aws_region}a", "${var.aws_region}b"]
}

module "network" {
  source = "./modules/network"

  name               = var.project_name
  availability_zones = local.availability_zones
}

module "database" {
  source = "./modules/database"

  name              = var.project_name
  subnet_ids        = module.network.private_subnet_ids
  security_group_id = module.network.db_security_group_id
  db_password       = var.db_password
}

module "app" {
  source = "./modules/app"

  name              = var.project_name
  subnet_ids        = module.network.private_subnet_ids
  security_group_id = module.network.app_security_group_id
  image_tag         = var.image_tag

  environment = {
    APP_ENV         = "production"
    ALLOWED_ORIGINS = var.allowed_origins
    FRONTEND_URL    = var.frontend_url
  }

  secret_names = ["SECRET_KEY", "JWT_SECRET", "DATABASE_URL"]
  secrets = {
    SECRET_KEY   = var.secret_key
    JWT_SECRET   = var.jwt_secret
    DATABASE_URL = "postgresql://${module.database.db_username}:${urlencode(var.db_password)}@${module.database.address}:5432/${module.database.db_name}"
  }
}
