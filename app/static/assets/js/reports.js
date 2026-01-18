// UI/static/assets/js/reports.js

// --- KHAI BÁO BIẾN TOÀN CỤC ---
let myPieChart = null;
let myBarChart = null;
let myLineChart = null;

// Hàm định dạng tiền tệ Việt Nam (Helper)
const formatter = new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
});

// ============================================================
// 1. HÀM TẢI DỮ LIỆU TỪ BACKEND (API)
// ============================================================
async function loadReportData() {
    const timeRange = document.getElementById('timeFilter').value;
    const walletId = document.getElementById('walletFilter').value;
    const type = document.getElementById('typeFilter').value;

    try {
        // Gọi API backend
        const url = `/api/reports/data?time_range=${timeRange}&wallet_id=${walletId}&type=${type}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error('Lỗi kết nối mạng hoặc server');
        }

        const data = await response.json();

        // Vẽ lại các biểu đồ với dữ liệu mới
        renderPieChart(data.pie_chart);
        renderBarChart(data.bar_chart);
        renderLineChart(data.line_chart);
        renderTopSpendingTable(data.top_spending);

    } catch (error) {
        console.error("Lỗi tải báo cáo:", error);
        // Có thể dùng thư viện thông báo đẹp hơn alert nếu muốn
        // alert("Không thể tải dữ liệu báo cáo. Vui lòng thử lại!");
    }
}

// ============================================================
// 2. CÁC HÀM VẼ BIỂU ĐỒ (Chart.js)
// ============================================================

function renderPieChart(data) {
    const ctx = document.getElementById('pieChart').getContext('2d');
    if (myPieChart) myPieChart.destroy(); // Xóa biểu đồ cũ trước khi vẽ mới

    myPieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.data,
                backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#858796', '#5a5c69'],
                hoverOffset: 4
            }]
        },
        options: {
            maintainAspectRatio: false,
            responsive: true,
            plugins: { 
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += formatter.format(context.raw);
                            return label;
                        }
                    }
                }
            }
        }
    });
}

function renderBarChart(data) {
    const ctx = document.getElementById('barChart').getContext('2d');
    if (myBarChart) myBarChart.destroy();

    myBarChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Số tiền',
                data: data.data,
                // Thêm màu thứ 3 (Màu Xám hoặc Xanh dương nhạt cho Chuyển khoản)
                backgroundColor: [
                    '#1cc88a', // Thu (Xanh lá)
                    '#e74a3b', // Chi (Đỏ)
                    '#36b9cc'  // Chuyển khoản (Xanh dương) <--- MỚI
                ],
                borderRadius: 5
            }]
        },
        options: {
            maintainAspectRatio: false,
            responsive: true,
            scales: { 
                y: { 
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) { return formatter.format(value); }
                    }
                } 
            },
            plugins: { 
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return formatter.format(context.raw);
                        }
                    }
                }
            }
        }
    });
}

function renderLineChart(data) {
    const ctx = document.getElementById('lineChart').getContext('2d');
    if (myLineChart) myLineChart.destroy();

    myLineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Chi tiêu',
                data: data.data,
                borderColor: '#4e73df',
                backgroundColor: 'rgba(78, 115, 223, 0.05)',
                tension: 0.3, // Đường cong mềm mại
                fill: true,
                pointRadius: 3,
                pointHoverRadius: 5
            }]
        },
        options: {
            maintainAspectRatio: false,
            responsive: true,
            scales: { 
                y: { 
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) { return formatter.format(value); }
                    }
                } 
            },
            interaction: { mode: 'index', intersect: false },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatter.format(context.raw);
                        }
                    }
                }
            }
        }
    });
}

// ============================================================
// 3. HÀM RENDER BẢNG & TIỆN ÍCH
// ============================================================

function renderTopSpendingTable(items) {
    const tbody = document.getElementById('topSpendingBody');
    tbody.innerHTML = ''; // Xóa nội dung cũ

    if (!items || items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center">Không có dữ liệu chi tiêu</td></tr>';
        return;
    }

    items.forEach(item => {
        const row = `
            <tr>
                <td>
                    <i class="fas fa-circle" style="color: #4e73df; font-size: 8px; margin-right: 5px;"></i> 
                    ${item.category}
                </td>
                <td style="font-weight: 600;">${item.amount_formatted}</td>
                <td>
                    <div class="progress" style="height: 10px; border-radius: 5px; background-color: #eaecf4;">
                        <div class="progress-bar bg-primary" role="progressbar" 
                             style="width: ${item.percent}%" 
                             aria-valuenow="${item.percent}" aria-valuemin="0" aria-valuemax="100">
                        </div>
                    </div>
                    <small style="color: #858796;">${item.percent}%</small>
                </td>
            </tr>
        `;
        tbody.insertAdjacentHTML('beforeend', row);
    });
}

// Hàm Xuất File (Excel/PDF)
function exportFile(type) {
    const timeRange = document.getElementById('timeFilter').value;
    const walletId = document.getElementById('walletFilter').value;
    
    // Mở tab mới để trình duyệt download/view file từ API backend
    const url = `/api/reports/export/${type}?time_range=${timeRange}&wallet_id=${walletId}`;
    
    if (type === 'pdf') {
        window.open(url, '_blank'); // PDF mở tab mới để in
    } else {
        window.location.href = url; // Excel tải xuống ngay
    }
}

// ============================================================
// 4. KHỞI TẠO & SỰ KIỆN (MAIN)
// ============================================================
document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Load danh sách ví cho bộ lọc (Nếu chưa có sẵn trong HTML)
    // Bạn có thể thêm hàm loadWalletsForFilter() vào đây nếu muốn lọc động
    async function loadWalletsForFilter() {
        try {
            const res = await fetch('/api/wallets');
            const wallets = await res.json();
            const select = document.getElementById('walletFilter');
            // Giữ nguyên option đầu tiên "Tất cả"
            select.innerHTML = '<option value="all">Tất cả Nguồn tiền</option>'; 
            
            wallets.forEach(w => {
                select.insertAdjacentHTML('beforeend', `<option value="${w.MaNguonTien}">${w.TenNguonTien}</option>`);
            });
        } catch(e) { console.error("Lỗi load ví:", e); }
    }
    // Gọi hàm này nếu bạn muốn dropdown ví tự cập nhật từ DB
    loadWalletsForFilter().then(() => {
        // Load dữ liệu báo cáo sau khi ví đã load xong (để tránh lỗi ID)
        loadReportData();
    });

    // 2. Load dữ liệu lần đầu (Nếu không dùng loadWalletsForFilter thì gọi thẳng ở đây)
    // loadReportData(); 

    // 3. Gán sự kiện thay đổi bộ lọc
    document.getElementById('timeFilter').addEventListener('change', loadReportData);
    document.getElementById('walletFilter').addEventListener('change', loadReportData);
    document.getElementById('typeFilter').addEventListener('change', loadReportData);
});