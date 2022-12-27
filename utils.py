from functools import wraps
from flask import session, redirect

def login_required(function):

    @wraps(function)
    def requisition_login(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return function(*args, **kwargs)
    
    return requisition_login

def brl(string):
    return f"R$ {string:.2f}"

def check_email(email):
    if email.find("@") == -1:
        return False
    return True