export interface Citation {
  id: number;
  source_file: string;
  page_number: number;
  snippet: string;
}

export interface QueryResponse {
  answer_text: string;
  citations: Citation[];
}

export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: Date;
}

export interface UploadResponse {
  message: string;
  stats: {
    pages: number;
    chunks_added: number;
    chunks_skipped: number;
    empty_pages: number;
  };
}

