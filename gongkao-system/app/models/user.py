"""
用户模型 - 用于认证和权限管理
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class User(UserMixin, db.Model):
    """
    用户模型
    
    角色：
    - admin: 管理员，拥有所有权限
    - supervisor: 督学人员，管理自己负责的学员
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    password_hash = db.Column(db.String(255), nullable=False, comment='密码哈希')
    real_name = db.Column(db.String(50), comment='真实姓名')
    role = db.Column(db.String(20), nullable=False, default='supervisor', comment='角色')
    phone = db.Column(db.String(20), comment='手机号')
    email = db.Column(db.String(100), comment='邮箱')
    last_login = db.Column(db.DateTime, comment='最后登录时间')
    status = db.Column(db.String(20), default='active', comment='状态')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """是否是管理员"""
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login用户加载函数"""
    return User.query.get(int(user_id))
