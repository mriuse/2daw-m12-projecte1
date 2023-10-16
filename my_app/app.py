import os, sqlite3, datetime
from flask import Flask, render_template, request, redirect, url_for, flash, abort

app = Flask(__name__)

# Config
app.config["UPLOAD_FOLDER"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "static/uploads"))
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["MAX_CONTENT_LENGTH"] = 2 * 1000 * 1000 #2MB
app.config['SECRET_KEY'] = "AaBbCc"
DATABASE = "database.db"

# Database functions
def connect_db():
    db_path = DATABASE
    connect = sqlite3.connect(db_path)
    connect.row_factory = sqlite3.Row;
    return connect

def get_categories():
    with connect_db() as connect:
        query = connect.execute("SELECT id, name FROM categories")
        cats = query.fetchall()
    return cats


# Validation functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate(data, file, img:bool):
    errors = []
    # Name
    if data["name"] == "":
        errors.append("Name of product must not be empty!")
    elif len(data["name"]) > 255:
        errors.append("Name of product cannot be longer than 255 characters!")
    # Description
    if data["desc"] == "":
        errors.append("Description must not be empty!")
    # Image
    if "image" not in file:
        errors.append("ERROR: File part not submitted")
    elif img == True and file["image"].filename == "":
        errors.append("No product image selected!")
    elif img == True and not allowed_file(file["image"].filename):
        errors.append("Unsupported file type!")
    elif img == True and file["image"].content_length > app.config['MAX_CONTENT_LENGTH']:
        errors.append("File must not be bigger than 2MB!")
    # Price
    if data["price"] == "":
        errors.append("Price must not be empty!")
    return errors

# SQL operation functions
def sql_insert(data, file):
    # Generate data
    name = data["name"]
    desc = data["desc"]
    cat = data["cat"]
    image = file["image"]
    price = data["price"]
    date = datetime.datetime.now().strftime("%Y-%m-%d %X")
    image.save(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
    # Save data (database insert)
    with connect_db() as connect:
        connect.execute("INSERT INTO products (title, description, photo, price, category_id, seller_id, created, updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (name, desc, image.filename, price, cat, 1, date, date))
        connect.commit()

def sql_replace(data, file, id:int, img:bool):
    # Generate data
    name = data["name"]
    desc = data["desc"]
    cat = data["cat"]
    image = file["image"]
    price = data["price"]
    date = datetime.datetime.now().strftime("%Y-%m-%d %X")
    with connect_db() as connect:
        if img:
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
            connect.execute("UPDATE products SET title = ?, description = ?, photo = ?, price = ?, category_id = ?, updated = ? WHERE p.id ="+str(id), (name, desc, image.filename, price, cat, date))
        else:
            connect.execute("UPDATE products SET title = ?, description = ?, price = ?, category_id = ?, updated = ? WHERE id ="+str(id), (name, desc, price, cat, date))
        connect.commit()
    
# Main application
@app.route("/")
def init():
    return redirect(url_for("prod_list"))

@app.route("/products/list")
def prod_list():
    with connect_db() as connect:
        query = connect.execute("SELECT id, title, photo, price, updated FROM products ORDER BY id ASC")
        list = query.fetchall()
    return render_template("prod_list.html", list = list)

@app.route("/products/read/<int:id>")
def prod_info(id):
    with connect_db() as connect:
        query = connect.execute("SELECT p.id, p.title, p.description, p.photo, p.price, c.name as category, u.name as seller, p.created, p.updated FROM products p INNER JOIN categories c ON p.category_id = c.id INNER JOIN users u ON p.seller_id = u.id WHERE p.id = "+str(id))
        info = query.fetchone()
    return render_template("prod_info.html", info = info)

@app.route("/products/add", methods=["GET", "POST"])
def prod_add():
    if request.method == "GET":
        errors = []
        # Show form
        cats = get_categories()
        return render_template("prod_add.html", cats = cats)
    elif request.method == "POST":
        # Get POST data
        data = request.form
        file = request.files
        img = True
        # TODO Validate data
        errors = validate(data, file, img)
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for("prod_add"))
        else:
            sql_insert(data, file)
            # Redirect to list page
            flash("Successfully added new listing!")
            return redirect(url_for("prod_list"))
    else:
        # Not found response
        abort(404)

@app.route("/products/edit/<int:id>", methods=["GET", "POST"])
def prod_edit(id:int):
    if request.method == "GET":
        errors = []
        # Show form
        with connect_db() as connect:
            query = connect.execute("SELECT * FROM products WHERE id = "+str(id))
            info = query.fetchone()
        cats = get_categories()
        return render_template("prod_edit.html", info = info, cats = cats)
    elif request.method == "POST":
        # Get POST data
        data = request.form
        file = request.files
        if file["image"].filename == "":
            img = False
        else:
            img = True
        # TODO Validate data
        errors = validate(data, file, img)
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for("prod_edit"))
        else:
            sql_replace(data, file, id, img)
            # Redirect to list page
            flash("Successfully updated listing!")
            return redirect(url_for("prod_list"))
    else:
        # Not found response
        abort(404)
if __name__ == '__main__':
    app.run()