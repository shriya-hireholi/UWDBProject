import requests
from flask import Flask, session, render_template, request, redirect, jsonify, url_for
from flask_session import Session
from db_connection import db, app
from sqlalchemy import text

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def check_user_session():
    is_logged_in = False
    if session.get("username") is not None:
        is_logged_in = True
    return redirect(url_for('home_page', is_active=is_logged_in))


@app.route("/temp_home", methods=["GET", "POST"])
def home_page():
    is_active = request.args.get('is_active') == "True"
    query = f"SELECT TOP 10 * FROM books ORDER BY average_rating DESC;"
    get_top_10_books = db.session.execute(text(query))
    return render_template("search_result.html", ans=get_top_10_books, is_active=is_active)

@app.route("/login", methods=["GET", "POST"])
def login_page():
    session.clear()
    user_name = request.form.get("name")
    user_password = request.form.get("pwd")
    print(user_name)
    print(user_password)
    if user_name and user_password:
        query = f"SELECT user_password FROM users WHERE username LIKE '%{user_name}%';"
        password = db.session.execute(text(query)).fetchone()
        if password is not None and user_password == password[0]:
            session["username"] = user_name
            return redirect(url_for('home_page', is_active=True))
        else:
            return redirect(url_for('signup_page'))
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup_page():
    user_name = request.form.get("name")
    user_password = request.form.get("pwd")
    if user_name and user_password:
        query = text("INSERT INTO users (username, user_password) VALUES (:username, :user_password);")
        db.session.execute(query,{"username": user_name, "user_password": user_password})
        db.session.commit()
        session["username"] = user_name
        return redirect(url_for('home_page', is_active=True))
    return render_template("signup.html")

@app.route("/find", methods=["POST"])
def find():
    isbn = request.form.get("isbn")
    title = request.form.get("name")
    author = request.form.get("author")
    if len(isbn)==0:
        ans = queryOne("title",title) if len(author)==0 else queryOne("author", author) if len(title)==0 else queryTwo("title", title, "author", author)
    elif len(title)==0:
        ans = queryOne("isbn",isbn) if len(author)==0 else queryOne("author", author) if len(isbn)==0 else queryTwo("isbn", isbn, "author", author)
    elif len(author)==0:
        ans = queryOne("isbn",isbn) if len(title)==0 else queryOne("title", title) if len(isbn)==0 else queryTwo("isbn", isbn, "title", title)
    else:
        query = f"SELECT * FROM books WHERE isbn LIKE '%{isbn}%' AND title LIKE '%{title}%' AND author LIKE '%{author}%'"
        ans = db.session.execute(text(query)).fetchall()
    return render_template("search_result.html", ans=ans)

def queryOne(name, value):
    query = f"SELECT * FROM books WHERE {name} LIKE '%{value}%'"
    ans = db.session.execute(text(query)).fetchall()
    return ans

def queryTwo(n1, v1, n2, v2):
    query = f"SELECT * FROM books WHERE {n1} LIKE '%{v1}%' AND {n2} LIKE '%{v2}%'"
    ans = db.session.execute(text(query)).fetchall()
    return ans

@app.route("/details/<isbn>", methods=["GET", "POST"])
def details(isbn):
    if request.method == "POST":
        if session.get("username") is None:
            return redirect("/login")
        else:
            username = session.get("username")
            query = f"SELECT * FROM reviews WHERE isbn = {isbn} AND username = {username}"
            ans = db.session.execute(text(query)).fetchall()
            if ans == []:
                rating = request.form.get("rating")
                review = request.form.get("review")
                insert_query = f"""
                    INSERT INTO Reviews (rating, review)
                    VALUES ({rating}, '{review}')
                    RETURNING review_id
                """
                review_id = db.session.execute(text(insert_query)).fetchone()[0]

                insert_query_user_rating = f"""
                    INSERT INTO UserRating (review_id, user_id)
                    VALUES ({review_id}, (SELECT user_id FROM Users WHERE username = '{username}'))
                """
                db.session.execute(text(insert_query_user_rating))

                insert_query_book_rating = f"""
                    INSERT INTO BookRating (review_id, isbn)
                    VALUES ({review_id}, '{isbn}')
                """
                db.session.execute(text(insert_query_book_rating))

                db.session.commit()

        return redirect("/details/"+isbn)
    else:
        query = f"SELECT * FROM books WHERE isbn={isbn}"
        ans =db.session.execute(text(query)).fetchone()
        reviews_query = f"SELECT rating, review FROM Reviews JOIN Book_Rating ON Reviews.review_id = Book_Rating.review_id WHERE Book_Rating.isbn = {isbn}" 
        reviews = db.session.execute(text(reviews_query)).fetchall()
        return render_template("details.html", res=ans, reviews=reviews)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/api/<isbn>", methods=['GET'])
def api(isbn):
    # query = f
    row = db.execute("SELECT name, author, year, books.isbn, COUNT(reviews.id) as review_count, AVG(CAST(reviews.rating AS INTEGER)) as average_score FROM books INNER JOIN reviews ON books.isbn = reviews.isbn WHERE books.isbn = :isbn GROUP BY name, author, year, books.isbn", {"isbn": isbn})
    if row.rowcount != 1:
        return jsonify({"Error": "No Data for this isbn"}), 422
    tmp = row.fetchone()
    result = dict(tmp.items())
    result['average_score'] = float('%.1f'%(result['average_score']))
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)