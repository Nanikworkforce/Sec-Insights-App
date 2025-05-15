from django.core.management.base import BaseCommand
from backend.sec_app.utility.utils import initialize_metric_standards

class Command(BaseCommand):
    help = 'Initialize standard financial metrics'

    def handle(self, *args, **options):
        self.stdout.write("Initializing standard metrics...")
        initialize_metric_standards()
        self.stdout.write(self.style.SUCCESS("Successfully initialized standard metrics")) 