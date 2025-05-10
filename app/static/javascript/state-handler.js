document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    
    socket.on('state_change', function(data) {
        updateButtonState(data.state);
    });
    
    fetch('/api/state')
        .then(response => response.json())
        .then(data => {
            updateButtonState(data.state);
        });
    
    function updateButtonState(state) {
        const previewButton = document.querySelector('button[onclick="setState(\'PREVIEW\')"]');
        const recordButton = document.querySelector('button[onclick="setState(\'WRITE\')"]');
        
        if (previewButton) {
            previewButton.className = 'btn btn-dark';
            previewButton.querySelector('i').className = 'fa fa-eye';
            previewButton.disabled = false;
        }
        
        if (recordButton) {
            recordButton.className = 'btn btn-dark';
            recordButton.querySelector('i').className = 'fa fa-circle text-danger';
        }
        
        if (state === 'PREVIEW' && previewButton && recordButton) {
            previewButton.className = 'btn btn-warning';
            previewButton.querySelector('i').className = 'fa fa-eye';
            
            recordButton.className = 'btn btn-dark';
            recordButton.querySelector('i').className = 'fa fa-circle text-danger';
            
        } else if (state === 'WRITE' && previewButton && recordButton) {
            recordButton.className = 'btn btn-danger';
            recordButton.querySelector('i').className = 'fa fa-stop';
            
            previewButton.className = 'btn btn-dark';
            previewButton.disabled = true;
        }
        
        const stateDisplay = document.getElementById('current-state');
        if (stateDisplay) {
            stateDisplay.textContent = `Current State: ${state}`;
        }
    }
});
