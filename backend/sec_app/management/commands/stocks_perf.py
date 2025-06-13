import pandas as pd
from django.core.management.base import BaseCommand
from sec_app.models.company import Company
import os
from django.db import transaction

class Command(BaseCommand):
    help = 'Load company data from tickers directory (fast bulk version)'

    def handle(self, *args, **options):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))

        self.stdout.write(f"Current directory: {current_dir}")
        self.stdout.write(f"Project root: {project_root}")

        possible_paths = [
            os.path.join(project_root, 'sec_app', 'stdmetrics'),
            os.path.join(project_root, 'backend', 'sec_app', 'stdmetrics'),
            os.path.join(os.path.dirname(project_root), 'sec_app', 'stdmetrics')
        ]

        tickers_dir = None
        for path in possible_paths:
            if os.path.exists(path):
                tickers_dir = path
                break

        if not tickers_dir:
            self.stdout.write(self.style.ERROR("Could not find tickers directory. Tried:"))
            for path in possible_paths:
                self.stdout.write(self.style.ERROR(f"- {path}"))
            return

        self.stdout.write(f"Found tickers directory at: {tickers_dir}")
        ticker_files = [f for f in os.listdir(tickers_dir) if f.endswith('_StdMetrics.csv')]
        self.stdout.write(f"Found {len(ticker_files)} ticker files")

        excel_path = os.path.join(project_root, 'backend', 'sec_app', 'data', 'stocks_perf_data.xlsx')
        df = None
        if os.path.exists(excel_path):
            try:
                df = pd.read_excel(excel_path)
                df.columns = df.columns.str.strip().str.lower()
                self.stdout.write(self.style.SUCCESS(f"Excel columns: {df.columns.tolist()}"))
                df['symbol'] = df['symbol'].str.upper()
                self.stdout.write(self.style.SUCCESS("Excel file loaded successfully"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not read Excel file: {str(e)}"))
        else:
            self.stdout.write(self.style.WARNING("Excel file not found, using ticker as fallback name"))

        company_objs = []
        unmatched_tickers = []
        matched_tickers = []

        for file_name in ticker_files:
            ticker = file_name.replace('_StdMetrics.csv', '')
            company_name = ticker  # default fallback

            if df is not None:
                try:
                    company_name = df.loc[df['symbol'] == ticker.upper(), 'company name'].iloc[0]
                    matched_tickers.append(ticker)
                except (KeyError, IndexError):
                    unmatched_tickers.append(ticker)

            placeholder_cik = f"CIK{ticker}"[:10]
            company_objs.append(
                Company(
                    ticker=ticker,
                    name=company_name,
                    cik=placeholder_cik
                )
            )

        existing_companies = Company.objects.filter(ticker__in=[c.ticker for c in company_objs])
        existing_ticker_set = set(existing_companies.values_list('ticker', flat=True))

        to_create = [c for c in company_objs if c.ticker not in existing_ticker_set]
        to_update = [c for c in company_objs if c.ticker in existing_ticker_set]

        companies_added = 0
        companies_updated = 0

        if to_create:
            with transaction.atomic():
                Company.objects.bulk_create(to_create, batch_size=1000, ignore_conflicts=True)
            companies_added = len(to_create)
            self.stdout.write(self.style.SUCCESS(f"Added {companies_added} new companies"))

        if to_update:
            existing_objs = {c.ticker: c for c in Company.objects.filter(ticker__in=[c.ticker for c in to_update])}
            for c in to_update:
                obj = existing_objs.get(c.ticker)
                if obj:
                    obj.name = c.name
                    obj.cik = c.cik
            with transaction.atomic():
                Company.objects.bulk_update(list(existing_objs.values()), ['name', 'cik'], batch_size=1000)
            companies_updated = len(to_update)
            self.stdout.write(self.style.SUCCESS(f"Updated {companies_updated} companies"))

        self.stdout.write(self.style.SUCCESS(
            f"Successfully processed companies: {companies_added} added, {companies_updated} updated"
        ))

        self.stdout.write(self.style.WARNING(f"{len(unmatched_tickers)} tickers had no Excel match:"))
        for t in unmatched_tickers:
            self.stdout.write(f" - {t}")
