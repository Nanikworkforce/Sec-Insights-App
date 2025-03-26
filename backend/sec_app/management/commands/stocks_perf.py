# sec_app/management/commands/import_companies.py

import pandas as pd
from django.core.management.base import BaseCommand
from sec_app.models.company import Company

class Command(BaseCommand):
    help = 'Import company data from stocks_perf_data.xlsx (selected columns only)'

    def handle(self, *args, **kwargs):
        file_path = '/backend/data/stocks_perf_data.xlsx' 

        try:
            use_cols = ['Symbol', 'Company', 'Sector', 'Industry', 'CIK']
            df = pd.read_excel(file_path, engine='openpyxl', usecols=use_cols)

            for _, row in df.iterrows():
                ticker = str(row['Symbol']).strip()
                name = str(row['Company']).strip()
                sector = str(row.get('Sector', '')).strip()
                industry = str(row.get('Industry', '')).strip()
                cik = str(row.get('CIK', '')).strip()
                # country = str(row.get('Country', '')).strip()
                # market_cap = row.get('Market Cap')
                # assets = row.get('Assets')

                company, created = Company.objects.get_or_create(
                    ticker=ticker,
                    defaults={
                        'name': name,
                        'sector': sector if pd.notna(sector) else None,
                        'industry': industry if pd.notna(industry) else None,
                        'cik': cik if pd.notna(cik) else None,
                        # 'country': country if pd.notna(country) else None,
                        # 'market_cap': market_cap if pd.notna(market_cap) else None,
                        # 'assets': assets if pd.notna(assets) else None
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"✔ Created company: {ticker} - {name}"))
                else:
                    self.stdout.write(f"↪ Company {ticker} already exists. Skipped.")

            self.stdout.write(self.style.SUCCESS("✅ Company import complete."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Error importing companies: {e}"))
