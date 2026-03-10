from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify, request
from functools import wraps
from datetime import datetime, timedelta

from app import db
from sqlalchemy.orm import aliased
from app.models import User, ChatbotLog, AILog, Transaction, Category

# Khai báo Blueprint
admin_bp = Blueprint('admin', __name__)

# --- Hàm hỗ trợ ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: return redirect(url_for('auth.login'))
        if session.get('user_role') != 'admin':
            flash('Bạn không có quyền truy cập trang này!', 'error')
            return redirect(url_for('views.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes Giao diện ---
@admin_bp.route('/admin/users')
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

# --- API Xóa Log ---
@admin_bp.route('/api/admin/cleanup-logs', methods=['DELETE'])
@admin_required
def cleanup_logs():
    try:
        expiration_date = datetime.now() - timedelta(days=30)
        deleted_count = ChatbotLog.query.filter(ChatbotLog.created_at < expiration_date).delete()
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'Đã xóa {deleted_count} tin nhắn cũ hơn 30 ngày.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
# ==========================================
# API HỖ TRỢ TRANG QUẢN LÝ NGƯỜI DÙNG
# ==========================================

@admin_bp.route('/api/admin/users/<string:user_id>/role', methods=['PUT'])
@admin_required
def update_user_role(user_id):
    # Tránh admin tự hạ quyền mình
    if user_id == session.get('user_id'):
        return jsonify({'status': 'error', 'message': 'Không thể tự đổi quyền của chính mình'}), 403
        
    user = User.query.get(user_id)
    if not user: 
        return jsonify({'status': 'error', 'message': 'Không tìm thấy người dùng'}), 404
    
    new_role = request.json.get('role')
    if new_role in ['user', 'admin']:
        user.role = new_role
        db.session.commit()
        return jsonify({'status': 'success'})
        
    return jsonify({'status': 'error', 'message': 'Quyền không hợp lệ'}), 400


@admin_bp.route('/api/admin/users/<string:user_id>/status', methods=['PUT'])
@admin_required
def update_user_status(user_id):
    # Tránh admin tự khóa mình
    if user_id == session.get('user_id'):
        return jsonify({'status': 'error', 'message': 'Không thể tự khóa tài khoản của mình'}), 403
        
    user = User.query.get(user_id)
    if not user: 
        return jsonify({'status': 'error', 'message': 'Không tìm thấy người dùng'}), 404
    
    # Cập nhật trạng thái
    user.status = request.json.get('status')
    db.session.commit()
    return jsonify({'status': 'success'})

@admin_bp.route('/admin/ai-monitoring')
@admin_required
def ai_monitoring():
    # Tạo bí danh (alias) vì chúng ta cần join bảng Category 2 lần (cho AI đoán và cho Thực tế)
    PredictedCategory = aliased(Category)
    ActualCategory = aliased(Category)

    # Lấy dữ liệu và kết nối các bảng
    logs_query = db.session.query(
        AILog,
        Transaction.description.label('description'),
        PredictedCategory.name.label('predicted_name'),
        ActualCategory.name.label('actual_name')
    ).outerjoin(Transaction, AILog.transaction_id == Transaction.id)\
     .outerjoin(PredictedCategory, AILog.predicted_cat == PredictedCategory.id)\
     .outerjoin(ActualCategory, AILog.actual_cat == ActualCategory.id)\
     .order_by(AILog.created_at.desc()).limit(100).all() # Lấy 100 log gần nhất cho nhẹ web

    return render_template('admin/ai_monitoring.html', logs=logs_query)


@admin_bp.route('/admin/chatbot-logs')
@admin_required
def chatbot_logs():
    # Lấy toàn bộ lịch sử chat kèm thông tin user, sắp xếp cũ -> mới (để hiện chat từ trên xuống)
    logs_query = db.session.query(ChatbotLog, User)\
        .join(User, ChatbotLog.user_id == User.id)\
        .order_by(ChatbotLog.created_at.asc()).all()

    conversations = {}
    for log, user in logs_query:
        if user.id not in conversations:
            conversations[user.id] = {
                'user_id': user.id,
                'user_name': user.name,
                'logs': [],
                'latest_time': log.created_at,
                'snippet': ''
            }
        # Thêm tin nhắn vào mảng logs của người dùng này
        conversations[user.id]['logs'].append(log)
        # Cập nhật thời gian và đoạn trích dẫn mới nhất
        conversations[user.id]['latest_time'] = log.created_at
        
        snippet = log.question if log.question else ''
        conversations[user.id]['snippet'] = (snippet[:25] + '...') if len(snippet) > 25 else snippet

    # Sắp xếp lại danh sách bên trái: Ai nhắn gần đây nhất thì lên đầu (Mới -> Cũ)
    sorted_convos = sorted(conversations.values(), key=lambda x: x['latest_time'], reverse=True)

    return render_template('admin/chatbot_logs.html', conversations=sorted_convos)

# ==========================================
# QUẢN LÝ DANH MỤC (CATEGORIES)
# ==========================================

@admin_bp.route('/admin/categories')
@admin_required
def categories():
    # Chỉ trả về giao diện, dữ liệu sẽ do JS gọi API sau
    return render_template('admin/categories.html')

@admin_bp.route('/api/admin/categories', methods=['GET'])
@admin_required
def get_admin_categories():
    # Lấy các danh mục mặc định (user_id là null)
    categories = Category.query.filter(Category.user_id == None).all()
    return jsonify([
        {
            "id": c.id,
            "name": c.name,
            "type": c.type # 'thu' hoặc 'chi'
        } for c in categories
    ])

@admin_bp.route('/api/admin/categories', methods=['POST'])
@admin_required
def save_category():
    data = request.json
    cat_id = data.get('id')
    name = data.get('name')
    cat_type = data.get('type')

    if cat_id: # Trường hợp SỬA
        category = Category.query.get(cat_id)
        if category:
            category.name = name
            category.type = cat_type
    else: # Trường hợp THÊM MỚI
        category = Category(name=name, type=cat_type, user_id=None)
        db.session.add(category)
    
    db.session.commit()
    return jsonify({"status": "success", "message": "Đã lưu danh mục"})

@admin_bp.route('/api/admin/categories/<int:id>', methods=['DELETE'])
@admin_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    return jsonify({"status": "success", "message": "Đã xóa danh mục"})