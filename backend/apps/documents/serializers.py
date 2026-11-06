from rest_framework import serializers

from apps.common.ai import get_embedding
from apps.documents.models import Document


def _embedding_text(title: str, content: str) -> str:
    return f"{title}\n{content}"


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "title", "content", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        text = _embedding_text(validated_data["title"], validated_data["content"])
        validated_data["embedding"] = get_embedding(text)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        title = validated_data.get("title", instance.title)
        content = validated_data.get("content", instance.content)
        if "title" in validated_data or "content" in validated_data:
            validated_data["embedding"] = get_embedding(_embedding_text(title, content))
        return super().update(instance, validated_data)


class SearchResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    content_excerpt = serializers.CharField()
    similarity_score = serializers.FloatField()
