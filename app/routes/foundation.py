import uuid
from flask import Blueprint, request, session, jsonify

from app import db
from app.models import Wallet, Category
from app.utils import api_login_required
from sqlalchemy import or_

foundation_bp = Blueprint('foundation', __name__)

@foundation_bp.route('/api/wallets', methods=['GET', 'POST'])
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

@foundation_bp.route('/api/wallets/<string:wallet_id>', methods=['PUT', 'DELETE'])
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

@foundation_bp.route('/api/categories', methods=['GET', 'POST'])
@api_login_required
def manage_categories():
    user_id = session['user_id']
    if request.method == 'GET':
        cats = Category.query.filter(or_(Category.user_id == user_id, Category.user_id == None)).all()
        return jsonify([{'MaDanhMuc': c.id, 'TenDanhMuc': c.name, 'LoaiDanhMuc': c.type} for c in cats])
    
    if request.method == 'POST':
        data = request.json
        try:
            db.session.add(Category(
                user_id=user_id,
                name=data.get('name'), type=data.get('type')
            ))
            db.session.commit()
            return jsonify({'status': 'success'})
        except Exception as e: return jsonify({'status': 'error', 'message': str(e)}), 500

@foundation_bp.route('/api/categories/<int:cat_id>', methods=['PUT', 'DELETE'])
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
