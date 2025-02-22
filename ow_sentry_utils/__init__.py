import re

SENTRY_IGNORE_ERRORS = {
    # The celery autoscaler generates following errors while
    # downscaling workers. The error is generated
    # by the worker that gets terminated due to downscaling.
    # Hence, it is safe to ignore these errors.
    'celery.worker.request': [
        r'Worker exited prematurely: signal 15 \(SIGTERM\) Job:',
        r'Worker exited prematurely: signal 9 \(SIGKILL\) Job:',
        r'Worker exited prematurely: exitcode 15 Job:',
        r'Worker exited prematurely: exitcode 9 Job:',
    ],
    'multiprocessing': [
        (
            r'Process (?:\'|\")ForkPoolWorker-([\d.]+)(?:\'|\") pid:([\d.]+)'
            r' exited with (?:\'|\")signal 9 \(SIGKILL\)(?:\'|\")'
        ),
        (
            r'Process (?:\'|\")ForkPoolWorker-([\d.]+)(?:\'|\") pid:([\d.]+)'
            r' exited with (?:\'|\")signal 15 \(SIGTERM\)(?:\'|\")'
        ),
    ],
    'celery.concurrency.asynpool': [r'Timed out waiting for UP message from '],
    # Daphne throws below error when we restart the service using
    # "supervisorctl restart all". This error gets resolved automatically,
    # hence, we can safely ignore this.
    'daphne.server': [r'Couldn\'t listen on any\:b\'\/opt\/openwisp2\/daphne0\.sock'],
}


def traces_sampler(context):
    if context['transaction_context']['op'] == 'celery.task':
        return 0.0
    if context.get('asgi_scope') and context['asgi_scope']['path'].startswith(
        ('/controller/checksum/', '/api/v1/monitoring/device/', '/api/v1/freeradius/')
    ):
        return 0.0001
    return 0.001


def before_send(event, hint):
    event_logger = event.get('logger', None)
    if event_logger not in SENTRY_IGNORE_ERRORS.keys():
        return event
    # Sentry event contains error message and paramenters
    # required for formatting the error message if the
    # error message contains placeholders.
    # E.g. error_message "Worker exited prematurely: exitcode %d"
    # with error_params "[15]"".
    error_message = event.get('logentry', {}).get('message', '')
    error_params = event.get('logentry', {}).get('params', [])
    for ignore_error in SENTRY_IGNORE_ERRORS[event_logger]:
        # Substitute the placeholders in error_message with their
        # corressponding value in error_params before searching
        # for ignore_error regular expression.
        if re.search(ignore_error, error_message % tuple(error_params)):
            return None
    return event
