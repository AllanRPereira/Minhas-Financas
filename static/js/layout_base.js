function dropbox_js(event) {    
    // Function that show and hide the elements of a dropbox
    let list;
    if (event.target.tagName == "DIV") {
        list = event.target.children;
    } else {
        list = event.target.parentElement.children;
    }
    for (let element of list) {
        if (element.style["display"] != "none" && !element.className.includes("header")) {
            element.style["display"] = "none";
        } else {
            element.style["display"] = "flex";
        }
    }
}

function show(element) {
    // Function that show/hidden the nav mobile dropbox by the clicking on the button

    let id = element.attributes.for.value;
    let drop_nav = document.getElementById(id);
    if (drop_nav.className == 'show') {
        drop_nav.className = '';
    } else {
        drop_nav.className = 'show';
    }
}

function set_value(id, element) {
    // Seta um valor para o atributo value do elemento com o id recebeido
    // Obtém o valor do id do element

    let input_selected = document.getElementById(id);
    input_selected.value = element.id;
}

let older_popup = "";
let opened_popup = "";
function show_popup(element="", id="") {
    // Função utilizada para exibir uma mensagem que abrange a tela
    // Utilizada para exibir os formulários de adicionar (Cartão, Inves, ...)
    if (id == "") {
        popup = document.getElementById(`${element.attributes['value'].value}-pop-up`);
    } else {
        popup = document.getElementById(id)
    }
    popup.style["display"] = "flex";
    if (opened_popup != "") {
        older_popup = opened_popup;
    }
    opened_popup = popup;
}

function close_popup() {
    // Função que esconde a atual popup aberta

    if (opened_popup != "") {
        opened_popup.style["display"] = "none";
    }
}

function change_popup(id_popup) {
    // Função que altera entre duas popups

    if (opened_popup != "") {
        close_popup();
    }
    if (id_popup == "comeback") {
        let temp = older_popup;
        opened_popup = "";
        older_popup = "";
        show_popup("", temp.id);
    } else {
        show_popup("", id_popup);
    }
}

function show_message(message, code) {
    // Função que configura uma mensagem para ser exibida como popup na tela
    // Utilizada para exibir respostas de requisições fetch na aplicação

    title = document.getElementById("title-message");
    p_message = document.getElementById("popup-message");
    alert_message = document.getElementById("alert-message");
    if (code == 200) {
        alert_message.className = "green";
        update_options();
    } else {
        alert_message.className = "red";
    }
    title.textContent = "Resultado da operação"
    p_message.textContent = message;
    change_popup("message-pop-up");
}
function update_options() {
    // Função para atualizar as opções de Income e Teller de um usuário.
    // Utilizada após adicionar um novo Income ou Teller.

    let dictionary = {
        to_options : "to_select",
        from_options : "from_select",
        teller_category : "to_category_select",
        income_category : "from_category_select"
    };
    fetch("/get_options", {
        method : "GET"
    }).then(function(response) {
        response.json().then(function(elements) {
            for (var key of Object.keys(dictionary)) {
                let array_elements = elements[key];
                let id = dictionary[key];
                let select = document.getElementById(id);
                let size = select.children.length;
                // Remove as opções alteriores
                for (let i = 1, c = 1; i < size; i++) {
                    select.removeChild(select.children[c]);
                }

                // Adiciona as novas obtidas.
                for (var value of array_elements) {
                    let element = document.createElement("option");

                    // Capitalizar o nome da opção
                    value = value.charAt(0).toUpperCase() + value.toLowerCase().slice(1);
                    element.value = value;
                    element.textContent = value;
                    select.appendChild(element);
                }
            }
        });
    });
}

function input_color_money(event) {
    // Função usada para alterar a cor de um input monetário dependendo do saldo

    let input = event.target;
    let label = input.nextElementSibling;
    let number_value = Number(input.value);
    if (Object.is(number_value, NaN)) {
        label.hidden=false;
    } else {
        if (number_value > 0) {
            input.style["background-color"] = "rgba(68, 189, 50, 0.5)";
            input.style["border-bottom"] = "2px solid #4cd137";
            input.style["outline"] = "0.5px solid #4cd137";
            input.onfocus = function () {
                input.style["outline"] = "0.5px solid #4cd137";
            }
        } else if (number_value == 0) {
            input.style["background-color"] = "";
            input.style["border-bottom"] = "";
            input.style["outline"] = "";
            input.onfocus = "";
        } else {
            input.style["background-color"] = "rgba(232, 65, 24, 0.5)";
            input.style["border-bottom"] = "2px solid #c23616";
            input.style["outline"] = "0.5px solid #c23616";
            input.onfocus = function () {
                input.style["outline"] = "0.5px solid #c23616";
            }
        }
        if (label.hidden == false) {
            label.hidden = true;
        }
    }
    input.onblur = function() {
        input.style["outline"] = "";
    }
}

function transfer(button) {
    // Função para redirecionar de página
    window.location.assign(button.attributes.href.value);
}

window.addEventListener("load", function() {
    // Momento de adicionar os Listeners da aplicação

    // Todos os forms que possuem essa classe enviam as informações
    // de uma forma assíncrona. O link é o próprio action do form
    forms = document.getElementsByClassName("onformsubmit");
    for (let form of forms) {
        let url_form = form.action;
        form.onsubmit = async function(event) {
            event.preventDefault();
            let responseAdd = fetch(url_form, {
                method : "POST",
                body :  new FormData(form)
            });
    
            let result = await responseAdd;
            let message = await result.text();
            show_message(message, result.status);
        }
    }

    inputs_color_money = document.getElementsByClassName("color_money_listener");
    for (let input of inputs_color_money) {
        input.addEventListener("keyup", function(event) {
            return input_color_money(event);
        });
    }

    // Tecla para fechar popups
    window.addEventListener("keyup", function(event) {
        if (event.key === "Escape") {
            close_popup();
        }
    });

    for (let dropbox of document.getElementsByClassName("dropbox")) {
        dropbox.addEventListener("mouseover", dropbox_js);
        dropbox.addEventListener("mouseout", dropbox_js);
    }
    for (let mob_dropbox of document.getElementsByClassName("mobile-dropbox")) {
        mob_dropbox.addEventListener("click", dropbox_js);
    }
});