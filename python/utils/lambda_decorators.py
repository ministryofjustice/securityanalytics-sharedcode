from functools import wraps
import traceback
from asyncio import get_event_loop
import json
from utils.json_serialisation import dumps


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


def async_handler(handler):
    @wraps(handler)
    def wrapper(event, context):
        context.loop = get_event_loop()
        return context.loop.run_until_complete(handler(event, context))
    return wrapper


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
