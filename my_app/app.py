import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Config
basedir = os.path.abspath(os.path.dirname(__file__)) 
app.config["UPLOAD_FOLDER"] = os.path.join(basedir, "static/uploads")
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + basedir + "/database.db"
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif"}

app.config["SECRET_KEY"] = "AaBbCc"
app.config["DEBUG"] = True
FILESIZE = 2 * 1000 * 1000  # 2MB
time_format = "%Y-%m-%d %X"

# Build DB
db_file = os.path.join(basedir, "database.db")
db = SQLAlchemy()
db.init_app(app)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True)
    slug = db.Column(db.String(255), unique=True)
    user = db.relationship('Product', backref='prod_cat')

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    created = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())
    updated = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now(), onupdate=datetime.datetime.now())

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    photo = db.Column(db.String(255))
    price = db.Column(db.DECIMAL(10, 2))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())
    updated = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now(), onupdate=datetime.datetime.now())

def get_cats():
    cats = Category.query.with_entities(Category.id, Category.name).all()
    return cats

# Validation functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

def validate(data, file, img:bool):
    errors = []
    # Name
    if not data["name"]:
        errors.append("Name of product must not be empty!")
    elif len(data["name"]) > 255:
        errors.append("Name of product cannot be longer than 255 characters!")
    # Description
    if not data["desc"]:
        errors.append("Description must not be empty!")
    # Image
    if "image" not in file:
        errors.append("ERROR: File part not submitted")
    elif img and file["image"].filename == "":
        errors.append("No product image selected!")
    elif img:
        if not allowed_file(file["image"].filename):
            errors.append("Unsupported file type!")
        elif file["image"].content_length > FILESIZE:
            errors.append("File must not be bigger than 2MB!")
    # Price
    if not data["price"]:
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
    date = datetime.datetime.now()
    # Save uploaded image
    image.save(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))

    # Save data (database insert)
    product = Product(title = name, description = desc, photo = image.filename, price = price, category_id = cat, seller_id = 1, created=date, updated=date)
    db.session.add(product)
    db.session.commit()

def sql_replace(data, file, id:int, img:bool):
    # Generate data
    name = data["name"]
    desc = data["desc"]
    cat = data["cat"]
    image = file["image"]
    price = data["price"]
    date = datetime.datetime.now()
    
    # Update data
    product = Product.query.get(id)
    if product:
        if img:
            # Save uploaded image
            image = file["image"]
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
            product.title, product.description, product.photo, product.price, product.category_id, product.updated = name, desc, image.filename, price, cat, date
        else:
            product.title, product.description, product.price, product.category_id, product.updated = name, desc, price, cat, date
        db.session.commit()

# Main application
@app.route("/")
def init():
    return redirect(url_for("prod_list"))

@app.route("/products/list")
def prod_list():
    list = Product.query.with_entities(Product.id, Product.title, Product.photo, Product.price, Product.updated).order_by(Product.id.asc()).all()
    return render_template("prod_list.html", list = list)

@app.route("/products/read/<int:id>")
def prod_info(id):
    info = (
        db.session.query(Product.id, Product.title, Product.description, Product.photo, Product.price, Category.name.label("category"), User.name.label("user"), Product.created, Product.updated)
        .join(Category, Product.category_id == Category.id).join(User, Product.seller_id == User.id)
    ).filter(Product.id == id).first()
    return render_template("prod_info.html", info = info)

@app.route("/products/add", methods=["GET", "POST"])
def prod_add():
    if request.method == "GET":
        errors = []
        # Show form
        cats = get_cats()
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
        info = Product.query.get(id)
        cats = get_cats()
        return render_template("prod_edit.html", info = info, cats = cats)
    elif request.method == "POST":
        # Get POST data
        data = request.form
        file = request.files
        if file["image"].filename == "":
            img = False
        else:
            img = True
        # Validate data
        errors = validate(data, file, img)
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for("prod_edit", id = id))
        else:
            sql_replace(data, file, id, img)
            # Redirect to list page
            flash("Successfully updated listing!")
            return redirect(url_for("prod_list"))
    else:
        # Not found response
        abort(404)

@app.route("/products/delete/<int:id>", methods=["GET", "POST"])
def prod_delete(id:int):
    product = Product.query.get(id)
    if request.method == "GET":
        if product:
            return render_template("prod_delete.html", id = id, info = product)
        else:
            flash("The specified listing does not exist!")
            return redirect(url_for("prod_list"))
    elif request.method == "POST":
        if product:
            db.session.delete(product)
            db.session.commit()
            flash("Successfully removed listing!")
        else:
            flash("The specified listing does not exist!")
        return redirect(url_for("prod_list"))
    else:
        # Not found response
        abort(404)

if __name__ == '__main__':
    app.run()