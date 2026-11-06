import { apiClient } from "./client";
import type { Document, Paginated, SearchResponse } from "../types";

export function listDocuments() {
  return apiClient.get<Paginated<Document>>("/documents/");
}

export function getDocument(id: number) {
  return apiClient.get<Document>(`/documents/${id}/`);
}

export function createDocument(data: { title: string; content: string }) {
  return apiClient.post<Document>("/documents/", data);
}

export function updateDocument(id: number, data: { title?: string; content?: string }) {
  return apiClient.patch<Document>(`/documents/${id}/`, data);
}

export function deleteDocument(id: number) {
  return apiClient.delete(`/documents/${id}/`);
}

export function searchDocuments(query: string, k = 5) {
  return apiClient.get<SearchResponse>("/search/", { params: { q: query, k } });
}
