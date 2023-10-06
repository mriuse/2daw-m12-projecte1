import sqlite3
from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

DATABASE = "database.db"

def connect_db():
    db_path = DATABASE
    connect = sqlite3.connect(db_path)
    connect.row_factory = sqlite3.Row;
    return connect

@app.route("/")
def init():
    return redirect(url_for("prod_list"))

@app.route("/products/list")
def prod_list():
    with connect_db() as connect:
        query = connect.execute("SELECT id, title, photo, price, updated FROM products ORDER BY id ASC")
        list = query.fetchall();
    return render_template('prod_list.html', list = list)

@app.route("/products/read/<int:id>")
def prod_info(id):
    with connect_db() as connect:
        query = connect.execute("SELECT title, description, photo, price, category_id, seller_id, created, updated FROM products WHERE id = "+str(id))
        info = query.fetchone()
    return render_template('prod_info.html', info = info)