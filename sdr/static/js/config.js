var scanners = {};

$(document).ready(function () {
    if ($('#config').attr('mqtt_path')) {
        connect((window.location.protocol == 'http:' ? 'ws://' : 'wss://') + window.location.host + $('#config').attr('mqtt_path'));
    }
    else {
        connect((window.location.protocol == 'http:' ? 'ws://' : 'wss://') + window.location.hostname + ':' + $('#config').attr('mqtt_port'));
    }
    $("#expert_mode_checkbox").change(function () {
        if (this.checked) {
            $("#expert_mode_section").show();
        }
        else {
            $("#expert_mode_section").hide();
        }
    });
});

function connect(url) {
    let client = mqtt.connect(url, { username: $('#config').attr('mqtt_user'), password: $('#config').attr('mqtt_password') });
    client.on("message", function (topic, message) {
        let values = topic.split("/");
        let command = values[1];
        let scanner_id = values[2];
        if (command == 'status') {
            if (!(scanner_id in scanners)) {
                scanners[scanner_id] = jQuery.parseJSON(new TextDecoder().decode(message));
                addScanner(scanners[scanner_id]);
            }
        }
        else if (command == "config" && values[3] == "success") {
            $("#save").html("Save");
            $('#save_success').modal('show');
        }
    });

    client.on("connect", function () {
        console.log("connected to " + url);
        onConnect(client);
    });
    client.on("error", function () {
        client.end();
    });
    client.stream.on('error', function () {
        client.end();
    });
}

function onConnect(client) {
    client.subscribe("sdr/status/+");
    client.subscribe("sdr/config/+/success");
    client.publish("sdr/list");
    $("#save").click(function () {
        for (const [scanner_id, value] of Object.entries(scanners)) {
            client.publish("sdr/config/" + scanner_id, JSON.stringify(value));
        }
        $("#save").prop("disabled", true);
        $("#save").html("<span class=\"spinner-border spinner-border-sm\" aria-hidden=\"true\"></span><span role=\"status\">Loading...</span>");
    });
}

function parseValue(value, type) {
    if (type == 'string') {
        return value;
    }
    else if (type == 'float') {
        return parseFloat(value);
    }
    else if (type == 'bool') {
        return value.toLowerCase() === "true";
    }
    else {
        return parseInt(value);
    }
}

function addScanner(scanner) {
    let d = document.createElement("div");
    $(d).addClass('form-check');

    let i = document.createElement("input");
    $(i).addClass('form-check-input');
    $(i).prop("type", "radio");
    $(i).prop("name", "scanner_selector");
    $(i).click(function () {
        selectScanner(scanner);
    });

    let l = document.createElement("label");
    $(l).addClass("form-check-label");
    $(l).append("scanner #" + ($("#scanner_selector").children().length + 1));
    $(l).click(function () {
        $(i).prop('checked', true);
        selectScanner(scanner);
    });

    $(d).append(i);
    $(d).append(l);
    $("#scanner_selector").append(d);
}

function selectScanner(scanner) {
    updateInput(scanner, '#transmission_tunning_step', ['recording', 'step']);
    updateInput(scanner, '#transmission_max_noise_time_ms', ['recording', 'max_noise_time_ms']);
    updateInput(scanner, "#transmission_min_time_ms", ['recording', 'min_time_ms']);
    updateInput(scanner, "#transmission_sample_rate", ['recording', 'min_sample_rate']);
    updateInput(scanner, "#color_log_enabled", ['output', 'color_log_enabled'], 'bool');
    updateInput(scanner, "#console_log_level", ['output', 'console_log_level'], 'string');
    updateInput(scanner, "#file_log_level", ['output', 'file_log_level'], 'string');

    $("#device_selector").empty();
    $("#ignored_frequencies").find("tr:gt(0)").remove();
    scanner['scanned_frequencies'].forEach(function (device) {
        addDevice(device);
    });
    scanner['ignored_frequencies'].forEach(function (range) {
        addIgnoredFrequency(scanner['ignored_frequencies'], range);
    });
    $("#new_ignored_frequency").prop("disabled", false);
    $("#new_ignored_frequency").unbind("click");
    $("#new_ignored_frequency").click(function () {
        scanner['ignored_frequencies'].push({ 'frequency': 0, 'bandwidth': 0 });
        let range = scanner['ignored_frequencies'][scanner['ignored_frequencies'].length - 1];
        addIgnoredFrequency(scanner['ignored_frequencies'], range);
        $("#save").prop("disabled", false);
    });
    $("#device_enabled").prop("disabled", true);
    $("#device_sample_rate").prop("disabled", true);
    $("#new_scanned_frequency").prop("disabled", true);
}

function updateInput(scanner, element_id, keys, type = 'integer') {
    if (2 <= keys.length) { $(element_id).val(scanner[keys[0]][keys[1]]); }
    else { $(element_id).val(scanner[keys[0]]); }
    $(element_id).prop("disabled", false);
    $(element_id).change(function () {
        let value = parseValue($(this).val(), type)
        if (2 <= keys.length) { scanner[keys[0]][keys[1]] = value; }
        else { scanner[keys[0]] = value; }
        $("#save").prop("disabled", false);
    });
}

function addDevice(device) {
    let d = document.createElement("div");
    $(d).addClass('form-check');

    let i = document.createElement("input");
    $(i).addClass('form-check-input');
    $(i).prop("type", "radio");
    $(i).prop("name", "device_selector");
    $(i).click(function () {
        selectDevice(device);
    });

    let l = document.createElement("label");
    $(l).addClass("form-check-label");
    $(l).append(device["device_driver"] + " - " + device["device_serial"]);
    $(l).click(function () {
        $(i).prop('checked', true);
        selectDevice(device);
    });

    $(d).append(i);
    $(d).append(l);

    $("#device_selector").append(d);
    $("#scanned_frequencies").find("tr:gt(0)").remove();
    $("#gains").find("tr:gt(0)").remove();
}

function addIgnoredFrequency(ranges, range) {
    let tr = document.createElement("tr");
    $(tr).append(createInput(range['frequency'], function (value) {
        range['frequency'] = value;
        $("#save").prop("disabled", false);
    }));
    $(tr).append(createInput(range['bandwidth'], function (value) {
        range['bandwidth'] = value;
        $("#save").prop("disabled", false);
    }));
    $(tr).append(createButton("Delete", function () {
        let index = Array.prototype.indexOf.call($(tr).parent().children(), tr) - 1;
        ranges.splice(index, 1);
        tr.remove();
        $("#save").prop("disabled", false);
    }));
    $("#ignored_frequencies").append(tr);
}

function selectDevice(device) {
    let setInputsEnabled = function (enabled) {
        $("#device_sample_rate").prop("disabled", !enabled);
        $("#scanned_frequencies :input").prop("disabled", !enabled);
        $("#gains :input").prop("disabled", !enabled);
    };

    $("#device_enabled").prop("checked", device["device_enabled"]);
    $("#device_enabled").prop("disabled", false);
    $("#device_enabled").unbind("click");
    $("#device_enabled").click(function () {
        device['device_enabled'] = $(this).is(':checked');
        setInputsEnabled($(this).is(':checked'));
        $("#save").prop("disabled", false);
    });

    $("#device_sample_rate").unbind("click");
    $("#device_sample_rate").empty();
    device['device_sample_rates'].forEach(function (sample_rate) {
        $("#device_sample_rate").append(new Option(sample_rate, sample_rate));
    });
    $("#device_sample_rate").val(device['device_sample_rate']);
    $("#device_sample_rate").change(function () {
        device['device_sample_rate'] = parseInt($(this).val());
        $("#save").prop("disabled", false);
    });

    $("#scanned_frequencies").find("tr:gt(0)").remove();

    $("#gains").find("tr:gt(0)").remove();
    device['ranges'].forEach(function (range) {
        addScannedFrequency(device['ranges'], range);
    });
    device['device_gains'].forEach(function (gain) {
        addGain(gain);
    });

    $("#new_scanned_frequency").unbind("click");
    $("#new_scanned_frequency").click(function () {
        device['ranges'].push({ 'start': 0, 'stop': 0 });
        let range = device['ranges'][device['ranges'].length - 1];
        addScannedFrequency(device['ranges'], range);
        $("#save").prop("disabled", false);
    });

    setInputsEnabled(device["device_enabled"]);
}

function addScannedFrequency(ranges, range) {
    let tr = document.createElement("tr");
    $(tr).append(createInput(range['start'], function (value) {
        range['start'] = value;
    }));
    $(tr).append(createInput(range['stop'], function (value) {
        range['stop'] = value;
    }));
    $(tr).append(createButton("Delete", function () {
        let index = Array.prototype.indexOf.call($(tr).parent().children(), tr) - 1;
        ranges.splice(index, 1);
        tr.remove();
        $("#save").prop("disabled", false);
    }));
    $("#scanned_frequencies").append(tr);
}

function addGain(gain) {
    let tr = document.createElement("tr");
    $(tr).append(createLabel(gain["name"]));
    $(tr).append(createInput(gain["value"], function (value) {
        gain['value'] = value;
    }, 'float'));
    $("#gains").append(tr);
}

function createLabel(value) {
    let td = document.createElement("td");
    td.append(value);
    return td;
}

function createInput(value, callback, type = 'integer') {
    let td = document.createElement("td");
    let i = document.createElement("input");
    $(i).addClass("form-control");
    $(i).val(value);
    $(i).change(function () {
        callback(parseValue($(this).val(), type));
        $("#save").prop("disabled", false);
    });
    td.append(i);
    return td;
}

function createButton(value, callback) {
    let td = document.createElement("td");
    let b = document.createElement("button");
    $(b).addClass("btn");
    $(b).addClass("btn-danger");
    $(b).attr("type", "button");
    $(b).append(value);
    $(b).click(callback);
    td.append(b)
    return td;
}
