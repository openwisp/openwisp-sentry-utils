from unittest import TestCase

from ow_sentry_utils import SENTRY_IGNORE_ERRORS, before_send, traces_sampler


class TestBeforeSend(TestCase):
    def _event(self, logger, message, params=None):
        return {
            'logger': logger,
            'logentry': {'message': message, 'params': params or []},
        }

    def test_event_from_other_logger_is_kept(self):
        event = self._event(
            'django.request', 'Worker exited prematurely: signal 9 (SIGKILL) Job: 1'
        )
        self.assertIs(before_send(event, {}), event)

    def test_event_without_logger_is_kept(self):
        event = {'message': 'Internal Server Error'}
        self.assertIs(before_send(event, {}), event)

    def test_ignored_error_is_dropped(self):
        for logger, message in [
            (
                'celery.worker.request',
                'Worker exited prematurely: signal 15 (SIGTERM) Job: 3.',
            ),
            ('celery.worker.request', 'Worker exited prematurely: exitcode 9 Job: 7.'),
            (
                'multiprocessing',
                "Process 'ForkPoolWorker-2' pid:41 exited with 'signal 9 (SIGKILL)'",
            ),
            (
                'celery.concurrency.asynpool',
                'Timed out waiting for UP message from <Process 1>',
            ),
            ('daphne.server', "Couldn't listen on any:b'/opt/openwisp2/daphne0.sock'"),
            ('paramiko.transport', 'Socket exception: Connection reset by peer'),
        ]:
            with self.subTest(logger=logger, message=message):
                self.assertIsNone(before_send(self._event(logger, message), {}))

    def test_params_are_substituted_before_matching(self):
        event = self._event(
            'celery.worker.request',
            'Worker exited prematurely: exitcode %d Job: %s.',
            [15, 4],
        )
        self.assertIsNone(before_send(event, {}))

    def test_other_error_from_ignored_logger_is_kept(self):
        event = self._event(
            'celery.worker.request', 'Worker exited prematurely: exitcode 1 Job: 4.'
        )
        self.assertIs(before_send(event, {}), event)

    def test_added_ignore_pattern_is_used(self):
        SENTRY_IGNORE_ERRORS['custom.logger'] = [r'^Expected noise$']
        self.addCleanup(SENTRY_IGNORE_ERRORS.pop, 'custom.logger')
        self.assertIsNone(
            before_send(self._event('custom.logger', 'Expected noise'), {})
        )
        event = self._event('custom.logger', 'Real problem')
        self.assertIs(before_send(event, {}), event)


class TestTracesSampler(TestCase):
    def test_celery_tasks_are_not_sampled(self):
        context = {'transaction_context': {'op': 'celery.task'}}
        self.assertEqual(traces_sampler(context), 0.0)

    def test_frequent_device_views_are_rarely_sampled(self):
        for path in [
            '/controller/checksum/abc/',
            '/api/v1/monitoring/device/abc/',
            '/api/v1/freeradius/authorize/',
        ]:
            with self.subTest(path=path):
                context = {
                    'transaction_context': {'op': 'http.server'},
                    'asgi_scope': {'path': path},
                }
                self.assertEqual(traces_sampler(context), 0.0001)

    def test_other_transactions_use_the_default_rate(self):
        for context in [
            {
                'transaction_context': {'op': 'http.server'},
                'asgi_scope': {'path': '/admin/'},
            },
            {'transaction_context': {'op': 'http.server'}},
        ]:
            with self.subTest(context=context):
                self.assertEqual(traces_sampler(context), 0.001)
