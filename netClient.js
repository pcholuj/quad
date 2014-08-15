var net = require('net');
var XboxController = require('xbox-controller');
var xbox = new XboxController();
console.log('started');
var config = {
    host: '192.168.1.139',
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
        self.button = {
            aux1: false,
            aux2: false,
            aux3: false,
            aux4: false
        };

        self.armed = false;

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

        xbox.on('left:move', function (data) {
            if (data.x > 30000) {
                data.x = 30000;
            }

            if (data.x < -30000) {
                data.x = -30000;
            }

            self.sendRc({
                pitch: parseInt(1500 - data.x / 60, 10)
            });
        });

        xbox.on('y:press', function (key) {
            self.aux1 = self.aux1 ? false : true;
            self.sendRc({
                aux1: self.aux1 ? 1000 : 2000
            });
        });

        xbox.on('b:press', function (key) {
            self.aux2 = self.aux1 ? false : true;
            self.sendRc({
                aux2: self.aux2 ? 1000 : 2000
            });
        });

        xbox.on('a:press', function (key) {
            self.aux3 = self.aux3 ? false : true;
            self.sendRc({
                aux3: self.aux3 ? 1000 : 2000
            });
        });

        xbox.on('x:press', function (key) {
            self.aux4 = self.aux4 ? false : true;
            self.sendRc({
                aux4: self.aux4 ? 1000 : 2000
            });
        });

        xbox.on('right:move', function (data) {
            if (data.x > 30000) {
                data.x = 30000;
            }

            if (data.x < -30000) {
                data.x = -30000;
            }

            if (data.y > 30000) {
                data.y = 30000;
            }

            if (data.y < -30000) {
                data.y = -30000;
            }

            self.sendRc({
                roll: parseInt(1500 - data.x / 60, 10),
                yaw: parseInt(1500 - data.x / 60, 10)
            });
        });


        xbox.on('lefttrigger', function (position) {
            self.sendRc({
                throttle: parseInt(1000 + (position * 4), 10)
            });
        });
    };

    return Client;

}());

new Client(config);