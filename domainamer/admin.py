from django.contrib import admin

from .models import DomainAlertEvent, DomainWatchItem


@admin.register(DomainWatchItem)
class DomainWatchItemAdmin(admin.ModelAdmin):
    list_display = ("id", "base_name", "tlds", "is_active", "last_checked_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("base_name",)


@admin.register(DomainAlertEvent)
class DomainAlertEventAdmin(admin.ModelAdmin):
    list_display = ("id", "domain", "previous_status", "current_status", "checked_at", "created_at")
    list_filter = ("current_status", "previous_status")
    search_fields = ("domain",)
