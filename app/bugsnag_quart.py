"""
Quart version of Bugsnag's Flask support.

Reference: https://github.com/bugsnag/bugsnag-python/blob/master/bugsnag/flask/__init__.py
"""

# pylint: disable=unused-argument

import asyncio
from importlib.metadata import version

import bugsnag
import quart
from bugsnag.breadcrumbs import BreadcrumbType
from bugsnag.legacy import _auto_leave_breadcrumb
from bugsnag.utils import remove_query_from_url
from bugsnag.wsgi import request_path


async def add_quart_request_to_notification(event: bugsnag.Event):  # pragma: no cover
    if not quart.request:
        return

    event.request = quart.request
    if event.context is None:
        event.context = (
            f"{quart.request.method} {request_path(dict(quart.request.scope))}"
        )

    if "id" not in event.user:
        event.set_user(id=quart.request.remote_addr)
    event.add_tab("session", dict(quart.session))
    event.add_tab(
        "request",
        {
            "url": quart.request.base_url,
            "headers": dict(quart.request.headers),
            "params": dict(await quart.request.form),
            "data": await quart.request.get_json(silent=True)
            or dict(body=await quart.request.data),
        },
    )
    if bugsnag.configure().send_environment:
        event.add_tab("environment", dict(quart.request.scope))


def handle_exceptions(app):
    middleware = bugsnag.configure().internal_middleware
    bugsnag.configure().runtime_versions["quart"] = version("quart")

    async def async_add_quart_request_to_notification(event):
        await add_quart_request_to_notification(event)

    def sync_add_quart_request_to_notification(event):
        asyncio.run(async_add_quart_request_to_notification(event))

    middleware.before_notify(sync_add_quart_request_to_notification)
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

    if quart.request:
        _auto_leave_breadcrumb(
            "http request",
            _get_breadcrumb_metadata(quart.request),
            BreadcrumbType.NAVIGATION,
        )


def _get_breadcrumb_metadata(request) -> dict:
    metadata = {"to": request_path(dict(request.scope))}

    if "referer" in request.headers:
        metadata["from"] = remove_query_from_url(request.headers["referer"])

    return metadata
