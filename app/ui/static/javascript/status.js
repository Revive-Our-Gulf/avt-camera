var socket = io();

function updateRecordButton(isRecording, elapsedTime) {
    const button = document.getElementById('recordButton');

    // Reset elapsed time if needed
    if (elapsedTime > 86400) {
        elapsedTime = 0;
    }

    // Calculate elapsed minutes and seconds.
    const minutes = Math.floor(elapsedTime / 60);
    const seconds = Math.floor(elapsedTime % 60);
    const timeText = ` ${minutes < 10 ? "0" : ""}${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;

    if (isRecording) {
        button.classList.add('btn-danger');
        button.classList.remove('btn-success');
        // Show stop icon along with the elapsed time.
        button.innerHTML = `<i class="fa fa-stop"></i>${timeText}`;
    } else {
        button.classList.add('btn-success');
        button.classList.remove('btn-danger');
        // Show play icon along with 00:00 when not recording.
        button.innerHTML = `<i class="fa fa-play"></i> 00:00`;
    }
}

// Listen for the current state from main.py via socket.io
socket.on('current_recording_state', function(data) {
    updateRecordButton(data.isRecording, data.elapsedTime);
});

// On startup, request the current recording state and update every second.
window.onload = function() {
    socket.emit('get_recording_state');
    setInterval(function() {
        socket.emit('get_recording_state');
    }, 1000);
};



