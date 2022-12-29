from functools import wraps
from flask import session, redirect
from flask_mail import Message
from datetime import datetime

def login_required(function):

    @wraps(function)
    def requisition_login(*args, **kwargs):
        if session.get("id_user") is None:
            return redirect("/login")
        return function(*args, **kwargs)
    
    return requisition_login

def brl(string):
    return f"R$ {string:.2f}"

def percen(string):
    return f"{100 * string:.1f}%"

def date_stamp(t):
    return f"{t.year}/{t.month}/{t.day}"

def check_email(email):
    if email.find("@") == -1:
        return False
    return True

def check_to_from(db, element_to, element_from, id):
    if element_to == "" or element_from == "":
        return None

    element_to = element_to.lower()
    element_from = element_from.lower()
    query = """
    SELECT LOWER(pay.name) FROM payment_content AS pay WHERE id_user=?
    """
    result = db.execute(query, (id, )).fetchall()
    to_payment = False
    from_payment = False
    if element_from in result:
        element_from = True
    if element_to in result:
        to_payment = True

    return (from_payment, to_payment)

def get_graphs():
    graphs = {
        "Principais fontes de gastos": {
            "headers": ("Nome", "Gasto Total", "Porcentagem"),
            "func" : main_expenses
        },
        "Gastos por categoria": {
            "headers": ("Nome", "Gasto Total", "Porcentagem"),
            "func" : category_expenses
        },
        "Principais rendimentos": {
            "headers": ("Nome", "Rendimento Total", "Porcentagem"),
            "func" : main_income
        }
    }

    return graphs

def main_expenses(db, id):
    query = """
    SELECT te.name, SUM(value)
    FROM transactions AS tr
    INNER JOIN payer AS p ON tr.id_to=p.id
    INNER JOIN teller AS te ON p.id_teller=te.id
    INNER JOIN users ON users.id=tr.id_user
    WHERE tr.id_user=?
    GROUP BY te.name
    ORDER BY SUM(value)
    """
    data_one = base_graph_static(db, query, (id, ))

    return get_final_data(data_one)

def category_expenses(db, id):
    query = """
    SELECT cat.name, SUM(value) FROM transactions AS tr
    INNER JOIN payer AS py ON py.id=tr.id_to
    INNER JOIN teller AS te ON te.id=py.id_teller
    INNER JOIN categorys AS cat ON cat.id=te.id_category
    WHERE tr.id_user=?
    GROUP BY cat.name
    ORDER BY SUM(value) DESC;
    """
    data_one = base_graph_static(db, query, (id, ))
    return get_final_data(data_one)

def main_income(db, id):
    query = """
    SELECT cat.name, SUM(value) FROM transactions AS tr
    INNER JOIN yield AS yi ON yi.id=tr.id_from
    INNER JOIN incomes AS inc ON inc.id=yi.id_income
    INNER JOIN categorys AS cat ON cat.id=inc.id_category
    WHERE tr.id_user=?
    GROUP BY cat.name
    ORDER BY SUM(value) DESC
    """
    data_one = base_graph_static(db, query, (id, ))
    return get_final_data(data_one)

def get_final_data(data):
    total = sum([graph["value"] for graph in data])
    if len(data) >= 10:
        size = 10
    else:
        size = len(data)
    data = sorted(data, key=lambda y:y["value"], reverse=True)
    for i in range(size):
        data[i]["percen"] = data[i]["value"] / total
    return data[:size]


def base_graph_static(db, query, bind):
    data = []
    for title, value in db.execute(query, bind):
        element = {}
        element["title"] = title
        element["value"] = value
        data.append(element)
    return data

def send_email(mail, subject, content, destination):
    msg = Message(subject, recipients=[destination,])
    msg.html = content
    try:
        mail.send(msg)
    except Exception as error:
        return (False, str(error))
    
    return (True, "")

def get_sql_query_token(token_data):

    if token["type"] == 1: #Password Change
        query = ("UPDATE users SET hash=? WHERE id_user=?", (token["hash"], token["id_user"]))
        msg = "Senha alterada com sucesso"

    return (query, msg)

def token_validity(db, token_data):
    if datetime.now().timestamp() - token_data["timestamp"] > 360:
        return (False, "Link atingiu o tempo máximo")
    
    try:
        data = db.execute("SELECT type FROM tokens WHERE id=?", (token_data["id"], )).fetchone()
        if data == None or data == [] or data[0] != token_data["type"]:
            return (False, "Token inválido")
            
    except Exception as error:
        return (False, error)
    
    return (True, "")
    

