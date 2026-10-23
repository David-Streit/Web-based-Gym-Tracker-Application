from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from api.dependencies import current_user_id
from api.schemas.workouts import WorkoutCreated, WorkoutDetail, WorkoutListItem, WorkoutWrite
from services.workout_service import WorkoutService

router = APIRouter(prefix="/api/workouts", tags=["workouts"])
service = WorkoutService()
UserId = Annotated[int, Depends(current_user_id)]


def _handle_error(exc: ValueError) -> None:
    message = str(exc)
    if "not found" in message.lower() or "not yours" in message.lower():
        raise HTTPException(status_code=404, detail="Workout not found") from exc
    raise HTTPException(status_code=400, detail=message) from exc


@router.get("", response_model=list[WorkoutListItem])
def list_workouts(user_id: UserId, limit: Annotated[int, Query(ge=1, le=100)] = 20):
    return service.list_sessions(user_id=user_id, limit=limit)


@router.get("/{workout_id}", response_model=WorkoutDetail)
def read_workout(workout_id: int, user_id: UserId):
    try:
        return service.get_session_by_id(workout_id, user_id)
    except ValueError as exc:
        _handle_error(exc)


@router.post("", response_model=WorkoutCreated, status_code=status.HTTP_201_CREATED)
def create_workout(payload: WorkoutWrite, user_id: UserId):
    try:
        workout_id = service.create_session(user_id, payload.workout_date, payload.notes, payload.muscle_ids)
        return {"id": workout_id}
    except ValueError as exc:
        _handle_error(exc)


@router.put("/{workout_id}", response_model=WorkoutDetail)
def update_workout(workout_id: int, payload: WorkoutWrite, user_id: UserId):
    try:
        service.update_session(workout_id, user_id, payload.workout_date, payload.notes, payload.muscle_ids)
        return service.get_session_by_id(workout_id, user_id)
    except ValueError as exc:
        _handle_error(exc)


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(workout_id: int, user_id: UserId):
    try:
        service.delete_session(workout_id, user_id)
    except ValueError as exc:
        _handle_error(exc)
    return Response(status_code=204)
