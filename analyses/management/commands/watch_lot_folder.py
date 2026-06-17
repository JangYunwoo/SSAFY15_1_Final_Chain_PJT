import shutil
import time
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from analyses.services.batch_analyzer import create_batch_from_csv_file


class Command(BaseCommand):
    help = "Watch a LOT CSV folder and automatically analyze new CSV files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-dir",
            default=str(settings.BASE_DIR / "LotData"),
            help="Base directory containing incoming, processed, and failed folders.",
        )
        parser.add_argument(
            "--interval",
            type=float,
            default=2.0,
            help="Polling interval in seconds.",
        )
        parser.add_argument(
            "--user",
            default="",
            help="Username used as the creator of automated analysis batches.",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="Process current CSV files once and exit.",
        )

    def handle(self, *args, **options):
        base_dir = Path(options["base_dir"]).resolve()
        incoming_dir = base_dir / "incoming"
        processed_dir = base_dir / "processed"
        failed_dir = base_dir / "failed"
        for folder in (incoming_dir, processed_dir, failed_dir):
            folder.mkdir(parents=True, exist_ok=True)

        user = self.get_actor(options["user"])
        self.stdout.write(self.style.SUCCESS(f"Watching {incoming_dir} as {user.username}"))

        while True:
            self.process_pending_files(incoming_dir, processed_dir, failed_dir, user)
            if options["once"]:
                break
            time.sleep(options["interval"])

    def get_actor(self, username):
        User = get_user_model()
        if username:
            try:
                return User.objects.get(username=username)
            except User.DoesNotExist as exc:
                raise CommandError(f"User '{username}' does not exist.") from exc

        user = User.objects.filter(is_superuser=True).first()
        if user:
            return user

        user = User.objects.filter(is_staff=True).first() or User.objects.first()
        if user:
            return user

        raise CommandError("No user exists. Create a user or pass --user.")

    def process_pending_files(self, incoming_dir, processed_dir, failed_dir, user):
        for file_path in sorted(incoming_dir.glob("*.csv")):
            if not self.is_file_ready(file_path):
                continue

            try:
                batch = create_batch_from_csv_file(file_path, user)
            except Exception as exc:
                destination = self.unique_destination(failed_dir, file_path.name)
                shutil.move(str(file_path), destination)
                self.stderr.write(self.style.ERROR(f"FAILED {file_path.name}: {exc}"))
                continue

            destination = self.unique_destination(processed_dir, file_path.name)
            shutil.move(str(file_path), destination)
            self.stdout.write(self.style.SUCCESS(f"DONE {file_path.name}: {batch.batch_code}"))

    def is_file_ready(self, file_path):
        try:
            first_size = file_path.stat().st_size
            time.sleep(0.2)
            return file_path.exists() and file_path.stat().st_size == first_size
        except OSError:
            return False

    def unique_destination(self, folder, filename):
        destination = folder / filename
        if not destination.exists():
            return str(destination)

        stamp = timezone.localtime().strftime("%Y%m%d%H%M%S")
        source_name = Path(filename)
        return str(folder / f"{source_name.stem}-{stamp}{source_name.suffix}")
