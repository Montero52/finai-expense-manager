from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify, request
from functools import wraps
from datetime import datetime, timedelta

from app import db
from sqlalchemy.orm import aliased
from app.models import User, ChatbotLog, AILog, Transaction, Category

# Khai báo Blueprint
admin_bp = Blueprint('admin', __name__)

# --- Hàm hỗ trợ ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: return redirect(url_for('auth.login'))
        if session.get('user_role') != 'admin':
            flash('Bạn không có quyền truy cập trang này!', 'error')
            return redirect(url_for('views.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes Giao diện ---
@admin_bp.route('/admin/users')
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/admin/categories')
@admin_required
def categories():
    return render_template('admin/categories.html')

# --- API Xóa Log ---
@admin_bp.route('/api/admin/cleanup-logs', methods=['DELETE'])
@admin_required
def cleanup_logs():
    try:
        expiration_date = datetime.now() - timedelta(days=30)
        deleted_count = ChatbotLog.query.filter(ChatbotLog.created_at < expiration_date).delete()
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'Đã xóa {deleted_count} tin nhắn cũ hơn 30 ngày.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
# ==========================================
# API HỖ TRỢ TRANG QUẢN LÝ NGƯỜI DÙNG
# ==========================================

@admin_bp.route('/api/admin/users/<string:user_id>/role', methods=['PUT'])
@admin_required
def update_user_role(user_id):
    # Tránh admin tự hạ quyền mình
    if user_id == session.get('user_id'):
        return jsonify({'status': 'error', 'message': 'Không thể tự đổi quyền của chính mình'}), 403
        
    user = User.query.get(user_id)
    if not user: 
        return jsonify({'status': 'error', 'message': 'Không tìm thấy người dùng'}), 404
    
    new_role = request.json.get('role')
    if new_role in ['user', 'admin']:
        user.role = new_role
        db.session.commit()
        return jsonify({'status': 'success'})
        
    return jsonify({'status': 'error', 'message': 'Quyền không hợp lệ'}), 400


@admin_bp.route('/api/admin/users/<string:user_id>/status', methods=['PUT'])
@admin_required
def update_user_status(user_id):
    # Tránh admin tự khóa mình
    if user_id == session.get('user_id'):
        return jsonify({'status': 'error', 'message': 'Không thể tự khóa tài khoản của mình'}), 403
        
    user = User.query.get(user_id)
    if not user: 
        return jsonify({'status': 'error', 'message': 'Không tìm thấy người dùng'}), 404
    
    # Cập nhật trạng thái
    user.status = request.json.get('status')
    db.session.commit()
    return jsonify({'status': 'success'})

@admin_bp.route('/admin/ai-monitoring')
@admin_required
def ai_monitoring():
    # Tạo bí danh (alias) vì chúng ta cần join bảng Category 2 lần (cho AI đoán và cho Thực tế)
    PredictedCategory = aliased(Category)
    ActualCategory = aliased(Category)

    # Lấy dữ liệu và kết nối các bảng
    logs_query = db.session.query(
        AILog,
        Transaction.description.label('description'),
        PredictedCategory.name.label('predicted_name'),
        ActualCategory.name.label('actual_name')
    ).outerjoin(Transaction, AILog.transaction_id == Transaction.id)\
     .outerjoin(PredictedCategory, AILog.predicted_cat == PredictedCategory.id)\
     .outerjoin(ActualCategory, AILog.actual_cat == ActualCategory.id)\
     .order_by(AILog.created_at.desc()).limit(100).all() # Lấy 100 log gần nhất cho nhẹ web

    return render_template('admin/ai_monitoring.html', logs=logs_query)

