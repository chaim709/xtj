"""
专业目录模型 - 存储专业大类和具体专业的映射关系
"""
from datetime import datetime
from app import db


class MajorCategory(db.Model):
    """
    专业大类模型
    
    存储专业参考目录中的50个专业大类
    """
    __tablename__ = 'major_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Integer, nullable=False, comment='序号（1-50）')
    name = db.Column(db.String(50), nullable=False, index=True, comment='大类名称')
    year = db.Column(db.Integer, default=2026, comment='适用年份')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    majors = db.relationship('Major', backref='category', lazy='dynamic', cascade='all, delete-orphan')
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('code', 'year', name='uix_category_code_year'),
    )
    
    def __repr__(self):
        return f'<MajorCategory {self.code}-{self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'year': self.year,
            'major_count': self.majors.count() if self.majors else 0
        }


class Major(db.Model):
    """
    具体专业模型
    
    存储每个专业大类下的具体专业名称
    """
    __tablename__ = 'majors'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('major_categories.id'), nullable=False, comment='所属专业大类ID')
    name = db.Column(db.String(100), nullable=False, index=True, comment='专业名称')
    education_level = db.Column(db.String(20), comment='学历层次：研究生/本科/专科')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 唯一约束：同一大类下同一学历层次的专业名称唯一
    __table_args__ = (
        db.UniqueConstraint('category_id', 'name', 'education_level', name='uix_major_unique'),
        db.Index('idx_major_name', 'name'),
    )
    
    def __repr__(self):
        return f'<Major {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'name': self.name,
            'education_level': self.education_level
        }


# 预定义的50个专业大类（用于初始化）
MAJOR_CATEGORIES = [
    (1, '中文文秘类'),
    (2, '艺术类'),
    (3, '法律类'),
    (4, '社会政治类'),
    (5, '经济类'),
    (6, '公共管理类'),
    (7, '工商管理类'),
    (8, '商务贸易类'),
    (9, '财务财会类'),
    (10, '税务税收类'),
    (11, '统计类'),
    (12, '审计类'),
    (13, '教育类'),
    (14, '外国语言文学类'),
    (15, '公安类'),
    (16, '监所管理类'),
    (17, '计算机类'),
    (18, '计算机（软件）类'),
    (19, '计算机（网络管理）类'),
    (20, '电子信息类'),
    (21, '机电控制类'),
    (22, '机械工程类'),
    (23, '交通工程类'),
    (24, '航道港口类'),
    (25, '船舶工程类'),
    (26, '水利工程类'),
    (27, '城建规划类'),
    (28, '土地管理类'),
    (29, '测绘类'),
    (30, '建筑工程类'),
    (31, '材料工程类'),
    (32, '地质矿产类'),
    (33, '安全生产类'),
    (34, '能源动力类'),
    (35, '环境保护类'),
    (36, '化学工程类'),
    (37, '医药化工类'),
    (38, '食品工程类'),
    (39, '生物工程类'),
    (40, '轻工纺织类'),
    (41, '农业类'),
    (42, '林业类'),
    (43, '畜牧养殖类'),
    (44, '医学类'),
    (45, '公共卫生类'),
    (46, '药学类'),
    (47, '基础理学类'),
    (48, '兵工宇航类'),
    (49, '仪表仪器及测试技术类'),
    (50, '军事学类'),
]
