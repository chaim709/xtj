"""
用户模型 - User & UserProfile
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    """用户基本信息表"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    real_name = db.Column(db.String(50))
    
    # 用户类型
    role = db.Column(db.String(20), default='student')  # student/admin
    
    # 状态
    is_active = db.Column(db.Boolean, default=True)
    is_vip = db.Column(db.Boolean, default=False)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # 关联关系
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    recommendations = db.relationship('Recommendation', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class UserProfile(db.Model):
    """用户画像表"""
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # 学历信息
    education = db.Column(db.String(20))  # 专科/本科/研究生/博士
    major = db.Column(db.String(100))  # 专业名称
    major_category = db.Column(db.String(50))  # 专业大类
    graduation_year = db.Column(db.Integer)  # 毕业年份
    graduation_status = db.Column(db.String(20))  # 应届/往届
    
    # 成绩信息
    estimated_score = db.Column(db.Integer)  # 预估分数
    xingce_score = db.Column(db.Integer)  # 行测分数
    shenlun_score = db.Column(db.Integer)  # 申论分数
    
    # 地域偏好
    preferred_cities = db.Column(db.Text)  # JSON格式：["合肥市", "芜湖市"]
    acceptable_cities = db.Column(db.Text)  # JSON格式
    base_layer_willing = db.Column(db.Boolean, default=False)  # 是否愿意去基层
    
    # 特殊身份
    special_status = db.Column(db.String(50))  # 服务基层项目人员/退役军人/党员
    political_status = db.Column(db.String(20))  # 党员/团员/群众
    has_work_experience = db.Column(db.Boolean, default=False)
    work_years = db.Column(db.Integer, default=0)
    
    # 期望条件
    min_salary = db.Column(db.Integer)  # 最低年薪期望
    development_priority = db.Column(db.Boolean, default=False)  # 是否优先发展
    
    # 竞争力评分
    competitiveness_score = db.Column(db.Integer)  # 0-100分
    score_details = db.Column(db.Text)  # JSON格式的详细评分
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserProfile user_id={self.user_id}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'education': self.education,
            'major': self.major,
            'major_category': self.major_category,
            'graduation_status': self.graduation_status,
            'estimated_score': self.estimated_score,
            'preferred_cities': self.preferred_cities,
            'special_status': self.special_status,
            'political_status': self.political_status,
            'competitiveness_score': self.competitiveness_score
        }
