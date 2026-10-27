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
