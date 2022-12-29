from flask import session

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


