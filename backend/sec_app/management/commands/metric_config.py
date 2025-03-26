import pandas as pd
from django.core.management.base import BaseCommand
from sec_app.models.mapping import MetricMapping

class Command(BaseCommand):
    help = "Load Metric Mappings from Excel file into MetricMapping model"

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Excel file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        try:
            df = pd.read_excel(file_path)

            # Clean column headers in case there are extra spaces or formatting
            df.columns = [str(col).strip() for col in df.columns]

            for _, row in df.iterrows():
                xbrl_tag = str(row.get('XBRL Tag', '')).strip()
                standard_name = str(row.get('Data Field', '')).strip()
                priority_raw = row.get('Priority', False)

                # Handle True/False/Yes/No/1/0 cases
                priority = False
                if str(priority_raw).strip().lower() in ['true', 'yes', '1']:
                    priority = True

                if xbrl_tag and standard_name:
                    MetricMapping.objects.update_or_create(
                        xbrl_tag=xbrl_tag,
                        defaults={
                            'standard_name': standard_name,
                            'priority': priority
                        }
                    )

            self.stdout.write(self.style.SUCCESS("✅ Metric mappings successfully imported."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to import: {str(e)}"))
