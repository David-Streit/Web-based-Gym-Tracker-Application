from __future__ import annotations
from datetime import date
from urllib.parse import quote
from nicegui import ui


def configure_admin_pages(admin_service, require_admin, set_current_user_id, full_page_style: str):
    """Admin area: search a user by name and edit or delete their entries."""

    TABS = ["Workouts", "PRs", "Weight", "Exercises"]

    def _user_url(username: str, tab: str | None = None) -> str:
        url = f"/admin/user/{quote(username, safe='')}"
        return f"{url}?tab={tab}" if tab else url

    def _logout():
        set_current_user_id(None)
        ui.navigate.to("/")

    def _metric(label: str, value: str):
        with ui.card().classes("flex-1 items-center").style(
            "background: #1e1e1e; text-align: center; padding: 16px; min-width: 140px;"
        ):
            ui.label(label).classes("text-sm text-gray-400")
            ui.label(value).classes("text-2xl font-bold")

    def _empty(text: str):
        ui.label(text).classes("text-gray-500 mt-2")

    def _parse_date(value) -> date:
        return date.fromisoformat(str(value).replace("/", "-"))

    def _parse_kg(value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValueError("Please enter a valid weight in kg.")

    def _confirm_delete(text: str, action, reload):
        """Shared confirmation dialog for every delete button."""
        with ui.dialog() as dialog, ui.card().classes("p-4"):
            ui.label(text).classes("text-lg font-semibold")
            ui.label("This cannot be undone.").classes("text-sm text-gray-400")

            def run():
                try:
                    action()
                    ui.notify("Deleted", type="positive")
                    dialog.close()
                    reload()
                except (ValueError, PermissionError) as e:
                    ui.notify(str(e), type="negative")

            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                ui.button("Delete", color="negative", on_click=run)
        dialog.open()

    def _edit_dialog(title: str, build_fields, save, reload):
        """Shared edit dialog: build_fields() creates the inputs and returns them, save(fields) stores."""
        with ui.dialog() as dialog, ui.card().classes("p-4").style("min-width: 360px;"):
            ui.label(title).classes("text-lg font-semibold")
            fields = build_fields()

            def run():
                try:
                    save(fields)
                    ui.notify("Saved", type="positive")
                    dialog.close()
                    reload()
                except (ValueError, PermissionError) as e:
                    ui.notify(str(e), type="negative")

            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                ui.button("Save", on_click=run)
        dialog.open()

    def _actions_slot(table, prefix: str):
        table.add_slot(
            "body-cell-actions",
            f"""
            <q-td :props="props">
                <q-btn dense flat icon="edit" @click="$parent.$emit('{prefix}_edit', props.row)" />
                <q-btn dense flat icon="delete" @click="$parent.$emit('{prefix}_delete', props.row)" />
            </q-td>
            """,
        )

    def _date_input(value: date):
        today = date.today().isoformat()
        return ui.input("Date", value=value.isoformat()).props(f"type=date max={today} outlined").classes("w-full")

    def _kg_input(label: str, value):
        return ui.input(label, value=str(value) if value is not None else "").props(
            "type=number step=0.5 outlined"
        ).classes("w-full")

    # ------------------------------------------------------------------ search
    @ui.page("/admin")
    def admin_page():
        admin_id, redirect = require_admin()
        if redirect:
            return redirect
        ui.dark_mode().enable()
        ui.add_head_html(full_page_style)

        with ui.column().classes("w-full items-center").style(
            "height: 100vh; overflow: hidden; padding: 16px; gap: 12px;"
        ):
            with ui.row().classes("items-center justify-between w-full").style(
                "max-width: 900px; flex-shrink: 0;"
            ):
                with ui.column().classes("gap-0"):
                    ui.label("Admin").classes("text-3xl font-bold")
                    ui.label("Find a user and manage their entries").classes("text-sm text-gray-400")
                ui.button("Logout", on_click=_logout).props("flat")

            with ui.card().classes("w-full").style(
                "max-width: 900px; flex: 1; overflow-y: auto; padding: 20px;"
            ):
                def open_user(username: str):
                    try:
                        admin_service.get_user_entries(admin_id, username)
                        ui.navigate.to(_user_url(username.strip()))
                    except (ValueError, PermissionError) as e:
                        ui.notify(str(e), type="negative")

                with ui.row().classes("w-full gap-2 items-end"):
                    search_input = ui.input(
                        "Search username", placeholder="e.g. max"
                    ).props("outlined clearable autofocus").classes("flex-1")
                    ui.button("Open", on_click=lambda: open_user(search_input.value or ""))

                ui.label("Users").classes("text-lg font-semibold mt-4")

                columns = [
                    {"name": "username", "label": "Username", "field": "username", "sortable": True, "align": "left"},
                    {"name": "workout_count", "label": "Workouts", "field": "workout_count", "sortable": True},
                    {"name": "actions", "label": "", "field": "actions"},
                ]

                def build_rows(query: str) -> list[dict]:
                    return admin_service.search_users(admin_id, query)

                table = ui.table(columns=columns, rows=build_rows(""), row_key="id").classes("w-full")
                table.props('no-data-label="No users match this name."')
                table.add_slot(
                    "body-cell-actions",
                    """
                    <q-td :props="props">
                        <q-btn dense flat icon="manage_accounts" @click.stop="$parent.$emit('open_user', props.row)" />
                    </q-td>
                    """,
                )
                table.on("open_user", lambda ev: ui.navigate.to(_user_url(ev.args["username"])))
                table.on("row-click", lambda ev: ui.navigate.to(_user_url(ev.args[1]["username"])))

                # the list filters while typing; Enter opens the exact username
                def refresh_table():
                    table.rows = build_rows(search_input.value or "")
                    table.update()

                search_input.on_value_change(lambda _: refresh_table())
                search_input.on("keydown.enter", lambda: open_user(search_input.value or ""))

    # ------------------------------------------------------------ one user
    @ui.page("/admin/user/{username}")
    def admin_user_page(username: str, tab: str = "Workouts"):
        admin_id, redirect = require_admin()
        if redirect:
            return redirect
        ui.dark_mode().enable()
        ui.add_head_html(full_page_style)

        try:
            data = admin_service.get_user_entries(admin_id, username)
        except (ValueError, PermissionError) as e:
            with ui.column().classes("w-full items-center").style("padding: 32px; gap: 12px;"):
                ui.label(str(e)).classes("text-lg")
                ui.button("Back to search", on_click=lambda: ui.navigate.to("/admin")).props("outline")
            return

        user = data["user"]
        user_id = user["id"]
        workouts = data["workouts"]
        prs = data["personal_records"]
        weights = data["weight_entries"]
        goal = data["weight_goal"]
        exercises = data["exercises"]
        muscles = admin_service.list_muscles(admin_id)

        def reload(tab_name: str):
            return lambda: ui.navigate.to(_user_url(user["username"], tab_name))

        with ui.column().classes("w-full items-center").style(
            "height: 100vh; overflow: hidden; padding: 16px; gap: 12px;"
        ):
            with ui.row().classes("items-center justify-between w-full").style(
                "max-width: 900px; flex-shrink: 0;"
            ):
                with ui.column().classes("gap-0"):
                    ui.label(user["username"]).classes("text-3xl font-bold")
                    ui.label("Manage this user's entries").classes("text-sm text-gray-400")
                with ui.row().classes("gap-2"):
                    ui.button("Back to search", on_click=lambda: ui.navigate.to("/admin")).props("outline")
                    ui.button("Logout", on_click=_logout).props("flat")

            with ui.card().classes("w-full").style(
                "max-width: 900px; flex: 1; overflow-y: auto; padding: 20px;"
            ):
                with ui.row().classes("w-full gap-4 mb-4"):
                    _metric("Workouts", str(len(workouts)))
                    _metric("Last workout", workouts[0]["date"].strftime("%d.%m.%Y") if workouts else "—")
                    _metric("Current weight", f"{weights[0]['weight_kg']} kg" if weights else "—")
                    _metric("Goal", f"{goal} kg" if goal else "—")

                with ui.tabs().classes("w-full") as tabs:
                    tab_elements = {name: ui.tab(name) for name in TABS}

                start_tab = tab_elements.get(tab, tab_elements["Workouts"])
                with ui.tab_panels(tabs, value=start_tab).classes("w-full").style("background: transparent;"):

                    # ---------------- workouts
                    with ui.tab_panel(tab_elements["Workouts"]):
                        if not workouts:
                            _empty("No workouts logged.")
                        else:
                            by_id = {w["id"]: w for w in workouts}
                            table = ui.table(
                                columns=[
                                    {"name": "date", "label": "Date", "field": "date", "sortable": True, "align": "left"},
                                    {"name": "muscles", "label": "Muscles", "field": "muscles", "align": "left"},
                                    {"name": "notes", "label": "Notes", "field": "notes", "align": "left"},
                                    {"name": "actions", "label": "", "field": "actions"},
                                ],
                                rows=[
                                    {
                                        "id": w["id"],
                                        "date": w["date"].strftime("%d.%m.%Y"),
                                        "muscles": ", ".join(w["muscle_names"]),
                                        "notes": w.get("notes") or "",
                                    }
                                    for w in workouts
                                ],
                                row_key="id",
                                pagination=15,
                            ).classes("w-full")
                            _actions_slot(table, "workout")

                            def edit_workout(ev):
                                w = by_id[ev.args["id"]]

                                def fields():
                                    d = _date_input(w["date"])
                                    n = ui.textarea("Notes", value=w.get("notes") or "").props("autogrow outlined").classes("w-full")
                                    ui.label("Muscles trained").classes("text-sm text-gray-400 mt-2")
                                    boxes = []
                                    with ui.row().classes("gap-x-4 gap-y-0"):
                                        for m in muscles:
                                            boxes.append((m["id"], ui.checkbox(m["name"], value=m["id"] in w["muscle_ids"])))
                                    return d, n, boxes

                                def save(f):
                                    d, n, boxes = f
                                    admin_service.update_workout(
                                        admin_id, user_id, w["id"],
                                        workout_date=_parse_date(d.value),
                                        notes=n.value or None,
                                        muscle_ids=[mid for mid, cb in boxes if cb.value],
                                    )

                                _edit_dialog(f"Edit workout from {ev.args['date']}", fields, save, reload("Workouts"))

                            table.on("workout_edit", edit_workout)
                            table.on("workout_delete", lambda ev: _confirm_delete(
                                f"Delete workout from {ev.args['date']}?",
                                lambda: admin_service.delete_workout(admin_id, user_id, ev.args["id"]),
                                reload("Workouts"),
                            ))

                    # ---------------- personal records
                    with ui.tab_panel(tab_elements["PRs"]):
                        if not prs:
                            _empty("No personal records.")
                        else:
                            pr_by_id = {}
                            rows = []
                            for exercise_name, records in prs.items():
                                best = max(records, key=lambda r: r["weight_kg"])
                                for r in reversed(records):  # newest first
                                    pr_by_id[r["id"]] = r
                                    rows.append({
                                        "id": r["id"],
                                        "exercise": exercise_name,
                                        "weight_kg": r["weight_kg"],
                                        "date": r["date"].strftime("%d.%m.%Y"),
                                        "best": "★" if r["id"] == best["id"] else "",
                                    })
                            table = ui.table(
                                columns=[
                                    {"name": "exercise", "label": "Exercise", "field": "exercise", "sortable": True, "align": "left"},
                                    {"name": "weight_kg", "label": "Weight (kg)", "field": "weight_kg", "sortable": True},
                                    {"name": "date", "label": "Date", "field": "date", "align": "left"},
                                    {"name": "best", "label": "Best", "field": "best"},
                                    {"name": "actions", "label": "", "field": "actions"},
                                ],
                                rows=rows,
                                row_key="id",
                                pagination=15,
                            ).classes("w-full")
                            _actions_slot(table, "pr")

                            def edit_pr(ev):
                                r = pr_by_id[ev.args["id"]]

                                def fields():
                                    return _kg_input("Weight (kg)", r["weight_kg"]), _date_input(r["date"])

                                def save(f):
                                    kg, d = f
                                    admin_service.update_pr(admin_id, user_id, r["id"], _parse_kg(kg.value), _parse_date(d.value))

                                _edit_dialog(f"Edit PR: {ev.args['exercise']}", fields, save, reload("PRs"))

                            table.on("pr_edit", edit_pr)
                            table.on("pr_delete", lambda ev: _confirm_delete(
                                f"Delete {ev.args['exercise']} PR ({ev.args['weight_kg']} kg, {ev.args['date']})?",
                                lambda: admin_service.delete_pr(admin_id, user_id, ev.args["id"]),
                                reload("PRs"),
                            ))

                    # ---------------- body weight
                    with ui.tab_panel(tab_elements["Weight"]):
                        with ui.row().classes("items-end gap-2 mb-4"):
                            goal_input = ui.input(
                                "Goal (kg)", value=str(goal) if goal else ""
                            ).props("type=number step=0.5 outlined").style("width: 140px;")

                            def save_goal():
                                try:
                                    admin_service.set_weight_goal(admin_id, user_id, _parse_kg(goal_input.value))
                                    ui.notify("Goal saved", type="positive")
                                    reload("Weight")()
                                except (ValueError, PermissionError) as e:
                                    ui.notify(str(e), type="negative")

                            ui.button("Save goal", on_click=save_goal).props("outline")

                        if not weights:
                            _empty("No weight entries.")
                        else:
                            entry_by_id = {e["id"]: e for e in weights}
                            table = ui.table(
                                columns=[
                                    {"name": "date", "label": "Date", "field": "date", "sortable": True, "align": "left"},
                                    {"name": "weight_kg", "label": "Weight (kg)", "field": "weight_kg", "sortable": True},
                                    {"name": "actions", "label": "", "field": "actions"},
                                ],
                                rows=[
                                    {"id": e["id"], "date": e["date"].strftime("%d.%m.%Y"), "weight_kg": e["weight_kg"]}
                                    for e in weights
                                ],
                                row_key="id",
                                pagination=15,
                            ).classes("w-full")
                            _actions_slot(table, "weight")

                            def edit_weight(ev):
                                e = entry_by_id[ev.args["id"]]

                                def fields():
                                    return _date_input(e["date"]), _kg_input("Weight (kg)", e["weight_kg"])

                                def save(f):
                                    d, kg = f
                                    admin_service.update_weight_entry(
                                        admin_id, user_id, e["id"], _parse_date(d.value), _parse_kg(kg.value)
                                    )

                                _edit_dialog(f"Edit weight entry from {ev.args['date']}", fields, save, reload("Weight"))

                            table.on("weight_edit", edit_weight)
                            table.on("weight_delete", lambda ev: _confirm_delete(
                                f"Delete weight entry from {ev.args['date']}?",
                                lambda: admin_service.delete_weight_entry(admin_id, user_id, ev.args["id"]),
                                reload("Weight"),
                            ))

                    # ---------------- custom exercises
                    with ui.tab_panel(tab_elements["Exercises"]):
                        with ui.row().classes("items-end gap-2 mb-4"):
                            new_exercise = ui.input("New exercise").props("outlined").style("width: 240px;")

                            def add_exercise():
                                try:
                                    admin_service.create_exercise(admin_id, user_id, new_exercise.value or "")
                                    ui.notify("Exercise added", type="positive")
                                    reload("Exercises")()
                                except (ValueError, PermissionError) as e:
                                    ui.notify(str(e), type="negative")

                            ui.button("Add", on_click=add_exercise).props("outline")

                        if not exercises:
                            _empty("No custom exercises.")
                        else:
                            table = ui.table(
                                columns=[
                                    {"name": "name", "label": "Exercise", "field": "name", "sortable": True, "align": "left"},
                                    {"name": "actions", "label": "", "field": "actions"},
                                ],
                                rows=exercises,
                                row_key="id",
                                pagination=15,
                            ).classes("w-full")
                            table.add_slot(
                                "body-cell-actions",
                                """
                                <q-td :props="props">
                                    <q-btn dense flat icon="delete" @click="$parent.$emit('exercise_delete', props.row)" />
                                </q-td>
                                """,
                            )
                            table.on("exercise_delete", lambda ev: _confirm_delete(
                                f"Delete exercise '{ev.args['name']}'?",
                                lambda: admin_service.delete_exercise(admin_id, user_id, ev.args["id"]),
                                reload("Exercises"),
                            ))
