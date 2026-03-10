from django.conf import settings
from django.core.management.base import BaseCommand

from domainamer.services.watchlist import process_queued_watchlist_jobs
from domainamer.views import _get_orchestrator


class Command(BaseCommand):
    help = "Process queued watchlist check jobs."

    def handle(self, *args, **options):
        batch_size = int(getattr(settings, "WATCHLIST_JOB_BATCH_SIZE", 20))
        orchestrator = _get_orchestrator()
        processed = process_queued_watchlist_jobs(
            availability_resolver=orchestrator.check,
            batch_size=batch_size,
        )
        self.stdout.write(self.style.SUCCESS(f"Processed {processed} watchlist jobs"))
