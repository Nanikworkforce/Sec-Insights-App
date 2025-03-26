from django.db import models
from .period import FinancialPeriod
from .filling import FilingDocument
from backend.basemodel import TimeBaseModel     

class SentimentAnalysis(TimeBaseModel):
    document = models.ForeignKey(FilingDocument, on_delete=models.CASCADE)
    sentiment_score = models.FloatField()  # e.g., range from -1 to 1
    sentiment_label = models.CharField(max_length=10)  # Positive, Neutral, Negative
    keywords = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.document.company.name} - {self.document.period.period} - {self.document.section_name}"





