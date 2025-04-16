# backend/sec_app/management/commands/import_ticker_data.py
import os
import pandas as pd
from django.core.management.base import BaseCommand
from sec_app.models.company import Company
from sec_app.models.metric import FinancialMetric
from sec_app.models.period import FinancialPeriod

class Command(BaseCommand):
    help = 'Import financial data from CSV files'

    def handle(self, *args, **kwargs):
        # Path to the directory containing CSV files
        directory_path = 'sec_app/ticker_perf/'

        # Iterate over each CSV file in the directory
        for filename in os.listdir(directory_path):
            if filename.endswith('.csv'):
                filepath = os.path.join(directory_path, filename)
                self.import_csv(filepath)

    def import_csv(self, filepath):
        df = pd.read_csv(filepath)
        ticker = os.path.basename(filepath).split('_')[0]

        # Check for existing company with the same ticker
        existing_companies = Company.objects.filter(ticker=ticker)
        if existing_companies.count() > 1:
            print(f"Multiple companies found with ticker {ticker}. Please resolve duplicates.")
            return
        elif existing_companies.count() == 1:
            company = existing_companies.first()
        else:
            # Ensure you have a valid CIK for each company
            cik = self.get_cik_for_ticker(ticker)
            if cik == '0000000000':
                print(f"Warning: No valid CIK found for ticker {ticker}. Skipping.")
                return
            company = Company.objects.create(ticker=ticker, name=ticker, cik=cik)

        # Assuming the first column is the metric name
        metric_names = df.iloc[:, 0]

        # Iterate over each year column
        for year in df.columns[1:]:
            for i, metric_name in enumerate(metric_names):
                value = df.at[i, year]

                # Check if the value is missing or invalid
                if pd.isna(value):
                    print(f"Skipping missing value for {metric_name} in {year}")
                    continue

                # Create or get the financial period for the year
                period, _ = FinancialPeriod.objects.get_or_create(
                    company=company,
                    period=year,
                    defaults={'start_date': f'{year}-01-01', 'end_date': f'{year}-12-31'}
                )

                # Create or update the financial metric
                FinancialMetric.objects.update_or_create(
                    company=company,
                    period=period,
                    metric_name=metric_name,
                    defaults={'value': value, 'unit': 'USD'}  # Assuming USD as the unit
                )

    def get_cik_for_ticker(self, ticker):
        cik_lookup = {
            'AAP':  '0001158449',
            'AAPL': '0000320193',
            'MSFT': '0000789019',
            'GOOGL': '0001652044',
            'TSLA': '0001065280',
            'NVDA': '0001652044',
            'AMZN': '0001018724',
            'TSM': '0001652044',
            'WMT': '0001065280',
            'JNJ': '0000030607',
            'NFLX': '0001065280',
            'META': '0001326801',
            'ANGI': '0001705110',
            'AXIL': '0001718500'
            
        }
        return cik_lookup.get(ticker, '0000000000')  