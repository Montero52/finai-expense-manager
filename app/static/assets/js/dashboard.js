// Hàm định dạng tiền tệ
const formatter = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' });

document.addEventListener('DOMContentLoaded', function() {
    loadWallets();
    loadChart();
    loadBudgets();
    loadAISuggestions();
});

// 1. TẢI DỮ LIỆU VÍ TIỀN
async function loadWallets() {
    const container = document.getElementById('wallet-list-container');
    try {
        const response = await fetch('/api/wallets');
        const wallets = await response.json();
        
        container.innerHTML = ''; // Xóa icon loading
        
        if (wallets.length === 0) {
            container.innerHTML = '<p class="text-center w-100" style="color: #999;">Chưa có ví nào. Hãy thêm ví nhé!</p>';
            return;
        }

        const icons = ['fa-wallet', 'fa-credit-card', 'fa-piggy-bank', 'fa-money-bill-wave'];
        const colors = ['#2ecc71', '#3498db', '#e74c3c', '#f1c40f'];

        wallets.forEach((wallet, index) => {
            const icon = icons[index % icons.length];
            const color = colors[index % colors.length];
            
            const html = `
                <div class="wallet-item">
                    <i class="fas ${icon}" style="background-color: ${color};"></i>
                    <h4>${wallet.TenNguonTien}</h4>
                    <p>${formatter.format(wallet.SoDu)}</p>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', html);
        });
    } catch (error) {
        container.innerHTML = '<p class="text-center text-danger w-100">Lỗi tải dữ liệu ví.</p>';
        console.error("Lỗi:", error);
    }
}

// 2. VẼ BIỂU ĐỒ THU CHI THÁNG NÀY
async function loadChart() {
    try {
        // Tận dụng lại API báo cáo đã viết hôm trước
        const response = await fetch('/api/reports/data?time_range=this_month');
        const data = await response.json();
        
        const ctx = document.getElementById('dashboardChart').getContext('2d');
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.bar_chart.labels, // ['Thu nhập', 'Chi tiêu', 'Chuyển khoản']
                datasets: [{
                    label: 'Số tiền',
                    data: data.bar_chart.data,
                    backgroundColor: ['#2ecc71', '#e74c3c', '#3498db'],
                    borderRadius: 5
                }]
            },
            options: {
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { ticks: { callback: function(value) { return formatter.format(value); } } }
                }
            }
        });
    } catch (error) {
        console.error("Lỗi vẽ biểu đồ:", error);
    }
}

// 3. TẢI TIẾN ĐỘ NGÂN SÁCH
async function loadBudgets() {
    const container = document.getElementById('budget-list-container');
    try {
        const response = await fetch('/api/budgets');
        const budgets = await response.json();
        
        container.innerHTML = '';
        
        if (budgets.length === 0) {
            container.innerHTML = '<li class="text-center" style="color: #999;">Bạn chưa thiết lập ngân sách nào.</li>';
            return;
        }

        budgets.forEach(b => {
            const progressColor = b.is_exceeded ? '#e74c3c' : (b.progress > 80 ? '#f39c12' : '#3498db');
            
            const html = `
                <li class="budget-item">
                    <div class="budget-info">
                        <span>${b.name}</span>
                        <span class="${b.is_exceeded ? 'text-danger fw-bold' : ''}">
                            ${formatter.format(b.spent)} / ${formatter.format(b.amount)}
                        </span>
                    </div>
                    <div class="progress-bar-table" style="height: 8px; background-color: #eee; border-radius: 4px; overflow: hidden;">
                        <div style="width: ${b.progress}%; height: 100%; background-color: ${progressColor}; transition: width 0.5s;"></div>
                    </div>
                </li>
            `;
            container.insertAdjacentHTML('beforeend', html);
        });
    } catch (error) {
        container.innerHTML = '<li class="text-center text-danger">Lỗi tải ngân sách.</li>';
        console.error("Lỗi:", error);
    }
}

// 4. LẤY GỢI Ý TỪ AI GEMINI (CÓ BỘ NHỚ ĐỆM CACHE & ĐÃ NÂNG CẤP DÙNG API RIÊNG)
async function loadAISuggestions() {
    const container = document.getElementById('ai-suggestion-container');
    
    // --- BƯỚC 1: KIỂM TRA CACHE TRƯỚC ---
    const cachedData = sessionStorage.getItem('finai_dashboard_insights');
    if (cachedData) {
        // Nếu đã có cache, in ra ngay lập tức không cần đợi
        const insights = JSON.parse(cachedData);
        container.innerHTML = '';
        insights.forEach(text => {
            container.insertAdjacentHTML('beforeend', `<li><i class="fas fa-lightbulb"></i> ${text}</li>`);
        });
        return; // Dừng hàm tại đây, KHÔNG GỌI API NỮA!
    }

    // --- BƯỚC 2: NẾU CHƯA CÓ CACHE THÌ MỚI GỌI API ---
    try {
        const response = await fetch('/api/dashboard-insights');
        const result = await response.json();
        
        container.innerHTML = ''; // Xóa icon loading

        // ==========================================
        //  TRẠM KIỂM SOÁT: BẮT TÍN HIỆU AI BỊ TẮT
        // ==========================================

        if (result.status === 'disabled') {
            container.innerHTML = `
                <div style="text-align: center; color: #858796; padding: 15px 0;">
                    <p style="margin-bottom: 5px; font-weight: 500;">Gợi ý Thông minh đang tắt.</p>
                    <a href="/settings#ai" style="font-size: 0.85rem; color: #4e73df; text-decoration: none;">
                        <i class="fas fa-cog"></i> Bật AI trong Cài đặt
                    </a>
                </div>
            `;
            return; // Dừng hàm ngay lập tức, không chạy các lệnh dưới nữa
        }


        if (result.status === 'success' && result.data.length > 0) {
            
            // LƯU KẾT QUẢ VÀO CACHE CHO LẦN SAU
            sessionStorage.setItem('finai_dashboard_insights', JSON.stringify(result.data));

            // Lặp qua mảng 3 câu khuyên và in ra
            result.data.forEach(text => {
                container.insertAdjacentHTML('beforeend', `<li><i class="fas fa-lightbulb"></i> ${text}</li>`);
            });
        } else {
            throw new Error(result.message || "AI không trả về dữ liệu.");
        }

    } catch (error) {
        container.innerHTML = '<li><i class="fas fa-exclamation-triangle" style="color:#e74c3c;"></i> Hệ thống AI đang bận. Vui lòng quay lại sau.</li>';
        console.error("Lỗi tải AI Dashboard:", error);
    }
}