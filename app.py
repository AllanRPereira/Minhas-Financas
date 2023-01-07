from flask import Flask, render_template, request, redirect, session, flash, url_for, g
from flask_session import Session
from flask_mail import Mail, Message
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from time import time
from datetime import datetime
from utils import *
from model.database import *
from routes.credit_cards.credit_cards import credit_page
from routes.debts.debts import debt_page
from routes.investments.investments import invest_page
from consts import CREDIT_CARD, WALLET, INVESTMENTS, DEBTS, ALL_PAYMENTS
import sqlite3
import jwt
import os
import logging as log

app = Flask(__name__)
app.register_blueprint(credit_page)
app.register_blueprint(debt_page)
app.register_blueprint(invest_page)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.filters["brl"] = brl
app.jinja_env.filters["percen"] = percen
app.jinja_env.filters["date_stamp"] = date_stamp
functions = {
    "min_year" : min_year,
    "max_year" : max_year
}
app.jinja_env.globals.update(functions)


# Configure e-mail
if os.environ.get("EMAIL_PASS") is None:
    raise Exception("Senha do acesso ao email não foi definida!")

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = "devmail.5237@gmail.com"
app.config["MAIL_PASSWORD"] = os.environ.get("EMAIL_PASS")
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_DEFAULT_SENDER"] = "devmail.5237@gmail.com"

mail = Mail(app)

# Configurações da sessão
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configuração da chave de codificação dos tokens
TOKEN_KEY = os.environ.get("TOKEN_KEY")
if TOKEN_KEY is None:
    raise Exception("Chave de codificação dos tokens não foi definida!!")

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.commit()
        db.close()

@app.route("/", methods=["GET"])
@login_required
def index():
    """
    Homepage da aplicação, onde há os saldos e as estatísticas
    """

    db = get_db()
    payments_balance = get_payments_balance(db)
    graphs = get_statics(db)
    return render_template("main/index.html",payments=payments_balance, graphs=graphs)

@app.route("/js/options", methods=["GET"])
@login_required
def options():
    """
    Rota utilizada pelo layout.js para atualizar dinamicamente os Incomes e os
    Tellers disponíveis no momento de adicionar uma transação.
    """

    db = get_db()
    return get_options(db)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("main/login.html")
    
    if request.method == "POST":
        if not check_email(request.form.get("email", "")):
            return error_handler("Email inválido")
        
        if request.form.get("password", "") == "":
            return error_handler("Senha não pode ser nula")

        db = get_db()
        data = get_user_pass_by_email(db, request.form.get("email"))
        for id, hash in data:
            if check_password_hash(hash, request.form.get("password")):
                session["id_user"] = id
                return redirect("/")
        else:
            return error_handler("Usuário/Senha Inválidos")
        

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Página de registro da aplicação
    Importante:
        Token Type do registro é o código 0
    """

    if request.method == "GET":
        return render_template("main/register.html")
    if request.method == "POST":
        if not check_email(request.form.get("email", "")):
            return error_handler("Email é inválido")

        if request.form.get("password", "") == "":
            return error_handler("Senha não pode ser nula")

        if request.form.get("password") != request.form.get("confirmation", ""):
            return error_handler("Senhas não conferem")
        
        db = get_db()
        hash = generate_password_hash(request.form.get("password"))
        try:
            token_id = add_token(db, 0)
        except Exception as error:
            return error_handler(str(error))

        payload = {
            "id": token_id,
            "type": 0,
            "email": request.form.get("email").lower(),
            "hash": hash,
            "timestamp": datetime.now().timestamp() # Checar tempo de vida do token
        }

        register_token = jwt.encode(payload, TOKEN_KEY, algorithm="HS256")
        content = render_template("mail/mail_confirmation.html", token=register_token)
        status, error = send_email(mail, "Minhas Finanças: Confirmação de Conta", content, request.form.get("email"))
        if not status:
            return error_handler(error)

        return success_handler("Email enviado com sucesso")

@app.route("/register/confirmation", methods=["GET"])
def confirmation():
    """
    Rota que confirma a o cadastro por meio do link enviado por e-mail
    """

    token = request.args.get("token", "")
    if token == "":
        return error_handler("Link é inválido")
    
    db = get_db()

    try:
        token_data = jwt.decode(token, TOKEN_KEY, algorithms=["HS256",])
    except Exception as error:
        return error_handler(str(error))
    
    status, content = token_validity(db, token_data)
    if not status:
        return error_handler(content)
    
    db = get_db()
    id_user = add_user(db, token_data["email"], token_data["hash"])

    # Adiciona os meios base de pagamento
    names = ("carteira", "cartão de crédito", "investimentos", "dívidas")
    for i in range(4):
        add_payment(db, names[i], 0, i, id_user)

    delete_token(db, token_data["id"])

    return success_handler("Conta criada com sucesso!")

@app.route("/recovery", methods=["GET", "POST"])
def recovery():
    """
    Rota para a recuperação de senha
    Importante:
        Token type para recovery é 1
    """

    if request.method == "GET":
        if request.args.get("token", "") == "":
            return render_template("main/recovery.html", recovery=True)
        else:
            return render_template("main/recovery.html", recovery=False, token=request.args.get("token"))

    if request.method == "POST":
        email = request.form.get("email", "").lower()
        if not check_email(email):
            return error_handler("Email inválido!")
        
        db = get_db()
        id_user = get_user_pass_by_email(db, email, password=False)
        if id_user == []:
            return error_handler("Usuário não encontrado!")

        id_user = id_user[0][0]
        id_token = add_token(db, 1, id_user=id_user)
        payload = {
            "id" : id_token,
            "id_user" : id_user,
            "type" : 1,
            "timestamp": datetime.now().timestamp()
        }
        recover_token = jwt.encode(payload, TOKEN_KEY, algorithm="HS256")
        content = render_template("mail/mail_recovery.html", token=recover_token)
        status, response = send_email(mail, "Minhas Finanças: Recuperação de senha", content, email)
        if not status:
            return error_handler(response)

        return success_handler("Email enviado com sucesso!")

@app.route("/recovery/set", methods=["POST"])
def recovery_set():
    """
    Rota que efetivamente faz a mudança da senha no banco de dados
    verificando se os dados fornecidos são válidos.
    """

    password = request.form.get("password", "")
    confirmation = request.form.get("confirmation", "")
    token = request.form.get("token")
    try:
        token_data = jwt.decode(token, TOKEN_KEY, algorithms=["HS256"])
    except Exception as error:
        return error_handler("Token não é válido!")

    if password == "":
        return error_handler("Campo de senha deve ser preenchido corretamente")
    if password != confirmation:
        return error_handler("Campos de senha não são iguais!")

    db = get_db()
    status, content = token_validity(db, token_data)
    if not status:
        return error_handler(content)
    hash = generate_password_hash(password)
    result = set_user_information(db, token_data["id_user"], password=hash)
    if not result:
        return success_handler("Senha alterada com sucesso!")
    else:
        return error_handler("Há falta de dados para a redefinição")

@app.route("/transactions", methods=["GET"])
@login_required
def transactions():
    # Obtém todas as transações de um usuário
    return redirect("/transactions/all/0")

@app.route("/transactions/<string:type_pay>/<int:id>", methods=["GET", "POST"])
@login_required
def filter_transactions(type_pay, id):
    """
    Obtém as transações por meio de um filtro que são:
        type_pay -> Método de pagamento, Cartão, Investimento ou Dívida
        id -> Índice do meio de pagamento dentro os possíveis de um usuário
        Obs.: Id não é o na tabela, é relativo ao usuário.
    """
    extra_filter = ""

    if request.method == "POST":
        if request.form.get("type_filter") == "year_month":
            year, month = request.form.get("data_filter").split("-")
            if not year.isdigit() or not month.isdigit():
                return error_handler("Data inválida!")
            year, month = int(year), int(month)
            timestamp_min = datetime(year=year, month=month, day=1).timestamp()

            if month == 12:
                year += 1
                month = 1
            else:
                month += 1

            timestamp_max = datetime(year=year, month=month, day=1).timestamp()

        elif request.form.get("type_filter") == "year":
            year = request.form.get("data_filter")
            if not year.isdigit():
                return error_handler("Data inválida!")
            year = int(year)
            if year > max_year() or year < min_year():
                return error_handler("Ano selecionado é inválido!")
            timestamp_min = datetime(year=year, month=1, day=1).timestamp()
            timestamp_max = datetime(year=year+1, month=1, day=1).timestamp()

        else:
            return error_handler("Opção inválida para filtragem")

        extra_filter = f"""
        AND tr.timestamp >= {timestamp_min}
        AND tr.timestamp <= {timestamp_max}
        """

    dict_operator = {
        "creditcard" : CREDIT_CARD,
        "investment" : INVESTMENTS,
        "debt" : DEBTS,
    }
    if type_pay in dict_operator:
        db = get_db()
        ids = get_ids_payment_type(db, dict_operator[type_pay])
        if id >= len(ids):
            return error_handler("Opção Inválida!")
        id_pay = ids[id]
        filter_query = f"""
        AND ( (pay.id_payment != -1 OR yi.id_payment != -1) AND (pay.id_payment={id_pay} OR yi.id_payment={id_pay}) )
        {extra_filter}
        """
        data = get_transactions(db, filter=filter_query)
        return render_template("main/transactions.html", data=data)

    if type_pay.lower() == "all":
        db = get_db()
        data = get_transactions(db, filter=extra_filter)
        return render_template("main/transactions.html", data=data)
    
    return error_handler("URL inválida!")

@app.route("/<string:operation>/transaction", methods=["POST"])
@login_required
def operator_transaction(operation):
    # Rota para adicionar uma nova transação
    if operation not in ("add", "set"):
        return "Url é inválida", 404

    status, content = check_name(request.form.get("name"))
    if not status:
        return content

    if request.form.get("value", "") == "":
        return ("O valor não pode estar vazio", 400)
    try:
        value = request.form.get("value").replace(",", ".")
        value = abs(float(value))
    except ValueError:
        return ("O valor deve ser um número real", 400)
    except Exception as error:
        return (f"Um erro aconteceu {str(error)}", 400)

    if request.form.get("datetime", "") == "":
        return ("Uma data deve ser escolhida", 400)
    
    if len(request.form.get("description", "")) > 100:
        return ("Descrição não pode ter mais de 100 caracteres", 400)

    db = get_db()
    check = check_to_from(db, request.form.get("to", ""), request.form.get("from", ""), session["id_user"])
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
        "description" : request.form.get("description", "")
    }
    
    if operation == "add":
        id_trans = add_transacion(db, data_insert)
    else:
        return "TODO", 200

    return (f"Transação inserida com sucesso", 200)

@app.route("/filter/transactions", methods=["POST"])
@login_required
def date_filter_transactions():
    return "TODO", 200

@app.route("/add/to", methods=["POST"])
@login_required
def add_to():
    # Rota utilizada para adicionar um novo Teller (Fonte de Gasto)

    name = request.form.get("name", "")
    category = request.form.get("category", "")
    new_category = request.form.get("new_category", "")
    status, content = check_add_to_from(name, category, new_category)

    if status == False:
        return content, 400
    else:
        db = get_db()

        if content == "new_category":
            add_category(db, new_category)
        
        return add_teller(db, name, request.form.get(content))

@app.route("/add/from", methods=["POST"])
@login_required
def add_from():
    # Rota para adicionar um novo Income (Fonte de Renda)

    name = request.form.get("name", "")
    category = request.form.get("category", "")
    new_category = request.form.get("new_category", "")
    status, content = check_add_to_from(name, category, new_category)

    if status == False:
        return content, 400
    else:
        db = get_db()

        if content == "new_category":
            add_category(db, new_category)
        
        return add_income(db, name, request.form.get(content))


@app.route("/message", methods=["GET"])
def message():
    # Rota para exibir uma página de mensagem na tela
    # Utilizada para erros, confirmações e outros

    if 'msg' not in session:
        return render_template("main/message_page.html", status="none", type="Sem dados", content="Nenhuma mensagem"), 200

    msg = session["msg"].copy()
    session.pop("msg")
    return render_template("main/message_page.html", **msg), msg["code"]

def error_handler(error):
    # Função que atua como manipulador dos erros que podem surgir

    payload = {
        "status": "error",
        "type": "Erro",
        "content": error,
        "code": 400
    }
    session['msg'] = payload
    return redirect(url_for("message"))

def success_handler(success):
    # Função utilizada para exibir mensagens de sucesso na tela 

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