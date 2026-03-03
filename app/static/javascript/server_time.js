document.addEventListener('DOMContentLoaded', function() {
    const dateTimeElement = document.getElementById('current-date-time');

    function updateDateTime() {
        if (!dateTimeElement) return;

        fetch('/api/server_time')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    dateTimeElement.textContent = data.server_time;
                } else {
                    dateTimeElement.textContent = 'Unable to read server time';
                }
            })
            .catch(() => {
                dateTimeElement.textContent = 'Connection error reading server time';
            });
    }

    updateDateTime();
});
