from flask import Flask, render_template, request, redirect, session, flash, url_for, g
from flask_session import Session
from flask_mail import Mail, Message
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import jwt
import os
from datetime import datetime
from utils import login_required, brl, send_email, check_email, token_validity, percen, get_graphs, date_stamp, check_to_from
from db_operations import insert_data_transaction, get_data_payment, get_to_options, get_from_options, get_payment_options, get_categorys, add_category, add_income, add_teller, add_payment, get_ids_payment_type

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

WALLET = 0
CREDIT_CARD = 1
INVESTMENTS = 2
DEBTS = 3

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
    options = get_options()

    return render_template("main/index.html",payments=payments_balance, graphs=graphs, **options)

@app.route("/get_options", methods=["GET"])
@login_required
def get_options():
    db = get_db()

    payment_options = get_payment_options(db)
    to_options = get_to_options(db)
    to_options.extend(payment_options)
    to_options = sorted(to_options)

    from_options = get_from_options(db)
    from_options.extend(payment_options)
    from_options = sorted(from_options)

    categorys = get_categorys(db)

    data = {
        "to_options" : to_options,
        "from_options" : from_options,
        "income_category" : categorys["income"],
        "teller_category" : categorys["teller"]
    }

    return data

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
    SELECT type, SUM(balance) FROM payment_content AS p
    WHERE p.id_user=?
    GROUP BY type
    """
    user_methods = db.execute(query, (id_user, )).fetchall()
    payment_methods = get_dict_payments()
    if user_methods != None and user_methods != []:
        for type_method, balance in user_methods:
            payment_methods[type_method]["balance"] = balance
    
    query = """
    SELECT MAX(tr.timestamp) FROM payment_content AS pay
    INNER JOIN payer AS py ON py.id_payment=pay.id
    INNER JOIN transactions AS tr ON py.id=tr.id_to
    WHERE tr.id_user=? AND pay.type=?
    UNION
    SELECT MAX(tr.timestamp) FROM payment_content AS pay
    INNER JOIN yield AS y ON y.id_payment=pay.id
    INNER JOIN transactions AS tr ON y.id=tr.id_from
    WHERE tr.id_user=? AND pay.type=?
    ORDER BY MAX(tr.timestamp) DESC
    LIMIT 1
    """
    for type_method in range(4):
        lastest_move = db.execute(query, (id_user, type_method, id_user, type_method)).fetchone()
        if lastest_move != []:
            if lastest_move[0] != None:
                payment_methods[type_method]["lastest_move"] = datetime.fromtimestamp(lastest_move[0])

    return payment_methods

def get_dict_payments():
    titles = ["Carteira", "Cartão de Crédito", "Investimentos", "Dívidas"]
    payment_methods = []
    for title in titles:
        payment = {
            "title": title,
            "balance": 0,
            "lastest_move": 0,
            "id" : "/"
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
        return render_template("main/login.html")
    
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
        return render_template("main/register.html")
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
            "email": request.form.get("email").lower(),
            "hash": str(hash),
            "timestamp": datetime.now().timestamp()
        }

        register_token = jwt.encode(payload, TOKEN_KEY, algorithm="HS256")
        content = render_template("mail/mail_confirmation.html", token=register_token)
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
        id_user = db.execute("INSERT INTO users (email, password) VALUES (?, ?)", (token_data["email"], token_data["hash"])).lastrowid
        names = ("Carteira", "Cartão de Crédito", "Investimentos", "Dívidas")
        for i in range(4): # Four payment methods
            db.execute("INSERT INTO payment_content (id_user, type, name) VALUES (?,?,?)",
                        (id_user, i, names[i]))
    except Exception as error:
        return error_handler(str(error))
    
    return success_handler("Conta criada com sucesso!")

@app.route("/recovery", methods=["GET", "POST"])
def recovery():
    db = get_db()

    if request.method == "GET":
        if request.args.get("token") == None:
            return render_template("main/recovery.html", recovery=True)
        else:
            return render_template("main/recovery.html", recovery=False, token=request.args.get("token"))

    if request.method == "POST":
        email = request.form.get("email").lower()
        if not check_email(email):
            return error_handler("Email inválido!")
        
        query = "SELECT id FROM users WHERE email=?"
        result = db.execute(query, (email, )).fetchone()
        if result != None and result != []:
            id_user = result[0]
            id_token = db.execute("INSERT INTO tokens (id_user, type) VALUES (?, ?)", (id_user, 1)).lastrowid
            payload = {
                "id" : id_token,
                "id_user" : id_user,
                "type" : 1,
                "timestamp": round(datetime.now().timestamp(), 2)
            }
            recover_token = jwt.encode(payload, TOKEN_KEY, algorithm="HS256")
            content = render_template("mail/mail_recovery.html", token=recover_token)
            status, response = send_email(mail, "Minhas Finanças: Recuperação de senha", content, email)
            if not status:
                return error_handler(response)

        return success_handler("Email enviado com sucesso!")

@app.route("/recovery/set", methods=["POST"])
def recovery_set():
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")
    token = request.form.get("token")
    try:
        token_data = jwt.decode(token, TOKEN_KEY, algorithms=["HS256"])
    except Exception as error:
        return error_handler("Token não é válido!")

    if password == "" or password == None:
        return error_handler("Campo de senha deve ser preenchido corretamente")
    if password != confirmation:
        return error_handler("Campos de senha não são iguais!")

    db = get_db()
    status, content = token_validity(db, token_data)
    if not status:
        return error_handler(content)
    hash = generate_password_hash(password)
    query = "UPDATE users SET password=? WHERE id=?"
    db.execute(query, (hash, token_data["id_user"]))

    return success_handler("Senha alterada com sucesso!")

@app.route("/transactions", methods=["GET"])
@login_required
def transactions(filter=""):
    db = get_db()
    query = f"""
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
    WHERE tr.id_user=? {filter}
    ORDER BY tr.timestamp;
    """
    data = {
        "headers": ("Nome", "Valor", "Data", "Origem", "Destino")
    }
    query_result = db.execute(query, (session["id_user"], )).fetchall()
    print(query_result)
    if query_result == [None, ]:
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

    return render_template("main/transactions.html", data=data)


@app.route("/transactions/<string:type_pay>/<int:id>", methods=["GET"])
@login_required
def filter_transactions(type_pay, id):
    dict_operator = {
        "creditcard" : CREDIT_CARD,
        "investment" : INVESTMENTS,
        "debt" : DEBTS
    }
    if type_pay in dict_operator:
        db = get_db()
        ids = get_ids_payment_type(db, dict_operator[type_pay])
        if id >= len(ids):
            return error_handler("Opção Inválida!")
        id_pay = ids[id][0]
        filter_query = f"""
        AND ( (pay.id_payment != -1 OR yi.id_payment != -1) AND (pay.id_payment={id_pay} OR yi.id_payment={id_pay}) )
        """
        return transactions(filter=filter_query)
    
    return error_handler("URL inválida!")

@app.route("/creditcard", methods=["GET"])
@login_required
def creditcard():
    db = get_db()
    creditcard = get_data_payment(db, CREDIT_CARD)
    options = get_options()
    return render_template("main/credit_card.html", cards=creditcard, **options)

@app.route("/add/creditcard", methods=["POST"])
@login_required
def add_credit_card():
    name = request.form.get("name")
    due_date = request.form.get("due_date")
    initial_bill = request.form.get("initial_bill").upper().replace("R$", "").replace(",", ".").replace(" ", "")
    status, content = check_name(name)
    if not status:
        return content
    try:
        initial_bill = float(initial_bill)
    except ValueError:
        return ("A fatura inicial deve ser um número", 400)
    
    try:
        due_date = datetime.fromisoformat(due_date).timestamp()
    except Exception as error:
        return ("Campo de data não é valido "+ str(error), 400)
    
    
    db = get_db()
    return add_payment(db, name, initial_bill, CREDIT_CARD)

@app.route("/debts", methods=["GET"])
@login_required
def debts():
    db = get_db()
    debts = get_data_payment(db, DEBTS)
    options = get_options()
    return render_template("main/debts.html", debts=debts, **options)

@app.route("/add/debt", methods=["POST"])
@login_required
def add_debt():
    name = request.form.get("name")
    date_debt = request.form.get("debt_date")
    current_amount = request.form.get("debt_value").upper().replace("R$", "").replace(",", ".").replace(" ", "")
    status, content = check_name(name)
    if not status:
        return content

    if len(name) > 25:
        return ("Nome deve ter menos de 25 letras", 400)
    try:
        current_amount = float(current_amount)
    except ValueError:
        return ("Rendimento deve ser número", 400)
    
    try:
        date_debt = datetime.fromisoformat(date_debt).timestamp()
    except Exception as error:
        return ("Campo de data não é valido "+ str(error), 400)
    
    
    db = get_db()
    return add_payment(db, name, current_amount, DEBTS)


@app.route("/investiments", methods=["GET"])
@login_required
def investiments():
    db = get_db()
    investments = get_data_payment(db, INVESTMENTS)
    options = get_options()
    return render_template("main/investiments.html", investments=investments, **options)

@app.route("/add/investiment", methods=["POST"])
@login_required
def add_investiment():
    name = request.form.get("name")
    rendiment = request.form.get("rendiment").replace("%", "").replace(",", ".")
    current_amount = request.form.get("current_amount").upper().replace("R$", "").replace(",", ".")
    status, content = check_name(name)
    if not status:
        return content

    try:
        rendiment = float(rendiment)
        current_amount = float(current_amount)
    except ValueError:
        return ("Rendimento e quantidade devem ser número", 400)
    
    db = get_db()
    return add_payment(db, name, current_amount, INVESTMENTS)

@app.route("/add/transaction", methods=["POST"])
@login_required
def add_transaction():
    status, content = check_name(request.form.get("name"))
    if not status:
        return content

    if request.form.get("value") == "":
        return ("O valor não pode estar vazio", 400)
    try:
        value = request.form.get("value").replace(",", ".")
        value = abs(float(value))
    except ValueError:
        return ("O valor deve ser um número real", 400)
    except Exception as error:
        return (f"Um erro aconteceu {str(error)}", 400)

    if request.form.get("datetime") == "":
        return ("Uma data deve ser escolhida", 400)
    
    if len(request.form.get("description")) > 100:
        return ("Descrição não pode ter mais de 100 caracteres", 400)

    db = get_db()
    check = check_to_from(db, request.form.get("to"), request.form.get("from"), session["id_user"])
    if check == None:
        return ("Destino e/ou origem das transações são inválidos", 400)
    
    timestamp = datetime.fromisoformat(request.form.get("datetime")).timestamp()
    data_insert = {
        "name" : request.form.get("name").lower(),
        "value" : value,
        "timestamp" : timestamp,
        "from" : request.form.get("from").lower(),
        "from_payment" : check[0],
        "to" : request.form.get("to").lower(),
        "to_payment" : check[1],
        "description" : request.form.get("description")
    }
    
    id_trans = insert_data_transaction(db, data_insert)

    return (f"Transação inserida com sucesso", 200)

def check_name(name):
    if name == None or name == "":
        return ("Nome não pode ser nulo", 400)
    if len(name) > 25:
        return ("Nome deve ter menos de 25 letras", 400)
    return (True, "")

@app.route("/add/to", methods=["POST"])
@login_required
def add_to():
    status, content = check_add_to_from()
    if status == False:
        return content, 400
    else:
        db = get_db()
        if request.form.get("category") != "":
            return add_teller(db, request.form.get("name"), request.form.get("category"))
        else:
            add_category(db, request.form.get("new_category"))
            return add_teller(db, request.form.get("name"), request.form.get("new_category"))

@app.route("/add/from", methods=["POST"])
@login_required
def add_from():
    status, content = check_add_to_from()
    if status == False:
        return content, 400
    else:
        db = get_db()
        if request.form.get("category") != "":
            return add_income(db, request.form.get("name"), request.form.get("category"))
        else:
            add_category(db, request.form.get("new_category"))
            return add_income(db, request.form.get("name"), request.form.get("new_category"))


def check_add_to_from():
    name = request.form.get("name")
    category = request.form.get("category")
    new_category = request.form.get("new_category")
    if name == "" or name == None:
        return (False, "Nome não pode estar vazio")

    cond_one = category == "" or category == None
    cond_two = new_category == "" or new_category == None
    if cond_one and cond_two:
        return (False, "Categoria deve ser escolhida")
    
    if not cond_one:
        if len(category) > 25:
            return (False, "Categoria deve ter menos de 25 letras")
    else:
        if len(new_category) > 25:
            return (False, "Nova categoria deve ter menos de 25 letras")

    return (True, "")

@app.route("/message", methods=["GET"])
def message():
    if 'msg' not in session:
        return render_template("main/message_page.html", status="none", type="Sem dados", content="Nenhuma mensagem"), 200

    msg = session["msg"].copy()
    session.pop("msg")
    return render_template("main/message_page.html", **msg), msg["code"]

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

def internal_error(error):
    if not isinstance(error, HTTPException):
        error = InternalServerError()
    return error_handler(f"Algo deu errado:{error.code} / {error.name}")


for code in default_exceptions:
    app.errorhandler(code)(internal_error)