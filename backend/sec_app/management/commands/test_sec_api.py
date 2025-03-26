from django.core.management.base import BaseCommand
import requests
import json
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test SEC API endpoints directly'

    def add_arguments(self, parser):
        parser.add_argument('ticker', type=str, help='Ticker symbol to test')
        parser.add_argument('--verbose', action='store_true', help='Show detailed response')

    def handle(self, *args, **options):
        ticker = options['ticker'].upper()
        verbose = options.get('verbose', False)
        
        self.stdout.write(f"Testing SEC API for ticker: {ticker}")
        
        # Headers for SEC API requests
        headers = {
            'User-Agent': 'Nanik paul@nanikworkforce.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov'
        }
        
        # Step 1: Get CIK
        from sec_app.api_client import get_cik_from_ticker
        cik = get_cik_from_ticker(ticker)
        
        if not cik:
            self.stdout.write(self.style.ERROR(f"❌ Could not find CIK for {ticker}"))
            return
        
        self.stdout.write(self.style.SUCCESS(f"✅ Found CIK: {cik}"))
        
        # Step 2: Test different URL formats for submissions
        cik_no_zeros = cik.lstrip('0')
        
        urls_to_test = [
            f"https://data.sec.gov/submissions/CIK{cik_no_zeros}.json",
            f"https://data.sec.gov/submissions/CIK/{cik_no_zeros}.json",
            f"https://data.sec.gov/submissions/{cik_no_zeros}.json",
            f"https://data.sec.gov/api/submissions/CIK{cik_no_zeros}.json"
        ]
        
        for url in urls_to_test:
            self.stdout.write(f"Testing URL: {url}")
            
            try:
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS(f"✅ Success! Status code: {response.status_code}"))
                    
                    if verbose:
                        # Pretty print the first part of the JSON response
                        try:
                            data = response.json()
                            self.stdout.write("Response preview:")
                            self.stdout.write(json.dumps(data, indent=2)[:500] + "...")
                        except Exception as e:
                            self.stdout.write(f"Error parsing JSON: {str(e)}")
                    
                    # This is the correct URL format, update it in the settings
                    self.stdout.write(self.style.SUCCESS(f"✅ Found working URL format: {url}"))
                    return
                else:
                    self.stdout.write(self.style.ERROR(f"❌ Failed! Status code: {response.status_code}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))
        
        self.stdout.write(self.style.ERROR("❌ All URL formats failed")) 