from __future__ import annotations

from pathlib import Path
from config import PROJECT_ROOT, BOOKS_CSV_PATH, CHROMA_DB_PATH, COLLECTION_NAME

import chromadb
import pandas as pd


def load_books_df(csv_path: str | Path = BOOKS_CSV_PATH) -> pd.DataFrame:
    """Load the library book catalog into a DataFrame and check if any required columns are missing."""
    df = pd.read_csv(csv_path)
    required_columns = {
        "title",
        "author",
        "subject",
        "call_number",
        "shelf",
        "copies",
        "status",
    }
    missing = required_columns - set(df.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"CSV is missing required columns: {missing_list}")
    return df


def seed_chroma(books_df: pd.DataFrame, collection_name: str = COLLECTION_NAME, persist_dir: str | Path = CHROMA_DB_PATH) -> dict:
    """Embed each book subject into a ChromaDB collection for semantic search."""
    client = chromadb.PersistentClient(path=str(persist_dir))
    collection = client.get_or_create_collection(collection_name)

    documents: list[str] = []
    ids: list[str] = []
    metadatas: list[dict] = []

    for i, row in books_df.iterrows():
        subject = str(row.get("subject", "")).strip()
        if not subject:
            continue

        documents.append(subject)
        ids.append(str(i))
        metadatas.append(
            {
                "title": str(row["title"]),
                "author": str(row["author"]),
                "call_number": str(row["call_number"]),
                "shelf": str(row["shelf"]),
                "copies": int(row["copies"]),
                "status": str(row["status"]),
            }
        )

    if documents:
        collection.add(documents=documents, ids=ids, metadatas=metadatas)

    return {
        "collection": collection_name,
        "document_count": len(documents),
    }


if __name__ == "__main__":
    books_df = load_books_df()
    result = seed_chroma(books_df)
    print(result)
    