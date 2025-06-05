from django.core.management.base import BaseCommand
from sec_app.models.company import Company
import pandas as pd
import os

class Command(BaseCommand):
    help = 'Bulk load company data from tickers directory'

    def handle(self, *args, **options):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))

        possible_paths = [
            os.path.join(project_root, 'sec_app', 'stdmetrics'),
            os.path.join(project_root, 'backend', 'sec_app', 'stdmetrics'),
            os.path.join(os.path.dirname(project_root), 'sec_app', 'stdmetrics')
        ]

        tickers_dir = next((p for p in possible_paths if os.path.exists(p)), None)
        if not tickers_dir:
            self.stdout.write(self.style.ERROR("No valid tickers directory found."))
            return

        ticker_files = [f for f in os.listdir(tickers_dir) if f.endswith('_StdMetrics.csv')]
        self.stdout.write(f"Found {len(ticker_files)} ticker files")

        # Extract tickers from filenames
        tickers = [f.replace('_StdMetrics.csv', '') for f in ticker_files]

        # Fetch existing companies
        existing_companies = Company.objects.filter(ticker__in=tickers)
        existing_ticker_map = {c.ticker: c for c in existing_companies}

        to_create = []
        to_update = []

        for ticker in tickers:
            company_name = ticker
            placeholder_cik = f"CIK{ticker}"

            if ticker in existing_ticker_map:
                company = existing_ticker_map[ticker]
                company.name = company_name
                company.cik = placeholder_cik
                to_update.append(company)
            else:
                to_create.append(Company(
                    ticker=ticker,
                    name=company_name,
                    cik=placeholder_cik
                ))

        if to_create:
            Company.objects.bulk_create(to_create, batch_size=500)
        if to_update:
            Company.objects.bulk_update(to_update, ['name', 'cik'], batch_size=500)

        self.stdout.write(self.style.SUCCESS(
            f'Companies processed: {len(to_create)} added, {len(to_update)} updated'
        ))
