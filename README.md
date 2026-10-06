# Task Manager

Jira-style task management app with a Django REST API and a React frontend.

```
Task-Manager/
  backend/     Django REST Framework API
  frontend/    React (Vite) UI
```

---

## Backend

See paths and setup details under `backend/`.

```bash
cd backend
uv sync
# ensure backend/.env exists (SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASE_URL)
uv run python manage.py migrate
uv run python manage.py loaddata users organization department projects tasks comments   # optional
uv run python manage.py runserver
```

API base: `http://127.0.0.1:8000/api/`  
Docs: `http://127.0.0.1:8000/api/docs/`

Seeded admin (from fixtures): `admin@example.com` / `Admin1234!`

---

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:5173`. Vite proxies `/api` to the Django server.

### What's included

- Login / register
- Projects list + create
- Kanban board (drag issues between To Do / In Progress / Done)
- Backlog (filterable issue list)
- Issue detail (status, priority, assignee, due date, comments + replies)
- Project settings (edit, members, delete)
- Organizations & departments
- Admin user management
- Small **ⓘ** icons next to actions — hover to see the exact API method + path

---

## Tech

| Layer | Stack |
|---|---|
| Backend | Django 6, DRF, Token auth, django-filter, PostgreSQL, django-cors-headers |
| Frontend | React 19, React Router, Vite |

Python imports still use `apps.*` and `config.*` — run Django commands from `backend/`.
# Task
