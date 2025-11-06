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
    updateInput(scanner, '#latitude', ['position', 'latitude'], 'string');
    updateInput(scanner, '#longitude', ['position', 'longitude'], 'string');
    updateInput(scanner, '#altitude', ['position', 'altitude']);
    updateInput(scanner, '#api_key', ['api_key'], 'string');

    $("#device_selector").empty();
    $("#ignored_frequencies").find("tr:gt(0)").remove();
    scanner['devices'].forEach(function (device) {
        addDevice(scanner, device);
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

function addDevice(scanner, device) {
    let d = document.createElement("div");
    $(d).addClass('form-check');

    let i = document.createElement("input");
    $(i).addClass('form-check-input');
    $(i).prop("type", "radio");
    $(i).prop("name", "device_selector");
    $(i).click(function () {
        selectDevice(scanner, device);
    });

    let l = document.createElement("label");
    $(l).addClass("form-check-label");
    $(l).append(device["driver"] + " - " + device["serial"]);
    $(l).click(function () {
        $(i).prop('checked', true);
        selectDevice(scanner, device);
    });

    $(d).append(i);
    $(d).append(l);

    if (device['connected']) {
        let a = document.createElement("span");
        $(a).addClass("mx-2");
        $(a).addClass("badge");
        $(a).addClass("bg-success");
        $(a).html("connected");
        $(d).append(a);
    }
    else {
        let a = document.createElement("span");
        $(a).addClass("mx-2");
        $(a).addClass("badge");
        $(a).addClass("bg-danger");
        $(a).html("not connected");
        $(d).append(a);
    }

    $("#device_selector").append(d);
}

function setValue(element, keys, value) {
    let current = element;
    for (let i = 0; i < keys.length - 1; i++) {
        const key = keys[i];
        if (!(key in current) || typeof current[key] !== 'object' || current[key] === null) {
            current[key] = {};
        }
        current = current[key];
    }
    current[keys[keys.length - 1]] = value;
}

function updateInput(element, element_id, keys, type = 'integer') {
    let value = element;
    keys.forEach(function (key) {
        value = value[key];
    });
    $(element_id).val(value);
    $(element_id).change(function () {
        setValue(element, keys, parseValue($(this).val(), type));
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

function selectDevice(scanner, device) {
    device['alias'] = '';
    if (device['connected']) {
        $("#device_section").show();
    }
    else {
        $("#device_section").hide();
    }

    let setInputsEnabled = function (enabled) {
        if (enabled)
            $("#device_settings").show();
        else
            $("#device_settings").hide();
    }

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
    $("#satellites").find("tr:gt(1)").remove();
    $("#gains").find("tr:gt(0)").remove();
    $("#crontab").find("tr:gt(1)").remove();

    device['ranges'].forEach(function (range) {
        addScannedFrequency(device['ranges'], range);
    });
    device['satellites'].forEach(function (satellite) {
        addSatellite(device['satellites'], satellite);
    });
    device['gains'].forEach(function (gain) {
        addGain(gain);
    });
    device['crontabs'].forEach(function (crontab) {
        addCrontab(device['crontabs'], crontab);
    });

    $("#new_scanned_frequency").unbind("click");
    $("#new_scanned_frequency").click(function () {
        device['ranges'].push({ 'start': 0, 'stop': 0 });
        let range = device['ranges'][device['ranges'].length - 1];
        addScannedFrequency(device['ranges'], range);
    });

    $("#new_satellite").unbind("click");
    $("#new_satellite").click(function () {
        device['satellites'].push({ 'id': 0, 'name': '', frequency: 0, bandwidth: 0, modulation: '' });
        let satellite = device['satellites'][device['satellites'].length - 1];
        addSatellite(device['satellites'], satellite);
    });
    $("#preview_satellites").unbind("click");
    $("#preview_satellites").click(function () {
        previewSatellites(scanner, device);
    });

    $("#new_crontab").unbind("click");
    $("#new_crontab").click(function () {
        device['crontabs'].push({ 'name': '', 'expression': '0 0 * * *', duration: 60, frequency: 0, bandwidth: 0, modulation: '' });
        let crontab = device['crontabs'][device['crontabs'].length - 1];
        addCrontab(device['crontabs'], crontab);
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

function addSatellite(satellites, satellite) {
    let tr = document.createElement("tr");
    $(tr).append(createInput(satellite['id'], function (value) {
        satellite['id'] = value;
    }));
    $(tr).append(createInput(satellite['name'], function (value) {
        satellite['name'] = value;
    }, "string"));
    $(tr).append(createInput(satellite['frequency'], function (value) {
        satellite['frequency'] = value;
    }));
    $(tr).append(createInput(satellite['bandwidth'], function (value) {
        satellite['bandwidth'] = value;
    }));
    $(tr).append(createInputSelect(satellite['modulation'], function (value) {
        satellite['modulation'] = value;
    }, "", ["AM", "FM", "Other"], "string"));
    $(tr).append(createButton("Delete", function () {
        let index = Array.prototype.indexOf.call($(tr).parent().children(), tr) - 1;
        index -= 1; // because help
        satellites.splice(index, 1);
        tr.remove();
    }));
    $("#satellites").append(tr);
}

function addGain(gain) {
    let tr = document.createElement("tr");
    $(tr).append(createLabel(gain["name"]));
    $(tr).append(createInput(gain["value"], function (value) {
        gain['value'] = value;
    }, 'float'));
    $(tr).append(createLabel(gain["min"]));
    $(tr).append(createLabel(gain["max"]));
    $(tr).append(createLabel(gain["step"]));
    $("#gains").append(tr);
}

function addCrontab(objects, object) {
    let tr = document.createElement("tr");
    $(tr).append(createInput(object['name'], function (value) {
        object['name'] = value;
    }, "string"));
    $(tr).append(createInput(object['expression'], function (value) {
        object['expression'] = value;
    }, "string"));
    $(tr).append(createInput(object['duration'], function (value) {
        object['duration'] = value;
    }, "integer"));
    $(tr).append(createInput(object['frequency'], function (value) {
        object['frequency'] = value;
    }));
    $(tr).append(createInput(object['bandwidth'], function (value) {
        object['bandwidth'] = value;
    }));
    $(tr).append(createInputSelect(object['modulation'], function (value) {
        object['modulation'] = value;
    }, "", ["AM", "FM", "Other"], "string"));
    $(tr).append(createButton("Delete", function () {
        let index = Array.prototype.indexOf.call($(tr).parent().children(), tr) - 1;
        index -= 1; // because help
        objects.splice(index, 1);
        tr.remove();
    }));
    $("#crontab").append(tr);
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

function createInputSelect(value, callback, label, options, type = 'integer') {
    let td = document.createElement("td");
    let i = document.createElement("select");
    let labelOption = document.createElement("option");
    $(labelOption).html(label);
    $(labelOption).attr('selected', '');
    $(labelOption).attr('disabled', '');
    $(labelOption).attr('hidden', '');
    i.append(labelOption);
    options.forEach(function (option) {
        let o = document.createElement("option");
        $(o).html(option);
        $(o).val(option);
        i.append(o);
    });
    $(i).val(value);
    $(i).addClass("form-select");
    $(i).addClass("form-control");
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

function previewSatellites(scanner, device) {
    let satellites = $.map(device['satellites'], function (value) {
        return value['id'] + ";" + value['name'];
    });
    $.ajax({
        dataType: "html",
        data: {
            "api_key": scanner['api_key'],
            "latitude": scanner['position']['latitude'],
            "longitude": scanner['position']['longitude'],
            "altitude": scanner['position']['altitude'],
            "satellites": satellites.join(","),
        },
        url: "/sdr/satellites/",
        success: function (data) {
            $("#preview_flights_content").html(data);
            $('#preview_flights').modal('show');
        }
    });
}
