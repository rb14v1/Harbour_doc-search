"""
Dual-path storage for document embeddings.

Real deployments run on Postgres + the pgvector extension, so the embedding
column should be a pgvector.django.VectorField there. But this app must also
be fully buildable/testable on a machine with no Postgres/pgvector install
(e.g. this sandbox) - so when settings.USE_SQLITE is True, the SAME model
attribute (`embedding`) is instead backed by a plain JSONField storing a
list of floats. SQLite has no vector extension and no CREATE EXTENSION
equivalent, so it can't support VectorField at all.

Everything downstream (models, serializers, views, apps/common/ai.py,
apps/common/vector_search.py) uses the model attribute name only and never
branches on which backend produced it - the branching lives here, once.

NOTE ON MIGRATIONS: apps/documents/migrations/0001_initial.py calls this
same EmbeddingField() factory (rather than hardcoding a field class) so the
one migration file produces the correct column type on whichever database
it is actually applied against, in lockstep with settings.USE_SQLITE.
"""
from django.conf import settings
from django.db import models

# text-embedding-3-large's native dimensionality is 3072, but the OpenAI
# embeddings API supports shortening output vectors via the `dimensions`
# param - we default to 1536. Configurable via OPENAI_EMBEDDING_DIMENSIONS.
EMBEDDING_DIMENSIONS = settings.EMBEDDING_DIMENSIONS


def EmbeddingField(**kwargs):
    """Returns a Django model Field instance for storing an embedding
    vector, chosen per-backend. Call this exactly like a Field class, e.g.

        embedding = EmbeddingField()

    in a model body - it returns a real field instance (JSONField or
    pgvector's VectorField), so Django's migration/ORM machinery treats it
    identically to any other field.
    """
    if settings.USE_SQLITE:
        field_kwargs = {"default": list, "blank": True}
        field_kwargs.update(kwargs)
        return models.JSONField(**field_kwargs)

    # Imported lazily so the `pgvector` package only needs to actually
    # provide a working VectorField when Postgres is in use.
    from pgvector.django import VectorField

    field_kwargs = {"dimensions": EMBEDDING_DIMENSIONS, "null": True, "blank": True}
    field_kwargs.update(kwargs)
    return VectorField(**field_kwargs)
