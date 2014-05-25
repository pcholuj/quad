var net = require('net');
var joystick = new(require('joystick'))(0, 3500, 350);

var config = {
    host: '127.0.0.1',
    port: 3000
};

var Client = (function () {
    'use strict';

    function Client(options) {
        // enforces new
        if (!(this instanceof Client)) {
            return new Client(options);
        }
        var self = this;
        this.client = new net.Socket();


        this.client.connect(options.port, options.host, function () {
            self.bindJoy.call(self);
            setInterval(function () {
                self.sendRaw(105, 105);
            }, 1000);
        });

        this.client.on('data', function (data) {
            console.log(JSON.parse(data));
        });

    }

    Client.prototype.sendRaw = function (code, data) {
        this.client.write(JSON.stringify({
            action: 'raw',
            data: [code, data]
        }) + '\n');
    };

    Client.prototype.sendRc = function (data) {
        this.client.write(JSON.stringify({
            action: 'rc',
            data: data
        }) + '\n');
    };

    Client.prototype.bindJoy = function () {
        var self = this;

        joystick.on('axis', function (data) {
            if (data.number == 4 && data.type === 'axis') {
                if (data.value > 30000) {
                    data.value = 30000;
                }

                if (data.value < -30000) {
                    data.value = -30000;
                }

                self.sendRc({
                    yaw: parseInt(1500 - data.value / 60, 10)
                });
            }

            if (data.number == 3 && data.type === 'axis') {
                if (data.value > 30000) {
                    data.value = 30000;
                }

                if (data.value < -30000) {
                    data.value = -30000;
                }

                self.sendRc({
                    roll: parseInt(1500 - data.value / 60, 10)
                });
            }

            if (data.number == 0 && data.type === 'axis') {
                if (data.value > 30000) {
                    data.value = 30000;
                }

                if (data.value < -30000) {
                    data.value = -30000;
                }

                self.sendRc({
                    pitch: parseInt(1500 - data.value / 60, 10)
                });
            }

            if (data.number == 1 && data.type === 'axis') {
                if (data.value < -30000) {
                    data.value = -30000;
                }

                if (data.value > 0) {
                    data.value = 0;
                }

                self.sendRc({
                    throttle: parseInt(1000 - data.value / 30, 10)
                });
            }

            if (data.number == 2 && data.type === 'axis') {
                if (data.value > 30000) {
                    data.value = 30000;
                }

                if (data.value < -30000) {
                    data.value = -30000;
                }

                self.sendRc({
                    aux1: parseInt(1500 - data.value / 60, 10)
                });
            }
        });
    };

    return Client;

}());

new Client(config);