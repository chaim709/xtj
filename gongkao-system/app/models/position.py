"""
岗位模型 - 存储公务员岗位信息
"""
from datetime import datetime
from app import db


class Position(db.Model):
    """
    岗位模型
    
    存储公务员岗位的基本信息、招录条件和竞争数据
    """
    __tablename__ = 'positions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 年份和考试类型
    year = db.Column(db.Integer, nullable=False, index=True, comment='年份')
    exam_type = db.Column(db.String(20), nullable=False, default='省考', comment='考试类型：省考/国考')
    
    # 地区信息
    affiliation = db.Column(db.String(20), comment='隶属关系：省/市/县')
    region_code = db.Column(db.String(20), comment='地区代码')
    region_name = db.Column(db.String(50), index=True, comment='地区名称')
    city = db.Column(db.String(50), index=True, comment='所属城市')
    system_type = db.Column(db.String(50), index=True, comment='系统类型：省级机关/监狱戒毒/统计系统/各市')
    
    # 单位信息
    department_code = db.Column(db.String(20), comment='单位代码')
    department_name = db.Column(db.String(100), index=True, comment='单位名称')
    
    # 职位信息
    position_code = db.Column(db.String(20), comment='职位代码')
    position_name = db.Column(db.String(100), comment='职位名称')
    position_desc = db.Column(db.Text, comment='职位简介')
    
    # 招录条件
    exam_category = db.Column(db.String(10), comment='考试类别：A/B/C')
    open_ratio = db.Column(db.Integer, default=3, comment='开考比例')
    recruit_count = db.Column(db.Integer, default=1, comment='招考人数')
    education = db.Column(db.String(50), comment='学历要求')
    major_requirement = db.Column(db.Text, comment='专业要求（原始文本）')
    other_requirements = db.Column(db.Text, comment='其他条件')
    
    # 竞争数据（报名后更新）
    apply_count = db.Column(db.Integer, comment='报名人数')
    competition_ratio = db.Column(db.Float, comment='竞争比')
    min_entry_score = db.Column(db.Float, comment='最低进面分')
    max_entry_score = db.Column(db.Float, comment='最高进面分')
    max_xingce_score = db.Column(db.Float, comment='最高行测分')
    max_shenlun_score = db.Column(db.Float, comment='最高申论分')
    max_police_score = db.Column(db.Float, comment='公安专业知识最高分')
    min_police_score = db.Column(db.Float, comment='公安专业知识最低分')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 唯一约束：年份+考试类型+地区代码+单位代码+职位代码
    __table_args__ = (
        db.UniqueConstraint('year', 'exam_type', 'region_code', 'department_code', 'position_code', 
                           name='uix_position_unique'),
    )
    
    def __repr__(self):
        return f'<Position {self.year}-{self.department_name}-{self.position_name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'year': self.year,
            'exam_type': self.exam_type,
            'city': self.city,
            'region_name': self.region_name,
            'department_name': self.department_name,
            'position_code': self.position_code,
            'position_name': self.position_name,
            'position_desc': self.position_desc,
            'exam_category': self.exam_category,
            'recruit_count': self.recruit_count,
            'education': self.education,
            'major_requirement': self.major_requirement,
            'other_requirements': self.other_requirements,
            'apply_count': self.apply_count,
            'competition_ratio': self.competition_ratio,
            'min_entry_score': self.min_entry_score,
            'max_entry_score': self.max_entry_score,
        }
    
    @property
    def difficulty_level(self):
        """
        计算难度级别
        
        Returns:
            str: easy/medium/hard
        """
        if self.competition_ratio is None:
            return 'unknown'
        
        if self.competition_ratio > 50 or (self.min_entry_score and self.min_entry_score > 145):
            return 'hard'
        elif self.competition_ratio > 20 or (self.min_entry_score and self.min_entry_score > 130):
            return 'medium'
        else:
            return 'easy'
    
    @property
    def difficulty_score(self):
        """
        计算难度分数 (0-100)
        
        Returns:
            float: 难度分数
        """
        score = 0
        
        # 竞争比权重 40%
        if self.competition_ratio:
            ratio_score = min(self.competition_ratio / 100 * 100, 100)
            score += ratio_score * 0.4
        
        # 进面分权重 40%
        if self.min_entry_score:
            # 假设满分200，进面分130-160之间
            score_pct = (self.min_entry_score - 100) / 60 * 100
            score += min(max(score_pct, 0), 100) * 0.4
        
        # 招录人数权重 20%（招的越少越难）
        if self.recruit_count:
            count_score = max(100 - self.recruit_count * 10, 0)
            score += count_score * 0.2
        
        return round(score, 1)


class StudentPosition(db.Model):
    """
    学员-岗位关联表
    
    记录学员收藏、推荐、报名的岗位
    """
    __tablename__ = 'student_positions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, comment='学员ID')
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id'), nullable=False, comment='岗位ID')
    status = db.Column(db.String(20), default='recommended', comment='状态：recommended/favorite/applied')
    match_score = db.Column(db.Float, comment='匹配分数')
    recommend_reason = db.Column(db.Text, comment='推荐理由')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关系
    student = db.relationship('Student', backref=db.backref('position_relations', lazy='dynamic'))
    position = db.relationship('Position', backref=db.backref('student_relations', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'position_id', name='uix_student_position'),
    )
    
    def __repr__(self):
        return f'<StudentPosition {self.student_id}-{self.position_id}>'
