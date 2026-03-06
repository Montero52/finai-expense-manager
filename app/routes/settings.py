from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.models import User
from app import db
from app.utils import api_login_required

# Khai báo Blueprint
settings_bp = Blueprint('settings', __name__)

# 2. API CẬP NHẬT HỌ TÊN
@settings_bp.route('/api/settings/profile', methods=['POST'])
@api_login_required
def update_profile():
    data = request.json
    new_name = data.get('fullName', '').strip()
    
    if not new_name:
        return jsonify({'status': 'error', 'message': 'Họ tên không được để trống'}), 400
        
    try:
        user = User.query.get(session['user_id'])
        user.name = new_name  # Khớp với model User của bạn
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Cập nhật họ tên thành công!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Lỗi server: ' + str(e)}), 500

# 3. API ĐỔI MẬT KHẨU
@settings_bp.route('/api/settings/password', methods=['POST'])
@api_login_required
def update_password():
    data = request.json
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')
    confirm_password = data.get('confirmNewPassword')
    
    if not current_password or not new_password or not confirm_password:
        return jsonify({'status': 'error', 'message': 'Vui lòng điền đầy đủ thông tin'}), 400
        
    if new_password != confirm_password:
        return jsonify({'status': 'error', 'message': 'Mật khẩu mới không khớp nhau'}), 400
        
    try:
        user = User.query.get(session['user_id'])
        
        # Dùng hàm check_password từ model của bạn
        if not user.check_password(current_password):
            return jsonify({'status': 'error', 'message': 'Mật khẩu hiện tại không đúng'}), 401
            
        # Dùng hàm set_password từ model của bạn
        user.set_password(new_password)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Đổi mật khẩu thành công!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Lỗi server: ' + str(e)}), 500