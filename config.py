from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent # Resolve dependencies between OS
BOOKS_CSV_PATH = PROJECT_ROOT / "BooksCatalog.csv" 
CATALOG_DB_PATH = PROJECT_ROOT / "catalog.db"
CHROMA_DB_PATH = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "book_subjects"
