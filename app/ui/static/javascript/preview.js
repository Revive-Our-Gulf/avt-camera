var socket = io();
var isPreviewActive = false;

function togglePreview() {
    isPreviewActive = !isPreviewActive;
    const button = document.getElementById('previewButton');
    
    if (isPreviewActive) {
        button.classList.remove('btn-secondary');
        button.classList.add('btn-danger');
        socket.emit('start_preview');
        
        // MJPEG stream will start automatically when camera is in preview mode
        refreshMJPEGStream(true);
    } else {
        button.classList.remove('btn-danger');
        button.classList.add('btn-secondary');
        socket.emit('stop_preview');
        
        // Optionally pause the MJPEG stream
        refreshMJPEGStream(false);
    }
}

// Function to refresh MJPEG stream
function refreshMJPEGStream(active) {
    const img = document.getElementById('live_feed');
    if (img) {
        if (active) {
            // Add a timestamp parameter to force reload the stream
            img.src = '/mjpeg_stream?' + new Date().getTime();
        } else {
            // Show a placeholder or blank instead
            img.src = '';
        }
    }
}

// Handle server-sent preview state updates
socket.on('preview_state', function(data) {
    isPreviewActive = data.isActive;
    const button = document.getElementById('previewButton');
    
    if (isPreviewActive) {
        button.classList.remove('btn-secondary');
        button.classList.add('btn-danger');
        refreshMJPEGStream(true);
    } else {
        button.classList.remove('btn-danger');
        button.classList.add('btn-secondary');
        refreshMJPEGStream(false);
    }
});

// Update this to reflect recording state changes
socket.on('current_recording_state', function(data) {
    const previewButton = document.getElementById('previewButton');
    if (data.isRecording) {
        previewButton.disabled = true;
        // No need to change MJPEG stream status here as it should continue during recording
    } else {
        previewButton.disabled = false;
        // No need to update preview state here as the server will send a separate preview_state event
    }
});