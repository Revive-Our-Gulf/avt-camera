// static/parameters.js
var socket = io();

function updateParameters() {
    var form = document.getElementById('parametersForm');
    var formData = new FormData(form);
    var data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });

    socket.emit('update_parameters', data);
}

function resetParameters() {
    var form = document.getElementById('parametersForm');
    var formData = new FormData(form);
    var data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });
    socket.emit('restore_default_parameters', data);
}

socket.on('parameters_updated', function(updatedParameters) {
    for (var key in updatedParameters) {
        if (updatedParameters.hasOwnProperty(key)) {
            var param = updatedParameters[key];
            var input = document.getElementById(key);
            var currentValueSpan = document.getElementById(key + '_current_value');

            if (input.tagName === 'SELECT') {
                input.value = param.value;
            } else {
                input.value = param.value;
            }

            if (currentValueSpan) {
                currentValueSpan.textContent = 'Current: ' + param.value;
            }
        }
    }
});