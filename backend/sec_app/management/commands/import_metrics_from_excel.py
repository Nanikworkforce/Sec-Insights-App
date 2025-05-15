from django.core.management.base import BaseCommand
import pandas as pd
import logging
from sec_app.models.metric import FinancialMetric
from backend.sec_app.utility.utils import create_default_company
import os

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import financial metrics from an Excel file'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to the Excel file containing metric standards')
        parser.add_argument('--sheet', type=str, default='Metrics', help='Sheet name containing the metrics')

    def handle(self, *args, **options):
        excel_file = options['excel_file']
        sheet_name = options['sheet']
        
        # Check if file exists
        if not os.path.exists(excel_file):
            self.stderr.write(self.style.ERROR(f"❌ Failed to import: [Errno 2] No such file or directory: '{excel_file}'"))
            self.stderr.write("Creating a sample file for you...")
            
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(excel_file), exist_ok=True)
            
            metrics_data = [
                {
                    'metric_name': 'Revenue',
                    'xbrl_tag': 'us-gaap:Revenues',
                    'unit': 'USD',
                    'category': 'Income Statement'
                },
                {
                    'metric_name': 'Net Income',
                    'xbrl_tag': 'us-gaap:NetIncomeLoss',
                    'unit': 'USD',
                    'category': 'Income Statement'
                },
                {
                    'metric_name': 'Operating Income',
                    'xbrl_tag': 'us-gaap:OperatingIncomeLoss',
                    'unit': 'USD',
                    'category': 'Income Statement'
                },
                {
                    'metric_name': 'Total Assets',
                    'xbrl_tag': 'us-gaap:Assets',
                    'unit': 'USD',
                    'category': 'Balance Sheet'
                },
                {
                    'metric_name': 'Total Liabilities',
                    'xbrl_tag': 'us-gaap:Liabilities',
                    'unit': 'USD',
                    'category': 'Balance Sheet'
                },
                {
                    'metric_name': 'Cash and Cash Equivalents',
                    'xbrl_tag': 'us-gaap:CashAndCashEquivalentsAtCarryingValue',
                    'unit': 'USD',
                    'category': 'Balance Sheet'
                },
                {
                    'metric_name': 'Gross Profit',
                    'xbrl_tag': 'us-gaap:GrossProfit',
                    'unit': 'USD',
                    'category': 'Income Statement'
                },
                {
                    'metric_name': 'EBITDA',
                    'xbrl_tag': 'us-gaap:EBITDA',
                    'unit': 'USD',
                    'category': 'Income Statement'
                }
            ]
            
            # Create a DataFrame
            df = pd.DataFrame(metrics_data)
            
            try:
                # Save to Excel
                df.to_excel(excel_file, sheet_name='Metrics', index=False)
                self.stdout.write(self.style.SUCCESS(f"✅ Sample metrics Excel file created at: {excel_file}"))
                self.stdout.write("Now trying to import the metrics...")
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ Error creating Excel file: {str(e)}"))
                return
        
        try:
            # Create default company and period
            period_obj = create_default_company()
            
            # Read the Excel file
            self.stdout.write(f"Reading metrics from {excel_file}, sheet: {sheet_name}")
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # Check required columns
            required_columns = ['metric_name', 'xbrl_tag']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.stderr.write(self.style.ERROR(f"Error: Missing required columns: {', '.join(missing_columns)}"))
                return
            
            # Process each row
            metrics_created = 0
            metrics_updated = 0
            
            for _, row in df.iterrows():
                metric_name = row['metric_name']
                xbrl_tag = row['xbrl_tag']
                
                # Get optional fields with defaults
                unit = row.get('unit', 'USD')
                category = row.get('category', 'Financial')
                
                # Create or update the metric
                metric, created = FinancialMetric.objects.update_or_create(
                    metric_name=metric_name,
                    period=period_obj,
                    defaults={
                        'xbrl_tag': xbrl_tag,
                        'unit': unit,
                        'value': 0.0
                    }
                )
                
                if created:
                    metrics_created += 1
                    self.stdout.write(f"Created metric: {metric_name} with XBRL tag: {xbrl_tag}")
                else:
                    metrics_updated += 1
                    self.stdout.write(f"Updated metric: {metric_name} with XBRL tag: {xbrl_tag}")
            
            self.stdout.write(self.style.SUCCESS(
                f"Successfully processed {metrics_created + metrics_updated} metrics "
                f"({metrics_created} created, {metrics_updated} updated) from {excel_file}"
            ))
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error importing metrics: {str(e)}")) 