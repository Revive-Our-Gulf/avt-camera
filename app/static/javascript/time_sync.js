document.addEventListener('DOMContentLoaded', function() {
    const remotePiDiffElement = document.getElementById('remote-pi-diff');
    const refreshButton = document.getElementById('refresh-time-btn');
    
    // Initial fetch
    updateTimeDiff();
    
    // Set up refresh every 30 seconds
    setInterval(updateTimeDiff, 30000);
    
    // Add click handler for refresh button
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            refreshButton.disabled = true;
            refreshButton.querySelector('i').className = 'fa fa-sync fa-spin';
            
            updateTimeDiff().finally(() => {
                setTimeout(() => {
                    refreshButton.disabled = false;
                    refreshButton.querySelector('i').className = 'fa fa-sync';
                }, 500);
            });
        });
    }
    
    function updateTimeDiff() {
        return fetch('/api/remote_pi_time')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const timeDiffSecs = data.time_diff_seconds;
                    const timeDiffAbs = Math.abs(timeDiffSecs);
                    
                    // Format the time difference nicely
                    let diffText = '';
                    if (timeDiffSecs > 0) {
                        diffText = `Blueos is ${formatTimeDifference(timeDiffAbs)} ahead`;
                    } else if (timeDiffSecs < 0) {
                        diffText = `Blueos is ${formatTimeDifference(timeDiffAbs)} behind`;
                    } else {
                        diffText = 'No difference';
                    }
                    
                    remotePiDiffElement.textContent = diffText;
                    
                    // Add color indicator based on time difference
                    remotePiDiffElement.className = '';
                    if (timeDiffAbs > 60) {
                        remotePiDiffElement.className = 'text-danger';
                    } else if (timeDiffAbs > 10) {
                        remotePiDiffElement.className = 'text-warning';
                    } else {
                        remotePiDiffElement.className = 'text-success';
                    }
                } else {
                    remotePiDiffElement.textContent = data.error || 'Unable to get time data';
                    remotePiDiffElement.className = 'text-danger';
                }
            })
            .catch(error => {
                console.error('Error fetching time data:', error);
                remotePiDiffElement.textContent = 'Connection error';
                remotePiDiffElement.className = 'text-danger';
            });
    }
    
    function formatTimeDifference(seconds) {
        if (seconds < 60) {
            return `${seconds.toFixed(2)} seconds`;
        } else if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${minutes}m`;
        }
    }
});