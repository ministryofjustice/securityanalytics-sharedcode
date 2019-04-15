from functools import wraps


def ssm_parameters(ssm_client, *param_names):
    def decorator(handler):
        @wraps(handler)
        def wrapper(event, context):
            ssm_params = ssm_client.get_parameters(Names=[*param_names])
            event['ssm_params'] = {p['Name']: p['Value'] for p in ssm_params}
            return handler(event, context)
        return wrapper
    return decorator


def suppress_exceptions(return_val):
    def decorator(handler):
        @wraps(handler)
        def wrapper(event, context):
            try:
                return handler(event, context)
            except Exception as e:
                print(e)
                return return_val
        return wrapper
    return decorator
