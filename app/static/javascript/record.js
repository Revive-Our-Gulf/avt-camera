var socket = io();

function toggleRecording() {
    // No need to check if button is disabled, as we'll handle camera start automatically
    var folderNameInput = document.getElementById('folderName');
    var folderName = folderNameInput.value.trim() || 'transect';
    
    socket.emit('toggle_recording', { folderName: folderName });
}

socket.on('error', function(data) {
    alert(data.message);
});