resource "aws_ssm_parameter" "utils_layer" {
  name        = "/${var.app_name}/${terraform.workspace}/lambda/layers/utils/arn"
  description = "The arn of the lambda layer"
  type        = "String"
  value       = "${aws_lambda_layer_version.lambda_layer.arn}"
  overwrite   = "true"

  tags {
    app_name  = "${var.app_name}"
    workspace = "${terraform.workspace}"
  }
}
