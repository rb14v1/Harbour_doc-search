from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.ai import generate_answer, get_embedding
from apps.common.vector_search import similarity_search
from apps.documents.models import Document
from apps.documents.serializers import DocumentSerializer

EXCERPT_LENGTH = 280
DEFAULT_TOP_K = 5
MAX_TOP_K = 50


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SearchView(APIView):
    """GET /api/search/?q=<query>&k=<top_k>

    Embeds the query, runs similarity_search over the requesting user's own
    documents (and only that user's documents - see
    apps/documents/tests/test_search.py for the cross-user isolation test),
    and returns the top-k matches plus an AI-generated answer grounded in
    their content (see apps/common/ai.py for the stub/real split).
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = (request.query_params.get("q") or "").strip()
        if not query:
            return Response(
                {"detail": "Query parameter 'q' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            top_k = int(request.query_params.get("k", DEFAULT_TOP_K))
        except (TypeError, ValueError):
            top_k = DEFAULT_TOP_K
        top_k = max(1, min(top_k, MAX_TOP_K))

        queryset = Document.objects.filter(user=request.user)
        query_vector = get_embedding(query)
        results = similarity_search(queryset, query_vector, top_k)

        documents_payload = [
            {
                "id": doc.id,
                "title": doc.title,
                "content_excerpt": doc.content[:EXCERPT_LENGTH],
                "similarity_score": round(float(score), 6),
            }
            for doc, score in results
        ]
        generated_answer = generate_answer(query, [doc.content for doc, _score in results])

        return Response({
            "query": query,
            "results": documents_payload,
            "generated_answer": generated_answer,
        })
