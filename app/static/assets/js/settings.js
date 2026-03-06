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

    // ==========================================
    // 3. LƯU TÙY CHỈNH (Ngôn ngữ, Tiền tệ)
    // ==========================================
    const formPreferences = document.getElementById('formPreferences');
    if (formPreferences) {
        formPreferences.addEventListener('submit', async function(e) {
            e.preventDefault();
            const btn = this.querySelector('button[type="submit"]');
            const originalText = btn.innerHTML;
            
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang lưu...';
            btn.disabled = true;

            try {
                const res = await fetch('/api/settings/preferences', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        currency: document.getElementById('currency').value,
                        language: document.getElementById('language').value
                    })
                });
                const data = await res.json();
                
                if (res.ok) alert('✅ ' + data.message);
                else alert('❌ ' + data.message);
            } catch (err) {
                alert('Lỗi kết nối máy chủ!');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }

    // ==========================================
    // 4. BẬT/TẮT AI (Tự động lưu khi gạt nút)
    // ==========================================
    const aiToggle = document.getElementById('aiSuggestion');
    const aiLabel = document.getElementById('aiStatusLabel');
    
    if (aiToggle) {
        aiToggle.addEventListener('change', async function() {
            // Tạm thời vô hiệu hóa nút gạt để chờ API
            this.disabled = true;
            aiLabel.innerText = "Đang xử lý...";
            
            const isChecked = this.checked;

            try {
                const res = await fetch('/api/settings/ai', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ aiSuggestion: isChecked })
                });
                const data = await res.json();
                
                if (res.ok) {
                    // Cập nhật nhãn bằng chữ cho đẹp
                    aiLabel.innerText = isChecked ? "Đang Bật" : "Đang Tắt";
                } else {
                    alert('❌ ' + data.message);
                    this.checked = !isChecked; // Trả lại trạng thái cũ nếu lỗi
                    aiLabel.innerText = !isChecked ? "Đang Bật" : "Đang Tắt";
                }
            } catch (err) {
                alert('Lỗi kết nối máy chủ!');
                this.checked = !isChecked;
                aiLabel.innerText = !isChecked ? "Đang Bật" : "Đang Tắt";
            } finally {
                this.disabled = false;
            }
        });
    }
});