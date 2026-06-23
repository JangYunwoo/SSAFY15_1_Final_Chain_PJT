from django.core.management.base import BaseCommand

from analyses.models import GmsConnectionState


class Command(BaseCommand):
    help = "Re-enable GMS calls after its gateway has been verified."

    def handle(self, *args, **options):
        state, _ = GmsConnectionState.objects.get_or_create(pk=1)
        state.is_circuit_open = False
        state.failure_count = 0
        state.last_error = ""
        state.save(update_fields=["is_circuit_open", "failure_count", "last_error", "updated_at"])
        self.stdout.write(self.style.SUCCESS("GMS calls re-enabled."))
