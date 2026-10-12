from django.contrib import admin
from .models import Model, ModelArtifact, ModelVersion, Deployment
# Register your models here.

admin.site.register([Model,ModelVersion, ModelArtifact, Deployment])