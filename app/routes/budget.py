import uuid
from datetime import datetime, date
from flask import Blueprint, request, session, jsonify
from sqlalchemy import func

from app import db
from app.models import Budget, Category, Transaction
from app.utils import api_login_required

budget_bp = Blueprint('budget', __name__)

@budget_bp.route('/api/budgets', methods=['GET', 'POST'])
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

@budget_bp.route('/api/budgets/<string:budget_id>', methods=['DELETE'])
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