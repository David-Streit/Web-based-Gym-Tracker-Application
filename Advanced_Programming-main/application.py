from __future__ import annotations
import os
from fastapi.responses import RedirectResponse
from nicegui import ui, app

from db.engine import init_db
from services.auth_service import AuthService
from services.workout_service import WorkoutService
from services.muscle_map_service import MuscleMapService
from services.weight_service import WeightService
from services.admin_service import AdminService
from ui.pages import configure_pages
# test

class GymProgressTrackerApplication:

    def __init__(self):
        self.auth_service = None
        self.workout_service = None
        self.muscle_map_service = None
        self.weight_service = None
        self.admin_service = None

    def build_services(self):
        self.auth_service = AuthService()
        self.workout_service = WorkoutService()
        self.muscle_map_service = MuscleMapService(
            workout_service=self.workout_service
        )
        self.weight_service = WeightService()
        self.admin_service = AdminService(
            workout_service=self.workout_service,
            weight_service=self.weight_service,
        )

    def get_current_user_id(self):
        return app.storage.user.get("user_id")

    def set_current_user_id(self, user_id):
        if user_id is None:
            app.storage.user.clear()
        else:
            app.storage.user["user_id"] = user_id

    def require_login(self):
        """
        For the normal tracker pages. Returns (user_id, None) for a logged-in
        user, otherwise (None, redirect): logged-out visitors go to the login
        page, admins go to the admin area (admins do not track workouts).
        """
        user_id = self.get_current_user_id()
        if user_id is None:
            return None, RedirectResponse("/")
        if self.auth_service.get_user_by_id(user_id) is None:
            # stale session, e.g. after the database was reset
            self.set_current_user_id(None)
            return None, RedirectResponse("/")
        if self.auth_service.is_admin(user_id):
            return None, RedirectResponse("/admin")
        return user_id, None

    def require_admin(self):
        """Returns the admin's user id, or a redirect for everyone else."""
        user_id = self.get_current_user_id()
        if user_id is None:
            return None, RedirectResponse("/")
        if not self.auth_service.is_admin(user_id):
            return None, RedirectResponse("/dashboard")
        return user_id, None

    def configure(self):
        app.add_static_files('/static', 'static')

        init_db()
        self.build_services()

        configure_pages(
            auth_service=self.auth_service,
            workout_service=self.workout_service,
            muscle_map_service=self.muscle_map_service,
            weight_service=self.weight_service,
            admin_service=self.admin_service,
            require_login=self.require_login,
            require_admin=self.require_admin,
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