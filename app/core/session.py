from __future__ import annotations
from itsdangerous import URLSafeSerializer, BadSignature
from fastapi import Request, Response
from .config import settings

_serializer = URLSafeSerializer(settings.SESSION_SECRET, salt="fishlog-session")
COOKIE_NAME = "fishlog_session"

def set_session(response: Response, data: dict) -> None:
    token = _serializer.dumps(data)
    response.set_cookie(COOKIE_NAME, token, httponly=True, samesite="lax")

def clear_session(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME)

def get_session(request: Request) -> dict | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        return _serializer.loads(token)
    except BadSignature:
        return None
