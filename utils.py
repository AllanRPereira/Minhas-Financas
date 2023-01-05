from functools import wraps
from flask import session, redirect
from flask_mail import Message
from datetime import datetime
from model.database import get_main_incomes, get_main_expenses, get_expenses_by_category

def login_required(function):
    """
    Wrap para bloquear acessos sem o id_user definido na sessão

    function -> Função que será restrita
    """

    @wraps(function)
    def requisition_login(*args, **kwargs):
        if session.get("id_user") is None:
            return redirect("/login")
        return function(*args, **kwargs)
    
    return requisition_login

def brl(string):
    # Filtro para converter em valor monetário brasileiro

    return f"R$ {string:.2f}"

def percen(string):
    # Filtro para porcentagem

    return f"{100 * string:.1f}%"

def date_stamp(t):
    # Converte o objeto datetime em formato de data
    # Ou afirma que não há esse momento de tempo. Timestamp = 0

    if t == 0:
        return "Não há"
    return f"{t.day}/{t.month}/{t.year}"

def check_email(email):
    # Checa se o email digitado possui a divisão pelo @

    if email.find("@") == -1:
        return False
    return True

def check_name(name):
    """
    Verifica se o nome de um cartão, investimento ou débito atende os requisitos
    para ser insertido em sua respectiva tabela.

    name -> Nome do método de pagamento
    """

    if name == None or name == "":
        return ("Nome não pode ser nulo", 400)
    if len(name) > 25:
        return ("Nome deve ter menos de 25 letras", 400)
    return (True, "")

def check_add_to_from(name, category, new_category):
    if name == "":
        return (False, "Nome não pode estar vazio")

    cond_one = category == ""
    cond_two = new_category == ""
    if cond_one and cond_two:
        return (False, "Categoria deve ser escolhida")
    
    if not cond_one:
        if len(category) > 25:
            return (False, "Categoria deve ter menos de 25 letras")
    else:
        if len(new_category) > 25:
            return (False, "Nova categoria deve ter menos de 25 letras")

    return (True, "category" if not cond_one else "new_category")

def format_number(string):
    # Formata o texto obtido pelo campo de valor para um float
    return string.upper().replace("R$", "").replace(",", ".").replace(" ", "")

def check_to_from(db, element_to, element_from, id):
    """
    Checa se o destino do gasto e a fonte da renda são
    meios de pagamento. Nesse caso eles terão seus balanços alterados
    na função de inserir a transação!

    db -> Conexão com banco de dados
    element_to -> Nome da fonte de gasto
    element_from -> Nome da fonte de renda
    id -> Id do usuário

    Retorna o booleano referente a situação de ambos
    """

    if element_to == "" or element_from == "":
        return None

    element_to = element_to.lower()
    element_from = element_from.lower()
    query = """
    SELECT LOWER(pay.name) FROM payment_content AS pay WHERE id_user=?
    """
    data = db.execute(query, (id, )).fetchall()
    result = [element[0] for element in data]
    to_payment = False
    from_payment = False
    if element_from in result:
        from_payment = True
    if element_to in result:
        to_payment = True

    return (from_payment, to_payment)

def get_statics(db):
    """
    Função que cria as estatística que serão exibidas na homepage.
    Utiliza um dicionário base que apresenta um parâmetro 'func' que é 
    a função em db_operations responsável por prover os dados para a estatística

    db -> Conexão com banco de dados
    """

    graphs = {
        "Principais fontes de gastos": {
            "headers": ("Nome", "Gasto Total", "Porcentagem"),
            "func" : get_main_expenses
        },
        "Gastos por categoria": {
            "headers": ("Nome", "Gasto Total", "Porcentagem"),
            "func" : get_expenses_by_category
        },
        "Principais rendimentos": {
            "headers": ("Nome", "Rendimento Total", "Porcentagem"),
            "func" : get_main_incomes
        }
    }

    for title, graph in graphs.copy().items():
        graphs[title]["data"] = transform_graphs_data(graph["func"](db))

    return graphs

def transform_graphs_data(db_cursor_result):
    """
    Adiciona os dados obtidos pela query ao banco de dados 
    ao dicionário que será utilizado pelo render_template 
    na exibição correta das estatísticas!

    db_cursor_result -> Retorno de uma db.execute!

    """

    data = []
    for title, value in db_cursor_result:
        element = {}
        element["title"] = title
        element["value"] = value
        data.append(element)

    total = sum([graph["value"] for graph in data])
    if len(data) >= 10:
        size = 10
    else:
        size = len(data)
    data = sorted(data, key=lambda y:y["value"], reverse=True)
    for i in range(size):
        data[i]["percen"] = data[i]["value"] / total
    return data[:size]

def send_email(mail, subject, content, destination):
    """
    Função que envia o e-mail para confirmação da conta
    ou recuperação da conta.

    mail -> Conexão com o servidor de email
    subject -> Assunto da mensagem
    content -> Render HTML para o email
    destination -> Email do usuário

    Retorna uma tupla (status, content('Dados do Erro'))
    """

    msg = Message(subject, recipients=[destination,])
    msg.html = content
    try:
        mail.send(msg)
    except Exception as error:
        return (False, str(error))
    
    return (True, "")

def token_validity(db, token_data):
    """
    Checa se um dado token é válido:
        1. Checa o tempo da criação (Menor que 10 minutos)
        2. Checa se o token foi cadastrado no banco de dados (Para ser válido)
    
    db -> Conexão com banco de dados
    token_data -> Payload do token em forma de dicionário

    Retorna uma tupla (status, content('Dados do Erro'))
    """

    if datetime.now().timestamp() - token_data["timestamp"] > 360:
        return (False, "Link atingiu o tempo máximo")
    
    try:
        data = db.execute("SELECT type FROM tokens WHERE id=?", (token_data["id"], )).fetchone()
        if data == None or data == [] or data[0] != token_data["type"]:
            return (False, "Token inválido")
            
    except Exception as error:
        return (False, error)
    
    return (True, "")
    

