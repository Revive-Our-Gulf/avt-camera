function updateSettings() {
    fetch('/api/camera_settings')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log('Camera settings updated:', data.settings);
                document.getElementById('exposureTime').textContent = (parseInt(data.settings.ExposureTime, 10) / 1000).toFixed(2);
                if (data.settings.ExposureAuto == "Continuous") {
                    document.getElementById('exposureAuto').textContent = 'On';
                }
                else {
                    document.getElementById('exposureAuto').textContent = 'Off';
                }
                if (data.settings.LineSource == "ExposureActive") {
                    document.getElementById('strobe').textContent = 'On';
                } else {
                    document.getElementById('strobe').textContent = 'Off';
                }
                
            }
        })
        .catch(error => {
            console.error('Error fetching camera settings:', error);
        });
}

setInterval(updateSettings, 2500);
updateSettings();