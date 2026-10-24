from __future__ import annotations
from datetime import date, timedelta
from nicegui import ui, app
from fastapi.responses import RedirectResponse
from ui.heatmap import build_heatmap_svg


def configure_pages(
    auth_service,
    workout_service,
    muscle_map_service,
    weight_service,
    admin_service,
    require_login,
    require_admin,
    get_current_user_id,
    set_current_user_id,
):

    #shared full-page style
    FULL_PAGE_STYLE = """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-app: #0f1115;
            --bg-surface: #181b22;
            --bg-surface-2: #1f232c;
            --bg-elevated: #262b36;
            --border-soft: rgba(255,255,255,0.07);
            --border-strong: rgba(255,255,255,0.12);
            --text-primary: #f3f4f6;
            --text-muted: #9ca3af;
            --accent: #22c55e;
            --accent-hover: #16a34a;
            --accent-soft: rgba(34,197,94,0.12);
            --shadow-card: 0 10px 30px rgba(0,0,0,0.45), 0 2px 6px rgba(0,0,0,0.25);
        }
        html, body, .q-page {
            margin: 0; padding: 0; height: 100%; overflow: hidden;
            background: var(--bg-app);
            font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
            -webkit-font-smoothing: antialiased;
            color: var(--text-primary);
        }
        .nicegui-content, .q-page-container {
            padding: 0 !important;
            margin: 0 !important;
        }
        ::-webkit-scrollbar { width: 10px; height: 10px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb {
            background: rgba(255,255,255,0.08);
            border-radius: 10px;
            border: 2px solid transparent;
            background-clip: padding-box;
        }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.18); background-clip: padding-box; }

        /* Cards */
        .q-card {
            background: var(--bg-surface) !important;
            border: 1px solid var(--border-soft);
            border-radius: 16px !important;
            box-shadow: var(--shadow-card) !important;
            transition: border-color 0.2s ease, transform 0.2s ease;
        }

        /* Buttons */
        .q-btn {
            border-radius: 10px !important;
            font-weight: 600 !important;
            letter-spacing: 0.2px;
            text-transform: none !important;
            transition: all 0.2s ease !important;
        }
        .q-btn:not(.q-btn--flat):not(.q-btn--outline):not([class*="bg-"]) {
            background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
            color: #07140c !important;
            box-shadow: 0 4px 14px rgba(34,197,94,0.25);
        }
        .q-btn:not(.q-btn--flat):not(.q-btn--outline):not([class*="bg-"]):hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 18px rgba(34,197,94,0.35);
        }
        .q-btn--outline {
            border: 1px solid var(--border-strong) !important;
            color: var(--text-primary) !important;
        }
        .q-btn--outline:hover { background: rgba(255,255,255,0.05) !important; }
        .q-btn--round { border-radius: 999px !important; }

        /* Inputs */
        .q-field--outlined .q-field__control {
            border-radius: 10px !important;
            background: var(--bg-surface-2);
        }
        .q-field--outlined .q-field__control:before { border-color: var(--border-soft) !important; }
        .q-field--outlined .q-field__control:hover:before { border-color: var(--border-strong) !important; }
        .q-field--focused .q-field__control:after { border-color: var(--accent) !important; }
        .q-field__label { color: var(--text-muted) !important; }

        /* Checkboxes */
        .q-checkbox__inner--truthy .q-checkbox__bg { background: var(--accent) !important; border-color: var(--accent) !important; }

        /* Tables */
        .q-table {
            background: transparent !important;
            border-radius: 12px;
        }
        .q-table thead th {
            background: var(--bg-surface-2) !important;
            color: var(--text-muted) !important;
            font-weight: 600 !important;
            font-size: 12px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            border-bottom: 1px solid var(--border-soft) !important;
        }
        .q-table tbody tr { transition: background 0.15s ease; }
        .q-table tbody tr:hover { background: rgba(255,255,255,0.03) !important; }
        .q-table tbody td { border-bottom: 1px solid var(--border-soft) !important; }

        /* Separator */
        .q-separator { background: var(--border-soft) !important; }

        /* Linear progress */
        .q-linear-progress {
            border-radius: 999px !important;
            overflow: hidden;
            background: rgba(255,255,255,0.06) !important;
        }

        /* Headings */
        .text-2xl, .text-3xl, .text-7xl {
            font-family: 'Inter', sans-serif;
            letter-spacing: -0.02em;
        }
    </style>
    """

    @ui.page("/")
    def login_page():
        ui.dark_mode().enable()
        ui.add_head_html(FULL_PAGE_STYLE)
        ui.add_head_html("""
        <style>
            html, body { margin: 0; padding: 0; height: 100%; overflow: hidden; }
            .login-page {
                position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                width: 100vw; height: 100vh;
                display: flex; flex-direction: column;
                align-items: center; justify-content: center;
                background: url("/static/Login_Page1.png") no-repeat center center;
                background-size: cover;
                overflow: hidden;
            }
            .login-page::before {
                content: "";
                position: absolute; inset: 0;
                background: linear-gradient(135deg,
                    rgba(15,17,21,0.55) 0%,
                    rgba(15,17,21,0.75) 60%,
                    rgba(15,17,21,0.85) 100%);
                pointer-events: none;
            }
            .login-page > * { position: relative; z-index: 1; }
            .login-title {
                font-weight: 800;
                letter-spacing: -0.03em;
                line-height: 1.2;
                padding-bottom: 0.15em;
                background: linear-gradient(120deg, #ffffff 0%, #d1fae5 50%, #22c55e 100%);
                -webkit-background-clip: text;
                background-clip: text;
                color: transparent;
                text-shadow: 0 4px 24px rgba(34,197,94,0.15);
                margin-bottom: 8px;
            }
            .login-subtitle {
                color: #d1d5db;
                font-size: 15px;
                letter-spacing: 0.3px;
                margin-bottom: 24px;
            }
            .auth-card {
                background: rgba(24,27,34,0.78) !important;
                backdrop-filter: blur(18px) saturate(140%);
                -webkit-backdrop-filter: blur(18px) saturate(140%);
                border: 1px solid rgba(255,255,255,0.08) !important;
                border-radius: 20px !important;
                padding: 32px !important;
                box-shadow: 0 20px 60px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.04) inset !important;
            }
        </style>
        """)

        if get_current_user_id() is not None:
            ui.navigate.to("/dashboard")
            return

        with ui.column().classes("login-page w-full h-screen items-center justify-center"):
            ui.label("Gym Progress Tracker").classes("text-7xl login-title")

            with ui.card().classes("auth-card w-full max-w-md"):
                ui.label("Login or register to start tracking.").classes("login-subtitle")
                username = ui.input("Username").props("clearable outlined").classes("w-full")
                password = ui.input(
                    "Password", password=True, password_toggle_button=True
                ).props("outlined").classes("w-full")

                def do_login():
                    # authenticate user credentials through auth_service
                    try:
                        user_id = auth_service.login(username.value or "", password.value or "")
                        set_current_user_id(user_id)
                        ui.navigate.to("/dashboard")
                    except ValueError as e:
                        ui.notify(str(e), type="negative")

                with ui.row().classes("gap-3 mt-4 w-full"):
                    ui.button("Login", on_click=do_login).classes("flex-1")
                    ui.button(
                        "Register", on_click=lambda: ui.navigate.to("/register")
                    ).props("outline").classes("flex-1")

                username.on("keydown.enter", lambda e: do_login())
                password.on("keydown.enter", lambda e: do_login())

    @ui.page("/register")
    def register_page():
        ui.dark_mode().enable()
        ui.add_head_html(FULL_PAGE_STYLE)
        ui.add_head_html("""
        <style>
            html, body { margin: 0; padding: 0; height: 100%; overflow: hidden; }
            .register-page {
                position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                width: 100vw; height: 100vh;
                display: flex; flex-direction: column;
                align-items: center; justify-content: center;
                background-color: #0f1115;
                background-image: url("/static/Register_Page2.png");
                background-repeat: no-repeat;
                background-position: center center;
                background-size: contain;
                overflow: hidden;
            }
            .register-page::before {
                content: "";
                position: absolute; inset: 0;
                background: linear-gradient(135deg,
                    rgba(15,17,21,0.55) 0%,
                    rgba(15,17,21,0.75) 60%,
                    rgba(15,17,21,0.85) 100%);
                pointer-events: none;
            }
            .register-page > * { position: relative; z-index: 1; }
            .auth-card {
                background: rgba(24,27,34,0.78) !important;
                backdrop-filter: blur(18px) saturate(140%);
                -webkit-backdrop-filter: blur(18px) saturate(140%);
                border: 1px solid rgba(255,255,255,0.08) !important;
                border-radius: 20px !important;
                padding: 32px !important;
                box-shadow: 0 20px 60px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.04) inset !important;
            }
            .register-title {
                font-weight: 800;
                letter-spacing: -0.02em;
                background: linear-gradient(120deg, #ffffff 0%, #d1fae5 50%, #22c55e 100%);
                -webkit-background-clip: text;
                background-clip: text;
                color: transparent;
            }
        </style>
        """)

        with ui.column().classes("register-page w-full items-center justify-center"):
            with ui.card().classes("auth-card w-full max-w-lg"):
                ui.label("Create your account").classes("text-3xl register-title")
                ui.label("Start tracking your gym progress today.").classes(
                    "text-gray-400 mb-4"
                ).style("font-size: 14px;")

                new_username = ui.input("Username").props("clearable outlined").classes("w-full")
                new_password = ui.input(
                    "Password", password=True, password_toggle_button=True
                ).props("outlined").classes("w-full")

                def do_create_account():
                    # register a new user using auth_service and log them in
                    try:
                        user_id = auth_service.register(
                            new_username.value or "",
                            new_password.value or "",
                        )
                        set_current_user_id(user_id)
                        ui.notify("Register Successful!", type="positive")
                        ui.navigate.to("/dashboard")
                    except ValueError as e:
                        ui.notify(str(e), type="negative")

                with ui.row().classes("gap-3 mt-4 w-full"):
                    # submit registration form
                    ui.button("Create Account", on_click=do_create_account).classes("flex-1")
                    ui.button(
                        "Back to Login", on_click=lambda: ui.navigate.to("/")
                    ).props("outline").classes("flex-1")

    @ui.page("/dashboard")
    def dashboard_page() :
        user_id, redirect = require_login()
        if redirect:
            return redirect
        ui.dark_mode().enable()
        ui.add_head_html(FULL_PAGE_STYLE)

        with ui.column().classes("w-full items-center").style("height: 100vh; overflow: hidden;"):

            with ui.column().style(
                "max-width: 1100px; width: 100%; "
                "background: linear-gradient(135deg, #1f232c 0%, #181b22 100%); "
                "border: 1px solid rgba(255,255,255,0.07); "
                "border-radius: 20px; "
                "padding: 24px 32px; margin-top: 24px; gap: 14px; "
                "box-shadow: 0 14px 36px rgba(0,0,0,0.45), "
                "inset 0 1px 0 rgba(255,255,255,0.04); flex-shrink: 0; "
                "position: relative; overflow: hidden;"
            ):
                ui.html(
                    '<div style="position:absolute; top:0; left:0; right:0; height:2px; '
                    'background:linear-gradient(90deg, transparent 0%, #22c55e 50%, transparent 100%); '
                    'opacity:0.7;"></div>'
                )
                # load current user profile for the dashboard greeting
                user = auth_service.get_user_by_id(user_id)
                username = user["username"]
                ui.label(f"Welcome back, {username}").classes("text-3xl font-bold").style(
                    "letter-spacing: -0.02em; margin: 0;"
                )
                ui.label("Dashboard").classes("text-sm").style(
                    "color: #9ca3af; text-transform: uppercase; letter-spacing: 2px; "
                    "font-weight: 600; margin-top: -4px;"
                )
                with ui.row().classes("items-center gap-3 mt-2"):
                    ui.button("New Workout", on_click=lambda: ui.navigate.to("/workout/new"))
                    ui.button("Weekly Summary", on_click=lambda: ui.navigate.to("/week")).props("outline")
                    ui.button("PR Tracker", on_click=lambda: ui.navigate.to("/pr-tracker")).props("outline")
                    ui.button("Weight Tracker", on_click=lambda: ui.navigate.to("/weight-tracker")).props("outline")
                    ui.button(
                        "Logout",
                        on_click=lambda: (set_current_user_id(None), ui.navigate.to("/")),
                    ).props("flat")

            with ui.column().style(
                "max-width: 1100px; width: 100%; flex: 1; overflow-y: auto; "
                "padding: 20px 0 16px 0; gap: 12px;"
            ):
                ui.label("Recent Workouts").classes("text-lg font-semibold").style(
                    "letter-spacing: -0.01em;"
                )

                # fetch recent workout sessions for display on the dashboard
                sessions = workout_service.list_sessions(user_id=user_id, limit=14)

                if not sessions:
                    with ui.card().classes("w-full").style(
                        "padding: 32px; text-align: center; background: var(--bg-surface);"
                    ):
                        ui.label("No workouts yet.").style(
                            "font-size: 16px; color: #d1d5db; margin-bottom: 4px;"
                        )
                        ui.label("Click 'New Workout' to add your first one.").style(
                            "font-size: 13px; color: #9ca3af;"
                        )
                    return

                rows = []
                for s in sessions:
                    rows.append({
                        "id": s["id"],
                        "date": s["date"].strftime("%d.%m.%Y"),
                        "muscles": ", ".join(s["muscle_names"]),
                        "notes": s.get("notes") or "",
                    })

                columns = [
                    {"name": "date", "label": "Date", "field": "date", "sortable": True},
                    {"name": "muscles", "label": "Muscles", "field": "muscles"},
                    {"name": "notes", "label": "Notes", "field": "notes"},
                    {"name": "actions", "label": "Actions", "field": "actions"},
                ]

                table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full")

                def delete_row(ev):
                    row_data = ev.args
                    with ui.dialog() as dialog, ui.card().classes("p-4"):
                        ui.label(f'Do you want to delete the entry from {row_data["date"]}?')
                        with ui.row().classes("w-full justify-end"):
                            ui.button("Cancel", on_click=dialog.close).props("flat")
                            ui.button(
                                "Delete",
                                on_click=lambda: execute_deletion(row_data, dialog),
                                color="red",
                            )
                    dialog.open()

                def execute_deletion(row, dialog):
                    # delete a session from the database and refresh the dashboard
                    try:
                        workout_service.delete_session(session_id=row["id"], user_id=user_id)
                        ui.notify("Workout deleted", type="positive")
                        dialog.close()
                        ui.navigate.to("/dashboard")
                    except Exception as e:
                        ui.notify(f"Error: {e}", type="negative")

                def edit_row(ev):
                    row = ev.args
                    ui.navigate.to(f"/workout/edit/{row['id']}")

                table.on("edit_row", edit_row)
                table.on("delete_row", delete_row)
                table.add_slot(
                    "body-cell-actions",
                    """
                    <q-td :props="props">
                        <q-btn dense flat icon="edit" @click="$parent.$emit('edit_row', props.row)" />
                        <q-btn dense flat icon="delete" @click="$parent.$emit('delete_row', props.row)" />
                    </q-td>
                    """,
                )

    #shared helper: builds the muscles + exercises columns
    def _build_workout_form(
        user_id: int,
        workout_service,
        notes_value: str = "",
        selected_muscle_ids: set | None = None,
    ):
        """Returns (workout_date_widget, notes_widget, checkboxes, exercise_inputs)."""
        selected_muscle_ids = selected_muscle_ids or set()

        # load muscle and exercise options for the workout form
        all_muscles = workout_service.list_muscles()
        all_exercises_list = ["Benchpress", "Deadlift", "Squats", "Lat Pulldown"]
        custom_exercises = workout_service.list_exercises(user_id=user_id)
        all_exercises_list.extend([e["name"] for e in custom_exercises])

        workout_date = ui.input("Date", value=date.today().isoformat()).props(f"type=date max={date.today().isoformat()}")
        notes = ui.textarea("Notes (optional)", value=notes_value).props("autogrow").style(
            "max-height: 80px; overflow-y: auto;"
        )

        checkboxes: list = []
        exercise_inputs: dict = {}

        with ui.element("div").style(
            "display: flex; flex-direction: row; gap: 24px; "
            "width: 100%; flex: 1; min-height: 0;"
        ):
            with ui.element("div").style(
                "width: 35%; min-width: 0; overflow-x: hidden; overflow-y: auto; max-height: 55vh;"
            ):
                ui.label("Muscles trained").classes("font-semibold")
                with ui.column().classes("gap-1"):
                    for m in all_muscles:
                        cb = ui.checkbox(m["name"], value=(m["id"] in selected_muscle_ids))
                        checkboxes.append((m, cb))

            with ui.element("div").style(
                "width: 65%; min-width: 0; overflow-x: hidden; overflow-y: auto; "
                "max-height: 55vh; padding-right: 12px; box-sizing: border-box;"
            ):
                ui.label("Exercises and PRs (kg)").classes("font-semibold")
                with ui.column().classes("gap-3").style("width: 100%;"):
                    for exercise in all_exercises_list:
                        with ui.row().classes("gap-2 items-center").style(
                            "flex-wrap: nowrap; width: 100%; min-width: 0;"
                        ):
                            cb = ui.checkbox(exercise).style("width: 140px; flex-shrink: 0;")
                            pr_input = ui.input(
                                "PR",
                                placeholder="kg",
                                validation={
                                    "Please enter a number": lambda v: (
                                        v == ""
                                        or v.replace(".", "", 1).replace("-", "", 1).isdigit()
                                    )
                                },
                            ).props("type=number").style(
                                "width: 100px; flex-shrink: 0; flex-grow: 0;"
                            )
                            exercise_inputs[exercise] = (cb, pr_input)

        return workout_date, notes, checkboxes, exercise_inputs

    @ui.page("/workout/edit/{session_id}")
    def edit_workout_page(session_id: int):
        user_id, redirect = require_login()
        if redirect:
            return redirect
        ui.dark_mode().enable()
        ui.add_head_html(FULL_PAGE_STYLE)

        # load the existing workout session details for editing
        # unknown id or a workout of another user -> back to dashboard instead of error 500
        try:
            session_data = workout_service.get_session_by_id(
                session_id=session_id,
                user_id=user_id,
            )
        except ValueError:
            return RedirectResponse("/dashboard")

        with ui.column().classes("w-full items-center").style(
            "height: 100vh; overflow: hidden; padding: 16px;"
        ):
            with ui.card().classes("w-full max-w-6xl").style(
                "height: 100%; display: flex; flex-direction: column; overflow: hidden;"
            ):
                with ui.row().classes("items-center justify-between w-full").style("flex-shrink: 0;"):
                    ui.label("Edit Workout").classes("text-2xl font-bold")
                    with ui.row().classes("gap-2"):
                        ui.button("Cancel", on_click=lambda: ui.navigate.to("/dashboard")).props("outline")

                ui.separator().style("flex-shrink: 0;")

                with ui.column().style("flex: 1; overflow-y: auto; padding: 8px 0;"):
                    # build the edit workout form with current session data
                    workout_date, notes, checkboxes, exercise_inputs = _build_workout_form(
                        user_id=user_id,
                        workout_service=workout_service,
                        notes_value=session_data["notes"] or "",
                        selected_muscle_ids=set(session_data["muscle_ids"]),
                    )
                    workout_date.value = session_data["date"].isoformat()

                ui.separator().style("flex-shrink: 0;")
                with ui.row().classes("gap-2 justify-end").style("flex-shrink: 0; padding-top: 8px;"):
                    def save():
                        new_muscle_ids = [m["id"] for (m, cb) in checkboxes if cb.value]
                        if not new_muscle_ids:
                            ui.notify("Select at least one muscle group.", type="warning")
                            return
                        try:
                            workout_date_value = date.fromisoformat(
                                str(workout_date.value).replace("/", "-")
                            )
                            # save updated workout session details
                            workout_service.update_session(
                                session_id=session_id,
                                user_id=user_id,
                                workout_date=workout_date_value,
                                notes=notes.value,
                                muscle_ids=new_muscle_ids,
                            )
                            for exercise_name, (cb, pr_input) in exercise_inputs.items():
                                if cb.value and pr_input.value:
                                    try:
                                        weight = float(pr_input.value)
                                        if weight > 0:
                                            workout_service.save_pr(
                                                user_id=user_id,
                                                exercise_name=exercise_name,
                                                weight_kg=weight,
                                                recorded_date=workout_date_value,
                                            )
                                    except ValueError:
                                        pass
                            ui.notify("Workout updated!", type="positive")
                            ui.navigate.to("/dashboard")
                        except ValueError as e:
                            ui.notify(str(e), type="negative")

                    ui.button("Save Changes", on_click=save)
                    ui.button("Cancel", on_click=lambda: ui.navigate.to("/dashboard")).props("outline")

    @ui.page("/workout/new")
    def new_workout_page():
        user_id, redirect = require_login()
        if redirect:
            return redirect
        ui.dark_mode().enable()
        ui.add_head_html(FULL_PAGE_STYLE)

        def show_add_exercise_dialog(user_id: int):
            # modal dialog used to manage custom exercises for the current user
            with ui.dialog() as dialog, ui.card().classes("p-6 w-full max-w-md"):
                ui.label("Exercises").classes("text-xl font-bold")

                exercise_list = ui.column().classes("gap-2 mb-4 border p-3 rounded")

                def refresh_exercise_list():
                    exercise_list.clear()
                    # load custom exercises from workout_service
                    exercises = workout_service.list_exercises(user_id=user_id)
                    with exercise_list:
                        if not exercises:
                            ui.label("No custom exercises yet.").classes("text-gray-500")
                        else:
                            for exercise in exercises:
                                with ui.row().classes("justify-between items-center w-full"):
                                    ui.label(exercise["name"])
                                    ui.button(
                                        icon="delete",
                                        on_click=lambda ex_id=exercise["id"]: delete_exercise(ex_id),
                                    ).props("flat color=negative size=sm")

                def delete_exercise(ex_id):
                    # remove an exercise and refresh the workout creation view
                    try:
                        workout_service.delete_exercise(ex_id, user_id)
                        ui.notify("Exercise deleted!", type="positive")
                        dialog.close()
                        ui.navigate.to("/workout/new")
                    except ValueError as e:
                        ui.notify(str(e), type="negative")

                refresh_exercise_list()

                ui.label("Add New Exercise").classes("text-md font-semibold mt-4")
                exercise_name = ui.input("Exercise Name").classes("w-full")

                def add_exercise():
                    # create a new custom exercise for the user
                    try:
                        if not exercise_name.value or not exercise_name.value.strip():
                            ui.notify("Exercise name cannot be empty.", type="warning")
                            return
                        workout_service.create_exercise(
                            user_id=user_id,
                            name=exercise_name.value.strip(),
                        )
                        ui.notify("Exercise added!", type="positive")
                        exercise_name.value = ""
                        dialog.close()
                        ui.navigate.to("/workout/new")
                    except ValueError as e:
                        ui.notify(str(e), type="negative")

                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button("Close", on_click=dialog.close).props("outline")
                    ui.button("Add", on_click=add_exercise)

            dialog.open()

        # load muscles and exercises for the new workout form
        all_muscles = workout_service.list_muscles()
        all_exercises_list = ["Benchpress", "Deadlift", "Squats", "Lat Pulldown"]
        custom_exercises = workout_service.list_exercises(user_id=user_id)
        all_exercises_list.extend([e["name"] for e in custom_exercises])

        # load recent workouts so the user can reuse a template
        recent_sessions = workout_service.list_sessions(user_id=user_id, limit=10)
        template_options = {
            s["id"]: f"{s['date'].strftime('%d.%m.%Y')} - {', '.join(s['muscle_names'])}"
            for s in recent_sessions
        }

        with ui.column().classes("w-full items-center").style(
            "height: 100vh; overflow: hidden; padding: 16px;"
        ):
            with ui.card().classes("w-full max-w-4xl").style(
                "height: 100%; display: flex; flex-direction: column; overflow: hidden;"
            ):
                ui.label("New Workout").classes("text-2xl font-bold").style("flex-shrink: 0;")
                ui.separator().style("flex-shrink: 0;")

                with ui.column().style("flex-shrink: 0; padding-bottom: 8px;"):
                    def load_template(e):
                        # load a past workout into the current form as a template
                        if not e.value:
                            return
                        details = workout_service.get_session_by_id(e.value, user_id)
                        notes_widget.value = details["notes"] or ""
                        selected_muscles = set(details["muscle_ids"])
                        for m, cb in muscle_checkboxes:
                            cb.value = m["id"] in selected_muscles
                        ui.notify("Template loaded!", type="positive")

                    ui.label("Load from recent workouts").classes("font-semibold")
                    ui.select(
                        options=template_options,
                        label="Load from past workout...",
                        on_change=load_template,
                        clearable=True,
                    ).classes("w-full")

                workout_date = ui.input("Date", value=date.today().isoformat()).props(
                    f"type=date max={date.today().isoformat()}"
                ).style("flex-shrink: 0;")
                notes_widget = ui.textarea("Notes (optional)").props("autogrow").style(
                    "flex-shrink: 0; max-height: 80px; overflow-y: auto;"
                )

                muscle_checkboxes: list = []
                exercise_inputs: dict = {}

                with ui.element("div").style("display: flex; flex-direction: row; gap: 32px; flex: 1; min-height: 0; width: 100%;"):
                    # Left side config
                    with ui.element("div").style("width: 50%; overflow-y: auto;"):
                        ui.label("Muscles trained").classes("font-semibold")
                        with ui.column().classes("gap-1"):
                            for m in all_muscles:
                                cb = ui.checkbox(m["name"])
                                muscle_checkboxes.append((m, cb))

                    # Right side config
                    with ui.element("div").style("width: 50%; overflow-y: auto;"):
                        ui.button("Edit Exercises", on_click=lambda: show_add_exercise_dialog(user_id)).classes("mb-3")
                        ui.label("Exercises & PRs (kg)").classes("font-semibold")
                        with ui.column().classes("gap-1"):
                            for exercise in all_exercises_list:
                                with ui.row().classes("gap-2 items-center"):
                                    cb = ui.checkbox(exercise).style("width: 150px;")
                                    pr_input = ui.input(
                                        "PR",
                                        placeholder="kg",
                                        validation={
                                            "Please enter a number": lambda v: (
                                                v == ""
                                                or v.replace(".", "", 1).replace("-", "", 1).isdigit()
                                            )
                                        },
                                    ).props("type=number").style("width: 100px")
                                    exercise_inputs[exercise] = (cb, pr_input)

                ui.separator().style("flex-shrink: 0;")
                with ui.row().classes("gap-2 justify-end").style("flex-shrink: 0; padding-top: 8px;"):
                    def save():
                        selected_ids = [m["id"] for (m, cb) in muscle_checkboxes if cb.value]
                        if not selected_ids:
                            ui.notify("Select at least one muscle group.", type="warning")
                            return
                        try:
                            workout_date_val = date.fromisoformat(
                                str(workout_date.value).replace("/", "-")
                            )
                            # create a new workout session record
                            workout_service.create_session(
                                user_id=user_id,
                                workout_date=workout_date_val,
                                notes=notes_widget.value,
                                muscle_ids=selected_ids,
                            )
                            # PRs save
                            for exercise_name, (cb, pr_input) in exercise_inputs.items():
                                if cb.value and pr_input.value:
                                    try:
                                        weight = float(pr_input.value)
                                        if weight > 0:
                                            # store a PR for the exercise entered in the form
                                            workout_service.save_pr(
                                                user_id=user_id,
                                                exercise_name=exercise_name,
                                                weight_kg=weight,
                                                recorded_date=workout_date_val,
                                            )
                                    except ValueError:
                                        pass
                            ui.notify("Workout saved!", type="positive")
                            ui.navigate.to("/dashboard")
                        except ValueError as e:
                            ui.notify(str(e), type="negative")

                    ui.button("Save Workout", on_click=save)
                    ui.button("Cancel", on_click=lambda: ui.navigate.to("/dashboard")).props("outline")

    @ui.page("/week")
    def week_view_page():
        user_id, redirect = require_login()
        if redirect:
            return redirect
        ui.dark_mode().enable()
        ui.add_head_html(FULL_PAGE_STYLE)

        state = {"week_offset": 0}

        def get_week_label():
            offset = state["week_offset"]
            if offset == 0:
                return "This Week"
            if offset == 1:
                return "Last Week"
            return f"{offset} weeks ago"

        @ui.refreshable
        def week_display():
            current_day = date.today() - timedelta(weeks=state["week_offset"])
            # load weekly muscle summary data from muscle_map_service
            result = muscle_map_service.week_summary(
                user_id=user_id,
                day_in_week=current_day,
            )

            start_str = result["week_start"].strftime("%d.%m.%Y")
            end_str = result["week_end"].strftime("%d.%m.%Y")

            ui.label(f"Week: {start_str} \u2192 {end_str}").classes("text-lg font-semibold")
            ui.separator()

            with ui.element("div").style(
                "display: flex; flex-direction: row; gap: 24px;"
                "width: 100%; flex: 1; overflow: hidden;"
            ):
                #left = Summary (top) + Legend (bottom)
                with ui.element("div").style(
                    "width: 25%; min-width: 180px; display: flex; flex-direction: column; "
                    "gap: 16px; overflow-y: auto;"
                ):
                    with ui.column().classes("gap-2"):
                        ui.label("Summary").classes("text-xl font-bold").style(
                            "letter-spacing: -0.01em;"
                        )
                        if not result["muscles"]:
                            ui.label("No workouts this week yet.").style(
                                "color: #9ca3af; font-size: 13px;"
                            )
                        else:
                            for item in result["muscles"]:
                                ui.html(
                                    f'<div style="display:flex; justify-content:space-between; '
                                    f'align-items:center; gap:12px; width:100%; box-sizing:border-box; '
                                    f'padding:6px 10px; border-radius:8px; '
                                    f'background:rgba(255,255,255,0.03); font-size:13px;">'
                                    f'<span style="color:#e5e7eb;">{item["name"]}</span>'
                                    f'<span style="color:#22c55e; font-weight:600; white-space:nowrap;">'
                                    f'{item["count"]} session{"s" if item["count"] != 1 else ""}</span></div>'
                                ).style("width: 100%;")

                    ui.separator()

                    with ui.column().classes("gap-2"):
                        ui.label("Legend").classes("font-semibold")
                        for color_hex, text in [
                            ("#2a2f38", "Not trained"),
                            ("#fde047", "1 training"),
                            ("#fb923c", "2 trainings"),
                            ("#ef4444", "3+ trainings"),
                        ]:
                            ui.html(
                                f'<div style="display:flex; align-items:center; gap:10px; font-size:13px; color:#d1d5db;">'
                                f'<span style="width:14px; height:14px; border-radius:50%; '
                                f'background:{color_hex}; box-shadow: 0 0 0 1px rgba(255,255,255,0.08), '
                                f'0 2px 4px rgba(0,0,0,0.3);"></span>{text}</div>'
                            )

                #right big heatmap
                with ui.element("div").style(
                    "display: flex; align-items: center; justify-content: flex-end; "
                    "overflow: hidden; flex: 1; padding-right: 10px; margin-left: 300px;"
                ):
                    # render the muscle heatmap SVG for the weekly summary
                    ui.html(build_heatmap_svg(result)).style(
                        "width: 200%; max-width: 1700px; height: 200%; max-height: 95vh; "
                        "display: flex; align-items: center; justify-content: center; "
                        "transform: scale(1.3);"
                    )

        #page shell fixed header + nav + scrollable content
        with ui.column().classes("w-full items-center").style(
            "height: 100vh; overflow: hidden; padding: 16px; gap: 8px;"
        ):
            #title + week navigation (always visible at top)
            with ui.element("div").style(
                "display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; "
                "gap: 16px; width: 100%; max-width: 1200px; flex-shrink: 0;"
            ):
                with ui.element("div").style("justify-self: start;"):
                    ui.label("Weekly Summary").classes("text-2xl font-bold")

                with ui.row().classes("items-center gap-2").style("justify-self: center;"):
                    def go_previous():
                        state["week_offset"] += 1
                        next_button.enabled = True
                        week_label.text = get_week_label()
                        week_display.refresh()

                    def go_next():
                        if state["week_offset"] > 0:
                            state["week_offset"] -= 1
                            if state["week_offset"] == 0:
                                next_button.enabled = False
                            week_label.text = get_week_label()
                            week_display.refresh()

                    ui.button(icon="arrow_back", on_click=go_previous).props("round flat")
                    week_label = ui.label(get_week_label())
                    next_button = ui.button(icon="arrow_forward", on_click=go_next).props("round flat")
                    next_button.enabled = False

                with ui.element("div").style("justify-self: end;"):
                    ui.button("Back", on_click=lambda: ui.navigate.to("/dashboard")).props("outline")

            #content card, fills remaining space, no outer scroll
            with ui.card().classes("w-full").style(
                "max-width: 1200px; flex: 1; overflow: hidden; display: flex; flex-direction: column;"
            ):
                with ui.column().style("flex: 1; overflow: hidden;"):
                    week_display()
        
    @ui.page("/pr-tracker")
    def pr_tracker_page():
        user_id, redirect = require_login()
        if redirect:
            return redirect
        ui.dark_mode().enable()
        ui.add_head_html(FULL_PAGE_STYLE)

        # load PR summaries and grouped PR history for the chart and table
        best_prs = workout_service.get_best_prs(user_id=user_id)
        all_prs_grouped = workout_service.get_all_prs_by_exercise(user_id=user_id)

        import json as _json

        js_data: dict = {}
        for ex, entries in all_prs_grouped.items():
            js_data[ex] = [
                {"date": e["date"].isoformat(), "kg": e["weight_kg"]}
                for e in entries
            ]

        CHART_JS_CDN = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"

        STOCK_PAGE_STYLE = """
        <style>
            .pr-tab-btn {
                padding: 6px 18px;
                border-radius: 999px;
                font-size: 13px;
                font-weight: 500;
                cursor: pointer;
                border: 1px solid rgba(255,255,255,0.1);
                background: rgba(255,255,255,0.02);
                color: #d1d5db;
                transition: all 0.2s ease;
            }
            .pr-tab-btn:hover {
                background: rgba(255,255,255,0.06);
                color: #fff;
            }
            .pr-tab-btn.active {
                background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
                color: #07140c;
                border-color: transparent;
                font-weight: 600;
                box-shadow: 0 4px 14px rgba(34,197,94,0.25);
            }
            .pr-stat-card {
                background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 12px;
                padding: 14px 18px;
                flex: 1;
                min-width: 110px;
                transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
            }
            .pr-stat-card:hover {
                border-color: rgba(34,197,94,0.4);
                background: linear-gradient(135deg, rgba(34,197,94,0.06) 0%, rgba(255,255,255,0.01) 100%);
                box-shadow: 0 0 0 1px rgba(34,197,94,0.15), 0 6px 18px rgba(0,0,0,0.25);
            }
            .pr-stat-label {
                font-size: 11px;
                color: #9ca3af;
                margin: 0 0 6px;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-weight: 600;
            }
            .pr-stat-value {
                font-size: 22px;
                font-weight: 700;
                margin: 0;
                color: #f3f4f6;
                letter-spacing: -0.02em;
            }
        </style>
        """

        CHART_HTML = """
<div id="pr-chart-root" style="padding: 0;">
  <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:16px;">
    <div class="pr-stat-card">
      <p class="pr-stat-label">Best PR</p>
      <p class="pr-stat-value" id="pr-val-best">—</p>
    </div>
    <div class="pr-stat-card">
      <p class="pr-stat-label">First PR</p>
      <p class="pr-stat-value" id="pr-val-first">—</p>
    </div>
    <div class="pr-stat-card">
      <p class="pr-stat-label">Progress</p>
      <p class="pr-stat-value" id="pr-val-progress">—</p>
    </div>
    <div class="pr-stat-card">
      <p class="pr-stat-label">Entries</p>
      <p class="pr-stat-value" id="pr-val-count">—</p>
    </div>
  </div>
  <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:14px;" id="pr-tabs"></div>
  <div style="position:relative; width:100%; height:280px;">
    <canvas id="prStockChart" role="img" aria-label="PR progress chart">No data.</canvas>
  </div>
  <div style="display:flex; align-items:center; gap:8px; margin-top:10px; font-size:12px; color:#888;">
    <span style="width:28px; height:2px; background:#22c55e; display:inline-block; border-radius:2px;"></span>
    PR history (kg)
  </div>
</div>
"""

        js_data_json = _json.dumps(js_data)

        CHART_SCRIPT = f"""
<script src="{CHART_JS_CDN}"></script>
<script>
function initPrChart() {{
  var DATA = {js_data_json};
  var exercises = Object.keys(DATA);
  var currentEx = exercises[0] || null;
  var chart = null;

  function fmt(d) {{
    var dt = new Date(d);
    return dt.toLocaleDateString('de-DE', {{day:'2-digit', month:'short', year:'2-digit'}});
  }}

  function renderStats(entries) {{
    if (!entries || entries.length === 0) return;
    var best = Math.max.apply(null, entries.map(function(e){{return e.kg;}}));
    var first = entries[0].kg;
    var diff = parseFloat((best - first).toFixed(1));
    var pct  = first > 0 ? (diff / first * 100).toFixed(1) : 0;
    var up   = diff >= 0;
    document.getElementById('pr-val-best').textContent    = best + ' kg';
    document.getElementById('pr-val-first').textContent   = first + ' kg';
    document.getElementById('pr-val-count').textContent   = entries.length;
    document.getElementById('pr-val-progress').innerHTML  =
      '<span style="color:' + (up ? '#22c55e' : '#ef4444') + '">' +
      (up ? '+' : '') + diff + ' kg (' + (up ? '+' : '') + pct + '%)</span>';
  }}

  function renderChart(exName) {{
    var entries = DATA[exName] || [];
    var labels  = entries.map(function(e){{ return fmt(e.date); }});
    var values  = entries.map(function(e){{ return e.kg; }});
    var up      = values.length < 2 || values[values.length-1] >= values[0];
    var lineCol = up ? '#22c55e' : '#ef4444';
    var fillCol = up ? 'rgba(34,197,94,0.07)' : 'rgba(239,68,68,0.07)';

    renderStats(entries);

    if (chart) {{ chart.destroy(); chart = null; }}

    var canvas = document.getElementById('prStockChart');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    chart = new Chart(ctx, {{
      type: 'line',
      data: {{
        labels: labels,
        datasets: [{{
          label: exName + ' (kg)',
          data: values,
          borderColor: lineCol,
          backgroundColor: fillCol,
          borderWidth: 2,
          fill: true,
          tension: 0.35,
          pointBackgroundColor: lineCol,
          pointBorderColor: '#fff',
          pointBorderWidth: 1.5,
          pointRadius: 5,
          pointHoverRadius: 7,
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{
            callbacks: {{
              label: function(c) {{ return ' ' + c.parsed.y + ' kg'; }}
            }}
          }}
        }},
        scales: {{
          x: {{
            grid: {{ color: 'rgba(128,128,128,0.12)' }},
            ticks: {{ color: '#888', font: {{ size: 12 }}, maxRotation: 30,
                      autoSkip: true, maxTicksLimit: 8 }}
          }},
          y: {{
            grid: {{ color: 'rgba(128,128,128,0.12)' }},
            ticks: {{
              color: '#888',
              font: {{ size: 12 }},
              callback: function(v) {{ return v + ' kg'; }}
            }}
          }}
        }}
      }}
    }});
  }}

  function renderTabs() {{
    var container = document.getElementById('pr-tabs');
    if (!container) return;
    container.innerHTML = '';
    exercises.forEach(function(name) {{
      var btn = document.createElement('button');
      btn.textContent = name;
      btn.className = 'pr-tab-btn' + (name === currentEx ? ' active' : '');
      btn.addEventListener('click', function() {{
        currentEx = name;
        renderTabs();
        renderChart(name);
      }});
      container.appendChild(btn);
    }});
  }}

  if (exercises.length > 0) {{
    renderTabs();
    renderChart(currentEx);
  }} else {{
    var root = document.getElementById('pr-chart-root');
    if (root) root.innerHTML =
      '<p style="color:#888; padding:32px 0;">No PRs recorded yet. Add weight in your next workout!</p>';
  }}
}}

setTimeout(initPrChart, 300);
</script>
"""

        with ui.column().classes("w-full items-center").style(
            "height: 100vh; overflow: hidden; padding: 16px; gap: 12px;"
        ):
            with ui.row().classes("items-center justify-between w-full").style(
                "max-width: 1100px; flex-shrink: 0;"
            ):
                ui.label("PR Tracker").classes("text-3xl font-bold")
                ui.button("Back", on_click=lambda: ui.navigate.to("/dashboard")).props("outline")

            with ui.element("div").style(
                "max-width: 1100px; width: 100%; flex: 1; display: flex; "
                "gap: 20px; overflow: hidden;"
            ):
                #left Stock chart
                with ui.card().classes("w-full").style(
                    "flex: 1.2; overflow: hidden; display: flex; flex-direction: column;"
                ):
                    ui.add_head_html(STOCK_PAGE_STYLE)
                    ui.add_body_html(CHART_SCRIPT)
                    ui.html(CHART_HTML).style("flex: 1; overflow: hidden;")

                #right PR table
                with ui.card().classes("w-full").style(
                    "flex: 1; overflow-y: auto; min-width: 460px;"
                ):
                    ui.label("All PRs").classes("text-lg font-semibold mb-2")

                    if not best_prs:
                        ui.label(
                            "No PRs yet. Enter a weight in your next workout!"
                        ).classes("text-gray-500")
                    else:
                        columns = [
                            {"name": "exercise", "label": "Exercise", "field": "exercise", "sortable": True},
                            {"name": "weight_kg", "label": "Best (kg)", "field": "weight_kg", "sortable": True},
                            {"name": "date", "label": "Date", "field": "date"},
                            {"name": "actions", "label": "", "field": "actions"},
                        ]
                        rows = [
                            {
                                "id": pr["id"],
                                "exercise": pr["exercise"],
                                "weight_kg": pr["weight_kg"],
                                "date": pr["date"].strftime("%d.%m.%Y"),
                                "date_iso": pr["date"].isoformat(),
                            }
                            for pr in best_prs
                        ]
                        table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full")

                        def edit_pr(ev):
                            row = ev.args
                            # open dialog for editing an existing PR entry
                            with ui.dialog() as dialog, ui.card().classes("p-6 w-full max-w-sm"):
                                ui.label(f"Edit PR — {row['exercise']}").classes("text-xl font-bold")
                                ui.separator()
                                weight_input = ui.input(
                                    "Weight (kg)",
                                    value=str(row["weight_kg"]),
                                    placeholder="Enter new weight",
                                ).props("type=number")
                                date_input = ui.input(
                                    "Recorded Date",
                                    value=row["date_iso"],
                                ).props(f"type=date max={date.today().isoformat()}")

                                def save_pr_edit():
                                    try:
                                        workout_service.update_pr(
                                            pr_id=row["id"],
                                            user_id=user_id,
                                            weight_kg=float(weight_input.value),
                                            recorded_date=date.fromisoformat(
                                                str(date_input.value).replace("/", "-")
                                            ),
                                        )
                                        ui.notify("PR updated!", type="positive")
                                        dialog.close()
                                        ui.navigate.to("/pr-tracker")
                                    except ValueError as e:
                                        ui.notify(str(e), type="negative")

                                with ui.row().classes("justify-end gap-2"):
                                    ui.button("Cancel", on_click=dialog.close).props("outline")
                                    ui.button("Save", on_click=save_pr_edit)
                            dialog.open()

                        def delete_pr(ev):
                            row = ev.args
                            # confirm and delete a PR entry from the user's history
                            with ui.dialog() as dialog, ui.card().classes("p-4"):
                                ui.label(f"Delete {row['exercise']} PR?").classes("text-lg font-semibold")
                                ui.label("This action cannot be undone.").classes("text-sm text-gray-500")
                                with ui.row().classes("w-full justify-end gap-2"):
                                    ui.button("Cancel", on_click=dialog.close).props("flat")
                                    ui.button(
                                        "Delete",
                                        color="negative",
                                        on_click=lambda: execute_pr_deletion(row["id"], dialog),
                                    )
                            dialog.open()

                        def execute_pr_deletion(pr_id: int, dialog):
                            try:
                                workout_service.delete_pr(pr_id=pr_id, user_id=user_id)
                                ui.notify("PR deleted", type="positive")
                                dialog.close()
                                ui.navigate.to("/pr-tracker")
                            except ValueError as e:
                                ui.notify(str(e), type="negative")

                        table.on("edit_pr", edit_pr)
                        table.on("delete_pr", delete_pr)
                        table.add_slot(
                            "body-cell-actions",
                            """
                            <q-td :props="props">
                                <q-btn dense flat icon="edit" @click="$parent.$emit('edit_pr', props.row)" />
                                <q-btn dense flat icon="delete" @click="$parent.$emit('delete_pr', props.row)" />
                            </q-td>
                            """,
                        )

    @ui.page("/weight-tracker")
    def weight_tracker_page():
        user_id, redirect = require_login()
        if redirect:
            return redirect
        ui.dark_mode().enable()
        ui.add_head_html(FULL_PAGE_STYLE)

        # load weight tracking entries and the current goal for this user
        entries = weight_service.list_entries(user_id)
        current_goal = weight_service.get_goal(user_id)

        with ui.column().classes("w-full items-center").style(
            "height: 100vh; overflow: hidden; padding: 16px; gap: 12px;"
        ):
            #header
            with ui.row().classes("items-center justify-between w-full").style(
                "max-width: 900px; flex-shrink: 0;"
            ):
                ui.label("Weight Tracker").classes("text-3xl font-bold")
                ui.button("Back", on_click=lambda: ui.navigate.to("/dashboard")).props("outline")

            with ui.card().classes("w-full").style(
                "max-width: 900px; flex: 1; overflow-y: auto; padding: 20px;"
            ):
                #3 metric cards
                latest = entries[0]["weight_kg"] if entries else None
                start = entries[-1]["weight_kg"] if entries else None

                with ui.row().classes("w-full gap-4 mb-4"):
                    with ui.card().classes("flex-1 items-center").style(
                        "background: #1e1e1e; text-align: center; padding: 16px;"
                    ):
                        ui.label("Current").classes("text-sm text-gray-400")
                        ui.label(f"{latest} kg" if latest else "—").classes("text-2xl font-bold")

                    with ui.card().classes("flex-1 items-center").style(
                        "background: #1e1e1e; text-align: center; padding: 16px;"
                    ):
                        ui.label("Goal").classes("text-sm text-gray-400")
                        ui.label(f"{current_goal} kg" if current_goal else "—").classes("text-2xl font-bold")

                    with ui.card().classes("flex-1 items-center").style(
                        "background: #1e1e1e; text-align: center; padding: 16px;"
                    ):
                        ui.label("Remaining").classes("text-sm text-gray-400")
                        if latest and current_goal:
                            diff = round(latest - current_goal, 1)
                            if diff > 0:
                                diff_text = f"Lose {diff} kg"
                                diff_color = "#ef4444"
                            elif diff < 0:
                                diff_text = f"Gain {abs(diff)} kg"
                                diff_color = "#3b82f6"
                            else:
                                diff_text = "Goal reached!"
                                diff_color = "#22c55e"
                            ui.label(diff_text).classes("text-2xl font-bold").style(f"color: {diff_color};")
                        else:
                            ui.label("—").classes("text-2xl font-bold")

                #progress bar
                if latest and current_goal and start:
                    if start != current_goal:
                        total_diff = abs(start - current_goal)
                        current_diff = abs(latest - current_goal)
                        progress = max(0.0, min(1.0, 1.0 - (current_diff / total_diff)))
                    else:
                        progress = 1.0

                    with ui.card().classes("w-full mb-4").style("background: #1e1e1e; padding: 16px;"):
                        ui.label("Progress to goal").classes("text-sm text-gray-400 mb-1")
                        ui.linear_progress(value=progress, show_value=False).props("color=green size=10px")

                ui.separator()

                #goal + new entry
                with ui.row().classes("w-full gap-6 mt-4 mb-4 items-end"):
                    with ui.column().classes("gap-1"):
                        ui.label("Goal Weight").classes("text-sm text-gray-400")
                        goal_input = ui.input(
                            "kg",
                            value=str(current_goal) if current_goal else "",
                            placeholder="e.g. 75",
                        ).props("type=number").style("width: 100px")

                        def save_goal():
                            # save or update the user's weight goal
                            try:
                                if not goal_input.value:
                                    ui.notify("Please enter a target weight.", type="warning")
                                    return
                                weight_service.set_goal(user_id, float(goal_input.value))
                                ui.notify("Goal saved!", type="positive")
                                ui.navigate.to("/weight-tracker")
                            except ValueError as e:
                                ui.notify(str(e), type="negative")

                        ui.button("Save", on_click=save_goal).props("outline")

                    with ui.column().classes("gap-1"):
                        ui.label("New Entry").classes("text-sm text-gray-400")
                        with ui.row().classes("gap-2 items-end"):
                            date_input = ui.input("Date", value=date.today().isoformat()).props(f"type=date max={date.today().isoformat()}")
                            weight_input = ui.input(
                                "Weight (kg)", placeholder="e.g. 81.5"
                            ).props("type=number").style("width: 120px")

                            def add_entry():
                                # add a new weight log entry for the current user
                                try:
                                    if not weight_input.value:
                                        ui.notify("Please enter a weight.", type="warning")
                                        return
                                    entry_date = date.fromisoformat(
                                        str(date_input.value).replace("/", "-")
                                    )
                                    weight_service.add_entry(
                                        user_id=user_id,
                                        entry_date=entry_date,
                                        weight_kg=float(weight_input.value),
                                    )
                                    ui.notify("Entry saved!", type="positive")
                                    ui.navigate.to("/weight-tracker")
                                except ValueError as e:
                                    ui.notify(str(e), type="negative")

                            ui.button("Add", on_click=add_entry)

                ui.separator()

                #history
                ui.label("History").classes("text-lg font-semibold mt-4")

                if not entries:
                    ui.label("No entries yet. Enter your first weight!").classes("text-gray-500 mt-2")
                else:
                    columns = [
                        {"name": "date", "label": "Date", "field": "date", "sortable": True},
                        {"name": "weight_kg", "label": "Weight (kg)", "field": "weight_kg", "sortable": True},
                        {"name": "diff", "label": "Weight away from Goal", "field": "diff"},
                        {"name": "actions", "label": "", "field": "actions"},
                    ]

                    rows = []
                    for e in entries:
                        diff_to_goal = round(e["weight_kg"] - current_goal, 1) if current_goal else None
                        if diff_to_goal is None:
                            diff_str = "—"
                        elif diff_to_goal > 0:
                            diff_str = f"Lose {diff_to_goal} kg"
                        elif diff_to_goal < 0:
                            diff_str = f"Gain {abs(diff_to_goal)} kg"
                        else:
                            diff_str = "Goal reached!"
                        rows.append({
                            "id": e["id"],
                            "date": e["date"].strftime("%d.%m.%Y"),
                            "weight_kg": e["weight_kg"],
                            "diff": diff_str,
                        })

                    table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full")

                    def delete_entry(ev):
                        row = ev.args
                        with ui.dialog() as dialog, ui.card().classes("p-4"):
                            ui.label(f"Delete entry from {row['date']}?").classes("text-lg font-semibold")
                            with ui.row().classes("w-full justify-end gap-2"):
                                ui.button("Cancel", on_click=dialog.close).props("flat")
                                ui.button(
                                    "Delete",
                                    color="negative",
                                    on_click=lambda: execute_delete(row["id"], dialog),
                                )
                        dialog.open()

                    def execute_delete(entry_id: int, dialog):
                        try:
                            weight_service.delete_entry(entry_id, user_id)
                            ui.notify("Entry deleted", type="positive")
                            dialog.close()
                            ui.navigate.to("/weight-tracker")
                        except ValueError as e:
                            ui.notify(str(e), type="negative")

                    table.on("delete_entry", delete_entry)
                    table.add_slot(
                        "body-cell-actions",
                        """
                        <q-td :props="props">
                            <q-btn dense flat icon="delete" @click="$parent.$emit('delete_entry', props.row)" />
                        </q-td>
                        """,
                    )

    from ui.admin_pages import configure_admin_pages
    configure_admin_pages(
        admin_service=admin_service,
        require_admin=require_admin,
        set_current_user_id=set_current_user_id,
        full_page_style=FULL_PAGE_STYLE,
    )
