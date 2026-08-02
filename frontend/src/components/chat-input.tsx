"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUp, Square } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface ChatInputProps {
  disabled: boolean;
  onSend: (text: string) => void;
  onStop: () => void;
}

export function ChatInput({ disabled, onSend, onStop }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "0px";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [value]);

  const submit = () => {
    const text = value.trim();
    if (!text || disabled) return;
    setValue("");
    onSend(text);
  };

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-5">
      <div className="relative">
        <Textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="Ex : Quel est notre produit le plus vendu ce mois-ci ?"
          className="pr-14 shadow-lg shadow-black/5 dark:shadow-black/20"
        />
        <div className="absolute bottom-2 right-2">
          {disabled ? (
            <Button
              variant="destructive"
              size="icon"
              onClick={onStop}
              aria-label="Arrêter"
            >
              <Square size={14} fill="currentColor" />
            </Button>
          ) : (
            <Button
              size="icon"
              onClick={submit}
              disabled={!value.trim()}
              aria-label="Envoyer"
              className={cn(
                "transition-all",
                value.trim()
                  ? "opacity-100"
                  : "opacity-40 hover:opacity-70",
              )}
            >
              <ArrowUp size={17} />
            </Button>
          )}
        </div>
      </div>
      <p className="mt-2 text-center text-[11px] text-muted-foreground">
        L'assistant peut se tromper. Vérifiez les chiffres importants.
      </p>
    </div>
  );
}
