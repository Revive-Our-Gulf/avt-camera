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
                handleTriggeringModeChange(); // Initial check
            } else {
                showStatus('Error loading settings', 'danger');
            }
        })
        .catch(error => {
            console.error('Error setting up app settings:', error);
            showStatus('Failed to load settings', 'danger');
        });

    // Function to generate form elements based on setting definitions
    function generateSettingsForm(settings) {
        settingsContainer.innerHTML = ''; // Clear loading spinner
        
        for (const setting of settings) {
            const formGroup = document.createElement('div');
            formGroup.className = 'form-group row mb-3';
            formGroup.id = `form-group-${setting.id}`; // Add ID for dynamic visibility
            
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
                    
                case 'select': // Handle select type
                case 'enum':   // Also handle enum type the same way
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
                    
                case 'number':
                    inputElement = document.createElement('input');
                    inputElement.type = 'number';
                    inputElement.className = 'form-control';
                    inputElement.id = setting.id;
                    inputElement.name = setting.id;
                    inputElement.value = setting.value || '';
                    if (setting.min !== undefined) inputElement.min = setting.min;
                    if (setting.max !== undefined) inputElement.max = setting.max;
                    inputElement.step = setting.step || 'any';
                    break;
                    
                default: // text input
                    inputElement = document.createElement('input');
                    inputElement.type = 'text';
                    inputElement.className = 'form-control';
                    inputElement.id = setting.id;
                    inputElement.name = setting.id;
                    inputElement.value = setting.value || '';
            }
            
            // Simply append the input element without descriptions
            inputContainer.appendChild(inputElement);
            
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

    // Handle visibility of settings based on triggering_mode
    function handleTriggeringModeChange() {
        const triggeringModeElement = document.getElementById('triggering_mode');
        const recordingFrameRateGroup = document.getElementById('form-group-recording_frame_rate');
        const distanceTriggeringGroup = document.getElementById('form-group-distance_triggering');
        
        if (triggeringModeElement) {
            const updateVisibility = () => {
                const mode = triggeringModeElement.value;
                if (mode === 'time') {
                    recordingFrameRateGroup.style.display = 'flex';
                    distanceTriggeringGroup.style.display = 'none';
                } else if (mode === 'distance') {
                    recordingFrameRateGroup.style.display = 'none';
                    distanceTriggeringGroup.style.display = 'flex';
                } else {
                    recordingFrameRateGroup.style.display = 'none';
                    distanceTriggeringGroup.style.display = 'none';
                }
            };
            
            triggeringModeElement.addEventListener('change', updateVisibility);
            updateVisibility(); // Initial visibility update
        }
    }
});