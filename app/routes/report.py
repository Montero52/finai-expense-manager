from flask import Blueprint, render_template, request, session, jsonify, send_file, redirect, url_for
from functools import wraps
from datetime import datetime, timedelta, date
import calendar
import pandas as pd
from io import BytesIO
from sqlalchemy import func

from app import db
from app.models import Transaction, Category, Wallet

# Khai báo Blueprint
report_bp = Blueprint('report', __name__)

# --- Hàm hỗ trợ ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def api_login_required_check():
    return 'user_id' not in session

def get_date_range(time_range):
    today = date.today()
    if time_range == 'this_month':
        start_date = date(today.year, today.month, 1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = date(today.year, today.month, last_day)
    elif time_range == 'last_month':
        first_of_this_month = date(today.year, today.month, 1)
        end_date = first_of_this_month - timedelta(days=1)
        start_date = date(end_date.year, end_date.month, 1)
    elif time_range == 'year':
        start_date = date(today.year, 1, 1)
        end_date = date(today.year, 12, 31)
    else:
        start_date = date(today.year, today.month, 1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = date(today.year, today.month, last_day)
    return start_date, end_date

# --- Routes Giao diện ---
@report_bp.route('/reports')
@login_required
def reports():
    return render_template('user/reports.html')

# --- API Endpoints ---
@report_bp.route('/api/reports/data', methods=['GET'])
def get_report_data():
    if api_login_required_check(): return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    user_id = session['user_id']
    time_range = request.args.get('time_range', 'this_month')
    wallet_id = request.args.get('wallet_id', 'all')
    req_type = request.args.get('type', 'expense') 
    db_type = 'chi' if req_type == 'expense' else 'thu'

    start_date, end_date = get_date_range(time_range)
    query = db.session.query(Transaction).filter(Transaction.user_id == user_id, Transaction.date >= start_date, Transaction.date <= end_date)
    if wallet_id != 'all' and wallet_id: query = query.filter(Transaction.wallet_id == wallet_id)

    # 1. Biểu đồ tròn
    cat_query = query.filter(Transaction.type == db_type)
    category_stats = cat_query.with_entities(Category.name, func.sum(Transaction.amount)).outerjoin(Category, Transaction.category_id == Category.id).group_by(Category.name).all()
    pie_labels = [item[0] if item[0] else "Chưa phân loại" for item in category_stats]
    pie_data = [float(item[1]) for item in category_stats]

    # 2. Biểu đồ cột
    cashflow_query = db.session.query(Transaction).filter(Transaction.user_id == user_id, Transaction.date >= start_date, Transaction.date <= end_date)
    if wallet_id != 'all' and wallet_id: cashflow_query = cashflow_query.filter(Transaction.wallet_id == wallet_id)
    income_total = cashflow_query.filter(Transaction.type == 'thu').with_entities(func.sum(Transaction.amount)).scalar() or 0
    expense_total = cashflow_query.filter(Transaction.type == 'chi').with_entities(func.sum(Transaction.amount)).scalar() or 0
    transfer_total = cashflow_query.filter(Transaction.type == 'chuyen').with_entities(func.sum(Transaction.amount)).scalar() or 0
    
    # 3. Biểu đồ đường
    trend_query = query.filter(Transaction.type == db_type).with_entities(Transaction.date, func.sum(Transaction.amount)).group_by(Transaction.date).order_by(Transaction.date).all()
    line_chart_data = {"labels": [item[0].strftime('%d/%m') for item in trend_query], "data": [float(item[1]) for item in trend_query]}

    # 4. Top chi tiêu
    top_cat_query = query.filter(Transaction.type == 'chi').with_entities(Category.name, func.sum(Transaction.amount)).outerjoin(Category, Transaction.category_id == Category.id).group_by(Category.name).order_by(func.sum(Transaction.amount).desc()).all()
    total_expense_period = sum([item[1] for item in top_cat_query]) if top_cat_query else 0
    top_spending_list = [{"category": name if name else "Chưa phân loại", "amount": float(amount), "amount_formatted": "{:,.0f} đ".format(amount).replace(",", "."), "percent": round((amount / total_expense_period * 100), 1) if total_expense_period > 0 else 0} for name, amount in top_cat_query]

    return jsonify({
        "pie_chart": {"labels": pie_labels, "data": pie_data},
        "bar_chart": {"labels": ["Thu nhập", "Chi tiêu", "Chuyển khoản"], "data": [float(income_total), float(expense_total), float(transfer_total)]},
        "line_chart": line_chart_data,
        "top_spending": top_spending_list,
        "summary": {"total_income": income_total, "total_expense": expense_total, "balance": income_total - expense_total}
    })

@report_bp.route('/api/reports/export/excel', methods=['GET'])
def export_excel():
    if api_login_required_check(): return jsonify({'status': 'error'}), 401
    user_id = session['user_id']
    time_range = request.args.get('time_range', 'this_month')
    start_date, end_date = get_date_range(time_range)

    query = db.session.query(Transaction).filter(Transaction.user_id == user_id, Transaction.date >= start_date, Transaction.date <= end_date).outerjoin(Category, Transaction.category_id == Category.id).outerjoin(Wallet, Transaction.wallet_id == Wallet.id).order_by(Transaction.date.desc())
    transactions = query.all()
    
    data_list = []
    for t in transactions:
        loai = "Chi tiêu" if t.type == 'chi' else ("Thu nhập" if t.type == 'thu' else "Chuyển khoản")
        data_list.append({"Ngày": t.date.strftime('%d/%m/%Y'), "Danh mục": t.category.name if t.category else "Chưa phân loại", "Nội dung": t.description, "Số tiền": t.amount, "Loại": loai, "Ví": t.wallet.name if t.wallet else "Không xác định"})
    
    df = pd.DataFrame(data_list) if data_list else pd.DataFrame(columns=["Ngày", "Danh mục", "Nội dung", "Số tiền", "Loại", "Ví"])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer: df.to_excel(writer, index=False, sheet_name='Báo cáo')
    output.seek(0)
    return send_file(output, download_name=f"Bao_cao_{time_range}_{date.today()}.xlsx", as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@report_bp.route('/api/reports/export/pdf', methods=['GET'])
def export_pdf():
    if api_login_required_check(): return redirect(url_for('auth.login'))
    user_id = session['user_id']
    time_range = request.args.get('time_range', 'this_month')
    start_date, end_date = get_date_range(time_range)

    transactions = db.session.query(Transaction).filter(Transaction.user_id == user_id, Transaction.date >= start_date, Transaction.date <= end_date).outerjoin(Category).outerjoin(Wallet).order_by(Transaction.date.desc()).all()
    total_income = sum(t.amount for t in transactions if t.type == 'thu')
    total_expense = sum(t.amount for t in transactions if t.type == 'chi')

    return render_template('user/pdf_report.html', transactions=transactions, start_date=start_date.strftime('%d/%m/%Y'), end_date=end_date.strftime('%d/%m/%Y'), total_income=total_income, total_expense=total_expense, user_name=session.get('user_name', 'Người dùng'), today=date.today().strftime('%d/%m/%Y'))