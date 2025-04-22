// Store folder name in localStorage when it changes
document.getElementById('folderNameInput').addEventListener('input', function(e) {
    localStorage.setItem('folderName', e.target.value);
});

// Restore from localStorage on page load
document.addEventListener('DOMContentLoaded', function() {
    const storedFolderName = localStorage.getItem('folderName');
    if (storedFolderName) {
        document.getElementById('folderNameInput').value = storedFolderName;
    }
});

// Override the setState function to include the folder name
window.setState = function(state) {
    const folderName = document.getElementById('folderNameInput').value.trim();
    
    fetch('/api/state', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            state: state,
            folder_name: folderName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            alert('Failed to change state: ' + data.error);
        }
        // Don't update the UI here - let the socket.io event handle that
    })
    .catch(error => {
        console.error('Error:', error);
    });
};