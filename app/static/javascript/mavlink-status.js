document.addEventListener('DOMContentLoaded', function () {
    function getStatusBadges() {
        return document.querySelectorAll('[data-mavlink-status]');
    }

    function getStatusHearts() {
        return document.querySelectorAll('[data-mavlink-heart]');
    }

    function updateMavlinkStatusBadges(statusData) {
        const badges = getStatusBadges();
        if (!badges.length) {
            return;
        }

        badges.forEach((badge) => {
            if (statusData.last_message_age_seconds !== null) {
                badge.textContent = `${statusData.last_message_age_seconds}s`;
            } else {
                badge.textContent = '--s';
            }
        });
    }

    function updateMavlinkStatusHearts(statusData) {
        const hearts = getStatusHearts();
        if (!hearts.length) {
            return;
        }

        hearts.forEach((heart) => {
            if (!statusData.connected) {
                heart.classList.remove('fa-heart', 'text-white', 'text-warning');
                heart.classList.add('fa-heart-crack', 'text-danger');
                return;
            }

            if (statusData.is_stale) {
                heart.classList.remove('fa-heart', 'text-white', 'text-danger');
                heart.classList.add('fa-heart-crack', 'text-warning');
                return;
            }

            if (statusData.connected && !statusData.is_stale) {
                heart.classList.remove('fa-heart-crack');
                heart.classList.add('fa-heart');
                heart.classList.remove('text-danger', 'text-warning');
                heart.classList.add('text-white');
            }
        });
    }

    function updateMavlinkStatus(statusData) {
        updateMavlinkStatusBadges(statusData);
        updateMavlinkStatusHearts(statusData);
    }

    function refreshMavlinkStatus() {
        fetch('/api/mavlink/status')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.status) {
                    updateMavlinkStatus(data.status);
                }
            })
            .catch(() => {
                updateMavlinkStatus({ connected: false, is_stale: true, last_message_age_seconds: null });
            });
    }

    refreshMavlinkStatus();
    setInterval(refreshMavlinkStatus, 2000);
});
