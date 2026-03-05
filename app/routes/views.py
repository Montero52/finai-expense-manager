from flask import Blueprint, render_template, session, redirect, url_for
from app.utils import login_required

views_bp = Blueprint('views', __name__)

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

@views_bp.route('/settings')
@login_required
def settings():
    return render_template('user/settings.html')

@views_bp.route('/reports')
@login_required
def reports():
    return render_template('user/reports.html')