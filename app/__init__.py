import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from config import Config

# 1. Khởi tạo Flask App và Database ngay lập tức
app = Flask(__name__)
app.config.from_object(Config)

# Tự động tạo thư mục instance nếu chưa có (Để tránh lỗi khi chạy lần đầu)
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

db = SQLAlchemy(app)
mail = Mail(app)

# 2. Import routes và models Ở CUỐI FILE
# Lý do: Để khi routes.py chạy, biến 'app' và 'db' ở trên đã được tạo xong.
from app import routes, models


# 3. Tạo bảng database (nếu chưa có)
with app.app_context(): 
    db.create_all()

# 4. Đăng ký Blueprint cho báo cáo
from app.routes import report_bp
app.register_blueprint(report_bp)