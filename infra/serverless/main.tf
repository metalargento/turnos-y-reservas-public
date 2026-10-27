# Serverless variant of the deployment (alternative to ../ which uses App Runner).
# State is local by default. To keep it remote, enable the block below and
# create the bucket first (versioned and encrypted):
#
# terraform {
#   backend "s3" {
#     bucket       = "<your-state-bucket>"
#     key          = "turnos-y-reservas/serverless.tfstate"
#     region       = "us-east-1"
#     encrypt      = true
#     use_lockfile = true
#   }
# }

module "frontend" {
  source = "./modules/frontend"

  name = var.project_name
}

module "api" {
  source = "./modules/api"

  name      = var.project_name
  image_tag = var.image_tag

  environment = {
    APP_ENV         = "production"
    ALLOWED_ORIGINS = module.frontend.url
    FRONTEND_URL    = module.frontend.url
  }

  secrets = {
    SECRET_KEY   = var.secret_key
    JWT_SECRET   = var.jwt_secret
    DATABASE_URL = var.database_url
  }
}
