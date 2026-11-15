"""In-memory access tokens for the API.

A token is issued by POST /api/auth/login and sent as
"Authorization: Bearer <token>" on later requests. Tokens live only in the
memory of the running process, so they are lost on restart (users simply log
in again). This is a deliberate simplification for the course project.
"""
from __future__ import annotations

import secrets

_tokens: dict[str, int] = {}


def issue_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    _tokens[token] = user_id
    return token


def user_id_for_token(token: str | None) -> int | None:
    if not token:
        return None
    return _tokens.get(token)


def revoke_token(token: str | None) -> None:
    if token:
        _tokens.pop(token, None)
