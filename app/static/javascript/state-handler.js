document.addEventListener('DOMContentLoaded', function () {
    const socket = io();
    let currentState = 'UNAVAILABLE'; // Track current state

    socket.on('state_change', function (data) {
        hideLoadingIndicator();
        updateButtonState(data.state);
        currentState = data.state; // Update current state

        // Update the UI elements based on state
        if (data.folder) {
            const folderNameInput = document.getElementById('folderNameInput');
            if (folderNameInput) {
                folderNameInput.value = data.folder;
            }
        }
    });

    // Handle video feed load events
    const videoFeed = document.getElementById('live_feed');
    if (videoFeed) {
        // Check if the video feed is already loaded
        if (videoFeed.complete && videoFeed.naturalWidth !== 0) {
            hideLoadingIndicator();
        } else {
            // Listen for the load event
            videoFeed.onload = function () {
                hideLoadingIndicator();
            };

            // Safety timeout - hide loading after 10 seconds regardless
            setTimeout(function () {
                hideLoadingIndicator();
            }, 10000);
        }
    }

    fetch('/api/state')
        .then(response => response.json())
        .then(data => {
            currentState = data.state; // Set initial state
            updateButtonState(data.state);
        });

    function showLoadingIndicator(message) {
        const loadingOverlay = document.getElementById('stream-loading');
        const loadingMessage = document.getElementById('loading-message');

        if (loadingOverlay) {
            loadingOverlay.classList.remove('d-none');

            if (loadingMessage && message) {
                loadingMessage.textContent = message;
            }
        }
    }

    function hideLoadingIndicator() {
        const loadingOverlay = document.getElementById('stream-loading');
        if (loadingOverlay) {
            loadingOverlay.classList.add('d-none');
        }
    }

    function updateButtonState(state) {
        const previewButton = document.querySelector('button[onclick="setState(\'PREVIEW\')"]');
        const recordButton = document.querySelector('button[onclick="setState(\'WRITE\')"]');

        if (previewButton) {
            previewButton.className = 'btn btn-dark';
            previewButton.querySelector('i').className = 'fa fa-eye';
            // Remove the disabled attribute completely
            previewButton.disabled = false;
        }

        if (recordButton) {
            recordButton.className = 'btn btn-dark';
            recordButton.querySelector('i').className = 'fa fa-circle text-danger';
            // Remove the disabled attribute completely
            recordButton.disabled = false;
        }

        if (state === 'PREVIEW' && previewButton && recordButton) {
            previewButton.className = 'btn btn-warning';
            previewButton.querySelector('i').className = 'fa fa-eye';

            recordButton.className = 'btn btn-dark';
            recordButton.querySelector('i').className = 'fa fa-circle text-danger';
        } else if (state === 'WRITE' && previewButton && recordButton) {
            recordButton.className = 'btn btn-danger';
            recordButton.querySelector('i').className = 'fa fa-stop';

            previewButton.className = 'btn btn-dark';
        }

        const stateDisplay = document.getElementById('current-state');
        if (stateDisplay) {
            stateDisplay.textContent = `Current State: ${state}`;
        }
    }


    window.setState = function (newState) {
        updateButtonState(newState);
        // Only show loading when entering a new state, not when exiting
        const shouldShowLoading =
            // Show when going from UNAVAILABLE to PREVIEW or WRITE
            (currentState === 'UNAVAILABLE' && (newState === 'PREVIEW' || newState === 'WRITE')) ||
            // Show when going from PREVIEW to WRITE
            (currentState === 'PREVIEW' && newState === 'WRITE') ||
            // Show when stopping recording (WRITE to UNAVAILABLE)
            (currentState === 'WRITE' && newState === 'UNAVAILABLE')

        if (shouldShowLoading) {
            let message = "Initializing camera...";

            if (newState === 'PREVIEW') {
                message = "Starting preview mode...";
            } else if (newState === 'WRITE') {
                message = "Starting recording mode...";
            }

            showLoadingIndicator(message);
        }

        const folderNameInput = document.getElementById('folderNameInput');
        let folderName = '';

        if (folderNameInput) {
            folderName = folderNameInput.value.trim();
        }

        fetch('/api/state', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                state: newState,
                folder_name: folderName
            })
        })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    hideLoadingIndicator();
                    console.error('Failed to change state:', data.error || 'Unknown error');

                    // Show error message to user
                    const errorMsg = data.error || 'Unknown error occurred';
                    const loadingMessage = document.getElementById('loading-message');
                    if (loadingMessage) {
                        loadingMessage.innerHTML = `<span class="text-danger">${errorMsg}</span>`;
                        setTimeout(hideLoadingIndicator, 3000);
                    }
                }
            })
            .catch(error => {
                hideLoadingIndicator();
                console.error('Error changing state:', error);
            });
    };
});