var socket = io();
var isRecording = false;
var recordingStartTime = null;
var recordingInterval = null;

socket.on('image_update', function(data) {
    var img = document.getElementById('live_feed');
    img.src = 'data:image/jpeg;base64,' + data.image;
});

function toggleRecording() {
    var button = document.getElementById('recordButton');
    var folderNameInput = document.getElementById('folderName');
    var folderName = folderNameInput.value.trim() || 'transect';
    var currentFolderName = document.getElementById('currentFolderName');
    var recordingDuration = document.getElementById('recordingDuration');

    isRecording = !isRecording;

    if (isRecording) {
        button.style.backgroundColor = "red";
        button.textContent = "Stop";
        recordingStartTime = Date.now();
        currentFolderName.textContent = folderName;

        recordingInterval = setInterval(function() {
            var elapsedTime = Math.floor((Date.now() - recordingStartTime) / 1000);
            recordingDuration.textContent = elapsedTime;
        }, 1000);
    } else {
        button.style.backgroundColor = "green";
        button.textContent = "Start";
        clearInterval(recordingInterval);
        recordingDuration.textContent = "0";
    }

    socket.emit('toggle_recording', { isRecording: isRecording, folderName: folderName });
}

function updateExposureTime() {
    var exposureTime = document.getElementById('exposureTime').value;
    socket.emit('update_exposure_time', { exposureTime: exposureTime });
}