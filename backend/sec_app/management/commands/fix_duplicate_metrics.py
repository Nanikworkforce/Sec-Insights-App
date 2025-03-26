from django.core.management.base import BaseCommand
from sec_app.models.metric import FinancialMetric
from sec_app.models.company import Company
from django.db.models import Count

class Command(BaseCommand):
    help = 'Fix duplicate metrics in the database'

    def add_arguments(self, parser):
        parser.add_argument('--ticker', type=str, help='Filter by company ticker')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')

    def handle(self, *args, **options):
        ticker = options.get('ticker')
        dry_run = options.get('dry_run', False)
        
        # Find duplicate metrics
        if ticker:
            try:
                company = Company.objects.get(ticker=ticker)
                self.stdout.write(f"Looking for duplicate metrics for {company.name} ({ticker})...")
                
                # Find duplicates by metric_name and period
                duplicates = FinancialMetric.objects.filter(company=company) \
                    .values('metric_name', 'period') \
                    .annotate(count=Count('id')) \
                    .filter(count__gt=1)
                
                if not duplicates:
                    self.stdout.write(self.style.SUCCESS(f"No duplicate metrics found for {ticker}"))
                    return
                
                self.stdout.write(f"Found {len(duplicates)} duplicate metric groups for {ticker}")
                
                for dup in duplicates:
                    metrics = FinancialMetric.objects.filter(
                        company=company,
                        metric_name=dup['metric_name'],
                        period=dup['period']
                    ).order_by('id')
                    
                    self.stdout.write(f"  - {dup['metric_name']} ({metrics.count()} duplicates)")
                    
                    # Keep the most recent one (highest ID)
                    keep = metrics.last()
                    delete_ids = [m.id for m in metrics if m.id != keep.id]
                    
                    if dry_run:
                        self.stdout.write(f"    Would keep: {keep.id} (value: {keep.value})")
                        self.stdout.write(f"    Would delete: {delete_ids}")
                    else:
                        FinancialMetric.objects.filter(id__in=delete_ids).delete()
                        self.stdout.write(f"    Kept: {keep.id} (value: {keep.value})")
                        self.stdout.write(f"    Deleted: {delete_ids}")
                
                if not dry_run:
                    self.stdout.write(self.style.SUCCESS(f"Successfully fixed duplicate metrics for {ticker}"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"Dry run completed. No changes made."))
                    
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Company with ticker {ticker} not found"))
        else:
            # Fix duplicates for all companies
            self.stdout.write("Looking for duplicate metrics across all companies...")
            
            # Find duplicates by company, metric_name and period
            duplicates = FinancialMetric.objects.values('company', 'metric_name', 'period') \
                .annotate(count=Count('id')) \
                .filter(count__gt=1)
            
            if not duplicates:
                self.stdout.write(self.style.SUCCESS("No duplicate metrics found"))
                return
            
            self.stdout.write(f"Found {len(duplicates)} duplicate metric groups")
            
            for dup in duplicates:
                if dup['company'] is None:
                    company_name = "DEFAULT"
                else:
                    try:
                        company = Company.objects.get(id=dup['company'])
                        company_name = f"{company.name} ({company.ticker})"
                    except Company.DoesNotExist:
                        company_name = f"Unknown (ID: {dup['company']})"
                
                metrics = FinancialMetric.objects.filter(
                    company_id=dup['company'],
                    metric_name=dup['metric_name'],
                    period=dup['period']
                ).order_by('id')
                
                self.stdout.write(f"  - {company_name}: {dup['metric_name']} ({metrics.count()} duplicates)")
                
                # Keep the most recent one (highest ID)
                keep = metrics.last()
                delete_ids = [m.id for m in metrics if m.id != keep.id]
                
                if dry_run:
                    self.stdout.write(f"    Would keep: {keep.id} (value: {keep.value})")
                    self.stdout.write(f"    Would delete: {delete_ids}")
                else:
                    FinancialMetric.objects.filter(id__in=delete_ids).delete()
                    self.stdout.write(f"    Kept: {keep.id} (value: {keep.value})")
                    self.stdout.write(f"    Deleted: {delete_ids}")
            
            if not dry_run:
                self.stdout.write(self.style.SUCCESS("Successfully fixed all duplicate metrics"))
            else:
                self.stdout.write(self.style.SUCCESS("Dry run completed. No changes made.")) 