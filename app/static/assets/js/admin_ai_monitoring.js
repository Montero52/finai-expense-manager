// Quản lý bộ lọc trạng thái (Đúng/Sai) cho bảng Giám sát AI
document.addEventListener("DOMContentLoaded", function() {
    const filterSelect = document.getElementById('result-filter');
    const rows = document.querySelectorAll('.log-row');

    if (filterSelect) {
        filterSelect.addEventListener('change', function() {
            const filterValue = this.value; // 'all', 'correct', 'incorrect'

            rows.forEach(row => {
                if (filterValue === 'all') {
                    row.style.display = '';
                } else if (filterValue === 'correct') {
                    row.style.display = row.classList.contains('log-correct') ? '' : 'none';
                } else if (filterValue === 'incorrect') {
                    row.style.display = row.classList.contains('log-incorrect') ? '' : 'none';
                }
            });
        });
    }
});