document.addEventListener('DOMContentLoaded', function() {
    
    // ==========================================
    // 0. LOGIC CHUYỂN ĐỔI TAB
    // ==========================================
    const navLinks = document.querySelectorAll('.settings-nav-link');
    const tabPanels = document.querySelectorAll('.tab-panel');

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Lấy ID tab cần mở
            const tabId = this.getAttribute('data-tab');
            
            // Xóa class active cũ
            navLinks.forEach(nav => nav.classList.remove('active'));
            tabPanels.forEach(panel => panel.classList.remove('active'));
            
            // Bật class active cho tab mới
            this.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // ==========================================
    // 1. XỬ LÝ ĐỔI HỌ TÊN
    // ==========================================
    const formProfile = document.getElementById('formUpdateProfile');
    if (formProfile) {
        formProfile.addEventListener('submit', async function(e) {
            e.preventDefault();
            const newName = document.getElementById('fullName').value;
            const btn = this.querySelector('button[type="submit"]');
            const originalText = btn.innerHTML;
            
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang lưu...';
            btn.disabled = true;

            try {
                const res = await fetch('/api/settings/profile', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ fullName: newName })
                });
                const data = await res.json();
                
                if (res.ok && data.status === 'success') {
                    alert('✅ ' + data.message);
                } else {
                    alert('❌ ' + data.message);
                }
            } catch (err) {
                alert('Lỗi kết nối máy chủ!');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }

    // ==========================================
    // 2. XỬ LÝ ĐỔI MẬT KHẨU
    // ==========================================
    const formPassword = document.getElementById('formUpdatePassword');
    if (formPassword) {
        formPassword.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const currentPassword = document.getElementById('currentPassword').value;
            const newPassword = document.getElementById('newPassword').value;
            const confirmNewPassword = document.getElementById('confirmNewPassword').value;
            
            if (newPassword !== confirmNewPassword) {
                alert('❌ Mật khẩu mới không khớp nhau!');
                return;
            }

            const btn = this.querySelector('button[type="submit"]');
            const originalText = btn.innerHTML;
            
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xử lý...';
            btn.disabled = true;

            try {
                const res = await fetch('/api/settings/password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        currentPassword: currentPassword,
                        newPassword: newPassword,
                        confirmNewPassword: confirmNewPassword
                    })
                });
                const data = await res.json();
                
                if (res.ok && data.status === 'success') {
                    alert('✅ ' + data.message);
                    formPassword.reset(); // Xóa trắng form sau khi đổi thành công
                } else {
                    alert('❌ ' + data.message);
                }
            } catch (err) {
                alert('Lỗi kết nối máy chủ!');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }
});