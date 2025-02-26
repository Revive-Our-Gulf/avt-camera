var socket = io();
var isRecording = false; // Add this variable to track the recording state

function toggleRecording() {
    var folderNameInput = document.getElementById('folderName');
    var folderName = folderNameInput.value.trim() || 'transect';

    isRecording = !isRecording; // Toggle the recording state

    console.log("Toggling recording state:", isRecording);
    socket.emit('toggle_recording', { isRecording: isRecording, folderName: folderName });
}

function updateRecordingState(recording, elapsedTime) {
    var button = document.getElementById('recordButton');
    isRecording = recording; // Update the local isRecording variable

    if (isRecording) {
        button.classList.add('btn-danger');
        button.classList.remove('btn-success');
        button.textContent = 'Stop';
    } else {
        button.classList.add('btn-success');
        button.classList.remove('btn-danger');
        
        button.textContent = 'Start';
    }
    console.log("Elapsed time:", elapsedTime);
    updateTimeDisplay(elapsedTime);
}

function updateTimeDisplay(elapsedTime) {
    if (elapsedTime > 86400){
        elapsedTime = 0;
    }
    var timeRecording = document.getElementById('timeRecording');
    if (isRecording) {
        var minutes = Math.floor(elapsedTime / 60);
        var seconds = Math.floor(elapsedTime % 60);
        timeRecording.textContent = minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
    } else {
        timeRecording.textContent = "0:00";
    }
}

socket.on('recording_state_updated', function(data) {
    console.log("Received recording_state_updated:", data);
    updateRecordingState(data.isRecording, data.elapsedTime);
});

window.onload = function() {
    socket.emit('get_recording_state');
    setInterval(function() {
        socket.emit('get_recording_state');
    }, 1000);
};

socket.on('current_recording_state', function(data) {
    console.log("Received current_recording_state:", data);
    updateRecordingState(data.isRecording, data.elapsedTime);
});