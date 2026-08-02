"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import {
  Database,
  MessageSquare,
  Moon,
  Plus,
  Sun,
  Trash2,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { Conversation } from "@/lib/types";
import { Button } from "@/components/ui/button";

interface SidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  open: boolean;
  onClose: () => void;
  provider: string;
  model: string;
  backendOnline: boolean;
}

export function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
  open,
  onClose,
  provider,
  model,
  backendOnline,
}: SidebarProps) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const modelShort = model.includes("/")
    ? model.split("/").slice(-2).join("/").replace(":Q4_K_M", "")
    : model;

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onClose}
        />
      )}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-border bg-card/80 backdrop-blur transition-transform duration-200 lg:static lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex items-center gap-3 px-4 pt-5 pb-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-foreground text-background shadow-md">
            <Database size={18} />
          </div>
          <div className="flex-1 leading-tight">
            <p className="text-sm font-semibold">AI SQL Assistant</p>
            <p className="text-[11px] text-muted-foreground">LangChain + local LLM</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={onClose}
            aria-label="Fermer"
          >
            <X size={18} />
          </Button>
        </div>

        <div className="px-3 pb-2">
          <Button
            onClick={onNew}
            className="w-full justify-start gap-2 rounded-xl"
            size="lg"
          >
            <Plus size={18} />
            Nouveau chat
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-2">
          {conversations.length === 0 ? (
            <p className="px-2 py-6 text-center text-xs text-muted-foreground">
              Aucune conversation pour l'instant.
            </p>
          ) : (
            <ul className="space-y-1">
              {conversations.map((conv) => (
                <li key={conv.id} className="group relative">
                  <button
                    onClick={() => onSelect(conv.id)}
                    className={cn(
                      "flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm transition-colors",
                      conv.id === activeId
                        ? "bg-accent text-accent-foreground"
                        : "text-muted-foreground hover:bg-accent/60 hover:text-accent-foreground",
                    )}
                  >
                    <MessageSquare size={15} className="shrink-0" />
                    <span className="truncate">{conv.title}</span>
                  </button>
                  <button
                    onClick={() => onDelete(conv.id)}
                    aria-label="Supprimer"
                    className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-muted-foreground opacity-0 transition-opacity hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100"
                  >
                    <Trash2 size={14} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="border-t border-border p-3">
          <div className="flex items-center gap-2 rounded-lg bg-muted/60 px-3 py-2">
            <span
              className={cn(
                "h-2 w-2 shrink-0 rounded-full",
                backendOnline ? "bg-foreground" : "bg-muted-foreground",
              )}
            />
            <div className="min-w-0 flex-1 leading-tight">
              <p className="truncate text-xs font-medium capitalize">
                {provider === "nvidia"
                  ? "NVIDIA NIM"
                  : provider === "gemini"
                    ? "Google Gemini"
                    : "Ollama (local)"}
              </p>
              <p className="truncate text-[11px] text-muted-foreground" title={model}>
                {modelShort}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 shrink-0"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              aria-label="Basculer le thème"
            >
              {mounted && theme === "dark" ? <Sun size={15} /> : <Moon size={15} />}
            </Button>
          </div>
        </div>
      </aside>
    </>
  );
}
