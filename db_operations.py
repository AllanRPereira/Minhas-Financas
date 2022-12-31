from flask import session
from datetime import datetime

def insert_data_transaction(db, dict_data):
    if dict_data["to_payment"]:
        id_to = db.execute("SELECT id FROM payment_content WHERE LOWER(name)=? AND id_user=?", 
                        (dict_data["to"].lower(), session["id_user"])).fetchone()[0]

        id_payer = db.execute("INSERT INTO payer (id_payment) VALUES (?)", (id_to, )).lastrowid

        # Add to the payment method
        db.execute("UPDATE payment_content SET balance=balance+? WHERE id=?", (dict_data["value"], id_to))

    else:
        id_to = db.execute("SELECT id FROM teller WHERE LOWER(name)=? AND id_user=?", 
                            (dict_data["to"], session["id_user"])).fetchone()[0]
        id_payer = db.execute("INSERT INTO payer (id_teller) VALUES (?)", (id_to, )).lastrowid

    if dict_data["from_payment"]:
        id_from = db.execute("SELECT id FROM payment_content WHERE LOWER(name)=? AND id_user=?", 
                    (dict_data["from"].lower(), session["id_user"])).fetchone()[0]

        id_yield = db.execute("INSERT INTO yield (id_payment) VALUES (?)", (id_from, )).lastrowid

        # Subtract from the payment method
        db.execute("UPDATE payment_content SET balance=balance-? WHERE id=?", (dict_data["value"], id_from))

    else:
        id_from = db.execute("SELECT id FROM incomes WHERE LOWER(name)=? AND id_user=?", 
                            (dict_data["from"], session["id_user"])).fetchone()[0]
        id_yield = db.execute("INSERT INTO yield (id_income) VALUES (?)", (id_from, )).lastrowid
    
    insert_content = (
        dict_data["name"].lower(), 
        dict_data["value"], 
        dict_data["timestamp"], 
        dict_data["description"], 
        id_payer, id_yield, session["id_user"]
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
    SELECT id, name, balance FROM payment_content
    WHERE id_user=? AND type=?
    """

    data = []
    result = db.execute(query, (session["id_user"], type_pay))
    i = 0
    for row in result:
        if row == (None, None, None):
            break

        element = {
            "id" : i,
            "title" : row[1],
            "balance" : row[2],
            "lastest_move" : get_lastest_move(db, row[0])
        }
        data.append(element)
        i += 1
    return data

def get_lastest_move(db, id_method):
    query = """
    SELECT MAX(tr.timestamp) FROM payment_content AS pay
    INNER JOIN payer AS py ON py.id_payment=pay.id
    INNER JOIN transactions AS tr ON tr.id_to=py.id
    WHERE tr.id_user=? AND pay.id=?
    UNION
    SELECT MAX(tr.timestamp) FROM payment_content AS pay
    INNER JOIN yield AS y ON y.id_payment=pay.id
    INNER JOIN transactions AS tr ON tr.id_from=y.id
    WHERE tr.id_user=? AND pay.id=?
    ORDER BY MAX(tr.timestamp) DESC
    LIMIT 1
    """
    result = db.execute(query, (session["id_user"], id_method, session["id_user"], id_method)).fetchone()
    if result == (None, ):
        return 0
    else:
        return datetime.fromtimestamp(result[0])

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
    SELECT LOWER(name) FROM payment_content
    WHERE id_user=?
    """
    data = db.execute(query, (session["id_user"], ))
    options = []
    for row in data:
        options.append(row[0])
    return options

def get_ids_payment_type(db, type_pay):
    query = """
    SELECT id FROM payment_content AS pay
    WHERE pay.id_user=? AND pay.type=?
    """
    result = db.execute(query, (session["id_user"], type_pay)).fetchall()
    return result

def get_categorys(db):
    categorys ={
        "income" : [],
        "teller" : []
    }

    query = """
    SELECT DISTINCT LOWER(cat.name) FROM categorys AS cat
    INNER JOIN incomes AS inc ON inc.id_category=cat.id
    WHERE inc.id_user=?
    """
    data = db.execute(query, (session["id_user"], ))
    for row in data:
        categorys["income"].append(row[0])

    query = """
    SELECT DISTINCT LOWER(cat.name) FROM categorys AS cat
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
    
def add_payment(db, name, balance, type_pay):
    query = """
    INSERT INTO payment_content (id_user, type, name, balance)
    VALUES (?, ?, ?, ?)
    """

    db.execute(query, (session["id_user"], type_pay, name, balance))

    return ("Adicionado com sucesso! Recarregue a página", 200)