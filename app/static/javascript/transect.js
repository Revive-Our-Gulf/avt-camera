function setTransectName() {
    var folderNameInput = document.getElementById('folderName');
    var folderName = folderNameInput.value.trim() || 'transect';
    fetch('/set_transect_name', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ transect_name: folderName })
    })
    getTransectName();
}

function getTransectName() {
    fetch('/get_transect_name')
    .then(response => response.json())
    .then(data => {
        document.getElementById('folderName').value = data.transect_name;
        document.getElementById('CurrentTransectName').innerText = data.transect_name;
    });
}

window.onload = function() {
    getTransectName();
};

window.addEventListener('load', function() {
    getTransectName();
});