"use client";

import { Database, Sparkles } from "lucide-react";

const SUGGESTIONS = [
  "Quel est notre produit le plus vendu le mois dernier ?",
  "Chiffre d'affaires total par pays, trié du plus haut au plus bas",
  "Quels sont les 5 clients avec le plus de commandes ?",
  "Combien de commandes sont en attente (pending) ?",
];

interface WelcomeProps {
  tables: string[];
  onSuggestion: (text: string) => void;
}

export function Welcome({ tables, onSuggestion }: WelcomeProps) {
  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col items-center px-4 pt-[12vh] text-center animate-fade-in-up">
      <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-foreground text-background shadow-lg">
        <Database size={26} />
      </div>
      <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
        Posez une question sur vos données
      </h1>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        Décrivez ce que vous voulez savoir en langage naturel. L'assistant génère
        le SQL, l'exécute et vous répond.
      </p>

      <div className="mt-8 grid w-full gap-2 sm:grid-cols-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onSuggestion(s)}
            className="group flex items-start gap-2 rounded-xl border border-border bg-card p-3 text-left text-xs text-muted-foreground transition-all hover:border-border hover:bg-accent hover:text-foreground"
          >
            <Sparkles
              size={13}
              className="mt-0.5 shrink-0 text-muted-foreground group-hover:text-foreground"
            />
            {s}
          </button>
        ))}
      </div>

      {tables.length > 0 && (
        <p className="mt-8 text-[11px] text-muted-foreground">
          Tables disponibles :{" "}
          <span className="font-medium text-foreground/80">
            {tables.map((t) => `\`${t}\``).join(" · ")}
          </span>
        </p>
      )}
    </div>
  );
}
