from functools import wraps
import traceback
from utils.json_serialisation import dumps


def ssm_parameters(ssm_client, *param_names):
    def decorator(handler):
        @wraps(handler)
        def wrapper(event, context):
            ssm_params = ssm_client.get_parameters(Names=[*param_names])['Parameters']
            print(f"Retrieved SSM Parameters {dumps(ssm_params)}")
            event['ssm_params'] = {p['Name']: p['Value'] for p in ssm_params}
            return handler(event, context)
        return wrapper
    return decorator


def suppress_exceptions(return_function):
    def decorator(handler):
        @wraps(handler)
        def wrapper(event, context):
            try:
                return handler(event, context)
            except Exception as e:
                print(e)
                traceback.print_exc(e)
                return return_function(e)
        return wrapper
    return decorator
