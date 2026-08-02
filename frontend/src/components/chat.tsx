"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Menu, Wifi, WifiOff } from "lucide-react";
import { API_URL, fetchConfig, streamChat } from "@/lib/api";
import { cn, uid } from "@/lib/utils";
import type { ChatMessage, Conversation } from "@/lib/types";
import { Sidebar } from "@/components/sidebar";
import { MessageItem } from "@/components/message-item";
import { ChatInput } from "@/components/chat-input";
import { Welcome } from "@/components/welcome";

const STORAGE_KEY = "ai-sql-conversations";

function loadConversations(): Conversation[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Conversation[]) : [];
  } catch {
    return [];
  }
}

export default function Chat() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [hydrated, setHydrated] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const [provider, setProvider] = useState("ollama");
  const [model, setModel] = useState("…");
  const [tables, setTables] = useState<string[]>([]);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const streamBufRef = useRef<Record<string, string>>({});

  const active = conversations.find((c) => c.id === activeId) ?? null;

  useEffect(() => {
    setConversations(loadConversations());
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
  }, [conversations, hydrated]);

  useEffect(() => {
    fetchConfig()
      .then((cfg) => {
        setBackendOnline(true);
        setProvider(cfg.provider);
        setModel(cfg.provider === "nvidia" ? cfg.nvidia.model : cfg.ollama.model);
        setTables(cfg.tables.map((t) => t.name));
      })
      .catch(() => {
        setBackendOnline(false);
        setModel("—");
      });
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [conversations, streaming]);

  const patchMessage = useCallback(
    (convId: string, msgId: string, patch: Partial<ChatMessage>) => {
      setConversations((prev) =>
        prev.map((c) =>
          c.id !== convId
            ? c
            : {
                ...c,
                messages: c.messages.map((m) => (m.id === msgId ? { ...m, ...patch } : m)),
              },
        ),
      );
    },
    [],
  );

  const sendMessage = useCallback(
    (text: string) => {
      let convId = activeId;
      if (!convId) {
        convId = uid();
        const title = text.length > 42 ? `${text.slice(0, 42)}…` : text;
        setConversations((prev) => [
          { id: convId as string, title, createdAt: Date.now(), messages: [] },
          ...prev,
        ]);
        setActiveId(convId);
      }

      const userMsg: ChatMessage = { id: uid(), role: "user", content: text, status: "done" };
      const assistantMsg: ChatMessage = {
        id: uid(),
        role: "assistant",
        content: "",
        status: "streaming",
      };

      setConversations((prev) =>
        prev.map((c) =>
          c.id !== convId
            ? c
            : { ...c, messages: [...c.messages, userMsg, assistantMsg] },
        ),
      );
      setStreaming(true);

      const history = conversations.find((c) => c.id === convId)?.messages ?? [];

      streamBufRef.current[assistantMsg.id] = "";
      abortRef.current = streamChat(text, [...history, userMsg], {
        onSql: (sql) => patchMessage(convId as string, assistantMsg.id, { sql }),
        onToken: (delta) => {
          streamBufRef.current[assistantMsg.id] += delta;
          patchMessage(convId as string, assistantMsg.id, {
            content: streamBufRef.current[assistantMsg.id],
          });
        },
        onError: (message) => {
          patchMessage(convId as string, assistantMsg.id, {
            status: "error",
            error: message,
          });
          setStreaming(false);
        },
        onDone: () => {
          patchMessage(convId as string, assistantMsg.id, { status: "done" });
          setStreaming(false);
        },
      });
    },
    [activeId, conversations, patchMessage],
  );

  const stopStream = useCallback(() => {
    abortRef.current?.abort();
    setStreaming(false);
  }, []);

  const selectConversation = (id: string) => {
    setActiveId(id);
    setSidebarOpen(false);
  };

  const newConversation = () => {
    stopStream();
    setActiveId(null);
    setSidebarOpen(false);
  };

  const deleteConversation = (id: string) => {
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (activeId === id) setActiveId(null);
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={selectConversation}
        onNew={newConversation}
        onDelete={deleteConversation}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        provider={provider}
        model={model}
        backendOnline={backendOnline}
      />

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center gap-3 border-b border-border/60 px-4">
          <button
            className="rounded-md p-2 hover:bg-accent lg:hidden"
            onClick={() => setSidebarOpen(true)}
            aria-label="Ouvrir le menu"
          >
            <Menu size={18} />
          </button>
          <h1 className="truncate text-sm font-medium">
            {active ? active.title : "Nouvelle conversation"}
          </h1>
          <div className="ml-auto flex items-center gap-2">
            <span
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px]",
                backendOnline
                  ? "border-border bg-muted text-foreground"
                  : "border-destructive/30 bg-destructive/10 text-destructive",
              )}
              title={backendOnline ? `Connecté à ${API_URL}` : "Backend injoignable"}
            >
              {backendOnline ? <Wifi size={11} /> : <WifiOff size={11} />}
              {backendOnline ? "Backend en ligne" : "Backend hors ligne"}
            </span>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto">
          {!active || active.messages.length === 0 ? (
            <Welcome tables={tables} onSuggestion={sendMessage} />
          ) : (
            <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-6">
              {active.messages.map((m) => (
                <MessageItem key={m.id} message={m} />
              ))}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <ChatInput disabled={streaming} onSend={sendMessage} onStop={stopStream} />
      </main>
    </div>
  );
}
