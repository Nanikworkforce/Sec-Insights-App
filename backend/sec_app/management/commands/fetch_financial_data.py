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
        directory_path = 'sec_app/tickers'
        self.stdout.write(f"Looking for CSV files in: {directory_path}")

        # Iterate over each CSV file in the directory
        for filename in os.listdir(directory_path):
            if filename.endswith('_StdMetrics.csv'):
                filepath = os.path.join(directory_path, filename)
                self.stdout.write(f"Processing file: {filename}")
                self.import_csv(filepath)

    def import_csv(self, filepath):
        df = pd.read_csv(filepath)
        ticker = os.path.basename(filepath).split('_')[0]
        self.stdout.write(f"Processing ticker: {ticker}")

        # Get or create company
        company = self.get_or_create_company(ticker)
        if not company:
            return

        # Process annual data (2005-2024)
        self.process_annual_data(df, company)
        
        # Process multi-year periods
        self.process_period_data(df, company, '2Y')
        self.process_period_data(df, company, '3Y')
        self.process_period_data(df, company, '4Y')
        self.process_period_data(df, company, '5Y')
        self.process_period_data(df, company, '10Y')
        self.process_period_data(df, company, '15Y')
        self.process_period_data(df, company, '20Y')

    def get_or_create_company(self, ticker):
        existing_companies = Company.objects.filter(ticker=ticker)
        if existing_companies.count() > 1:
            self.stdout.write(self.style.ERROR(f"Multiple companies found with ticker {ticker}"))
            return None
        elif existing_companies.count() == 1:
            return existing_companies.first()
        else:
            cik = self.get_cik_for_ticker(ticker)
            if cik == '0000000000':
                self.stdout.write(self.style.WARNING(f"No valid CIK found for ticker {ticker}"))
            company = Company.objects.create(ticker=ticker, name=ticker, cik=cik)
            self.stdout.write(self.style.SUCCESS(f"Created new company: {ticker}"))
            return company

    def process_annual_data(self, df, company):
        # Process each year from 2005 to 2024
        for year in range(2005, 2025):
            year_str = str(year)
            if year_str not in df.columns:
                continue

            period, _ = FinancialPeriod.objects.get_or_create(
                company=company,
                period=year_str,
                defaults={
                    'start_date': f'{year}-01-01',
                    'end_date': f'{year}-12-31'
                }
            )

            self.create_metrics(df, company, period, year_str)

    def process_period_data(self, df, company, period_type):
        # Get the column names for this period type
        period_cols = [col for col in df.columns if col.startswith(f'{period_type}: ')]
        
        for col in period_cols:
            # Extract years from column name (e.g., "2Y: 2005-06" -> "2005-06")
            years = col.split(': ')[1]
            
            period, _ = FinancialPeriod.objects.get_or_create(
                company=company,
                period=years,
                defaults={
                    'start_date': f'{years.split("-")[0]}-01-01',
                    'end_date': f'20{years.split("-")[1]}-12-31'
                }
            )

            self.create_metrics(df, company, period, col)

    def create_metrics(self, df, company, period, column):
        metric_names = df.iloc[:, 0]
        for i, metric_name in enumerate(metric_names):
            if metric_name == 'statementType':
                continue

            value = df.at[i, column]
            if pd.isna(value):
                continue

            FinancialMetric.objects.update_or_create(
                company=company,
                period=period,
                metric_name=metric_name,
                defaults={'value': value, 'unit': 'USD'}
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