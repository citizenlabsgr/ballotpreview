"""
Quart version of Bugsnag's Flask support.

Reference: https://github.com/bugsnag/bugsnag-python/blob/master/bugsnag/flask/__init__.py
"""

import bugsnag
import quart
from bugsnag.wsgi import request_path


def add_quart_request_to_notification(notification):
    if not quart.request:
        return

    if notification.context is None:
        notification.context = "%s %s" % (
            quart.request.method,
            request_path(quart.request.environ),
        )

    if "id" not in notification.user:
        notification.set_user(id=quart.request.remote_addr)
    notification.add_tab("session", dict(quart.session))
    notification.add_tab("environment", dict(quart.request.environ))
    notification.add_tab(
        "request",
        {
            "url": quart.request.base_url,
            "headers": dict(quart.request.headers),
            "params": dict(quart.request.form),
            "data": quart.request.get_json(silent=True)
            or dict(body=quart.request.data),
        },
    )


def handle_exceptions(app):
    middleware = bugsnag.configure().internal_middleware
    bugsnag.configure().runtime_versions["quart"] = quart.__version__
    middleware.before_notify(add_quart_request_to_notification)
    quart.got_request_exception.connect(__log_exception, app)
    quart.request_started.connect(__track_session, app)


def __log_exception(sender, exception, **extra):  # pylint: disable=unused-argument
    bugsnag.auto_notify(
        exception,
        severity_reason={
            "type": "unhandledExceptionMiddleware",
            "attributes": {"framework": "Quart"},
        },
    )


def __track_session(sender, **extra):  # pylint: disable=unused-argument
    if bugsnag.configuration.auto_capture_sessions:
        bugsnag.start_session()
