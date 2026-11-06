from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.common.test_utils import auth_client, create_user, pad_vector
from apps.documents.models import Document


class SearchEndpointTests(APITestCase):
    def setUp(self):
        self.user_a = create_user(email="search-a@example.com")
        self.user_b = create_user(email="search-b@example.com")

        self.doc_a1 = Document.objects.create(
            user=self.user_a, title="A doc one", content="A's first document content.",
            embedding=pad_vector([1.0, 0.0, 0.0]),
        )
        self.doc_a2 = Document.objects.create(
            user=self.user_a, title="A doc two", content="A's second document content.",
            embedding=pad_vector([0.0, 1.0, 0.0]),
        )
        self.doc_b1 = Document.objects.create(
            user=self.user_b, title="B doc one", content="B's document content, should never leak to A.",
            embedding=pad_vector([1.0, 0.0, 0.0]),
        )

    def test_requires_query_param(self):
        client = auth_client(self.user_a)
        response = client.get(reverse("document-search"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_requires_authentication(self):
        response = self.client.get(reverse("document-search"), {"q": "test"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_search_only_returns_own_documents(self):
        client = auth_client(self.user_a)
        response = client.get(reverse("document-search"), {"q": "document content", "k": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [row["id"] for row in response.data["results"]]
        self.assertIn(self.doc_a1.id, ids)
        self.assertIn(self.doc_a2.id, ids)
        self.assertNotIn(self.doc_b1.id, ids)

    def test_response_includes_generated_answer_stub(self):
        client = auth_client(self.user_a)
        response = client.get(reverse("document-search"), {"q": "document content"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("generated_answer", response.data)
        self.assertIn("[STUB AI RESPONSE", response.data["generated_answer"])

    def test_result_shape(self):
        client = auth_client(self.user_a)
        response = client.get(reverse("document-search"), {"q": "document content", "k": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        row = response.data["results"][0]
        self.assertIn("id", row)
        self.assertIn("title", row)
        self.assertIn("content_excerpt", row)
        self.assertIn("similarity_score", row)

    def test_k_parameter_limits_results(self):
        client = auth_client(self.user_a)
        response = client.get(reverse("document-search"), {"q": "document content", "k": 1})
        self.assertEqual(len(response.data["results"]), 1)
