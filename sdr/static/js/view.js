function addSelectOption(id, value) {
    $(id).append($('<option>', {
        value: value,
        text: value
    }));
}

function createLabel(value) {
    let td = document.createElement("td");
    td.append(value);
    return td;
}

function createInput(id, placeholder) {
    let td = document.createElement("td");
    let i = document.createElement("input");
    $(i).addClass("form-control");
    $(i).attr('id', id);
    $(i).attr('placeholder', placeholder);
    td.append(i);
    return td;
}