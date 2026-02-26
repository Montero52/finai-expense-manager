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

# 2. Tạo bảng database (nếu chưa có)
with app.app_context(): 
    db.create_all()

# 3. Đăng ký Blueprint cho báo cáo
from app.routes.auth import auth_bp
from app.routes.core import core_bp
from app.routes.report import report_bp
from app.routes.ai import ai_bp
from app.routes.admin import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(core_bp)
app.register_blueprint(report_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(admin_bp)