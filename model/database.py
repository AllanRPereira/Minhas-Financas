from flask import session, g
from datetime import datetime
import sqlite3
import os

"""
Importante:

Há quatro tipos de payment_content:
0 - Carteira
1 - Cartão de Crédito
2 - Investimento
3 - Dívida

Códigos utilizados em funções que necessitam de type_pay
"""

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL is None:
    raise Exception("Local do banco de dados não informado!")

def add_user(db, email, hash):
    try:
        query = "INSERT INTO users (email, password) VALUES (?, ?)"
        id_user = db.execute(query, (email, hash)).lastrowid
        return id_user
    except Exception as error:
        return error_handler(str(error))

def add_payment(db, name, balance, type_pay, id_user="", extra_data=-1):
    """
    Adiciona uma nova forma de pagamento (payment_content)
    associando-a à um usuário.
    
    db -> Conexão com o banco de dados
    name -> Nome do método de pagamento
    balance -> Saldo inicial do método
    type_pay -> Tipo de Método de pagamento (Carteira, Cartão, Investimento e Dívida)
    extra_data -> Dado extra de cada método de pagamento, indivídual para cada!
    """

    query = """
    INSERT INTO payment_content (id_user, type, name, balance, extra_data)
    VALUES (?, ?, ?, ?, ?)
    """

    if id_user == "": id_user = session["id_user"]

    id_payment = db.execute(query, (id_user, type_pay, name, balance, extra_data)).lastrowid

    return id_payment

def add_category(db, name):
    """
    Adicionar uma nova categoria ao banco de dados.

    db -> Conexão com o banco de dados
    name -> Nome da categoria
    """

    query = """
    INSERT INTO categorys (name) VALUES (?)
    """
    return db.execute(query, (name.lower(), )).lastrowid

def add_income(db, name, category):
    """
    Adiciona um novo income no banco de dados. É necessário que
    a categoria da nova fonte de renda (income) já exista previamente.

    db -> Conexão com o banco de dados
    name -> Nome do novo Income
    category -> Nome da categoria do Income

    Retorna uma tupla com o resultado da requisição e o código
    """

    id_category = get_id_category(db, category)
    if id_category == False: return "Não foi possível obter a categoria", 400

    query = "INSERT INTO incomes (name, id_user, id_category) VALUES (?, ?, ?)"
    db.execute(query, (name.lower(), session["id_user"], id_category))

    return "Origem adicionada com sucesso", 200

def add_teller(db, name, category):
    """
    Análogo à adicionar uma nova fonte de renda, porém
    agora adicionando uma nova forma de gasto (Teller)

    db -> Conexão com o banco de dados
    name -> Nome da nova fonte de gasto
    category -> Nome da categoria do Teller
    """

    id_category = get_id_category(db, category)
    if id_category == False: return "Não foi possível obter a categoria", 400
    
    query = "INSERT INTO teller (name, id_user, id_category) VALUES (?, ?, ?)"
    db.execute(query, (name.lower(), session["id_user"], id_category))

    return "Destino adicionado com sucesso", 200
    
def add_token(db, type_token, id_user=-1):
    # id_user = -1 é um valor genêrico para a query ter a mesma estrutura em confirmation e recover

    query = "INSERT INTO tokens (id_user, type) VALUES (?, ?)"
    return db.execute(query, (id_user, type_token)).lastrowid
 
def add_transacion(db, dict_data):
    """
    Insero os dados necessários para criação de uma transação no BD retornando o id
    da transação criada.

    db -> Conexão com o banco de dados
    dict_data -> Dicionário com os dados relevantes (Ver em App.py)
    """

    if dict_data["to_payment"]:
        # Valor é direcionado para uma fonte que possue um saldo

        # Id do meio de pagamento
        id_to = db.execute("SELECT id FROM payment_content WHERE LOWER(name)=? AND id_user=?", 
                        (dict_data["to"].lower(), session["id_user"])).fetchone()[0]

        # Id do Payer que é o intermediário de ligação
        id_payer = db.execute("INSERT INTO payer (id_payment) VALUES (?)", (id_to, )).lastrowid

        # Atualização do saldo no meio de pagamento de destino
        db.execute("UPDATE payment_content SET balance=balance+? WHERE id=?", (dict_data["value"], id_to))

    else:
        # Vai para um Teller que não possue saldo, sendo então apenas um gasto

        id_to = db.execute("SELECT id FROM teller WHERE LOWER(name)=? AND id_user=?", 
                            (dict_data["to"], session["id_user"])).fetchone()[0]
        id_payer = db.execute("INSERT INTO payer (id_teller) VALUES (?)", (id_to, )).lastrowid

    if dict_data["from_payment"]:
        # Procedimento análogo ao "to_payment"

        id_from = db.execute("SELECT id FROM payment_content WHERE LOWER(name)=? AND id_user=?", 
                    (dict_data["from"].lower(), session["id_user"])).fetchone()[0]

        id_yield = db.execute("INSERT INTO yield (id_payment) VALUES (?)", (id_from, )).lastrowid

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
        id_payer, 
        id_yield, 
        session["id_user"]
    )
    id_trans = db.execute("""INSERT INTO transactions 
            (name, value, timestamp, description, id_to, id_from, id_user) 
            VALUES (?,?,?,?,?,?,?)""", insert_content).lastrowid
    
    return id_trans

def get_data_payment(db, type_pay):
    """
    Retorna os dados de uma payment_content, inclusive
    utilizando a função get_lastest_move para obter o timestamp
    da última transação com esse método de pagamento

    db -> Conexão com o banco de dados
    type_pay -> Tipo de pagamento

    """
    
    query = """
    SELECT id, name, balance FROM payment_content
    WHERE id_user=? AND type=?
    ORDER BY id
    """

    data = []
    result = db.execute(query, (session["id_user"], type_pay))
    for i, row in enumerate(result):
        if row == (None, None, None):
            break

        element = {
            "id" : i,
            "title" : row[1],
            "balance" : row[2],
            "lastest_move" : get_lastest_move(db, row[0])
        }
        data.append(element)
        
    return data

def get_lastest_move(db, id_method):
    """
    Obtém o objeto datetime da última transação encontrada
    para um dado id de pagamento. Tanto o pagamento sendo uma fonte (yield)
    quanto um destino (payer)

    db -> Instância de conexão do banco de dados
    id_method -> Id do método no banco de dados

    """


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
        return 0 # É avaliado posteriormente como não possuindo valor
    else:
        return datetime.fromtimestamp(result[0])

def get_to_options(db):
    """
    Obtém os nomes de todos os objetos de gasto (Teller) de um
    dado usuário. São utilizados no momento de criar uma transação
    no dropbox da homepage

    db -> Conexão com o banco de dados
    """

    query = """
    SELECT DISTINCT LOWER(name) FROM teller
    WHERE id_user=?
    """
    cursor = db.execute(query, (session["id_user"], ))
    return run_over_row(cursor)

def get_from_options(db):
    """
    Analógo ao get_to_options mas obtendo a informação das 
    fontes de renda (incomes) de um dado usuário.

    db -> Conexão com o banco de dados
    """

    query = """
    SELECT DISTINCT LOWER(name) FROM incomes
    WHERE id_user=?
    """
    cursor = db.execute(query, (session["id_user"], ))
    return run_over_row(cursor)

def get_payment_options(db):
    """
    Obtém as formas de pagamento que um dado usuário possui.
    Todos os usuários possuem uma carteira no momento da criação da conta

    db -> Conexão com o banco de dados
    """

    query = """
    SELECT LOWER(name) FROM payment_content
    WHERE id_user=?
    ORDER BY id
    """
    cursor = db.execute(query, (session["id_user"], ))
    return run_over_row(cursor)

def run_over_row(db_cursor_result):
    """
    Percorre um cursor.object do banco de dados.

    db_cursor_result -> db.cursor.result
    """

    options = []
    for row in db_cursor_result:
        options.append(row[0])
    return options

def get_ids_payment_type(db, type_pay):
    """
    Obtém os id's dos meios de pagamento que:
        1. São do usuário da sessão
        2. São do tipo definido em type_pay
    
    db -> Conexão com o banco de dados
    type_pay -> Tipo de meio de pagamento 
    """

    query = """
    SELECT id FROM payment_content AS pay
    WHERE pay.id_user=? AND pay.type=?
    """
    result = db.execute(query, (session["id_user"], type_pay)).fetchall()
    ids = [row[0] for row in result]
    return ids

def get_categorys(db):
    """
    Obtém as categorias dos incomes e dos tellers
    de um dado usuário por meio de duas querys

    db -> Conexão com o banco de dados
    """

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

def get_id_category(db, category):
    """
    Obtém o id de uma categoria, caso não exista, retorna False

    db -> Conexão com o banco de dados
    category -> Nome da categoria
    """

    query = "SELECT id FROM categorys WHERE LOWER(name)=?"
    id_category = db.execute(query, (category.lower(), )).fetchone()
    if id_category == None:
        return False
    else:
        return id_category[0]
    
def get_main_incomes(db):
    """
    Função que obtém do banco de dados as principais fontes de 
    renda de um dado usuário.

    db -> Conexão com o banco de dados

    Retorna cursor da resposta do banco de dados
    """

    query = """
    SELECT cat.name, SUM(value) FROM transactions AS tr
    INNER JOIN yield AS yi ON yi.id=tr.id_from
    INNER JOIN incomes AS inc ON inc.id=yi.id_income
    INNER JOIN categorys AS cat ON cat.id=inc.id_category
    WHERE tr.id_user=?
    GROUP BY cat.name
    ORDER BY SUM(value) DESC
    """
    result = db.execute(query, (session["id_user"], ))
    return result

def get_expenses_by_category(db):
    """
    Função que obtém as principais fontes de gasto de um usuário
    de forma que são separadas por meio das suas categorias

    db -> Conexão com banco de dados

    Retorna cursor da resposta do banco de dados
    """

    query = """
    SELECT cat.name, SUM(value) FROM transactions AS tr
    INNER JOIN payer AS py ON py.id=tr.id_to
    INNER JOIN teller AS te ON te.id=py.id_teller
    INNER JOIN categorys AS cat ON cat.id=te.id_category
    WHERE tr.id_user=?
    GROUP BY cat.name
    ORDER BY SUM(value) DESC;
    """
    result = db.execute(query, (session["id_user"], ))
    return result

def get_main_expenses(db):
    """
    Análogo ao get_main_incomes porém obtendo as principais fontes de renda
    de um dado usuário

    db -> Conexão com banco de dados

    Retorna cursor da resposta do banco de dados
    """

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
    result = db.execute(query, (session["id_user"], ))
    return result

def get_payments_balance(db):
    """
    Função que obtém os dados de cada método de pagamento,
    Nome, Saldo e a última transação tanto de gasto quanto de ganho
    realizado por um dado método

    db -> Conexão com banco de dados

    """
    id_user = session["id_user"]
    query = """
    SELECT type, SUM(balance) FROM payment_content AS p
    WHERE p.id_user=?
    GROUP BY type
    """

    user_methods = db.execute(query, (id_user, )).fetchall()

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

def get_transactions(db, filter=""):
    """
    Obtém todas as transações do usuário. Pode ter um filtro
    que determina quais o meios de pagamento que devem ser mostrados

    db -> Conexão com banco de dados
    filter -> Query SQL que filtra os dados

    Retorna uma lista de dicionários com os dados de cada transação
    """

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
    ORDER BY tr.timestamp DESC;
    """
    data = {
        "headers": ("Nome", "Valor", "Data", "Origem", "Destino")
    }
    query_result = db.execute(query, (session["id_user"], )).fetchall()
    if query_result == [None, ]:
        data["rows"] = ("-", "-", "-", "-", "-")
    else:
        data["rows"] = []
        for row in query_result:
            element = {
                "name" : row[0],
                "value" : row[1],
                "date" : datetime.fromtimestamp(row[2]),
                "origin" : row[3],
                "destination" : row[4]
            }
            data["rows"].append(element)
    return data

def get_options(db):
    """
    Rota utilizada pelo layout.js para atualizar dinamicamente os Incomes e os
    Tellers disponíveis no momento de adicionar uma transação.
    """

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

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = sqlite3.connect(DATABASE_URL)
        g._database = db
    return db

def get_user_pass_by_email(db, email, password=True):
    """
    Obtém os dados de um usuário da tabela 'users'.
    Pode tanto obter o id e o password ou só o id

    db -> Conexão com banco de dados
    email -> Email do usuário
    password -> Booleano que determina se quer ou não a senha do usuário

    Retorna os dados requisitados
    """

    if password:
        query = "SELECT id, password FROM users WHERE email=? LIMIT 1"
    else:
        query = "SELECT id FROM users WHERE email=? LIMIT 1"
    return db.execute(query, (email, )).fetchall()

def set_user_information(db, id_user, password=False, email=False):
    """
    Altera no banco de dados as informações do usuário.
    Tem-se os booleanos password e email que determinam qual informação será pedida.

    id_user -> Id do usuário na tabela
    password -> Booleano para obter a senha
    email -> Booleano para obter o email

    Retorna os dados requisitados
    """

    query = "UPDATE users SET "
    bind = tuple()
    if password != False:
        query += "password=? "
        bind += (password, )

    if email != False:
        query += "email=? "
        bind += (email, )
    
    query += "WHERE id=?"
    bind += id_user
    
    db.execute(query, bind)
    return True

def set_payment(db, **kwargs):
    kwargs["id_user"] = session["id_user"]
    pair_set = []
    binds = []
    for key, value in kwargs.items():
        pair_set.append(f"{key}=?")
        binds.append(value)
    binds.append(kwargs["id"])
    binds = tuple(binds)

    query = f"UPDATE payment_content SET {','.join(pair_set)} WHERE id=?"
    db.execute(query, binds)
    return True

def delete_token(db, id_token):
    query = "DELETE FROM tokens WHERE id=?"
    db.execute(query, (id_token, ))
    return True