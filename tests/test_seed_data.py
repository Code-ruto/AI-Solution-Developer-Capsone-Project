import pandas as pd

import seed_data


def test_load_books_df_reads_csv():
    df = seed_data.load_books_df()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert {"title", "author", "subject", "call_number", "shelf", "copies", "status"}.issubset(set(df.columns))


def test_seed_chroma_accepts_dataframe():
    df = seed_data.load_books_df()
    seeded = seed_data.seed_chroma(df)
    assert seeded is not None
