from django.db import models

# Create your models here.
from tenants.models import Tenant


class Model(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="models"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ModelVersion(models.Model):

    model = models.ForeignKey(
        Model,
        on_delete=models.CASCADE,
        related_name='versions'
    )

    version = models.CharField(max_length=10)

    def __str__(self):
        return self.version


class ModelArtifact(models.Model):
    model_version = models.OneToOneField(
        ModelVersion,
        on_delete=models.CASCADE,
        related_name="artifact"
    )

    storage_uri = models.CharField(max_length=500)
    original_filename = models.CharField(max_length=255, blank=True, default="")
    file_size = models.PositiveBigIntegerField(default=0)
    sha256 = models.CharField(max_length=64, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.storage_uri



class Deployment(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        DEPLOYING = "DEPLOYING", "Deploying"
        RUNNING = "RUNNING", "Running"
        FAILED = "FAILED", "Failed"
        STOPPED = "STOPPED", "Stopped"

    model_version = models.ForeignKey(
        ModelVersion,
        on_delete=models.CASCADE,
        related_name="deployments"
    )

    name = models.CharField(max_length=100)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    endpoint = models.URLField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name