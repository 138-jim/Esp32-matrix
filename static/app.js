// LED Display Driver - Web UI JavaScript

let currentConfig = null;

// API base URL
const API_BASE = window.location.origin;

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    console.log('LED Display Driver UI loaded');
    refreshConfig();
    refreshStatus();

    // Auto-refresh status every 2 seconds
    setInterval(refreshStatus, 2000);
});

// Load and display configuration
async function refreshConfig() {
    try {
        const response = await fetch(`${API_BASE}/api/config`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        currentConfig = await response.json();
        displayPanels(currentConfig);
        showStatus('Configuration loaded', 'success');
    } catch (error) {
        console.error('Error loading config:', error);
        showStatus(`Error loading config: ${error.message}`, 'error');
    }
}

// Display panels in the UI
function displayPanels(config) {
    const panelList = document.getElementById('panelList');
    panelList.innerHTML = '';

    if (!config || !config.panels) {
        panelList.innerHTML = '<li>No panels configured</li>';
        return;
    }

    config.panels.forEach((panel, index) => {
        const panelItem = document.createElement('li');
        panelItem.className = 'panel-item';

        panelItem.innerHTML = `
            <div class="panel-item-header">
                <span class="panel-item-title">Panel ${panel.id}</span>
                <span style="color: #94a3b8">Rotation: ${panel.rotation}°</span>
            </div>
            <div class="panel-controls">
                <div>
                    <label>Position X:</label>
                    <input type="number" id="panel_${panel.id}_x" value="${panel.position[0]}"
                           min="0" max="10" onchange="updatePanel(${panel.id})">
                </div>
                <div>
                    <label>Position Y:</label>
                    <input type="number" id="panel_${panel.id}_y" value="${panel.position[1]}"
                           min="0" max="10" onchange="updatePanel(${panel.id})">
                </div>
                <div>
                    <label>Rotation:</label>
                    <select id="panel_${panel.id}_rot" onchange="updatePanel(${panel.id})">
                        <option value="0" ${panel.rotation === 0 ? 'selected' : ''}>0°</option>
                        <option value="90" ${panel.rotation === 90 ? 'selected' : ''}>90°</option>
                        <option value="180" ${panel.rotation === 180 ? 'selected' : ''}>180°</option>
                        <option value="270" ${panel.rotation === 270 ? 'selected' : ''}>270°</option>
                    </select>
                </div>
                <button onclick="updatePanel(${panel.id})">Apply</button>
            </div>
        `;

        panelList.appendChild(panelItem);
    });
}

// Update single panel
async function updatePanel(panelId) {
    try {
        const x = parseInt(document.getElementById(`panel_${panelId}_x`).value);
        const y = parseInt(document.getElementById(`panel_${panelId}_y`).value);
        const rotation = parseInt(document.getElementById(`panel_${panelId}_rot`).value);

        const response = await fetch(`${API_BASE}/api/panels/${panelId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                position: [x, y],
                rotation: rotation
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        showStatus(`Panel ${panelId} updated successfully`, 'success');

        // Refresh config after a short delay to show updated values
        setTimeout(refreshConfig, 500);

    } catch (error) {
        console.error('Error updating panel:', error);
        showStatus(`Error updating panel: ${error.message}`, 'error');
    }
}

// Save entire configuration
async function saveConfig() {
    if (!currentConfig) {
        showStatus('No configuration loaded', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                config: currentConfig
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        showStatus('Configuration saved successfully', 'success');

    } catch (error) {
        console.error('Error saving config:', error);
        showStatus(`Error saving config: ${error.message}`, 'error');
    }
}

// Display test pattern
async function testPattern(patternName) {
    try {
        const response = await fetch(`${API_BASE}/api/test-pattern`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                pattern: patternName,
                duration: 0
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        showStatus(`Pattern started: ${patternName}`, 'success');

    } catch (error) {
        console.error('Error displaying pattern:', error);
        showStatus(`Error displaying pattern: ${error.message}`, 'error');
    }
}

// Stop current test pattern
async function stopPattern() {
    try {
        const response = await fetch(`${API_BASE}/api/stop-pattern`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        showStatus('Pattern stopped', 'success');

    } catch (error) {
        console.error('Error stopping pattern:', error);
        showStatus(`Error stopping pattern: ${error.message}`, 'error');
    }
}

// Set brightness
async function setBrightness() {
    try {
        const brightness = parseInt(document.getElementById('brightness').value);

        const response = await fetch(`${API_BASE}/api/brightness`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                brightness: brightness
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        showStatus(`Brightness set to ${brightness}`, 'success');
        refreshStatus();

    } catch (error) {
        console.error('Error setting brightness:', error);
        showStatus(`Error setting brightness: ${error.message}`, 'error');
    }
}

// Update brightness display value
function updateBrightnessDisplay(value) {
    document.getElementById('brightnessValue').textContent = value;
}

// Refresh system status
async function refreshStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const status = await response.json();

        // Update status displays
        document.getElementById('fpsValue').textContent = status.fps.toFixed(1);
        document.getElementById('queueValue').textContent = status.queue_size;
        document.getElementById('ledValue').textContent = status.led_count;
        document.getElementById('widthValue').textContent = status.width;
        document.getElementById('heightValue').textContent = status.height;
        document.getElementById('currentBrightness').textContent = status.brightness;

        // Update brightness slider if significantly different
        const currentSlider = parseInt(document.getElementById('brightness').value);
        if (Math.abs(currentSlider - status.brightness) > 5) {
            document.getElementById('brightness').value = status.brightness;
            document.getElementById('brightnessValue').textContent = status.brightness;
        }

    } catch (error) {
        console.error('Error refreshing status:', error);
        // Don't show error message for status updates to avoid spam
    }
}

// Show status message
function showStatus(message, type = 'info') {
    const statusDiv = document.getElementById('statusMessage');
    statusDiv.textContent = message;
    statusDiv.className = '';

    if (type === 'error') {
        statusDiv.classList.add('error');
    } else if (type === 'success') {
        statusDiv.classList.add('success');
    }

    // Auto-clear after 5 seconds
    setTimeout(() => {
        if (statusDiv.textContent === message) {
            statusDiv.textContent = '';
            statusDiv.className = '';
        }
    }, 5000);
}
