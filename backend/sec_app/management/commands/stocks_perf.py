# sec_app/management/commands/import_companies.py

import pandas as pd
from django.core.management.base import BaseCommand
from sec_app.models.company import Company
import os

class Command(BaseCommand):
    help = 'Load company data from tickers directory'

    def handle(self, *args, **options):
        # Get the project root directory (where manage.py is)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
        
        self.stdout.write(f"Current directory: {current_dir}")
        self.stdout.write(f"Project root: {project_root}")
        
        # Try all possible locations
        possible_paths = [
            os.path.join(project_root, 'sec_app', 'tickers'),
            os.path.join(project_root, 'backend', 'sec_app', 'tickers'),
            os.path.join(os.path.dirname(project_root), 'sec_app', 'tickers')
        ]
        
        # Debug: List all directories and files
        self.stdout.write("\nChecking directories:")
        for path in possible_paths:
            self.stdout.write(f"\nChecking path: {path}")
            if os.path.exists(path):
                self.stdout.write(f"Directory exists!")
                try:
                    files = os.listdir(path)
                    self.stdout.write(f"Files in directory:")
                    for f in files:
                        self.stdout.write(f"  - {f}")
                except Exception as e:
                    self.stdout.write(f"Error reading directory: {str(e)}")
            else:
                self.stdout.write("Directory does not exist")
        
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
        
        companies_added = 0
        companies_updated = 0

        for file_name in ticker_files:
            ticker = file_name.replace('_StdMetrics.csv', '')
            file_path = os.path.join(tickers_dir, file_name)

            try:
                df = pd.read_csv(file_path)
                company_name = ticker
                
                # Generate a unique placeholder CIK for each company
                placeholder_cik = f"CIK{ticker}"  # Using ticker as part of CIK to ensure uniqueness
                
                company, created = Company.objects.update_or_create(
                    ticker=ticker,
                    defaults={
                        'name': company_name,
                        'cik': placeholder_cik  # Using the placeholder CIK instead of empty string
                    }
                )

                if created:
                    companies_added += 1
                    self.stdout.write(self.style.SUCCESS(f"Added company: {ticker}"))
                else:
                    companies_updated += 1
                    self.stdout.write(self.style.SUCCESS(f"Updated company: {ticker}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing {file_name}: {str(e)}"))

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed companies: {companies_added} added, {companies_updated} updated'
            )
        )
