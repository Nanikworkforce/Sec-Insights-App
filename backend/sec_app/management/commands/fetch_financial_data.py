import os
import time
import tempfile
from django.core.management.base import BaseCommand
from sec_app.api_client import fetch_financial_data
from sec_app.utils import save_financial_data_to_db
from sec_app.models.mapping import MetricMapping
from asgiref.sync import async_to_sync


class Command(BaseCommand):
    help = 'Fetch financial data from SEC for a given ticker'

    def add_arguments(self, parser):
        parser.add_argument('ticker', type=str, help='Stock ticker symbol')

    def handle(self, *args, **options):
        ticker = options['ticker']
        lock_file = os.path.join(tempfile.gettempdir(), f"fetch_financial_data_{ticker}.lock")
        if os.path.exists(lock_file):
            if time.time() - os.path.getmtime(lock_file) < 600: 
                self.stdout.write(self.style.WARNING(f"Another process is already fetching data for {ticker}"))
                return
            else:
                os.remove(lock_file)        
        with open(lock_file, 'w') as f:
            f.write(str(time.time()))
        
        try:
            self.stdout.write(f"Fetching data for {ticker}...")
            filings = fetch_financial_data(ticker)
            if filings:
                self.stdout.write(f"Found {len(filings.get('filings', []))} valid 10-K filings for {ticker}")
                async_to_sync(save_financial_data_to_db)(filings)
                self.stdout.write(self.style.SUCCESS(f"Successfully saved financial data for {ticker}"))
            else:
                self.stdout.write(self.style.WARNING(f"No financial data found for {ticker}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing data for {ticker}: {str(e)}"))
        finally:
            if os.path.exists(lock_file):
                os.remove(lock_file) 