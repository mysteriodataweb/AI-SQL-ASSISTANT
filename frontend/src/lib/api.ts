import type { BackendConfig, ChatMessage, StreamHandlers } from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function fetchConfig(): Promise<BackendConfig> {
  const res = await fetch(`${API_URL}/api/config`);
  if (!res.ok) throw new Error(`Backend unreachable (${res.status})`);
  return res.json();
}

/**
 * Stream the chat answer from the backend over SSE.
 * Returns an AbortController so the caller can stop the stream.
 */
export function streamChat(
  message: string,
  history: ChatMessage[],
  handlers: StreamHandlers,
): AbortController {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          history: history
            .filter((m) => m.content)
            .map((m) => ({ role: m.role, content: m.content })),
        }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        throw new Error(`Erreur backend (${res.status})`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      const handleBlock = (block: string) => {
        const lines = block.split("\n");
        let event = "message";
        const dataLines: string[] = [];
        for (const line of lines) {
          if (line.startsWith("event:")) event = line.slice(6).trim();
          else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
        }
        if (dataLines.length === 0) return;
        let data: Record<string, unknown>;
        try {
          data = JSON.parse(dataLines.join("\n"));
        } catch {
          return;
        }
        switch (event) {
          case "meta":
            handlers.onMeta?.(data as { provider: string; model: string });
            break;
          case "sql":
            handlers.onSql?.(String(data.sql ?? ""));
            break;
          case "status":
            handlers.onStatus?.(String(data.message ?? ""));
            break;
          case "token":
            handlers.onToken?.(String(data.delta ?? ""));
            break;
          case "error":
            handlers.onError?.(String(data.message ?? "Une erreur est survenue."));
            break;
          case "done":
            handlers.onDone?.();
            break;
        }
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() ?? "";
        for (const block of blocks) handleBlock(block);
      }
      if (buffer.trim()) handleBlock(buffer);
    } catch (err) {
      if (!controller.signal.aborted) {
        handlers.onError?.(
          err instanceof Error
            ? err.message
            : "Impossible de contacter le backend. Vérifiez qu'il est lancé.",
        );
      }
    }
  })();

  return controller;
}
