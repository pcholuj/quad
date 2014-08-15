var net = require('net');
var serialport = require("serialport");
var SerialPort = serialport.SerialPort; // localize object constructor
var msp = require('./msp.js');

var config = {
    port: 3000,
    serialPort: '/dev/ttyUSB0',
    serialOptions: {
        baudrate: 115200,
        databits: 8,
        stopbits: 1,
        parity: 'none',
        parser: serialport.parsers.raw
    }
};

var Serwer = (function () {
    'use strict';

    function Serwer(options) {
        // enforces new
        if (!(this instanceof Serwer)) {
            return new Serwer(options);
        }
        var self = this;
        var intervalRc = null;

        self.cache = '';
        self.msp = new msp.protocol();
        this.clients = [];

        this.rc = {
            roll: 1500,
            pitch: 1500,
            yaw: 1500,
            throttle: 1500,
            aux1: 1500,
            aux2: 1500,
            aux3: 1500,
            aux4: 1500
        };

        self.msp.on('*', function (eventName, data) {
            self.sendNet.call(self, eventName, data);
        });

        this.port = new SerialPort(options.serialPort, options.serialOptions, false);
        this.port.open(function () {
            self.portOpened = true;

            self.port.on('data', function (data) {
                self.msp.message_decode_new(data);
            });

            self.port.on('error', function () {
                console.log('error', arguments);
            });

            intervalRc = setInterval(function () {
                self.portWrite(200, self.parseRc.call(self));
            }, 100);
        });

        process.on('exit', function (code) {
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

            clearInterval(intervalRc);
            self.portWrite(200, self.parseRc.call(self));
        });


        this.serwer = net.createServer(function (socket) {
            self.clients.push(socket);

            socket.on('data', function (data) {
                data = self.cache + data.toString();
                var dataArray = data.trim().split('\n');

                if (data.slice(-1) === '\n') {
                    self.cache = '';
                } else {
                    self.cache = dataArray.pop();
                }

                for (var part in dataArray) {
                    var jdata = dataArray[part];
                    try {
                        jdata = JSON.parse(jdata);
                        self.parseNetData.call(self, jdata);
                    } catch (e) {
                        console.error('ERROR recive data', e);
                    }

                }
            });

            socket.on('end', function () {
                self.clients.splice(self.clients.indexOf(socket), 1);

                self.rc.throttle = 1000;
                self.rc.aux1 = 2000;
            });
        }).listen(options.port);
    }

    Serwer.prototype.parseNetData = function (response) {
        var self = this;

        if (response.action === 'rc') {
            var data = response.data;
            for (var i in data) {
                if (typeof self.rc[i] !== 'undefined') {
                    self.rc[i] = data[i];
                }
            }
        } else {
            self.portWrite.apply(self, response.data);
        }
    };

    Serwer.prototype.parseRc = function () {
        var buf = new Buffer(16);
        buf.writeUInt16LE(this.rc.roll, 0);
        buf.writeUInt16LE(this.rc.pitch, 2);
        buf.writeUInt16LE(this.rc.yaw, 4);
        buf.writeUInt16LE(this.rc.throttle, 6);
        buf.writeUInt16LE(this.rc.aux1, 8);
        buf.writeUInt16LE(this.rc.aux2, 10);
        buf.writeUInt16LE(this.rc.aux3, 12);
        buf.writeUInt16LE(this.rc.aux4, 14);
        return buf;
    };

    Serwer.prototype.portWrite = function (code, data) {
        var buffer = this.msp.message_encode(code, data);
        this.port.write(buffer, function (err, res) {
            if (err) {
                console.error("Error writing to port");
                console.error(err);
                return;
            }
        });
    };

    Serwer.prototype.sendNet = function (eventName, data) {
        var message = JSON.stringify({
            eventName: eventName,
            data: data
        });

        for (var i in this.clients) {
            if (typeof this.clients[i].write === 'function') {
                this.clients[i].write(JSON.stringify(message));
            }
        }
    };

    return Serwer;

}());


new Serwer(config);