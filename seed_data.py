from app import app, db
from app.models import User, Category, Wallet, Transaction, UserSetting
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

def seed_database():
    with app.app_context():
        print("Đang xóa Database cũ và tạo lại cấu trúc mới...")
        db.drop_all()  # Xóa sạch các bảng cũ bị lỗi/sai kiểu dữ liệu
        db.create_all() # Tạo lại các bảng mới chuẩn Integer
        print("Đã khởi tạo cấu trúc dữ liệu thành công!")

        try:
            # ==========================================
            # 1. TẠO NGƯỜI DÙNG (Không tự gán ID)
            # ==========================================
            print("Đang tạo Người dùng...")
            admin = User(
                name="Admin Tối Cao", email="admin@finai.com", 
                password_hash=generate_password_hash("123456"), role="admin", status=1
            )
            user1 = User(
                name="Nguyễn Văn A", email="nva@finai.com", 
                password_hash=generate_password_hash("123456"), role="user", status=1
            )
            db.session.add_all([admin, user1])
            
            # ĐIỂM NHẤN: Dùng flush() để lấy ID số nguyên cho admin và user1
            db.session.flush() 

            # Tạo Thiết lập cho User (Vì database yêu cầu)
            db.session.add_all([
                UserSetting(user_id=admin.id),
                UserSetting(user_id=user1.id)
            ])

            # ==========================================
            # 2. TẠO DANH MỤC GỐC
            # ==========================================
            print("Đang tạo Danh mục gốc...")
            cat_luong = Category(name="Tiền lương", type="thu", user_id=None)
            cat_thuong = Category(name="Tiền thưởng", type="thu", user_id=None)
            cat_anuong = Category(name="Ăn uống", type="chi", user_id=None)
            cat_dichuyen = Category(name="Di chuyển", type="chi", user_id=None)
            cat_muasam = Category(name="Mua sắm", type="chi", user_id=None)
            
            db.session.add_all([cat_luong, cat_thuong, cat_anuong, cat_dichuyen, cat_muasam])
            db.session.flush() # Lấy ID cho các danh mục

            # ==========================================
            # 3. TẠO NGUỒN TIỀN (VÍ)
            # ==========================================
            print("Đang tạo Nguồn tiền (Ví)...")
            wallet_tienmat = Wallet(name="Ví tiền mặt", type="tien_mat", balance=2000000, user_id=user1.id)
            wallet_vib = Wallet(name="Thẻ VIB", type="ngan_hang", balance=15000000, user_id=user1.id)
            
            db.session.add_all([wallet_tienmat, wallet_vib])
            db.session.flush() # Lấy ID cho các ví

            # ==========================================
            # 4. TẠO GIAO DỊCH TEST
            # ==========================================
            print("Đang tạo Giao dịch test...")
            base_date = datetime.now()
            transactions = []

            # Giao dịch THU
            transactions.append(Transaction(
                user_id=user1.id, wallet_id=wallet_vib.id, category_id=cat_luong.id,
                type="thu", amount=15000000, description="Lương tháng này", 
                date=base_date.date() - timedelta(days=5) # Lưu ý: date() vì trong models là db.Date
            ))
            
            # Giao dịch CHI ngẫu nhiên
            notes_chi = ["Ăn phở", "Đổ xăng", "Mua áo phông", "Uống cafe", "Đi siêu thị"]
            cats_chi = [cat_anuong.id, cat_dichuyen.id, cat_muasam.id]
            
            for i in range(15):
                t_date = base_date.date() - timedelta(days=random.randint(0, 15))
                t_amount = random.randint(3, 50) * 10000
                
                transactions.append(Transaction(
                    user_id=user1.id, wallet_id=wallet_tienmat.id, category_id=random.choice(cats_chi),
                    type="chi", amount=t_amount, description=random.choice(notes_chi), date=t_date
                ))

            db.session.add_all(transactions)

            # LƯU CHÍNH THỨC TẤT CẢ VÀO DATABASE
            db.session.commit()

            print("==========================================")
            print("TẠO DỮ LIỆU MẪU THÀNH CÔNG!")
            print("Admin : admin@finai.com / 123456")
            print("User  : nva@finai.com   / 123456")
            print("==========================================")

        except Exception as e:
            db.session.rollback()
            print(f"Lỗi khi tạo dữ liệu: {e}")

if __name__ == "__main__":
    seed_database()