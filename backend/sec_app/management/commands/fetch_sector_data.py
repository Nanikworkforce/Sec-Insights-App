from django.core.management.base import BaseCommand
from django.core.management import call_command
from sec_app.models.company import Company
import time

class Command(BaseCommand):
    help = 'Fetch financial data for companies in a specific sector'

    def add_arguments(self, parser):
        parser.add_argument('sector', type=str, help='Sector name (e.g., Technology, Healthcare)')
        parser.add_argument('--delay', type=int, default=3, help='Delay between requests in seconds')
        parser.add_argument('--limit', type=int, default=10, help='Maximum number of companies to process')

    def handle(self, *args, **options):
        sector = options['sector']
        delay = options['delay']
        limit = options['limit']
        
        # Get companies in the specified sector
        companies = Company.objects.filter(sector__icontains=sector).exclude(ticker='DEFAULT')
        
        if not companies.exists():
            self.stdout.write(self.style.ERROR(f"No companies found in sector: {sector}"))
            return
        
        # Limit the number of companies to process
        companies = companies[:limit]
        
        self.stdout.write(f"Fetching data for {companies.count()} companies in {sector} sector")
        
        results = {'success': [], 'failure': []}
        
        for i, company in enumerate(companies):
            ticker = company.ticker
            self.stdout.write(f"[{i+1}/{companies.count()}] Processing {ticker} ({company.name})...")
            
            try:
                call_command('fetch_financial_data', ticker)
                
                # Check if metrics were created
                from sec_app.models.metric import FinancialMetric
                metrics = FinancialMetric.objects.filter(company=company)
                
                if metrics.exists():
                    results['success'].append(ticker)
                    self.stdout.write(self.style.SUCCESS(f"✅ Successfully fetched data for {ticker}"))
                else:
                    results['failure'].append(ticker)
                    self.stdout.write(self.style.WARNING(f"⚠️ No metrics found for {ticker}"))
            except Exception as e:
                results['failure'].append(ticker)
                self.stdout.write(self.style.ERROR(f"❌ Error processing {ticker}: {str(e)}"))
            
            if i < companies.count() - 1:  # Don't delay after the last company
                self.stdout.write(f"Waiting {delay}s before next request...")
                time.sleep(delay)
        
        # Summary
        self.stdout.write("\n--- SUMMARY ---")
        self.stdout.write(f"Total companies processed: {companies.count()}")
        self.stdout.write(f"Successful: {len(results['success'])} - {', '.join(results['success'])}")
        self.stdout.write(f"Failed: {len(results['failure'])} - {', '.join(results['failure'])}")
        
        success_rate = len(results['success']) / companies.count() * 100
        self.stdout.write(f"Success rate: {success_rate:.1f}%") 