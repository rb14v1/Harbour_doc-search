import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

from apps.common.embedding_field import EmbeddingField


def create_vector_extension(apps, schema_editor):
    """Postgres-only feature guard (same spirit as the dev-sqlite override
    in config/settings/base.py): pgvector requires `CREATE EXTENSION
    vector` once per database before a VectorField column can exist. SQLite
    (used in dev/test via USE_SQLITE=True) has no concept of extensions and
    stores the embedding as a plain JSONField instead (see
    apps/common/embedding_field.py), so this is a strict no-op there.

    Written as RunPython rather than RunSQL so the branch on
    schema_editor.connection.vendor can be expressed in plain Python instead
    of a conditional SQL string.
    """
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(create_vector_extension, noop),
        migrations.CreateModel(
            name="Document",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("content", models.TextField()),
                # Calls the SAME dual-path factory the model uses (rather
                # than hardcoding a field class) so this one migration
                # produces the correct column type - pgvector VectorField on
                # Postgres, JSONField on SQLite - for whichever database it
                # is actually applied against. See
                # apps/common/embedding_field.py for the full rationale.
                ("embedding", EmbeddingField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="documents", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
