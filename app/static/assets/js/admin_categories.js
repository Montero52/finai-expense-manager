document.addEventListener('DOMContentLoaded', function () {
    const categoryForm = document.getElementById('admin-category-form');
    const idHidden = document.getElementById('edit-category-id');
    const nameInput = document.getElementById('category-name');
    const typeSelect = document.getElementById('category-type');
    const submitBtn = document.getElementById('submit-btn');
    const cancelBtn = document.getElementById('cancel-edit-btn');
    const btnTextEl = document.getElementById('btn-text');
    const tableBody = document.getElementById('admin-categories-body');

    let adminCategories = [];

    // 1. Tải danh sách danh mục từ API
    async function loadAdminCategories() {
        try {
            console.log("Đang gọi API lấy danh mục...");
            const res = await fetch('/api/admin/categories');
            if (!res.ok) throw new Error("Không thể kết nối API");
            
            adminCategories = await res.json();
            console.log("Dữ liệu nhận được:", adminCategories); // Kiểm tra xem id, name có đúng không
            
            renderTable();
        } catch (err) {
            console.error('Lỗi tải danh mục:', err);
            tableBody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:red;">Lỗi tải dữ liệu. Vui lòng kiểm tra Console.</td></tr>`;
        }
    }

    // 2. Vẽ bảng dữ liệu
    function renderTable() {
        tableBody.innerHTML = '';
        
        if (adminCategories.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="4" style="text-align:center;">Chưa có danh mục nào.</td></tr>`;
            return;
        }

        adminCategories.forEach(cat => {
            // Đảm bảo dùng đúng cat.id và cat.name từ Backend gửi về
            const typeLabel = cat.type === 'thu' ? 'Thu nhập' : 'Chi tiêu';
            const typeClass = cat.type === 'thu' ? 'badge-success' : 'badge-danger';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${cat.id}</td>
                <td><strong>${cat.name}</strong></td>
                <td><span class="badge ${typeClass}">${typeLabel}</span></td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="adminEditCategory(${cat.id})">
                        <i class="fas fa-edit"></i> Sửa
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="adminDeleteCategory(${cat.id})">
                        <i class="fas fa-trash"></i> Xóa
                    </button>
                </td>
            `;
            tableBody.appendChild(tr);
        });
    }

    // 3. Xử lý gửi Form (Thêm hoặc Cập nhật)
    categoryForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        // CHÚ Ý: idHidden.value lúc này là số (Integer) hoặc rỗng
        const payload = {
            id: idHidden.value ? parseInt(idHidden.value) : null,
            name: nameInput.value.trim(),
            type: typeSelect.value
        };

        try {
            const res = await fetch('/api/admin/categories', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const result = await res.json();
            if (res.ok) {
                resetForm();
                loadAdminCategories();
            } else {
                alert('Lỗi: ' + (result.message || 'Không thể lưu danh mục'));
            }
        } catch (err) {
            console.error(err);
            alert('Lỗi kết nối tới server.');
        }
    });

    // 4. Chế độ sửa
    window.adminEditCategory = function (id) {
        const cat = adminCategories.find(c => c.id === id);
        if (!cat) return;

        idHidden.value = cat.id;
        nameInput.value = cat.name;
        typeSelect.value = cat.type;

        btnTextEl.textContent = 'Cập nhật';
        submitBtn.classList.replace('btn-primary', 'btn-warning');
        cancelBtn.style.display = 'inline-block';
        nameInput.focus();
    };

    // 5. Xóa danh mục
    window.adminDeleteCategory = async function (id) {
        if (!confirm('Bạn có chắc muốn xóa danh mục gốc này?')) return;

        try {
            const res = await fetch(`/api/admin/categories/${id}`, { method: 'DELETE' });
            if (res.ok) {
                loadAdminCategories();
            } else {
                alert('Xóa danh mục thất bại.');
            }
        } catch (err) {
            console.error(err);
        }
    };

    function resetForm() {
        categoryForm.reset();
        idHidden.value = '';
        btnTextEl.textContent = 'Thêm danh mục';
        submitBtn.classList.replace('btn-warning', 'btn-primary');
        cancelBtn.style.display = 'none';
    }

    cancelBtn.addEventListener('click', resetForm);

    loadAdminCategories();
});