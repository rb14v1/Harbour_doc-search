from django.test import TestCase

from apps.common.test_utils import create_user, pad_vector
from apps.common.vector_search import similarity_search
from apps.documents.models import Document


class SimilaritySearchRankingTests(TestCase):
    """Constructs documents with KNOWN embedding vectors (not the AI stub)
    so the expected nearest-first ordering can be asserted exactly. Vectors
    are hand-crafted short (e.g. [1, 0, 0]) for readability, then padded to
    EMBEDDING_DIMENSIONS via pad_vector() — real Postgres pgvector columns
    reject any other length, while SQLite's JSONField fallback doesn't
    enforce one, so padding is required for this test to pass on both
    backends identically."""

    def setUp(self):
        self.user = create_user(email="vs@example.com")

        def make(title, vector):
            return Document.objects.create(user=self.user, title=title, content="x", embedding=pad_vector(vector))

        # Query vector will be [1, 0, 0, ...].
        self.exact_match = make("exact", [1.0, 0.0, 0.0])
        self.close_match = make("close", [0.9, 0.1, 0.0])
        self.orthogonal = make("orthogonal", [0.0, 1.0, 0.0])
        self.opposite = make("opposite", [-1.0, 0.0, 0.0])

    def test_nearest_first_ordering(self):
        query_vector = pad_vector([1.0, 0.0, 0.0])
        results = similarity_search(Document.objects.filter(user=self.user), query_vector, top_k=10)
        ordered_titles = [doc.title for doc, _score in results]
        self.assertEqual(
            ordered_titles,
            ["exact", "close", "orthogonal", "opposite"],
        )

    def test_exact_match_has_similarity_one(self):
        query_vector = pad_vector([1.0, 0.0, 0.0])
        results = similarity_search(Document.objects.filter(user=self.user), query_vector, top_k=10)
        scores = dict((doc.title, score) for doc, score in results)
        self.assertAlmostEqual(scores["exact"], 1.0, places=6)

    def test_opposite_vector_has_similarity_negative_one(self):
        query_vector = pad_vector([1.0, 0.0, 0.0])
        results = similarity_search(Document.objects.filter(user=self.user), query_vector, top_k=10)
        scores = dict((doc.title, score) for doc, score in results)
        self.assertAlmostEqual(scores["opposite"], -1.0, places=6)

    def test_top_k_limits_result_count(self):
        query_vector = pad_vector([1.0, 0.0, 0.0])
        results = similarity_search(Document.objects.filter(user=self.user), query_vector, top_k=2)
        self.assertEqual(len(results), 2)
        self.assertEqual([doc.title for doc, _ in results], ["exact", "close"])
