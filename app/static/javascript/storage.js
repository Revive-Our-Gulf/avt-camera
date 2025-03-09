var socket = io();

socket.on('storage_info', function(data) {
    var storageBar = document.getElementById('storage-bar');
    if (data.free_space_gb !== undefined && data.total_space_gb !== undefined) {
        var freeSpaceGB = data.free_space_gb.toFixed(2);
        var totalSpaceGB = data.total_space_gb.toFixed(2);
        var usedSpaceGB = (totalSpaceGB - freeSpaceGB).toFixed(2);
        var usedPercentage = ((usedSpaceGB / totalSpaceGB) * 100).toFixed(2);

        storageBar.style.width = usedPercentage + '%';
        storageBar.setAttribute('aria-valuenow', usedPercentage);
        storageBar.innerHTML = `${usedSpaceGB} GB / ${totalSpaceGB} GB (${usedPercentage}%)`;
    } else {
        console.error('Invalid data received:', data);
    }
});

window.onload = function() {
    socket.emit('get_storage');
    setInterval(function() {
        socket.emit('get_storage');
    }, 1000);
};