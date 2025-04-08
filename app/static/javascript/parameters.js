document.addEventListener('DOMContentLoaded', function() {
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
    
        // Add status message div
        const statusDiv = document.createElement('div');
        statusDiv.id = 'statusMessage';
        statusDiv.className = 'alert mt-3';
        statusDiv.style.display = 'none';
        parametersContainer.appendChild(statusDiv);
    }
    
    // Event listener for apply button
    parametersContainer.addEventListener('click', function(event) {
        if (event.target && event.target.id === 'applySettingsButton') {
            applySettings();
        }
    });
    
    // Function to apply settings to camera
    function applySettings() {
        const settings = {};
        
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
                }
            }
        }
        
        console.log('Applying settings:', settings);
        
        // Send settings to server
        fetch('/api/camera/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Settings applied:', data);
            
            const statusDiv = document.getElementById('statusMessage');
            if (data.success) {
                statusDiv.className = 'alert alert-success mt-3';
                statusDiv.textContent = 'Settings applied successfully';
            } else {
                statusDiv.className = 'alert alert-danger mt-3';
                statusDiv.textContent = 'Error applying settings: ' + data.message;
            }
            
            statusDiv.style.display = 'block';
            
            // Hide status after 3 seconds
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 3000);
        })
        .catch(error => {
            console.error('Error:', error);
            const statusDiv = document.getElementById('statusMessage');
            statusDiv.className = 'alert alert-danger mt-3';
            statusDiv.textContent = 'Error applying settings';
            statusDiv.style.display = 'block';
        });
    }
});