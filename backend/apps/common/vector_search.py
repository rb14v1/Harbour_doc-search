"""
Backend-agnostic cosine-similarity search over a queryset's embedding field.

On Postgres, this delegates to pgvector's CosineDistance, which pushes the
computation down into the database via the `<=>` operator (fast, indexable).

On SQLite (dev/test only - see apps/common/embedding_field.py), there is no
vector extension, so candidates are pulled into Python and scored with a
plain-math cosine similarity (no numpy dependency required).

Either way, callers get the same return shape: a list of (model_instance,
similarity_score) tuples, highest similarity first, length <= top_k. Business
logic (e.g. the search endpoint) never needs to know which path ran.
"""
import math

from django.conf import settings


def _cosine_similarity(vec_a, vec_b):
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return -1.0  # worst possible score - sinks incomparable rows to the bottom
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def similarity_search(queryset, query_vector, top_k, field_name="embedding"):
    """
    queryset: any queryset of a model with an EmbeddingField() column.
    query_vector: list[float] to compare against.
    top_k: maximum number of results to return.
    field_name: name of the embedding attribute (default "embedding").

    Returns: list[(instance, similarity_score)], descending by similarity,
    length <= top_k.
    """
    if settings.USE_SQLITE:
        scored = []
        for obj in queryset:
            vec = getattr(obj, field_name) or []
            score = _cosine_similarity(query_vector, vec)
            scored.append((obj, score))
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:top_k]

    from pgvector.django import CosineDistance

    annotated = queryset.annotate(
        _distance=CosineDistance(field_name, query_vector)
    ).order_by("_distance")[:top_k]
    # pgvector's cosine distance is defined as (1 - cosine_similarity), so
    # similarity = 1 - distance keeps the score on the same scale as the
    # SQLite path above.
    return [(obj, 1 - obj._distance) for obj in annotated]
