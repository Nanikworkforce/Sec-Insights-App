from django.core.management.base import BaseCommand
from django.core.management import call_command
import time
from io import StringIO
from contextlib import redirect_stdout

class Command(BaseCommand):
    help = 'Test fetching data for popular tickers'

    def add_arguments(self, parser):
        parser.add_argument('--delay', type=int, default=3, help='Delay between requests in seconds')
        parser.add_argument('--limit', type=int, default=5, help='Number of tickers to test')

    def handle(self, *args, **options):
        delay = options['delay']
        limit = options['limit']
        
        # List of popular tickers to test
        popular_tickers = [
            'AAPL',  # Apple
            'MSFT',  # Microsoft
            'GOOGL', # Alphabet (Google)
            'AMZN',  # Amazon
            'META',  # Meta (Facebook)
            'TSLA',  # Tesla
            'NVDA',  # NVIDIA
            'JPM',   # JPMorgan Chase
            'JNJ',   # Johnson & Johnson
            'V',     # Visa
        ]
        
        # Limit the number of tickers to test
        tickers_to_test = popular_tickers[:limit]
        
        self.stdout.write(f"Testing {len(tickers_to_test)} popular tickers with {delay}s delay between requests")
        
        results = {'success': [], 'failure': []}
        
        for i, ticker in enumerate(tickers_to_test):
            self.stdout.write(f"[{i+1}/{len(tickers_to_test)}] Testing {ticker}...")
            
            # Capture output to determine success/failure
            output = StringIO()
            with redirect_stdout(output):
                call_command('fetch_financial_data', ticker)
            
            output_text = output.getvalue()
            
            if "Successfully saved financial data" in output_text:
                results['success'].append(ticker)
                self.stdout.write(self.style.SUCCESS(f"✅ Successfully fetched data for {ticker}"))
            else:
                results['failure'].append(ticker)
                self.stdout.write(self.style.ERROR(f"❌ Failed to fetch data for {ticker}"))
            
            if i < len(tickers_to_test) - 1:  # Don't delay after the last ticker
                self.stdout.write(f"Waiting {delay}s before next request...")
                time.sleep(delay)
        
        # Summary
        self.stdout.write("\n--- SUMMARY ---")
        self.stdout.write(f"Total tickers tested: {len(tickers_to_test)}")
        self.stdout.write(f"Successful: {len(results['success'])} - {', '.join(results['success'])}")
        self.stdout.write(f"Failed: {len(results['failure'])} - {', '.join(results['failure'])}")
        
        success_rate = len(results['success']) / len(tickers_to_test) * 100
        self.stdout.write(f"Success rate: {success_rate:.1f}%")
        
        if success_rate > 0:
            self.stdout.write(self.style.SUCCESS("Test completed with some successful fetches"))
        else:
            self.stdout.write(self.style.ERROR("Test completed with no successful fetches")) 