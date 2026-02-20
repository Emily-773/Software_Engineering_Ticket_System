from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    Role, UserRole, Category, Priority, Ticket, Comment, Attachment, StatusHistory
)

admin.site.register(Role)
admin.site.register(UserRole)
admin.site.register(Category)
admin.site.register(Priority)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "reporter", "assignee", "category", "priority", "created_at")
    list_filter = ("status", "category", "priority")
    search_fields = ("title", "description", "reporter__username", "assignee__username")

admin.site.register(Comment)
admin.site.register(Attachment)
admin.site.register(StatusHistory)
