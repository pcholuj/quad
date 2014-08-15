var net = require('net');
var XboxController = require('xbox-controller')
var xbox = new XboxController
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
        self.armed = false;
        // self.bindJoy.call(self);
        
        this.client.connect(options.port, options.host, function () {
            console.log('connected')
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

    Client.prototype.testJoy = function() {
        joystick.on('button', function (data) {
            console.log(data);
        });

        joystick.on('axis', function (data) {
            console.log(data);
        })
    };

    Client.prototype.bindJoy = function () {
        var self = this;





        // joystick.on('button', function (data) {
        //     if (data.number === 8 && data.value === 1) {
        //         self.armed = self.armed ? false : true;
        //         self.sendRc({
        //             aux1: self.armed ? 1000 : 2000
        //         });
        //     }
        // });

        // joystick.on('axis', function (data) {
        //     // console.log(data);
        //     if (data.number == 0 && data.type === 'axis') {
        //         if (data.value > 30000) {
        //             data.value = 30000;
        //         }

        //         if (data.value < -30000) {
        //             data.value = -30000;
        //         }

        //         self.sendRc({
        //             yaw: parseInt(1500 - data.value / 60, 10)
        //         });
        //     }

        //     if (data.number == 3 && data.type === 'axis') {
        //         if (data.value > 30000) {
        //             data.value = 30000;
        //         }

        //         if (data.value < -30000) {
        //             data.value = -30000;
        //         }

        //         self.sendRc({
        //             roll: parseInt(1500 - data.value / 60, 10)
        //         });
        //     }

        //     if (data.number === 4 && data.type === 'axis') {
        //         if (data.value > 30000) {
        //             data.value = 30000;
        //         }

        //         if (data.value < -30000) {
        //             data.value = -30000;
        //         }

        //         self.sendRc({
        //             pitch: parseInt(1500 - data.value / 60, 10)
        //         });
        //     }

        //     if (data.number == 2 && data.type === 'axis') {
        //         if (data.value > 30000) {
        //             data.value = 30000;
        //         }

        //         if (data.value < -30000) {
        //             data.value = -30000;
        //         }

        //         data.value = data.value + 30000;

        //         if (data.value > 600000) {
        //             data.value = 600000;
        //         }

        //         self.sendRc({
        //             throttle: parseInt(1000 + data.value / 60, 10)
        //         });
        //     }

        xbox.on('left:move', function(data){
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
            self.armed = self.armed ? false : true;
            self.sendRc({
                aux1: self.armed ? 1000 : 2000
            });
        });

        xbox.on('right:move', function(data){
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
        })


        xbox.on('lefttrigger', function(position){
            self.sendRc({
                throttle: parseInt(1000 + (position * 4), 10)
            });
        });

            // if (data.number == 5 && data.type === 'axis') {
            //     if (data.value > 30000) {
            //         data.value = 30000;
            //     }

            //     if (data.value < -30000) {
            //         data.value = -30000;
            //     }

            //     self.sendRc({
            //         aux1: parseInt(1500 - data.value / 60, 10)
            //     });
            // }
    
    };

    return Client;

}());

new Client(config);
