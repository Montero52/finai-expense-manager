from flask import Blueprint, request, session, jsonify
from functools import wraps
from datetime import datetime, timedelta
import uuid

from app import db
from app.models import Category, Transaction, Wallet, ChatbotLog
from app.ai_service import ai_engine

# Khai báo Blueprint
ai_bp = Blueprint('ai', __name__)

def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@ai_bp.route('/api/predict-category', methods=['POST'])
@api_login_required
def predict_category():
    data = request.json
    description = data.get('description', '')
    if not description: return jsonify({'status': 'error', 'message': 'No description'})

    result = ai_engine.predict(description)
    if result:
        category = Category.query.filter(Category.name.ilike(result['category']), Category.user_id == session['user_id']).first()
        if category:
            return jsonify({'status': 'success', 'category_id': category.id, 'category_name': category.name, 'category_type': category.type, 'confidence': result['confidence']})
    return jsonify({'status': 'no_match'})

@ai_bp.route('/api/chat', methods=['POST'])
@api_login_required
def chat_ai():
    data = request.json
    user_question = data.get('message', '')
    user_id = session['user_id']
    
    last_30_days = datetime.now() - timedelta(days=30)
    transactions = Transaction.query.filter(Transaction.user_id == user_id, Transaction.date >= last_30_days).all()
    wallets = Wallet.query.filter_by(user_id=user_id).all()
    
    context_text = "--- TỔNG QUAN TÀI CHÍNH ---\nSỐ DƯ CÁC VÍ:\n"
    for w in wallets: context_text += f"- {w.name}: {int(w.balance):,} VND\n"
        
    context_text += "\nLỊCH SỬ GIAO DỊCH 30 NGÀY QUA:\n"
    if not transactions:
        context_text += "(Chưa có giao dịch nào)\n"
    else:
        type_map = {'chi': 'CHI TIÊU', 'thu': 'THU NHẬP', 'chuyen': 'CHUYỂN KHOẢN (Nội bộ)'}
        for t in transactions:
            cat_name = t.category.name if t.category else "Khác"
            context_text += f"- [{type_map.get(t.type, t.type)}] Ngày {t.date.strftime('%d/%m')}: {int(t.amount):,}đ - Danh mục: {cat_name} ({t.description})\n"

    ai_response = ai_engine.chat_with_data(user_question, context_text)
    
    try:
        db.session.add(ChatbotLog(id=str(uuid.uuid4())[:8], user_id=user_id, question=user_question, answer=ai_response, created_at=datetime.now()))
        db.session.commit()
    except Exception as e: print(f"Lỗi lưu log chat: {e}")
    
    return jsonify({'response': ai_response})

@ai_bp.route('/api/chat/history', methods=['GET'])
@api_login_required
def get_chat_history():
    logs = ChatbotLog.query.filter_by(user_id=session['user_id']).order_by(ChatbotLog.created_at.desc()).limit(20).all()
    logs.reverse()
    
    history = []
    for log in logs:
        history.append({'role': 'user', 'content': log.question})
        history.append({'role': 'ai', 'content': log.answer})
    return jsonify(history)