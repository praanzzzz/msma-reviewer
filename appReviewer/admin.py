from django.contrib import admin
from .models import CustomUser, Category, Scenario, Question
from django.contrib.auth.admin import UserAdmin


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = (
        ("Personal Information", {"fields": ("email", "password", "profile_picture")}),
        ("Permissions",{"fields": ("is_active","is_verified","is_subscribed","is_staff","is_superuser")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    list_display = (
        "email",
        "id",
        "is_active",
        "is_verified",
        "is_subscribed",
        "last_login",
        "date_joined",
    )

    search_fields = (
        "id",
        "email",
    )

    ordering = ("id",)

    # def has_add_permissions(self, request):
    #     return False

    # def has_delete_permissions(self, request, onj=None)
    #     return False


admin.site.register(Category)
admin.site.register(Scenario)
admin.site.register(Question)
admin.site.register(CustomUser, CustomUserAdmin)
