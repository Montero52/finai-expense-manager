from flask import Blueprint, request, session, jsonify
from functools import wraps
from datetime import datetime, timedelta
import uuid
from sqlalchemy import func

from app import db
from app.models import Category, Transaction, Wallet, ChatbotLog
from app.ai_service import ai_engine

# Khai báo Blueprint
ai_bp = Blueprint('ai', __name__)

def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: 
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# API 1: DỰ ĐOÁN DANH MỤC THÔNG MINH
# ==========================================
@ai_bp.route('/api/predict-category', methods=['POST'])
@api_login_required
def predict_category():
    data = request.json
    description = data.get('description', '')
    if not description: 
        return jsonify({'status': 'error', 'message': 'No description'})

    user_id = session['user_id']
    
    # 1. Lấy danh sách Menu Danh mục CỦA RIÊNG USER ĐÓ
    user_cats = Category.query.filter_by(user_id=user_id).all()
    cat_names = [cat.name for cat in user_cats] # Ví dụ: ['Ăn uống', 'Xăng xe', 'Đóng họ']

    # 2. Truyền Menu này cho AI chọn
    result = ai_engine.predict(description, cat_names)
    
    # 3. Xử lý kết quả trả về từ dạng JSON của AI
    if result and result.get('category'):
        category_name = result['category']
        
        # Tìm lại Object Category trong Database
        category = Category.query.filter(
            Category.name.ilike(category_name), 
            Category.user_id == user_id
        ).first()
        
        if category:
            return jsonify({
                'status': 'success', 
                'category_id': category.id, 
                'category_name': category.name, 
                'category_type': category.type, 
                'confidence': result.get('confidence', 90)
            })
            
    return jsonify({'status': 'no_match'})

# ==========================================
# API 2: CHATBOT TRỢ LÝ TÀI CHÍNH CÁ NHÂN
# ==========================================
@ai_bp.route('/api/chat', methods=['POST'])
@api_login_required
def chat_ai():
    data = request.json
    user_question = data.get('message', '')
    if not user_question:
        return jsonify({'response': 'Vui lòng nhập câu hỏi.'}), 400

    user_id = session['user_id']
    last_30_days = datetime.now() - timedelta(days=30)
    
    # --- XÂY DỰNG NGỮ CẢNH (CONTEXT) CHO AI ---
    
    # 1. Lấy số dư ví hiện tại
    wallets = Wallet.query.filter_by(user_id=user_id).all()
    context_text = "--- TỔNG QUAN TÀI CHÍNH ---\nSỐ DƯ CÁC VÍ:\n"
    for w in wallets: 
        context_text += f"- {w.name}: {int(w.balance):,} VND\n"
        
    # 2. TỔNG HỢP CHI TIÊU 30 NGÀY QUA (Dùng Group By để tránh nổ Token)
    expense_summary = db.session.query(
        Category.name, func.sum(Transaction.amount)
    ).join(Transaction, Transaction.category_id == Category.id).filter(
        Transaction.user_id == user_id, 
        Transaction.date >= last_30_days,
        Transaction.type == 'chi'
    ).group_by(Category.name).all()

    context_text += "\nTHỐNG KÊ CHI TIÊU 30 NGÀY QUA:\n"
    if not expense_summary:
        context_text += "(Chưa có dữ liệu chi tiêu)\n"
    else:
        for cat_name, total in expense_summary:
            context_text += f"- {cat_name}: {int(total):,}đ\n"

    # 3. Lấy 5 giao dịch gần nhất để AI hiểu rõ bối cảnh mua sắm
    recent_transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.date.desc()).limit(5).all()
    context_text += "\n5 GIAO DỊCH GẦN NHẤT:\n"
    for t in recent_transactions:
        cat_name = t.category.name if t.category else "Khác"
        type_label = "CHI" if t.type == 'chi' else "THU" if t.type == 'thu' else "CHUYỂN KHOẢN"
        context_text += f"- {t.date.strftime('%d/%m')}: {int(t.amount):,}đ ({type_label}) - {cat_name} ({t.description})\n"

    # --- GỌI GOOGLE GEMINI ---
    try:
        ai_response = ai_engine.chat_with_data(user_question, context_text)
    except Exception as e:
        print(f"Lỗi gọi AI API: {e}")
        return jsonify({'response': 'Hệ thống AI đang bảo trì hoặc bận kết nối, vui lòng thử lại sau!'})
    
    # --- LƯU LOG LỊCH SỬ CHAT ---
    try:
        log_id = str(uuid.uuid4())[:8]
        db.session.add(ChatbotLog(
            id=log_id, 
            user_id=user_id, 
            question=user_question, 
            answer=ai_response, 
            created_at=datetime.now()
        ))
        db.session.commit()
    except Exception as e: 
        print(f"Lỗi lưu log chat: {e}")
        db.session.rollback() # Tránh treo Database nếu lưu lỗi
    
    return jsonify({'response': ai_response})

# ==========================================
# API 3: LẤY LỊCH SỬ TIN NHẮN CHATBOT
# ==========================================
@ai_bp.route('/api/chat/history', methods=['GET'])
@api_login_required
def get_chat_history():
    # Lấy 20 tin nhắn gần nhất
    logs = ChatbotLog.query.filter_by(user_id=session['user_id']).order_by(ChatbotLog.created_at.desc()).limit(20).all()
    logs.reverse() # Đảo ngược lại để tin cũ ở trên, tin mới ở dưới
    
    history = []
    for log in logs:
        history.append({'role': 'user', 'content': log.question})
        history.append({'role': 'ai', 'content': log.answer})
    return jsonify(history)