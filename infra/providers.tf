# By default the provider talks to real AWS using your own credentials.
# Set use_fake_credentials = true to run `terraform plan` offline (used in CI):
# no AWS account is needed and nothing is ever created.
provider "aws" {
  region = var.aws_region

  access_key = var.use_fake_credentials ? "fake" : null
  secret_key = var.use_fake_credentials ? "fake" : null

  skip_credentials_validation = var.use_fake_credentials
  skip_requesting_account_id  = var.use_fake_credentials
  skip_metadata_api_check     = var.use_fake_credentials

  default_tags {
    tags = {
      Project   = var.project_name
      ManagedBy = "terraform"
    }
  }
}
