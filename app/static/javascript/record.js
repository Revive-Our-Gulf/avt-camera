var socket = io();

function toggleRecording() {
    // Only proceed if the button is not disabled
    var recordButton = document.getElementById('recordButton');
    if (recordButton.disabled) {
        return;
    }
    
    var folderNameInput = document.getElementById('folderName');
    var folderName = folderNameInput.value.trim() || 'transect';
    
    socket.emit('toggle_recording', { folderName: folderName });
}

socket.on('error', function(data) {
    alert(data.message);
});