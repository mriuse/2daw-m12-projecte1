import sqlite3
from flask import Flask, render_template, g

app = Flask(__name__)
DATABASE = "database.db" 

@app.route("/")
def index():
    return render_template("index.html")