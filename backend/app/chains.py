import json
import re
import sqlite3
from typing import Iterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.config import get_settings
from app.llm import get_chat_model
from app.schema import schema_for_prompt

SQL_SYSTEM = """You are an expert SQLite analyst. Given a database schema and a question in natural \
language, you generate the exact SQL query that answers it.

SCHEMA:
{schema}

RULES:
- Return ONLY the raw SQL query. No markdown fences, no comments, no explanations.
- Use the SQLite dialect (strftime, date(), etc.).
- Use table and column names EXACTLY as they appear in the schema.
- Column aliases: use a clear alias for computed columns (e.g. AS revenue, AS total_qty).
- Dates are stored as TEXT like 'YYYY-MM-DD HH:MM:SS'. Use strftime('%Y-%m', created_at) to group by month.
- When the question says "best-selling", "le plus vendu", order by quantity and take the top rows.
- Compute totals with SUM(...) and COUNT(...).
- Never invent columns or tables that are not in the schema.
- If the question is ambiguous, make a sensible assumption and stay with it.

EXAMPLE 1
Question: "Quel est notre produit le plus vendu le mois dernier ?"
SQL: SELECT p.name, SUM(oi.quantity) AS total_qty FROM order_items oi JOIN products p ON p.id = oi.product_id JOIN orders o ON o.id = oi.order_id WHERE strftime('%Y-%m', o.created_at) = strftime('%Y-%m', 'now', '-1 month') GROUP BY p.name ORDER BY total_qty DESC LIMIT 1

EXAMPLE 2
Question: "Quel est le chiffre d'affaires par pays ?"
SQL: SELECT c.country, ROUND(SUM(o.total), 2) AS revenue FROM orders o JOIN customers c ON c.id = o.customer_id GROUP BY c.country ORDER BY revenue DESC
"""

ANSWER_SYSTEM = """You are a friendly data analyst. A user asked a question in natural language. The SQL \
query below was run against the database and produced the results below.

Your job: write a clear, concise answer to the user's question, using the real numbers from the results.
- Respond in the SAME language as the user's question (usually French).
- Lead with the direct answer, then add 1-3 lines of useful context.
- Use markdown: bold key numbers, short lists, a small markdown table when there are several rows.
- Round numbers nicely (money with 2 decimals, quantities as integers).
- If there are no results, say that no matching data was found.
- Never mention the SQL or the schema.
- Never use emojis or emoticons; use plain text and markdown only.

QUESTION:
{question}

SQL:
{sql}

RESULTS:
{results}
"""


def _extract_sql(raw: str) -> str:
    """Extract a clean SQL statement from raw LLM output (robust to fences / thinking tags)."""
    text = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"^```(?:sql)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    text = text.strip()
    lines = text.splitlines()
    for line in reversed(lines):
        if line.strip().lower().startswith(("select", "with")):
            return "; ".join(part.strip() for part in lines[lines.index(line) :]).strip()
    return text


def _guard_sql(sql: str) -> None:
    """Reject anything that is not a read-only query."""
    stripped = sql.strip().rstrip(";").strip()
    if not stripped:
        raise ValueError("The model returned an empty query.")
    if ";" in stripped:
        raise ValueError("Only a single SQL statement is allowed.")
    if not re.match(r"^(select|with|explain)\b", stripped, re.IGNORECASE):
        raise ValueError("Only SELECT (read-only) queries are allowed.")
    if re.search(r"\b(insert|update|delete|drop|alter|create|replace|truncate|attach|detach|pragma|exec|shell)\b", stripped, re.IGNORECASE):
        raise ValueError("The query contains a forbidden SQL keyword.")


def _run_query(sql: str) -> str:
    """Execute the query in read-only mode and format the result for the LLM."""
    settings = get_settings()
    path = str(settings.db_path)
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql)
        cols = [desc[0] for desc in cur.description] if cur.description else []
        rows = cur.fetchmany(settings.max_rows_for_answer + 1)
    except sqlite3.Error as exc:
        raise RuntimeError(f"SQL execution failed: {exc}") from exc
    finally:
        conn.close()

    if not cols:
        return "(query returned no columns)"
    lines = [" | ".join(cols)]
    for row in rows[: settings.max_rows_for_answer]:
        lines.append(" | ".join(str(v) for v in row))
    total = f"... ({len(rows)} rows shown)" if len(rows) > settings.max_rows_for_answer else f"({len(rows)} row(s))"
    lines.append(total)
    return "\n".join(lines)


def _to_messages(question: str, history: list[dict]) -> list:
    messages: list = []
    for item in history[-6:]:
        role = item.get("role")
        content = item.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=question))
    return messages


def generate_sql(question: str, history: list[dict]) -> str:
    """Step 1 + 2: turn the question into a validated SQL query, with one retry on error."""
    model, _, _ = get_chat_model()
    settings = get_settings()
    system = SQL_SYSTEM.format(schema=schema_for_prompt())
    messages = [SystemMessage(content=system)] + _to_messages(question, history)

    response = model.invoke(messages)
    sql = _extract_sql(response.content)

    try:
        _guard_sql(sql)
        _run_query(sql)
    except (ValueError, RuntimeError) as exc:
        messages.append(AIMessage(content=response.content))
        messages.append(
            HumanMessage(content=f"The query above failed or was rejected: {exc}. "
                                f"Please fix it and return ONLY the corrected SQL query.")
        )
        retry = model.invoke(messages)
        sql = _extract_sql(retry.content)
        _guard_sql(sql)
        _run_query(sql)

    return sql


def _answer_chain(model):
    def run(inputs: dict) -> Iterator:
        messages = [SystemMessage(content=ANSWER_SYSTEM.format(**inputs)), HumanMessage(content=inputs["question"])]
        return model.stream(messages)

    return run


def chat_stream(question: str, history: list[dict]) -> Iterator[str]:
    """Full pipeline with SSE events: sql -> status -> answer tokens -> done."""
    model, provider, model_name = get_chat_model()

    def event(name: str, data: dict) -> str:
        return f"event: {name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    yield event("meta", {"provider": provider, "model": model_name})

    try:
        sql = generate_sql(question, history)
    except Exception as exc:
        yield event("error", {"message": f"Impossible de générer la requête SQL : {exc}"})
        return

    yield event("sql", {"sql": sql})
    yield event("status", {"message": "Exécution de la requête…"})

    try:
        results = _run_query(sql)
    except Exception as exc:
        yield event("error", {"message": f"Erreur lors de l'exécution : {exc}"})
        return

    yield event("start", {})
    try:
        stream = _answer_chain(model)
        for chunk in stream({"question": question, "sql": sql, "results": results}):
            text = chunk.content if hasattr(chunk, "content") else str(chunk)
            if text:
                yield event("token", {"delta": text})
    except Exception as exc:
        yield event("error", {"message": f"Erreur lors de l'interprétation : {exc}"})

    yield event("done", {})


if __name__ == "__main__":
    import sys

    question = " ".join(sys.argv[1:]) or "Quel est le produit le plus vendu ?"
    from app.database import create_database

    create_database()
    for ev in chat_stream(question, []):
        print(ev, end="")
