import os
import pandas as pd
from django.core.management.base import BaseCommand
from sec_app.models.company import Company

class Command(BaseCommand):
    help = 'Load company data from tickers directory (optimized)'

    def handle(self, *args, **options):
        # Locate project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))

        possible_paths = [
            os.path.join(project_root, 'sec_app', 'stdmetrics'),
            os.path.join(project_root, 'backend', 'sec_app', 'stdmetrics'),
            os.path.join(os.path.dirname(project_root), 'sec_app', 'stdmetrics')
        ]

        tickers_dir = next((p for p in possible_paths if os.path.exists(p)), None)
        if not tickers_dir:
            self.stdout.write(self.style.ERROR("❌ Could not find tickers directory."))
            return

        self.stdout.write(f"📁 Using tickers directory: {tickers_dir}")
        ticker_files = [f for f in os.listdir(tickers_dir) if f.endswith('_StdMetrics.csv')]
        self.stdout.write(f"📄 Found {len(ticker_files)} ticker files")

        # Cache existing companies
        existing_companies = Company.objects.in_bulk(field_name='ticker')
        to_create = []
        to_update = []

        for file_name in ticker_files:
            ticker = file_name.replace('_StdMetrics.csv', '')
            file_path = os.path.join(tickers_dir, file_name)

            try:
                # Load file quickly (we don’t need the data)
                df = pd.read_csv(file_path, nrows=1)  # Only read the header
                name = ticker
                cik = f"CIK{ticker}"

                if ticker in existing_companies:
                    company = existing_companies[ticker]
                    # Only update if values differ
                    if company.name != name or company.cik != cik:
                        company.name = name
                        company.cik = cik
                        to_update.append(company)
                else:
                    to_create.append(Company(name=name, ticker=ticker, cik=cik))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"⚠️ Error with {file_name}: {str(e)}"))

        # Bulk create and update
        if to_create:
            Company.objects.bulk_create(to_create, batch_size=500)
        if to_update:
            Company.objects.bulk_update(to_update, ['name', 'cik'], batch_size=500)

        self.stdout.write(self.style.SUCCESS(
            f"✅ Done: {len(to_create)} created, {len(to_update)} updated."
        ))
