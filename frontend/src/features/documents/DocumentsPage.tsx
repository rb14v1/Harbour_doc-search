import { useEffect, useState, type FormEvent } from "react";

import { createDocument, deleteDocument, listDocuments, updateDocument } from "../../api/documents";
import { extractErrorMessage } from "../../api/client";
import type { Document } from "../../types";

export function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editing, setEditing] = useState<Document | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const res = await listDocuments();
      setDocuments(res.data.results);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function startEdit(doc: Document) {
    setEditing(doc);
    setTitle(doc.title);
    setContent(doc.content);
  }

  function resetForm() {
    setEditing(null);
    setTitle("");
    setContent("");
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (editing) {
        await updateDocument(editing.id, { title, content });
      } else {
        await createDocument({ title, content });
      }
      resetForm();
      await load();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this document?")) return;
    setError(null);
    try {
      await deleteDocument(id);
      await load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Documents</h1>
      </div>

      <div className="card">
        <form className="document-form" onSubmit={handleSubmit}>
          <label>
            Title
            <input value={title} onChange={(e) => setTitle(e.target.value)} required />
          </label>
          <label>
            Content
            <textarea
              rows={5}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              required
            />
          </label>
          <div className="actions">
            <button type="submit" disabled={submitting}>{editing ? "Save" : "Add document"}</button>
            {editing && <button type="button" className="secondary" onClick={resetForm}>Cancel</button>}
          </div>
        </form>
        {error && <div className="form-error">{error}</div>}
      </div>

      <div className="card">
        {loading ? (
          <p>Loading...</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Content</th>
                <th>Updated</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id}>
                  <td>{doc.title}</td>
                  <td className="muted">{doc.content.slice(0, 120)}{doc.content.length > 120 ? "…" : ""}</td>
                  <td className="muted">{new Date(doc.updated_at).toLocaleString()}</td>
                  <td className="actions">
                    <button className="secondary" onClick={() => startEdit(doc)}>Edit</button>
                    <button className="danger" onClick={() => handleDelete(doc.id)}>Delete</button>
                  </td>
                </tr>
              ))}
              {documents.length === 0 && (
                <tr><td colSpan={4} className="muted">No documents yet.</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
