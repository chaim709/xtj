"""
岗位模型 - Position
"""
from datetime import datetime
from app import db


class Position(db.Model):
    """岗位信息表"""
    __tablename__ = 'positions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 基本信息（江苏版默认 2025 年）
    year = db.Column(db.Integer, nullable=False, default=2025, index=True)
    exam_type = db.Column(db.String(20), default='事业单位', index=True)
    city = db.Column(db.String(50), index=True)  # 地市
    affiliation = db.Column(db.String(20))  # 隶属关系
    region_name = db.Column(db.String(50))  # 区域名称
    system_type = db.Column(db.String(50), index=True)  # 系统类型
    
    # 单位和岗位
    department_code = db.Column(db.String(50))  # 单位代码
    department_name = db.Column(db.String(200), index=True)  # 单位名称
    position_code = db.Column(db.String(50))  # 岗位代码
    position_name = db.Column(db.String(200))  # 岗位名称
    position_desc = db.Column(db.Text)  # 岗位描述
    
    # 考试信息
    exam_category = db.Column(db.String(20))  # 考试类别(A/B/C/D/E)
    open_ratio = db.Column(db.Integer)  # 开考比例
    recruit_count = db.Column(db.Integer, default=1)  # 招录人数
    
    # 条件要求
    education = db.Column(db.String(100))  # 学历要求
    major_requirement = db.Column(db.Text)  # 专业要求
    other_requirements = db.Column(db.Text)  # 其他要求
    
    # 竞争数据（部分岗位可能没有）
    apply_count = db.Column(db.Integer)  # 报名人数
    competition_ratio = db.Column(db.Float)  # 竞争比
    min_entry_score = db.Column(db.Float)  # 最低进面分
    max_entry_score = db.Column(db.Float)  # 最高进面分
    
    # 分析字段（系统计算）
    estimated_salary = db.Column(db.Integer)  # 预估年薪（万元）
    estimated_competition_ratio = db.Column(db.Float, index=True)  # 预估竞争比
    difficulty_level = db.Column(db.String(20))  # 难度等级
    recommendation_score = db.Column(db.Float)  # 推荐评分
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    favorites = db.relationship('Favorite', backref='position', lazy='dynamic', cascade='all, delete-orphan')
    recommendations = db.relationship('Recommendation', backref='position', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Position {self.department_name} - {self.position_name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'year': self.year,
            'exam_type': self.exam_type,
            'city': self.city,
            'affiliation': self.affiliation,
            'region_name': self.region_name,
            'system_type': self.system_type,
            'department_code': self.department_code,
            'department_name': self.department_name,
            'position_code': self.position_code,
            'position_name': self.position_name,
            'position_desc': self.position_desc,
            'exam_category': self.exam_category,
            'recruit_count': self.recruit_count,
            'education': self.education,
            'major_requirement': self.major_requirement,
            'other_requirements': self.other_requirements,
            'competition_ratio': self.competition_ratio,
            'min_entry_score': self.min_entry_score,
            'estimated_salary': self.estimated_salary,
            'estimated_competition_ratio': self.estimated_competition_ratio,
            'difficulty_level': self.difficulty_level,
            'recommendation_score': self.recommendation_score
        }
    
    @staticmethod
    def get_cities(year=2025, exam_type='事业单位'):
        """获取所有城市列表"""
        cities = db.session.query(Position.city).filter(
            Position.year == year,
            Position.exam_type == exam_type,
            Position.city.isnot(None)
        ).distinct().order_by(Position.city).all()
        return [city[0] for city in cities]
    
    @staticmethod
    def get_system_types():
        """获取所有系统类型"""
        types = db.session.query(Position.system_type).filter(
            Position.system_type.isnot(None)
        ).distinct().order_by(Position.system_type).all()
        return [t[0] for t in types]
