from fastapi import APIRouter, Depends, HTTPException, status

from services.workout_service import WorkoutService

from api.dependencies import current_user_id
from api.schemas.workouts import ExerciseCreate


router = APIRouter(
    prefix="/api/exercises",
    tags=["Exercises"],
)

workout_service = WorkoutService()


# GET all exercises belonging to the user
@router.get("")
def get_exercises(
    user_id: int = Depends(current_user_id),
):
    return workout_service.list_exercises(
        user_id=user_id,
    )


# CREATE an exercise
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def create_exercise(
    exercise: ExerciseCreate,
    user_id: int = Depends(current_user_id),
):
    try:
        exercise_id = workout_service.create_exercise(
            user_id=user_id,
            name=exercise.name,
        )

        return {
            "message": "Exercise created successfully",
            "id": exercise_id,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# DELETE an exercise
@router.delete("/{exercise_id}")
def delete_exercise(
    exercise_id: int,
    user_id: int = Depends(current_user_id),
):
    try:
        workout_service.delete_exercise(
            exercise_id=exercise_id,
            user_id=user_id,
        )

        return {
            "message": "Exercise deleted successfully",
        }

    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Exercise not found",
        )