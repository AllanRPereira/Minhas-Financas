from flask import Blueprint, render_template, request
from utils import login_required, format_number, check_name
from model.database import add_payment, set_payment, get_options, get_db, get_data_payment, get_ids_payment_type
from consts import DEBTS
from datetime import datetime

debt_page = Blueprint("debt_page", __name__, template_folder="../../templates")

@debt_page.route("/debts", methods=["GET"])
@login_required
def debts():
    # Rota utilizada para visualizar as dívidas de um usuário

    db = get_db()
    debts = get_data_payment(db, DEBTS)
    options = get_options(db)
    return render_template("main/debts.html", debts=debts, **options)

@debt_page.route("/<string:operation>/debt", methods=["POST"])
@login_required
def operator_debt(operation):
    # Rota utilizado pelo layout.js para adicionar uma nova dívida

    if operation not in ("add", "set"):
        return ("Url é inválida", 404)

    name = request.form.get("name")
    date_debt = request.form.get("debt_date")
    current_amount = format_number(request.form.get("debt_value"))
    status, content = check_name(name)
    if not status:
        return content

    try:
        current_amount = float(current_amount)
    except ValueError:
        return ("Rendimento deve conter apenas números e pontos", 400)
    
    try:
        date_debt = round(datetime.fromisoformat(date_debt).timestamp(), 0)
    except Exception as error:
        return ("Campo de data não é valido "+ str(error), 400)
    
    
    db = get_db()
    if operation == "add":
        add_payment(db, name, current_amount, DEBTS, extra_data=date_debt)
    else:
        try:
            relative_id_payment = int(request.form.get("id_debt"))
            payments = get_ids_payment_type(db, DEBTS)
            if len(payments) <= relative_id_payment:
                raise Exception()
            id_payment = payments[relative_id_payment]
        except Exception as error:
            return ("Dívida inválida para edição!")
        
        payload = {
            "id" : id_payment,
            "name" : name,
            "balance" : current_amount,
            "type" : DEBTS,
            "extra_data" : date_debt
        }
        set_payment(db, **payload)
        return ("Alterado com sucesso! Recarregue a página", 200)
    return ("Adicionado com sucesso! Recarregue a página", 200)
