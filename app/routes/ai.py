from flask import Blueprint, request, session, jsonify, Response, stream_with_context
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func

from app import db
from app.models import Category, Transaction, Wallet, ChatbotLog, UserSetting
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

    # --- GỌI GOOGLE GEMINI VÀ TRẢ VỀ THEO LUỒNG (STREAMING) ---
    try:
        response_stream = ai_engine.chat_with_data(user_question, context_text)
        
        if isinstance(response_stream, str): # Nếu trả về string báo lỗi
            return jsonify({'response': response_stream})

        # Hàm generator để bắn từng chữ về giao diện
        @stream_with_context
        def generate():
            full_answer = ""
            try:
                for chunk in response_stream:
                    if chunk.text:
                        full_answer += chunk.text
                        yield chunk.text # Bắn ngay chữ này về Frontend
                
                # CHỈ LƯU DATABASE KHI ĐÃ NÓI XONG HOÀN TOÀN
                db.session.add(ChatbotLog(
                    user_id=user_id, 
                    question=user_question, 
                    answer=full_answer, 
                    created_at=datetime.now()
                ))
                db.session.commit()
            except Exception as e:
                print(f"Lỗi Stream/Database: {e}")
                db.session.rollback()

        # Trả về Response dạng luồng (text/plain)
        return Response(generate(), mimetype='text/plain')

    except Exception as e:
        print(f"Lỗi gọi AI API: {e}")
        return jsonify({'response': 'Hệ thống AI đang bảo trì, vui lòng thử lại sau!'})

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

# ==========================================
# API 4: GỢI Ý NHANH CHO DASHBOARD (JSON)
# ==========================================
@ai_bp.route('/api/dashboard-insights', methods=['GET'])
@api_login_required
def dashboard_insights():
    user_id = session['user_id']

    user_setting = UserSetting.query.get(user_id)
        # Nếu có setting và cột ai_suggestions đang là 0 (Tắt)
    if user_setting and user_setting.ai_suggestions == 0:
        return jsonify({
            'status': 'disabled',
            'message': 'Tính năng AI đang bị tắt.'
        })
    # 1. Lấy dữ liệu tổng quan tháng này
    today = datetime.today()
    first_day = today.replace(day=1)
    
    # Lấy toàn bộ giao dịch từ đầu tháng
    transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.date >= first_day
    ).all()
    
    total_income = sum(t.amount for t in transactions if t.type == 'thu')
    total_expense = sum(t.amount for t in transactions if t.type == 'chi')
    
    # 2. Xây dựng Prompt "Ép khuôn" AI (Đã tối ưu hóa)
    context_text = f"Thống kê tháng này - Thu nhập: {int(total_income):,} VND. Chi tiêu: {int(total_expense):,} VND."
    
    question = (
        "Dựa vào số liệu trên, hãy đưa ra 3 lời khuyên tài chính. "
        "YÊU CẦU NGHIÊM NGẶT ĐỂ ĐỊNH DẠNG: "
        "1. TUYỆT ĐỐI KHÔNG chào hỏi, KHÔNG xưng hô (vd: Cấm dùng 'Chào bạn', 'FinAI đây'). "
        "2. TUYỆT ĐỐI KHÔNG có câu dẫn dắt (vd: Cấm dùng 'Đây là lời khuyên...'). "
        "3. Trả về ĐÚNG 3 dòng, mỗi dòng là một lời khuyên trực tiếp, hành động ngay. "
        "4. Độ dài tối đa: Dưới 15 chữ cho MỖI dòng. "
        "5. Không dùng markdown, không dùng icon."
    )
    try:
        # Gọi AI (Tận dụng lại hàm chat_with_data)
        response_stream = ai_engine.chat_with_data(question, context_text)
        
        if isinstance(response_stream, str): # Xử lý lỗi từ engine
            return jsonify({'status': 'error', 'message': response_stream})
            
        # 3. Gom toàn bộ luồng Stream lại thành 1 chuỗi duy nhất ở Backend
        full_answer = ""
        for chunk in response_stream:
            if chunk.text:
                full_answer += chunk.text
                
        # 4. Làm sạch dữ liệu và tách thành mảng (Array) 3 câu
        # Lọc bỏ các dòng trống và ký tự gạch đầu dòng rườm rà
        insights = [line.strip().lstrip('-*•').strip() for line in full_answer.split('\n') if line.strip()]
        
        # Trả về JSON tĩnh chuẩn mực
        return jsonify({'status': 'success', 'data': insights[:3]})
        
    except Exception as e:
        print(f"Lỗi AI Dashboard: {e}")
        return jsonify({'status': 'error', 'message': 'Hệ thống AI đang bận.'}), 500