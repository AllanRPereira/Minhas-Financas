from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from flask_mail import Mail, Message
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import jwt
from datetime import datetime
from utils import login_required, brl

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.filters["brl"] = brl


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

connection = sqlite3.connect("minhasfinancas.db")
db = connection.cursor()

@app.route("/", methods=["GET"])
@login_required
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    if request.method == "POST":
        return "TODO"

# Registro - Token Type -> 0
# Recuperação de senha - Token Type -> 1

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
        if not check_email(request.form.get("email")):
            return "E-mail inválido"

        if request.form.get("password") == "":
            return "Senha inválida"
        
        if request.form.get("password") != request.form.get("confirmation"):
            return "Senhas não conferem"
        
        hash = generate_password_hash(request.form.get("password"))
        token_id = db.execute("INSERT INTO tokens (type) VALUES (?)", 0)
        payload = {
            "token_id": token_id,
            "email": request.form.get("email"),
            "hash": hash,
            "timestamp": datetime.now().timestamp()
        }
        


@app.route("/testHome", methods=["GET"])
def testHome():
    return render_template("index.html")

