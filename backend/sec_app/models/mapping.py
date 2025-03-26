from django.db import models
from backend.basemodel import TimeBaseModel

# sec_app/models/metric_mapping.py
class MetricMapping(TimeBaseModel):
    xbrl_tag = models.CharField(max_length=100, unique=True)
    standard_name = models.CharField(max_length=100)
    priority = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.xbrl_tag} - {self.standard_name}"

