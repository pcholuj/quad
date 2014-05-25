var Main = (function() {
    'use strict';

    function Main(args) {
        // enforces new
        if (!(this instanceof Main)) {
            return new Main(args);
        }
        this.socket = io.connect('http://localhost:8080');


        this.initMpu();
    }

    Main.prototype.initMpu = function() {
        this.socket.on('mpu', function(data) {
            if (data.gyro) {
                console.log(data.gyro);
            }
            if (data.temp) {
                $('#temp').html('Current temperature: ' + parseInt(data.temp, 10) + 'C')
            }
        })
    };

    return Main;

}());


$(document).ready(function() {
    Main();
})