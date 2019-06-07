data "aws_iam_policy_document" "dlq_policy" {
  statement {
    actions = ["sqs:SendMessage"]
    effect  = "Allow"

    principals {
      type        = "AWS"
      identifiers = [var.account_id]
    }

    # Allow the source to send messages
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"

      values = [
        var.source_arn,
      ]
    }

    resources = [aws_sqs_queue.dlq.arn]
  }
}

resource "aws_sqs_queue_policy" "dlq_policy" {
  queue_url = aws_sqs_queue.dlq.id
  policy    = data.aws_iam_policy_document.dlq_policy.json
}

resource "aws_sqs_queue" "dlq" {
  name = "${terraform.workspace}-${var.app_name}-${var.recorder_name}"

  # TODO set settings for e.g. dead letter queue, message retention, and kms master key

  tags = {
    app_name  = var.app_name
    workspace = terraform.workspace
  }
}

