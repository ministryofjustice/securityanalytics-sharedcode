resource "aws_lambda_function" "dlq_recorder" {
  depends_on       = [aws_iam_role_policy_attachment.dlq_recorder_perms]
  function_name    = "${terraform.workspace}-${var.app_name}-${var.recorder_name}"
  handler          = "dlq_recorder.dlq_recorder.save_dead_letter"
  role             = aws_iam_role.dlq_recorder.arn
  runtime          = "python3.7"
  filename         = "${path.module}/empty.zip"
  source_code_hash = filebase64sha256("${path.module}/empty.zip")

  layers = [
    data.aws_ssm_parameter.utils_layer.value,
    data.aws_ssm_parameter.dlq_recorder_layer.value,
  ]

  tracing_config {
    mode = var.use_xray ? "Active" : "PassThrough"
  }

  environment {
    variables = {
      REGION        = var.aws_region
      STAGE         = terraform.workspace
      APP_NAME      = var.app_name
      USE_XRAY      = var.use_xray
      DLQ_NAME      = var.recorder_name
      S3_BUCKET     = var.s3_bucket
      S3_KEY_PREFIX = var.s3_key_prefix
    }
  }

  tags = {
    workspace = terraform.workspace
    app_name  = var.app_name
  }
}

resource "aws_lambda_permission" "dlq_invoke" {
  statement_id  = "AllowExecutionFromSQS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dlq_recorder.function_name
  principal     = "sqs.amazonaws.com"
  source_arn    = aws_sqs_queue.dlq.arn
}

resource "aws_lambda_event_source_mapping" "dlq_trigger" {
  depends_on       = [aws_lambda_permission.dlq_invoke]
  event_source_arn = aws_sqs_queue.dlq.arn
  function_name    = aws_lambda_function.dlq_recorder.arn
  enabled          = true
  batch_size       = 10
}

data "aws_iam_policy_document" "lambda_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "dlq_recorder_perms" {
  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    # TODO reduce this scope
    resources = ["*"]
  }

  # To enable XRAY trace
  statement {
    effect = "Allow"

    actions = [
      "xray:PutTraceSegments",
      "xray:PutTelemetryRecords",
      "xray:GetSamplingRules",
      "xray:GetSamplingTargets",
      "xray:GetSamplingStatisticSummaries"
    ]

    # TODO make a better bound here
    resources = [
      "*",
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "sqs:DeleteMessage",
      "sqs:ReceiveMessage",
      "sqs:GetQueueAttributes",
    ]

    resources = [aws_sqs_queue.dlq.arn]
  }

  statement {
    effect = "Allow"

    actions = [
      "s3:PutObject",
    ]

    resources = [
      var.s3_bucket_arn,
      "${var.s3_bucket_arn}/*",
    ]
  }
}

resource "aws_iam_role" "dlq_recorder" {
  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json

  tags = {
    app_name  = var.app_name
    workspace = terraform.workspace
  }
}

resource "aws_iam_policy" "dlq_recorder_perms" {
  name   = "${terraform.workspace}-${var.app_name}-${var.recorder_name}"
  policy = data.aws_iam_policy_document.dlq_recorder_perms.json
}

resource "aws_iam_role_policy_attachment" "dlq_recorder_perms" {
  role       = aws_iam_role.dlq_recorder.name
  policy_arn = aws_iam_policy.dlq_recorder_perms.id
}

