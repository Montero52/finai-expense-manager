// Xử lý thay đổi quyền (Role)
async function updateUserRole(userId, newRole) {
    if (!confirm(`Bạn có chắc muốn đổi quyền thành ${newRole.toUpperCase()}?`)) {
        location.reload(); 
        return;
    }
    
    try {
        const res = await fetch(`/api/admin/users/${userId}/role`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role: newRole })
        });
        
        const data = await res.json();
        if (res.ok) { 
            alert('Cập nhật quyền thành công!'); 
            location.reload(); 
        } else { 
            alert('Lỗi: ' + data.message); 
            location.reload(); 
        }
    } catch(e) { 
        console.error("Error updating role:", e); 
        alert('Lỗi hệ thống'); 
    }
}

// Xử lý Khóa/Mở khóa tài khoản (Status)
async function toggleUserStatus(userId, currentStatus) {
    const actionText = currentStatus === 1 ? 'Khóa' : 'Mở khóa';
    if (!confirm(`Bạn có chắc chắn muốn ${actionText} tài khoản này?`)) return;

    const newStatus = currentStatus === 1 ? 0 : 1;
    
    try {
        const res = await fetch(`/api/admin/users/${userId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        
        const data = await res.json();
        if (res.ok) { 
            location.reload(); 
        } else { 
            alert('Lỗi: ' + data.message); 
        }
    } catch(e) { 
        console.error("Error toggling status:", e); 
        alert('Lỗi hệ thống'); 
    }
}