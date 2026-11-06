from django.conf import settings
from django.db import models

from apps.common.embedding_field import EmbeddingField


class Document(models.Model):
    """A single searchable document owned by one user.

    `embedding` is computed from `title + "\\n" + content` - see
    DocumentSerializer.create/update in serializers.py (deliberately NOT a
    model save() override, so embedding computation is easy to unit test in
    isolation from model persistence).
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=255)
    content = models.TextField()
    embedding = EmbeddingField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
