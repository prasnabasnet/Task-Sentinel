# Backend Changelog - B2B Multi-Tenant System Refactoring

## 1. Role & Identity Updates (`apps.users`)
- **Updated `RoleChoices`**:
  - `SUPERADMIN` ("Super Admin"): Platform administrator.
  - `ORG_ADMIN` ("Org Admin"): Owner & admin of a specific organization.
  - `PM` ("Project Manager"): Manager scoped to assigned department(s).
  - `TM` ("Team Member"): Member scoped to assigned tasks and projects.
- **Minimal Public Registration (`RegisterUserService`)**:
  - Requires `email`, `username`, `password`, and `organization_name`.
  - Atomically creates a `User` with role `ORG_ADMIN` and an `Organization` owned by them.
  - Adds the new user to `OrganizationMember`.
- **Direct Onboarding (`CreateMemberService`)**:
  - Created `CreateMemberService` accessible via `POST /api/users/members/`.
  - Enables `ORG_ADMIN` to directly create `PM` or `TM` users inside their organization.
  - Optionally links new users to a department via `department_id`.
  - Triggers a Celery background task (`send_member_welcome_email_task`) in `apps.shared.tasks` to email credentials (`email` and `raw_password`).

## 2. Permissions (`apps.users.permissions.py`)
- **Updated `IsAdminOrOrgOwner`**:
  - Acts as primary access check.
  - Grants access if user is `SUPERADMIN` / superuser, OR if `ORG_ADMIN` belongs to / owns the organization associated with the request or target object.
- **Updated `IsAdmin`**:
  - Checks for `SUPERADMIN`, `ORG_ADMIN`, or `is_superuser`.

## 3. Scoping & Boundary Enforcement Logic

### Hierarchy Rules
- **ORG_ADMIN**:
  - Can view and manage all departments, projects, and tasks under their organization (`department__organization`).
- **PM (Project Manager)**:
  - Can create projects and tasks within their assigned department (`department__head` or `department__members`).
  - Restricted from creating projects outside their department scope.
- **TM (Team Member)**:
  - Can only view tasks assigned to them (`assignees`).
  - Updating task attributes restricted exclusively to `status` and `priority`.
  - Restricted from creating tasks or projects.

### Scoping Implementations Across Services & Views
- `apps.projects.views.project.ProjectViewSet.get_queryset()`:
  - Scopes project queries based on tenant (`ORG_ADMIN`), department (`PM`), or task assignment/membership (`TM`).
- `apps.projects.services.CreateProjectService`:
  - Enforces `PM` department ownership/membership when creating projects.
- `apps.tasks.views.task.TaskViewSet.get_queryset()`:
  - Filters tasks strictly by organization for `ORG_ADMIN`, department for `PM`, and direct assignment (`assignees`) for `TM`.
- `apps.tasks.services.CreateTaskService` & `UpdateTaskService`:
  - Restricts task creation to `ORG_ADMIN` and department `PM`s.
  - Restricts `TM` updates strictly to `status` and `priority`.
