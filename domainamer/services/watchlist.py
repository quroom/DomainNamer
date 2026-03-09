from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Iterable

from .availability import AvailabilityDecision
from ..models import DomainAlertEvent, DomainWatchItem

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
