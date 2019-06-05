from functools import wraps
import traceback
from asyncio import get_event_loop
import json
import os
from utils.json_serialisation import dumps
from aws_xray_sdk.core.async_context import AsyncContext
from aws_xray_sdk.core import xray_recorder


def ssm_parameters(ssm_client, *param_names):
    def decorator(handler):
        @wraps(handler)
        def wrapper(event, context):
            loop = get_event_loop()
            task = loop.create_task(ssm_client.get_parameters(Names=[*param_names]))
            ssm_params = loop.run_until_complete(task)['Parameters']
            print(f"Retrieved SSM Parameters {dumps(ssm_params)}")
            event['ssm_params'] = {p['Name']: p['Value'] for p in ssm_params}
            return handler(event, context)
        return wrapper
    return decorator


def suppress_exceptions(return_value):
    def decorator(handler):
        @wraps(handler)
        def wrapper(event, context):
            try:
                return handler(event, context)
            except Exception as e:
                print(e)
                traceback.print_exc()
                if isinstance(return_value, Exception):
                    raise return_value from None
                else:
                    return return_value
        return wrapper
    return decorator


def async_handler():
    def decorator(handler):
        # It is a little hard to get lambdas, asyncio, and xray all working together
        # asyncio + xray => we have to configure the recorder to use the async context.
        # Lambda configures xray to use the LambdaContext instead of AsyncContext
        # That context is special e.g. it will deny you creating a new segment and it
        # will have the trace entity pre-populated.
        # This hack will obtain the original trace entity from the lambda context into the
        # async context.
        # N.B. We are losing features of the LambdaContext in the process e.g. no check against
        # beginning another segment. The documentation for
        # aws_xray_sdk.core.lambda_launcher.LambdaContext._refresh_context
        # seems to suggest that LambdaContext also guards against resource leaks in the lambda
        # context (not xray recorder context!)
        # TODO probably best to implement an AsyncLambdaContext context that combines the
        # behaviour of LambdaContext and AsyncContext. Better still raise an issue against xray
        # libraries
        async def set_context(future):
            service_name = os.environ["AWS_LAMBDA_FUNCTION_NAME"]
            current = xray_recorder.current_segment()
            xray_context = AsyncContext()
            xray_context.set_trace_entity(current)
            xray_recorder.configure(service=service_name, context=xray_context)
            return await future

        @wraps(handler)
        def wrapper(event, context):
            context.loop = get_event_loop()
            invoke = handler(event, context)
            # Terraform true and false are 0/1
            if should_xray():
                from aws_xray_sdk.core import patch_all
                patch_all()
                invoke = set_context(invoke)
            return context.loop.run_until_complete(invoke)

        def should_xray():
            return "USE_XRAY" in os.environ and os.environ["USE_XRAY"].lower() in {"true", "1"}

        return wrapper
    return decorator


def dump_json_body(handler):
    @wraps(handler)
    def wrapper(event, context):
        response = handler(event, context)
        if 'body' in response:
            try:
                response['body'] = dumps(response['body'])
            except Exception as exception:
                return {'statusCode': 500, 'body': str(exception)}
        return response
    return wrapper


def load_json_body(handler):
    @wraps(handler)
    def wrapper(event, context):
        if isinstance(event.get('body'), str):
            try:
                event['body'] = json.loads(event['body'])
                # TODO add the right exception type here
            except:
                return {'statusCode': 400, 'body': 'BAD REQUEST'}
        return handler(event, context)

    return wrapper
