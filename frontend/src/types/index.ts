export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  date_joined: string;
}

export interface Document {
  id: number;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface SearchResult {
  id: number;
  title: string;
  content_excerpt: string;
  similarity_score: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  generated_answer: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
