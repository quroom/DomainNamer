from django.db import models


class DomainWatchItem(models.Model):
    base_name = models.CharField(max_length=63)
    tlds = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    last_statuses = models.JSONField(default=dict)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
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
