from flask import session
from datetime import datetime

def insert_data_transaction(db, dict_data):
    if dict_data["to_payment"]:
        id_to = db.execute("SELECT id FROM payment_content WHERE LOWER(name)=? AND id_user=?", 
                        (dict_data["to"].lower(), session["id_user"]))
        id_payer = db.execute("INSERT INTO payer (id_payment) VALUES (?)", (id_to, )).lastrowid
    else:
        id_to = db.execute("INSERT INTO teller (name, id_user) VALUES (?, ?)", 
                        (dict_data["to"], session["id_user"])).lastrowid
        id_payer = db.execute("INSERT INTO payer (id_teller) VALUES (?)", (id_to, )).lastrowid

    if dict_data["from_payment"]:
        id_from = db.execute("SELECT id FROM payment_content WHERE LOWER(name)=? AND id_user=?", 
                    (dict_data["from"].lower(), session["id_user"]))
        id_yield = db.execute("INSERT INTO yield (id_payment) VALUES (?)", (id_from, )).lastrowid

    else:
        id_from = db.execute("INSERT INTO incomes (name, id_user) VALUES (?, ?)", 
                        (dict_data["from"], session["id_user"])).lastrowid
        id_yield = db.execute("INSERT INTO yield (id_income) VALUES (?)", (id_from, )).lastrowid
    
    insert_content = (
        dict_data["name"], dict_data["value"], dict_data["timestamp"], dict_data["description"], id_payer, id_yield, session["id_user"]
    )
    id_trans = db.execute("""INSERT INTO transactions 
            (name, value, timestamp, description, id_to, id_from, id_user) 
            VALUES (?,?,?,?,?,?,?)""", insert_content).lastrowid
    return id_trans

def get_data_payment(db, type_pay):
    """
    There is four type payments/account methods
    0 - Wallet
    1 - Credit Card
    2 - Investiment
    3 - Debt
    """

    query = """
    SELECT pay.name, pay.balance, MAX(tr.timestamp) FROM payment_content AS pay
    INNER JOIN transactions AS tr ON tr.id_user=pay.id_user
    INNER JOIN yield AS y ON y.id=tr.id_from
    INNER JOIN payer AS py ON py.id=tr.id_to
    WHERE pay.id_user=? AND pay.type=?
    GROUP BY pay.name
    ORDER BY pay.name
    """
    result = db.execute(query, (session['id_user'], type_pay))
    data = []
    for row in result:
        element = {
            "title" : row[0],
            "balance" : row[1],
            "lastest_move" : datetime.fromtimestamp(row[2])
        }
        data.append(element)
    return data

def get_to_options(db):
    query = """
    SELECT DISTINCT LOWER(name) FROM teller
    WHERE id_user=?
    """
    data = db.execute(query, (session["id_user"], ))
    options = []
    for row in data:
        options.append(row[0])
    return options

def get_from_options(db):
    query = """
    SELECT DISTINCT LOWER(name) FROM incomes
    WHERE id_user=?
    """
    data = db.execute(query, (session["id_user"], ))
    options = []
    for row in data:
        options.append(row[0])
    return options

def get_payment_options(db):
    query = """
    SELECT name FROM payment_content
    WHERE id_user=?
    """
    data = db.execute(query, (session["id_user"], ))
    options = []
    for row in data:
        options.append(row[0])
    return options

def get_categorys(db):
    categorys ={
        "income" : [],
        "teller" : []
    }

    query = """
    SELECT DISTINCT cat.name FROM categorys AS cat
    INNER JOIN incomes AS inc ON inc.id_category=cat.id
    WHERE inc.id_user=?
    """
    data = db.execute(query, (session["id_user"], ))
    for row in data:
        categorys["income"].append(row[0])

    query = """
    SELECT DISTINCT cat.name FROM categorys AS cat
    INNER JOIN teller AS te ON te.id_category=cat.id
    WHERE te.id_user=?
    """

    data = db.execute(query, (session["id_user"], ))
    for row in data:
        categorys["teller"].append(row[0])

    return categorys

def add_category(db, name):
    query = """
    INSERT INTO categorys (name) VALUES (?)
    """
    db.execute(query, (name.lower(), ))

def get_id_category(db, category):
    query = "SELECT id FROM categorys WHERE LOWER(name)=?"
    id_category = db.execute(query, (category.lower(), )).fetchone()
    if id_category == None:
        return False
    else:
        return id_category[0]
    

def add_income(db, name, category):
    id_category = get_id_category(db, category)
    if id_category == False: return "Não foi possível obter a categoria", 400

    query = "INSERT INTO incomes (name, id_user, id_category) VALUES (?, ?, ?)"
    db.execute(query, (name.lower(), session["id_user"], id_category))

    return "Origem adicionada com sucesso", 200

def add_teller(db, name, category):
    id_category = get_id_category(db, category)
    if id_category == False: return "Não foi possível obter a categoria", 400
    
    query = "INSERT INTO teller (name, id_user, id_category) VALUES (?, ?, ?)"
    db.execute(query, (name.lower(), session["id_user"], id_category))

    return "Destino adicionado com sucesso", 200
    
