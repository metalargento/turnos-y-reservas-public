# App: runs the backend container on AWS App Runner.
#   ECR            -> private registry where the Docker image is stored
#   Secrets Manager -> holds SECRET_KEY, JWT_SECRET, DATABASE_URL (never in code)
#   App Runner     -> pulls the image, runs it, gives it an HTTPS URL
#   VPC connector  -> lets the container reach the private database

resource "aws_ecr_repository" "this" {
  name                 = var.name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# --- Secrets -----------------------------------------------------------------

resource "aws_secretsmanager_secret" "this" {
  for_each = toset(var.secret_names)

  name                    = "${var.name}/${each.key}"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "this" {
  for_each = toset(var.secret_names)

  secret_id     = aws_secretsmanager_secret.this[each.key].id
  secret_string = var.secrets[each.key]
}

# --- IAM ---------------------------------------------------------------------
# Two roles: one so App Runner can pull the image, one so the running
# container can read its secrets.

data "aws_iam_policy_document" "build_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["build.apprunner.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecr_access" {
  name_prefix        = "${var.name}-ecr-"
  assume_role_policy = data.aws_iam_policy_document.build_trust.json
}

resource "aws_iam_role_policy_attachment" "ecr_access" {
  role       = aws_iam_role.ecr_access.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

data "aws_iam_policy_document" "tasks_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["tasks.apprunner.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "instance" {
  name_prefix        = "${var.name}-instance-"
  assume_role_policy = data.aws_iam_policy_document.tasks_trust.json
}

data "aws_iam_policy_document" "read_secrets" {
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [for s in aws_secretsmanager_secret.this : s.arn]
  }
}

resource "aws_iam_role_policy" "read_secrets" {
  name   = "read-secrets"
  role   = aws_iam_role.instance.id
  policy = data.aws_iam_policy_document.read_secrets.json
}

# --- Service -----------------------------------------------------------------

resource "aws_apprunner_vpc_connector" "this" {
  vpc_connector_name = var.name
  subnets            = var.subnet_ids
  security_groups    = [var.security_group_id]
}

resource "aws_apprunner_service" "this" {
  service_name = var.name

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.ecr_access.arn
    }

    image_repository {
      image_identifier      = "${aws_ecr_repository.this.repository_url}:${var.image_tag}"
      image_repository_type = "ECR"

      image_configuration {
        port                          = "8080"
        runtime_environment_variables = var.environment
        runtime_environment_secrets = {
          for name, secret in aws_secretsmanager_secret.this : name => secret.arn
        }
      }
    }

    auto_deployments_enabled = false
  }

  instance_configuration {
    cpu               = "256"
    memory            = "512"
    instance_role_arn = aws_iam_role.instance.arn
  }

  network_configuration {
    egress_configuration {
      egress_type       = "VPC"
      vpc_connector_arn = aws_apprunner_vpc_connector.this.arn
    }
  }

  health_check_configuration {
    protocol = "HTTP"
    path     = "/health"
  }

  depends_on = [aws_iam_role_policy_attachment.ecr_access]
}
