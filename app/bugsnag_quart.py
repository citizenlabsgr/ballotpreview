"""
Quart version of Bugsnag's Flask support.

Reference: https://github.com/bugsnag/bugsnag-python/blob/master/bugsnag/flask/__init__.py
"""

# pylint: disable=unused-argument

from importlib.metadata import version

import bugsnag
import quart
from bugsnag.wsgi import request_path


def add_quart_request_to_notification(notification):  # pragma: no cover
    if not quart.request:
        return

    if notification.context is None:
        notification.context = f"{quart.request.method} {request_path(quart.request.environ)}"  # type: ignore

    if "id" not in notification.user:
        notification.set_user(id=quart.request.remote_addr)
    notification.add_tab("session", dict(quart.session))
    notification.add_tab(
        "request",
        {
            "url": quart.request.base_url,
            "headers": dict(quart.request.headers),
        },
    )


def handle_exceptions(app):
    middleware = bugsnag.configure().internal_middleware
    bugsnag.configure().runtime_versions["quart"] = version("quart")
    middleware.before_notify(add_quart_request_to_notification)
    quart.got_request_exception.connect(_log_exception, app)
    quart.request_started.connect(_track_session, app)


def _log_exception(sender, exception, **extra):  # pragma: no cover
    bugsnag.auto_notify(
        exception,
        severity_reason={
            "type": "unhandledExceptionMiddleware",
            "attributes": {"framework": "Quart"},
        },
    )


def _track_session(sender, **extra):
    if bugsnag.configuration.auto_capture_sessions:
        bugsnag.start_session()
