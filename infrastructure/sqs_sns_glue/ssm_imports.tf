data "aws_ssm_parameter" "utils_layer" {
  name = "/${var.app_name}/${var.ssm_source_stage}/lambda/layers/utils/arn"
}

data "aws_ssm_parameter" "msg_glue_layer" {
  name = "/${var.app_name}/${var.ssm_source_stage}/lambda/layers/msg_glue/arn"
}

