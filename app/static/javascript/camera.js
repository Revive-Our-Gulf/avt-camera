const socket = io();

socket.on('state_change', function(data) {
    updateUIForState(data.state);
});

function getState() {
    fetch('/api/state')
        .then(response => response.json())
        .then(data => {
            updateUIForState(data.state);
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function updateUIForState(state) {
    document.getElementById('current-state').textContent = 'Current State: ' + state;
    const previewButton = document.querySelector('button[onclick="setState(\'PREVIEW\')"]');
    const writeButton = document.querySelector('button[onclick="setState(\'WRITE\')"]');
    previewButton.classList.remove('active');
    writeButton.classList.remove('active');
    if (state === 'PREVIEW') {
        previewButton.classList.add('active');
    } else if (state === 'WRITE') {
        writeButton.classList.add('active');
    }
}

function setState(state) {
    fetch('/api/state', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ state: state })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            alert('Failed to change state: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

getState();

function toggleFocusMode() {
    const focusModeButton = document.getElementById('focusModeButton');
    
    fetch('/api/toggle_focus_mode', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.focus_mode_enabled) {
                focusModeButton.classList.remove('btn-primary');
                focusModeButton.classList.add('btn-warning');
                focusModeButton.innerHTML = '<i class="fas fa-camera-retro"></i> <span class="badge badge-light"></span>';
            } else {
                focusModeButton.classList.remove('btn-warning');
                focusModeButton.classList.add('btn-primary');
                focusModeButton.innerHTML = '<i class="fas fa-camera-retro"></i>';
            }
        } else {
            alert('Failed to toggle focus mode: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const focusSlider = document.getElementById('focusToleranceSlider');
    const focusValue = document.getElementById('focusToleranceValue');
    
    if (focusSlider) {
        // Update the displayed value when slider changes
        focusSlider.addEventListener('input', function() {
            focusValue.textContent = this.value;
        });
        
        // Send the new value to the server when slider is released
        focusSlider.addEventListener('change', function() {
            fetch('/api/focus/tolerance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ threshold: parseInt(this.value) })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Focus tolerance updated successfully');
                } else {
                    console.error('Error updating focus tolerance:', data.error);
                }
            })
            .catch(error => {
                console.error('Network error:', error);
            });
        });
    }
});