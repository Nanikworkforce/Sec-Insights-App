from django.db import models
from .company import Company

class Filing(models.Model):
    """
    Model representing an SEC filing (10-K, 10-Q, etc.)
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='filings')
    form = models.CharField(max_length=10, help_text="Form type (e.g., 10-K, 10-Q)")
    filing_date = models.DateField(help_text="Date the filing was submitted to SEC")
    accession_number = models.CharField(max_length=20, blank=True, null=True, help_text="SEC accession number")
    fiscal_year_end = models.DateField(blank=True, null=True, help_text="End date of the fiscal year")
    
    class Meta:
        unique_together = ('company', 'filing_date', 'form')
        ordering = ['-filing_date']
        db_table = 'sec_app_filing'
    
    def __str__(self):
        return f"{self.company.ticker} - {self.form} ({self.filing_date})" 