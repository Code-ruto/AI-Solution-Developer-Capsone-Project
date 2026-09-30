import sqlite3
import ollama
import json
import chromadb
import logging
import time

import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    force=True,
)
logger = logging.getLogger(__name__)

from config import CHROMA_DB_PATH, COLLECTION_NAME

import ollama

def ask_llm(prompt: str, model: str = "llama3.2") -> str:
    start = time.time()
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response.message.content
    if content is None:
        raise ValueError("Model returned no content")
    logger.info(f"ask_llm took {time.time() - start:.2f}s")
    return content




def find_exact_match(query: str, db_path: str = "catalog.db") -> list[dict]:
    start = time.time()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM books WHERE LOWER(title) LIKE LOWER(?) OR LOWER(author) LIKE LOWER(?) ORDER BY title",
        (f"%{query}%", f"%{query}%")
    )
    rows = cursor.fetchall()
    conn.close()
    logger.info(f"find_exact_match took {time.time() - start:.3f}s, {len(rows)} results")
    return [dict(row) for row in rows]

def extract_intent(user_query: str) -> dict:
    """Use the LLM to classify a query as title/author/topic and extract the search term."""
    start = time.time()
    prompt = f"""You are a library search assistant. Classify the user's query as one of:
"title", "author", or "topic". Respond with ONLY valid JSON in this exact format:
{{"type": "<title|author|topic>", "value": "<the extracted search term>"}}

User query: "{user_query}"
"""
    raw_response = ask_llm(prompt)

    try:
        intent = json.loads(raw_response)
    except json.JSONDecodeError:
        intent = {"type": "unknown", "value": user_query}

    logger.info(f"extract_intent total: {time.time() - start:.2f}s, intent={intent}")
    return intent
    


def semantic_search(topic: str, client, threshold: float = 1.0, collection_name: str = COLLECTION_NAME) -> dict | None:
    start = time.time()
    collection = client.get_or_create_collection(collection_name)

    if collection.count() == 0:
        logger.info(f"semantic_search took {time.time() - start:.3f}s, empty collection")
        return None

    results = collection.query(query_texts=[topic], n_results=1)

    if not results.get("distances") or not results["distances"][0]:
        logger.info(f"semantic_search took {time.time() - start:.3f}s, no distances")
        return None

    distance = results["distances"][0][0]
    logger.info(f"semantic_search took {time.time() - start:.3f}s, distance={distance:.3f}")

    if distance > threshold:
        return None

    if not results.get("metadatas") or not results["metadatas"][0]:
        return None

    return results["metadatas"][0][0]

def search_catalog(user_query: str, client) -> dict:
    total_start = time.time()
    intent = extract_intent(user_query)

    exact_matches = find_exact_match(intent["value"])

    if exact_matches:
        first = exact_matches[0]
        result_status = "checked_out" if first["status"] == "checked out" else "found"
        logger.info(f"search_catalog total: {time.time() - total_start:.2f}s (exact match path)")
        return {"status": result_status, "book": first, "match_count": len(exact_matches)}

    semantic_result = semantic_search(intent["value"], client)
    if semantic_result is not None:
        result_status = "checked_out" if semantic_result["status"] == "checked out" else "found"
        logger.info(f"search_catalog total: {time.time() - total_start:.2f}s (semantic path)")
        return {"status": result_status, "book": semantic_result, "match_count": 1}

    logger.info(f"search_catalog total: {time.time() - total_start:.2f}s (not found)")
    return {"status": "not_found"}
    

def format_response(result: dict) -> str:
    """Turn a search_catalog result into a natural-language sentence, no LLM needed."""
    if result["status"] == "not_found":
        return "Sorry, I couldn't find anything matching that in our catalog."

    book = result["book"]
    multiple_note = f" (one of {result['match_count']} matches)" if result.get("match_count", 1) > 1 else ""

    if result["status"] == "checked_out":
        return f'"{book["title"]}" by {book["author"]} is currently checked out{multiple_note}.'

    return f'"{book["title"]}" by {book["author"]} is available on the {book["shelf"]} shelf{multiple_note}.'


if __name__ == "__main__":
    test_client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
    for query in ["something by Shakespeare", "do you have 1984?", "something about cooking"]:
        result = search_catalog(query, test_client)
        print(result)
        print(format_response(result))
        print()