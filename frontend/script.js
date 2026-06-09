document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');

    // Auto-resize textarea
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value.trim() === '') {
            sendBtn.disabled = true;
        } else {
            sendBtn.disabled = false;
        }
    });

    // Enter to send
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        // Reset input
        userInput.value = '';
        userInput.style.height = 'auto';
        sendBtn.disabled = true;

        // Append user message
        appendMessage('user', text);

        // Append loading message
        const loadingId = 'loading-' + Date.now();
        appendLoading(loadingId);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: text })
            });

            console.log("Raw response status:", response.status);
            const rawText = await response.text();
            console.log("Raw response text:", rawText);

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${rawText}`);
            }

            const data = JSON.parse(rawText);
            
            // Remove loading
            document.getElementById(loadingId).remove();
            
            // Append AI response (parsed via marked if available)
            const htmlContent = typeof marked !== 'undefined' ? marked.parse(data.reply) : data.reply;
            appendMessage('ai', htmlContent, true);

        } catch (error) {
            document.getElementById(loadingId).remove();
            appendMessage('ai', `<p style="color: #ef4444;">Connection error: ${error.message}</p>`, true);
        }
    }

    function appendMessage(sender, content, isHtml = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender === 'user' ? 'user-message' : 'system-message'}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = sender === 'user' ? 'U' : 'AI';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (isHtml) {
            contentDiv.innerHTML = content;
        } else {
            const p = document.createElement('p');
            p.textContent = content;
            contentDiv.appendChild(p);
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        
        scrollToBottom();
    }

    function appendLoading(id) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system-message';
        messageDiv.id = id;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = 'AI';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        
        const dot1 = document.createElement('div');
        dot1.className = 'dot';
        const dot2 = document.createElement('div');
        dot2.className = 'dot';
        const dot3 = document.createElement('div');
        dot3.className = 'dot';
        
        indicator.appendChild(dot1);
        indicator.appendChild(dot2);
        indicator.appendChild(dot3);
        
        contentDiv.appendChild(indicator);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        
        scrollToBottom();
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
