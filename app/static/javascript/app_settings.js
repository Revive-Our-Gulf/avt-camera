document.addEventListener('DOMContentLoaded', function() {
    const settingsContainer = document.getElementById('settingsContainer');
    let settingDefinitions = [];
    
    // Fetch setting definitions
    fetch('/api/app_settings')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                settingDefinitions = data.settings;
                // Generate form based on settings
                generateSettingsForm(settingDefinitions);
            } else {
                showStatus('Error loading settings', 'danger');
            }
        })
        .catch(error => {
            console.error('Error setting up app settings:', error);
            showStatus('Failed to load settings', 'danger');
        });

    // Format value with description if present
    function formatDescription(setting) {
        if (setting.description) {
            return `<small class="form-text text-muted">${setting.description}</small>`;
        }
        return '';
    }

    // Function to generate form elements based on setting definitions
    function generateSettingsForm(settings) {
        settingsContainer.innerHTML = ''; // Clear loading spinner
        
        for (const setting of settings) {
            const formGroup = document.createElement('div');
            formGroup.className = 'form-group row mb-3';
            
            // Create label
            const label = document.createElement('label');
            label.className = 'col-sm-3 col-form-label';
            label.setAttribute('for', setting.id);
            label.textContent = setting.name;
            
            // Create input container
            const inputContainer = document.createElement('div');
            inputContainer.className = 'col-sm-9';
            
            let inputElement;
            
            // Create input based on type
            switch (setting.type) {
                case 'boolean':
                    inputElement = document.createElement('div');
                    inputElement.className = 'form-check';
                    
                    const checkboxInput = document.createElement('input');
                    checkboxInput.type = 'checkbox';
                    checkboxInput.className = 'form-check-input';
                    checkboxInput.id = setting.id;
                    checkboxInput.name = setting.id;
                    checkboxInput.checked = setting.value === true;
                    
                    const checkboxLabel = document.createElement('label');
                    checkboxLabel.className = 'form-check-label';
                    checkboxLabel.setAttribute('for', setting.id);
                    checkboxLabel.textContent = 'Enabled';
                    
                    inputElement.appendChild(checkboxInput);
                    inputElement.appendChild(checkboxLabel);
                    break;
                case 'number':
                    inputElement = document.createElement('input');
                    inputElement.type = 'number';
                    inputElement.className = 'form-control';
                    inputElement.id = setting.id;
                    inputElement.name = setting.id;
                    inputElement.value = setting.value;
                    
                    if (setting.min !== undefined) inputElement.min = setting.min;
                    if (setting.max !== undefined) inputElement.max = setting.max;
                    break;
                case 'select':
                    inputElement = document.createElement('select');
                    inputElement.className = 'form-select';
                    inputElement.id = setting.id;
                    inputElement.name = setting.id;
                    
                    for (const option of setting.options || []) {
                        const optionElement = document.createElement('option');
                        optionElement.value = option;
                        optionElement.textContent = option;
                        if (option === setting.value) {
                            optionElement.selected = true;
                        }
                        inputElement.appendChild(optionElement);
                    }
                    break;
                default: // text input
                    inputElement = document.createElement('input');
                    inputElement.type = 'text';
                    inputElement.className = 'form-control';
                    inputElement.id = setting.id;
                    inputElement.name = setting.id;
                    inputElement.value = setting.value || '';
            }
            
            // Add description if available
            if (setting.description) {
                const descriptionElement = document.createElement('div');
                descriptionElement.innerHTML = formatDescription(setting);
                inputContainer.appendChild(inputElement);
                inputContainer.appendChild(descriptionElement);
            } else {
                inputContainer.appendChild(inputElement);
            }
            
            // Append everything to the form group
            formGroup.appendChild(label);
            formGroup.appendChild(inputContainer);
            settingsContainer.appendChild(formGroup);
        }
    }

    // Show status message
    function showStatus(message, type) {
        const statusDiv = document.getElementById('statusMessage');
        statusDiv.className = `alert alert-${type} mt-3`;
        statusDiv.textContent = message;
        statusDiv.style.display = 'block';
        
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 3000);
    }

    // Handle form submission
    document.getElementById('appSettingsForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Collect settings from form
        const settings = {};
        for (const setting of settingDefinitions) {
            const element = document.getElementById(setting.id);
            if (element) {
                let value;
                
                // Handle different input types
                if (setting.type === 'boolean') {
                    value = element.checked;
                } else if (setting.type === 'number') {
                    value = parseFloat(element.value);
                } else {
                    value = element.value;
                }
                
                settings[setting.id] = value;
            }
        }
        
        fetch('/api/app_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showStatus('Settings saved successfully', 'success');
            } else {
                showStatus('Error saving settings: ' + (data.error || 'Unknown error'), 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showStatus('Failed to save settings', 'danger');
        });
    });
});