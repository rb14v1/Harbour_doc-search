from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.common.embedding_field import EMBEDDING_DIMENSIONS
from apps.documents.models import Document

User = get_user_model()

DEMO_EMAIL = "demo@example.com"


class SeedMigrationDataTests(TestCase):
    """The 0002_seed_data data migration has already run against the test
    database by the time TestCase sets up (migrations run once to build the
    test DB), so this just verifies its effects are present and correct -
    it does not re-invoke the migration itself."""

    def test_demo_user_exists(self):
        self.assertTrue(User.objects.filter(email=DEMO_EMAIL).exists())

    def test_demo_user_password_is_usable(self):
        user = User.objects.get(email=DEMO_EMAIL)
        self.assertTrue(user.check_password("demo12345"))

    def test_expected_number_of_seed_documents(self):
        user = User.objects.get(email=DEMO_EMAIL)
        count = Document.objects.filter(user=user).count()
        self.assertGreaterEqual(count, 8)
        self.assertLessEqual(count, 10)

    def test_every_seed_document_has_full_length_embedding(self):
        user = User.objects.get(email=DEMO_EMAIL)
        for doc in Document.objects.filter(user=user):
            self.assertIsNotNone(doc.embedding)
            self.assertEqual(len(doc.embedding), EMBEDDING_DIMENSIONS)

    def test_seed_documents_cover_multiple_topics(self):
        user = User.objects.get(email=DEMO_EMAIL)
        titles = " ".join(Document.objects.filter(user=user).values_list("title", flat=True)).lower()
        # Loose smoke check that content spans the intended topics.
        self.assertTrue(any(word in titles for word in ["risotto", "bread", "braising"]))
        self.assertTrue(any(word in titles for word in ["hik", "trail"]))
        self.assertTrue(any(word in titles for word in ["budget", "fund", "compound"]))
