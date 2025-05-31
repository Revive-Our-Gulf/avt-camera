document.addEventListener('DOMContentLoaded', function () {
    const parametersContainer = document.getElementById('parametersContainer');
    let parameterDefinitions = [];

    // Fetch parameter definitions
    fetch('/api/camera/parameters')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                parameterDefinitions = data.parameters;
                // Generate form based on parameters
                generateParameterTable(parameterDefinitions);

                // Then fetch current values
                return fetch('/api/camera/settings');
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log("Camera settings response:", data);
            if (data.success) {
                // Update form values with current settings
                for (const param of parameterDefinitions) {
                    const element = document.getElementById(param.id);
                    const currentValueSpan = document.getElementById(`current-${param.id}`);

                    if (element && data.settings[param.id] !== undefined) {
                        console.log(`Setting ${param.id} = ${data.settings[param.id]}`);
                        element.value = data.settings[param.id];

                        if (currentValueSpan) {
                            currentValueSpan.textContent = data.settings[param.id];
                        }
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error loading parameters:', error);
        });

    // Function to generate table-based parameter form
    function generateParameterTable(parameters) {
        parametersContainer.innerHTML = ''; // Clear loading spinner

        // Create table structure
        const table = document.createElement('table');
        table.className = 'table table-sm table-striped table-hover';

        // Create table header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');

        const nameHeader = document.createElement('th');
        nameHeader.textContent = 'Parameter';

        const currentHeader = document.createElement('th');
        currentHeader.textContent = 'Current Value';

        const newValueHeader = document.createElement('th');
        newValueHeader.textContent = 'New Value';

        headerRow.appendChild(nameHeader);
        headerRow.appendChild(currentHeader);
        headerRow.appendChild(newValueHeader);
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Create table body
        const tbody = document.createElement('tbody');

        for (const param of parameters) {
            const row = document.createElement('tr');

            // Parameter name cell
            const nameCell = document.createElement('td');
            nameCell.textContent = param.name + (param.unit ? ` (${param.unit})` : '');
            nameCell.className = 'align-middle';

            // Current value cell
            const currentValueCell = document.createElement('td');
            const currentValue = document.createElement('span');
            currentValue.id = `current-${param.id}`;
            currentValue.className = 'current-value';
            currentValue.textContent = '...';
            currentValueCell.appendChild(currentValue);
            currentValueCell.className = 'align-middle';

            // New value (input) cell
            const inputCell = document.createElement('td');

            // Create input element based on type
            let inputElement;

            if (param.type === 'select') {
                inputElement = document.createElement('select');
                inputElement.className = 'form-control form-control-sm';

                for (const option of param.options) {
                    const optionElement = document.createElement('option');
                    optionElement.value = option;
                    optionElement.textContent = option;
                    inputElement.appendChild(optionElement);
                }
            } else if (param.type === 'number') {
                inputElement = document.createElement('input');
                inputElement.type = 'number';
                inputElement.className = 'form-control form-control-sm';
                if (param.min !== undefined) inputElement.min = param.min;
                if (param.max !== undefined) inputElement.max = param.max;

                inputElement.step = param.increment !== undefined ? param.increment : "any";
                inputElement.value = param.default;
            } else {
                // Default to text input
                inputElement = document.createElement('input');
                inputElement.type = 'text';
                inputElement.className = 'form-control form-control-sm';
                inputElement.value = param.default || '';
            }

            // Set common attributes
            inputElement.id = param.id;
            inputElement.name = param.id;

            // Make input read-only if not writeable
            if (param.writeable === false) {
                inputElement.disabled = true;
                inputElement.classList.add('read-only-input');
            }

            inputCell.appendChild(inputElement);

            // Add cells to row
            row.appendChild(nameCell);
            row.appendChild(currentValueCell);
            row.appendChild(inputCell);

            // Add row to table body
            tbody.appendChild(row);
        }

        table.appendChild(tbody);
        parametersContainer.appendChild(table);

    }

    document.getElementById('cameraSettingsForm').addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent form from submitting normally
        applySettings();
    });

    function applySettings() {
        const settings = {};
        const settingsList = [];
        const socket = io(); // Get socket.io connection
        let statusHideTimer = null;

        // Collect all input values
        for (const param of parameterDefinitions) {
            if (param.writeable !== false) {
                const element = document.getElementById(param.id);
                if (element) {
                    let value = element.value;

                    // Convert to number if type is number
                    if (param.type === 'number') {
                        value = parseFloat(value);
                    }

                    settings[param.id] = value;
                    settingsList.push({
                        id: param.id,
                        name: param.name || param.id,
                        value: value
                    });
                }
            }
        }

        console.log('Preparing to apply settings:', settings);

        // Create and show detailed loading indicator
        const statusDiv = document.getElementById('statusMessage');
        statusDiv.className = 'alert alert-info mt-3';

        // Create detailed status with list of settings being applied
        let statusHTML = '<div class="d-flex align-items-center mb-2">' +
            '<div class="spinner-border spinner-border-sm me-2" role="status"></div>' +
            '<strong>Applying settings...</strong>' +
            '</div>';

        // Add detailed list of settings being applied
        statusHTML += '<div class="small mt-2"><ul class="list-unstyled mb-0">';
        settingsList.forEach(item => {
            statusHTML += `<li id="setting-${item.id}">
                 <i class="fa fa-circle-notch fa-spin me-1"></i>
                 ${item.name}: ${item.value}
               </li>`;
        });
        statusHTML += '</ul></div>';

        statusDiv.innerHTML = statusHTML;
        statusDiv.style.display = 'block';

        // Force cleanup of any existing timers
        if (statusHideTimer) {
            clearTimeout(statusHideTimer);
        }

        // Clean up any existing listeners before adding new ones
        socket.off('setting_applied');
        socket.off('settings_complete');
        socket.off('settings_error');

        // Setup listener for setting updates
        socket.on('setting_applied', function (data) {
            console.log('Setting applied:', data);
            const settingElement = document.getElementById(`setting-${data.id}`);
            if (settingElement) {
                settingElement.innerHTML = `<i class="fa fa-check text-success me-1"></i> ${data.name}: ${data.value}`;

                // Also update the current value display
                const currentValueSpan = document.getElementById(`current-${data.id}`);
                if (currentValueSpan) {
                    currentValueSpan.textContent = data.value;
                }
            }
        });

        socket.on('settings_complete', function (data) {
            console.log('All settings applied:', data);

            // Update header to show completion
            const headerElement = statusDiv.querySelector('.d-flex');
            if (headerElement) {
                headerElement.innerHTML = '<i class="fa fa-check-circle text-success me-2"></i><strong>Settings applied successfully</strong>';
            }

            // Change alert style to success
            statusDiv.className = 'alert alert-success mt-3';

            // Hide status after 5 seconds
            statusHideTimer = setTimeout(() => {
                if (statusDiv) {
                    statusDiv.style.display = 'none';
                }

                // Clean up event listeners
                socket.off('setting_applied');
                socket.off('settings_complete');
                socket.off('settings_error');
            }, 5000);
        });

        socket.on('settings_error', function (data) {
            console.error('Error applying settings:', data);
            statusDiv.className = 'alert alert-danger mt-3';
            statusDiv.innerHTML = `<i class="fa fa-exclamation-triangle me-2"></i> Error applying settings: ${data.message}`;

            // Clean up event listeners
            socket.off('setting_applied');
            socket.off('settings_complete');
            socket.off('settings_error');
        });

        // Add a safety timeout to clean up everything after 30 seconds
        setTimeout(() => {
            if (statusDiv && statusDiv.style.display !== 'none') {
                statusDiv.style.display = 'none';
            }
            socket.off('setting_applied');
            socket.off('settings_complete');
            socket.off('settings_error');
        }, 30000);

        // Send the settings to be applied progressively
        fetch('/api/camera/settings/progressive', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        })
            .catch(error => {
                console.error('Error initiating progressive settings:', error);
                statusDiv.className = 'alert alert-danger mt-3';
                statusDiv.innerHTML = '<i class="fa fa-exclamation-triangle me-2"></i> Error applying settings';

                // Clean up event listeners
                socket.off('setting_applied');
                socket.off('settings_complete');
                socket.off('settings_error');
            });
    }
});