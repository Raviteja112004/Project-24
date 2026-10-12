import hashlib
import os
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.module_loading import import_string
from django.utils.text import slugify
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.models import TenantMembership

from .models import Model, ModelArtifact, ModelVersion
from .serializers import ModelArtifactSerializer, ModelArtifactUploadSerializer, ModelSerializer


def get_artifact_storage():
    backend_path = getattr(
        settings,
        'MODEL_ARTIFACT_STORAGE_BACKEND',
        'django.core.files.storage.FileSystemStorage',
    )
    backend = import_string(backend_path)
    storage_location = getattr(
        settings,
        'MODEL_ARTIFACT_STORAGE_LOCATION',
        str(Path(settings.MEDIA_ROOT) / 'model_artifacts'),
    )
    return backend(location=storage_location)


class ModelViewSet(viewsets.ModelViewSet):
    queryset = Model.objects.all().order_by("-created_at")
    serializer_class = ModelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Model.objects.none()

        tenant_ids = TenantMembership.objects.filter(user=user).values_list(
            "tenant_id", flat=True
        )

        if not tenant_ids:
            return Model.objects.none()

        return Model.objects.filter(tenant_id__in=tenant_ids).order_by("-created_at")

    def get_object(self):
        obj = super().get_object()
        tenant_ids = TenantMembership.objects.filter(user=self.request.user).values_list(
            "tenant_id", flat=True
        )

        if obj.tenant_id not in tenant_ids:
            raise PermissionDenied("You do not have access to this model.")

        return obj

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication is required to create a model.")

        memberships = TenantMembership.objects.filter(user=user)
        tenant_ids = list(memberships.values_list("tenant_id", flat=True))

        if not tenant_ids:
            raise PermissionDenied("You are not a member of any tenant.")

        if len(tenant_ids) > 1:
            raise PermissionDenied(
                "You belong to multiple tenants. Please select an explicit tenant "
                "through a validated tenant selection flow before creating a model."
            )

        serializer.save(tenant_id=tenant_ids[0])


class ModelArtifactUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, model_version_id):
        model_version = get_object_or_404(ModelVersion, pk=model_version_id)
        tenant_ids = TenantMembership.objects.filter(user=request.user).values_list(
            "tenant_id", flat=True
        )

        if model_version.model.tenant_id not in tenant_ids:
            raise PermissionDenied(
                "You do not belong to the tenant that owns this model version."
            )

        if ModelArtifact.objects.filter(model_version=model_version).exists():
            raise ValidationError("An artifact already exists for this model version.")

        uploaded_file = request.FILES.get("file")
        if uploaded_file is None:
            raise ValidationError("A file upload is required.")

        serializer = ModelArtifactUploadSerializer(data={"file": uploaded_file})
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        file_bytes = uploaded_file.read()
        uploaded_file.seek(0)

        if len(file_bytes) > settings.MODEL_ARTIFACT_MAX_UPLOAD_SIZE:
            raise ValidationError("File size exceeds the 50 MB upload limit.")

        safe_name = os.path.basename(uploaded_file.name.strip().replace("\\", "/"))
        if safe_name in {"", ".", ".."}:
            raise ValidationError("Unsafe file name.")

        storage = get_artifact_storage()
        tenant_slug = slugify(model_version.model.tenant.slug or model_version.model.tenant.name)
        model_slug = slugify(model_version.model.name)
        version_slug = slugify(model_version.version)
        relative_dir = Path('model_artifacts') / tenant_slug / model_slug / version_slug
        saved_path = None

        try:
            with transaction.atomic():
                saved_path = storage.save(
                    str(relative_dir / safe_name),
                    ContentFile(file_bytes),
                )

                artifact = ModelArtifact.objects.create(
                    model_version=model_version,
                    storage_uri=saved_path,
                    original_filename=safe_name,
                    file_size=len(file_bytes),
                    sha256=hashlib.sha256(file_bytes).hexdigest(),
                )

                response_data = ModelArtifactSerializer(artifact).data
                return Response(response_data, status=status.HTTP_201_CREATED)
        except Exception:
            if saved_path:
                try:
                    storage.delete(saved_path)
                except Exception:
                    pass
            raise
