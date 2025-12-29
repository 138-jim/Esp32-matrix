// LED Display Driver - Web UI JavaScript

let currentConfig = null;

// API base URL
const API_BASE = window.location.origin;

// Update clock display
function updateClock() {
    const now = new Date();

    // Format time as HH:MM:SS
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const timeString = `${hours}:${minutes}:${seconds}`;

    // Format date as "Day, Month DD, YYYY"
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const dateString = now.toLocaleDateString('en-US', options);

    // Update the display
    document.getElementById('clockTime').textContent = timeString;
    document.getElementById('clockDate').textContent = dateString;
}

// Refresh hardware stats
async function refreshHardwareStats() {
    try {
        const response = await fetch(`${API_BASE}/api/system-stats`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const stats = await response.json();

        // Update CPU stats
        document.getElementById('cpuValue').textContent = `${stats.cpu_percent.toFixed(1)}%`;

        // Update CPU temperature
        if (stats.cpu_temp_c !== null) {
            document.getElementById('cpuTempValue').textContent = `${stats.cpu_temp_c}°C`;
        } else {
            document.getElementById('cpuTempValue').textContent = 'N/A';
        }

        // Update RAM stats
        document.getElementById('ramValue').textContent = `${stats.ram_percent.toFixed(1)}%`;

        // Update power stats
        document.getElementById('piPowerValue').textContent = `${stats.pi_power_w}W`;
        document.getElementById('ledPowerValue').textContent = `${stats.led_power_w}W`;
        document.getElementById('totalPowerValue').textContent = `${stats.total_power_w}W`;

        // Update info text
        document.getElementById('piModelInfo').textContent =
            `${stats.pi_model} | ${stats.ram_used_mb.toFixed(0)}MB / ${stats.ram_total_mb.toFixed(0)}MB RAM`;
        document.getElementById('ledCurrentInfo').textContent =
            `${stats.led_count} LEDs @ ${stats.led_current_a.toFixed(2)}A | Max: ${stats.led_max_power_w}W`;

        // Update power limiter info
        if (stats.power_limiter) {
            const limiter = stats.power_limiter;
            let limitText = `Limit: ${limiter.max_current_amps}A`;
            if (limiter.enabled) {
                if (limiter.last_limited_brightness !== null) {
                    limitText += ` | ⚠️ ACTIVE (Limited: ${limiter.limit_applied_count}×)`;
                } else {
                    limitText += ' | ✓ Enabled';
                }
            } else {
                limitText += ' | Disabled';
            }
            document.getElementById('powerLimitInfo').textContent = limitText;
            document.getElementById('powerLimitInfo').style.color =
                (limiter.enabled && limiter.last_limited_brightness !== null) ? '#ff8888' : '#94a3b8';
        }

    } catch (error) {
        console.error('Error refreshing hardware stats:', error);
        // Don't show error message to avoid spam
    }
}

// Load power limit settings
async function loadPowerLimit() {
    try {
        const response = await fetch(`${API_BASE}/api/power-limit`);
        if (response.ok) {
            const limit = await response.json();
            document.getElementById('powerLimitAmps').value = limit.max_current_amps;
            document.getElementById('powerLimitEnabled').checked = limit.enabled;
        }
    } catch (error) {
        console.error('Error loading power limit:', error);
    }
}

// Save power limit settings
async function savePowerLimit() {
    try {
        const maxCurrentAmps = parseFloat(document.getElementById('powerLimitAmps').value);
        const enabled = document.getElementById('powerLimitEnabled').checked;

        const response = await fetch(`${API_BASE}/api/power-limit`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                max_current_amps: maxCurrentAmps,
                enabled: enabled
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        showStatus(`Power limit ${enabled ? 'enabled' : 'disabled'} at ${maxCurrentAmps}A`, 'success');

    } catch (error) {
        console.error('Error saving power limit:', error);
        showStatus(`Error saving power limit: ${error.message}`, 'error');
    }
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    console.log('LED Display Driver UI loaded');
    refreshConfig();
    refreshStatus();
    loadSleepSchedule();
    loadPowerLimit();
    updateClock();  // Initial clock update
    refreshHardwareStats();  // Initial hardware stats update

    // Auto-refresh status every 2 seconds
    setInterval(refreshStatus, 2000);

    // Auto-refresh sleep schedule every 30 seconds
    setInterval(loadSleepSchedule, 30000);

    // Update clock every second
    setInterval(updateClock, 1000);

    // Update hardware stats every 2 seconds
    setInterval(refreshHardwareStats, 2000);
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

// Set elapsed time color
async function setElapsedColor(color) {
    try {
        const response = await fetch(`${API_BASE}/api/elapsed-time-color`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                color: color
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        showStatus(`Elapsed time color set to ${color}`, 'success');

    } catch (error) {
        console.error('Error setting elapsed time color:', error);
        showStatus(`Error setting color: ${error.message}`, 'error');
    }
}

// Save sleep schedule
async function saveSleepSchedule() {
    try {
        const offTime = document.getElementById('sleepOffTime').value;
        const onTime = document.getElementById('sleepOnTime').value;
        const enabled = document.getElementById('sleepEnabled').checked;

        const response = await fetch(`${API_BASE}/api/sleep-schedule`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                off_time: offTime,
                on_time: onTime,
                enabled: enabled
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        const result = await response.json();
        updateSleepStatus(result.schedule);
        showStatus(`Sleep schedule ${enabled ? 'enabled' : 'disabled'}`, 'success');

    } catch (error) {
        console.error('Error saving sleep schedule:', error);
        showStatus(`Error saving schedule: ${error.message}`, 'error');
    }
}

// Load and update sleep schedule status
async function loadSleepSchedule() {
    try {
        const response = await fetch(`${API_BASE}/api/sleep-schedule`);
        if (response.ok) {
            const schedule = await response.json();

            // Update UI with current values
            if (schedule.off_time) {
                document.getElementById('sleepOffTime').value = schedule.off_time;
            }
            if (schedule.on_time) {
                document.getElementById('sleepOnTime').value = schedule.on_time;
            }
            document.getElementById('sleepEnabled').checked = schedule.enabled;

            updateSleepStatus(schedule);
        }
    } catch (error) {
        console.error('Error loading sleep schedule:', error);
    }
}

// Update sleep status display
function updateSleepStatus(schedule) {
    const statusDiv = document.getElementById('sleepStatus');
    if (schedule.enabled) {
        const status = schedule.is_sleeping ? '😴 Display is sleeping' : '✅ Schedule active';
        statusDiv.innerHTML = `${status}<br>Off: ${schedule.off_time} | On: ${schedule.on_time}`;
        statusDiv.style.color = schedule.is_sleeping ? '#e74c3c' : '#27ae60';
    } else {
        statusDiv.innerHTML = 'Schedule disabled';
        statusDiv.style.color = '#7f8c8d';
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
