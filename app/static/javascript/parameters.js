// static/parameters.js
var socket = io();

function updateParameters() {
    var form = document.getElementById('parametersForm');
    var formData = new FormData(form);
    var data = {};

    formData.forEach((value, key) => {
        data[key] = value;
    });

    // Display a message saying parameters updated
    alert('Parameters updated.');

    socket.emit('update_parameters', data);
}

function resetParameters() {
    socket.emit('reset_parameters');
}

socket.on('parameters_updated', function(updatedParameters) {
    for (var param_name in updatedParameters) {
        if (updatedParameters.hasOwnProperty(param_name)) {
            var param = updatedParameters[param_name];
            var input = document.getElementById(param_name);
            var currentValueSpan = document.getElementById(param_name + '_current_value');

            if (input.tagName === 'SELECT') {
                input.value = param;
            } else {
                input.value = param;
            }

            if (currentValueSpan) {
                currentValueSpan.textContent = param;
            }
        }
    }
});

socket.on('parameters_reset', function(message) {
    alert(message.message);
    location.reload();
});