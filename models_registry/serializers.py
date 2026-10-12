import os

from django.conf import settings
from rest_framework import serializers

from .models import Model, ModelArtifact


class ModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Model
        fields = ["id", "tenant", "name", "description", "created_at"]
        read_only_fields = ["id", "tenant", "created_at"]


class ModelArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelArtifact
        fields = [
            "id",
            "model_version",
            "storage_uri",
            "original_filename",
            "file_size",
            "sha256",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "storage_uri",
            "original_filename",
            "file_size",
            "sha256",
            "created_at",
        ]


class ModelArtifactUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        if value.size > settings.MODEL_ARTIFACT_MAX_UPLOAD_SIZE:
            raise serializers.ValidationError("File size exceeds the 50 MB upload limit.")

        original_name = value.name or ""
        if not original_name:
            raise serializers.ValidationError("Missing filename.")

        safe_name = os.path.basename(original_name.strip().replace("\\", "/"))
        if safe_name in {"", ".", ".."}:
            raise serializers.ValidationError("Unsafe filename.")

        if safe_name.lower().endswith(".onnx") is False:
            raise serializers.ValidationError("Only .onnx files are supported.")

        value.seek(0)
        first_chunk = value.read(64)
        value.seek(0)

        if not first_chunk or not any(first_chunk):
            raise serializers.ValidationError("Uploaded file is empty or unreadable.")

        return value
