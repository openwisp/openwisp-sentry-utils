import re


SENTRY_IGNORE_ERRORS = {
    'celery.worker.request': [r'Worker exited prematurely: signal 15 (SIGTERM) Job:'],
    'multiprocessing': [
        r'Process \"ForkPoolWorker-2\" pid:([\d.]+) exited with "signal 9 \(SIGKILL\)\"'
    ],
}


def traces_sampler(context):
    if context['transaction_context']['op'] == 'celery.task':
        return 0.0
    if context.get('asgi_scope') and context['asgi_scope']['path'].startswith(
        ['/controller/checksum/', '/api/v1/monitoring/device/']
    ):
        return 0.0001
    return 0.001


def before_send(event, hint):
    event_logger = event.get('logger', None)
    if event_logger not in SENTRY_IGNORE_ERRORS.keys():
        return event
    error_message = event.get('logentry', {}).get('message', '')
    for error in SENTRY_IGNORE_ERRORS[event_logger]:
        if re.match(error, error_message):
            return None
