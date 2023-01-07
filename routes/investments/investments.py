from flask import Blueprint, render_template, request
from utils import login_required, format_number, check_name
from model.database import add_payment, set_payment, get_options, get_db, get_data_payment, get_ids_payment_type
from consts import INVESTMENTS
from datetime import datetime

invest_page = Blueprint("invest_page", __name__, template_folder="../../templates")

@invest_page.route("/investiments", methods=["GET"])
@login_required
def investiments():
    # Rota utilizada para exibir os investimentos de um usuário

    db = get_db()
    investments = get_data_payment(db, INVESTMENTS)
    options = get_options(db)
    return render_template("main/investiments.html", investments=investments, **options)

@invest_page.route("/<string:operation>/investiment", methods=["POST"])
@login_required
def operator_investiment(operation):
    # Rota utilizada pelo layout.js para adicionar um novo investimento para um usuário

    if operation not in ("add", "set"):
        return "Url é inválida", 404

    name = request.form.get("name")
    rendiment = request.form.get("rendiment").replace("%", "").replace(",", ".")
    current_amount = format_number(request.form.get("current_amount"))
    status, content = check_name(name)
    if not status:
        return content

    try:
        rendiment = float(rendiment)
        current_amount = float(current_amount)
    except ValueError:
        return ("Rendimento e quantidade devem ser número", 400)
    
    db = get_db()
    if operation == "add":
        add_payment(db, name, current_amount, INVESTMENTS, extra_data=rendiment)
    else:
        try:
            relative_id_payment = int(request.form.get("id_investiment"))
            payments = get_ids_payment_type(db, INVESTMENTS)
            if len(payments) <= relative_id_payment:
                raise Exception()
            id_payment = payments[relative_id_payment]
        except Exception as error:
            print(error)
            return ("Investimento inválido para edição!")
        
        payload = {
            "id" : id_payment,
            "name" : name,
            "balance" : current_amount,
            "type" : INVESTMENTS,
            "extra_data" : rendiment
        }
        set_payment(db, **payload)
        return ("Alterado com sucesso! Recarregue a página", 200)

    return ("Adicionado com sucesso! Recarregue a página", 200)
