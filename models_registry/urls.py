from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ModelArtifactUploadView, ModelViewSet

router = DefaultRouter()
router.register(r"models", ModelViewSet, basename="model")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "model-versions/<int:model_version_id>/upload-artifact/",
        ModelArtifactUploadView.as_view(),
        name="model-version-upload-artifact",
    ),
]