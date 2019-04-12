from functools import wraps


def ssm_parameters(ssm_client, *param_names):
    def ssm_p_decorator(handler):
        @wraps(handler)
        def ssm_wrapper(event, context):
            ssm_params = ssm_client.get_parameters(Names=[*param_names])
            event['ssm_params'] = {p['Name']: p['Value'] for p in ssm_params}
            return handler(event, context)
        return ssm_wrapper
    return ssm_p_decorator

