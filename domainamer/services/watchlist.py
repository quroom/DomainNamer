from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Iterable

from .availability import AvailabilityDecision
from django.utils import timezone as dj_timezone

from ..models import DomainAlertEvent, DomainWatchItem, WatchlistCheckJob

AvailabilityResolver = Callable[[str], AvailabilityDecision]


def run_watchlist_check(
    watch_items: Iterable[DomainWatchItem],
    availability_resolver: AvailabilityResolver,
    checked_at: datetime | None = None,
) -> dict[str, int]:
    checked_at = checked_at or datetime.now(timezone.utc)
    summary = {
        "processed_items": 0,
        "checked_domains": 0,
        "alerts_created": 0,
    }

    for item in watch_items:
        previous_statuses = dict(item.last_statuses or {})
        next_statuses = dict(previous_statuses)

        for tld in item.tlds:
            domain = f"{item.base_name}.{tld}"
            decision = availability_resolver(domain)
            current_status = decision.status
            previous_status = previous_statuses.get(domain, "unknown")

            if previous_status == "unavailable" and current_status == "available":
                DomainAlertEvent.objects.create(
                    watch_item=item,
                    domain=domain,
                    previous_status=previous_status,
                    current_status=current_status,
                    checked_at=checked_at,
                )
                summary["alerts_created"] += 1

            next_statuses[domain] = current_status
            summary["checked_domains"] += 1

        item.last_statuses = next_statuses
        item.last_checked_at = checked_at
        item.save(update_fields=["last_statuses", "last_checked_at", "updated_at"])
        summary["processed_items"] += 1

    return summary


def process_watchlist_check_job(
    job: WatchlistCheckJob,
    availability_resolver: AvailabilityResolver,
) -> WatchlistCheckJob:
    started_at = dj_timezone.now()
    job.status = WatchlistCheckJob.STATUS_RUNNING
    job.started_at = started_at
    job.error_message = ""
    job.save(update_fields=["status", "started_at", "error_message", "updated_at"])

    try:
        items = DomainWatchItem.objects.filter(owner=job.owner, is_active=True).order_by("id")
        summary = run_watchlist_check(items, availability_resolver=availability_resolver, checked_at=started_at)
        job.summary = summary
        job.status = WatchlistCheckJob.STATUS_SUCCEEDED
        job.completed_at = dj_timezone.now()
        job.save(update_fields=["summary", "status", "completed_at", "updated_at"])
    except Exception as exc:
        job.status = WatchlistCheckJob.STATUS_FAILED
        job.error_message = str(exc)
        job.completed_at = dj_timezone.now()
        job.save(update_fields=["status", "error_message", "completed_at", "updated_at"])

    return job


def process_queued_watchlist_jobs(
    availability_resolver: AvailabilityResolver,
    batch_size: int = 20,
) -> int:
    processed = 0
    queued_jobs = WatchlistCheckJob.objects.filter(status=WatchlistCheckJob.STATUS_QUEUED).order_by("created_at")[
        :batch_size
    ]
    for job in queued_jobs:
        process_watchlist_check_job(job, availability_resolver=availability_resolver)
        processed += 1
    return processed
