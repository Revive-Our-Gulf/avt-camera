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
            folderNameInput.value = currentTransectName;
            updateInputStyle();
        });
}

function setTransectName() {
    const folderNameInput = document.getElementById('folderName');
    const transectName = folderNameInput.value.trim();
    if (transectName) {
        saveTransectName(transectName);
        currentTransectName = transectName;
        updateInputStyle();
        alert(`Transect name saved as: ${transectName}`);
    } else {
        alert('Please enter a transect name.');
    }
}

function updateInputStyle() {
    const folderNameInput = document.getElementById('folderName');
    const saveButton = document.getElementById('setNameButton');
    // If the current input doesn't match the saved transect name and is not empty, enable & show blue save button.
    if (folderNameInput.value.trim() !== currentTransectName.trim() && folderNameInput.value.trim() !== '') {
        saveButton.classList.remove('btn-secondary');
        saveButton.classList.add('btn-primary');
        saveButton.disabled = false;
    } else {
        // Otherwise, disable save button and show it as grey.
        saveButton.classList.remove('btn-primary');
        saveButton.classList.add('btn-secondary');
        saveButton.disabled = true;
    }
}

// Listen for Enter key to trigger save
document.getElementById('folderName').addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        setTransectName();
    }
});

// Listen for any input change to update the styling
document.getElementById('folderName').addEventListener('input', updateInputStyle);

// Load the current transect name when the page loads
window.addEventListener('load', getTransectName);