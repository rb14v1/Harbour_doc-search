from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.common.test_utils import auth_client, create_user, pad_vector
from apps.documents.models import Document


class DocumentIsolationTests(APITestCase):
    def setUp(self):
        self.user_a = create_user(email="a@example.com")
        self.user_b = create_user(email="b@example.com")
        self.doc_a = Document.objects.create(
            user=self.user_a, title="A's document", content="Belongs to A.", embedding=pad_vector([0.1, 0.2])
        )

    def test_user_cannot_list_other_users_documents(self):
        client = auth_client(self.user_b)
        response = client.get(reverse("document-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [row["id"] for row in response.data["results"]]
        self.assertNotIn(self.doc_a.id, ids)

    def test_user_cannot_retrieve_other_users_document_by_id(self):
        client = auth_client(self.user_b)
        response = client.get(reverse("document-detail", args=[self.doc_a.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_update_other_users_document(self):
        client = auth_client(self.user_b)
        response = client.patch(reverse("document-detail", args=[self.doc_a.id]), {"title": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.doc_a.refresh_from_db()
        self.assertEqual(self.doc_a.title, "A's document")

    def test_user_cannot_delete_other_users_document(self):
        client = auth_client(self.user_b)
        response = client.delete(reverse("document-detail", args=[self.doc_a.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Document.objects.filter(pk=self.doc_a.id).exists())


class DocumentCrudTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="c@example.com")
        self.client_a = auth_client(self.user)

    def test_create_computes_embedding(self):
        response = self.client_a.post(reverse("document-list"), {
            "title": "New doc",
            "content": "Some content here.",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        doc = Document.objects.get(pk=response.data["id"])
        self.assertIsNotNone(doc.embedding)
        self.assertTrue(len(doc.embedding) > 0)
        self.assertEqual(doc.user, self.user)

    def test_update_recomputes_embedding(self):
        create_response = self.client_a.post(reverse("document-list"), {
            "title": "Original",
            "content": "Original content.",
        })
        doc_id = create_response.data["id"]
        original_embedding = Document.objects.get(pk=doc_id).embedding

        update_response = self.client_a.patch(reverse("document-detail", args=[doc_id]), {
            "content": "Completely different content now.",
        })
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        new_embedding = Document.objects.get(pk=doc_id).embedding
        # pgvector-django returns VectorField values as numpy arrays on
        # Postgres (vs plain lists from SQLite's JSONField fallback), and
        # numpy arrays raise "ambiguous truth value" under assertNotEqual
        # directly — cast both to plain lists first so this compares
        # correctly on either backend.
        self.assertNotEqual(list(original_embedding), list(new_embedding))

    def test_list_requires_authentication(self):
        response = self.client.get(reverse("document-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
