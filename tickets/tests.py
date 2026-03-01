from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Role, UserRole, RoleName, Category, Priority, Ticket, TicketStatus

User = get_user_model()

class TicketWorkflowTests(TestCase):
    def setUp(self):
        self.role_admin = Role.objects.create(role_name=RoleName.ADMIN)
        self.role_tech = Role.objects.create(role_name=RoleName.TECHNICIAN)
        self.role_rep = Role.objects.create(role_name=RoleName.REPORTER)

        self.admin = User.objects.create_user(username="admin1", password="pass")
        UserRole.objects.create(user=self.admin, role=self.role_admin)

        self.tech = User.objects.create_user(username="tech1", password="pass")
        UserRole.objects.create(user=self.tech, role=self.role_tech)

        self.rep = User.objects.create_user(username="rep1", password="pass")
        UserRole.objects.create(user=self.rep, role=self.role_rep)

        self.cat = Category.objects.create(name="IT", is_active=True)
        self.pri = Priority.objects.create(name="High", rank=3)

    def test_ticket_created_starts_new(self):
        t = Ticket(title="A", description="B", category=self.cat, priority=self.pri, reporter=self.rep)
        t.initialise_status(self.rep, TicketStatus.NEW)
        t.save()
        self.assertEqual(t.status, TicketStatus.NEW)

    def test_cannot_close_from_in_progress(self):
        t = Ticket.objects.create(title="A", description="B", category=self.cat, priority=self.pri, reporter=self.rep)
        t.status = TicketStatus.IN_PROGRESS
        with self.assertRaises(ValidationError):
            t.change_status(TicketStatus.CLOSED, self.admin)

    def test_assign_technician_sets_assignee(self):
        t = Ticket.objects.create(title="A", description="B", category=self.cat, priority=self.pri, reporter=self.rep)
        t.assign_technician(self.tech, self.admin)
        self.assertEqual(t.assignee, self.tech)
        self.assertIsNotNone(t.assigned_at)
