from django.contrib import admin

from .models import DomainAlertEvent, DomainWatchItem, WatchlistCheckJob


@admin.register(DomainWatchItem)
class DomainWatchItemAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "base_name", "tlds", "canonical_tlds", "is_active", "last_checked_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("base_name", "owner__username")


@admin.register(DomainAlertEvent)
class DomainAlertEventAdmin(admin.ModelAdmin):
    list_display = ("id", "domain", "previous_status", "current_status", "checked_at", "created_at")
    list_filter = ("current_status", "previous_status")
    search_fields = ("domain",)


@admin.register(WatchlistCheckJob)
class WatchlistCheckJobAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "status", "created_at", "started_at", "completed_at")
    list_filter = ("status",)
    search_fields = ("owner__username",)
