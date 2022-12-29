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

function show_popup() {
    popup = document.getElementById("pop-up");
    popup.style["display"] = "flex";
}

function close_popup() {
    popup = document.getElementById("pop-up");
    popup.style["display"] = "none";
}

window.addEventListener("load", function() {
    // Events listener for the elements in the layout_page

    for (let dropbox of document.getElementsByClassName("dropbox")) {
        dropbox.addEventListener("mouseenter", dropbox_js);
        dropbox.addEventListener("mouseleave", dropbox_js);
    }
    for (let mob_dropbox of document.getElementsByClassName("mobile-dropbox")) {
        mob_dropbox.addEventListener("click", dropbox_js);
        mob_dropbox.addEventListener("click", dropbox_js);
    }
});