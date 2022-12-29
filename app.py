from flask import Flask, render_template, request, redirect, session, flash, url_for, g
from flask_session import Session
from flask_mail import Mail, Message
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import jwt
import os
from datetime import datetime
from utils import login_required, brl, send_email, check_email, token_validity, percen, get_graphs, date_stamp, check_to_from
from db_operations import insert_data_transaction

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.filters["brl"] = brl
app.jinja_env.filters["percen"] = percen
app.jinja_env.filters["date_stamp"] = date_stamp


# Configure e-mail
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = "devmail.5237@gmail.com"
app.config["MAIL_PASSWORD"] = os.environ.get("EMAIL_PASS")
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_DEFAULT_SENDER"] = "devmail.5237@gmail.com"

mail = Mail(app)

# Ensure responses aren't cached
"""
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response
"""

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

TOKEN_KEY = os.environ.get("TOKEN_KEY")

DATABASE = f"{os.getcwd()}/minhasfinancas.db"
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = sqlite3.connect(DATABASE)
        g._database = db
    return db

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.commit()
        db.close()

@app.route("/", methods=["GET"])
@login_required
def index():
    payments_balance = get_payments_balance()
    graphs = get_statics()
    return render_template("index.html", payments=payments_balance, graphs=graphs)

def get_payments_balance():
    """
    There is four type payments/account methods
    0 - Wallet
    1 - Credit Card
    2 - Investiment
    3 - Debt
    """

    db = get_db()
    id_user = session["id_user"]
    query = """
    SELECT type, balance FROM payment_content AS p
    INNER JOIN users ON users.id=p.id_user
    WHERE users.id=?
    """
    user_methods = db.execute(query, (id_user, )).fetchall()
    payment_methods = get_dict_payments()
    if user_methods != None and user_methods != []:
        for type_method, balance in user_methods:
            payment_methods[type_method]["balance"] += balance
    
    query = """
    SELECT timestamp FROM transactions AS tr
    INNER JOIN payment_content AS p ON tr.id_from=p.id
    WHERE tr.id_user=? AND p.type=?
    ORDER BY timestamp
    LIMIT 1
    """
    for type_method in range(4):
        lastest_move = db.execute(query, (id_user, type_method)).fetchone()
        if lastest_move != [] and lastest_move != None:
            payment_methods[type_method]["lastest_move"] = datetime.fromtimestamp(lastest_move[0])

    return payment_methods

def get_dict_payments():
    titles = ["Carteira", "Cartão de Crédito", "Investimentos", "Dívidas"]
    payment_methods = []
    for title in titles:
        payment = {
            "title": title,
            "balance": 0,
            "lastest_move": 0
        }
        payment_methods.append(payment)
    return payment_methods

def get_statics():
    graphs_dict = get_graphs()
    db = get_db()
    id_user = session["id_user"]

    for title, graph in graphs_dict.copy().items():
        graphs_dict[title]["data"] = graphs_dict[title]["func"](db, id_user)
    
    return graphs_dict

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    if request.method == "POST":
        if not check_email(request.form.get("email")):
            return error_handler("Email inválido")
        
        if request.form.get("password") == "":
            return error_handler("Senha não pode ser nula")

        db = get_db()
        data = db.execute("SELECT id, password FROM users WHERE email=?", 
                            (request.form.get("email"), )).fetchone()
        if data == None or data == []:
            return error_handler("Usuário ou senha incorretos!")
        
        password = data[1]
        if not check_password_hash(password, request.form.get("password")):
            return error_handler("Usuário ou senha incorretos!")
        
        session["id_user"] = data[0]
        return redirect("/")
    
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# Registro - Token Type -> 0
# Recuperação de senha - Token Type -> 1

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
        if not check_email(request.form.get("email")):
            return error_handler("Email é inválido")

        if request.form.get("password") == "":
            return error_handler("Senha não pode ser nula")

        if request.form.get("password") != request.form.get("confirmation"):
            return error_handler("Senhas não conferem")
        
        db = get_db()
        hash = generate_password_hash(request.form.get("password"))
        try:
            token_id = db.execute("INSERT INTO tokens (type) VALUES (?)", (0, )).lastrowid
        except Exception as error:
            return error_handler(str(error))

        payload = {
            "id": token_id,
            "type": 0,
            "email": request.form.get("email"),
            "hash": str(hash),
            "timestamp": datetime.now().timestamp()
        }

        register_token = jwt.encode(payload, TOKEN_KEY, algorithm="HS256")
        content = render_template("mail_confirmation.html", token=register_token)
        status, error = send_email(mail, "Minhas Finanças: Confirmação de Conta", content, request.form.get("email"))
        if not status:
            return error_handler(error)

        return success_handler("Email enviado com sucesso")

@app.route("/register/confirmation", methods=["GET"])
def confirmation():
    token = request.args.get("token")
    if token == "":
        return error_handler("Link é inválido")
    
    db = get_db().cursor()

    try:
        token_data = jwt.decode(token, TOKEN_KEY, algorithms=["HS256",])
    except Exception as error:
        return error_handler(str(error))
    
    status, content = token_validity(db, token_data)
    if not status:
        return error_handler(content)
    
    try:
        db.execute("INSERT INTO users (email, password) VALUES (?, ?)", (token_data["email"], token_data["hash"]))
    except Exception as error:
        return error_handler(str(error))
    
    return success_handler("Conta criada com sucesso!")

@app.route("/transactions", methods=["GET"])
@login_required
def transactions():
    db = get_db()
    query = """
    SELECT 
    tr.name, tr.value, tr.timestamp, 
    CASE 
        WHEN yi.id_income != -1 THEN (SELECT inc.name FROM incomes AS inc WHERE inc.id=yi.id_income)
        WHEN yi.id_payment != -1 THEN (SELECT payment.name FROM payment_content AS payment WHERE payment.id=yi.id_payment)
    END,
    CASE
        WHEN pay.id_teller != -1 THEN (SELECT te.name FROM teller AS te WHERE te.id=pay.id_teller)
        WHEN pay.id_payment != -1 THEN (SELECT payment.name FROM payment_content AS payment WHERE payment.id=pay.id_payment)
    END
    FROM transactions AS tr
    INNER JOIN yield AS yi ON yi.id=tr.id_from
    INNER JOIN payer AS pay ON pay.id=tr.id_to
    WHERE tr.id_user=?
    ORDER BY tr.timestamp;
    """
    data = {
        "headers": ("Nome", "Valor", "Data", "Origem", "Destino")
    }
    query_result = db.execute(query, (session["id_user"], )).fetchall()
    if query_result == None or query_result == []:
        data["rows"] = ("-", "-", "-", "-", "-")
    else:
        data["rows"] = []
        for row in query_result:
            t = datetime.fromtimestamp(row[2])
            element = {
                "name" : row[0],
                "value" : row[1],
                "date" : datetime.fromtimestamp(row[2]),
                "origin" : row[3],
                "destination" : row[4]
            }
            data["rows"].append(element)

    return render_template("transactions.html", data=data)

@app.route("/creditcard", methods=["GET"])
@login_required
def creditcard():
    return render_template("credit_card.html")

@app.route("/debts", methods=["GET"])
@login_required
def debts():
    return render_template("debts.html")

@app.route("/investiments", methods=["GET"])
@login_required
def investiments():
    return render_template("investiments.html")

@app.route("/add/transaction", methods=["POST"])
@login_required
def add_transaction():
    # name, value, datetime, to, from, description

    if request.form.get("name") == "":
        return error_handler("O nome não pode estar vazio")

    if len(request.form.get("name")) > 25:
        return error_handler("Nome não pode ter mais de 25 caracteres")

    if request.form.get("value") == "":
        return error_handler("O valor não pode estar vazio")
    try:
        value = request.form.get("value").replace(",", ".")
        value = float(value)
    except ValueError:
        return error_handler("O valor deve ser um número real")
    except Exception as error:
        return error_handler(f"Um erro aconteceu {str(error)}")

    if request.form.get("datetime") == "":
        return error_handler("Uma data deve ser escolhida")
    
    if len(request.form.get("description")) > 100:
        return error_handler("Descrição não pode ter mais de 100 caracteres")

    db = get_db()
    check = check_to_from(db, request.form.get("to"), request.form.get("from"), session["id_user"])
    if check == None:
        return error_handler("Destino e/ou origem das transações são inválidos")
    
    timestamp = datetime.fromisoformat(request.form.get("datetime")).timestamp()
    data_insert = {
        "name" : request.form.get("name"),
        "value" : request.form.get("value"),
        "timestamp" : timestamp,
        "from" : request.form.get("from"),
        "from_payment" : check[0],
        "to" : request.form.get("to"),
        "to_payment" : check[1],
        "description" : request.form.get("description")
    }
    
    id_trans = insert_data_transaction(db, data_insert)

    return success_handler(f"Transação inserida: Id {id_trans}")
    

@app.route("/message", methods=["GET"])
def message():
    if 'msg' not in session:
        return render_template("message.html", status="none", type="Sem dados", content="Nenhuma mensagem"), 200

    msg = session["msg"].copy()
    session.pop("msg")
    return render_template("message.html", **msg), msg["code"]


def error_handler(error):
    payload = {
        "status": "error",
        "type": "Erro",
        "content": error,
        "code": 400
    }
    session['msg'] = payload
    return redirect(url_for("message"))

def success_handler(success):
    payload = {
        "status": "success",
        "type": "Sucesso",
        "content": success,
        "code" : 200
    }
    session['msg'] = payload
    return redirect(url_for("message"))