variable "aws_region" {
  type=string
}

variable "app_name" {
  type=string
}

variable "account_id" {
  type=string
}

variable "ssm_source_stage" {
  type = string
}

variable "use_xray" {
  type = string
  description = "Whether to instrument lambdas"
  default = true
}

variable "recorder_name" {
  type=string
}

variable "s3_bucket" {
  type = string
}

variable "s3_bucket_arn" {
  type = string
}

variable "s3_key_prefix" {
  type = string
}

variable "source_arn" {
  type = string
  description = "The arn of the source for the DLQ e.g. a lambda"
}