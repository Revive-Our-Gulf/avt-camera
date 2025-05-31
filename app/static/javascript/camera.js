const socket = io();

function getState() {
    return fetch('/api/state')
        .then(response => response.json())
        .then(data => {
            return data.state;
        })
        .catch(error => {
            console.error('Error fetching camera state:', error);
            return null;
        });
}

// Add reconnection handler
socket.on('connect', function() {
    console.log('Socket connected/reconnected, refreshing state');
    
    // Force reconnection of the video stream
    const videoFeed = document.getElementById('live_feed');
    if (videoFeed) {
        const currentSrc = videoFeed.src;
        videoFeed.src = '';  // Disconnect current stream
        setTimeout(() => {
            videoFeed.src = currentSrc || '/video_feed';  // Reconnect after brief pause
        }, 100);
    }
    
    // Keep your existing state refresh
    getState();
    
    // Update connection status UI
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
        statusElement.textContent = 'Connected';
        statusElement.className = 'alert alert-success';
        setTimeout(() => { statusElement.className = 'd-none'; }, 3000);
    }
});
