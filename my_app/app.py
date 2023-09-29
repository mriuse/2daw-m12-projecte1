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
        res = connect.execute("SELECT photo, title, seller_id, updated, price FROM products ORDER BY id ASC")
        list = res.fetchall();
    return render_template('prod_list.html', list = list)