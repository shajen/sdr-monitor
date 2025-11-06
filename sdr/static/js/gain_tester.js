var scanners = {};

$(document).ready(function () {
    setWaiting(true);
    $('#scanner').on('change', () => selectScanner($(this).find(":selected").val()));
    connect(onConnect, onMessage);
});

function setWaiting(enabled) {
    $("#waiting_section").toggle(enabled);
    $("#start").prop("disabled", enabled);
    $("#stop").prop("disabled", enabled);
    $("#status").prop("disabled", enabled);
}

function clearGains() {
    $("#gains").find("tr:gt(0)").remove();
}

function clearSampleRates() {
    $("#sample_rate").find("tr:gt(0)").remove();
}

function clearDevices() {
    clearGains();
    clearSampleRates();
    $("#device").find("option:gt(0)").remove();
}

function addGain(gain) {
    let tr = document.createElement("tr");
    $(tr).append(createLabel(gain["name"]));
    $(tr).append(createInput(gain["name"], "Leave empty to test all values"));
    $(tr).append(createLabel(gain["min"]));
    $(tr).append(createLabel(gain["max"]));
    $(tr).append(createLabel(gain["step"]));
    $("#gains").append(tr);
}

function runDevice(scanner, device, callback) {
    scanners[scanner]['devices'].forEach(function (_device) {
        const name = _device['driver'] + "_" + _device['serial'];
        if (device == name) {
            callback(_device);
        }
    });
}

function addScanner(scanner) {
    addSelectOption('#scanner', scanner);
    $("#scanner").val('default');
}

function selectScanner(scanner) {
    $("#device").unbind("change");
    clearDevices();
    scanners[scanner]['devices'].forEach((device) => addSelectOption('#device', device['driver'] + "_" + device['serial']));
    $('#device').on('change', function () {
        $("#device option:selected").each(function () {
            selectDevice(scanner, $(this).text());
        });
    });
    $("#device").val('default');
}

function selectDevice(scanner, device) {
    runDevice(scanner, device, function (_device) {
        clearGains();
        clearSampleRates();
        _device['gains'].forEach((gain) => addGain(gain));
        _device['sample_rates'].forEach((sample_rate) => addSelectOption('#sample_rate', sample_rate));
    });
}

function sendStart(client) {
    const scanner = $('#scanner').val();
    const device = $('#device').val();
    let gains = {}
    runDevice(scanner, device, function (_device) {
        _device['gains'].forEach(function (gain) {
            const id = `#${gain['name']}`
            const value = $(id).val()
            if (value) {
                gains[gain['name']] = value.split(/\s+/).map(Number);
            }
        });
    });
    config = {}
    config['name'] = $('#name').val();
    config['sample_rate'] = parseInt($('#sample_rate').val());
    config['frequency_range'] = { 'start': parseInt($('#range_start').val()), 'stop': parseInt($('#range_stop').val()) }
    config['duration'] = parseInt($('#duration').val());
    config['gains'] = gains
    setWaiting(true);
    client.publish(`sdr/gain_test/${scanner}/${device}/start`, JSON.stringify(config));
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

function onMessage(topic, message) {
    const values = topic.split("/");
    if (values[1] == 'gain_test' && values[4] == 'status') {
        setWaiting(false);
        const data = jQuery.parseJSON(message);
        $("#status_content").html(data['message']);
        $('#status_modal').modal('show');
    }
    else if (values[1] == 'status') {
        const scanner = values[2];
        if (!(scanner in scanners)) {
            scanners[scanner] = jQuery.parseJSON(message);
            addScanner(scanner);
        }
    }
}
