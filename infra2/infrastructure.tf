#############################################
# Backend setup
#############################################

terraform {
  backend "s3" {
    # This is configured using the -backend-config parameter with 'terraform init'
    bucket         = ""
    dynamodb_table = "sec-an-terraform-locks"
    key            = "shared_code-demo/terraform.tfstate"
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
}

module "DELETEME" {
   source = "../infrastructure/dead_letter_recorder"
   app_name = var.app_name
   aws_region=var.aws_region
   account_id = var.account_id 
   ssm_source_stage = local.ssm_source_stage
   recorder_name = "test_dlq_recorder"
   s3_bucket = "sallyauntfanny"
   s3_bucket_arn = "arn:aws:s3:::sallyauntfanny"
   s3_key_prefix = "fun/fanta"
   source_arn = "*"
}
