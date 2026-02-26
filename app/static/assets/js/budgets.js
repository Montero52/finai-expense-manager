document.addEventListener("DOMContentLoaded", function() {
    // --- UI Modal Logic ---
    const modal = document.getElementById('budgetModal');
    
    document.getElementById('openBudgetModal').onclick = () => {
        modal.style.display = 'flex';
        loadCategoriesForModal(); // Tải danh mục mỗi khi mở modal
    }
    document.getElementById('closeBudgetModal').onclick = () => modal.style.display = 'none';
    document.getElementById('cancelBudgetModal').onclick = (e) => { 
        e.preventDefault(); 
        modal.style.display = 'none'; 
    };

    // --- Core Logic ---
    function formatMoney(amount) {
        return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount);
    }

    // Tải danh mục vào Modal
    async function loadCategoriesForModal() {
        try {
            const res = await fetch('/api/categories');
            const categories = await res.json();
            const container = document.getElementById('categoryCheckboxes');
            container.innerHTML = '';
            
            categories.forEach(c => {
                if(c.LoaiDanhMuc === 'chi') { 
                    container.innerHTML += `<label><input type="checkbox" name="categories" value="${c.MaDanhMuc}"> ${c.TenDanhMuc}</label>`;
                }
            });
        } catch (error) {
            console.error("Lỗi khi tải danh mục:", error);
        }
    }

    // Tải Ngân sách lên Giao diện
    async function loadBudgets() {
        try {
            const res = await fetch('/api/budgets');
            const budgets = await res.json();
            const grid = document.getElementById('budgetGrid');
            grid.innerHTML = '';

            if (budgets.length === 0) {
                grid.innerHTML = '<p style="color: #666; text-align: center; width: 100%;">Bạn chưa có ngân sách nào. Hãy tạo mới!</p>';
                return;
            }

            budgets.forEach(b => {
                
                const isExceeded = b.is_exceeded ? 'exceeded' : '';
                
                // 1. Xử lý Thời gian tuyệt đối (Ngày cụ thể)
                const startArr = b.start_date.split('-'); // Cắt chuỗi YYYY-MM-DD
                const endArr = b.end_date.split('-');
                const dateRangeText = `${startArr[2]}/${startArr[1]} - ${endArr[2]}/${endArr[1]}`;

                // 2. Xử lý Thời gian tương đối (Đếm ngược)
                let daysText = '';
                let timeClass = ''; // Thêm class để đổi màu chữ nếu quá hạn
                if (b.days_left > 0) {
                    daysText = `Còn ${b.days_left} ngày`;
                } else if (b.days_left === 0) {
                    daysText = 'Hôm nay là hạn chót';
                    timeClass = 'exceeded'; // Đổi màu đỏ/cam cảnh báo
                } else {
                    daysText = 'Đã hết hạn';
                    timeClass = 'exceeded'; 
                }
                
                let tagsHtml = b.categories.map(c => `<span class="tag">${c.name}</span>`).join('');

                grid.innerHTML += `
                    <div class="budget-card">
                        <div class="budget-card-header">
                            <h3><i class="fas fa-wallet"></i> ${b.name}</h3>
                            <div class="budget-actions">
                                <button class="btn-icon btn-delete" onclick="deleteBudget('${b.id}')"><i class="fas fa-trash"></i></button>
                            </div>
                        </div>
                        <div class="budget-card-body">
                            <p class="budget-card-amount ${isExceeded}">
                                ${formatMoney(b.spent)} / ${formatMoney(b.amount)}
                            </p>
                            <div class="progress-bar">
                                <div class="progress-bar-fill ${isExceeded}" style="width: ${b.progress}%;"></div>
                            </div>
                            
                            <div style="display: flex; justify-content: space-between; margin-top: 12px; font-size: 0.85rem; font-weight: 500;">
                                <span style="color: #888;"><i class="fas fa-calendar-alt"></i> ${dateRangeText}</span>
                                <span class="${timeClass}" style="${timeClass === '' ? 'color: #28a745;' : 'color: #dc3545;'}"><i class="fas fa-clock"></i> ${daysText}</span>
                            </div>
                        </div>
                        <div class="budget-card-footer" style="margin-top: 15px;">
                            <span style="font-size: 0.85rem; color: #666; margin-right: 5px;">Áp dụng cho:</span> ${tagsHtml}
                        </div>
                    </div>`;
            });
        } catch (error) {
            console.error("Lỗi khi tải danh sách ngân sách:", error);
            document.getElementById('budgetGrid').innerHTML = '<p style="color: red;">Có lỗi xảy ra khi tải dữ liệu.</p>';
        }
    }

    // Tạo Ngân sách mới
    document.getElementById('budgetForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const checkedBoxes = document.querySelectorAll('input[name="categories"]:checked');
        const selectedCats = Array.from(checkedBoxes).map(cb => cb.value);

        if(selectedCats.length === 0) {
            alert("Vui lòng chọn ít nhất 1 danh mục!");
            return;
        }

        const data = {
            name: document.getElementById('budgetName').value,
            amount: document.getElementById('budgetAmount').value,
            start_date: document.getElementById('budgetStart').value,
            end_date: document.getElementById('budgetEnd').value,
            category_ids: selectedCats
        };

        try {
            const res = await fetch('/api/budgets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (res.ok) {
                modal.style.display = 'none';
                this.reset();
                loadBudgets(); // Tải lại giao diện sau khi thêm thành công
            } else {
                const errData = await res.json();
                alert(`Lỗi: ${errData.message || "Không thể tạo ngân sách."}`);
            }
        } catch (error) {
            console.error("Lỗi khi lưu ngân sách:", error);
            alert("Lỗi kết nối đến máy chủ.");
        }
    });

    // Xóa Ngân sách
    window.deleteBudget = async function(id) {
        if(confirm('Bạn có chắc chắn muốn xóa ngân sách này?')) {
            try {
                const res = await fetch(`/api/budgets/${id}`, { method: 'DELETE' });
                if(res.ok) {
                    loadBudgets();
                } else {
                    alert("Có lỗi xảy ra khi xóa.");
                }
            } catch (error) {
                console.error("Lỗi khi xóa ngân sách:", error);
            }
        }
    }

    // Khởi chạy việc tải ngân sách khi load trang
    loadBudgets();
});