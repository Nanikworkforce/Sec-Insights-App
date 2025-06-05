# sec_app/management/commands/import_companies.py

import pandas as pd
from django.core.management.base import BaseCommand
from sec_app.models.company import Company
import os
from django.db import transaction

class Command(BaseCommand):
    help = 'Load company data from tickers directory (fast bulk version)'

    def handle(self, *args, **options):
        # Get the project root directory (where manage.py is)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
        
        self.stdout.write(f"Current directory: {current_dir}")
        self.stdout.write(f"Project root: {project_root}")
        
        # Try all possible locations
        possible_paths = [
            os.path.join(project_root, 'sec_app', 'stdmetrics'),
            os.path.join(project_root, 'backend', 'sec_app', 'stdmetrics'),
            os.path.join(os.path.dirname(project_root), 'sec_app', 'stdmetrics')
        ]
        
        # Find the first path that exists
        tickers_dir = None
        for path in possible_paths:
            if os.path.exists(path):
                tickers_dir = path
                break
        
        if not tickers_dir:
            self.stdout.write(self.style.ERROR(f"Could not find tickers directory. Tried:"))
            for path in possible_paths:
                self.stdout.write(self.style.ERROR(f"- {path}"))
            return
        
        self.stdout.write(f"Found tickers directory at: {tickers_dir}")
        
        ticker_files = [f for f in os.listdir(tickers_dir) if f.endswith('_StdMetrics.csv')]
        self.stdout.write(f"Found {len(ticker_files)} ticker files")
        
        # --- Bulk upsert logic ---
        # Gather all companies to be created/updated
        company_objs = []
        for file_name in ticker_files:
            ticker = file_name.replace('_StdMetrics.csv', '')
            # No need to read CSV, just use ticker for name and CIK
            company_name = ticker
            # Ensure CIK is max 10 characters to match model field
            placeholder_cik = f"CIK{ticker}"[:10]
            company_objs.append(
                Company(
                    ticker=ticker,
                    name=company_name,
                    cik=placeholder_cik
                )
            )

        # Fetch existing companies in one query
        existing_companies = Company.objects.filter(ticker__in=[c.ticker for c in company_objs])
        existing_ticker_set = set(existing_companies.values_list('ticker', flat=True))

        # Split into new and to-update
        to_create = [c for c in company_objs if c.ticker not in existing_ticker_set]
        to_update = [c for c in company_objs if c.ticker in existing_ticker_set]

        companies_added = 0
        companies_updated = 0

        # Bulk create new companies
        if to_create:
            with transaction.atomic():
                Company.objects.bulk_create(to_create, batch_size=1000, ignore_conflicts=True)
            companies_added = len(to_create)
            self.stdout.write(self.style.SUCCESS(f"Added {companies_added} new companies"))

        # Bulk update existing companies (only name/cik)
        if to_update:
            # Fetch all existing company objects to update
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

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed companies: {companies_added} added, {companies_updated} updated'
            )
        )
