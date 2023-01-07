import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import string
import random
import os

"""
Parte do software utilizada para gerar conteúdo para o banco de dados.
    1. Reseta o banco de dados
    2. Adiciona um usuário
    3. Cria os payment_content
    4. Cria as categorias
    5. Criar os Tellers e os Incomes
    6. Adicionar as transações
"""


def random_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


# Reset database
os.remove("model/minhasfinancas.db")
query_tables = open("static/sql/database.sql", "r").read()
password = generate_password_hash("test")
db = sqlite3.connect("model/minhasfinancas.db")
db.executescript(query_tables)
print("Banco de dados resetado!")

id_user = db.execute("INSERT INTO users (email, password) VALUES (?, ?)", ("test@test", password)).lastrowid

print(f"Id do usuário:{id_user}")

# Formas de pagamento
id_payments = [0, 0, 0, 0]
id_payments[0] = db.execute("INSERT INTO payment_content (type, id_user, name, balance) VALUES (0, ?, 'Carteira', 100)", (id_user, )).lastrowid
id_payments[1] = db.execute("INSERT INTO payment_content (type, id_user, name) VALUES (1, ?, 'Nubank')", (id_user, )).lastrowid
id_payments[2] = db.execute("INSERT INTO payment_content (type, id_user, name) VALUES (2, ?, 'Caixinha Notebook')", (id_user, )).lastrowid
id_payments[3] = db.execute("INSERT INTO payment_content (type, id_user, name) VALUES (3, ?, 'Dívida Sandra')", (id_user, )).lastrowid

print(f"Formas de pagamento adicionadas: {id_payments}")

# Categorias de Gastos
categorias = ["Supermercado", "Saúde", "Educação", "Transporte", "Salário", "Presente", "Imóveis", "Serviços"]
id_categorias = []
n_category = 3
for categoria in categorias:
    id_categorias.append(db.execute("INSERT INTO categorys (name) VALUES (?)", (categoria, )).lastrowid)
rent_categorys = id_categorias[4:]
teller_categorys = id_categorias[:4]
print(f"Categorias adicionadas: {id_categorias}")

# Criar Tellers

list_name = [random_generator() for i in range(50)]
id_teller = []
for name in list_name:
    data_insert = (name, id_user, teller_categorys[random.randint(0, n_category)])
    id_teller.append(db.execute("INSERT INTO teller (name, id_user, id_category) VALUES (?, ?, ?)", data_insert).lastrowid)

print("Tellers adicionados!")

# Criar Incomes

list_name = [random_generator() for i in range(50)]
id_incomes = []
for name in list_name:
    data_insert = (name, id_user, rent_categorys[random.randint(0, n_category)])
    id_incomes.append(db.execute("INSERT INTO incomes (name, id_user, id_category) VALUES (?, ?, ?)", data_insert).lastrowid)

print("Incomes adicionados")

db.commit()

# Transações

query = """
    INSERT INTO transactions (value, name, timestamp, id_to, id_from, id_user)
    VALUES (?, ?, ?, ?, ?, ?)
    """

data_insert = []
money = [0, 0, 0, 0]
for i in range(20):
    cash = round(random.random() * 10, 2)

    id_from = random.randint(0, 3)
    result = random.randint(0, 5)
    if result == 0:
        data_payer = (id_incomes[random.randint(0, 49)], )
        id_yield = db.execute("INSERT INTO yield (id_income) VALUES (?)", data_payer).lastrowid

    else:
        data_payer = (id_payments[id_from], )
        id_yield = db.execute("INSERT INTO yield (id_payment) VALUES (?)", data_payer).lastrowid
        db.execute("UPDATE payment_content SET balance=balance-? WHERE id=?", (cash, data_payer[0]))

    if random.randint(0, 1) == 0:
        data_payer = (id_teller[random.randint(0, 49)], )
        id_payer = db.execute("INSERT INTO payer (id_teller) VALUES (?)", data_payer).lastrowid
    else:
        data_payer = (id_payments[random.randint(0, 3)], )
        id_payer = db.execute("INSERT INTO payer (id_payment) VALUES (?)", data_payer).lastrowid
        db.execute("UPDATE payment_content SET balance=balance+? WHERE id=?", (cash, data_payer[0]))
    
    if result != 0:
        money[id_from] += cash

    data_insert.append((
        cash,
        random_generator(size=10),
        round(datetime.now().timestamp() + i),
        id_payer,
        id_yield, 
        id_user
    ))


db.executemany(query, data_insert)
db.commit()
for id_from in range(4):
    db.execute("UPDATE payment_content SET balance=balance-? WHERE id=?", (money[id_from], id_from))
db.commit()
db.close()

print("Transações realizadas")

print("Dados adicionados com sucesso!")