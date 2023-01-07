function dropbox_js(event) {    
    // Function that show and hide the elements of a dropbox
    let list;
    if (event.target.tagName == "DIV") {
        list = event.target.children;
    } else if (event.target.tagName == "I") {
        // No caso de clicar no ícone na barra de navegação
        list = event.target.parentElement.parentElement.children;
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

function set_value({id, element} = {}) {
    // Seta um valor para o atributo value do elemento com o id recebeido
    // Obtém o valor do id do element

    let input_selected = document.getElementById(id);
    input_selected.value = element.getAttribute("data-id");
}

let queue = [];
function insert_queue(element) {
    if (queue.length < 5) {
        queue.push(element);
    } else {
        queue.shift();
        queue.push(element);
    }
}

function delete_last_queue() {
    return queue.pop();    
}

function get_last_queue() {
    let position = queue.length - 1;
    if (position >= 0) {
        return queue[position];
    } else {
        return "";
    }
} 

function show_popup({element, id, object} = {}) {
    // Função utilizada para exibir uma mensagem que abrange a tela
    // Utilizada para exibir os formulários de adicionar (Cartão, Investimentos, ...)

    if (id != undefined) {
        popup = document.getElementById(id);
    } else if (element != undefined) {
        popup = document.getElementById(`${element.getAttribute("data-popup-input")}-pop-up`);   
    } else if (object != undefined) {
        popup = object;
    } else {
        return false;
    }
    popup.style["display"] = "flex";
    insert_queue(popup);
}

function close_popup() {
    // Função que esconde a atual popup aberta
    element = get_last_queue();
    if (element) {
        element.style["display"] = "None";
    }
}

function change_popup(id_popup) {
    // Função que altera entre duas popups

    if (get_last_queue()) {
        close_popup();
    }
    if (id_popup == "comeback") {
        delete_last_queue(); // Elimina a mensagem
        delete_last_queue(); // Elimina o subform
        let popup = get_last_queue(); // Form principal
        show_popup({object:popup});
    } else {
        show_popup({id:id_popup});
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
    fetch("/js/options", {
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

    update_options();

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
        dropbox.addEventListener("click", dropbox_js);
    }
    for (let mob_dropbox of document.getElementsByClassName("mobile-dropbox")) {
        mob_dropbox.addEventListener("click", dropbox_js);
    }
});