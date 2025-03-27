// static/parameters.js
var socket = io();

function updateParameters() {
    if (!validateForm()) {
        return false;
    }


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

function restartPipeline() {
    socket.emit('restart_pipeline');
}

function validateForm() {
    let isValid = true;
    const inputs = document.querySelectorAll('#parametersForm input[type="number"]');
    
    inputs.forEach(input => {
        const value = parseFloat(input.value);
        const min = input.hasAttribute('min') ? parseFloat(input.getAttribute('min')) : null;
        const max = input.hasAttribute('max') ? parseFloat(input.getAttribute('max')) : null;
        
        // Reset previous error styling
        input.classList.remove('is-invalid');
        
        // Check if value is outside bounds
        if ((min !== null && value < min) || (max !== null && value > max)) {
            input.classList.add('is-invalid');
            isValid = false;
            
            // Create or update error message
            let errorMsg = input.nextElementSibling;
            if (!errorMsg || !errorMsg.classList.contains('invalid-feedback')) {
                errorMsg = document.createElement('div');
                errorMsg.className = 'invalid-feedback';
                input.parentNode.appendChild(errorMsg);
            }
            errorMsg.textContent = `Value must be between ${min || '-∞'} and ${max || '∞'}`;
        }
    });
    
    return isValid;
}