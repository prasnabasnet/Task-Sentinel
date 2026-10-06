from django.db.models import Count, Q
from django.utils import timezone


def dashboard_callback(request, context):
    """
    Callback function for Django Unfold dashboard to inject KPI metric cards
    and summary statistics into the admin index context.
    """
    try:
        from apps.users.models import User
        from apps.projects.models import Project
        from apps.tasks.models import Task
        from apps.organization.models import Organization

        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        total_projects = Project.objects.count()
        
        total_tasks = Task.objects.count()
        todo_tasks = Task.objects.filter(status=Task.Status.TODO).count()
        in_progress_tasks = Task.objects.filter(status=Task.Status.IN_PROGRESS).count()
        done_tasks = Task.objects.filter(status=Task.Status.DONE).count()
        urgent_tasks = Task.objects.filter(
            Q(priority=Task.Priority.CRITICAL) | Q(priority=Task.Priority.HIGH),
            ~Q(status=Task.Status.DONE)
        ).count()

        total_orgs = Organization.objects.count()

        context.update({
            "kpi_metrics": [
                {
                    "title": "Total Users",
                    "metric": total_users,
                    "footer": f"{active_users} active users",
                    "icon": "group",
                },
                {
                    "title": "Active Projects",
                    "metric": total_projects,
                    "footer": f"Across {total_orgs} organization(s)",
                    "icon": "folder",
                },
                {
                    "title": "Tasks Progress",
                    "metric": f"{done_tasks}/{total_tasks}",
                    "footer": f"{in_progress_tasks} in progress, {todo_tasks} to do",
                    "icon": "check_circle",
                },
                {
                    "title": "High Priority Tasks",
                    "metric": urgent_tasks,
                    "footer": "Requires attention",
                    "icon": "warning",
                },
            ]
        })
    except Exception:
        # Prevent dashboard failure during initial migrations or DB issues
        pass

    return context


def badge_tasks_count(request):
    """Callback for Tasks sidebar badge count (pending/in-progress tasks)."""
    try:
        from apps.tasks.models import Task
        count = Task.objects.exclude(status=Task.Status.DONE).count()
        return str(count) if count > 0 else ""
    except Exception:
        return ""


def badge_projects_count(request):
    """Callback for Projects sidebar badge count."""
    try:
        from apps.projects.models import Project
        count = Project.objects.count()
        return str(count) if count > 0 else ""
    except Exception:
        return ""


def badge_users_count(request):
    """Callback for Users sidebar badge count."""
    try:
        from apps.users.models import User
        count = User.objects.filter(is_active=True).count()
        return str(count) if count > 0 else ""
    except Exception:
        return ""
