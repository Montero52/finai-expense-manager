from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# ==================================================
# 1. BẢNG NGƯỜI DÙNG (CORE)
# ==================================================
class User(db.Model):
    __tablename__ = 'nguoidung'

    id = db.Column('MaNguoiDung', db.String(8), primary_key=True)
    name = db.Column('HoTen', db.String(100))
    email = db.Column('Email', db.String(100), unique=True, nullable=False)
    password_hash = db.Column('MatKhau', db.String(200), nullable=False)
    role = db.Column('VaiTro', db.String(20), default='user')  # 'user' hoặc 'admin'
    status = db.Column('TrangThai', db.Integer, default=1)
    created_at = db.Column('NgayTao', db.DateTime, default=datetime.now)
    last_login = db.Column('LanDangNhapCuoi', db.DateTime)

    # --- QUAN HỆ (Relationships) ---
    # Giúp truy cập dữ liệu liên quan dễ dàng: user.wallets, user.transactions...
    settings = db.relationship('UserSetting', backref='user', uselist=False, lazy=True)
    wallets = db.relationship('Wallet', backref='user', lazy=True)
    categories = db.relationship('Category', backref='user', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    budgets = db.relationship('Budget', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ==================================================
# 2. BẢNG THIẾT LẬP NGƯỜI DÙNG
# ==================================================
class UserSetting(db.Model):
    __tablename__ = 'thietlapnguoidung'

    user_id = db.Column('MaNguoiDung', db.String(8), db.ForeignKey('nguoidung.MaNguoiDung', ondelete='CASCADE'), primary_key=True)
    currency = db.Column('DonViTienTe', db.String(10), default='VND')
    language = db.Column('NgonNgu', db.String(10), default='vi')
    notifications = db.Column('ThongBao', db.Integer, default=1)
    ai_suggestions = db.Column('AI_GoiY', db.Integer, default=1)
    theme = db.Column('GiaoDien', db.String(20), default='light')

# ==================================================
# 3. BẢNG NGUỒN TIỀN (VÍ)
# ==================================================
class Wallet(db.Model):
    __tablename__ = 'nguontien'

    id = db.Column('MaNguonTien', db.String(8), primary_key=True)
    user_id = db.Column('MaNguoiDung', db.String(8), db.ForeignKey('nguoidung.MaNguoiDung', ondelete='CASCADE'), nullable=False)
    name = db.Column('TenNguonTien', db.String(100), nullable=False)
    type = db.Column('LoaiNguonTien', db.String(50)) # Tiền mặt, Ngân hàng...
    balance = db.Column('SoDu', db.Float, default=0.0)
    created_at = db.Column('NgayTao', db.DateTime, default=datetime.now)

# ==================================================
# 4. BẢNG DANH MỤC
# ==================================================
class Category(db.Model):
    __tablename__ = 'danhmuc'

    id = db.Column('MaDanhMuc', db.String(8), primary_key=True)
    user_id = db.Column('MaNguoiDung', db.String(8), db.ForeignKey('nguoidung.MaNguoiDung', ondelete='CASCADE'))
    name = db.Column('TenDanhMuc', db.String(100), nullable=False)
    type = db.Column('LoaiDanhMuc', db.String(10), nullable=False) # 'thu' hoặc 'chi'
    parent_id = db.Column('MaDanhMucCha', db.String(8), db.ForeignKey('danhmuc.MaDanhMuc', ondelete='SET NULL'))

    # Quan hệ đệ quy (Danh mục con)
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]), lazy=True)

# ==================================================
# 5. BẢNG GIAO DỊCH (Quan trọng nhất)
# ==================================================
class Transaction(db.Model):
    __tablename__ = 'giaodich'

    id = db.Column('MaGiaoDich', db.String(8), primary_key=True)
    user_id = db.Column('MaNguoiDung', db.String(8), db.ForeignKey('nguoidung.MaNguoiDung', ondelete='CASCADE'), nullable=False)
    
    wallet_id = db.Column('MaNguonTien', db.String(8), db.ForeignKey('nguontien.MaNguonTien'), nullable=False)
    dest_wallet_id = db.Column('MaNguonTien_Dich', db.String(8), db.ForeignKey('nguontien.MaNguonTien'), nullable=True)
    
    category_id = db.Column('MaDanhMuc', db.String(8), db.ForeignKey('danhmuc.MaDanhMuc', ondelete='SET NULL'), nullable=True)
    
    type = db.Column('LoaiGiaoDich', db.String(20), nullable=False) # 'thu', 'chi', 'chuyen'
    amount = db.Column('SoTien', db.Float, nullable=False)
    description = db.Column('MoTa', db.String(255))
    date = db.Column('NgayGiaoDich', db.Date, nullable=False)
    created_at = db.Column('NgayTao', db.DateTime, default=datetime.now)

    # Các trường AI
    ai_category_id = db.Column('MaDanhMuc_AI', db.String(8), db.ForeignKey('danhmuc.MaDanhMuc', ondelete='SET NULL'))
    ai_confidence = db.Column('DoTinCay_AI', db.Float)

    # Quan hệ để lấy tên Ví/Danh mục trực tiếp (trans.wallet.name)
    wallet = db.relationship('Wallet', foreign_keys=[wallet_id])
    dest_wallet = db.relationship('Wallet', foreign_keys=[dest_wallet_id])
    category = db.relationship('Category', foreign_keys=[category_id])

# ==================================================
# 6. BẢNG NGÂN SÁCH
# ==================================================

# 7. Bảng Trung gian Ngân sách - Danh mục
budget_category = db.Table('ngansach_danhmuc',
    db.Column('MaNganSach', db.String(8), db.ForeignKey('ngansach.MaNganSach', ondelete='CASCADE'), primary_key=True),
    db.Column('MaDanhMuc', db.String(8), db.ForeignKey('danhmuc.MaDanhMuc', ondelete='CASCADE'), primary_key=True)
)

class Budget(db.Model):
    __tablename__ = 'ngansach'

    id = db.Column('MaNganSach', db.String(8), primary_key=True)
    user_id = db.Column('MaNguoiDung', db.String(8), db.ForeignKey('nguoidung.MaNguoiDung', ondelete='CASCADE'), nullable=False)
    name = db.Column('TenNganSach', db.String(100), nullable=False)
    limit_amount = db.Column('SoTienGioiHan', db.Float, nullable=False)
    start_date = db.Column('NgayBatDau', db.Date, nullable=False)
    end_date = db.Column('NgayKetThuc', db.Date, nullable=False)
    created_at = db.Column('NgayTao', db.DateTime, default=datetime.now)

    # Quan hệ Many-to-Many với Danh mục
    categories = db.relationship('Category', secondary=budget_category, backref=db.backref('budgets', lazy=True))



# ==================================================
# 8. CÁC BẢNG PHỤ TRỢ KHÁC
# ==================================================

class AILog(db.Model):
    __tablename__ = 'ai_lichsu'
    id = db.Column('MaAI_Log', db.String(8), primary_key=True)
    user_id = db.Column('MaNguoiDung', db.String(8), db.ForeignKey('nguoidung.MaNguoiDung', ondelete='CASCADE'))
    transaction_id = db.Column('MaGiaoDich', db.String(8), db.ForeignKey('giaodich.MaGiaoDich', ondelete='SET NULL'))
    predicted_cat = db.Column('DanhMucDuDoan', db.String(8), db.ForeignKey('danhmuc.MaDanhMuc', ondelete='CASCADE'))
    actual_cat = db.Column('DanhMucChinhXac', db.String(8), db.ForeignKey('danhmuc.MaDanhMuc', ondelete='CASCADE'))
    confidence = db.Column('DoTinCay', db.Float)
    feedback = db.Column('PhanHoi', db.String(50)) # 'dung', 'sai'
    created_at = db.Column('NgayTao', db.DateTime, default=datetime.now)

class TwoFactorAuth(db.Model):
    __tablename__ = 'xacthuc2fa'
    user_id = db.Column('MaNguoiDung', db.String(8), db.ForeignKey('nguoidung.MaNguoiDung', ondelete='CASCADE'), primary_key=True)
    secret_key = db.Column('SecretKey', db.String(100), nullable=False)
    is_active = db.Column('DaKichHoat', db.Integer, default=0)
    backup_code = db.Column('MaDuPhong', db.String(200))

class ChatbotLog(db.Model):
    __tablename__ = 'chatbot_lichsu'
    id = db.Column('MaHoiThoai', db.String(8), primary_key=True)
    user_id = db.Column('MaNguoiDung', db.String(8), db.ForeignKey('nguoidung.MaNguoiDung', ondelete='CASCADE'))
    question = db.Column('NoiDungHoi', db.Text)
    answer = db.Column('NoiDungTraLoi', db.Text)
    created_at = db.Column('NgayTao', db.DateTime, default=datetime.now)

class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    email = db.Column('Email', db.String(100), db.ForeignKey('nguoidung.Email', ondelete='CASCADE'), primary_key=True)
    token = db.Column('Token', db.String(100), nullable=False)
    expires_at = db.Column('ThoiGianHetHan', db.DateTime, nullable=False)