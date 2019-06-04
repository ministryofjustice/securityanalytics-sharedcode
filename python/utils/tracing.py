# enables x-ray tracing, returns the recorder which can be used to add subsegments
def create_trace_recorder(service_name):
    from aws_xray_sdk.core.async_context import AsyncContext
    from aws_xray_sdk.core import xray_recorder
    xray_recorder.configure(service=service_name, context=AsyncContext())
    from aws_xray_sdk.core import patch_all

    patch_all()
