from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import get_user_model

from .forms import TicketCreateForm, AssignTechnicianForm
from .models import (
    Ticket,
    StatusHistory,
    TicketStatus,
    RoleName,
    user_has_role,
    Category,
    Priority,
)

User = get_user_model()


@login_required
def ticket_list(request):
    """
    Role-based ticket list:
    - Admin: all tickets
    - Technician: assigned tickets
    - Reporter: reported tickets
    Supports filtering via GET params.
    """
    qs = Ticket.objects.select_related("reporter", "assignee", "category", "priority").order_by("-created_at")

    if user_has_role(request.user, RoleName.ADMIN):
        base_qs = qs
        list_title = "All Tickets"
    elif user_has_role(request.user, RoleName.TECHNICIAN):
        base_qs = qs.filter(assignee=request.user)
        list_title = "Assigned Tickets"
    else:
        base_qs = qs.filter(reporter=request.user)
        list_title = "My Tickets"

    status = request.GET.get("status", "").strip()
    category = request.GET.get("category", "").strip()
    priority = request.GET.get("priority", "").strip()
    q = request.GET.get("q", "").strip()

    if status:
        base_qs = base_qs.filter(status=status)
    if category:
        base_qs = base_qs.filter(category_id=category)
    if priority:
        base_qs = base_qs.filter(priority_id=priority)
    if q:
        base_qs = base_qs.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(reporter__username__icontains=q)
            | Q(assignee__username__icontains=q)
        )

    context = {
        "tickets": base_qs,
        "title": list_title,
        "filters": {"status": status, "category": category, "priority": priority, "q": q},
        "categories": Category.objects.filter(is_active=True).order_by("name"),
        "priorities": Priority.objects.all().order_by("rank", "name"),
        "statuses": TicketStatus.choices,
    }
    return render(request, "tickets/ticket_list.html", context)


@login_required
def ticket_create(request):
    if request.method == "POST":
        form = TicketCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                ticket: Ticket = form.save(commit=False)
                ticket.reporter = request.user
                ticket.initialise_status(request.user, TicketStatus.NEW)
                ticket.save()

                StatusHistory.objects.create(
                    ticket=ticket,
                    from_status=None,
                    to_status=TicketStatus.NEW,
                    changed_by=request.user,
                )

            messages.success(request, f"Ticket created (#{ticket.id}).")
            return redirect("ticket_detail", ticket_id=ticket.id)
    else:
        form = TicketCreateForm()

    return render(request, "tickets/ticket_create.html", {"form": form})


@login_required
def ticket_detail(request, ticket_id: int):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    return render(request, "tickets/ticket_detail.html", {"ticket": ticket})


@login_required
def ticket_assign_technician(request, ticket_id: int):
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    # Allow superuser OR Admin role
    if not (request.user.is_superuser or user_has_role(request.user, RoleName.ADMIN)):
        raise PermissionDenied("Only Admin can assign technicians.")

    # Keep your original idea: technicians by role OR staff users
    tech_qs = User.objects.filter(
        Q(user_role__role__role_name=RoleName.TECHNICIAN) | Q(is_staff=True)
    ).distinct().order_by("username")

    # If no technicians exist, don't crash / don't show empty form
    if not tech_qs.exists():
        messages.error(
            request,
            "No technicians are available to assign. Create a technician user (or set a user as staff/technician role) first."
        )
        return redirect("ticket_detail", ticket_id=ticket.id)

    if request.method == "POST":
        form = AssignTechnicianForm(request.POST, tech_qs=tech_qs)
        if form.is_valid():
            technician = form.cleaned_data["technician"]

            # Avoid 500s: show a message if the ticket cannot transition
            if not ticket.can_transition_to(TicketStatus.OPEN):
                messages.error(
                    request,
                    f"Cannot assign technician because the ticket cannot move to Open from '{ticket.status}'."
                )
                return redirect("ticket_detail", ticket_id=ticket.id)

            try:
                with transaction.atomic():
                    from_status = ticket.status
                    ticket.assign_technician(technician, request.user)
                    ticket.change_status(TicketStatus.OPEN, request.user)
                    ticket.save()

                    StatusHistory.objects.create(
                        ticket=ticket,
                        from_status=from_status,
                        to_status=TicketStatus.OPEN,
                        changed_by=request.user,
                    )

                messages.success(request, f"Assigned {technician.username} and set status to Open.")
                return redirect("ticket_detail", ticket_id=ticket.id)

            except Exception as e:
                # Last-resort safety: never 500 the user in production
                messages.error(request, f"Assign failed: {e}")
                return redirect("ticket_detail", ticket_id=ticket.id)
    else:
        form = AssignTechnicianForm(tech_qs=tech_qs)

    return render(request, "tickets/ticket_assign.html", {"ticket": ticket, "form": form})