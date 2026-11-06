"""
Stub-by-default AI layer: embeddings + chat "answer" generation.

Neither function makes a network call or requires any API key unless the
OPENAI_API_KEY environment variable is set. This is deliberate: it lets the
whole pipeline (document storage, embedding storage, similarity search,
ranking, the RAG search endpoint, the seed data migration, and the full test
suite) be built and exercised end-to-end with zero cost and zero network
dependency. Set OPENAI_API_KEY to switch both functions to real OpenAI
calls with no other code changes required anywhere in the app.
"""
import hashlib
import math
import os
import random

from apps.common.embedding_field import EMBEDDING_DIMENSIONS


def _l2_normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0:
        return vector
    return [x / norm for x in vector]


def get_embedding(text: str) -> list[float]:
    """
    Returns an embedding vector (length EMBEDDING_DIMENSIONS) for `text`.

    STUB MODE (default - no OPENAI_API_KEY set):
    Returns a DETERMINISTIC pseudo-random unit vector seeded from a SHA-256
    hash of the input text (same text -> identical vector, every time;
    different text -> a different vector). This is NOT semantically
    meaningful in any way - it does not capture meaning, topic, or
    similarity between texts the way a real embedding model would. It
    exists solely so the full pipeline (storage, pgvector/SQLite similarity
    search, ranking, the search endpoint) is completely testable without an
    API key, network access, or cost. Search results computed against stub
    embeddings will look essentially arbitrary/random with respect to
    meaning - that is expected, not a bug. Set OPENAI_API_KEY to get
    semantically meaningful search.

    REAL MODE (OPENAI_API_KEY set):
    Calls the OpenAI embeddings API using OPENAI_EMBEDDING_MODEL (default
    "text-embedding-3-large") with dimensions=EMBEDDING_DIMENSIONS.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        from openai import OpenAI  # imported lazily: only needed in real mode

        client = OpenAI(api_key=api_key)
        model = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
        response = client.embeddings.create(
            model=model,
            input=text,
            dimensions=EMBEDDING_DIMENSIONS,
        )
        return list(response.data[0].embedding)

    seed = hashlib.sha256(text.encode("utf-8")).hexdigest()
    rng = random.Random(seed)
    vector = [rng.uniform(-1, 1) for _ in range(EMBEDDING_DIMENSIONS)]
    return _l2_normalize(vector)


def generate_answer(question: str, context_snippets: list[str]) -> str:
    """
    Returns a natural-language answer to `question`, grounded in
    `context_snippets` (typically the content of the top search results).

    STUB MODE (default - no OPENAI_API_KEY set): returns a deterministic
    templated string identifying how many documents were found and an
    excerpt of the top match. No network call.

    REAL MODE (OPENAI_API_KEY set): calls the OpenAI chat completions API
    using OPENAI_CHAT_MODEL (default "gpt-5.6-sol") with a prompt that
    instructs the model to ground its answer in context_snippets only.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        from openai import OpenAI  # imported lazily: only needed in real mode

        client = OpenAI(api_key=api_key)
        model = os.environ.get("OPENAI_CHAT_MODEL", "gpt-5.6-sol")
        context_block = "\n\n".join(f"- {snippet}" for snippet in context_snippets) or "(no documents found)"
        prompt = (
            "Answer the question using ONLY the context snippets below. "
            "If the answer is not contained in the context, say so explicitly.\n\n"
            f"Context:\n{context_block}\n\nQuestion: {question}"
        )
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    top_excerpt = context_snippets[0][:200] if context_snippets else "none"
    return (
        f"[STUB AI RESPONSE — set OPENAI_API_KEY for real output] "
        f"Found {len(context_snippets)} related document(s). Top match excerpt: {top_excerpt}"
    )
