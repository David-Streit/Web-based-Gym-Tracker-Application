"""HTTP client the NiceGUI pages use to talk to our REST API.

The NiceGUI server (Python) renders the HTML. When the user saves a workout,
the page handler runs on that server and sends a real HTTP request to the API
(same process and port by default, see application.py). The API applies the
business rules in WorkoutService and stores the data in SQLite.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from typing import Any

import httpx


def api_base_url() -> str:
    port = os.environ.get("PORT", "8080")
    return os.environ.get("API_BASE_URL", f"http://127.0.0.1:{port}")


@dataclass
class ApiResult:
    ok: bool
    status_code: int
    data: Any = None
    error: str | None = None


def _error_message(response: httpx.Response) -> str:
    try:
        detail = response.json().get("detail")
    except ValueError:
        return f"Unexpected response from API ({response.status_code})."
    # 422 validation errors from FastAPI come as a list
    if isinstance(detail, list) and detail:
        first = detail[0]
        field = ".".join(str(p) for p in first.get("loc", [])[1:])
        return f"{field}: {first.get('msg')}" if field else str(first.get("msg"))
    return str(detail or f"Request failed ({response.status_code}).")


async def _request(
    method: str,
    path: str,
    token: str | None = None,
    json: Any = None,
) -> ApiResult:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        async with httpx.AsyncClient(base_url=api_base_url(), timeout=10) as client:
            response = await client.request(method, path, headers=headers, json=json)
    except httpx.HTTPError:
        return ApiResult(
            ok=False,
            status_code=0,
            error="Could not reach the API. Is the server running?",
        )

    if response.is_success:
        return ApiResult(ok=True, status_code=response.status_code, data=response.json())
    return ApiResult(ok=False, status_code=response.status_code, error=_error_message(response))


async def login(username: str, password: str) -> ApiResult:
    return await _request(
        "POST",
        "/api/auth/login",
        json={"username": username, "password": password},
    )


def _workout_body(workout_date: date, notes: str | None, muscle_ids: list[int]) -> dict:
    return {
        "workout_date": workout_date.isoformat(),
        "notes": notes or None,
        "muscle_ids": muscle_ids,
    }


async def create_workout(
    token: str,
    workout_date: date,
    notes: str | None,
    muscle_ids: list[int],
) -> ApiResult:
    return await _request(
        "POST",
        "/api/workouts",
        token=token,
        json=_workout_body(workout_date, notes, muscle_ids),
    )


async def update_workout(
    token: str,
    workout_id: int,
    workout_date: date,
    notes: str | None,
    muscle_ids: list[int],
) -> ApiResult:
    return await _request(
        "PUT",
        f"/api/workouts/{workout_id}",
        token=token,
        json=_workout_body(workout_date, notes, muscle_ids),
    )
