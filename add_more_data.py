import pandas as pd
from db_connection import db
from sqlalchemy.exc import IntegrityError

books_df = pd.read_csv('books.csv')

last_50_rows = books_df.tail(50)

for index, row in last_50_rows.iterrows():
    authors = row['authors'].split(',')
    isbn = row['isbn10']
    for author in authors:
        try:
            db.session.execute(
                f"INSERT INTO Authors (isbn, authors) VALUES ('{isbn}', '{author.strip()}');"
            )
            db.session.commit()
        except IntegrityError:
            pass

for index, row in last_50_rows.iterrows():
    isbn = row['isbn10']
    title = row['title'].replace("'", "''")
    categories = row['categories'].replace("'", "''") if isinstance(row['categories'], str) else None 
    thumbnail = row['thumbnail'].replace("'", "''") if isinstance(row['thumbnail'], str) else None 
    average_rating = row['average_rating']
    published_year = row['published_year']

    try:
        db.session.execute(
            f"INSERT INTO Books (isbn, title, categories, thumbnail, average_rating, published_year) VALUES ('{isbn}', '{title}', '{categories}', '{thumbnail}', {average_rating}, {published_year});"
        )
        db.session.commit()
    except IntegrityError:
        pass

print("Data insertion completed for the last 50 rows.")
