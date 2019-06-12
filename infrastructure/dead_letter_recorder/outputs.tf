output "arn" {
  value = aws_sqs_queue.dlq.arn
}

output "url" {
  value = aws_sqs_queue.dlq.id
}

output "name" {
  value = aws_sqs_queue.dlq.name
}