from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from flask_mail import Message
import uuid
import secrets
from datetime import datetime, timedelta

# Import nội bộ
from app import db, mail
from app.models import User, UserSetting, Wallet, PasswordResetToken

# 1. Khai báo Blueprint
auth_bp = Blueprint('auth', __name__)

# ==========================================
# AUTHENTICATION ROUTES (Xác thực)
# ==========================================

@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Nếu đã đăng nhập, chuyển hướng ngay
    if 'user_id' in session:
        if session.get('user_role') == 'admin':
            return redirect(url_for('admin.users')) # Lưu ý: Sau này đổi thành admin.users
        return redirect(url_for('core.dashboard'))  # Lưu ý: Sau này đổi thành core.dashboard

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            
            if user.role == 'admin':
                return redirect(url_for('admin.users')) # Lưu ý khi tách blueprint
            return redirect(url_for('core.dashboard'))  # Lưu ý khi tách blueprint
        else:
            flash('Email hoặc mật khẩu không chính xác.', 'error')

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        password = request.form['password'].strip()
        confirm_password = request.form.get('confirm-password', '').strip()

        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp!', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email này đã được đăng ký!', 'error')
            return redirect(url_for('auth.register'))

        try:
            # 1. Tạo User
            new_user_id = str(uuid.uuid4())[:8]
            new_user = User(id=new_user_id, name=fullname, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            
            # 2. Tạo Setting & Ví mặc định
            db.session.add(UserSetting(user_id=new_user_id))
            db.session.add(Wallet(
                id=str(uuid.uuid4())[:8],
                user_id=new_user_id,
                name="Ví tiền mặt",
                type="Tiền mặt",
                balance=0
            ))

            db.session.commit()
            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi hệ thống: {str(e)}', 'error')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

# --- Quên Mật Khẩu ---

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('Email này chưa được đăng ký!', 'error')
            return redirect(url_for('auth.forgot_password'))
            
        token = secrets.token_urlsafe(32)
        expiration = datetime.now() + timedelta(minutes=15)
        
        # Upsert token
        reset_entry = PasswordResetToken.query.filter_by(email=email).first()
        if reset_entry:
            reset_entry.token = token
            reset_entry.expires_at = expiration
        else:
            db.session.add(PasswordResetToken(email=email, token=token, expires_at=expiration))
            
        db.session.commit()
        
        try:
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            msg = Message('Khôi phục mật khẩu - AI Finance', recipients=[email])
            msg.body = f"Bấm vào link để đặt lại mật khẩu:\n{reset_url}\nLink hết hạn sau 15 phút."
            mail.send(msg)
            return redirect(url_for('auth.email_sent'))
        except Exception as e:
            print(e)
            flash('Lỗi gửi email.', 'error')

    return render_template('auth/forgot_password.html')

@auth_bp.route('/email-sent')
def email_sent():
    return render_template('auth/email_sent.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset_entry = PasswordResetToken.query.filter_by(token=token).first()
    
    if not reset_entry or reset_entry.expires_at < datetime.now():
        flash('Link không hợp lệ hoặc đã hết hạn!', 'error')
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        password = request.form['new-password']
        confirm_password = request.form['confirm-password']
        
        if password != confirm_password:
            flash('Mật khẩu không khớp', 'error')
            return redirect(url_for('auth.reset_password', token=token))
            
        user = User.query.filter_by(email=reset_entry.email).first()
        if user:
            user.set_password(password)
            db.session.delete(reset_entry)
            db.session.commit()
            flash('Thành công! Hãy đăng nhập.', 'success')
            return redirect(url_for('auth.login'))
            
    return render_template('auth/reset_password.html', token=token)