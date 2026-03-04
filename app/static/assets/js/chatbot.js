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

    // --- 2. LOGIC XỬ LÝ GIAO DIỆN & HIỆU ỨNG ---
    const sendBtn = document.getElementById('sendChatBtn');
    const chatInput = document.getElementById('chatQuery');
    const chatBody = document.getElementById('chatBody');

    if (!sendBtn || !chatInput) return;

    // Hàm chuyển đổi Markdown của Google Gemini sang HTML thuần
    function parseMarkdown(text) {
        let html = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'); // Xử lý chữ in đậm
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>'); // Xử lý chữ in nghiêng
        html = html.replace(/\n/g, '<br>'); // Xử lý xuống dòng
        return html;
    }

    // Hàm hiển thị tin nhắn (có hỗ trợ hiệu ứng gõ chữ)
    function appendMessage(text, sender, isTyping = false) {
        const div = document.createElement('div');
        div.className = `chat-message ${sender}`;
        const p = document.createElement('p');
        div.appendChild(p);
        chatBody.appendChild(div);

        const htmlContent = parseMarkdown(text);

        if (isTyping && sender === 'ai') {
            // HIỆU ỨNG GÕ CHỮ (Typing Effect)
            let i = 0;
            let isTag = false;
            let currentHTML = '';
            
            function typeChar() {
                if (i < htmlContent.length) {
                    let char = htmlContent.charAt(i);
                    currentHTML += char;
                    
                    // Nhận diện thẻ HTML (như <br> hoặc <strong>) để gõ nhanh qua, tránh bị vỡ giao diện
                    if (char === '<') isTag = true;
                    if (char === '>') isTag = false;
                    
                    p.innerHTML = currentHTML;
                    chatBody.scrollTop = chatBody.scrollHeight; // Cuộn liên tục khi đang gõ
                    i++;
                    
                    // Gõ tức thì (0ms) nếu là thẻ HTML, gõ chậm (15ms) nếu là chữ thường
                    setTimeout(typeChar, isTag ? 0 : 15);
                }
            }
            typeChar();
        } else {
            // Hiển thị ngay lập tức (dùng cho User hoặc khi tải Lịch sử chat)
            p.innerHTML = htmlContent;
            chatBody.scrollTop = chatBody.scrollHeight;
        }
    }

    // --- 3. LOGIC GIAO TIẾP VỚI SERVER (API) ---
    async function handleChat() {
        const message = chatInput.value.trim();
        if (!message) return;

        // 1. In câu hỏi của User
        appendMessage(message, 'user', false);
        chatInput.value = ''; 

        // 2. Tạo khung Chatbot trống và icon đang tải
        const aiMessageId = 'ai-' + Date.now();
        const div = document.createElement('div');
        div.className = 'chat-message ai';
        const p = document.createElement('p');
        p.id = aiMessageId;
        p.innerHTML = '<em><i class="fas fa-circle-notch fa-spin"></i></em>';
        div.appendChild(p);
        chatBody.appendChild(div);
        chatBody.scrollTop = chatBody.scrollHeight;

        try {
            // 3. Gửi Request lên API
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            });

            // Nếu server trả về lỗi JSON (không phải stream)
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                const data = await response.json();
                p.innerHTML = parseMarkdown(data.response);
                return;
            }

            // 4. HỨNG LUỒNG DỮ LIỆU TỪ SERVER (STREAMING)
            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let fullText = '';
            p.innerHTML = ''; // Xóa icon loading

            while (true) {
                const { done, value } = await reader.read();
                if (done) break; // Khép luồng khi AI nói xong
                
                // Giải mã dữ liệu và cộng dồn vào văn bản
                const chunk = decoder.decode(value, { stream: true });
                fullText += chunk;
                
                // Dịch Markdown và in ra màn hình ngay lập tức
                p.innerHTML = parseMarkdown(fullText);
                chatBody.scrollTop = chatBody.scrollHeight; // Cuộn theo chữ
            }

        } catch (error) {
            console.error("Chat Error:", error);
            p.innerHTML = "Lỗi kết nối server. Vui lòng thử lại sau.";
        }
    }

    // Tải lịch sử chat
    async function loadChatHistory() {
        try {
            const response = await fetch('/api/chat/history');
            if (!response.ok) return; 

            const history = await response.json();
            
            if (history.length > 0) {
                chatBody.innerHTML = ''; 
            }

            history.forEach(msg => {
                // Tải lịch sử thì hiện ngay lập tức, không dùng hiệu ứng gõ
                appendMessage(msg.content, msg.role, false); 
            });

        } catch (error) {
            console.error("Lỗi tải lịch sử chat:", error);
        }
    }

    // --- 4. GẮN SỰ KIỆN LẮNG NGHE ---
    sendBtn.addEventListener('click', handleChat);

    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') handleChat();
    });

    // Khởi chạy khi vào web
    loadChatHistory();
});