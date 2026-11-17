"""HTTP middleware applied to every route."""

import re
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"
# Client-supplied IDs are accepted only in this shape, which rules out log injection.
_VALID_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")


async def attach_request_id(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Expose a request ID on `request.state` and echo it in the response header."""
    incoming = request.headers.get(REQUEST_ID_HEADER, "")
    request_id = incoming if _VALID_REQUEST_ID.fullmatch(incoming) else uuid4().hex
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = request_id
    return response
