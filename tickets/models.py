from __future__ import annotations

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class RoleName(models.TextChoices):
    ADMIN = "Admin", "Admin"
    TECHNICIAN = "Technician", "Technician"
    REPORTER = "Reporter", "Reporter"


class TicketStatus(models.TextChoices):
    NEW = "New", "New"
    OPEN = "Open", "Open"
    IN_PROGRESS = "In Progress", "In Progress"
    RESOLVED = "Resolved", "Resolved"
    CLOSED = "Closed", "Closed"
    REOPENED = "Reopened", "Reopened"


class Role(models.Model):
    role_name = models.CharField(max_length=32, choices=RoleName.choices, unique=True)

    def __str__(self) -> str:
        return self.role_name


class UserRole(models.Model):
    """
    Links Django's built-in User to exactly one Role (matches your UML).
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_role")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="users")

    def __str__(self) -> str:
        return f"{self.user} -> {self.role}"


def user_has_role(user, role_name: str) -> bool:
    # Allow Django superusers to act as Admin in the app (important for Render demo)
    if getattr(user, "is_superuser", False) and role_name == RoleName.ADMIN:
        return True

    return hasattr(user, "user_role") and user.user_role.role.role_name == role_name


class Category(models.Model):
    ...
    name = models.CharField(max_length=80, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class Priority(models.Model):
    name = models.CharField(max_length=20, unique=True)  # Low/Medium/High/Critical
    rank = models.PositiveIntegerField(default=1)

    def __str__(self) -> str:
        return self.name


class Ticket(models.Model):
    title = models.CharField(max_length=120)
    description = models.TextField()

    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.NEW)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_at = models.DateTimeField(null=True, blank=True)

    # reporter (mandatory)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reported_tickets"
    )
    # assignee (optional 0..1)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="assigned_tickets"
    )

    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    priority = models.ForeignKey(Priority, on_delete=models.PROTECT)

    def __str__(self) -> str:
        return f"#{self.id} {self.title}"

    # ---------- Lifecycle rules (matches your state machine) ----------

    def can_transition_to(self, new_status: str) -> bool:
        allowed = {
            TicketStatus.NEW: {TicketStatus.OPEN},
            TicketStatus.OPEN: {TicketStatus.IN_PROGRESS, TicketStatus.CLOSED},
            TicketStatus.IN_PROGRESS: {TicketStatus.RESOLVED},
            TicketStatus.RESOLVED: {TicketStatus.CLOSED, TicketStatus.REOPENED},
            TicketStatus.CLOSED: {TicketStatus.REOPENED},
            TicketStatus.REOPENED: {TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED},
        }
        return new_status in allowed.get(self.status, set())

    def initialise_status(self, changed_by, initial_status: str = TicketStatus.NEW) -> None:
        """
        Creation-time initialisation (your polished sequence diagram).
        """
        if self.pk is not None:
            raise ValidationError("initialise_status can only be used on unsaved tickets.")
        self.status = initial_status

    def change_status(self, new_status: str, changed_by) -> None:
        if not self.can_transition_to(new_status):
            raise ValidationError(f"Invalid transition: {self.status} -> {new_status}")
        self.status = new_status

    def assign_technician(self, technician, assigned_by) -> None:
        if not user_has_role(technician, RoleName.TECHNICIAN):
            raise ValidationError("Assignee must have Technician role.")
        self.assignee = technician
        self.assigned_at = timezone.now()


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"Comment {self.id} on Ticket {self.ticket_id}"


class Attachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="attachments")
    file = models.FileField(upload_to="attachments/")
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"Attachment {self.id} on Ticket {self.ticket_id}"


class StatusHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=20, choices=TicketStatus.choices, null=True, blank=True)
    to_status = models.CharField(max_length=20, choices=TicketStatus.choices)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="status_changes")
    changed_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.ticket_id}: {self.from_status} -> {self.to_status}"
