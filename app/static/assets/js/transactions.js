// UI/static/assets/js/transactions.js

// --- BIẾN TOÀN CỤC ---
let allCategories = [];
let currentTransactions = [];
let lastDescription = ''; // Biến mới: Lưu lại câu mô tả cũ để AI không đoán lại nhiều lần

// ==============================================
// 1. QUẢN LÝ TAB & DANH MỤC
// ==============================================

function switchTab(tabName) {
    const tabExpense = document.getElementById('tab-expense');
    const tabIncome = document.getElementById('tab-income');
    const tabTransfer = document.getElementById('tab-transfer');
    
    const groupCategory = document.getElementById('group-category');
    const groupSourceWallet = document.getElementById('group-source-wallet');
    const groupDestWallet = document.getElementById('group-dest-wallet');

    tabExpense.classList.remove('active');
    tabIncome.classList.remove('active');
    tabTransfer.classList.remove('active');
    
    if (tabName === 'expense') {
        tabExpense.classList.add('active');
        groupCategory.style.display = 'flex';
        groupSourceWallet.style.display = 'flex';
        groupDestWallet.style.display = 'none';
        document.getElementById('transaction-type').value = 'expense';
        renderCategories('expense'); 

    } else if (tabName === 'income') {
        tabIncome.classList.add('active');
        groupCategory.style.display = 'flex';
        groupSourceWallet.style.display = 'none';
        groupDestWallet.style.display = 'flex';
        document.getElementById('transaction-type').value = 'income';
        renderCategories('income'); 

    } else if (tabName === 'transfer') {
        tabTransfer.classList.add('active');
        groupCategory.style.display = 'none'; 
        groupSourceWallet.style.display = 'flex';
        groupDestWallet.style.display = 'flex';
        document.getElementById('transaction-type').value = 'transfer';
    }
}

async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        allCategories = await response.json();
        const currentType = document.getElementById('transaction-type').value || 'expense';
        renderCategories(currentType);
    } catch (error) {
        console.error('Lỗi tải danh mục:', error);
    }
}

function renderCategories(typeFilter) {
    const select = document.getElementById('category');
    if (!select) return;
    
    select.innerHTML = '<option value="">-- Chọn danh mục --</option>';
    const mapType = { 'expense': 'chi', 'income': 'thu', 'transfer': null };
    const dbType = mapType[typeFilter];
    
    if (!dbType) return; 

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
        
        const defaultOpt = '<option value="">-- Chọn ví --</option>';
        if(sourceSelect) sourceSelect.innerHTML = defaultOpt;
        if(destSelect) destSelect.innerHTML = defaultOpt;

        if (wallets.length > 0) {
            wallets.forEach(wallet => {
                const balance = formatMoney(wallet.SoDu); 
                const text = `${wallet.TenNguonTien} (${balance})`;
                
                if(sourceSelect) {
                    const opt1 = document.createElement('option');
                    opt1.value = wallet.MaNguonTien; opt1.textContent = text;
                    sourceSelect.appendChild(opt1);
                }
                if(destSelect) {
                    const opt2 = document.createElement('option');
                    opt2.value = wallet.MaNguonTien; opt2.textContent = text;
                    destSelect.appendChild(opt2);
                }
            });
        }
    } catch (error) { console.error('Lỗi tải ví:', error); }
}

// ==============================================
// 3. DANH SÁCH & LỌC GIAO DỊCH (ĐÃ TỐI ƯU HỢP NHẤT)
// ==============================================

async function loadTransactions() {
    try {
        const response = await fetch('/api/transactions');
        currentTransactions = await response.json(); 
        renderList(currentTransactions); // Gọi hàm render duy nhất
    } catch (error) {
        console.error('Lỗi tải giao dịch:', error);
    }
}

function renderList(data) {
    const listContainer = document.querySelector('.transaction-list');
    if (!listContainer) return;
    
    listContainer.innerHTML = ''; 

    if (data.length === 0) {
        listContainer.innerHTML = '<p style="text-align:center; padding: 20px; color: #999;">Không có giao dịch nào.</p>';
        return;
    }

    data.forEach(t => {
        let iconClass = 'fa-question', color = '#95a5a6', amountClass = '', sign = '';

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
                ${sign} ${formatMoney(Math.abs(t.amount))}
            </div>
            <div class="action-buttons">
                <button class="btn-action btn-edit" onclick="startEdit('${t.id}')" title="Sửa"><i class="fas fa-edit"></i></button>
                <button class="btn-action btn-delete" onclick="deleteTransaction('${t.id}')" title="Xóa"><i class="fas fa-trash"></i></button>
            </div>
        `;
        listContainer.appendChild(li);
    });
}

function filterTransactions() {
    const keyword = document.getElementById('search-keyword').value.toLowerCase();
    const dateStart = document.getElementById('filter-date-start').value;
    const dateEnd = document.getElementById('filter-date-end').value;
    const type = document.getElementById('filter-type').value;

    const filteredData = currentTransactions.filter(t => {
        const matchKeyword = (t.description && t.description.toLowerCase().includes(keyword)) || 
                             (t.category_name && t.category_name.toLowerCase().includes(keyword));
        const matchType = type === "" || t.type === type;
        let matchDate = true;
        if (dateStart && t.date < dateStart) matchDate = false;
        if (dateEnd && t.date > dateEnd) matchDate = false;

        return matchKeyword && matchType && matchDate;
    });

    renderList(filteredData);
}

// ==============================================
// 4. THÊM / SỬA / XÓA (CRUD)
// ==============================================

async function handleAddTransaction(event) {
    event.preventDefault();
    const editId = document.getElementById('edit-transaction-id').value;
    const isEdit = !!editId;
    const url = isEdit ? `/api/transactions/${editId}` : '/api/transactions';
    const method = isEdit ? 'PUT' : 'POST';

    const data = {
        type: document.getElementById('transaction-type').value,
        amount: parseMoneyToBase(ocument.getElementById('amount').value),
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
            cancelEdit();
            loadTransactions();
            loadWallets(); 
            sessionStorage.removeItem('finai_dashboard_insights');
        } else { alert('Lỗi: ' + result.message); }
    } catch (error) { console.error('Lỗi kết nối:', error); }
}

async function deleteTransaction(id) {
    if (!confirm('Bạn có chắc muốn xóa giao dịch này? Tiền sẽ được hoàn lại vào ví.')) return;
    try {
        const response = await fetch(`/api/transactions/${id}`, { method: 'DELETE' });
        if (response.ok) { 
            loadTransactions(); 
            loadWallets(); 
            sessionStorage.removeItem(' finai_dashboard_insights');
        } 
        else { alert('Xóa thất bại.'); }
    } catch (error) { console.error('Lỗi xóa:', error); }
}

function startEdit(id) {
    const t = currentTransactions.find(item => item.id === id);
    if (!t) return;

    document.querySelector('.transaction-form-card').scrollIntoView({ behavior: 'smooth' });
    document.getElementById('edit-transaction-id').value = t.id;
    document.getElementById('amount').value = formatMoneyForInput(t.amount);
    document.getElementById('description').value = t.description;
    lastDescription = t.description; // Lưu lại để tránh AI chạy khi không cần thiết
    document.getElementById('date').value = t.date;

    let tabMode = 'expense';
    if (t.type === 'thu') tabMode = 'income';
    else if (t.type === 'chuyen') tabMode = 'transfer';
    switchTab(tabMode);

    setTimeout(() => {
        const catSelect = document.getElementById('category');
        if (catSelect && t.category_id) catSelect.value = t.category_id;

        const sourceSelect = document.getElementById('source-wallet');
        const destSelect = document.getElementById('dest-wallet');

        if (tabMode === 'income') { if (destSelect) destSelect.value = t.wallet_id; } 
        else if (tabMode === 'transfer') {
            if (sourceSelect) sourceSelect.value = t.wallet_id;      
            if (destSelect) destSelect.value = t.dest_wallet_id; 
        } 
        else { if (sourceSelect) sourceSelect.value = t.wallet_id; }
    }, 100); 

    const btnSave = document.getElementById('btn-save');
    if(btnSave) {
        btnSave.innerHTML = 'Cập nhật Giao dịch';
        btnSave.style.backgroundColor = "#f39c12"; 
    }
    const btnCancel = document.getElementById('btn-cancel-edit');
    if(btnCancel) btnCancel.style.display = 'block'; 
}

function cancelEdit() {
    document.getElementById('transaction-form').reset();
    document.getElementById('edit-transaction-id').value = '';
    lastDescription = ''; // Reset biến AI
    
    const btnSave = document.getElementById('btn-save');
    if(btnSave) {
        btnSave.textContent = "Lưu Giao dịch";
        btnSave.style.backgroundColor = ""; 
    }
    const btnCancel = document.getElementById('btn-cancel-edit');
    if(btnCancel) btnCancel.style.display = 'none';

    document.getElementById('date').valueAsDate = new Date();
    switchTab('expense');
}

// ==============================================
// 5. TÍCH HỢP AI GỢI Ý DANH MỤC (TỐI ƯU HÓA)
// ==============================================

async function handleAIPrediction() {
    const descInput = document.getElementById('description');
    const aiIcon = document.getElementById('ai-loading-icon');
    
    if (!descInput) return;
    
    const text = descInput.value.trim();
    const currentTab = document.getElementById('transaction-type').value;

    // 3 Chốt chặn an toàn: Bỏ qua nếu rỗng, nếu là chuyển khoản, hoặc nếu text CHƯA THAY ĐỔI
    if (!text || currentTab === 'transfer' || text === lastDescription) return;

    lastDescription = text; // Cập nhật lại câu mới nhất
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
            const typeMap = { 'thu': 'income', 'chi': 'expense' };
            const predictedTab = typeMap[data.category_type]; 

            // AI thông minh: Tự động lật sang tab Thu hoặc Chi nếu đoán khác Tab hiện tại
            if (predictedTab && predictedTab !== currentTab) {
                switchTab(predictedTab);
                console.log(`AI tự động chuyển tab sang: ${predictedTab}`);
            }

            // Đợi 50ms cho DOM của Dropdown load xong danh mục mới (nếu có chuyển tab)
            setTimeout(() => {
                if(catSelect) {
                    catSelect.value = data.category_id;
                    
                    // Hiệu ứng "Ting ting" báo hiệu AI đã điền
                    catSelect.style.transition = "all 0.3s";
                    catSelect.style.border = "2px solid #2ecc71"; 
                    catSelect.style.boxShadow = "0 0 10px rgba(46, 204, 113, 0.3)";
                    setTimeout(() => {
                        catSelect.style.border = "";
                        catSelect.style.boxShadow = "";
                    }, 2000);
                }
            }, 50);
        }
    } catch (error) {
        console.error("AI Error:", error);
    } finally {
        if(aiIcon) aiIcon.style.display = 'none';
    }
}

// ==============================================
// 6. KHỞI TẠO SỰ KIỆN KHI LOAD TRANG
// ==============================================
document.addEventListener('DOMContentLoaded', function() {
    switchTab('expense');
    document.getElementById('date').valueAsDate = new Date();
    
    const form = document.getElementById('transaction-form');
    if (form) form.addEventListener('submit', handleAddTransaction);

    const btnCancel = document.getElementById('btn-cancel-edit');
    if(btnCancel) btnCancel.addEventListener('click', cancelEdit);

    const descInput = document.getElementById('description');
    if (descInput) descInput.addEventListener('blur', handleAIPrediction);

    // Sự kiện tìm kiếm / Lọc
    const searchInputs = ['search-keyword', 'filter-date-start', 'filter-date-end', 'filter-type'];
    searchInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener(id === 'search-keyword' ? 'keyup' : 'change', filterTransactions);
    });

    // Tải dữ liệu ban đầu
    loadWallets();
    loadCategories().then(() => { loadTransactions(); });
});