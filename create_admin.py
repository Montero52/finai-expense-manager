# create_admin.py
import uuid
from app import app, db
from app.models import User, UserSetting, Wallet

# Cấu hình Admin
ADMIN_EMAIL = "admin@finance.com"
ADMIN_PASS = "admin123"
ADMIN_NAME = "Quản Trị Viên Hệ Thống"

def create_admin():
    # Cần chạy trong Application Context của Flask để truy cập được DB
    with app.app_context():
        db.create_all()
        # 1. Kiểm tra xem admin đã tồn tại chưa
        existing_user = User.query.filter_by(email=ADMIN_EMAIL).first()
        if existing_user:
            print(f"Tài khoản {ADMIN_EMAIL} đã tồn tại!")
            return

        try:
            # 2. Tạo User Admin
            user_id = str(uuid.uuid4())[:8]
            admin_user = User(
                id=user_id,
                name=ADMIN_NAME,
                email=ADMIN_EMAIL,
                role='admin',
                status=1
            )
            admin_user.set_password(ADMIN_PASS)
            db.session.add(admin_user)

            # 3. Tạo thiết lập mặc định
            setting = UserSetting(user_id=user_id)
            db.session.add(setting)
            
            # 4. Tạo ví mặc định cho Admin (để test)
            wallet = Wallet(
                id=str(uuid.uuid4())[:8],
                user_id=user_id,
                name="Kho bạc Admin",
                type="Tiền mặt",
                balance=999999999
            )
            db.session.add(wallet)

            # Lưu tất cả
            db.session.commit()
            
            print("="*40)
            print("ĐÃ TẠO TÀI KHOẢN ADMIN THÀNH CÔNG!")
            print(f"Email: {ADMIN_EMAIL}")
            print(f"Pass:  {ADMIN_PASS}")
            print("="*40)

        except Exception as e:
            db.session.rollback()
            print(f"Lỗi: {e}")

if __name__ == "__main__":
    create_admin()