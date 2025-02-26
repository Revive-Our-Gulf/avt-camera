var socket = io();

function updateButtonStatus(isRecording) {
    const button = document.getElementById('recordButton');

    if (isRecording) {
        button.classList.add('btn-danger');
        button.classList.remove('btn-success');
        button.textContent = 'Stop';
    } else {
        button.classList.add('btn-success');
        button.classList.remove('btn-danger');
        button.textContent = 'Start';
    }
}

function updateTimeDisplay(elapsedTime, isRecording) {
    const timeRecording = document.getElementById('timeRecording');
    if (elapsedTime > 86400) {
        elapsedTime = 0;
    }
    if (isRecording) {
        const minutes = Math.floor(elapsedTime / 60);
        const seconds = Math.floor(elapsedTime % 60);
        timeRecording.textContent = minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
    } else {
        timeRecording.textContent = "0:00";
    }
}

// Listen for the current state from main.py via socket.io
socket.on('current_recording_state', function(data) {
    updateButtonStatus(data.isRecording);
    updateTimeDisplay(data.elapsedTime, data.isRecording);
});

// On startup, request the current recording state and update every second.
window.onload = function() {
    socket.emit('get_recording_state');
    setInterval(function() {
        socket.emit('get_recording_state');
    }, 1000);
};