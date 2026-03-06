from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ["email", "username", "is_staff", "is_admin"]
    fieldsets = UserAdmin.fieldsets + (
        (None, {"fields": ("phone", "address", "is_admin")}),
    )
    ordering = ["email"]

admin.site.register(User, CustomUserAdmin)