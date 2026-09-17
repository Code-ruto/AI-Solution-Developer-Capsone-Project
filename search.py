import sqlite3

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

if __name__ == "__main__":
    print(find_exact_match("1984"))
    print(find_exact_match("dune"))
    print(find_exact_match("Purple Elephant"))