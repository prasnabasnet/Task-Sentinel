from django.db import models


class Task(models.Model):

    class Status(models.TextChoices):
        TODO = 'TODO', 'To Do'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        DONE = 'DONE', 'Done'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    class IssueType(models.TextChoices):
        TASK = 'TASK', 'Task'
        BUG = 'BUG', 'Bug / Defect'

    class Severity(models.TextChoices):
        CRITICAL = 'CRITICAL', 'Critical'
        MAJOR = 'MAJOR', 'Major'
        MINOR = 'MINOR', 'Minor'
        TRIVIAL = 'TRIVIAL', 'Trivial'

    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='tasks')

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)

    issue_type = models.CharField(
        max_length=20, 
        choices=IssueType.choices, 
        default=IssueType.TASK
    )
    severity = models.CharField(
        max_length=20, 
        choices=Severity.choices, 
        default=Severity.MINOR, 
        blank=True, 
        null=True
    )

    steps_to_reproduce = models.TextField(blank=True, null=True)
    expected_behavior = models.TextField(blank=True, null=True)
    actual_behavior = models.TextField(blank=True, null=True)
    environment = models.CharField(max_length=255, blank=True, null=True)

    assignees = models.ManyToManyField('users.User', related_name='assigned_tasks', blank=True)

    created_by = models.ForeignKey('users.User', on_delete=models.PROTECT, related_name='created_tasks')

    due_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        db_table = 'tasks_task'

    def __str__(self):
        return f"[{self.status}] {self.title} (Priority: {self.priority})"

