import requests
from flask import Flask, session, render_template, request, redirect, jsonify, url_for
from flask_session import Session
from db_connection import db, app
from sqlalchemy import text
from flask import abort

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

def get_session_username():
	username = ""
	if session.get("username") is not None:
		username = session.get("username")
	return username

@app.route("/temp_home", methods=["GET", "POST"])
def home_page():
	username = get_session_username()
	is_active = request.args.get('is_active') == "True"
	query = f"SELECT TOP 10 * FROM books ORDER BY average_rating DESC;"
	get_top_10_books = db.session.execute(text(query))
	return render_template("home.html", ans=get_top_10_books, is_active=is_active, heading="Book List", name=username)

@app.route("/login", methods=["GET", "POST"])
def login_page():
	session.clear()

	if request.method == "POST":
		user_name = request.form.get("name")
		user_password = request.form.get("pwd")
		query = f"SELECT user_password FROM users WHERE username LIKE '%{user_name}%';"
		password = db.session.execute(text(query)).fetchone()
		if password is not None and user_password == password[0]:
			session["username"] = user_name
			return redirect(url_for('home_page', is_active=True))
		else:
			return(redirect(url_for('signup_page')))
	return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup_page():

	if request.method == "POST":
		user_name = request.form.get("name")
		user_password = request.form.get("pwd")
		if user_name and user_password:
			query = text("INSERT INTO users (username, user_password) VALUES (:username, :user_password);")
			db.session.execute(query,{"username": user_name, "user_password": user_password})
			db.session.commit()
			session["username"] = user_name
			return redirect(url_for('home_page', is_active=True))
	return render_template("signup.html")

def query_books(isbn, title, author, categories):
	if not isbn and not title and not author and not categories:
		return []
	conditions = []
	params = {}
	if isbn:
		conditions.append("books.isbn = :isbn")
		params["isbn"] = f"%{isbn}%"
	if title:
		conditions.append("title LIKE :title")
		params["title"] = f"%{title}%"
	if author:
		conditions.append("author LIKE :author")
		params["author"] = f"%{author}%"
	if categories:
		conditions.append("categories LIKE :categories")
		params["categories"] = f"%{categories}%"
	query = text("""
			  SELECT *
			  FROM books
			  WHERE isbn IN (
				SELECT DISTINCT books.isbn
				FROM books
				JOIN authors ON books.isbn = authors.isbn
				WHERE {});""".format(" AND ".join(conditions))
			)
	return db.session.execute(query, params).fetchall()

@app.route("/search", methods=["GET", "POST"])
def search_page():
	
	username = get_session_username()
	if request.method == "POST":
		isbn = request.form.get("isbn")
		title = request.form.get("name")
		author = request.form.get("author")
		categories = request.form.get("categories")
		ans = query_books(isbn, title, author, categories)
		return render_template("home.html", ans=ans, heading="Search Results")
	
	query = f"SELECT TOP 5 categories, count(*) as categories_count FROM books GROUP BY categories ORDER BY categories_count DESC"
	top_5_categories = db.session.execute(text(query))
	return render_template("search.html", top_5_categories=top_5_categories, name=username)


def get_reviews_query(isbn):
	query=text("""
			SELECT rating, review, username, reviews.review_id, User_Rating.user_id
			FROM Reviews 
			JOIN Book_Rating ON Reviews.review_id = Book_Rating.review_id 
			JOIN User_Rating ON Reviews.review_id = User_Rating.review_id 
			JOIN Users ON User_Rating.user_id = Users.user_id
			WHERE isbn = :isbn;
		""")
	result = db.session.execute(query, {"isbn": isbn}).fetchall()
	return result

@app.route("/details/<isbn>", methods=["GET", "POST"])
def details(isbn):
	is_active = request.args.get('is_active') == "True"
	username = get_session_username() or None
	user_id = None

	query = f"SELECT * FROM books WHERE isbn={isbn}"
	ans = db.session.execute(text(query)).fetchone()

	if username:
		user_id_query = f"SELECT user_id from Users where username LIKE '%{username}%'"
		user_id = db.session.execute(text(user_id_query)).fetchone()[0]

	reviews = get_reviews_query(isbn)
	if request.method == "POST":
		query = f"SELECT rating, review FROM Reviews JOIN Book_Rating ON Reviews.review_id = Book_Rating.review_id JOIN User_Rating ON Reviews.review_id = User_Rating.review_id WHERE user_id = {user_id} AND isbn = {isbn}"
		result = db.session.execute(text(query)).fetchall()
		if not result:
			rating = request.form.get("rating")
			review = request.form.get("content")
			insert_query = f"""
				INSERT INTO Reviews (rating, review)
				VALUES ({rating}, '{review}')
			"""
			db.session.execute(text(insert_query))
			db.session.commit()

			get_review_id_query = f"SELECT TOP 1 review_id FROM Reviews ORDER BY review_id DESC"
			review_id = db.session.execute(text(get_review_id_query)).fetchone()[0]

			insert_query_user_rating = f"""
				INSERT INTO User_Rating (review_id, user_id)
				VALUES ({review_id}, {user_id})
			"""
			db.session.execute(text(insert_query_user_rating))
			db.session.commit()

			insert_query_book_rating = f"""
				INSERT INTO Book_Rating (review_id, isbn)
				VALUES ({review_id}, '{isbn}')
			"""
			db.session.execute(text(insert_query_book_rating))
			db.session.commit()
		
		#return render_template("details.html", res=ans, reviews=reviews, is_active=is_active)
		return redirect(url_for('details', isbn=isbn, name=username, is_active=is_active, uid=user_id))

	return render_template("details.html", res=ans, reviews=reviews, name=username, is_active=is_active, uid=user_id)
	
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

@app.route('/delete/<review_id>', methods=['GET', 'POST'])
def delete(review_id):
	isbn=request.args.get("isbn")
	is_active = request.args.get('is_active') == "True"
	query=f"DELETE FROM reviews where review_id={review_id};"
	db.session.execute(text(query))
	db.session.commit()
	return redirect(url_for('details', isbn=isbn, is_active=is_active))


@app.route('/update/<review_id>', methods=['GET', 'POST'])
def update(review_id):
    return

if __name__ == "__main__":
	app.run(debug=True)
