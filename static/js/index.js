function reset_border(section) {
    for (let i = 0; i < 4; i++) {
        section.children[i].style["border"] = "0.5px solid black";
    }
}

function merge_border() {
    let balance_section = document.getElementById("balances");

    reset_border(balance_section);
    if (window.matchMedia("(max-width:610px)").matches) {
        for (let i = 0; i < 2; i++) {
            balance_section.children[i].style["border-bottom"] = "0";
        }
        for (let i = 0; i < 3; i+=2) {
            balance_section.children[i].style["border-right"] = "0";
        }
    } else {
        for (let i = 0; i < 3; i++) {
            balance_section.children[i].style["border-right"] = "0";
        }
    }
}

window.addEventListener("load", function() {
    merge_border();
    window.addEventListener("resize", merge_border);
});