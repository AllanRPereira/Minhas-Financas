from flask import Blueprint, render_template, request
from utils import login_required, format_number, check_name
from model.database import add_payment, set_payment, get_options, get_db, get_data_payment, get_ids_payment_type
from consts import CREDIT_CARD

credit_page = Blueprint("credit_page", __name__, template_folder="../../templates")

@credit_page.route("/creditcard", methods=["GET"])
@login_required
def creditcard():
    #Rota para obter e exibir os cartões de crédito

    db = get_db()
    creditcard = get_data_payment(db, CREDIT_CARD)
    options = get_options(db)
    return render_template("main/credit_card.html", cards=creditcard, **options)

@credit_page.route("/<string:operation>/creditcard", methods=["POST"])
@login_required
def operator_credit_card(operation):
    # Rota utilizado pelo layout.js para adicionar um novo cartão

    if operation not in ["add", "set"]:
        return ("Url é inválida", 404)

    name = request.form.get("name", "")
    due_date = request.form.get("due_date", "")
    initial_bill = format_number(request.form.get("initial_bill", ""))
    status, content = check_name(name)
    if not status:
        return content
    try:
        initial_bill = float(initial_bill)
    except ValueError:
        return ("A fatura inicial deve ser um número", 400)
    
    try:
        due_date = int(due_date)
    except Exception as error:
        return ("Campo de vencimento não é valido "+ str(error), 400)
    
    db = get_db()
    if operation == "add":
        add_payment(db, name, initial_bill, CREDIT_CARD, extra_data=due_date)
    else:
        try:
            relative_id_payment = int(request.form.get("id_credit_card"))
            payments = get_ids_payment_type(db, CREDIT_CARD)
            if len(payments) <= relative_id_payment:
                raise Exception()
            id_payment = payments[relative_id_payment]
        except Exception as error:
            return ("Cartão inválido para edição!")
        
        payload = {
            "id" : id_payment,
            "name" : name,
            "balance" : initial_bill,
            "type" : CREDIT_CARD,
            "extra_data" : due_date
        }
        set_payment(db, **payload)
        return ("Alterado com sucesso! Recarregue a página", 200)
    return ("Adicionado com sucesso! Recarregue a página", 200)