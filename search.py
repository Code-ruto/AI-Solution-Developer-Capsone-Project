import sqlite3
import ollama
import json

import ollama

def ask_llm(prompt: str, model: str = "llama3.2") -> str:
    """Converts all parameters into string type data. Instantiates llama 3.2 llm instance
    and sets the response to get the prompt from users. Will return the content of the response.
    Handles empty content returns with message displaying that no model content was returned."""
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response.message.content
    if content is None:
        raise ValueError("Model returned no content")
    return content  # now guaranteed to be str




def find_exact_match(query: str, db_path: str = "catalog.db") -> dict | None:  # replace db path with database name
    """Look up a book by exact title or author match (case-insensitive)."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # lets you access columns by name, not just index
    cursor = conn.cursor() # This is the cursor that iterates over the database

    # TODO #1 solved: search title OR author, case-insensitive, using
    # parameterized ? placeholders (never string-format user input into SQL)
    cursor.execute(
        "SELECT * FROM books WHERE LOWER(title) = LOWER(?) OR LOWER(author) = LOWER(?)",
        (query, query)
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    # TODO #2 solved: sqlite3.Row supports dict() conversion directly
    # because of the row_factory line above
    return dict(row)

def extract_intent(user_query: str) -> dict:
    """Use the LLM to classify a query as title/author/topic and extract the search term."""
    prompt = f"""You are a library search assistant. Classify the user's query as one of:
"title", "author", or "topic". Respond with ONLY valid JSON in this exact format:
{{"type": "<title|author|topic>", "value": "<the extracted search term>"}}

User query: "{user_query}"
"""
    raw_response = ask_llm(prompt)

    try:
        intent = json.loads(raw_response)
    except json.JSONDecodeError:
        # the model didn't return clean JSON — fall back to a safe default
        # rather than crashing, so the rest of your pipeline can handle it
        intent = {"type": "unknown", "value": user_query}

    return intent

if __name__ == "__main__":
    print(extract_intent("do you have anything by George Orwell?"))
    print(extract_intent("where can I find 1984?"))
    print(extract_intent("something about World War II"))