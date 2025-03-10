var socket = io();

socket.on('time_sync_status', function(data) {
    const timeSyncStatus = document.getElementById('timeSyncStatus');
    if (data.status === 'success') {
        timeSyncStatus.textContent = data.message;
        timeSyncStatus.classList.remove('text-danger');
        timeSyncStatus.classList.add('text-success');
    } else {
        timeSyncStatus.textContent = data.message;
        timeSyncStatus.classList.remove('text-success');
        timeSyncStatus.classList.add('text-danger');
    }
});

window.onload = function() {
    socket.emit('get_time_sync');
    setInterval(function() {
        socket.emit('get_time_sync');
    }, 2500);
};