export interface ColumnInfo {
  name: string;
  type: string;
}

export interface TableInfo {
  name: string;
  columns: ColumnInfo[];
}

export interface BackendConfig {
  provider: string;
  ollama: { model: string; base_url: string };
  nvidia: { model: string; configured: boolean };
  gemini: { model: string; configured: boolean };
  tables: TableInfo[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sql?: string;
  status?: "streaming" | "done" | "error";
  error?: string;
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: number;
  messages: ChatMessage[];
}

export interface StreamHandlers {
  onMeta?: (meta: { provider: string; model: string }) => void;
  onSql?: (sql: string) => void;
  onStatus?: (message: string) => void;
  onToken?: (delta: string) => void;
  onError?: (message: string) => void;
  onDone?: () => void;
}
