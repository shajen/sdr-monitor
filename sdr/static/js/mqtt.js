function getUrl() {
    if ($('#config').attr('mqtt_frontend_path')) {
        return (window.location.protocol == 'http:' ? 'ws://' : 'wss://') + window.location.host + $('#config').attr('mqtt_frontend_path');
    }
    else {
        return $('#config').attr('mqtt_url');
    }
}

function connect(_onConnect, _onMessage) {
    const url = getUrl()
    let client = mqtt.connect(url, { username: $('#config').attr('mqtt_user'), password: $('#config').attr('mqtt_password') });
    client.on("connect", function () {
        console.log("connected to " + url);
        _onConnect(client);
    });
    client.on("message", function (topic, message) {
        _onMessage(topic, new TextDecoder().decode(message));
    });
    client.on("error", function () {
        client.end();
    });
    client.stream.on('error', function () {
        client.end();
    });
}