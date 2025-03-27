var socket = io();
var isPreviewActive = false;

function togglePreview() {
    isPreviewActive = !isPreviewActive;
    const button = document.getElementById('previewButton');
    
    if (isPreviewActive) {
        button.classList.remove('btn-secondary');
        button.classList.add('btn-danger');
        socket.emit('start_preview');
    } else {
        button.classList.remove('btn-danger');
        button.classList.add('btn-secondary');
        socket.emit('stop_preview');
    }
}

// Handle server-sent preview state updates
// Handle server-sent preview state updates
socket.on('preview_state', function(data) {
    isPreviewActive = data.isActive;
    const button = document.getElementById('previewButton');
    
    if (isPreviewActive) {
        button.classList.remove('btn-secondary');
        button.classList.add('btn-danger');
    } else {
        button.classList.remove('btn-danger');
        button.classList.add('btn-secondary');
        
        const img = document.getElementById('live_feed');
        // Optional: Clear the image when preview stops
        if (img) {
            img.src = '';
        }
    }
});

// Update this to reflect recording state changes
socket.on('current_recording_state', function(data) {
    const previewButton = document.getElementById('previewButton');
    if (data.isRecording) {
        previewButton.disabled = true;
    } else {
        previewButton.disabled = false;
        // No need to update preview state here as the server will send a separate preview_state event
    }
});

document.addEventListener('DOMContentLoaded', function() {
    socket.emit('get_preview_state');
});