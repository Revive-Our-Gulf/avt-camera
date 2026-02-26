document.addEventListener('DOMContentLoaded', function () {
    function getStatusBadges() {
        return document.querySelectorAll('[data-mavlink-status]');
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

    function refreshMavlinkStatus() {
        fetch('/api/mavlink/status')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.status) {
                    updateMavlinkStatusBadges(data.status);
                }
            })
            .catch(() => {
                updateMavlinkStatusBadges({ connected: false, is_stale: true, last_message_age_seconds: null });
            });
    }

    refreshMavlinkStatus();
    setInterval(refreshMavlinkStatus, 2000);
});
