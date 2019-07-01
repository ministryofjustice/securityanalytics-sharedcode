resource "aws_lambda_function" "sqs_sns_glue" {
  depends_on = [aws_iam_role_policy_attachment.scan_initiator_perms]
  function_name    = "${terraform.workspace}-${var.app_name}-${var.glue_name}"
  handler          = "aws_messaging_glue.sqs_sns_glue.forward_messages"
  role             = aws_iam_role.sqs_sns_glue.arn
  runtime          = "python3.7"
  filename         = "${path.module}/empty.zip"
  source_code_hash = filebase64sha256("${path.module}/empty.zip")

  layers = [
    data.aws_ssm_parameter.utils_layer.value,
    data.aws_ssm_parameter.msg_glue_layer.value,
  ]

  environment {
    variables = {
      REGION   = var.aws_region
      STAGE    = terraform.workspace
      APP_NAME = var.app_name
      TOPIC    = var.sns_topic_arn
    }
  }

  tags = {
    workspace = terraform.workspace
    app_name  = var.app_name
  }
}

resource "aws_lambda_permission" "glue_invoke" {
  statement_id  = "AllowExecutionFromSQS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sqs_sns_glue.function_name
  principal     = "sqs.amazonaws.com"
  source_arn    = var.sqs_queue_arn
}

resource "aws_lambda_event_source_mapping" "glue_trigger" {
  depends_on = [aws_lambda_permission.glue_invoke]
  event_source_arn = var.sqs_queue_arn
  function_name    = aws_lambda_function.sqs_sns_glue.arn
  enabled          = true
  batch_size       = 10
}

data "aws_iam_policy_document" "lambda_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    effect = "Allow"

    principals {
      type = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "sqs_sns_glue_perms" {
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

  statement {
    effect = "Allow"

    actions = [
      "sqs:DeleteMessage",
      "sqs:ReceiveMessage",
      "sqs:GetQueueAttributes",
    ]

    resources = [var.sqs_queue_arn]
  }

  statement {
    effect = "Allow"

    actions = [
      "sns:Publish",
    ]

    resources = [var.sns_topic_arn]
  }
}

resource "aws_iam_role" "sqs_sns_glue" {
  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json

  tags = {
    app_name  = var.app_name
    workspace = terraform.workspace
  }
}

resource "aws_iam_policy" "scan_initiator_perms" {
  name   = "${terraform.workspace}-${var.app_name}-${var.glue_name}"
  policy = data.aws_iam_policy_document.sqs_sns_glue_perms.json
}

resource "aws_iam_role_policy_attachment" "scan_initiator_perms" {
  role       = aws_iam_role.sqs_sns_glue.name
  policy_arn = aws_iam_policy.scan_initiator_perms.id
}

