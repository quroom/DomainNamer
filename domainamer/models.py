from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class DomainWatchItem(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="domain_watch_items", null=True, blank=True)
    base_name = models.CharField(max_length=63)
    tlds = models.JSONField(default=list)
    canonical_tlds = models.CharField(max_length=255, default="")
    is_active = models.BooleanField(default=True)
    last_statuses = models.JSONField(default=dict)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner", "is_active"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "base_name", "canonical_tlds"],
                name="uq_watch_owner_base_tlds",
            ),
        ]

    def __str__(self) -> str:
        tlds = ",".join(self.tlds)
        return f"{self.base_name} ({tlds})"


class DomainAlertEvent(models.Model):
    watch_item = models.ForeignKey(
        DomainWatchItem,
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    domain = models.CharField(max_length=255)
    previous_status = models.CharField(max_length=32)
    current_status = models.CharField(max_length=32)
    checked_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["domain", "created_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.domain}: {self.previous_status} -> {self.current_status}"


class WatchlistCheckJob(models.Model):
    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_QUEUED, "Queued"),
        (STATUS_RUNNING, "Running"),
        (STATUS_SUCCEEDED, "Succeeded"),
        (STATUS_FAILED, "Failed"),
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlist_check_jobs")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    summary = models.JSONField(default=dict)
    error_message = models.TextField(blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"WatchlistCheckJob<{self.id}>:{self.owner_id}:{self.status}"
