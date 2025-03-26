from django.core.management.base import BaseCommand
from sec_app.management.commands.fetch_financial_data import Command as FetchCommand

class Command(BaseCommand):
    help = 'Fetch financial data for multiple tickers'

    def add_arguments(self, parser):
        parser.add_argument('tickers', nargs='+', type=str, help='List of ticker symbols')

    def handle(self, *args, **options):
        tickers = options['tickers']
        fetch_command = FetchCommand()
        
        for ticker in tickers:
            self.stdout.write(f"Processing {ticker}...")
            fetch_command.handle(ticker=ticker)
            self.stdout.write(self.style.SUCCESS(f"Completed processing {ticker}")) 