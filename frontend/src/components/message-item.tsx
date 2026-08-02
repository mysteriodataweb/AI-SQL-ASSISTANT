"use client";

import { useState } from "react";
import { AlertCircle, ChevronDown, Database } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/lib/types";
import { Markdown } from "@/components/markdown";

function TypingDots() {
  return (
    <div className="flex items-center gap-1.5 py-2" aria-label="Réflexion en cours">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-2 w-2 rounded-full bg-muted-foreground/70 animate-dot-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );
}

function SqlCard({ sql }: { sql: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="my-3 overflow-hidden rounded-lg border border-border bg-muted/40">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground"
      >
        <Database size={13} />
        Requête SQL générée
        <ChevronDown
          size={14}
          className={cn("ml-auto transition-transform", open && "rotate-180")}
        />
      </button>
      {open && (
        <pre className="overflow-x-auto border-t border-border bg-black/[0.03] p-3 font-mono text-[0.75rem] leading-5 text-foreground dark:bg-black/30">
          {sql}
        </pre>
      )}
    </div>
  );
}

export function MessageItem({ message }: { message: ChatMessage }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end animate-fade-in-up">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-primary px-4 py-3 text-sm leading-6 text-primary-foreground shadow-sm sm:max-w-[70%]">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3 animate-fade-in-up">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-foreground text-background shadow-sm">
        <Database size={15} />
      </div>
      <div className="min-w-0 flex-1 pt-0.5">
        {message.sql && <SqlCard sql={message.sql} />}

        {message.status === "error" ? (
          <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2.5 text-sm text-destructive">
            <AlertCircle size={16} className="mt-0.5 shrink-0" />
            <div>
              <p className="font-medium">Une erreur est survenue</p>
              <p className="mt-0.5 text-xs opacity-90">{message.error}</p>
            </div>
          </div>
        ) : message.content ? (
          <Markdown>{message.content}</Markdown>
        ) : message.status === "streaming" ? (
          <TypingDots />
        ) : null}

        {message.status === "streaming" && message.content && (
          <div className="mt-1 h-px w-16 bg-primary/40" />
        )}
      </div>
    </div>
  );
}
