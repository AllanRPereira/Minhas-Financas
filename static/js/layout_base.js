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

let opened_popup = "";
function show_popup(element) {
    popup = document.getElementById(`${element.attributes['value'].value}-pop-up`);
    popup.style["display"] = "flex";
    opened_popup = popup;
}

function show_popup_by_id(id) {
    popup = document.getElementById(id)
    popup.style["display"] = "flex";
    opened_popup = popup;
}

function close_popup() {
    if (opened_popup != "") {
        opened_popup.style["display"] = "none";
        opened_popup = "";
    }
}

function change_popup(id_popup) {
    if (opened_popup != "") {
        close_popup();
    }
    show_popup_by_id(id_popup);
}

function show_message(message, code) {
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
    let elements;
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
                for (let i = 1, c = 1; i < size; i++) {
                    select.removeChild(select.children[c]);
                }

                for (var value of array_elements) {
                    let element = document.createElement("option");
                    value = value.charAt(0).toUpperCase() + value.toLowerCase().slice(1);
                    element.value = value;
                    element.textContent = value;
                    select.appendChild(element);
                }
            }
        });
    });
}

window.addEventListener("load", function() {
    // Events listener for the elements in the layout_page

    forms = document.getElementsByClassName("onformsubmit");
    for (var form of forms) {
        url_form = form.action;
        form.onsubmit = async function(event) {
            event.preventDefault();
            let responseAdd = fetch(url_form, {
                method : "POST",
                body :  new FormData(fromForm)
            });
    
            let result = await responseAdd;
            let message = await result.text();
            show_message(message, result.status);
        }
    }

    window.addEventListener("keyup", function(event) {
        if (event.key === "Escape") {
            close_popup();
        }
    });

    for (let dropbox of document.getElementsByClassName("dropbox")) {
        dropbox.addEventListener("mouseenter", dropbox_js);
        dropbox.addEventListener("mouseleave", dropbox_js);
    }
    for (let mob_dropbox of document.getElementsByClassName("mobile-dropbox")) {
        mob_dropbox.addEventListener("click", dropbox_js);
        mob_dropbox.addEventListener("click", dropbox_js);
    }
});