from django.db import models
from backend.basemodel import TimeBaseModel

class Company(TimeBaseModel):
    name = models.CharField(max_length=255)
    ticker = models.CharField(max_length=10, db_index=True, unique=True)
    cik = models.CharField(max_length=10, unique=True, null=True, blank=True)
    sector = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.ticker})"

    class Meta:
        verbose_name_plural = "companies"
        indexes = [
            models.Index(fields=['ticker']),
        ]

