// static/assets/js/foundations.js

// ==================== QUẢN LÝ VÍ (WALLETS) ====================
let currentWallets = []; // Biến toàn cục lưu danh sách ví

// 1. Tải danh sách và thêm nút Sửa
async function loadWalletsTable() {
    try {
        const response = await fetch('/api/wallets');
        currentWallets = await response.json(); // Lưu lại data
        
        const tableBody = document.querySelector('#wallets .crud-table tbody');
        tableBody.innerHTML = '';

        if (currentWallets.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="4" style="text-align:center">Chưa có ví nào</td></tr>';
            return;
        }

        currentWallets.forEach(w => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${w.TenNguonTien}</td>
                <td>${w.LoaiNguonTien}</td>
                <td style="font-weight: bold; color: #2980b9;">${parseInt(w.SoDu).toLocaleString()} đ</td>
                <td style="text-align: right;">
                    <button  class="btn-action btn-edit" onclick="openEditWallet('${w.MaNguonTien}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-icon btn-delete" onclick="deleteWallet('${w.MaNguonTien}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tableBody.appendChild(tr);
        });
    } catch (error) { console.error(error); }
}

// 2. Hàm mở Modal Sửa
function openEditWallet(id) {
    const w = currentWallets.find(item => item.MaNguonTien === id);
    if(!w) return;

    // Điền dữ liệu cũ
    document.getElementById('edit-wallet-id').value = w.MaNguonTien;
    document.getElementById('walletName').value = w.TenNguonTien;
    document.getElementById('walletType').value = w.LoaiNguonTien;
    document.getElementById('walletBalance').value = w.SoDu;

    // Đổi tiêu đề Modal
    document.getElementById('walletModalTitle').textContent = "Cập nhật Nguồn tiền";
    
    // Mở Modal
    document.getElementById('walletModal').style.display = 'flex';
}

// 3. Xử lý Submit (Thêm hoặc Sửa)
async function handleAddWallet(e) {
    e.preventDefault();
    
    const id = document.getElementById('edit-wallet-id').value;
    const isEdit = !!id; // Có ID là đang sửa

    const url = isEdit ? `/api/wallets/${id}` : '/api/wallets';
    const method = isEdit ? 'PUT' : 'POST';

    const data = {
        name: document.getElementById('walletName').value,
        type: document.getElementById('walletType').value,
        balance: document.getElementById('walletBalance').value
    };

    const res = await fetch(url, {
        method: method,
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    
    if(res.ok) {
        alert(isEdit ? 'Cập nhật thành công!' : 'Thêm ví thành công!');
        document.getElementById('walletForm').reset();
        document.getElementById('edit-wallet-id').value = ''; // Reset ID
        document.getElementById('walletModalTitle').textContent = "Thêm Nguồn tiền"; // Reset tiêu đề
        document.getElementById('walletModal').style.display = 'none';
        loadWalletsTable();
    } else {
        alert('Lỗi xảy ra');
    }
}

async function deleteWallet(id) {
    if(!confirm('Xóa ví này?')) return;
    await fetch(`/api/wallets/${id}`, {method: 'DELETE'});
    loadWalletsTable();
}

// ==================== QUẢN LÝ DANH MỤC (CATEGORIES) ====================
let currentCategories = []; // 1. Biến lưu trữ danh sách

async function loadCategoriesTable() {
    try {
        const response = await fetch('/api/categories');
        currentCategories = await response.json(); // Lưu data vào biến
        
        const tableBody = document.querySelector('#categories .crud-table tbody');
        tableBody.innerHTML = '';

        if (currentCategories.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="4" style="text-align:center">Chưa có danh mục nào</td></tr>';
            return;
        }

        currentCategories.forEach(c => {
            const typeBadge = c.LoaiDanhMuc === 'thu' 
                ? '<span class="type-badge type-income">Thu nhập</span>' 
                : '<span class="type-badge type-expense">Chi tiêu</span>';
                
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${c.TenDanhMuc}</td>
                <td>${typeBadge}</td>
                <td>-</td>
                <td style="text-align: right;">
                    <button  class="btn-action btn-edit" onclick="openEditCategory('${c.MaDanhMuc}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-icon btn-delete" onclick="deleteCategory('${c.MaDanhMuc}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tableBody.appendChild(tr);
        });
    } catch (error) { console.error(error); }
}

// 3. Hàm mở Modal Sửa
function openEditCategory(id) {
    const c = currentCategories.find(item => item.MaDanhMuc === id);
    if(!c) return;

    // Điền dữ liệu cũ
    document.getElementById('edit-category-id').value = c.MaDanhMuc;
    document.getElementById('catName').value = c.TenDanhMuc;
    document.getElementById('catType').value = c.LoaiDanhMuc;

    // Đổi tiêu đề Modal
    document.getElementById('categoryModalTitle').textContent = "Cập nhật Danh mục";
    
    // Mở Modal
    document.getElementById('categoryModal').style.display = 'flex';
}

async function deleteCategory(id) {
    if(!confirm('Xóa danh mục này?')) return;
    await fetch(`/api/categories/${id}`, {method: 'DELETE'});
    loadCategoriesTable();
}

// 4. Xử lý Submit (Thêm hoặc Sửa)
async function handleAddCategory(e) {
    e.preventDefault();
    
    const id = document.getElementById('edit-category-id').value;
    const isEdit = !!id;

    const url = isEdit ? `/api/categories/${id}` : '/api/categories';
    const method = isEdit ? 'PUT' : 'POST';

    const data = {
        name: document.getElementById('catName').value,
        type: document.getElementById('catType').value
    };

    const res = await fetch(url, {
        method: method,
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });

    if(res.ok) {
        alert(isEdit ? 'Cập nhật thành công!' : 'Thêm danh mục thành công!');
        document.getElementById('categoryForm').reset();
        document.getElementById('edit-category-id').value = ''; // Reset ID
        document.getElementById('categoryModalTitle').textContent = "Thêm Danh mục mới"; // Reset tiêu đề
        document.getElementById('categoryModal').style.display = 'none';
        loadCategoriesTable();
    } else {
        alert('Lỗi xảy ra');
    }
}


// ==================== KHỞI TẠO ====================
document.addEventListener('DOMContentLoaded', function() {
    loadWalletsTable();
    loadCategoriesTable();

    const wForm = document.getElementById('walletForm');
    if(wForm) wForm.addEventListener('submit', handleAddWallet);

    const cForm = document.getElementById('categoryForm');
    if(cForm) cForm.addEventListener('submit', handleAddCategory);
});