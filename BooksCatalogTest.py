# Adding CSV of Books catalog and converting it to a sqlite3 Database
import pandas as pd
import sqlite3


books_df = pd.read_csv("BooksCatalog.csv")
print(books_df.shape)   # should print (25, 7) — 25 rows, 7 columns
print(books_df.head())  # shows first 5 rows
print(books_df.dtypes)  # check: is `copies` already read as int64?


conn = sqlite3.connect("catalog.db")   # creates catalog.db if it doesn't exist yet
books_df.to_sql(
    "books",           # the table name you want inside catalog.db
    conn,               # the connection to write through
    if_exists="replace",  # if the table already exists, drop and recreate it
    index=False          # don't write pandas' row-number index as its own column
)
conn.close()


cursor = conn.execute("SELECT COUNT(*) FROM books")
print(cursor.fetchone())   # should print (25,)
cursor = conn.execute("SELECT title, copies, status FROM books WHERE copies > 1")
print(cursor.fetchall())
conn.close()