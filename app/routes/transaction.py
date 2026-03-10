from datetime import datetime
from flask import Blueprint, request, session, jsonify

from app import db
from app.models import Transaction, Wallet
from app.utils import api_login_required
from decimal import Decimal

transaction_bp = Blueprint('transaction', __name__)

@transaction_bp.route('/api/transactions', methods=['GET'])
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

@transaction_bp.route('/api/transactions', methods=['POST'])
@api_login_required
def add_transaction():
    data = request.json
    user_id = session['user_id']
    
    try:
        trans_type = data.get('type')
        db_type = {'expense': 'chi', 'income': 'thu', 'transfer': 'chuyen'}.get(trans_type, 'chi')
        amount = Decimal(str(data.get('amount')))
        
        source_id = data.get('source_wallet_id')
        dest_id = data.get('dest_wallet_id')
        final_wallet_id = dest_id if db_type == 'thu' else source_id
        final_dest_id = dest_id if db_type == 'chuyen' else None

        if not final_wallet_id:
            return jsonify({'status': 'error', 'message': 'Chưa chọn ví'}), 400

        new_trans = Transaction(
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

@transaction_bp.route('/api/transactions/<int:trans_id>', methods=['PUT'])
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
        t.amount     = Decimal(data.get('amount'))
        
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

@transaction_bp.route('/api/transactions/<int:trans_id>', methods=['DELETE'])
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