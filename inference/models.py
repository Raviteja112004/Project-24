from django.db import models
from models_registry.models import ModelVersion


class InferenceJob(models.Model):
    model_version = models.ForeignKey(
        ModelVersion,
        on_delete=models.CASCADE,
        related_name="inference_jobs"
    )

    status = models.CharField(
        max_length=20,
        default="PENDING"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.model_version} - {self.status}"