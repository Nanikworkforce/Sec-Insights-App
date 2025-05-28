from django.db import models
from sec_app.models.period import FinancialPeriod
from backend.basemodel import TimeBaseModel
from sec_app.models.company import Company

class FinancialMetric(TimeBaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE,null=True,blank=True)
    period = models.ForeignKey(FinancialPeriod, on_delete=models.CASCADE)
    metric_name = models.CharField(max_length=100)  # e.g., "Revenue", "EPS"
    value = models.FloatField(default=0.0)
    xbrl_tag = models.CharField(max_length=100, blank=True, null=True)
    unit = models.CharField(max_length=20, default='USD')

    def __str__(self):
        return f"{self.period.company.name} - {self.metric_name}: {self.value} {self.unit}"

    class Meta:
        ordering = ['period', 'metric_name']
        unique_together = ('metric_name', 'period', 'company')
        indexes = [
            models.Index(fields=['company', 'metric_name', 'period']),
            models.Index(fields=['metric_name']),
            models.Index(fields=['period']),
        ]