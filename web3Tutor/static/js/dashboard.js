// Dashboard Functionality
let timeSpent = parseInt(localStorage.getItem('timeSpent')) || 0;
let timerInterval;
let xpPoints = 100;

function startTimer() {
    timerInterval = setInterval(() => {
        timeSpent++;
        localStorage.setItem('timeSpent', timeSpent);
        updateTimeDisplay();
        updateTimeOnServer();
        
        // Award XP points every 5 minutes
        if (timeSpent % 300 === 0) {
            awardXPPoints(10);
            showNotification('Earned 10 XP points for dedication!', 'success');
        }
    }, 1000);
}

function awardXPPoints(points) {
    xpPoints += points;
    const xpDisplay = document.querySelector('.stat-info p');
    if (xpDisplay) {
        xpDisplay.textContent = xpPoints;
    }
}

function updateTimeDisplay() {
    const timeDisplay = document.querySelector('.stat-info p');
    if (timeDisplay) {
        const hours = Math.floor(timeSpent / 3600);
        const minutes = Math.floor((timeSpent % 3600) / 60);
        const seconds = timeSpent % 60;
        timeDisplay.textContent = `${hours}h ${minutes}m ${seconds}s`;
    }
}

async function updateTimeOnServer() {
    if (timeSpent % 60 === 0) {
        try {
            const response = await fetch('/api/update_time_spent', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ time: 1 })
            });
            if (!response.ok) throw new Error('Failed to update time');
        } catch (error) {
            console.error('Error updating time:', error);
        }
    }
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

function toggleTheme() {
    const body = document.body;
    if (body) {
        const isDark = body.classList.toggle('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        updateThemeElements(isDark);
    }
}

function updateThemeElements(isDark) {
    const root = document.documentElement;
    if (root) {
        if (isDark) {
            root.style.setProperty('--bg-dark', '#1a1a2e');
            root.style.setProperty('--text', '#ecf0f1');
            root.style.setProperty('--card-bg', '#16213e');
        } else {
            root.style.setProperty('--bg-dark', '#ffffff');
            root.style.setProperty('--text', '#333333');
            root.style.setProperty('--card-bg', '#f5f5f5');
        }
    }
}

function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const body = document.body;
    if (body) {
        body.classList.toggle('dark-theme', savedTheme === 'dark');
        updateThemeElements(savedTheme === 'dark');
    }
}

function setupNotesAutosave() {
    const notesTextarea = document.getElementById('userNotes');
    if (notesTextarea) {
        let saveTimeout;
        notesTextarea.addEventListener('input', () => {
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(() => saveNotes(), 1000);
        });
    }
}

async function saveNotes() {
    const notesTextarea = document.getElementById('userNotes');
    if (!notesTextarea) return;

    const notes = notesTextarea.value;
    try {
        const response = await fetch('/api/save_notes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes })
        });

        if (!response.ok) throw new Error('Failed to save notes');

        const saveBtn = document.querySelector('.notes-container .btn');
        if (saveBtn) {
            saveBtn.textContent = 'Saved!';
            setTimeout(() => saveBtn.textContent = 'Save Notes', 2000);
        }
    } catch (error) {
        console.error('Error saving notes:', error);
        showNotification('Failed to save notes', 'error');
    }
}

async function startPath(level) {
    try {
        const response = await fetch('/api/start_learning_path', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ level })
        });

        if (!response.ok) throw new Error('Failed to start learning path');

        const result = await response.json();
        if (result.path_id) {
            window.location.href = `/roadmap/${result.path_id}`;
            showNotification('Learning path started! +50 XP');
        }
    } catch (error) {
        console.error('Error starting learning path:', error);
        showNotification('Failed to start learning path', 'error');
    }
}

function initializeWallet() {
    const connectWalletBtn = document.getElementById('connectWalletBtn');
    const walletSelect = document.getElementById('walletSelect');
    const walletAddress = document.getElementById('walletAddress');

    if (connectWalletBtn && walletSelect && walletAddress) {
        connectWalletBtn.addEventListener('click', async () => {
            const selectedWallet = walletSelect.value;
            if (!selectedWallet) {
                showNotification('Please select a wallet', 'error');
                return;
            }

            try {
                if (selectedWallet === 'metamask' && typeof window.ethereum !== 'undefined') {
                    const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                    const address = accounts[0];
                    walletAddress.textContent = `${address.slice(0, 6)}...${address.slice(-4)}`;
                    connectWalletBtn.textContent = 'Connected';
                    connectWalletBtn.disabled = true;
                    await updateWalletConnection(address);
                } else {
                    showNotification('Please install the selected wallet', 'error');
                }
            } catch (error) {
                console.error('Error connecting wallet:', error);
                showNotification('Failed to connect wallet', 'error');
            }
        });
    }
}

async function updateWalletConnection(address) {
    try {
        const response = await fetch('/api/update_wallet', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ wallet_address: address })
        });
        if (!response.ok) throw new Error('Failed to update wallet connection');
    } catch (error) {
        console.error('Error updating wallet connection:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    startTimer();

    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    const pathButtons = document.querySelectorAll('.path-card button');
    if (pathButtons) {
        pathButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const pathCard = e.target.closest('.path-card');
                if (pathCard) {
                    const level = pathCard.dataset.level;
                    startPath(level);
                }
            });
        });
    }

    initializeWallet();
    setupNotesAutosave();
    initializeProgressTracking();
});

// Learning Path Functions

// Progress Tracking
function initializeProgressTracking() {
    // Update time spent
    //setInterval(updateTimeSpent, 60000); // Update every minute

    // Initialize progress bars
    const progressBars = document.querySelectorAll('.progress-fill');
    if (progressBars) {
        progressBars.forEach(bar => {
            const percent = bar.getAttribute('data-progress');
            if (percent) {
                bar.style.width = `${percent}%`;
            }
        });
    }
}


// Wallet Connection Update
async function updateTopicProgress(topicId, completed) {
    try {
        const response = await fetch('/update_topic_progress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                topic_id: topicId,
                completed: completed
            })
        });
        const data = await response.json();
        if (data.status === 'success') {
            // Update XP points display
            const xpDisplay = document.querySelector('.stat-info p');
            if (xpDisplay && data.xp_points) {
                xpDisplay.textContent = data.xp_points;
            }
            // Show completion notification
            if (completed) {
                showNotification('Topic completed! +100 XP', 'success');
            }
            return true;
        }
    } catch (error) {
        console.error('Error updating progress:', error);
        showNotification('Error updating progress', 'error');
    }
    return false;
}