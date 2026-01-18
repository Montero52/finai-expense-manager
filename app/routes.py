from functools import wraps
from datetime import datetime, timedelta, date
import uuid
import secrets
import calendar
import pandas as pd
from io import BytesIO

from app.ai_service import ai_engine


from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify, send_file
from werkzeug.security import check_password_hash
from flask_mail import Message

# Import nội bộ
from app import app, db, mail
from sqlalchemy import func

from app.models import User, UserSetting, Wallet, Category, Transaction, PasswordResetToken, ChatbotLog


# ==========================================
# 0. HELPER DECORATORS (Hàm hỗ trợ)
# ==========================================

def login_required(f):
    """Bắt buộc đăng nhập mới được truy cập Route này"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Bắt buộc là Admin mới được truy cập"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('user_role') != 'admin':
            flash('Bạn không có quyền truy cập trang này!', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def api_login_required(f):
    """Bắt buộc đăng nhập dành riêng cho API (Trả về JSON lỗi thay vì Redirect)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# 1. AUTHENTICATION (Xác thực)
# ==========================================

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Nếu đã đăng nhập, chuyển hướng ngay
    if 'user_id' in session:
        if session.get('user_role') == 'admin':
            return redirect(url_for('users'))
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            
            if user.role == 'admin':
                return redirect(url_for('users'))
            return redirect(url_for('dashboard'))
        else:
            flash('Email hoặc mật khẩu không chính xác.', 'error')

    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        password = request.form['password'].strip()
        confirm_password = request.form.get('confirm-password', '').strip()

        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp!', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email này đã được đăng ký!', 'error')
            return redirect(url_for('register'))

        try:
            # 1. Tạo User
            new_user_id = str(uuid.uuid4())[:8]
            new_user = User(id=new_user_id, name=fullname, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            
            # 2. Tạo Setting & Ví mặc định
            db.session.add(UserSetting(user_id=new_user_id))
            db.session.add(Wallet(
                id=str(uuid.uuid4())[:8],
                user_id=new_user_id,
                name="Ví tiền mặt",
                type="Tiền mặt",
                balance=0
            ))

            db.session.commit()
            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi hệ thống: {str(e)}', 'error')
            return redirect(url_for('register'))

    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- Quên Mật Khẩu ---

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('Email này chưa được đăng ký!', 'error')
            return redirect(url_for('forgot_password'))
            
        token = secrets.token_urlsafe(32)
        expiration = datetime.now() + timedelta(minutes=15)
        
        # Upsert token
        reset_entry = PasswordResetToken.query.filter_by(email=email).first()
        if reset_entry:
            reset_entry.token = token
            reset_entry.expires_at = expiration
        else:
            db.session.add(PasswordResetToken(email=email, token=token, expires_at=expiration))
            
        db.session.commit()
        
        try:
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('Khôi phục mật khẩu - AI Finance', recipients=[email])
            msg.body = f"Bấm vào link để đặt lại mật khẩu:\n{reset_url}\nLink hết hạn sau 15 phút."
            mail.send(msg)
            return redirect(url_for('email_sent'))
        except Exception as e:
            print(e)
            flash('Lỗi gửi email.', 'error')

    return render_template('auth/forgot_password.html')

@app.route('/email-sent')
def email_sent():
    return render_template('auth/email_sent.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset_entry = PasswordResetToken.query.filter_by(token=token).first()
    
    if not reset_entry or reset_entry.expires_at < datetime.now():
        flash('Link không hợp lệ hoặc đã hết hạn!', 'error')
        return redirect(url_for('forgot_password'))
        
    if request.method == 'POST':
        password = request.form['new-password']
        confirm_password = request.form['confirm-password']
        
        if password != confirm_password:
            flash('Mật khẩu không khớp', 'error')
            return redirect(url_for('reset_password', token=token))
            
        user = User.query.filter_by(email=reset_entry.email).first()
        if user:
            user.set_password(password)
            db.session.delete(reset_entry)
            db.session.commit()
            flash('Thành công! Hãy đăng nhập.', 'success')
            return redirect(url_for('login'))
            
    return render_template('auth/reset_password.html', token=token)


# ==========================================
# 2. USER VIEWS (Giao diện Người dùng)
# ==========================================

@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('user_role') == 'admin':
        return redirect(url_for('users'))
    return render_template('user/dashboard.html', user_name=session['user_name'])

@app.route('/transactions')
@login_required
def transactions():
    return render_template('user/transactions.html')

@app.route('/budgets')
@login_required
def budgets():
    return render_template('user/budgets.html')

@app.route('/reports')
@login_required
def reports():
    return render_template('user/reports.html')

report_bp = Blueprint('report', __name__)

# --- CÁC HÀM PHỤ TRỢ (GIỮ NGUYÊN) ---
def api_login_required_check():
    if 'user_id' not in session:
        return True 
    return False

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

# --- API LẤY DỮ LIỆU BÁO CÁO (GIỮ NGUYÊN) ---
@report_bp.route('/api/reports/data', methods=['GET'])
def get_report_data():
    if api_login_required_check(): return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    time_range = request.args.get('time_range', 'this_month')
    wallet_id = request.args.get('wallet_id', 'all')
    req_type = request.args.get('type', 'expense') 
    db_type = 'chi' if req_type == 'expense' else 'thu'

    start_date, end_date = get_date_range(time_range)
    
    query = db.session.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    )

    if wallet_id != 'all' and wallet_id:
        query = query.filter(Transaction.wallet_id == wallet_id)

    # Biểu đồ tròn
    cat_query = query.filter(Transaction.type == db_type)
    category_stats = cat_query.with_entities(Category.name, func.sum(Transaction.amount))\
        .outerjoin(Category, Transaction.category_id == Category.id)\
        .group_by(Category.name).all()

    pie_labels = []
    pie_data = []
    for item in category_stats:
        name = item[0] if item[0] else "Chưa phân loại"
        pie_labels.append(name)
        pie_data.append(float(item[1]))

# --- BIỂU ĐỒ CỘT (Thu vs. Chi vs. Chuyển khoản) ---
    cashflow_query = db.session.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    )
    if wallet_id != 'all' and wallet_id:
        cashflow_query = cashflow_query.filter(Transaction.wallet_id == wallet_id)

    # 1. Tính tổng cho cả 3 loại (QUAN TRỌNG: Thêm dòng transfer_total)
    income_total = cashflow_query.filter(Transaction.type == 'thu').with_entities(func.sum(Transaction.amount)).scalar() or 0
    expense_total = cashflow_query.filter(Transaction.type == 'chi').with_entities(func.sum(Transaction.amount)).scalar() or 0
    transfer_total = cashflow_query.filter(Transaction.type == 'chuyen').with_entities(func.sum(Transaction.amount)).scalar() or 0  # <--- THÊM DÒNG NÀY

    # 2. Đưa dữ liệu vào mảng (QUAN TRỌNG: Thêm transfer_total vào mảng data)
    bar_chart_data = {
        "labels": ["Thu nhập", "Chi tiêu", "Chuyển khoản"], # <--- Thêm nhãn
        "data": [float(income_total), float(expense_total), float(transfer_total)] # <--- Thêm số liệu
    }

    # Biểu đồ đường
    trend_query = query.filter(Transaction.type == db_type).with_entities(
        Transaction.date, func.sum(Transaction.amount)
    ).group_by(Transaction.date).order_by(Transaction.date).all()

    line_chart_data = {
        "labels": [item[0].strftime('%d/%m') for item in trend_query],
        "data": [float(item[1]) for item in trend_query]
    }

    # Top chi tiêu
    top_cat_query = query.filter(Transaction.type == 'chi') \
        .with_entities(Category.name, func.sum(Transaction.amount)) \
        .outerjoin(Category, Transaction.category_id == Category.id) \
        .group_by(Category.name).order_by(func.sum(Transaction.amount).desc()).all()

    total_expense_period = sum([item[1] for item in top_cat_query]) if top_cat_query else 0
    top_spending_list = []
    for name, amount in top_cat_query:
        cat_name = name if name else "Chưa phân loại"
        percent = (amount / total_expense_period * 100) if total_expense_period > 0 else 0
        top_spending_list.append({
            "category": cat_name,
            "amount": float(amount),
            "amount_formatted": "{:,.0f} đ".format(amount).replace(",", "."),
            "percent": round(percent, 1)
        })

    return jsonify({
        "pie_chart": {"labels": pie_labels, "data": pie_data},
        "bar_chart": {"labels": ["Thu nhập", "Chi tiêu"], "data": [float(income_total), float(expense_total)]},
        "line_chart": line_chart_data,
        "top_spending": top_spending_list,
        "summary": {
            "total_income": income_total,
            "total_expense": expense_total,
            "balance": income_total - expense_total
        }
    })

# --- API XUẤT EXCEL (GIỮ NGUYÊN) ---
@report_bp.route('/api/reports/export/excel', methods=['GET'])
def export_excel():
    if api_login_required_check(): return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    user_id = session['user_id']
    
    time_range = request.args.get('time_range', 'this_month')
    wallet_id = request.args.get('wallet_id', 'all')
    start_date, end_date = get_date_range(time_range)

    query = db.session.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    )
    
    if wallet_id != 'all' and wallet_id:
        query = query.filter(Transaction.wallet_id == wallet_id)
        
    query = query.outerjoin(Category, Transaction.category_id == Category.id)\
                 .outerjoin(Wallet, Transaction.wallet_id == Wallet.id)\
                 .order_by(Transaction.date.desc())

    data_list = []
    transactions = query.all()
    
    if not transactions:
        df = pd.DataFrame(columns=["Ngày", "Danh mục", "Nội dung", "Số tiền", "Loại", "Ví"])
    else:
        for t in transactions:
            loai = "Chi tiêu"
            if t.type == 'thu': loai = "Thu nhập"
            elif t.type == 'chuyen': loai = "Chuyển khoản"
            
            data_list.append({
                "Ngày": t.date.strftime('%d/%m/%Y'),
                "Danh mục": t.category.name if t.category else "Chưa phân loại",
                "Nội dung": t.description,
                "Số tiền": t.amount,
                "Loại": loai,
                "Ví": t.wallet.name if t.wallet else "Không xác định"
            })
        df = pd.DataFrame(data_list)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Báo cáo')
    output.seek(0)

    filename = f"Bao_cao_{time_range}_{date.today()}.xlsx"
    return send_file(output, download_name=filename, as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# --- API XUẤT PDF (ĐÃ SỬA - TRẢ VỀ HTML ĐỂ IN TRÌNH DUYỆT) ---
@report_bp.route('/api/reports/export/pdf', methods=['GET'])
def export_pdf():
    if api_login_required_check(): 
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    user_name = session.get('user_name', 'Người dùng')

    time_range = request.args.get('time_range', 'this_month')
    wallet_id = request.args.get('wallet_id', 'all')
    start_date, end_date = get_date_range(time_range)

    query = db.session.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    )
    
    if wallet_id != 'all' and wallet_id:
        query = query.filter(Transaction.wallet_id == wallet_id)
        
    transactions = query.outerjoin(Category, Transaction.category_id == Category.id)\
                        .outerjoin(Wallet, Transaction.wallet_id == Wallet.id)\
                        .order_by(Transaction.date.desc()).all()

    total_income = sum(t.amount for t in transactions if t.type == 'thu')
    total_expense = sum(t.amount for t in transactions if t.type == 'chi')

    # Trả về HTML để trình duyệt tự in
    return render_template(
        'user/pdf_report.html',
        transactions=transactions,
        start_date=start_date.strftime('%d/%m/%Y'),
        end_date=end_date.strftime('%d/%m/%Y'),
        total_income=total_income,
        total_expense=total_expense,
        user_name=user_name,
        today=date.today().strftime('%d/%m/%Y')
    )

@app.route('/foundations')
@login_required
def foundations():
    return render_template('user/foundations.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('user/settings.html')


# ==========================================
# 3. API ENDPOINTS (Xử lý dữ liệu JSON)
# ==========================================

# --- Transactions API ---

@app.route('/api/transactions', methods=['GET'])
@api_login_required
def get_transactions():
    user_id = session['user_id']
    trans_list = Transaction.query.filter_by(user_id=user_id)\
        .order_by(Transaction.date.desc(), Transaction.created_at.desc()).all()
    
    return jsonify([{
        'id': t.id,
        'type': t.type,
        'amount': t.amount,
        'description': t.description,
        'date': t.date.strftime('%Y-%m-%d'),
        'category_id': t.category_id,
        'category_name': t.category.name if t.category else 'Khác',
        'wallet_id': t.wallet_id,
        'wallet_name': t.wallet.name if t.wallet else 'Unknown',
        'dest_wallet_id': t.dest_wallet_id,
        'dest_wallet_name': t.dest_wallet.name if t.dest_wallet else None
    } for t in trans_list])

@app.route('/api/transactions', methods=['POST'])
@api_login_required
def add_transaction():
    data = request.json
    user_id = session['user_id']
    
    try:
        trans_type = data.get('type')
        db_type = {'expense': 'chi', 'income': 'thu', 'transfer': 'chuyen'}.get(trans_type, 'chi')
        amount = float(data.get('amount', 0))
        
        source_id = data.get('source_wallet_id')
        dest_id = data.get('dest_wallet_id')
        final_wallet_id = dest_id if db_type == 'thu' else source_id
        final_dest_id = dest_id if db_type == 'chuyen' else None

        if not final_wallet_id:
            return jsonify({'status': 'error', 'message': 'Chưa chọn ví'}), 400

        new_trans = Transaction(
            id=str(uuid.uuid4())[:8],
            user_id=user_id,
            wallet_id=final_wallet_id,
            dest_wallet_id=final_dest_id,
            category_id=data.get('category_id'),
            type=db_type,
            amount=amount,
            description=data.get('description'),
            date=datetime.strptime(data.get('date'), '%Y-%m-%d') if data.get('date') else datetime.now(),
            ai_category_id=data.get('ai_category_id'),
            ai_confidence=data.get('ai_confidence')
        )
        db.session.add(new_trans)

        # Cập nhật số dư
        wallet = Wallet.query.get(final_wallet_id)
        if db_type == 'chi':
            wallet.balance -= amount
        elif db_type == 'thu':
            wallet.balance += amount
        elif db_type == 'chuyen':
            wallet.balance -= amount
            dest_wallet = Wallet.query.get(final_dest_id)
            if dest_wallet: dest_wallet.balance += amount

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Đã lưu giao dịch!'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/transactions/<string:trans_id>', methods=['PUT'])
@api_login_required
def update_transaction(trans_id):
    data = request.json
    user_id = session['user_id']
    
    try:
        t = Transaction.query.filter_by(id=trans_id, user_id=user_id).first()
        if not t: return jsonify({'status': 'error', 'message': 'Không tìm thấy'}), 404

        # Hoàn tiền cũ
        old_wallet = Wallet.query.get(t.wallet_id)
        old_dest = Wallet.query.get(t.dest_wallet_id) if t.dest_wallet_id else None

        if t.type == 'chi': old_wallet.balance += t.amount
        elif t.type == 'thu': old_wallet.balance -= t.amount
        elif t.type == 'chuyen':
            old_wallet.balance += t.amount
            if old_dest: old_dest.balance -= t.amount

        # Cập nhật dữ liệu mới
        new_ui_type = data.get('type')
        t.type = {'expense': 'chi', 'income': 'thu', 'transfer': 'chuyen'}.get(new_ui_type, 'chi')
        t.amount = float(data.get('amount', 0))
        t.description = data.get('description')
        t.date = datetime.strptime(data.get('date'), '%Y-%m-%d')
        t.category_id = data.get('category_id')
        
        source_id = data.get('source_wallet_id')
        dest_id = data.get('dest_wallet_id')
        t.wallet_id = dest_id if t.type == 'thu' else source_id
        t.dest_wallet_id = dest_id if t.type == 'chuyen' else None

        # Trừ tiền mới
        new_wallet = Wallet.query.get(t.wallet_id)
        new_dest = Wallet.query.get(t.dest_wallet_id) if t.dest_wallet_id else None

        if t.type == 'chi': new_wallet.balance -= t.amount
        elif t.type == 'thu': new_wallet.balance += t.amount
        elif t.type == 'chuyen':
            new_wallet.balance -= t.amount
            if new_dest: new_dest.balance += t.amount

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Đã cập nhật!'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/transactions/<string:trans_id>', methods=['DELETE'])
@api_login_required
def delete_transaction(trans_id):
    try:
        t = Transaction.query.filter_by(id=trans_id, user_id=session['user_id']).first()
        if not t: return jsonify({'status': 'error'}), 404
        
        # Hoàn tiền
        wallet = Wallet.query.get(t.wallet_id)
        if t.type == 'chi': wallet.balance += t.amount
        elif t.type == 'thu': wallet.balance -= t.amount
        elif t.type == 'chuyen':
            wallet.balance += t.amount
            dest = Wallet.query.get(t.dest_wallet_id)
            if dest: dest.balance -= t.amount
            
        db.session.delete(t)
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- Wallets & Categories API ---

@app.route('/api/wallets', methods=['GET', 'POST'])
@api_login_required
def manage_wallets():
    user_id = session['user_id']
    if request.method == 'GET':
        wallets = Wallet.query.filter_by(user_id=user_id).all()
        return jsonify([{'MaNguonTien': w.id, 'TenNguonTien': w.name, 'LoaiNguonTien': w.type, 'SoDu': w.balance} for w in wallets])
    
    if request.method == 'POST':
        data = request.json
        try:
            db.session.add(Wallet(
                id=str(uuid.uuid4())[:8], user_id=user_id,
                name=data.get('name'), type=data.get('type'), balance=float(data.get('balance', 0))
            ))
            db.session.commit()
            return jsonify({'status': 'success'})
        except Exception as e: return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/wallets/<string:wallet_id>', methods=['PUT', 'DELETE'])
@api_login_required
def modify_wallet(wallet_id):
    user_id = session['user_id']
    wallet = Wallet.query.filter_by(id=wallet_id, user_id=user_id).first()
    if not wallet: return jsonify({'status': 'error'}), 404

    try:
        if request.method == 'DELETE':
            db.session.delete(wallet)
        elif request.method == 'PUT':
            data = request.json
            wallet.name = data.get('name')
            wallet.type = data.get('type')
            wallet.balance = float(data.get('balance', 0))
        
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e: return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/categories', methods=['GET', 'POST'])
@api_login_required
def manage_categories():
    user_id = session['user_id']
    if request.method == 'GET':
        cats = Category.query.filter_by(user_id=user_id).all()
        return jsonify([{'MaDanhMuc': c.id, 'TenDanhMuc': c.name, 'LoaiDanhMuc': c.type} for c in cats])
    
    if request.method == 'POST':
        data = request.json
        try:
            db.session.add(Category(
                id=str(uuid.uuid4())[:8], user_id=user_id,
                name=data.get('name'), type=data.get('type')
            ))
            db.session.commit()
            return jsonify({'status': 'success'})
        except Exception as e: return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/categories/<string:cat_id>', methods=['PUT', 'DELETE'])
@api_login_required
def modify_category(cat_id):
    user_id = session['user_id']
    cat = Category.query.filter_by(id=cat_id, user_id=user_id).first()
    if not cat: return jsonify({'status': 'error'}), 404

    try:
        if request.method == 'DELETE':
            db.session.delete(cat)
        elif request.method == 'PUT':
            data = request.json
            cat.name = data.get('name')
            cat.type = data.get('type')
        
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e: return jsonify({'status': 'error', 'message': str(e)}), 500

# --- API Dự đoán Danh mục ---
@app.route('/api/predict-category', methods=['POST'])
@api_login_required # Đảm bảo user đã đăng nhập
def predict_category():
    data = request.json
    description = data.get('description', '')
    
    if not description:
        return jsonify({'status': 'error', 'message': 'No description'})

    # 1. Gọi AI dự đoán
    result = ai_engine.predict(description)
    
    if result:
        predicted_name = result['category']
        
        # 2. Tìm ID danh mục trong DB của User này
        # Lưu ý: Tên danh mục AI trả về (ví dụ "Ăn uống") phải khớp với tên trong DB
        category = Category.query.filter(
            Category.name.ilike(predicted_name), # ilike để không phân biệt hoa thường
            Category.user_id == session['user_id']
        ).first()
        
        if category:
            return jsonify({
                'status': 'success',
                'category_id': category.id,
                'category_name': category.name,
                'category_type': category.type,
                'confidence': result['confidence']
            })
            
    # Nếu không tìm thấy hoặc AI không chắc chắn
    return jsonify({'status': 'no_match'})

# app/routes.py (Thêm vào cuối file hoặc khu vực API)

@app.route('/api/chat', methods=['POST'])
@api_login_required
def chat_ai():
    data = request.json
    user_question = data.get('message', '')
    user_id = session['user_id']
    
    # 1. Thu thập dữ liệu tài chính của User (Context)
    # Ví dụ: Lấy giao dịch trong 30 ngày qua
    last_30_days = datetime.now() - timedelta(days=30)
    transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.date >= last_30_days
    ).all()
    
    # Lấy số dư ví
    wallets = Wallet.query.filter_by(user_id=user_id).all()
    
    # 2. Biến đổi dữ liệu thành văn bản để AI đọc
    context_text = "--- TỔNG QUAN TÀI CHÍNH ---\n"
    
    # Thông tin Ví
    context_text += "SỐ DƯ CÁC VÍ:\n"
    for w in wallets:
        context_text += f"- {w.name}: {int(w.balance):,} VND\n"
        
    # Thông tin Giao dịch (Tóm tắt)
    context_text = "--- TỔNG QUAN TÀI CHÍNH ---\n"
    
    context_text += "SỐ DƯ CÁC VÍ:\n"
    for w in wallets:
        context_text += f"- {w.name}: {int(w.balance):,} VND\n"
        
    context_text += "\nLỊCH SỬ GIAO DỊCH 30 NGÀY QUA:\n"
    if not transactions:
        context_text += "(Chưa có giao dịch nào)\n"
    else:
        # Tạo từ điển để dịch mã loại giao dịch
        type_map = {
            'chi': 'CHI TIÊU',      # Viết hoa để nhấn mạnh
            'thu': 'THU NHẬP',
            'chuyen': 'CHUYỂN KHOẢN (Nội bộ)' # Ghi rõ là nội bộ
        }

        for t in transactions:
            # Dịch loại giao dịch sang tiếng Việt
            type_vn = type_map.get(t.type, t.type)
            
            cat_name = t.category.name if t.category else "Khác"
            date_str = t.date.strftime('%d/%m')
            
            # Gửi dữ liệu đã được gắn nhãn rõ ràng
            context_text += f"- [{type_vn}] Ngày {date_str}: {int(t.amount):,}đ - Danh mục: {cat_name} ({t.description})\n"

    # 3. Gửi cho AI xử lý
    ai_response = ai_engine.chat_with_data(user_question, context_text)
    
    try:
        new_log = ChatbotLog(
            id=str(uuid.uuid4())[:8],
            user_id=user_id,
            question=user_question,
            answer=ai_response,
            created_at=datetime.now()
        )
        db.session.add(new_log)
        db.session.commit()
    except Exception as e:
        print(f"Lỗi lưu log chat: {e}")
        # Không return lỗi để user vẫn nhận được câu trả lời
    
    return jsonify({'response': ai_response})

# 2. Thêm API mới: Lấy lịch sử chat
@app.route('/api/chat/history', methods=['GET'])
@api_login_required
def get_chat_history():
    user_id = session['user_id']
    
    # Lấy 20 tin nhắn gần nhất, sắp xếp cũ -> mới để hiển thị đúng thứ tự
    logs = ChatbotLog.query.filter_by(user_id=user_id)\
        .order_by(ChatbotLog.created_at.desc())\
        .limit(20).all()
    
    # Đảo ngược lại danh sách để tin cũ nhất hiện trên cùng
    logs.reverse()
    
    history = []
    for log in logs:
        history.append({'role': 'user', 'content': log.question})
        history.append({'role': 'ai', 'content': log.answer})
        
    return jsonify(history)

# ==========================================
# 4. ADMIN ROUTES (Giao diện Admin)
# ==========================================

@app.route('/api/admin/cleanup-logs', methods=['DELETE'])
@admin_required
def cleanup_logs():
    try:
        # Tính mốc thời gian: Hiện tại - 30 ngày
        expiration_date = datetime.now() - timedelta(days=30)
        
        # Thực hiện xóa
        deleted_count = ChatbotLog.query.filter(ChatbotLog.created_at < expiration_date).delete()
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': f'Đã xóa {deleted_count} tin nhắn cũ hơn 30 ngày.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
@app.route('/admin/users')

@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/categories')
@admin_required
def categories():
    return render_template('admin/categories.html')

@app.route('/admin/ai-monitoring')
@admin_required
def ai_monitoring():
    return render_template('admin/ai_monitoring.html')

@app.route('/admin/chatbot-logs')
@admin_required
def chatbot_logs():
    return render_template('admin/chatbot_logs.html')