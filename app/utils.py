from functools import wraps
from flask import session, redirect, url_for, jsonify

def login_required(f):
    """Bắt buộc đăng nhập mới được truy cập Route HTML"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def api_login_required(f):
    """Bắt buộc đăng nhập dành riêng cho API (Trả về JSON lỗi)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function
