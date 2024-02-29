import requests
from flask import Flask, session, render_template, request, redirect, jsonify
from flask_session import Session
from db_connection import db, app
from sqlalchemy import text

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# # Set up database
# engine = create_engine(os.getenv("DATABASE_URL"))
# db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
	if session.get("username") is not None:
		return render_template("home.html", name=session.get("username"))
	return render_template("login.html")

@app.route("/home", methods=["POST"])
def home():
	session.clear()
	name = request.form.get("name")
	dbpwd = db.execute("SELECT user_password FROM users WHERE username = :username", {"username": name}).fetchone()
	if dbpwd != None:
		pwd = request.form.get("pwd")
		if pwd == dbpwd[0]:
			session["username"] = name
			return render_template("home.html", name=name)
	else:
		return redirect("/signup")
	return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
	session.clear()
	name = request.form.get("name")
	pwd = request.form.get("pwd")
	db.session.execute(text("INSERT INTO users (username, user_password) VALUES (:username, :password);"),{"username": name, "password": pwd})
	
	db.session.commit()
	
	session["username"] = name
	return render_template("home.html", name=name)

@app.route("/signup")
def signup():
	if session.get("username") is not None:
		return render_template("home.html", name=session.get("username"))
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

@app.route("/details/<isbn>")
def details(isbn):
	query = f"SELECT * FROM books WHERE isbn={isbn}"
	ans =db.session.execute(text(query)).fetchone()
	response = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": 'JkwcGThDCN97xqvW7Stg', "isbns": isbn})
	sna = response.json()
	if response.status_code != 200:
		raise Exception("ERROR: API request unsuccessful.")
	reviews_query = f"SELECT rating, review, username FROM reviews WHERE isbn = {isbn}"
	reviews = db.session.execute(text(reviews_query)).fetchall()
	return render_template("details.html", res=ans, avg=sna['books'][0]['average_rating'], rating=sna['books'][0]['average_rating'], total=sna['books'][0]['ratings_count'], reviews=reviews)

@app.route("/logout")
def logout():
	session.clear()
	return redirect("/")

@app.route("/review/<isbn>", methods=["POST"])
def review(isbn):
	username = session.get("username")
	query = f"SELECT * FROM reviews WHERE isbn = {isbn} AND username = {username}"
	ans = db.session.execute(text(query)).fetchall()
	if ans == []:
		rating = request.form.get("rating")
		content = request.form.get("content")
		insert_query = f"INSERT INTO reviews (rating, content, username, isbn) VALUES ({rating}, {content}, {username}, {isbn})"
		db.session.execute()
		db.session.commit()
	return redirect("/details/"+isbn)

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
