// Hàm chuyển đổi khung chat khi click vào danh sách bên trái
function switchChat(userId, userName) {
    // 1. Đổi tiêu đề Header
    document.getElementById('current-chat-user').innerText = userName;

    // 2. Ẩn trạng thái rỗng
    document.getElementById('empty-chat-state').style.display = 'none';

    // 3. Ẩn tất cả các khung chat đang mở
    const allPanes = document.querySelectorAll('.chat-content-pane');
    allPanes.forEach(pane => pane.style.display = 'none');

    // 4. Bỏ class active của tất cả danh sách
    const allItems = document.querySelectorAll('.conversation-item');
    allItems.forEach(item => item.classList.remove('active'));

    // 5. Hiển thị khung chat được chọn và set active
    document.getElementById('chat-pane-' + userId).style.display = 'block';
    document.getElementById('nav-user-' + userId).classList.add('active');

    // 6. Cuộn xuống cuối cùng của khung chat
    const chatContainer = document.getElementById('chat-body-container');
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Hàm gọi API xóa Log cũ
async function cleanupLogs() {
    if (!confirm('Hành động này sẽ XÓA VĨNH VIỄN các tin nhắn chatbot cũ hơn 30 ngày để giải phóng dung lượng. Bạn có chắc chắn không?')) {
        return;
    }

    try {
        const res = await fetch('/api/admin/cleanup-logs', { method: 'DELETE' });
        const data = await res.json();
        
        if (res.ok) {
            alert(data.message);
            location.reload();
        } else {
            alert('Lỗi: ' + data.message);
        }
    } catch (e) {
        console.error(e);
        alert('Lỗi kết nối đến máy chủ.');
    }
}

// Auto-click vào người dùng đầu tiên (nếu có) khi load trang
document.addEventListener("DOMContentLoaded", function() {
    const firstUser = document.querySelector('.conversation-item');
    if (firstUser) {
        firstUser.click();
    }
});
