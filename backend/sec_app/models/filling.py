from django.db import models
from .period import FinancialPeriod
from .company import Company
from backend.basemodel import TimeBaseModel
from .filing import Filing

class FilingDocument(TimeBaseModel):
    filing = models.ForeignKey(Filing, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    period = models.ForeignKey(FinancialPeriod, on_delete=models.CASCADE)
    section_name = models.CharField(max_length=100)  # e.g., "MD&A"
    content = models.TextField()

    def __str__(self):
        return f"{self.company.name} - {self.period.period} - {self.section_name}"
