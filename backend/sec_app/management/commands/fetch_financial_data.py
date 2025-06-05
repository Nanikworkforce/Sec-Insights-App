# backend/sec_app/management/commands/import_ticker_data.py
import os
import pandas as pd
from django.core.management.base import BaseCommand
from sec_app.models.company import Company
from sec_app.models.metric import FinancialMetric
from sec_app.models.period import FinancialPeriod
from django.db import transaction
from tqdm import tqdm

class Command(BaseCommand):
    help = 'Import financial data from CSV files'

    def handle(self, *args, **kwargs):
        directory_path = 'sec_app/stdmetrics'
        self.stdout.write(f"Looking for CSV files in: {directory_path}")

        # Get all CSV files
        csv_files = [f for f in os.listdir(directory_path) if f.endswith('_StdMetrics.csv')]
        total_files = len(csv_files)
        self.stdout.write(f"Found {total_files} files to process")

        # Process in batches of 100 files
        batch_size = 100
        for i in range(0, total_files, batch_size):
            batch_files = csv_files[i:i + batch_size]
            self.process_batch(batch_files, directory_path, i, total_files)

    def process_batch(self, batch_files, directory_path, batch_start, total_files):
        with transaction.atomic():
            metrics_to_create = []
            periods_cache = {}
            
            for filename in tqdm(batch_files, desc=f"Processing files {batch_start+1}-{batch_start+len(batch_files)} of {total_files}"):
                filepath = os.path.join(directory_path, filename)
                ticker = filename.split('_')[0]
                
                try:
                    # Get company (should already exist from stocks_perf command)
                    company = Company.objects.get(ticker=ticker)
                    
                    # Process the CSV file
                    df = pd.read_csv(filepath, index_col=0)
                    
                    # Process annual data
                    self.process_annual_data(df, company, metrics_to_create, periods_cache)
                    
                    # Process multi-year periods
                    for period_type in ['2Y', '3Y', '4Y', '5Y', '10Y', '15Y', '20Y']:
                        self.process_period_data(df, company, period_type, metrics_to_create, periods_cache)
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing {filename}: {str(e)}"))

            # Bulk create all metrics for this batch
            if metrics_to_create:
                FinancialMetric.objects.bulk_create(
                    metrics_to_create,
                    batch_size=1000,
                    ignore_conflicts=True
                )
                self.stdout.write(f"Created {len(metrics_to_create)} metrics in this batch")

    def process_annual_data(self, df, company, metrics_to_create, periods_cache):
        for year in range(2005, 2025):
            year_str = str(year)
            if year_str not in df.columns:
                continue

            # Get or create period (using cache)
            period_key = f"{company.id}-{year_str}"
            if period_key not in periods_cache:
                period, _ = FinancialPeriod.objects.get_or_create(
                    company=company,
                    period=year_str,
                    defaults={
                        'start_date': f'{year}-01-01',
                        'end_date': f'{year}-12-31'
                    }
                )
                periods_cache[period_key] = period
            period = periods_cache[period_key]

            # Create metrics
            for metric_name in df.index:
                if metric_name == 'statementType':
                    continue
                    
                value = df.at[metric_name, year_str]
                if pd.notna(value):
                    metrics_to_create.append(
                        FinancialMetric(
                            company=company,
                            period=period,
                            metric_name=metric_name,
                            value=value
                        )
                    )

    def process_period_data(self, df, company, period_type, metrics_to_create, periods_cache):
        period_cols = [col for col in df.columns if col.startswith(f'{period_type}: ')]
        
        for col in period_cols:
            years = col.split(': ')[1]
            
            # Get or create period (using cache)
            period_key = f"{company.id}-{years}"
            if period_key not in periods_cache:
                period, _ = FinancialPeriod.objects.get_or_create(
                    company=company,
                    period=years,
                    defaults={
                        'start_date': f'{years.split("-")[0]}-01-01',
                        'end_date': f'20{years.split("-")[1]}-12-31'
                    }
                )
                periods_cache[period_key] = period
            period = periods_cache[period_key]

            # Create metrics
            for metric_name in df.index:
                if metric_name == 'statementType':
                    continue
                    
                value = df.at[metric_name, col]
                if pd.notna(value):
                    metrics_to_create.append(
                        FinancialMetric(
                            company=company,
                            period=period,
                            metric_name=metric_name,
                            value=value
                        )
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