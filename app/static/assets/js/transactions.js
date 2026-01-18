// UI/static/assets/js/transactions.js

// --- BIẾN TOÀN CỤC ---
let allCategories = [];
let currentTransactions = [];

// ==============================================
// 1. QUẢN LÝ TAB & DANH MỤC
// ==============================================

// Hàm chuyển Tab (Chi tiêu / Thu nhập / Chuyển khoản)
function switchTab(tabName) {
    const tabExpense = document.getElementById('tab-expense');
    const tabIncome = document.getElementById('tab-income');
    const tabTransfer = document.getElementById('tab-transfer');
    
    const groupCategory = document.getElementById('group-category');
    const groupSourceWallet = document.getElementById('group-source-wallet');
    const groupDestWallet = document.getElementById('group-dest-wallet');

    // 1. Reset active class
    tabExpense.classList.remove('active');
    tabIncome.classList.remove('active');
    tabTransfer.classList.remove('active');
    
    // 2. Xử lý hiển thị theo từng Tab
    if (tabName === 'expense') {
        tabExpense.classList.add('active');
        groupCategory.style.display = 'flex';
        groupSourceWallet.style.display = 'flex';
        groupDestWallet.style.display = 'none';
        document.getElementById('transaction-type').value = 'expense';
        renderCategories('expense'); // Tải danh mục chi tiêu

    } else if (tabName === 'income') {
        tabIncome.classList.add('active');
        groupCategory.style.display = 'flex';
        groupSourceWallet.style.display = 'none';
        groupDestWallet.style.display = 'flex';
        document.getElementById('transaction-type').value = 'income';
        renderCategories('income'); // Tải danh mục thu nhập

    } else if (tabName === 'transfer') {
        tabTransfer.classList.add('active');
        groupCategory.style.display = 'none'; // Chuyển khoản ko cần danh mục
        groupSourceWallet.style.display = 'flex';
        groupDestWallet.style.display = 'flex';
        document.getElementById('transaction-type').value = 'transfer';
    }
}

// Hàm tải tất cả danh mục từ Server (Chạy 1 lần khi load trang)
async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        allCategories = await response.json();
        
        // Sau khi tải xong, kiểm tra xem đang ở tab nào để render danh mục đó
        const currentType = document.getElementById('transaction-type').value || 'expense';
        renderCategories(currentType);
    } catch (error) {
        console.error('Lỗi tải danh mục:', error);
    }
}

// 1. Hàm Tải dữ liệu gốc (Chỉ gọi 1 lần hoặc khi data thay đổi)
async function loadTransactions() {
    try {
        const response = await fetch('/api/transactions');
        currentTransactions = await response.json();
        
        // Mặc định hiển thị toàn bộ
        renderList(currentTransactions);
        
    } catch (error) {
        console.error('Lỗi tải giao dịch:', error);
    }
}

// 1. Hàm Tải dữ liệu gốc (Chỉ gọi 1 lần hoặc khi data thay đổi)
async function loadTransactions() {
    try {
        const response = await fetch('/api/transactions');
        currentTransactions = await response.json();
        
        // Mặc định hiển thị toàn bộ
        renderList(currentTransactions);
        
    } catch (error) {
        console.error('Lỗi tải giao dịch:', error);
    }
}

function renderList(data) {
    const listContainer = document.querySelector('.transaction-list');
    listContainer.innerHTML = ''; 

    if (data.length === 0) {
        listContainer.innerHTML = '<p style="text-align:center; padding: 20px; color: #999;">Không tìm thấy giao dịch nào.</p>';
        return;
    }

    data.forEach(t => {
        // ... (Copy nguyên đoạn logic tạo thẻ <li> cũ của bạn vào đây) ...
        // ... Từ đoạn: let iconClass = ... đến listContainer.appendChild(li); ...
        
        // Code mẫu tóm tắt để bạn dễ hình dung vị trí:
        let iconClass = 'fa-question';
        let color = '#95a5a6';
        let amountClass = '';
        let sign = '';

        if (t.type === 'chi') {
            iconClass = 'fa-utensils'; color = '#dc3545'; amountClass = 'amount-expense'; sign = '-';
        } else if (t.type === 'thu') {
            iconClass = 'fa-briefcase'; color = '#28a745'; amountClass = 'amount-income'; sign = '+';
        } else {
            iconClass = 'fa-exchange-alt'; color = '#3498db'; amountClass = 'amount-transfer'; sign = '';
        }

        const li = document.createElement('li');
        li.className = 'transaction-item';
        li.innerHTML = `
            <div class="item-icon" style="background-color: ${color};"><i class="fas ${iconClass}"></i></div>
            <div class="item-info">
                <span class="item-description">${t.description || 'Không có mô tả'}</span>
                <span class="item-category">${t.date} • ${t.category_name}</span>
            </div>
            <div class="item-amount ${amountClass}">${sign} ${parseInt(t.amount).toLocaleString('vi-VN')} đ</div>
            <div class="action-buttons">
                <button class="btn-action btn-edit" onclick="startEdit('${t.id}')"><i class="fas fa-edit"></i></button>
                <button class="btn-action btn-delete" onclick="deleteTransaction('${t.id}')"><i class="fas fa-trash"></i></button>
            </div>
        `;
        listContainer.appendChild(li);
    });
}

// 3. Hàm Lọc dữ liệu (Logic chính)
function filterTransactions() {
    const keyword = document.getElementById('search-keyword').value.toLowerCase();
    const dateStart = document.getElementById('filter-date-start').value;
    const dateEnd = document.getElementById('filter-date-end').value;
    const type = document.getElementById('filter-type').value;

    const filteredData = currentTransactions.filter(t => {
        // 1. Lọc từ khóa (Tìm trong mô tả hoặc tên danh mục)
        const matchKeyword = (t.description && t.description.toLowerCase().includes(keyword)) || 
                             (t.category_name && t.category_name.toLowerCase().includes(keyword));
        
        // 2. Lọc loại giao dịch
        const matchType = type === "" || t.type === type;

        // 3. Lọc khoảng thời gian
        let matchDate = true;
        if (dateStart && t.date < dateStart) matchDate = false;
        if (dateEnd && t.date > dateEnd) matchDate = false;

        return matchKeyword && matchType && matchDate;
    });

    // Vẽ lại danh sách đã lọc
    renderList(filteredData);
}

// 4. Hàm Reset bộ lọc
function resetFilters() {
    document.getElementById('search-keyword').value = '';
    document.getElementById('filter-date-start').value = '';
    document.getElementById('filter-date-end').value = '';
    document.getElementById('filter-type').value = '';
    
    renderList(currentTransactions); // Vẽ lại toàn bộ
}

// Hàm hiển thị danh mục vào Dropdown dựa trên loại (thu/chi)
function renderCategories(typeFilter) {
    const select = document.getElementById('category');
    select.innerHTML = '<option value="">-- Chọn danh mục --</option>';

    // Map từ Frontend Type sang Database Type
    const mapType = {
        'expense': 'chi',
        'income': 'thu',
        'transfer': null
    };
    
    const dbType = mapType[typeFilter];
    if (!dbType) return; 

    // Lọc và tạo option
    const filtered = allCategories.filter(c => c.LoaiDanhMuc === dbType);
    filtered.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat.MaDanhMuc;
        option.textContent = cat.TenDanhMuc;
        select.appendChild(option);
    });
}

// ==============================================
// 2. QUẢN LÝ VÍ (WALLETS)
// ==============================================

async function loadWallets() {
    try {
        const response = await fetch('/api/wallets');
        const wallets = await response.json();
        
        const sourceSelect = document.getElementById('source-wallet');
        const destSelect = document.getElementById('dest-wallet');
        
        // Reset options
        const defaultOpt = '<option value="">-- Chọn ví --</option>';
        sourceSelect.innerHTML = defaultOpt;
        destSelect.innerHTML = defaultOpt;

        if (wallets.length > 0) {
            wallets.forEach(wallet => {
                // Format tiền tệ
                const balance = parseInt(wallet.SoDu).toLocaleString('vi-VN');
                const text = `${wallet.TenNguonTien} (${balance} đ)`;
                
                // Thêm vào Source
                const opt1 = document.createElement('option');
                opt1.value = wallet.MaNguonTien;
                opt1.textContent = text;
                sourceSelect.appendChild(opt1);

                // Thêm vào Dest
                const opt2 = document.createElement('option');
                opt2.value = wallet.MaNguonTien;
                opt2.textContent = text;
                destSelect.appendChild(opt2);
            });
        }
    } catch (error) {
        console.error('Lỗi tải ví:', error);
    }
}

// ==============================================
// 3. QUẢN LÝ GIAO DỊCH (CRUD)
// ==============================================

// Tải danh sách giao dịch
async function loadTransactions() {
    try {
        const response = await fetch('/api/transactions');
        currentTransactions = await response.json(); // Lưu vào biến toàn cục để dùng khi Sửa
        
        const listContainer = document.querySelector('.transaction-list');
        listContainer.innerHTML = ''; 

        if (currentTransactions.length === 0) {
            listContainer.innerHTML = '<p style="text-align:center; padding: 20px; color: #999;">Chưa có giao dịch nào.</p>';
            return;
        }

        currentTransactions.forEach(t => {
            // Xác định icon và màu sắc
            let iconClass = 'fa-question';
            let color = '#95a5a6';
            let amountClass = '';
            let sign = '';

            if (t.type === 'chi') {
                iconClass = 'fa-utensils'; 
                color = '#dc3545'; // Màu Đỏ (Fix cứng)
                amountClass = 'amount-expense';
                sign = '-';
            } else if (t.type === 'thu') {
                iconClass = 'fa-briefcase';
                color = '#28a745'; // Màu Xanh lá (Fix cứng)
                amountClass = 'amount-income';
                sign = '+';
            } else {
                iconClass = 'fa-exchange-alt';
                color = '#3498db'; // Màu Xanh dương
                amountClass = 'amount-transfer';
                sign = '';
            }

const li = document.createElement('li');
            li.className = 'transaction-item';
            li.innerHTML = `
                <div class="item-icon" style="background-color: ${color};">
                    <i class="fas ${iconClass}"></i>
                </div>
                <div class="item-info">
                    <span class="item-description">${t.description || 'Không có mô tả'}</span>
                    <span class="item-category">
                        ${t.date} • ${t.type === 'chuyen' ? 'Chuyển khoản' : t.category_name}
                        ${t.type === 'chuyen' ? `(${t.wallet_name} <i class="fas fa-arrow-right"></i> ${t.dest_wallet_name})` : `(${t.wallet_name})`}
                    </span>
                </div>
                <div class="item-amount ${amountClass}">
                    ${sign} ${parseInt(t.amount).toLocaleString('vi-VN')} đ
                </div>
                
                <div class="action-buttons">
                    <button class="btn-action btn-edit" onclick="startEdit('${t.id}')" title="Sửa">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-action btn-delete" onclick="deleteTransaction('${t.id}')" title="Xóa">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            listContainer.appendChild(li);
        });

    } catch (error) {
        console.error('Lỗi tải giao dịch:', error);
    }
}

// Xử lý Thêm mới hoặc Cập nhật
async function handleAddTransaction(event) {
    event.preventDefault();

    // Kiểm tra xem đang Thêm hay Sửa
    const editId = document.getElementById('edit-transaction-id').value;
    const isEdit = !!editId;

    const url = isEdit ? `/api/transactions/${editId}` : '/api/transactions';
    const method = isEdit ? 'PUT' : 'POST';

    // Lấy dữ liệu từ form
    const data = {
        type: document.getElementById('transaction-type').value,
        amount: document.getElementById('amount').value,
        description: document.getElementById('description').value,
        date: document.getElementById('date').value,
        category_id: document.getElementById('category').value,
        source_wallet_id: document.getElementById('source-wallet').value,
        dest_wallet_id: document.getElementById('dest-wallet').value
    };

    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            alert(isEdit ? 'Cập nhật thành công!' : 'Thêm giao dịch thành công!');
            
            // Reset form và thoát chế độ sửa
            cancelEdit();

            // Cập nhật lại dữ liệu toàn trang
            loadTransactions();
            loadWallets(); // Quan trọng: Cập nhật số dư ví ngay lập tức
        } else {
            alert('Lỗi: ' + result.message);
        }

    } catch (error) {
        console.error('Lỗi kết nối:', error);
    }
}

// Xóa giao dịch
async function deleteTransaction(id) {
    if (!confirm('Bạn có chắc muốn xóa giao dịch này? Tiền sẽ được hoàn lại vào ví.')) return;

    try {
        const response = await fetch(`/api/transactions/${id}`, { method: 'DELETE' });
        
        if (response.ok) {
            loadTransactions();
            loadWallets(); // Cập nhật số dư
        } else {
            alert('Xóa thất bại.');
        }
    } catch (error) {
        console.error('Lỗi xóa:', error);
    }
}

// ==============================================
// 4. CHỨC NĂNG SỬA (EDIT MODE)
// ==============================================

function startEdit(id) {
    // Tìm giao dịch trong biến toàn cục
    const t = currentTransactions.find(item => item.id === id);
    if (!t) return;

    // 1. Cuộn lên form
    document.querySelector('.transaction-form-card').scrollIntoView({ behavior: 'smooth' });

    // 2. Điền thông tin cơ bản
    document.getElementById('edit-transaction-id').value = t.id;
    document.getElementById('amount').value = t.amount;
    document.getElementById('description').value = t.description;
    document.getElementById('date').value = t.date;

    // 3. Chuyển Tab phù hợp
    // (Database lưu 'chi'/'thu' -> Frontend dùng 'expense'/'income')
    let tabMode = 'expense';
    if (t.type === 'thu') tabMode = 'income';
    else if (t.type === 'chuyen') tabMode = 'transfer';

    switchTab(tabMode);

    // 4. Điền Ví và Danh mục
    // Dùng setTimeout để đảm bảo Dropdown đã được render xong sau khi switchTab
    setTimeout(() => {
        // --- ĐIỀN DANH MỤC ---
        const catSelect = document.getElementById('category');
        // Kiểm tra xem có dropdown danh mục không (Chuyển khoản không có)
        if (catSelect && t.category_id) {
            catSelect.value = t.category_id;
        }

        // --- ĐIỀN VÍ ---
        const sourceSelect = document.getElementById('source-wallet');
        const destSelect = document.getElementById('dest-wallet');

        if (tabMode === 'income') {
            // Thu nhập: Ví nhận tiền được lưu trong MaNguonTien (wallet_id)
            // nên ta điền nó vào ô "Đến nguồn tiền" (dest-wallet)
            if (destSelect) destSelect.value = t.wallet_id;
        } 
        else if (tabMode === 'transfer') {
            // Chuyển khoản: Cần điền cả 2 ví
            if (sourceSelect) sourceSelect.value = t.wallet_id;      // Ví nguồn
            if (destSelect) destSelect.value = t.dest_wallet_id; // Ví đích
        } 
        else { // expense (Chi tiêu)
            // Chi tiêu: Ví trả tiền là MaNguonTien
            if (sourceSelect) sourceSelect.value = t.wallet_id;
        }

    }, 100); // Chờ 100ms để DOM cập nhật

    // 5. Đổi giao diện nút "Lưu" thành "Cập nhật"
    const btnSave = document.getElementById('btn-save');
    btnSave.innerHTML = 'Cập nhật Giao dịch';
    btnSave.style.backgroundColor = "#f39c12"; // Màu cam để cảnh báo đang sửa
    
    const btnCancel = document.getElementById('btn-cancel-edit');
    if(btnCancel) btnCancel.style.display = 'block'; // Hiện nút Hủy
}

function cancelEdit() {
    document.getElementById('transaction-form').reset();
    document.getElementById('edit-transaction-id').value = '';
    
    const btnSave = document.getElementById('btn-save');
    btnSave.textContent = "Lưu Giao dịch";
    btnSave.style.backgroundColor = ""; // Reset màu
    
    const btnCancel = document.getElementById('btn-cancel-edit');
    if(btnCancel) btnCancel.style.display = 'none';

    document.getElementById('date').valueAsDate = new Date();
    switchTab('expense');
}

// Gán sự kiện nút Hủy
document.addEventListener('DOMContentLoaded', function() {
    const btnCancel = document.getElementById('btn-cancel-edit');
    if(btnCancel) {
        btnCancel.addEventListener('click', cancelEdit);
    }
});

// ==============================================
// 5. KHỞI TẠO
// ==============================================
document.addEventListener('DOMContentLoaded', function() {
    switchTab('expense');
    
    const form = document.getElementById('transaction-form');
    if (form) {
        form.addEventListener('submit', handleAddTransaction);
    }

    loadTransactions();
    loadWallets();
    loadCategories();

    document.getElementById('search-keyword').addEventListener('keyup', filterTransactions);
    document.getElementById('filter-date-start').addEventListener('change', filterTransactions);
    document.getElementById('filter-date-end').addEventListener('change', filterTransactions);
    document.getElementById('filter-type').addEventListener('change', filterTransactions);
});

// ... (Các code cũ giữ nguyên) ...

// --- TÍCH HỢP AI GỢI Ý DANH MỤC ---
const descInput = document.getElementById('description');
const aiIcon = document.getElementById('ai-loading-icon');

if (descInput) {
    descInput.addEventListener('blur', async function() {
        const text = this.value.trim();
        if (!text) return;

        // Bỏ qua nếu đang ở tab chuyển khoản
        const currentTab = document.getElementById('transaction-type').value;
        if (currentTab === 'transfer') return;

        if(aiIcon) aiIcon.style.display = 'inline-block';

        try {
            const response = await fetch('/api/predict-category', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ description: text })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                const catSelect = document.getElementById('category');
                
                // --- LOGIC MỚI: TỰ ĐỘNG CHUYỂN TAB ---
                // Map từ DB (thu/chi) sang Frontend (income/expense)
                const typeMap = { 'thu': 'income', 'chi': 'expense' };
                const predictedTab = typeMap[data.category_type]; // Ví dụ: 'income'

                // Nếu loại dự đoán KHÁC loại hiện tại -> Chuyển tab ngay
                if (predictedTab && predictedTab !== currentTab) {
                    switchTab(predictedTab);
                    // Thông báo nhẹ cho user biết
                    console.log(`AI đã tự động chuyển sang tab ${predictedTab}`);
                }
                // --------------------------------------

                // Sau khi chuyển tab xong, dropdown đã có danh mục đúng -> Chọn nó
                if(catSelect) {
                    catSelect.value = data.category_id;
                    
                    // Hiệu ứng báo hiệu thành công
                    catSelect.style.transition = "all 0.3s";
                    catSelect.style.border = "2px solid #2ecc71"; 
                    catSelect.style.boxShadow = "0 0 10px rgba(46, 204, 113, 0.3)";
                    setTimeout(() => {
                        catSelect.style.border = "";
                        catSelect.style.boxShadow = "";
                    }, 2000);
                }
            }
        } catch (error) {
            console.error("AI Error:", error);
        } finally {
            if(aiIcon) aiIcon.style.display = 'none';
        }
    });
}