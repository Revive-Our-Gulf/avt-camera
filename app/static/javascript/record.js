var socket = io();
var isRecording = false;
var recordingStartTime = null;
var recordingInterval = null;

function toggleRecording() {
    var button = document.getElementById('recordButton');
    var folderNameInput = document.getElementById('folderName');
    var folderName = folderNameInput.value.trim() || 'transect';

    isRecording = !isRecording;

    if (isRecording) {
        button.style.backgroundColor = "red";
        button.textContent = "Stop";
        recordingStartTime = Date.now();

        recordingInterval = setInterval(function() {
            var elapsedTime = Math.floor((Date.now() - recordingStartTime) / 1000);
            var recordingDuration = document.getElementById('recordingDuration');
            if (recordingDuration) {
                recordingDuration.textContent = elapsedTime;
            }
        }, 1000);
    } else {
        button.style.backgroundColor = "green";
        button.textContent = "Start";
        clearInterval(recordingInterval);
        var recordingDuration = document.getElementById('recordingDuration');
        if (recordingDuration) {
            recordingDuration.textContent = "0";
        }
    }

    socket.emit('toggle_recording', { isRecording: isRecording, folderName: folderName });
}

function updateExposureTime() {
    var exposureTime = document.getElementById('exposureTime').value;
    socket.emit('update_exposure_time', { exposureTime: exposureTime });
}

socket.on('recording_state_updated', function(data) {
    var button = document.getElementById('recordButton');
    var currentFolderName = document.getElementById('currentFolderName');
    var recordingDuration = document.getElementById('recordingDuration');

    isRecording = data.isRecording;
    if (currentFolderName) {
        currentFolderName.textContent = data.folderName;
    }

    if (isRecording) {
        button.style.backgroundColor = "red";
        button.textContent = "Stop";
        recordingStartTime = Date.now();

        recordingInterval = setInterval(function() {
            var elapsedTime = Math.floor((Date.now() - recordingStartTime) / 1000);
            if (recordingDuration) {
                recordingDuration.textContent = elapsedTime;
            }
        }, 1000);
    } else {
        button.style.backgroundColor = "green";
        button.textContent = "Start";
        clearInterval(recordingInterval);
        if (recordingDuration) {
            recordingDuration.textContent = "0";
        }
    }
});