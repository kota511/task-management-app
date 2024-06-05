from django.contrib import admin
from .models import User, Team, Task, Invitation

# Register your models here.

"""Configure admin interface for the user model"""
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'username', 'first_name', 'last_name', 'email', 'is_active'
    ]

"""Configure admin interface for teams model"""
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'owner', 'created_at'
    ]

"""Configure admin interface for task model"""
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'due_date', 'team', 'assigned_to', 'status', 'priority', 'created_at', 'updated_at'
    ]

"""Configure admin interface for invitation model"""
@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = [
        'team', 'sender', 'recipient', 'created_at'
    ]