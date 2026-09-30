import sqlite3
import ollama
import json
import chromadb
from config import CHROMA_DB_PATH, COLLECTION_NAME

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

    cursor.execute(
        "SELECT * FROM books WHERE LOWER(title) = LOWER(?) OR LOWER(author) = LOWER(?)",
        (query, query)
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

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

def semantic_search(topic: str, threshold: float = 1.0, collection_name: str = COLLECTION_NAME, persist_dir: str = str(CHROMA_DB_PATH)) -> dict | None:    
    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection(collection_name)

    print(f"\n--- query: {topic!r}, collection count: {collection.count()} ---")

    if collection.count() == 0:
        return None

    results = collection.query(query_texts=[topic], n_results=1)
    print("raw results:", results)  # <-- see the whole thing before any filtering

    if not results.get("distances") or not results["distances"][0]:
        print("failed the distances-empty check")
        return None

    distance = results["distances"][0][0]
    print("distance:", distance)

    if distance > threshold:
        print("failed the threshold check")
        return None

    if not results.get("metadatas") or not results["metadatas"][0]:
        print("failed the metadatas-empty check")
        return None

    return results["metadatas"][0][0]

def search_catalog(user_query: str) -> dict:
    intent = extract_intent(user_query)

    # Always try exact match first, regardless of what the LLM classified 
    # this protects against misclassification (e.g., a title read as a topic)
    exact_result = find_exact_match(intent["value"])

    if exact_result is not None:
        if exact_result["status"] == "checked out":
            return {"status": "checked_out", "book": exact_result}
        return {"status": "found", "book": exact_result}

    semantic_result = semantic_search(intent["value"])
    if semantic_result is not None:
        if semantic_result["status"] == "checked out":
            return {"status": "checked_out", "book": semantic_result}
        return {"status": "found", "book": semantic_result}

    return {"status": "not_found"}

    return {"status": "not_found"}

def format_response(result: dict) -> str:
    """Turn a search_catalog result into a natural-language sentence."""
    prompt = f"""You are a friendly library assistant. Given the following search result,
write ONE short, natural sentence for the student. Only use the facts given below —
do not add any information not present here.

Result: {result}
"""
    return ask_llm(prompt)


if __name__ == "__main__":
    for query in ["do you have 1984?", "do you have anything by Rachel Carson?", "something about ancient military strategy", "purple elephant recipes"]:
        result = search_catalog(query)
        print(format_response(result))
