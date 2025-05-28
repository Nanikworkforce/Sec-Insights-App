from django.db import models
from backend.basemodel import TimeBaseModel
from .company import Company

class FinancialPeriod(TimeBaseModel):
    PERIOD_TYPES = [
        ('annual', 'Annual'),
        ('quarterly', 'Quarterly'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    period = models.CharField(max_length=20)
    period_type = models.CharField(max_length=10, choices=PERIOD_TYPES, default='annual')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    filing_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ['company', 'period']
        ordering = ['-period']

    def __str__(self):
        return f"{self.company.ticker} - {self.period}"


