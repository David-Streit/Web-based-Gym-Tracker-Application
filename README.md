# Gym Progress Tracker - Web Edition

**Current stage:** Milestone 1 - design draft. This README is updated throughout the project; we do not start a separate document for each milestone.

Later sections (implementation, execution, integration) will be added from the fourth theory session onwards. For now, this document records our design draft, decisions and open questions.

## Project overview

The Gym Progress Tracker is an application for recreational lifters who want to record what they actually lift (exercises, sets, weight and reps) and see how their training develops over time. Most people track progress with photos or memory; few write down numbers, so they cannot tell whether they are progressing, stagnating or neglecting muscle groups.

We are **not starting from zero**. In the Advanced Programming module our group built a local Python application with NiceGUI, SQLAlchemy and SQLite: [georgvondembussche/Advanced_Programming](https://github.com/georgvondembussche/Advanced_Programming). It already supports registration/login, workout sessions with trained muscle groups, a weekly muscle heatmap, personal records (PRs) and body-weight tracking.

In this module we transform it into a proper **web-based application**:

- a documented **REST API** (FastAPI, as in class) that exposes the existing business logic and data independently of the user interface,
- a web frontend that is usable **on a phone in the gym** as well as on desktop (frontend technology still undecided, see section 3),
- a small number of **new features**, starting with logging exercises and sets inside a workout (see *Initial scope*).

### Team and initial responsibilities

| Member | Initial responsibility | Next action |
|---|---|---|
| David Streit | Coordination and README | Keep decisions, questions and the milestone commit together; set up the new repository |
| Benno Busche | Users and workflow | Refine the "log a workout" workflow and the user stories below |
| Tim Freyvogel | Sketches and interaction | Sketch mobile screens for the workflow (new workout, add sets, confirmation) |
| Georg von dem Bussche | Data and API exploration | Maintain the sample JSON in `docs/examples/` and map existing services to proposed operations |

These are starting responsibilities, not permanent silos. Everyone reviews each other's work and should be able to explain the whole draft. Responsibilities will be rotated as needed.

## 1. Analysis

### Scenario, users and goals

- **Situation or problem:** Lifters train several times a week but rarely record numbers. Without a record of weight and reps they cannot apply progressive overload deliberately, do not notice plateaus and do not see which muscle groups they neglect. Spreadsheets and paper notes are inconvenient to use between sets.
- **Intended users:**
  - *Beginner lifter* - wants structure and a simple way to log a session without a spreadsheet.
  - *Intermediate lifter* - wants to see per-exercise progress, PRs and weekly training balance to decide when to increase weight or volume.
  - Each user only sees their own data; there is no public content in the first scope (an optional public landing page may follow).
- **Proposed benefit:** Logging a session takes a minute on a phone; the app turns the logged sets into useful feedback (weekly muscle heatmap, volume, new PRs) instead of the user having to calculate it.
- **What exists from Advanced Programming:**
  - The current version stores a workout session as *date + notes + selected muscle groups* (one session per day). Exercises exist as a per-user list, and PRs are entered manually on a separate page. **Sets, weight and reps are not yet stored per session**, so progress cannot be derived from training data.
  - The UI and logic run in one NiceGUI process; there is no API that another client could use.
- **Initial scope:** *Log a workout session with exercises and sets* - create, view, edit and delete one's own sessions through the API, and see the result in the weekly overview. This is the core entity for the API minimum (CRUD with business rules and access checks).
- **Can wait:** automatic PR detection from logged sets, progress charts per exercise based on sets, body-weight tracker migration, workout templates/routines, rest timer, CSV export, admin-managed global exercise library, integrations (e.g. Strava).

### User stories

1. As a **lifter**, I want to register and log in, so that my training data stays private.
2. As a **lifter**, I want to log a workout with the exercises, sets, weight and reps I did, so that I have an exact record of my training instead of relying on memory.
3. As a **lifter**, I want to edit or delete a logged workout, so that I can correct mistakes made between sets.
4. As a **lifter**, I want to see my workouts of the current week and a muscle heatmap, so that I notice which muscle groups I am neglecting.
5. As a **lifter**, I want to add my own exercises with a muscle group, so that I can log machines or variations that are not in the default list.
6. As a **lifter**, I want to use the app on my phone in the gym, so that I can log sets right after doing them.
7. *(later)* As a **lifter**, I want the app to tell me when a logged set is a new personal record, so that I don't have to maintain PRs separately.

**Outside the initial scope:** nutrition/calorie tracking, social features (sharing, following), trainer/coach roles, payment.

### First workflow: log a workout session

| Step | User / role | Action | Information needed | Expected result or feedback |
|---|---|---|---|---|
| 1 | Lifter | Logs in | Username, password | Dashboard with recent sessions; error message on invalid credentials |
| 2 | Lifter | Opens "New workout" | Workout date (defaults to today) | Empty session form; warning if a session already exists for that date (offer to open it instead) |
| 3 | Lifter | Adds an exercise | Exercise from own list (search/select) | Exercise card appears, showing its muscle group |
| 4 | Lifter | Adds sets to the exercise | Weight in kg (decimal), reps (whole number) | Set row is listed with its number; inline error if reps ≤ 0 or weight < 0 |
| 5 | Lifter | Repeats steps 3–4, optionally adds notes | Further exercises and sets, notes | Running summary: number of sets, total volume, muscle groups hit |
| 6 | Lifter | Saves the workout | Complete session | Confirmation with the saved session; dashboard and weekly heatmap updated |
| 7 | Lifter | Opens the weekly overview | Current week (default) | Sessions of the week and heatmap with intensity per muscle group |

**Exceptions worth discussing:**

- *Exercise not in the list* — should the lifter be able to create it inline during step 3 (faster in the gym) or only on the exercise page (simpler)?
- *Session already exists for that date* — the current app rejects a second session per day. Lifters who train twice a day (e.g. cardio in the morning, weights in the evening) cannot record this. Keep the rule or drop it?
- *Lost connection while logging in the gym* — should unsaved sets be kept in the browser until the save succeeds?
- *Exercise deleted later* — what happens to past sessions that reference it (block deletion, or keep history and hide the exercise)?

## 2. Design

### Screens and navigation

The existing NiceGUI screens are our starting point (see screenshots in the [Advanced Programming repository](https://github.com/georgvondembussche/Advanced_Programming/tree/main/static/New%20UI)): login, register, dashboard, new/edit workout, weekly summary with heatmap, PR tracker and weight tracker.

For the first workflow we are sketching three **mobile-first** screens (sketches will be added to `docs/sketches/`):

1. **New workout** - date picker (today preselected), "Add exercise" button with a searchable list, notes field.
   *Feedback:* warning banner if a session for this date already exists.
2. **Exercise card with sets** - one card per exercise, each with a compact row per set (weight, reps) and an "Add set" button that copies the previous set's values to save typing. Large touch targets for use between sets.
   *Feedback:* inline validation per field; running total of sets and volume at the bottom.
3. **Saved / summary** - confirmation, list of exercises and sets, muscle groups hit, link to the weekly overview.
   *Feedback:* clear error message if saving failed, with the entered data still on screen.

Navigation: a bottom navigation bar on mobile (Dashboard · New workout · Week · Profile) and a side or top bar on desktop, consistent across all pages.

### Domain concepts and example data

Sample JSON (fictional data) is stored in [`docs/examples/`](docs/examples/):

- [`exercises.json`](docs/examples/exercises.json) — muscle groups and a user's exercise list
- [`workout-session-request.json`](docs/examples/workout-session-request.json) — what the client sends to create a workout
- [`workout-session-response.json`](docs/examples/workout-session-response.json) — what the server returns after saving

Create request (excerpt):

```json
{
  "workout_date": "2026-09-28",
  "notes": "Push day, last bench set to failure",
  "entries": [
    {
      "exercise_id": 12,
      "sets": [
        { "weight_kg": 70.0, "reps": 8 },
        { "weight_kg": 75.0, "reps": 6 }
      ]
    }
  ]
}
```

**Important fields and references:**

| Concept | Fields (type) | References / notes |
|---|---|---|
| User | `id` (int), `username` (string), password hash | Owner of all other data. Not part of request bodies: the user is taken from the login, so nobody can write into another user's data by changing an ID. |
| MuscleGroup | `id` (int), `name` (string), `svg_key` (string) | Fixed list of 7 groups seeded by the app (Legs, Chest, Back, Shoulders, Biceps, Triceps, Abs); `svg_key` links to the body heatmap. |
| Exercise | `id` (int), `name` (string), `muscle_group_id` (int), `is_custom` (bool) | **New:** each exercise gets a primary muscle group. Currently exercises have no muscle group. |
| WorkoutSession | `id` (int), `workout_date` (date, ISO `YYYY-MM-DD`), `notes` (string, optional) | Belongs to one user. Existing entity. |
| Set (*new*) | `set_number` (int), `weight_kg` (float), `reps` (int) | Belongs to one session **and** one exercise. Grouped by exercise as `entries` in JSON. |
| Derived values | `muscle_groups`, `total_volume_kg`, `new_personal_records` | Calculated by the server, not sent by the client. Volume = Σ weight × reps. |

**Uncertainties:**

- Should the muscle groups of a session be **derived from its exercises** (proposed) or still selected manually as in the current version? Deriving them removes double input but loses sessions without exercises (e.g. "quick leg day, didn't log details").
- One muscle group per exercise is a simplification (a bench press also trains triceps and shoulders). Secondary muscle groups would make the heatmap more accurate but the data model more complex.
- Should default exercises be **global** (shared by all users, `is_custom: false`) or copied per user? The current version stores them per user.
- Bodyweight exercises (pull-ups): store `weight_kg: 0` or the added weight only?

### Business rules and possible operations

**Rules (draft, in plain language):**

- A workout date may not be in the future. *(existing rule)*
- A workout must contain at least one exercise with at least one set. *(replaces the existing rule "select at least one muscle group")*
- Reps must be a whole number ≥ 1; weight must be ≥ 0 kg (0 = bodyweight) and below a plausibility limit (e.g. 500 kg) to catch typos.
- An exercise used in a workout must belong to the logged-in user (or be a default exercise).
- Users can only read, change and delete their own workouts, exercises and records; another user's ID returns "not found".
- *Exception:* a session for the same date already exists → currently rejected; open question whether to allow it.
- *Exception:* a logged set is heavier than the stored best for that exercise → the save still succeeds and the response lists it as a new PR (later feature).

Today these rules are enforced in the service layer (`services/workout_service.py` raises `ValueError`). The plan is to keep them there so that both the API and the web interface use the same checks; where exactly each rule is enforced will be documented at milestone 2.

**Proposed operations (draft, not final endpoints):**

| User goal | Proposed action | Example input | Expected output | Open question |
|---|---|---|---|---|
| Log in | Create a login session/token | Username, password | Confirmation and access to own data; error on wrong credentials | Session cookie or token? (wait for security sessions) |
| See my exercises | Read list of exercises | – | Default and custom exercises with muscle group | Global defaults or per user? |
| Add a custom exercise | Create exercise | Name, muscle group | New exercise with ID; error if name already exists | Inline creation during logging? |
| Log a workout | Create workout session | Date, notes, exercises with sets (see JSON) | Saved session with ID, volume, muscle groups | Allow two sessions per day? |
| Review my history | Read list of my sessions | Optional date range | Sessions, newest first | Paging needed? |
| Inspect one workout | Read one session | Session ID | Session with all sets | – |
| Correct a mistake | Change a session | Session ID, updated date/notes/sets | Updated session; validation errors as above | Replace all sets at once or edit single sets? |
| Remove a workout | Remove a session | Session ID | Confirmation; session no longer listed | Undo option in the UI? |
| See weekly balance | Read weekly summary | Any date in the week | Sessions, count and intensity per muscle group | Week starts Monday (current implementation) |

Workout sessions are the **core entity** for which the API will provide full CRUD. Exercises are a second candidate; PRs and body weight already exist and can be added to the API later.

### Inspiration from existing apps or APIs - optional

- **Strong / Hevy** (mobile workout loggers): the "add set copies the previous set" interaction and large inputs designed for use between sets are what we want to adopt for our mobile screens. We want to improve on them by putting the weekly muscle balance (heatmap) front and centre rather than hiding it in statistics.
- **wger** (open-source workout manager with a public REST API, [wger.de](https://wger.de)): its exercise data links exercises to primary and secondary muscles, which is relevant to our open question about secondary muscle groups. We do not plan to integrate it.

## 3. Project management

### Decisions, open questions and next steps

| Question / decision | Current position | Next step / person |
|---|---|---|
| Which application do we build? | **Decided:** extend the Gym Progress Tracker from Advanced Programming instead of a new idea | Confirm with lecturer at design coaching |
| Repository | Start a **new repository** for this module and reuse code from the old one. Do not copy `.venv/`, `.nicegui/` user storage or `data/gym_tracker.db` (contains account data/password hashes); add them to `.gitignore` | [Name] |
| Backend technology | Draft: FastAPI (as in class), reusing the existing SQLAlchemy models and service layer | Decide after milestone 2 introduction |
| Frontend technology | **Undecided:** (a) keep NiceGUI and let it call our API or services, (b) server-rendered templates (Jinja2) with FastAPI, (c) separate JavaScript frontend | Decide after the integration classes; must work well on mobile |
| How to store sets, weight and reps | Proposed new `Set` entity linked to session and exercise | Draw updated ERD - [Name] |
| Muscle groups per session | Proposed: derive from exercises instead of manual selection | Discuss in coaching |
| Two sessions per day | Undecided (currently forbidden) | Ask users in our circle / coaching |
| PR tracking | Keep manual PR page for now; automatic detection from sets is a later feature | Revisit after milestone 2 |
| Database | SQLite stays for local reproducibility | Revisit only if we deploy publicly |

### Milestone progress

| Milestone | Available evidence | Status / next step |
|---|---|---|
| 1 - Design draft | This README (analysis, workflow, operations), sample JSON in `docs/examples/`, existing screenshots from Advanced Programming; sketches in `docs/sketches/` | Sketches to be added before coaching; record coaching feedback here |
| 2 - Contract and available implementation | OpenAPI contract and implemented/tested progress | [Update later] |
| Integration - later | Revised feature scope, frontend decision, architecture and a connected workflow | [Update after classroom examples; details in Moodle] |

Contributions and decisions are described in this README; commit counts do not measure individual effort.

## 4. References and acknowledgements

- **Previous project:** [Gym Progress Tracker (Advanced Programming, FS26)](https://github.com/georgvondembussche/Advanced_Programming) - our own earlier work; data model, services, validation rules, heatmap and screenshots are reused and adapted here.
- **Libraries (current version):** NiceGUI, SQLAlchemy, pytest. Planned: FastAPI (classroom path).
- **Inspiration:** Strong, Hevy, wger (see section 2).
- **Course material:** Web-based Applications HS26 lecture slides and README template.
- **AI assistance:** Claude was used to draft this README and the sample JSON from our existing repository and the course template; the content was reviewed and adapted by the team.

Template lineage: the earlier [Pizzeria Reference Project](https://github.com/FHNW-INT/Pizzeria_Reference_Project) organised documentation around analysis, design, implementation, execution and project management. This template updates that structure for the HS26 Python/FastAPI teaching path.

