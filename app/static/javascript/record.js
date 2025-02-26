var socket = io();

function toggleRecording() {
    var folderNameInput = document.getElementById('folderName');
    var folderName = folderNameInput.value.trim() || 'transect';
    
    socket.emit('toggle_recording', { folderName: folderName });
}