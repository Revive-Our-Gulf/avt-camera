var socket = io();
var isPreviewActive = false;

function togglePreview() {
    isPreviewActive = !isPreviewActive;
    const button = document.getElementById('previewButton');
    const recordButton = document.getElementById('recordButton');
    
    if (isPreviewActive) {
        button.classList.remove('btn-secondary');
        button.classList.add('btn-info');
        recordButton.disabled = false; // Enable recording button when preview is active
        socket.emit('start_preview');
    } else {
        button.classList.remove('btn-info');
        button.classList.add('btn-secondary');
        recordButton.disabled = true; // Disable recording when preview is inactive
        socket.emit('stop_preview');
    }
}

// Handle server-sent preview state updates
socket.on('preview_state', function(data) {
    isPreviewActive = data.isActive;
    const button = document.getElementById('previewButton');
    const recordButton = document.getElementById('recordButton');
    
    if (isPreviewActive) {
        button.classList.remove('btn-secondary');
        button.classList.add('btn-info');
        recordButton.disabled = false;
    } else {
        button.classList.remove('btn-info');
        button.classList.add('btn-secondary');
        recordButton.disabled = true;
        
        // Hide the image when preview is not active
        const img = document.getElementById('live_feed');
        img.src = '';
    }
});

// Request current preview state when page loads
document.addEventListener('DOMContentLoaded', function() {
    socket.emit('get_preview_state');
    
    // Initially disable recording button until preview is active
    document.getElementById('recordButton').disabled = true;
});