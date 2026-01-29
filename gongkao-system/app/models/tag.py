"""
薄弱项标签模型 - 记录学员的薄弱知识点
"""
from datetime import datetime
from app import db


class WeaknessTag(db.Model):
    """
    薄弱项标签模型
    
    通过标签化管理学员的薄弱知识点，支持多级分类
    """
    __tablename__ = 'weakness_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, comment='学员ID')
    
    # 知识点分类
    module = db.Column(db.String(50), nullable=False, comment='一级模块')
    sub_module = db.Column(db.String(100), comment='子模块/知识点')
    
    # 掌握程度
    accuracy_rate = db.Column(db.Float, comment='正确率(%)')
    level = db.Column(db.String(10), default='yellow', comment='难度等级(red/yellow/green)')
    
    # 练习统计
    practice_count = db.Column(db.Integer, default=0, comment='练习次数')
    last_practice_date = db.Column(db.Date, comment='最后练习日期')
    
    # 状态
    is_resolved = db.Column(db.Boolean, default=False, comment='是否已攻克')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<WeaknessTag {self.module}-{self.sub_module}>'
    
    @staticmethod
    def get_level_from_rate(rate):
        """
        根据正确率计算等级
        
        Args:
            rate: 正确率(0-100)
        
        Returns:
            等级: red/yellow/green
        """
        if rate < 50:
            return 'red'
        elif rate < 70:
            return 'yellow'
        else:
            return 'green'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'module': self.module,
            'sub_module': self.sub_module,
            'accuracy_rate': self.accuracy_rate,
            'level': self.level,
            'practice_count': self.practice_count,
            'is_resolved': self.is_resolved,
        }


class ModuleCategory(db.Model):
    """
    知识点分类表 - 存储题型/知识点体系
    """
    __tablename__ = 'module_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    level1 = db.Column(db.String(50), nullable=False, comment='一级分类')
    level2 = db.Column(db.String(100), comment='二级分类')
    level3 = db.Column(db.String(150), comment='三级分类')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    def __repr__(self):
        return f'<ModuleCategory {self.level1}-{self.level2}>'
    
    @staticmethod
    def get_modules():
        """获取所有一级模块"""
        return db.session.query(ModuleCategory.level1).distinct().all()
    
    @staticmethod
    def get_sub_modules(level1):
        """获取指定一级模块下的所有子模块"""
        return ModuleCategory.query.filter_by(level1=level1).all()
