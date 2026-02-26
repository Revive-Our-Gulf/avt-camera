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
            badge.className = 'badge';

            if (!statusData.connected) {
                badge.classList.add('bg-danger');
                badge.textContent = 'Disconnected';
                return;
            }

            if (statusData.is_stale) {
                badge.classList.add('bg-warning', 'text-dark');
                badge.textContent = 'Stale';
                return;
            }

            badge.classList.add('bg-success');
            if (statusData.last_message_age_seconds !== null) {
                badge.textContent = `Connected (${statusData.last_message_age_seconds}s)`;
            } else {
                badge.textContent = 'Connected';
            }
        });
    }

    function updateMavlinkStatusHearts(statusData) {
        const hearts = getStatusHearts();
        if (!hearts.length) {
            return;
        }

        hearts.forEach((heart) => {
            if (statusData.connected && !statusData.is_stale) {
                heart.classList.remove('fa-heart-crack');
                heart.classList.add('fa-heart');
                heart.classList.remove('text-danger');
                heart.classList.add('text-white');
                return;
            }

            heart.classList.remove('fa-heart');
            heart.classList.add('fa-heart-crack');
            heart.classList.remove('text-white');
            heart.classList.add('text-danger');
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
