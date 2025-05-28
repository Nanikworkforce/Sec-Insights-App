from backend.basemodel import TimeBaseModel
from django.db import models

class ChatLog(TimeBaseModel):
    question = models.TextField()
    answer = models.TextField()
    context = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.question} ({self.answer})"

    class Meta:
        verbose_name_plural = "Chatlogs"