var scanners = {};

$(document).ready(function () {
    if ($('#config').attr('mqtt_frontend_path')) {
        connect((window.location.protocol == 'http:' ? 'ws://' : 'wss://') + window.location.host + $('#config').attr('mqtt_frontend_path'));
    }
    else {
        connect($('#config').attr('mqtt_url'));
    }
});

function connect(url) {
    let client = mqtt.connect(url, { username: $('#config').attr('mqtt_user'), password: $('#config').attr('mqtt_password') });
    client.on("message", function (topic, message) {
        let values = topic.split("/");
        let command = values[1];
        let scanner_id = values[2];
        if (command == 'status') {
            $("#loading_section").hide();
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
    $("#scanner_section").show();
    $("#device_section").hide();
    $("#save").prop("disabled", false);
    updateInput(scanner, '#transmission_tunning_step', ['recording', 'step']);
    updateInput(scanner, '#transmission_max_noise_time_ms', ['recording', 'max_noise_time_ms']);
    updateInput(scanner, "#transmission_min_time_ms", ['recording', 'min_time_ms']);
    updateInput(scanner, "#transmission_sample_rate", ['recording', 'min_sample_rate']);
    updateInput(scanner, "#color_log_enabled", ['output', 'color_log_enabled'], 'bool');
    updateInput(scanner, "#console_log_level", ['output', 'console_log_level'], 'string');
    updateInput(scanner, "#file_log_level", ['output', 'file_log_level'], 'string');
    updateInput(scanner, "#workers", ['workers']);
    updateInput(scanner, '#latitude', ['position', 'latitude'], 'float');
    updateInput(scanner, '#longitude', ['position', 'longitude'], 'float');
    updateInput(scanner, '#altitude', ['position', 'altitude'], 'float');
    updateInput(scanner, '#api_key', ['api_key'], 'string');

    $("#device_selector").empty();
    $("#ignored_frequencies").find("tr:gt(0)").remove();
    scanner['devices'].forEach(function (device) {
        addDevice(device);
    });
    scanner['ignored_frequencies'].forEach(function (range) {
        addIgnoredFrequency(scanner['ignored_frequencies'], range);
    });
    $("#new_ignored_frequency").unbind("click");
    $("#new_ignored_frequency").click(function () {
        scanner['ignored_frequencies'].push({ 'frequency': 0, 'bandwidth': 0 });
        let range = scanner['ignored_frequencies'][scanner['ignored_frequencies'].length - 1];
        addIgnoredFrequency(scanner['ignored_frequencies'], range);
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
    $(l).append(device["driver"] + " - " + device["serial"]);
    $(l).click(function () {
        $(i).prop('checked', true);
        selectDevice(device);
    });

    $(d).append(i);
    $(d).append(l);

    $("#device_selector").append(d);
}

function updateInput(element, element_id, keys, type = 'integer') {
    if (2 <= keys.length) { $(element_id).val(element[keys[0]][keys[1]]); }
    else { $(element_id).val(element[keys[0]]); }
    $(element_id).change(function () {
        let value = parseValue($(this).val(), type)
        if (2 <= keys.length) { element[keys[0]][keys[1]] = value; }
        else { element[keys[0]] = value; }
    });
}

function addIgnoredFrequency(ranges, range) {
    let tr = document.createElement("tr");
    $(tr).append(createInput(range['frequency'], function (value) {
        range['frequency'] = value;
    }));
    $(tr).append(createInput(range['bandwidth'], function (value) {
        range['bandwidth'] = value;
    }));
    $(tr).append(createButton("Delete", function () {
        let index = Array.prototype.indexOf.call($(tr).parent().children(), tr) - 1;
        ranges.splice(index, 1);
        tr.remove();
    }));
    $("#ignored_frequencies").append(tr);
}

function selectDevice(device) {
    let setInputsEnabled = function (enabled) {
        if (enabled)
            $("#device_settings").show();
        else
            $("#device_settings").hide();
    }

    $("#device_section").show();
    $("#device_enabled").prop("checked", device["enabled"]);
    $("#device_enabled").unbind("click");
    $("#device_enabled").click(function () {
        device['enabled'] = $(this).is(':checked');
        setInputsEnabled($(this).is(':checked'));
    });

    $("#device_sample_rate").unbind("click");
    $("#device_sample_rate").empty();
    device['sample_rates'].forEach(function (sample_rate) {
        $("#device_sample_rate").append(new Option(sample_rate, sample_rate));
    });
    $("#device_sample_rate").val(device['sample_rate']);
    $("#device_sample_rate").change(function () {
        device['sample_rate'] = parseInt($(this).val());
    });

    $("#devices").find("tr:gt(0)").remove();
    $("#sattelites").find("tr:gt(1)").remove();
    $("#gains").find("tr:gt(0)").remove();

    device['ranges'].forEach(function (range) {
        addScannedFrequency(device['ranges'], range);
    });
    device['sattelites'].forEach(function (sattelite) {
        addSattelite(device['sattelites'], sattelite);
    });
    device['gains'].forEach(function (gain) {
        addGain(gain);
    });

    $("#new_scanned_frequency").unbind("click");
    $("#new_scanned_frequency").click(function () {
        device['ranges'].push({ 'start': 0, 'stop': 0 });
        let range = device['ranges'][device['ranges'].length - 1];
        addScannedFrequency(device['ranges'], range);
    });

    $("#new_sattelite").unbind("click");
    $("#new_sattelite").click(function () {
        device['sattelites'].push({ 'id': 0, 'name': '', frequency: 0, bandwidth: 0, modulation: '' });
        let sattelite = device['sattelites'][device['sattelites'].length - 1];
        addSattelite(device['sattelites'], sattelite);
    });

    updateInput(device, '#start_recording_level', ['start_recording_level']);
    updateInput(device, '#stop_recording_level', ['stop_recording_level']);
    setInputsEnabled(device["enabled"]);
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
    }));
    $("#devices").append(tr);
}

function addSattelite(sattelites, sattelite) {
    let tr = document.createElement("tr");
    $(tr).append(createInput(sattelite['id'], function (value) {
        sattelite['id'] = value;
    }));
    $(tr).append(createInput(sattelite['name'], function (value) {
        sattelite['name'] = value;
    }));
    $(tr).append(createInput(sattelite['frequency'], function (value) {
        sattelite['frequency'] = value;
    }));
    $(tr).append(createInput(sattelite['bandwidth'], function (value) {
        sattelite['bandwidth'] = value;
    }));
    $(tr).append(createInput(sattelite['modulation'], function (value) {
        sattelite['modulation'] = value;
    }));
    $(tr).append(createButton("Delete", function () {
        let index = Array.prototype.indexOf.call($(tr).parent().children(), tr) - 1;
        index -= 1; // because help
        sattelites.splice(index, 1);
        tr.remove();
    }));
    $("#sattelites").append(tr);
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
