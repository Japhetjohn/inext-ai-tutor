
let ws = null;
const messageInput = document.getElementById('messageInput');
const chatMessages = document.getElementById('chatMessages');
const sendBtn = document.getElementById('sendBtn');

function connectWebSocket() {
    const userId = localStorage.getItem('user_id');
    if (!userId) return;

    ws = new WebSocket(`ws://${window.location.host}/ws/chat/${userId}`);
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.message) {
            addMessage(data.message, false);
        }
    };

    ws.onclose = function() {
        console.log('WebSocket connection closed');
        setTimeout(connectWebSocket, 1000);
    };
}

function addMessage(message, isUser = true) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
    
    const content = document.createElement('div');
    content.className = 'message-content';
    content.innerHTML = message;
    
    messageDiv.appendChild(content);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function handleSend() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    addMessage(message, true);
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(message);
    }
    messageInput.value = '';
}

sendBtn.addEventListener('click', handleSend);

messageInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
    }
});

document.querySelectorAll('.topic-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        messageInput.value = this.textContent;
        handleSend();
    });
});

// Auto-resize textarea
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

connectWebSocket();
