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

def check_email(email):
    if email.find("@") == -1:
        return False
    return True

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

def main_expenses(db, total, id):
    query = """
    SELECT te.name, SUM(value)
    FROM transactions AS tr
    INNER JOIN payer AS p ON tr.id_to=p.id
    INNER JOIN teller AS te ON p.id_teller=te.id
    INNER JOIN users ON users.id=tr.id_user
    WHERE tr.id_user=?
    GROUP BY te.name
    UNION
    SELECT pc.name, SUM(value)
    FROM transactions AS tr
    INNER JOIN payer AS p ON tr.id_to=p.id
    INNER JOIN payment_content AS pc ON p.id_payment=pc.id
    WHERE tr.id_user=?
    GROUP BY pc.name
    ORDER BY SUM(value) DESC
    """
    data_one = base_graph_static(db, query, (id, id))

    query = """
    SELECT pc.name, SUM(value)
    FROM transactions AS tr
    INNER JOIN yield AS yi ON tr.id_from=yi.id
    INNER JOIN payment_content AS pc ON yi.id_payment=pc.id
    WHERE tr.id_user=?
    GROUP BY pc.name
    ORDER BY SUM(value) DESC
    """
    data_two = base_graph_static(db, query, (id, ))
    keys = [data_one[index]["title"] for index in range(len(data_one))]
    for graph in data_two:
        if graph["title"] in keys:
            index = keys.index(graph["title"])
            data_one[index]["value"] -= graph["value"]
    total = sum([graph["value"] for graph in data_one])
    data_one = sorted(data_one, key=lambda x: x["value"], reverse=True)
    if len(data_one) >= 10:
        size = 10
    else:
        size = len(data_one)
    for i in range(size):
        data_one[i]["percen"] = data_one[i]["value"] / total

    return data_one[:10]

def category_expenses(db, total, id):
    query = """
    SELECT cat.name, SUM(value) FROM transactions AS tr
    INNER JOIN categorys AS cat ON cat.id=tr.id_category
    INNER JOIN payer AS py ON py.id=tr.id_to
    INNER JOIN teller AS te ON te.id=py.id_teller
    WHERE tr.id_user=?
    GROUP BY cat.name
    ORDER BY SUM(value) DESC
    """
    data_one = base_graph_static(db, query, (id, ))
    total = sum([graph["value"] for graph in data_one])
    if len(data_one) >= 10:
        size = 10
    else:
        size = len(data_one)
    for i in range(size):
        data_one[i]["percen"] = data_one[i]["value"] / total
    return data_one

def main_income(db, total, id):
    query = """
    SELECT cat.name, SUM(value) FROM transactions AS tr
    INNER JOIN categorys AS cat ON cat.id=tr.id_category
    INNER JOIN yield AS yi ON yi.id=tr.id_from
    INNER JOIN incomes AS inc ON inc.id=yi.id_income
    WHERE tr.id_user=?
    GROUP BY cat.name
    ORDER BY SUM(value) DESC
    """
    data_one = base_graph_static(db, query, (id, ))
    total = sum([graph["value"] for graph in data_one])
    if len(data_one) >= 10:
        size = 10
    else:
        size = len(data_one)
    for i in range(size):
        data_one[i]["percen"] = data_one[i]["value"] / total
    return data_one

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
    

