from django.urls import path
from . import views

urlpatterns = [
    path("tickets/", views.ticket_list, name="ticket_list"),
    path("tickets/create/", views.ticket_create, name="ticket_create"),
    path("tickets/<int:ticket_id>/", views.ticket_detail, name="ticket_detail"),
    path("tickets/<int:ticket_id>/assign/", views.ticket_assign_technician, name="ticket_assign"),
]