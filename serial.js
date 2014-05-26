var serialport = require("serialport");
var SerialPort = serialport.SerialPort; // localize object constructor
var msp = require('./msp.js');
var joystick = new(require('joystick'))(0, 3500, 350);

var Copter = (function () {

    function Copter(args) {
        // enforces new
        if (!(this instanceof Copter)) {
            return new Copter(args);
        }
        var self = this;

        self.msp = new msp.protocol();
        self.rc = {
            roll: 1500,
            pitch: 1500,
            yaw: 1500,
            throttle: 1500,
            aux1: 1500,
            aux2: 1500,
            aux3: 1500,
            aux4: 1500
        };

        this.port = new SerialPort("/dev/ttyUSB0", {
            baudrate: 115200,
            databits: 8,
            stopbits: 1,
            parity: 'none',
            parser: serialport.parsers.raw
        }, false);

        var prepare = function () {
            var buf = new Buffer(16);
            buf.writeUInt16LE(self.rc.roll, 0);
            buf.writeUInt16LE(self.rc.pitch, 2);
            buf.writeUInt16LE(self.rc.yaw, 4);
            buf.writeUInt16LE(self.rc.throttle, 6);
            buf.writeUInt16LE(self.rc.aux1, 8);
            buf.writeUInt16LE(self.rc.aux2, 10);
            buf.writeUInt16LE(self.rc.aux3, 12);
            buf.writeUInt16LE(self.rc.aux4, 14);
            return buf;
        };

        this.port.open(function () {
            self.port.on('data', function (data) {
                self.msp.message_decode_new(data);
            });

            setInterval(function () {
                self.write(105, 105);
            }, 1000);

            setInterval(function () {
                self.write(200, prepare());
            }, 10);

            joystick.on('button', console.log);
            joystick.on('axis', function (data) {
                if (data.number == 4 && data.type === 'axis') {
                    if (data.value > 30000) {
                        data.value = 30000;
                    }

                    if (data.value < -30000) {
                        data.value = -30000;
                    }

                    self.rc.yaw = parseInt(1500 - data.value / 60, 10);
                }

                if (data.number == 3 && data.type === 'axis') {
                    if (data.value > 30000) {
                        data.value = 30000;
                    }

                    if (data.value < -30000) {
                        data.value = -30000;
                    }

                    self.rc.roll = parseInt(1500 - data.value / 60, 10);
                }

                if (data.number == 0 && data.type === 'axis') {
                    if (data.value > 30000) {
                        data.value = 30000;
                    }

                    if (data.value < -30000) {
                        data.value = -30000;
                    }

                    self.rc.pitch = parseInt(1500 - data.value / 60, 10);
                }

                if (data.number == 1 && data.type === 'axis') {
                    if (data.value < -30000) {
                        data.value = -30000;
                    }

                    if (data.value > 0) {
                        data.value = 0;
                    }

                    self.rc.throttle = parseInt(1000 - data.value / 30, 10) - 1;
                }

                 if (data.number == 2 && data.type === 'axis') {
                    if (data.value > 30000) {
                        data.value = 30000;
                    }

                    if (data.value < -30000) {
                        data.value = -30000;
                    }

                    self.rc.aux1 = parseInt(1500 - data.value / 60, 10);
                }
            });
        });

        this.port.on('error', function () {
            console.log('error', arguments);
        });

        this.msp.on('*', function (eventName, data) {
            console.log('Event', eventName);
            console.log('Data', data);
        });
    }

    Copter.prototype.write = function (code, data) {
        var buffer = this.msp.message_encode(code, data);
        this.port.write(buffer, function (err, res) {
            if (err) {
                console.error("Error writing to port");
                console.error(err);
                return;
            }
        });
    };

    return Copter;
}());


Copter();