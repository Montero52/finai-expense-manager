from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify
from functools import wraps
from datetime import datetime, timedelta

from app import db
from app.models import User, ChatbotLog

# Khai báo Blueprint
admin_bp = Blueprint('admin', __name__)

# --- Hàm hỗ trợ ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: return redirect(url_for('auth.login'))
        if session.get('user_role') != 'admin':
            flash('Bạn không có quyền truy cập trang này!', 'error')
            return redirect(url_for('core.dashboard'))
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

@admin_bp.route('/admin/ai-monitoring')
@admin_required
def ai_monitoring():
    return render_template('admin/ai_monitoring.html')

@admin_bp.route('/admin/chatbot-logs')
@admin_required
def chatbot_logs():
    return render_template('admin/chatbot_logs.html')

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