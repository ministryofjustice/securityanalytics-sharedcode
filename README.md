[![CircleCI](https://circleci.com/gh/ministryofjustice/securityanalytics-sharedcode.svg?style=svg)](https://circleci.com/gh/ministryofjustice/securityanalytics-sharedcode)

# utils

## json_serialisation

Extends the standard json.dumps method to use a custom serialiser e.g. for decimals, dates and datetimes, and sets

## lambda_decorators

This module provides decorators to annotate methods with in order to simplify implementing Lambda functions.

### ssm_parameters

This decorator takes a list of ssm parameter names, and an ssm client. It will retreive those parameters and expose them by adding an "ssm_params" dictionary to the event passed to your Lambda.

### forward_exceptions_to_dlq

AWS Lambda will only use the dead letter queue configured if the Lambda is called asynchronously e.g. not SQS or DynamoDB streams. In such situations you might still want exceptions to sent to a dead letter queue. This decorator takes an sqs client and sqs queue url, the method it is applied to will have any exceptions caught and sent over sqs.

### suppress_exceptions

This decorator will catch exceptions and use the supplied return value either returning it, or if it is an exception, throwing it instead of the original exception. This is useful for when a lambda is part of an api gateway and internal errors should not be sent to the client

### async_handler

This decorator does two things. The first is to ensure that your lambda is running on an event loop, enabling you to write async lambda code. 

The other thing that it attempts to do is to ensure that Xray is setup properly. Unfortunately xray and aiboto3 do not seem to play well together and that feature is currently disabled.

### dump_json_body & load_json_body

These two decorators can be used if the "body" of event received, or object returned by the lambda are to be (de)serialised as json. This saves the developer having to add (de)serialisation manually to each lambda.

## objectify_dict

This util uses a named tuple to convert a dictionary into a form that gives object like access. This enables prettier looking code, but at some runtime overhead.

## scan_results

This util should be moved to the task execution project. It is used to report results to elastic search for indexing and is used in the results parser lambda's for each scan.

## time_utils

Hack class to get RFC 3339 style timestamp strings from python datetime objects.

# test_utils

## resetting_mocks

Decorator that will reset the provided mocks after a test completes.

## serialise_mocks

Changes the behaviour of serialisation of mocks.

## coroutine_of, future_of, future_exception

These util methods are useful when mocking async code.

# lambda_templates

## LazyInitLambda

This is a class that implements a lazy loading lifecycle for object orientated lambda functions. This makes testing and writing lambda functions simpler and is used by the scanning framework. It is envisioned that there will be many subclasses of this abstract type.

# dlq_recorder

This the the lambda code that picks up new dead letters and reports them to the elastic search via the input queue of that project.

# aws_messaging_glue

Since AWS doesn't have a way to subscribe SQS to SNS in the same way you can SNS to SQS. This lambda provides that capability and is used with the delay queue in the scan initiator in the task execution project.