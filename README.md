# AI SQL Assistant

> Interrogez votre base de données **en langage naturel** — l'assistant génère le SQL, l'exécute et vous répond en clair.

![Backend](https://img.shields.io/badge/backend-FastAPI-009688?style=flat-square)
![Frontend](https://img.shields.io/badge/frontend-Next.js%2015-000000?style=flat-square)
![LLM](https://img.shields.io/badge/LLM-Ollama%20%2F%20NVIDIA%20NIM-4B5563?style=flat-square)

Posez une question en français (ou autre langue) : « *Quel est notre produit le plus vendu ce mois-ci ?* ».
L'assistant traduit la question en **SQL**, l'exécute sur votre base de données en **lecture seule**, puis
**résume le résultat** en langage naturel, avec les bons chiffres.

---

## ✨ Fonctionnalités

- 🗣️ **Langage naturel → SQL** : aucune connaissance de SQL requise.
- ⚡ **Réponses en streaming** (SSE) : le texte s'affiche token par token.
- 🛡️ **Sécurité** : requêtes en lecture seule uniquement (SELECT / WITH), écritures bloquées.
- 💬 **Historique de conversation** : sidebar type ChatGPT, persistance locale (localStorage).
- 🌙 **Mode sombre / clair**.
- 🧠 **LLM au choix** : Ollama **local** (gratuit, privé) ou **NVIDIA NIM** (modèles 70B en cloud).

## 🧠 Comment ça marche ?

```
question ──▶ [LLM : schéma + règles] ──▶ SQL validé
                                             │
                                             ▼
                              [SQLite en lecture seule]
                                             │
                                             ▼
       réponse claire ◀── [LLM : interprète les résultats]
```

1. Le LLM reçoit le **schéma de la base** + vos règles et génère le SQL.
2. La requête est **validée** (lecture seule) puis **exécutée**.
3. Le LLM **interprète les résultats** et répond en langage naturel.

## 🚀 Démarrage rapide

### Prérequis

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.com) avec un modèle : `ollama pull qwen3:1.7b`

### 1. Backend (FastAPI + LangChain)

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate            # Windows (ou: source .venv/bin/activate)
pip install -r requirements.txt

copy .env.example .env              # Windows (ou: cp .env.example .env)
uvicorn app.main:app --port 8000
```

À la première exécution, une base SQLite de démo est créée automatiquement (`backend/data/sales.db`).

### 2. Frontend (Next.js)

```bash
cd frontend
npm install
copy .env.local.example .env.local  # Windows (ou: cp .env.local.example .env.local)
npm run dev                         # → http://localhost:3000
```

Ouvrez **http://localhost:3000** et posez votre première question.

## ⚙️ Choisir le LLM

| Provider        | Avantages                                             | Config                                              |
|-----------------|-------------------------------------------------------|-----------------------------------------------------|
| **Ollama**      | 100 % local, gratuit, hors-ligne, privé               | `LLM_PROVIDER=ollama`, `OLLAMA_MODEL=...`           |
| **Gemini**      | Très intelligents, aucun GPU requis                   | `LLM_PROVIDER=gemini` + `GEMINI_API_KEY` (gratuit sur [aistudio.google.com](https://aistudio.google.com/apikey)) |
| **NVIDIA NIM**  | Modèles 70B de très haute qualité, aucun GPU requis   | `LLM_PROVIDER=nvidia` + `NVIDIA_API_KEY` (gratuit sur [build.nvidia.com](https://build.nvidia.com)) |

### Modèles Ollama conseillés

- `qwen3:1.7b` — léger et rapide, idéal CPU / petit GPU *(défaut)*
- `hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M` — plus précis, exige ~8 Go de VRAM

> 💡 **GPU limité ?** Si Ollama échoue avec une erreur `cudaMalloc: out of memory`, forcez le CPU :
> définissez la variable d'environnement `OLLAMA_NUM_GPU=0` puis redémarrez Ollama.

## 🗄️ Utiliser votre propre base

Par défaut l'assistant lit `backend/data/sales.db` (SQLite). Pour votre propre base :
modifiez `DATABASE_PATH` dans `backend/.env` (SQLite), ou adaptez `app/schema.py` et `app/chains.py`
(`_run_query`) pour PostgreSQL / MySQL.

## 📡 API

| Méthode | Endpoint      | Description                                          |
|---------|---------------|------------------------------------------------------|
| GET     | `/api/config` | Provider, modèle, tables du schéma                   |
| POST    | `/api/chat`   | SSE : `meta` → `sql` → `status` → `start` → `token*` → `done` |
| POST    | `/api/reset`  | Régénère la base de démo                             |

### Tester l'API directement

```bash
curl -N -X POST http://localhost:8000/api/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"Quel est le produit le plus vendu ?\", \"history\": []}"
```

## 🛠️ Stack technique

| Couche    | Technologie                                   |
|-----------|-----------------------------------------------|
| Frontend  | Next.js 15, Tailwind CSS, react-markdown      |
| Backend   | FastAPI, LangChain, SQLAlchemy, SQLite        |
| LLM       | Ollama (local) ou NVIDIA NIM (cloud)          |

## 📄 Licence

Projet libre — consultez le dépôt pour plus de détails.
