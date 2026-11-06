from django.test import SimpleTestCase

from apps.common.ai import generate_answer, get_embedding
from apps.common.embedding_field import EMBEDDING_DIMENSIONS


class EmbeddingStubTests(SimpleTestCase):
    """No OPENAI_API_KEY is set in the test environment, so get_embedding
    must be running in deterministic stub mode."""

    def test_same_text_produces_identical_vector(self):
        vec1 = get_embedding("The quick brown fox")
        vec2 = get_embedding("The quick brown fox")
        self.assertEqual(vec1, vec2)

    def test_different_text_produces_different_vector(self):
        vec1 = get_embedding("The quick brown fox")
        vec2 = get_embedding("A completely different sentence")
        self.assertNotEqual(vec1, vec2)

    def test_vector_has_configured_dimensionality(self):
        vec = get_embedding("some text")
        self.assertEqual(len(vec), EMBEDDING_DIMENSIONS)

    def test_vector_is_l2_normalized(self):
        vec = get_embedding("normalize me")
        norm = sum(x * x for x in vec) ** 0.5
        self.assertAlmostEqual(norm, 1.0, places=6)

    def test_values_within_expected_range(self):
        vec = get_embedding("range check")
        self.assertTrue(all(-1.0 <= x <= 1.0 for x in vec))


class GenerateAnswerStubTests(SimpleTestCase):
    def test_stub_format_with_results(self):
        answer = generate_answer("what is risotto", ["Risotto is a creamy Italian rice dish."])
        self.assertIn("[STUB AI RESPONSE", answer)
        self.assertIn("Found 1 related document(s)", answer)
        self.assertIn("Risotto is a creamy Italian rice dish.", answer)

    def test_stub_format_with_no_results(self):
        answer = generate_answer("anything", [])
        self.assertIn("Found 0 related document(s)", answer)
        self.assertIn("Top match excerpt: none", answer)

    def test_stub_excerpt_is_truncated_to_200_chars(self):
        long_content = "x" * 500
        answer = generate_answer("q", [long_content])
        self.assertIn("x" * 200, answer)
        self.assertNotIn("x" * 201, answer)
