from flask import Blueprint, render_template, session, redirect, url_for
from app.utils import login_required

views_bp = Blueprint('views', __name__)
from flask import session
from app.models import User

# ========================================================
# TRẠM PHÁT SÓNG TOÀN CỤC: Bơm biến 'user' vào MỌI file HTML
# ========================================================
@views_bp.app_context_processor
def inject_user():
    # Kiểm tra nếu người dùng đã đăng nhập (có user_id trong session)
    if 'user_id' in session:
        # Tìm user trong Database
        current_user = User.query.get(session['user_id'])
        # Trả về biến tên là 'user' để tất cả file HTML đều dùng được
        return dict(user=current_user)
    
    # Nếu chưa đăng nhập, trả về user là rỗng
    return dict(user=None)

@views_bp.route('/dashboard')
@login_required
def dashboard():
    if session.get('user_role') == 'admin':
        return redirect(url_for('admin.users'))
    return render_template('user/dashboard.html', user_name=session['user_name'])

@views_bp.route('/transactions')
@login_required
def transactions():
    return render_template('user/transactions.html')

@views_bp.route('/budgets')
@login_required
def budgets():
    return render_template('user/budgets.html')

@views_bp.route('/foundations')
@login_required
def foundations():
    return render_template('user/foundations.html')

@views_bp.route('/reports')
@login_required
def reports():
    return render_template('user/reports.html')