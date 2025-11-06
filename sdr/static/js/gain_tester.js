var scanners = {};

$(document).ready(function () {
    setWaiting(true);
    $('#scanner').on('change', () => selectScanner($(this).find(":selected").val()));
    if ($('#config').attr('mqtt_frontend_path')) {
        connect((window.location.protocol == 'http:' ? 'ws://' : 'wss://') + window.location.host + $('#config').attr('mqtt_frontend_path'));
    }
    else {
        connect($('#config').attr('mqtt_url'));
    }
});

function setWaiting(enabled) {
    if (enabled) {
        $("#waiting_section").show();
    }
    else {
        $("#waiting_section").hide();
    }
    $("#start").prop("disabled", enabled);
    $("#stop").prop("disabled", enabled);
    $("#status").prop("disabled", enabled);
}

function connect(url) {
    let client = mqtt.connect(url, { username: $('#config').attr('mqtt_user'), password: $('#config').attr('mqtt_password') });
    client.on("message", function (topic, message) {
        const values = topic.split("/");
        if (values[1] == 'gain_test' && values[4] == 'status') {
            setWaiting(false);
            const data = jQuery.parseJSON(new TextDecoder().decode(message));
            $("#status_content").html(data['message']);
            $('#status_modal').modal('show');
        }
        else if (values[1] == 'status') {
            const scanner = values[2];
            if (!(scanner in scanners)) {
                scanners[scanner] = jQuery.parseJSON(new TextDecoder().decode(message));
                addScanner(scanner);
            }
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

function addScanner(scanner) {
    $('#scanner').append($('<option>', {
        value: scanner,
        text: scanner
    }));
    $("#scanner").val('default');
}

function selectScanner(scanner) {
    $("#device").unbind("change");
    $("#device").find("option:gt(0)").remove();
    scanners[scanner]['devices'].forEach(function (device) {
        const name = device['driver'] + "_" + device['serial'];
        $('#device').append($('<option>', {
            value: name,
            text: name
        }));
    });
    $('#device').on('change', function () {
        $("#device option:selected").each(function () {
            selectDevice(scanner, $(this).text());
        });
    });
    $("#device").val('default');
}

function createLabel(value) {
    let td = document.createElement("td");
    td.append(value);
    return td;
}

function createInput(id) {
    let td = document.createElement("td");
    let i = document.createElement("input");
    $(i).addClass("form-control");
    $(i).attr('id', id);
    $(i).attr('placeholder', "Leave empty to test all values");
    td.append(i);
    return td;
}

function addGain(gain) {
    let tr = document.createElement("tr");
    $(tr).append(createLabel(gain["name"]));
    $(tr).append(createInput(gain["name"]));
    $(tr).append(createLabel(gain["min"]));
    $(tr).append(createLabel(gain["max"]));
    $(tr).append(createLabel(gain["step"]));
    $("#gains").append(tr);
}

function selectDevice(scanner, device_name) {
    scanners[scanner]['devices'].forEach(function (device) {
        const name = device['driver'] + "_" + device['serial'];
        if (device_name == name) {
            $("#gains").find("tr:gt(0)").remove();
            device['gains'].forEach(function (gain) {
                addGain(gain);
            });
        }
    });
}

function addGains(gains, key, value) {
    if (value) {
        gains[key] = value.split(/\s+/).map(Number);
    }
}

function sendStart(client) {
    const scanner = $('#scanner').val();
    const device_name = $('#device').val();
    let gains = {}
    scanners[scanner]['devices'].forEach(function (device) {
        const name = device['driver'] + "_" + device['serial'];
        if (device_name == name) {
            device['gains'].forEach(function (gain) {
                const id = `#${gain['name']}`
                const value = $(id).val()
                if (value) {
                    gains[gain['name']] = value.split(/\s+/).map(Number);
                }
            });
        }
    });
    config = {}
    config['name'] = $('#name').val();
    config['sample_rate'] = parseInt($('#sample_rate').val());
    config['frequency_range'] = { 'start': parseInt($('#range_start').val()), 'stop': parseInt($('#range_stop').val()) }
    config['duration'] = parseInt($('#duration').val());
    config['gains'] = gains
    setWaiting(true);
    client.publish(`sdr/gain_test/${scanner}/${device_name}/start`, JSON.stringify(config));
}

function sendStop(client) {
    const scanner = $('#scanner').val();
    const device = $('#device').val();
    setWaiting(true);
    client.publish(`sdr/gain_test/${scanner}/${device}/stop`);
}

function sendStatus(client) {
    const scanner = $('#scanner').val();
    const device = $('#device').val();
    setWaiting(true);
    client.publish(`sdr/gain_test/${scanner}/${device}/get_status`);
}

function onConnect(client) {
    setWaiting(false);
    client.subscribe("sdr/gain_test/+/+/status");
    client.subscribe("sdr/status/+");
    client.publish("sdr/list");

    $("#start").click(() => sendStart(client));
    $("#stop").click(() => sendStop(client));
    $("#status").click(() => sendStatus(client));
}
