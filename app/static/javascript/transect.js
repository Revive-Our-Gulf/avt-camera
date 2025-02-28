// Global variable to store the current transect name
let currentTransectName = '';

function saveTransectName(name) {
    fetch('/set_transect_name', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ transect_name: name })
    });
}

function getTransectName() {
    fetch('/get_transect_name')
        .then(response => response.json())
        .then(data => {
            currentTransectName = data.transect_name;
            const folderNameInput = document.getElementById('folderName');
            if (folderNameInput) {
                folderNameInput.value = currentTransectName;
            }
            
            // Update the button text
            const transectNameSpan = document.getElementById('currentTransectName');
            if (transectNameSpan) {
                transectNameSpan.textContent = currentTransectName;
            }
        });
}

function openTransectNameOverlay() {
    const overlay = document.getElementById('transectNameOverlay');
    overlay.style.display = 'flex';
    
    // Focus the input after a short delay to ensure overlay is visible
    setTimeout(() => {
        const input = document.getElementById('folderName');
        input.focus();
        input.select();
    }, 100);
}

function closeTransectNameOverlay() {
    const overlay = document.getElementById('transectNameOverlay');
    overlay.style.display = 'none';
    
    // Reset the input to the current name
    const folderNameInput = document.getElementById('folderName');
    if (folderNameInput) {
        folderNameInput.value = currentTransectName;
    }
}

function setTransectName() {
    const folderNameInput = document.getElementById('folderName');
    const transectName = folderNameInput.value.trim();
    if (transectName) {
        saveTransectName(transectName);
        currentTransectName = transectName;
        
        // Update the button text
        const transectNameSpan = document.getElementById('currentTransectName');
        if (transectNameSpan) {
            transectNameSpan.textContent = transectName;
        }
        
        // Close the overlay
        closeTransectNameOverlay();
    } else {
        alert('Please enter a transect name.');
    }
}

// Listen for Enter key to trigger save
document.addEventListener('DOMContentLoaded', function() {
    const folderNameInput = document.getElementById('folderName');
    if (folderNameInput) {
        folderNameInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                setTransectName();
            }
            if (event.key === 'Escape') {
                closeTransectNameOverlay();
            }
        });
    }
    
    // Load the current transect name when the page loads
    getTransectName();
});