import { useState, type FormEvent } from "react";

import { searchDocuments } from "../../api/documents";
import { extractErrorMessage } from "../../api/client";
import type { SearchResponse } from "../../types";

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setError(null);
    setLoading(true);
    try {
      const res = await searchDocuments(query, topK);
      setResponse(res.data);
      setHasSearched(true);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  const isStubAnswer = response?.generated_answer.startsWith("[STUB AI RESPONSE");

  return (
    <div>
      <div className="page-header">
        <h1>Search</h1>
      </div>

      <div className="card stub-notice">
        AI responses are placeholder stubs unless an OPENAI_API_KEY is configured on the backend.
        Stub embeddings are also NOT semantically meaningful - search ranking will look arbitrary
        until a real API key is set. See the README for details.
      </div>

      <div className="card">
        <form className="inline-form" onSubmit={handleSubmit}>
          <label>
            Query
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. how do I budget for an emergency fund?"
              required
            />
          </label>
          <label>
            Results
            <input
              type="number"
              min={1}
              max={50}
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
            />
          </label>
          <button type="submit" disabled={loading}>{loading ? "Searching..." : "Search"}</button>
        </form>
        {error && <div className="form-error">{error}</div>}
      </div>

      {hasSearched && response && (
        <>
          <div className="card answer-card">
            <h2>Answer</h2>
            {isStubAnswer && (
              <div className="stub-notice small">
                AI responses are placeholder stubs — set OPENAI_API_KEY on the backend for real output.
              </div>
            )}
            <p>{response.generated_answer}</p>
          </div>

          <div className="card">
            <h2>Matching documents</h2>
            {response.results.length === 0 ? (
              <p className="muted">No documents found. Add some on the Documents page first.</p>
            ) : (
              <ul className="search-results">
                {response.results.map((result) => (
                  <li key={result.id} className="search-result">
                    <div className="search-result-header">
                      <strong>{result.title}</strong>
                      <span className="muted">similarity: {result.similarity_score.toFixed(4)}</span>
                    </div>
                    <p className="muted">{result.content_excerpt}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  );
}
