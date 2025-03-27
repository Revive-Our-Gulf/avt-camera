var socket = io();

socket.on('image_update', function(data) {
    var liveFeed = document.getElementById('live_feed');
    if (liveFeed) {
        liveFeed.src = 'data:image/jpeg;base64,' + data.image;
    }
});