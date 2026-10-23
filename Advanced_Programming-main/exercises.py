from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from api.dependencies import current_user_id
from api.schemas.workouts import ExerciseItem, ExerciseWrite
from services.workout_service import WorkoutService

router = APIRouter(prefix="/api/exercises", tags=["exercises"])
service = WorkoutService()
UserId = Annotated[int, Depends(current_user_id)]


@router.get("", response_model=list[ExerciseItem])
def list_exercises(user_id: UserId):
    return service.list_exercises(user_id)


@router.post("", response_model=ExerciseItem, status_code=status.HTTP_201_CREATED)
def create_exercise(payload: ExerciseWrite, user_id: UserId):
    try:
        exercise_id = service.create_exercise(user_id, payload.name)
        return {"id": exercise_id, "name": payload.name.strip()}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(exercise_id: int, user_id: UserId):
    try:
        service.delete_exercise(exercise_id, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Exercise not found") from exc
    return Response(status_code=204)
