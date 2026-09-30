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




def find_exact_match(query: str, db_path: str = "catalog.db") -> list[dict]:
    """Look up books by partial title or author match (case-insensitive). Returns a list, possibly empty."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM books WHERE LOWER(title) LIKE LOWER(?) OR LOWER(author) LIKE LOWER(?) ORDER BY title",
        (f"%{query}%", f"%{query}%")
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

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

def semantic_search(topic: str, client, threshold: float = 1.0, collection_name: str = COLLECTION_NAME) -> dict | None:
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

def search_catalog(user_query: str, client) -> dict:
    intent = extract_intent(user_query)
    print("DEBUG intent:", intent)

    exact_matches = find_exact_match(intent["value"])

    if exact_matches:
        first = exact_matches[0]
        result_status = "checked_out" if first["status"] == "checked out" else "found"
        return {
            "status": result_status,
            "book": first,
            "match_count": len(exact_matches),
        }

    semantic_result = semantic_search(intent["value"], client)
    if semantic_result is not None:
        result_status = "checked_out" if semantic_result["status"] == "checked out" else "found"
        return {"status": result_status, "book": semantic_result, "match_count": 1}

    return {"status": "not_found"}
    

def format_response(result: dict) -> str:
    """Turn a search_catalog result into a natural-language sentence."""
    prompt = f"""You are a friendly library assistant. Given the following search result,
        write ONE short, natural sentence for the student. Only use the facts given below,
        do not add any information not present here. If match_count is greater than 1,
        mention that there are multiple matches and this is just one of them.
        Do not include any preamble, introductory text, emojis, or explanation, output only the sentence itself.

Result: {result}
"""
    return ask_llm(prompt)

if __name__ == "__main__":
    test_client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
    for query in ["something by Shakespeare", "do you have 1984?", "something about cooking"]:
        result = search_catalog(query, test_client)
        print(result)
        print(format_response(result))
        print()