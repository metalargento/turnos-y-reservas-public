# API: the FastAPI backend as a Lambda function behind API Gateway.
#   ECR          -> private registry where the Docker image is stored
#   Lambda       -> runs the image only while a request is being served
#   API Gateway  -> public HTTPS URL, forwards every request to the function
# There is no VPC: the database is external (Supabase) and reached over the
# internet with TLS. The function runs outside a VPC, so there is no NAT cost.
#
# The image is the same Dockerfile used by the other variants. To run it on
# Lambda it needs the AWS Lambda Web Adapter, which translates API Gateway
# events into plain HTTP calls to the app on port 8080 (no code change).

resource "aws_ecr_repository" "this" {
  name                 = var.name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# --- IAM ---------------------------------------------------------------------
# The function only needs to write its own logs.

data "aws_iam_policy_document" "lambda_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "this" {
  name_prefix        = "${var.name}-fn-"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json
}

resource "aws_iam_role_policy_attachment" "logs" {
  role       = aws_iam_role.this.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- Function ----------------------------------------------------------------

resource "aws_cloudwatch_log_group" "function" {
  name              = "/aws/lambda/${var.name}"
  retention_in_days = 14
}

resource "aws_lambda_function" "this" {
  function_name = var.name
  role          = aws_iam_role.this.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.this.repository_url}:${var.image_tag}"
  memory_size   = var.memory_mb
  timeout       = var.timeout_seconds

  environment {
    variables = merge(var.environment, var.secrets, {
      # Lambda Web Adapter settings: where the app listens and its health path.
      AWS_LWA_PORT                 = "8080"
      AWS_LWA_READINESS_CHECK_PATH = "/health"
    })
  }

  depends_on = [
    aws_iam_role_policy_attachment.logs,
    aws_cloudwatch_log_group.function,
  ]
}

# --- API Gateway -------------------------------------------------------------
# CORS is handled by the app itself (middleware/cors_policy.py), so it is not
# configured here. Throttling replaces the in-memory rate limit, which cannot
# work when every Lambda instance has its own memory.

resource "aws_apigatewayv2_api" "this" {
  name          = var.name
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "this" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.this.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.this.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_rate_limit  = var.throttle_rate
    throttling_burst_limit = var.throttle_burst
  }
}

resource "aws_lambda_permission" "api" {
  statement_id  = "AllowApiGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}
