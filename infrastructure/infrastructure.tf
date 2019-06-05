#############################################
# Backend setup
#############################################

terraform {
  backend "s3" {
    # This is configured using the -backend-config parameter with 'terraform init'
    bucket         = ""
    dynamodb_table = "sec-an-terraform-locks"
    key            = "shared_code/terraform.tfstate"
    region         = "eu-west-2" # london
  }
}

#############################################
# Variables used across the whole application
#############################################

variable "aws_region" {
  default = "eu-west-2" # london
}

# Set this variable with your app.auto.tfvars file or enter it manually when prompted
variable "app_name" {
}

variable "account_id" {
}

variable "ssm_source_stage" {
  default = "DEFAULT"
}

variable "known_deployment_stages" {
  type    = list(string)
  default = ["dev", "qa", "prod"]
}

provider "aws" {
  region = var.aws_region

  # N.B. To support all authentication use cases, we expect the local environment variables to provide auth details.
  allowed_account_ids = [var.account_id]
}

#############################################
# Resources
#############################################

locals {
  # When a build is done as a user locally, or when building a stage e.g. dev/qa/prod we use
  # the workspace name e.g. progers or dev
  # When the circle ci build is run we override the var.ssm_source_stage to explicitly tell it
  # to use the resources in dev. Change
  ssm_source_stage = var.ssm_source_stage == "DEFAULT" ? terraform.workspace : var.ssm_source_stage

  utils_zip        = "../.generated/${var.app_name}_utils.zip"
  msg_glue_zip     = "../.generated/${var.app_name}_msg_glue.zip"
  dlq_recorder_zip = "../.generated/${var.app_name}_dlq_recorder.zip"
}

data "external" "utils_zip" {
  program = ["python", "../python/package_lambda.py", local.utils_zip, "utils.packaging.config.json", "../Pipfile.lock"]
}

data "external" "msg_glue_zip" {
  program = ["python", "../python/package_lambda.py", "-x", local.msg_glue_zip, "msg_glue.packaging.config.json", "../Pipfile.lock"]
}

data "external" "dlq_recorder_zip" {
  program = ["python", "../python/package_lambda.py", "-x", local.dlq_recorder_zip, "dlq_recorder.packaging.config.json", "../Pipfile.lock"]
}

resource "aws_lambda_layer_version" "utils_layer" {
  description         = "Utils layer with hash ${data.external.utils_zip.result.hash}"
  filename            = local.utils_zip
  layer_name          = "${terraform.workspace}-${var.app_name}-shared-utils"
  compatible_runtimes = ["python3.7"]
}

resource "aws_lambda_layer_version" "msg_glue_layer" {
  description         = "Message glue layer with hash ${data.external.msg_glue_zip.result.hash}"
  filename            = local.msg_glue_zip
  layer_name          = "${terraform.workspace}-${var.app_name}-msg-glue"
  compatible_runtimes = ["python3.7"]
}

resource "aws_lambda_layer_version" "dlq_recorder_layer" {
  description         = "Dead letter queue recorder ${data.external.dlq_recorder_zip.result.hash}"
  filename            = local.dlq_recorder_zip
  layer_name          = "${terraform.workspace}-${var.app_name}-dlq-recorder"
  compatible_runtimes = ["python3.7"]
}
