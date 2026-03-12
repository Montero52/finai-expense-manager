import os
from app import app, db
from app.models import User, Wallet

# Cấu hình Admin (ưu tiên lấy từ biến môi trường, fallback cho môi trường dev)
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@finance.com")
ADMIN_PASS = os.environ.get("ADMIN_PASSWORD", "admin123")
ADMIN_NAME = os.environ.get("ADMIN_NAME", "Quản Trị Viên Hệ Thống")

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
            admin_user = User(
                name=ADMIN_NAME,
                email=ADMIN_EMAIL,
                role='admin',
                status=1
            )
            admin_user.set_password(ADMIN_PASS)
            db.session.add(admin_user)

            # 3. Tạo thiết lập mặc định
            db.session.flush()
            
            # 4. Tạo ví mặc định cho Admin (để test)
            wallet = Wallet(
                user_id=admin_user.id,
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