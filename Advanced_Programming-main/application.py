from __future__ import annotations
import os
from nicegui import ui, app

from db.engine import init_db
from services.auth_service import AuthService
from services.workout_service import WorkoutService
from services.muscle_map_service import MuscleMapService
from services.weight_service import WeightService
from ui.pages import configure_pages


class GymProgressTrackerApplication:

    def __init__(self):
        self.auth_service = None
        self.workout_service = None
        self.muscle_map_service = None
        self.weight_service = None

    def build_services(self):
        self.auth_service = AuthService()
        self.workout_service = WorkoutService()
        self.muscle_map_service = MuscleMapService(
            workout_service=self.workout_service
        )
        self.weight_service = WeightService()

    def get_current_user_id(self):
        return app.storage.user.get("user_id")

    def set_current_user_id(self, user_id):
        if user_id is None:
            app.storage.user.clear()
        else:
            app.storage.user["user_id"] = user_id

    def require_login(self):
        user_id = self.get_current_user_id()
        if user_id is None:
            ui.navigate.to("/")
            raise RuntimeError("Not logged in")
        return user_id

    def configure(self):
        app.add_static_files('/static', 'static')

        init_db()
        self.build_services()

        configure_pages(
            auth_service=self.auth_service,
            workout_service=self.workout_service,
            muscle_map_service=self.muscle_map_service,
            weight_service=self.weight_service,
            require_login=self.require_login,
            get_current_user_id=self.get_current_user_id,
            set_current_user_id=self.set_current_user_id,
        )

    def run(self):
        self.configure()

        ui.run(
            title="Gym Progress Tracker",
            reload=False,
            storage_secret=os.environ.get(
                "NICEGUI_STORAGE_SECRET",
                "dev-secret-change-me"
            ),
        )