from functools import wraps
from datetime import datetime, date
import uuid
from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify

# Import nội bộ
from app import db
from app.models import User, Wallet, Category, Transaction, Budget
from sqlalchemy import func

# 1. Khai báo Blueprint
core_bp = Blueprint('core', __name__)

# ==========================================
# 0. HELPER DECORATORS (Hàm hỗ trợ dùng chung)
# ==========================================

def login_required(f):
    """Bắt buộc đăng nhập mới được truy cập Route này"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login')) # Đã sửa thành auth.login
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

# ==========================================
# 1. USER VIEWS (Giao diện Người dùng)
# ==========================================

@core_bp.route('/dashboard')
@login_required
def dashboard():
    if session.get('user_role') == 'admin':
        return redirect(url_for('admin.users'))
    return render_template('user/dashboard.html', user_name=session['user_name'])

@core_bp.route('/transactions')
@login_required
def transactions():
    return render_template('user/transactions.html')

@core_bp.route('/budgets')
@login_required
def budgets():
    return render_template('user/budgets.html')

@core_bp.route('/foundations')
@login_required
def foundations():
    return render_template('user/foundations.html')

@core_bp.route('/settings')
@login_required
def settings():
    return render_template('user/settings.html')

@core_bp.route('/reports')
@login_required
def reports():
    return render_template('user/reports.html')

report_bp = Blueprint('report', __name__)
# ==========================================
# 2. API ENDPOINTS (Xử lý dữ liệu JSON)
# ==========================================

# --- Giao dịch (Transactions) ---

@core_bp.route('/api/transactions', methods=['GET'])
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

@core_bp.route('/api/transactions', methods=['POST'])
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

@core_bp.route('/api/transactions/<string:trans_id>', methods=['PUT'])
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

@core_bp.route('/api/transactions/<string:trans_id>', methods=['DELETE'])
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

# --- Nguồn tiền (Wallets) & Danh mục (Categories) ---

@core_bp.route('/api/wallets', methods=['GET', 'POST'])
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

@core_bp.route('/api/wallets/<string:wallet_id>', methods=['PUT', 'DELETE'])
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

@core_bp.route('/api/categories', methods=['GET', 'POST'])
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

@core_bp.route('/api/categories/<string:cat_id>', methods=['PUT', 'DELETE'])
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

# ==========================================
# --- API Ngân sách (Budgets) ---
# ==========================================

@core_bp.route('/api/budgets', methods=['GET', 'POST'])
@api_login_required
def manage_budgets():
    user_id = session['user_id']
    
    if request.method == 'GET':
        try:
            budgets = Budget.query.filter_by(user_id=user_id).all()
            result = []
            today = date.today()
            
            for b in budgets:
                # Lấy số tiền giới hạn từ model của bạn
                limit_amt = getattr(b, 'limit_amount', 0)
                
                cat_ids = [c.id for c in b.categories]
                spent = 0
                
                # Tính tổng chi tiêu
                if cat_ids:
                    spent = db.session.query(func.sum(Transaction.amount)).filter(
                        Transaction.user_id == user_id,
                        Transaction.type == 'chi',
                        Transaction.category_id.in_(cat_ids),
                        Transaction.date >= b.start_date,
                        Transaction.date <= b.end_date
                    ).scalar() or 0
                    
                # Tính % tiến độ
                progress = (spent / limit_amt) * 100 if limit_amt > 0 else 0
                days_left = (b.end_date - today).days
                
                result.append({
                    'id': b.id,
                    'name': b.name,
                    'amount': limit_amt,
                    'spent': spent,
                    'progress': min(progress, 100),
                    'is_exceeded': spent > limit_amt,
                    'start_date': b.start_date.strftime('%Y-%m-%d'),
                    'end_date': b.end_date.strftime('%Y-%m-%d'),
                    'days_left': max(days_left, 0),
                    'categories': [{'id': c.id, 'name': c.name} for c in b.categories]
                })
            return jsonify(result)
            
        except Exception as e:
            import traceback
            print("=== LỖI API GET BUDGETS ===")
            traceback.print_exc()
            return jsonify({'status': 'error', 'message': str(e)}), 500
            
    if request.method == 'POST':
        data = request.json
        try:
            new_budget = Budget(
                id=str(uuid.uuid4())[:8],
                user_id=user_id,
                name=data.get('name'),
                limit_amount=float(data.get('amount')), # Dùng limit_amount
                start_date=datetime.strptime(data.get('start_date'), '%Y-%m-%d').date(),
                end_date=datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
            )
            
            # Gắn các danh mục được chọn vào ngân sách
            cat_ids = data.get('category_ids', [])
            selected_cats = Category.query.filter(Category.id.in_(cat_ids), Category.user_id == user_id).all()
            new_budget.categories.extend(selected_cats)
            
            db.session.add(new_budget)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Đã tạo ngân sách!'})
        except Exception as e:
            db.session.rollback()
            print("=== LỖI API POST BUDGETS ===")
            import traceback
            traceback.print_exc()
            return jsonify({'status': 'error', 'message': str(e)}), 500

@core_bp.route('/api/budgets/<string:budget_id>', methods=['DELETE'])
@api_login_required
def delete_budget(budget_id):
    try:
        budget = Budget.query.filter_by(id=budget_id, user_id=session['user_id']).first()
        if not budget:
            return jsonify({'status': 'error', 'message': 'Không tìm thấy'}), 404
            
        db.session.delete(budget)
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500