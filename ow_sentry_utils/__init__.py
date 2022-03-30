def traces_sampler(context):
    if context['transaction_context']['op'] == 'celery.task':
        return 0.0
    if context.get('asgi_scope') and context['asgi_scope']['path'].startswith(
        ['/controller/checksum/', '/api/v1/monitoring/device/']
    ):
        return 0.0001
    return 0.001
