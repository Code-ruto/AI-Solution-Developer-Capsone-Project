"""
Pulls real, subject-tagged books from Open Library's free Subjects API
and writes them into a CSV matching your existing BooksCatalog.csv schema.
Open Library's usage guidelines ask for a real User-Agent and no
high-volume scraping, this script respects both: one request per
subject, with a short pause between requests.
"""

import csv
import random
import time

import requests

# Each subject pulls up to `limit` books.

# Books are limited to the subjects below for more accurate subject classification
SUBJECTS = [
    "fiction", "science_fiction", "fantasy", "mystery", "biology",
    "poetry", "cooking", "travel", "sports",
    "computer_science", "mathematics", "biography", "history",
]

LIMIT_PER_SUBJECT = 20  # 13 subjects x 20 books = up to 260 rows

HEADERS = {
    # Open Library asks apps to identify themselves
    "User-Agent": "CAP942-LibraryBookFinder/1.0 (student project)"
}

SHELF_MAP = {
    # Map books to corrsesponding shelves based on subject.
    "fiction": "Fiction A-Z",
    "science_fiction": "Fiction A-Z",
    "fantasy": "Fiction A-Z",
    "mystery": "Fiction A-Z",
    "biology": "Nonfiction Science",
    "poetry": "Nonfiction Literature",
    "cooking": "Nonfiction Cooking",
    "travel": "Nonfiction Travel",
    "sports": "Nonfiction Sports",
    "computer_science": "Nonfiction Technology",
    "mathematics": "Nonfiction Math",
    "biography": "Nonfiction Biography",
    "history": "Nonfiction History",
}


def fetch_subject(subject: str, limit: int) -> list[dict]:
    """Fetch one subject's works from Open Library."""
    url = f"https://openlibrary.org/subjects/{subject}.json"
    response = requests.get(url, params={"limit": limit}, headers=HEADERS)
    response.raise_for_status()
    data = response.json()

    rows = []
    for work in data.get("works", []):
        title = work.get("title")
        authors = work.get("authors", [])
        author_name = authors[0]["name"] if authors else "Unknown"

        if not title:
            continue

        rows.append({
            "title": title,
            "author": author_name,
            "subject": subject.replace("_", " "),
            "shelf": SHELF_MAP.get(subject, f"Nonfiction {subject.replace('_', ' ').title()}"),
            "copies": random.randint(1, 3),
            "status": random.choices(
                ["available", "checked out"], weights=[85, 15]
            )[0],
        })
    return rows


def main():
    all_rows = []
    for subject in SUBJECTS:
        print(f"Fetching subject: {subject}")
        try:
            rows = fetch_subject(subject, LIMIT_PER_SUBJECT)
            all_rows.extend(rows)
            print(f"  got {len(rows)} books")
        except requests.RequestException as e:
            print(f"  failed: {e}")
        time.sleep(1)  # be polite to the API

    # de-duplicate by title, since some subjects overlap
    seen = set()
    unique_rows = []
    for row in all_rows:
        key = row["title"].lower()
        if key not in seen:
            seen.add(key)
            unique_rows.append(row)

    with open("BooksCatalogExpanded.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["title", "author", "subject", "shelf", "copies", "status"]
        )
        writer.writeheader()
        writer.writerows(unique_rows)

    print(f"\nWrote {len(unique_rows)} unique books to BooksCatalogExpanded.csv")


if __name__ == "__main__":
    main()
