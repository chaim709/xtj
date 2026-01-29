"""
用户认证路由 - 登录/注销
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    # 已登录用户跳转到工作台
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        from app.models.user import User
        from datetime import datetime
        from app import db
        
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('请输入用户名和密码', 'danger')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('用户名或密码错误', 'danger')
            return render_template('auth/login.html')
        
        if user.status != 'active':
            flash('账号已被禁用，请联系管理员', 'danger')
            return render_template('auth/login.html')
        
        # 登录成功
        login_user(user, remember=remember)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        flash(f'欢迎回来，{user.real_name or user.username}！', 'success')
        
        # 跳转到之前请求的页面或工作台
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('dashboard.index'))
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """注销"""
    logout_user()
    flash('您已成功退出登录', 'info')
    return redirect(url_for('auth.login'))
