import os
from dotenv import load_dotenv

# Lấy đường dẫn thư mục hiện tại
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load dữ liệu từ file .env
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    # 1. Secret Key
    # Nếu không tìm thấy trong .env thì dùng key mặc định (cho an toàn khi chạy dev)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'khoa-mac-dinh-khong-an-toan'
    
    # 2. Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'quanlychitieu.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 3. Cấu hình Email (Lấy từ .env)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')