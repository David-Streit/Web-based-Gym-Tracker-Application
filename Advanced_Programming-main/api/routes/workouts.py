
from fastapi import APIRouter, Depends, HTTPException, status

from services.workout_service import WorkoutService
from api.dependencies import current_user_id
from api.schemas.workouts import WorkoutCreate, WorkoutUpdate


router = APIRouter(
    prefix="/api/workouts",
    tags=["Workouts"],
)

workout_service = WorkoutService()


# GET all workouts belonging to the user
@router.get("")
def get_workouts(
    user_id: int = Depends(current_user_id),
):
    return workout_service.list_sessions(
        user_id=user_id,
    )


# GET a specific workout
@router.get("/{workout_id}")
def get_workout(
    workout_id: int,
    user_id: int = Depends(current_user_id),
):
    try:
        return workout_service.get_session_by_id(
            session_id=workout_id,
            user_id=user_id,
        )

    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Workout not found",
        )


# CREATE a new workout
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def create_workout(
    workout: WorkoutCreate,
    user_id: int = Depends(current_user_id),
):
    try:
        workout_id = workout_service.create_session(
            user_id=user_id,
            workout_date=workout.workout_date,
            notes=workout.notes,
            muscle_ids=workout.muscle_ids,
        )

        return {
            "message": "Workout created successfully",
            "id": workout_id,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# UPDATE an existing workout
@router.put("/{workout_id}")
def update_workout(
    workout_id: int,
    workout: WorkoutUpdate,
    user_id: int = Depends(current_user_id),
):
    try:
        workout_service.update_session(
            session_id=workout_id,
            user_id=user_id,
            workout_date=workout.workout_date,
            notes=workout.notes,
            muscle_ids=workout.muscle_ids,
        )

        return {
            "message": "Workout updated successfully",
            "id": workout_id,
        }

    except ValueError as error:
        message = str(error)

        raise HTTPException(
            status_code=(
                404 if "not found" in message.lower()
                else 400
            ),
            detail=message,
        )


# DELETE a workout
@router.delete("/{workout_id}")
def delete_workout(
    workout_id: int,
    user_id: int = Depends(current_user_id),
):
    try:
        workout_service.delete_session(
            session_id=workout_id,
            user_id=user_id,
        )

        return {
            "message": "Workout deleted successfully",
        }

    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Workout not found",
        )
