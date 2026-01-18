
document.addEventListener('DOMContentLoaded', function() {
    // --- 1. LOGIC ĐÓNG/MỞ CỬA SỔ CHAT ---
    const chatWindow = document.getElementById('aiChatWindow');
    const openBtn = document.getElementById('openChatBtn');
    const closeBtn = document.getElementById('closeChatBtn');

    if (openBtn) {
        openBtn.addEventListener('click', () => {
            chatWindow.style.display = 'flex';
            openBtn.style.display = 'none';
            setTimeout(() => document.getElementById('chatQuery').focus(), 100); 
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            chatWindow.style.display = 'none';
            openBtn.style.display = 'flex';
        });
    }

    // --- 2. LOGIC GỬI TIN NHẮN CHO AI ---
    const sendBtn = document.getElementById('sendChatBtn');
    const chatInput = document.getElementById('chatQuery');
    const chatBody = document.getElementById('chatBody');

    if (!sendBtn || !chatInput) return;

    function appendMessage(text, sender) {
        const div = document.createElement('div');
        div.className = `chat-message ${sender}`;
        div.innerHTML = `<p>${text}</p>`;
        chatBody.appendChild(div);
        chatBody.scrollTop = chatBody.scrollHeight; 
    }

    async function handleChat() {
        const message = chatInput.value.trim();
        if (!message) return;

        appendMessage(message, 'user');
        chatInput.value = ''; 

        const loadingId = 'loading-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'chat-message ai';
        loadingDiv.id = loadingId;
        loadingDiv.innerHTML = `<p><em>Đang suy nghĩ... <i class="fas fa-spinner fa-spin"></i></em></p>`;
        chatBody.appendChild(loadingDiv);
        chatBody.scrollTop = chatBody.scrollHeight;

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();
            
            if (data.response) {
                const formattedText = data.response.replace(/\n/g, '<br>');
                appendMessage(formattedText, 'ai');
            } else {
                appendMessage("Xin lỗi, tôi không nhận được phản hồi.", 'ai');
            }

        } catch (error) {
            console.error("Chat Error:", error);
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();
            appendMessage("Lỗi kết nối server. Vui lòng thử lại sau.", 'ai');
        }
    }

        async function loadChatHistory() {
        try {
            const response = await fetch('/api/chat/history');
            if (!response.ok) return; // Nếu chưa đăng nhập hoặc lỗi thì thôi

            const history = await response.json();
            
            // Xóa tin nhắn chào mặc định (nếu có lịch sử)
            if (history.length > 0) {
                chatBody.innerHTML = ''; 
            }

            history.forEach(msg => {
                // Tái sử dụng hàm appendMessage cũ nhưng sửa lại format xuống dòng
                const formattedText = msg.content.replace(/\n/g, '<br>');
                appendMessage(formattedText, msg.role);
            });

        } catch (error) {
            console.error("Lỗi tải lịch sử chat:", error);
        }
    }

    sendBtn.addEventListener('click', handleChat);

    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') handleChat();
    });

    loadChatHistory();
});

